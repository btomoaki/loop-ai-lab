"""
runner/formatters.py - Extension-based dynamic code formatter registry.
"""
import subprocess
from pathlib import Path

# 拡張子と対応フォーマッタコマンドのマッピング定義
FORMATTER_REGISTRY = {
    ".go": ["gofmt", "-w"],
    ".py": ["python3", "-m", "autopep8", "--in-place"],
    ".js": ["npx", "prettier", "--write"],
    ".ts": ["npx", "prettier", "--write"],
    ".json": ["npx", "prettier", "--write"],
}

def auto_format_workspace(target_dir: Path):
    """ターゲットワークスペース内のファイルを走査し、対応するフォーマッタを自動適用する"""
    if not target_dir.exists():
        return

    # ワークスペース内の拡張子一覧を採集
    all_files = [p for p in target_dir.rglob("*") if p.is_file() and not p.name.startswith(".") and ".git" not in str(p)]
    extensions = {p.suffix for p in all_files}

    for ext in extensions:
        if ext in FORMATTER_REGISTRY:
            cmd = FORMATTER_REGISTRY[ext]
            target_files = [str(p.relative_to(target_dir)) for p in all_files if p.suffix == ext]
            if target_files:
                try:
                    res = subprocess.run(cmd + target_files, cwd=target_dir, capture_output=True, check=False)
                    if res.returncode == 0:
                        print(f" 🎨 [Auto-Format] Executed {' '.join(cmd)} on {len(target_files)} {ext} file(s)")
                except Exception as e:
                    print(f" ⚠️  [Auto-Format Warning] Failed to run {' '.join(cmd)}: {e}")
