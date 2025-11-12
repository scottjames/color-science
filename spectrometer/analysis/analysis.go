package analysis

import (
	"math"
	"strconv"

	"github.com/itohio/color-science/spectrometer/as734x"
)

type Analyzer struct {
	variant       as734x.Variant
	prevIntensity uint32
}

type Channel struct {
	Name       string  `json:"name"`
	Raw        uint16  `json:"raw"`
	Normalized float32 `json:"normalized"`
}

type Spectrum struct {
	Channels []Channel `json:"channels"`
	Sum      uint32    `json:"sum"`
	Max      uint16    `json:"max"`
}

type FlickerStats struct {
	Frequency  uint16  `json:"frequency_hz"`
	Valid      bool    `json:"valid"`
	Modulation float32 `json:"modulation_percent"`
	Saturated  bool    `json:"saturated"`
	Raw        uint8   `json:"raw"`
}

type Measurement struct {
	TimestampUs   int64        `json:"timestamp_us"`
	Variant       string       `json:"variant"`
	IntegrationUs uint32       `json:"integration_us"`
	Gain          float32      `json:"gain"`
	Spectrum      Spectrum     `json:"spectrum"`
	Flicker       FlickerStats `json:"flicker"`
	Saturated     bool         `json:"saturated"`
}

func NewAnalyzer(variant as734x.Variant) Analyzer {
	return Analyzer{variant: variant}
}

func (a *Analyzer) Process(raw as734x.RawMeasurement) Measurement {
	names := channelNames[a.variant]
	channels := make([]Channel, len(raw.Channels))
	var sum uint32
	var max uint16
	for i, v := range raw.Channels {
		sum += uint32(v)
		if v > max {
			max = v
		}
		channels[i] = Channel{Name: safeName(names, i), Raw: v}
	}
	if max > 0 {
		inv := 1 / float32(max)
		for i := range channels {
			channels[i].Normalized = float32(channels[i].Raw) * inv
		}
	}
	mod := a.computeModulation(sum)
	flicker := FlickerStats{
		Frequency:  raw.Flicker.Frequency,
		Valid:      raw.Flicker.Valid,
		Modulation: mod,
		Saturated:  raw.Flicker.Saturated,
		Raw:        raw.Flicker.Raw,
	}
	return Measurement{
		TimestampUs:   raw.Timestamp.UnixMicro(),
		Variant:       raw.Variant.String(),
		IntegrationUs: raw.IntegrationUs,
		Gain:          raw.Gain.Multiplier(),
		Spectrum: Spectrum{
			Channels: channels,
			Sum:      sum,
			Max:      max,
		},
		Flicker:   flicker,
		Saturated: raw.Saturated,
	}
}

func (a *Analyzer) computeModulation(current uint32) float32 {
	prev := a.prevIntensity
	a.prevIntensity = current
	if prev == 0 || current == 0 {
		return 0
	}
	avg := float32(prev+current) / 2
	if avg == 0 {
		return 0
	}
	diff := float32(math.Abs(float64(int64(current) - int64(prev))))
	return diff / avg * 100
}

func safeName(names []string, idx int) string {
	if idx < len(names) {
		return names[idx]
	}
	return "CH" + strconv.Itoa(idx)
}

var channelNames = map[as734x.Variant][]string{
	as734x.VariantAS7341: {
		"F1_405nm",
		"F2_435nm",
		"F3_480nm",
		"F4_515nm",
		"F5_555nm",
		"F6_590nm",
		"F7_630nm",
		"F8_680nm",
		"CLEAR",
		"NIR",
	},
	as734x.VariantAS7343: {
		"FZ_450nm",
		"FY_555nm",
		"FXL_600nm",
		"NIR_855nm",
		"VIS1",
		"FD1",
		"F2_425nm",
		"F3_475nm",
		"F4_515nm",
		"F6_640nm",
		"VIS2",
		"FD2",
		"F1_405nm",
		"F7_690nm",
		"F8_745nm",
		"F5_550nm",
		"VIS3",
		"FD3",
	},
}
