# Prompt History

## Step 1: 2026-08-03
- **Prompt:** `First init`
- **Summary:** Initialized project workspace and created initial loop engineering template structure.

## Step 2: 2026-08-05
- **Prompt:** `Add progress management and alignment audit agents`
- **Summary:** Added progress management harness, alignment auditor agent, and periodic review mechanism (REVIEW_INTERVAL) to loop-ai-lab.

## Step 3: 2026-08-05
- **Prompt:** `Implement Python hybrid LLM runner (Local LLM Executor + Gemini Evaluator)`
- **Summary:** Created Python-based orchestration runner (`runner/run_loop.py`) integrating Local LLM for code execution and Gemini API for evaluation and audit.

## Step 4: 2026-08-06
- **Prompt:** `Add evaluation history logging and context injection feature`
- **Summary:** Implemented evaluation log tracking (EVALUATION_LOG.md) and injected recent decision history into AI prompt context to prevent evaluation drift.

## Step 5: 2026-08-06
- **Prompt:** `English conversion of AI agent prompts and structured output parsing in runner`
- **Summary:** Converted all internal AI agent system prompts to strict English for zero ambiguity, and refactored python runner with robust structured JSON/file parsing.

## Step 6: 2026-08-06
- **Prompt:** `Refactor log management and add placeholder path parsing guardrails`
- **Summary:** Refactored log file storage into gitignored logs/ directory, added deliverable reports/ directory for customer artifacts, and filtered placeholder paths in runner.

## Step 7: 2026-08-06
- **Prompt:** `Add documentation standards (README.md) and local dev setup rules to policies`
- **Summary:** Enhanced policies to mandate automatic README.md creation with versioning/kubectl commands, and set up local verification environment rules (Ingress/manifests).

## Step 8: 2026-08-06
- **Prompt:** `Add incremental file generation rule (Max 1-2 files per step) to agents`
- **Summary:** Mandated single-task, incremental file generation rules in Evaluator/Executor system prompts to prevent token truncation and incomplete outputs.

## Step 9: 2026-08-06
- **Prompt:** `Separate target repository Git management and add automated step commit/rollback workflow`
- **Summary:** Added workspace/ directory to .gitignore for independent repository isolation, and implemented target Git auto-init, step commit on Green, and hard-reset rollback on harness failure.

## Step 10: 2026-08-06
- **Prompt:** `Expand Ollama API context length (16k) and remove single-step file output limits`
- **Summary:** Configured Ollama num_ctx option for dynamic 16k context window expansion, increased timeout to 600s, and removed file count restrictions in agent prompts for powerful local LLMs (Qwen 27B).

## Step 11: 2026-08-06
- **Prompt:** `Strengthen README documentation completeness rules in policies and harness verification`
- **Summary:** Mandated comprehensive README requirements (app purpose/Nginx explanation, exact helm install/kubectl apply commands, values parameter table) and added automatic README validation to verify-harness.sh.

## Step 12: 2026-08-11
- **Prompt:** `Migrate local LLM backend from Ollama to llama.cpp server with startup scripts and configurable port`
- **Summary:** Added LlamaCppAdapter using OpenAI-compatible /v1/chat/completions endpoint. Updated config.env with EXECUTOR_PROVIDER=llama_cpp, LOCAL_LLM_URL=http://127.0.0.1:11435, and LLAMA_MAX_TOKENS for per-request output token control. Created Windows batch startup scripts (scripts/llama-start-devstral.bat, llama-start-qwen-coder.bat) with LLAMA_HOME/LLAMA_PORT/LLAMA_CTX/LLAMA_NGL environment variable overrides. Default port set to 11435 to keep 8080 available for loop-engineered applications.

## Step 13: 2026-08-16
- **Prompt:** `Refactor documentation generation responsibilities to Evaluator upon successful harness completion`
- **Summary:** Offloaded README/documentation generation from local Executor to cloud Evaluator (Claude) upon harness green completion, unblocking local LLM context limits and ensuring comprehensive documentation.

## Step 14: 2026-08-16
- **Prompt:** `Enhance autonomous runner with progress review logging and strengthen Go build validation policies for Identicon Generator.`
- **Summary:**
  - Added periodic `📊 [Progress Review]` summary log output in `runner/run_loop.py` triggered every `REVIEW_INTERVAL` steps and upon loop completion.
  - Reinforced Go module import consistency, `//go:embed` asset co-generation, and struct test type safety rules across `policies/feature_dev.md` and `agents/code-executor.md`.
  - Corrected harness verification command paths in `config.env` to ensure raw Go compilation logs are accurately evaluated.
- **Files Affected:** `runner/run_loop.py`, `config.env`, `policies/feature_dev.md`, `agents/code-executor.md`, `prompt_history.md`

## Step 15: 2026-08-17
- **Prompt:** `Refactor and modularize run_loop.py into dedicated submodules with extension-based dynamic code formatters.`
- **Summary:**
  - Decoupled `runner/run_loop.py` by extracting code parsing into `runner/parser.py`, Git operations into `runner/git_ops.py`, and auto-formatting into `runner/formatters.py`.
  - Implemented extension-based dynamic code formatter registry (`runner/formatters.py`) that auto-detects modified file types (`.go`, `.py`, `.js`, etc.) and executes appropriate formatters prior to Git commits.
- **Files Affected:** `runner/run_loop.py`, `runner/parser.py`, `runner/git_ops.py`, `runner/formatters.py`, `prompt_history.md`

## Step 12 - 2026-08-19
- **Prompt**: PROGRESS.md / memo.md / current_issues.md による状態分離アーキテクチャの実装
- **Summary of Decision**: プロンプト内への過去ログ・文脈埋め込みを廃止し、状態管理を `PROGRESS.md`, `memo.md`, `current_issues.md` に完全分離。Evaluator プロンプトは「指示のみ」の超軽量構造に改修する。

