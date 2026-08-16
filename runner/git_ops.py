"""
runner/git_ops.py - Target repository Git operations and checkpoint commits.
"""
import subprocess
from pathlib import Path
from runner.formatters import auto_format_workspace

def ensure_target_git_init(target_dir: Path):
    """ターゲットディレクトリに Git リポジトリを初期化し初期コミットを行う"""
    git_dir = target_dir / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init"], cwd=target_dir, capture_output=True, check=True)
        print(f" 📦 [Target Git] Initialized independent Git repository in: {target_dir}")

def commit_step_if_needed(target_dir: Path, loop_count: int, message: str):
    """GREEN 達成時に、自動フォーマットを実行した上でコミットを刻む"""
    ensure_target_git_init(target_dir)

    try:
        # コミット前に拡張子別の自動フォーマッタを実行
        auto_format_workspace(target_dir)

        subprocess.run(["git", "add", "."], cwd=target_dir, check=True, capture_output=True)
        commit_msg = f"Step #{loop_count}: {message[:60]}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=target_dir, check=True, capture_output=True)
        print(f" 🔖 [Target Git] Auto-committed step #{loop_count} checkpoint into target repository.")
    except Exception as e:
        print(f" ⚠️  [Target Git] Could not commit step #{loop_count}: {e}")
