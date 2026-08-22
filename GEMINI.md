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

## Master Constraint: Workspace Self-Containment & No Outside Files Rule
- **NEVER create temporary, script, or cache files outside the project repository** (e.g. strictly forbidden to write to `/tmp/`, `/home/`, or system directories).
- All helper scripts, scratch files, and generator utilities MUST be stored strictly within the project repository (e.g. `scripts/` or `scratch/`) to ensure full auditability, version control, and zero hidden state.
