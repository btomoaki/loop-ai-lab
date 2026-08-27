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


class SprintRefinementEngine:
    """【セレモニー 2】スプリントバックログリファインメント & ハーネス生成エンジン (完全ファイル委譲 & Fail-Fast 設計)"""

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
                return data.get("DEFAULT_LLM_PROVIDER", "local")
            except Exception:
                pass
        return "local"

    def update_status_dashboard(self, current_epic_title: str):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        epic_dirs = sorted([d for d in self.init_dir.glob("epic_*") if d.is_dir()])
        epic_rows = []
        for d in epic_dirs:
            bk = d / "epic_backlog.yaml"
            if bk.exists():
                epic_rows.append(f"- **{d.name}**: ✅ リファインメント完了 (バックログ & ハーネス配備済)")
            else:
                epic_rows.append(f"- **{d.name}**: ⏳ リファインメント進行中")
        
        epic_summary_block = "\n".join(epic_rows) if epic_rows else "- エピック分解・リファインメント準備中..."

        dashboard_content = f"""# 📌 Loop AI Lab - リアルタイム Scrum 進行状況ダッシュボード

- **現在実行中のフェーズ**: 🚀 【セレモニー 2】スプリントバックログ・リファインメント
- **処理中エピック**: `{current_epic_title}`
- **最終更新日時**: `{now_str}`

---

## �� 全エピック進捗ステータス
{epic_summary_block}
"""
        CodeParser.atomic_write_text(self.status_file, dashboard_content)
        print(f"📊 [Status Dashboard] Updated state/status.md (Refinement: {current_epic_title})", flush=True)

    def run_sprint_refinement_for_epic(self, epic_dir: Path, title: str, scope: str, max_retries: int = 3):
        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="2_sprint_refinement", include_dev_rules=True)
        inst_file_rel = "agents/2_sprint_refinement/sprint_refinement_planner.md"
        
        # Step 1: debate_log.md
        debate_file = epic_dir / "debate_log.md"
        if not debate_file.exists():
            print(f"💬 [Ceremony 2] Step 1: Generating debate_log.md for: {title}...", flush=True)
            self.update_status_dashboard(title)
            
            prompt1 = (
                f"[TASK: CEREMONY 2 SPRINT REFINEMENT DEBATE - {title}]\n"
                f"Recursively read and analyze all referenced files and directories listed below to execute this task.\n\n"
                f"Target Epic Title: {title}\n"
                f"Target Epic Scope: {scope}\n\n"
                f"=== 1. EXECUTION INSTRUCTIONS ===\n- {inst_file_rel}\n\n"
                f"=== 2. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
                f"=== 3. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
                f"=== 4. MULTI-PERSONA DEFINITIONS ===\n{refs['personas']}\n"
            )
            
            for attempt in range(1, max_retries + 1):
                print(f"🔍 [Ceremony 2] Requesting Debate Log for '{title}' (Attempt {attempt}/{max_retries})...", flush=True)
                llm_res1 = self.refinement_agent.generate_text(prompt1)
                
                prefix = f"# 💬 Epic Architecture Debate Log: {title}\n\n"
                if llm_res1 and not llm_res1.strip().startswith("#"):
                    content1 = prefix + llm_res1.strip()
                else:
                    content1 = (llm_res1 or "").strip()

                if len(content1) >= 400 and ("## 1. Multi-Persona Discussion" in content1 or "## 2. Debate Log" in content1 or "Scrum Master" in content1):
                    CodeParser.atomic_write_text(debate_file, content1)
                    print(f"📝 [Ceremony 2] Saved debate_log.md ({len(content1)} chars) for: {epic_dir.name}")
                    break
                print(f"⚠️ [Ceremony 2 Warning] Debate response insufficient for {title} ({len(content1)} chars). Retrying...")
            else:
                raise RuntimeError(f"❌ [Ceremony 2 Failed] Could not generate valid debate_log.md for '{title}' after {max_retries} attempts!")

        # Step 2: epic_backlog.yaml
        backlog_file = epic_dir / "epic_backlog.yaml"
        if not backlog_file.exists():
            print(f"📝 [Ceremony 2] Step 2: Generating epic_backlog.yaml for: {title}...", flush=True)
            self.update_status_dashboard(title)
            
            target_ws_rel = self.config.workspace_rel or "workspace/app"
            img_name = self.config.container_image_name or "app"

            prompt2 = (
                f"[TASK: CEREMONY 2 SPRINT BACKLOG YAML - {title}]\n"
                f"Recursively read and analyze all referenced files and directories listed below to execute this task.\n\n"
                f"Target Epic Title: {title}\n"
                f"Target Epic Scope: {scope}\n"
                f"Target Workspace: {target_ws_rel}\n"
                f"Container Image: {img_name}\n\n"
                f"=== 1. EXECUTION INSTRUCTIONS ===\n- {inst_file_rel}\n\n"
                f"=== 2. DEBATE DECISIONS ===\n{debate_file.read_text(encoding='utf-8')}\n\n"
                f"=== 3. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
                "【MANDATORY OUTPUT FORMAT】\n"
                "Output ONLY valid YAML wrapped in ```yaml codeblock containing 'epic', 'scope', 'target_workspace', and 'tasks' list."
            )
            
            for attempt in range(1, max_retries + 1):
                print(f"🔍 [Ceremony 2] Requesting Backlog YAML for '{title}' (Attempt {attempt}/{max_retries})...", flush=True)
                llm_res2 = self.refinement_agent.generate_text(prompt2)
                
                raw_yaml_match = re.search(r"```(?:yaml)?\n(.*?)```", llm_res2 or "", re.DOTALL)
                yaml_content = raw_yaml_match.group(1).strip() if raw_yaml_match else (llm_res2 or "").strip()
                
                try:
                    parsed = yaml.safe_load(yaml_content) or {}
                    if isinstance(parsed, dict) and "tasks" in parsed and isinstance(parsed["tasks"], list) and len(parsed["tasks"]) > 0:
                        if "target_workspace" not in parsed:
                            parsed["target_workspace"] = target_ws_rel
                        if "epic" not in parsed:
                            parsed["epic"] = title
                        
                        CodeParser.atomic_write_text(backlog_file, yaml.dump(parsed, default_flow_style=False, allow_unicode=True))
                        print(f"📝 [Ceremony 2] Saved valid epic_backlog.yaml with {len(parsed['tasks'])} tasks for: {epic_dir.name}")
                        break
                except Exception as e:
                    print(f"⚠️ [Ceremony 2 YAML Parse Error] {e}")

                print(f"⚠️ [Ceremony 2 Warning] Attempt {attempt} failed to parse valid backlog YAML for {title}. Retrying...")
            else:
                raise RuntimeError(f"❌ [Ceremony 2 Failed] Failed to generate valid epic_backlog.yaml for '{title}' after {max_retries} attempts!")

    def run_sprint_refinement(self, overall_debate_log: str):
        print("🚀 [Ceremony 2: Sprint Refinement] Executing Sprint Backlog Refinement...", flush=True)
        
        epics = self.extract_epics_from_log(overall_debate_log)
        if not epics:
            raise RuntimeError("❌ [Ceremony 2 Failed] No epics available for refinement!")

        for idx, ep in enumerate(epics, 1):
            title = ep["title"]
            scope = ep["scope"]
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', title).lower().strip('_')
            clean_name = re.sub(r'_+', '_', clean_name)
            epic_dir_name = f"epic_{idx}_{clean_name}" if not clean_name.startswith(f"epic_{idx}") else clean_name
            epic_dir = self.init_dir / epic_dir_name
            epic_dir.mkdir(parents=True, exist_ok=True)
            
            self.run_sprint_refinement_for_epic(epic_dir, title, scope)

        # Backlog 分割 & テストハーネス生成
        print("🚀 [Ceremony 2] Step 2: Generating automated test harness scripts...", flush=True)
        self.update_status_dashboard("All Epics")
        BacklogSplitter.split_all_epics(self.root_dir, self.config)
        TestHarnessGenerator.generate_all(self.root_dir, self.config)
        self.update_status_dashboard("All Epics")
        print("🎉 [Ceremony 2 Complete] Sprint Refinement pipeline completed successfully!", flush=True)
        return True

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
            raise RuntimeError("❌ [Epic Extraction Failed] Could not extract any epics for Ceremony 2!")
        return epics
