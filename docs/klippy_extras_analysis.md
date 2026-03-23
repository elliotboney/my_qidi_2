# Qidi Q2 — Klippy Extras .so Module Analysis

All 10 `.so` files are **Cython-compiled CPython 3.9 extension modules** targeting aarch64 (ARM64 Linux). All contain debug info and are not stripped, making analysis feasible.

Source path prefix embedded in binaries: `extras/` (e.g., `extras/box_extras.pyx`)

---

## Module Index

| File | Size | Classes | Purpose |
|------|------|---------|---------|
| `box_extras.so` | 4.7M | BoxExtras, BoxEndstop, ToolChange, BoxButton, BoxOutput | Core Box management, drying, tool changes |
| `box_stepper.so` | 3.0M | BoxExtruderStepper | Filament feeding, slot load/unload, runout |
| `box_detect.so` | 1.8M | BoxDetect | Auto-detect Box units via USB serial |
| `air.so` | 1.6M | PrinterAirProbe, WeighCalibration, WeighEndstopWrapper, WeighGatherSamples, WeighDriftCompensation | Weight-based probing system |
| `heater_air_core.so` | 1.5M | Heater_air, PrinterAirHeater, AIR_ControlBangBang | Air/chamber heater control |
| `cs1237.so` | 995K | CS1237, CS1237Command | CS1237 ADC weight sensor driver |
| `aht20_f.so` | 968K | AHT20_F | AHT20 I2C temp/humidity sensor |
| `hx711.so` | 737K | HX711, HX711Command | HX711 load cell ADC driver |
| `buttons_irq.so` | 596K | _IRQButtonMCU, MCU_irq_button | IRQ-based button input handler |
| `box_rfid.so` | 559K | BoxRFID | RFID filament tag reader |

---

## Detailed Module Breakdown

### box_extras.so — Core Box Management

The largest and most complex module. Manages the Qidi Box multi-material system including filament operations, drying, button handling, RFID, and tool changes.

**Class: `BoxExtras`** (47+ methods)

Filament Operations:
- `cmd_RELOAD_ALL` — Reload all filament slots
- `cmd_AUTO_RELOAD_FILAMENT` — Auto-reload filament
- `cmd_CUT_FILAMENT` — Cut filament
- `cmd_CLEAR_FLUSH` — Clear flush state
- `cmd_CLEAR_OOZE` — Clear ooze state
- `cmd_TIGHTEN_FILAMENT` — Tighten filament in tube
- `cmd_CLEAR_RUNOUT_NUM` — Reset runout counter

Drying System:
- `cmd_ENABLE_BOX_DRY` — Start drying cycle
- `cmd_DISABLE_BOX_DRY` — Stop drying cycle
- `heating_handler` — Temperature control loop for drying
- `set_box_temp` — Set Box heater target temperature
- `cmd_disable_box_heater` — Turn off Box heater
- `get_temp_by_slot`, `get_temp_by_num`, `get_box_temp_by_slot` — Temperature queries

Button Handling:
- `b_button_callback` — Box button press handler
- `buffer_button_callback` — Buffer sensor button callback
- `button_extruder_load` — Button-triggered extruder load
- `button_extruder_unload` — Button-triggered extruder unload
- `button_box_unload` — Button-triggered Box unload

Print Management:
- `cmd_BOX_PRINT_START` — Initialize Box for a print
- `cmd_TRY_RESUME_PRINT` — Attempt to resume print after error
- `cmd_RESUME_PRINT_1` — Resume print continuation
- `cmd_INIT_MAPPING_VALUE` — Initialize filament slot mapping

Buffer/Stepper:
- `cmd_BUFFER_MONITORING` — Monitor buffer sensor state
- `cmd_INIT_BUFFER_STATE` — Initialize buffer state
- `cmd_RUN_STEPPER` — Run Box stepper motor
- `init_sync_buffer_state` — Sync buffer state on init
- `set_init_rotation_distance` — Set initial rotation distance
- `call_set_rotation_distance` — Update rotation distance
- `_buffer_response_timer` — Timer for buffer monitoring

RFID:
- `cmd_INIT_RFID_READ` — Start RFID read sequence
- `delayed_init_rfid` — Delayed RFID initialization

