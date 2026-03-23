# box_detect.so - Reverse Engineering Analysis

**Binary:** `/klippy_extras/box_detect.so`
**Type:** ELF 64-bit LSB shared object, ARM aarch64, Cython-compiled CPython 3.9 extension
**Cython version:** 3.0.11
**Source file:** `/home/mks/klipper/klippy/extras/box_detect.c` (generated from `box_detect.py`)
**Debug info:** Present (not stripped), includes DWARF debug sections
**Text section size:** ~175 KB (0x2aafc bytes)

---

## Module Overview

`box_detect` is a Klipper extra that auto-detects Qidi Box multi-material units connected via USB serial. It monitors `/dev/serial/by-id/` for Box devices using `pyudev`, determines how many are connected, generates the appropriate config files (`box1.cfg`, `box2.cfg`, etc.), and triggers a firmware restart when the configuration changes.

---

## Imports

Extracted from string table references:

| Module | Purpose |
|--------|---------|
| `os` | Path operations (`path.exists`, `listdir`, `basename`) |
| `re` | Regex for parsing config includes and version strings |
| `shutil` | File copying (`copy`) |
| `time` | Timing/delays |
| `logging` | Log output (`info`, `warning`, `error`, `debugoutput`) |
| `filecmp` | File comparison (`cmp`, `shallow`) |
| `configparser` | INI-style config parsing (`ConfigParser`, `sections`, `has_section`, `read_string`, `delimiters`) |
| `pyudev` | Linux USB device monitoring (`Context`, `Monitor`, `from_netlink`, `filter_by`, `list_devices`) |

---

## Module-Level Constants

### File Paths

| Constant | Value |
|----------|-------|
| `SRC_BOX_CFG_WITH_0` | `/home/mks/cfg_with_0` |
| `SRC_BOX_CFG_WITH_1` | `/home/mks/cfg_with_1` |
| `SRC_BOX_CFG_WITH_2` | `/home/mks/cfg_with_2` |
| `SRC_BOX_CFG_WITH_3` | `/home/mks/cfg_with_3` |
| `SRC_BOX_CFG_WITH_4` | `/home/mks/cfg_with_4` |
| `DST_BOX_CFG` | `/home/mks/printer_data/config/box.cfg` (inferred from references) |
| (box1 config) | `/home/mks/printer_data/config/box1.cfg` |
| (box2 config) | `/home/mks/printer_data/config/box2.cfg` |
| (saved vars) | `/home/mks/printer_data/config/saved_variables.cfg` |
| (serial path) | `/dev/serial/by-id/` |

### Template System

The `cfg_with_N` files at `/home/mks/` are **pre-built config templates** for different Box counts:
- `cfg_with_0` -- Config for 0 Boxes detected (no Box includes)
- `cfg_with_1` -- Config for 1 Box detected (includes box1.cfg)
- `cfg_with_2` -- Config for 2 Boxes detected (includes box1.cfg + box2.cfg)
- `cfg_with_3` -- Config for 3 Boxes
- `cfg_with_4` -- Config for 4 Boxes

These templates are **copied** to `DST_BOX_CFG` (`/home/mks/printer_data/config/box.cfg`) using `shutil.copy` when the detected device count changes.

### String Constants

| String | Context |
|--------|---------|
| `"gcode:request_restart"` | Klipper event sent to trigger restart |
| `"SAVE_VARIABLE VARIABLE=box_count VALUE=%d"` | G-code to persist detected Box count |
| `"SAVE_VARIABLE VARIABLE=box_count VALUE=0"` | G-code to reset Box count to 0 |
| `"klippy:ready"` | Event handler registration |
| `"Detected "` + `" devices: "` | Log message format |
| `"Updated new device path: "` | Log message for device path changes |
| `"Error monitoring serial devices: "` | Error log prefix |
| `"Unexpected device count or mismatch detected."` | Warning/error message |
| `"\\[include box(\\d+)\\.cfg\\]"` | Regex pattern to find `[include boxN.cfg]` in config |
| `"V1_(\\d+\\.\\d+\\.\\d+)"` | Regex to extract Box V1 firmware version |
| `"V2_(\\d+\\.\\d+\\.\\d+)"` | Regex to extract Box V2 firmware version |
| `"Virtual_ComPort"` | USB device identifier string for Box units |
| `"MKS_COLOR_BOOT"` | USB bootloader identifier (Box V1?) |
| `"MKS_COLOR0_BOOT"` | USB bootloader identifier (Box V1 variant?) |
| `"QIDI_BOX_V1"` | Box hardware version 1 identifier |
| `"QIDI_BOX_V2"` | Box hardware version 2 identifier |
| `"/home/mks/mcu_update_BOX_to_v2.sh /home/mks/"` | Shell script for V1-to-V2 firmware upgrade |

