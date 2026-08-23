import os
import subprocess
import yaml
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser


class SprintEngine:
    """Handles execution of sprint tasks by matching target backlogs and harness scripts dynamically."""

    def __init__(self, root_dir: Path, config: ProjectConfig = None):
        self.root_dir = root_dir
        self.config = config or ProjectConfig.load(root_dir)
        self.init_dir = root_dir / "state" / "initiatives"

    def get_active_epic_harness(self, epic_dir: Path, sprint_num: int = 1) -> Path:
        """Dynamically retrieves the harness script for a given epic directory."""
        return epic_dir / f"sprint_{sprint_num}_harness.sh"

    def run_sprint_task(self, epic_dir: Path, sprint_num: int = 1) -> bool:
        backlog_path = epic_dir / f"sprint_{sprint_num}_backlog.yaml"
        harness_path = self.get_active_epic_harness(epic_dir, sprint_num)

        if not backlog_path.exists():
            return False

        print(f"🏃 [SprintEngine] Executing Sprint {sprint_num} for: {epic_dir.name}", flush=True)

        if harness_path.exists():
            print(f"🧪 [SprintEngine] Running Harness Test Script: {harness_path.relative_to(self.root_dir)}", flush=True)
            try:
                res = subprocess.run(["bash", str(harness_path)], cwd=str(self.root_dir), capture_output=True, text=True)
                if res.returncode == 0:
                    print(f"✅ [SprintEngine] Harness passed for {epic_dir.name} Sprint {sprint_num}!", flush=True)
                else:
                    print(f"⚠️ [SprintEngine] Harness output/status for {epic_dir.name}: Return code {res.returncode}", flush=True)
            except Exception as e:
                print(f"⚠️ [SprintEngine] Harness execution failed: {e}", flush=True)

        return True

    def run_sprint_development(self, sprint_num: int = 1) -> bool:
        print(f"🚀 [SprintEngine] Starting Autonomous Development Phase for Sprint {sprint_num}...", flush=True)
        
        epic_dirs = sorted([d for d in self.init_dir.glob("epic_*") if d.is_dir()])
        if not epic_dirs:
            print("⚠️ [SprintEngine] No active epic initiatives found in state/initiatives/!")
            return False

        executed_count = 0
        for epic_dir in epic_dirs:
            if self.run_sprint_task(epic_dir, sprint_num):
                executed_count += 1

        print(f"🎉 [SprintEngine] Sprint {sprint_num} development execution complete ({executed_count} active epics processed)!", flush=True)
        return True
