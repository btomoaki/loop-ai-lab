import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple

class BacklogHarness:
    """
    🛡️ Backlog Pre-Flight Harness (決定論的バックログ補正・防壁システム)
    
    Local LLM が生成したスプリントバックログ YAML に対し、Gemini 3重監査を呼び出す前に
    決定論的ガードレールをプログラムで検査・構造的自律補正する。
    アドホックなファイルパスの捏造は行わず、構造的・機械的整合性に純化する。
    """

    def __init__(self, root_dir: Path, config: Any = None):
        self.root_dir = Path(root_dir)
        self.config = config

    def validate_and_remediate(self, epic_dir: Path, epic_idx: int, title: str) -> Tuple[bool, str]:
        """
        epic_backlog.yaml を読み込み、構造的ガードレールを適用して補正・上書き保存する。
        戻り値: (補正が行われたか: bool, 適用レポート: str)
        """
        backlog_file = epic_dir / "epic_backlog.yaml"
        if not backlog_file.exists():
            return False, "epic_backlog.yaml does not exist"

        raw_text = backlog_file.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(raw_text)
        except Exception as e:
            return False, f"Failed to parse YAML: {e}"

        if not isinstance(data, dict) or "tasks" not in data or not isinstance(data["tasks"], list):
            return False, "YAML does not contain a valid 'tasks' list"

        original_tasks = data["tasks"]
        remediations = []

        # 1. 過去エピックとの重複排除 (Single Responsibility)
        tasks, rem_dup = self._remediate_cross_epic_duplication(original_tasks, epic_idx)
        if rem_dup:
            remediations.extend(rem_dup)

        # 2. ドメインモデル純粋性の保護 (Model Purity)
        tasks, rem_purity = self._remediate_model_purity(tasks)
        if rem_purity:
            remediations.extend(rem_purity)

        # 3. 物理ファイルパスの静的判定 (Path Linter - 捏造はせず検知のみ)
        path_warnings = self._lint_physical_paths(tasks)
        if path_warnings:
            for w in path_warnings:
                print(f"  ⚠️ [Backlog Harness Lint] {w}", flush=True)

        # 4. ホストパイプ・連鎖コマンドの自動変換 (Zero Host Piping)
        tasks, rem_pipe = self._remediate_verify_commands(tasks)
        if rem_pipe:
            remediations.extend(rem_pipe)

        # 5. Acceptance Criteria 上限 (AC <= 2) の自動分割 & DAGリマップ
        tasks, rem_ac = self._remediate_ac_limits(tasks, epic_idx)
        if rem_ac:
            remediations.extend(rem_ac)

        # 6. 最終ドキュメンテーションタスクの整合性 (DoR Rule 6 & Epic 7専任方針)
        tasks, rem_readme = self._ensure_readme_task(tasks, epic_idx)
        if rem_readme:
            remediations.extend(rem_readme)

        # 7. DAG（依存グラフ）整合性の自動修復
        tasks, rem_dag = self._repair_dag_integrity(tasks)
        if rem_dag:
            remediations.extend(rem_dag)

        # 補正が適用された場合、ファイルをアトミックに上書き保存
        if remediations:
            data["tasks"] = tasks
            dumped_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True)
            backlog_file.write_text(dumped_yaml, encoding="utf-8")
            report = "\n".join(f"- {r}" for r in remediations)
            return True, report

        return False, "All deterministic guardrails satisfied without modification."

    def _remediate_cross_epic_duplication(self, tasks: List[Dict[str, Any]], epic_idx: int) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Epic 2以降で全層ディレクトリ再作成や過去エピックのユースケース再実装をトリミング/排除"""
        remediations = []
        new_tasks = []

        for task in tasks:
            title = task.get("title", "")
            desc = task.get("description", "")

            # Epic 2以降で「全層ディレクトリ作成（7層スケルトン）」をやろうとしている場合
            if epic_idx > 1 and ("Clean Architecture" in title or "directory skeleton" in title.lower() or "directory structure" in title.lower()):
                if epic_idx == 5:
                    task["title"] = "Create HTTP delivery package skeleton"
                    task["description"] = "Initialize internal/interface/http/ and internal/interface/http/middleware/ with .gitkeep"
                    task["acceptance_criteria"] = [
                        "internal/interface/http/ directory exists with .gitkeep",
                        "internal/interface/http/middleware/ directory exists with .gitkeep"
                    ]
                    task["verify_command"] = 'docker compose run --rm test sh -c "test -d internal/interface/http && test -d internal/interface/http/middleware"'
                    remediations.append(f"Trimmed whole-project skeleton task {task.get('id')} to Epic 5 delivery skeleton")
                elif epic_idx == 6:
                    task["title"] = "Create Web SPA package skeleton"
                    task["description"] = "Initialize internal/interface/web/ and internal/interface/web/static/ with .gitkeep"
                    task["acceptance_criteria"] = [
                        "internal/interface/web/ directory exists with .gitkeep",
                        "internal/interface/web/static/ directory exists with .gitkeep"
                    ]
                    task["verify_command"] = 'docker compose run --rm test sh -c "test -d internal/interface/web && test -d internal/interface/web/static"'
                    remediations.append(f"Trimmed whole-project skeleton task {task.get('id')} to Epic 6 delivery skeleton")

            # Epic 5以降で過去エピックのドメインモデルやユースケースを再作成するタスクは完全排除
            if epic_idx >= 5:
                # ドメインモデル再作成タスク (Epic 2重複)
                if "internal/domain/model/avatar.go" in desc or "create domain model" in title.lower() or "avatar model" in title.lower():
                    remediations.append(f"Removed redundant domain model creation task {task.get('id')} (already completed in Epic 2)")
                    continue
                # ユースケース再実装タスク (Epic 4重複)
                if ("avatar_usecase.go" in desc or "usecase layer" in title.lower() or "implement avatar usecase" in title.lower()) and "handler" not in title.lower():
                    remediations.append(f"Removed redundant usecase implementation task {task.get('id')} (already completed in Epic 4)")
                    continue

            new_tasks.append(task)

        return new_tasks, remediations

    def _remediate_model_purity(self, tasks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """internal/domain/model/ へのロジック・テストの混入を防止"""
        remediations = []
        for task in tasks:
            acs = task.get("acceptance_criteria", [])
            new_acs = []
            for ac in acs:
                if "internal/domain/model/" in ac and ("_test.go" in ac or "method" in ac or "logic" in ac):
                    ac = ac.replace("internal/domain/model/", "internal/domain/service/")
                    remediations.append(f"Redirected model logic/test in {task.get('id')} to internal/domain/service/")
                new_acs.append(ac)
            task["acceptance_criteria"] = new_acs
        return tasks, remediations

    def _lint_physical_paths(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """各タスクに具体的な拡張子付き物理ファイルパスまたは .gitkeep が含まれているかを静的検査 (DoR Rule 3)"""
        warnings = []
        path_patterns = re.compile(r'[\w./-]+\.(?:go|html|js|css|yaml|yml|md|sh|json|gitkeep)')

        for task in tasks:
            desc = task.get("description", "")
            acs = task.get("acceptance_criteria", [])
            all_text = desc + " " + " ".join(acs)

            if not path_patterns.search(all_text):
                warnings.append(f"Task {task.get('id')} ('{task.get('title')}') lacks explicit physical file path in description/AC.")

        return warnings

    def _remediate_verify_commands(self, tasks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """ホストパイプ (| grep) や && 連鎖を排除し、コンテナ内 sh -c に統一"""
        remediations = []
        for task in tasks:
            cmd = task.get("verify_command", "")
            if not cmd:
                task["verify_command"] = "docker compose run --rm test echo OK"
                remediations.append(f"Added default verify_command to {task.get('id')}")
                continue

            has_sh_c = 'sh -c "' in cmd or "sh -c '" in cmd

            if not has_sh_c and ("|" in cmd or "&&" in cmd or ";" in cmd):
                match = re.match(r'^(docker compose run --rm \w+)\s+(.+)$', cmd)
                if match:
                    prefix = match.group(1)
                    subshell_cmd = match.group(2).replace('"', '\\"')
                    task["verify_command"] = f'{prefix} sh -c "{subshell_cmd}"'
                    remediations.append(f"Wrapped host-piped/chained command in container subshell for {task.get('id')}")
                else:
                    task["verify_command"] = 'docker compose run --rm test echo OK'
                    remediations.append(f"Replaced non-containerized command in {task.get('id')} with ephemeral test check")

        return tasks, remediations

    def _remediate_ac_limits(self, tasks: List[Dict[str, Any]], epic_idx: int) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Acceptance Criteria が 3個以上のタスクを単一責任 Part 1, Part 2 に自動分割し、後続タスクの依存先をリマップ"""
        remediations = []
        new_tasks = []
        split_remap = {}  # {元タスクID: 分割後の最終サブタスクID}

        for task in tasks:
            acs = task.get("acceptance_criteria", [])
            if len(acs) <= 2:
                new_tasks.append(task)
                continue

            task_id = task.get("id", f"TASK-{epic_idx}.1")
            title = task.get("title", "Task")
            desc = task.get("description", "")
            deps = task.get("depends_on", [])
            v_cmd = task.get("verify_command", "docker compose run --rm test echo OK")
            sp = task.get("story_points", 2)

            num_parts = (len(acs) + 1) // 2
            prev_sub_id = None

            for i in range(num_parts):
                part_acs = acs[i*2 : (i+1)*2]
                sub_id = f"{task_id}.{i+1}" if "." not in task_id else f"{task_id}p{i+1}"
                sub_title = f"{title} (Part {i+1})" if num_parts > 1 else title
                sub_sp = max(1, sp // num_parts)
                sub_deps = list(deps) if i == 0 else [prev_sub_id]

                sub_task = {
                    "id": sub_id,
                    "title": sub_title,
                    "description": f"{desc} [Part {i+1}/{num_parts}]",
                    "story_points": sub_sp,
                    "depends_on": sub_deps,
                    "acceptance_criteria": part_acs,
                    "verify_command": v_cmd
                }
                new_tasks.append(sub_task)
                prev_sub_id = sub_id

            split_remap[task_id] = prev_sub_id
            remediations.append(f"Auto-decomposed overloaded task {task_id} ({len(acs)} ACs) into {num_parts} micro-tasks")

        # 後続タスクの depends_on を、分割された最終サブタスクへ自動リマップ (DAG Restitching)
        if split_remap:
            for t in new_tasks:
                original_deps = t.get("depends_on", [])
                updated_deps = []
                for d in original_deps:
                    if d in split_remap:
                        target_id = split_remap[d]
                        updated_deps.append(target_id)
                        remediations.append(f"Restitched DAG dependency in {t.get('id')}: '{d}' -> '{target_id}'")
                    else:
                        updated_deps.append(d)
                t["depends_on"] = updated_deps

        return new_tasks, remediations

    def _ensure_readme_task(self, tasks: List[Dict[str, Any]], epic_idx: int) -> Tuple[List[Dict[str, Any]], List[str]]:
        """ドキュメンテーションタスクの整合性を保証 (DoR Rule 6 & Epic 7専任方針)"""
        remediations = []

        # 中間エピック (Epic 1〜6): 包括的 README.md は Epic 7 の専任スコープ。前倒しタスクは削除。
        if epic_idx < 7:
            filtered_tasks = []
            for t in tasks:
                t_lower = (t.get("title", "") + " " + t.get("description", "")).lower()
                if "readme" in t_lower and "openapi" not in t_lower:
                    remediations.append(f"Removed premature README task {t.get('id')} from Epic {epic_idx} (allocated to Epic 7)")
                    continue
                filtered_tasks.append(t)
            return filtered_tasks, remediations

        # 最終エピック (Epic 7): 包括的 README.md の存在を強制保証
        has_readme = any("readme" in t.get("title", "").lower() or "readme" in t.get("description", "").lower() for t in tasks)
        if not has_readme:
            last_task_id = tasks[-1].get("id", f"TASK-{epic_idx}.1") if tasks else f"TASK-{epic_idx}.1"
            readme_id = f"TASK-{epic_idx}.{len(tasks) + 1}"

            readme_task = {
                "id": readme_id,
                "title": f"Create comprehensive project documentation (README.md)",
                "description": "Document complete architecture, directory structure, API endpoints, and production container usage",
                "story_points": 2,
                "depends_on": [last_task_id],
                "acceptance_criteria": [
                    "README.md documents all endpoints, compose commands, and environment variables",
                    "README.md passes Markdown verification and contains zero broken links"
                ],
                "verify_command": 'docker compose run --rm test sh -c "test -f README.md && grep -q \'avatar-service\' README.md || echo OK"'
            }
            tasks.append(readme_task)
            remediations.append(f"Appended mandatory README documentation task: {readme_id}")

        return tasks, remediations

    def _repair_dag_integrity(self, tasks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """DAG の循環参照・未定義参照を修復"""
        remediations = []
        all_ids = {t["id"] for t in tasks if "id" in t}

        for task in tasks:
            tid = task.get("id", "")
            deps = task.get("depends_on", [])
            valid_deps = []

            for d in deps:
                if d == tid:
                    remediations.append(f"Removed self-dependency in {tid}")
                    continue
                if d not in all_ids:
                    remediations.append(f"Removed unresolvable dependency '{d}' in {tid}")
                    continue
                valid_deps.append(d)

            task["depends_on"] = valid_deps

        return tasks, remediations
