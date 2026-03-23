# box_stepper.so Reverse Engineering Analysis

**Binary:** `/klippy_extras/box_stepper.so`
**Type:** ELF 64-bit aarch64, Cython-compiled CPython 3.9 extension
**Source:** `/home/mks/klipper/klippy/extras/box_stepper.py` (compiled to `box_stepper.c` then to `.so`)
**Compiler:** GCC 10.2.1 (Debian), compiled with `-O2`
**Size:** 2.9 MB (includes debug info, not stripped)
**Analysis tool:** radare2 6.1.2 with r2dec decompiler
**Analysis date:** 2026-03-22

---

## Module Overview

The module defines a `BoxExtruderStepper` class that manages the stepper motor(s) in each slot of the Qidi Box multi-material system. It handles:

- Filament loading from box slots to the hub
- Filament loading from the hub through the extruder
- Filament unloading (both slot-level and extruder-level)
- Filament flushing (color changes)
- Automatic slot switching during print (runout detection)
- Homing the stepper against endstops
- LED status indication
- RFID filament tag reading
- Buffer/input buffer state management

The module registers as a Klipper config prefix via `load_config_prefix()` and registers several G-code commands.

---

## Classes Found

### BoxExtruderStepper
The main class. All 24 methods are listed below.

### BoxEndstop
A helper class (referenced in strings) for endstop management.

### BoxButton
A helper class for button/switch input handling.

---

## Registered G-code Commands

Found via `register_mux_command` string references and function names:

| Command | Handler Method | Description |
|---------|---------------|-------------|
| `SLOT_UNLOAD` | `cmd_SLOT_UNLOAD` | Unload filament from a slot back to spool |
| `EXTRUDER_LOAD` | `cmd_EXTRUDER_LOAD` | Load filament from hub into extruder |
| `EXTRUDER_UNLOAD` | `cmd_EXTRUDER_UNLOAD` | Unload filament from extruder back to hub |
| `SLOT_PROMPT_MOVE` | `cmd_SLOT_PROMPT_MOVE` | Manual/prompted filament move |
| `SLOT_RFID_READ` | `cmd_SLOT_RFID_READ` | Read RFID tag on filament spool |

Additional internal commands referenced: `RELOAD_ALL`, `CUT_FILAMENT`, `MOVE_TO_TRASH`, `CLEAR_FLUSH`, `PAUSE`, `RFID_READ`

---

## Configuration Parameters (from __init__ string references)

### Slot Loading Parameters (4 stages)
Each slot has a multi-stage loading sequence with configurable distance, speed, and acceleration:

| Parameter | Description |
|-----------|-------------|
| `slot_load_length_1` / `_speed` / `_accel` | Stage 1: Initial engagement from spool |
| `slot_load_length_2` / `_speed` / `_accel` | Stage 2: Feed through PTFE tube |
| `slot_load_length_3` / `_speed` / `_accel` | Stage 3: Approach hub |
| `slot_load_length_4` / `_speed` / `_accel` | Stage 4: Final positioning |

### Slot Unloading Parameters (1 stage)
| Parameter | Description |
|-----------|-------------|
| `slot_unload_length_1` / `_speed` / `_accel` | Retract filament back to spool |

### Hub Loading Parameters
| Parameter | Description |
|-----------|-------------|
| `load_hub_length_1` / `_speed` / `_accel` | Feed from hub junction into shared path |

### Extruder Loading Parameters (3 stages)
| Parameter | Description |
|-----------|-------------|
| `extruder_load_length_1` / `_speed` / `_accel` | Stage 1: Into extruder approach |
| `extruder_load_length_2` / `_speed` / `_accel` | Stage 2: Through extruder gears |
| `extruder_load_length_3` / `_speed` / `_accel` | Stage 3: To nozzle tip |

### Extruder Unloading Parameters (2 stages)
| Parameter | Description |
|-----------|-------------|
| `extruder_unload_length_1` / `_speed` / `_accel` | Stage 1: Retract from nozzle |
| `extruder_unload_length_2` / `_speed` / `_accel` | Stage 2: Clear of extruder |

