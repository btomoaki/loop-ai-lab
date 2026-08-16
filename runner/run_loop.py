import os
import sys
import json
import subprocess
from pathlib import Path
import re

# モジュール検索パスに自リポジトリを追加
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "runner"))

from adapters import get_llm_adapter

def load_env_config():
    config = {}
    config_path = BASE_DIR / "config.env"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip().strip('"').strip("'")
    return config

def read_file_safe(file_path: Path) -> str:
    if file_path.exists():
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"[Error reading {file_path.name}]: {e}"
    return f"[File {file_path.name} does not exist yet]"

def get_directory_tree(target_dir: Path) -> str:
    if not target_dir.exists():
        return "[Target directory does not exist]"
    tree = []
    for root, dirs, files in os.walk(target_dir):
        rel_root = Path(root).relative_to(target_dir)
        if rel_root == Path("."):
            tree.append(f"📁 {target_dir.name}/")
        else:
            tree.append(f"  📁 {rel_root}/")
        for f in files:
            if not f.startswith("."):
                tree.append(f"    📄 {f}")
    return "\n".join(tree)

def apply_code_changes(llm_output: str, target_dir: Path):
    file_blocks = re.findall(r'# FILE:\s*([^\n]+)\n```(?:[a-zA-Z0-9_-]+)?\n(.*?)```', llm_output, re.DOTALL)
    if not file_blocks:
        print(" ⚠️  [Parser] No valid # FILE: path blocks found in LLM output.")
        return

    for rel_path_str, code_content in file_blocks:
        rel_path_str = rel_path_str.strip()
        if rel_path_str.startswith("workspace/"):
            rel_path_str = rel_path_str.replace("workspace/helm-app/", "").replace("workspace/sample-project/", "")
        
        target_path = target_dir / rel_path_str
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(code_content.strip() + "\n", encoding="utf-8")
        print(f" ✍️  [Applied Changes] Updated target file: {target_path}")

def append_evaluation_log(log_file: Path, loop_count: int, instruction: str, is_success: bool, output_log: str):
    log_file.parent.mkdir(parents=True, exist_ok=True)
    status_str = "SUCCESS" if is_success else "FAILED"
    entry = f"""
## Step #{loop_count} [{status_str}]
- **Instruction**: {instruction[:150]}...
- **Harness Output Summary**:
```
{output_log[-300:] if output_log else "No output"}
```
---
"""
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)

def get_recent_evaluation_history(log_file: Path, max_history: int = 3) -> str:
    if not log_file.exists():
        return ""
    content = log_file.read_text(encoding="utf-8")
    entries = content.strip().split("---\n")
    recent = entries[-max_history:]
    return "\n---\n".join(recent)

