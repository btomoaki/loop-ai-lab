# 📝 プロジェクト次回引き継ぎメモ (Handover Notes)

## 1. 次回再開時のクイックスタート (Quick Start for Next Session)

### 🏃 自律 TDD 開発フェーズ (Sprint Development) の継続実行
- **状況**: `state/status.md` ダッシュボードおよび `sprint_N_done.yaml` 出力機能が完成済み。
- **実行コマンド**: `PYTHONPATH=. python3 runner/main.py run --phase sprint`

---

## 2. 本日完了した主要成果 (Completed Milestones Today)
- **プロンプト長 40% スリム化**: フォルダ単位参照 (`- .agents/personas/` 等) による軽量化。
- **セレモニー別エンジン分割**: `EpicRefinementEngine`, `SprintRefinementEngine`, `SprintExecutionEngine` へ構造分離。
- **エージェントフォルダ隔離**: `agents/` ディレクトリを 3 セレモニーサブフォルダに完全分類。
- **リアルタイムダッシュボード (`state/status.md`)**: 実行中のエピック/タスク/TDD試行回数を可視化。
- **完了実績ログ (`sprint_N_done.yaml`)**: ハーネス合格時に作成ファイルと完了タスクを自動記録。
- **2大物理コスト規定 (FinOps)**: `Physical Compute & Energy Cost Efficiency` ＆ `Time-to-Market Optimization` の配備。

---

## 3. 将来的ロードマップ (Future Architecture Roadmap)

### 💡 Scrum パッケージ＆プラグイン構造化構想 (Spaghetti Prevention)
- **改修構想**: 将来的にスクラム関連ファイル（`.agents/`, `agents/`, `runner/engine/`）を `packages/scrum/` パッケージへ一元統合する設計改善。
