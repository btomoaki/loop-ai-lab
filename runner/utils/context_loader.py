import os
from pathlib import Path


class ContextLoader:
    """Utility for dynamically loading clean file references, rules, and personas for LLM prompts."""

    @staticmethod
    def get_refinement_file_references(root_dir: Path) -> dict:
        """references/, .agents/rules/, .agents/personas/ 配下のファイルを完全動的ロード。"""
        
        ref_dir = root_dir / "references"
        spec_files = sorted([f"references/{f.name}" for f in ref_dir.glob("*.md")]) if ref_dir.exists() else []
        specs_ref = "\n".join([f"- {f}" for f in spec_files]) or "- references/system_specification.md"

        rules_dir = root_dir / ".agents" / "rules"
        rule_files = sorted([str(f.relative_to(root_dir)) for f in rules_dir.glob("**/*.md")]) if rules_dir.exists() else []
        rules_ref = "\n".join([f"- {f}" for f in rule_files]) or "- .agents/rules/development/go_clean_architecture.md"

        personas_dir = root_dir / ".agents" / "personas"
        persona_files = sorted([f.name for f in personas_dir.glob("*.md")]) if personas_dir.exists() else []
        personas_ref = "\n".join([f"- .agents/personas/{p}" for p in persona_files]) or "- .agents/personas/*.md"

        return {
            "specs": specs_ref,
            "rules": rules_ref,
            "personas": personas_ref
        }
