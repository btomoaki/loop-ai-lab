import re
from pathlib import Path


class CodeParser:
    """Utility class for parsing LLM output and writing files atomically with robust fallback handling."""

    @staticmethod
    def atomic_write_text(file_path: Path, content: str):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(file_path)

    @staticmethod
    def apply_code_changes(llm_output: str, target_dir: Path, config=None):
        if not llm_output or not llm_output.strip():
            print(" ⚠️ [CodeParser] Empty LLM output provided.")
            return []

        # Pattern 1: Standard `# FILE: path/to/file`
        pattern1 = r'(?:#|//)\s*FILE:\s*([^\n]+)\n```(?:[a-zA-Z0-9_-]+)?\n(.*?)```'
        matches = re.findall(pattern1, llm_output, re.DOTALL)

        # Pattern 2: Fallback without backticks `# FILE: path/to/file`
        if not matches:
            pattern2 = r'(?:#|//)\s*FILE:\s*([^\n]+)\n(.*?)(?=\n(?:#|//)\s*FILE:|\Z)'
            matches = re.findall(pattern2, llm_output, re.DOTALL)

        # Pattern 3: Fallback from first-line comments inside ```go codeblocks like `// main.go` or `// internal/core/identicon.go`
        if not matches:
            pattern3 = r'```(?:go|golang|yaml|yml|markdown)?\n(?://|#)\s*([a-zA-Z0-9_\-/\.]+\.(?:go|yaml|yml|mod|sum))\n(.*?)```'
            matches = re.findall(pattern3, llm_output, re.DOTALL)

        if not matches:
            print(" ⚠️ [CodeParser] No valid file path blocks found in LLM output.")
            return []

        ws_prefixes = [f"{target_dir.name}/", "./"]
        if config and hasattr(config, "workspace_prefixes"):
            ws_prefixes += config.workspace_prefixes

        applied_paths = []
        for rel_path_str, code_content in matches:
            rel_path_str = rel_path_str.strip().lstrip("./")

            for ws_pfx in ws_prefixes:
                if rel_path_str.startswith(ws_pfx):
                    rel_path_str = rel_path_str[len(ws_pfx):]

            code_content = re.sub(r"^```(?:[a-zA-Z0-9_-]+)?\n?", "", code_content.strip(), flags=re.IGNORECASE)
            code_content = re.sub(r"\n?```$", "", code_content.strip()).strip()

            if not rel_path_str:
                continue

            target_path = (target_dir / rel_path_str).resolve()
            CodeParser.atomic_write_text(target_path, code_content + "\n")
            print(f" ✍️ [Applied Changes] Updated target file: {target_path.relative_to(target_dir.parent.parent)}")
            applied_paths.append(target_path)

        return applied_paths
