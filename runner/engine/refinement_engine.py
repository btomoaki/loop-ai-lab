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

    def run_refinement(self) -> bool:
        # 1. セレモニー 1: 全体エピックリファインメント
        overall_debate_log = self.epic_engine.run_epic_refinement()

        # 2. 全体ディベートログから動的エピック一覧を抽出
        dynamic_epics = self.epic_engine.extract_epics_from_overall_log(overall_debate_log)
        if not dynamic_epics:
            raise RuntimeError("❌ [RefinementEngine] Zero epics extracted from Ceremony 1 log!")

        # 3. セレモニー 2: スプリントバックログリファインメント
        return self.sprint_refinement_engine.run_sprint_refinement(dynamic_epics)
