package model

import (
	"crypto/md5"
	"encoding/hex"
	"fmt"
)

type Grid struct {
	Cells [5][5]bool
}

func NewGrid(hash [16]byte) *Grid {
	g := &Grid{}
	for row := 0; row < 5; row++ {
		for col := 0; col < 5; col++ {
			if col < 3 {
				// Map hash bytes to first 3 columns
				byteIndex := (row*3 + col) % 16
				g.Cells[row][col] = (hash[byteIndex] % 2) == 0
			} else {
				// Enforce horizontal symmetry for columns 3 and 4
				g.Cells[row][3] = g.Cells[row][1]
				g.Cells[row][4] = g.Cells[row][0]
			}
		}
	}
	return g
}

func (g *Grid) String() string {
	var s string
	for row := 0; row < 5; row++ {
		for col := 0; col < 5; col++ {
			if g.Cells[row][col] {
				s += "1 "
			} else {
				s += "0 "
			}
		}
		s += "\n"
	}
	return s
}
