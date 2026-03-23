# Qidi Q2 — G-Code Command Reference (Klippy Extras)

All custom G-code commands registered by the Qidi klippy_extras modules. This covers both the Python source modules and the Cython-compiled .so modules.

---

## Python Modules

### chamber_fan.py — Chamber Fan Control

| Command | Parameters | Description |
|---------|-----------|-------------|
| `TOGGLE_CHAMBER_FAN` | *(none)* | Toggle chamber fan on/off. Fan runs automatically when any linked heater has a target temp, then idles for `idle_timeout` seconds at `idle_speed`. |

Config section: `[chamber_fan <name>]`

---

### color_feeder.py — Color Feeder / Filament Slot Router

| Command | Parameters | Description |
|---------|-----------|-------------|
| `B0` | `T=<int>` | Load filament from slot T. Sets current feed to the named slot, moves stepper 500mm forward. |
| `B1` | `T=<int>` | Smart load: if filament detected and same slot, extrude 1000mm. If different slot, retract with homing. If undetected, home forward 1000mm. |
| `BOX_OUT` | *(none)* | Retract/unload the currently loaded filament (reverse homing move of -800mm). Only acts if filament is detected and a slot is selected. |
| `BOX_MODIFY_LIST` | `KEY=<str>` `VALUE=<str>` | Modify the T-index to slot name mapping at runtime (e.g., `KEY=T0 VALUE=slot_a`). |
| `LOG_BOX_INFO` | *(none)* | Log all slot info (material, color, state) to Klipper log. |

Config section: `[color_feeder]`

---

### feed_slot.py — Feed Slot (per-slot RFID + stepper)

| Command | Parameters | Description |
|---------|-----------|-------------|
| `RFID_READ SLOT=<name>` | `SLOT=<name>` | Read RFID card from the FM17550 NFC reader on the named slot. Returns material, color (hex), and manufacturer ID. Raises error if card unreadable or data < 16 bytes. |

Config section: `[feed_slot <name>]` (uses `load_config_prefix`)

**RFID Data Format:** Byte 0 = material ID (mapped to 50 materials: PLA, ABS, PETG, TPU, etc.), Byte 1 = color ID (mapped to 24 hex colors), Byte 2 = manufacturer ID.

---

### heater_feng.py — Air/Chamber Heater Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `M150` | `S=<float>` | Set air heater temperature target (degrees C). S=0 turns off. |
| `M151` | `S=<float>` | Alias for M150 (same behavior). |
| `M152` | `E=<int>` | Set air heater PWM output directly (bypasses temperature control). |

Config section: `[heater_feng]`

---

### echelon_stepper.py — Echelon Stepper (per-slot stepper motor)

All commands are multiplexed by `STEPPER=<name>`.

| Command | Parameters | Description |
|---------|-----------|-------------|
| `ECHELON_SP STEPPER=<name>` | `STEPPER=<name>` | Set stepper position to zero (reset origin). |
| `ECHELON_QUERY STEPPER=<name>` | `STEPPER=<name>` | Query endstop state for the named stepper. |
| `ECHELON_STEPPER STEPPER=<name>` | `STEPPER=<name>` `MOVE=<float>` `SPEED=<float>` (opt) `ACCEL=<float>` (opt) | Move stepper by MOVE mm. Positive = forward, negative = reverse. Also sets current feed and saves to `/home/mks/color_feeder.json`. |
| `ECHELON_STEPPER_HOMING STEPPER=<name>` | `STEPPER=<name>` `MOVE=<float>` `SPEED=<float>` (opt) `ACCEL=<float>` (opt) `RETRACT=<int>` (opt) `PDI=<int>` (opt) | Home stepper toward endstop. RETRACT: 0=retract by `retract_dist`, 1 or 2=move by PDI after homing. |
| `ECHELON_INVERT STEPPER=<name>` | `STEPPER=<name>` | Invert the endstop logic for the named stepper (toggles `_invert` flag). |

Config section: `[echelon_stepper <name>]` / `[feed_slot <name>]`

---

### closed_loop.py — Closed-Loop Stepper Motor Control (RS485)

All commands are multiplexed by `STEPPER=<name>`. Communicates with closed-loop stepper drivers via RS485 using a custom protocol (sync byte `0xFA`).

