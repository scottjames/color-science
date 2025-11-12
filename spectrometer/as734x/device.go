package as734x

import (
	"errors"
	"time"
)

var (
	errUnknownDevice   = errors.New("as734x: unknown device")
	errUnsupportedGain = errors.New("as734x: gain not supported by variant")
)

type Device struct {
	bus      Bus
	addr     uint8
	variant  Variant
	cfg      Config
	bank     uint8
	cfg0     byte
	cfg0Init bool
}

func New(bus Bus) *Device {
	return &Device{
		bus:  bus,
		addr: DefaultConfig().Address,
		bank: 0,
	}
}

func (d *Device) Configure(cfg Config) error {
	if cfg.Address == 0 {
		cfg.Address = DefaultConfig().Address
	}
	d.addr = cfg.Address

	if err := d.powerOn(); err != nil {
		return err
	}

	variant, err := d.detectVariant()
	if err != nil {
		return err
	}
	d.variant = variant
	d.cfg = cfg

	switch d.variant {
	case VariantAS7341:
		return d.configureAS7341()
	case VariantAS7343:
		return d.configureAS7343()
	default:
		return errUnknownDevice
	}
}

func (d *Device) Variant() Variant {
	return d.variant
}

func (d *Device) Read() (RawMeasurement, error) {
	if d.variant == VariantAS7341 {
		return d.readAS7341()
	}
	if d.variant == VariantAS7343 {
		return d.readAS7343()
	}
	return RawMeasurement{}, errUnknownDevice
}

func (d *Device) powerOn() error {
	return d.writeRegRaw(regEnable, 0x01)
}

func (d *Device) detectVariant() (Variant, error) {
	if id, err := d.readRegRaw(regWhoAmIAS7341); err == nil {
		if (id & 0xFC) == (as7341ChipID << 2) {
			return VariantAS7341, nil
		}
	}

	if id, err := d.readAS7343ID(); err == nil {
		if id == as7343ChipID {
			return VariantAS7343, nil
		}
	}

	return VariantUnknown, errUnknownDevice
}

func (d *Device) readAS7343ID() (byte, error) {
	id, err := d.readRegRaw(regIDAS7343)
	if err == nil && id == as7343ChipID {
		return id, nil
	}
	if err := d.forceBankAS7343(1); err != nil {
		return 0, err
	}
	return d.readRegRaw(regIDAS7343)
}

func (d *Device) integrationTimeUs() uint32 {
	return integrationTimeUs(d.cfg.ATime, d.cfg.AStep)
}

func integrationTimeUs(atime uint8, astep uint16) uint32 {
	steps := uint32(atime) + 1
	delta := uint32(astep) + 1
	// 2.78 microseconds per step.
	return (steps * delta * 2780) / 1000
}

func (d *Device) waitForDataReady(reg byte, mask byte, timeout time.Duration) error {
	deadline := time.Now().Add(timeout)
	for {
		b, err := d.readReg(reg)
		if err != nil {
			return err
		}
		if b&mask != 0 {
			return nil
		}
		if time.Now().After(deadline) {
			return errors.New("as734x: data ready timeout")
		}
		time.Sleep(time.Millisecond * 5)
	}
}
