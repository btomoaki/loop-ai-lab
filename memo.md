# 📝 プロジェクト次回引き継ぎメモ (Handover Notes)

## 1. 次回着手する最優先課題 (Priority Tasks)

### ① スプリント自動開発ループ (Development Phase) の実行とTDD検証【最優先・機能優先】
- **内容**: 確立された全10統合ペルソナ ＆ 3セレモニー構造（DoR: 受入基準 <= 2）のもとで、`sprint_1_backlog.yaml` を元にした LLM 開発エージェントによる Go ソースコードの自動生成と、`sprint_1_harness.sh` テストハーネスの合格検証（Red ➔ Green）を実行する。
- **実行コマンド**: `PYTHONPATH=. python3 runner/main.py run --phase sprint`

---

## 2. 将来的な設計改善・リファクタリング構想 (Future Architecture Roadmap)

### 💡 Scrum パッケージ＆プラグイン構造化構想 (Spaghetti Prevention)
- **背景・課題**: 現在、スクラムに関連するファイルが `.agents/` (ルール/ペルソナ), `agents/` (プロンプト), `runner/engine/` (Pythonコード) と複数ディレクトリに散乱しており、スパゲッティ化の懸念がある。
- **改修構想**: これらを `packages/scrum/` という単一パッケージ内に自己完結型としてパッケージング統合する。
  - `packages/scrum/rules/`
  - `packages/scrum/personas/`
  - `packages/scrum/prompts/`
  - `packages/scrum/engine/`
- **効果**: `main.py` からの依存関係・呼び出し制御が極めてスマートになり、将来的に「小説執筆パッケージ」等への切り替えも容易になる。

---

## 3. 確立されたパイプライン規定・成果物マップ (Current Architecture State)
- **全10統合ペルソナ (`.agents/personas/`)**:
  - `po_business_analyst`, `scrum_master` (ファシリ集中・中立性), `operations_release_manager` (Day 2 Ops), `spec_compliance_auditor`, `software_architect_developer`, `db_data_engineer`, `devops_cloud_architect`, `finops_cost_governance` ($0.00/無料枠最優先), `qa_engineer` (Opposing View), `security_ethics_auditor` (AI倫理ストッパー/Rate Limiting 429/Swagger認証)
- **3つの独立セレモニー (`.agents/rules/` & `runner/engine/`)**:
  - `1_epic_refinement`: エピックリファインメント & 代替案エスカレーション (`epic_refinement_engine.py`)
  - `2_sprint_refinement`: バックログ分解 & DoR (`Acceptance Criteria <= 2`) (`sprint_refinement_engine.py`)
  - `3_sprint_execution`: スプリント開発 & DoDレビュー gate (アドホック設計変更禁止) (`sprint_execution_engine.py`)
- **スリム化コンテキストローダー (`ContextLoader`)**:
  - `- references/`, `- .agents/rules/1_epic_refinement/`, `- .agents/personas/` のフォルダ単位参照でプロンプt長を40%削減。

---

## 4. 次回再開用クイックスタートコマンド
```bash
# 既存のリファインメント成果物およびバックログの確認
ls -la state/initiatives/

# スプリント実装フェーズ（自動TDD開発ループ）の開始
PYTHONPATH=. python3 runner/main.py run --phase sprint
```
