# Meta Architecture Policy: Externalization & Dynamic Rule Ingestion

## 1. Single Source of Truth Rule (Specification Externalization)
- All architectural constraints, design patterns, coding standards, personas, and refinement instructions must be externalized as Markdown files under `.agents/rules/` and `.agents/personas/`.
- Never hardcode domain logic, file paths, persona definitions, or rule instructions inside Python runner code (`RefinementEngine`, `ScrumRunner`, etc.).
- Adding or modifying a Markdown file in `.agents/rules/` must immediately update the AI system's behavior without requiring Python code changes.

## 2. Dynamic Context Loading Rule (Automatic Rule Ingestion)
- All execution engines (`RefinementEngine`, `SprintEngine`, etc.) must automatically scan and ingest all Markdown files inside `.agents/rules/` (recursively across all subdirectories) and `.agents/personas/` at runtime.
- Ingested rules must be injected into the LLM prompt context to guarantee 100% compliance with current repository standards.

## 3. Iterative Refactoring Principle (Gradual Hardcode Elimination)
- Existing legacy hardcoded paths or logic in runner scripts shall not be refactored all at once.
- Refactoring to eliminate hardcoded logic will be proposed iteratively whenever a future development task or feature modification directly touches that area of code.
