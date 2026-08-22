from pathlib import Path

import tempfile
import os

def atomic_write_text(target_path: Path, content: str, encoding: str = "utf-8"):
    """Write text to temporary file first, then atomically replace target file."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_name(f".tmp_{target_path.name}")
    try:
        temp_path.write_text(content, encoding=encoding)
        os.replace(temp_path, target_path)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise e


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

    print(f" 📦 [Parser] Successfully extracted and applied {created_count} file(s).")

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

def extract_spec_sections(references_dir: Path) -> list:
    """Extract H2 and H3 section headings from all markdown files in references/."""
    sections = []
    if not references_dir.exists():
        return sections
    for fpath in sorted(references_dir.glob("*.md")):
        text = fpath.read_text(encoding="utf-8")
        for line in text.splitlines():
            line_str = line.strip()
            if line_str.startswith("## ") or line_str.startswith("### "):
                import re
                clean_title = re.sub(r"^[#\s]+", "", line_str)
                sections.append({"file": fpath.name, "section": clean_title})
    return sections

def audit_spec_coverage(references_dir: Path, initiatives_dir: Path) -> dict:
    """Audit if generated initiatives cover all extracted spec sections."""
    spec_sections = extract_spec_sections(references_dir)
    covered_sections = set()
    
    for backlog_path in initiatives_dir.glob("epic_*/sprint_1_backlog.yaml"):
        text = backlog_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "spec_section:" in line:
                val = line.split("spec_section:", 1)[1].strip().strip('"').strip("'")
                covered_sections.add(val)
    
    uncovered = [s for s in spec_sections if s["section"] not in covered_sections]
    return {
        "total_spec_sections": len(spec_sections),
        "covered_count": len(covered_sections),
        "uncovered_sections": uncovered
    }