| Command | Parameters | Description |
|---------|-----------|-------------|
| `SET_OPERATING_CURRENT STEPPER=<name>` | `STEPPER=<name>` `VALUE=<int>` | Set motor operating current in mA (max 3000). Protocol function `0x83`. |
| `SET_HOMING_CURRENT STEPPER=<name>` | `STEPPER=<name>` `VALUE=<int>` | Set motor homing current in mA. Protocol function `0x93`. |
| `SET_HOMING_STATE STEPPER=<name>` | `STEPPER=<name>` `VALUE=<int>` | Set homing state: 1 = enter homing mode, 2 = exit homing mode. Protocol function `0x55`. |
| `SET_HOMING_MODE STEPPER=<name>` | `STEPPER=<name>` `VALUE=<int>` | Set homing mode. Protocol function `0x56`. |
| `SET_HOMING_TRIGGER_CURRENT STEPPER=<name>` | `STEPPER=<name>` `SV=<int>` `EV=<int>` | Set homing trigger parameters: SV = start value (2 bytes), EV = end value (1 byte). Protocol function `0x51`. |
| `TEST_READ_DATA STEPPER=<name>` | `STEPPER=<name>` | Read data from closed-loop driver (debug). |

Config section: `[closed_loop <name>]`

**RS485 Protocol:** Frame format: `[0xFA] [addr] [function] [data...] [CRC8]`. CRC8 = sum of all preceding bytes mod 256.

---

### autotune_tmc.py — TMC Stepper Driver Auto-Tuning

Multiplexed by `STEPPER=<name>`.

| Command | Parameters | Description |
|---------|-----------|-------------|
| `AUTOTUNE_TMC STEPPER=<name>` | `STEPPER=<name>` `TUNING_GOAL=<str>` (opt) `EXTRA_HYSTERESIS=<int>` (opt) `TBL=<int>` (opt) `TOFF=<int>` (opt) `TPFD=<int>` (opt) `SGT=<int>` (opt) `SG4_THRS=<int>` (opt) `VOLTAGE=<float>` (opt) `OVERVOLTAGE_VTH=<float>` (opt) | Apply autotuning to TMC driver. Re-tunes all parameters on the fly. |

**TUNING_GOAL values:**
- `auto` — Silent for Z, Performance for X/Y (default)
- `silent` — StealthChop at all speeds
- `performance` — SpreadCycle at all speeds
- `autoswitch` — StealthChop at low speed, SpreadCycle when needed (experimental)

**Parameter ranges:**
- `EXTRA_HYSTERESIS`: 0–8
- `TBL`: 0–3
- `TOFF`: 1–15
- `TPFD`: 0–15
- `SGT`: -64–63
- `SG4_THRS`: 0–255
- `VOLTAGE`: 0.0–60.0V
- `OVERVOLTAGE_VTH`: 0.0–60.0V

Config section: `[autotune_tmc <stepper_name>]`

Supported drivers: tmc2130, tmc2208, tmc2209, tmc2240, tmc2660, tmc5160

---

### gcode_shell_command.py — Shell Command Execution

Multiplexed by `CMD=<name>`.

| Command | Parameters | Description |
|---------|-----------|-------------|
| `RUN_SHELL_COMMAND CMD=<name>` | `CMD=<name>` `PARAMS=<str>` (opt) | Run a pre-configured shell command. PARAMS are appended as arguments. Output is streamed to the G-code console if `verbose=true`. Times out after configured `timeout` (default 2s). |

Config section: `[gcode_shell_command <name>]`

---

### motor_constants.py — Motor Constants Database

No G-code commands registered. Provides motor specifications (resistance, inductance, holding torque, steps/rev, max current) used by `autotune_tmc`.

Config section: `[motor_constants <motor_name>]`

---

### heater_air.py / probe_air.py / box_heater_fan.py — Thin Wrappers

These files are thin wrappers that delegate to compiled .so modules:
- `heater_air.py` → loads `heater_air_core.so` (PrinterAirHeater)
- `probe_air.py` → loads `air.so` (PrinterAirProbe)
- `box_heater_fan.py` → No G-code commands (timer-based fan control for Box heaters, same pattern as `chamber_fan.py`)

---

## Cython-Compiled .so Modules

Commands extracted via reverse engineering (radare2 decompilation). See [klippy_extras_analysis.md](klippy_extras_analysis.md) and the [detailed reports](klippy_extras_decompiled/) for full analysis.

### box_extras.so — Core Box Management

#### Filament Operations