Initialization:
- `handle_connect` — Connection handler
- `delayed_init_error_raw` — Delayed error init
- `update_b_endstop`, `update_e_endstop` — Update endstop states
- `get_dis_dif`, `get_e_dis` — Distance calculations

Status:
- `get_status` — Report status to Fluidd/Moonraker
- `save_variable` — Persist variables
- `get_value_by_key`, `get_key_by_value`, `search_index_by_value` — Variable lookups
- `print_sensor_state_to_log` — Log sensor states

**Class: `ToolChange`**
- `cmd_TOOL_CHANGE_START` — Begin tool change sequence
- `cmd_TOOL_CHANGE_END` — End tool change sequence
- `cmd_CLEAR_TOOLCHANGE_STATE` — Reset tool change state
- `get_position`, `move` — Position tracking during tool change

**Class: `BoxEndstop`** — Endstop wrapper for Box
- `add_stepper`, `get_endstops`, `set_scram`

**Class: `BoxButton`** — Button configuration holder

**Class: `BoxOutput`** — Pin output control
- `set_pin` — Set output pin value

---

### box_stepper.so — Filament Feeding Stepper

Controls the stepper motors in each Box slot for filament feeding, unloading, and slot switching.

**Class: `BoxExtruderStepper`**

Motion:
- `do_move` — Execute stepper move
- `dwell` — Timed pause
- `drip_move` — Slow drip feed move
- `sync_print_time` — Sync with print timing
- `disable_stepper` — Disable stepper motor
- `_calc_endstop_rate` — Calculate endstop check rate

Homing:
- `do_home` — Home the stepper
- `get_mcu_endstops` — Get MCU endstop references
- `multi_complete` — Multi-axis completion handler

Slot Operations:
- `slot_load` — Load filament from slot
- `cmd_SLOT_UNLOAD` — Unload filament from slot
- `cmd_EXTRUDER_LOAD` — Load filament into extruder
- `cmd_EXTRUDER_UNLOAD` — Unload filament from extruder
- `cmd_SLOT_PROMPT_MOVE` — Prompt-based slot move
- `slot_sync` — Sync slot state
- `flush_all_filament` — Flush all filament from tubes
- `switch_next_slot` — Switch to next filament slot
- `cmd_SLOT_RFID_READ` — Read RFID during slot operation

Buffer/Runout:
- `runout_button_callback` — Filament runout detection
- `init_buffer_state` — Initialize buffer sensor state

LED:
- `set_led` — Control slot LED indicator
- `led_handle_connect` — LED initialization on connect

Status:
- `get_status` — Report slot status

Key variables: `filament_slot`, `color_slot`, `next_slot`, `next_color_slot`, `next_filament_slot`, `next_vendor_slot`, `slot_load_length_1`, `slot_load_length_1_accel`, `can_load_slot`, `last_load_slot`, `filament_present`, `rfid_state`, `rfid_device`, `auto_reload_detect`, `check_wrapping_filament_state`

---

### box_detect.so — Box Auto-Detection

Detects Qidi Box units connected via USB serial and dynamically updates printer configuration.

**Functions:**
- `monitor_serial_devices` — Scan for new serial devices (uses generator expressions)
- `is_monitor_config_file_empty` — Check if monitoring config exists
- `update_monitor_config_file` — Write discovered Box config
- `add_printer_objects` — Register detected Boxes with Klipper

**Class: `BoxDetect`**
- `_handle_ready` — Ready event handler
- `get_config_mcu_serials` — Get configured MCU serial paths
- `monitor_serial_by_id` — Monitor specific serial device by ID
- `_update_config_file` — Update config with new Box
- `_request_restart` — Request Klipper restart after config change
- `get_check_serials_id` — Get serial IDs to monitor
- `count_box_includes` — Count `[include box%d.cfg]` lines

Key variables: `box_count`, `box_index`, `box_name`, `mcu_box`, `dst_box_cfg`, `src_box_cfg_with_0` through `src_box_cfg_with_4`

G-code: `SAVE_VARIABLE VARIABLE=box_count`

---

### air.so — Weight-Based Probe System

Implements a weight/force-based Z-probe using load cell sensors (CS1237/HX711). This is Qidi's alternative to BLTouch/inductive probes.

**Class: `PrinterAirProbe`** — Main probe interface
- `add_client`, `get_probe_params`, `get_offsets`, `get_status`, `start_probe_session`, `register_drift_compensation`

