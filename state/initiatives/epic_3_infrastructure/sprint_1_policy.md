```markdown
# Implementation Policy: Epic 3 — Sprint 1
**Task:** Implement 250x250 PNG Image Rasterizer and Stream Encoder Adapter  
**Target Files:**
- `internal/infrastructure/renderer/png_renderer.go`
- `internal/infrastructure/renderer/png_renderer_test.go`

---

## 1. Architectural & Design Guidelines

### 1.1 Clean Architecture Placement
- **Layer:** Infrastructure Layer (`internal/infrastructure/renderer`)
- **Port Implementation:** Must implement the domain port interface `repository.AvatarRenderer`:
  ```go
  package repository

  type AvatarRenderer interface {
      Render(avatar *model.Avatar) ([]byte, error)
  }
  ```
- **Constructor / Provider:** Export `NewPNGRenderer() repository.AvatarRenderer` returning the domain port interface type to enable decoupled dependency injection.
- **Inward Dependency Rule:** The renderer package may import `internal/domain/model` and `internal/domain/repository`, but domain packages must never import `internal/infrastructure/renderer`.

### 1.2 Zero External Dependencies
- Use **only** standard Go library packages:
  - `bytes`
  - `errors`
  - `fmt`
  - `image`
  - `image/color`
  - `image/draw`
  - `image/png`
- Under no circumstances may third-party drawing or imaging libraries (e.g., `fogleman/gg`, `disintegration/imaging`) be imported.

---

## 2. Technical & Algorithmic Specifications

### 2.1 Canvas & Background Initialization
- **Canvas Geometry:** Allocate a 250x250 pixel RGBA image:
  ```go
  bounds := image.Rect(0, 0, 250, 250)
  img := image.NewRGBA(bounds)
  ```
- **Background Fill:** Fill the canvas with background color `#F0F2F5` (`color.RGBA{R: 240, G: 242, B: 245, A: 255}`) or `avatar.BackgroundColor` if defined on the entity:
  ```go
  bgColor := avatar.BackgroundColor
  draw.Draw(img, bounds, &image.Uniform{C: bgColor}, image.Point{}, draw.Src)
  ```

### 2.2 Grid Rasterization
- **Grid Traversal:** Iterate through the 5×5 boolean grid (`avatar.Grid.Matrix` or `avatar.Grid[row][col]`).
- **Cell Geometry:** Each cell is a 50×50 pixel square:
  - Row index `row` $\in [0, 4]$, Column index `col` $\in [0, 4]$
  - Rectangular coordinates: `image.Rect(col*50, row*50, (col+1)*50, (row+1)*50)`
- **Block Painting:** For cells evaluated as `true`, paint the block using `draw.Draw` with `avatar.MainColor` (or `avatar.Color`):
  ```go
  if avatar.Grid.Cells[row][col] {
      cellRect := image.Rect(col*50, row*50, (col+1)*50, (row+1)*50)
      draw.Draw(img, cellRect, &image.Uniform{C: avatar.MainColor}, image.Point{}, draw.Src)
  }
  ```

### 2.3 Binary PNG Stream Encoding
- Encode the in-memory RGBA image to PNG format using `png.Encode` writing to a `bytes.Buffer`:
  ```go
  var buf bytes.Buffer
  if err := png.Encode(&buf, img); err != nil {
      return nil, fmt.Errorf("failed to encode png image: %w", err)
  }
  return buf.Bytes(), nil
  ```

### 2.4 Input Validation & Error Handling
- Return an explicit, descriptive error when:
  - `avatar == nil` (e.g., `errors.New("avatar cannot be nil")`)
  - `avatar.Grid == nil`
- Never panic on malformed input.

---

## 3. Testing & Definition of Done (DoD) Requirements

### 3.1 Unit Test Suite (`png_renderer_test.go`)
1. **Magic Bytes Validation:** Verify that rendered bytes start with the official 8-byte PNG signature:
   `[]byte{0x89, 'P', 'N', 'G', 0x0D, 0x0A, 0x1A, 0x0A}`.
2. **Dimension Assertions:** Decode the rendered byte slice via `png.Decode` and assert:
   - `bounds.Dx() == 250`
   - `bounds.Dy() == 250`
3. **Pixel Color Sampling:** Sample pixels at cell centers `(col*50 + 25, row*50 + 25)`:
   - If cell is `true`: color must match `avatar.MainColor`.
   - If cell is `false`: color must match background `#F0F2F5`.
4. **Boundary & Nil Handling:** Verify `Render(nil)` returns an error without panicking.
5. **Coverage:** Achieve 100% statement and branch coverage for `PNGRenderer`.

### 3.2 Static Analysis & Formatting
- Code must pass `gofmt -l` with zero diffs.
- Code must pass `go vet ./internal/infrastructure/renderer/...`.
```
