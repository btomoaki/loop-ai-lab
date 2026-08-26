import os
import re
import yaml
from pathlib import Path
from runner.utils.code_parser import CodeParser


class BacklogSplitter:
    """Utility to split monolithic epic_backlog.yaml into sprint_1_backlog.yaml, sprint_2_backlog.yaml, etc."""

    @staticmethod
    def split_epic_backlog(epic_dir: Path, config=None):
        epic_backlog_file = epic_dir / "epic_backlog.yaml"
        if not epic_backlog_file.exists():
            return []

        try:
            raw_text = epic_backlog_file.read_text(encoding="utf-8")
            data = yaml.safe_load(raw_text) or {}
        except Exception as e:
            print(f"⚠️ [BacklogSplitter] Failed to parse {epic_backlog_file}: {e}")
            return []

        tasks = data.get("tasks", [])
        if not tasks:
            print(f"⚠️ [BacklogSplitter] No tasks found in {epic_backlog_file}")
            return []

        epic_title = data.get("epic", epic_dir.name)
        scope = data.get("scope", "")
        
        ws_fallback = "workspace/app"
        if config and hasattr(config, "workspace_rel") and config.workspace_rel:
            ws_fallback = config.workspace_rel
        target_ws = data.get("target_workspace", ws_fallback)

        created_files = []
        for idx, task in enumerate(tasks, 1):
            sprint_file = epic_dir / f"sprint_{idx}_backlog.yaml"
            
            sprint_data = {
                "sprint": idx,
                "epic": epic_title,
                "scope": scope,
                "target_workspace": target_ws,
                "tasks": [task]
            }

            yaml_str = yaml.dump(sprint_data, default_flow_style=False, allow_unicode=True)
            CodeParser.atomic_write_text(sprint_file, yaml_str)
            created_files.append(sprint_file)
            print(f"📦 [BacklogSplitter] Created step-by-step Sprint {idx} ({task.get('id', 'TASK')}) with scope in {epic_dir.name}")

        return created_files

    @staticmethod
    def split_all_epics(root_dir: Path, config=None):
        init_dir = root_dir / "state" / "initiatives"
        if not init_dir.exists():
            return {}

        results = {}
        for epic_dir in sorted(init_dir.glob("epic_*")):
            if epic_dir.is_dir():
                sprint_files = BacklogSplitter.split_epic_backlog(epic_dir, config)
                results[epic_dir.name] = sprint_files
        return results
