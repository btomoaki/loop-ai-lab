import os
from pathlib import Path


class ContextLoader:
    """Utility for loading lightweight file path references for LLM prompts."""

    @staticmethod
    def get_refinement_file_references(root_dir: Path) -> dict:
        """リファインメントフェーズで本当に必要な参照のみをワイルドカード表記で返却。無関係な開発ルールは除外。"""
        
        # Specification references
        specs_ref = "- references/icon_generator.md"
        
        # Refinement-relevant rules only (excluding development/*.md)
        rules_ref = (
            "- .agents/rules/refinement/*.md\n"
            "- .agents/rules/policies/*.md"
        )
        
        # Personas references
        personas_ref = "- .agents/personas/*.md"

        return {
            "specs": specs_ref,
            "rules": rules_ref,
            "personas": personas_ref
        }
