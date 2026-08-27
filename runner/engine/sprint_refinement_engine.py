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
    """【セレモニー 2】スプリントバックログリファインメント & ハーネス生成エンジン (status.md 自動更新)"""

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

## 📊 全エピック進捗ステータス
{epic_summary_block}
"""
        CodeParser.atomic_write_text(self.status_file, dashboard_content)
        print(f"📊 [Status Dashboard] Updated state/status.md (Refinement: {current_epic_title})", flush=True)

    def run_sprint_refinement_for_epic(self, epic_dir: Path, title: str, scope: str):
        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="2_sprint_refinement", include_dev_rules=True)
        
        # Step 1: debate_log.md
        debate_file = epic_dir / "debate_log.md"
        if not debate_file.exists():
            print(f"💬 [Ceremony 2] Step 1: Generating debate_log.md for: {title}...", flush=True)
            self.update_status_dashboard(title)
            
            prompt1 = (
                f"[TASK: CEREMONY 2 SPRINT REFINEMENT DEBATE - {title}]\n"
                f"Scope: {scope}\n\n"
                f"=== 1. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
                f"=== 2. REPOSITORY & DEV RULES ===\n{refs['rules']}\n\n"
                f"=== 3. MULTI-PERSONA INSTRUCTIONS ===\n{refs['personas']}\n\n"
                "【INSTRUCTION】\n"
                f"Generate the Ceremony 2 Sprint Refinement Debate Log for '{title}'.\n"
                "Start directly with:\n"
                f"# 💬 Epic Architecture Debate Log: {title}\n\n"
                "## 1. Multi-Persona Discussion\n"
                f"- **[Scrum Master Persona]**: Welcome team to refinement for {title}. Enforce DoR and scoping.\n"
                "- **[PO Persona]**: Acceptance criteria and business goals.\n"
                "- **[Architect Persona]**: Layer structure and design.\n"
                "- **[Anti-Complexity Persona]**: Challenge over-engineering, enforce KISS/YAGNI.\n"
                "- **[Capacity Guardian Persona]**: Confirm micro-sized task units.\n"
                "- **[QA & DevOps Personas]**: Test verification and CI readiness.\n"
            )
            
            llm_res1 = self.refinement_agent.generate_text(prompt1)
            debate_prefix = f"# 💬 Epic Architecture Debate Log: {title}\n\n## 1. Multi-Persona Discussion\n- **[Scrum Master Persona]**: Welcome team to the refinement session for {title}. Let us review the primary business goals and architectural constraints.\n"
            content1 = (debate_prefix + llm_res1.strip()) if (llm_res1 and not llm_res1.strip().startswith("#")) else (llm_res1 or debate_prefix)
            CodeParser.atomic_write_text(debate_file, content1)

        # Step 2: epic_backlog.yaml
        backlog_file = epic_dir / "epic_backlog.yaml"
        if not backlog_file.exists():
            print(f"📝 [Ceremony 2] Step 2: Generating epic_backlog.yaml for: {title}...", flush=True)
            self.update_status_dashboard(title)
            
            prompt2 = (
                f"[TASK: CEREMONY 2 SPRINT BACKLOG YAML - {title}]\n"
                f"Scope: {scope}\n\n"
                f"=== 1. RULES & PERSONAS ===\n{refs['rules']}\n\n"
                "【INSTRUCTION】\n"
                "Generate a valid YAML epic backlog. Output ONLY raw YAML starting with ```yaml.\n"
                "```yaml\n"
                f"epic: {title}\n"
                f"scope: {scope}\n"
                f"target_workspace: {self.config.workspace_rel or 'workspace/app'}\n"
                f"container_image_name: {self.config.container_image_name or 'app'}\n"
                "tasks:\n"
                "  - id: TASK-1.1\n"
                "    title: Core functionality implementation\n"
                "    description: Implement core domain logic\n"
                "    acceptance_criteria:\n"
                "      - Core unit test passes\n"
                "```"
            )
            
            llm_res2 = self.refinement_agent.generate_text(prompt2)
            raw_yaml_match = re.search(r"```(?:yaml)?\n(.*?)```", llm_res2, re.DOTALL)
            yaml_content = raw_yaml_match.group(1).strip() if raw_yaml_match else llm_res2.strip()
            
            try:
                yaml.safe_load(yaml_content)
                CodeParser.atomic_write_text(backlog_file, yaml_content)
                print(f"📝 [Ceremony 2] Saved direct epic_backlog.yaml for: {epic_dir.name}")
            except Exception:
                mock_data = {
                    "epic": title,
                    "scope": scope,
                    "target_workspace": self.config.workspace_rel or "workspace/app",
                    "container_image_name": self.config.container_image_name or "app",
                    "tasks": [
                        {
                            "id": "TASK-1.1",
                            "title": f"Implement core functionality for {title}",
                            "description": scope,
                            "acceptance_criteria": ["Core unit tests must pass with 100% success"]
                        }
                    ]
                }
                CodeParser.atomic_write_text(backlog_file, yaml.dump(mock_data, default_flow_style=False, allow_unicode=True))

    def run_sprint_refinement(self, overall_debate_log: str):
        print("🚀 [Ceremony 2: Sprint Refinement] Executing Sprint Backlog Refinement...", flush=True)
        
        epics = self.extract_epics_from_log(overall_debate_log)
        if not epics:
            epics = [{"title": "Epic 1 Core Foundation", "scope": "Core application logic and interface endpoints"}]

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
        pattern = r"(?:^|\n)##\s*2\.\s*Epic\s*Breakdown.*?\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, debate_log, re.DOTALL | re.IGNORECASE)
        if match:
            lines = match.group(1).strip().splitlines()
            for line in lines:
                m_epic = re.search(r"^\s*-\s*\*\*([^\*]+)\*\*:\s*(.*)", line)
                if m_epic:
                    epics.append({
                        "title": m_epic.group(1).strip(),
                        "scope": m_epic.group(2).strip()
                    })
        return epics
