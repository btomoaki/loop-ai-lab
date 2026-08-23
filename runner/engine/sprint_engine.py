import subprocess
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser
from runner.generators.harness_generator import HarnessGenerator
from runner.adapters.llm_adapter import LLMAdapterFactory


class SprintEngine:
    """Handles Sprint Development loop: code generation, harness verification, and auto-fix loop."""

    def __init__(self, root_dir: Path, config: ProjectConfig = None):
        self.root_dir = root_dir
        self.config = config or ProjectConfig.load(root_dir)
        self.dev_agent = LLMAdapterFactory.get_adapter()

    def load_active_yaml_backlog(self, sprint_num: int) -> str:
        initiatives_dir = self.root_dir / "state" / "initiatives"
        found = sorted(list(initiatives_dir.glob(f"**/sprint_{sprint_num}_backlog.yaml")))
        if found:
            return found[0].read_text(encoding="utf-8")
        return f"sprint: {sprint_num}\ntask:\n  id: TASK-{sprint_num}\n  name: Sprint Task\n"

    def find_sprint_harness(self, sprint_num: int) -> Path:
        initiatives_dir = self.root_dir / "state" / "initiatives"
        found = sorted(list(initiatives_dir.glob(f"**/sprint_{sprint_num}_harness.sh")))
        if found:
            return found[0]
        return initiatives_dir / "epic_1_domain_core" / f"sprint_{sprint_num}_harness.sh"

    def _resolve_workspace(self) -> Path:
        """config.workspace_rel からワークスペースパスを解決する。"""
        if self.config.workspace_rel:
            return self.root_dir / self.config.workspace_rel
        return self.root_dir / "workspace"

    def _init_workspace(self, target_workspace: Path):
        """プロジェクトファイルが無い場合、初期化コマンドを実行する。"""
        target_workspace.mkdir(parents=True, exist_ok=True)

        if self.config.project_file and not (target_workspace / self.config.project_file).exists():
            for cmd in self.config.init_commands:
                print(f"🛠️ [SprintEngine] Initializing workspace: {cmd}", flush=True)
                subprocess.run(cmd.split(), cwd=target_workspace, capture_output=True)

    def _build_init_prompt(self, b_spec: str) -> str:
        """初回コード生成プロンプトを config から動的構築する。"""
        lang = self.config.language or "the target language"
        ext = self.config.file_extension or ""
        ws = self.config.workspace_rel or "workspace/"

        prompt = (
            "[SYSTEM INSTRUCTION: INITIAL CODE GENERATION]\n"
            f"Read the backlog specification below and implement the task cleanly in {lang}.\n\n"
            f"CRITICAL OUTPUT FORMAT: You MUST wrap your code using exact # FILE: {ws}/... header blocks!\n"
            "Example:\n"
        )

        if self.config.language == "go":
            prompt += (
                f"# FILE: internal/domain/model/<struct_name>{ext}\n"
                "```go\n"
                "package model\n\n"
                "type <StructName> struct {}\n"
                "```\n\n"
            )
        else:
            prompt += (
                f"# FILE: src/example{ext}\n"
                f"```{lang}\n"
                "// Implementation here\n"
                "```\n\n"
            )

        prompt += "BACKLOG SPECIFICATION:\n" + b_spec
        return prompt

    def _build_fix_prompt(self, attempt: int, returncode: int, stdout: str, stderr: str) -> str:
        """修正プロンプトを config から動的構築する。"""
        ws = self.config.workspace_rel or "workspace/"
        return (
            f"[SYSTEM INSTRUCTION: SPRINT CODE FIX - ATTEMPT {attempt}]\n"
            f"The test harness failed with exit code {returncode}. Fix the code below:\n\n"
            f"ERROR LOG:\n{stdout}\n{stderr}\n\n"
            f"Provide updated code using exact # FILE: {ws}/... header blocks."
        )

    def run_sprint_development(self, sprint_num: int = 1, max_loops: int = 5) -> bool:
        HarnessGenerator.ensure_initiative_files_integrity(self.root_dir, self.config)
        harness_path = self.find_sprint_harness(sprint_num)

        target_workspace = self._resolve_workspace()
        self._init_workspace(target_workspace)

        print(f"\n==================================================")
        print(f" 🚀 [SprintEngine] Executing Sprint {sprint_num} Development Loop")
        print(f"==================================================")

        attempt = 0
        b_spec = self.load_active_yaml_backlog(sprint_num)
        init_prompt = self._build_init_prompt(b_spec)

        try:
            raw_code = self.dev_agent.generate_text(init_prompt)
            CodeParser.apply_code_changes(raw_code, target_workspace, self.config)
        except Exception as e:
            print(f"⚠️ [SprintEngine Initial Gen Warning]: {e}", flush=True)

        while True:
            attempt += 1
            print(f"\n⚙️ [Sprint {sprint_num} Attempt {attempt}] Running Test Harness: {harness_path.relative_to(self.root_dir)}...", flush=True)

            res = subprocess.run(["bash", str(harness_path)], cwd=self.root_dir, capture_output=True, text=True)
            issues_log_path = self.root_dir / "state" / ".evaluator" / "current_issues.md"

            if res.returncode == 0:
                CodeParser.atomic_write_text(issues_log_path, f"# Current Issues Log\n\n- Loop #{attempt} Status: PASS (100% GREEN)\n- Harness Exit Code: 0\n")
                print(f"🎉 [Sprint {sprint_num} Success] Test Harness PASSED 100% GREEN in attempt {attempt}!", flush=True)
                return True

            CodeParser.atomic_write_text(issues_log_path, f"# Current Issues Log\n\n- Loop #{attempt} Status: FAIL (Exit Code {res.returncode})\n\n## Terminal Error Log\n```text\n{res.stdout}\n{res.stderr}\n```\n")
            print(f"⚠️ [Harness Failure #{attempt}/{max_loops}]: Harness returned exit code {res.returncode}.", flush=True)

            if attempt >= max_loops:
                print(f"❌ [Sprint {sprint_num} Failed]: Reached max failed harness limit ({max_loops}). Stopping sprint.", flush=True)
                return False

            dev_prompt = self._build_fix_prompt(attempt, res.returncode, res.stdout, res.stderr)
            print(f"🚀 [SprintEngine] Attempt {attempt}: Requesting code fixes from Local LLM...", flush=True)
            raw_code = self.dev_agent.generate_text(dev_prompt)
            CodeParser.apply_code_changes(raw_code, target_workspace, self.config)