| Command | Parameters | Description |
|---------|-----------|-------------|
| `CUT_FILAMENT` | *(none)* | Cut filament. Runs: `CUT_FILAMENT_1` → `MOVE_TO_TRASH` → `M83` → `G1 E-60 F300` (60mm retract at 300mm/min). |
| `CLEAR_FLUSH` | *(none)* | Clear flush bucket/wiper after purge. |
| `CLEAR_OOZE` | *(none)* | Clear nozzle ooze. Oscillates X98–X115 at F4000/F8000 across brush (5 passes). |
| `TIGHTEN_FILAMENT` | *(none)* | Tighten filament tension in feed path after slot change. |
| `RELOAD_ALL` | *(none)* | Reload all filament slots. Iterates all slots, reloads each. |
| `AUTO_RELOAD_FILAMENT` | *(none)* | Auto-reload filament after runout. Runs: `DISABLE_ALL_SENSOR` → `_CG28` → `MOVE_TO_TRASH` → `M109 S{hotendtemp}`. On failure: error `QDE_004_023`. |
| `CLEAR_RUNOUT_NUM` | *(none)* | Reset the filament runout event counter. |

#### Drying System

| Command | Parameters | Description |
|---------|-----------|-------------|
| `ENABLE_BOX_DRY` | Box number (positional) | Start drying for a specific Box unit. Validates box number (error: "!!Invalid BOX number. Available: 1-N"). Registers `heating_handler` timer. Sends `SET_HEATER_TEMPERATURE HEATER=heater_box TARGET=<temp>`. Reads presets from `officiall_filas_list.cfg`. |
| `DISABLE_BOX_DRY` | Box number (positional) | Stop drying. Unregisters heating timer. Sets heater target to 0. |
| `DISABLE_BOX_HEATER` | *(none)* | Turn off box heater directly. |

#### Tool Change

| Command | Parameters | Description |
|---------|-----------|-------------|
| `TOOL_CHANGE_START` | `SLOT=<int>` `TEMP=<float>` (inferred) | Begin filament swap. Records position, determines unload/load slots. 3 modes: **load-only** (`MOVE_TO_TRASH` → `M109 S{temp}` → `EXTRUDER_LOAD`), **unload+load** (adds `EXTRUDER_UNLOAD`), **cut+unload+load** (adds `CUT_FILAMENT`). |
| `TOOL_CHANGE_END` | *(none)* | Complete tool change. Purge: `G1 E150 F300` → `M106 S255` → `G4 P5000` → `CLEAR_OOZE` → `CLEAR_FLUSH`. Then wipe: oscillating X/Y moves across brush. Post-wipe: `G1 E-4 F1800` retract. Restores position. |
| `CLEAR_TOOLCHANGE_STATE` | *(none)* | Reset tool change state machine. |

#### Buffer / Stepper

| Command | Parameters | Description |
|---------|-----------|-------------|
| `BUFFER_MONITORING` | `ENABLE=<0\|1>` | Enable/disable continuous buffer monitoring during printing. Error hint: "intput buffer state 'ENABLE= 1/0'". Starts `_buffer_response_timer` when enabled. |
| `INIT_BUFFER_STATE` | *(none)* | Initialize buffer monitoring state. Validates box enabled and slot selected. Error: "Box disabled or no slot selected, cannot init buffer state." |
| `INIT_SYNC_BUFFER_STATE` | *(none)* | Synchronize buffer state on initialization. |
| `RUN_STEPPER` | `STEPPER=<name>` `distance` `speed` (inferred) | Directly control a box stepper motor. Looks up stepper by name, executes `do_move`. |
| `SET_INIT_ROTATION_DISTANCE` | *(none)* | Set initial extruder rotation distance for box stepper calibration. |

#### Print Management

| Command | Parameters | Description |
|---------|-----------|-------------|
| `BOX_PRINT_START` | `SLOT=<int>` `HOTENDTEMP=<float>` `TEMP=<float>` | Initialize box for a print. Checks/disables active drying, sets slot mapping, may run `INIT_RFID_READ`, runs `INIT_BUFFER_STATE` + `INIT_SYNC_BUFFER_STATE`. |
| `TRY_RESUME_PRINT` | *(none)* | Resume print after filament error/pause. Validates filament loaded, runs `BUFFER_MONITORING ENABLE=1`, then `RESUME_PRINT` macro. On failure: `M118 Printer resume failed`. |
| `RESUME_PRINT_1` | *(none)* | Secondary resume handler with position restoration and load/purge sequence. Outputs `M118 box check finish` on success. |
| `RETRY` | `retry_step` (inferred) | Retry a failed operation. Parses step name with regex `([a-zA-Z_]+)(\d+)_(\d+)$`. Error: "Invalid retry_step format" / "No step to retry". |
| `INIT_MAPPING_VALUE` | *(none)* | Initialize filament-to-slot mapping. |