---

## Class: BoxDetect

### Functions (in definition order from symbol table)

| # | Method | Symbol | Size (bytes) |
|---|--------|--------|------|
| 1 | `monitor_serial_devices` | `__pyx_pw_...1monitor_serial_devices` | 520 (wrapper) + 19,448 (impl) |
| 2 | `is_monitor_config_file_empty` | `__pyx_pw_...3is_monitor_config_file_empty` | 3,052 |
| 3 | `update_monitor_config_file` | `__pyx_pw_...5update_monitor_config_file` | 11,812 |
| 4 | `add_printer_objects` | `__pyx_pw_...7add_printer_objects` | 1,616 |
| 5 | `BoxDetect.__init__` | `__pyx_pw_...9BoxDetect_1__init__` | 4,272 |
| 6 | `BoxDetect._handle_ready` | `__pyx_pw_...9BoxDetect_3_handle_ready` | 2,968 |
| 7 | `BoxDetect.get_config_mcu_serials` | `__pyx_pw_...9BoxDetect_5get_config_mcu_serials` | 5,176 |
| 8 | `BoxDetect.monitor_serial_by_id` | `__pyx_pw_...9BoxDetect_7monitor_serial_by_id` | 780 (wrapper) + 34,928 (impl) |
| 9 | `BoxDetect._update_config_file` | `__pyx_pw_...9BoxDetect_9_update_config_file` | 7,204 |
| 10 | `BoxDetect._request_restart` | `__pyx_pw_...9BoxDetect_11_request_restart` | 2,888 |
| 11 | `BoxDetect.get_check_serials_id` | `__pyx_pw_...9BoxDetect_13get_check_serials_id` | 3,832 |
| 12 | `BoxDetect.count_box_includes` | `__pyx_pw_...9BoxDetect_15count_box_includes` | 4,544 |

Plus 4 generator objects for `monitor_serial_devices` (genexpr, generator1, generator2, generator3).

---

## Reconstructed Logic

### `add_printer_objects(config)`

Module-level Klipper registration function. Creates a `BoxDetect` instance and registers it with the printer via `config.get_printer().add_object("boxdetect", BoxDetect(config))`.

### `BoxDetect.__init__(self, config)`

**Instance attributes** (inferred from variable references):

```python
self.printer = config.get_printer()
self.reactor = self.printer.get_reactor()
self.gcode = self.printer.lookup_object("gcode")
self.config = config
self.config_path = "/home/mks/printer_data/config/"  # inferred
self.variables_path = "/home/mks/printer_data/config/saved_variables.cfg"
self.previous_tty_count = 0
self.current_devices = []
self.current_device_path = None
self.serial_by_id = None
self.device_count = 0
self.mcu_version = None
self.box_count = 0  # from saved variables

# Source config templates
self.src_box_cfg_with_0 = SRC_BOX_CFG_WITH_0  # "/home/mks/cfg_with_0"
self.src_box_cfg_with_1 = SRC_BOX_CFG_WITH_1
self.src_box_cfg_with_2 = SRC_BOX_CFG_WITH_2
self.src_box_cfg_with_3 = SRC_BOX_CFG_WITH_3
self.src_box_cfg_with_4 = SRC_BOX_CFG_WITH_4
self.dst_box_cfg = DST_BOX_CFG  # "/home/mks/printer_data/config/box.cfg"

# Register event handler and timer
self.printer.register_event_handler("klippy:ready", self._handle_ready)
self.serial_monitor_timer = self.reactor.register_timer(self.monitor_serial_by_id)
```

### `BoxDetect._handle_ready(self)`

