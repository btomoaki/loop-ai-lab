# Loop AI Lab - System Architecture & Handover Materials
**作成日時**: 2026-08-21
**目的**: 別PC環境（ローカルLLM非搭載環境）での手動リファクタリング、仕様確認、およびシステム引き継ぎ用の課題・懸念点まとめ

---

## 1. 全体構造と設計アーキテクチャ

本プロジェクト (`loop-ai-lab`) は、アジャイル・Scrum 開発プロセスを自動化・自律実行するためのスクラムランナー基盤です。

### 階層構造 (Initiative -> Epic Phase -> Task/Sprint YAML)
```text
state/
├── .evaluator/
│   ├── memo.md             # 永続化されたアーキテクチャルール・設計決定事項
│   └── current_issues.md   # 最新ループのテスト実行結果・エラーログ
├── initiatives/
│   └── .gitkeep            # 各 Epic の生成物 (sprint_1_backlog.yaml, harness.sh, policy.md) の出力先
workspace/
└── avatar-service/        # 対象マイクロサービスのソースコード開発領域
    ├── go.mod
    └── internal/
        └── domain/
            ├── model/      # 【重要】純粋な struct / データ構造のみを配置
            └── service/    # (今後) 生成ロジックやドメインサービス/ファクトリを配置
```

---

## 2. 【重要】今回確定したドメイン設計ルール (Model Layer Purity)

次回リファインメントおよびコード修正時の最重要ルールです：

1. **`internal/domain/model/` の純粋性**:
   - `model/` パッケージに配置するファイル（例: `grid.go`）は、**純粋な struct や値オブジェクトの型定義（`type Grid struct { Cells [5][5]bool }`）のみ** に留めます。
2. **ファクトリ・生成ロジックの分離**:
   - `func NewGrid(...)` のようなコンストラクタ、イニシャライザ、変換アルゴリズム関数を **`model/` パッケージ内に記述してはいけません**。
   - これらは `domain/service/` や `factory/` などの別パッケージへ完全分離してください。

---

## 3. スクラムランナー (`runner/`) の仕組みと技術的修正点

### ① LLM 通信アダプター (`runner/adapters.py`)
- **参照先**: llama.cpp Native Endpoint `http://127.0.0.1:11435/completion`
- **ソケットハング対策**: `urllib` のリクエストヘッダーに `"Connection": "close"` を追加済み（LLMの応答完了時にソケットを即切断）。
- **ローカルLLM非搭載環境での注意点**:
  - ローカルLLMがない環境で `run_scrum.py` を実行すると 11435 ポートへの接続エラーになります。
  - 別PCで実行する場合は、環境変数 `GEMINI_API_KEY` を設定して `GeminiAdapter` を使うか、ハーネス単体テスト (`bash state/initiatives/epic_X/sprint_1_harness.sh`) を直接実行してください。

### ② マークダウンコードブロックの誤抽出・サニタイズ (`runner/run_scrum.py`)
- LLM がコードを出力する際、先頭や末尾に ` ```go ` や ` ``` ` などのフェンス記法を混入させる問題に対し、`parse_and_extract_files` 内で強力な regex サニタイズと自動 `gofmt -w` を実行する安全防御コードを組み込み済みです。

### ③ テストハーネスの非ブロック化
- `subprocess.run` 呼び出し時に `stdin=subprocess.DEVNULL` を指定し、ハーネススクリプトが標準入力待ちでハングする現象を防止しています。

---

## 4. ループ側の課題・懸念点まとめ (Handover Issues)

別PCで構文や矛盾点をリファクタリングする際、特にご留意いただきたい課題です：

| # | 領域 | 課題・懸念点 | 推奨される対応策 |
|---|---|---|---|
| 1 | **Refinement Prompts** | `refinement-planner.md` のプロンプトが旧来の `model/` 内への関数同梱を生成してしまう懸念がある。 | リファインメント時に `state/.evaluator/memo.md` の内容（モデル純粋化ルール）を確実にプロンプトへ組み込み、`model/` に関数を生成させないようプロンプトの制約条件を強化する。 |
| 2 | **Test Harness Strictness** | 各 Epic の `sprint_1_harness.sh` 内で `go vet` や `gofmt` の判定が厳密。 | ハーネス生成時に `go vet` や `gofmt` が落ちた場合のエラーメッセージが LLM に正確に届くよう、サニタイズ処理を維持する。 |
| 3 | **環境依存性** | `run_scrum.py` 起動時に 11435 ポート (Devstral) に固定依存している。 | アダプター切替引数 (`--provider gemini` / `--provider local`) を `run_scrum.py` の CLI オプションとして柔軟に受け取れるようリファクタリングすると別PCでも使いやすい。 |

---

## 5. 別PC（LLM非搭載環境）での手動リファクタ・検証手順

1. **ドメインモデルの整理**:
   - `workspace/avatar-service/internal/domain/model/grid.go` に純粋な `struct` のみを定義。
   - 生成関数 `NewGrid` を `internal/domain/service/grid_factory.go` 等へ分離。
2. **ハーネスの単体実行**:
   - `bash state/initiatives/epic_1_domain/sprint_1_harness.sh` を直接実行し、`Check 1/6` 〜 `Check 6/6` が ALL GREEN になるか検証。
3. **コミット**:
   - 整理完了後、`git commit` で履歴を保存。