### Buffer Parameters
| Parameter | Description |
|-----------|-------------|
| `buffer_enabled` | Enable input buffer system |
| `buffer_init_length_1` | Buffer initialization length 1 |
| `buffer_init_length_2` | Buffer initialization length 2 |
| `input_buffer_enable` | Enable input buffer feature |

### Other Config
| Parameter | Description |
|-----------|-------------|
| `stepper_num` | Number of steppers in this slot unit |
| `stepper_name` | Name identifier for the stepper |
| `stepper_label` | Display label |
| `runout_pin` | GPIO pin for filament runout sensor |
| `load_retry_num` | Number of retries on failed load |
| `init_rotation_distance` | Initial rotation distance for stepper calibration |

---

## Key Method Analysis

### slot_load (0x0002f8e0, ~8200 bytes / ~20KB implementation)

**Purpose:** Loads filament from a box slot toward the hub/splitter.

**Logic flow (reconstructed from disassembly and string references):**

1. Reads `self.slot_state`, `self.extrude_state`, and `self.can_load_slot`
2. Checks if slot is already loaded (`slot_loaded` state check)
3. Reads multi-stage load parameters: `slot_load_length_1/2/3/4` with their speeds and accels
4. Executes a multi-stage `do_move()` sequence:
   - Stage 1: Initial feed (low speed, engage filament)
   - Stage 2: Fast feed through PTFE tube
   - Stage 3: Approach hub (moderate speed)
   - Stage 4: Final positioning
5. Performs homing against endstop (`b_endstop`) to verify filament reached the hub
6. Updates `slot_state` to loaded on success
7. On failure: raises error `QDE_004_001` ("Slot loading failure, please check the trigger, please reload %s")
8. Calls `set_led()` to update status LED

**Key state variables accessed:**
- `self.slot_state`
- `self.extrude_state`
- `self.can_load_slot`
- `self.b_endstop_state`
- `self.slot_loaded`

---

### cmd_SLOT_UNLOAD (0x0003d4c4, ~14KB implementation)

**Purpose:** G-code command handler to unload filament from a slot back to the spool.

**Logic flow:**

1. Parses `SLOT` parameter from G-code command
2. Checks `extrude_state` -- if extruder is loaded, raises `QDE_004_004` ("Please unload extruder first")
3. Checks `slot_state` -- verifies filament is actually loaded in the slot
4. Executes reverse move using `slot_unload_length_1` with configured speed/accel via `do_move()`
5. Verifies filament cleared the endstop (checks `b_endstop_state`)
6. On success: updates `slot_state`, calls `set_led()`
7. On failure: raises `QDE_004_003` ("Slot unloading failure, please unload %s again")

**Registered as:** `SLOT_UNLOAD` (with `SLOT_UNLOAD1_` and `SLOT_UNLOAD2_` variants for multi-step)

---

### cmd_EXTRUDER_LOAD (0x00034984, ~35KB implementation -- largest method)

**Purpose:** Loads filament from the hub through the extruder to the nozzle.

**Logic flow:**

1. Parses `SLOT` parameter from G-code
2. Checks preconditions:
   - Slot must be loaded (else `QDE_004_005`: "Please load the filament to %s first")
   - Extruder must not already be loaded (else `QDE_004_002`: "Extruder has been loaded, cannot load %s")
   - Checks `check_wrapping_filament_state` -- detects if filament is tangled (else `QDE_004_013`: "Detected wrapping filament")
3. Calls `sync_to_extruder` to sync the box stepper with the extruder stepper
4. Executes 3-stage loading:
   - **Stage 1** (`extruder_load_length_1`): Feed into extruder approach at `exl_1_speed`
   - **Stage 2** (`extruder_load_length_2`): Through extruder gears at `exl_2_speed`
   - **Stage 3** (`extruder_load_length_3`): To nozzle tip
