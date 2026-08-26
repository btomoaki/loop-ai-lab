from pathlib import Path
import yaml
from runner.parser import atomic_write_text

def ensure_initiative_files_integrity(root_dir: Path):
    """Dynamic Harness Generator Engine for Go Code & Container/Deployment Epics."""
    init_dir = root_dir / "state/initiatives"
    if not init_dir.exists():
        return
        
    for epic_dir in sorted(list(init_dir.glob("epic_*"))):
        policy_path = epic_dir / "epic_policy.md"
        if not policy_path.exists():
            policy_content = f"# {epic_dir.name} Policy\n## Verification Rules\n- All code and containers must pass verification harness.\n"
            atomic_write_text(policy_path, policy_content)
            
        backlog_files = list(epic_dir.glob("sprint_*_backlog.yaml"))
        for b_file in backlog_files:
            if b_file.name == "sprint_backlog.yaml":
                continue
            
            sprint_suffix = b_file.name.replace("_backlog.yaml", "")
            harness_path = epic_dir / f"{sprint_suffix}_harness.sh"
            
            epic_name = epic_dir.name.lower()
            test_cmd = "go test ./..."
            epic_title = epic_dir.name
            
            # Determine appropriate default test_cmd based on Epic type
            if "container" in epic_name:
                test_cmd = "docker build -t avatar-service:latest ."
            elif "cloud_run" in epic_name or "deploy" in epic_name:
                test_cmd = "grep -q 'USER' Dockerfile && docker build -t avatar-service:cloudrun ."
            
            try:
                b_data = yaml.safe_load(b_file.read_text(encoding="utf-8")) or {}
                if "test_command" in b_data:
                    test_cmd = b_data["test_command"]
                epic_title = b_data.get("epic", epic_dir.name)
            except Exception:
                pass
            
            target_ws_rel = b_data.get("target_workspace", "workspace/identicon-generator")
            module_name = b_data.get("module_name", "identicon-generator")

            format_cmd = b_data.get("format_cmd", "gofmt -w . 2>/dev/null || true")

            # Build specialized harness script
            if "container" in epic_name or "cloud_run" in epic_name or "deploy" in epic_name or "docker" in test_cmd:
                harness_content = f"""#!/usr/bin/env bash
set -e
BASE_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")/../../.." && pwd)"
TARGET_DIR="${{BASE_DIR}}/{target_ws_rel}"

echo "🧪 [Step 1: Container/Deployment Harness - {sprint_suffix}] Verifying {epic_title}..."
if [ ! -d "${{TARGET_DIR}}" ]; then
    mkdir -p "${{TARGET_DIR}}"
fi

cd "${{TARGET_DIR}}"
if [ ! -f "Dockerfile" ]; then
    echo "❌ [Harness Failure] Dockerfile missing in workspace!"
    exit 2
fi

echo "🚀 Executing Container Harness Command: {test_cmd}"
{test_cmd} || exit 2
echo "[PASS] Container/Deployment Acceptance Criteria Passed!"
"""
            else:

                harness_content = f"""#!/usr/bin/env bash
set -e
BASE_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")/../../.." && pwd)"
TARGET_DIR="${{BASE_DIR}}/{target_ws_rel}"

echo "🔍 [Step 1: Code Integrity Check] Verifying package integrity in {target_ws_rel}..."
mkdir -p "${{TARGET_DIR}}"
cd "${{TARGET_DIR}}"

{format_cmd} 2>/dev/null || true

echo "🧪 [Step 2: Task Check - {sprint_suffix}_harness] Verifying {epic_title}..."
{test_cmd} || exit 2
echo "[PASS] Acceptance Criteria Passed!"
"""

            atomic_write_text(harness_path, harness_content)
            harness_path.chmod(0o755)
            print(f"🛠️ [Generic Harness Engine] Generated/Updated harness: {harness_path.name} (Command: {test_cmd})")


class TestHarnessGenerator:
    """Class wrapper for harness generation."""
    @staticmethod
    def generate_all(root_dir: Path, config=None):
        ensure_initiative_files_integrity(root_dir)