#### RFID

| Command | Parameters | Description |
|---------|-----------|-------------|
| `INIT_RFID_READ` | *(none)* | Trigger RFID tag reading for filament identification. Calls `start_rfid_read` on `box_rfid`. |

#### Sensor Control

| Command | Parameters | Description |
|---------|-----------|-------------|
| `DISABLE_ALL_SENSOR` | *(none)* | Disable all filament sensors. Referenced in auto-reload pre-sequence. |

---

### box_stepper.so — Filament Feeding

All commands are multiplexed by slot (registered via `register_mux_command`).

| Command | Parameters | Description |
|---------|-----------|-------------|
| `SLOT_UNLOAD` | `SLOT=<name>` | Unload filament from slot back to spool. Checks extruder unloaded first (else `QDE_004_004`). Uses `slot_unload_length_1` with configured speed/accel. Verifies via `b_endstop`. On failure: `QDE_004_003`. |
| `EXTRUDER_LOAD` | `SLOT=<name>` | Load filament from hub into extruder. 3-stage load (`extruder_load_length_1/2/3`). Checks wrapping (`QDE_004_013`), slot loaded (`QDE_004_005`), not already loaded (`QDE_004_002`). May run `shake_for_load_toolhead` (toolhead oscillation Y:200↔70, X same, at 500mm/s while extruding ~30mm). On failure: `QDE_004_006`. |
| `EXTRUDER_UNLOAD` | `SLOT=<name>` | Unload filament from extruder to hub. 2-stage unload (`extruder_unload_length_1/2`). May run `shake_for_unload_toolhead`. Multiple failure codes: `QDE_004_008`, `QDE_004_009`, `QDE_004_025`. Embedded G-code: `G1 E-10 F300` (tip-shape retract). |
| `SLOT_PROMPT_MOVE` | *(unknown)* | Manual/prompted filament move (user-initiated via UI). |
| `SLOT_RFID_READ` | *(unknown)* | Read RFID tag on filament spool in slot. Uses `box_rfid` interface. |

**Internal commands used by box_stepper (not directly user-invoked):**
- `slot_load` — 4-stage slot loading (`slot_load_length_1/2/3/4`), homing against `b_endstop`. On failure: `QDE_004_001`.
- `flush_all_filament` — Purge sequence: `G1 E150 F300` → `G1 E-2 F1800` → `M106 S255` → `G4 P5000` → `M106 S0` → `CLEAR_FLUSH` (×2). On failure: `QDE_004_017`.
- `switch_next_slot` — Auto slot switch. Priority: `next_filament_slot` > `next_color_slot` > `next_vendor_slot`. No replacement: `QDE_004_022`.

---

### heater_air_core.so — Air/Chamber Heater

| Command | Parameters | Description |
|---------|-----------|-------------|
| `SET_AIR_TEMPERATURE` | `TARGET=<float>` (default 0) | Set air/chamber heater temperature target. Validates against `min_temp`/`max_temp` range (error: "Requested temperature (%.1f) out of range (%.1f:%.1f)"). TARGET=0 turns off. Also enables heater via `set_en(True)`. |
| `TURN_OFF_HEATERS` | *(none)* | Turn off all registered air heaters. Sets target temperature to 0 for every heater. |

---

### air.so — Weight Probe

| Command | Parameters | Description |
|---------|-----------|-------------|
| `WEIGH_CALIBRATE` | *(standard Klipper probe params)* | Calibrate weight probe. Help: "Calibrate weigh probe". Runs manual probe to establish Z=0 reference, then automated moves through multiple Z heights collecting frequency readings. Builds frequency-to-height curve via `bisect` + linear interpolation. Errors: "Failed calibration - frequency not increasing each step", "Failed calibration - incomplete sensor data". |

---

### cs1237.so — CS1237 ADC Weight Sensor

