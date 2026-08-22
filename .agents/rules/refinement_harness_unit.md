# Pure Domain & Service Unit Test Harness Rule

## Rule Definition
1. **Language Standard Test Mandate**: Pure domain data models and algorithm services MUST use language-standard test frameworks (e.g., `go test -v ./...`).
2. **Invariants Assertion**: Harnesses MUST assert internal business invariants (e.g., 5x5 left-right grid symmetry, deterministic color generation).
