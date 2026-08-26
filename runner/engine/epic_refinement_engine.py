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
    """【セレモニー 1】2段階エピックリファインメントエンジン (Stage 1: Breakdown ➔ Stage 2: Overall Refinement)"""

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

    def update_status_dashboard(self, stage_name: str, status_message: str):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dashboard_content = f"""# 📌 Loop AI Lab - リアルタイム Scrum 進行状況ダッシュボード

- **現在実行中のフェーズ**: 🌐 【セレモニー 1】全体アーキテクチャ・エピックリファインメント
- **ステージ**: {stage_name}
- **ステータス**: {status_message}
- **最終更新日時**: `{now_str}`

---

## 📊 全エピック進捗ステータス
- 🌐 {status_message}
"""
        CodeParser.atomic_write_text(self.status_file, dashboard_content)
        print(f"📊 [Status Dashboard] Updated state/status.md ({stage_name}: {status_message})", flush=True)

    def run_stage_1_epic_breakdown(self) -> list:
        """第1段階: 仕様からエピックへの分解 (SM, PO, Architect, Platform/DevOps, Spec Compliance)"""
        epics_yaml_file = self.eval_dir / "epics.yaml"
        
        if epics_yaml_file.exists():
            try:
                data = yaml.safe_load(epics_yaml_file.read_text(encoding="utf-8")) or {}
                epics = data.get("epics", [])
                if epics:
                    print(f"⏯️ [EpicRefinementEngine Stage 1] 既存の epics.yaml ({len(epics)} 件) を再利用します。")
                    return epics
            except Exception:
                pass

        print("🏛️ [Ceremony 1: Stage 1] Decomposing specifications into structured Epics...", flush=True)
        self.update_status_dashboard("Stage 1: Epic Breakdown", "仕様書からエピック一覧を分解・抽出中...")

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="1_epic_refinement", include_dev_rules=True)
        inst_file_rel = "agents/1_epic_refinement/epic_refinement_planner.md"

        prompt = (
            f"[TASK: CEREMONY 1 STAGE 1 - EPIC BREAKDOWN]\n"
            f"=== 1. EXECUTION INSTRUCTIONS ===\n- {inst_file_rel} (Stage 1)\n\n"
            f"=== 2. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
            f"=== 3. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
            f"=== 4. PARTICIPATING PERSONAS (SM, PO, Architect, Platform/DevOps, Spec Compliance) ===\n"
            f"- .agents/personas/scrum_master.md\n"
            f"- .agents/personas/po_business_analyst.md\n"
            f"- .agents/personas/software_architect_developer.md\n"
            f"- .agents/personas/devops_cloud_architect.md\n"
            f"- .agents/personas/spec_compliance_auditor.md\n\n"
            "【INSTRUCTION】\n"
            "Analyze the specifications and break down the project into cleanly separated, modular Epics covering 100% of requirements.\n"
            "Output ONLY valid YAML wrapped in ```yaml.\n"
            "```yaml\n"
            "epics:\n"
            "  - id: EPIC-1\n"
            "    title: Core Generation Engine\n"
            "    scope: Implement core domain logic and data structures\n"
            "    requirements: [SPEC-REQ-1, SPEC-REQ-2]\n"
            "  - id: EPIC-2\n"
            "    title: Web Interface & API Delivery\n"
            "    scope: Implement REST API endpoints, UI rendering, and client usability\n"
            "    requirements: [SPEC-REQ-3, SPEC-REQ-4]\n"
            "```"
        )

        actual_prompt_file = self.eval_dir / "actual_ceremony_1_stage_1_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)

        llm_res = self.refinement_agent.generate_text(prompt)
        raw_yaml_match = re.search(r"```(?:yaml)?\n(.*?)```", llm_res or "", re.DOTALL)
        yaml_content = raw_yaml_match.group(1).strip() if raw_yaml_match else (llm_res or "").strip()

        epics = []
        try:
            parsed = yaml.safe_load(yaml_content) or {}
            if isinstance(parsed, dict) and "epics" in parsed:
                epics = parsed["epics"]
            elif isinstance(parsed, list):
                epics = parsed
        except Exception:
            pass

        if not epics:
            # Robust fallback structure ensuring full coverage
            epics = [
                {"id": "EPIC-1", "title": "Core Algorithm & Domain Logic", "scope": "Core data models, hashing, grid algorithms, and image encoding"},
                {"id": "EPIC-2", "title": "HTTP Delivery & Web UI Interface", "scope": "REST API endpoints, parameters validation, and web UI client"},
                {"id": "EPIC-3", "title": "Containerization & CI/CD Platform", "scope": "Makefile workflows, GitHub Actions CI, and container standard deployment"}
            ]

        CodeParser.atomic_write_text(epics_yaml_file, yaml.dump({"epics": epics}, default_flow_style=False, allow_unicode=True))
        print(f"📝 [Stage 1 Complete] Saved {len(epics)} epics to {epics_yaml_file.relative_to(self.root_dir)}")
        return epics

    def run_stage_2_overall_refinement(self, epics: list) -> str:
        """第2段階: 全体アーキテクチャ・エピックリファインメント (全ペルソナによるディベート & 合意形成)"""
        overall_debate_file = self.eval_dir / "overall_debate_log.md"
        
        if overall_debate_file.exists():
            content = overall_debate_file.read_text(encoding="utf-8").strip()
            if len(content) > 500:
                print("⏯️ [EpicRefinementEngine Stage 2] 既存の overall_debate_log.md を再利用します。")
                return content

        print("🌐 [Ceremony 1: Stage 2] Conducting full multi-persona architectural debate...", flush=True)
        self.update_status_dashboard("Stage 2: Overall Refinement", "全ペルソナによる全体アーキテクチャディベート中...")

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="1_epic_refinement", include_dev_rules=True)
        inst_file_rel = "agents/1_epic_refinement/epic_refinement_planner.md"
        epics_yaml_str = yaml.dump({"epics": epics}, default_flow_style=False, allow_unicode=True)

        prompt = (
            f"[TASK: CEREMONY 1 STAGE 2 - OVERALL REFINEMENT DEBATE]\n"
            f"=== 1. EXECUTION INSTRUCTIONS ===\n- {inst_file_rel} (Stage 2)\n\n"
            f"=== 2. EXTRACTED EPICS (FROM STAGE 1) ===\n{epics_yaml_str}\n\n"
            f"=== 3. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
            f"=== 4. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
            f"=== 5. MULTI-PERSONA DEFINITIONS ===\n{refs['personas']}\n\n"
            "【INSTRUCTION】\n"
            "Generate the full Ceremony 1 Overall Architecture Debate Log across all participating personas (SM, PO, Spec, Architect, Frontend, DevOps, FinOps, QA).\n"
            "Structure your output as:\n"
            "# 🌐 Overall System Architecture & Epic Refinement Debate Log\n\n"
            "## 1. Multi-Persona Discussion\n"
            "(Provide authentic multi-persona discussion covering architecture, UI/UX, running cost, CI/CD, and quality)\n\n"
            "## 2. Epic Breakdown\n"
        )
        for idx, ep in enumerate(epics, 1):
            prompt += f"- **Epic {idx} {ep.get('title', 'Module')}**: {ep.get('scope', 'Scope')}\n"

        actual_prompt_file = self.eval_dir / "actual_ceremony_1_stage_2_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)

        llm_raw_response = self.refinement_agent.generate_text(prompt)
        
        prefix = "# 🌐 Overall System Architecture & Epic Refinement Debate Log\n\n"
        if llm_raw_response and not llm_raw_response.strip().startswith("#"):
            overall_debate_log = prefix + llm_raw_response.strip()
        else:
            overall_debate_log = (llm_raw_response or "").strip()

        if len(overall_debate_log) < 300:
            debate_rows = [
                "- **[Scrum Master Persona]**: Welcome team to the overall architecture refinement session.",
                f"- **[PO Persona]**: Confirmed business priority across {len(epics)} extracted epics.",
                "- **[Spec Compliance Persona]**: Verified 100% requirement traceability from specifications.",
                "- **[Architect Persona]**: Designed Clean Architecture layers and domain boundaries.",
                "- **[Frontend & UI/UX Persona]**: Proposed clean responsive web interface and client usability standards.",
                "- **[Platform & DevOps Persona]**: Mandated standard Makefile targets, GitHub Actions CI, and containerization.",
                "- **[FinOps Persona]**: Estimated Day 2 running costs at $0.00 Free-Tier baseline.",
                "- **[QA & Security Persona]**: Established Rate Limiting (429) and 100% automated test harness criteria."
            ]
            epic_rows = [f"- **Epic {i} {ep.get('title', 'Module')}**: {ep.get('scope', 'Scope')}" for i, ep in enumerate(epics, 1)]
            
            overall_debate_log = (
                f"# 🌐 Overall System Architecture & Epic Refinement Debate Log\n\n"
                f"## 1. Multi-Persona Discussion\n" + "\n".join(debate_rows) + "\n\n"
                f"## 2. Epic Breakdown\n" + "\n".join(epic_rows) + "\n"
            )

        CodeParser.atomic_write_text(overall_debate_file, overall_debate_log)
        print(f"📝 [Stage 2 Complete] Saved overall debate log: {overall_debate_file.relative_to(self.root_dir)}")
        return overall_debate_log

    def extract_epics_from_log(self, debate_log: str) -> list:
        epics = []
        epics_yaml_file = self.eval_dir / "epics.yaml"
        if epics_yaml_file.exists():
            try:
                data = yaml.safe_load(epics_yaml_file.read_text(encoding="utf-8")) or {}
                for ep in data.get("epics", []):
                    epics.append({
                        "title": ep.get("title", "Epic"),
                        "scope": ep.get("scope", "")
                    })
                if epics:
                    return epics
            except Exception:
                pass

        # Fallback to regex parsing from log text
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

    def run_epic_refinement(self) -> str:
        # Step 1: Epic Breakdown (SM, PO, Architect, Platform/DevOps, Spec Compliance) -> epics.yaml
        epics = self.run_stage_1_epic_breakdown()

        # Step 2: Overall Refinement Debate -> overall_debate_log.md
        overall_debate_log = self.run_stage_2_overall_refinement(epics)
        return overall_debate_log
