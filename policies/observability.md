# 監視・運用ポリシー (Observability & Operation Policy)

本ドキュメントは、メトリクス収集・ログ可視化・アラート設定に関する Well-Architected 規約を定義します。

## 1. セット構築原則 (Set Creation Rule)
- **アラート・ダッシュボードのペア作成**:
  - 新しい監視アラート（PrometheusAlert, Cloud Monitoring Alert 等）を定義した場合は、**必ずセットで対応する可視化ダッシュボード（Grafana / Cloud Dashboard）のマニフェストも作成・更新すること**。
  - アラート定義だけを孤立して作成することを禁止する。

## 2. ログ・メトリクス標準 (Standardization)
- **構造化ログ (JSON Log)**:
  - アプリケーションログはプレーンテキストではなく、検索・パースが容易な構造化 JSON 形式で出力すること。
- **標準命名規則**:
  - メトリクス名は `service_component_metric_unit` の標準フォーマットに従うこと。
