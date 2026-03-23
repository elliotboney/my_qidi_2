# Sensors and IO Module Analysis - Qidi Q2 Klipper Extras

Reverse-engineered from Cython-compiled `.so` binaries using radare2 on aarch64 ELF shared objects.

**Analysis date:** 2026-03-22
**Tool:** radare2 6.1.2
**Target architecture:** aarch64-linux-gnu (CPython 3.9)

---

## Table of Contents

1. [cs1237.so - CS1237 Weight Sensor ADC](#1-cs1237so---cs1237-weight-sensor-adc)
2. [hx711.so - HX711 Weight Sensor ADC](#2-hx711so---hx711-weight-sensor-adc)
3. [aht20_f.so - AHT20 Temperature/Humidity Sensor](#3-aht20_fso---aht20-temperaturehumidity-sensor)
4. [buttons_irq.so - IRQ-Based Button Input](#4-buttons_irqso---irq-based-button-input)
5. [box_rfid.so - FM17550 NFC/RFID Reader](#5-box_rfidso---fm17550-nfcrfid-reader)

---

## 1. cs1237.so - CS1237 Weight Sensor ADC

**Source file:** `cs1237.pyx` (Cython), compiled as `cs1237.cpython-39-aarch64-linux-gnu.so`
**Cython version:** 3.0.10/3.0.11 (mixed strings suggest upgrade during development)
**Module path on printer:** `/home/mks/klipper/klippy/extras/`

### Overview

The CS1237 is a 24-bit ADC designed for weight/load cell measurements. This module implements a Klipper sensor driver with homing support (weight-based homing/triggering), bulk data streaming, and zero/tare functionality.

### Classes

| Class | Purpose |
|-------|---------|
| `CS1237` | Main sensor driver - MCU config, homing, zero/tare |
| `CS1237Command` | G-code command handler - user-facing weight commands |

### CS1237 Class Methods

| Method | Size (bytes) | Purpose |
|--------|-------------|---------|
| `__init__` | 5940 | Constructor - config parsing, pin setup |
| `_build_config` | 4612 | MCU protocol command registration |
| `_handle_ready` | 3440 | Ready event handler |
| `get_mcu` | 588 | Return MCU reference |
| `setup_home` | 4328 | Configure weight-based homing |
| `clear_home` | 4200 | Clear homing state |
| `zero_home` | 5024 | Zero/tare the sensor for homing |
| `check_cs1237_zero` | 4960 | Validate zero calibration |

### CS1237Command Class Methods

| Method | Size (bytes) | Purpose |
|--------|-------------|---------|
| `__init__` | 1968 | Constructor |
| `register_commands` | 3712 | Register G-code commands |
| `cmd_CS1237_TEST` | 792 | Test command |
| `cmd_CS1237_WEIGHT_BEGIN` | 4452 | Start weight measurement |
| `cmd_CS1237_ZERO_DEBUG` | 5100 | Debug zero/tare value |
| `cmd_WEIGHTING_CONFIG_READ` | 2768 | Read sensor configuration |
| `cmd_WEIGHTING_DEBUG_QUERY` | 5352 | Debug query weight data |

### MCU Protocol Commands

These are the low-level commands sent to the MCU firmware:

```
# Configuration
config_cs1237 oid=%d dout_pin=%s sclk_pin=%s

# Querying sensor data
query_cs1237 oid=%c rest_ticks=%u
query_cs1237_data oid=%c data=%*s              (bulk data response)

# Homing (weight-based triggering)
cs1237_setup_home oid=%c clock=%u threshold=%u trsync_oid=%c trigger_reason=%c error_reason=%c
cs1237_home_state oid=%c homing=%c trigger_clock=%u

# Zero/tare
query_cs1237_zero oid=%c
query_cs1237_zero_read oid=%c data=%*s
query_cs1237_zero_read_o oid=%c data=%*s       (alternate format)
query_cs1237_zero_read_only oid=%c
query_cs1237_zero_config_read oid=%c config=%u

# Config read-back
query_cs1237_config_r oid=%c
query_cs1237_begin oid=%c config=%u
query_cs1237_begin_read oid=%c config=%u
query_cs1237_read oid=%c reg=%u read_len=%u

# Status
query_cs1237_status
```

### Hardware Configuration

- **Interface:** SPI-like 2-wire (DOUT + SCLK pins)
- **Config pins:** `dout_pin`, `sclk_pin` (looked up via Klipper pin resolver `ppins`)
- **Data format:** `cs1237_v_128` - suggests 128x gain configuration
- **Bulk data:** Uses Klipper's `BulkDataQueue` for streaming
- **Constants:**
  - `BYTES_PER_SAMPLE` - ADC data width
  - `MAX_SAMPLES_PER_BLOCK` - bulk transfer chunking
  - `MAX_BULK_MSG_SIZE` - message size limit
  - `UPDATE_INTERVAL` - polling rate
  - `BATCH_UPDATES` - batch processing flag
  - `CS1237_QUERY_RATES` - supported query rates

### Homing Protocol

The sensor supports weight-based homing (endstop triggering) via trsync:

1. `setup_home()` sends `cs1237_setup_home` with threshold, clock, trsync_oid, trigger/error reasons
2. MCU monitors weight data against threshold
3. When threshold exceeded, triggers trsync at `trigger_clock`
4. `cs1237_home_state` reports homing=%c (active/inactive) and trigger_clock
5. `clear_home()` deactivates homing
6. `zero_home()` tares the sensor before homing

### G-Code Commands

| Command | Description |
|---------|-------------|
| `CS1237_WEIGHT_BEGIN` | Start weight measurement acquisition |
| `CS1237_ZERO_DEBUG` | Debug: display zero/tare value |
| `WEIGHTING_CONFIG_READ` | Read sensor hardware config register |
| `WEIGHTING_DEBUG_QUERY` | Debug: query raw weight data |
| `WEIGHTING_TEST` | Test sensor communication |
| `WEIGHTING_DEBUG_ZERO_DATA` | Debug: zero calibration data |

### Status Messages

- `WEIGHT:CS1237 ZERO:%.3f` - reports zero/tare value
- `WEIGHT----sensor config failed: 0x%x` (Chinese: `传感器配置失败`)
- `WEIGHT----sensor config success: 0x%x` (Chinese: `传感器配置成功`)
- `Obtain CS1237 measurement values` - description string

---

## 2. hx711.so - HX711 Weight Sensor ADC

**Source file:** `hx711.pyx` (Cython), compiled as `hx711.cpython-39-aarch64-linux-gnu.so`
**Cython version:** 3.0.10
**Module path on printer:** `/home/mks/klipper/klippy/extras/`

### Overview

The HX711 is a popular 24-bit ADC for weight/load cell measurements. This module mirrors the CS1237 architecture very closely - same class structure, similar MCU commands, same homing mechanism. The HX711 adds explicit start/stop/end query commands and a weight target feature.

### Classes

| Class | Purpose |
|-------|---------|
| `HX711` | Main sensor driver - MCU config, homing, zero/tare |
| `HX711Command` | G-code command handler |

### HX711 Class Methods

| Method | Size (bytes) | Purpose |
|--------|-------------|---------|
| `__init__` | 5452 | Constructor - config parsing, pin setup |
| `_build_config` | 4020 | MCU protocol command registration |
| `get_mcu` | 588 | Return MCU reference |
| `setup_home` | 4328 | Configure weight-based homing |
| `clear_home` | 4200 | Clear homing state |
| `zero_home` | 1120 | Zero/tare the sensor |

### HX711Command Class Methods

| Method | Size (bytes) | Purpose |
|--------|-------------|---------|
| `__init__` | 1964 | Constructor |
| `register_commands` | 3600 | Register G-code commands |
| `cmd_WEIGHT_TARGET` | 2324 | Set target weight value |
| `cmd_WEIGHTING_START_QUERY` | 1528 | Start weight query streaming |
| `cmd_WEIGHTING_END_QUERY` | 1528 | Stop weight query streaming |
| `cmd_WEIGHTING_DEBUG_QUERY` | 5504 | Debug query weight data |

### MCU Protocol Commands

```
# Configuration
config_hx711 oid=%d dout_pin=%s sclk_pin=%s

# Querying sensor data
query_hx711 oid=%c rest_ticks=%u
query_hx711 oid=%d rest_ticks=0                (stop query)
query_hx711_data oid=%c data=%*s               (bulk data response)
query_hx711_data_out                           (data output variant)
query_hx711_read oid=%c
query_hx711_read_data                          (read response)

# Homing (weight-based triggering)
hx711_setup_home oid=%c clock=%u threshold=%u trsync_oid=%c trigger_reason=%c error_reason=%c
hx711_home_state oid=%c homing=%c trigger_clock=%u

# Zero/tare
query_hx711_zero oid=%c
query_hx711_zero_read oid=%c

# Status
query_hx711_status
```

### Hardware Configuration

- **Interface:** SPI-like 2-wire (DOUT + SCLK pins)
- **Config pins:** `dout_pin`, `sclk_pin`
- **Constants:**
  - `HX711_FREQ` - ADC sampling frequency
  - `UPDATE_INTERVAL` - polling rate
  - `MAX_BULK_MSG_SIZE`, `BATCH_UPDATES` - bulk data settings
- **Bulk data:** Uses `BulkDataQueue`

### Homing Protocol

Identical to CS1237:
1. `setup_home()` with threshold + trsync
2. MCU monitors, triggers when weight exceeds threshold
3. `hx711_home_state` reports status
4. `clear_home()` / `zero_home()` for cleanup/tare

### G-Code Commands

| Command | Description |
|---------|-------------|
| `WEIGHT_TARGET` | Set target weight for monitoring |
| `WEIGHTING_START_QUERY` | Begin continuous weight streaming |
| `WEIGHTING_END_QUERY` | Stop continuous weight streaming |
| `WEIGHTING_DEBUG_QUERY` | Debug: raw weight data query |

### Status/Debug Messages

- `HX711_Info: %d/0x%x(origin) / %.6f(ENOB)` - raw data + effective number of bits
- `HX711_Info:Data error!` - communication error
- `HX711_status:%d` - status code
- `HX711 end query!` - query termination
- `hx711 test start!` / `hx711 test end!` - test lifecycle
- `Obtain HX711 measurement values` - description
- `weight_mg` - weight output in milligrams

### Key Difference from CS1237

The HX711 module adds:
- `cmd_WEIGHT_TARGET` - allows setting a specific weight target for monitoring/triggering
- Explicit start/end query commands (vs CS1237's begin-only approach)
- `on_restart` handler - handles printer restart cleanup
- `start_hx711` initialization command

---

## 3. aht20_f.so - AHT20 Temperature/Humidity Sensor (Box Version)

**Source file:** `aht20_f.py` (Cython-compiled), compiled as `aht20_f.so`
**Cython version:** 3.0.11
**Module path on printer:** `/home/mks/klipper/klippy/extras/`
**Source path:** `/home/mks/klipper/klippy/extras/aht20_f.c`

### Overview

The AHT20 is an I2C temperature and humidity sensor. This "_f" variant is a factory/box-specific implementation used in the Qidi Box multi-material system. It integrates with Klipper's heater system and implements the standard sensor interface (setup_minmax, setup_callback, get_status).

### Class: AHT20_F

| Method | Size (bytes) | Purpose |
|--------|-------------|---------|
| `__init__` | 4900 | Constructor - I2C setup, heater binding |
| `handle_connect` | 1612 | klippy:connect event handler |
| `setup_minmax` | 1240 | Set temperature limits |
| `setup_callback` | 888 | Register measurement callback |
| `get_report_time_delta` | 592 | Return sampling interval |
| `get_status` | 1464 | Return current temp/humidity status |
| `check_crc8` | 3644 | CRC-8 validation of sensor data |
| `cmd_READ_TEMP_RH` | 1688 | G-code command to read temp/humidity |
| `_init_aht20_f` | 3588 | I2C initialization sequence |
| `_sample_aht20_f` | 9160 | Read and process sensor data |
| `_make_measurement` | 9588 | Full measurement cycle with retry logic |
| `_reset_device` | 4088 | Device reset sequence |

### Module-Level

| Function | Size (bytes) | Purpose |
|----------|-------------|---------|
| `load_config` | 1712 | Klipper config entry point |

### AHT20 Command Register Map

Constants found in the binary define the AHT20's I2C command set:

| Constant | Purpose |
|----------|---------|
| `AHT20_F_I2C_ADDR` | Default I2C address (standard AHT20: 0x38) |
| `AHT20_F_COMMANDS` | Command dictionary |
| `AHT20_F_MAX_BUSY_CYCLES` | Timeout: max busy-wait cycles |
| `MEASURE` | Trigger measurement command (0xAC for standard AHT20) |
| `RESET` | Soft reset command (0xBA for standard AHT20) |
| `SYS_CFG` | System configuration register |
| `AFE_CFG` | Analog front-end configuration |
| `OTP_AFE` | OTP (one-time programmable) AFE register |
| `OTP_CCP` | OTP calibration register |
| `CCP_CCN` | Calibration coefficient |
| `INDEX` | Register index command |

### I2C Protocol Details

**Initialization sequence** (`_init_aht20_f`):
1. Uses `MCU_I2C_from_config` to get I2C bus handle
2. Sends initialization/calibration commands via `i2c_write`
3. Reads back status via `i2c_read`
4. Checks calibration bit (`is_calibrated`)
5. If not calibrated, enters OTP/AFE configuration sequence
6. Logs: `aht20_f: successfully initialized, initial temp:` + temp value

**Measurement cycle** (`_sample_aht20_f`):
1. Sends MEASURE command via `i2c_write`
2. Reads response bytes via `i2c_read`
3. Checks busy bit (`is_busy`)
4. If busy, retries up to `AHT20_F_MAX_BUSY_CYCLES`
5. If still busy after max cycles: `aht20_f: device reported busy after %d cycles, resetting device`
6. Calls `_reset_device` and retries
7. Validates data with `check_crc8` (CRC-8 over received bytes)
8. Converts raw bytes to temperature and humidity
9. Temperature formula: standard AHT20 conversion (20-bit raw value)
10. Humidity formula: standard AHT20 conversion (20-bit raw value)

**Reset sequence** (`_reset_device`):
1. Sends RESET command
2. Waits for device to re-initialize
3. Re-runs initialization sequence

### Integration with Klipper

- **Heater binding:** Looks up associated heater via `heater_name` config option
  - Uses `lookup_heater` from Klipper's heaters module
  - Logs: `AHT20_F sensor using heater: <name>`
  - Error: `heater '<name>' not found for AHT20_F sensor`
- **Timer-based sampling:** Uses `register_timer` with `sample_timer` callback
- **Report time:** Configurable via `aht20_f_report_time` config option
- **Status output:** `{temp: <float>, humidity: <float>}` via `get_status`
- **G-code output:** `%s,temp:%f, humidity:%f` and `temperature: %.3f, humidity: %.3f`
- **Temperature range:** `min_temp` / `max_temp` with validation: `AHT20_F temperature outside range`
- **Sensor factory:** Registered via `add_sensor_factory`
- **G-code command:** `BOX_TEMP_READ` (registered as mux command via `register_mux_command`)

### Error Handling

- `aht20_f: exception encountered` - generic exception catch
- `aht20_f: received bytes less than <n>` - short read
- `aht20_f: received data from <source> reading data: %s` - data dump on error
- `aht20_f: device reported busy after %d cycles, resetting device` - timeout

---

## 4. buttons_irq.so - IRQ-Based Button Input

**Source file:** `buttons_irq.py` (Cython-compiled), compiled as `buttons_irq.so`
**Cython version:** (not explicitly tagged)
**Source path:** `/home/mks/klipper/klippy/extras/buttons_irq.c`

### Overview

This module implements interrupt-driven (IRQ) button handling for Klipper. Unlike standard Klipper button polling, this uses MCU-side interrupt detection with debouncing, providing faster response times. It supports multiple buttons per MCU with configurable pull-up, debounce, and invert settings.

### Classes

| Class | Purpose |
|-------|---------|
| `MCU_irq_button` | Top-level button manager - collects pins, dispatches to MCU handlers |
| `_IRQButtonMCU` | Per-MCU button handler - MCU communication, state tracking |

### MCU_irq_button Methods

| Method | Size (bytes) | Purpose |
|--------|-------------|---------|
| `__init__` | 1320 | Constructor |
| `register_buttons` | 7152 | Register button pins and callbacks |

### _IRQButtonMCU Methods

| Method | Size (bytes) | Purpose |
|--------|-------------|---------|
| `__init__` | 3804 | Constructor - MCU setup, state init |
| `setup_buttons` | 3936 | Configure button pins on MCU |
| `_build_config` | 4576 | Register MCU commands |
| `_handle_state` | 7780 | Process button state change from MCU |

### MCU Protocol Commands

```
# Configuration (per button)
config_irq_button oid=%d pin=%s pull_up=%d debounce_us=%d invert=%d

# State reporting
irq_button_state                               (MCU -> host: button state change)

# Acknowledgment
irq_button_ack oid=%c count=%c                 (host -> MCU: acknowledge state)

# Debug
_irq_button debounce_us=%d                     (debounce config echo)
```

### Hardware Configuration

- **Pin parameters:** Each button configured with:
  - `pin` - GPIO pin identifier
  - `pull_up` - internal pull-up enable (0/1)
  - `debounce_us` - debounce time in microseconds
  - `invert` - invert logic level (0/1)
- **Pin resolution:** Via `ppins.lookup_pin` with `pin_params` / `pin_params_list`
- **Multi-MCU constraint:** `IRQ button pins must be on same MCU` - all pins in a button group must be on one MCU
- **Logging:** `Creating new IRQ button object for MCU '%s' with %d pins`

### State Machine / Callback Flow

1. **Registration:** `register_buttons(pin_list, callback)` validates pins are on same MCU
2. **Config:** `_build_config` sends `config_irq_button` for each pin with debounce/pullup/invert settings
3. **MCU interrupt:** When button state changes, MCU sends `irq_button_state`
4. **Host processing:** `_handle_state` receives state, unpacks data, invokes registered callbacks
5. **Acknowledgment:** Host sends `irq_button_ack` with `oid` and `count` to MCU
6. **State tracking:** `ack_count` tracks acknowledgments, `states` tracks current pin states
7. **Async:** Callbacks registered via `register_async_callback` for thread-safe execution

### Key Attributes

- `callbacks` - list of registered callback functions
- `pin_list` / `pin_params_list` - configured pins and their parameters
- `ack_cmd` / `ack_count` - acknowledgment tracking
- `cmd_queue` - MCU command queue
- `mcu_button` / `mcu_name` - MCU reference
- `states` / `state` - current button states
- `count` / `max_count` - event counting

### Module Entry Point

```python
def load_config(config):  # registered with default arguments via __defaults__
```

---

## 5. box_rfid.so - FM17550 NFC/RFID Reader

**Source file:** `box_rfid.py` (Cython-compiled), compiled as `box_rfid.so`
**Cython version:** 3.0.11
**Source path:** `/home/mks/klipper/klippy/extras/box_rfid.c`

### Overview

This module interfaces with an FM17550 NFC/RFID reader chip (Chinese equivalent of MFRC522/PN532) used in the Qidi Box multi-material system. It reads NFC tags on filament spools to identify filament type, color, and other properties. Uses SPI communication and integrates with the Box filament slot system.

### Class: BoxRFID

| Method | Size (bytes) | Purpose |
|--------|-------------|---------|
| `__init__` | 4592 | Constructor - SPI setup, slot configuration |
| `_build_config` | 1996 | Register MCU commands |
| `read_card` | 1092 | Trigger single card read |
| `read_card_from_slot` | 848 | Read card from specific filament slot |
| `start_rfid_read` | 3176 | Start continuous RFID reading |
| `stop_read` | 2360 | Stop continuous reading |
| `_schedule_rfid_read` | 9612 | Main read loop - schedule, read, process |

### Module Entry Point

```python
def load_config_prefix(config):  # supports multiple instances via prefix
```

### MCU Protocol Commands

```
# Card read trigger
fm17550_read_card                              (host -> MCU: trigger read)
fm17550_read_card_cb oid=%c                    (MCU -> host: read callback/ready)

# Card data response
fm17550_read_card_return oid=%c status=%c data=%*s    (MCU -> host: card data)

# Query (stop)
query_fm17550 oid=%d rest_ticks=0              (stop continuous query)
```

### Hardware Configuration

- **Interface:** SPI via `MCU_SPI_from_config` (from `box_extras` module)
- **Chip:** FM17550 (Fudan Microelectronics NFC/RFID transceiver)
- **CS pin:** `spi_cs` configuration parameter
- **Command queue:** Via `get_command_queue` / `cmdqueue`
- **OID:** Object ID via `get_oid`

### RFID Read Protocol

**Single read** (`read_card`):
1. Send `fm17550_read_card` command
2. MCU communicates with FM17550 via SPI
3. MCU returns `fm17550_read_card_return` with status and raw data

**Continuous reading** (`start_rfid_read` / `_schedule_rfid_read`):
1. `start_rfid_read` initializes timer via `register_timer` with `read_rfid_timer`
2. Timer callback `_schedule_rfid_read` runs periodically
3. Each cycle: sends read command, processes response
4. Tracks `rfid_read_attempts` and `rfid_read_start_time` for timeout
5. `max_read_time` limits how long continuous reading runs
6. `stop_read` cancels timer via `unregister_timer`

**Slot-based reading** (`read_card_from_slot`):
1. References `stepper` / `stepper_name` / `stepper_label` - Box stepper positioning
2. Moves to specific slot, then triggers card read
3. Used for auto-detection during slot changes

### Data Processing

After reading a card, the module extracts filament information:

- `filament` / `filament_` - filament type identifier
- `color` / `color_` - filament color data
- `vendor_` - vendor/manufacturer identifier
- `share_type` - filament sharing/compatibility type
- `temp_message_1`, `temp_message_2` - temperature profile messages (print/bed temp)
- `label` - human-readable label
- `status` - read status code

### Error Handling

- `Unrecognized label read in %s` - unknown filament tag format
- `%s did not recognize the filament` - failed filament identification
- `NEVER` - used as a flag/sentinel value (possibly for retry policy)

### Integration with Box System

- **Config prefix:** `load_config_prefix` - supports `[box_rfid slot1]`, `[box_rfid slot2]`, etc.
- **Dependencies:** Imports `box_extras` module for SPI helper
- **Persistence:** Uses `save_variable` for storing read filament data
- **Feedback:** Uses `respond_info` to report filament identification to user
- **Restart handling:** `on_restart` handler for clean shutdown
- **Stepper integration:** Works with Box stepper system to position for slot reads

---

## Cross-Module Summary

### Architecture Pattern

All five modules follow the standard Klipper extras pattern:
1. `load_config` / `load_config_prefix` entry point
2. Main class with `__init__` (config parsing), `_build_config` (MCU command registration)
3. MCU commands use format strings with `oid=%c/d`, data fields
4. Commands registered via `add_config_cmd`, `lookup_command`, `lookup_query_command`
5. Events via `register_event_handler`, `register_config_callback`

### Weight Sensors (CS1237 + HX711) Comparison

| Feature | CS1237 | HX711 |
|---------|--------|-------|
| ADC Resolution | 24-bit | 24-bit |
| Interface | 2-wire (DOUT/SCLK) | 2-wire (DOUT/SCLK) |
| Homing support | Yes (trsync) | Yes (trsync) |
| Zero/tare | Yes (complex, multi-command) | Yes (simpler) |
| Weight target | No | Yes (`WEIGHT_TARGET`) |
| Start/stop query | Begin only | Start + End |
| Config read | Yes (`CONFIG_READ`) | No |
| Frequency config | No | Yes (`HX711_FREQ`) |
| Data output | `cs1237_data` | `hx711_data` + `hx711_data_out` |
| Bulk streaming | Yes (`BulkDataQueue`) | Yes (`BulkDataQueue`) |
| Status reporting | Limited | `HX711_status:%d` |

### Communication Interfaces

| Module | Interface | Protocol |
|--------|-----------|----------|
| cs1237 | 2-wire GPIO (DOUT+SCLK) | CS1237 proprietary serial |
| hx711 | 2-wire GPIO (DOUT+SCLK) | HX711 proprietary serial |
| aht20_f | I2C | Standard AHT20 I2C (addr 0x38) |
| buttons_irq | GPIO (per-pin) | MCU IRQ with debounce |
| box_rfid | SPI | FM17550 NFC commands |

### G-Code Command Registry

| Command | Module | Description |
|---------|--------|-------------|
| `CS1237_WEIGHT_BEGIN` | cs1237 | Start CS1237 weight measurement |
| `CS1237_ZERO_DEBUG` | cs1237 | Debug zero calibration |
| `WEIGHTING_CONFIG_READ` | cs1237 | Read sensor config register |
| `WEIGHTING_DEBUG_QUERY` | cs1237/hx711 | Debug raw weight data |
| `WEIGHTING_TEST` | cs1237 | Test sensor comms |
| `WEIGHT_TARGET` | hx711 | Set target weight |
| `WEIGHTING_START_QUERY` | hx711 | Start weight streaming |
| `WEIGHTING_END_QUERY` | hx711 | Stop weight streaming |
| `BOX_TEMP_READ` | aht20_f | Read box temperature/humidity |
