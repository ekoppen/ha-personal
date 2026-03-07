# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ESP32 Arduino project: a **combination lock** using a 12-LED NeoPixel ring. A spinning pixel acts as a vault dial — press the button three times to stop at positions. If the combination matches the secret code, an HTTP request is sent to Home Assistant. The combination and HA settings are configurable via a web interface served by the ESP32.

Originally built as a Halloween button, now repurposed as an interactive code lock.

## Hardware

- **Board**: ESP32 (uses WiFi + GPIO)
- **Button**: Pin 17, INPUT_PULLUP (active LOW)
- **NeoPixel Ring**: 12 LEDs on pin 16, NEO_GRB + NEO_KHZ800

## Dependencies

- `WiFi.h` (ESP32 core)
- `HTTPClient.h` (ESP32 core)
- `WebServer.h` (ESP32 core)
- `Preferences.h` (ESP32 core — NVS flash storage)
- `Adafruit_NeoPixel` (install via Arduino Library Manager)

## Build & Upload

This is an Arduino IDE / arduino-cli project. The sketch lives in `button-code-lock/button-code-lock.ino`.

```bash
# Compile
arduino-cli compile --fqbn esp32:esp32:esp32 button-code-lock/

# Upload (adjust port as needed)
arduino-cli upload --fqbn esp32:esp32:esp32 --port /dev/cu.usbserial-* button-code-lock/

# Monitor serial output
arduino-cli monitor --port /dev/cu.usbserial-* --config baudrate=115200
```

## Architecture

Single-file sketch built around a **state machine**:

```
IDLE → SPIN_1 → SHOW_1 → SPIN_2 → SHOW_2 → SPIN_3 → EVALUATE
                                                         ↓
                                              SUCCESS or FAIL → IDLE
```

### States

| State | Behavior | Direction |
|-------|----------|-----------|
| `IDLE` | Amber breathing pulse, waits for button | — |
| `SPIN_1` | Pixel spins with trail effect | Clockwise |
| `SHOW_1` | Flash stopped position (0.8s) | — |
| `SPIN_2` | Pixel spins back | Counter-clockwise |
| `SHOW_2` | Flash stopped position (0.8s) | — |
| `SPIN_3` | Pixel spins forward | Clockwise |
| `EVALUATE` | Compare input vs secret code | — |
| `SUCCESS` | Green chase animation + HA call | — |
| `FAIL` | Red flash 3x + fade out | — |

All SPIN states have a 10-second timeout that returns to IDLE.

### Key Functions

| Function | Responsibility |
|----------|---------------|
| `setup()` | WiFi, NeoPixel, button, Preferences, WebServer |
| `loop()` | `server.handleClient()` + state machine dispatch |
| `handleIdle()` | Amber pulse animation, button → SPIN_1 |
| `handleSpin()` | Spinning pixel with trail, timeout, button → stop |
| `handleShow()` | Flash stopped position, pause, advance to next spin |
| `handleEvaluate()` | Compare `inputCode[3]` with `secretCode[3]` |
| `handleSuccess()` | Green animation + `callHomeAssistant()` |
| `handleFail()` | Red flash → fade → IDLE |
| `callHomeAssistant()` | HTTP GET or POST to configurable HA URL |
| `setupWebServer()` | Register routes for config page |
| `handleWebRoot()` | HTML form for code + HA settings |
| `handleWebSave()` | Process form, save to Preferences |
| `loadPreferences()` / `savePreferences()` | NVS read/write |

## Configuration

### Web Interface (runtime)

After boot, the ESP32 serves a config page at `http://<IP>/`. Configure:
- **Combination code**: 3 positions (0–11), each via dropdown
- **Home Assistant URL**: webhook or REST API endpoint
- **Method**: GET or POST
- **Bearer Token**: optional, for REST API auth
- **POST payload**: optional JSON body

Settings are stored in ESP32 NVS flash and persist across reboots.

### Hardcoded (compile-time)

WiFi credentials (`ssid`, `password`) and hardware pins are constants at the top of the `.ino` file. WiFi credentials are in plaintext — keep this in mind when sharing the code.

## NVS Storage

Namespace: `"codelock"`

| Key | Type | Description |
|-----|------|-------------|
| `code0`–`code2` | int | Combination positions |
| `ha_url` | String | Home Assistant URL |
| `ha_method` | String | GET or POST |
| `ha_token` | String | Bearer token |
| `ha_payload` | String | POST body |
