#!/usr/bin/env python3
"""
Scrum AI Loop Orchestration Runner (2-Pass Refinement Engine & 10-Loop Limit)
"""

import os
import sys
import argparse
import subprocess
import re
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from runner.run_loop import load_env_config
from runner.adapters import get_llm_adapter

def parse_code_blocks(text: str) -> dict:
    files = {}
    pattern = r"(?:#|//|<!--)\s*FILE:\s*([^\s\n]+).*?\n```[a-zA-Z0-9_-]*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    for filepath, code in matches:
        fp = filepath.strip()
        valid_exts = ('.go', '.html', '.css', '.js', '.json', '.md', '.yml', '.yaml', '.sh', '.env', 'go.mod', 'go.sum', 'Dockerfile')
        if any(fp.endswith(ext) or fp in ('go.mod', 'go.sum') for ext in valid_exts):
            files[fp] = code.strip()
    return files

def apply_code_changes(files: dict, base_dir: Path):
    for rel_path, content in files.items():
        target_path = base_dir / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content + "\n", encoding="utf-8")
        print(f" ✍️  [Applied] {target_path}")

def run_refinement_phase(config, root_dir, sprint_num=1):
    print("\n==================================================")
    print(" 🔍 [Scrum Phase 1] 2-Pass Refinement Execution")
    print("==================================================")

    req_file_path = root_dir / config.get("REQUIREMENT_FILE", "requirements.sample.md")
    req_content = req_file_path.read_text(encoding="utf-8") if req_file_path.exists() else "No specific requirement file."

    refine_provider = config.get("REFINEMENT_PROVIDER", config.get("EVALUATOR_PROVIDER", "gemini")).lower().strip()
    refine_model = config.get("REFINEMENT_MODEL", config.get("EVALUATOR_MODEL", "gemini-3.7-flash-low"))

    if refine_provider in ("llama_cpp", "llama", "local_ollama", "ollama"):
        print("⚠️ [Refinement Guardrail Warning]: Falling back from local LLM to Gemini Cloud LLM for Refinement!")
        refine_provider = "gemini"
        refine_model = "gemini-3.7-flash-low"

    print(f" 🤖 [Refinement Engine]: Using {refine_provider.upper()} ({refine_model})")
    refinement_agent = get_llm_adapter(refine_provider, model_name=refine_model)

    policies_dir = root_dir / "policies"
    references_dir = root_dir / "references"
    avail_policies = [p.name for p in policies_dir.glob("*.md")] if policies_dir.exists() else []
    avail_refs = [r.name for r in references_dir.glob("*.md")] if references_dir.exists() else []

    retro_path = root_dir / "state/sprints/retrospective.md"
    retro_context = f"\n\n## 💡 LESSONS LEARNED FROM PAST RETROSPECTIVE:\n```markdown\n{retro_path.read_text(encoding='utf-8')}\n```" if retro_path.exists() else ""

    # Pass 1: Product Roadmap & Sprint Backlogs
    print("\n🧐 [Refinement Pass 1/2] Generating Product Roadmap & All Sprint Backlogs...")
    pass1_prompt = f"""[REFINEMENT PASS 1: ROADMAP & BACKLOGS]
You are Lead Product Owner. Split requirements into a detailed multi-sprint roadmap and backlogs.

## REQUIREMENTS:
```markdown
{req_content}
```

## AVAILABLE BASE POLICIES: {avail_policies}
## AVAILABLE KNOWLEDGE REFERENCES: {avail_refs}{retro_context}

## 🤖 TARGET EXECUTOR SPECIFICATION (Local LLM - Devstral 24B):
- Context Window: 16,384 tokens | Max Generation: 4,096 tokens
- High capacity for one-shot initial skeleton generation. Keep Sprint scope achievable in 3-5 loops.

## 🚫 CRITICAL CONSTRAINT (STRICT NEGATIVE PROMPT):
- ABSOLUTELY PROHIBITED: Do NOT write "Go標準ライブラリのみ" or "標準パッケージのみ" or "ゼロ依存" anywhere in product_backlog.md or backlog files!
- Third-party Go libraries (e.g. Gin, Chi, Zap, image packages) are FULLY ALLOWED and encouraged.

## YOUR TASK (PASS 1):
1. Write a HIGHLY DETAILED `state/sprints/product_backlog.md` (Product vision, detailed sprint roadmap for Sprint 1, 2, 3 with architecture/scope explanations, and gap analysis).
2. Write detailed Backlogs for ALL SPRINTS: `state/sprints/sprint_1_backlog.md`, `state/sprints/sprint_2_backlog.md`, `state/sprints/sprint_3_backlog.md`.

Please provide code blocks with `# FILE: filepath` markers for:
- `state/sprints/product_backlog.md`
- `state/sprints/sprint_1_backlog.md`
- `state/sprints/sprint_2_backlog.md`
- `state/sprints/sprint_3_backlog.md`
"""

    raw_pass1 = refinement_agent.generate_text(pass1_prompt)
    files_pass1 = parse_code_blocks(raw_pass1)
    if files_pass1:
        apply_code_changes(files_pass1, root_dir)
        print("✅ [Pass 1/2 Complete] Product Roadmap & Sprint Backlogs generated.")
    else:
        print("⚠️ [Pass 1/2] Failed to extract roadmap/backlog files.")
        return False

    # Pass 2: Custom Harnesses & Sprint Policy
    print("\n🛠️ [Refinement Pass 2/2] Generating Executable Custom Harnesses & Policy...")
    pb_path = root_dir / "state/sprints/product_backlog.md"

    pass2_prompt = f"""[REFINEMENT PASS 2: CUSTOM HARNESSES & POLICY]
You are Lead Architect. You MUST write complete, fully-functional executable bash test scripts for each Sprint.

## YOUR TASK (PASS 2):
Write COMPLETE bash scripts starting with `#!/usr/bin/env bash` and `set -euo pipefail`.

Please provide non-empty code blocks with `# FILE: filepath` markers for:
- `state/sprints/sprint_1_policy.md`
- `state/sprints/sprint_1_harness.sh`
- `state/sprints/sprint_2_harness.sh`
- `state/sprints/sprint_3_harness.sh`
"""

    raw_pass2 = refinement_agent.generate_text(pass2_prompt)
    files_pass2 = parse_code_blocks(raw_pass2)
    if files_pass2:
        apply_code_changes(files_pass2, root_dir)
        for s in [1, 2, 3]:
            h_path = root_dir / f"state/sprints/sprint_{s}_harness.sh"
            if h_path.exists():
                os.chmod(h_path, 0o755)
        print("🎉 [Scrum Phase 1 Complete] 2-Pass Refinement Finished 100% GREEN!")
        return True
    else:
        print("⚠️ [Pass 2/2] Failed to extract harness files.")
        return False

