# box_extras.so - Reverse Engineering Analysis

**Binary:** `/klippy_extras/box_extras.so`
**Type:** ELF 64-bit LSB shared object, ARM aarch64
**Compiler:** GCC 10.2.1 (Debian), Cython 3.0.11
**CPython:** 3.9 extension module
**Source:** `/home/mks/klipper/klippy/extras/box_extras.c` (Cython-generated C)
**Original:** `box_extras.py` (Cython source, not available)
**Size:** ~4.6 MB, 208 functions detected
**Analysis tool:** radare2 6.1.2 (cross-arch aarch64 on darwin-arm64)
**Analysis date:** 2026-03-22

---

## Table of Contents

1. [Module Overview](#module-overview)
2. [Classes](#classes)
3. [G-code Command Registration](#g-code-command-registration)
4. [Key Method Analysis](#key-method-analysis)
5. [G-code Sequences](#g-code-sequences)
6. [State Variables](#state-variables)
7. [Error Codes](#error-codes)
8. [Hardware Interaction](#hardware-interaction)
9. [Filament Drying System](#filament-drying-system)
10. [Tool Change System](#tool-change-system)
11. [Buffer Monitoring System](#buffer-monitoring-system)
12. [Numerical Constants](#numerical-constants)

---

## Module Overview

`box_extras.so` is the primary Klipper extension for the Qidi Box multi-material system. It manages:
- Filament slot selection and switching (up to 4 slots)
- Tool change operations (unload/cut/load sequences)
- Filament drying via box heaters
- Buffer monitoring (filament buffer state detection)
- RFID filament identification
- Endstop management for extruder (e_endstop) and box (b_endstop)
- Stepper motor control for the box feed system
- Print resume after filament errors

The module is loaded via `load_config()` (standard Klipper extra entry point).

---

## Classes

### BoxExtras (main class)
The primary class. Manages all box operations, heater control, filament slot logic, RFID, buffer monitoring, drying, and gcode command handlers.

**Size:** ~18,432 bytes for `set_box_temp` alone; the `__init__` implementation is ~4,936 bytes.

### ToolChange
Handles tool change (filament swap) operations during printing. Provides `move()`, position tracking, and the TOOL_CHANGE_START/END command pair.

### BoxOutput
Digital output pin control for box hardware. Methods: `__init__`, `set_pin`.

### BoxEndstop
Endstop management for the box system. Methods: `__init__`, `add_stepper`, `get_endstops`, `set_scram`.

### BoxButton
Button/switch input handler for the box. Method: `__init__`.

---

## G-code Command Registration

The following G-code commands are registered by this module (extracted from string references to `register_command`):

| Command | Handler Method | Description |
|---------|---------------|-------------|
| `ENABLE_BOX_DRY` | `cmd_ENABLE_BOX_DRY` | Start filament drying for a box unit |
| `DISABLE_BOX_DRY` | `cmd_DISABLE_BOX_DRY` | Stop filament drying |
| `BOX_PRINT_START` | `cmd_BOX_PRINT_START` | Initialize box system for a print job |
| `TOOL_CHANGE_START` | `cmd_TOOL_CHANGE_START` | Begin tool/filament change sequence |
| `TOOL_CHANGE_END` | `cmd_TOOL_CHANGE_END` | Complete tool/filament change sequence |
| `CUT_FILAMENT` | `cmd_CUT_FILAMENT` | Activate filament cutter mechanism |
| `TIGHTEN_FILAMENT` | `cmd_TIGHTEN_FILAMENT` | Tighten filament in the feed path |
| `RUN_STEPPER` | `cmd_RUN_STEPPER` | Directly control a box stepper motor |
| `CLEAR_OOZE` | `cmd_CLEAR_OOZE` | Clear filament ooze from nozzle |
| `CLEAR_FLUSH` | `cmd_CLEAR_FLUSH` | Clear flush material |
| `CLEAR_RUNOUT_NUM` | `cmd_CLEAR_RUNOUT_NUM` | Reset filament runout counter |
| `CLEAR_TOOLCHANGE_STATE` | `cmd_CLEAR_TOOLCHANGE_STATE` | Reset tool change state machine |
| `INIT_BUFFER_STATE` | `cmd_INIT_BUFFER_STATE` | Initialize buffer monitoring state |
| `INIT_RFID_READ` | `cmd_INIT_RFID_READ` | Trigger RFID filament identification |
| `INIT_MAPPING_VALUE` | `cmd_INIT_MAPPING_VALUE` | Initialize filament-to-slot mapping |
| `INIT_SYNC_BUFFER_STATE` | `init_sync_buffer_state` | Synchronize buffer state |
| `BUFFER_MONITORING` | `cmd_BUFFER_MONITORING` | Enable/disable buffer monitoring |
| `AUTO_RELOAD_FILAMENT` | `cmd_AUTO_RELOAD_FILAMENT` | Automatic filament reload after runout |
| `RELOAD_ALL` | `cmd_RELOAD_ALL` | Reload all filament slots |
| `TRY_RESUME_PRINT` | `cmd_TRY_RESUME_PRINT` | Attempt to resume print after error |
| `RESUME_PRINT_1` | `cmd_RESUME_PRINT_1` | Secondary print resume handler |
| `DISABLE_BOX_HEATER` | `cmd_disable_box_heater` | Turn off box heater |
| `SET_INIT_ROTATION_DISTANCE` | `set_init_rotation_distance` | Set initial extruder rotation distance |
| `BOX_TEMP_SET` | (likely via set_box_temp) | Set box temperature target |
| `EXTRUDER_LOAD` | `cmd_EXTRUDER_LOAD` | Load filament into extruder |
| `EXTRUDER_UNLOAD` | `cmd_EXTRUDER_UNLOAD` | Unload filament from extruder |
| `SLOT_UNLOAD` | `cmd_SLOT_UNLOAD` | Unload filament from a slot |
| `SLOT_RFID_READ` | `cmd_SLOT_RFID_READ` | Read RFID tag on a specific slot |
| `DISABLE_ALL_SENSOR` | (referenced in gcode) | Disable all filament sensors |

---

## Key Method Analysis

### cmd_ENABLE_BOX_DRY (0x3c980, 8148 bytes)

**Purpose:** Starts the filament drying process for a specific Box unit.

**Parameters:** Takes 2 positional arguments (self, gcmd). Uses a closure/lambda pattern (creates a `__pyx_scope_struct_1_cmd_ENABLE_BOX_DRY` scope object).

**Logic (reconstructed from strings and control flow):**
1. Validates box number (errors with `!!Invalid BOX number. Available: 1-` if out of range)
2. Creates a drying state setter via `_create_drying_state_setter()`
3. The setter is a closure that captures the box instance
4. Registers a timer callback (`heating_handler`) for periodic temperature management
5. Sets the `is_drying` state flag
6. Sets `box_drying_state` via `set_box_drying_state`
7. Logs `BOX_DRY started for BOX` + box number
8. Runs the heater command via `SET_HEATER_TEMPERATURE HEATER=heater_box` with ` TARGET=` parameter

**Related lambda:** `cmd_ENABLE_BOX_DRY_lambda` (0x15e40, 892 bytes) -- a callback used for the drying timer or state management.

### cmd_DISABLE_BOX_DRY (0x22880, 5396 bytes)

**Purpose:** Stops the filament drying process.

**Logic (reconstructed):**
1. Validates the box is actually drying
2. Unregisters the heating timer via `unregister_timer`
3. Sends `SET_HEATER_TEMPERATURE HEATER=heater_box` with ` TARGET=0` to turn off heater
4. Clears `is_drying` flag
5. Updates `box_drying_state`
6. Logs `DISABLE_BOX_DRY for BOX` + box number
7. If no other boxes are drying: `No active heating for BOX`

### _create_drying_state_setter / set_drying_state (0x161c0, 6068 bytes)

**Purpose:** Factory method that creates a closure for managing per-box drying state. The inner `set_drying_state` function captures `self` and box references.

**Logic:**
- Creates a closure that can set/clear the drying state for a specific box
- Used by `cmd_ENABLE_BOX_DRY` to create slot-specific state management
- References `self` via closure (free variable pattern in Cython)

### heating_handler (0x20220, 9824 bytes)

**Purpose:** Periodic timer callback that manages box heater temperature during drying.

**Parameters:** Takes 5 keyword arguments: `self`, `eventtime`, plus additional parameters for temperature/timer management.

**Logic (reconstructed from strings and structure):**
1. Called periodically via Klipper's reactor timer system
2. Reads current box temperatures (`box_temp`, `cache_temp`, `input_temp`)
3. Compares against `box_max_temp`, `box_min_temp`, `current_box_max_temp`
4. Manages `heating_timers` list
5. Checks `end_time` / `END_TIME` / `end_time_h` for drying duration expiry
6. Tracks `start_time`, `last_time` for timing
7. On error: logs `!!Error in heating:` + exception info
8. When drying time expires: sends `DISABLE_BOX_DRY` command
9. Uses `estimated_print_time` for timing synchronization
10. References `timer_info`, `old_timer`, `update_timer`
11. Manages `dry_state` transitions

**Temperature flow:**
- Gets temperatures via `get_temp_by_slot`, `get_temp_by_num`, `get_box_temp_by_slot`
- Sets temperature with `set_temp`, `set_box_temp`
- Uses `curt_filament_max_temp` as safety limit
- Reads from `officiall_filas_list.cfg` via ConfigParser for filament presets

### cmd_CUT_FILAMENT (0x257e0, 5772 bytes)

**Purpose:** Activates the filament cutting mechanism to sever filament during tool changes.

**Logic (reconstructed):**
1. Executes the cutting sequence: `CUT_FILAMENT_1\nMOVE_TO_TRASH\nM83\nG1 E-60 F300`
   - `CUT_FILAMENT_1` -- activates the physical cutter mechanism
   - `MOVE_TO_TRASH` -- moves toolhead to the waste/purge area
   - `M83` -- set extruder to relative mode
   - `G1 E-60 F300` -- retract 60mm of filament at 300mm/min after cutting
2. Uses `run_script_from_command` to execute gcode sequences
3. References `gcmd` for the command context

### cmd_BOX_PRINT_START (0x46724, 10428 bytes)

**Purpose:** Initializes the box system at the beginning of a multi-material print.

**Parameters:** Takes keyword arguments including `SLOT`, `HOTENDTEMP`, `TEMP`, possibly `EXTRUDER`.

**Logic (reconstructed):**
1. Validates box is enabled (`enable_box` check)
2. Checks if box is currently drying, and if so, may disable drying first
3. Sets `box_print_heat_state`
4. Reads `HOTENDTEMP` parameter for hotend target temperature
5. Reads `SLOT` parameter for initial slot selection
6. Reads `TEMP` for box heater target
7. Sets `init_slot`, `init_load_slot`, `selected_slot`
8. Configures `filament_slot` mapping
9. May run `INIT_RFID_READ\nM400\n` to identify loaded filament
10. Sets up the `preheat_gcode` / `heat_box_command`
11. Runs `INIT_BUFFER_STATE` and `INIT_SYNC_BUFFER_STATE`
12. References `print_stats`, `idle_timeout`, `toolhead`
13. Initializes `extrude_state`, `extrude_gcode`
14. Sets `is_tool_change = False` initially
15. May log `Not using BOX, not turning on the heater.` if box not needed

### cmd_TOOL_CHANGE_START (0x51fe4, 5332 bytes)

**Purpose:** Begins a filament swap during multi-material printing.

**Parameters:** Keyword args including `SLOT` (target slot), likely `TEMP`.

**Logic (reconstructed from strings and gcode sequences):**
1. Sets `is_tool_change = True`
2. Records current position (`last_position`, `last_x`, `last_y`)
3. Determines the `unload_slot` (current) and target `next_slot`
4. Determines if cutting is needed by checking `change_slot_gcode_cut` vs `change_slot_gcode`:
   - **With cut:** `MOVE_TO_TRASH\nM109 S{temp}\nM400\nCUT_FILAMENT\nMOVE_TO_TRASH\nEXTRUDER_UNLOAD SLOT={unload_slot}\nEXTRUDER_LOAD SLOT={init_load_slot}\n`
   - **Without cut:** `MOVE_TO_TRASH\nM109 S{temp}\nM400\nEXTRUDER_UNLOAD SLOT={unload_slot}\nEXTRUDER_LOAD SLOT={init_load_slot}\n`
   - **Load only (no prior filament):** `MOVE_TO_TRASH\nM109 S{temp}\nEXTRUDER_LOAD SLOT={init_load_slot}\n`
5. Runs the appropriate gcode sequence via `run_script`
6. Updates `selected_slot` to new slot
7. References `exclude_tool` (for skipping specific tools)

**Tool change sequence breakdown:**
```
MOVE_TO_TRASH              -> Move to waste/purge area
M109 S{temp}               -> Wait for hotend to reach temp
M400                       -> Wait for moves to complete
CUT_FILAMENT               -> Cut the current filament
MOVE_TO_TRASH              -> Return to waste area after cut
EXTRUDER_UNLOAD SLOT=X     -> Retract filament back to box
EXTRUDER_LOAD SLOT=Y       -> Feed new filament from target slot
```

### cmd_TOOL_CHANGE_END (0x34890, 7492 bytes)

**Purpose:** Completes the tool change operation and resumes printing.

**Logic (reconstructed):**
1. Sets `is_tool_change = False`
2. Performs purge sequence to prime new filament:
   - `M400\nM109 S{hotendtemp}\nG1 E150 F300\nM400\nM104 S0\nM106 S255\nG4 P5000\nCLEAR_OOZE\nCLEAR_FLUSH\nM106 S0`
   - Wait for moves, heat to hotend temp, extrude 150mm at 300mm/min (purge)
   - Wait, turn off hotend, fan to 100% for 5 seconds (cool ooze), clear ooze/flush, fan off
3. Performs wipe sequence:
   - `G1 Y0.5 F15000\nG1 X15 F15000\nG1 X-0.5 F5000\nG4 P1000\nG1 X1 F1000\nG1 X-0.5 F5000\nM400\n`
   - Fast Y/X moves for wiping, oscillating X for cleaning, wait
4. Alternative wipe pattern also present:
   - `G1 X15 F9000\nG1 Y0.5 F9000\n`
5. Post-wipe retract:
   - `M83\nG1 E-4 F1800\nG1 X1 F1000\nG4 P1000\nG1 X15 F3000\n`
   - Retract 4mm fast, small move, dwell 1s, move away
6. Resets `is_tool_change` and clears toolchange state
7. Updates `last_load_slot`, `had_load_slot`
8. Restores position via `reset_last_position`

### button_extruder_load (0x5d3b0 wrapper -> 0x58c90 impl, 17728 bytes)

**Purpose:** Handles the "load filament into extruder" button press or command.

**Logic (reconstructed):**
1. Checks `can_load_slot` and `had_load_slot` state
2. Validates slot selection (`selected_slot`)
3. Checks filament sensor state (`filament_detected`, `filament_present`)
4. If not detected: error `can not recognize the loaded filament`
5. Reads RFID data if available (`auto_read_rfid`, `start_rfid_read`)
6. Executes load sequence:
   - `\nG1 E25 F300\n` -- feed 25mm at 300mm/min
   - `\nG1 E100 F300\nG1 E-1 F1800\nCLEAR_FLUSH\n` -- feed 100mm, small retract, clear flush
   - `\nM83\nG1 E150 F300\n` -- relative mode, feed 150mm (full load)
7. Manages `load_success`, `init_extrude`, `had_load_extruder`
8. Updates `extrude_state`
9. Saves state via `save_variable`
10. Sets rotation distance: `call_set_rotation_distance`, `set_init_rotation_distance`
11. References `e_endstop_state` for extruder endstop detection
12. Runs `EXTRUDER_LOAD SLOT=slot{N}` gcode

### button_extruder_unload (0x36810, 11672 bytes)

**Purpose:** Handles filament unload from the extruder.

**Logic (reconstructed):**
1. Checks `extruder_unload_success` state
2. Runs unload gcode sequence:
   - `_CG28\nMOVE_TO_TRASH\nM400\n` -- conditional home, move to trash, wait
   - `_CG28\nM204 S10000\n` -- conditional home, set acceleration to 10000
   - Retraction moves (E-negative values)
3. Monitors `e_endstop_state` during retraction
4. On failure: `Extruder unloading failure.Please try again.`
5. On success: updates `from_box_unload`, `extruder_unload_success`
6. May trigger `SLOT_UNLOAD` for the box-side retraction
7. References `disable_stepper` to release motor after unload

### button_box_unload (0x5d690, 8216 bytes)

**Purpose:** Unloads filament from the box (PTFE tube side, not extruder side).

**References:** `from_box_unload`, `SLOT_UNLOAD`, `E_UNLOAD`, `disable_stepper`

### set_box_temp (0x41ae0, 18432 bytes -- largest function)

**Purpose:** Sets the box heater temperature. This is the most complex function.

**Parameters:** Multiple keyword args including `slot`, `temp`, `TEMP`, plus slot-specific temps.

**Logic (reconstructed):**
1. Resolves temperature for the specific slot from filament database
2. References `box_max_temps`, `box_max_temp`, `box_min_temp`
3. Reads filament presets from `officiall_filas_list.cfg` via ConfigParser
4. Sends `SET_HEATER_TEMPERATURE HEATER=heater_box` with ` TARGET=` value
5. If box not enabled: `Not using BOX, not turning on the heater.`
6. Error on bad slot: `!!Error setting slot`
7. Updates `cache_temp`, `print_temp`, `box_temp`
8. References `temp_values`, `temp_stepper`, `etemp`

### cmd_AUTO_RELOAD_FILAMENT (0x4c5a4, 6340 bytes)

**Purpose:** Automatically reloads filament after a runout event during printing.

**Logic (reconstructed):**
1. Called when filament runout is detected during a print
2. Sends pause command
3. Determines next available slot (`switch_next_slot`, `next_slot`)
4. Runs reload sequence:
   - `DISABLE_ALL_SENSOR\n_CG28\nMOVE_TO_TRASH\nM109 S{hotendtemp}` -- disable sensors, home, move to trash, heat
5. On failure: `Code:QDE_004_023; Message:Auto reload failed.`
6. On wrapping detection: `Code:QDE_004_013; Message:Detected wrapping filament,please check the filament.`
7. On unrecognized filament: `!!Code:QDE_004_021; Message:Unable to recognize loaded filament.`
8. References `check_wrapping_filament_state`

### cmd_RELOAD_ALL (0x6cd44, 10288 bytes)

**Purpose:** Reloads all filament slots -- likely used after refilling all 4 slots.

**References:** `RELOAD_ALL`, multiple slot iterations, `slot_count`, `slot_state`

### cmd_TRY_RESUME_PRINT (0x6ca64 wrapper -> 0x67590 impl, 16828 bytes)

**Purpose:** Attempts to resume a print after a filament error/pause.

**Logic (reconstructed):**
1. Checks print state via `print_stats`
2. Validates filament is loaded (`had_load_slot`, `load_success`)
3. Runs `BUFFER_MONITORING ENABLE=1` to re-enable monitoring
4. References `gcode_macro RESUME_PRINT`, `gcode_macro_resume`
5. Runs `RESUME_PRINT\n` gcode macro
6. On failure: `M118 Printer resume failed`
7. References `send_pause_command`, `pause_resume`

### cmd_RESUME_PRINT_1 (0x73e20 wrapper -> 0x6fc50 impl, 14692 bytes)

**Purpose:** Secondary resume handler with additional checks and state restoration.

**Logic:**
1. Restores position state
2. Runs load/purge sequence if needed
3. References `M118 box check finish\n` on success
4. Handles `TRY_MOVE_AGAIN` for retry logic

### cmd_RETRY (0x4c2c4 wrapper -> 0x48fe0 impl, 8552 bytes)

**Purpose:** Retry a failed operation step.

**Logic:**
- Reads `retry_step` parameter
- Validates format: `Invalid retry_step format`
- On no step: `No step to retry`
- References `retry_stpper` (sic -- typo in source), `step_name`
- Uses regex pattern `([a-zA-Z_]+)(\d+)_(\d+)$` to parse retry step names

### cmd_RUN_STEPPER (0x23da0, 2712 bytes)

**Purpose:** Directly controls a box stepper motor for debugging or calibration.

**Parameters:** `STEPPER` (name), `distance`, `speed`.

**Logic:**
1. Looks up stepper by name: `RUN_STEPPER STEPPER=` prefix
2. Executes `do_move` with specified distance and speed
3. References `control_stepper`, `box_stepper`, `extruder_stepper`

### cmd_TIGHTEN_FILAMENT (0x1e8c4, 5016 bytes)

**Purpose:** Tightens filament tension in the feed path, likely after a slot change.

**References:** `TIGHTEN_FILAMENT`, `need_load_stepper`, `stepper_name`

### cmd_INIT_RFID_READ (0x31810, 5456 bytes)

**Purpose:** Initiates RFID tag reading for filament identification.

**Logic:**
1. References `rfid`, `RFID`, `rfid_device`, `card_reader_`
2. Triggers `start_rfid_read`
3. Reads `filament_id`, `filament_slot`
4. Updates `can_run_init_read` state
5. References `box_rfid` (the RFID hardware interface from `box_rfid.so`)

### cmd_INIT_BUFFER_STATE (0x32d60, 5828 bytes)

**Purpose:** Initializes the buffer monitoring system state.

**Logic:**
1. Validates box enabled and slot selected
2. Error if disabled: `Box disabled or no slot selected, cannot init buffer state.`
3. Error if disabled: `Box disabled, cannot set buffer state.`
4. Error if no slot: `No slot selected, cannot init buffer state.`
5. References `buffer_state`, `buffer_init_success`, `buffer_init_length_1`, `buffer_init_length_2`
6. Success: `Init buffer state successful`

### cmd_BUFFER_MONITORING (0x61ab0, 7132 bytes)

**Purpose:** Enables or disables continuous buffer monitoring during printing.

**Parameters:** `ENABLE` (1 or 0).

**Logic:**
1. Parses `ENABLE` parameter
2. Error message hint: `intput buffer state 'ENABLE= 1/0'`
3. References `buffer_enabled`, `input_buffer_enable`
4. When enabled, starts `_buffer_response_timer`

### _buffer_response_timer (0x64e74, 9396 bytes)

**Purpose:** Periodic timer that checks the buffer state.

**Logic:**
1. Monitors `buffer_state`, `b_state`, `e_state`, `r_state`
2. References `buffer_pre_length`, `buffer_again`, `buffer_1`
3. On error: `buffer state error, auto reset buffer`
4. References `advance_activated`, `advance_print_time`
5. May trigger `PAUSE` on buffer issues

### handle_connect (0x3c800 wrapper -> 0x39620 impl, 8700 bytes)

**Purpose:** Event handler called when Klipper connects. Initializes all box hardware.

**Registered via:** `register_event_handler("klippy:ready", handle_connect)`

**Logic:**
1. Looks up Klipper objects: `toolhead`, `gcode`, `gcode_move`, `idle_timeout`
2. Initializes `print_stats`, `pause_resume`
3. Sets up `save_variables` interface
4. Initializes endstops and steppers
5. Runs `delayed_init_rfid` for RFID hardware init
6. Sets up `buffer_button_callback`, `b_button_callback`

---

## G-code Sequences

These are the complete multi-line G-code sequences embedded in the binary. They represent the core operational sequences.

### Tool Change - With Cutting
```gcode
MOVE_TO_TRASH
M109 S{temp}
M400
CUT_FILAMENT
MOVE_TO_TRASH
EXTRUDER_UNLOAD SLOT={unload_slot}
EXTRUDER_LOAD SLOT={init_load_slot}
```

### Tool Change - Without Cutting
```gcode
MOVE_TO_TRASH
M109 S{temp}
M400
EXTRUDER_UNLOAD SLOT={unload_slot}
EXTRUDER_LOAD SLOT={init_load_slot}
```

### Tool Change - Load Only (no prior filament)
```gcode
MOVE_TO_TRASH
M109 S{temp}
EXTRUDER_LOAD SLOT={init_load_slot}
```

### Filament Cut Sequence
```gcode
CUT_FILAMENT_1
MOVE_TO_TRASH
M83
G1 E-60 F300
```
*Cut filament, move to trash, retract 60mm at 300mm/min*

### Post-Tool-Change Purge Sequence
```gcode
M400
M109 S{hotendtemp}
G1 E150 F300
M400
M104 S0
M106 S255
G4 P5000
CLEAR_OOZE
CLEAR_FLUSH
M106 S0
```
*Wait, heat hotend, extrude 150mm purge, wait, heater off, fan 100%, dwell 5s, clear ooze/flush, fan off*

### Nozzle Wipe Sequence (fast)
```gcode
G1 Y0.5 F15000
G1 X15 F15000
G1 X-0.5 F5000
G4 P1000
G1 X1 F1000
G1 X-0.5 F5000
M400
```
*Fast wipe motion, oscillating X for cleaning*

### Nozzle Wipe Sequence (slow)
```gcode
G1 X15 F9000
G1 Y0.5 F9000
```

### Post-Wipe Retract
```gcode
M83
G1 E-4 F1800
G1 X1 F1000
G4 P1000
G1 X15 F3000
```
*Relative mode, retract 4mm fast, small move, dwell 1s, move away*

### Ooze Brush Sequence (aggressive)
```gcode
MOVE_TO_TRASH
M204 S5000
G1 X100 F200
G1 X90 F200
G1 X100 F200
G1 X115 F4000
G1 X98 F8000
G1 X115 F4000
G1 X98 F8000
G1 X115 F4000
G1 X98 F8000
G1 X115 F4000
G1 X98 F8000
G1 X115 F4000
G1 X98 F8000
```
*Move to trash, set accel 5000, slow approach, then 5x fast oscillation between X98-X115 for brush wiping*

### Quick Ooze Brush
```gcode
MOVE_TO_TRASH
M204 S5000
G1 X140 F8000
MOVE_TO_TRASH
```

### Extruder Load Sequences
```gcode
G1 E25 F300     (initial feed - 25mm at 300mm/min)
G1 E100 F300    (main feed - 100mm at 300mm/min)
G1 E-1 F1800   (small retract after feed)
CLEAR_FLUSH
M83
G1 E150 F300    (full load - 150mm at 300mm/min)
```

### Auto Reload Pre-sequence
```gcode
DISABLE_ALL_SENSOR
_CG28
MOVE_TO_TRASH
M109 S{hotendtemp}
```

### Conditional Home + Preparation
```gcode
_CG28
M204 S10000
```
*Conditional home, set acceleration to 10000mm/s^2*

### Conditional Home + Move to Trash
```gcode
_CG28
MOVE_TO_TRASH
M400
```

---

## State Variables

Instance attributes tracked on the BoxExtras object (extracted from string references):

### Slot/Filament State
| Variable | Purpose |
|----------|---------|
| `selected_slot` | Currently selected filament slot |
| `init_slot` | Initial slot at print start |
| `init_load_slot` | Slot being loaded during initialization |
| `last_load_slot` | Previously loaded slot |
| `had_load_slot` | Whether a slot has been loaded |
| `can_load_slot` | Whether loading is currently possible |
| `next_slot` | Next slot for tool change |
| `filament_slot` | Filament-to-slot mapping |
| `slot_count` | Number of available slots |
| `slot_state` | Per-slot state tracking |
| `slot_value` | Per-slot configuration values |
| `filament_id` | RFID-read filament identifier |
| `filament_detected` | Whether filament is physically detected |
| `filament_present` | Whether filament is present in path |

### Temperature State
| Variable | Purpose |
|----------|---------|
| `box_temp` | Current box temperature |
| `cache_temp` | Cached temperature value |
| `input_temp` | User-requested temperature |
| `print_temp` | Temperature during printing |
| `box_max_temp` | Maximum allowed box temperature |
| `box_min_temp` | Minimum box temperature threshold |
| `box_max_temps` | Per-slot max temperatures |
| `current_box_max_temp` | Current active max temp limit |
| `curt_filament_max_temp` | Current filament's max temp rating |
| `etemp` | Extruder temperature reference |
| `hotendtemp` | Hotend target temperature |
| `temp_values` | Temperature value storage |

### Drying State
| Variable | Purpose |
|----------|---------|
| `is_drying` | Whether drying is active |
| `dry_state` | Drying state machine value |
| `box_drying_state` | Per-box drying state |
| `heating_timers` | List of active heating timer handles |
| `start_time` | Drying start time |
| `end_time` / `end_time_h` | Drying end time / duration in hours |
| `last_time` | Last timer check time |

### Buffer/Feed State
| Variable | Purpose |
|----------|---------|
| `buffer_state` | Current buffer monitoring state |
| `buffer_enabled` | Whether buffer monitoring is active |
| `buffer_init_success` | Whether buffer init succeeded |
| `buffer_init_length_1` | Buffer initial length param 1 |
| `buffer_init_length_2` | Buffer initial length param 2 |
| `buffer_pre_length` | Pre-feed buffer length |
| `buffer_again` | Buffer retry flag |
| `buffer_1` | Buffer sub-state |
| `b_state` | Box-side buffer state |
| `e_state` | Extruder-side buffer state |
| `r_state` | RFID/read state |

### Endstop State
| Variable | Purpose |
|----------|---------|
| `e_endstop` | Extruder endstop object |
| `e_endstop_pin` | Extruder endstop pin config |
| `e_endstop_state` | Extruder endstop triggered state |
| `e_endstop_timer` | Extruder endstop polling timer |
| `b_endstop` | Box endstop object |
| `b_endstop_pin` | Box endstop pin config |
| `b_endstop_state` | Box endstop triggered state |
| `b_endstop_timer` | Box endstop polling timer |
| `r_endstop_state` | RFID endstop state |
| `e_expected_trigger` | Expected extruder trigger state |

### Stepper/Motor State
| Variable | Purpose |
|----------|---------|
| `box_stepper` | Box feed stepper motor |
| `control_stepper` | Control stepper reference |
| `extruder_stepper` | Extruder stepper reference |
| `buff_control_stepper` | Buffer control stepper |
| `next_slot_stepper` | Stepper for next slot |
| `loaded_stepper` | Currently loaded stepper |
| `need_load_stepper` | Stepper that needs loading |
| `temp_stepper` | Temporary stepper reference |
| `init_rotation_distance` | Initial extruder rotation distance |
| `real_rotation_distance` | Actual rotation distance |
| `low_rotation_distance` | Low-range rotation distance |
| `new_rotation_distance` | Updated rotation distance |
| `dis_dif` | Distance difference |
| `e_distance` | Extruder distance tracked |

### Tool Change State
| Variable | Purpose |
|----------|---------|
| `is_tool_change` | Whether tool change is in progress |
| `change_slot_gcode` | Gcode for slot change (no cut) |
| `change_slot_gcode_cut` | Gcode for slot change (with cut) |
| `load_slot_gcode` | Gcode for slot loading |
| `exclude_tool` | Tool to exclude from changes |

### Operation State
| Variable | Purpose |
|----------|---------|
| `enable_box` | Whether box is enabled |
| `box_count` | Number of box units |
| `box_operate_state` | Current operation state |
| `box_print_heat_state` | Heating state during print |
| `extrude_state` | Extruder state machine |
| `extrude_gcode` | Current extrude gcode |
| `load_success` | Whether last load succeeded |
| `extruder_unload_success` | Whether last unload succeeded |
| `home_success` | Whether homing succeeded |
| `had_success` | General success flag |
| `had_load_extruder` | Whether extruder has been loaded |
| `from_box_unload` | Whether unload came from box side |
| `advance_activated` | Whether pressure advance is active |
| `retry_step` | Current retry step name |

### Output Pins
| Variable | Purpose |
|----------|---------|
| `b_output` | Box output pin |
| `e_output` | Extruder output pin |
| `buffer_pin` | Buffer state pin |

---

## Error Codes

| Code | Severity | Message |
|------|----------|---------|
| `QDE_004_010` | Fatal (`!!`) | The current feeding status is incorrect. Please exit the filament from the extruder. |
| `QDE_004_013` | Warning | Detected wrapping filament, please check the filament. |
| `QDE_004_014` | Warning | Parameter setting error, please reset. |
| `QDE_004_021` | Fatal (`!!`) | Unable to recognize loaded filament. |
| `QDE_004_023` | Warning | Auto reload failed. |
| (no code) | Error (`!!`) | Error in heating: [exception] |
| (no code) | Error (`!!`) | Error setting slot |
| (no code) | Error (`!!`) | Invalid BOX number. Available: 1-[count] |
| (no code) | Info | Extruder unloading failure. Please try again. |
| (no code) | Info | Unable to recognize loaded filament. |

Error prefix conventions:
- `!!` prefix = fatal error displayed to user (triggers action)
- `Code:` prefix = structured error code for UI parsing
- No prefix = log message

---

## Hardware Interaction

### Stepper Motors
- `box_stepper` -- main box feed stepper (via `box_stepper.so`)
- `extruder_stepper` -- extruder motor
- `control_stepper` -- generic control stepper
- `buff_control_stepper` -- buffer tension control stepper
- Controlled via `do_move`, `disable_stepper`, `set_rotation_distance`

### Endstops
- `e_endstop` -- extruder-side endstop (filament present detection)
- `b_endstop` -- box-side endstop (slot detection)
- Queried via `query_endstops`, polled via timers (`e_endstop_timer`, `b_endstop_timer`)
- Can be set to scram (emergency stop) via `set_scram`

### Digital Outputs
- `b_output` -- box output pin (likely cutter solenoid or feed clutch)
- `e_output` -- extruder output pin
- `buffer_pin` -- buffer state indicator
- Controlled via `set_digital`, `set_pin`, `setup_pin`

### Buttons/Switches
- `b_button` -- box button (slot button)
- `buffer_button` -- buffer state button/switch
- Registered via `register_buttons`
- Callbacks: `b_button_callback`, `buffer_button_callback`

### RFID
- Interfaces with `box_rfid` (from `box_rfid.so`)
- Reads `filament_id` from RFID tags on filament spools
- Uses `card_reader_` prefix for device addressing
- Controlled via `start_rfid_read`, `auto_read_rfid`

### Heater
- Box heater controlled via `SET_HEATER_TEMPERATURE HEATER=heater_box TARGET=X`
- Heater object accessed via `get_heater`

### Sensors
- Filament switch sensor: `filament_switch_sensor filament_switch_sensor`
- Runout helper: `runout_helper`, `runout_` prefix
- Device monitoring via `pyudev` (Linux device monitoring)

---

## Filament Drying System

The drying system works as follows:

1. **Activation:** `ENABLE_BOX_DRY` starts drying for a specific box
2. **Timer:** A `heating_handler` timer callback runs periodically
3. **Temperature regulation:** The handler monitors box temperature and adjusts the heater target
4. **Duration tracking:** Uses `start_time`, `end_time`, `end_time_h` (hours)
5. **State management:** `is_drying`, `dry_state`, `box_drying_state` track per-box drying status
6. **Config:** Reads from `officiall_filas_list.cfg` for per-filament drying temperatures
7. **Shutdown:** `DISABLE_BOX_DRY` stops the timer and sets heater to 0

The drying state is persisted via `save_variable` / `save_variables` so it survives restarts.

---

## Tool Change System

The ToolChange class manages filament switching during multi-material prints:

1. **Position tracking:** Records (`last_x`, `last_y`, `last_position`) before moving to trash
2. **Move transform:** Uses `set_move_transform` / `next_transform` for coordinate system management
3. **Slot switching:** Three modes:
   - Load only (fresh start, no cut needed)
   - Unload+Load (no cutting, just retract and feed)
   - Cut+Unload+Load (cut filament, retract, load new)
4. **Purge:** 150mm extrusion at 300mm/min with fan cooling for ooze management
5. **Wipe:** Oscillating X/Y moves across a brush/wiper
6. **Resume:** Restores position and continues print

### Key Coordinates (from G-code)
- Wipe area: X=98 to X=115 (brush location)
- Trash/purge area: Referenced via `MOVE_TO_TRASH` macro
- Wipe Y offset: 0.5mm
- Wipe X range: -0.5 to 15mm in fine cleaning mode

---

## Buffer Monitoring System

The buffer system monitors filament tension between the box and the extruder:

1. **Init:** `INIT_BUFFER_STATE` calibrates the buffer sensors
2. **Enable:** `BUFFER_MONITORING ENABLE=1` starts continuous monitoring
3. **Timer:** `_buffer_response_timer` runs periodically to check buffer state
4. **States:** `buffer_state`, `b_state` (box side), `e_state` (extruder side)
5. **Recovery:** On error, auto-resets: `buffer state error, auto reset buffer`
6. **Pause:** Can trigger `PAUSE` if buffer problems detected
7. **Lengths:** `buffer_init_length_1`, `buffer_init_length_2`, `buffer_pre_length` for calibration

---

## Numerical Constants

### Speeds (mm/min)
| Value | Context |
|-------|---------|
| F200 | Slow approach for brush cleaning |
| F300 | Standard filament feed/retract speed |
| F1000 | Fine wipe movement |
| F1800 | Fast retract |
| F3000 | Medium travel |
| F4000 | Fast oscillation (brush) |
| F5000 | Medium-fast wipe |
| F8000 | Fast oscillation (brush), fast travel |
| F9000 | Fast wipe |
| F15000 | Maximum wipe speed |

### Distances (mm)
| Value | Context |
|-------|---------|
| E25 | Initial filament feed (short) |
| E100 | Main filament feed |
| E150 | Full purge extrusion |
| E-1 | Tiny retract after feed |
| E-4 | Post-wipe retract |
| E-60 | Post-cut retract |

### Accelerations (mm/s^2)
| Value | Context |
|-------|---------|
| S5000 | Brush wipe acceleration |
| S10000 | High-speed operation acceleration |

### Fan
| Value | Context |
|-------|---------|
| S255 | Fan 100% (M106 S255) for ooze cooling |
| S0 | Fan off |

### Timing (ms)
| Value | Context |
|-------|---------|
| P1000 | 1 second dwell during wipe |
| P5000 | 5 second dwell for cooling |

### Positions (mm)
| Value | Context |
|-------|---------|
| X90-X115 | Brush wipe oscillation range |
| X140 | Quick wipe extension |
| Y0.5 | Wipe Y offset |

---

## Function Address Map

| Address | Size | Function |
|---------|------|----------|
| 0x0000b868 | 4660 | `__pyx_pymod_exec_box_extras` (module init) |
| 0x00010b90 | 16 | `PyInit_box_extras` (entry point) |
| 0x00015aa0 | 920 | `ToolChange.move` |
| 0x00015e40 | 892 | `BoxExtras.cmd_ENABLE_BOX_DRY_lambda` |
| 0x000161c0 | 6068 | `BoxExtras._create_drying_state_setter.set_drying_state` |
| 0x00017974 | 724 | `load_config` |
| 0x00017c50 | 3696 | `BoxExtras.cmd_INIT_MAPPING_VALUE` |
| 0x00018ac0 | 4612 | `BoxExtras.get_box_temp_by_slot` |
| 0x00019cc4 | 4616 | `BoxExtras.get_temp_by_slot` |
| 0x0001aed0 | 4656 | `BoxExtras.get_temp_by_num` |
| 0x0001c100 | 2676 | `BoxExtras.search_index_by_value` |
| 0x0001cb74 | 3704 | `BoxExtras.get_key_by_value` |
| 0x0001d9f0 | 1236 | `BoxExtras.get_value_by_key` |
| 0x0001dec4 | 2560 | `BoxExtras.get_status` |
| 0x0001e8c4 | 5016 | `BoxExtras.cmd_TIGHTEN_FILAMENT` |
| 0x0001fc60 | 1464 | `BoxExtras.cmd_CLEAR_RUNOUT_NUM` |
| 0x00020220 | 9824 | `BoxExtras.heating_handler` |
| 0x00022880 | 5396 | `BoxExtras.cmd_DISABLE_BOX_DRY` |
| 0x00023da0 | 2712 | `BoxExtras.cmd_RUN_STEPPER` |
| 0x00024840 | 568 | `BoxExtras._create_drying_state_setter` |
| 0x00024a80 | 3416 | `BoxExtras.cmd_disable_box_heater` |
| 0x000257e0 | 5772 | `BoxExtras.cmd_CUT_FILAMENT` |
| 0x00026e70 | 1184 | `BoxExtras.cmd_CLEAR_OOZE` |
| 0x00027310 | 1184 | `BoxExtras.cmd_CLEAR_FLUSH` |
| 0x000277b0 | 2668 | `BoxExtras.update_e_endstop` |
| 0x00028220 | 1296 | `BoxExtras.update_b_endstop` |
| 0x00028730 | 1892 | `BoxExtras.delayed_init_error_raw` |
| 0x00028e94 | 3648 | `BoxExtras.delayed_init_rfid` |
| 0x00029cd4 | 1520 | `BoxExtras.get_e_dis` |
| 0x0002a2c4 | 1480 | `BoxExtras.get_dis_dif` |
| 0x0002a890 | 2200 | `BoxExtras.call_set_rotation_distance` |
| 0x0002b130 | 1916 | `BoxExtras.set_init_rotation_distance` |
| 0x0002b8b0 | 844 | `BoxExtras.b_button_callback` |
| 0x0002bc00 | 588 | `ToolChange.get_position` |
| 0x0002be50 | 1548 | `ToolChange.cmd_CLEAR_TOOLCHANGE_STATE` |
| 0x0002c460 | 4024 | `ToolChange.__init__` |
| 0x0002d420 | 3068 | `BoxOutput.set_pin` |
| 0x0002e020 | 4552 | `BoxOutput.__init__` |
| 0x0002f230 | 824 | `BoxEndstop.set_scram` |
| 0x0002f570 | 456 | `BoxEndstop.get_endstops` |
| 0x0002f740 | 1140 | `BoxEndstop.add_stepper` |
| 0x0002fbb4 | 5096 | `BoxEndstop.__init__` |
| 0x00030fa0 | 2156 | `BoxButton.__init__` |
| 0x00031810 | 5456 | `BoxExtras.cmd_INIT_RFID_READ` |
| 0x00032d60 | 5828 | `BoxExtras.cmd_INIT_BUFFER_STATE` |
| 0x00034890 | 7492 | `ToolChange.cmd_TOOL_CHANGE_END` |
| 0x00036810 | 11672 | `BoxExtras.button_extruder_unload` |
| 0x00039620 | 8700 | `BoxExtras.handle_connect` (impl) |
| 0x0003c800 | 384 | `BoxExtras.handle_connect` (wrapper) |
| 0x0003c980 | 8148 | `BoxExtras.cmd_ENABLE_BOX_DRY` |
| 0x0003f120 | 8168 | `BoxExtras.buffer_button_callback` |
| 0x00041ae0 | 18432 | `BoxExtras.set_box_temp` |
| 0x00046724 | 10428 | `BoxExtras.cmd_BOX_PRINT_START` |
| 0x00048fe0 | 8552 | `BoxExtras.cmd_RETRY` (impl) |
| 0x0004c2c4 | 736 | `BoxExtras.cmd_RETRY` (wrapper) |
| 0x0004c5a4 | 6340 | `BoxExtras.cmd_AUTO_RELOAD_FILAMENT` |
| 0x0004e6f0 | 6332 | `BoxExtras.init_sync_buffer_state` (impl) |
| 0x00051d04 | 736 | `BoxExtras.init_sync_buffer_state` (wrapper) |
| 0x00051fe4 | 5332 | `ToolChange.cmd_TOOL_CHANGE_START` |
| 0x00053c20 | 4936 | `BoxExtras.__init__` (impl) |
| 0x000589b0 | 736 | `BoxExtras.__init__` (wrapper) |
| 0x00058c90 | 17728 | `BoxExtras.button_extruder_load` (impl) |
| 0x0005d3b0 | 736 | `BoxExtras.button_extruder_load` (wrapper) |
| 0x0005d690 | 8216 | `BoxExtras.button_box_unload` |
| 0x0005f9d0 | 8416 | `BoxExtras.save_variable` |
| 0x00061ab0 | 7132 | `BoxExtras.cmd_BUFFER_MONITORING` |
| 0x00063690 | 5720 | `BoxExtras.print_sensor_state_to_log` |
| 0x00064e74 | 9396 | `BoxExtras._buffer_response_timer` |
| 0x00067590 | 16828 | `BoxExtras.cmd_TRY_RESUME_PRINT` (impl) |
| 0x0006ca64 | 736 | `BoxExtras.cmd_TRY_RESUME_PRINT` (wrapper) |
| 0x0006cd44 | 10288 | `BoxExtras.cmd_RELOAD_ALL` |
| 0x0006fc50 | 14692 | `BoxExtras.cmd_RESUME_PRINT_1` (impl) |
| 0x00073e20 | 736 | `BoxExtras.cmd_RESUME_PRINT_1` (wrapper) |

---

## Notes on Decompilation Limitations

- Cross-architecture analysis (aarch64 binary on macOS arm64 host) limits decompiler effectiveness
- Cython-generated code is ~90% CPython API boilerplate (reference counting, type checks, error handling)
- Actual Python logic is deeply interleaved with `Py_INCREF`/`Py_DECREF` and type dispatch code
- String constants are accessed via global `__pyx_n_s_*` / `__pyx_kp_s_*` pointers (static, not exported)
- r2ghidra plugin was not available; r2dec produced low-level pseudo-C dominated by CPython internals
- Function logic was reconstructed primarily from: string constants, G-code sequences, symbol names, function sizes, and control flow structure
- The original Python source would be approximately 800-1200 lines based on the complexity observed
