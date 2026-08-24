import os
import yaml
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser
from runner.utils.context_loader import ContextLoader
from runner.utils.backlog_splitter import BacklogSplitter
from runner.generators.harness_generator import HarnessGenerator
from runner.adapters.llm_adapter import LLMAdapterFactory


class SprintRefinementEngine:
    """【セレモニー 2】スプリントバックログリファインメントエンジン"""

    def __init__(self, root_dir: Path, config: ProjectConfig = None):
        self.root_dir = root_dir
        self.config = config or ProjectConfig.load(root_dir)
        self.init_dir = root_dir / "state" / "initiatives"
        self.eval_dir = root_dir / "state" / ".evaluator"
        self.init_dir.mkdir(parents=True, exist_ok=True)

        refinement_provider = self._get_refinement_provider()
        self.refinement_agent = LLMAdapterFactory.get_adapter(provider=refinement_provider)

    def _get_refinement_provider(self) -> str:
        config_file = self.root_dir / "config.yaml"
        if config_file.exists():
            try:
                data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
                return data.get("REFINEMENT_PROVIDER", "gemini")
            except Exception:
                pass
        return "gemini"

    def refine_single_epic(self, dir_name: str, title: str, scope: str, epic_idx: int):
        """Step 1: debate_log.md を出力。 Step 2: epic_backlog.yaml を直接生成。各チェックポイント対応。"""
        epic_folder = self.init_dir / dir_name
        epic_folder.mkdir(parents=True, exist_ok=True)
        epic_log_path = epic_folder / "debate_log.md"
        epic_backlog_file = epic_folder / "epic_backlog.yaml"

        refs = ContextLoader.get_ceremony_context(self.root_dir, ceremony="2_sprint_refinement", include_dev_rules=False)

        if epic_log_path.exists() and len(epic_log_path.read_text(encoding="utf-8").strip()) > 50:
            print(f"⏯️ [SprintRefinementEngine 中断再開] エピック '{dir_name}' の debate_log.md が完了済みのため Step 1 をスキップします。", flush=True)
        else:
            print(f"💬 [Ceremony 2] Step 1: Generating debate_log.md for: {title}...", flush=True)
            debate_prefix = f"# 💬 Epic Architecture Debate Log: {title}\n\n## 1. Multi-Persona Discussion\n- **[Scrum Master Persona]**: Welcome team to the refinement session for {title}. Let us review the primary business goals and architectural constraints.\n"

            debate_prompt = (
                f"[TASK: CEREMONY 2 EPIC REFINEMENT DEBATE - {title}]\n"
                f"Epic Directory: {dir_name}\n"
                f"Epic Scope: {scope}\n\n"
                f"=== OVERALL ARCHITECTURE CONTEXT ===\n"
                f"File Path: state/.evaluator/overall_debate_log.md\n\n"
                f"=== REPOSITORY RULES ===\n{refs['rules']}\n\n"
                f"=== PERSONAS ===\n{refs['personas']}\n\n"
                "Write multi-persona debate log strictly following ceremony 2 rules above.\n\n"
                + debate_prefix
            )

            actual_epic_prompt_file = self.eval_dir / "actual_epic_prompt.md"
            CodeParser.atomic_write_text(actual_epic_prompt_file, debate_prompt)

            debate_raw_response = self.refinement_agent.generate_text(debate_prompt)
            if not debate_raw_response or not debate_raw_response.strip():
                raise RuntimeError(f"❌ [SprintRefinementEngine] Failed to generate debate_log.md for '{title}'!")

            debate_response = debate_prefix + debate_raw_response
            CodeParser.atomic_write_text(epic_log_path, debate_response)

        if epic_backlog_file.exists() and "tasks:" in epic_backlog_file.read_text(encoding="utf-8"):
            print(f"⏯️ [SprintRefinementEngine 中断再開] エピック '{dir_name}' の epic_backlog.yaml が完了済みのため Step 2 をスキップします。", flush=True)
            return

        print(f"📝 [Ceremony 2] Step 2: Generating epic_backlog.yaml for: {title}...", flush=True)
        
        ws = self.config.workspace_rel or "workspace/identicon-generator"
        test_cmd = self.config.default_test_cmd or "go test ./..."
        img_name = self.config.container_image_name or "identicon-generator"

        if "container" in dir_name or "docker" in dir_name:
            current_test_cmd = f"docker build -t {img_name}:latest ."
        elif "cloud_run" in dir_name or "deployment" in dir_name:
            current_test_cmd = f"grep -q 'USER' Dockerfile && docker build -t {img_name}:cloudrun ."
        else:
            current_test_cmd = test_cmd

        yaml_prefix = (
            f"epic: \"{title}\"\n"
            f"scope: \"{scope}\"\n"
            f"target_workspace: \"{ws}\"\n"
            f"test_command: \"{current_test_cmd}\"\n"
            "tasks:\n"
        )

        yaml_prompt = (
            f"[TASK: CEREMONY 2 EPIC BACKLOG YAML GENERATION - {title}]\n"
            f"Epic Scope: {scope}\n\n"
            f"=== DEBATE LOG REFERENCE ===\n"
            f"File Path: {epic_log_path.relative_to(self.root_dir)}\n\n"
            "【INSTRUCTION: DoR Rules (Acceptance Criteria <= 2)】\n"
            "Generate ONLY the YAML tasks array starting with `- id: \"TASK-1.1\"` under `tasks:`.\n"
            "Each task MUST have at most 2 Acceptance Criteria.\n\n"
            + yaml_prefix
        )

        actual_epic_prompt_file = self.eval_dir / "actual_epic_prompt.md"
        CodeParser.atomic_write_text(actual_epic_prompt_file, yaml_prompt)

        yaml_response = self.refinement_agent.generate_text(yaml_prompt)
        
        clean_yaml = (yaml_response or "").strip()
        if clean_yaml.startswith("```yaml"):
            clean_yaml = clean_yaml[7:]
        if clean_yaml.startswith("```"):
            clean_yaml = clean_yaml[3:]
        if clean_yaml.endswith("```"):
            clean_yaml = clean_yaml[:-3]
        clean_yaml = clean_yaml.strip()

        if not clean_yaml.startswith("epic:"):
            full_yaml = yaml_prefix + clean_yaml
        else:
            full_yaml = clean_yaml

        if "tasks:" not in full_yaml or "TASK-" not in full_yaml:
            raise RuntimeError(f"❌ [SprintRefinementEngine] Failed to generate valid epic_backlog.yaml for '{title}'!")

        CodeParser.atomic_write_text(epic_backlog_file, full_yaml)
        print(f"📝 [Ceremony 2] Saved direct epic_backlog.yaml for: {dir_name}")

    def run_sprint_refinement(self, dynamic_epics: list) -> bool:
        print("🚀 [Ceremony 2: Sprint Refinement] Executing Sprint Backlog Refinement...", flush=True)

        for dir_name, title, scope, idx in dynamic_epics:
            self.refine_single_epic(dir_name, title, scope, idx)

        print("🚀 [Ceremony 2] Step 1: Splitting epic_backlog.yaml into sprint_x_backlog.yaml...", flush=True)
        BacklogSplitter.process_all_epics(self.root_dir, self.config)

        print("🚀 [Ceremony 2] Step 2: Generating automated test harness scripts...", flush=True)
        HarnessGenerator.generate_all_harnesses(self.root_dir, self.config)

        print("🎉 [Ceremony 2 Complete] Sprint Refinement pipeline completed successfully!", flush=True)
        return True
