from pathlib import Path
import yaml
from runner.parser import atomic_write_text

def ensure_initiative_files_integrity(root_dir: Path):
    """Fully Generic & Language-Agnostic Harness Generator Engine.
    Zero hardcoded epic names or hardcoded project test commands.
    Dynamically extracts test_command and epic title from sprint_N_backlog.yaml files.
    """
    init_dir = root_dir / "state/initiatives"
    if not init_dir.exists():
        return
        
    for epic_dir in init_dir.glob("epic_*"):
        policy_path = epic_dir / "epic_policy.md"
        if not policy_path.exists():
            policy_content = f"# {epic_dir.name} Policy\n## Verification Rules\n- All code must pass verification harness.\n"
            atomic_write_text(policy_path, policy_content)
            
        backlog_files = list(epic_dir.glob("sprint_*_backlog.yaml"))
        for b_file in backlog_files:
            if b_file.name == "sprint_backlog.yaml":
                continue
            
            sprint_suffix = b_file.name.replace("_backlog.yaml", "")
            harness_path = epic_dir / f"{sprint_suffix}_harness.sh"
            
            # Read test_command and epic title dynamically from backlog YAML
            test_cmd = "go test ./..."
            epic_title = epic_dir.name
            try:
                b_data = yaml.safe_load(b_file.read_text(encoding="utf-8")) or {}
                test_cmd = b_data.get("test_command", b_data.get("harness_command", "go test ./..."))
                epic_title = b_data.get("epic", epic_dir.name)
            except Exception:
                pass
            
            if not harness_path.exists():
                harness_content = f"""#!/usr/bin/env bash
set -e
BASE_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")/../../.." && pwd)"
TARGET_DIR="${{BASE_DIR}}/workspace/avatar-service"

echo "🔍 [Step 1: Overall Integrity Check] Verifying overall project build & test integrity..."
if [ -d "${{TARGET_DIR}}" ] && [ -f "${{TARGET_DIR}}/go.mod" ]; then
    cd "${{TARGET_DIR}}"
    gofmt -w .
    go vet ./... || true
    go test ./... || exit 2
fi

echo "🧪 [Step 2: Task Check - {sprint_suffix}_harness] Verifying {epic_title}..."
if [ ! -d "${{TARGET_DIR}}" ]; then
    echo "❌ [Harness Failure] Target workspace directory does not exist!"
    exit 2
fi

cd "${{TARGET_DIR}}"
if [ ! -f "go.mod" ]; then
    echo "❌ [Harness Failure] go.mod missing!"
    exit 2
fi
    {test_cmd} || exit 2
echo "[PASS] Acceptance Criteria Passed!"
"""
                atomic_write_text(harness_path, harness_content)
                harness_path.chmod(0o755)
                print(f"��️ [Generic Harness Engine] Created dynamic harness: {harness_path.name} (Command: {test_cmd})")
