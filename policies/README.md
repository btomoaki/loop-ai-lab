# ポリシー・開発規約置き場 (Policies Directory)

本ディレクトリは、タスク種別 (`TASK_TYPE`) や設計思想に応じた開発規約・アーキテクチャルール・ベストプラクティス (Well-Architected) を格納する場所です。

## ポリシーファイルの例
- `policies/bugfix.md`: バグ修正タスク用ルール (再現テスト作成、最小限のコード修正)
- `policies/feature_dev.md`: 新規機能開発用ルール (DDD、抽象定義優先、レイヤー分離)
- `policies/observability.md`: 監視・運用用ルール (アラート追加時はダッシュボードもセットで作成)
- `policies/infra_setup.md`: インフラ構築用ルール (LTS優先、公式ドキュメント準拠)

## AI エージェントの挙動
- `config.env` の `TASK_TYPE` や要件定義に応じて、AI エージェントは本ディレクトリ内の該当ポリシーを選択的に読み込み、規約に従ってタスク評価・実装を行います。
