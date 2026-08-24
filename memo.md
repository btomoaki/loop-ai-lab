# 📝 プロジェクト次回引き継ぎメモ (Handover Notes)

## 1. 次回再開時のクイックスタート (Quick Start for Next Session)

### 🏃 自律 TDD 開発フェーズ (Sprint Development) の継続実行
- **状況**: `state/status.md` リアルタイムダッシュボードおよび `sprint_N_result.yaml` 監査ログ保存機能が完成済み。
- **新ペルソナ配備**: `[Capacity Guardian Persona]`（無理をするなペルソナ）がセレモニー1＆2に常駐し、タスクを極小サイズに分割。
- **実行コマンド**: `PYTHONPATH=. python3 runner/main.py run --phase sprint`

---

## 2. 本日完了した主要成果 (Completed Milestones Today)
- **プロンプト長 40% スリム化**: フォルダ単位参照 (`- .agents/personas/` 等) による軽量化。
- **セレモニー別エンジン分割**: `EpicRefinementEngine`, `SprintRefinementEngine`, `SprintExecutionEngine` へ構造分離。
- **エージェントフォルダ隔離**: `agents/` ディレクトリを 3 セレモニーサブフォルダに完全分類。
- **リアルタイムダッシュボード (`state/status.md`)**: 実行中のエピック/タスク/TDD試行回数を可視化。
- **監査ログ (`sprint_N_result.yaml`)**: ハーネス結果 (PASSED/FAILED)、Exit Code、生成ファイル、失敗時の詳細エラーログを自動保存。
- **Fail-Fast 安全停止メカニズム**: ハーネス不合格時に無駄な後続実行を止め、安全停止する機能の検証完了。
- **ファイルパス参照＆動的インジェクション**: プロンプト内のエラーログや指示のファイルパス参照化によるスリム化。
- **`CodeParser` パスガード**: `<relative_path>` 等のプレースホルダー異常パスの自動検知・排除ガード。
- **ローカルLLM自動リトライ**: `0 chars` 空レスポンス時の 3 回自動再試行と 180 秒タイムアウト設定。
- **`[Capacity Guardian Persona]` (無理をするなペルソナ)**: バックログを LLM の出力コンテキスト限界に配慮した極小ユニット（Micro-Sized Backlog）へ強制分割させる新守護者ペルソナの完全組み込み。

---

## 3. 将来的ロードマップ (Future Architecture Roadmap)

### ⚡ エピック／スプリントの並列実行エンジン化 (Parallel Execution)
- **現状**: 各エピックおよびスプリントは現在シングルスレッド（直列）で順番に処理されている。
- **構想**: `ThreadPoolExecutor` や asyncio を導入し、独立したエピックのリファインメントおよび TDD 開発ループを並列並行（マルチスレッド）で同時実行・高速化する。

### 💡 Scrum パッケージ＆プラグイン構造化構想 (Spaghetti Prevention)
- **構想**: スクラム関連ファイル（`.agents/`, `agents/`, `runner/engine/`）を `packages/scrum/` パッケージへ一元統合し、完全モジュール化する。
