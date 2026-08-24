import os
import subprocess
import yaml
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser
from runner.utils.context_loader import ContextLoader
from runner.adapters.llm_adapter import LLMAdapterFactory


class SprintExecutionEngine:
    """【セレモニー 3】スプリント開発 & DoD受入判定エンジン（自律TDD実装ループ機能付き）"""

    def __init__(self, root_dir: Path, config: ProjectConfig = None):
        self.root_dir = root_dir
        self.config = config or ProjectConfig.load(root_dir)
        self.init_dir = root_dir / "state" / "initiatives"
        self.eval_dir = root_dir / "state" / ".evaluator"
        
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

    def get_active_epic_harness(self, epic_dir: Path, sprint_num: int = 1) -> Path:
        return epic_dir / f"sprint_{sprint_num}_harness.sh"

    def generate_code_for_backlog(self, epic_dir: Path, sprint_num: int, backlog_data: dict, last_error: str = None) -> bool:
        """LLM 開発エージェントを呼び出し、バックログタスクの実装コードを workspace/ 下へ自動書き出し"""
        tasks = backlog_data.get("tasks", [])
        scope = backlog_data.get("scope", "")
        epic_name = backlog_data.get("epic", epic_dir.name)
        target_ws = self.root_dir / backlog_data.get("target_workspace", "workspace/identicon-generator")
        target_ws.mkdir(parents=True, exist_ok=True)

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="3_sprint_execution", include_dev_rules=True)

        error_feedback = f"\n=== PREVIOUS TEST HARNESS FAILURE FEEDBACK ===\n{last_error}\nFix the implementation to resolve this error." if last_error else ""

        prompt = (
            f"[TASK: CEREMONY 3 TDD CODE GENERATION - {epic_name} (Sprint {sprint_num})]\n"
            f"Target Workspace: {target_ws.relative_to(self.root_dir)}\n"
            f"Scope: {scope}\n\n"
            f"=== 1. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
            f"=== 2. BACKLOG TASKS ===\n{yaml.dump(tasks, default_flow_style=False, allow_unicode=True)}\n"
            f"{error_feedback}\n\n"
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
            return False

        # 出力レスポンスから # FILE: ブロックを抽出して保存
        written_files = CodeParser.parse_and_write_files(llm_response, target_ws)
        print(f"📝 [SprintExecutionEngine] Written {len(written_files)} files into {target_ws.relative_to(self.root_dir)}", flush=True)
        return len(written_files) > 0

    def run_sprint_task(self, epic_dir: Path, sprint_num: int = 1, max_retries: int = 2) -> bool:
        backlog_path = epic_dir / f"sprint_{sprint_num}_backlog.yaml"
        harness_path = self.get_active_epic_harness(epic_dir, sprint_num)

        if not backlog_path.exists():
            return False

        try:
            raw_yaml = backlog_path.read_text(encoding="utf-8")
            backlog_data = yaml.safe_load(raw_yaml) or {}
        except Exception:
            return False

        print(f"\n🏃 [SprintExecutionEngine] Processing Sprint {sprint_num} for: {epic_dir.name}", flush=True)

        last_error = None
        for attempt in range(1, max_retries + 2):
            print(f"🔄 [TDD Cycle Attempt {attempt}/{max_retries + 1}] Generating/Updating code...", flush=True)
            self.generate_code_for_backlog(epic_dir, sprint_num, backlog_data, last_error)

            if harness_path.exists():
                print(f"🧪 [TDD Cycle] Running Test Harness: {harness_path.name}", flush=True)
                res = subprocess.run(["bash", str(harness_path)], cwd=str(self.root_dir), capture_output=True, text=True)
                
                if res.returncode == 0:
                    print(f"🎉 [TDD Cycle Passed!] Harness for {epic_dir.name} Sprint {sprint_num} PASSED with Exit Code 0!", flush=True)
                    return True
                else:
                    last_error = res.stdout + "\n" + res.stderr
                    print(f"⚠️ [TDD Cycle Failed] Attempt {attempt} returned exit code {res.returncode}. Feedback recorded.", flush=True)

        return False

    def run_sprint_development(self, sprint_num: int = 1) -> bool:
        print(f"🚀 [Ceremony 3: Sprint Execution] Starting Autonomous TDD Development for Sprint {sprint_num}...", flush=True)
        
        epic_dirs = sorted([d for d in self.init_dir.glob("epic_*") if d.is_dir()])
        if not epic_dirs:
            print("⚠️ [SprintExecutionEngine] No active epic initiatives found in state/initiatives/!")
            return False

        executed_count = 0
        passed_count = 0
        for epic_dir in epic_dirs:
            executed_count += 1
            if self.run_sprint_task(epic_dir, sprint_num):
                passed_count += 1

        print(f"🎉 [Ceremony 3 Complete] Sprint {sprint_num} TDD execution complete ({passed_count}/{executed_count} harnesses PASSED)!", flush=True)
        return passed_count > 0
