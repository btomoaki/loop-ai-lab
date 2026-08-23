# 🚀 Loop AI Lab - Autonomous Scrum Pipeline

AI ペルソナ群による「アーキテクチャディベート」「バックログ自動生成」「TDDテスト駆動開発」を自律実行する Scrum パイプラインフレームワークです。

---

## 🛠️ 基本コマンド (Basic Commands)

### 1. プロジェクトの初期化 (Init / Reset)
プロジェクトの設定 (`config.yaml`) および基本構造を初期化します。
最初から完全にやり直す場合（フルリセット）も本コマンドを実行してください。
```bash
PYTHONPATH=. python3 runner/main.py init
```

### 2. 設計フェーズの実行 (Refinement Phase)
仕様書（`references/`）を元に、マルチペルソナによる全体アーキテクチャディベート、エピック分類、および `sprint_x_backlog.yaml` / ハーネススクリプトを自動生成します。
```bash
PYTHONPATH=. python3 runner/main.py run --phase refinement
```

### 3. 実装スプリントの実行 (Development Phase)
生成されたスプリントバックログに従い、自律TDD開発（テスト作成 ➔ コード実装 ➔ ハーネス検証）を実行します。
```bash
PYTHONPATH=. python3 runner/main.py run --phase development
```

---

## ⏯️ 中断と再開の仕様 (Resume & Restart Behavior)

本フレームワークは**ファイルベースの「中断再開（Resume Mode）」**に対応しており、途中で停止した場合でも安全かつ高速に復帰できます。

### 1. 自動「中断再開」（Resume）
`run --phase refinement` を実行すると、すでに生成・完了している成果物（`overall_debate_log.md` や各エピックの `debate_log.md`, `epic_backlog.yaml`）を自動検知してスキップします。
途中でネットワークが切れたり中断した場合でも、**未完了のエピックの途中から即座に再開**されます。

### 2. ピンポイント再開（Pin-Point Restart）
特定のエピック以降のみを最新のルールでやり直したい場合は、該当するエピックフォルダのみを削除して再実行します。

```bash
# 例: epic_3 以降を削除して epic_3 から再開する場合
rm -rf state/initiatives/epic_3_* state/initiatives/epic_4_* ...

# 再度リファインメントを実行（epic_1, epic_2 はスキップされ、epic_3 から即座に再開）
PYTHONPATH=. python3 runner/main.py run --phase refinement
```

### 3. 完全リセット（Full Reset）
すべての既存成果物・状態を破棄して最初からやり直す場合：
```bash
rm -rf state/initiatives/ state/.evaluator/* workspace/*
PYTHONPATH=. python3 runner/main.py init
```

---

## 📄 参照ドキュメント (References)
- **仕様書**: `references/icon_generator.md`
- **確定意思決定事項**: `references/decisions.md`
- **リポジトリルール**: `.agents/rules/`
- **AIペルソナ定義**: `.agents/personas/`