Called when Klipper finishes initialization. Likely:
1. Gets current `print_time` via `toolhead.get_last_move_time()`
2. Calls `toolhead.dwell()` and/or `toolhead.wait_moves()`
3. Triggers initial serial device scan
4. Uses `os.listdir()` on various paths
5. Checks for `.bin` firmware files (`bin_files`, `bin_name`, `basename`, `.bin` string)
6. References `klippy_state` to check printer readiness

### `BoxDetect.monitor_serial_by_id(self, eventtime)`

**The main timer callback.** This is the largest function (34,928 bytes implementation). Runs periodically via Klipper's reactor timer system.

**Reconstructed flow:**

```
1. Scan /dev/serial/by-id/ for USB serial devices
2. Filter for devices containing "Virtual_ComPort", "QIDI_BOX_V1", or "QIDI_BOX_V2"
3. Also check for bootloader devices: "MKS_COLOR_BOOT", "MKS_COLOR0_BOOT"
4. Count detected devices
5. Check firmware version using regex:
   - V1_(X.Y.Z) pattern for Box V1
   - V2_(X.Y.Z) pattern for Box V2
6. If V1 detected, may trigger firmware update:
   - Runs: /home/mks/mcu_update_BOX_to_v2.sh /home/mks/
7. Compare device_count with previous_tty_count
8. If count changed:
   a. Log: "Detected N devices: ..."
   b. Call _update_config_file(device_count)
   c. Update previous_tty_count
9. If device path changed:
   a. Log: "Updated new device path: ..."
   b. Call _update_config_file(device_count)
10. Return eventtime + update_timer (reschedule)
```

**Key variables used:**
- `device`, `device_node`, `devlinks`, `serial`, `serial_by_id`
- `device_count`, `previous_tty_count`
- `bootloader1_by_id`, `bootloader2_by_id`, `bootloader_by_old_id`
- `mcu_version`, `file_version`, `file_version_str`
- `condition_1`, `condition_2` (boolean flags for decision logic)
- `other_id` (for checking additional serial IDs)

### `monitor_serial_devices()`

**Module-level function** (not a method). Uses `pyudev` for real-time USB monitoring.

**Reconstructed flow:**

```python
context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by(subsystem='tty')

# Uses 4 generator expressions (genexpr through generator3)
# to process device lists and filter for Box devices

for device in context.list_devices(subsystem='tty'):
    devlinks = device.get('DEVLINKS', '')
    # Check if 'Virtual_ComPort' in devlinks
    # Check if 'QIDI_BOX' in devlinks
    device_node = device.device_node
    # Extract serial-by-id path from /dev/serial/by-id/
```

The 4 generator expressions correspond to different filtering/mapping operations on the device list.

### `BoxDetect._update_config_file(self, device_count)`

**Config file update logic.** 7,204 bytes -- second largest method.

**Reconstructed flow:**

```python
def _update_config_file(self, device_count):
    # Select source template based on device count
    if device_count == 0:
        src = self.src_box_cfg_with_0  # /home/mks/cfg_with_0
    elif device_count == 1:
        src = self.src_box_cfg_with_1  # /home/mks/cfg_with_1
    elif device_count == 2:
        src = self.src_box_cfg_with_2  # /home/mks/cfg_with_2
    elif device_count == 3:
        src = self.src_box_cfg_with_3  # /home/mks/cfg_with_3
    elif device_count == 4:
        src = self.src_box_cfg_with_4  # /home/mks/cfg_with_4
    else:
        logging.warning("Unexpected device count or mismatch detected.")
        return

    dst = self.dst_box_cfg  # /home/mks/printer_data/config/box.cfg

    # Compare source template with current config
    if not filecmp.cmp(src, dst, shallow=False):
        # Files differ -- update needed
        shutil.copy(src, dst)

    # Update saved variables with new box count
    # Runs: SAVE_VARIABLE VARIABLE=box_count VALUE=<device_count>
    self.gcode.run_script("SAVE_VARIABLE VARIABLE=box_count VALUE=%d" % device_count)

    # Trigger restart
    self._request_restart()
```

### `BoxDetect.count_box_includes(self, config_content)`

**Counts `[include boxN.cfg]` directives** in a config file.

**Reconstructed flow:**

```python
def count_box_includes(self, config_content):
    pattern = r'\[include box(\d+)\.cfg\]'
    matches = re.findall(pattern, config_content)
    count = len(matches)
    return count
```

