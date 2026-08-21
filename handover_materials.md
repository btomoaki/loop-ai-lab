# Loop AI Lab - System Architecture & Handover Materials
**最終更新日時**: 2026-08-21
**目的**: システム引き継ぎ、アーキテクチャルール、および次回リファインメント・開発時の注意事項まとめ

---

## 1. 全体構造と設計アーキテクチャ

本プロジェクト (`loop-ai-lab`) は、アジャイル・Scrum 開発プロセスを自動化・自律実行するためのスクラムランナー基盤です。

### 階層構造 (Initiative -> Epic Phase -> Task/Sprint YAML)
```text
state/                      # 【非コミット領域】リファインメント・評価ループ時の動的・一時生成物 (.gitkeep 保護)
├── .evaluator/
│   ├── latest_prompt.md    # LLM へ送信された直近の完全プロンプト
│   ├── memo.md             # アーキテクチャルール・設計決定事項
│   └── current_issues.md   # テスト実行結果・エラーログ
├── initiatives/            # 各 Epic の生成物 (sprint_N_backlog.yaml, harness.sh, policy.md) の出力先
workspace/                  # 【非コミット領域】AIループによって生成・評価されるターゲット開発領域 (.gitkeep 保護)
runner/                     # 【主要ソース】スクラムランナー基盤 Python モジュール
scripts/                    # 【主要ソース】検証・環境初期化シェルスクリプト群
```

---

## 2. 確定ドメイン設計ルール (Model Layer Purity)

次回リファインメントおよびターゲットコード修正時の最重要ルールです：

1. **`internal/domain/model/` の純粋性**:
   - `model/` パッケージに配置するファイル（例: `grid.go`）は、**純粋な struct や値オブジェクトの型定義（`type Grid struct { Cells [5][5]bool }`）のみ** に留めます。
2. **ファクトリ・生成ロジックの分離**:
   - `func NewGrid(...)` のようなコンストラクタ、イニシャライザ、変換アルゴリズム関数を **`model/` パッケージ内に記述してはいけません**。
   - これらは `domain/service/` や `factory/` などの別パッケージへ完全分離してください。

---

## 3. Git 管理・コミットルール

- **主要ソース (コミット対象)**:
  - ハーネス基盤本体の固定コード・スクリプト・設定 (`runner/`, `scripts/`, `policies/`, `agents/`, `config.env` 等)
- **コミット対象外 (初期化・成果物・一時領域)**:
  - `.gitkeep` が配置されているディレクトリ配下全般 (`state/`, `workspace/`, `references/` 等)
  - 一時的な解析メモファイル (`repository_analysis.md` 等)

---

## 4. スクラムランナー (`runner/`) およびスクリプト (`scripts/`) の利用方法

### ① クラウド単体リファインメントの実行
ローカル LLM が起動していない環境でも、Gemini API キーを設定することでクラウド LLM のみで単体リファインメントを実行できます：

```bash
export GEMINI_API_KEY="your-gemini-api-key"
python3 runner/run_scrum.py --phase refinement
```
- `references/*.md`（`GEMINI.md`, `go_clean_architecture.md` 等）および `REQUIREMENT_FILE` が自動で読み込まれ、`state/initiatives/` 配下にスプリント計画・ハーネス・ポリシーが生成されます。

### ② ローカル LLM スプリント開発の実行
ローカルの `11435` ポートで `llama-server` (Devstral) 等を起動した状態で以下を実行します：

```bash
python3 runner/run_scrum.py --phase sprint --sprint 1
```

### ③ Lab 環境の安全初期化
ターゲットコードや一時状態をクリアする場合は以下を実行します：

```bash
# 通常クリーンアップ (state/.evaluator や workspace 内の成果物コードを初期化)
bash scripts/clean-env.sh

# フルクリーンアップ (state/initiatives 配下のスプリント計画も含め完全リセット)
bash scripts/clean-env.sh --all
```
※ いずれも各ディレクトリの `.git` および `.gitkeep` は安全に保護されます。

---

## 5. 次回リファインメント時の引き継ぎ注意事項

1. **バックログ・ハーネス生成時の「モデル純粋性」徹底**:
   - Evaluator が `sprint_1_backlog.yaml` および `sprint_1_harness.sh` を生成する際、旧仕様のように `internal/domain/model/grid.go` 内に `NewGrid` の存在を強要する条件を出力させないよう、`references/go_clean_architecture.md` や `state/.evaluator/memo.md` の指示を評価プロンプトで徹底させてください。