| Command | Parameters | Description |
|---------|-----------|-------------|
| `CS1237_WEIGHT_BEGIN` | *(none)* | Start weight measurement acquisition. Configures CS1237 ADC and begins data streaming. |
| `CS1237_ZERO_DEBUG` | *(none)* | Display zero/tare calibration value. Output: `WEIGHT:CS1237 ZERO:%.3f`. |
| `CS1237_TEST` | *(none)* | Test CS1237 sensor communication. |
| `WEIGHTING_CONFIG_READ` | *(none)* | Read CS1237 hardware configuration register. Output includes config hex value. Status messages in Chinese: 传感器配置成功/失败 (sensor config success/failure). |
| `WEIGHTING_DEBUG_QUERY` | *(none)* | Debug query for raw weight sensor data. Shared command name with HX711. |
| `WEIGHTING_DEBUG_ZERO_DATA` | *(none)* | Debug: display zero calibration data. |

MCU protocol: `config_cs1237 oid=%d dout_pin=%s sclk_pin=%s`. Homing via trsync: `cs1237_setup_home oid=%c clock=%u threshold=%u trsync_oid=%c trigger_reason=%c error_reason=%c`.

---

### hx711.so — HX711 ADC Weight Sensor

| Command | Parameters | Description |
|---------|-----------|-------------|
| `WEIGHT_TARGET` | *(target value)* | Set target weight value for monitoring/triggering. |
| `WEIGHTING_START_QUERY` | *(none)* | Start continuous weight data streaming. |
| `WEIGHTING_END_QUERY` | *(none)* | Stop continuous weight data streaming. Output: "HX711 end query!". |
| `WEIGHTING_DEBUG_QUERY` | *(none)* | Debug query for raw weight data. Output: `HX711_Info: %d/0x%x(origin) / %.6f(ENOB)`. Error: "HX711_Info:Data error!". |

MCU protocol: `config_hx711 oid=%d dout_pin=%s sclk_pin=%s`. Homing via trsync: `hx711_setup_home oid=%c clock=%u threshold=%u trsync_oid=%c trigger_reason=%c error_reason=%c`.

---

### aht20_f.so — AHT20 Temp/Humidity Sensor

| Command | Parameters | Description |
|---------|-----------|-------------|
| `BOX_TEMP_READ` | (multiplexed by sensor name) | Read temperature and humidity from AHT20 I2C sensor. Output: `temperature: %.3f, humidity: %.3f`. Validates CRC-8. Retries on busy (max cycles then reset). Error: "AHT20_F temperature outside range". |

I2C address: `0x38` (standard AHT20). Command registers: MEASURE, RESET, SYS_CFG, AFE_CFG, OTP_AFE, OTP_CCP, CCP_CCN, INDEX.

---

### box_detect.so — Box Auto-Detection

No user-invocable G-code commands registered. Internally uses:

| Internal Command | Description |
|-----------------|-------------|
| `SAVE_VARIABLE VARIABLE=box_count VALUE=<N>` | Persists detected Box count (0-4) to `saved_variables.cfg`. |

Detection: scans `/dev/serial/by-id/` via pyudev for `Virtual_ComPort`, `QIDI_BOX_V1`, `QIDI_BOX_V2`. Auto-upgrades V1→V2 via `/home/mks/mcu_update_BOX_to_v2.sh`.

---

### box_rfid.so — FM17550 NFC/RFID Reader

No direct user-invocable G-code commands (used internally by `box_extras` and `box_stepper`). The FM17550 chip is accessed via SPI.

| Internal Method | Description |
|----------------|-------------|
| `read_card` | Single card read via `fm17550_read_card` MCU command. Returns status + raw data bytes. |
| `read_card_from_slot` | Read card from specific slot (positions stepper first). |
| `start_rfid_read` | Start continuous RFID reading with timeout via timer. |
| `stop_read` | Cancel continuous reading. |

Data extracted from NFC tags: filament type, color, vendor, temperature profiles (`temp_message_1`, `temp_message_2`). Errors: "Unrecognized label read in %s", "%s did not recognize the filament".

---

### buttons_irq.so — IRQ Button Handler

No user-invocable G-code commands. Provides hardware interrupt-driven button input.

MCU protocol: `config_irq_button oid=%d pin=%s pull_up=%d debounce_us=%d invert=%d`. State changes reported via `irq_button_state`, acknowledged via `irq_button_ack oid=%c count=%c`. Constraint: all pins in a group must be on the same MCU.

---

## Error Code Reference (from .so modules)

### box_stepper.so Errors

