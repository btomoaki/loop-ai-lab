```markdown
# Sprint 1 Implementation Policy: 5×5 Symmetric Grid Matrix Entity & Deterministic Parity Fill Algorithm

## 1. Executive Summary & Sprint Scope
- **Epic:** Epic 1: Domain Core & Algorithmic Modeling
- **Sprint:** 1
- **Task:** Implement 5×5 Symmetric Grid Matrix Entity & Deterministic Parity Fill Algorithm
- **Target Files:**
  - `workspace/avatar-service/internal/domain/model/grid.go`
  - `workspace/avatar-service/internal/domain/model/grid_test.go`
- **Primary Objective:** Implement the core domain entity `Grid` and its exported constructor `NewGrid(hash [16]byte) *Grid` to convert a 16-byte MD5 digest into a horizontally symmetric 5×5 boolean matrix with 100% test coverage and zero third-party dependencies.

---

## 2. Architectural Principles & Clean Architecture Constraints
1. **Zero External Dependencies:**
   - `internal/domain/model` must strictly rely on Go standard/built-in primitives.
   - Do NOT import third-party packages (e.g., `github.com/*`).
   - Do NOT import infrastructure or presentation packages (`net/http`, `image`, `image/png`, `internal/infrastructure/...`, `internal/application/...`).
2. **Package Namespace Safety:**
   - Package declaration must be `package model`.
   - Built-in types (`[5][5]bool`, `[16]byte`) must be used directly.
3. **Immutability & Pure Functions:**
   - `NewGrid` is a pure function that deterministically produces a `*Grid` given an identical 16-byte MD5 array.

---

## 3. Detailed Algorithmic Specification

### 3.1 Domain Entity Structure
```go
package model

// Grid represents a 5x5 boolean matrix where true indicates a filled cell
// and false indicates a background/blank cell.
type Grid struct {
    Cells [5][5]bool
}
```

### 3.2 Constructor Signature
```go
// NewGrid constructs a 5x5 symmetric Grid based on byte parity from a 16-byte MD5 hash.
func NewGrid(hash [16]byte) *Grid
```

### 3.3 Parity-Based Cell Fill Logic
- For each byte $B_k$:
  - **Even Byte** (`byte % 2 == 0`): Cell is **filled** (`true`).
  - **Odd Byte** (`byte % 2 != 0`): Cell is **blank** (`false`).

### 3.4 16-Byte MD5 Hash to Matrix Mapping
The first 3 columns (Columns 0, 1, and 2) across all 5 rows are mapped directly from the 16-byte MD5 hash array according to the following strict index mapping:

| Row Index | Column 0 (Left) | Column 1 (Inner Left) | Column 2 (Center) | MD5 Byte Indices |
| :--- | :--- | :--- | :--- | :--- |
| **Row 0** | `hash[3]` | `hash[4]` | `hash[5]` | `B3, B4, B5` |
| **Row 1** | `hash[6]` | `hash[7]` | `hash[8]` | `B6, B7, B8` |
| **Row 2** | `hash[9]` | `hash[10]` | `hash[11]` | `B9, B10, B11` |
| **Row 3** | `hash[12]` | `hash[13]` | `hash[14]` | `B12, B13, B14` |
| **Row 4** | `hash[15]` | `hash[0]` | `hash[1]` | `B15, B0, B1` |

*(Note: `hash[2]` is reserved for color derivation in Sprint 2 and is omitted from the grid parity matrix).*

### 3.5 Horizontal Symmetry Mirroring Invariance
Columns 3 and 4 must strictly mirror Columns 1 and 0 across all 5 rows:
- `grid.Cells[row][3] = grid.Cells[row][1]` (Column 3 mirrors Column 1)
- `grid.Cells[row][4] = grid.Cells[row][0]` (Column 4 mirrors Column 0)
- Enforced for all `row` in `0..4`.

### 3.6 Full 5×5 Matrix Layout Visualization
```text
Row 0: [ B3  ] [ B4  ] [ B5  ] [ B4  ] [ B3  ]
Row 1: [ B6  ] [ B7  ] [ B8  ] [ B7  ] [ B6  ]
Row 2: [ B9  ] [ B10 ] [ B11 ] [ B10 ] [ B9  ]
Row 3: [ B12 ] [ B13 ] [ B14 ] [ B13 ] [ B12 ]
Row 4: [ B15 ] [ B0  ] [ B1  ] [ B0  ] [ B15 ]
         Col 0   Col 1   Col 2   Col 3   Col 4
        (Left)  (InnerL) (Center)(InnerR) (Right)
```

---

## 4. Test Suite Requirements (`grid_test.go`)

### 4.1 Required Test Cases
1. **`TestNewGrid_Parity`**:
   - Verify that individual byte parity calculations evaluate strictly to `true` for even values and `false` for odd values.
2. **`TestNewGrid_Symmetry`**:
   - Verify that for any arbitrary hash input, `Cells[r][3] == Cells[r][1]` and `Cells[r][4] == Cells[r][0]` hold true for all rows $r \in [0, 4]$.
3. **`TestNewGrid_Deterministic`**:
   - Verify that passing the same `[16]byte` hash vector produces an identical `Grid` output every time.
4. **`TestNewGrid_EdgeCases`**:
   - **All Even Bytes** (e.g., all `0x00` or `0x02`): Every cell in the 5×5 matrix must evaluate to `true`.
   - **All Odd Bytes** (e.g., all `0x01` or `0xFF`): Every cell in the 5×5 matrix must evaluate to `false`.
   - **Alternating Pattern** (e.g., even/odd alternating bytes): Verify exact expected cell layout.
   - **Zero-Filled Hash** (`[16]byte{}`): Verify all cells evaluate to `true` (since `0 % 2 == 0`).

---

## 5. Definition of Done (DoD) & Verification Checklist

- [ ] **Coverage:** 100% statement and branch coverage achieved for `grid.go` (`go test -v -cover ./internal/domain/model/...`).
- [ ] **Race Detection:** Zero race conditions detected (`go test -race ./internal/domain/model/...`).
- [ ] **Code Hygiene:** Strict compliance with `gofmt` and zero warnings from `go vet ./internal/domain/model/...`.
- [ ] **Architectural Purity:** `grid.go` contains zero third-party dependencies and zero infrastructure/rendering imports.
- [ ] **Symmetry Invariance:** Horizontal symmetry is mathematically preserved across all test vectors.
- [ ] **Test Harness:** Verification script `state/initiatives/epic_1_domain/sprint_1_harness.sh` executes with exit code 0.

---

## 6. Verification Execution
To verify the implementation against this policy and acceptance criteria, execute:

```bash
bash state/initiatives/epic_1_domain/sprint_1_harness.sh
```
```
