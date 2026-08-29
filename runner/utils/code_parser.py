import os
import re
from pathlib import Path


class CodeParser:
    """Utility for atomic file writes and extracting code blocks from LLM output."""

    @staticmethod
    def extract_code_block(text: str, language: str = "yaml") -> str:
        """指定された言語のコードブロック（```yaml ... ```）を抽出。"""
        if not text:
            return ""
        pattern = rf"```(?:{language})?\s*\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # フォールバック: ``` のみ
        match_generic = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
        if match_generic:
            return match_generic.group(1).strip()
        return text.strip()

    @staticmethod
    def atomic_write_text(file_path: Path, content: str):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(file_path)

    @staticmethod
    def is_invalid_path(path_str: str) -> bool:
        if not path_str or ".." in path_str or path_str.startswith("/"):
            return True
        return False

    @staticmethod
    def apply_code_changes(llm_output: str, target_dir: Path, config=None):
        pattern = r"(?:\\\[FILE:\\s*([^\\n\\]]+)\\]|#\\s*FILE:\\s*([^\\n\\r]+))\\s*```(?:[a-zA-Z0-9_-]+)?\\s*\\n(.*?)```"
        matches = list(re.finditer(pattern, llm_output, re.DOTALL))
        written_files = []

        for m in matches:
            rel_path = (m.group(1) or m.group(2) or "").strip()
            code = m.group(3)

            if CodeParser.is_invalid_path(rel_path):
                continue

            full_path = target_dir / rel_path
            CodeParser.atomic_write_text(full_path, code)
            written_files.append(rel_path)

        return written_files
