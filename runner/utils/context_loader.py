import os
from pathlib import Path


class ContextLoader:
    """Utility for isolated, ceremony-specific context loading for LLM prompts."""

    @staticmethod
    def get_ceremony_context(root_dir: Path, ceremony: str = "1_epic_refinement", include_dev_rules: bool = False) -> dict:
        """
        指定されたセレモニーに必要なルール・ペルソナ・仕様書のみをピンポイントでロード。
        ceremony: "1_epic_refinement", "2_sprint_refinement", "3_sprint_execution"
        """
        # 1. 参照仕様書 (references/ 配下の全ファイルを動的検出、拡張子非依存)
        ref_dir = root_dir / "references"
        spec_files = sorted([f"references/{f.name}" for f in ref_dir.glob("*") if f.is_file()]) if ref_dir.exists() else []
        specs_ref = "\n".join([f"- {f}" for f in spec_files]) or "- references/system_specification"

        # 2. セレモニー別専用ルール (.agents/rules/<ceremony>/ 配下のみピンポイント検出)
        rules_dir = root_dir / ".agents" / "rules" / ceremony
        rule_files = sorted([str(f.relative_to(root_dir)) for f in rules_dir.glob("*.md")]) if rules_dir.exists() else []
        
        # 共通ガバナンスルール
        governance_file = root_dir / ".agents" / "rules" / "scrum_ceremonies_and_governance.md"
        if governance_file.exists():
            rule_files.insert(0, str(governance_file.relative_to(root_dir)))

        # 開発・技術規格ルール (include_dev_rules=True の場合のみ追加)
        if include_dev_rules:
            dev_rules_dir = root_dir / ".agents" / "rules" / "development"
            if dev_rules_dir.exists():
                rule_files.extend([str(f.relative_to(root_dir)) for f in dev_rules_dir.glob("*.md")])

        rules_ref = "\n".join([f"- {f}" for f in rule_files]) or f"- .agents/rules/{ceremony}/*.md"

        # 3. ペルソナ定義 (.agents/personas/ 配下の全ファイル)
        personas_dir = root_dir / ".agents" / "personas"
        persona_files = sorted([f.name for f in personas_dir.glob("*.md")]) if personas_dir.exists() else []
        personas_ref = "\n".join([f"- .agents/personas/{p}" for p in persona_files]) or "- .agents/personas/*.md"

        return {
            "specs": specs_ref,
            "rules": rules_ref,
            "personas": personas_ref
        }

    @staticmethod
    def get_refinement_file_references(root_dir: Path) -> dict:
        """互換性のための既存ショートカット（デフォルト: セレモニー1）"""
        return ContextLoader.get_ceremony_context(root_dir, ceremony="1_epic_refinement", include_dev_rules=False)
