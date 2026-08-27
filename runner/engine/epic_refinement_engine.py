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
    """【セレモニー 1】2段階エピックリファインメントエンジン (完全ファイル委譲 & Fail-Fast 設計)"""

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

    def run_stage_1_epic_breakdown(self, max_retries: int = 3) -> list:
        """第1段階: 仕様からエピックへの分解 (Stage 1: Epic Breakdown)"""
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
        inst_file_rel = "agents/1_epic_refinement/stage_1_epic_breakdown.md"

        prompt = (
            f"[TASK: CEREMONY 1 STAGE 1 - EPIC BREAKDOWN]\n"
            f"Recursively read and analyze all referenced files and directories listed below to execute this task.\n\n"
            f"=== 1. EXECUTION INSTRUCTIONS ===\n- {inst_file_rel}\n\n"
            f"=== 2. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
            f"=== 3. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
            f"=== 4. MULTI-PERSONA DEFINITIONS ===\n{refs['personas']}\n\n"
            "【MANDATORY OUTPUT FORMAT】\n"
            "Respond ONLY with valid YAML wrapped inside ```yaml codeblock containing the 'epics' list."
        )

        actual_prompt_file = self.eval_dir / "actual_ceremony_1_stage_1_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)

        for attempt in range(1, max_retries + 1):
            print(f"🔍 [Ceremony 1: Stage 1] Requesting Epics YAML from LLM (Attempt {attempt}/{max_retries})...", flush=True)
            llm_res = self.refinement_agent.generate_text(prompt)
            
            raw_yaml_match = re.search(r"```(?:yaml)?\n(.*?)```", llm_res or "", re.DOTALL)
            yaml_content = raw_yaml_match.group(1).strip() if raw_yaml_match else (llm_res or "").strip()

            epics = []
            try:
                parsed = yaml.safe_load(yaml_content) or {}
                if isinstance(parsed, dict) and "epics" in parsed and isinstance(parsed["epics"], list):
                    epics = [e for e in parsed["epics"] if isinstance(e, dict) and "title" in e]
                elif isinstance(parsed, list):
                    epics = [e for e in parsed if isinstance(e, dict) and "title" in e]
            except Exception as e:
                print(f"⚠️ [Stage 1 YAML Parse Error] {e}")

            if epics:
                CodeParser.atomic_write_text(epics_yaml_file, yaml.dump({"epics": epics}, default_flow_style=False, allow_unicode=True))
                print(f"📝 [Stage 1 Complete] Successfully extracted and saved {len(epics)} epics to {epics_yaml_file.relative_to(self.root_dir)}")
                return epics
            
            print(f"⚠️ [Stage 1 Warning] Attempt {attempt} failed to parse valid epics list from LLM response (Response length: {len(llm_res or '')} chars). Retrying...")

        raise RuntimeError(f"❌ [Stage 1 Failed] Failed to extract valid epics list from LLM after {max_retries} attempts! Pipeline safely halted.")

    def run_stage_2_overall_refinement(self, epics: list, max_retries: int = 3) -> str:
        """第2段階: 全体アーキテクチャ・エピックリファインメント (Stage 2: Overall Refinement)"""
        overall_debate_file = self.eval_dir / "overall_debate_log.md"
        
        if overall_debate_file.exists():
            content = overall_debate_file.read_text(encoding="utf-8").strip()
            if len(content) > 500:
                print("⏯️ [EpicRefinementEngine Stage 2] 既存の overall_debate_log.md を再利用します。")
                return content

        print("🌐 [Ceremony 1: Stage 2] Conducting full multi-persona architectural debate...", flush=True)
        self.update_status_dashboard("Stage 2: Overall Refinement", "全ペルソナによる全体アーキテクチャディベート中...")

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="1_epic_refinement", include_dev_rules=True)
        inst_file_rel = "agents/1_epic_refinement/stage_2_overall_refinement.md"
        epics_yaml_str = yaml.dump({"epics": epics}, default_flow_style=False, allow_unicode=True)

        prompt = (
            f"[TASK: CEREMONY 1 STAGE 2 - OVERALL REFINEMENT DEBATE]\n"
            f"Recursively read and analyze all referenced files and directories listed below to execute this task.\n\n"
            f"=== 1. EXECUTION INSTRUCTIONS ===\n- {inst_file_rel}\n\n"
            f"=== 2. EXTRACTED EPICS (FROM STAGE 1) ===\n{epics_yaml_str}\n\n"
            f"=== 3. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
            f"=== 4. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
            f"=== 5. MULTI-PERSONA DEFINITIONS ===\n{refs['personas']}\n"
        )

        actual_prompt_file = self.eval_dir / "actual_ceremony_1_stage_2_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)

        for attempt in range(1, max_retries + 1):
            print(f"🔍 [Ceremony 1: Stage 2] Requesting Architecture Debate Log from LLM (Attempt {attempt}/{max_retries})...", flush=True)
            llm_raw_response = self.refinement_agent.generate_text(prompt)
            
            prefix = "# 🌐 Overall System Architecture & Epic Refinement Debate Log\n\n"
            if llm_raw_response and not llm_raw_response.strip().startswith("#"):
                overall_debate_log = prefix + llm_raw_response.strip()
            else:
                overall_debate_log = (llm_raw_response or "").strip()

            if len(overall_debate_log) >= 500 and "## 1. Multi-Persona Discussion" in overall_debate_log:
                CodeParser.atomic_write_text(overall_debate_file, overall_debate_log)
                print(f"📝 [Stage 2 Complete] Saved authentic debate log ({len(overall_debate_log)} chars) to {overall_debate_file.relative_to(self.root_dir)}")
                return overall_debate_log
            
            print(f"⚠️ [Stage 2 Warning] Attempt {attempt} returned insufficient debate content ({len(overall_debate_log)} chars). Retrying...")

        raise RuntimeError(f"❌ [Stage 2 Failed] Failed to generate valid architecture debate log from LLM after {max_retries} attempts! Pipeline safely halted.")

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

        if not epics:
            raise RuntimeError("❌ [Epic Extraction Failed] Could not extract any epics from debate log or epics.yaml!")
        return epics

    def run_epic_refinement(self) -> str:
        # Step 1: Epic Breakdown (SM, PO, Architect, Platform/DevOps, Spec Compliance) -> epics.yaml
        epics = self.run_stage_1_epic_breakdown()

        # Step 2: Overall Refinement Debate -> overall_debate_log.md
        overall_debate_log = self.run_stage_2_overall_refinement(epics)
        return overall_debate_log