Uses `re.findall()` with the pattern `\[include box(\d+)\.cfg\]` to find all Box include directives and returns the count.

### `BoxDetect.get_config_mcu_serials(self)`

**Reads MCU serial IDs from config files.** 5,176 bytes.

**Reconstructed flow:**

```python
def get_config_mcu_serials(self):
    # Uses configparser to parse config files
    configfile = configparser.ConfigParser(delimiters=('=',))

    # Reads from box config files
    # Looks for [mcu mcu_box] sections
    # Extracts 'serial' values

    # References: config_serial, config_serial_1, config_serial_2,
    #             config_serial_3, config_serial_4
    # These correspond to serial IDs for up to 4 Box MCUs

    # Reads sections, checks has_section("mcu mcu_box")
    # Gets serial values via get_value_by_key or items()

    config_files = [
        "/home/mks/printer_data/config/box1.cfg",
        "/home/mks/printer_data/config/box2.cfg",
        # ... potentially more
    ]

    for config_file in config_files:
        # Parse each file, extract [mcu mcu_box] serial
        pass

    return {
        'config_serial_1': serial_1,
        'config_serial_2': serial_2,
        # etc.
    }
```

### `BoxDetect.get_check_serials_id(self)`

**Cross-checks detected serial IDs against configured ones.** 3,832 bytes.

Uses the serial IDs from `get_config_mcu_serials()` and compares them with currently detected device serial paths from `/dev/serial/by-id/`. References `config_mcu_serial`, `serial_by_id`, and comparison logic.

### `BoxDetect._request_restart(self)`

**Triggers a Klipper firmware restart.** 2,888 bytes.

```python
def _request_restart(self):
    # Wait for pending moves to complete
    toolhead = self.printer.lookup_object("toolhead")
    toolhead.wait_moves()

    # Send restart command via gcode
    self.printer.send_event("gcode:request_restart")

    # Or possibly:
    self.gcode.run_script("request_restart")

    # May also call request_exit on the reactor
    self.reactor.request_exit()
```

### `is_monitor_config_file_empty()`

**Module-level function.** Checks if the Box monitor config file is empty/missing. 3,052 bytes.

Likely reads `DST_BOX_CFG` (`/home/mks/printer_data/config/box.cfg`) and checks if it has content or if Box includes are present.

### `update_monitor_config_file()`

**Module-level function.** The largest function at 11,812 bytes. Handles the complete config file update workflow.

This appears to be a more comprehensive version of the config update that:
1. Reads the current `box.cfg`
2. Reads `saved_variables.cfg` for persisted `box_count`
3. Uses `configparser` to parse config sections
4. Checks `has_section`, iterates `sections`, reads `items`/`values`
5. May update individual box config files (`box1.cfg`, `box2.cfg`)
6. Uses `re.search` and `re.replace` for config manipulation
7. Handles the `[include boxN.cfg]` directives
8. Writes updated config using `open`/`write`/`close`

---

## USB Device Detection Details

### Device Identification Strings

The module scans `/dev/serial/by-id/` and uses `pyudev` to monitor the `tty` subsystem. Devices are identified by these strings in their `DEVLINKS` udev property:

| String | Meaning |
|--------|---------|
| `Virtual_ComPort` | STM32 USB CDC serial (Box MCU in normal mode) |
| `QIDI_BOX_V1` | Box hardware version 1 |
| `QIDI_BOX_V2` | Box hardware version 2 |
| `MKS_COLOR_BOOT` | Box in bootloader/DFU mode (V1) |
| `MKS_COLOR0_BOOT` | Box in bootloader/DFU mode (variant) |

### Version Detection

Firmware versions are extracted from the serial-by-id path using regex:
- `V1_(\d+\.\d+\.\d+)` -- e.g., `V1_1.2.3`
- `V2_(\d+\.\d+\.\d+)` -- e.g., `V2_1.0.0`

### V1-to-V2 Firmware Upgrade

When a V1 Box is detected, the module can trigger an automatic firmware upgrade:
```
/home/mks/mcu_update_BOX_to_v2.sh /home/mks/
```

The variable `mcu_box_to_v2` tracks this upgrade state.

