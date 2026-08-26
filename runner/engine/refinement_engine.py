from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.engine.epic_refinement_engine import EpicRefinementEngine
from runner.engine.sprint_refinement_engine import SprintRefinementEngine


class RefinementEngine:
    """Orchestrates Ceremony 1 (Epic Refinement) and Ceremony 2 (Sprint Refinement)."""

    def __init__(self, root_dir: Path, config: ProjectConfig = None):
        self.root_dir = root_dir
        self.config = config or ProjectConfig.load(root_dir)
        self.epic_engine = EpicRefinementEngine(self.root_dir, self.config)
        self.sprint_refinement_engine = SprintRefinementEngine(self.root_dir, self.config)

    def run_epic_refinement_phase(self) -> list:
        """セレモニー 1 (エピック抽出ディベート) を実行し、抽出されたエピック一覧を返す。"""
        overall_debate_log = self.epic_engine.run_epic_refinement()
        dynamic_epics = self.epic_engine.extract_epics_from_overall_log(overall_debate_log)
        if not dynamic_epics:
            raise RuntimeError("❌ [RefinementEngine] Zero epics extracted from Ceremony 1 log!")

        print("\n" + "=" * 50)
        print("📋 [Ceremony 1 Complete] Actionable Epics Summary")
        print("=" * 50)
        for e_dir, title, scope, idx in dynamic_epics:
            print(f"  {idx}. [{e_dir}] {title}\n     Scope: {scope}")
        print("=" * 50)
        print("⏸️ [Review Gate] Ceremony 1 complete. Epics extracted and ready for user review.")
        print("=" * 50 + "\n")

        return dynamic_epics

    def run_refinement(self) -> bool:
        # 1. セレモニー 1: 全体エピックリファインメント
        dynamic_epics = self.run_epic_refinement_phase()

        # 2. セレモニー 2: スプリントバックログリファインメント
        return self.sprint_refinement_engine.run_sprint_refinement(dynamic_epics)

