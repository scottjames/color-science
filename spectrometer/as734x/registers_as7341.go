package as734x

const (
	as7341ChipID         = 0x09
	regWhoAmIAS7341      = 0x92
	regEnable            = 0x80
	regATime             = 0x81
	regAStepL            = 0xCA
	regAStepH            = 0xCB
	regCfg1              = 0xAA
	regStatus2AS7341     = 0xA3
	regCh0DataL          = 0x95
	regCfg6              = 0xAF
	regSmuxWriteMask     = 0x18
	regSmuxEnableBit     = 0x10
	regSpectralEnable    = 0x02
	regSmuxEnable        = 0x10
	regFlickerEnable     = 0x40
	regStatus2AValid     = 0x40
	regStatus2Saturation = 0x10
	regFdStatus          = 0xDB
)

const (
	smuxCmdRomReset byte = 0
	smuxCmdRead     byte = 1
	smuxCmdWrite    byte = 2
)
