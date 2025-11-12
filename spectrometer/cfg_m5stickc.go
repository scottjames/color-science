package main

import (
	"machine"

	"tinygo.org/x/drivers/axp192"
	si2c "tinygo.org/x/drivers/i2csoft"
)

var (
	displaySCK = machine.IO13
	displaySDO = machine.IO15
	displayRST = machine.IO18
	displayDC  = machine.IO23
	displayCS  = machine.IO5
	displayBL  = machine.NoPin

	i2cCLK  = machine.IO33
	i2cDATA = machine.IO32

	i2cInternalCLK  = machine.IO22
	i2cInternalDATA = machine.IO21
)

func initPower() {
	bus := si2c.New(i2cInternalCLK, i2cInternalDATA)
	bus.Configure(si2c.I2CConfig{Frequency: 100_000})
	pmu := axp192.New(bus)
	_ = pmu.SetLDOEnable(2, true)
}
