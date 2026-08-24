# 🏃 Ceremony 3: Autonomous TDD Dev Executor Instructions

## 1. Output Format Mandatory Rule (CRITICAL)
- Generate complete implementation and test code files in Go using `# FILE: <relative_path>` format.
- Do NOT use generic placeholders (like `# FILE: <relative_path>`). Always use concrete relative paths inside the target workspace.

### Example Format:
# FILE: main.go
package main

import "fmt"

func main() {
    fmt.Println("Identicon Generator Started")
}

# FILE: internal/core/identicon.go
package core

type Identicon struct {
    Input string
}

## 2. Architecture & Design Rules
- Strictly follow Clean Architecture 4-layer separation (Domain, Usecase, Interface/Delivery, Adapter/Infrastructure).
- Explicitly handle Go type casts (e.g. `uint8(r)` for RGBA color struct fields).
- Ensure Graceful Shutdown (`SIGTERM`/`SIGINT`) for all server executables.
- Write un-truncated, production-ready Go code and accompanying `*_test.go` unit tests.
