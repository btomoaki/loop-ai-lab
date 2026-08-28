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
    executor_model: str = "local-coder"
    llama_max_tokens: int = 4096
    extra_env: Dict[str, str] = field(default_factory=dict)


    @property
    def workspace_rel(self) -> str:
        return f"workspace/{self.project_name}"

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
            executor_model=os.getenv("EXECUTOR_MODEL", data.get("EXECUTOR_MODEL", "Devstral-Small-2-24B-Instruct")),
            llama_max_tokens=int(os.getenv("LLAMA_MAX_TOKENS", data.get("LLAMA_MAX_TOKENS", "4096"))),
        )
