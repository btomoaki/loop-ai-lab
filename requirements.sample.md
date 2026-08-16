# Helm チャート自動構築・検証要件

`workspace/helm-app` ディレクトリ内に、Nginx Web サービス用の正当な Helm チャートを構築すること。

## 必須成果物
- `Chart.yaml`: チャートのメタデータ定義 (apiVersion: v2, name: helm-app, version: 0.1.0)
- `values.yaml`: イメージ、レプリカ数、ポート等のデフォルト設定値定義 (Bitnami または公式 Nginx イメージ `nginx:alpine` を使用)
- `templates/deployment.yaml`: Deployment 定義
- `templates/service.yaml`: Service 定義

## 合否条件 (Acceptance Criteria)
- `helm lint` および `helm template` コマンドがエラーなく実行できること (Exit Code 0)。
