import os
import sys
import json
import re
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adapters import GeminiAdapter, LlamaCppAdapter, get_llm_adapter
from parser import apply_code_changes

def load_active_yaml_backlog(root_dir: Path, sprint_num: int) -> str:
    initiatives_dir = root_dir / "state" / "initiatives"
    found = sorted(list(initiatives_dir.glob(f"**/sprint_{sprint_num}_backlog.yaml")))
    if found:
        return found[0].read_text(encoding="utf-8")
    return ""

def update_current_issues(root_dir: Path, loop_num: int, exit_code: int, stdout: str, stderr: str):
    issues_file = root_dir / "state" / ".evaluator" / "current_issues.md"
    issues_file.parent.mkdir(parents=True, exist_ok=True)
    
    status_str = "PASS (100% GREEN)" if exit_code == 0 else f"FAIL (Exit Code {exit_code})"
    err_snippet = (stdout + "\n" + stderr).strip()[-1500:] if exit_code != 0 else "All acceptance criteria & tests passed 100% GREEN."
    
    content = f"""# Current Issues & Active Tasks

## Current Active Focus
- **Epic 1 (Domain Layer)**: Implement `internal/domain/model/grid.go` and `grid_test.go` in `workspace/avatar-service/`.
- **Sprint Harness Status**: {status_str} in Loop #{loop_num}

## Latest Harness Execution Failure Output (Loop #{loop_num}):
```text
{err_snippet}
```

## Remaining Epics
1. **Epic 1**: Domain Model & Core Logic
2. **Epic 2**: Use Case & Application Layer
3. **Epic 3**: Infrastructure Layer (HTTP/Storage)
4. **Epic 4**: Interface Layer & Integration Tests
"""
    issues_file.write_text(content, encoding="utf-8")
    print(f" 📝 [Updated] state/.evaluator/current_issues.md (Loop #{loop_num} Status: {status_str})", flush=True)

def run_sprint_development(config: Dict[str, Any], root_dir: Path, sprint_num: int = 1) -> bool:
    print("\n" + "="*50, flush=True)
    print(f" 🚀 [Scrum Phase 2] Executing Sprint {sprint_num} Development Loop", flush=True)
    print("="*50, flush=True)
    
    workspace_dir = root_dir / "workspace" / "avatar-service"
    initiatives_dir = root_dir / "state" / "initiatives"
    found = sorted(list(initiatives_dir.glob(f"**/sprint_{sprint_num}_harness.sh")))
    if found:
        harness_path = found[0]
    else:
        print(f"⚠️ Harness script missing for Sprint {sprint_num}! Guarding with generic harness...", flush=True)
        harness_path = root_dir / "scripts" / "generic-harness-guard.sh"

    local_llm_url = os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:11435")
    dev_agent = get_llm_adapter("llama_cpp", model_name="devstral", base_url=local_llm_url)
    print(f" 🤖 [Dev Engine]: Using Local LLM at {local_llm_url} ({getattr(dev_agent, 'model_name', 'devstral')})", flush=True)
    
    max_loops = 10
    loop = 0
    
    while loop < max_loops:
        loop += 1
        print(f"\n🔄 [Loop {loop}/{max_loops}] Running Test Harness: {harness_path.relative_to(root_dir)}...", flush=True)
        
        proc = subprocess.run(["bash", str(harness_path)], cwd=str(root_dir), capture_output=True, text=True, stdin=subprocess.DEVNULL)
        print(f"   Harness Exit Code: {proc.returncode}", flush=True)
        
        # Auto-update state/.evaluator/current_issues.md with latest result
        update_current_issues(root_dir, loop, proc.returncode, proc.stdout, proc.stderr)
        
        if proc.returncode == 0:
            print(f"🎉 [Sprint {sprint_num} Success] Test Harness PASSED 100% GREEN in loop {loop}!", flush=True)
            return True
            
        print(f"⚠️ [Harness Failure]: Harness returned exit code {proc.returncode}. Requesting code fixes...", flush=True)
        
        backlog_content = load_active_yaml_backlog(root_dir, sprint_num)
        memo_file = root_dir / "state" / ".evaluator" / "memo.md"
        issues_file = root_dir / "state" / ".evaluator" / "current_issues.md"
        memo_content = memo_file.read_text(encoding="utf-8") if memo_file.exists() else ""
        issues_content = issues_file.read_text(encoding="utf-8") if issues_file.exists() else ""

        dev_prompt = (
            f"[SPRINT {sprint_num} DEVELOPMENT FIX]\n"
            f"Fix the code failures reported by the test harness.\n\n"
            f"## SYSTEM ARCHITECTURE MEMO & DESIGN DECISIONS:\n"
            f"```markdown\n{memo_content}\n```\n\n"
            f"## CURRENT ISSUES & ACTIVE STATUS:\n"
            f"```markdown\n{issues_content}\n```\n\n"
            f"## ACTIVE SPRINT BACKLOG:\n"
            f"```yaml\n{backlog_content}\n```\n\n"
            f"## HARNESS STDOUT / STDERR:\n"
            f"```\n{proc.stdout}\n{proc.stderr}\n```\n\n"
            f"CRITICAL INSTRUCTIONS:\n"
            f"Output code updates using `# FILE: workspace/avatar-service/path/to/file` header.\n"
        )
        
        print(f"🚀 [DEBUG-LLM] Loop {loop}: Requesting code fixes from Local LLM...", flush=True)
        raw_code = dev_agent.generate_text(dev_prompt)
        print(f"📦 [DEBUG-LLM] Loop {loop}: Parsing and extracting files...", flush=True)
        apply_code_changes(raw_code, target_dir=root_dir)

    print(f"❌ [Sprint {sprint_num} Failed]: Max loops ({max_loops}) reached without passing test harness.", flush=True)
    return False