def run_sprint_phase(config, root_dir, sprint_num=1):
    print("\n==================================================")
    print(f" 🏃 [Scrum Phase 2] Executing Sprint #{sprint_num}")
    print("==================================================")

    custom_harness_path = root_dir / f"state/sprints/sprint_{sprint_num}_harness.sh"
    if not custom_harness_path.exists():
        print(f"❌ Custom harness for Sprint #{sprint_num} not found at {custom_harness_path}")
        return False

    target_dir = root_dir / config.get("TARGET_DIR", "workspace/sample-project")
    evaluator_provider = config.get("EVALUATOR_PROVIDER", "gemini")
    evaluator_model = config.get("EVALUATOR_MODEL", "gemini-3.7-flash-low")
    executor_provider = config.get("EXECUTOR_PROVIDER", "llama_cpp")
    executor_model = config.get("EXECUTOR_MODEL", "devstral")

    evaluator = get_llm_adapter(evaluator_provider, model_name=evaluator_model)
    local_url = config.get("LOCAL_LLM_URL", "http://127.0.0.1:11435/completion")
    executor = get_llm_adapter(executor_provider, model_name=executor_model, base_url=local_url)

    memo_path = root_dir / "state/memo.md"
    memo_context = f"\n\n## 📜 PROJECT ARCHITECTURE RULES & CONSTRAINTS (memo.md):\n```markdown\n{memo_path.read_text(encoding='utf-8')}\n```" if memo_path.exists() else ""

    retro_path = root_dir / "state/sprints/retrospective.md"
    retro_info = f"\n\n## 💡 PAST RETROSPECTIVE LESSONS:\n```markdown\n{retro_path.read_text(encoding='utf-8')[-800:]}\n```" if retro_path.exists() else ""

    issues_track_path = root_dir / "state/current_issues.md"
    if not issues_track_path.exists():
        issues_track_path.write_text(f"# 🐛 Current Sprint #{sprint_num} Issues & Recovery Tracking\n\n", encoding="utf-8")

    max_sprint_loops = 10
    for step in range(1, max_sprint_loops + 1):
        print(f"\n--- [Sprint #{sprint_num} / Loop Step #{step} of {max_sprint_loops}] ---")
        
        res = subprocess.run(["bash", str(custom_harness_path)], cwd=target_dir, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"🎉 [SUCCESS] Sprint #{sprint_num} Custom Harness PASSED 100% GREEN in Step #{step}!")
            
            pass_entry = f"\n### ✅ [Step #{step}] Harness Verification: PASSED (GREEN)\n- **Result**: All tests and formatting passed 100% GREEN!\n"
            with open(issues_track_path, "a", encoding="utf-8") as f:
                f.write(pass_entry)
            return True

        print(f"❌ [Sprint Harness] Failure detected (Exit Code: {res.returncode})")
        err_log = res.stdout[-1500:] if res.stdout else res.stderr[-1500:]

        eval_prompt = f"""[SYSTEM INSTRUCTION - SPRINT EVALUATOR]
You are Lead Sprint Evaluator. Analyze current harness failure and instruct the Executor on exact code changes.

## SPRINT #{sprint_num} BACKLOG:
```markdown
{(root_dir / f'state/sprints/sprint_{sprint_num}_backlog.md').read_text(encoding='utf-8') if (root_dir / f'state/sprints/sprint_{sprint_num}_backlog.md').exists() else 'N/A'}
```
{memo_context}{retro_info}

## CURRENT HARNESS FAILURE LOG (Step #{step}):
```text
{err_log}
```

TARGET OUTPUT FORMAT:
### 1. [ACTION REQUIRED]
- **What Failed**: Brief explanation of root cause.
- **Target Files**: `relative/file/path.go`
- **Required Fix**: Concrete implementation guidelines.
"""
        eval_instruction = evaluator.generate_text(eval_prompt)

        sprint_policy_path = root_dir / f"state/sprints/sprint_{sprint_num}_policy.md"
        active_policy_path = sprint_policy_path if sprint_policy_path.exists() else (root_dir / "policies/scrum_dev.md")

        exec_prompt = f"""[SYSTEM INSTRUCTION - CODE EXECUTOR]
Implement the exact code modifications requested by the Evaluator to pass Sprint #{sprint_num} Harness.

## 🎯 MANDATORY OUTPUT FORMAT:
You MUST provide code blocks starting with `# FILE: relative/path/to/file.ext` before each block!
Example:
# FILE: go.mod
```go
module identicon-generator
go 1.22
```

## POLICY: {active_policy_path.name}
{memo_context}

## EVALUATOR INSTRUCTION:
{eval_instruction}

## ERROR LOG (Step #{step}):
```text
{err_log}
```
"""
        raw_exec = executor.generate_text(exec_prompt)
        code_files = parse_code_blocks(raw_exec)

        step_entry = f"""
## 📌 [Step #{step}/{max_sprint_loops}] Issue & Fix Tracking
- **What Failed**: Harness Exit Code {res.returncode}
- **Evaluator Analysis**:
{eval_instruction[:400]}...
- **Files Modified**: {list(code_files.keys()) if code_files else 'None'}
- **Status**: Code applied, pending next verification loop.
---
"""
        with open(issues_track_path, "a", encoding="utf-8") as f:
            f.write(step_entry)

        if code_files:
            apply_code_changes(code_files, target_dir)

    print(f"❌ Sprint #{sprint_num} reached max limit ({max_sprint_loops} loops) without passing custom harness. Auto-stopping sprint.")
    print("📝 Generating Retrospective report (state/sprints/retrospective.md)...")

    retro_prompt = f"""[SPRINT RETROSPECTIVE ANALYZER]
Sprint #{sprint_num} failed to pass custom harness within {max_sprint_loops} loops.
Read `current_issues.md` for full step tracking history.

OUTPUT FORMAT:
Please output `# FILE: state/sprints/retrospective.md` containing:
1. **Root Cause Analysis**: Why did Sprint #{sprint_num} exceed {max_sprint_loops} loops?
2. **Bottlenecks Identified**: Architectural or test scope issues.
3. **Actionable Kaizen Improvements**: Concrete steps for next refinement/retry.
"""
    raw_retro = evaluator.generate_text(retro_prompt)
    retro_files = parse_code_blocks(raw_retro)
    if retro_files:
        apply_code_changes(retro_files, root_dir)
        print("🎉 [Retrospective] state/sprints/retrospective.md created successfully!")

    return False

def main():
    parser = argparse.ArgumentParser(description="Scrum AI Loop Runner")
    parser.add_argument("--sprint", type=int, default=1, help="Sprint number to execute")
    parser.add_argument("--phase", type=str, choices=["all", "refinement", "sprint"], default="all", help="Phase to run")
    args = parser.parse_args()

    config = load_env_config(root_dir / "config.env")

    if args.phase in ["all", "refinement"]:
        success = run_refinement_phase(config, root_dir, sprint_num=args.sprint)
        if not success:
            sys.exit(1)

    if args.phase in ["all", "sprint"]:
        success = run_sprint_phase(config, root_dir, sprint_num=args.sprint)
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
