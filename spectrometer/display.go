package main

import (
	"image/color"
	"machine"
	"time"

	"tinygo.org/x/drivers"
	"tinygo.org/x/drivers/st7735"
)

type Display struct {
	st7735.Device
}

var _ drivers.Displayer = (*Display)(nil)

func newDisplay() *Display {
	spi := machine.SPI3
	spi.Configure(machine.SPIConfig{
		Frequency: 32_000_000,
		SCK:       displaySCK,
		SDO:       displaySDO,
	})
	time.Sleep(200 * time.Millisecond)
	dev := st7735.New(spi, displayRST, displayDC, displayCS, displayBL)
	dev.Configure(st7735.Config{
		Model:        st7735.MINI80x160,
		Width:        80,
		Height:       160,
		ColumnOffset: 26,
		RowOffset:    1,
		Rotation:     st7735.ROTATION_270,
	})
	d := &Display{Device: dev}
	d.FillScreen(color.RGBA{0, 0, 0, 255})
	return d
}
