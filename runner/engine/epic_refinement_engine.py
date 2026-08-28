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
    """【セレモニー 1】全体アーキテクチャ・ディベート & エピックリファインメントエンジン (AI-to-AI 適応型)"""

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
- 🌐 {status_message}
"""
        CodeParser.atomic_write_text(self.status_file, dashboard_content)
        print(f"📊 [Status Dashboard] Updated state/status.md ({status_message})", flush=True)

    def run_epic_refinement(self) -> str:
        overall_debate_file = self.eval_dir / "overall_debate_log.md"
        
        if overall_debate_file.exists():
            content = overall_debate_file.read_text(encoding="utf-8").strip()
            if len(content) > 500:
                print("⏯️ [EpicRefinementEngine 中断再開] 全体ディベートログ (overall_debate_log.md) が存在するためスキップします。")
                return content

        print("🌐 [Ceremony 1: Epic Refinement] Conducting AI-to-AI Architecture Debate & Epic Breakdown...", flush=True)
        self.update_status_dashboard("💬 全ペルソナによる全体アーキテクチャディベート中...")

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="1_epic_refinement", include_dev_rules=True, config=self.config)
        inst_file_rel = "agents/1_epic_refinement/epic_refinement_planner.md"

        prompt = (
            f"[INST]\n"
            f"[TASK: CEREMONY 1 EPIC REFINEMENT DEBATE]\n"
            f"Recursively read and analyze all referenced files and specifications listed below.\n\n"
            f"=== 1. EXECUTION INSTRUCTIONS ===\n- {inst_file_rel}\n\n"
            f"=== 2. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
            f"=== 3. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
            f"=== 4. MULTI-PERSONA INSTRUCTIONS ===\n{refs['personas']}\n\n"
            f"=== 5. TARGET DEVELOPER AGENT PROFILE (DOWNSTREAM CODER) ===\n{refs['target_agent']}\n\n"
            "Output MUST follow this format:\n"
            "# 🌐 Overall System Architecture & Epic Refinement Debate Log\n\n"
            "## 1. Multi-Persona Discussion\n"
            "- **[PO Persona]**: Core business requirements and user value.\n"
            "- **[Architect Persona]**: System architecture and boundaries.\n"
            "- **[Anti-Complexity Persona]**: Challenge over-engineering, demand flat KISS/YAGNI architecture.\n"
            "- **[Spec Compliance Persona]**: Audit against requirements.\n"
            "- **[Capacity Guardian Persona]**: Limit epic scope to manageable units for downstream coder.\n"
            "- **[FinOps Persona]**: Physical compute efficiency and running cost governance.\n"
            "- **[QA & DevOps Personas]**: Testing, CI/CD, and operational readiness.\n\n"
            "## 2. Epic Breakdown\n"
            "- **Epic 1 <Title>**: <Scope description with explicit I/O contracts>\n"
            "- **Epic 2 <Title>**: <Scope description with explicit I/O contracts>\n"
            "[/INST]\n"
        )

        actual_prompt_file = self.eval_dir / "actual_ceremony_1_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)

        print("🔍 [Ceremony 1] Requesting Overall Architecture Debate Log from LLM...", flush=True)
        llm_raw_response = self.refinement_agent.generate_text(prompt)
        overall_debate_log = (llm_raw_response or "").strip()

        if len(overall_debate_log) >= 500 and "## 1. Multi-Persona Discussion" in overall_debate_log:
            CodeParser.atomic_write_text(overall_debate_file, overall_debate_log)
            print(f"📝 [Ceremony 1 Complete] Successfully generated and saved debate log to {overall_debate_file.relative_to(self.root_dir)}")
            return overall_debate_log

        CodeParser.atomic_write_text(overall_debate_file, overall_debate_log)
        print(f"\n⚠️ [Ceremony 1 Halted] Insufficient debate content ({len(overall_debate_log)} chars). Saved raw output to {overall_debate_file.relative_to(self.root_dir)}")
        raise RuntimeError("❌ [Ceremony 1 Failed] Failed to generate valid overall architecture debate log on 1st attempt.")

    def extract_epics_from_log(self, debate_log: str) -> list:
        epics = []
        
        # 1. Try extracting YAML codeblock if present
        raw_yaml_match = re.search(r"```(?:yaml)?\n(.*?)```", debate_log, re.DOTALL)
        if raw_yaml_match:
            try:
                parsed = yaml.safe_load(raw_yaml_match.group(1).strip()) or {}
                raw_epics = parsed.get("epics", []) if isinstance(parsed, dict) else (parsed if isinstance(parsed, list) else [])
                for e in raw_epics:
                    if isinstance(e, dict):
                        t = e.get("title") or e.get("name") or ""
                        s = e.get("scope") or e.get("description") or ""
                        if t.strip():
                            epics.append({"id": e.get("id", f"EPIC-{len(epics)+1}"), "title": t.strip(), "scope": s.strip()})
                if epics:
                    return epics
            except Exception:
                pass

        # 2. Extract Section 2 content
        pattern = r"(?:^|\n)##\s*2\.\s*Epic\s*Breakdown.*?\n(.*)"
        match = re.search(pattern, debate_log, re.DOTALL | re.IGNORECASE)
        section_text = match.group(1) if match else debate_log

        # 3. Match H3/H4 headers (e.g. ### **Epic 1: Prometheus Data Ingestor** or ### Epic 1 ...)
        h3_matches = list(re.finditer(r"(?:^|\n)###+\s*\*{0,2}(Epic\s*\d+[^:\n*]*[:\s\-]+[^\n*]+)\*{0,2}(.*?)(?=\n###|\Z)", section_text, re.DOTALL | re.IGNORECASE))
        if h3_matches:
            for m in h3_matches:
                t = m.group(1).strip().strip("*").strip()
                s = m.group(2).strip()
                if t and not t.lower().startswith("epic 1 <title>"):
                    epics.append({
                        "id": f"EPIC-{len(epics)+1}",
                        "title": t,
                        "scope": s
                    })
            if epics:
                return epics

        # 4. Match Markdown list items (- **Epic 1 <Title>**: <Scope>)
        lines = section_text.splitlines()
        for line in lines:
            m_epic = re.search(r"^\s*-\s*\*\*([^\*]+)\*\*:\s*(.*)", line)
            if m_epic:
                t = m_epic.group(1).strip()
                s = m_epic.group(2).strip()
                if t and not t.startswith("[") and not t.lower().startswith("epic 1 <title>"):
                    epics.append({
                        "id": f"EPIC-{len(epics)+1}",
                        "title": t,
                        "scope": s
                    })

        if not epics:
            raise RuntimeError("❌ [Epic Extraction Failed] Could not extract any epics from debate log!")
        return epics
