import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser
from runner.utils.context_loader import ContextLoader
from runner.utils.template_manager import TemplateManager
from runner.adapters.llm_adapter import LLMAdapterFactory


class EpicRefinementEngine:
    """【セレモニー 1】全体アーキテクチャ・ディベート & エピックリファインメントエンジン (Dependencies 完備版)"""

    def __init__(self, root_dir: Path, config: ProjectConfig = None):
        self.root_dir = root_dir
        self.config = config or ProjectConfig.load(root_dir)
        self.init_dir = root_dir / self.config.initiatives_dir
        self.eval_dir = root_dir / self.config.evaluator_dir
        self.status_file = root_dir / self.config.status_file

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
                return data.get("DEFAULT_LLM_PROVIDER", "gemini")
            except Exception:
                pass
        return "gemini"

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

        print("🌐 [Ceremony 1: Epic Refinement] Conducting Architecture Debate & Epic Breakdown...", flush=True)
        self.update_status_dashboard("💬 全ペルソナによる全体アーキテクチャディベート中...")

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="1_epic_refinement", include_dev_rules=True, config=self.config)
        inst_file_rel = "agents/1_epic_refinement/epic_refinement_planner.md"

        prompt = TemplateManager.render(
            "ceremony_1/debate.tpl",
            rules=refs['rules'],
            specs=refs['specs'],
            personas=refs['personas'],
            target_agent=refs['target_agent'],
            inst_file_rel=inst_file_rel,
        )

        actual_prompt_file = self.eval_dir / "actual_ceremony_1_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)

        print("🔍 [Ceremony 1] Requesting Overall Architecture Debate Log from LLM...", flush=True)
        llm_raw_response = self.refinement_agent.generate_text(prompt)
        overall_debate_log = (llm_raw_response or "").strip()

        if len(overall_debate_log) >= 500 and ("## 1." in overall_debate_log or "Debate" in overall_debate_log):
            CodeParser.atomic_write_text(overall_debate_file, overall_debate_log)
            print(f"📝 [Ceremony 1 Complete] Successfully generated and saved debate log to {overall_debate_file.relative_to(self.root_dir)}")
            return overall_debate_log

        CodeParser.atomic_write_text(overall_debate_file, overall_debate_log)
        print(f"\n⚠️ [Ceremony 1 Halted] Insufficient debate content ({len(overall_debate_log)} chars). Saved raw output to {overall_debate_file.relative_to(self.root_dir)}")
        raise RuntimeError("❌ [Ceremony 1 Failed] Failed to generate valid overall architecture debate log on 1st attempt.")

    def review_tripartite_governance(self, debate_log: str) -> bool:
        """セレモニー 1 で生成された overall_debate_log に対する3者独立レビュー（コスト・技術・責任の分離判定）"""
        review_cost_file = self.eval_dir / "ceremony_1_review_cost.md"
        review_tech_file = self.eval_dir / "ceremony_1_review_tech.md"
        review_scope_file = self.eval_dir / "ceremony_1_review_scope.md"

        # 中断再開チェック（既に3つとも APPROVED で存在する場合はスキップ）
        if review_cost_file.exists() and review_tech_file.exists() and review_scope_file.exists():
            c_text = review_cost_file.read_text(encoding="utf-8")
            t_text = review_tech_file.read_text(encoding="utf-8")
            s_text = review_scope_file.read_text(encoding="utf-8")
            c_ok = ("Verdict: **APPROVED**" in c_text or "APPROVED" in c_text) and "**VETO**" not in c_text and "Verdict: VETO" not in c_text
            t_ok = ("Verdict: **APPROVED**" in t_text or "APPROVED" in t_text) and "**VETO**" not in t_text and "Verdict: VETO" not in t_text
            s_ok = ("Verdict: **APPROVED**" in s_text or "APPROVED" in s_text) and "**VETO**" not in s_text and "Verdict: VETO" not in s_text
            if c_ok and t_ok and s_ok:
                print("⏯️ [Ceremony 1 Review 中断再開] 3者レビューログが全て APPROVED で存在するためスキップします。")
                return True

        print("\n" + "=" * 70)
        print("⚖️ [Ceremony 1: 3者ディベートによるコスト・技術・責任の独立レビュー判定開始]")
        print("=" * 70, flush=True)

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="1_epic_refinement", include_dev_rules=True, config=self.config)

        # 1. コストの分離・判断 (FinOps & Cost Governance)
        print("💰 [Ceremony 1 Review 1/3] FinOps & Cost Governance Auditor inspecting Rate Limiting & Over-Engineering...", flush=True)
        finops_persona_file = self.root_dir / ".agents" / "personas" / "finops_cost_governance.md"
        finops_content = finops_persona_file.read_text(encoding="utf-8") if finops_persona_file.exists() else refs['personas']

        prompt_cost = TemplateManager.render(
            "ceremony_1/review_cost.tpl",
            finops_directives=finops_content,
            debate_log=debate_log,
        )
        cost_res = self.refinement_agent.generate_text(prompt_cost)
        cost_text = (cost_res or "").strip()
        CodeParser.atomic_write_text(review_cost_file, cost_text)
        print(f"  📝 Saved FinOps cost review to {review_cost_file.relative_to(self.root_dir)}")

        # 2. 技術の分離・判断 (Software Architect & Ruler)
        print("🏛️ [Ceremony 1 Review 2/3] Software Architect & Ruler inspecting Clean Architecture & Rules...", flush=True)
        prompt_tech = TemplateManager.render(
            "ceremony_1/review_tech.tpl",
            tech_rules=refs['rules'],
            debate_log=debate_log,
        )
        tech_res = self.refinement_agent.generate_text(prompt_tech)
        tech_text = (tech_res or "").strip()
        CodeParser.atomic_write_text(review_tech_file, tech_text)
        print(f"  📝 Saved Tech architecture review to {review_tech_file.relative_to(self.root_dir)}")

        # 3. 責任・仕様の分離・判断 (PO & Spec Compliance Auditor)
        print("📋 [Ceremony 1 Review 3/3] Spec Compliance Auditor & PO inspecting Specifications & Scope...", flush=True)
        prompt_scope = TemplateManager.render(
            "ceremony_1/review_scope.tpl",
            specs=refs['specs'],
            debate_log=debate_log,
        )
        scope_res = self.refinement_agent.generate_text(prompt_scope)
        scope_text = (scope_res or "").strip()
        CodeParser.atomic_write_text(review_scope_file, scope_text)
        print(f"  📝 Saved Spec compliance review to {review_scope_file.relative_to(self.root_dir)}")

        # 判定検証
        cost_pass = ("Verdict: **APPROVED**" in cost_text or "APPROVED" in cost_text) and "**VETO**" not in cost_text and "Verdict: VETO" not in cost_text
        tech_pass = ("Verdict: **APPROVED**" in tech_text or "APPROVED" in tech_text) and "**VETO**" not in tech_text and "Verdict: VETO" not in tech_text
        scope_pass = ("Verdict: **APPROVED**" in scope_text or "APPROVED" in scope_text) and "**VETO**" not in scope_text and "Verdict: VETO" not in scope_text

        print("\n" + "-" * 50)
        print("📊 [Ceremony 1 Tripartite Review Verdicts]")
        print(f"  💰 1. Cost & FinOps     : {'✅ APPROVED' if cost_pass else '❌ VETO'}")
        print(f"  🏛️ 2. Tech & Architect  : {'✅ APPROVED' if tech_pass else '❌ VETO'}")
        print(f"  📋 3. Scope & PO        : {'✅ APPROVED' if scope_pass else '❌ VETO'}")
        print("-" * 50 + "\n", flush=True)

        if not (cost_pass and tech_pass and scope_pass):
            failed = []
            if not cost_pass: failed.append("Cost/FinOps (Rate Limiting or unrequested feature detected)")
            if not tech_pass: failed.append("Tech/Architect (Architecture or rule violation detected)")
            if not scope_pass: failed.append("Scope/PO (Dropped specification or scope leak detected)")
            raise RuntimeError(f"❌ [Ceremony 1 VETO] Tripartite review failed: {', '.join(failed)}. Check state/.evaluator/ceremony_1_review_*.md for details.")

        print("🎉 [Ceremony 1 Tripartite Review Passed] All 3 personas (Cost, Tech, Scope) APPROVED the overall architecture & Epics!\n", flush=True)
        return True

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

        # 3. Match H3/H4 headers (e.g. ### **Epic 1: ...** or ### Epic 1 ...)
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

        # 4. Match Multiline Markdown list items (- **Epic 1 <Title>**:\n  - Background: ...\n  - Scope: ...)
        list_matches = list(re.finditer(r"(?:^|\n)\s*-\s*\*\*(Epic\s*\d+[^:\n*]*[:\s\-]+[^\n*]+)\*\*:\s*\n?(.*?)(?=(?:\n\s*-\s*\*\*Epic\s*\d+)|\Z)", section_text, re.DOTALL | re.IGNORECASE))
        if list_matches:
            for m in list_matches:
                t = m.group(1).strip()
                s = m.group(2).strip()
                if t and not t.startswith("[") and not t.lower().startswith("epic 1 <title>"):
                    epics.append({
                        "id": f"EPIC-{len(epics)+1}",
                        "title": t,
                        "scope": s
                    })
            if epics:
                return epics

        # 5. Fallback single-line match
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