| Code | Severity | Message | Trigger |
|------|----------|---------|---------|
| `QDE_004_001` | Fatal | Slot loading failure, please check the trigger, please reload %s | `slot_load` |
| `QDE_004_002` | Fatal | Extruder has been loaded, cannot load %s | `EXTRUDER_LOAD` |
| `QDE_004_003` | Fatal | Slot unloading failure, please unload %s again | `SLOT_UNLOAD` |
| `QDE_004_004` | Fatal | Please unload extruder first | `SLOT_UNLOAD` |
| `QDE_004_005` | Warning | Please load the filament to %s first | `EXTRUDER_LOAD` |
| `QDE_004_006` | Warning | Extruder loading failure | `EXTRUDER_LOAD` |
| `QDE_004_007` | Warning | Extruder not loaded | `EXTRUDER_UNLOAD` |
| `QDE_004_008` | Warning | Extruder unloading failure (retry prompt) | `EXTRUDER_UNLOAD` |
| `QDE_004_009` | Warning | Extruder unloading failure (retry prompt) | `EXTRUDER_UNLOAD` |
| `QDE_004_011` | Warning | Detected that filament have been loaded, please unload first | `EXTRUDER_LOAD` |
| `QDE_004_013` | Warning | Detected wrapping filament, please check | `EXTRUDER_LOAD` |
| `QDE_004_016` | Warning | Filament exhausted, please load to %s | `runout_button_callback` |
| `QDE_004_017` | Warning | Filament flush failed | `flush_all_filament` |
| `QDE_004_018` | Warning | No filament specified, cannot auto-replace %s | `switch_next_slot` |
| `QDE_004_019` | Fatal | Please check if your PTFE Tube is bent | Various |
| `QDE_004_020` | Fatal | Detected filament unloaded, please reload | `runout_button_callback` |
| `QDE_004_022` | Warning | No replaceable slot found | `switch_next_slot` |
| `QDE_004_025` | Warning | Extruder unloading failure (retry prompt) | `EXTRUDER_UNLOAD` |

### box_extras.so Errors

| Code | Severity | Message | Trigger |
|------|----------|---------|---------|
| `QDE_004_010` | Fatal | The current feeding status is incorrect. Please exit the filament from the extruder. | Various |
| `QDE_004_013` | Warning | Detected wrapping filament, please check the filament. | `AUTO_RELOAD_FILAMENT` |
| `QDE_004_014` | Warning | Parameter setting error, please reset. | Various |
| `QDE_004_021` | Fatal | Unable to recognize loaded filament. | `AUTO_RELOAD_FILAMENT` |
| `QDE_004_023` | Warning | Auto reload failed. | `AUTO_RELOAD_FILAMENT` |

---

## Material ID Mapping (from feed_slot.py)

| ID | Material | ID | Material | ID | Material |
|----|----------|----|----------|----|----------|
| 1 | PLA | 18 | ASA | 37 | PET-CF |
| 2 | PLA Matte | 19 | ASA-AERO | 38 | PET-GF |
| 3 | PLA Metal | 24 | PA | 41 | PETG |
| 4 | PLA Silk | 25 | PA-CF | 44 | PPS-CF |
| 5 | PLA-CF | 30 | PAHT-CF | 47 | PVA |
| 6 | PLA-Wood | 31 | PAHT-GF | 50 | TPU |
| 11 | ABS | 34 | PC/ABS-FR | | |
| 12 | ABS-GF | | | | |
| 13 | ABS-Metal | | | | |

## Color ID Mapping (from feed_slot.py)

| ID | Hex | ID | Hex | ID | Hex |
|----|-----|----|-----|----|-----|
| 1 | #FAFAFA (White) | 9 | #228332 (Green) | 17 | #FE717A (Pink) |
| 2 | #060606 (Black) | 10 | #99DEFF (Light Blue) | 18 | #FF362D (Red) |
| 3 | #D9E3ED (Silver) | 11 | #1714B0 (Navy) | 19 | #E2DFCD (Cream) |
| 4 | #5CF30F (Lime) | 12 | #CEC0FE (Lavender) | 20 | #898F9B (Gray) |
| 5 | #63E492 (Mint) | 13 | #CADE4B (Yellow-Green) | 21 | #6E3812 (Brown) |
| 6 | #2850FF (Blue) | 14 | #1353AB (Dark Blue) | 22 | #CAC59F (Tan) |
| 7 | #FE98FE (Magenta) | 15 | #5EA9FD (Sky Blue) | 23 | #F28636 (Orange) |
| 8 | #DFD628 (Yellow) | 16 | #A878FF (Purple) | 24 | #B87F2B (Gold) |
