import os
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

    def run_sprint_task(self, epic_dir_name: str, sprint_num: int = 1) -> bool:
        epic_dir = self.init_dir / epic_dir_name
        backlog_path = epic_dir / f"sprint_{sprint_num}_backlog.yaml"
        harness_path = self.get_active_epic_harness(epic_dir, sprint_num)

        if not backlog_path.exists():
            print(f"⚠️ [SprintEngine] Backlog missing for {epic_dir_name}: {backlog_path}")
            return False

        print(f"🏃 [SprintEngine] Processing active sprint for: {epic_dir_name}")
        return True