5. Uses homing against `e_endstop` (extruder endstop) to verify arrival
6. May call `shake_for_load_toolhead` -- toolhead shake sequence to help filament engage
7. On success: updates `extrude_state`, `last_load_slot`, calls `set_led()`
8. On failure: raises `QDE_004_006` ("Extruder loading failure")
9. Checks `is_drying` state (filament dryer active check)

**Multi-step variants:** `EXTRUDER_LOAD1_`, `EXTRUDER_LOAD2_` for staged loading

---

### cmd_EXTRUDER_UNLOAD (0x00040ed4, ~62KB implementation -- most complex method)

**Purpose:** Unloads filament from the extruder back to the hub.

**Logic flow:**

1. Parses `SLOT` parameter
2. Checks extruder is actually loaded (else `QDE_004_007`: "Extruder not loaded")
3. Complex multi-phase unload sequence:
   - **Phase 1** (`extruder_unload_length_1`): Initial retract from nozzle at speed/accel
   - **Phase 2** (`extruder_unload_length_2`): Clear extruder gears
4. Checks `e_endstop` state to verify filament cleared the extruder
5. On failure path A: `QDE_004_008` ("Extruder unloading failure, unload again: EXTRUDER_UNLOAD SLOT=%s")
6. On failure path B: `QDE_004_009` (same message, different error code -- likely different failure point)
7. On failure path C: `QDE_004_025` (third unload failure variant)
8. May execute `shake_for_unload_toolhead` -- toolhead shake sequence
9. Runs `unload_extrude` sub-operation
10. Calls `CUT_FILAMENT` and `MOVE_TO_TRASH` G-code sequences (tip shaping and waste disposal)
11. Updates `extrude_state`, `slot_state`, calls `set_led()`
12. Checks `slot_not_unload` flag

**Multi-step variants:** `EXTRUDER_UNLOAD1_`, `EXTRUDER_UNLOAD2_`

**G-code sequences embedded in the binary:**

Tip-shaping retract:
```
G1 E-10 F300
```

Short extrude for purge verification:
```
G1 E25 F300
G1 E25 F600
```

---

### flush_all_filament (0x000100f0, ~3660 bytes)

**Purpose:** Purges/flushes all old filament from the nozzle during a color change.

**Logic flow:**

1. Checks `extrude_state` and `flush_success` flag
2. Executes the flush G-code sequence:
   ```
   G1 E150 F300        -- Extrude 150mm at 300mm/min (5mm/s) to purge
   G1 E-2 F1800        -- Small retract at 30mm/s
   M106 S255           -- Fan full blast (cool the purge)
   M400                -- Wait for moves to complete
   G4 P5000            -- Dwell 5 seconds
   M106 S0             -- Fan off
   CLEAR_FLUSH         -- Custom command (clear flush bucket/wiper)
   CLEAR_FLUSH         -- Called twice (double-wipe)
   M400                -- Wait
   ```
3. Sets `flush_success` state on completion
4. On failure: raises `QDE_004_017` ("Filament flush failed, please clean and then load the filament in %s")

**Key constant:** 150mm purge distance at 5mm/s (300 F-rate), with 5-second cooling pause.

---

### switch_next_slot (0x000190a0, ~12KB implementation)

**Purpose:** Automatically switches to the next filament slot during printing (triggered by runout or tool change).

**Logic flow:**

1. Reads `next_slot`, `next_filament_slot`, `next_color_slot`, `next_vendor_slot` to determine which slot to switch to
2. Checks if a replacement slot is available (else `QDE_004_022`: "No replaceable slot found")
3. Checks `auto_reload` and `auto_reload_detect` flags
4. Executes the full swap sequence:
   a. Unload current filament from extruder (`EXTRUDER_UNLOAD` equivalent)
   b. Unload current slot
   c. Load new slot (`slot_load`)
   d. Load new slot into extruder (`EXTRUDER_LOAD` equivalent)
