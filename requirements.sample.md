# 要件定義書サンプル (Requirements Specification Sample)

本ファイルは `loop-ai-lab` 自律ループに引き渡す要件仕様書のサンプルテンプレートです。

## 1. 目的・目標 (Goal)
- [ ] ターゲットプロジェクトにおける目的や達成すべき成果物を記述します。

## 2. 必須要件 (Requirements)
1. **機能・構成要件**:
   - 実装・構築すべき仕様や形式（ソースコード, Docker Compose, Helm チャート等）を指定。
2. **検証条件 (Acceptance Criteria)**:
   - `VERIFY_COMMAND`（例: `make test` や `docker compose config`）がエラーなく終了すること。
3. **クレデンシャル安全性の維持**:
   - パスワードやAPIキー等の機密情報をコード上に直書きしないこと。
