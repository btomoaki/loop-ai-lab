# 📝 プロジェクト次回引き継ぎメモ (Handover Notes)

## 0. 📌 直近の達成状況 & 次回再開手順 (2026-09-04 最終更新)

### 🏆 本日の達成状況 & Epic 1〜4 完走

1. **Epic 1〜4 の精緻化 & 3重監査（Audit）の全件 APPROVED 獲得**:
   - **Epic 1 (開発基盤 & コンテナ化シフトレフト)**: Attempt 1 で一発 **APPROVED**。7層ディレクトリとポート `8080:8080`、コンテナワンショット検証を完全クリア。
   - **Epic 2 (ドメインコアモデル & 幾何学アルゴリズム)**: Attempt 2 で **APPROVED**。モデル純粋性とアルゴリズム単体テストをクリア。
   - **Epic 3 (インフラ PNG レンダラー & ラスター化)**: Attempt 2 で **APPROVED**。ピクセル描画と画像出力の分離をクリア。
   - **Epic 4 (ユースケース & DI配線)**: Attempt 3 で **APPROVED**。`AC <= 2` 上限遵守、非標準 `internal/di/` ディレクトリ排除、標準レイヤー内での依存性注入配線をクリア。

2. **全プロンプトの完全英語化（ASCII統一）& 絵文字・全角文字の完全排除**:
   - `assets/*.tpl` 配下のすべてのテンプレート、および `sprint_execution_engine.py`（Ceremony 3 コード生成）、`sprint_refinement_engine.py`（監査プロンプト）から絵文字（`🌐`, `📋`, `🔨`, `🚫`, `🎯`, `🚨`, `🕵️`, `🛡️` など）および全角墨付き括弧（`【】`）を完全撤廃し、純粋な ASCII 英語テキストに統一。
   - ペルソナ定義内の日本語表記（`[Ruler Persona (ルーラー / 規律・ポリシー統制官)]`）を `[Ruler Persona (Discipline & Policy Controller)]` に英訳統一。トークン消費とトークナイザーのバイト分割ノイズを解消。

3. **直前の VETO に対する全層根本是正（ホストパイプ禁止 & 受入条件具体化義務化）**:
   - **Zero Host Piping & Chaining Policy**: `verify_command` でのホストパイプ（`| grep`）、リダイレクト、`&&` によるコマンド連鎖を全ルール・プランナー・テンプレートで厳格に禁止。ワンショット（`docker compose run --rm <service> ...`）単一コマンドに一元化。
   - **No Ambiguity & Explicit Enumeration Mandate**: 受入条件（AC）における `"etc."` 省略を禁止し、Clean Architecture 7層ディレクトリおよび Compose 仕様（ポート `8080:8080`、ベースイメージ、ボリュームマウント、作業ディレクトリ）の完全列挙を義務化。

4. **テンプレート外部化（`assets/` 配下）& プロンプトキャッシュ最適化（Cache-First Sequence）の確立**:
   - `assets/first_phrase.tpl` を新設し、`LLMAdapter` 基底クラスにおいて全 LLM 呼び出し時に `[INST]` 特殊タグ直後へ自動注入（Prefix Injection）する共通機構を実装。
   - `assets/ceremony_2_backlog.tpl` を「静的 DoR / ホストパイプ禁止ルール ➔ エピック仕様 ➔ リトライフィードバック ➔ YAML生成タスク」の厳格な **Cache-First 順序** に再編成。KV キャッシュヒット率を最大化。

5. **スマート・レジューム機能の運用確立**:
   - `state/initiatives` を保持しているため、合格済みの Epic 1〜4（APPROVED 獲得済み）は自動で瞬時にスキップされ、次回は未完了の **Epic 5** からピンポイントで即座に再開されます。

---

## 1. 🚀 今後実装予定の機能・アーキテクチャロードマップ (Future Architecture Roadmap)

過去の議論および本日洗い出された、**今後優先的に実装・改善していくべき重要構想リスト** です。新チャットへ確実に引き継ぎます：

