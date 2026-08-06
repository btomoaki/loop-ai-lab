# インフラ・ミドルウェア構築ポリシー (Infrastructure & Middleware Policy)

本ドキュメントは、インフラコード (Docker / Kubernetes / Helm / Terraform / Cloud Run 等) やミドルウェアの選定規約を定義します。

## 1. ミドルウェア・コンテナ選定基準 (Selection Criteria)
- **ローカルプルスルーキャッシュ (local-setup) の優先利用**:
  - Docker Hub や GHCR からイメージを pull/build する際は、`local-setup` が提供するローカルプロキシキャッシュ (`registry.localhost` または `ghcr.localhost`) を優先利用すること。
- **安定版 (LTS / Stable) の優先**:
  - ベースイメージやパッケージは、開発中の最新版ではなく公式推奨の長期サポート版 (LTS) または Stable タグを採用すること。
- **公式・Bitnami レジストリ優先**:
  - オープンソースミドルウェア（PostgreSQL, Redis, RabbitMQ 等）を採用する際は、公式または Bitnami などの検証済みリポジトリを最優先利用すること。
- **ドキュメント・エコシステム重視**:
  - サポートコミュニティが広く、標準ドキュメントが豊富な構成を採用すること。

## 2. 構成原則 (Infrastructure Principles)
- **環境差異の排除**:
  - ローカル環境とクラウドデプロイ環境の構成差分を極力無くし、環境変数経由でスイッチ可能にすること。
- **ネットワーク境界の隔離**:
  - 外部公開が不要なミドルウェア・データベースは外部ポートバインドを避け、内部ネットワーク (`local-common-net` や K8s ClusterIP) に閉じ込めること。
