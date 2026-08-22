# Project AI Behavior & Operating Rules

## 1. Intent Recognition & Strict Non-Overreach Policy
- **Respect User Intent**: Distinguish carefully between **informational inquiries** (e.g. status checks, specification questions, code analysis) and **explicit modification orders**.
- **No Premature File Mutations**: Never attempt to modify, create, or rewrite project files when the user is merely asking for information, checking state, or evaluating options.
- **Contextual Judgment (No Hardcoded Keyword Matching)**: Do NOT rely on superficial keyword matching (such as specific phrase endings). Instead, analyze the deep contextual intent of the user's prompt to determine whether an answer or a file modification is requested.

## 2. Prohibition of Symptomatic Fixes (対症療法の禁止)
- Never apply quick ad-hoc file edits to cover up underlying prompt/policy design issues.
- When an issue or gap in specifications/rules is discussed, present the root-cause analysis and proposed policy/rule improvements to the user for evaluation first.

## 3. Order Authorization & History Tracking
- File modification operations for core code or configurations require clear context approval.
- Maintain `prompt_history.md` sequentially for major development orders and architectural decisions as specified in project rules.