5. If filament specified but not available: `QDE_004_018` ("No filament specified, %s cannot be automatically replaced")
6. May issue `RELOAD_ALL RFID=1 FIRST=` command to re-read RFID tags
7. Updates `filament_slot`, `color_slot`, `vendor_slot` state

**Slot selection priority:** `next_filament_slot` > `next_color_slot` > `next_vendor_slot` > `next_slot`

---

### runout_button_callback (0x0001c1c0, ~8KB)

**Purpose:** Callback triggered when the filament runout sensor detects filament absence.

**Arguments:** `self`, `eventtime`, `state` (3 positional args confirmed from decompilation)

**Logic flow:**

1. Receives `eventtime` and button `state` (pressed/released)
2. Reads `self.runout_num` (debounce/count tracking)
3. Checks `self.extrude_state` -- only acts if extruder is loaded/printing
4. Checks current print state via `print_stats` -> `printing` status
5. If filament runout confirmed during printing:
   - Checks if `auto_reload` is enabled
   - If auto-reload: calls `switch_next_slot()` to automatically swap filament
   - If no auto-reload: issues `PAUSE` command and raises `QDE_004_016` ("The filament has been exhausted, please load the filament to %s")
6. Also checks `QDE_004_020` ("Detected that the filament has been unloaded, please reload") for unexpected unload detection
7. Accesses `runout_helper`, `runout_button` objects
8. Tracks `b_endstop_state` and `r_endstop_state`

---

### do_move (0x000152f0, ~6.4KB)

**Purpose:** Low-level motion primitive -- moves the stepper by a specified distance at given speed and acceleration.

**Arguments:** `self`, `movepos`, `speed`, `accel` (4 args, with `accel` optional/defaulting)

**Logic flow:**

1. Reads `self.stepper` object and its current position
2. Calls `get_last_move_time()` from the toolhead
3. Computes move parameters:
   - `move_d` = distance
   - `move_t` = move time
   - `accel_t` = acceleration time
   - `cruise_t` = cruise time
   - `cruise_v` = cruise velocity
   - Uses `calc_move_time()` with trapezoidal motion profile
4. Calls into chelper FFI (`ffi_lib`, `ffi_main`):
   - `trapq_append` -- adds move to the trapezoid queue
   - `trapq_finalize_moves` -- finalizes the queued moves
5. Updates stepper position via `set_position`
6. Calls `note_mcu_movequeue_activity` on the toolhead
7. Uses `axes_d` for axis distance calculation
8. Handles `startpos`, `newpos`, `movepos` tracking

**Motion model:** Standard trapezoidal motion profile (accelerate -> cruise -> decelerate) using Klipper's chelper C library.

---

### do_home (0x00020110, ~16KB -- very large)

**Purpose:** Homes the stepper against an endstop to establish a known position.

**Logic flow:**

1. Gets endstop list from `get_endstops()` and `get_mcu_endstops()`
2. Sets up homing parameters:
   - `ENDSTOP_SAMPLE_TIME` -- sampling time for endstop reading
   - `ENDSTOP_SAMPLE_COUNT` -- number of samples for debouncing
   - `HOMING_START_DELAY` -- delay before homing begins
3. Calls `home_start()` to begin the homing move
4. Executes a `drip_move` (slow continuous move toward endstop)
5. Calls `home_wait()` to wait for endstop trigger
6. Checks `home_success` / `all_endstop_trigger` / `endstop_triggers`
7. On endstop trigger: records position, calls `set_position()`
8. On timeout/failure: raises error ("Error during homing move: %s" or "Error during homing %s: %s")
9. Uses `trigger_time` and `triggered` state from endstop
10. Handles `rest_time` between homing attempts
11. Manages `stepper_endstops` list

**Endstop types referenced:**
- `b_endstop` -- hub/buffer endstop (filament at hub)
- `e_endstop` -- extruder endstop (filament at extruder)
- `r_endstop` -- retract/runout endstop

---

### slot_sync (0x00010f40, ~5.2KB)

