"""
runner/git_ops.py - Target repository Git operations, checkpoint commits, and rollback.
"""
import subprocess
from pathlib import Path
from runner.formatters import auto_format_workspace

def ensure_target_git_init(target_dir: Path):
    """ターゲットディレクトリに Git リポジトリを初期化し、必要に応じて初期コミットを行う"""
    if not target_dir.exists():
        return
    git_dir = target_dir / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init"], cwd=target_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Loop AI Agent"], cwd=target_dir, check=False)
        subprocess.run(["git", "config", "user.email", "agent@loop-ai-lab.local"], cwd=target_dir, check=False)
        print(f" 📦 [Target Git] Initialized independent Git repository in: {target_dir}")
        
        # 既存ファイルが存在する場合、初期コミットを作成
        try:
            status_res = subprocess.run(["git", "status", "--porcelain"], cwd=target_dir, capture_output=True, text=True)
            if status_res.stdout.strip():
                subprocess.run(["git", "add", "."], cwd=target_dir, check=True, capture_output=True)
                subprocess.run(["git", "commit", "-m", "chore: initial repository baseline"], cwd=target_dir, check=True, capture_output=True)
                print(f" 🔖 [Target Git] Created baseline initial commit in: {target_dir}")
        except Exception as e:
            print(f" ⚠️  [Target Git Warning] Failed to create initial commit: {e}")

def commit_sprint_checkpoint(target_dir: Path, epic_name: str, sprint_num: int, task_title: str):
    """GREEN 達成時に、自動フォーマットを実行した上でスプリント合格コミットを刻む"""
    ensure_target_git_init(target_dir)
    try:
        auto_format_workspace(target_dir)
        subprocess.run(["git", "add", "."], cwd=target_dir, check=True, capture_output=True)
        commit_msg = f"feat({epic_name}): sprint {sprint_num} - {task_title}"[:72]
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=target_dir, check=True, capture_output=True)
        print(f" 🔖 [Target Git] Checkpoint committed for Sprint {sprint_num}: '{commit_msg}'")
    except Exception as e:
        print(f" ⚠️  [Target Git] Could not commit Sprint {sprint_num} checkpoint: {e}")

def rollback_to_last_checkpoint(target_dir: Path):
    """リトライ時、直前の合格コミット状態へ巻き戻し、失敗試行での中間ゴミを一掃する"""
    git_dir = target_dir / ".git"
    if not git_dir.exists():
        return
    try:
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=target_dir, check=True, capture_output=True)
        subprocess.run(["git", "clean", "-fd"], cwd=target_dir, check=True, capture_output=True)
        print(f" 🔄 [Target Git] Rolled back workspace to last clean checkpoint (HEAD).")
    except Exception as e:
        print(f" ⚠️  [Target Git Warning] Failed to rollback workspace: {e}")

