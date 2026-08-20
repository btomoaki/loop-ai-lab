# Development Memo & Design Rules

## Key Architecture & Design Decisions
- **Hierarchical Initiative Model**: Initiative Overview -> Epic Phase -> Sprint Task YAML
- **Sequential Refinement**: Refinement is executed per-Epic to avoid context window exhaustion.
- **Dynamic Harness**: Project environment checks and test execution are handled dynamically by harness scripts, not hardcoded into Python runners.
- **Sanitized Outputs**: LLM output markers (```) are automatically stripped by `parse_and_extract_files`.
- **Local LLM Engine**: Devstral 24B (llama.cpp) runs on `http://127.0.0.1:11435/completion` with non-blocking HTTP socket close (`Connection: close`).


## Domain Design & Code Organization Rules
- **Model Layer Purity**: `internal/domain/model/` contains ONLY pure data structures and structs (e.g. `type Grid struct`).
- **Separation of Factory/Logic**: Constructor & algorithmic logic functions (e.g. `func NewGrid(...)`) MUST NOT be placed inside `internal/domain/model/`. They must be decoupled into domain services or factory components.
