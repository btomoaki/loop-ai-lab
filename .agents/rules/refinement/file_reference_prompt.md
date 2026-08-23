# File-Path Reference & Context Sharing Rule

## Rule Definition
1. **No Raw Text Concatenation**: Prompts MUST NOT concatenate long texts or logs into the prompt payload. This prevents context window overflow and semantic compression breakdown.
2. **Evaluator File-Path Sharing**: LLM context sharing MUST occur by specifying physical file paths under `state/.evaluator/`:
   - Task Specification: `state/initiatives/<epic>/sprint_N_backlog.yaml`
   - Active Status & Failure Logs: `state/.evaluator/current_issues.md`
   - Architectural Debates: `state/.evaluator/refinement_debate_log.md`
3. **Ultra-Lightweight Prompt Standard**: Prompts sent to LLMs MUST remain ultra-lightweight (< 300 chars) specifying target file paths and strict code block headers (`# FILE: relative/path`).
