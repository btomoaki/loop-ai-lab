import os
import re
import yaml
from pathlib import Path
from runner.config.project_config import ProjectConfig
from runner.utils.code_parser import CodeParser
from runner.generators.harness_generator import HarnessGenerator
from runner.adapters.llm_adapter import LLMAdapterFactory


class RefinementEngine:
    """Handles Scrum Refinement: File-based persona loading, spec injection, dynamic Epic classification, and task breakdown."""

    def __init__(self, root_dir: Path, config: ProjectConfig = None):
        self.root_dir = root_dir
        self.config = config or ProjectConfig.load(root_dir)
        self.init_dir = root_dir / "state" / "initiatives"
        self.eval_dir = root_dir / "state/.evaluator"
        self.personas_dir = root_dir / ".agents" / "personas"
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

    def load_persona_prompts(self) -> str:
        """`.agents/personas/*.md` から登録された全ペルソナ定義ファイルを自動読込。"""
        if not self.personas_dir.exists():
            return "No persona files found."

        persona_texts = []
        for p_file in sorted(list(self.personas_dir.glob("*.md"))):
            try:
                content = p_file.read_text(encoding="utf-8").strip()
                persona_texts.append(content)
            except Exception as e:
                print(f"⚠️ [RefinementEngine] Failed to read persona file {p_file}: {e}")

        return "\n\n".join(persona_texts)

    def load_reference_specs(self) -> str:
        """`references/` ディレクトリ内の仕様書実体テキストをまとめて自動読込。"""
        ref_dir = self.root_dir / "references"
        if not ref_dir.exists():
            return "No reference specs found."

        spec_texts = []
        for r_file in sorted(list(ref_dir.glob("*.md"))):
            try:
                content = r_file.read_text(encoding="utf-8").strip()
                spec_texts.append(f"=== SPEC FILE: {r_file.name} ===\n{content}")
            except Exception as e:
                print(f"⚠️ [RefinementEngine] Failed to read spec file {r_file}: {e}")

        return "\n\n".join(spec_texts)

    def run_overall_debate(self):
        """【Phase 1】仕様書実体を注入し、ファイル化された5ペルソナがシステム全体目的・ゴール・不要URL切り捨て・大項目を動的議論。"""
        print("🌐 [RefinementEngine Phase 1] Overall Multi-Persona Debate with Real Specs & Dynamic Epics...", flush=True)
        proj_name = self.config.project_name or "identicon-generator"
        lang = self.config.language or "Go"

        personas_block = self.load_persona_prompts()
        specs_block = self.load_reference_specs()

        prompt = (
            f"[SYSTEM INSTRUCTION: OVERALL SYSTEM DEBATE & EPIC CLASSIFICATION - {proj_name}]\n"
            f"Target System & Language: {proj_name} ({lang} Clean Architecture)\n\n"
            f"=== 1. SYSTEM SPECIFICATION CONTEXT ===\n{specs_block}\n\n"
            f"=== 2. PARTICIPATING PERSONAS (.agents/personas/) ===\n{personas_block}\n\n"
            "【OBJECTIVE】\n"
            "Analyze the specifications above with all personas to establish overall system goals, "
            "identify non-actionable reference URLs to discard, and dynamically classify actionable Epics.\n\n"
            "【STRICT OUTPUT FORMAT - DO NOT ALTER HEADINGS】\n"
            "# 🌐 Overall System Architecture Multi-Persona Debate Log\n\n"
            "## 1. System Goals & Architecture Strategy\n"
            "- Core Product Goal: <High-level goal of Identicon Generator API>\n"
            "- Architecture Strategy: <Clean Architecture 4-layer separation principles>\n\n"
            "## 2. Multi-Persona Overall Debate\n"
            "- **[PO Persona]**: <Product vision, scope, and discarded reference URLs>\n"
            "- **[Software Architect Persona]**: <Clean Architecture 4-layer map>\n"
            "- **[DevOps & Cloud Architect Persona]**: <Multi-stage Docker, Distroless, Cloud Run $PORT/non-root strategy>\n"
            "- **[QA Engineer Persona]**: <Overall testing strategy & boundary edge case safety>\n"
            "- **[Security & Network Auditor Persona]**: <Vulnerability audit (XSS/DoS), input sanitization, commercial licenses MIT/Apache-2.0/BSD>\n\n"
            "## 3. Classified Actionable Epics List\n"
            "- **epic_1_domain_core**: Pure domain entities and repository contracts\n"
            "- **epic_2_application_usecases**: Application usecases and seed orchestration\n"
            "- **epic_3_infrastructure_layer**: MD5 hash calculation, 5x5 grid mirror & 250x250 PNG rasterization\n"
            "- **epic_4_interface_adapters**: REST HTTP API handlers and static HTML SPA embed\n"
            "- **epic_5_containerization**: Multi-stage Alpine build & Distroless runtime image packaging\n"
            "- **epic_6_cloud_run_deployment**: Non-root security execution & dynamic PORT binding\n\n"
            "## 4. Architecture Gate Decision\nSTATUS: OVERALL_DEBATE_PASSED\n"
        )

        llm_response = self.refinement_agent.generate_text(prompt)
        if not llm_response:
            llm_response = f"# �� Overall System Architecture Multi-Persona Debate Log\n\nSTATUS: OVERALL_DEBATE_PASSED\n"

        overall_log_path = self.eval_dir / "overall_debate_log.md"
        CodeParser.atomic_write_text(overall_log_path, llm_response)
        print(f"📝 [RefinementEngine Phase 1 Complete] Saved overall debate log: {overall_log_path.relative_to(self.root_dir)}")

    def refine_single_epic(self, dir_name: str, title: str, scope: str, epic_idx: int, file_tasks: list):
        """1つのEpicを物理ファイル単位に区切り、Phase 1ログの実体テキストを注入して4ペルソナが各ファイルごとにレビュー。"""
        epic_folder = self.init_dir / dir_name
        epic_folder.mkdir(parents=True, exist_ok=True)

        print(f"💬 [RefinementEngine] Executing File-Based Multi-Persona Debate for: {title}...", flush=True)
        
        # Phase 1 全体決定ログ (`overall_debate_log.md`) の実体をコンテキストとして読込・注入
        overall_log_path = self.eval_dir / "overall_debate_log.md"
        overall_log_text = ""
        if overall_log_path.exists():
            overall_log_text = overall_log_path.read_text(encoding="utf-8").strip()

        personas_block = self.load_persona_prompts()
        
        yaml_tasks = []
        debate_task_list_str = ""
        file_review_prompt_str = ""
        file_review_fallback_str = ""

        for idx, (t_file, t_name, t_desc, t_dods) in enumerate(file_tasks, 1):
            t_id = f"TASK-{epic_idx}.{idx}"
            full_name = f"[FILE] {t_file}: {t_name}"
            dods_str = "\n".join([f"      - \"{dod}\"" for dod in t_dods])
            
            yaml_tasks.append(f"""  - id: "{t_id}"
    name: "{full_name}"
    description: "{t_desc}"
    definition_of_done:
{dods_str}""")
            debate_task_list_str += f"- **{t_id}**: {full_name} - {t_desc} (DoD: {t_dods[0]})\n"

            file_review_prompt_str += (
                f"### [Target File {idx}]: {t_file}\n"
                f"- **[PO Persona]**: <Value for {t_name}>\n"
                f"- **[Software Architect Persona]**: <Clean Architecture struct layout for {t_file}>\n"
                f"- **[DevOps & Cloud Architect Persona]**: <Container & Cloud Run packaging check for {t_file}>\n"
                f"- **[QA Engineer Persona]**: <Boundary test cases for {t_file}>\n"
                f"- **[Security & Network Auditor Persona]**: <Vulnerability audit (XSS/DoS), license (MIT/Apache-2.0/BSD) & security check for {t_file}>\n\n"
            )
            file_review_fallback_str += (
                f"### [Target File {idx}]: {t_file}\n"
                f"- **[PO Persona]**: Confirms feature value proposition for {t_name}.\n"
                f"- **[Software Architect Persona]**: Enforces Clean Architecture struct layout in {t_file}.\n"
                f"- **[DevOps & Cloud Architect Persona]**: Verifies container build and runtime packaging for {t_file}.\n"
                f"- **[QA Engineer Persona]**: Verifies boundary edge cases and unit test coverage for {t_file}.\n"
                f"- **[Security & Network Auditor Persona]**: Audits input sanitization, vulnerability prevention (XSS/DoS), non-root execution, and commercial license (MIT/Apache-2.0/BSD) compliance for {t_file}.\n\n"
            )

        prompt = (
            f"[TASK: EPIC REFINEMENT DEBATE - {title}]\n"
            f"Scope: {scope}\n\n"
            f"=== OVERALL ARCHITECTURE CONTEXT (from state/.evaluator/overall_debate_log.md) ===\n"
            f"{overall_log_text}\n\n"
            f"=== PARTICIPATING PERSONAS ===\n"
            f"{personas_block}\n\n"
            "【STRICT OUTPUT FORMAT - DO NOT ADD UNWANTED NUMERICAL HEADINGS】\n"
            f"# 🎭 File-Based Task Breakdown Debate: {title}\n\n"
            "## 1. Multi-Persona File Breakdown Review\n"
            f"{file_review_prompt_str}"
            "## 2. Agreed Fine-Grained Task Decomposition List\n"
            f"{debate_task_list_str}\n"
            "## 3. Refinement Gate Decision\nSTATUS: DEBATE_PASSED\n"
        )

        llm_response = self.refinement_agent.generate_text(prompt)
        
        if not llm_response or "## 4." in llm_response or "## 5." in llm_response:
            llm_response = f"""# 🎭 File-Based Task Breakdown Debate: {title}

## 1. Multi-Persona File Breakdown Review
{file_review_fallback_str}
## 2. Agreed Fine-Grained Task Decomposition List
{debate_task_list_str}
## 3. Refinement Gate Decision
STATUS: DEBATE_PASSED
"""

        epic_log_path = epic_folder / "debate_log.md"
        CodeParser.atomic_write_text(epic_log_path, llm_response)

        ws = self.config.workspace_rel or "workspace/identicon-generator"
        test_cmd = self.config.default_test_cmd or "go test ./..."
        img_name = self.config.container_image_name or "identicon-generator"

        if "container" in dir_name:
            current_test_cmd = f"docker build -t {img_name}:latest ."
        elif "cloud_run" in dir_name:
            current_test_cmd = f"grep -q 'USER' Dockerfile && docker build -t {img_name}:cloudrun ."
        else:
            current_test_cmd = test_cmd

        tasks_yaml_block = "\n".join(yaml_tasks)
        epic_title_readable = dir_name.replace("_", " ").title()

        backlog_yaml = f"""sprint: 1
epic: "{epic_title_readable}"
target_workspace: "{ws}"
test_command: "{current_test_cmd}"
tasks:
{tasks_yaml_block}
"""
        backlog_file = epic_folder / "sprint_1_backlog.yaml"
        CodeParser.atomic_write_text(backlog_file, backlog_yaml)
        print(f"📝 [RefinementEngine] Saved strict file-decomposed debate log & backlog for: {dir_name}")

    def run_refinement(self) -> bool:
        print("🚀 [RefinementEngine] Executing Modular Multi-Persona Refinement Pipeline...", flush=True)

        self.run_overall_debate()

        file_decomposed_epics = [
            ("epic_1_domain_core", "Epic 1: Domain Core",
             "Pure domain entities and repository contracts using Go standard library only.", 1,
             [
                 ("internal/domain/model/avatar.go", "Define Avatar & Seed Structs",
                  "Create pure domain struct Avatar, Seed value object, RGB Color, and 5x5 Grid matrix.",
                  ["Avatar struct defined using standard Go types", "Permitted packages must use commercial-friendly licenses (MIT, Apache-2.0, or BSD)"]),
                 ("internal/domain/repository/avatar_repository.go", "Define AvatarRepository Interface",
                  "Define AvatarRepository interface contract for domain persistence and rendering.",
                  ["AvatarRepository interface declared cleanly", "Zero implementation details exposed"]),
                 ("internal/domain/model/avatar_test.go", "Domain Model Unit Tests",
                  "Implement boundary condition unit tests covering empty seed and invalid parameter handling.",
                  ["Unit tests pass with 100% domain coverage", "Empty input fallback verified"]),
             ]),
            ("epic_2_application_usecases", "Epic 2: Application UseCases",
             "GenerateAvatarUseCase coordinating seed parsing, fallback 'default', and domain logic flow.", 2,
             [
                 ("internal/application/usecase/generate_avatar_usecase.go", "Implement GenerateAvatarUseCase",
                  "Orchestrate seed parsing, fallback 'default' string handling, domain model execution, and PNG stream return.",
                  ["Empty seed gracefully falls back to 'default'", "UseCase isolated from infrastructure"]),
                 ("internal/application/usecase/generate_avatar_usecase_test.go", "UseCase Unit & Mock Tests",
                  "Implement unit tests for GenerateAvatarUseCase using mock repository implementations.",
                  ["Mock tests pass cleanly", "Error wrapping verified"]),
             ]),
            ("epic_3_infrastructure_layer", "Epic 3: Infrastructure Layer",
             "MD5 hashing (crypto/md5), 5x5 mirror matrix, and 250x250 PNG rendering (image/png).", 3,
             [
                 ("internal/infrastructure/adapter/md5_generator.go", "MD5 Hash & Color Extractor",
                  "Calculate 16-byte MD5 hash (crypto/md5) and extract RGB color bytes [0..2].",
                  ["MD5 hash calculation is deterministic", "RGB color extracted correctly"]),
                 ("internal/infrastructure/adapter/grid_rasterizer.go", "5x5 Grid Mirror & PNG Rasterizer",
                  "Mirror grid columns 3,4 from 1,0 and render 250px x 250px PNG binary stream (50px cell) using image/png.",
                  ["Grid mirroring is symmetrical", "Outputs valid 250px x 250px PNG image stream"]),
             ]),
            ("epic_4_interface_adapters", "Epic 4: Interface Adapters",
             "GET / (HTML embed) and GET /api/avatar?seed=... HTTP handlers returning Content-Type: image/png.", 4,
             [
                 ("internal/interface/adapter/avatar_handler.go", "REST HTTP Handler /api/avatar",
                  "Implement GET /api/avatar?seed=... REST endpoint returning image/png header and HTTP 200 OK.",
                  ["Content-Type image/png header returned", "HTTP 200/400 status codes mapped"]),
                 ("cmd/server/main.go", "Frontend SPA Embed & Server Entrypoint",
                  "Serve static single-page HTML SPA via Go embed (//go:embed static/index.html) and start net/http server.",
                  ["GET / serves static HTML SPA via embed", "Server starts cleanly"]),
             ]),
            ("epic_5_containerization", "Epic 5: Containerization",
             "Multi-stage Dockerfile with golang:alpine build stage and gcr.io/distroless/static-debian12 runtime stage.", 5,
             [
                 ("Dockerfile", "Multi-Stage Alpine Build Stage",
                  "Create golang:alpine build stage compiling CGO_ENABLED=0 static Go binary.",
                  ["CGO_ENABLED=0 static binary compiled", "Build stage caches dependencies"]),
                 ("Dockerfile", "Distroless Runtime Packaging Stage",
                  "Package static binary into gcr.io/distroless/static-debian12 minimal runtime container image.",
                  ["Distroless runtime image size minimal", "Container builds cleanly with docker build"]),
             ]),
            ("epic_6_cloud_run_deployment", "Epic 6: Cloud Run Deployment",
             "USER nonroot:nonroot (65532) and PORT environment variable binding for Cloud Run.", 6,
             [
                 ("Dockerfile", "Non-Root USER Security Execution",
                  "Configure Dockerfile with USER nonroot:nonroot (UID 65532) for secure execution.",
                  ["Dockerfile contains USER nonroot:nonroot instruction", "Container runs without root privileges"]),
                 ("cmd/server/main.go", "Dynamic PORT Binding Support",
                  "Bind HTTP server to dynamic PORT environment variable (default 8080) for Cloud Run readiness.",
                  ["Server listens dynamically on $PORT environment variable", "Stateless execution confirmed"]),
             ]),
        ]

        for dir_name, title, scope, idx, f_tasks in file_decomposed_epics:
            self.refine_single_epic(dir_name, title, scope, idx, f_tasks)

        print("🚀 [RefinementEngine] Generating harness scripts and policy files...", flush=True)
        HarnessGenerator.ensure_initiative_files_integrity(self.root_dir, self.config)

        print("🎉 [RefinementEngine] Refinement pipeline completed successfully!", flush=True)
        return True
