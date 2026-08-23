# 📝 プロジェクト残課題・引き継ぎメモ

## 1. 次回着手する残課題 (Next Tasks)

### ① スプリント自動開発ループ (Development Phase) の完走
- **目標**: `state/initiatives/` 内の全エピックにおける `sprint_1_backlog.yaml` を読み込み、LLM 開発エージェントによる `workspace/identicon-generator/` 下への Go ソースコード自動生成と、`sprint_1_harness.sh` によるテスト自動検証（Red ➔ Green）ループを実行・完遂する。
- **実行コマンド**: `PYTHONPATH=. python3 runner/main.py run --phase sprint`

### ② 生成された Go アプリケーションの動作検証
- **目標**: 決定論的 PNG アバター生成（250px × 250px）、OpenAPI 仕様 (`docs/openapi.yaml`)、および Graceful Shutdown (`syscall.SIGTERM`/`SIGINT`) の動作が Go テスト (`go test ./...`) およびコンテナビルドで全てパスすることを確認する。

---

## 2. 次回再開用クイックスタートコマンド
```bash
# 既存のリファインメント成果物およびバックログの確認
ls -la state/initiatives/

# スプリント実装フェーズ（自動TDD開発ループ）の再開
PYTHONPATH=. python3 runner/main.py run --phase sprint
```
