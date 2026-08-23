import yaml
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser


class HarnessGenerator:
    """Pure script generator: Creates bash verification harness scripts from sprint_x_backlog.yaml files."""

    @classmethod
    def generate_sprint_harness(cls, epic_dir: Path, sprint_num: int, sprint_backlog_path: Path):
        """Generates bash verification harness script for a single sprint backlog."""
        if not sprint_backlog_path.exists():
            return

        try:
            raw_yaml = sprint_backlog_path.read_text(encoding="utf-8")
            data = yaml.safe_load(raw_yaml) or {}
        except Exception as e:
            print(f"⚠️ [HarnessGenerator Warning] Failed to parse {sprint_backlog_path}: {e}")
            return

        tasks = data.get("tasks", [])
        test_cmd = data.get("test_command", "go test ./...")
        target_ws = data.get("target_workspace", "workspace/identicon-generator")

        task_verifications = []
        for t in tasks:
            t_id = t.get("id", "TASK")
            t_name = t.get("name", "Task")
            task_verifications.append(f"""
echo "🔍 Verifying Task {t_id}: {t_name}"
if ! {test_cmd}; then
    echo "❌ Task {t_id} Verification Failed!"
    exit 1
fi
echo "✅ Task {t_id} Passed!"
""")

        verifications_block = "\n".join(task_verifications)

        script_content = f"""#!/usr/bin/env bash
set -e

echo "=================================================="
echo "🚀 Sprint {sprint_num} Harness Verification: {epic_dir.name}"
echo "=================================================="

cd "{target_ws}" || exit 1

{verifications_block}

echo "=================================================="
echo "🎉 All Sprint {sprint_num} Harness Checks Passed!"
echo "=================================================="
"""
        harness_script_path = epic_dir / f"sprint_{sprint_num}_harness.sh"
        CodeParser.atomic_write_text(harness_script_path, script_content)
        harness_script_path.chmod(0o755)
        print(f"🛠️ [HarnessGenerator] Generated Harness: {harness_script_path.name} in {epic_dir.name}")

    @classmethod
    def generate_all_harnesses(cls, root_dir: Path, config: ProjectConfig):
        """Generates harness scripts for all sprint_x_backlog.yaml files across initiatives."""
        init_dir = root_dir / "state" / "initiatives"
        if not init_dir.exists():
            return

        for epic_dir in sorted(list(init_dir.glob("epic_*"))):
            if epic_dir.is_dir():
                for sprint_file in sorted(list(epic_dir.glob("sprint_*_backlog.yaml"))):
                    # Extract sprint number from filename sprint_1_backlog.yaml
                    m = sprint_file.name.split("_")
                    if len(m) >= 2 and m[1].isdigit():
                        s_num = int(m[1])
                        cls.generate_sprint_harness(epic_dir, s_num, sprint_file)
