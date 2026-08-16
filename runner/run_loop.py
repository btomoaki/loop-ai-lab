#!/usr/bin/env python3
"""
runner/run_loop.py - Autonomous Loop Orchestrator Main Entrypoint.
Decoupled & Modularized Architecture.
"""
import sys
import os
import subprocess
from pathlib import Path

# Add current project root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runner.adapters import get_adapter
from runner.parser import apply_code_changes
from runner.git_ops import ensure_target_git_init, commit_step_if_needed

def load_env_config(config_path: Path) -> dict:
    """config.env を読み込み辞書型で返す"""
    config = {}
    if not config_path.exists():
        print(f"❌ Error: Config file not found at {config_path}")
        sys.exit(1)
    
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                config[key.strip()] = val.strip().strip('"').strip("'")
    return config

def main():
    root_dir = Path(__file__).resolve().parent.parent
    config_path = root_dir / "config.env"
    config = load_env_config(config_path)

    active_task_type = config.get("ACTIVE_TASK_TYPE", "feature_dev")
    target_dir = root_dir / config.get("TARGET_DIR", "workspace/sample-project")
    req_file_path = root_dir / config.get("REQUIREMENT_FILE", "requirements.sample.md")
    eval_log_path = root_dir / config.get("EVALUATION_LOG_FILE", "logs/EVALUATION_LOG.md")
    verify_command = config.get("VERIFY_COMMAND", "go test ./...")
    max_loops = int(config.get("MAX_LOOPS", 5))
    review_interval = int(config.get("REVIEW_INTERVAL", 3))

    evaluator_provider = config.get("EVALUATOR_PROVIDER", "gemini")
    evaluator_model = config.get("EVALUATOR_MODEL", "gemini-2.5-flash")
    executor_provider = config.get("EXECUTOR_PROVIDER", "llama_cpp")
    executor_model = config.get("EXECUTOR_MODEL", "qwen2.5-coder-32b-instruct-q4_k_m")
    local_llm_url = config.get("LOCAL_LLM_URL", "http://127.0.0.1:11435")

    print(f"🚀 Starting loop-ai-lab multi-step orchestration runner (Max Loops: {max_loops})...\n")

    ensure_target_git_init(target_dir)

    policy_file = f"policies/{active_task_type}.md"
    policy_path = root_dir / policy_file
    policy_content = policy_path.read_text(encoding="utf-8") if policy_path.exists() else ""
    requirement_content = req_file_path.read_text(encoding="utf-8") if req_file_path.exists() else ""

    evaluator = get_adapter(evaluator_provider, model_name=evaluator_model)
    executor = get_adapter(executor_provider, model_name=executor_model, api_url=local_llm_url)

    harness_script = root_dir / "scripts" / "verify-harness.sh"

    for step_num in range(1, max_loops + 1):
        print("=" * 50)
        print(f" 🔄 [Loop Runner] Step #{step_num}")
        print("=" * 50)
        print(f" 🤖 Evaluator Adapter: [{evaluator_provider}] ({evaluator_model})")
        print(f" 🤖 Executor Adapter : [{executor_provider}] ({executor_model})")
        print(f" 📜 Policy Active    : [{policy_file}]\n")

        # 1. Evaluator Phase
        print("🧐 [1/3] Evaluator (Cloud LLM) evaluating progress & history...")
        history_content = eval_log_path.read_text(encoding="utf-8") if eval_log_path.exists() else ""
        
        eval_prompt = f"""
[SYSTEM INSTRUCTION - LOOP CONTROLLER / EVALUATOR]
You are the lead architect evaluator.
Your goal is to inspect history and guide the executor step-by-step toward 100% harness success.

=== POLICY RULES ===
{policy_content}

=== REQUIREMENTS ===
{requirement_content}

=== HISTORY LOG ===
{history_content}

Instructions for Step #{step_num}:
Analyze history and issue a clear, precise instruction for the executor for this step.
"""
        eval_instruction = evaluator.generate(eval_prompt)
        print(f"   Instruction Output: {eval_instruction[:120]}...\n")

        # 2. Executor Phase
        print("🛠️ [2/3] Executor (Local LLM) generating implementation...")
        exec_prompt = f"""
[SYSTEM INSTRUCTION - CODE EXECUTOR]
=== POLICY RULES ===
{policy_content}

=== INSTRUCTION FOR STEP #{step_num} ===
{eval_instruction}

Generate the exact file changes using `# FILE: filepath` markers.
"""
        code_output = executor.generate(exec_prompt)
        apply_code_changes(code_output, target_dir)

        # 3. Progress Review Logging
        if step_num % review_interval == 0 or step_num == max_loops:
            print("\n" + "=" * 60)
            print(f"📊 [Progress Review] Step #{step_num} / Max {max_loops}")
            print(f" 🎯 Task Type      : {active_task_type}")
            print(f" 📂 Target Dir     : {target_dir}")
            print(f" 📝 Evaluator      : {evaluator_provider} ({evaluator_model})")
            print("=" * 60 + "\n")

        # 4. Harness Validation
        print("\n🧪 [3/3] Running Harness Validation...")
        env = os.environ.copy()
        env["TARGET_DIR"] = str(target_dir)
        env["VERIFY_COMMAND"] = verify_command

        res = subprocess.run([str(harness_script)], env=env, capture_output=True, text=True)

        print("-" * 65)
        print(res.stdout)
        if res.stderr:
            print(res.stderr)
        print("-" * 65)

        harness_success = (res.returncode == 0)

        # Record Log
        log_entry = f"\n## Step #{step_num} [{'PASSED' if harness_success else 'FAILED'}]\n"
        log_entry += f"- **Instruction**: {eval_instruction[:200]}...\n"
        log_entry += f"- **Harness Output Summary**:\n```\n{res.stdout[-600:]}\n```\n---\n"
        
        eval_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(eval_log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)

        if harness_success:
            print(f"🎉 [SUCCESS] Step #{step_num} Passed Harness Validation!")
            commit_step_if_needed(target_dir, step_num, f"Step #{step_num} passed harness")
            sys.exit(0)
        else:
            print(f"❌ [FAILED] Harness Verification Failed (Exit Code: {res.returncode})\n")

    print(f"❌ [STOPPED] Reached MAX_LOOPS ({max_loops}) limit without full resolution.")
    sys.exit(1)

if __name__ == "__main__":
    main()
