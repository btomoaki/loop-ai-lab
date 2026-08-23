"""ProjectConfig: config.yaml の project: セクションを読み込むデータクラス。"""

import yaml
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProjectConfig:
    """プロジェクト固有設定を保持するデータクラス。

    config.yaml の project: セクションから読み込まれる。
    全フィールドにデフォルト値を持ち、project: が存在しなくてもエラーにならない。
    """

    # プロジェクト情報
    project_name: str = ""
    workspace_rel: str = ""

    # 言語プロファイル
    language: str = ""
    module_name: str = ""
    default_test_cmd: str = ""
    init_commands: list = field(default_factory=list)
    project_file: str = ""
    format_cmd: str = ""
    lint_cmd: str = ""
    file_extension: str = ""

    # コンテナ・デプロイ
    container_image_name: str = ""
    container_base: str = ""
    run_user: str = ""
    port: int = 0

    @classmethod
    def load(cls, root_dir: Path) -> "ProjectConfig":
        """config.yaml から ProjectConfig を読み込む。

        project: セクションが存在しない場合は全デフォルト値の ProjectConfig を返す。
        """
        config_path = root_dir / "config.yaml"
        if not config_path.exists():
            print("⚠️ [ProjectConfig] config.yaml が見つかりません。デフォルト値を使用します。")
            return cls()

        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        data = raw.get("project", {})
        if not data:
            print("⚠️ [ProjectConfig] config.yaml に project: セクションがありません。'runner/main.py init' で生成してください。")
            return cls()

        return cls(
            project_name=data.get("name", ""),
            workspace_rel=data.get("workspace", ""),
            language=data.get("language", ""),
            module_name=data.get("module_name", ""),
            default_test_cmd=data.get("default_test_cmd", ""),
            init_commands=data.get("init_commands", []),
            project_file=data.get("project_file", ""),
            format_cmd=data.get("format_cmd", ""),
            lint_cmd=data.get("lint_cmd", ""),
            file_extension=data.get("file_extension", ""),
            container_image_name=data.get("container_image_name", ""),
            container_base=data.get("container_base", ""),
            run_user=data.get("run_user", ""),
            port=data.get("port", 0),
        )

    @property
    def workspace_prefixes(self) -> list:
        """CodeParser用: 重複パス除去に使うプレフィックス一覧。"""
        if not self.project_name:
            return []
        return [
            f"workspace/{self.project_name}/",
            f"{self.project_name}/",
        ]

    @property
    def has_container(self) -> bool:
        """コンテナ関連設定が存在するか。"""
        return bool(self.container_image_name or self.container_base)
