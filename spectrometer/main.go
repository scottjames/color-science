package main

import (
	"encoding/json"
	"image/color"
	"machine"
	"time"

	"github.com/itohio/color-science/spectrometer/analysis"
	"github.com/itohio/color-science/spectrometer/as734x"
	"github.com/itohio/color-science/spectrometer/i2c"
	ui "github.com/itohio/tinygui"
	"github.com/itohio/tinygui/container"
	"github.com/itohio/tinygui/layout"
	"github.com/itohio/tinygui/widget"
	"tinygo.org/x/tinyfont/freemono"
)

func main() {
	initPower()

	display := newDisplay()
	showRunning(display)

	uart := machine.Serial
	uart.Configure(machine.UARTConfig{BaudRate: 115200})

	bus := i2c.New(i2cCLK, i2cDATA)
	_ = bus.Configure(i2c.I2CConfig{Frequency: 100_000})

	sensor := as734x.New(bus)
	cfg := as734x.DefaultConfig()
	if err := sensor.Configure(cfg); err != nil {
		writeError(uart, err)
		return
	}

	analyzer := analysis.NewAnalyzer(sensor.Variant())
	ticker := time.NewTicker(250 * time.Millisecond)
	defer ticker.Stop()

	for range ticker.C {
		raw, err := sensor.Read()
		if err != nil {
			writeError(uart, err)
			continue
		}
		measurement := analyzer.Process(raw)
		writeJSON(uart, measurement)
	}
}

func showRunning(display *Display) {
	display.FillScreen(color.RGBA{0, 0, 0, 255})
	w, h := display.Size()
	label := widget.NewLabel(w, 16, &freemono.Regular9pt7b, func() string { return "Running" }, color.RGBA{255, 255, 255, 255})
	box := container.New[ui.Widget](w, 16,
		container.WithLayout[ui.Widget](layout.VList(2)),
		container.WithChildren[ui.Widget](label),
	)
	ctx := ui.NewContext(display, w, h, 0, 0)
	box.Draw(&ctx)
}

func writeError(uart *machine.UART, err error) {
	payload := struct {
		Error string `json:"error"`
		TS    int64  `json:"timestamp_us"`
	}{
		Error: err.Error(),
		TS:    time.Now().UnixMicro(),
	}
	writeJSON(uart, payload)
}

func writeJSON(uart *machine.UART, payload interface{}) {
	data, err := json.Marshal(payload)
	if err != nil {
		uart.Write([]byte("{\"error\":\"marshal\"}\n"))
		return
	}
	uart.Write(data)
	uart.Write([]byte("\n"))
}
