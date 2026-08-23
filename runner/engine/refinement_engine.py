import os
import re
import yaml
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser
from runner.utils.context_loader import ContextLoader
from runner.utils.backlog_splitter import BacklogSplitter
from runner.generators.harness_generator import HarnessGenerator
from runner.adapters.llm_adapter import LLMAdapterFactory


class RefinementEngine:
    """Handles Scrum Refinement: Strict Rule-driven Pipeline with Checkpoint & Resume Mode."""

    def __init__(self, root_dir: Path, config: ProjectConfig = None):
        self.root_dir = root_dir
        self.config = config or ProjectConfig.load(root_dir)
        self.init_dir = root_dir / "state" / "initiatives"
        self.eval_dir = root_dir / "state/.evaluator"
        self.init_dir.mkdir(parents=True, exist_ok=True)
        self.eval_dir.mkdir(parents=True, exist_ok=True)

        refinement_provider = self._get_refinement_provider()
        print(f"🧠 [RefinementEngine] Using Provider '{refinement_provider}' for Refinement Pipeline.", flush=True)
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

    def extract_epics_from_overall_log(self, debate_text: str) -> list:
        """全体ディベートログからエピックリストと Scope を抽出。ペルソナによる自然な分類をそのまま採用。"""
        epics = []
        p1 = r'(?:#+|\-|\*|\d+\.)?\s*\*\*(epic_[a-zA-Z0-9_]+)\*\*[:\s]*(.*)'
        for m in re.finditer(p1, debate_text):
            e_dir = m.group(1).strip()
            title = e_dir.replace("_", " ").title()
            scope = m.group(2).strip().replace('`', '') or f"Scope for {e_dir}"
            epics.append((e_dir, title, scope, len(epics) + 1))

        if not epics:
            p2 = r'(epic_[a-zA-Z0-9_]+)[:\s]*(.*)'
            for m in re.finditer(p2, debate_text):
                e_dir = m.group(1).strip()
                title = e_dir.replace("_", " ").title()
                scope = m.group(2).strip().replace('`', '') or f"Scope for {e_dir}"
                epics.append((e_dir, title, scope, len(epics) + 1))

        return epics

    def run_overall_debate(self):
        """【Phase 1】全体アーキテクチャディベートを実行。安全な「中断再開」対応。"""
        overall_log_path = self.eval_dir / "overall_debate_log.md"

        if overall_log_path.exists() and len(overall_log_path.read_text(encoding="utf-8").strip()) > 100:
            print(f"⏯️ [RefinementEngine 中断再開] 全体ディベートログ (overall_debate_log.md) が存在するためスキップし、既存成果物をそのまま使用します。", flush=True)
            return

        print("🌐 [RefinementEngine Phase 1] Pure Rule-Driven Overall Multi-Persona Debate...", flush=True)
        proj_name = self.config.project_name or "identicon-generator"
        lang = self.config.language or "Go"

        refs = ContextLoader.get_refinement_file_references(self.root_dir)
        
        spec_files = list((self.root_dir / "references").glob("*.md")) if (self.root_dir / "references").exists() else []
        if not spec_files:
            raise RuntimeError("❌ [RefinementEngine Alert] Missing System Specification in references/! Cannot proceed without input specification. Halting for user escalation.")

        prompt = (
            f"[SYSTEM INSTRUCTION: OVERALL SYSTEM DEBATE & EPIC CLASSIFICATION - {proj_name}]\n"
            f"Target System & Language: {proj_name} ({lang} Clean Architecture)\n\n"
            f"=== 1. SYSTEM SPECIFICATIONS ===\n{refs['specs']}\n\n"
            f"=== 2. REPOSITORY RULES & POLICIES ===\n{refs['rules']}\n\n"
            f"=== 3. PARTICIPATING PERSONAS ===\n{refs['personas']}\n\n"
            "Analyze the specification with all 6 personas strictly following the rules above.\n"
            "Dynamically classify single-responsibility Epics under section '## 3. Classified Actionable Epics List'.\n"
            "Required Naming Pattern:\n"
            "- **epic_1_feature_name**: Scope description directly derived from specification\n\n"
            "End with STATUS: OVERALL_DEBATE_PASSED (or STATUS: REQUIRES_SPEC_DECISION if trade-offs needed).\n\n"
            "# 🌐 Overall System Architecture Multi-Persona Debate Log\n\n"
            "## 1. System Goals & Specification Alignment\n"
            f"- Specification Target: {proj_name}\n"
        )

        actual_prompt_file = self.eval_dir / "actual_phase1_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)
        print(f"📄 [RefinementEngine] Saved initial Phase 1 prompt context ({len(prompt)} chars) to: {actual_prompt_file.relative_to(self.root_dir)}")

        llm_raw_response = self.refinement_agent.generate_text(prompt)
        if not llm_raw_response or not llm_raw_response.strip():
            raise RuntimeError("❌ [RefinementEngine Escalation] LLM returned an empty response for Phase 1 Overall Debate! Halting pipeline for user escalation.")

        llm_response = (
            "# 🌐 Overall System Architecture Multi-Persona Debate Log\n\n"
            "## 1. System Goals & Specification Alignment\n"
            f"- Specification Target: {proj_name}\n"
            + llm_raw_response
        )

        CodeParser.atomic_write_text(overall_log_path, llm_response)
        print(f"📝 [RefinementEngine Phase 1 Complete] Saved overall debate log: {overall_log_path.relative_to(self.root_dir)}")

        if "ERROR_MISSING_SPECIFICATION" in llm_response:
            raise RuntimeError("❌ [RefinementEngine Escalation] LLM reported missing system specification! Halting pipeline for user escalation.")

        if "REQUIRES_SPEC_DECISION" in llm_response:
            raise RuntimeError("⚖️ [RefinementEngine Trade-off Escalation] Unfeasible requirement detected! Alternatives proposed in state/.evaluator/overall_debate_log.md. Halting for user decision.")

    def refine_single_epic(self, dir_name: str, title: str, scope: str, epic_idx: int):
        """Step 1: debate_log.md を出力。 Step 2: epic_backlog.yaml を直接生成。各チェックポイント対応。"""
        epic_folder = self.init_dir / dir_name
        epic_folder.mkdir(parents=True, exist_ok=True)
        epic_log_path = epic_folder / "debate_log.md"
        epic_backlog_file = epic_folder / "epic_backlog.yaml"

        refs = ContextLoader.get_refinement_file_references(self.root_dir)

        if epic_log_path.exists() and len(epic_log_path.read_text(encoding="utf-8").strip()) > 50:
            print(f"⏯️ [RefinementEngine 中断再開] エピック '{dir_name}' の debate_log.md が完了済みのため Step 1 をスキップします。", flush=True)
        else:
            print(f"💬 [RefinementEngine] Step 1: Generating debate_log.md for: {title}...", flush=True)
            debate_prefix = f"# 💬 Epic Architecture Debate Log: {title}\n\n## 1. Multi-Persona Discussion\n- **[PO Persona]**: Core business requirements for {title}.\n"

            debate_prompt = (
                f"[TASK: EPIC REFINEMENT DEBATE LOG - {title}]\n"
                f"Epic Directory: {dir_name}\n"
                f"Epic Scope: {scope}\n\n"
                f"=== OVERALL ARCHITECTURE CONTEXT ===\n"
                f"File Path: state/.evaluator/overall_debate_log.md\n\n"
                f"=== REPOSITORY RULES ===\n{refs['rules']}\n\n"
                f"=== PERSONAS ===\n{refs['personas']}\n\n"
                "Write multi-persona debate log strictly following repository rules above.\n\n"
                + debate_prefix
            )

            actual_epic_prompt_file = self.eval_dir / "actual_epic_prompt.md"
            CodeParser.atomic_write_text(actual_epic_prompt_file, debate_prompt)

            debate_raw_response = self.refinement_agent.generate_text(debate_prompt)
            if not debate_raw_response or not debate_raw_response.strip():
                raise RuntimeError(f"❌ [RefinementEngine Escalation] LLM failed to generate debate_log.md for epic '{title}'! Halting pipeline for user escalation.")

            debate_response = debate_prefix + debate_raw_response
            CodeParser.atomic_write_text(epic_log_path, debate_response)

        if epic_backlog_file.exists() and "tasks:" in epic_backlog_file.read_text(encoding="utf-8"):
            print(f"⏯️ [RefinementEngine 中断再開] エピック '{dir_name}' の epic_backlog.yaml が完了済みのため Step 2 をスキップします。", flush=True)
            return

        print(f"📝 [RefinementEngine] Step 2: Generating direct epic_backlog.yaml for: {title}...", flush=True)
        
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
            f"[TASK: DIRECT EPIC BACKLOG YAML GENERATION - {title}]\n"
            f"Epic Scope: {scope}\n\n"
            f"=== DEBATE LOG REFERENCE ===\n"
            f"File Path: {epic_log_path.relative_to(self.root_dir)}\n\n"
            "【INSTRUCTION】\n"
            "Generate ONLY the YAML tasks array starting with `- id: \"TASK-1.1\"` under `tasks:`.\n\n"
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
            raise RuntimeError(f"❌ [RefinementEngine Escalation] LLM failed to generate valid epic_backlog.yaml for epic '{title}'! Raw response: '{yaml_response}'. Halting pipeline for user escalation.")

        CodeParser.atomic_write_text(epic_backlog_file, full_yaml)
        print(f"📝 [RefinementEngine] Saved direct epic_backlog.yaml for: {dir_name}")

    def run_refinement(self) -> bool:
        print("🚀 [RefinementEngine] Executing Dynamic Refinement Pipeline...", flush=True)

        self.run_overall_debate()

        overall_log_path = self.eval_dir / "overall_debate_log.md"
        overall_log_text = overall_log_path.read_text(encoding="utf-8") if overall_log_path.exists() else ""
        dynamic_epics = self.extract_epics_from_overall_log(overall_log_text)

        if not dynamic_epics:
            raise RuntimeError("❌ [RefinementEngine Escalation] Zero epics could be extracted from Phase 1 Overall Debate log! Please inspect state/.evaluator/overall_debate_log.md. Halting pipeline for user escalation.")

        for dir_name, title, scope, idx in dynamic_epics:
            self.refine_single_epic(dir_name, title, scope, idx)

        print("🚀 [RefinementEngine] Step 1: Splitting epic_backlog.yaml into sprint_x_backlog.yaml...", flush=True)
        BacklogSplitter.process_all_epics(self.root_dir, self.config)

        print("🚀 [RefinementEngine] Step 2: Generating harness scripts...", flush=True)
        HarnessGenerator.generate_all_harnesses(self.root_dir, self.config)

        print("🎉 [RefinementEngine] Dynamic Refinement pipeline completed successfully!", flush=True)
        return True
