import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser
from runner.utils.context_loader import ContextLoader
from runner.utils.template_manager import TemplateManager
from runner.utils.backlog_splitter import BacklogSplitter
from runner.harness_generator import TestHarnessGenerator
from runner.adapters.llm_adapter import LLMAdapterFactory
from runner.engine.epic_refinement_engine import EpicRefinementEngine
from runner.engine.backlog_harness import BacklogHarness


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
            "specauditor": "[Spec Compliance Auditor Persona]",
            "ruler": "[Ruler Persona (ルーラー / 規律・ポリシー統制官)]"
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
        self.init_dir = root_dir / self.config.initiatives_dir
        self.eval_dir = root_dir / self.config.evaluator_dir
        self.status_file = root_dir / self.config.status_file

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
            except Exception as e:
                raise RuntimeError(f"❌ [Ceremony 2 Error] Failed to read retrospective file '{retro_file}': {e}") from e
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

        # 必須の進行役(ScrumMaster)、ビジネスオーナー(PO)、規律執行役(Ruler)をディベート参加者に確保
        for essential_role, formal_title in [
            ("scrummaster", "[Scrum Master Persona]"),
            ("po", "[PO Persona]"),
            ("ruler", "[Ruler Persona (Discipline & Policy Controller)]"),
        ]:
            if essential_role not in required_personas:
                required_personas.append(essential_role)
            if formal_title not in required_personas_formal:
                required_personas_formal.append(formal_title)

        roles_yaml_path = TemplateManager.get_template_path("ceremony_2/persona_roles.yaml")
        if not roles_yaml_path.exists():
            raise FileNotFoundError(f"❌ [Ceremony 2 Error] Required persona roles configuration not found: {roles_yaml_path}")
        try:
            roles_config = yaml.safe_load(roles_yaml_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            raise RuntimeError(f"❌ [Ceremony 2 Error] Failed to parse persona roles YAML '{roles_yaml_path}': {e}") from e

        persona_format_lines = []
        for p_formal in required_personas_formal:
            p_f_lower = p_formal.lower()
            matched = False
            for role_key, role_meta in roles_config.items():
                aliases = role_meta.get("aliases", [role_key])
                if any(re.search(rf"\b{re.escape(alias)}\b", p_f_lower) for alias in aliases):
                    formal = role_meta.get("formal_name", p_formal)
                    instruction = role_meta.get("instruction", "")
                    persona_format_lines.append(f"- **{formal}**: {instruction}")
                    matched = True
                    break
            if not matched:
                persona_format_lines.append(f"- **{p_formal}**: Evaluates epic tasks from dedicated domain perspective.")
        
        persona_format_str = "\n".join(persona_format_lines)

        # 1. debate_log.md 生成
        # 1. debate_log.md 生成
        if not debate_file.exists():
            print(f"💬 [Ceremony 2] Step 1: Generating debate_log.md for: {title}...", flush=True)
            self.update_status_dashboard(title, "ディベートログ生成中...")
            
            prompt_debate = TemplateManager.render(
                "ceremony_2/debate.tpl",
                rules=refs['rules'],
                specs=refs['specs'],
                personas=filtered_personas_instruction,
                target_agent=refs['target_agent'],
                inst_file_rel=inst_file_rel,
                title=title,
                scope=scope,
                retro_content=retro_content,
                persona_format_str=persona_format_str,
            )
            res = self.refinement_agent.generate_text(prompt_debate)
            CodeParser.atomic_write_text(debate_file, (res or "").strip())

        # 2. epic_backlog.yaml 生成 または 実装者主導の PATCH / REBUILD
        if backlog_file.exists() and previous_audit_feedback:
            # 🔄 リトライ時: 実装者（プランナー）に既存バックログと監査指摘を提示し、PATCH または REBUILD を判断させる
            print(f"🔄 [Ceremony 2] Step 2: Evaluating audit feedback with existing backlog for: {title}...", flush=True)
            self.update_status_dashboard(title, "監査フィードバック反映・修正中...")

            current_backlog_yaml = backlog_file.read_text(encoding="utf-8")
            prompt_patch = TemplateManager.render(
                "ceremony_2/patch.tpl",
                title=title,
                workspace_rel=self.config.workspace_rel,
                container_image_name=self.config.container_image_name,
                scope=scope,
                previous_audit_feedback=previous_audit_feedback,
                current_backlog_yaml=current_backlog_yaml,
                epic_idx=epic_idx,
            )

            res_patch = self.refinement_agent.generate_text(prompt_patch)
            res_patch_str = (res_patch or "").strip()

            if "ACTION: REBUILD" in res_patch_str:
                rebuild_reason = res_patch_str.split("Reason:")[1].strip() if "Reason:" in res_patch_str else "Architectural mismatch"
                print(f"  🔄 [Implementer Decision] Planner requested FULL REBUILD for Epic {epic_idx}: {rebuild_reason}", flush=True)
                if debate_file.exists():
                    debate_file.unlink()
                if backlog_file.exists():
                    backlog_file.unlink()
                # ディベートから再生成
                return self.run_sprint_refinement_for_epic(epic_dir, title, scope, required_personas, epic_idx, previous_audit_feedback="")
            
            parsed_yaml = CodeParser.extract_code_block(res_patch_str, "yaml")
            if not parsed_yaml or "tasks:" not in parsed_yaml:
                raise RuntimeError(
                    f"❌ [Ceremony 2 Failed] Failed to extract valid YAML with 'tasks:' from patch response for {epic_dir.name}!\n"
                    f"Raw Response:\n{res_patch_str}"
                )
            CodeParser.atomic_write_text(backlog_file, parsed_yaml.strip())
            print(f"  📝 [Implementer Decision] Planner applied micro-patch to epic_backlog.yaml for: {epic_dir.name}", flush=True)

            # 🛡️ Backlog Pre-Flight Harness による決定論的 7大ガードレール検査 & 自動補正
            harness = BacklogHarness(self.root_dir, self.config)
            remediated, report = harness.validate_and_remediate(epic_dir, epic_idx, title)
            if remediated:
                print(f"  🛡️ [Backlog Harness] Auto-remediated backlog for Epic {epic_idx} after patch:\n{report}", flush=True)
            else:
                print(f"  🛡️ [Backlog Harness] Verified Epic {epic_idx} backlog: All 7 guardrails passed.", flush=True)

        elif not backlog_file.exists():
            print(f"📝 [Ceremony 2] Step 2: Generating epic_backlog.yaml for: {title}...", flush=True)
            self.update_status_dashboard(title, "バックログYAML生成中...")

            prompt_yaml = TemplateManager.render(
                "ceremony_2/backlog.tpl",
                title=title,
                workspace_rel=self.config.workspace_rel,
                container_image_name=self.config.container_image_name,
                scope=scope,
                retro_content=retro_content,
                epic_idx=epic_idx,
            )
            res_yaml = self.refinement_agent.generate_text(prompt_yaml)
            parsed_yaml = CodeParser.extract_code_block(res_yaml or "", "yaml")
            
            if not parsed_yaml or "tasks:" not in parsed_yaml:
                raise RuntimeError(
                    f"❌ [Ceremony 2 Failed] Failed to generate valid epic_backlog.yaml with 'tasks:' for {epic_dir.name}!\n"
                    f"Raw Response:\n{res_yaml}"
                )
            CodeParser.atomic_write_text(backlog_file, parsed_yaml.strip())
            print(f"📝 [Ceremony 2] Saved direct epic_backlog.yaml for: {epic_dir.name}")

            # 🛡️ Backlog Pre-Flight Harness による決定論的 7大ガードレール検査 & 自動補正
            harness = BacklogHarness(self.root_dir, self.config)
            remediated, report = harness.validate_and_remediate(epic_dir, epic_idx, title)
            if remediated:
                print(f"  🛡️ [Backlog Harness] Auto-remediated backlog for Epic {epic_idx} before audit:\n{report}", flush=True)
            else:
                print(f"  🛡️ [Backlog Harness] Verified Epic {epic_idx} backlog: All 7 guardrails passed.", flush=True)

    def run_epic_backlog_audit(self, epic_dir: Path, title: str, detailed_spec: str, epic_idx: int, attempt: int) -> dict:
        """エピック単体のバックログを対象に、セキュリティと仕様漏れをGeminiで都度監査する。"""
        backlog_file = epic_dir / "epic_backlog.yaml"
        if not backlog_file.exists():
            raise RuntimeError(f"❌ [Epic Audit Error] Backlog file does not exist: {backlog_file}")

        try:
            backlog_content = backlog_file.read_text(encoding="utf-8")
        except Exception as e:
            raise RuntimeError(f"❌ [Epic Audit Error] Failed to read backlog file '{backlog_file}': {e}") from e

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="2_sprint_refinement", include_dev_rules=True, config=self.config)

        # ----------------------------------------------------
        # 1. Spec Compliance Auditor による単独チェック
        # ----------------------------------------------------
        print(f"🔍 [Epic Audit 1/2 (Attempt #{attempt})] Spec Compliance Auditor inspecting {epic_dir.name}...", flush=True)
        prompt_spec = TemplateManager.render(
            "ceremony_2/epic_audit_spec_compliance.tpl",
            title=title,
            epic_idx=epic_idx,
            attempt=attempt,
            detailed_spec=detailed_spec,
            backlog_content=backlog_content,
        )
        spec_res = self.gemini_audit_agent.generate_text(prompt_spec)
        spec_text = (spec_res or "").strip()
        
        # ----------------------------------------------------
        # 2. Security & AI Ethics Auditor による単独チェック
        # ----------------------------------------------------
        print(f"🛡️ [Epic Audit 2/2 (Attempt #{attempt})] Security & AI Ethics Auditor inspecting {epic_dir.name}...", flush=True)
        prompt_sec = TemplateManager.render(
            "ceremony_2/epic_audit_security_ethics.tpl",
            title=title,
            epic_idx=epic_idx,
            attempt=attempt,
            detailed_spec=detailed_spec,
            backlog_content=backlog_content,
        )
        sec_res = self.gemini_audit_agent.generate_text(prompt_sec)
        sec_text = (sec_res or "").strip()

        # ----------------------------------------------------
        # 3. Ruler による規律遵守・ルール腐敗監査
        # ----------------------------------------------------
        print(f"🔍 [Epic Audit 3/3 (Attempt #{attempt})] Ruler Persona inspecting rules & containerization for {epic_dir.name}...", flush=True)
        prompt_ruler = TemplateManager.render(
            "ceremony_2/epic_audit_ruler_governance.tpl",
            epic_name=epic_dir.name,
            backlog_content=backlog_content,
        )
        ruler_res = self.gemini_audit_agent.generate_text(prompt_ruler)
        ruler_text = (ruler_res or "").strip()

        # 保存
        audit_dir = epic_dir / f"attempt_{attempt}"
        audit_dir.mkdir(parents=True, exist_ok=True)
        CodeParser.atomic_write_text(audit_dir / "audit_spec_compliance.md", spec_text)
        CodeParser.atomic_write_text(audit_dir / "audit_security_ethics.md", sec_text)
        CodeParser.atomic_write_text(audit_dir / "audit_ruler_governance.md", ruler_text)

        if "RULER_ALERT:" in ruler_text:
            alert_msg = ruler_text.split("RULER_ALERT:")[1].splitlines()[0].strip()
            print(f"⚠️ [Ruler Alert Detected in {epic_dir.name}] {alert_msg}", flush=True)

        spec_passed = "Verdict: **APPROVED**" in spec_text or "Verdict: APPROVED" in spec_text or "**APPROVED**" in spec_text
        sec_passed = "Verdict: **APPROVED**" in sec_text or "Verdict: APPROVED" in sec_text or "**APPROVED**" in sec_text
        ruler_passed = "Verdict: **APPROVED**" in ruler_text or "Verdict: APPROVED" in ruler_text or "**APPROVED**" in ruler_text
        overall_passed = spec_passed and sec_passed and ruler_passed

        feedback = ""
        if not spec_passed:
            feedback += f"### Spec Compliance Issues:\n{spec_text}\n\n"
        if not sec_passed:
            feedback += f"### Security & Ethics Issues:\n{sec_text}\n\n"
        if not ruler_passed:
            feedback += f"### Ruler Governance & Policy Violations:\n{ruler_text}\n\n"

        return {
            "overall_passed": overall_passed,
            "spec_passed": spec_passed,
            "sec_passed": sec_passed,
            "ruler_passed": ruler_passed,
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
                t_list = []
                for t in data.get("tasks", []):
                    ac_strs = [str(c) if not isinstance(c, dict) else f"{list(c.keys())[0]}: {list(c.values())[0]}" for c in t.get("acceptance_criteria", [])]
                    t_list.append(f"  - [{t.get('id')}] {t.get('title')} (SP: {t.get('story_points', 1)}, AC: {', '.join(ac_strs)})")
                backlog_summaries.append(f"### {data.get('title', b_file.parent.name)}\n" + "\n".join(t_list))
            except Exception as e:
                raise RuntimeError(f"🚨 [Fatal Backlog Syntax Error] Failed to parse {b_file}: {e}. Ensure all strings with colons are quoted in YAML.")
        all_backlogs_str = "\n\n".join(backlog_summaries)

        # ----------------------------------------------------
        # 1. Spec Compliance Auditor による単独チェック (仕様改ざん即時VETO & DoR ACチェック)
        # ----------------------------------------------------
        print(f"🔍 [Audit 1/4 (Loop #{attempt})] Spec Compliance Auditor inspecting backlog...", flush=True)
        spec_audit_file = loop_dir / "audit_spec_compliance.md"
        prompt_spec = TemplateManager.render(
            "ceremony_2/audit_spec_compliance.tpl",
            specs=refs['specs'],
            all_backlogs_str=all_backlogs_str,
            attempt=attempt,
        )
        spec_res = self.gemini_audit_agent.generate_text(prompt_spec)
        spec_text = (spec_res or "").strip()
        CodeParser.atomic_write_text(spec_audit_file, spec_text)
        CodeParser.atomic_write_text(self.eval_dir / "ceremony_2" / "audits" / "audit_spec_compliance.md", spec_text)

        spec_passed = "Verdict: **APPROVED**" in spec_text or "Verdict: APPROVED" in spec_text or "**APPROVED**" in spec_text
        spec_status_icon = "✅ APPROVED" if spec_passed else "🛑 VETO/REJECTED"
        print(f"📝 [Audit 1/4 Complete - Loop #{attempt}] Spec Compliance: {spec_status_icon} (Saved to {spec_audit_file.relative_to(self.root_dir)})")

        # ----------------------------------------------------
        # 2. Security & AI Ethics Auditor による単独チェック
        # ----------------------------------------------------
        print(f"🛡️ [Audit 2/4 (Loop #{attempt})] Security & AI Ethics Auditor inspecting backlog...", flush=True)
        sec_audit_file = loop_dir / "audit_security_ethics.md"
        prompt_sec = TemplateManager.render(
            "ceremony_2/audit_security_ethics.tpl",
            all_backlogs_str=all_backlogs_str,
            attempt=attempt,
        )
        sec_res = self.gemini_audit_agent.generate_text(prompt_sec)
        sec_text = (sec_res or "").strip()
        CodeParser.atomic_write_text(sec_audit_file, sec_text)
        CodeParser.atomic_write_text(self.eval_dir / "ceremony_2" / "audits" / "audit_security_ethics.md", sec_text)

        sec_passed = "Verdict: **APPROVED**" in sec_text or "Verdict: APPROVED" in sec_text or "**APPROVED**" in sec_text
        sec_status_icon = "✅ APPROVED" if sec_passed else "🛑 VETO/REJECTED"
        print(f"📝 [Audit 2/4 Complete - Loop #{attempt}] Security & Ethics: {sec_status_icon} (Saved to {sec_audit_file.relative_to(self.root_dir)})")

        # ----------------------------------------------------
        # 3. Platform & DevOps Auditor による単独チェック (責務分解点監査 & PF協調契約)
        # ----------------------------------------------------
        print(f"☁️ [Audit 3/4 (Loop #{attempt})] Platform & DevOps Auditor inspecting responsibility boundary & cloud contract...", flush=True)
        platform_audit_file = loop_dir / "audit_platform_ops.md"
        prompt_platform = TemplateManager.render(
            "ceremony_2/audit_platform_ops.tpl",
            all_backlogs_str=all_backlogs_str,
            attempt=attempt,
        )
        platform_res = self.gemini_audit_agent.generate_text(prompt_platform)
        platform_text = (platform_res or "").strip()
        CodeParser.atomic_write_text(platform_audit_file, platform_text)
        CodeParser.atomic_write_text(self.eval_dir / "ceremony_2" / "audits" / "audit_platform_ops.md", platform_text)

        platform_passed = "Verdict: **APPROVED**" in platform_text or "Verdict: APPROVED" in platform_text or "**APPROVED**" in platform_text
        platform_status_icon = "✅ APPROVED" if platform_passed else "🛑 VETO/REJECTED"
        print(f"📝 [Audit 3/4 Complete - Loop #{attempt}] Platform & DevOps: {platform_status_icon} (Saved to {platform_audit_file.relative_to(self.root_dir)})")

        # ----------------------------------------------------
        # 4. Ruler による全エピック横断の規律・コンテナ化・ルール腐敗監査
        # ----------------------------------------------------
        print(f"🔍 [Audit 4/4 (Loop #{attempt})] Ruler Persona inspecting cross-epic governance & containerization...", flush=True)
        ruler_audit_file = loop_dir / "audit_ruler_governance.md"
        prompt_ruler = TemplateManager.render(
            "ceremony_2/audit_ruler_governance.tpl",
            all_backlogs_str=all_backlogs_str,
            attempt=attempt,
        )
        ruler_res = self.gemini_audit_agent.generate_text(prompt_ruler)
        ruler_text = (ruler_res or "").strip()
        CodeParser.atomic_write_text(ruler_audit_file, ruler_text)
        CodeParser.atomic_write_text(self.eval_dir / "ceremony_2" / "audits" / "audit_ruler_governance.md", ruler_text)

        ruler_passed = "Verdict: **APPROVED**" in ruler_text or "Verdict: APPROVED" in ruler_text or "**APPROVED**" in ruler_text
        ruler_status_icon = "✅ APPROVED" if ruler_passed else "🛑 VETO/REJECTED"
        print(f"📝 [Audit 4/4 Complete - Loop #{attempt}] Ruler Governance: {ruler_status_icon} (Saved to {ruler_audit_file.relative_to(self.root_dir)})")

        overall_passed = spec_passed and sec_passed and platform_passed and ruler_passed
        summary_data = {
            "loop_attempt": attempt,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "spec_compliance_passed": spec_passed,
            "security_ethics_passed": sec_passed,
            "platform_devops_passed": platform_passed,
            "ruler_governance_passed": ruler_passed,
            "overall_approved": overall_passed
        }
        CodeParser.atomic_write_text(loop_dir / "audit_summary.yaml", yaml.dump(summary_data, default_flow_style=False))

        return {
            "attempt": attempt,
            "spec_passed": spec_passed,
            "sec_passed": sec_passed,
            "platform_passed": platform_passed,
            "ruler_passed": ruler_passed,
            "overall_passed": overall_passed,
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
            raise RuntimeError(
                "❌ [Ceremony 2 Failed] No valid epics extracted from overall debate log! "
                "Halting pipeline to prevent silent execution of mock epics."
            )

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
                extract_prompt = TemplateManager.render(
                    "ceremony_2/extract_spec.tpl",
                    title=title,
                    overall_debate_log=overall_debate_log,
                )
                try:
                    spec_response = gemini_adapter.generate_text(extract_prompt)
                    # 最外層のマークダウンコードブロック枠のみ安全に取り除き、本文中のコードブロックは保護する
                    clean_yaml = (spec_response or "").strip()
                    lines = clean_yaml.splitlines()
                    if lines and lines[0].strip().startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    clean_yaml = "\n".join(lines).strip()
                    CodeParser.atomic_write_text(spec_file, clean_yaml)
                except Exception as e:
                    raise RuntimeError(f"❌ [Ceremony 2 Failed] Failed to extract detailed spec for '{title}' via Gemini: {e}") from e
            
            if not spec_file.exists():
                raise RuntimeError(f"❌ [Ceremony 2 Failed] Specification file {spec_file.name} does not exist for '{title}'!")

            try:
                spec_data = yaml.safe_load(spec_file.read_text(encoding="utf-8")) or {}
                required_personas = spec_data.get("required_personas", [])
                detailed_spec = spec_data.get("detailed_spec", scope)
                if not required_personas:
                    raise ValueError("Field 'required_personas' is empty or missing")
            except Exception as e:
                raise RuntimeError(f"❌ [Ceremony 2 Failed] Failed to parse specification file for '{title}': {e}") from e

            # 対策案B: ハーネスによる補正処理 (エイリアスマップを使用)
            log_personas = extract_personas_from_log_for_epic(overall_debate_log, title, self.formal_to_alias)
            if log_personas:
                required_personas = log_personas
                print(f"  🎯 [Harness Persona Match] Restored persona aliases from overall log: {required_personas}")

            # ⏩ スマート・レジューム判定: 既に全監査（Spec / Security / Ruler）合格済みの監査ログがあるエピックはスキップ
            backlog_file = epic_dir / "epic_backlog.yaml"
            if backlog_file.exists():
                approved = False
                for att_dir in sorted(epic_dir.glob("attempt_*"), reverse=True):
                    spec_f = att_dir / "audit_spec_compliance.md"
                    sec_f = att_dir / "audit_security_ethics.md"
                    r_file = att_dir / "audit_ruler_governance.md"
                    if spec_f.exists() and sec_f.exists() and r_file.exists():
                        spec_ok = "Verdict: **APPROVED**" in spec_f.read_text(encoding="utf-8") or "Verdict: APPROVED" in spec_f.read_text(encoding="utf-8")
                        sec_ok = "Verdict: **APPROVED**" in sec_f.read_text(encoding="utf-8") or "Verdict: APPROVED" in sec_f.read_text(encoding="utf-8")
                        ruler_ok = "Verdict: **APPROVED**" in r_file.read_text(encoding="utf-8") or "Verdict: APPROVED" in r_file.read_text(encoding="utf-8")
                        if spec_ok and sec_ok and ruler_ok:
                            approved = True
                            break
                if approved:
                    print(f"⏩ [Resume Skip] Epic {idx}: {title} は既に全監査合格済みです。即座にスキップして次へ進みます。", flush=True)
                    continue

            # エピックごとの都度監査＆自動リトライループ
            max_retries = getattr(self.config, "max_retries", 3)
            previous_feedback = ""
            for attempt in range(1, max_retries + 1):
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
                self.update_status_dashboard(title, f"🛑 監査不合格 (最大リトライ {max_retries} 回到達) - 安全停止中")
                raise RuntimeError(f"🚨 [Fail-Fast Halt] Epic {idx} ({title}) reached maximum retry limit ({max_retries}) without passing audits! Last feedback: {previous_feedback}")

        # Backlog 分割 & テストハーネス生成
        print("\n🚀 [Ceremony 2] Generating automated test harness scripts for all refined Epics...", flush=True)
        self.update_status_dashboard("All Epics", "テストハーネス生成中...")
        BacklogSplitter.split_all_epics(self.root_dir, self.config)
        TestHarnessGenerator.generate_all(self.root_dir, self.config)

        # 🛡️ 全体独立監査ゲートのスマート・レジューム判定:
        # 既存の loop_* ディレクトリの最新 audit_summary.yaml を確認し、既に全体承認 (overall_approved: true) されていれば再監査をスキップ
        latest_approved_loop = None
        for loop_d in sorted(self.eval_dir.glob("loop_*"), key=lambda p: int(p.name.split("_")[1]) if p.name.split("_")[1].isdigit() else 0, reverse=True):
            summary_f = loop_d / "audit_summary.yaml"
            if summary_f.exists():
                try:
                    s_data = yaml.safe_load(summary_f.read_text(encoding="utf-8")) or {}
                    if s_data.get("overall_approved", False):
                        latest_approved_loop = (loop_d, s_data)
                        break
                except Exception:
                    pass

        if latest_approved_loop:
            loop_dir, s_data = latest_approved_loop
            print(f"\n⏩ [Resume Skip] 全体独立監査は既に {loop_dir.name} にて全者承認 (APPROVED) 済みです。再監査をスキップして即座に Ceremony 3 へ進みます！", flush=True)
            self.update_status_dashboard("All Epics", f"リファインメント完了 (監査 {loop_dir.name} 承認済み)")
            return True

        # 🛡️ Gemini による各自独立監査ゲートの実行 (loop_N ディレクトリ構造で履歴管理)
        audit_result = self.run_individual_final_audits(attempt=current_attempt)

        print("\n" + "=" * 50)
        print(f"🏁 [Ceremony 2 Final Gate Summary - Directory: {audit_result['loop_dir'].relative_to(self.root_dir)}]")
        print(f"  - Loop Attempt Count: #{audit_result['attempt']}")
        print(f"  - Spec Compliance Audit: {'✅ PASS' if audit_result['spec_passed'] else '🛑 REJECTED/VETO'}")
        print(f"  - Security & Ethics Audit: {'✅ PASS' if audit_result['sec_passed'] else '🛑 REJECTED/VETO'}")
        print(f"  - Ruler Governance Audit: {'✅ PASS' if audit_result.get('ruler_passed', False) else '🛑 REJECTED/VETO'}")
        print(f"  - Final Verdict: {'🎉 ALL APPROVED' if audit_result['overall_passed'] else '🛑 VETO DETECTED (Halting Execution)'}")
        print("=" * 50 + "\n")

        if not audit_result["overall_passed"]:
            self.update_status_dashboard("All Epics", f"🛑 全体監査不合格 (VETO) - 安全停止中 (Loop #{audit_result['attempt']})")
            raise RuntimeError(
                f"🚨 [Fail-Fast Halt] Ceremony 2 Final Audits VETOED in Loop #{audit_result['attempt']}! "
                f"Spec: {'PASS' if audit_result['spec_passed'] else 'FAIL'}, "
                f"Sec: {'PASS' if audit_result['sec_passed'] else 'FAIL'}, "
                f"Ruler: {'PASS' if audit_result.get('ruler_passed', False) else 'FAIL'}. "
                f"Halting execution immediately to prevent unverified tasks from proceeding to implementation."
            )

        self.update_status_dashboard("All Epics", f"リファインメント完了 (監査 Loop #{audit_result['attempt']})")
        print(f"🎉 [Ceremony 2 Complete] Sprint Refinement & Independent Final Audits saved in {audit_result['loop_dir'].relative_to(self.root_dir)}!", flush=True)
        return True
