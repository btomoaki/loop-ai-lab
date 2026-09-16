# 📝 プロジェクト次回引き継ぎメモ (Handover Notes)

## 0. 📌 本日の作業完了ステータス & 次回再開手順 (2026-09-06 22:25 最新更新)

### 🏁 現在のステータス
- **リファインメント進捗**: **セレモニー 1 完全完了（APPROVED）** ➔ 次回は **セレモニー 2（スプリントバックログ・リファインメント）** から開始。
- **Git作業ツリー状態**: 全改修ファイルがステージング済み（`git add` 完了、コミット承認待ち）。
- **3者独立レビュー判定結果**:
  - 💰 **コスト (FinOps)**: [`state/.evaluator/ceremony_1_review_cost.md`](file:///home/wimet/work/loop-ai-lab/state/.evaluator/ceremony_1_review_cost.md) ➔ **✅ APPROVED** (Rate Limiting / 外部DB / 認証排除、Cloud Run 無料枠保証)
  - 🏛️ **技術 (Architect & Ruler)**: [`state/.evaluator/ceremony_1_review_tech.md`](file:///home/wimet/work/loop-ai-lab/state/.evaluator/ceremony_1_review_tech.md) ➔ **✅ APPROVED** (Clean Architecture 4層、Double-Mockability、事前コード実装禁止)
  - 📋 **責任 (PO & Spec Auditor)**: [`state/.evaluator/ceremony_1_review_scope.md`](file:///home/wimet/work/loop-ai-lab/state/.evaluator/ceremony_1_review_scope.md) ➔ **✅ APPROVED** (仕様書 100% 網羅、SVG排除、Cloud Run協調契約)

---

### 🏆 本日完了した最重要改修サマリー
1. **Ceremony 1 独立3者レビューゲート（コスト・技術・責任の分離判定）の新設**:
   - 単一LLMによるロールプレイ会話劇で終わらせず、確定したエピック分割案に対して**独立した3つのプロンプトで別個にGemini監査を実行**する仕組みを `EpicRefinementEngine` / `RefinementEngine` に実装。
   - 監査証跡を `state/.evaluator/ceremony_1_review_{cost,tech,scope}.md` として物理ファイル保存。3者全員が APPROVED でない限り Ceremony 2 に進めない防壁を確立。
2. **未要求仕様（Rate Limiting）の根本原因解明と完全根絶**:
   - `agents/2_sprint_refinement/sprint_refinement_planner.md` にハードコードされていた未要求仕様「Mandatory IP-based rate limiting (`HTTP 429`)」を完全削除（大元凶の根本治療）。
3. **Clean Architecture ディレクトリ命名の完全統一（Go予約語 `interface` の残存根絶）**:
   - 古い `internal/interface/` や `internal/usecase/` が残存していた全ファイル（`sprint_refinement_planner.md`, `backlog.tpl`, `patch.tpl`, `code_gen.tpl`, `backlog_harness.py`, `sprint_execution_engine.py`）をすべて最新規約に修正：
     - 抽象入力ポート: `internal/domain/usecase/`
     - 具象実装: `internal/application/usecase/`
     - 配信層（予約語回避）: `internal/delivery/http/`
     - 静的アセット: `web/static/`
4. **プロンプトテンプレート化 & セレモニー別階層化 (`template/prompt/`)**:
   - 旧 `assets/` を完全撤廃し、セレモニー別（`common/`, `ceremony_1/`, `ceremony_2/`, `ceremony_3/`）に再編。
5. **Fail-Fast 設計の徹底（サイレントフォールバックの完全排除）**:
   - プロンプト作成・レンダリング失敗時に空文字やデフォルト値で続行せず、即座に `raise RuntimeError` でエラー停止する方針を全アダプタ・エンジンに適用。

---

### 🔄 次回再開時の手順 (Refinement Restart Procedure)

1. **保留中コミットの実行**:
   ```bash
   git commit -m "feat(governance): add ceremony 1 tripartite review gate, eliminate rate limiting hardcodes, and unify clean architecture paths"
   ```

2. **セレモニー 2（スプリントバックログ詳細化 & 独立監査）の実行**:
   ※セレモニー 1 はすでに全3者 APPROVED で完了・保存されているため自動スキップされ、即座にクリーンな状態でセレモニー 2 が開始されます：
   ```bash
   PYTHONPATH=. python3 runner/main.py run --phase refinement -y
   ```

3. **全自動実行（リファインメント ➔ スプリント自律開発ループ）を行う場合**:
   ```bash
   PYTHONPATH=. python3 runner/main.py run --phase all -y
   ```

4. **進行状況のリアルタイム監視**:
   ```bash
   watch cat ./state/status.md
   ```

---

## 0.1 📌 以前の自律開発ループ進捗 & 過去の経緯 (2026-09-06 18:43)

### 🛠️ これまでに洗い出された根本是正必須課題（ゼロリセット前に一括改修）
0. **【最上流ガバナンス】「スペック担当 vs コスト担当 vs 実装アーキテクト」の3極バランス（三権分立）ディベート新設 (正式採用決定)**:
   - **背景**: 仕様外の機能混入（レートリミット等）を防ぎつつ、過剰なそぎ落とし（ハリボテ化）を防ぐ。
   - **3極構造と明確なガードレール**:
     - **スペック担当 (Spec Compliance)**: 仕様書（`references/`）の要件網羅と漏れ防止を監視。
     - **コスト担当 (FinOps / Anti-Complexity)**: 仕様外の外部機能（勝手なレートリミット、不要な外部DB/認証、過剰な外部ライブラリ導入）を厳しく排除・削減。
     - **実装・アーキテクト担当 (Software Architect)**: 保守性・テスタビリティ・疎結合性（Clean Architectureのレイヤー分離やインターフェース、テストコード）を「不可侵の内部品質基準（DoD）」として死守・擁護する。
     - **ガードレール**: コスト担当の攻撃対象は「仕様外機能・過剰な外部依存」に限定し、実装側の設計品質（Clean Architecture / TDD用モック・レイヤー）はコスト削減の対象外とする。
1. **テスト先行生成（Test-First TDD）への刷新 (最重要・ユーザー合意済み)**:
   - 現状の「Model ➔ Service ➔ Test」の実装先行順から、「AC ➔ Test（インターフェース/シグネチャ確定） ➔ 実装」へ逆転。
   - テストコードをコンテキストとして読み込ませて実装を生成させることで、シグネチャ乖離・型不整合・架空パッケージ捏造を一掃する。
2. **パッケージ管理ロックファイル（`go.sum`）の直接出力禁止 & `go mod tidy` 自動実行**:
   - LLM がデタラメなチェックサムを持つ `go.sum` を直接出力して `SECURITY ERROR: checksum mismatch` や `malformed go.sum` を引き起こす問題（Sprint 6, 8 で顕在化）。
   - **是正策**: LLM が生成したファイルリストから `go.sum` を強制除外し、依存追加時はコンテナ内の `go mod tidy` 経由のみとする。
3. **サブディレクトリ内への不正な `go.mod` / `go.sum` 出力防止**:
   - `internal/usecase/` 等に勝手に `go.mod` を作ってツールチェーンを壊す問題（Sprint 6）。ルート以外に出力された場合は即時検知・自動削除。
4. **最新 Go ツールチェーン & 公式 Linter コンテナ採用**:
   - `golang:alpine`（Go 1.27系）および `golangci/golangci-lint:v1.59-alpine` 採用済み。
5. **動的レイヤー判定の適正化**:
   - テスト単体タスク時に `Business_Logic` や `Entrypoint` を誤選択して既存完成コードを破壊しないよう、タスク種別ごとのレイヤー除外ルールを厳格化。
6. **予約語 `package interface` や未承認外部ライブラリ import の抑止**:
   - 標準パッケージ（`net/http` 等）や指定済みのルーティングライブラリ以外の架空 import をシステムプロンプトで厳格に規制。

---

## 0.1 📌 過去の達成状況 (2026-09-05 最終更新)

### 🏆 本日の歴史的達成: Ceremony 2（スプリント精緻化）完全完走 & 4重独立監査 Loop #5 全員 APPROVED 獲得！

1. **全体独立監査ゲート（Loop #5）において 4者全員からパーフェクト「APPROVED」を獲得**:
   - 🔍 **Spec Compliance Auditor**: **✅ APPROVED** (仕様・ADR全6件 100%網羅、仕様改ざんゼロ、全タスク DoR $AC \le 3$ 準拠)
   - 🛡️ **Security & AI Ethics Auditor**: **✅ APPROVED** (リソース枯渇防止、コンテナ non-root UID 65532、外部DB/認証不要のステートレス設計)
   - ☁️ **Platform & DevOps Auditor (新設)**: **✅ APPROVED** (Platform vs App 責務境界の完全遵守、クラウド協調契約クリア)
   - 🔍 **Ruler Governance Auditor**: **✅ APPROVED** (シフトレフトコンテナ検証、`--rm`/`trap` ライフサイクル保証、ドメインモデル純粋性)

2. **プラットフォーム vs アプリケーションの「責務の分解点」確立とインフラ運用者ペルソナの配置改革**:
   - **レートリミットの責務分離**:
     - IPレートリミットや DDoS/WAF 防御はエッジ・プラットフォーム（API Gateway, Cloud Armor, リバースプロキシ）の責務。
     - アプリ内にインメモリレートリミッターを持ち込むと、Cloud Run のステートレスオートスケーリングが破壊されるアンチパターンであることを明確化し、アプリ（Epic 5）から完全排除。
   - **インフラ運用者ペルソナ（Platform & DevOps）のレビュー側配置**:
     - ペルソナを作成側（ディベート）から**ルーラーと同じ「レビュー・監査側（独立監査ゲート）」**へ移管。
     - 「アプリがPFの責務を余計に侵犯していないか（ステートレス性の維持）」、「PFとの協調契約（動的 `$PORT`、`/healthz`、`SIGTERM` 10秒ドレイン、Distroless non-root）を満たしているか」を判定する専用監査ステップ（`audit_platform_ops.md`）を `sprint_refinement_engine.py` に新設。
   - **ガバナンスルール・ペルソナの整合改定**:
     - `.agents/rules/development/developer_standards.md` §3 を改定（一律のアプリ内レートリミット義務を撤廃し、責務境界とPF協調規約を規定）。
     - `.agents/personas/devops_cloud_architect.md` および `security_ethics_auditor.md` を新ポリシーに適合。

3. **全7エピック（Epic 1〜7）のスプリントバックログ完全是正**:
   - **Epic 1**: ホスト側 `&&` 連結排除、`TASK-1.2` の AC 過密（7件）を `TASK-1.2a`（コア層）と `TASK-1.2b`（配信・インフラ層）へ分割是正。
   - **Epic 2**: `TASK-2.5` に `hash[3..15]` の偶奇パリティ計算セル塗りつぶしACを明記、`TASK-2.8` のモデル数正規表現を `^3$` に修正。
   - **Epic 3**: テスト作成前の早期 `go test` をファイル存在・構文検査（`test -f`, `grep`）に是正。
   - **Epic 4**: ユースケース層と DI 配線の健全性確認済み。
   - **Epic 5**: 不要なレートリミットタスクを全廃し、欠番 `TASK-5.2` を解消、動的ポートバインドとシグナルハンドリングに純化。
   - **Epic 6**: 単一バイナリ同梱SPAフロントエンド（Go `embed`, Tailwind CDN, Vanilla JS, 250x250プレビュー, ダウンロード）確定。
   - **Epic 7**: `Dockerfile` パス正規化、コンテナ起動スクリプトへの `trap EXIT` 自動クリーンアップ保証を付与。

4. **PC再起動（クラッシュ）の根本原因特定（解決済み）**:
   - Windows イベントログ（Event ID 1001）調査により、ストップコード **`0x00000116` (`VIDEO_TDR_FAILURE`)** によるグラフィックドライバタイムアウト起因のBSoDと特定。電源ユニット故障ではないため、ハードウェアの買い換えは不要。

---

## 1. 🛡️ 全体独立監査で得られた教訓と再発防止フィードバック集 (Audit Anti-Patterns & Best Practices)

過去の全体独立監査（Loop #1〜#4）で指摘・VETOとなった典型的なアンチパターンと、その根本是正アプローチを体系化しました。今後のプロンプトテンプレート改善や新規エピック生成時のチェックリストとして活用します。

### ① ホスト側コマンド連鎖・パイプの禁止 (Shift-Left Containerization)
- **アンチパターン**:
  - `docker compose run --rm test go version && docker compose run --rm lint ...`
  - `docker compose run --rm test ... | grep foo`
- **問題点**: ホスト環境のシェル機能（`&&`, `|`）に依存し、ホスト側の終了ステータスやパイプ動作によってコンテナ外で検証が歪む。また「ホストツールチェーン汚染ゼロ」の理念に抵触する。
- **再発防止策**:
  - 複合検査が必要な場合は、**必ずコンテナ内サブシェルに集約する**:
    `docker compose run --rm test sh -c "test -f A && test -f B && echo OK"`
  - 単一サービス検証で十分な場合は `echo OK` や単一コマンドで完結させる。

### ② 受入条件（AC）の過密化と単一責任原則 (DoR Micro-Task Principle)
- **アンチパターン**:
  - `TASK-1.2`: 7個のディレクトリ作成（`cmd/`, `domain/model/`, `domain/service/`, `usecase/`, `interface/`, `infrastructure/`, `docs/`）を1タスクに詰め込み。
- **問題点**: Definition of Ready（DoR）の「1タスクあたりの受入条件は 2〜3 件以下」というマイクロタスク原則に違反し、後続の自律TDD実装（Ceremony 3）でLLMが混乱・タイムアウトを起こす。
- **再発防止策**:
  - レイヤーごと、関心事ごとにタスクを分割する（例: `TASK-1.2a: コアレイヤー骨格`, `TASK-1.2b: 配信・インフラレイヤー骨格`）。

### ③ テスト作成前タスクでの早期 `go test` 呼び出し (Prerequisite Validation)
- **アンチパターン**:
  - スケルトン作成タスクやハンドラー作成タスクの `verify_command` に、まだテストコード（`*_test.go`）が存在しない段階で `go test -v ./...` を指定。
- **問題点**: テストコードがないため Go コンパイラが `[no test files]` で即座に非ゼロ終了し、永久にパスしない。
- **再発防止策**:
  - テスト作成前タスクの検証は、**ファイル存在検査（`test -f ...`）**、**キーワード検査（`grep -q ...`）**、または **`echo OK`** を使用する。
  - `go test` は、テストコードを作成・配備するタスク以降でのみ指定する。

### ④ プラットフォーム vs アプリケーションの責務境界 (Separation of Concerns)
- **アンチパターン**:
  - アプリ（Cloud Run コンテナ）内に、インメモリの IP レートリミッター（トークンバケット）や WAF / DDoS 防御ロジックを実装。
- **問題点**:
  - コンテナがオートスケールした際にインメモリ状態が共有されず破綻する。
  - アプリの肥大化・ステートレス性の破壊を招き、セキュリティ監査とスペック監査の板挟み・死線（Deadlock）を引き起こす。
- **再発防止策**:
  - IPレートリミット、DoS防御、SSL終端は「エッジ・プラットフォームの責務」としてアプリから完全に排除する。
  - アプリの責務は「プラットフォームとの協調契約（動的 `$PORT`、軽量 `/healthz`、`SIGTERM` 10sドレイン、non-root）」に純化する。
  - インフラ運用者ペルソナをレビュー側（独立監査ゲート）に置き、アプリが越境していないかを客観的に監視させる。

### ⑤ コンテナ起動スクリプトのクリーンアップ保証 (Lifecycle Teardown Pair)
- **アンチパターン**:
  - `scripts/health-check.sh` などで `docker run ...` をバックグラウンド起動し、テスト後に `docker stop` する記述のみ。
- **問題点**: スクリプト途中でテストが失敗したりシグナルを受信した際に `docker stop` が呼ばれず、ゾンビコンテナがホストに残留・ポート衝突を引き起こす。
- **再発防止策**:
  - スクリプト冒頭で必ず **`trap 'docker stop ... && docker rm ...' EXIT INT TERM`** を宣言し、異常終了時も含めた確実なクリーンアップを義務化する。
  - ワンショット検証には必ず `--rm` を付与する。

### ⑥ YAML 文字列のクォート義務化とパースエラー即時可視化 (Strict YAML Quoting)
- **アンチパターン**:
  - `acceptance_criteria` や `verify_command` にコロンを含む文字列（`width: 250px`, `Content-Type: image/png`）を裸で記述。
- **問題点**: YAML パーサーがマッピング（Key-Value）と誤認して構文エラーとなり、パーサーが握りつぶすとゾンビタスク化する。
- **再発防止策**:
  - すべての文字列プロパティ（`title`, `acceptance_criteria`, `verify_command`）をダブルクォート（`"..."`）で囲む。
  - パーサー側で `try-except pass` による隠蔽を完全撤廃し、構文エラーは即座に `RuntimeError` でフェイルファスト化する。

### ⑦ ドメインモデル純粋性検査の意味論的アサーション (Semantic Assertion)
- **アンチパターン**:
  - `find internal/domain/model/ -name '*.go' | wc -l | grep -q '^4$'`
- **問題点**: 実際のモデルファイル数が 3 つだった場合、ファイル数カウントの不一致で永久に不合格になる（脆弱なテスト）。
- **再発防止策**:
  - ファイル数ではなく、本来検証すべき「モデル純粋性（ロジックや関数の混入がないこと）」を意味論的に直接検証する：
    `! grep -rn 'func\|return' internal/domain/model/ && echo OK`

---

## 2. 🚀 今後実装予定の機能・アーキテクチャロードマップ (Future Architecture Roadmap)

### 🧩 1. 用途別・階層別（Tiered）LLMモデルルーティング機能の本格体系化
- タスク種別（大局監査、要約、コード生成、テスト生成）や入力トークン長に応じて動的かつ宣言的にモデル・プロバイダーをルーティングできる設定駆動アーキテクチャへ昇格させる。

### ⚡ 2. 4重監査 & 異種LLMパイプライン並列実行エンジン化 (Parallel & Pipelined Execution)
- **Gemini仕様抽出の先行並列化（Prefetching / Fan-out）**: 全エピックの `epic_specification.yaml` を `asyncio.gather` で一括並列抽出し、待ち時間を圧縮。
- **異種リソース Producer-Consumer パイプライン**:
  - *Producer (Cloud Gemini)*: 仕様抽出を先行してキューへ供給。
  - *Consumer (Local LLM)*: キューから順次取得してディベート・バックログ生成。
  - *Async Auditor (Cloud Gemini)*: 生成完了したバックログに対してバックグラウンドで 4重独立監査（Spec, Security, DevOps, Ruler）を Fan-out 並行実行。

### 💡 3. Scrum パッケージ＆プラグイン構造化構想 (Spaghetti Prevention)
- スクラム関連資産を `packages/scrum/` 配下（`rules/`, `personas/`, `prompts/`, `engine/`）へ自己完結型として集約し、保守性と拡張性を最大化する。

---

## 3. 🏃 次回作業再開時の手順

スプリント精緻化（Ceremony 2）はすでに全 7 エピック合格済みで完全に完了しています。
次回作業を再開する際は、以下のコマンドを実行するだけで、直ちに **Ceremony 3（Downstream Coder による自律TDD開発ループ：Epic 1 Sprint 1〜）** からスタートします：

```bash
PYTHONPATH=. python3 runner/main.py run --phase all
```

- **Ceremony 3 実行内容**:
  - 各エピックのスプリント（TASK）ごとに、テスト作成 ➔ 実装 ➔ `verify_command` によるコンテナ内テスト実行 ➔ Red/Green 判定 ➔ DoD 判定が自律的に実行されます。

---

## 4. システム状態ダッシュボード (State Dashboard)
- 最新の実行状態やスプリント進捗は `state/status.md` にリアルタイム自動更新されます。
- 全体監査レポート（Loop #5）は `state/.evaluator/loop_5/` に完全に保存されています。

---

## 5. 🐧 Linux 環境移行に伴うローカル LLM (llama.cpp / llama-server) 運用引き継ぎ

### ① 移行の背景と目的
- **課題**: Windows ホスト側での `run_llama.ps1` 実行時、グラフィックドライバタイムアウト（BSoD: `0x00000116` `VIDEO_TDR_FAILURE`）や管理者権限昇格、Windows-WSL2 間のポート中継の不安定性が発生。
- **方針**: 以降のローカル LLM 実行基盤を Linux (WSL2 Ubuntu 24.04) ネイティブ環境に移行・集約し、プロセス管理と通信を同一 Linux OS 内で完結させて安定性とレスポンスを担保する。

---

### ② Windows vs Linux 環境差分対照表

| 項目 | Windows 環境 (旧) | Linux 環境 (新: WSL2 / Ubuntu 24.04) | 備考・注意点 |
| :--- | :--- | :--- | :--- |
| **起動スクリプト** | `run_llama.ps1` (PowerShell) | `scripts/run_llama.sh` (Bash) | バックグラウンド起動・プロセス管理を Bash で完結 |
| **実行バイナリ** | `C:\llama\llama-server.exe` | `llama-server` (ビルドまたはバイナリ) | `~/llama.cpp/build/bin/llama-server` 等に配置 |
| **モデル配置場所** | `C:\llama\models\` | `/mnt/c/llama/models/` | 既存モデル（Devstral 24B, Qwen2.5 32B）を直接参照可能 |
| **モデルファイル名** | `mistralai_Devstral-Small-2-24B-Instruct-2512-Q4_K_M.gguf` | 同左 (14.3 GB) | `config.env` の `EXECUTOR_MODEL` と一致 |
| **バックエンド / GPU** | Vulkan (`-dev Vulkan0,Vulkan1`) | CUDA (`GGML_CUDA=on`) または CPU | WSL2 CUDA 利用時は `/usr/lib/wsl/lib` 参照 |
| **待受ポート** | `11435` | `11435` | 変更なし (Linux 内 `127.0.0.1:11435`) |
| **コンテキスト長** | `-c 32768` | `-c 32768` | 最大 32k トークン |
| **最大出力トークン** | `8192` | `8192` | `config.env` の `LLAMA_MAX_TOKENS` |
| **並列処理数** | `-np 1` | `-np 1` | VRAM 枯渇防止のため 1 に固定 |

---

### ③ Linux 側での llama-server 起動スクリプト (`scripts/run_llama.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail

MODEL_DIR="/mnt/c/llama/models"
MODEL_NAME="${1:-mistralai_Devstral-Small-2-24B-Instruct-2512-Q4_K_M.gguf}"
MODEL_PATH="${MODEL_DIR}/${MODEL_NAME}"
PORT=11435

if [ ! -f "${MODEL_PATH}" ]; then
  echo "❌ Error: Model not found at ${MODEL_PATH}" >&2
  exit 1
fi

echo "🚀 Starting llama-server on Linux (Port: ${PORT}, Model: ${MODEL_NAME})..."

# WSL2 の CUDA ドライバライブラリパス
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}"

exec llama-server \
  -m "${MODEL_PATH}" \
  --port "${PORT}" \
  -c 32768 \
  -np 1 \
  -ngl 99 \
  --host 127.0.0.1
```

---

### ④ アプリケーション・Runner 側の設定影響 (`config.env`)
- `config.env` 内の下記設定は、Linux ネイティブ起動（`127.0.0.1:11435`）でも**設定変更なしでそのまま動作**します：
  ```ini
  EXECUTOR_PROVIDER="llama_cpp"
  EXECUTOR_MODEL="mistralai_Devstral-Small-2-24B-Instruct-2512-Q4_K_M.gguf"
  LOCAL_LLM_URL="http://127.0.0.1:11435/completion"
  LOCAL_LLM_ENDPOINT="http://127.0.0.1:11435/v1/chat/completions"
  LOCAL_LLM_COMPLETION_ENDPOINT="http://127.0.0.1:11435/completion"
  EXECUTOR_ENDPOINT="http://127.0.0.1:11435/v1/chat/completions"
  LLAMA_MAX_TOKENS=8192
  ```

---

### ⑤ 起動確認・ヘルスチェック手順
1. **サーバーヘルスチェック**:
   ```bash
   curl -s http://127.0.0.1:11435/health
   ```
2. **疎通・コード生成テスト**:
   ```bash
   python3 scripts/test-local-llm.py "Write a hello world in Go"
   ```

