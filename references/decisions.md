# Architecture Decisions (ADR)

## Decision #1: Simplicity First (固定パラメータ & 単一責務)
- **Status**: ACCEPTED
- **Context**: ユーザー入力や動的カスタマイズによる複雑化を防ぎ、決定論的かつ軽量なアバター生成を実現する。
- **Decision**: 
  - アイコンのサイズは `250px × 250px`、背景色は固定値 `RGBA{240, 242, 245, 255}` とする。
  - 動的なサイズ変更スライダーやカラーピッカー、不要なバリデーションAPIは作成しない。

## Decision #2: Output Format (PNG Only - SVG 全面禁止)
- **Status**: ACCEPTED
- **Context**: Go 標準ライブラリ（`image`, `image/png`, `image/color`）のみで完結させ、外部依存や巨大なカスタムベクター描画ロジックの自作によるハルシネーション・破綻を完全に排除する。
- **Decision**: 
  - 出力フォーマットは **`image/png` のみ** とする。
  - **SVG フォーマットの出力、SVG レンダラー、XML ベクター生成ロジックは一切実装しない（全面禁止）**。

## Decision #3: Modern Go Ecosystem & Pragmatic Dependencies (Avoid Reinventing the Wheel)
- **Status**: ACCEPTED
- **Context**: 下流の Coder モデルのトークン予算（8,192 tokens）を守りつつ、車輪の再発明を避けて信頼性と開発生産性を最大化する。
- **Decision**:
  - 標準ライブラリを基礎としつつ、Goエコシステムにおいて広く普及し、よくメンテナンスされているポピュラーなサードパーティライブラリ（HTTPルーティング、テストアサーション、構造化ログ、画像処理等）の積極的な活用を推奨・許可する。
  - 重量級のモノリシックフレームワークや不要な複雑性は避け、軽量・ステートレスで標準的なパッケージを選択する。
  - Web UI は Go 1.16+ `embed` パッケージによる単一バイナリ同梱型（HTML5 + Tailwind CSS CDN + Vanilla JS）とする。

## Decision #4: Clean Architecture Interface Injection
- **Status**: ACCEPTED
- **Context**: テスト容易性と疎結合性を担保する。
- **Decision**:
  - レンダリングロジックやハンドラー境界には Go インターフェース注入を採用し、100% 単体テストでモック可能とする。

## Decision #5: Cloud-Native Graceful Shutdown & Container Hardening
- **Status**: ACCEPTED
- **Context**: GCP Cloud Run 上での安全なゼロダウンタイム運用とコンテナセキュリティを確保する。
- **Decision**:
  - `signal.Notify` と `http.Server.Shutdown` による SIGTERM/SIGINT ハンドリング（10秒タイムアウト）を実装する。
  - Dockerfile はマルチステージビルドを採用し、実行ユーザーは非 root（UID `65532`）に固定する。

## Decision #6: OpenAPI 3.0 Contract Specification
- **Status**: ACCEPTED
- **Context**: API の仕様契約を明確化する。
- **Decision**:
  - `docs/openapi.yaml` に OpenAPI 3.0 形式で API 仕様を完全定義する。
