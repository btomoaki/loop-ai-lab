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
`run --phase refinement` を実行すると、すでに出力・完了している成果物（`overall_debate_log.md` や各エピックの `debate_log.md`, `epic_backlog.yaml`）を自動検知してスキップします。
途中で停止した場合でも、**未完了タスクの途中から即座に自動再開**されます。

### 2. ピンポイント再開（Pin-Point Restart）
特定のエピック以降のみを最新ルールでやり直したい場合は、該当するエピックフォルダ（`state/initiatives/epic_X`）のみを削除して再実行します。

```bash
# 例: epic_3 以降を削除して epic_3 からピンポイント再開する場合
rm -rf state/initiatives/epic_3_* state/initiatives/epic_4_* ...

# 再度リファインメントを実行（epic_1, epic_2 は自動スキップされ、epic_3 から即座に再開）
PYTHONPATH=. python3 runner/main.py run --phase refinement
```

### 3. 完全リセット（Full Reset）
成果物・ログ・ステートを全て消去して最初からやり直す場合：
```bash
PYTHONPATH=. python3 runner/main.py init
```

---

## ⚖️ トレードオフ・問いへの回答方法 (Answering Escalated Trade-offs)

リファインメント実行時に仕様の不備や代替案の選択（`Option A / Option B`）が発生した場合、パイプラインは安全のために `STATUS: REQUIRES_SPEC_DECISION` で一時停止します。

その場合は、`references/decisions.md`（または `references/qa.yaml` など）に以下のように**「Q & A 形式」で適当な感じで回答**を追記・保存してください。

```yaml
# references/decisions.md への追記例
- Q: 画像フォーマットは PNG ですか？
  A: PNG 固定です。サイズは 250px × 250px とします。

- Q: スタイルカスタマイズ機能は必要ですか？
  A: 必要ありません。シンプル優先で固定パラメータにします。
```

回答追記後、再度 `python3 runner/main.py run --phase refinement` を実行すると、AIペルソナ群が回答を反映して続きから自動再開されます。

---

## 📄 参照ドキュメント (References)
- **仕様書**: `references/icon_generator.md`
- **決定・回答事項**: `references/decisions.md`
- **リポジトリルール**: `.agents/rules/`
- **AIペルソナ定義**: `.agents/personas/`
