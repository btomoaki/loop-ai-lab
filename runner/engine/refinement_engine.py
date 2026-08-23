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
    """Handles Scrum Refinement: Strict Rule-driven Pipeline with Alternative Proposal Escalation."""

    FORBIDDEN_CONJUNCTIONS = ["_and_", "_with_", "_plus_", "_&_"]

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
        """全体ディベートログからエピックリストと Scope を抽出。結合キーワード (and/with) を物理ハーネスでチェック。"""
        epics = []
        
        p1 = r'(?:-|\*|\d+\.)?\s*\*\*(epic_[a-zA-Z0-9_]+)\*\*:\s*(.*)'
        for m in re.finditer(p1, debate_text):
            e_dir = m.group(1).strip()
            title = e_dir.replace("_", " ").title()
            scope = m.group(2).strip().replace('`', '')
            epics.append((e_dir, title, scope, len(epics) + 1))

        if not epics:
            p2 = r'(epic_[a-zA-Z0-9_]+):\s*(.*)'
            for m in re.finditer(p2, debate_text):
                e_dir = m.group(1).strip()
                title = e_dir.replace("_", " ").title()
                scope = m.group(2).strip().replace('`', '')
                epics.append((e_dir, title, scope, len(epics) + 1))

        # 🛡️ Physical Harness Check: Detect forbidden conjunctions in epic names
        valid_epics = []
        for e_dir, title, scope, idx in epics:
            has_conjunction = any(conj in e_dir.lower() for conj in self.FORBIDDEN_CONJUNCTIONS)
            if has_conjunction:
                print(f"⚠️ [Physical Harness Warning] Composite epic detected ({e_dir}). Splitting into single-responsibility epics...")
                parts = e_dir.split("_and_") if "_and_" in e_dir else e_dir.split("_with_")
                sub1_dir = parts[0]
                sub2_dir = f"epic_{idx+10}_{parts[1]}" if len(parts) > 1 else f"{sub1_dir}_details"
                
                valid_epics.append((sub1_dir, sub1_dir.replace("_", " ").title(), f"Core implementation for {parts[0]}", len(valid_epics)+1))
                if len(parts) > 1:
                    valid_epics.append((sub2_dir, sub2_dir.replace("_", " ").title(), f"Implementation for {parts[1]}", len(valid_epics)+1))
            else:
                valid_epics.append((e_dir, title, scope, len(valid_epics)+1))

        return valid_epics

    def run_overall_debate(self):
        """【Phase 1】全体アーキテクチャディベートを実行。送信前の初回コンテキストを自動ファイル保存。"""
        print("🌐 [RefinementEngine Phase 1] Pure Rule-Driven Overall Multi-Persona Debate...", flush=True)
        proj_name = self.config.project_name or "identicon-generator"
        lang = self.config.language or "Go"

        refs = ContextLoader.get_refinement_file_references(self.root_dir)
        
        # 🚨 Specification Existence Guard
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
            "End with STATUS: OVERALL_DEBATE_PASSED (or STATUS: REQUIRES_SPEC_DECISION if trade-offs needed)."
        )

        # 📄 Save initial raw prompt context automatically to file for user inspection
        actual_prompt_file = self.eval_dir / "actual_phase1_prompt.md"
        CodeParser.atomic_write_text(actual_prompt_file, prompt)
        print(f"📄 [RefinementEngine] Saved initial Phase 1 prompt context ({len(prompt)} chars) to: {actual_prompt_file.relative_to(self.root_dir)}")

        llm_response = self.refinement_agent.generate_text(prompt)
        
        if not llm_response or not llm_response.strip():
            raise RuntimeError("❌ [RefinementEngine Escalation] LLM returned an empty response for Phase 1 Overall Debate! Halting pipeline for user escalation.")

        overall_log_path = self.eval_dir / "overall_debate_log.md"
        CodeParser.atomic_write_text(overall_log_path, llm_response)
        print(f"📝 [RefinementEngine Phase 1 Complete] Saved overall debate log: {overall_log_path.relative_to(self.root_dir)}")

        if "ERROR_MISSING_SPECIFICATION" in llm_response:
            raise RuntimeError("❌ [RefinementEngine Escalation] LLM reported missing system specification! Halting pipeline for user escalation.")

        if "REQUIRES_SPEC_DECISION" in llm_response:
            raise RuntimeError("⚖️ [RefinementEngine Trade-off Escalation] Unfeasible requirement detected! Alternatives proposed in state/.evaluator/overall_debate_log.md. Halting for user decision.")

    def refine_single_epic(self, dir_name: str, title: str, scope: str, epic_idx: int):
        """Step 1: debate_log.md (議論対話) を出力。 Step 2: epic_backlog.yaml (スコープ＆タスクデータ) を直接生成。生成失敗時は即座に例外停止。"""
        epic_folder = self.init_dir / dir_name
        epic_folder.mkdir(parents=True, exist_ok=True)

        print(f"💬 [RefinementEngine] Step 1: Generating debate_log.md for: {title}...", flush=True)
        
        refs = ContextLoader.get_refinement_file_references(self.root_dir)

        debate_prompt = (
            f"[TASK: EPIC REFINEMENT DEBATE LOG - {title}]\n"
            f"Epic Directory: {dir_name}\n"
            f"Epic Scope: {scope}\n\n"
            f"=== OVERALL ARCHITECTURE CONTEXT ===\n"
            f"File Path: state/.evaluator/overall_debate_log.md\n\n"
            f"=== REPOSITORY RULES ===\n{refs['rules']}\n\n"
            f"=== PERSONAS ===\n{refs['personas']}\n\n"
            "Write multi-persona debate log strictly following repository rules above."
        )

        debate_response = self.refinement_agent.generate_text(debate_prompt)
        if not debate_response or not debate_response.strip():
            raise RuntimeError(f"❌ [RefinementEngine Escalation] LLM failed to generate debate_log.md for epic '{title}'! Halting pipeline for user escalation.")

        epic_log_path = epic_folder / "debate_log.md"
        CodeParser.atomic_write_text(epic_log_path, debate_response)

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

        yaml_prompt = (
            f"[TASK: DIRECT EPIC BACKLOG YAML GENERATION - {title}]\n"
            f"Epic Scope: {scope}\n\n"
            f"=== DEBATE LOG REFERENCE ===\n"
            f"File Path: {epic_log_path.relative_to(self.root_dir)}\n\n"
            "【INSTRUCTION】\n"
            "Output ONLY valid YAML (no markdown codeblock formatting, raw YAML text) representing epic_backlog.yaml. "
            "Decompose this epic scope into fine-grained file creation tasks.\n\n"
            "【REQUIRED YAML STRUCTURE】\n"
            f"epic: \"{title}\"\n"
            f"scope: \"{scope}\"\n"
            f"target_workspace: \"{ws}\"\n"
            f"test_command: \"{current_test_cmd}\"\n"
            "tasks:\n"
            f"  - id: \"TASK-{epic_idx}.1\"\n"
            "    name: \"[FILE] path/to/file1.go\"\n"
            "    description: \"Task description\"\n"
            "    definition_of_done:\n"
            "      - \"DoD criteria\"\n"
        )

        yaml_response = self.refinement_agent.generate_text(yaml_prompt)
        
        clean_yaml = (yaml_response or "").strip()
        if clean_yaml.startswith("```yaml"):
            clean_yaml = clean_yaml[7:]
        if clean_yaml.startswith("```"):
            clean_yaml = clean_yaml[3:]
        if clean_yaml.endswith("```"):
            clean_yaml = clean_yaml[:-3]
        clean_yaml = clean_yaml.strip()

        if not clean_yaml or "tasks:" not in clean_yaml:
            raise RuntimeError(f"❌ [RefinementEngine Escalation] LLM failed to generate valid epic_backlog.yaml for epic '{title}'! Raw response: '{yaml_response}'. Halting pipeline for user escalation.")

        epic_backlog_file = epic_folder / "epic_backlog.yaml"
        CodeParser.atomic_write_text(epic_backlog_file, clean_yaml)
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
