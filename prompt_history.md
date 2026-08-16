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
