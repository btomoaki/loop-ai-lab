import re
import yaml
from datetime import datetime
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser
from runner.utils.context_loader import ContextLoader
from runner.adapters.llm_adapter import LLMAdapterFactory


class EpicRefinementEngine:
    """【セレモニー 1】全体エピックリファインメントエンジン (status.md 更新機能付き)"""

    def __init__(self, root_dir: Path, config: ProjectConfig = None):
        self.root_dir = root_dir
        self.config = config or ProjectConfig.load(root_dir)
        self.eval_dir = root_dir / "state" / ".evaluator"
        self.status_file = root_dir / "state" / "status.md"
        self.eval_dir.mkdir(parents=True, exist_ok=True)

        refinement_provider = self._get_refinement_provider()
        self.refinement_agent = LLMAdapterFactory.get_adapter(provider=refinement_provider)

    def _get_refinement_provider(self) -> str:
        config_file = self.root_dir / "config.yaml"
        if config_file.exists():
            try:
                data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
                return data.get("REFINEMENT_PROVIDER", "gemini")
            except Exception:
                pass
        return "gemini"

    def update_status_dashboard(self, status_text: str):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"""# 📌 Loop AI Lab - リアルタイム Scrum 進行状況ダッシュボード

- **現在実行中のフェーズ**: 🌐 【セレモニー 1】全体アーキテクチャ・エピックリファインメント
- **ステータス**: {status_text}
- **最終更新日時**: `{now_str}`

---

## 📊 全エピック進捗ステータス
- 🌐 全体仕様解釈 & 多ペルソナディベート実行中...
"""
        CodeParser.atomic_write_text(self.status_file, content)

    def extract_epics_from_overall_log(self, debate_text: str) -> list:
        epics = []
        p1 = r'(?:#+|\-|\*|\d+\.)?\s*\*\*(epic_[a-zA-Z0-9_]+)\*\*[:\s]*(.*)'
        for m in re.finditer(p1, debate_text):
            e_dir = m.group(1).strip()
            title = e_dir.replace("_", " ").title()
            scope = m.group(2).strip().replace('`', '') or f"Scope for {e_dir}"
            epics.append((e_dir, title, scope, len(epics) + 1))

        if not epics:
            p2 = r'(epic_[a-zA-Z0-9_]+)[:\s]*(.*)'
            for m in re.finditer(p2, debate_text):
                e_dir = m.group(1).strip()
                title = e_dir.replace("_", " ").title()
                scope = m.group(2).strip().replace('`', '') or f"Scope for {e_dir}"
                epics.append((e_dir, title, scope, len(epics) + 1))

        return epics

    def run_epic_refinement(self) -> str:
        overall_log_path = self.eval_dir / "overall_debate_log.md"

        if overall_log_path.exists() and len(overall_log_path.read_text(encoding="utf-8").strip()) > 100:
            print(f"⏯️ [EpicRefinementEngine 中断再開] 全体ディベートログ (overall_debate_log.md) が存在するためスキップします。", flush=True)
            self.update_status_dashboard("⏯️ 全体ディベート完了 (ログ読み込み完了)")
            return overall_log_path.read_text(encoding="utf-8")

        print("🌐 [Ceremony 1: Epic Refinement] Overall Multi-Persona Debate...", flush=True)
        self.update_status_dashboard("💬 全10ペルソナによる全体アーキテクチャディベート中...")
        
        proj_name = self.config.project_name or "identicon-generator"
        lang = self.config.language or "Go"

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="1_epic_refinement", include_dev_rules=False)
        
        spec_files = list((self.root_dir / "references").glob("*")) if (self.root_dir / "references").exists() else []
        if not spec_files:
            raise RuntimeError("❌ [EpicRefinementEngine Alert] Missing Specification in references/! Halting pipeline.")

        prompt = (
            f"[SYSTEM INSTRUCTION: CEREMONY 1 OVERALL SYSTEM DEBATE - {proj_name}]\n"
            f"Target System & Language: {proj_name} ({lang} Clean Architecture)\n\n"
            f"=== 1. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
            f"=== 2. REPOSITORY RULES ===\n{refs['rules']}\n\n"
            f"=== 3. PARTICIPATING PERSONAS ===\n{refs['personas']}\n\n"
            "Analyze the specification with all participating personas strictly following the rules above.\n"
            "Dynamically classify single-responsibility Epics under section '## 3. Classified Actionable Epics List'.\n"
            "Required Naming Pattern:\n"
            "- **epic_1_feature_name**: Scope description directly derived from specification\n\n"
            "End with STATUS: OVERALL_DEBATE_PASSED (or STATUS: REQUIRES_SPEC_DECISION if trade-offs needed).\n\n"
            "# 🌐 Overall System Architecture Multi-Persona Debate Log\n\n"
            "## 1. System Goals & Specification Alignment\n"
            f"- Specification Target: {proj_name}\n"
        )

        actual_prompt_file = self.eval_dir / "actual_phase1_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)

        llm_raw_response = self.refinement_agent.generate_text(prompt)
        if not llm_raw_response or not llm_raw_response.strip():
            raise RuntimeError("❌ [EpicRefinementEngine] LLM returned an empty response! Halting pipeline.")

        llm_response = (
            "# 🌐 Overall System Architecture Multi-Persona Debate Log\n\n"
            "## 1. System Goals & Specification Alignment\n"
            f"- Specification Target: {proj_name}\n"
            + llm_raw_response
        )

        CodeParser.atomic_write_text(overall_log_path, llm_response)
        print(f"📝 [Ceremony 1 Complete] Saved overall debate log: {overall_log_path.relative_to(self.root_dir)}")

        if "REQUIRES_SPEC_DECISION" in llm_response:
            self.update_status_dashboard("⚖️ トレードオフ検出により安全停止中 (User Decision Required)")
            raise RuntimeError("⚖️ [EpicRefinementEngine Escalation] Trade-off detected! Alternatives proposed in overall_debate_log.md. Halting for user decision.")

        self.update_status_dashboard("✅ セレモニー 1 全体ディベート合格完了")
        return llm_response
