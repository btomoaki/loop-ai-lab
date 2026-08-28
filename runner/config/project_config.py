import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ProjectConfig:
    project_name: str = "app"
    language: str = "go"
    test_command: str = "go test ./..."
    run_command: str = "go run ."
    dev_rules_path: str = ".agents/rules/development/"
    provider: str = "local"
    developer_model_type: str = "coder"
    developer_model_context_limit: int = 4096
    developer_model_description: str = "Coder-specialized local LLM with limited context window. Requires self-contained, micro-scoped Epics with explicit Input/Output data structures, pure functions, and testable boundary specifications."
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

        return cls(
            project_name=os.getenv("PROJECT_NAME", data.get("PROJECT_NAME", "app")),
            language=os.getenv("LANGUAGE", data.get("LANGUAGE", "go")),
            test_command=os.getenv("TEST_COMMAND", data.get("TEST_COMMAND", "go test ./...")),
            run_command=os.getenv("RUN_COMMAND", data.get("RUN_COMMAND", "go run .")),
            dev_rules_path=os.getenv("DEV_RULES_PATH", data.get("DEV_RULES_PATH", ".agents/rules/development/")),
            provider=os.getenv("DEFAULT_LLM_PROVIDER", data.get("DEFAULT_LLM_PROVIDER", "local")),
            developer_model_type=os.getenv("DEVELOPER_MODEL_TYPE", "coder"),
            developer_model_context_limit=int(os.getenv("DEVELOPER_MODEL_CONTEXT_LIMIT", "4096")),
            developer_model_description=os.getenv("DEVELOPER_MODEL_DESCRIPTION", "Coder-specialized local LLM with limited context window. Requires self-contained, micro-scoped Epics with explicit Input/Output data structures, pure functions, and testable boundary specifications."),
        )