**Class: `WeighCalibration`** — Probe calibration
- `set_target_adc_value` — Set ADC target for trigger
- `is_calibrated`, `load_calibration`, `apply_calibration`
- `freq_to_height`, `height_to_freq` — Frequency/height conversion
- `do_calibration_moves` — Run calibration sequence
- `calc_freqs` — Calculate frequency values
- `post_manual_probe` — Post manual probe callback
- `cmd_WEIGH_CALIBRATE` — G-code calibration command
- `register_drift_compensation`

**Class: `WeighEndstopWrapper`** — Endstop interface for probing
- `get_mcu`, `add_stepper`, `get_steppers`
- `home_start`, `home_wait`, `home_zero`, `home_check`
- `query_endstop`, `probing_move`
- `multi_probe_begin`, `multi_probe_end`
- `probe_prepare`, `probe_finish`
- `get_position_endstop`

**Class: `WeighGatherSamples`** — Sample collection
- `_add_measurement`, `finish`, `_await_samples`
- `_lookup_toolhead_pos`, `note_probe`, `note_probe_and_position`

**Class: `WeighDriftCompensation`** — Temperature drift correction
- `get_temperature`, `note_z_calibration_start/finish`
- `adjust_freq`, `unadjust_freq`

---

### heater_air_core.so — Air/Chamber Heater Control

Manages the chamber/air heater system with bang-bang control.

**Class: `Heater_air`** — Individual air heater
- `set_en` — Enable/disable heater
- `set_pwm` — Set PWM output
- `temperature_callback` — Temp reading callback
- `_handle_shutdown` — Emergency shutdown handler
- `get_name`, `get_pwm_delay`, `get_max_power`, `get_smooth_time`
- `set_temp`, `get_temp`, `check_busy`, `set_control`, `alter_target`
- `stats` — Heater statistics
- `get_status` — Status for Fluidd
- `cmd_SET_AIR_TEMPERATURE` — G-code command

**Class: `PrinterAirHeater`** — Heater manager
- `load_config`, `add_sensor_factory`, `setup_heater`, `setup_sensor`
- `get_all_heaters`, `lookup_heater`, `register_sensor`, `register_monitor`
- `set_temperature`, `set_air_output`, `_get_temp`, `_wait_for_temperature`
- `turn_off_all_heaters`, `cmd_TURN_OFF_HEATERS`
- `_handle_ready`, `get_status`

**Class: `AIR_ControlBangBang`** — Bang-bang controller
- `temperature_update`, `check_busy`

Key variables: `air_pin`, `heater_max_power`, `mini_air_temp`, `available_heaters`, `available_sensors`, `have_load_sensors`

---

### cs1237.so — CS1237 ADC Driver

Driver for the Chipsea CS1237 24-bit ADC, used for the weight/force sensor.

**Class: `CS1237`**
- `_handle_ready`, `_build_config`, `get_mcu`
- `setup_home`, `clear_home`, `zero_home`
- `check_cs1237_zero` — Zero calibration check

**Class: `CS1237Command`** — G-code interface
- `register_commands`
- `cmd_WEIGHTING_CONFIG_READ` — Read ADC config
- `cmd_WEIGHTING_DEBUG_QUERY` — Debug query
- `cmd_CS1237_WEIGHT_BEGIN` — Start weight measurement
- `cmd_CS1237_ZERO_DEBUG` — Zero debug
- `cmd_CS1237_TEST` — Test command

Uses `bulk_sensor` interface for data streaming.

---

### aht20_f.so — AHT20 Temperature/Humidity Sensor

Driver for AHT20 I2C temperature and humidity sensor, used inside the Qidi Box for monitoring filament environment.

**Class: `AHT20_F`**
- `handle_connect` — I2C connection setup
- `setup_minmax` — Configure temp limits
- `setup_callback` — Register data callback
- `get_report_time_delta` — Reporting interval
- `cmd_READ_TEMP_RH` — Read temp and humidity (G-code: `BOX_TEMP_READ`)
- `check_crc8` — CRC8 data validation
- `_make_measurement` — Trigger measurement
- `_reset_device` — Reset sensor
- `_init_aht20_f` — Initialize sensor
- `_sample_aht20_f` — Read sensor data
- `get_status` — Report temp/humidity

