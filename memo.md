# 📝 プロジェクト次回引き継ぎメモ (Handover Notes)

## 0. 📌 直近の達成状況 & 次回再開手順 (2026-09-05 最終更新)

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
