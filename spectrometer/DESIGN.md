## Spectrometer Firmware Design

### Goal
- Build firmware for ESP32-based spectrometer using the AMS AS7341/AS7343 spectral sensors (auto-detect at runtime).
- Provide a reusable TinyGo driver family for the AS7341/AS7343 that follows TinyGo device idioms (explicit configuration, zero-value usability, minimal heap use).
- Stream spectral channel readings and flicker statistics over UART for ingestion by a host Python script.
- Show a simple "Running" status on an attached display driven through the local `tinyui` (TinyGUI) work-in-progress library.

### Scope & Non-Goals
- **In scope:** I2C communication with AS7341, sensor configuration, spectral channel acquisition, basic statistical post-processing (per-channel lux, normalized spectrum), flicker detection (frequency estimation, modulation depth), UART serialization (newline-delimited JSON), minimal display status.
- **Out of scope:** Rich on-device UI, persistent storage, calibration routines, dynamic configuration via UI, non-UART transports, advanced flicker waveform reconstruction.

### High-Level Architecture
1. **Drivers (`as734x` package):**
   - Provide a common `Device` struct with chip metadata detected via `WHOAMI`.
   - Expose `Configure`, `ReadSpectral`, and `ReadFlicker` methods with chip-specific SMUX profiles.
   - Abstract register access behind small helpers (`writeRegister`, `readRegister`, `readSequence`, etc.).
   - Support both hardware `machine.I2C` and custom `i2c.I2C` implementations via a minimal bus interface.

2. **Analysis (`analysis` package):**
   - Convert raw counts to calibrated values using integration time and gain.
   - Compute flicker stats (dominant frequency classification from AS7341 flicker engine, modulation percentage from channel deltas).
   - Bundle measurements into typed structs ready for serialization.

3. **Runtime (`main`):**
   - Initialise pins using ESP32/M5StickC configuration similar to `FishFeeder`.
   - Setup software I2C bus (re-using local `i2c` package) to communicate with AS7341.
   - Launch goroutines for:
     - Periodic sensor sampling (spectral + flicker).
     - UART writer that streams JSON lines to host.
     - Display heartbeat using `tinyui` container that prints "Running".
   - Provide graceful error logging via UART.

4. **Display (`tinyui` integration):**
   - Use local TinyGUI (aliased as `tinyui`) with a static layout.
   - Display stays minimal per current requirements.

### Data Flow
```
[I2C Bus] → [AS734X Driver] → [Analysis] → [Measurement Struct]
      ↘                                 ↘
       [Flicker Engine Registers]        ↘
                ↘                         ↘
          [Flicker Stats]            [UART Encoder] → UART → Host Python Script
                                           ↘
                                    [Display Status]
```

### Configuration & Build
- Target board: ESP32 (M5StickC-style pinout).
- Build command: `tinygo build -target=m5stick-c`.
- Flashing: mirror `FishFeeder` workflow using `esptool`.
- Ensure `go.mod` uses local replace directive for the WIP `tinyui` library.

### Open Questions
1. Calibration constants for channel conversion – rely on datasheet defaults or expose via constants per chip variant?
2. Required sampling cadence and averaging depth for stable flicker stats?
3. UART protocol framing – is newline-delimited JSON acceptable for the Python host?
4. Should we expose runtime configuration over UART in the future?


