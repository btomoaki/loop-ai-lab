# 新規機能開発ポリシー (Feature Development Policy)

本ドキュメントは、新規機能追加および新規アプリケーション設計における開発規約・ガイドラインを定義します。

## 1. アーキテクチャ設計・思想 (Architecture Pattern)
- **DDD (Domain-Driven Development) / クリーンアーキテクチャの適用**:
  - ビジネスロジックを技術的関心事（DB, Web API, 外部接続等）から完全に分離すること。
  - レイヤー構造: `Domain` (データ・ビジネスルール) ➜ `UseCase` (アプリケーションロジック) ➜ `Infrastructure` (DB・API実装) ➜ `Interface / Controller` (HTTP・CLI表現層)。
- **抽象度優先の実装順序 (Abstraction First)**:
  - 具体クラスの実装よりも前に、必ず **インターフェース（抽象クラス / interface / protocol）** を定義・設計すること。
  - 上位レイヤー（Domain/UseCase）は下位レイヤー（Infrastructure）の具体に直接依存せず、抽象に依存すること (DIP: 依存性逆転の原則)。

## 2. 実装・コーディング規約 (Coding Standards)
- **単体テスト併行作成**:
  - 新機能の作成時には、対応する単体テスト（Unit Test）を必ずセットで作成すること。
- **設定値の外部化**:
  - ハードコードを禁止し、環境変数 (`.env`) や設定ファイル経由で注入可能にすること。
- **README.md の当たり前の自動同梱**:
  - アプリケーションコードを作成する際は、必ずビルド手順、ローカル動作確認方法、主要環境変数一覧を記載した `README.md` をプロジェクト直下に自動生成・更新すること。

## Go プロジェクト実装時の厳格ルール (Go Module Rules)
- **`go.mod` と `import` パスの完全一致**:
  - `go.mod` で定義したモジュール名 (例: `module avatar-service`) を、すべてのサブパッケージの `import` パスのプレフィックスとして厳格に使用すること。
  - 例: `go.mod` が `module avatar-service` の場合、内部インポートは `import "avatar-service/internal/domain"` とすること（`github.com/...` や存在しない外部ドメインの混在を厳禁とする）。
- **標準ライブラリのみ（ゼロ依存）原則**:
  - 仕様で「外部依存なし / 標準機能のみ」と指示されている場合、サードパーティ製パッケージのインポートを行わず `image`, `crypto/md5`, `net/http` 等の標準パッケージのみで完結させること。

- **Go embed ディレクティブ原則 (Embed Asset Rule)**:
  - `//go:embed` を含むコードを出力する場合、参照先の静的ファイル（例: `static/index.html` や `static/css/style.css`）を同一ステップ内で必ず同時に生成すること（未存在参照によるコンパイルエラーの防止）。
- **単体テストコードの厳格性**:
  - テストコードを追加する際は、テスト対象の構造体のフィールドの公開・非公開（大文字/小文字）および型を厳密に一致させること。