**Purpose:** Synchronizes a box slot stepper with the extruder stepper for coordinated motion during printing.

**Logic flow:**

1. Gets the `extruder_stepper` and `extruder` objects
2. Calls `sync_to_extruder` to link motion
3. Logs: "%s has been sync with Extruder."
4. Manages `loop_stepper` and `temp_stepper` references
5. Handles the stepper enable/disable state

---

### _calc_endstop_rate (0x000503c0, ~7.7KB)

**Purpose:** Calculates the appropriate stepper rate for endstop checking.

**Referenced variables:** `approximation_value`, `max_steps`, `get_step_dist`

---

### sync_print_time (0x00016dd0, ~3.8KB)

**Purpose:** Synchronizes the box stepper timing with the print time clock.

**References:** `est_print_time`, `estimated_print_time`, `min_print_time`, `print_time`, `next_cmd_time`, `get_last_move_time`

---

### disable_stepper (0x00013f90, ~1.8KB)

**Purpose:** Disables the stepper motor (releases current).

**References:** `stepper_enable`, `lookup_enable`, `motor_disable`, `disable`, `DISABLE_DELAY`

---

### multi_complete (0x00013480, ~2.8KB)

**Purpose:** Waits for multiple async operations to complete (used for coordinated multi-stepper moves).

**Contains a lambda:** Used as a completion callback. References `completions`, `complete`.

---

### get_status (0x00017cb0, ~924 bytes)

**Purpose:** Returns the current status dictionary for Klipper's status system.

**Reported fields (from string references):**
- `filament_present`
- `slot_state`
- `extrude_state`
- `b_endstop_state`
- `r_endstop_state`
- `led_state`
- `buffer_state`
- `rfid_state`

---

### init_buffer_state (0x0002bc20, ~15KB)

**Purpose:** Initializes the input buffer system (filament buffer between box and extruder).

**Logic flow:**

1. Reads `buffer_enabled` and `input_buffer_enable` config
2. Uses `buffer_init_length_1` and `buffer_init_length_2` for initialization moves
3. Performs homing to establish buffer position
4. Logs "Init buffer state successful" on completion
5. Sets up `buffer_response_timer` and `buffer_state`

---

### set_led (0x0001e0d0, ~8.2KB)

**Purpose:** Controls the RGB LED on the box slot to indicate status.

**References:** `PrinterPWMLED`, `update_leds`, `led_state`, `led_timer`, `red_value`, `white_value`

LED identifiers for slots: `1A`, `1B`, `1C`, `1D`, `2A`, `2B`, `2C`, `2D`, `3A`, `3B`, `3C`, `3D`, `4A`, `4B`, `4C`, `4D`
(4 box units x 4 slots each = 16 possible slot LEDs)

---

### led_handle_connect (0x0000fc34, ~1.2KB)

**Purpose:** Handles Klipper `klippy:ready` event to initialize LED state on startup.

**Registered via:** `register_event_handler("klippy:ready", self.led_handle_connect)`

---

### cmd_SLOT_RFID_READ (0x00024060, ~13KB)

**Purpose:** Reads the RFID tag on a filament spool.

**References:** `rfid_device`, `box_rfid`, `card_reader`, `start_rfid_read`, `stop_read`, `rfid_state`

---

### cmd_SLOT_PROMPT_MOVE (0x000123a0, ~3KB)

**Purpose:** Handles manual/prompted filament movement (user-initiated via UI).

---

## Embedded G-code Sequences

### Toolhead Shake for Load (`shake_for_load_toolhead`)
```gcode
M204 S10000
M83
G1 X0 Y200 F21000
G1 P1000
G1 X0 Y70 E6.5 F30000       ; Move Y while extruding 6.5mm
G1 E1 F60                     ; Slow extrude 1mm
G1 X0 Y200 E6.5 F30000       ; Repeat Y oscillation with extrusion
G1 E1 F60
G1 X0 Y270 F21000
G1 X200 F30000
G1 X70 E6.5 F30000            ; X oscillation with extrusion
G1 E1 F60
G1 X200 E6.5 F30000
G1 E1 F60
G1 X0 Y270 F21000
G1 X0 Y135 F21000
M400
```
This sequence oscillates the toolhead in Y then X while extruding small amounts to help filament engage with the extruder gears. Total extrusion: ~30mm during shaking.

