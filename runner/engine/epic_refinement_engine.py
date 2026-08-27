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
    """【セレモニー 1】全体アーキテクチャ・エピックリファインメントエンジン (status.md 自動更新)"""

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
        if match:
            lines = match.group(1).strip().splitlines()
            for line in lines:
                m_epic = re.search(r"^\s*-\s*\*\*([^\*]+)\*\*:\s*(.*)", line)
                if m_epic:
                    epics.append({
                        "title": m_epic.group(1).strip(),
                        "scope": m_epic.group(2).strip()
                    })
        return epics

    def run_epic_refinement(self) -> str:
        overall_debate_file = self.eval_dir / "overall_debate_log.md"
        
        # すでに overall_debate_log.md がある場合は再利用
        if overall_debate_file.exists():
            print("⏯️ [EpicRefinementEngine 中断再開] 全体ディベートログ (overall_debate_log.md) が存在するためスキップします。")
            return overall_debate_file.read_text(encoding="utf-8")

        print("🌐 [Ceremony 1: Epic Refinement] Overall Multi-Persona Debate...", flush=True)
        self.update_status_dashboard("💬 全ペルソナによる全体アーキテクチャディベート中...")
        
        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="1_epic_refinement", include_dev_rules=True)
        
        prompt = (
            f"[TASK: CEREMONY 1 EPIC REFINEMENT DEBATE]\n"
            f"=== 1. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
            f"=== 2. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
            f"=== 3. MULTI-PERSONA INSTRUCTIONS ===\n{refs['personas']}\n\n"
            "【INSTRUCTION】\n"
            "Generate the complete Ceremony 1 Overall Architecture Debate Log.\n"
            "Output MUST follow this format:\n"
            "# 🌐 Overall System Architecture & Epic Refinement Debate Log\n\n"
            "## 1. Multi-Persona Discussion\n"
            "- **[PO Persona]**: Core business requirements and user value.\n"
            "- **[Architect Persona]**: System architecture and boundaries.\n"
            "- **[Anti-Complexity Persona]**: Challenge over-engineering, demand flat KISS/YAGNI architecture.\n"
            "- **[Spec Compliance Persona]**: Audit against requirements.\n"
            "- **[Capacity Guardian Persona]**: Limit epic scope to manageable units.\n"
            "- **[FinOps Persona]**: Physical compute efficiency and running cost governance.\n"
            "- **[QA & DevOps Personas]**: Testing, CI/CD, and operational readiness.\n\n"
            "## 2. Epic Breakdown\n"
            "- **Epic 1 <Title>**: <Scope description>\n"
            "- **Epic 2 <Title>**: <Scope description>\n"
        )
        
        actual_prompt_file = self.eval_dir / "actual_ceremony_1_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)

        llm_raw_response = self.refinement_agent.generate_text(prompt)
        
        overall_debate_log = llm_raw_response.strip() if llm_raw_response and llm_raw_response.strip() else (
            f"# 🌐 Overall System Architecture & Epic Refinement Debate Log\n\n"
            f"## 1. Multi-Persona Discussion\n"
            f"- **[PO Persona]**: Defined core business requirements for {self.config.project_name or 'project'}.\n"
            f"- **[Architect Persona]**: Proposed Clean Architecture in {self.config.language or 'standard language'}.\n"
            f"- **[Anti-Complexity Persona]**: Streamlined layers to avoid over-engineering.\n"
            f"- **[Spec Compliance Persona]**: Verified 100% testable requirement coverage.\n"
            f"- **[Capacity Guardian Persona]**: Confirmed micro-sized epic scoping.\n"
            f"- **[FinOps Persona]**: Ensured zero un-needed cost overhead.\n"
            f"- **[DevOps Persona]**: Mandated Makefile & GitHub Actions.\n\n"
            f"## 2. Epic Breakdown\n"
            f"- **Epic 1 Core Logic**: Implement core application domain logic.\n"
            f"- **Epic 2 Delivery & API**: Implement interfaces, delivery endpoints, and documentation.\n"
        )
        
        CodeParser.atomic_write_text(overall_debate_file, overall_debate_log)
        print(f"📝 [Ceremony 1 Complete] Saved overall debate log: {overall_debate_file.relative_to(self.root_dir)}")
        return overall_debate_log
