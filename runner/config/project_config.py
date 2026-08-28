import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ProjectConfig:
    project_name: str = "identicon-generator"
    language: str = "go"
    test_command: str = "go test ./..."
    run_command: str = "go run ."
    verify_command: str = "go test ./..."
    dev_rules_path: str = ".agents/rules/development/"
    provider: str = "gemini"
    refinement_provider: str = "gemini"
    evaluator_provider: str = "gemini"
    executor_provider: str = "llama_cpp"
    executor_model: str = "mistralai_Devstral-Small-2-24B-Instruct-2512-Q4_K_M.gguf"
    llama_max_tokens: int = 8192
    workspace_rel: str = "workspace/identicon-generator"
    container_image_name: str = "identicon-generator"
    extra_env: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, root_dir: Path) -> 'ProjectConfig':
        config_file = root_dir / "config.yaml"
        env_file = root_dir / "config.env"
        data: Dict[str, Any] = {}

        # 1. Load config.env if present
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    os.environ[k] = v

        # 2. Load config.yaml if present
        if config_file.exists():
            try:
                data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
            except Exception:
                pass

        proj_name = os.getenv("PROJECT_NAME", data.get("PROJECT_NAME", "identicon-generator"))

        return cls(
            project_name=proj_name,
            language=os.getenv("LANGUAGE", data.get("LANGUAGE", "go")),
            test_command=os.getenv("TEST_COMMAND", data.get("TEST_COMMAND", "go test ./...")),
            run_command=os.getenv("RUN_COMMAND", data.get("RUN_COMMAND", "go run .")),
            verify_command=os.getenv("VERIFY_COMMAND", data.get("VERIFY_COMMAND", "go test ./...")),
            dev_rules_path=os.getenv("DEV_RULES_PATH", data.get("DEV_RULES_PATH", ".agents/rules/development/")),
            provider=os.getenv("DEFAULT_LLM_PROVIDER", os.getenv("REFINEMENT_PROVIDER", data.get("DEFAULT_LLM_PROVIDER", "gemini"))),
            refinement_provider=os.getenv("REFINEMENT_PROVIDER", "gemini"),
            evaluator_provider=os.getenv("EVALUATOR_PROVIDER", "gemini"),
            executor_provider=os.getenv("EXECUTOR_PROVIDER", "llama_cpp"),
            executor_model=os.getenv("EXECUTOR_MODEL", data.get("EXECUTOR_MODEL", "mistralai_Devstral-Small-2-24B-Instruct-2512-Q4_K_M.gguf")),
            llama_max_tokens=int(os.getenv("LLAMA_MAX_TOKENS", data.get("LLAMA_MAX_TOKENS", "8192"))),
            workspace_rel=os.getenv("WORKSPACE_REL", os.getenv("TARGET_DIR", f"workspace/{proj_name}")),
            container_image_name=os.getenv("CONTAINER_IMAGE_NAME", proj_name),
        )
