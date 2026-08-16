# インフラ・IaC セットアップ ポリシー (Infrastructure Setup Policy)

## 1. 原則 (Principles)
- **宣言的インフラ (Declarative Infrastructure)**: 手動変更を禁止し、すべて Dockerfile, Compose, Helm Chart, Terraform 等のコードで管理すること。
- **再現性とクリーンネス**: ローカル環境依存を排除し、誰の環境でも同一の `make test` や `helm template` で検証可能とすること。

## 2. ローカル検証インフラ (local-setup) 連携ルール
- **ネットワーク & プロキシ標準**:
  - Web アプリケーションや API をデプロイする場合は、ホスト直付けのポートマッピング（例: `-p 80:80`）を避け、可能な限り `local-setup` プロキシ（`http://localhost` または *.localhost）経由でルーティング可能に構成すること。
  - Kubernetes / Helm チャートの場合は `Ingress` または `NodePort` を標準で含めること。
- **コンテナレジストリ**:
  - カスタムイメージをビルド・使用する場合は `registry.localhost` (ローカルレジストリ) を優先的に利用すること。

## 3. 実装・ドキュメント作成の責務分離ルール (Separation of Concerns)
- **ローカル Executor の責務 (Code Only)**:
  - 1ステップでのコード生成は機能コード（`Chart.yaml`, `values.yaml`, `templates/*.yaml` 等）の実装・修正に専念すること。
  - `README.md` の作成・編集を一度のステップで同時に行う必要はない。
- **Evaluator / System の責務 (Documentation & Delivery)**:
  - ハーネス検証（`helm lint`, `helm template` 等）が合格 (Green) した後、システムが自動的に Evaluator (Claude) を呼び出し、最新のコードベースに基づく親切な `README.md` を最終生成・コミットする。

## 4. 実装ステップ分割ルール (Step Execution Rules)
- **1ステップあたりの出力ファイル数は最大3ファイルまで**:
  - 一度の実装ステップで生成・更新するファイルは最大3つに限定すること。
  - ファイル数が多い場合は、複数ステップに分割して実装すること。
- **優先順位**:
  1. まず `Chart.yaml` + `values.yaml` を作成・修正する
  2. 次に `templates/` 配下のマニフェストを作成・修正する