def ensure_target_git_init(target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    git_dir = target_dir / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init"], cwd=target_dir, capture_output=True, check=True)
        print(f" 📦 [Target Git] Initialized independent Git repository in: {target_dir}")

def commit_target_step(target_dir: Path, loop_count: int, message: str):
    try:
        subprocess.run(["git", "add", "."], cwd=target_dir, check=True, capture_output=True)
        commit_msg = f"Step #{loop_count}: {message[:60]}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=target_dir, check=True, capture_output=True)
        print(f" 🔖 [Target Git] Auto-committed step #{loop_count} checkpoint into target repository.")
    except Exception as e:
        print(f" ⚠️  [Target Git] Could not commit step #{loop_count}: {e}")

def generate_final_readme(evaluator, target_dir: Path, policy_content: str):
    """ハーネス合格後に Evaluator (Claude) を用いて完成したコードベースから親切な README.md を自動生成する"""
    print("\n📝 [Documentation] Generating comprehensive README.md via Evaluator (Claude)...")
    
    tree_out = get_directory_tree(target_dir)
    files_content = []
    for p in target_dir.rglob("*"):
        if p.is_file() and not p.name.startswith(".") and ".git" not in str(p) and p.name != "README.md":
            rel_path = p.relative_to(target_dir)
            try:
                content = p.read_text(encoding="utf-8")
                files_content.append(f"--- File: {rel_path} ---\n{content}\n")
            except Exception:
                pass
                
    files_str = "\n".join(files_content)
    
    prompt = f"""
You are an expert technical writer and developer advocate.
The code implementation in target directory '{target_dir.name}' has PASSED all functional verification tests (Green).

Active Infrastructure Policy:
{policy_content}

Target Directory File Structure:
{tree_out}

Full Implementation Source Code:
{files_str}

Instruction:
Generate a clear, human-friendly, high-quality `README.md` for this repository.
The README.md MUST include:
1. Overview & Purpose of the application/chart.
2. Version Information (chart version, app version, image tags).
3. Standard Installation & Launch commands (e.g. `helm install <name> .`, `kubectl apply`, `docker run`, etc.).
4. Non-Helm / alternative launch instructions if applicable (e.g. `helm template . | kubectl apply -f -`).
5. Key Parameters table (`values.yaml` or environment variables with parameter name, default value, and description).

Output ONLY the raw markdown content of `README.md` without any wrapping markdown fence blocks or extra commentary.
"""
    readme_content = evaluator.generate_text(prompt, system_instruction="You are a professional documentation generator.")
    
    readme_content = re.sub(r"^```markdown\s*", "", readme_content, flags=re.IGNORECASE)
    readme_content = re.sub(r"^```\s*", "", readme_content)
    readme_content = re.sub(r"\s*```$", "", readme_content)
    
    readme_path = target_dir / "README.md"
    readme_path.write_text(readme_content.strip() + "\n", encoding="utf-8")
    print(f" ✍️  [Documentation] Saved generated README.md to {readme_path}")

def run_loop_step(loop_count: int, config: dict):
    print(f"\n==================================================")
    print(f" 🔄 [Loop Runner] Step #{loop_count}")
    print(f"==================================================")

    evaluator_provider = config.get("EVALUATOR_PROVIDER", "gemini")
    evaluator_model = config.get("EVALUATOR_MODEL", "gemini-2.5-flash")
    evaluator = get_llm_adapter(evaluator_provider, evaluator_model)

    executor_provider = config.get("EXECUTOR_PROVIDER", "local_ollama")
    executor_model = config.get("EXECUTOR_MODEL", "qwen3.6:27b")
    local_url = config.get("LOCAL_LLM_URL", "http://localhost:11434/v1")
    num_ctx = int(config.get("OLLAMA_NUM_CTX", "16384"))
    max_tokens = int(config.get("LLAMA_MAX_TOKENS", "4096"))
    executor = get_llm_adapter(executor_provider, executor_model, base_url=local_url, num_ctx=num_ctx, max_tokens=max_tokens)

    print(f" 🤖 Evaluator Adapter: [{evaluator_provider}] ({evaluator_model})")
    print(f" 🤖 Executor Adapter : [{executor_provider}] ({executor_model})")

    target_dir = BASE_DIR / config.get("TARGET_DIR", "workspace/sample-project")
    ensure_target_git_init(target_dir)

    req_path = BASE_DIR / config.get("REQUIREMENT_FILE", "requirements.sample.md")
    prog_path = BASE_DIR / config.get("PROGRESS_FILE", "PROGRESS.md")
    eval_log_path = BASE_DIR / config.get("EVALUATION_LOG_FILE", "EVALUATION_LOG.md")
    
    task_type = config.get("ACTIVE_TASK_TYPE", "infra_setup")
    policy_path = BASE_DIR / "policies" / f"{task_type}.md"
    active_policy = read_file_safe(policy_path)
    print(f" 📜 Policy Active    : [{policy_path.relative_to(BASE_DIR)}]")

    controller_agent = read_file_safe(BASE_DIR / "agents" / "loop-controller.md")

    history_count = int(config.get("REVIEW_INTERVAL", "3"))
    requirements = read_file_safe(req_path)
    progress = read_file_safe(prog_path)
    recent_history = get_recent_evaluation_history(eval_log_path, history_count)

    eval_prompt = f"""
--- TARGET REQUIREMENTS ---
{requirements}

--- CURRENT PROGRESS ---
{progress}

--- ACTIVE POLICY ({task_type}) ---
{active_policy}

--- RECENT EVALUATION HISTORY (Last {history_count} Steps) ---
{recent_history if recent_history else "No previous history yet."}

--- TASK INSTRUCTION FOR CONTROLLER ---
Evaluate the current progress, test failure logs, and recent history.
Formulate exactly ONE actionable, unambiguous task for the Code Executor Agent.
Instruct the Code Executor Agent to format output using explicit `# FILE: <relative_path>` markers before each code block.
"""
    print("\n🧐 [1/3] Evaluator (Gemini) evaluating progress & history...")
    instruction = evaluator.generate_text(eval_prompt, system_instruction=controller_agent)
    print(f"   Instruction Output: {instruction[:120]}...")

    executor_agent = read_file_safe(BASE_DIR / "agents" / "code-executor.md")
    print("\n🛠️ [2/3] Executor (Local LLM) generating implementation...")
    code_output = executor.generate_text(instruction, system_instruction=executor_agent)
    print(f"   Code Output: {code_output[:120]}...")

    apply_code_changes(code_output, target_dir)

    print("\n🧪 [3/3] Running Harness Validation...")
    verify_script = BASE_DIR / "scripts" / "verify-harness.sh"
    res = subprocess.run(["bash", str(verify_script)], capture_output=True, text=True)
    
    print(res.stdout)
    is_success = (res.returncode == 0)
    
    append_evaluation_log(eval_log_path, loop_count, instruction, is_success, res.stdout)
    print(f" 📝 [Decision Log] Recorded Step #{loop_count} outcome into {eval_log_path.name}")

    if is_success:
        print("✅ [SUCCESS] Functional Harness Verification Passed!")
        generate_final_readme(evaluator, target_dir, active_policy)
        commit_target_step(target_dir, loop_count, f"{instruction} + Final README.md generation")
        return True
    else:
        print(f"❌ [FAILED] Harness Verification Failed (Exit Code: {res.returncode})")
        return False

def main():
    config = load_env_config()
    max_loops = int(config.get("MAX_LOOPS", "5"))
    print(f"🚀 Starting loop-ai-lab multi-step orchestration runner (Max Loops: {max_loops})...\n")
    
    for loop in range(1, max_loops + 1):
        is_success = run_loop_step(loop, config)
        if is_success:
            print(f"\n🎉 [COMPLETE] All requirements satisfied at Step #{loop}! Autonomous loop finished successfully.")
            sys.exit(0)
        else:
            print(f"\n⚠️  [RETRY] Step #{loop} failed. Proceeding to Step #{loop + 1} with updated logs and context...")
            
    print(f"\n❌ [STOPPED] Reached MAX_LOOPS ({max_loops}) limit without full resolution. Human review required.")
    sys.exit(1)

if __name__ == "__main__":
    main()
