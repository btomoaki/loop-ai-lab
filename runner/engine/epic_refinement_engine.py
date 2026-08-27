import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser
from runner.utils.context_loader import ContextLoader
from runner.adapters.llm_adapter import LLMAdapterFactory


class EpicRefinementEngine:
    """【セレモニー 1】全体アーキテクチャ・エピックリファインメントエンジン (安定統合版)"""

    def __init__(self, root_dir: Path, config: ProjectConfig = None):
        self.root_dir = root_dir
        self.config = config or ProjectConfig.load(root_dir)
        self.init_dir = root_dir / "state" / "initiatives"
        self.eval_dir = root_dir / "state" / ".evaluator"
        self.status_file = root_dir / "state" / "status.md"

        self.init_dir.mkdir(parents=True, exist_ok=True)
        self.eval_dir.mkdir(parents=True, exist_ok=True)

        refinement_provider = self._get_refinement_provider()
        print(f"🧠 [EpicRefinementEngine] Using Provider '{refinement_provider}' for Ceremony 1.", flush=True)
        self.refinement_agent = LLMAdapterFactory.get_adapter(provider=refinement_provider)

    def _get_refinement_provider(self) -> str:
        config_file = self.root_dir / "config.yaml"
        if config_file.exists():
            try:
                data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
                return data.get("DEFAULT_LLM_PROVIDER", "local")
            except Exception:
                pass
        return "local"

    def update_status_dashboard(self, status_message: str):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dashboard_content = f"""# 📌 Loop AI Lab - リアルタイム Scrum 進行状況ダッシュボード

- **現在実行中のフェーズ**: 🌐 【セレモニー 1】全体アーキテクチャ・エピックリファインメント
- **ステータス**: {status_message}
- **最終更新日時**: `{now_str}`

---

## 📊 全エピック進捗ステータス
- 🌐 全体仕様解釈 & 多ペルソナディベート実行中...
"""
        CodeParser.atomic_write_text(self.status_file, dashboard_content)
        print(f"📊 [Status Dashboard] Updated state/status.md (Ceremony 1: {status_message})", flush=True)

    def extract_epics_from_log(self, debate_log: str) -> list:
        epics = []
        pattern = r"(?:^|\n)##\s*2\.\s*Epic\s*Breakdown.*?\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, debate_log, re.DOTALL | re.IGNORECASE)
        lines = match.group(1).strip().splitlines() if match else debate_log.splitlines()

        for line in lines:
            m_epic = re.search(r"^\s*-\s*\*\*([^\*]+)\*\*:\s*(.*)", line)
            if m_epic:
                epics.append({
                    "title": m_epic.group(1).strip(),
                    "scope": m_epic.group(2).strip()
                })
        return epics

    def run_epic_refinement(self, max_retries: int = 3) -> str:
        overall_debate_file = self.eval_dir / "overall_debate_log.md"
        
        if overall_debate_file.exists():
            content = overall_debate_file.read_text(encoding="utf-8").strip()
            if len(content) > 500:
                print("⏯️ [EpicRefinementEngine 中断再開] 全体ディベートログ (overall_debate_log.md) が存在するためスキップします。")
                return content

        print("🌐 [Ceremony 1: Epic Refinement] Overall Multi-Persona Debate...", flush=True)
        self.update_status_dashboard("💬 全ペルソナによる全体アーキテクチャディベート中...")
        
        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="1_epic_refinement", include_dev_rules=True)
        inst_file_rel = "agents/1_epic_refinement/epic_refinement_planner.md"

        prompt = (
            f"[TASK: CEREMONY 1 EPIC REFINEMENT DEBATE]\n"
            f"=== 1. EXECUTION INSTRUCTIONS ===\n- {inst_file_rel}\n\n"
            f"=== 2. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
            f"=== 3. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
            f"=== 4. MULTI-PERSONA DEFINITIONS ===\n{refs['personas']}\n\n"
            "【INSTRUCTION】\n"
            "Generate the complete Ceremony 1 Overall Architecture Debate Log.\n"
            "Structure your output as follows:\n"
            "# 🌐 Overall System Architecture & Epic Refinement Debate Log\n\n"
            "## 1. Multi-Persona Discussion\n"
            "(Substantial debate between participating personas analyzing specifications, boundaries, and costs)\n\n"
            "## 2. Epic Breakdown\n"
            "- **Epic 1 <Title>**: <Scope description>\n"
            "- **Epic 2 <Title>**: <Scope description>\n"
        )
        
        actual_prompt_file = self.eval_dir / "actual_ceremony_1_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)

        for attempt in range(1, max_retries + 1):
            print(f"🔍 [Ceremony 1] Requesting Overall Architecture Debate Log from LLM (Attempt {attempt}/{max_retries})...", flush=True)
            llm_raw_response = self.refinement_agent.generate_text(prompt)
            
            prefix = "# 🌐 Overall System Architecture & Epic Refinement Debate Log\n\n"
            if llm_raw_response and not llm_raw_response.strip().startswith("#"):
                overall_debate_log = prefix + llm_raw_response.strip()
            else:
                overall_debate_log = (llm_raw_response or "").strip()

            epics = self.extract_epics_from_log(overall_debate_log)
            if len(overall_debate_log) >= 500 and len(epics) >= 2:
                CodeParser.atomic_write_text(overall_debate_file, overall_debate_log)
                print(f"📝 [Ceremony 1 Complete] Successfully generated debate log with {len(epics)} Epics to {overall_debate_file.relative_to(self.root_dir)}")
                return overall_debate_log
            
            print(f"⚠️ [Ceremony 1 Warning] Attempt {attempt} returned insufficient content or failed epic extraction (Length: {len(overall_debate_log)}, Epics: {len(epics)}). Retrying...")

        raise RuntimeError(f"❌ [Ceremony 1 Failed] Failed to generate valid overall architecture debate log after {max_retries} attempts!")
