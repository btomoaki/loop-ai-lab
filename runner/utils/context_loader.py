import os
from pathlib import Path


class ContextLoader:
    """Utility for clean, folder-level ceremony-specific context loading for LLM prompts."""

    @staticmethod
    def get_ceremony_context(root_dir: Path, ceremony: str = "1_epic_refinement", include_dev_rules: bool = False, language: str = None) -> dict:
        """
        指定されたセレモニーに必要な参照ファイルを動的に返却。
        """
        # references/* 配下の実際の仕様ファイル一覧を列挙
        ref_dir = root_dir / "references"
        if ref_dir.exists() and any(ref_dir.iterdir()):
            spec_files = [f"- references/{p.name}" for p in sorted(ref_dir.iterdir()) if p.is_file() and not p.name.startswith(".")]
            specs_ref = "\n".join(spec_files) if spec_files else "- references/*"
        else:
            specs_ref = "- references/*"

        rule_files = [
            "- .agents/rules/scrum_ceremonies_and_governance.md",
            f"- .agents/rules/{ceremony}/"
        ]
        if include_dev_rules:
            rule_files.append("- .agents/rules/development/")
            if language:
                lang_file = f".agents/rules/languages/{language.lower()}.md"
                if (root_dir / lang_file).exists():
                    rule_files.append(f"- {lang_file}")
            else:
                rule_files.append("- .agents/rules/languages/")

        rules_ref = "\n".join(rule_files)
        personas_ref = "- .agents/personas/"

        return {
            "specs": specs_ref,
            "rules": rules_ref,
            "personas": personas_ref
        }

    @staticmethod
    def get_refinement_file_references(root_dir: Path) -> dict:
        """互換性のための既存ショートカット"""
        return ContextLoader.get_ceremony_context(root_dir, ceremony="1_epic_refinement", include_dev_rules=False)
