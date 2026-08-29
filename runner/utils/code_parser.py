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
        """
        Extremely robust parser that scans LLM output for files.
        Handles both outside/inside code-block tags:
        [FILE: path] or # FILE: path or // FILE: path
        """
        written_files = []
        if not llm_output:
            return written_files

        # 1. 汎用的なファイル検出用の正規表現パターン
        # [FILE: path], # FILE: path, // FILE: path, ### filepath: path などに対応
        file_tag_pattern = r"(?:\[FILE:\s*([^\n\]]+)\]|(?://|#)\s*FILE:\s*([^\n\r\s]+)|###\s*filepath:\s*([^\n\r\s]+))"

        lines = llm_output.splitlines()
        current_path = None
        in_code_block = False
        code_lines = []

        for line in lines:
            stripped = line.strip()

            # コードブロックの開始/終了をチェック
            if stripped.startswith("```"):
                if in_code_block:
                    # コードブロック終了 -> 収集したコードを書き出す
                    if current_path and code_lines:
                        # もしコードブロックの内側1行目にファイル名が入っていた場合、それを取り除く
                        final_code = "\n".join(code_lines)
                        # 内側のタグをクリーンアップ
                        final_code = re.sub(file_tag_pattern, "", final_code).strip()
                        # 先頭の改行などを削除
                        final_code = final_code.lstrip()

                        if not CodeParser.is_invalid_path(current_path):
                            full_path = target_dir / current_path
                            CodeParser.atomic_write_text(full_path, final_code)
                            written_files.append(current_path)

                    in_code_block = False
                    code_lines = []
                    # 書き出し終わったらパス指定をクリア
                    current_path = None
                else:
                    # コードブロック開始
                    in_code_block = True
                    code_lines = []
                continue

            # 行の中にファイル指定タグがあるかチェック
            match = re.search(file_tag_pattern, line, re.IGNORECASE)
            if match:
                detected_path = (match.group(1) or match.group(2) or match.group(3) or "").strip()
                if detected_path:
                    current_path = detected_path
                # タグ行そのものはコードから除外するため、code_linesには追加しない
                continue

            # コードブロック内の場合、行を収集
            if in_code_block:
                code_lines.append(line)

        return written_files