def run_refinement(config: Dict[str, Any], root_dir: Path) -> bool:
    print("\n" + "="*50, flush=True)
    print(" 🎯 [Scrum Phase 1] Executing Cloud Refinement (Gemini / Cloud Evaluator)", flush=True)
    print("="*50, flush=True)

    refinement_provider = config.get("REFINEMENT_PROVIDER", os.getenv("EVALUATOR_PROVIDER", "gemini"))
    refinement_model = config.get("REFINEMENT_MODEL", os.getenv("EVALUATOR_MODEL", "gemini-2.5-flash"))
    
    evaluator = get_llm_adapter(refinement_provider, model_name=refinement_model)
    print(f" 🤖 [Refinement Engine]: Using Cloud Evaluator ({refinement_provider}: {refinement_model})", flush=True)

    req_file_setting = config.get("REQUIREMENT_FILE", "requirements.sample.md")
    req_file = root_dir / req_file_setting
    req_text = req_file.read_text(encoding="utf-8") if req_file.exists() else "Default application requirements."

    references_dir = root_dir / "references"
    references_text = ""
    if references_dir.exists():
        ref_files = sorted([p for p in references_dir.glob("*.md") if p.is_file()])
        for ref_file in ref_files:
            references_text += f"\n--- [REFERENCE FILE: {ref_file.name}] ---\n"
            references_text += ref_file.read_text(encoding="utf-8") + "\n"
        print(f" 📚 [References]: Loaded {len(ref_files)} reference document(s) from references/", flush=True)

    prompt = f"""
[SYSTEM INSTRUCTION - SCRUM REFINEMENT PO]
Analyze the requirement document and project reference materials to refine engineering Epics and Sprints.

REQUIREMENTS ({req_file_setting}):
{req_text}

PROJECT REFERENCE MATERIALS (references/*.md):
{references_text if references_text else "No additional reference materials."}

OUTPUT INSTRUCTIONS:
Output initiative breakdown and sprint backlogs using `# FILE: state/initiatives/path/to/file` header.
"""

    print("🚀 Requesting Refinement Plan from Cloud Evaluator...", flush=True)
    response = evaluator.generate_text(prompt)
    if response:
        apply_code_changes(response, target_dir=root_dir)
        print("🎉 [Refinement Success] Refinement phase completed successfully!", flush=True)
        return True
    else:
        print("ℹ️ [Refinement Note] Evaluator completed prompt exchange via state/.evaluator/.", flush=True)
        return True

def main():
    parser = argparse.ArgumentParser(description="Autonomous Scrum Runner")
    parser.add_argument("--sprint", type=int, default=1, help="Sprint number to execute")
    parser.add_argument("--phase", type=str, default="all", choices=["all", "refinement", "sprint"], help="Phase to run")
    args = parser.parse_args()
    
    root_dir = Path(__file__).resolve().parent.parent
    config = {}
    config_file = root_dir / "config.env"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip().strip('"').strip("'")
    
    if args.phase in ["all", "refinement"]:
        run_refinement(config, root_dir)

    if args.phase in ["all", "sprint"]:
        run_sprint_development(config, root_dir, sprint_num=args.sprint)

if __name__ == "__main__":
    main()