## Step 13 - 2026-08-19
- **Prompt**: スクラム開発要素（リファインメント・スプリント・カスタムハーネス）を取り入れた Scrum AI Loop の設計と実装
- **Summary of Decision**: リファインメントによる仕様漏れ確認・スプリント分割・スプリント専用カスタムハーネス生成を行う Phase 1 と、スコープ限定で自律開発・検証を行う Phase 2 からなる 2 段階スクラム型 AI ループを設計・実装する。

## Step 14 - 2026-08-19
- **Prompt**: 動的ポリシー・ナレッジ自動選択・構成機能（Dynamic Policy & Knowledge Wiring）の実装
- **Summary of Decision**: feature_dev.md から言語固有コードを references/go_clean_architecture.md へ分離。リファインメント時に policies/ と references/ から最適な規約を自動選定し、スプリント専用ポリシー `sprints/sprint_N_policy.md` を動的に自動構成する仕組みを導入する。

## Step 15 - 2026-08-19
- **Prompt**: リファインメント用モデルの分離とクラウドLLM固定ガードレールの実装 (`[Order] 今の内容を進めてください`)
- **Summary of Decision**: リファインメント（Phase 1）専用のプロバイダ設定 `REFINEMENT_PROVIDER` / `REFINEMENT_MODEL` を config.env に新設。Phase 1 ではローカル LLM の誤用を防止し、Gemini / Claude 等の強力なクラウド LLM が常時リファインメントを担当するよう runner/run_scrum.py を改修する。

## Step 16 - 2026-08-19
- **Prompt**: スプリント粒度（5ループ標準）の設定、全体プロダクトバックログ分割、およびレトロスペクティブ機能の実装 (`[Order] 今の内容を進めてください`)
- **Summary of Decision**: リファインメント時に全体仕様を「1スプリント＝約5ループ」のサイズに分割した `sprints/product_backlog.md` を作成。スプリント実行が5ループ内で完了しなかった場合は、Evaluator が原因とカイゼン案を解析した `sprints/retrospective.md` を自動生成する仕組みを実装する。

## Step 17 - 2026-08-19
- **Prompt**: ローカル LLM の動作スペック・コンテキスト上限（16k/4k）と能力特性（一括構築力・デバッグ修復特性）のインプット機能の実装
- **Summary of Decision**: Product Owner AI（Gemini）がローカル LLM のコンテキスト上限（16,384 tokens）と出力上限（4,096 tokens）、一括構築能力と複雑デバッグの苦手傾向をあらかじめ把握し、出力途切れや過剰なプロンプト要求を起こさないスプリント設計を行えるよう runner/run_scrum.py を改修する。

## Step 18 - 2026-08-19
- **Prompt**: 全スプリント分バックログ・ハーネス一括生成機能の実装と icon_generator.md の依存制約解除
- **Summary of Decision**: references/icon_generator.md から「Go標準パッケージのみ」の制約記述を削除。リファインメント（Phase 1）時に全スプリント（Sprint 1, 2, 3...）のバックログとカスタムハーネスを一括生成し、スプリントを最後まで中断なく完走できるように runner/run_scrum.py を改修する。

## Step 19 - 2026-08-19
- **Prompt**: 2段階リファインメント（2-Pass Refinement）の実装と全スプリント詳細出力
- **Summary of Decision**: 出力トークン圧迫による product_backlog.md の切り詰めを防止するため、リファインメントを「Pass 1: 詳細ロードマップ＋全スプリントバックログ出力」と「Pass 2: 各スプリントカスタムハーネス＋ポリシー出力」の2段階に分割。高密度かつ完全な全スプリント成果物を一括生成できるよう runner/run_scrum.py を改修する。
## Step 20 - 2026-08-19
- **Prompt**: Integration of state management and context injection using memo.md and current_issues.md
- **Summary of Decision**: Implemented structured issue and recovery tracking in `current_issues.md` for failed harness steps. Ensured full architecture rules from `memo.md` are continuously injected into Evaluator and Executor prompts in `runner/run_scrum.py`.

## Step 21 - 2026-08-19
- **Prompt**: Extend max loop limit to 10 per sprint and enforce auto-stop retrospectives
- **Summary of Decision**: Increased maximum autonomous loop limit per sprint from 5 to 10. Added auto-stop safeguard that generates `sprints/retrospective.md` when 10 loops are exceeded to enable continuous improvement.

## Step 22 - 2026-08-19
- **Prompt**: [Order] Summary of Scrum runner enhancements and state tracking implementation
- **Summary of Decision**: Implemented 10-loop max sprint execution, auto-stop retrospective generation, and state file tracking via `current_issues.md` and `memo.md`.

## Step 23 - 2026-08-19
- **Prompt**: [Order] Refactor directory structure to aggregate state and temporary management files into `state/`
- **Summary of Decision**: Refactor repository structure by moving dynamic state files (`memo.md`, `current_issues.md`, `PROGRESS.md`, `sprints/`) into a dedicated `state/` directory. Update path references in `runner/run_scrum.py`, `runner/run_loop.py`, and `.gitignore`.
## Step 24 - 2026-08-19
- **Prompt**: Remove unused `reports/` directory
- **Summary of Decision**: Deleted unused `reports/` directory and `reports/README.md` to keep the workspace root clean and maintain `references/` exclusively for user-provided reference files.
## Step 25 - 2026-08-20
- **Prompt**: Consolidate `references/` gitignore rules into root `.gitignore` and add `references/.gitkeep`
- **Summary of Decision**: Removed nested `references/.gitignore` and consolidated user reference exclusion rules directly into the root `.gitignore`. Created `references/.gitkeep` for directory structure preservation.