Key variables: `humidity`, `temperature`, `i2c`, `bus`, `default_addr`, `default_speed`, `report_time`, `init_sent`, `cycles`

Error messages: "AHT20_F temperature outside range", "device reported busy after %d cycles, resetting device", "received bytes less than expected"

---

### hx711.so — HX711 ADC Driver

Driver for the HX711 24-bit ADC, alternative load cell amplifier to CS1237.

**Class: `HX711`**
- `_build_config`, `get_mcu`
- `setup_home`, `clear_home`, `zero_home`

**Class: `HX711Command`** — G-code interface
- `register_commands`
- `cmd_WEIGHT_TARGET` — Set weight target
- `cmd_WEIGHTING_START_QUERY` — Start weight query
- `cmd_WEIGHTING_DEBUG_QUERY` — Debug query
- `cmd_WEIGHTING_END_QUERY` — End weight query

Uses `bulk_sensor` interface for data streaming.

---

### buttons_irq.so — IRQ Button Handler

Low-level button input handler using hardware interrupts instead of polling.

**Class: `_IRQButtonMCU`** — MCU-level IRQ button
- `setup_buttons` — Configure button pins
- `_build_config` — Build MCU config
- `_handle_state` — Process button state change (with lambda callback)

**Class: `MCU_irq_button`** — High-level button interface
- `register_buttons` — Register button callbacks

---

### box_rfid.so — RFID Filament Tag Reader

Reads RFID tags on Qidi filament spools to identify material type, color, and vendor.

**Class: `BoxRFID`**
- `_build_config` — MCU config for RFID hardware
- `read_card` — Read RFID card data
- `read_card_from_slot` — Read card in specific slot
- `_schedule_rfid_read` — Schedule periodic RFID reads
- `start_rfid_read` — Start reading
- `stop_read` — Stop reading

Key variables: `filament`, `stepper`, `stepper_label`, `stepper_name`, `rfid_read_attempts`, `rfid_read_start_time`, `read_rfid_timer`

Config prefix loader: `load_config_prefix` (supports multiple Box RFID instances)

---

## G-Code Commands Summary

| Command | Module | Description |
|---------|--------|-------------|
| `RELOAD_ALL` | box_extras | Reload all filament slots |
| `AUTO_RELOAD_FILAMENT` | box_extras | Auto-reload filament |
| `CUT_FILAMENT` | box_extras | Cut filament |
| `CLEAR_FLUSH` | box_extras | Clear flush state |
| `CLEAR_OOZE` | box_extras | Clear ooze state |
| `TIGHTEN_FILAMENT` | box_extras | Tighten filament |
| `ENABLE_BOX_DRY` | box_extras | Start drying |
| `DISABLE_BOX_DRY` | box_extras | Stop drying |
| `BUFFER_MONITORING` | box_extras | Monitor buffer |
| `INIT_BUFFER_STATE` | box_extras | Init buffer state |
| `RUN_STEPPER` | box_extras | Run Box stepper |
| `INIT_RFID_READ` | box_extras | Start RFID read |
| `CLEAR_RUNOUT_NUM` | box_extras | Reset runout counter |
| `BOX_PRINT_START` | box_extras | Init Box for print |
| `TRY_RESUME_PRINT` | box_extras | Resume after error |
| `RESUME_PRINT_1` | box_extras | Resume continuation |
| `INIT_MAPPING_VALUE` | box_extras | Init slot mapping |
| `TOOL_CHANGE_START` | box_extras | Begin tool change |
| `TOOL_CHANGE_END` | box_extras | End tool change |
| `CLEAR_TOOLCHANGE_STATE` | box_extras | Reset tool change |
| `SLOT_UNLOAD` | box_stepper | Unload slot |
| `EXTRUDER_LOAD` | box_stepper | Load extruder |
| `EXTRUDER_UNLOAD` | box_stepper | Unload extruder |
| `SLOT_PROMPT_MOVE` | box_stepper | Prompted slot move |
| `SLOT_RFID_READ` | box_stepper | Read RFID at slot |
| `SET_AIR_TEMPERATURE` | heater_air_core | Set chamber temp |
| `TURN_OFF_HEATERS` | heater_air_core | Turn off all heaters |
| `WEIGH_CALIBRATE` | air | Calibrate weight probe |
| `READ_TEMP_RH` / `BOX_TEMP_READ` | aht20_f | Read temp/humidity |
| `WEIGHTING_CONFIG_READ` | cs1237 | Read ADC config |
| `CS1237_WEIGHT_BEGIN` | cs1237 | Start weight measurement |
| `CS1237_ZERO_DEBUG` | cs1237 | Zero debug |
| `CS1237_TEST` | cs1237 | Test command |
| `WEIGHT_TARGET` | hx711 | Set weight target |
| `WEIGHTING_START_QUERY` | hx711 | Start weight query |
| `WEIGHTING_END_QUERY` | hx711 | End weight query |

