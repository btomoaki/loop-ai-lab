import os
import sys
import re
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

    def confirm_comprehensive_epic_review_gate(self, epics: list, auto_approve: bool = False) -> bool:
        """セレモニー 1 (overall_debate) 直後の総合的レビューゲート"""
        print("\n" + "=" * 70)
        print("🔍 [Human Review Gate: 総合アーキテクチャ・エピック品質チェック]")
        print("  [1] 仕様適合性 : 仕様書（references/）の要件が網羅され、不要な独自解釈がないか？")
        print("  [2] シンプルさ : オーバーエンジニアリング（不要な抽象化・過剰パターン）がないか？")
        print("  [3] 責務の境界 : Clean Architecture / プラットフォーム境界（インフラ責務の混入）が健全か？")
        print("  [4] モデル負荷 : 下流LLMが1スプリントで実装・テスト完結できる適切な粒度か？")
        print("  [5] ガバナンス : セキュリティ・コンテナ非特権・標準規約に反していないか？")
        print("=" * 70, flush=True)

        # 自動承認フラグまたは非対話環境の判定
        is_interactive = sys.stdin.isatty() and not os.getenv("CI") and not os.getenv("DEBIAN_FRONTEND") == "noninteractive"
        if auto_approve or not is_interactive or os.getenv("AUTO_APPROVE") == "1":
            print("⏩ [Review Gate] Auto-approved (--yes / non-interactive environment). Proceeding to Ceremony 2.\n", flush=True)
            return True

        try:
            prompt_msg = "👉 上記エピック分割・総合設計を承認し、Ceremony 2 (詳細バックログ分解) を開始しますか？ [y/N]: "
            user_input = input(prompt_msg).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n⏸️ [Review Gate] 入力が中断されました。安全に終了します。", flush=True)
            sys.exit(0)

        if user_input in ["y", "yes"]:
            print("🎉 [Review Gate] エピック分割が承認されました。Ceremony 2 を開始します！\n", flush=True)
            return True
        else:
            print(
                "\n⏸️ [Review Gate] ユーザー確認により一時停止しました。\n"
                "   state/.evaluator/ceremony_1/overall_debate_log.md または references/ を確認・修正後、\n"
                "   再度 'python runner/main.py run --phase refinement' を実行してください。\n",
                flush=True
            )
            sys.exit(0)

    def run_epic_refinement_phase(self, auto_approve: bool = False) -> str:
        """セレモニー 1 (エピック抽出ディベート) を実行し、ディベートログを返す。"""
        overall_debate_log = self.epic_engine.run_epic_refinement()

        # ⚖️ 3者独立レビュー判定（コスト・技術・責任の分離判断）
        self.epic_engine.review_tripartite_governance(overall_debate_log)

        epics = self.epic_engine.extract_epics_from_log(overall_debate_log)
        if not epics:
            raise RuntimeError("❌ [RefinementEngine] Zero epics extracted from Ceremony 1 log!")

        print("\n" + "=" * 50)
        print("📋 [Ceremony 1 Complete] Actionable Epics Summary")
        print("=" * 50)
        for idx, ep in enumerate(epics, 1):
            print(f"  {idx}. {ep['title']}\n     Scope: {ep['scope']}")
        print("=" * 50 + "\n")

        # ⏸️ overall_debate 直後の総合的レビューゲート
        self.confirm_comprehensive_epic_review_gate(epics, auto_approve=auto_approve)

        return overall_debate_log

    def run_refinement(self, auto_approve: bool = False) -> bool:
        # 1. セレモニー 1: 全体エピックリファインメント & 総合レビューゲート
        overall_debate_log = self.run_epic_refinement_phase(auto_approve=auto_approve)

        # 2. セレモニー 2: スプリントバックログリファインメント
        return self.sprint_refinement_engine.run_sprint_refinement(overall_debate_log)
