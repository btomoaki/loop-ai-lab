# Project AI Behavior & Operating Rules

## 1. MANDATORY CONDITION FOR FILE MODIFICATIONS (最優先ハードルール)
- **Explicit User Instruction Required**: File creation, modification, or deletion operations MUST ONLY be executed when the user provides an **explicit modification command** (e.g. "修正して", "適用して", "実装して").
- **Strict Prohibition on Inquiries**: For informational prompts, status checks, or bug reports (e.g. "〜か教えて", "〜になってるね"), NEVER modify any files. Report analysis results and wait for explicit instructions.

## 2. Intent Recognition & Non-Overreach Policy
- Analyze contextual intent to distinguish pure status inquiries from explicit work orders.
- Do NOT rely on hardcoded keyword matching alone; evaluate the full conversational intent.

## 3. Prohibition of Symptomatic Fixes (対症療法の禁止)
- Never apply quick ad-hoc file edits to cover up underlying prompt/policy design issues.
- Present root-cause analysis and proposed policy/rule improvements to the user for evaluation first.


## Section 3: FILE-PATH REFERENCE CONTEXT SHARING MANDATE
- **Prohibition of Raw Text Concatenation**: Prompts sent to any LLM (Evaluator or Dev Agent) MUST NOT concatenate massive raw texts (past logs, memos, debate logs) into the prompt body to avoid semantic compression breakdown.
- **Mandatory File-Path Reference**: Contexts, memos, and issue tracking MUST be stored as structured files inside `state/.evaluator/` (e.g. `state/.evaluator/current_issues.md`, `state/.evaluator/refinement_debate_log.md`).
- **Path-Only Sharing**: Prompts MUST specify target physical file paths inside `state/.evaluator/` and request the LLM to inspect the file path directly.

## Section 4: PROHIBITION OF ARTIFICIAL EPIC/TASK LIMITS (個数制限の厳禁)
- **Strict Ban on Hardcoded Counts**: NEVER impose artificial numeric limits on epics, tasks, or sprints (e.g. strictly forbidden to hardcode prompts like "2 to 4 epics" or "split into 3 tasks").
- **Domain & Responsibility-Driven Granularity**: Decomposition MUST be determined autonomously based on cohesive domain boundaries, single-responsibility principle (SRP), and LLM capacity realism. Multiple distinct components (e.g. domain logic, rasterizer, HTTP handlers, SPA frontend, container, cloud deployment) MUST NOT be forcefully merged into mega-epics.

## Section 5: LOCAL LLM CONTEXT PROTECTION & HYBRID ROUTING (ローカルLLM過負荷防止ルール)
- **Prohibition of Massive Prompts to Local LLM**: NEVER send massive context payloads (full system specifications, entire codebase dumps, concatenated multi-file documentation) to Local LLMs (Devstral / llama-server). Massive full-document parsing MUST exclusively be routed to Cloud Gemini (via `agy` CLI or cloud adapters).
- **Micro-Payload Guarantee for Local LLM**: Prompts sent to Local LLM MUST be strictly scoped micro-prompts (e.g. single epic contract under 25 lines, single test failure log, targeted function implementation) to prevent token truncation, timeouts, and hallucination.

## Section 6: PROHIBITION OF UNAUTHORIZED FALLBACKS & SILENT MOCKING (勝手なフォールバック・ゾンビ化の完全禁止)
- **Zero Silent Fallback Policy**: NEVER implement secret or automatic fallbacks that switch models (e.g., silently falling back from Cloud Gemini to Local LLM on failure) or inject hardcoded dummy mock data when LLM parsing/generation fails.
- **Fail-Fast & Explicit Escalation**: Whenever an LLM provider errors, connection times out, CLI exits with non-zero code, or output parsing fails, you MUST immediately halt execution and raise an explicit `RuntimeError` with the full raw response and error log.
- **Explicit User Consent for Recovery**: Any fallback, retry strategy shift, or degraded operation mode requires explicit user instruction before execution.

## Master Constraint: Workspace Self-Containment & No Outside Files Rule
- **NEVER create temporary, script, or cache files outside the project repository** (e.g. strictly forbidden to write to `/tmp/`, `/home/`, or system directories).
- All helper scripts, scratch files, and generator utilities MUST be stored strictly within the project repository (e.g. `scripts/` or `scratch/`) to ensure full auditability, version control, and zero hidden state.