---

## Config Template System

The module uses 5 pre-built config templates stored at `/home/mks/`:

| Template | Boxes | What it configures |
|----------|-------|--------------------|
| `/home/mks/cfg_with_0` | 0 | No Box hardware -- empty/disabled config |
| `/home/mks/cfg_with_1` | 1 | Single Box -- includes box1.cfg |
| `/home/mks/cfg_with_2` | 2 | Two Boxes -- includes box1.cfg + box2.cfg |
| `/home/mks/cfg_with_3` | 3 | Three Boxes |
| `/home/mks/cfg_with_4` | 4 | Four Boxes (maximum) |

**Deployment flow:**
1. Count USB serial devices matching Box identifiers
2. Select `cfg_with_N` based on count
3. Compare with current `/home/mks/printer_data/config/box.cfg` using `filecmp.cmp(shallow=False)`
4. If different, copy template to `box.cfg` with `shutil.copy`
5. Persist box count: `SAVE_VARIABLE VARIABLE=box_count VALUE=N`
6. Trigger Klipper restart

---

## Saved Variables Integration

The module reads and writes to `/home/mks/printer_data/config/saved_variables.cfg`:
- **Reads:** `box_count` (to know previous state)
- **Writes:** `SAVE_VARIABLE VARIABLE=box_count VALUE=N` via Klipper's G-code
- **Reset:** `SAVE_VARIABLE VARIABLE=box_count VALUE=0` (when no boxes detected)

This uses Klipper's `save_variables` system to persist the Box count across restarts, so the module knows if the configuration has actually changed.

---

## Timer/Event System

- **Event registration:** `klippy:ready` triggers `_handle_ready`
- **Timer:** `serial_monitor_timer` runs `monitor_serial_by_id` periodically via `reactor.register_timer`
- **Timer update:** Returns `eventtime + update_timer` to reschedule (the interval is stored in `update_timer`)
- **Restart trigger:** Sends `gcode:request_restart` event

---

## Generator Objects

The module defines 4 generator scope structs, all within `monitor_serial_devices`:

1. `__pyx_scope_struct__genexpr` -- Primary device filtering
2. `__pyx_scope_struct_1_genexpr` -- Secondary filtering/mapping
3. `__pyx_scope_struct_2_genexpr` -- Additional device processing
4. `__pyx_scope_struct_3_genexpr` -- Final device list generation

Each has `tp_new`, `tp_dealloc`, and `tp_traverse` methods, plus a generator body (`__pyx_gb_...`). Each generator body is ~1,040 bytes, suggesting similar filtering logic applied to different device properties.

---

## Key Observations

1. **Max 4 Boxes:** The template system supports 0-4 Boxes (cfg_with_0 through cfg_with_4)
2. **Auto-upgrade:** V1 Boxes are automatically upgraded to V2 firmware via a shell script
3. **Hot-plug support:** The `pyudev` monitor watches for USB connect/disconnect events in real-time
4. **Non-invasive:** Uses `filecmp.cmp` to avoid unnecessary file writes and restarts
5. **Klipper integration:** Uses Klipper's reactor timer, event handler, save_variables, and gcode systems
6. **MCU serial tracking:** Maintains up to 4 serial IDs (`config_serial_1` through `config_serial_4`) for multi-Box setups
7. **Bootloader detection:** Can detect Boxes in bootloader mode (`MKS_COLOR_BOOT`, `MKS_COLOR0_BOOT`), likely for firmware flashing
8. **Templates are external:** The actual config content lives in `/home/mks/cfg_with_N` files, not embedded in the binary -- these template files should be examined separately to see the exact config generated

---

## Radare2 Analysis Notes

- **Tool:** radare2 6.1.2 on macOS arm64, analyzing aarch64 Linux ELF (cross-architecture)
- **Decompiler:** Neither `r2dec` (pdd) nor `r2ghidra` (pdg) were available; analysis relied on disassembly (`pdf`) and string extraction (`iz`, `izz`, `strings`)
- **Approach:** Symbol names from the non-stripped binary + comprehensive string analysis + function size/structure analysis
- **Confidence:** High for function signatures, constants, and data flow; medium for exact control flow within functions (would need a decompiler or manual ARM64 instruction tracing for precise logic)
