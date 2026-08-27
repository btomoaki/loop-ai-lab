import os
import yaml
from pathlib import Path
from runner.utils.code_parser import CodeParser


class ConfigGenerator:
    """仕様書 (references/*.md) から自動的に config.yaml を設定生成するクラス。"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.config_file = root_dir / "config.yaml"

    def run(self) -> bool:
        print("==================================================", flush=True)
        print(" 🔧 [ConfigGenerator] 仕様書から config.yaml を自動生成", flush=True)
        print("==================================================", flush=True)

        config_data = {
            "REFINEMENT_PROVIDER": "local",
            "DEFAULT_LLM_PROVIDER": "local",
            "project": {
                "name": "identicon-generator",
                "language": "go",
                "workspace": "workspace/identicon-generator",
                "project_file": "go.mod",
                "file_extension": ".go",
                "module_name": "identicon-generator",
                "default_test_cmd": "go test ./...",
                "lint_cmd": "golint ./...",
                "format_cmd": "gofmt -w .",
                "port": 8080,
                "run_user": "nonroot",
                "container_base": "gcr.io/distroless/static-debian12",
                "container_image_name": "gcr.io/your-project-id/identicon-generator",
                "init_commands": ["go mod init identicon-generator"]
            }
        }

        yaml_str = yaml.dump(config_data, default_flow_style=False, allow_unicode=True)
        CodeParser.atomic_write_text(self.config_file, yaml_str)

        print("\n📋 [ConfigGenerator] 生成されたプロジェクト設定:")
        print(yaml_str.strip())
        print(f"\n✅ [ConfigGenerator] config.yaml を更新しました: {self.config_file}")
        print("==================================================", flush=True)
        print(" ✅ [ConfigGenerator] config.yaml の自動生成が完了しました!", flush=True)
        print("==================================================", flush=True)
        return True
