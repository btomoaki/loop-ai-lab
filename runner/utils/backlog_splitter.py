import yaml
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser


class BacklogSplitter:
    """Strict 1-task per 1-sprint step-by-step backlog splitter preserving epic scope."""

    TASKS_PER_SPRINT = 1  # Exactly 1 task per sprint for step-by-step verification

    @classmethod
    def split_epic_backlog(cls, epic_dir: Path, config: ProjectConfig):
        """Splits epic_backlog.yaml tasks strictly into individual sprint_1_backlog.yaml, sprint_2_backlog.yaml, etc. preserving scope."""
        epic_backlog_path = epic_dir / "epic_backlog.yaml"
        if not epic_backlog_path.exists():
            return

        try:
            raw_yaml = epic_backlog_path.read_text(encoding="utf-8")
            data = yaml.safe_load(raw_yaml) or {}
        except Exception as e:
            print(f"⚠️ [BacklogSplitter Warning] Failed to parse {epic_backlog_path}: {e}")
            return

        tasks = data.get("tasks", [])
        if not tasks:
            return

        epic_title = data.get("epic", epic_dir.name.replace("_", " ").title())
        epic_scope = data.get("scope", "Epic implementation scope")
        target_ws = data.get("target_workspace", config.workspace_rel or "workspace/identicon-generator")
        test_cmd = data.get("test_command", config.default_test_cmd or "go test ./...")

        # 1 Task = 1 Sprint (Step-by-step execution with scope)
        for s_idx, single_task in enumerate(tasks, 1):
            sprint_data = {
                "sprint": s_idx,
                "epic": epic_title,
                "scope": epic_scope,
                "target_workspace": target_ws,
                "test_command": test_cmd,
                "tasks": [single_task]  # Single task per sprint
            }

            sprint_backlog_file = epic_dir / f"sprint_{s_idx}_backlog.yaml"
            CodeParser.atomic_write_text(sprint_backlog_file, yaml.dump(sprint_data, sort_keys=False, allow_unicode=True))
            print(f"📦 [BacklogSplitter] Created step-by-step Sprint {s_idx} ({single_task.get('id')}) with scope in {epic_dir.name}")

    @classmethod
    def process_all_epics(cls, root_dir: Path, config: ProjectConfig):
        """Processes all initiative directories into step-by-step 1-task sprints."""
        init_dir = root_dir / "state" / "initiatives"
        if not init_dir.exists():
            return

        for epic_dir in sorted(list(init_dir.glob("epic_*"))):
            if epic_dir.is_dir():
                cls.split_epic_backlog(epic_dir, config)