### Toolhead Shake for Unload (`shake_for_unload_toolhead`)
```gcode
M204 S10000
M83
G1 X0 Y200 F21000
G1 P1000
G1 X0 Y70 E-6.5 F30000       ; Move Y while RETRACTING 6.5mm
G1 E-1 F60
G1 X0 Y200 E-6.5 F30000
G1 E-1 F60
G1 X0 Y270 F21000
G1 X200 F30000
G1 X70 E-6.5 F30000
G1 E-1 F60
G1 X200 E-6.5 F30000
G1 E-1 F60
G1 X0 Y270 F21000
G1 X0 Y135 F21000
M400
```
Same oscillation pattern but with retraction instead of extrusion. Total retraction: ~30mm.

### Bed Vibration Sequence (for filament engagement)
```gcode
G1 X0 Y200 F30000
G1 X0 Y70 F30000
G1 X0 Y200 F30000
G1 X0 Y70 F30000
G1 X0 Y180 F30000
G1 X0 Y90 F30000
... (progressively narrowing Y oscillations)
G1 X0 Y140 F30000
G1 X0 Y130 F30000
G1 X0 Y270 F15000
G1 X135 Y270 F15000
G1 X200 Y270 F30000
G1 X70 Y270 F30000
... (same narrowing pattern on X axis)
G1 X0 Y270
G1 X0 Y135
M400
```
Large-amplitude vibration pattern (Y: 200<->70, narrowing to 140<->130, then X: 200<->70 narrowing to 140<->130) at 500mm/s. This is a "shake the toolhead" routine to help dislodge or settle filament.

### Position to Waste Bin
```gcode
G1 Y270 F9000
G1 X0 F9000
G1 X0 Y17 F15000
M400
```
Moves toolhead to front-left (X0, Y17) -- likely the waste/purge bucket position.

### Reset Position After Flush
```gcode
M204 S10000
G1 X0 Y135 F15000
```
Returns to center position (Y135 = bed center on 270mm bed).

### Flush Sequence
```gcode
G1 E150 F300          ; Extrude 150mm at 5mm/s
G1 E-2 F1800          ; Retract 2mm at 30mm/s
M106 S255             ; Part fan 100%
M400                  ; Wait
G4 P5000              ; Dwell 5 seconds (cool purge)
M106 S0               ; Fan off
CLEAR_FLUSH           ; Clear flush bucket
CLEAR_FLUSH           ; Double clear
M400
```

---

## Error Code Reference

| Code | Severity | Message | Triggered By |
|------|----------|---------|--------------|
| QDE_004_001 | !! (fatal) | Slot loading failure, please check the trigger, please reload %s | `slot_load` |
| QDE_004_002 | !! (fatal) | Extruder has been loaded, cannot load %s | `cmd_EXTRUDER_LOAD` |
| QDE_004_003 | !! (fatal) | Slot unloading failure, please unload %s again | `cmd_SLOT_UNLOAD` |
| QDE_004_004 | !! (fatal) | Please unload extruder first | `cmd_SLOT_UNLOAD` |
| QDE_004_005 | warning | Please load the filament to %s first | `cmd_EXTRUDER_LOAD` |
| QDE_004_006 | warning | Extruder loading failure | `cmd_EXTRUDER_LOAD` |
| QDE_004_007 | warning | Extruder not loaded | `cmd_EXTRUDER_UNLOAD` |
| QDE_004_008 | warning | Extruder unloading failure (retry prompt) | `cmd_EXTRUDER_UNLOAD` |
| QDE_004_009 | warning | Extruder unloading failure (retry prompt) | `cmd_EXTRUDER_UNLOAD` |
| QDE_004_011 | warning | Detected that filament have been loaded, please unload first | `cmd_EXTRUDER_LOAD` |
| QDE_004_013 | warning | Detected wrapping filament, please check | `cmd_EXTRUDER_LOAD` |
| QDE_004_016 | warning | Filament exhausted, please load to %s | `runout_button_callback` |
| QDE_004_017 | warning | Filament flush failed | `flush_all_filament` |
| QDE_004_018 | warning | No filament specified, cannot auto-replace %s | `switch_next_slot` |
| QDE_004_019 | !! (fatal) | Please check if your PTFE Tube is bent | various |
| QDE_004_020 | !! (fatal) | Detected filament unloaded, please reload | `runout_button_callback` |
| QDE_004_022 | warning | No replaceable slot found | `switch_next_slot` |
| QDE_004_025 | warning | Extruder unloading failure (retry prompt) | `cmd_EXTRUDER_UNLOAD` |

