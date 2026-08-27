## 🎯 直近の最優先フォーカス（セレモニー 1 エピックリファインメント）
- **目標**: 仕様書（`references/`）を確実に読める状態のまま、コンテキスト溢れ（出力トークン枯渇・無限ループ）を起こさず、エピック分解とエピックプランニング（ディベート）を安定実行できるようにプロンプト・出力密度を調整する。
- **検証済み知見**:
  - パス指定による指示ファイル読み込みと、プロンプト末尾の出力開始テンプレート（べた書きアンカー）による強力な出力制御が有効。
  - 2段階分割よりも、昨日の1段階ベースライン（49ea835）を出発点として、出力サイズ（トークン消費）の調整・簡潔化を行うアプローチが最適。

# 📝 プロジェクト次回引き継ぎメモ (Handover Notes)

## 1. 次回再開時のクイックスタート (Quick Start for Next Session)

### 🏃 次回再開時のクリーンスタート手順 (Ceremony 2 スプリントリファインメント直行)
- **事前お掃除状態**: 🧹 生成物 (`sprint_x_backlog.yaml`, `sprint_x_harness.sh`, `workspace/identicon-generator`) のクリーンアップは完了済みです。
- **1. スプリントリファインメント実行コマンド**:
  - `PYTHONPATH=. python3 runner/main.py run --phase refinement`
- **2. 自律TDD開発実行コマンド**:
  - `PYTHONPATH=. python3 runner/main.py run --phase sprint --sprint 1`



---

## 2. 本日完了した主要成果 (Completed Milestones Today)
- **セレモニー1 人間レビューゲート (`--phase epic`)**: エピック抽出完了時にサマリーを出力して一時停止する安全ゲートの実装と検証。
- **プロンプト＆ルールの完全汎用化・汎用構造**: `agents/` 内のプロンプトから特定アプリ名・特定言語ルール・重複ペルソナを除去し、Single Source of Truth (`.agents/rules/`) へ一元化。
- **`[FinOps Cost Auditor Persona]` の配備**: セレモニー 1 & 2 に配備し、仕様外の余剰構築（CLI構築等）やオーバーエンジニアリングを排除。
- **`[Capacity Guardian Persona]` 8pt基準軸アジリティ調整**: 8 Story Points を基準軸とする動的分解ガバナンスルールの決定・明文化。
- **`runner/` エンジン＆ハーネスの言語非依存化**: `go.mod` 等の直書きを排し、`config.yaml` の `init_commands` と `format_cmd` から動的実行する汎用スクラムエンジンへのリファクタリング。

---

## 3. 将来的ロードマップ (Future Architecture Roadmap)

### 🚀 GitHub Actions CI/CD パイプライン標準化
- **構想**: 検証ハーネス実行や自動デプロイを `.github/workflows/` を基本インフラとして活用・標準化する。

### ⚡ エピック／スプリントの並列実行エンジン化 (Parallel Execution)
- **構想**: `ThreadPoolExecutor` や asyncio を導入し、独立したエピックのリファインメントおよび TDD 開発ループを並列実行・高速化する。

### 💡 Scrum パッケージ＆プラグイン構造化構想 (Spaghetti Prevention)
- **構想**: スクラム関連ファイル（`.agents/`, `agents/`, `runner/engine/`）を `packages/scrum/` パッケージへ一元統合・モジュール化する。

