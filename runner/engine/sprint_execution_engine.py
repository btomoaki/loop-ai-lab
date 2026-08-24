import os
import subprocess
import yaml
from datetime import datetime
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser
from runner.utils.context_loader import ContextLoader
from runner.adapters.llm_adapter import LLMAdapterFactory


class SprintExecutionEngine:
    """【セレモニー 3】スプリント開発 & DoD受入判定エンジン (ファイルパス参照 & status.md 自動更新)"""

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
        config_file = self.root_dir / "config.yaml"
        if config_file.exists():
            try:
                data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
                return data.get("DEFAULT_LLM_PROVIDER", "local")
            except Exception:
                pass
        return "local"

    def update_status_dashboard(self, active_epic: str, sprint_num: int, current_task: str, tdd_status: str, epic_statuses: dict):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        epic_rows = []
        for e_name, status in epic_statuses.items():
            epic_rows.append(f"- **{e_name}**: {status}")
        epic_summary_block = "\n".join(epic_rows)

        dashboard_content = f"""# �� Loop AI Lab - リアルタイム Scrum 進行状況ダッシュボード

- **現在実行中のフェーズ**: 🏃 【セレモニー 3】スプリント開発 & DoD受入判定
- **実行中エピック**: `{active_epic}` (Sprint {sprint_num})
- **処理中タスク**: `{current_task}`
- **TDD サイクル進行状態**: {tdd_status}
- **最終更新日時**: `{now_str}`

---

## 📊 全エピック進捗ステータス
{epic_summary_block}
"""
        CodeParser.atomic_write_text(self.status_file, dashboard_content)
        print(f"📊 [Status Dashboard] Updated state/status.md (Active: {active_epic} | Status: {tdd_status})", flush=True)

    def write_sprint_result_log(self, epic_dir: Path, sprint_num: int, backlog_data: dict, status: str, exit_code: int, written_files: list, error_log: str = None) -> Path:
        result_file = epic_dir / f"sprint_{sprint_num}_result.yaml"
        now_str = datetime.now().isoformat()
        
        rel_files = [str(f.relative_to(self.root_dir)) for f in written_files] if written_files else []
        
        result_data = {
            "sprint": sprint_num,
            "epic": backlog_data.get("epic", epic_dir.name),
            "timestamp": now_str,
            "status": status,
            "harness_exit_code": exit_code,
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

    def generate_code_for_backlog(self, epic_dir: Path, sprint_num: int, backlog_data: dict, result_file_ref: Path = None) -> list:
        tasks = backlog_data.get("tasks", [])
        scope = backlog_data.get("scope", "")
        epic_name = backlog_data.get("epic", epic_dir.name)
        target_ws = self.root_dir / backlog_data.get("target_workspace", "workspace/identicon-generator")
        target_ws.mkdir(parents=True, exist_ok=True)

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="3_sprint_execution", include_dev_rules=True)

        # 💡 エラーテキスト直接埋め込みではなく、result.yaml のファイルパス参照を指定！
        error_ref_block = (
            f"\n=== PREVIOUS TEST HARNESS FAILURE REFERENCE ===\n"
            f"File Path: {result_file_ref.relative_to(self.root_dir)}\n"
            f"Read the failure details and error logs from the physical file above to fix implementation issues."
        ) if result_file_ref and result_file_ref.exists() else ""

        prompt = (
            f"[TASK: CEREMONY 3 TDD CODE GENERATION - {epic_name} (Sprint {sprint_num})]\n"
            f"Target Workspace: {target_ws.relative_to(self.root_dir)}\n"
            f"Scope: {scope}\n\n"
            f"=== 1. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
            f"=== 2. BACKLOG TASKS ===\n{yaml.dump(tasks, default_flow_style=False, allow_unicode=True)}\n"
            f"{error_ref_block}\n\n"
            "【INSTRUCTION】\n"
            "Generate complete implementation and test code files in Go using `# FILE: <relative_path>` format.\n"
            "Example:\n"
            "# FILE: go.mod\n"
            "module github.com/yourusername/identicon-generator\n\n"
            "go 1.22\n\n"
            "# FILE: main.go\n"
            "package main\n\n"
            "import \"fmt\"\n\n"
            "func main() {\n"
            "    fmt.Println(\"Identicon Generator Started\")\n"
            "}\n\n"
            "Write un-truncated, production-ready Go code strictly following Clean Architecture 4-layer separation and Graceful Shutdown."
        )

        actual_prompt_file = self.eval_dir / "actual_dev_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)

        print(f"💻 [SprintExecutionEngine] Requesting LLM code generation for {epic_name}...", flush=True)
        llm_response = self.dev_agent.generate_text(prompt)

        if not llm_response or not llm_response.strip():
            print(f"⚠️ [SprintExecutionEngine Warning] LLM returned empty code response!")
            return []

        written_files = CodeParser.apply_code_changes(llm_response, target_ws)
        print(f"📝 [SprintExecutionEngine] Written {len(written_files)} files into {target_ws.relative_to(self.root_dir)}", flush=True)
        return written_files

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

        for attempt in range(1, max_retries + 1):
            tdd_status = f"🧪 TDD サイクル試行中 (Attempt {attempt}/{max_retries})"
            epic_statuses[epic_dir.name] = f"🏃 開発進行中 [{tdd_status}]"
            self.update_status_dashboard(epic_dir.name, sprint_num, current_task_name, tdd_status, epic_statuses)

            print(f"🔄 [TDD Cycle Attempt {attempt}/{max_retries}] Generating/Updating code...", flush=True)
            new_files = self.generate_code_for_backlog(epic_dir, sprint_num, backlog_data, result_file_ref)
            if new_files:
                last_written_files = new_files

            if harness_path.exists():
                print(f"🧪 [TDD Cycle] Running Test Harness: {harness_path.name}", flush=True)
                res = subprocess.run(["bash", str(harness_path)], cwd=str(self.root_dir), capture_output=True, text=True)
                
                if res.returncode == 0:
                    print(f"🎉 [TDD Cycle Passed!] Harness for {epic_dir.name} Sprint {sprint_num} PASSED with Exit Code 0!", flush=True)
                    epic_statuses[epic_dir.name] = f"✅ 【Pass】スプリント {sprint_num} ハーネス合格!"
                    self.update_status_dashboard(epic_dir.name, sprint_num, current_task_name, "✅ ハーネス合格", epic_statuses)
                    
                    self.write_sprint_result_log(epic_dir, sprint_num, backlog_data, "PASSED", 0, last_written_files)
                    return True
                else:
                    last_error = res.stdout + "\n" + res.stderr
                    print(f"⚠️ [TDD Cycle Failed] Attempt {attempt} returned exit code {res.returncode}. Logged to result.yaml.", flush=True)
                    result_file_ref = self.write_sprint_result_log(epic_dir, sprint_num, backlog_data, "FAILED", res.returncode, last_written_files, last_error)

        epic_statuses[epic_dir.name] = f"❌ 【Fail】リトライ上限到達 ({max_retries} 回)"
        self.update_status_dashboard(epic_dir.name, sprint_num, current_task_name, "🛑 開発失敗・安全停止", epic_statuses)
        return False

    def run_sprint_development(self, sprint_num: int = 1) -> bool:
        print(f"🚀 [Ceremony 3: Sprint Execution] Starting Autonomous TDD Development for Sprint {sprint_num}...", flush=True)
        
        epic_dirs = sorted([d for d in self.init_dir.glob("epic_*") if d.is_dir()])
        if not epic_dirs:
            print("⚠️ [SprintExecutionEngine] No active epic initiatives found in state/initiatives/!")
            return False

        epic_statuses = {d.name: "⏳ 待機中" for d in epic_dirs}
        
        for epic_dir in epic_dirs:
            success = self.run_sprint_task(epic_dir, sprint_num, epic_statuses)
            if not success:
                print(f"🛑 [Fail-Fast Safety Halt] Sprint {sprint_num} failed for '{epic_dir.name}'. Halting pipeline for safety.")
                raise RuntimeError(f"🛑 [SprintExecutionEngine] Harness failed for '{epic_dir.name}'. Pipeline safely halted.")

        print(f"🎉 [Ceremony 3 Complete] Sprint {sprint_num} TDD execution complete (All active harnesses PASSED)!", flush=True)
        return True
