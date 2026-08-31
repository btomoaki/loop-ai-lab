import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser
from runner.utils.context_loader import ContextLoader
from runner.utils.backlog_splitter import BacklogSplitter
from runner.harness_generator import TestHarnessGenerator
from runner.adapters.llm_adapter import LLMAdapterFactory
from runner.engine.epic_refinement_engine import EpicRefinementEngine


def load_persona_mappings(root_dir: Path) -> tuple:
    alias_to_formal = {}
    formal_to_alias = {}
    personas_dir = root_dir / ".agents" / "personas"
    if personas_dir.exists():
        for md_file in personas_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        yaml_content = parts[1]
                        data = yaml.safe_load(yaml_content) or {}
                        alias = data.get("alias")
                        formal_name = data.get("formal_name")
                        if alias and formal_name:
                            alias_to_formal[alias.strip()] = formal_name.strip()
                            formal_to_alias[formal_name.strip()] = alias.strip()
            except Exception as e:
                print(f"  ⚠️ Failed to parse persona metadata from {md_file.name}: {e}")
    if not alias_to_formal:
        alias_to_formal = {
            "capacity": "[Capacity Guardian Persona]",
            "db": "[DB / Data Engineer Persona]",
            "devops": "[Platform & DevOps Persona]",
            "finops": "[FinOps & Cost Governance Persona]",
            "frontend": "[Frontend UI/UX Engineer Persona]",
            "po": "[PO Persona]",
            "anticomplexity": "[Pragmatic Anti-Complexity Engineer Persona]",
            "qa": "[QA Engineer Persona]",
            "scrummaster": "[Scrum Master Persona]",
            "securityauditor": "[Security Ethics Auditor Persona]",
            "architect": "[Software Architect Persona]",
            "specauditor": "[Spec Compliance Auditor Persona]"
        }
        for k, v in alias_to_formal.items():
            formal_to_alias[v] = k
    return alias_to_formal, formal_to_alias


def extract_personas_from_log_for_epic(overall_log: str, title: str, formal_to_alias: dict) -> list:
    match = re.search(r"Epic\s*\d+", title, re.IGNORECASE)
    epic_prefix = match.group(0) if match else title
    pattern = re.compile(rf"(?:^|\n)\s*-\s*\*\*{epic_prefix}[^*]*\*\*:(.*?)(?=(?:\n\s*-\s*\*\*Epic\s*\d+)|\Z)", re.DOTALL | re.IGNORECASE)
    m = pattern.search(overall_log)
    if m:
        section_content = m.group(1)
        pers_match = re.search(r"Target\s*Personas[^:]*:\s*\[?([^\]\n\r]+)\]?", section_content, re.IGNORECASE)
        if pers_match:
            raw_personas = pers_match.group(1).split(",")
            aliases = []
            for p in raw_personas:
                p_clean = p.strip().strip("'\"`[]*")
                if p_clean:
                    p_lower = p_clean.lower()
                    matched_formal = None
                    for formal in formal_to_alias.keys():
                        formal_clean = formal.strip("[]")
                        if formal_clean.lower() in p_lower or p_lower in formal_clean.lower():
                            matched_formal = formal
                            break
                    if matched_formal:
                        aliases.append(formal_to_alias[matched_formal])
                    else:
                        aliases.append(p_clean.lower())
            if aliases:
                return aliases
    return []