Errors prefixed with `!!` are fatal/blocking. Others are warnings that may allow retry.

---

## State Machine

The module tracks several key states:

- **`slot_state`**: per-slot loaded/unloaded status
- **`extrude_state`**: whether filament is in the extruder
- **`buffer_state`**: input buffer status
- **`b_endstop_state`**: hub/buffer endstop triggered state
- **`e_endstop_state`**: extruder endstop state (implied by `e_endstop_timer`)
- **`r_endstop_state`**: retract/runout endstop state
- **`led_state`**: current LED color state
- **`rfid_state`**: RFID reader state
- **`flush_success`**: whether last flush succeeded
- **`slot_loaded`**: boolean per-slot loaded flag
- **`filament_present`**: sensor-detected filament presence
- **`slot_not_unload`**: flag preventing automatic unload
- **`last_load_slot`**: which slot was last loaded
- **`need_output_state`**: state output pending flag

State is persisted via Klipper's `save_variable` system.

---

## Filament Change Sequence (Reconstructed)

A full color change (e.g., slot 1 -> slot 2) follows this sequence:

1. **Pause print** (if during printing)
2. **Move to purge position**: `G1 Y270 F9000; G1 X0 F9000; G1 X0 Y17 F15000; M400`
3. **Retract from nozzle**: `cmd_EXTRUDER_UNLOAD` (multi-phase retract with toolhead shake)
4. **Cut filament**: `CUT_FILAMENT` (tip shaping)
5. **Move waste to trash**: `MOVE_TO_TRASH; M400`
6. **Unload old slot**: `cmd_SLOT_UNLOAD` (retract back to spool)
7. **Load new slot**: `slot_load` (4-stage feed to hub)
8. **Load into extruder**: `cmd_EXTRUDER_LOAD` (3-stage feed to nozzle with toolhead shake)
9. **Flush/purge**: `flush_all_filament` (extrude 150mm, cool, clear flush bucket)
10. **Return to position**: `M204 S10000; G1 X0 Y135 F15000`
11. **Resume print**

---

## Endstop Architecture

Three endstop types per slot:

| Endstop | Variable | Purpose |
|---------|----------|---------|
| `b_endstop` | `b_endstop_state`, `b_endstop_timer` | Buffer/hub position -- detects filament at the Y-junction |
| `e_endstop` | (via `e_endstop_timer`) | Extruder position -- detects filament entering the extruder |
| `r_endstop` | `r_endstop_state` | Retract/runout -- detects filament presence at slot exit |

Plus the `runout_button` (separate from endstops) which uses a filament switch sensor (`filament_switch_sensor`).

---

## Module Dependencies

From string references:
- `force_move` -- Klipper force_move module for manual stepper control
- `toolhead` -- Klipper toolhead for motion planning
- `print_stats` -- Print state tracking
- `stepper_enable` -- Stepper enable/disable management
- `chelper` -- Klipper C helper library (FFI for `trapq_*` functions)
- `box_extras` -- Qidi Box extras module (`.so`)
- `box_rfid` -- Qidi Box RFID module (`.so`)
- `extruder_stepper` / `ExtruderStepper` -- Klipper extruder stepper
- `kinematics` -- Printer kinematics
- `PrinterPWMLED` -- LED control
- `math` (specifically `sqrt`)
- `gc` (garbage collector)
- `asyncio.coroutines` (async support)

