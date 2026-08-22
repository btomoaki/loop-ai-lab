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
