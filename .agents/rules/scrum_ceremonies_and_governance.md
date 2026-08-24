# ⚙️ Scrum Ceremonies & Governance Rules

## 1. 🎯 AI自律スクラムセレモニー体系 (Ceremony Lifecycle)
本パイプラインは以下の 3 つのセレモニー（フェーズ）で構成される：

1. **エピックリファインメント (Epic Refinement)**:
   - 全体要求仕様書（System Specification）を読み解き、全体アーキテクチャディベートおよび単一責任エピック（`epic_1`〜`epic_N`）の抽出・分類を行う。
2. **スプリントバックログリファインメント (Sprint Backlog Refinement)**:
   - 各エピックごとにマルチペルソナディベートを行い、詳細タスク定義（`sprint_x_backlog.yaml`）および自動テストハーネス（`sprint_x_harness.sh`）を自動生成する。
3. **スプリント開発 & 受入判定 (Sprint Execution & Review Gate)**:
   - 自律TDD実装（Red ➔ Green）を行い、テストハーネスおよび完成の定義（DoD）を満たしているかを検証する。

## 2. 🚥 DoR (Definition of Ready: 開発着手準備完了の定義)
スプリント開発（TDD実装）に着手・進入するための必須条件：

1. **受入要件の厳格制限 (Acceptance Criteria <= 2)**:
   - 各タスクの受入基準（`acceptance_criteria`）は **2 個以下** であり、単一責任に限定されていること。（3 個以上の場合はリファインメント段階で即座に複数の小タスクへ分解する）。
   - **非機能要件の除外**: パフォーマンス、セキュリティ、コスト等の非機能要件（NFR）は DoR に含めず、開発後の DoD（完成の定義）で検証する。
2. **明確な物理ファイルパスの指定**:
   - タスクに作成・変更対象の物理ファイルパスが明記されていること。
3. **自動検証テストハーネスの存在**:
   - タスク動作を客観テストする `sprint_x_harness.sh` が生成されていること。

## 3. 🚫 スプリントレビューにおけるアドホックな設計変更禁止ルール (CRITICAL)
- **全体一貫性の保護 (System Architecture Consistency Guarantee)**:
  - スプリント開発・レビュー段階において、リファインメントフェーズで合意・決定されたアーキテクチャ、API契約、データ構造の**アドホック（場当たり的）な設計変更・仕様追加は厳重に禁止**する。
  - スプリントレビューの責務は、「リファインメントで定義されたDoD（テストハーネス100%Pass、Clean Architecture 4層構造、セキュリティ・倫理基準）を満たしているかのPass/Fail判定」のみとする。
- **一貫性破綻時のリファインメント・ロールバック規定**:
  - 万が一、開発途中で重大な仕様矛盾や設計上の不整合が発覚した場合は、コード上で捏造修正してはならない。即座に「リファインメントフェーズへのロールバック」を宣言し、全体一貫性を保った状態でディベートからやり直すこと。

## 4. 📂 セレモニー別規定成果物ファイル構造 (Standard Artifact Map)
各セレモニーが出力・維持すべき正規の成果物ファイルパス：

- **セレモニー 1 (エピックリファインメント)**:
  - `state/.evaluator/overall_debate_log.md` (全体アーキテクチャディベート & エピック一覧)
- **セレモニー 2 (スプリントバックログリファインメント)**:
  - `state/initiatives/epic_X/debate_log.md` (エピック詳細ディベート)
  - `state/initiatives/epic_X/epic_backlog.yaml` (エピック全体バックログ)
  - `state/initiatives/epic_X/sprint_N_backlog.yaml` (DoR適合スプリントタスク定義)
  - `state/initiatives/epic_X/sprint_N_harness.sh` (自動検証テストハーネス)
- **セレモニー 3 (スプリント開発 & 受入判定)**:
  - `workspace/<project_name>/...` (自動実装ソースコード & 単体テスト)
  - `state/initiatives/epic_X/sprint_N_review_gate.md` (DoD受入判定ログ)