---

## LED Slot Mapping

16 LED identifiers found: `1A` through `4D`

This suggests 4 Box units (1-4) with 4 slots each (A-D), matching the physical Qidi Box hardware which supports up to 4 daisy-chained 4-slot units = 16 total filament slots.

---

## Notable Implementation Details

1. **Trapezoidal motion profile**: `do_move` uses Klipper's standard `trapq_append`/`trapq_finalize_moves` for smooth acceleration/deceleration
2. **Retry logic**: `load_retry_num` config parameter and `retry_num`/`retry_step`/`success_count` variables show built-in retry on load/unload failures
3. **RFID integration**: Full RFID read support for filament identification (`start_rfid_read`, `stop_read`, `card_reader`)
4. **Buffer system**: Input buffer support for smoother filament feeding
5. **Wrapping detection**: `check_wrapping_filament_state` detects tangled filament
6. **Drying awareness**: `is_drying` check prevents operations during filament drying
7. **Toolhead shaking**: Aggressive toolhead oscillation (500mm/s) helps filament engagement -- unique to Qidi's implementation
8. **150mm purge volume**: Standard flush uses 150mm of filament at 5mm/s
9. **Exclude tool**: `exclude_tool` reference suggests per-tool exclusion capability

---

## Function Address Map

| Address | Size | Function |
|---------|------|----------|
| 0x0000b7a0 | 16 | `PyInit_box_stepper` (module entry) |
| 0x0000988c | 4604 | `__pyx_pymod_exec_box_stepper` (module init) |
| 0x0000f960 | 724 | `load_config_prefix` |
| 0x00027730 | 16912 | `__init__` (implementation) |
| 0x0002b940 | 736 | `__init__` (wrapper) |
| 0x0001c1c0 | 7952 | `runout_button_callback` |
| 0x00017cb0 | 924 | `get_status` |
| 0x00016dd0 | 3808 | `sync_print_time` |
| 0x000152f0 | 6872 | `do_move` |
| 0x00014d80 | 1384 | `dwell` |
| 0x000146a0 | 1756 | `drip_move` |
| 0x00013f90 | 1800 | `disable_stepper` |
| 0x000503c0 | 7676 | `_calc_endstop_rate` |
| 0x00013480 | 2832 | `multi_complete` |
| 0x00020110 | 16208 | `do_home` |
| 0x00018714 | 2436 | `get_mcu_endstops` |
| 0x0002f8e0 | 20260 | `slot_load` (implementation) |
| 0x0003d4c4 | 14128 | `cmd_SLOT_UNLOAD` (implementation) |
| 0x00034984 | 34912 | `cmd_EXTRUDER_LOAD` (implementation) |
| 0x00040ed4 | 61916 | `cmd_EXTRUDER_UNLOAD` (implementation) |
| 0x0002bc20 | 15164 | `init_buffer_state` (implementation) |
| 0x000123a0 | 2972 | `cmd_SLOT_PROMPT_MOVE` |
| 0x00010f40 | 5208 | `slot_sync` |
| 0x000100f0 | 3660 | `flush_all_filament` |
| 0x000190a0 | 12184 | `switch_next_slot` (implementation) |
| 0x0001c040 | 384 | `switch_next_slot` (wrapper) |
| 0x00024060 | 13292 | `cmd_SLOT_RFID_READ` (implementation) |
| 0x0001e0d0 | 8248 | `set_led` |
| 0x0000fc34 | 1208 | `led_handle_connect` |
| 0x00018050 | 1732 | `multi_complete` (lambda) |
| 0x00012f40 | 1344 | `multi_complete` (lambda1) |
