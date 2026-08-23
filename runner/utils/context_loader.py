import os
from pathlib import Path


class ContextLoader:
    """Utility for loading clean file path references and user decisions for LLM prompts."""

    @staticmethod
    def get_refinement_file_references(root_dir: Path) -> dict:
        """仕様書、決定事項、およびルール・ペルソナの参照テキストを出力。"""
        
        specs_ref = "- references/icon_generator.md\n- references/decisions.md (Architectural Decisions & Escalation Resolutions)"

        rules_ref = (
            "- .agents/rules/refinement/overall_debate.md (Alternative Proposal Escalation Directive)\n"
            "- .agents/rules/refinement/epic_granularity.md (Single Responsibility Principle & No 'and/with')"
        )
        
        personas_ref = (
            "- .agents/personas/*.md (PO, Specification Auditor, Software Architect, DevOps Cloud Architect, QA Engineer, Security Auditor)"
        )

        return {
            "specs": specs_ref,
            "rules": rules_ref,
            "personas": personas_ref
        }
