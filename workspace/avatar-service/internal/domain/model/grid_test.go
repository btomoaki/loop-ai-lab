```go
package model

import (
	"bytes"
	"crypto/md5"
	"encoding/hex"
	"fmt"
	"testing"
)

func TestNewGrid(t *testing.T) {
	tests := []struct {
		name     string
		hash     string
		expected [5][5]bool
	}{
		{
			name: "All even bytes",
			hash: "00000000000000000000000000000000",
			expected: [5][5]bool{
				{true, true, true, true, true},
				{true, true, true, true, true},
				{true, true, true, true, true},
				{true, true, true, true, true},
				{true, true, true, true, true},
			},
		},
		{
			name: "All odd bytes",
			hash: "01010101010101010101010101010101",
			expected: [5][5]bool{
				{false, false, false, false, false},
				{false, false, false, false, false},
				{false, false, false, false, false},
				{false, false, false, false, false},
				{false, false, false, false, false},
			},
		},
		{
			name: "Alternating bytes",
			hash: "000102030405060708090a0b0c0d0e0f",
			expected: [5][5]bool{
				{true, false, true, false, true},
				{true, false, true, false, true},
				{true, false, true, false, true},
				{true, false, true, false, true},
				{true, false, true, false, true},
			},
		},
		{
			name: "Zero-filled hash",
			hash: "00000000000000000000000000000000",
			expected: [5][5]bool{
				{true, true, true, true, true},
				{true, true, true, true, true},
				{true, true, true, true, true},
				{true, true, true, true, true},
				{true, true, true, true, true},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			hashBytes, err := hex.DecodeString(tt.hash)
			if err != nil {
				t.Fatalf("Failed to decode hex string: %v", err)
			}
			var hash [16]byte
			copy(hash[:], hashBytes)

			g := NewGrid(hash)

			if g == nil {
				t.Fatal("NewGrid returned nil")
			}

			for i := 0; i < 5; i++ {
				for j := 0; j < 5; j++ {
					if g.Cells[i][j] != tt.expected[i][j] {
						t.Errorf("Cell[%d][%d] = %v, want %v", i, j, g.Cells[i][j], tt.expected[i][j])
					}
				}
			}
		})
	}
}

func TestGridSymmetry(t *testing.T) {
	tests := []struct {
		name string
		hash string
	}{
		{
			name: "Symmetry test 1",
			hash: "000102030405060708090a0b0c0d0e0f",
		},
		{
			name: "Symmetry test 2",
			hash: "0102030405060708090a0b0c0d0e0f00",
		},
		{
			name: "Symmetry test 3",
			hash: "00000000000000000000000000000000",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			hashBytes, err := hex.DecodeString(tt.hash)
			if err != nil {
				t.Fatalf("Failed to decode hex string: %v", err)
			}
			var hash [16]byte
			copy(hash[:], hashBytes)

			g := NewGrid(hash)

			for i := 0; i < 5; i++ {
				if g.Cells[i][3] != g.Cells[i][1] {
					t.Errorf("Symmetry violation at row %d: Cells[%d][3] != Cells[%d][1]", i, i, i)
				}
				if g.Cells[i][4] != g.Cells[i][0] {
					t.Errorf("Symmetry violation at row %d: Cells[%d][4] != Cells[%d][0]", i, i, i)
				}
			}
		})
	}
}

func TestGridDeterministic(t *testing.T) {
	hash := "000102030405060708090a0b0c0d0e0f"
	hashBytes, err := hex.DecodeString(hash)
	if err != nil {
		t.Fatalf("Failed to decode hex string: %v", err)
	}
	var h [16]byte
	copy(h[:], hashBytes)

	g1 := NewGrid(h)
	g2 := NewGrid(h)

	if g1 == nil || g2 == nil {
		t.Fatal("NewGrid returned nil")
	}

	for i := 0; i < 5; i++ {
		for j := 0; j < 5; j++ {
			if g1.Cells[i][j] != g2.Cells[i][j] {
				t.Errorf("Determinism violation at Cell[%d][%d]: %v != %v", i, j, g1.Cells[i][j], g2.Cells[i][j])
			}
		}
	}
}

func TestGridParity(t *testing.T) {
	tests := []struct {
		name     string
		hash     string
		expected [5][5]bool
	}{
		{
			name: "Parity test 1",
			hash: "000102030405060708090a0b0c0d0e0f",
			expected: [5][5]bool{
				{true, false, true, false, true},
				{true, false, true, false, true},
				{true, false, true, false, true},
				{true, false, true, false, true},
				{true, false, true, false, true},
			},
		},
		{
			name: "Parity test 2",
			hash: "0102030405060708090a0b0c0d0e0f00",
			expected: [5][5]bool{
				{false, true, false, true, false},
				{true, false, true, false, true},
				{false, true, false, true, false},
				{true, false, true, false, true},
				{false, true, false, true, false},
			},
		},
		{
			name: "Parity test 3",
			hash: "00000000000000000000000000000000",
			expected: [5][5]bool{
				{true, true, true, true, true},
				{true, true, true, true, true},
				{true, true, true, true, true},
				{true, true, true, true, true},
				{true, true, true, true, true},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			hashBytes, err := hex.DecodeString(tt.hash)
			if err != nil {
				t.Fatalf("Failed to decode hex string: %v", err)
			}
			var hash [16]byte
			copy(hash[:], hashBytes)

			g := NewGrid(hash)

			for i := 0; i < 5; i++ {
				for j := 0; j < 5; j++ {
					if g.Cells[i][j] != tt.expected[i][j] {
						t.Errorf("Cell[%d][%d] = %v, want %v", i, j, g.Cells[i][j], tt.expected[i][j])
					}
				}
			}
		})
	}
}
```
