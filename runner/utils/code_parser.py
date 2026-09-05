import os
import re
from pathlib import Path


class CodeParser:
    """Utility for atomic file writes and extracting code blocks from LLM output."""

    @staticmethod
    def extract_code_block(text: str, language: str = "yaml") -> str:
        """指定された言語のコードブロックを安全に抽出（本文中の内部コードブロックを破壊しない）。"""
        if not text:
            return ""
        stripped = text.strip()
        lines = stripped.splitlines()
        # 先頭行が ```xxx で末尾行が ``` の場合は単純に外枠を剥ぎ取る
        if lines and lines[0].strip().startswith("```") and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()

        # 末尾の ``` までを貪欲にマッチ（内部の ``` による誤切断を防止）
        pattern_greedy = rf"```(?:{language})?\s*\n(.*)\n```\s*$"
        match_greedy = re.search(pattern_greedy, stripped, re.DOTALL | re.IGNORECASE)
        if match_greedy:
            return match_greedy.group(1).strip()

        pattern = rf"```(?:{language})?\s*\n(.*?)```"
        match = re.search(pattern, stripped, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return stripped

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
        """
        Extremely robust parser that scans LLM output for files.
        Handles both outside/inside code-block tags:
        [FILE: path] or # FILE: path or // FILE: path
        """
        def flush_file(path_str: str, lines_list: list):
            if not path_str or not lines_list:
                return None
            final_code = "\n".join(lines_list).strip()
            if not final_code:
                return None

            clean_path = path_str
            if clean_path.startswith("workspace/"):
                parts = clean_path.split("/")
                clean_path = "/".join(parts[2:]) if len(parts) > 2 else "/".join(parts[1:])

            if not CodeParser.is_invalid_path(clean_path):
                full_path = target_dir / clean_path
                CodeParser.atomic_write_text(full_path, final_code)
                return clean_path
            return None

        # 1. 厳格なファイル検出用パターン: [FILE: path] を最優先
        file_tag_pattern = r"(?:\[FILE:\s*([^\n\]]+)\]|(?://|#)\s*FILE:\s*([^\n\r\s]+)|###\s*filepath:\s*([^\n\r\s]+))"

        written_files = []
        lines = llm_output.splitlines()
        current_path = None
        in_code_block = False
        code_lines = []

        for line in lines:
            stripped = line.strip()

            # 行の中にファイル指定タグがあるかチェック
            match = re.search(file_tag_pattern, line, re.IGNORECASE)
            if match:
                # 新しいファイルタグが来たら、直前までに蓄積されたファイルを即座にフラッシュして書き出す
                saved = flush_file(current_path, code_lines)
                if saved and saved not in written_files:
                    written_files.append(saved)

                code_lines = []
                detected_path = (match.group(1) or match.group(2) or match.group(3) or "").strip()
                current_path = detected_path if detected_path else None
                continue

            # コードブロックの開始/終了をチェック
            if stripped.startswith("```"):
                if in_code_block:
                    # コードブロック終了 -> 蓄積したコードをフラッシュ
                    saved = flush_file(current_path, code_lines)
                    if saved and saved not in written_files:
                        written_files.append(saved)
                    code_lines = []
                    current_path = None
                    in_code_block = False
                else:
                    in_code_block = True
                    code_lines = []
                continue

            # コードブロック内の場合、行を収集
            if in_code_block and current_path:
                code_lines.append(line)

        # 全行走査後、未フラッシュのコードがあれば書き出す
        saved = flush_file(current_path, code_lines)
        if saved and saved not in written_files:
            written_files.append(saved)

        return written_files
