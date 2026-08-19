"""
runner/parser.py - Standardized code parsing and file system operations for LLM outputs.
"""
import re
from pathlib import Path

def apply_code_changes(llm_output: str, target_dir: Path):
    """LLM の構造化出力から # FILE: ブロックを抽出し、ターゲットディレクトリへ展開する"""
    if not llm_output or "# FILE:" not in llm_output:
        print(" ⚠️  [Parser] No valid # FILE: path blocks found in LLM output.")
        return []

    # # FILE: filepath\n```lang ... ``` の標準フォーマットを抽出
    pattern = r'# FILE:\s*([^\n]+)\n```(?:[a-zA-Z0-9_-]+)?\n(.*?)```'
    matches = re.findall(pattern, llm_output, re.DOTALL)

    # フォールバック: ``` が省略された場合の柔軟検出
    if not matches:
        pattern_fb = r'# FILE:\s*([^\n]+)\n(.*?)(?=# FILE:|\n---|\n# [A-Z]|$)'
        matches = re.findall(pattern_fb, llm_output, re.DOTALL)

    created_count = 0
    applied_paths = []
    for rel_path_str, code_content in matches:
        rel_path_str = rel_path_str.strip().lstrip("./")
        # ネスト・冗長パスの削除
        rel_path_str = re.sub(r"^(?:workspace/[^/]+/+)+", "", rel_path_str)
        rel_path_str = re.sub(r"^" + re.escape(target_dir.name) + r"/+", "", rel_path_str)

        # 残存マークダウンフェンスの剥ぎ取り
        code_content = re.sub(r"^```(?:[a-zA-Z0-9_-]+)?\n?", "", code_content.strip(), flags=re.IGNORECASE)
        code_content = re.sub(r"\n?```$", "", code_content.strip()).strip()

        if not rel_path_str:
            continue

        target_path = (target_dir / rel_path_str).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(code_content + "\n", encoding="utf-8")
        created_count += 1
        applied_paths.append(target_path)
        print(f" ✍️  [Applied Changes] Updated target file: {target_path}")

    print(f" �� [Parser] Successfully extracted and applied {created_count} file(s).")

def parse_code_blocks(text: str) -> dict:
    import re
    files = {}
    pattern = r"(?:#|//|<!--)\s*FILE:\s*([^\s\n]+).*?\n```[a-zA-Z0-9_-]*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    for filepath, code in matches:
        fp = filepath.strip()
        valid_exts = ('.go', '.html', '.css', '.js', '.json', '.md', '.yml', '.yaml', '.sh', '.env', 'go.mod', 'go.sum', 'Dockerfile')
        if any(fp.endswith(ext) or fp in ('go.mod', 'go.sum') for ext in valid_exts):
            files[fp] = code.strip()
    return files
