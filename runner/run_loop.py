#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
from adapters import get_llm_adapter

BASE_DIR = Path(__file__).resolve().parent.parent

def load_env_config():
    """config.env を読み込み環境変数に適用"""
    config_file = BASE_DIR / "config.env"
    config = {}
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip().strip('"').strip("'")
    return config

def read_file_safe(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

def append_evaluation_log(log_path: Path, loop_count: int, instruction: str, success: bool, log_output: str):
    """EVALUATION_LOG.md に今回のループ結果を追記"""
    status_str = "PASSED (Green)" if success else "FAILED (Red)"
    entry = f"""
### Loop #{loop_count} - Status: {status_str}
- **Evaluator Instruction**: {instruction.strip().replace('\n', ' ')[:200]}...
- **Harness Result**: {log_output.strip().replace('\n', ' ')[:200]}...
"""
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

def get_recent_evaluation_history(log_path: Path, count: int = 3) -> str:
    """EVALUATION_LOG.md から直近 N 件の履歴エントリを抽出"""
    if not log_path.exists():
        return ""
    content = log_path.read_text(encoding="utf-8")
    entries = content.split("### Loop #")
    if len(entries) <= 1:
        return ""
    recent = entries[-count:]
    return "### Loop #" + "### Loop #".join(recent)

def run_loop_step(loop_count: int, config: dict):
    print(f"\n==================================================")
    print(f" 🔄 [Loop Runner] Step #{loop_count}")
    print(f"==================================================")

    # 1. アダプターの初期化 (評価用 ＆ 実装用)
    evaluator_provider = config.get("EVALUATOR_PROVIDER", "gemini")
    evaluator_model = config.get("EVALUATOR_MODEL", "gemini-2.5-flash")
    evaluator = get_llm_adapter(evaluator_provider, evaluator_model)

    executor_provider = config.get("EXECUTOR_PROVIDER", "local_ollama")
    executor_model = config.get("EXECUTOR_MODEL", "deepseek-coder")
    local_url = config.get("LOCAL_LLM_URL", "http://localhost:11434/v1")
    executor = get_llm_adapter(executor_provider, executor_model, base_url=local_url)

    print(f" 🤖 Evaluator Adapter: [{evaluator_provider}] ({evaluator_model})")
    print(f" 🤖 Executor Adapter : [{executor_provider}] ({executor_model})")

    # 2. 状態・コンテキスト・過去の判断履歴・ポリシーの取得 (ワンショットステートレス)
    req_path = BASE_DIR / config.get("REQUIREMENT_FILE", "requirements.sample.md")
    prog_path = BASE_DIR / config.get("PROGRESS_FILE", "PROGRESS.md")
    eval_log_path = BASE_DIR / config.get("EVALUATION_LOG_FILE", "EVALUATION_LOG.md")
    history_count = int(config.get("HISTORY_CONTEXT_COUNT", "3"))
    task_type = config.get("TASK_TYPE", "feature_dev")

    # TASK_TYPE に応じたポリシーファイルの動的読み込み
    policy_path = BASE_DIR / "policies" / f"{task_type}.md"
    policy_content = read_file_safe(policy_path)
    if policy_content:
        print(f" 📜 Policy Active    : [policies/{task_type}.md]")

    controller_agent = read_file_safe(BASE_DIR / "agents" / "loop-controller.md")
    requirements = read_file_safe(req_path)
    progress = read_file_safe(prog_path)
    recent_history = get_recent_evaluation_history(eval_log_path, history_count)

    # 3. Evaluator (Gemini) ステップ: 過去判断履歴およびタスクポリシーを含めた一貫性のある指示の生成
    eval_prompt = f"""
--- REQUIREMENTS ---
{requirements}

--- CURRENT PROGRESS ---
{progress}

--- ACTIVE POLICY ({task_type}) ---
{policy_content if policy_content else "Standard Guidelines apply."}

--- RECENT EVALUATION HISTORY (Last {history_count} Steps) ---
{recent_history if recent_history else "No previous history yet."}

--- INSTRUCTION ---
上記仕様、進捗状況、開発ポリシー ({task_type})、および過去の評価履歴を確認し、ポリシーおよび前言撤回を起こさないよう一貫した方針で、次に実行すべき1つの具体的な実装・修正タスクを指示してください。
"""
    print("\n🧐 [1/3] Evaluator (Gemini) evaluating progress & history...")
    instruction = evaluator.generate_text(eval_prompt, system_instruction=controller_agent)
    print(f"   Instruction Output: {instruction[:120]}...")

    # 4. Executor (Local LLM) ステップ: コード書き換えの実行
    executor_agent = read_file_safe(BASE_DIR / "agents" / "code-executor.md")
    print("\n🛠️ [2/3] Executor (Local LLM) generating implementation...")
    code_output = executor.generate_text(instruction, system_instruction=executor_agent)
    print(f"   Code Output: {code_output[:120]}...")

    # 5. ハーネス検証ステップ
    print("\n🧪 [3/3] Running Harness Validation...")
    verify_script = BASE_DIR / "scripts" / "verify-harness.sh"
    res = subprocess.run(["bash", str(verify_script)], capture_output=True, text=True)
    
    print(res.stdout)
    is_success = (res.returncode == 0)
    
    # 6. 判断ブレ蓄積ログ (EVALUATION_LOG.md) の記録
    append_evaluation_log(eval_log_path, loop_count, instruction, is_success, res.stdout)
    print(f" 📝 [Decision Log] Recorded Step #{loop_count} outcome into {eval_log_path.name}")

    if is_success:
        print("✅ [SUCCESS] Loop Step Completed Successfully!")
        return True
    else:
        print(f"❌ [FAILED] Harness Verification Failed (Exit Code: {res.returncode})")
        return False

def main():
    config = load_env_config()
    print("🚀 starting loop-ai-lab python hybrid orchestration runner...")
    
    # 動作確認デモ用 1ステップ実行
    run_loop_step(1, config)

if __name__ == "__main__":
    main()
