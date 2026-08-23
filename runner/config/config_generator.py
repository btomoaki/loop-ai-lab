"""ConfigGenerator: references/ 配下の仕様書からLLM経由で config.yaml を自動生成する。"""

import re
import yaml
from pathlib import Path
from runner.adapters.llm_adapter import LLMAdapterFactory


class ConfigGenerator:
    """仕様書を解析して config.yaml の project: セクションを自動生成する。"""

    # scan_references で除外するファイル名
    EXCLUDE_FILES = {"GEMINI.md", ".gitkeep"}

    # 仕様書から抽出する重要セクションのキーワード
    KEY_SECTIONS = [
        "技術スタック", "Technology Stack",
        "アーキテクチャ", "Architecture",
        "コンテナ", "Container", "Docker",
        "デプロイ", "Deploy", "Cloud Run",
        "システム概要", "Overview",
        "ポート", "Port",
    ]

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.refs_dir = root_dir / "references"
        self.llm = LLMAdapterFactory.get_adapter()

    def scan_references(self) -> str:
        """references/ 内の全 .md ファイルを読み込み、重要セクションを抽出して返す。"""
        if not self.refs_dir.exists():
            print("⚠️ [ConfigGenerator] references/ ディレクトリが見つかりません。")
            return ""

        texts = []
        for md_file in sorted(self.refs_dir.glob("*.md")):
            if md_file.name in self.EXCLUDE_FILES:
                continue
            content = md_file.read_text(encoding="utf-8")
            # 長い仕様書は重要セクションのみ抽出
            if len(content) > 2000:
                content = self._extract_key_sections(content)
            texts.append(f"--- {md_file.name} ---\n{content}")
            print(f"📄 [ConfigGenerator] 読み込み: {md_file.name} ({len(content)} chars)")

        if not texts:
            print("⚠️ [ConfigGenerator] references/ 内に有効な .md ファイルがありません。")
            return ""

        return "\n\n".join(texts)

    def _extract_key_sections(self, content: str) -> str:
        """長い仕様書から重要セクション（技術スタック、コンテナ設計等）のみ抽出する。"""
        lines = content.split("\n")
        result = []
        capturing = False
        current_section_level = 0

        for line in lines:
            # 見出し行を検出
            heading_match = re.match(r'^(#{1,4})\s+(.+)', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2)
                # キーワードに一致するセクションはキャプチャ開始
                if any(kw.lower() in title.lower() for kw in self.KEY_SECTIONS):
                    capturing = True
                    current_section_level = level
                    result.append(line)
                    continue
                # 同レベル以上の別セクションに到達したらキャプチャ終了
                elif capturing and level <= current_section_level:
                    capturing = False

            if capturing:
                result.append(line)

        return "\n".join(result) if result else content[:2000]

    def generate_project_config(self) -> dict:
        """LLMに仕様書を渡し、構造化されたproject configをYAMLとして生成する。"""
        specs = self.scan_references()
        if not specs:
            return {}

        prompt = (
            "[INSTRUCTION] Read the spec below. Output ONLY a YAML block. No explanation.\n\n"
            "```yaml\n"
            "project:\n"
            "  name: <project-name>\n"
            "  workspace: workspace/<project-name>\n"
            "  language: <go|python|rust|yaml|typescript>\n"
            "  module_name: <module-name>\n"
            "  default_test_cmd: <test command>\n"
            "  init_commands:\n"
            "    - <init command or empty list []>\n"
            "  project_file: <go.mod|Cargo.toml|package.json|etc>\n"
            "  format_cmd: <format command>\n"
            "  lint_cmd: <lint command>\n"
            "  file_extension: <.go|.py|.rs|.yaml|.ts>\n"
            "  container_image_name: <image name or empty>\n"
            "  container_base: <base image or empty>\n"
            "  run_user: <container user or empty>\n"
            "  port: <port number or 0>\n"
            "```\n\n"
            f"SPEC:\n{specs}"
        )

        print("🔍 [ConfigGenerator] LLMに仕様書を送信してプロジェクト設定を生成中...", flush=True)
        resp = self.llm.generate_text(prompt)

        if not resp:
            print("⚠️ [ConfigGenerator] LLMから応答がありませんでした。")
            return {}

        return self._parse_yaml_response(resp)

    def _parse_yaml_response(self, resp: str) -> dict:
        """LLM応答からYAMLブロックを抽出してパースする。"""
        # ```yaml ... ``` ブロックを探す
        match = re.search(r'```yaml\s*\n(.*?)```', resp, re.DOTALL)
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError as e:
                print(f"⚠️ [ConfigGenerator] YAMLパースエラー: {e}")
                return {}

        # フォールバック: project: で始まる行を探す
        match2 = re.search(r'(project:\s*\n(?:\s+.+\n)*)', resp)
        if match2:
            try:
                return yaml.safe_load(match2.group(1)) or {}
            except yaml.YAMLError:
                pass

        # 最終フォールバック: 応答全体をYAMLとしてパース
        try:
            return yaml.safe_load(resp) or {}
        except yaml.YAMLError:
            print("⚠️ [ConfigGenerator] LLM応答をYAMLとしてパースできませんでした。")
            print(f"--- LLM応答 (先頭500文字) ---\n{resp[:500]}")
            return {}

    def write_config(self, project_data: dict):
        """既存 config.yaml に project: セクションをマージ書き込みする。"""
        config_path = self.root_dir / "config.yaml"

        if config_path.exists():
            existing = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        else:
            existing = {}

        existing.update(project_data)

        config_path.write_text(
            yaml.dump(existing, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        print(f"✅ [ConfigGenerator] config.yaml を更新しました: {config_path}")

    def run(self) -> bool:
        """仕様書読み込み → LLM生成 → config.yaml 書き込みの一連のフロー。"""
        print("=" * 50)
        print(" 🔧 [ConfigGenerator] 仕様書から config.yaml を自動生成")
        print("=" * 50, flush=True)

        project_data = self.generate_project_config()
        if not project_data:
            print("❌ [ConfigGenerator] プロジェクト設定の生成に失敗しました。")
            return False

        # 生成された設定をプレビュー表示
        print("\n📋 [ConfigGenerator] 生成されたプロジェクト設定:")
        print(yaml.dump(project_data, allow_unicode=True, default_flow_style=False))

        self.write_config(project_data)

        print("=" * 50)
        print(" ✅ [ConfigGenerator] config.yaml の自動生成が完了しました!")
        print("=" * 50)
        return True
