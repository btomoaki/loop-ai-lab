import os
import re
import subprocess
import yaml
from datetime import datetime
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser
from runner.utils.context_loader import ContextLoader
from runner.adapters.llm_adapter import LLMAdapterFactory
from runner.git_ops import ensure_target_git_init, commit_sprint_checkpoint, rollback_to_last_checkpoint


class SprintExecutionEngine:
    """【セレモニー 3】スプリント開発 & DoD受入判定エンジン (ステップ型レイヤー分割リクエスト・アーキテクチャ)"""

    def __init__(self, root_dir: Path, config: ProjectConfig = None):
        self.root_dir = root_dir
        self.config = config or ProjectConfig.load(root_dir)
        self.init_dir = root_dir / "state" / "initiatives"
        self.eval_dir = root_dir / "state" / ".evaluator"
        self.status_file = root_dir / "state" / "status.md"
        
        dev_provider = self._get_dev_provider()
        print(f"🧠 [SprintExecutionEngine] Using Provider '{dev_provider}' for Autonomous TDD Loop.", flush=True)
        self.dev_agent = LLMAdapterFactory.get_adapter(provider=dev_provider)

    def _get_dev_provider(self) -> str:
        # project_config の executor_provider (llama_cpp) を最優先で使用します
        if hasattr(self, "config") and self.config and self.config.executor_provider:
            return self.config.executor_provider

        config_file = self.root_dir / "config.yaml"
        if config_file.exists():
            try:
                data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
                return data.get("EXECUTOR_PROVIDER", data.get("DEFAULT_LLM_PROVIDER", "local"))
            except Exception:
                pass
        return "local"

    @staticmethod
    def sanitize_module_name(raw_name: str, lang: str) -> str:
        """言語ごとの識別子・パッケージ名ルールに沿ってサニタイズ"""
        if not raw_name:
            return "app"
        clean = raw_name.replace("workspace/", "").strip("/")
        if "/" in clean:
            clean = clean.split("/")[-1]

        l = lang.lower()
        if l in ["python", "py"]:
            return re.sub(r"[^a-zA-Z0-9_]", "_", clean).lower()
        elif l in ["go", "golang"]:
            # Goはハイフン許容 (URL path style)
            return re.sub(r"[^a-zA-Z0-9_\-\.]", "-", clean).lower()
        elif l in ["rust"]:
            return re.sub(r"[^a-zA-Z0-9_]", "_", clean).lower()
        else:
            return re.sub(r"[^a-zA-Z0-9_\-]", "_", clean).lower()

    def update_status_dashboard(self, active_epic: str, sprint_num: int, current_task: str, tdd_status: str, epic_statuses: dict):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        active_epic_dir = self.init_dir / active_epic
        active_total_sprints = len(list(active_epic_dir.glob("sprint_*_backlog.yaml"))) if active_epic_dir.exists() else 1
        active_sprint_str = f"Sprint {sprint_num}/{active_total_sprints}" if active_total_sprints > 0 else f"Sprint {sprint_num}"

        epic_rows = []
        for e_name, status in epic_statuses.items():
            e_dir = self.init_dir / e_name
            total_s = len(list(e_dir.glob("sprint_*_backlog.yaml"))) if e_dir.exists() else 0
            total_meta = f"(全 {total_s} スプリント)" if total_s > 0 and "(" not in status else ""
            epic_rows.append(f"- **{e_name}**: {status} {total_meta}".strip())
        epic_summary_block = "\n".join(epic_rows)

        dashboard_content = f"""# 📌 Loop AI Lab - リアルタイム Scrum 進行状況ダッシュボード

- **現在実行中のフェーズ**: 🏃 【セレモニー 3】スプリント開発 & DoD受入判定
- **実行中エピック**: `{active_epic}` ({active_sprint_str})
- **処理中タスク**: `{current_task}`
- **TDD サイクル進行状態**: {tdd_status}
- **最終更新日時**: `{now_str}`

---

## 📊 全エピック進捗ステータス
{epic_summary_block}
"""
        CodeParser.atomic_write_text(self.status_file, dashboard_content)
        print(f"📊 [Status Dashboard] Updated state/status.md (Active: {active_epic} ({active_sprint_str}) | Status: {tdd_status})", flush=True)

    def write_sprint_result_log(self, epic_dir: Path, sprint_num: int, backlog_data: dict, status: str, exit_code: int, written_files: list, error_log: str = None, attempt: int = 1, retry_reset: bool = False) -> Path:
        result_file = epic_dir / f"sprint_{sprint_num}_result.yaml"
        now_str = datetime.now().isoformat()
        
        rel_files = [str(Path(self.root_dir / f).relative_to(self.root_dir)) for f in written_files] if written_files else []
        
        result_data = {
            "sprint": sprint_num,
            "epic": backlog_data.get("epic", epic_dir.name),
            "timestamp": now_str,
            "status": status,
            "harness_exit_code": exit_code,
            "attempt": attempt,
            "retry_count_reset": retry_reset,
            "generated_files": rel_files,
            "tasks": backlog_data.get("tasks", [])
        }

        if error_log:
            result_data["last_error_log"] = error_log.strip()
        
        yaml_text = yaml.dump(result_data, default_flow_style=False, allow_unicode=True)
        CodeParser.atomic_write_text(result_file, yaml_text)
        print(f"📝 [Sprint Result Log] Saved {result_file.relative_to(self.root_dir)} (Status: {status})", flush=True)
        return result_file

    def get_active_epic_harness(self, epic_dir: Path, sprint_num: int = 1) -> Path:
        return epic_dir / f"sprint_{sprint_num}_harness.sh"

    def generate_layer_code(self, epic_dir: Path, sprint_num: int, backlog_data: dict, layer_name: str, layer_target: str, result_file_ref: Path = None) -> list:
        """1回のレスポンスで1つのレイヤーのみを出力させる段階型生成関数"""
        epic_name = backlog_data.get("epic", epic_dir.name)
        target_ws_rel = backlog_data.get("target_workspace") or self.config.workspace_rel or "workspace/app"
        target_ws = self.root_dir / target_ws_rel
        target_ws.mkdir(parents=True, exist_ok=True)

        lang = self.config.language or "target programming language"
        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="3_sprint_execution", include_dev_rules=True)
        inst_file = self.root_dir / "agents" / "3_sprint_execution" / "sprint_dev_executor.md"
        inst_content = inst_file.read_text(encoding="utf-8") if inst_file.exists() else f"Write clean {lang} code."

        backlog_file = epic_dir / f"sprint_{sprint_num}_backlog.yaml"
        backlog_content = backlog_file.read_text(encoding="utf-8") if backlog_file.exists() else yaml.dump(backlog_data)

        error_content = ""
        if result_file_ref and result_file_ref.exists():
            try:
                res_data = yaml.safe_load(result_file_ref.read_text(encoding="utf-8")) or {}
                last_log = res_data.get("last_error_log", "")
                if last_log:
                    error_content = f"\n=== PREVIOUS HARNESS FAILURE FEEDBACK ===\n{last_log}\nFix the implementation to resolve the above compiler or test errors."
            except Exception:
                pass

        # 言語ルールおよびクリーンアーキテクチャルールの本文を直接読み込み
        lang_rule_file = self.root_dir / ".agents" / "rules" / "languages" / f"{lang}.md"
        lang_rule_content = lang_rule_file.read_text(encoding="utf-8") if lang_rule_file.exists() else ""

        arch_rule_file = self.root_dir / ".agents" / "rules" / "development" / "clean_architecture_and_design.md"
        arch_rule_content = arch_rule_file.read_text(encoding="utf-8") if arch_rule_file.exists() else ""

        # config.yaml からモジュール名を取得し、言語仕様に即してサニタイズ
        raw_mod_name = getattr(self.config, "project_name", None) or target_ws.name
        clean_mod_name = self.sanitize_module_name(raw_mod_name, lang)
        project_file = "go.mod" if lang.lower() in ["go", "golang"] else "project_file"

        # 先行生成されたテストコードがある場合、実装レイヤーのコンテキストとして注入 (Test-First TDD)
        existing_test_context = ""
        if layer_name in ["Business_Logic_and_Usecase", "Entrypoint_and_Interface"]:
            test_files = list(target_ws.glob("**/*_test.go"))
            if test_files:
                test_snippets = []
                for tf in test_files[:3]:  # コンテキスト長を考慮し最大3ファイル
                    try:
                        rel_p = tf.relative_to(target_ws)
                        content = tf.read_text(encoding="utf-8")
                        test_snippets.append(f"--- [EXISTING TEST: {rel_p}] ---\n{content}\n")
                    except Exception:
                        pass
                if test_snippets:
                    existing_test_context = (
                        "\n=== 2.5 EXISTING TEST SPECIFICATIONS (TEST-FIRST TDD CONTRACT) ===\n"
                        "The following test files have been generated FIRST. Your implementation MUST strictly match\n"
                        "the function names, signatures, receiver types, and return types expected in these tests:\n"
                        + "\n".join(test_snippets) + "\n"
                    )

        prompt = (
            f"[INST]\n"
            f"=== 1. MANDATORY LANGUAGE & ARCHITECTURE RULES ===\n"
            f"{lang_rule_content}\n\n{arch_rule_content}\n\n"
            f"=== 2. EXECUTION INSTRUCTIONS ===\n{inst_content}\n\n"
            f"{existing_test_context}"
            f"[CRITICAL ARCHITECTURAL & CODING MANDATES]\n"
            f"1. The root module/package name in {project_file} and for all internal package imports MUST strictly be '{clean_mod_name}'.\n"
            f"2. NEVER prefix module names or internal imports with 'workspace/' or directory paths.\n"
            f"   - Correct:   import \"{clean_mod_name}/internal/domain/model\"\n"
            f"   - Forbidden: import \"workspace/{clean_mod_name}/...\" or \"workspace/...\"\n"
            f"3. [PACKAGE NAME COLLISION GUARD]: When importing both standard 'net/http' and internal '{clean_mod_name}/internal/interface/http',\n"
            f"   you MUST use an explicit alias for the internal package (e.g. `httpDelivery \"{clean_mod_name}/internal/interface/http\"`) to avoid 'redeclared' errors.\n"
            f"4. [STRICT PROHIBITION OF LOCKFILES]: NEVER generate or output 'go.sum', 'package-lock.json', or checksum files. Dependencies must be declared ONLY in {project_file}.\n"
            f"5. [NO UNAUTHORIZED SUBMODULES OR NESTED DIRECTORIES]: NEVER create 'go.mod' or 'go.sum' inside internal/ subdirectories.\n"
            f"6. [NO UNAUTHORIZED EXTERNAL LIBRARIES]: Do NOT import unapproved external libraries (e.g. gorilla/mux, time/rate) unless explicitly instructed in tasks.\n\n"
            f"=== 3. BACKLOG TASKS ===\n{backlog_content}\n"
            f"{error_content}\n\n"
            f"[TASK: CEREMONY 3 STEPPED CODE GENERATION - {epic_name} (Sprint {sprint_num})]\n"
            f"Target Workspace Path: {target_ws.relative_to(self.root_dir)}\n"
            f"Project Root Module Name: {clean_mod_name}\n"
            f"Programming Language: {lang}\n"
            f"CURRENT TARGET LAYER FOCUS: {layer_name} ({layer_target})\n\n"
            f"[STRICT OUTPUT FORMAT MANDATE]\n"
            f"For EACH file, you MUST write '[FILE: relative/path/to/file]' on its own separate line immediately BEFORE its code block.\n"
            f"NEVER combine multiple files into a single code block. NEVER use '# FILE:' comments inside code blocks.\n"
            f"Example format:\n"
            f"[FILE: internal/domain/model/entity.go]\n"
            f"```{lang}\npackage model\n...\n```\n\n"
            f"Generate ONLY files belonging to the {layer_name} layer ({layer_target}).\n"
            f"[/INST]\n"
        )

        actual_prompt_file = self.eval_dir / f"actual_dev_prompt_{layer_name.lower()}.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)

        print(f"💻 [SprintExecutionEngine Step: {layer_name}] Requesting LLM code generation...", flush=True)
        llm_response = self.dev_agent.generate_text(prompt)

        if not llm_response or not llm_response.strip():
            print(f"⚠️ [SprintExecutionEngine Warning] LLM returned empty response for layer {layer_name}!")
            return []

        CodeParser.atomic_write_text(self.root_dir / "state" / f"debug_llm_response_{layer_name.lower()}.txt", llm_response)
        written_files = CodeParser.apply_code_changes(llm_response, target_ws)

        # 🛡️ ロックファイル（go.sum）および不正なサブディレクトリ内 go.mod/go.sum の強制排除
        sanitized_written_files = []
        for wf in written_files:
            rel_wf = wf.relative_to(target_ws)
            if rel_wf.name == "go.sum":
                print(f"🛡️ [Lockfile Guard] Removing unauthorized LLM-generated lockfile: {rel_wf}")
                try:
                    wf.unlink(missing_ok=True)
                except Exception:
                    pass
                continue
            if len(rel_wf.parts) > 1 and rel_wf.name in ["go.mod", "go.sum"]:
                print(f"🛡️ [Submodule Guard] Removing unauthorized nested module file: {rel_wf}")
                try:
                    wf.unlink(missing_ok=True)
                except Exception:
                    pass
                continue
            sanitized_written_files.append(wf)

        print(f" [SprintExecutionEngine] Written {len(sanitized_written_files)} files for layer {layer_name}", flush=True)
        return sanitized_written_files

    @staticmethod
    def determine_target_layers(backlog_data: dict) -> list:
        """バックログのタスク内容を解析し、必要なレイヤーのみを動的に絞り込む"""
        tasks = backlog_data.get("tasks", [])
        if not tasks:
            return [
                ("Domain_and_Models", "Core domain models, schemas, and business entity structures"),
                ("Business_Logic_and_Usecase", "Application usecase / service logic handlers"),
                ("Entrypoint_and_Interface", "Main entrypoints, interface handlers/controllers, and build configs"),
                ("Unit_and_Integration_Tests", "Unit tests and integration test suites")
            ]

        text_corpus = ""
        for t in tasks:
            text_corpus += " " + t.get("title", "")
            text_corpus += " " + t.get("description", "")
            text_corpus += " " + " ".join(t.get("acceptance_criteria", []))
            text_corpus += " " + t.get("verify_command", "")
        text_lower = text_corpus.lower()

        # 1. パスによる直接判定（最優先・高精度）
        has_model_path = "internal/domain/model" in text_lower
        has_service_path = "internal/domain/service" in text_lower or "internal/usecase" in text_lower
        has_interface_path = any(p in text_lower for p in ["internal/interface", "cmd/", "docker", "compose", "makefile", "openapi"])

        # 専用タスク判定（既存コードの破壊防止・過剰レイヤー除外）
        is_pure_test_task = bool(re.search(r"\b(add|create|implement)\s+.*(unit\s+tests?|integration\s+tests?|test\s+cases?)\b", text_lower)) and not bool(re.search(r"\b(implement|create)\s+.*(service|handler|rasterizer|model)\b", text_lower))
        is_lint_or_docs_task = bool(re.search(r"\b(linter|golangci|\.golangci|readme|documentation|docs)\b", text_lower)) and not bool(re.search(r"\b(service|usecase|domain|matrix|hasher)\b", text_lower))

        # テスト単体追加タスク: 実装レイヤーを厳格に除外して既存コードの破壊を防止
        if is_pure_test_task:
            return [("Unit_and_Integration_Tests", "Unit tests and integration test suites")]

        # Linter / ドキュメント単体タスク: インターフェース・設定レイヤーのみ
        if is_lint_or_docs_task:
            return [("Entrypoint_and_Interface", "Main entrypoints, interface handlers/controllers, and build configs")]

        # Model層単体タスク（TASK-1.1等）: テスト不要・Model層のみ1ステップで即完了
        if has_model_path and not has_service_path and not has_interface_path:
            return [("Domain_and_Models", "Core domain models, schemas, and business entity structures")]

        selected = {}

        # 1. Domain & Models レイヤー判定
        if has_model_path or re.search(r"\bmodels?\b|\bentity\b|\bentities\b", text_lower):
            selected["Domain_and_Models"] = ("Domain_and_Models", "Core domain models, schemas, and business entity structures")

        # 2. Unit & Integration Tests レイヤー判定 (Test-First: テストを先行生成)
        if re.search(r"\btests?\b|\bverify\b|\bcoverage\b", text_lower):
            selected["Unit_and_Integration_Tests"] = ("Unit_and_Integration_Tests", "Unit tests and integration test suites")

        # 3. Business Logic & Usecase レイヤー判定
        if has_service_path or re.search(r"\bservices?\b|\busecases?\b|\bhash\b|\brasteriz\b|\bencoding\b", text_lower):
            selected["Business_Logic_and_Usecase"] = ("Business_Logic_and_Usecase", "Application usecase / service logic handlers")

        # 4. Entrypoint & Interface レイヤー判定
        if has_interface_path or re.search(r"\bcmd/|\bhttps?\b|\bhandlers?\b|\brouters?\b|\bapi\b|\bdocker\b|\bcompose\b|\bmakefile\b|\bopenapi\b", text_lower):
            selected["Entrypoint_and_Interface"] = ("Entrypoint_and_Interface", "Main entrypoints, interface handlers/controllers, and build configs")

        if not selected:
            selected["Domain_and_Models"] = ("Domain_and_Models", "Core domain models, schemas, and business entity structures")
            selected["Business_Logic_and_Usecase"] = ("Business_Logic_and_Usecase", "Application usecase / service logic handlers")

        # 🏆 Test-First TDD 順序でソート:
        # [1] Domain_and_Models -> [2] Unit_and_Integration_Tests (先行テスト) -> [3] Business_Logic_and_Usecase -> [4] Entrypoint_and_Interface
        test_first_order = [
            "Domain_and_Models",
            "Unit_and_Integration_Tests",
            "Business_Logic_and_Usecase",
            "Entrypoint_and_Interface"
        ]
        target_layers = [selected[layer_key] for layer_key in test_first_order if layer_key in selected]
        return target_layers

    def generate_code_in_steps(self, epic_dir: Path, sprint_num: int, backlog_data: dict, result_file_ref: Path = None) -> list:
        """必要なレイヤーのみを動的に判定・生成し、無駄な呼び出しとコンテキスト溢れを根絶する"""
        layers = self.determine_target_layers(backlog_data)
        layer_names = [l[0] for l in layers]
        print(f"🎯 [SprintExecutionEngine] Dynamically selected layers for Sprint {sprint_num}: {layer_names}", flush=True)

        all_written_files = []
        for l_name, l_target in layers:
            files = self.generate_layer_code(epic_dir, sprint_num, backlog_data, l_name, l_target, result_file_ref)
            all_written_files.extend(files)

        return all_written_files

    def run_sprint_task(self, epic_dir: Path, sprint_num: int, epic_statuses: dict, max_retries: int = 3) -> bool:
        backlog_path = epic_dir / f"sprint_{sprint_num}_backlog.yaml"
        harness_path = self.get_active_epic_harness(epic_dir, sprint_num)

        if not backlog_path.exists():
            epic_statuses[epic_dir.name] = "⚠️ バックログなし"
            return False

        try:
            raw_yaml = backlog_path.read_text(encoding="utf-8")
            backlog_data = yaml.safe_load(raw_yaml) or {}
        except Exception:
            epic_statuses[epic_dir.name] = "⚠️ バックログ破損"
            return False

        tasks = backlog_data.get("tasks", [])
        current_task_name = tasks[0].get("title", tasks[0].get("id", "Task")) if tasks else "Sprint Tasks"

        print(f"\n🏃 [SprintExecutionEngine] Processing Sprint {sprint_num} for: {epic_dir.name}", flush=True)

        last_written_files = []
        result_file_ref = epic_dir / f"sprint_{sprint_num}_result.yaml"

        total_sprints = len(list(epic_dir.glob("sprint_*_backlog.yaml"))) or 1
        sprint_progress_tag = f"Sprint {sprint_num}/{total_sprints}"

        # ⏩ レジューム判定: 既に PASSED 済みの場合はスキップ
        if result_file_ref.exists():
            try:
                res_data = yaml.safe_load(result_file_ref.read_text(encoding="utf-8")) or {}
                if res_data.get("status") == "PASSED":
                    print(f"⏩ [Resume Skip] {epic_dir.name} ({sprint_progress_tag}) は既に合格済みです。スキップして次へ進みます。", flush=True)
                    epic_statuses[epic_dir.name] = f"✅ 【Pass】{sprint_progress_tag} 合格済み"
                    self.update_status_dashboard(epic_dir.name, sprint_num, current_task_name, "✅ 合格済み (スキップ)", epic_statuses)
                    return True
            except Exception:
                pass

        # ターゲットリポジトリの Git 管理を保証
        target_ws_rel = backlog_data.get("target_workspace", "workspace/identicon-generator")
        target_ws_dir = (self.root_dir / target_ws_rel).resolve()
        ensure_target_git_init(target_ws_dir)

        for attempt in range(1, max_retries + 1):
            if attempt > 1:
                # 直前の失敗Attemptで散らかった残骸を直前の合格コミット状態へ安全に完全ロールバック
                print(f"🧹 [Auto-Rollback] Attempt {attempt}: Rolling back workspace to last clean checkpoint (HEAD)...", flush=True)
                rollback_to_last_checkpoint(target_ws_dir)

            tdd_status = f"🧪 TDD サイクル試行中 (Attempt {attempt}/{max_retries})"
            epic_statuses[epic_dir.name] = f"🏃 開発進行中 [{sprint_progress_tag} | {tdd_status}]"
            self.update_status_dashboard(epic_dir.name, sprint_num, current_task_name, tdd_status, epic_statuses)

            print(f"🔄 [TDD Cycle Attempt {attempt}/{max_retries}] Generating code in stepped layer requests...", flush=True)
            new_files = self.generate_code_in_steps(epic_dir, sprint_num, backlog_data, result_file_ref)
            if new_files:
                last_written_files = new_files

            if harness_path.exists():
                print(f"🧪 [TDD Cycle] Running Test Harness: {harness_path.name}", flush=True)
                res = subprocess.run(["bash", str(harness_path)], cwd=str(self.root_dir), capture_output=True, text=True)
                
                if res.returncode == 0:
                    print(f"🎉 [TDD Cycle Passed!] Harness for {epic_dir.name} Sprint {sprint_num} PASSED at Attempt {attempt}/{max_retries} with Exit Code 0!", flush=True)
                    if attempt > 1:
                        print(f"🔄 [Retry Count Reset] Resetting retry counter. Next sprint/task will start fresh from Attempt 1.", flush=True)
                    epic_statuses[epic_dir.name] = f"✅ 【Pass】{sprint_progress_tag} ハーネス合格! (Attempt {attempt})"
                    self.update_status_dashboard(epic_dir.name, sprint_num, current_task_name, f"✅ ハーネス合格 (Attempt {attempt})", epic_statuses)
                    
                    self.write_sprint_result_log(epic_dir, sprint_num, backlog_data, "PASSED", 0, last_written_files, attempt=attempt, retry_reset=True)
                    commit_sprint_checkpoint(target_ws_dir, epic_dir.name, sprint_num, current_task_name)
                    return True
                else:
                    last_error = res.stdout + "\n" + res.stderr
                    print(f"⚠️ [TDD Cycle Failed] Attempt {attempt} returned exit code {res.returncode}. Logged to result.yaml.", flush=True)
                    result_file_ref = self.write_sprint_result_log(epic_dir, sprint_num, backlog_data, "FAILED", res.returncode, last_written_files, last_error, attempt=attempt, retry_reset=False)

        epic_statuses[epic_dir.name] = f"❌ 【Fail】{sprint_progress_tag} リトライ上限到達 ({max_retries} 回)"
        self.update_status_dashboard(epic_dir.name, sprint_num, current_task_name, "🛑 開発失敗・安全停止", epic_statuses)
        return False

    def run_sprint_development(self, sprint_num: int = None) -> bool:
        """スプリント自律開発＆DoD受入判定ループ (特定スプリント指定、または全スプリント完走)"""
        mode_desc = f"Sprint {sprint_num}" if sprint_num else "All Sprints in sequence"
        print(f"🚀 [Ceremony 3: Sprint Execution] Starting Autonomous TDD Development ({mode_desc})...", flush=True)
        
        epic_dirs = sorted([d for d in self.init_dir.glob("epic_*") if d.is_dir()])
        if not epic_dirs:
            print("⚠️ [SprintExecutionEngine] No active epic initiatives found in state/initiatives/!")
            return False

        epic_statuses = {d.name: "⏳ 待機中" for d in epic_dirs}
        
        for epic_dir in epic_dirs:
            # エピック内のバックログ一覧を取得してスプリント番号順にソート
            backlog_files = sorted(
                list(epic_dir.glob("sprint_*_backlog.yaml")),
                key=lambda p: int(re.search(r"sprint_(\d+)_backlog", p.name).group(1)) if re.search(r"sprint_(\d+)_backlog", p.name) else 999
            )
            
            if not backlog_files:
                continue

            # 特定スプリント番号が指定されている場合はそれのみ、指定なし(None)なら全スプリントをループ
            target_sprints = [sprint_num] if sprint_num else [
                int(re.search(r"sprint_(\d+)_backlog", p.name).group(1)) for p in backlog_files if re.search(r"sprint_(\d+)_backlog", p.name)
            ]

            for s_num in target_sprints:
                success = self.run_sprint_task(epic_dir, s_num, epic_statuses)
                if not success:
                    print(f"🛑 [Fail-Fast Safety Halt] Sprint {s_num} failed for '{epic_dir.name}'. Halting pipeline for safety.")
                    raise RuntimeError(f"🛑 [SprintExecutionEngine] Harness failed for '{epic_dir.name}' Sprint {s_num}. Pipeline safely halted.")

            epic_statuses[epic_dir.name] = f"✅ 【All Sprints Passed】全 {len(target_sprints)} スプリント完了!"

        print("🎉 [Ceremony 3 Complete] Autonomous TDD execution complete (All active epics & harnesses PASSED)!", flush=True)
        return True