class SprintRefinementEngine:
    """【セレモニー 2】スプリントリファインメントエンジン (DoR AC 2個以下厳守 & Zero Spec Tampering & Capacity Guardian >=8 SP 分解ルール)"""

    def __init__(self, root_dir: Path, config: ProjectConfig = None):
        self.root_dir = root_dir
        self.config = config or ProjectConfig.load(root_dir)
        self.init_dir = root_dir / "state" / "initiatives"
        self.eval_dir = root_dir / "state" / ".evaluator"
        self.status_file = root_dir / "state" / "status.md"

        self.init_dir.mkdir(parents=True, exist_ok=True)
        self.eval_dir.mkdir(parents=True, exist_ok=True)

        refinement_provider = self._get_refinement_provider()
        print(f"🧠 [SprintRefinementEngine] Using Provider '{refinement_provider}' for Ceremony 2.", flush=True)
        self.refinement_agent = LLMAdapterFactory.get_adapter(provider=refinement_provider)

        print("🧠 [SprintRefinementEngine] Using Provider 'gemini' for Independent Final Audits.", flush=True)
        self.gemini_audit_agent = LLMAdapterFactory.get_adapter(provider="gemini")
        self.alias_to_formal, self.formal_to_alias = load_persona_mappings(self.root_dir)

    def _get_refinement_provider(self) -> str:
        # project_config.refinement_provider (llama_cpp / local) を最優先で使用
        if hasattr(self, "config") and self.config and self.config.refinement_provider:
            return self.config.refinement_provider

        config_file = self.root_dir / "config.yaml"
        if config_file.exists():
            try:
                data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
                return data.get("REFINEMENT_PROVIDER", data.get("DEFAULT_LLM_PROVIDER", "gemini"))
            except Exception:
                pass
        return "gemini"

    def update_status_dashboard(self, epic_name: str, status_msg: str = "バックログ分解およびテストハーネス生成中..."):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dashboard_content = f"""# 📌 Loop AI Lab - リアルタイム Scrum 進行状況ダッシュボード

- **現在実行中のフェーズ**: ⚙️ 【セレモニー 2】スプリントバックログ・リファインメント
- **対象エピック**: `{epic_name}`
- **ステータス**: {status_msg}
- **最終更新日時**: `{now_str}`

---

## 📊 全エピック進捗ステータス
- ⚙️ {epic_name} ({status_msg})
"""
        CodeParser.atomic_write_text(self.status_file, dashboard_content)
        print(f"📊 [Status Dashboard] Updated state/status.md ({epic_name}: {status_msg})", flush=True)

    def _get_ceremony_retrospective(self) -> str:
        retro_file = self.eval_dir / "retrospective" / "ceremony.md"
        if retro_file.exists():
            try:
                content = retro_file.read_text(encoding="utf-8").strip()
                if content:
                    return f"🚨 CRITICAL SCUM CEREMONY RETROSPECTIVE (LESSONS LEARNED - MUST ADHERE):\n{content}\n"
            except Exception:
                pass
        return ""

    def run_sprint_refinement_for_epic(self, epic_dir: Path, title: str, scope: str, required_personas: list, epic_idx: int, previous_audit_feedback: str = ""):
        debate_file = epic_dir / "debate_log.md"
        backlog_file = epic_dir / "epic_backlog.yaml"

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="2_sprint_refinement", include_dev_rules=True, config=self.config)
        inst_file_rel = "agents/2_sprint_refinement/sprint_refinement_planner.md"
        
        retro_content = self._get_ceremony_retrospective()
        if previous_audit_feedback:
            retro_content += f"\n🚨 PREVIOUS AUDIT VETO FEEDBACK (MUST FIX IN THIS RETRY):\n{previous_audit_feedback}\n"

        required_personas_formal = []
        for p in required_personas:
            p_clean = p.strip().lower()
            if p_clean in self.alias_to_formal:
                required_personas_formal.append(self.alias_to_formal[p_clean])
            else:
                matched = None
                for formal in self.alias_to_formal.values():
                    if p_clean in formal.lower() or formal.lower() in p_clean:
                        matched = formal
                        break
                if matched:
                    required_personas_formal.append(matched)
                else:
                    required_personas_formal.append(p)

        filtered_personas_instruction = ""
        if "personas" in refs:
            persona_blocks = refs["personas"].split("\n\n")
            active_persona_blocks = []
            for block in persona_blocks:
                for p in required_personas_formal:
                    p_clean = p.strip("[]")
                    if p_clean.lower() in block.lower():
                        active_persona_blocks.append(block)
                        break
            filtered_personas_instruction = "\n\n".join(active_persona_blocks)
        else:
            filtered_personas_instruction = refs.get("personas", "")

        persona_format_lines = []
        for p_formal in required_personas_formal:
            p_f_lower = p_formal.lower()
            if "scrum master" in p_f_lower:
                persona_format_lines.append("- **[Scrum Master Persona]**: Facilitates the session, validates task sequencing, and establishes sprint DoD.")
            elif "software architect" in p_f_lower or "architect" in p_f_lower:
                persona_format_lines.append("- **[Software Architect Persona]**: Micro-task package structure, domain interfaces, and pure function boundaries using Go standard library.")
            elif "frontend" in p_f_lower:
                persona_format_lines.append("- **[Frontend UI/UX Engineer Persona]**: Web UI components adhering strictly to specifications (No unrequested heavy frameworks).")
            elif "db / data" in p_f_lower or "database" in p_f_lower or "db" in p_f_lower:
                persona_format_lines.append("- **[DB / Data Engineer Persona]**: Data structures and persistence constraints (stateless).")
            elif "platform" in p_f_lower or "devops" in p_f_lower:
                persona_format_lines.append("- **[Platform & DevOps Persona]**: Dockerfile (non-root UID 65532), Makefile, and Cloud Run runtime execution.")
            elif "qa engineer" in p_f_lower or "quality assurance" in p_f_lower or "qa" in p_f_lower:
                persona_format_lines.append("- **[QA Engineer Persona]**: TDD unit test suites, edge cases, and automated verify commands.")
            elif "capacity guardian" in p_f_lower or "capacity" in p_f_lower:
                persona_format_lines.append("- **[Capacity Guardian Persona]**: AI Model Expert. Enforces strict DoR, task size constraints, and prevents bloated structures.")
            elif "anti-complexity" in p_f_lower or "pragmatic" in p_f_lower:
                persona_format_lines.append("- **[Pragmatic Anti-Complexity Engineer Persona]**: YAGNI sarcastic guard cutting over-engineering.")
            elif "finops" in p_f_lower or "cost" in p_f_lower:
                persona_format_lines.append("- **[FinOps & Cost Governance Persona]**: Resource and cloud cost efficiency guard.")
            elif "spec compliance" in p_f_lower or "specauditor" in p_f_lower:
                persona_format_lines.append("- **[Spec Compliance Auditor Persona]**: Audits specification compliance and checks for vector format limitations.")
            elif "security" in p_f_lower or "ethics" in p_f_lower or "securityauditor" in p_f_lower:
                persona_format_lines.append("- **[Security Ethics Auditor Persona]**: Audits security standards, rate limiting, and container hardening.")
        
        persona_format_str = "\n".join(persona_format_lines)

        # 1. debate_log.md 生成
        if not debate_file.exists():
            print(f"💬 [Ceremony 2] Step 1: Generating debate_log.md for: {title}...", flush=True)
            self.update_status_dashboard(title, "ディベートログ生成中...")
            
            prompt_debate = (
                f"[INST]\n"
                f"[TASK: SPRINT REFINEMENT DEBATE FOR {title}]\n"
                f"=== 1. EXECUTION INSTRUCTIONS ===\n- {inst_file_rel}\n\n"
                f"=== 2. TARGET EPIC ===\n- Title: {title}\n- Scope: {scope}\n\n"
                f"=== 3. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
                f"=== 4. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
                f"=== 5. MULTI-PERSONA INSTRUCTIONS ===\n{filtered_personas_instruction}\n\n"
                f"=== 6. TARGET DEVELOPER AGENT PROFILE (CODER MODEL) ===\n{refs['target_agent']}\n\n"
                f"=== 7. CEREMONY RETROSPECTIVE (IF ANY) ===\n{retro_content}\n\n"
                "Output MUST follow this format:\n"
                f"# 📋 Sprint Refinement Debate Log: {title}\n\n"
                "## 1. Multi-Persona Discussion\n"
                "### 🔨 Sprint Builders:\n"
                f"{persona_format_str}\n\n"
                "## 2. Sprint Backlog Plan\n"
                "- **TASK-1.1**: <Description, Story Points, Dependencies, and AC (Max 2 ACs)>\n"
                "- **TASK-1.2**: <Description, Story Points, Dependencies, and AC (Max 2 ACs)>\n"
                "[/INST]\n"
            )
            res = self.refinement_agent.generate_text(prompt_debate)
            CodeParser.atomic_write_text(debate_file, (res or "").strip())

        # 2. epic_backlog.yaml 生成
        if not backlog_file.exists():
            print(f"📝 [Ceremony 2] Step 2: Generating epic_backlog.yaml for: {title}...", flush=True)
            self.update_status_dashboard(title, "バックログYAML生成中...")

            prompt_yaml = (
                f"[INST]\n"
                f"[TASK: GENERATE EPIC BACKLOG YAML FOR {title}]\n"
                f"Generate a valid YAML block containing micro-scoped, dependency-ordered tasks for {title}.\n"
                f"Target workspace directory is: {self.config.workspace_rel}\n"
                f"Container image name is: {self.config.container_image_name}\n\n"
                f"=== SCOPE & SPECIFICATION ===\n{scope}\n\n"
                f"=== CEREMONY RETROSPECTIVE (IF ANY) ===\n{retro_content}\n\n"
                "🚨 CRITICAL DEFINITION OF READY (DoR) RULES:\n"
                "1. Each task MUST have at most 1 or 2 acceptance criteria (strictly Maximum 3).\n"
                "2. references/* is READ-ONLY. NEVER create tasks modifying references/!\n"
                "3. Any task estimated >=8 SP must be decomposed into smaller sub-tasks (1-5 SP).\n\n"
                "Output MUST be a valid YAML block enclosed in ```yaml ... ```:\n"
                "```yaml\n"
                f"epic_id: EPIC-{epic_idx}\n"
                f"title: \"{title}\"\n"
                f"workspace_rel: \"{self.config.workspace_rel}\"\n"
                "tasks:\n"
                f"  - id: TASK-{epic_idx}.1\n"
                "    title: \"Setup domain foundation and interfaces\"\n"
                "    description: \"Detailed task scope\"\n"
                "    story_points: 1\n"
                "    depends_on: []\n"
                "    acceptance_criteria:\n"
                "      - \"Criterion 1 (Concrete assertion)\"\n"
                "      - \"Criterion 2 (Concrete assertion)\"\n"
                "    verify_command: \"go test ./...\"\n"
                f"  - id: TASK-{epic_idx}.2\n"
                "    title: \"Implement core functionality\"\n"
                "    description: \"Detailed task scope\"\n"
                "    story_points: 2\n"
                f"    depends_on: [\"TASK-{epic_idx}.1\"]\n"
                "    acceptance_criteria:\n"
                "      - \"Criterion 1 (Concrete assertion)\"\n"
                "      - \"Criterion 2 (Concrete assertion)\"\n"
                "    verify_command: \"go test ./...\"\n"
                "```\n"
                "[/INST]\n"
            )
            res_yaml = self.refinement_agent.generate_text(prompt_yaml)
            parsed_yaml = CodeParser.extract_code_block(res_yaml or "", "yaml")
            
            if parsed_yaml and "tasks:" in parsed_yaml:
                CodeParser.atomic_write_text(backlog_file, parsed_yaml.strip())
                print(f"📝 [Ceremony 2] Saved direct epic_backlog.yaml for: {epic_dir.name}")
            else:
                mock_data = {
                    "epic_id": f"EPIC-{epic_idx}",
                    "title": title,
                    "workspace_rel": self.config.workspace_rel,
                    "container_image_name": self.config.container_image_name,
                    "tasks": [
                        {
                            "id": f"TASK-{epic_idx}.1",
                            "title": f"Setup {title}",
                            "description": scope,
                            "story_points": 1,
                            "depends_on": [],
                            "acceptance_criteria": ["Core components implemented", "All tests pass"],
                            "verify_command": self.config.test_command
                        }
                    ]
                }
                CodeParser.atomic_write_text(backlog_file, yaml.dump(mock_data, default_flow_style=False, allow_unicode=True))

    def run_epic_backlog_audit(self, epic_dir: Path, title: str, detailed_spec: str, epic_idx: int, attempt: int) -> dict:
        """エピック単体のバックログを対象に、セキュリティと仕様漏れをGeminiで都度監査する。"""
        backlog_file = epic_dir / "epic_backlog.yaml"
        if not backlog_file.exists():
            return {"overall_passed": False, "spec_passed": False, "sec_passed": False, "feedback": "No backlog file found."}

        try:
            backlog_content = backlog_file.read_text(encoding="utf-8")
        except Exception as e:
            return {"overall_passed": False, "spec_passed": False, "sec_passed": False, "feedback": f"Failed to read backlog: {e}"}

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="2_sprint_refinement", include_dev_rules=True, config=self.config)

        # ----------------------------------------------------
        # 1. Spec Compliance Auditor による単独チェック
        # ----------------------------------------------------
        print(f"🔍 [Epic Audit 1/2 (Attempt #{attempt})] Spec Compliance Auditor inspecting {epic_dir.name}...", flush=True)
        prompt_spec = (
            f"[INST]\n"
            f"[TASK: EPIC-LEVEL SPECIFICATION COMPLIANCE AUDIT]\n"
            f"You are the Specification Compliance Auditor (.agents/personas/spec_compliance_auditor.md).\n"
            f"Cross-reference the generated sprint backlog for this specific Epic against its detailed specification.\n\n"
            f"🚨 AUDIT SCOPE LIMITATION (CRITICAL):\n"
            f"- Evaluate ONLY the tasks within this Epic: '{title}'.\n"
            f"- Do NOT inspect or complain about other Epics, missing requirements belonging to other Epics, or system integration aspects outside this Epic's scope.\n"
            f"- If a requirement is not part of this Epic's scope, it is OUT OF SCOPE. Do NOT VETO based on out-of-scope missing features.\n\n"
            f"=== 1. EPIC SPECIFICATION ===\n{detailed_spec}\n\n"
            f"=== 2. GENERATED SPRINT BACKLOG FOR THIS EPIC ===\n{backlog_content}\n\n"
            f"Output format:\n"
            f"# 🕵️ Epic Spec Compliance Audit Report (Epic {epic_idx}, Attempt {attempt})\n\n"
            f"## 1. Traceability Checklist\n"
            f"- [Requirement / Decision]: [Mapped Task ID] -> Status (COVERED / MISSING / VIOLATION)\n\n"
            f"## 2. Verdict\n"
            f"- Verdict: **APPROVED** or **VETO**\n"
            f"- Summary: <Details and issues found. Mention specific tasks and required actions to fix if VETO.>\n"
            f"[/INST]\n"
        )
        spec_res = self.gemini_audit_agent.generate_text(prompt_spec)
        spec_text = (spec_res or "").strip()
        
        # ----------------------------------------------------
        # 2. Security & AI Ethics Auditor による単独チェック
        # ----------------------------------------------------
        print(f"🛡️ [Epic Audit 2/2 (Attempt #{attempt})] Security & AI Ethics Auditor inspecting {epic_dir.name}...", flush=True)
        prompt_sec = (
            f"[INST]\n"
            f"[TASK: EPIC-LEVEL SECURITY & ETHICS AUDIT]\n"
            f"You are the Security & AI Ethics Auditor (.agents/personas/security_ethics_auditor.md).\n"
            f"Audit the sprint backlog of this specific Epic for security, container hardening, and dependency safety rules.\n\n"
            f"🚨 AUDIT SCOPE LIMITATION (CRITICAL):\n"
            f"- Evaluate ONLY the tasks within this Epic: '{title}'.\n"
            f"- Do NOT inspect or complain about security aspects outside this Epic's scope (e.g., container settings if this Epic is just about domain core logic).\n\n"
            f"=== 1. EPIC SPECIFICATION ===\n{detailed_spec}\n\n"
            f"=== 2. GENERATED SPRINT BACKLOG FOR THIS EPIC ===\n{backlog_content}\n\n"
            f"Output format:\n"
            f"# 🛡️ Epic Security & AI Ethics Audit Report (Epic {epic_idx}, Attempt {attempt})\n\n"
            f"## 1. Security Checklist\n"
            f"- [Security Standard / Rule]: Status (COVERED / MISSING / VIOLATION / NOT_APPLICABLE)\n\n"
            f"## 2. Verdict\n"
            f"- Verdict: **APPROVED** or **VETO**\n"
            f"- Summary: <Details and issues found. Mention specific tasks and required actions to fix if VETO.>\n"
            f"[/INST]\n"
        )
        sec_res = self.gemini_audit_agent.generate_text(prompt_sec)
        sec_text = (sec_res or "").strip()

        # 保存
        audit_dir = epic_dir / f"attempt_{attempt}"
        audit_dir.mkdir(parents=True, exist_ok=True)
        CodeParser.atomic_write_text(audit_dir / "audit_spec_compliance.md", spec_text)
        CodeParser.atomic_write_text(audit_dir / "audit_security_ethics.md", sec_text)

        spec_passed = "Verdict: **APPROVED**" in spec_text or "Verdict: APPROVED" in spec_text or "**APPROVED**" in spec_text
        sec_passed = "Verdict: **APPROVED**" in sec_text or "Verdict: APPROVED" in sec_text or "**APPROVED**" in sec_text
        overall_passed = spec_passed and sec_passed

        feedback = ""
        if not spec_passed:
            feedback += f"### Spec Compliance Issues:\n{spec_text}\n\n"
        if not sec_passed:
            feedback += f"### Security & Ethics Issues:\n{sec_text}\n\n"

        return {
            "overall_passed": overall_passed,
            "spec_passed": spec_passed,
            "sec_passed": sec_passed,
            "feedback": feedback.strip()
        }

    def run_individual_final_audits(self, attempt: int = 1) -> dict:
        """【各自独立監査ゲート】loop_N ディレクトリ構造で各回の監査結果・履歴を保存"""
        loop_dir = self.eval_dir / f"loop_{attempt}"
        loop_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n🕵️ [Independent Final Audits - Loop #{attempt}] Running Separate Audits via Gemini...", flush=True)
        self.update_status_dashboard("Independent Final Audits", f"Gemini による個別独立監査を実行中 (Loop #{attempt})...")

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="2_sprint_refinement", include_dev_rules=True, config=self.config)
        
        # 全スプリントバックログを収集
        backlog_summaries = []
        for b_file in sorted(self.init_dir.glob("*/epic_backlog.yaml")):
            try:
                data = yaml.safe_load(b_file.read_text(encoding="utf-8")) or {}
                t_list = [f"  - [{t.get('id')}] {t.get('title')} (SP: {t.get('story_points', 1)}, AC: {', '.join(t.get('acceptance_criteria', []))})" for t in data.get("tasks", [])]
                backlog_summaries.append(f"### {data.get('title', b_file.parent.name)}\n" + "\n".join(t_list))
            except Exception:
                pass
        all_backlogs_str = "\n\n".join(backlog_summaries)

        # ----------------------------------------------------
        # 1. Spec Compliance Auditor による単独チェック (仕様改ざん即時VETO & DoR ACチェック)
        # ----------------------------------------------------
        print(f"🔍 [Audit 1/2 (Loop #{attempt})] Spec Compliance Auditor inspecting backlog...", flush=True)
        spec_audit_file = loop_dir / "audit_spec_compliance.md"
        prompt_spec = (
            f"[INST]\n"
            f"[TASK: INDEPENDENT SPECIFICATION COMPLIANCE AUDIT (LOOP #{attempt})]\n"
            f"You are the Specification Compliance Auditor (.agents/personas/spec_compliance_auditor.md).\n"
            f"Cross-reference ALL generated sprint backlogs against the source specifications in references/ line-by-line.\n\n"
            f"CRITICAL AUDIT RULES:\n"
            f"1. ZERO SPEC TAMPERING: If ANY task attempts to edit, modify, or update files in references/, you MUST ISSUE AN IMMEDIATE VETO.\n"
            f"2. DoR COMPLIANCE: Verify that each task has at most 2-3 acceptance criteria (single responsibility micro-tasks).\n"
            f"3. Check for 100% adherence to specifications in references/* and decisions in references/decisions.md.\n\n"
            f"=== 1. SYSTEM SPECIFICATIONS & DECISIONS ===\n{refs['specs']}\n\n"
            f"=== 2. GENERATED SPRINT BACKLOGS ACROSS ALL EPICS ===\n{all_backlogs_str}\n\n"
            f"Output format:\n"
            f"# 🕵️ Specification Compliance Audit Report (Loop #{attempt})\n\n"
            f"## 1. Traceability Checklist\n"
            f"- [Requirement / Decision]: [Mapped Task ID] -> Status (COVERED / MISSING / VIOLATION / TAMPERING)\n\n"
            f"## 2. Verdict\n"
            f"- Verdict: **APPROVED** or **VETO**\n"
            f"- Summary: <Details>\n"
            f"[/INST]\n"
        )
        spec_res = self.gemini_audit_agent.generate_text(prompt_spec)
        spec_text = (spec_res or "").strip()
        CodeParser.atomic_write_text(spec_audit_file, spec_text)
        CodeParser.atomic_write_text(self.eval_dir / "audit_spec_compliance.md", spec_text)

        spec_passed = "Verdict: **APPROVED**" in spec_text or "Verdict: APPROVED" in spec_text or "**APPROVED**" in spec_text
        spec_status_icon = "✅ APPROVED" if spec_passed else "🛑 VETO/REJECTED"
        print(f"📝 [Audit 1/2 Complete - Loop #{attempt}] Spec Compliance: {spec_status_icon} (Saved to {spec_audit_file.relative_to(self.root_dir)})")

        # ----------------------------------------------------
        # 2. Security & AI Ethics Auditor による単独チェック
        # ----------------------------------------------------
        print(f"🛡️ [Audit 2/2 (Loop #{attempt})] Security & AI Ethics Auditor inspecting backlog...", flush=True)
        sec_audit_file = loop_dir / "audit_security_ethics.md"
        prompt_sec = (
            f"[INST]\n"
            f"[TASK: INDEPENDENT SECURITY & ETHICS AUDIT (LOOP #{attempt})]\n"
            f"You are the Security & AI Ethics Auditor (.agents/personas/security_ethics_auditor.md).\n"
            f"Audit the sprint backlogs for security standards, rate limiting (HTTP 429), container hardening (non-root UID 65532), and zero unrequested external services.\n\n"
            f"=== GENERATED SPRINT BACKLOGS ===\n{all_backlogs_str}\n\n"
            f"Output format:\n"
            f"# 🛡️ Security & AI Ethics Audit Report (Loop #{attempt})\n\n"
            f"## 1. Security Checklist\n"
            f"- Rate Limiting & DoS Protection: (PASS / FAIL)\n"
            f"- Container Security (non-root): (PASS / FAIL)\n"
            f"- Zero Unrequested Services (DB/Auth): (PASS / FAIL)\n\n"
            f"## 2. Verdict\n"
            f"- Verdict: **APPROVED** or **VETO**\n"
            f"- Summary: <Details>\n"
            f"[/INST]\n"
        )
        sec_res = self.gemini_audit_agent.generate_text(prompt_sec)
        sec_text = (sec_res or "").strip()
        CodeParser.atomic_write_text(sec_audit_file, sec_text)
        CodeParser.atomic_write_text(self.eval_dir / "audit_security_ethics.md", sec_text)

        sec_passed = "Verdict: **APPROVED**" in sec_text or "Verdict: APPROVED" in sec_text or "**APPROVED**" in sec_text
        sec_status_icon = "✅ APPROVED" if sec_passed else "🛑 VETO/REJECTED"
        print(f"📝 [Audit 2/2 Complete - Loop #{attempt}] Security & Ethics: {sec_status_icon} (Saved to {sec_audit_file.relative_to(self.root_dir)})")

        summary_data = {
            "loop_attempt": attempt,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "spec_compliance_passed": spec_passed,
            "security_ethics_passed": sec_passed,
            "overall_approved": spec_passed and sec_passed
        }
        CodeParser.atomic_write_text(loop_dir / "audit_summary.yaml", yaml.dump(summary_data, default_flow_style=False))

        return {
            "attempt": attempt,
            "spec_passed": spec_passed,
            "sec_passed": sec_passed,
            "overall_passed": spec_passed and sec_passed,
            "loop_dir": loop_dir
        }

    def run_sprint_refinement(self, overall_debate_log: str):
        print("🚀 [Ceremony 2: Sprint Refinement] Executing Sprint Backlog Refinement...", flush=True)
        
        # 既存の loop ディレクトリ数をカウントして attempt を算出
        existing_loops = list(self.eval_dir.glob("loop_*"))
        current_attempt = len(existing_loops) + 1

        # EpicRefinementEngine の堅牢なパーサーを利用して全エピックを抽出
        epic_engine = EpicRefinementEngine(self.root_dir, self.config)
        epics = epic_engine.extract_epics_from_log(overall_debate_log)
        
        if not epics:
            epics = [{"title": "Epic 1 Core Foundation", "scope": "Core application logic and interface endpoints"}]

        print(f"📋 [Ceremony 2] Found {len(epics)} Epics to refine in Ceremony 2 (Loop Attempt #{current_attempt})!", flush=True)

        for idx, ep in enumerate(epics, 1):
            title = ep["title"]
            scope = ep["scope"]
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', title).lower().strip('_')
            clean_name = re.sub(r'_+', '_', clean_name)
            epic_dir_name = f"epic_{idx}_{clean_name}" if not clean_name.startswith(f"epic_{idx}") else clean_name
            epic_dir = self.init_dir / epic_dir_name
            epic_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"\n⚙️ [Ceremony 2: Refining Epic {idx}/{len(epics)}] {title} (Dir: {epic_dir_name})", flush=True)
            
            # Gemini (クラウド) を使用して、巨大な overall_debate_log から本エピックに関する詳細仕様と関与ペルソナのみをピンポイントで切り出す
            spec_file = epic_dir / "epic_specification.yaml"
            if not spec_file.exists():
                print(f"  📄 [Ceremony 2] Extracting detailed specs and target personas for: {title}...", flush=True)
                gemini_adapter = LLMAdapterFactory.get_adapter(provider="gemini")
                extract_prompt = (
                    f"You are a Senior Project Manager and Systems Architect.\n"
                    f"Read the following overall debate log, and extract ONLY the detailed technical specifications, architecture decisions, interfaces, configurations, and rules that are directly relevant to this specific epic: \"{title}\".\n"
                    f"Also, identify the target required personas for detailed design debate of this epic strictly based on the 'Target Personas for Detailed Design' listed under this specific epic in the overall debate log. Map them to their brief alias keys (e.g. 'architect', 'qa', 'devops', 'anticomplexity', 'finops', 'scrummaster', 'capacity', 'specauditor', 'securityauditor', 'po', 'frontend', 'db'). Do NOT dynamically re-evaluate or shrink this list, keep all listed personas.\n\n"
                    f"=== OVERALL DEBATE LOG ===\n{overall_debate_log}\n\n"
                    f"Output strictly in YAML format as follows:\n"
                    f"epic_title: \"{title}\"\n"
                    f"required_personas:\n"
                    f"  - \"architect\"\n"
                    f"  - \"qa\"\n"
                    f"detailed_spec: |\n"
                    f"  <detailed specs and constraints extracted from the log>\n"
                )
                try:
                    spec_response = gemini_adapter.generate_text(extract_prompt)
                    # YAMLコードブロックなどを取り除いてクリーンにする
                    clean_yaml = spec_response or ""
                    if "```yaml" in clean_yaml:
                        clean_yaml = clean_yaml.split("```yaml")[1].split("```")[0]
                    elif "```" in clean_yaml:
                        clean_yaml = clean_yaml.split("```")[1].split("```")[0]
                    CodeParser.atomic_write_text(spec_file, clean_yaml.strip())
                except Exception as e:
                    print(f"  ⚠️ [Ceremony 2 Warning] Failed to extract spec using Gemini: {e}")
            
            required_personas = ["architect", "qa"]
            detailed_spec = scope
            if spec_file.exists():
                try:
                    spec_data = yaml.safe_load(spec_file.read_text(encoding="utf-8")) or {}
                    required_personas = spec_data.get("required_personas", ["architect", "qa"])
                    detailed_spec = spec_data.get("detailed_spec", scope)
                except Exception as e:
                    print(f"  ⚠️ [Ceremony 2 Warning] Failed to parse spec file: {e}")

            # 対策案B: ハーネスによる補正処理 (エイリアスマップを使用)
            log_personas = extract_personas_from_log_for_epic(overall_debate_log, title, self.formal_to_alias)
            if log_personas:
                required_personas = log_personas
                print(f"  🎯 [Harness Persona Match] Restored persona aliases from overall log: {required_personas}")

            # エピックごとの都度監査＆自動リトライループ
            max_retries = getattr(self.config, "max_retries", 3)
            previous_feedback = ""
            for attempt in range(1, max_retries + 1):
                # リトライ時は既存のディベートログとバックログYAMLを削除して再生成を強制する
                if attempt > 1:
                    debate_file = epic_dir / "debate_log.md"
                    backlog_file = epic_dir / "epic_backlog.yaml"
                    if debate_file.exists():
                        debate_file.unlink()
                    if backlog_file.exists():
                        backlog_file.unlink()

                self.run_sprint_refinement_for_epic(epic_dir, title, detailed_spec, required_personas, idx, previous_audit_feedback=previous_feedback)
                
                # エピック単体での仕様漏れ・セキュリティ都度監査
                audit_res = self.run_epic_backlog_audit(epic_dir, title, detailed_spec, idx, attempt)
                if audit_res["overall_passed"]:
                    print(f"  ✅ [Refinement Approved] Epic {idx} passed all local audits on attempt #{attempt}!", flush=True)
                    break
                else:
                    print(f"  🛑 [Refinement Vetoed] Epic {idx} failed audits on attempt #{attempt}. Retrying with feedback...", flush=True)
                    previous_feedback = audit_res["feedback"]
            else:
                print(f"  ⚠️ [Refinement Max Retries] Epic {idx} reached maximum retry limit ({max_retries}) without passing audits.", flush=True)

        # Backlog 分割 & テストハーネス生成
        print("\n🚀 [Ceremony 2] Generating automated test harness scripts for all refined Epics...", flush=True)
        self.update_status_dashboard("All Epics", "テストハーネス生成中...")
        BacklogSplitter.split_all_epics(self.root_dir, self.config)
        TestHarnessGenerator.generate_all(self.root_dir, self.config)

        # 🛡️ Gemini による各自独立監査ゲートの実行 (loop_N ディレクトリ構造で履歴管理)
        audit_result = self.run_individual_final_audits(attempt=current_attempt)

        print("\n" + "=" * 50)
        print(f"🏁 [Ceremony 2 Final Gate Summary - Directory: {audit_result['loop_dir'].relative_to(self.root_dir)}]")
        print(f"  - Loop Attempt Count: #{audit_result['attempt']}")
        print(f"  - Spec Compliance Audit: {'✅ PASS' if audit_result['spec_passed'] else '🛑 REJECTED/VETO'}")
        print(f"  - Security & Ethics Audit: {'✅ PASS' if audit_result['sec_passed'] else '🛑 REJECTED/VETO'}")
        print(f"  - Final Verdict: {'🎉 ALL APPROVED' if audit_result['overall_passed'] else '⚠️ VETO DETECTED (Requires Review)'}")
        print("=" * 50 + "\n")

        self.update_status_dashboard("All Epics", f"リファインメント完了 (監査 Loop #{audit_result['attempt']})")
        print(f"🎉 [Ceremony 2 Complete] Sprint Refinement & Independent Final Audits saved in {audit_result['loop_dir'].relative_to(self.root_dir)}!", flush=True)
        return True
