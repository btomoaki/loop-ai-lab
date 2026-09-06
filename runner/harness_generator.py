from pathlib import Path
import yaml
from runner.parser import atomic_write_text

from runner.config.project_config import ProjectConfig

def ensure_initiative_files_integrity(root_dir: Path, config=None):
    """Dynamic Harness Generator Engine for Go Code & Container/Deployment Epics."""
    cfg = config or ProjectConfig.load(root_dir)
    init_dir = root_dir / cfg.initiatives_dir
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
            test_cmd = cfg.test_command or "go test ./..."
            epic_title = epic_dir.name
            container_tag = cfg.container_image_name or cfg.project_name
            
            # Determine appropriate default test_cmd based on Epic type
            if "container" in epic_name:
                test_cmd = f"docker build -t {container_tag}:latest ."
            elif "cloud_run" in epic_name or "deploy" in epic_name:
                test_cmd = f"grep -q 'USER' Dockerfile && docker build -t {container_tag}:cloudrun ."
            
            try:
                b_data = yaml.safe_load(b_file.read_text(encoding="utf-8")) or {}
                tasks = b_data.get("tasks", [])
                if tasks and isinstance(tasks, list) and len(tasks) > 0 and "verify_command" in tasks[0]:
                    test_cmd = tasks[0]["verify_command"]
                elif "test_command" in b_data:
                    test_cmd = b_data["test_command"]
                epic_title = b_data.get("epic", epic_dir.name)
            except Exception:
                pass
            
            target_ws_rel = b_data.get("target_workspace", b_data.get("workspace_rel", cfg.workspace_rel))
            module_name = b_data.get("module_name", cfg.project_name)

            format_cmd = b_data.get("format_cmd", "gofmt -w . 2>/dev/null || true")

            # Build specialized harness script (distinguish Docker containers from DI / Dependency Wiring)
            is_container_harness = ("docker" in test_cmd) or ("dockerfile" in test_cmd) or \
                                   ("cloud_run" in epic_name or "deploy" in epic_name) or \
                                   ("container" in epic_name and "di" not in epic_name and "wiring" not in epic_name and "injection" not in epic_name)
            if is_container_harness:
                harness_content = f"""#!/usr/bin/env bash
set -e
BASE_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")/../../.." && pwd)"
TARGET_DIR="${{BASE_DIR}}/{target_ws_rel}"

echo "🧪 [Step 1: Container/Deployment Harness - {sprint_suffix}] Verifying {epic_title}..."
if [ ! -d "${{TARGET_DIR}}" ]; then
    mkdir -p "${{TARGET_DIR}}"
fi

cd "${{TARGET_DIR}}"
if [[ "{test_cmd}" == *"docker build"* ]] && [ ! -f "Dockerfile" ]; then
    echo "❌ [Harness Failure] Dockerfile missing in workspace!"
    exit 2
elif [[ "{test_cmd}" != *"docker build"* ]] && [ ! -f "compose.yaml" ]; then
    echo "❌ [Harness Failure] compose.yaml missing in workspace!"
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

# Go Workspace Module Guard (Self-healing workaround for missing go.mod)
clean_mod_name="{Path(target_ws_rel).name}"
if [ ! -f "go.mod" ] && command -v go >/dev/null 2>&1; then
    echo "📦 [Harness Workaround] Initializing missing Go module: ${{clean_mod_name}}..."
    go mod init "${{clean_mod_name}}" 2>/dev/null || true
fi

# Automatically resolve Go dependencies with self-healing checksum recovery
if [ -f "go.mod" ] && command -v go >/dev/null 2>&1; then
    echo "📦 Resolving Go dependencies safely (self-healing go.sum)..."
    # LLMが偽go.sumを出力した場合の checksum mismatch (SECURITY ERROR) を防ぐため、事前にクリアして公式プロキシから再検証
    rm -f go.sum
    go mod tidy
fi

# Model Purity Enforcement: Block if 'return' keyword is present in internal/domain/model/*.go
if [ -d "internal/domain/model" ]; then
    MODEL_FILES=$(find internal/domain/model -maxdepth 1 -name "*.go" ! -name "*_test.go" 2>/dev/null)
    if [ -n "$MODEL_FILES" ]; then
        if grep -En '\\breturn\\b' $MODEL_FILES >/dev/null 2>&1; then
            echo "❌ [Harness Failure] Model Purity Violation: Function logic or 'return' statement detected in internal/domain/model!"
            echo "Details:"
            grep -En '\\breturn\\b' $MODEL_FILES
            echo "Fix: Structs in internal/domain/model/ must be pure data definitions only. Move all constructors and logic to internal/domain/service/."
            exit 2
        fi
    fi
fi

# Model Test Prohibition Enforcement: Block if test files exist in internal/domain/model/
if [ -d "internal/domain/model" ]; then
    MODEL_TEST_FILES=$(find internal/domain/model -maxdepth 1 -name "*_test.go" 2>/dev/null)
    if [ -n "$MODEL_TEST_FILES" ]; then
        echo "❌ [Harness Failure] Model Test Prohibition: Test files detected in internal/domain/model/!"
        echo "Details:"
        echo "$MODEL_TEST_FILES"
        echo "Fix: Structs in internal/domain/model/ are pure schema definitions with zero business logic. Do NOT write test files in internal/domain/model/. Move all unit tests to internal/domain/service/."
        exit 2
    fi
fi

{format_cmd} 2>/dev/null || true

echo "🧪 [Step 2: Task Check - {sprint_suffix}_harness] Verifying {epic_title}..."

# Tooling Availability Guard: If command uses golangci-lint and it's not installed on host, run tests safely
if echo "{test_cmd}" | grep -q "golangci-lint" && ! command -v golangci-lint >/dev/null 2>&1; then
    echo "⚠️ [Harness Notice] 'golangci-lint' not installed on host. Running verification without host-polluting linter."
    SAFE_TEST_CMD=$(echo "{test_cmd}" | sed -E 's/&& *golangci-lint run [^ ]*//g' | sed -E 's/golangci-lint run [^ ]* *&& *//g')
    eval "$SAFE_TEST_CMD" || exit 2
else
    {test_cmd} || exit 2
fi

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
