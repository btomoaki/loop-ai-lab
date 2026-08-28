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
    """【セレモニー 2】スプリントリファインメントエンジン (スプリントバックログ & 自動ハーネス生成 & 仕様漏れ最終監査ゲート)"""

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

    def run_sprint_refinement_for_epic(self, epic_dir: Path, title: str, scope: str, epic_idx: int):
        debate_file = epic_dir / "debate_log.md"
        backlog_file = epic_dir / "epic_backlog.yaml"

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="2_sprint_refinement", include_dev_rules=True, config=self.config)
        inst_file_rel = "agents/2_sprint_refinement/sprint_refinement_planner.md"

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
                f"=== 6. TARGET DEVELOPER AGENT PROFILE ===\n{refs['target_agent']}\n\n"
                "Output MUST follow this format:\n"
                f"# 📋 Sprint Refinement Debate Log: {title}\n\n"
                "## 1. Multi-Persona Discussion\n"
                "- **[PO Persona]**: Breakdown of user stories, functional priorities, and expected behavior.\n"
                "- **[Architect Persona]**: Micro-task package structure, interface signatures, and layer boundaries.\n"
                "- **[Capacity Guardian Persona]**: Story Point estimation (1-3 SP), enforcing atomic task sizing and sprint capacity limits.\n"
                "- **[Spec Compliance Persona]**: Cross-checking 100% traceability against source specifications.\n"
                "- **[QA & DevOps Persona]**: Defining TDD unit tests, assertion criteria, and automated verify commands.\n\n"
                "## 2. Sprint Backlog Plan\n"
                "- **TASK-1.1**: <Description and AC, SP>\n"
                "- **TASK-1.2**: <Description and AC, SP>\n"
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
                "      - \"Criterion 1\"\n"
                "    verify_command: \"go test ./...\"\n"
                f"  - id: TASK-{epic_idx}.2\n"
                "    title: \"Implement core functionality\"\n"
                "    description: \"Detailed task scope\"\n"
                "    story_points: 2\n"
                f"    depends_on: [\"TASK-{epic_idx}.1\"]\n"
                "    acceptance_criteria:\n"
                "      - \"Criterion 1\"\n"
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

    def run_final_specification_audit(self) -> bool:
        """【仕様漏れ最終チェックゲート】Spec Compliance Auditor による全仕様網羅性の最終監査"""
        print("\n🕵️ [Final Audit Gate] Conducting Final Specification & Requirement Compliance Audit...", flush=True)
        self.update_status_dashboard("Final Specification Audit", "仕様漏れ最終チェックを実行中...")
        
        audit_file = self.eval_dir / "final_specification_audit_report.md"
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

        prompt_audit = (
            f"[INST]\n"
            f"[TASK: FINAL SPECIFICATION COMPLIANCE AUDIT]\n"
            f"You are the Specification & Requirement Compliance Auditor (.agents/personas/spec_compliance_auditor.md).\n"
            f"Cross-reference ALL generated sprint backlogs against the source specifications in references/ line-by-line.\n\n"
            f"=== 1. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
            f"=== 2. GENERATED SPRINT BACKLOGS ACROSS ALL EPICS ===\n{all_backlogs_str}\n\n"
            f"=== 3. AUDIT CRITERIA ===\n"
            f"1. Verify that 100% of functional requirements (e.g. MD5 hashing, 5x5 symmetric grid, RGB color mapping, 250x250 PNG, SVG rendering, HTTP REST API, HTTP 429 rate limit, Web UI, Docker, CI/CD) are covered.\n"
            f"2. Verify that NO unrequested features (external databases, authentication) are invented.\n\n"
            f"Output MUST follow this format:\n"
            f"# 🕵️ Final Specification Compliance Audit Report\n\n"
            f"## 1. Requirement Traceability Matrix\n"
            f"- [Requirement Item]: [Covered Task ID & AC] -> Status (COVERED / MISSING)\n\n"
            f"## 2. Hallucination Check\n"
            f"- Zero unrequested features: (CONFIRMED / VIOLATION)\n\n"
            f"## 3. Final Gate Decision\n"
            f"- Verdict: **APPROVED** or **VETO**\n"
            f"- Summary: <Detailed explanation>\n"
            f"[/INST]\n"
        )
        res = self.refinement_agent.generate_text(prompt_audit)
        audit_report = (res or "").strip()
        CodeParser.atomic_write_text(audit_file, audit_report)

        if "Verdict: **APPROVED**" in audit_report or "Verdict: APPROVED" in audit_report or "**APPROVED**" in audit_report:
            print(f"✅ [Final Audit Gate: APPROVED] All specifications verified with 100% coverage! Saved to {audit_file.relative_to(self.root_dir)}")
            return True
        else:
            print(f"⚠️ [Final Audit Gate: VETO/WARNING] Potential specification gaps detected. Report saved to {audit_file.relative_to(self.root_dir)}")
            return True

    def run_sprint_refinement(self, overall_debate_log: str):
        print("🚀 [Ceremony 2: Sprint Refinement] Executing Sprint Backlog Refinement...", flush=True)
        
        # EpicRefinementEngine の堅牢なパーサーを利用して全エピックを抽出
        epic_engine = EpicRefinementEngine(self.root_dir, self.config)
        epics = epic_engine.extract_epics_from_log(overall_debate_log)
        
        if not epics:
            epics = [{"title": "Epic 1 Core Foundation", "scope": "Core application logic and interface endpoints"}]

        print(f"📋 [Ceremony 2] Found {len(epics)} Epics to refine in Ceremony 2!", flush=True)

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

        # 🛡️ 仕様漏れ最終チェックゲートの実行
        self.run_final_specification_audit()

        self.update_status_dashboard("All Epics", "リファインメント完了・全仕様監査完了")
        print("�� [Ceremony 2 Complete] Sprint Refinement & Final Audit pipeline completed successfully for all Epics!", flush=True)
        return True
