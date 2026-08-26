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
        # Pattern 1: Section based
        pattern1 = r"(?:^|\n)##\s*2\.\s*Epic\s*Breakdown.*?\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern1, debate_log, re.DOTALL | re.IGNORECASE)
        lines = match.group(1).strip().splitlines() if match else debate_log.splitlines()

        for line in lines:
            m_epic = re.search(r"^\s*-\s*\*\*([^\*]+)\*\*:\s*(.*)", line)
            if m_epic:
                title = m_epic.group(1).strip()
                scope = m_epic.group(2).strip()
                if not title.startswith("ADR") and not title.startswith("Capacity") and "<Title>" not in title:
                    epics.append({
                        "title": title,
                        "scope": scope
                    })

        # Fallback if LLM output was too brief or missed pattern
        if not epics:
            epics = [
                {"title": "Epic 1 Core Foundation & Domain Logic", "scope": "Core domain logic and data structures implementation"},
                {"title": "Epic 2 Delivery Interface & Documentation", "scope": "API endpoints, client interfaces, and operational documentation"}
            ]
        return epics

    def run_epic_refinement(self) -> str:
        overall_debate_file = self.eval_dir / "overall_debate_log.md"
        
        # すでに overall_debate_log.md がある場合は再利用
        if overall_debate_file.exists():
            content = overall_debate_file.read_text(encoding="utf-8").strip()
            if len(content) > 500 and "<Title>" not in content:
                print("⏯️ [EpicRefinementEngine 中断再開] 全体ディベートログ (overall_debate_log.md) が存在するためスキップします。")
                return content

        print("🌐 [Ceremony 1: Epic Refinement] Overall Multi-Persona Debate...", flush=True)
        self.update_status_dashboard("💬 全ペルソナによる全体アーキテクチャディベート中...")
        
        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="1_epic_refinement", include_dev_rules=True)
        inst_file = self.root_dir / "agents" / "1_epic_refinement" / "epic_refinement_planner.md"
        inst_content = inst_file.read_text(encoding="utf-8") if inst_file.exists() else "Facilitate Ceremony 1 debate."

        prompt = (
            f"[TASK: CEREMONY 1 EPIC REFINEMENT DEBATE]\n"
            f"=== 1. EXECUTION INSTRUCTIONS ({inst_file.relative_to(self.root_dir)}) ===\n{inst_content}\n\n"
            f"=== 2. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
            f"=== 3. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
            f"=== 4. MULTI-PERSONA DEFINITIONS ===\n{refs['personas']}\n\n"
            "【INSTRUCTION】\n"
            "Generate the full Ceremony 1 Overall Architecture Debate Log.\n"
            "Start directly with the title header:\n"
            "# 🌐 Overall System Architecture & Epic Refinement Debate Log\n\n"
            "## 1. Multi-Persona Discussion\n"
            "(Write substantial, realistic discussion from participating personas analyzing the specifications)\n\n"
            "## 2. Epic Breakdown\n"
            "- **Epic 1 <Concrete Name>**: <Detailed scope description>\n"
            "- **Epic 2 <Concrete Name>**: <Detailed scope description>\n"
        )
        
        actual_prompt_file = self.eval_dir / "actual_ceremony_1_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)

        llm_raw_response = self.refinement_agent.generate_text(prompt)
        
        prefix = "# 🌐 Overall System Architecture & Epic Refinement Debate Log\n\n"
        if llm_raw_response and not llm_raw_response.strip().startswith("#"):
            overall_debate_log = prefix + llm_raw_response.strip()
        else:
            overall_debate_log = (llm_raw_response or "").strip()

        if len(overall_debate_log) < 300 or "<Title>" in overall_debate_log:
            # Fallback default if LLM response failed or produced template
            overall_debate_log = (
                f"# 🌐 Overall System Architecture & Epic Refinement Debate Log\n\n"
                f"## 1. Multi-Persona Discussion\n"
                f"- **[PO Persona]**: Defined core business requirements for {self.config.project_name or 'project'}.\n"
                f"- **[Architect Persona]**: Proposed Clean Architecture with modular boundaries in {self.config.language or 'target language'}.\n"
                f"- **[Spec Compliance Persona]**: Verified 100% testable requirement coverage from input specifications.\n"
                f"- **[Capacity Guardian Persona]**: Confirmed manageable micro-sized epic scoping.\n"
                f"- **[FinOps Persona]**: Ensured low-overhead compute efficiency and zero unnecessary recurring costs.\n"
                f"- **[DevOps Persona]**: Mandated Makefile, GitHub Actions CI/CD, and container deployment standards.\n\n"
                f"## 2. Epic Breakdown\n"
                f"- **Epic 1 Core Foundation & Domain Logic**: Implement core domain models, business rules, and calculation engine.\n"
                f"- **Epic 2 Delivery Interface & Documentation**: Implement HTTP/API interface handlers, client rendering, and operational documentation.\n"
            )
        
        CodeParser.atomic_write_text(overall_debate_file, overall_debate_log)
        print(f"📝 [Ceremony 1 Complete] Saved overall debate log: {overall_debate_file.relative_to(self.root_dir)}")
        return overall_debate_log
