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
    """【セレモニー 2】スプリントリファインメントエンジン (スプリントバックログ & 自動ハーネス生成)"""

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

    def update_status_dashboard(self, epic_name: str):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dashboard_content = f"""# 📌 Loop AI Lab - リアルタイム Scrum 進行状況ダッシュボード

- **現在実行中のフェーズ**: ⚙️ 【セレモニー 2】スプリントバックログ・リファインメント
- **対象エピック**: `{epic_name}`
- **ステータス**: バックログ分解およびテストハーネス生成中...
- **最終更新日時**: `{now_str}`

---

## 📊 全エピック進捗ステータス
- ⚙️ {epic_name} をリファインメント中
"""
        CodeParser.atomic_write_text(self.status_file, dashboard_content)
        print(f"📊 [Status Dashboard] Updated state/status.md (Refinement: {epic_name})", flush=True)

    def run_sprint_refinement_for_epic(self, epic_dir: Path, title: str, scope: str):
        debate_file = epic_dir / "debate_log.md"
        backlog_file = epic_dir / "epic_backlog.yaml"

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="2_sprint_refinement", include_dev_rules=True, config=self.config)
        inst_file_rel = "agents/2_sprint_refinement/sprint_refinement_planner.md"

        # 1. debate_log.md 生成
        if not debate_file.exists():
            print(f"💬 [Ceremony 2] Step 1: Generating debate_log.md for: {title}...", flush=True)
            self.update_status_dashboard(title)
            
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
                "- **[PO Persona]**: Breakdown of user stories and acceptance criteria.\n"
                "- **[Architect Persona]**: Micro-task boundaries and TDD test design.\n"
                "- **[Spec Compliance Persona]**: Traceability check against specifications.\n"
                "- **[QA & DevOps Persona]**: Automated test harness and verification commands.\n"
                "[/INST]\n"
            )
            res = self.refinement_agent.generate_text(prompt_debate)
            CodeParser.atomic_write_text(debate_file, (res or "").strip())

        # 2. epic_backlog.yaml 生成
        if not backlog_file.exists():
            print(f"📝 [Ceremony 2] Step 2: Generating epic_backlog.yaml for: {title}...", flush=True)
            self.update_status_dashboard(title)

            prompt_yaml = (
                f"[INST]\n"
                f"[TASK: GENERATE EPIC BACKLOG YAML FOR {title}]\n"
                f"Generate a valid YAML block containing micro-scoped tasks for {title}.\n"
                f"Target workspace directory is: {self.config.workspace_rel}\n"
                f"Container image name is: {self.config.container_image_name}\n\n"
                f"=== SCOPE ===\n{scope}\n\n"
                "Output MUST be a valid YAML block enclosed in ```yaml ... ```:\n"
                "```yaml\n"
                "epic_id: EPIC-X\n"
                f"title: \"{title}\"\n"
                f"workspace_rel: \"{self.config.workspace_rel}\"\n"
                "tasks:\n"
                "  - id: TASK-1.1\n"
                "    title: \"Implement core functionality\"\n"
                "    description: \"Detailed description\"\n"
                "    acceptance_criteria:\n"
                "      - \"Criterion 1\"\n"
                "      - \"Criterion 2\"\n"
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
                    "epic_id": epic_dir.name.upper(),
                    "title": title,
                    "workspace_rel": self.config.workspace_rel,
                    "container_image_name": self.config.container_image_name,
                    "tasks": [
                        {
                            "id": "TASK-1.1",
                            "title": f"Setup {title}",
                            "description": scope,
                            "acceptance_criteria": ["Core components implemented", "All tests pass"],
                            "verify_command": self.config.test_command
                        }
                    ]
                }
                CodeParser.atomic_write_text(backlog_file, yaml.dump(mock_data, default_flow_style=False, allow_unicode=True))

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
            self.run_sprint_refinement_for_epic(epic_dir, title, scope)

        # Backlog 分割 & テストハーネス生成
        print("\n🚀 [Ceremony 2] Generating automated test harness scripts for all refined Epics...", flush=True)
        self.update_status_dashboard("All Epics")
        BacklogSplitter.split_all_epics(self.root_dir, self.config)
        TestHarnessGenerator.generate_all(self.root_dir, self.config)
        self.update_status_dashboard("All Epics")
        print("🎉 [Ceremony 2 Complete] Sprint Refinement pipeline completed successfully for all Epics!", flush=True)
        return True
