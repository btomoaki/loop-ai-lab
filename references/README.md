# 参照資料・ドキュメント置き場 (References Directory)

本ディレクトリは、AI自律ループ実行時に参照させる各種ドキュメントや補足資料を雑多に格納するための場所です。

## 格納する資料の例
- 外部 API 仕様書 (OpenAPI / Swagger / Protocol Buffers 等)
- 設計メモ、アーキテクチャ概要ドキュメント
- 参考となるコード断片・データ構造サンプル
- ドメイン知識やガイドラインに関するメモ (`.md`, `.txt`, `.json`, `.yaml` 等)

## AI エージェントの挙動
- `Loop Controller Agent` および `Code Executor Agent` は、要件定義書 (`REQUIREMENT_FILE`) に加え、本 `references/` 配下に配置されたドキュメントを自律的に参照して実装に活用します。
