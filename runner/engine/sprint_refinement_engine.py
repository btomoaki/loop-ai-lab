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

    def _get_refinement_provider(self) -> str:
        config_file = self.root_dir / "config.yaml"
        if config_file.exists():
            try:
                data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
                return data.get("DEFAULT_LLM_PROVIDER", "gemini")
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

    def run_sprint_refinement_for_epic(self, epic_dir: Path, title: str, scope: str, epic_idx: int):
        debate_file = epic_dir / "debate_log.md"
        backlog_file = epic_dir / "epic_backlog.yaml"

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="2_sprint_refinement", include_dev_rules=True, config=self.config)
        inst_file_rel = "agents/2_sprint_refinement/sprint_refinement_planner.md"
        
        retro_content = self._get_ceremony_retrospective()

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
                f"=== 5. MULTI-PERSONA INSTRUCTIONS ===\n{refs['personas']}\n\n"
                f"=== 6. TARGET DEVELOPER AGENT PROFILE (CODER MODEL) ===\n{refs['target_agent']}\n\n"
                f"=== 7. CEREMONY RETROSPECTIVE (IF ANY) ===\n{retro_content}\n\n"
                "Output MUST follow this format:\n"
                f"# 📋 Sprint Refinement Debate Log: {title}\n\n"
                "## 1. Multi-Persona Discussion\n"
                "### 🔨 Sprint Builders:\n"
                "- **[Scrum Master Persona]**: Facilitates the session, validates task sequencing, and establishes sprint DoD.\n"
                "- **[Architect Persona]**: Micro-task package structure, domain interfaces, and pure function boundaries using Go standard library.\n"
                "- **[Frontend UI/UX Engineer Persona]**: Web UI components adhering strictly to specifications (No unrequested heavy frameworks).\n"
                "- **[DB / Data Engineer Persona]**: Data structures and persistence constraints (stateless).\n"
                "- **[Platform & DevOps Persona]**: Dockerfile (non-root UID 65532), Makefile, and Cloud Run runtime execution.\n"
                "- **[QA Engineer Persona]**: TDD unit test suites, edge cases, and automated verify commands.\n\n"
                "### 🛡️ Independent Constraint Guards:\n"
                "- **[Capacity Guardian Persona]**: AI Model Expert. Enforces DoR (strictly 1-2 ACs per task), limits task size (1-5 SP), mandates that any task with >=8 SP be decomposed immediately, and prohibits bloated frameworks.\n"
                "- **[Pragmatic Anti-Complexity Engineer Persona]**: YAGNI sarcastic guard cutting over-engineering and eliminating unrequested features.\n"
                "- **[FinOps & Cost Governance Persona]**: Resource, time, and cloud cost efficiency guard.\n\n"
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
            self.run_sprint_refinement_for_epic(epic_dir, title, scope, idx)

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
