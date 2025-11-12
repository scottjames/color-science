module github.com/itohio/color-science/spectrometer

go 1.25.3

require (
	github.com/itohio/tinygui v0.0.0
	tinygo.org/x/drivers v0.31.0
	tinygo.org/x/tinyfont v0.6.0
)

require github.com/google/shlex v0.0.0-20191202100458-e7afc7fbc510 // indirect

replace github.com/itohio/tinygui => ../../tinygui
