# 📝 プロジェクト残課題・引き継ぎメモ

## 1. 次回着手する残課題 (Next Tasks)

### ① スプリント自動開発ループ (Development Phase) の完走
- **目標**: `state/initiatives/` 内の全エピックにおける `sprint_1_backlog.yaml` を読み込み、LLM 開発エージェントによる Go ソースコード自動生成と `sprint_1_harness.sh` によるテスト自動検証（Red ➔ Green）ループを実行・完遂する。
- **実行コマンド**: `PYTHONPATH=. python3 runner/main.py run --phase sprint`

### ② 大型ファイル・エージェントプロンプトのセレモニー別分割検討
- **目標**: 影響範囲を見ながら慎重にリファクタリングを進行する。
  - `runner/engine/refinement_engine.py` のセレモニー別分離検討
  - `agents/refinement-planner.md` 等のモノリシックなエージェント定義ファイルを【セレモニー1】【セレモニー2】用に分割整理

---

## 2. 次回再開用クイックスタートコマンド
```bash
# 既存のリファインメント成果物およびバックログの確認
ls -la state/initiatives/

# スプリント実装フェーズ（自動TDD開発ループ）の再開
PYTHONPATH=. python3 runner/main.py run --phase sprint
```
