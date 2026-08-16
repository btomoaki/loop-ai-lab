"""
runner/parser.py - Code parsing and file system operations for LLM outputs.
"""
import re
from pathlib import Path

def apply_code_changes(llm_output: str, target_dir: Path):
    """LLM 出力から # FILE: ブロックを抽出し、ターゲットディレクトリへ展開する"""
    file_blocks = re.findall(r'# FILE:\s*([^\n]+)\n```(?:[a-zA-Z0-9_-]+)?\n(.*?)```', llm_output, re.DOTALL)
    if not file_blocks:
        print(" ⚠️  [Parser] No valid # FILE: path blocks found in LLM output.")
        return

    for rel_path_str, code_content in file_blocks:
        rel_path_str = rel_path_str.strip()
        # ネストされたパスの正規化
        rel_path_str = re.sub(r"^(?:workspace/[^/]+/+)+", "", rel_path_str)
        rel_path_str = re.sub(r"^" + re.escape(target_dir.name) + r"/+", "", rel_path_str)
        
        target_path = (target_dir / rel_path_str).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(code_content.strip() + "\n", encoding="utf-8")
        print(f" ✍️  [Applied Changes] Updated target file: {target_path}")