---

## Architecture Notes

- All modules follow the Klipper extras pattern: `load_config(config)` or `load_config_prefix(config)` entry point
- Box system uses a hub architecture: `box_extras` is the central coordinator, `box_stepper` handles motion, `box_rfid` handles tag reading, `box_detect` handles USB discovery
- Weight probe system (`air` + `cs1237`/`hx711`) is a complete probe implementation with calibration, drift compensation, and multi-probe support
- The `heater_air_core` module is a parallel heater system to Klipper's built-in heaters, specifically for chamber/air heating
- `buttons_irq` replaces Klipper's polling-based button handler with hardware interrupt-driven input

## Detailed Decompilation Reports

Per-module deep analysis (radare2 + r2dec/r2ghidra decompilation) is available in `klippy_extras_decompiled/`:

| Report | Covers |
|--------|--------|
| [box_extras_analysis.md](klippy_extras_decompiled/box_extras_analysis.md) | Core Box management — drying, tool changes, filament ops, 26+ G-code commands |
| [box_stepper_analysis.md](klippy_extras_decompiled/box_stepper_analysis.md) | Filament feeding — multi-stage load/unload, 19 error codes, toolhead shaking, auto-reload |
| [box_detect_analysis.md](klippy_extras_decompiled/box_detect_analysis.md) | Box auto-detection — USB serial scanning, pyudev, config templates, V1→V2 auto-upgrade |
| [air_and_heater_analysis.md](klippy_extras_decompiled/air_and_heater_analysis.md) | Weight probe + chamber heater — frequency-based probing, bang-bang control, drift compensation |
| [sensors_and_io_analysis.md](klippy_extras_decompiled/sensors_and_io_analysis.md) | CS1237, HX711, AHT20, buttons_irq, box_rfid — MCU protocols, I2C/SPI, FM17550 NFC |

## Key Constants Discovered

| Constant | Value | Context |
|----------|-------|---------|
| Purge volume | 150mm at 5mm/s | Filament flush sequence |
| Post-cut retract | 60mm | After filament cut |
| Initial feed | 25mm | First stage of load |
| Main feed | 100mm | Main stage of load |
| Cooling dwell | 5 seconds at 100% fan | Post-flush cooling |
| Toolhead shake speed | 500mm/s | Y: 200↔70, X same pattern |
| Wipe X range | X98–X115 at F8000 | Ooze/wipe brush zone |
| Max Box units | 4 | Templates cfg_with_0 through cfg_with_4 |
| LED slots | 16 (4×4) | Slot IDs 1A–4D |
| RFID chip | FM17550 | NFC reader via SPI |
| Weight ADCs | CS1237, HX711 | 24-bit, bulk sensor interface |
| Temp sensor | AHT20 | I2C, CRC-8 validated |
| Button debounce | configurable `debounce_us` | IRQ-driven, per-pin |

## Error Code Summary

### Box Stepper Errors (QDE_004_xxx)
19 error codes from QDE_004_001 through QDE_004_025 covering:
- Slot load/unload failures
- Wrapping detection (QDE_004_013)
- PTFE tube bent detection (QDE_004_019)
- Endstop trigger failures
- Buffer monitoring errors

### Box Extras Errors
5 error codes from QDE_004_010 through QDE_004_023 covering:
- Drying system failures
- Tool change errors
- RFID read failures

## Decompilation Method

Analysis performed using:
- `file` — ELF identification (aarch64, not stripped, with debug_info)
- `nm -D` — Dynamic symbol extraction (PyInit_, __pyx_ prefixes)
- `strings` — String constant extraction (method names, error messages, variable names)
- `radare2 6.1.2` with `r2dec` and `r2ghidra` plugins — Function decompilation and control flow analysis
- Cross-architecture analysis (macOS arm64 host → aarch64 Linux target)