### 🧩 1. 用途別・階層別（Tiered）LLMモデルルーティング機能の本格体系化
- **現状**: 現在はエンジンコード（`sprint_refinement_engine.py` 等）内にハードコードに近い形で「仕様抽出・監査＝Cloud Gemini」「ディベート・YAML生成・コード生成＝Local LLM」と振り分けられている。
- **構想・改善**: `config.yaml` やモデルプロファイル定義に基づき、タスク種別（大局監査、要約、コード生成、テスト生成）や入力トークン長に応じて動的かつ宣言的にモデル・プロバイダーをルーティングできる設定駆動アーキテクチャへ昇格させる。

### ⚡ 2. 3重監査 & 独立エピックの並列実行エンジン化 (Parallel Execution)
- **現状**: 各エピックおよび監査官の審査はシングルスレッド（直列）で順番に処理されている。
- **構想・改善**:
  - **監査の Fan-out / Fan-in 並列化**: 独立している 3 監査官（Spec Compliance, Security, Ruler）の `agy CLI` 呼び出しを `asyncio` / スレッドで同時に並行実行し、エピック毎の監査待ち時間を約 1/3 に短縮する。
  - **依存関係のないエピックの並列ディベート**: DAG 上で独立したエピックのリファインメントを並行処理する。

### ⚠️ 3. `cmd/server/main.go` 過剰束縛の是正（`cmd/<app名>/main.go` への柔軟化）
- **現状の課題**: ルール（`developer_standards.md`）やテンプレート（`ceremony_2_backlog.tpl`）のディレクトリ骨格指示に `cmd/server/` と固定ハードコードされているため、CLIツールやワーカー等もすべて `server` コマンドに強制されてしまう（Rule Rot 懸念）。
- **改善方針**: Go の標準プラクティスである **`cmd/<app名>/main.go`**（本プロジェクトであれば `cmd/avatar-service/main.go` や実行バイナリ名に即したディレクトリ）が選択できるよう、ルールとプロンプトテンプレートを一般化する。

### 💡 4. Scrum パッケージ＆プラグイン構造化構想 (Spaghetti Prevention)
- **現状の課題**: スクラム関連ファイルが `.agents/` (ルール/ペルソナ), `agents/` (プロンプト), `runner/engine/` (Pythonコード) と複数ディレクトリに散乱しており、スパゲッティ化の懸念がある。
- **改善構想**: これらを `packages/scrum/` という単一パッケージ内に自己完結型としてパッケージング統合する。
  - `packages/scrum/rules/`
  - `packages/scrum/personas/`
  - `packages/scrum/prompts/`
  - `packages/scrum/engine/`
- **効果**: `main.py` からの依存関係・呼び出し制御が極めてスマートになり、将来的に「小説執筆パッケージ」等への切り替えも容易になる。

### 🚀 5. GitHub Actions CI/CD パイプライン標準化
- **構想**: テストハーネス実行や自動デプロイをローカルシェル依存から `.github/workflows/` を基本インフラとして活用・標準化する。

---

## 2. 🏃 明日（新チャット）再開時の手順

次回作業を再開する際は、以下のコマンドを実行するだけで自動的にパイプラインが進行します（Epic 1〜4 はスマートレジュームで瞬時にスキップされ、**Epic 5** のスプリント精緻化から始まります）：

```bash
PYTHONPATH=. python3 runner/main.py run --phase all
```

- **残エピック**:
  - **Epic 5**: HTTP 配信 API、レートリミッター & OpenAPI 仕様
  - **Epic 6**: プロダクション Docker パッケージング & GCP Cloud Run 配信基盤
  - **Epic 7**: SPA Web フロントエンド & アセットプレビュー
- **Ceremony 3（自律 TDD 開発ループ）**:
  - 全エピックの精緻化と監査が完了次第、**Downstream Coder による自律TDD実装・Red/Green/DoD ゲート** へ突入します。

---

## 3. システム状態ダッシュボード (State Dashboard)
- 現在の実行状態やスプリント進捗は `state/status.md` にリアルタイム自動更新されます。
- 各エピックのスプリント成果物は `state/initiatives/<epic_dir_name>/` に集約されています。
