import re
from pathlib import Path


class CodeParser:
    """Utility class for parsing LLM output and writing files atomically."""

    @staticmethod
    def atomic_write_text(file_path: Path, content: str):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(file_path)

    @staticmethod
    def apply_code_changes(llm_output: str, target_dir: Path, config=None):
        """Extract # FILE: header blocks and apply code changes.

        Args:
            llm_output: LLMからの出力テキスト
            target_dir: コード書き込み先のディレクトリ
            config: ProjectConfig（パスプレフィックス除去用、省略可）
        """
        if not llm_output or "# FILE:" not in llm_output:
            print(" ⚠️ [CodeParser] No valid # FILE: path blocks found in LLM output.")
            return []

        pattern = r'# FILE:\s*([^\n]+)\n```(?:[a-zA-Z0-9_-]+)?\n(.*?)```'
        matches = re.findall(pattern, llm_output, re.DOTALL)

        if not matches:
            pattern_fallback = r'# FILE:\s*([^\n]+)\n(.*?)(?=\n# FILE:|\Z)'
            matches = re.findall(pattern_fallback, llm_output, re.DOTALL)

        # config からワークスペースプレフィックスを取得、なければ target_dir.name でフォールバック
        if config and hasattr(config, "workspace_prefixes"):
            ws_prefixes = config.workspace_prefixes + [f"{target_dir.name}/"]
        else:
            ws_prefixes = [f"{target_dir.name}/"]

        applied_paths = []
        for rel_path_str, code_content in matches:
            rel_path_str = rel_path_str.strip().lstrip("./")

            # Remove duplicate workspace prefix if present
            for ws_pfx in ws_prefixes:
                if rel_path_str.startswith(ws_pfx):
                    rel_path_str = rel_path_str[len(ws_pfx):]

            code_content = re.sub(r"^```(?:[a-zA-Z0-9_-]+)?\n?", "", code_content.strip(), flags=re.IGNORECASE)
            code_content = re.sub(r"\n?```$", "", code_content.strip()).strip()

            if not rel_path_str:
                continue

            target_path = (target_dir / rel_path_str).resolve()
            CodeParser.atomic_write_text(target_path, code_content + "\n")
            print(f" ✍️ [Applied Changes] Updated target file: {target_path}")
            applied_paths.append(target_path)

        return applied_paths
