import os
from pathlib import Path
from runner.config.project_config import ProjectConfig


class ContextLoader:
    """Utility for clean, ceremony-specific context loading with dynamic agent adaptation."""

    @staticmethod
    def get_ceremony_context(root_dir: Path, ceremony: str = "1_epic_refinement", include_dev_rules: bool = False, config: ProjectConfig = None) -> dict:
        """
        指定されたセレモニーに必要な参照ファイル一覧および開発者モデルプロファイルを返却。
        """
        cfg = config or ProjectConfig.load(root_dir)
        
        # 1. References files (What to build - system specifications)
        ref_dir = root_dir / "references"
        if ref_dir.exists() and ref_dir.is_dir():
            spec_files = sorted([f"- {f.relative_to(root_dir)}" for f in ref_dir.glob("**/*") if f.is_file()])
            specs_ref = "\n".join(spec_files) if spec_files else "- references/"
        else:
            specs_ref = "- references/"

        # 2. Rule files (Universal governance & quality constraints across all ceremonies)
        rule_files = [
            "- .agents/rules/scrum_ceremonies_and_governance.md"
        ]
        if include_dev_rules:
            rule_files.append("- .agents/rules/development/")
            if cfg.language:
                lang_file = f".agents/rules/languages/{cfg.language.lower()}.md"
                if (root_dir / lang_file).exists():
                    rule_files.append(f"- {lang_file}")
            else:
                rule_files.append("- .agents/rules/languages/")

        rules_ref = "\n".join(rule_files)

        # 3. Personas files (Explicit participants)
        persona_dir = root_dir / ".agents" / "personas"
        if persona_dir.exists() and persona_dir.is_dir():
            persona_files = sorted([f"- {f.relative_to(root_dir)}" for f in persona_dir.glob("*.md") if f.is_file()])
            personas_ref = "\n".join(persona_files) if persona_files else "- .agents/personas/"
        else:
            personas_ref = "- .agents/personas/"

        target_agent_profile = (
            f"- Target Executor Model: {cfg.executor_model}\n"
            f"- Max Context Limit: {cfg.llama_max_tokens} tokens\n"
            f"- Persona Constraint: Downstream executor is a code-specialized model with strict context limit. "
            f"Requires micro-scoped, self-contained Epics with explicit Input/Output data structures, pure functions, and testable boundary specifications."
        )

        return {
            "specs": specs_ref,
            "rules": rules_ref,
            "personas": personas_ref,
            "target_agent": target_agent_profile
        }

    @staticmethod
    def get_refinement_file_references(root_dir: Path) -> dict:
        """互換性のためのショートカット"""
        return ContextLoader.get_ceremony_context(root_dir, ceremony="1_epic_refinement", include_dev_rules=False)
