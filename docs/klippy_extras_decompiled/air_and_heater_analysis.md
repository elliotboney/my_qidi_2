# Decompilation Analysis: air.so and heater_air_core.so

Binary analysis performed with radare2 6.1.2 + r2ghidra on aarch64 ELF shared objects compiled from Cython (.pyx) sources.

---

## File 1: air.cpython-39-aarch64-linux-gnu.so

- **Source**: `/home/mks/cry_studio/air` (original Cython source: `air.pyx`)
- **Compiler**: GCC 10.2.1 (Debian), Cython-compiled Python 3.9
- **Size**: 1.6 MB, not stripped, with debug info
- **Total pyx functions**: 47 (public wrappers + implementations)

### Class Architecture

The module implements a **weight-based probe system** (strain gauge / load cell probe) for Klipper. It contains 5 classes:

| Class | Purpose |
|-------|---------|
| `WeighEndstopWrapper` | Klipper endstop interface for the weight sensor; handles homing, probing, trigger detection |
| `WeighCalibration` | Calibrates the weight sensor by mapping frequency readings to Z heights |
| `WeighGatherSamples` | Collects and processes sensor data samples during probing |
| `WeighDriftCompensation` | Compensates for temperature-induced drift in frequency readings |
| `PrinterAirProbe` | Top-level probe interface; registered as the `probe` object in Klipper |

### External Dependencies (imported modules/objects)

- `phoming` (Klipper's probing homing module)
- `MCU_trsync`, `TriggerDispatch` (MCU trigger synchronization)
- `ProbeCommandHelper`, `ProbeOffsetsHelper`, `ProbeSessionHelper` (standard Klipper probe framework)
- `manual_probe` (for post-calibration manual probe step)
- `math.sqrt`, `bisect` (for calibration curve math)
- `toolhead` (for motion commands)

### Key Config Parameters (from strings)

- `sensor_type` -- sensor hardware type selection (via `getchoice`)
- `x_offset`, `y_offset`, `z_offset` -- probe offsets from nozzle
- `probe_speed` / `PROBE_SPEED` -- speed during probing moves
- `sample_time`, `sample_count` -- sensor sampling configuration
- `target_adc_value` -- target ADC value for triggering
- `probe_accel` -- acceleration override during probing
- `max_z` -- maximum Z position for calibration moves

---

### WeighEndstopWrapper

This class wraps the weight sensor as a Klipper-compatible endstop. It implements the full endstop interface (`add_stepper`, `get_steppers`, `get_mcu`, `query_endstop`, `home_start`, `home_wait`, `home_zero`, `home_check`, `get_position_endstop`).

#### probing_move (method 19 in vtable)

Not directly found as a separate function in the symbol table -- probing is handled through the standard endstop homing interface. The actual probing move is delegated to `phoming` and `MCU_trsync`/`TriggerDispatch`.

**Likely flow**: `probing_move` sets up the sensor for monitoring, initiates a downward Z move via the toolhead, and waits for the weight sensor to trigger. The trigger is detected when the frequency reading crosses the `target_adc_value` threshold.

#### home_start(self, print_time, sample_time, sample_count, rest_time, triggered=True)

**Signature**: Takes 5 positional args (self + 4 required + 1 optional)

**Reconstructed logic**:
1. Calls `self._sensor_helper.setup_home(...)` to configure the sensor for homing mode
2. Gets the `trigger_completion` object from the sensor helper
3. Sets up `MCU_trsync` for synchronized trigger detection
4. Configures `TriggerDispatch` to coordinate the trigger response
5. Returns the trigger dispatch object for `home_wait` to consume

**Key string references**: `setup_home`, `trigger_completion`, `MCU_trsync`, `TriggerDispatch`, `clear_home`

**Error handling**: Reports `WEIGHT sensor error` on sensor failure, `probe_weigh sensor outage` on sensor outage

#### home_wait(self, home_end_time)

**Signature**: 2 args (self + home_end_time)

**Reconstructed logic**:
1. Waits for the trigger dispatch to complete (blocking until trigger or timeout)
2. Checks `trigger_time` from the result
3. If `REASON_ENDSTOP_HIT` -- probe triggered, records position
4. If `REASON_COMMS_TIMEOUT` or `REASON_SENSOR_ERROR` -- handles error
5. Calls `clear_home` on sensor helper after completion
6. Returns the trigger position

#### probe_prepare(self)

**Size**: 3912 bytes (one of the largest functions)

**Reconstructed logic**:
1. Stores current `max_accel` as `old_max_accel`
2. Sets toolhead max_accel to `probe_accel` (reduced acceleration for probing)
3. Logs `WEIGHT-enter probe_accel`
4. Calls `flush_step_generation` on toolhead
5. Prepares the sensor for data collection

#### probe_finish(self)

**Reconstructed logic**:
1. Restores `old_max_accel` on the toolhead
2. Logs `WEIGHT-exit probe_accel`
3. Cleans up sensor state

#### multi_probe_begin / multi_probe_end

Standard Klipper multi-probe interface. `begin` prepares for a sequence of probes (e.g., bed mesh), `end` cleans up. These likely set a flag to avoid repeated probe_prepare/probe_finish overhead.

#### query_endstop(self, print_time)

Returns the current state of the weight endstop at a given print time. Queries the sensor helper for current frequency and compares against threshold.

---

### WeighCalibration

Handles the calibration process that maps weight sensor frequency readings to Z heights. This is critical for converting raw sensor data into accurate Z positions.

#### cmd_WEIGH_CALIBRATE(self, gcmd)

**G-code command**: `WEIGH_CALIBRATE`
**Help text**: "Calibrate weigh probe"

**Signature**: 2 args (self + gcmd)

**Reconstructed logic**:
1. Parses G-code parameters from `gcmd`
2. Invokes `manual_probe` to perform a manual Z calibration first (user manually positions nozzle at bed)
3. Passes `post_manual_probe` as callback
4. The manual probe result gives the reference Z height

#### post_manual_probe(self, kin_pos)

Called after manual probe completes with the reference kinematic position.

**Reconstructed logic**:
1. Records `probe_calibrate_z` from the manual probe result
2. Calls `do_calibration_moves` to collect frequency data at multiple heights
3. Processes the results through `calc_freqs`

#### do_calibration_moves(self, gcmd) -- Generator/Coroutine

**Size**: 11,088 bytes (the largest function -- this is a Cython generator)

**Generator structure**: Uses `__pyx_scope_struct__do_calibration_moves` as the generator frame. Contains an inner function `handle_batch` for processing sensor data batches.

**Reconstructed logic**:
1. Creates a `WeighGatherSamples` instance for data collection
2. Moves the toolhead to a starting position
3. **Loop**: Iterates through multiple Z heights (stepping down toward the bed)
   - At each height, dwells briefly for sensor readings to stabilize
   - Calls the sensor helper to record frequency readings
   - Invokes `handle_batch` to accumulate batch data
   - Records (height, frequency) pairs
4. After all moves, calls `calc_freqs` to process the collected data
5. Validates data: raises error if "frequency not increasing each step" or "incomplete sensor data"

**Error messages**:
- `"Failed calibration - frequency not increasing each step"` -- sensor data is not monotonic
- `"Failed calibration - incomplete sensor data"` -- not enough samples collected

#### handle_batch (inner function)

**Size**: 784 bytes

Processes a batch of sensor readings during calibration. Accumulates frequency averages (`freq_avg`) and timing data (`freq_clock`).

#### freq_to_height(self, freq)

**Signature**: 2 args (self + freq)

**Reconstructed logic** (from wrapper analysis):
This is a thin wrapper that delegates to the implementation function. Based on the `bisect` import and the calibration data structure, this likely:
1. Uses `bisect` to find where `freq` falls in the sorted calibration frequency array
2. Performs linear interpolation between adjacent calibration points
3. Returns the interpolated Z height

The calibration data is stored as sorted parallel arrays of frequencies and heights.

#### height_to_freq(self, height)

Inverse of `freq_to_height`. Converts a Z height to an expected frequency reading using the same calibration data but searching the height array.

#### calc_freqs(self)

**Size**: 7,132 bytes

**Reconstructed logic**:
1. Processes the raw (position, frequency) data collected during calibration
2. Computes frequency averages for each position
3. Validates that frequencies are monotonically increasing with decreasing Z height
4. Builds the calibration lookup tables used by `freq_to_height` and `height_to_freq`
5. Stores calibration data (likely as `_calibration` attribute)

#### load_calibration(self, config) / apply_calibration(self, config)

Load/apply saved calibration data from Klipper's config/saved_variables system.

#### set_target_adc_value(self, target_adc_value)

Sets the trigger threshold for the probe. When the frequency reading exceeds this value, the probe triggers.

---

### WeighGatherSamples

Manages the collection of sensor data during probing operations.

#### __init__(self, ...)

Initializes the sample collection with timing parameters.

#### _await_samples(self)

**Size**: 6,032 bytes (generator/coroutine)

Asynchronously waits for sensor data. This is the main data collection loop that:
1. Registers a callback with the sensor
2. Waits for samples to arrive
3. Accumulates measurements
4. Handles timeouts and sensor errors

#### _add_measurement(self, ...)

**Size**: 1,540 bytes

Processes a single sensor measurement. Records the frequency, timestamp, and associates it with a toolhead position using `_lookup_toolhead_pos`.

#### _lookup_toolhead_pos(self)

Correlates a sensor reading timestamp with the toolhead position at that time using `get_past_mcu_position` and `mcu_to_commanded_position`.

#### note_probe_and_position(self, ...)

Records a probe trigger event along with the corresponding toolhead position.

#### finish(self)

Finalizes sample collection, computes statistics (uses `total_count`, `total_variance`).

---

### PrinterAirProbe

The top-level probe object registered with Klipper as `probe`. Implements the standard probe interface.

#### __init__(self, config)

**Reconstructed logic**:
1. Reads probe configuration from `config`:
   - `sensor_type` (via `getchoice`)
   - `x_offset`, `y_offset`, `z_offset` (float values)
   - `probe_speed` / `PROBE_SPEED`
   - `sample_time`, `sample_count`
   - `probe_accel`
2. Creates a `WeighEndstopWrapper` instance as `mcu_probe`
3. Creates a `WeighCalibration` instance
4. Creates `ProbeCommandHelper`, `ProbeOffsetsHelper`, `ProbeSessionHelper` from standard Klipper probe framework
5. Registers itself as the `probe` object with the printer

#### get_probe_params(self, gcmd=None)

**Signature**: 1-2 args (self + optional gcmd)

**Reconstructed logic**:
Delegates to `mcu_probe.get_probe_params(gcmd)`. Returns a dict with probe parameters including speed, offsets, sample settings, etc. The optional `gcmd` allows overriding params from G-code command args.

#### get_offsets(self)

**Signature**: 1 arg (self only)

**Reconstructed logic**:
Calls `probe_offsets.get_offsets()` which returns a tuple of `(x_offset, y_offset, z_offset)`. These are the configured offsets of the probe relative to the nozzle.

#### get_status(self, eventtime)

Returns probe status dict for Klipper's status system. Includes `last_freq` and calibration state.

#### start_probe_session(self, gcmd)

Creates and returns a `ProbeSessionHelper` for managing a series of probe operations.

#### register_drift_compensation(self, compensation)

Registers a `WeighDriftCompensation` instance to adjust readings for temperature drift.

---

### WeighDriftCompensation

Compensates for temperature-induced drift in the weight sensor's frequency readings.

#### get_temperature(self)

Returns the current temperature reading from a temperature sensor (used for drift compensation).

#### note_z_calibration_start(self)

Called when Z calibration begins. Records the starting temperature for drift baseline.

#### note_z_calibration_finish(self)

Called when Z calibration finishes. Records the ending temperature. The temperature difference is used to calculate drift compensation factors.

#### adjust_freq(self, freq, temp=None)

**Signature**: 2-3 args (self + freq + optional temp)

**Reconstructed logic**:
1. If `temp` is not provided, calls `get_temperature()` to get current temp
2. Calculates the temperature difference from the calibration baseline temperature
3. Applies a compensation factor to the frequency: adjusts `freq` based on the temperature delta
4. Returns the compensated frequency

The compensation is likely linear: `adjusted_freq = freq + (temp_diff * drift_factor)`

#### unadjust_freq(self, freq)

Reverse of `adjust_freq`. Removes the drift compensation from an already-adjusted frequency reading. Used when saving calibration data that should be in raw (uncompensated) form.

---

## File 2: heater_air_core.cpython-39-aarch64-linux-gnu.so

- **Source**: `/home/mks/studio/heater_air` (original Cython source: `heater_air_core.pyx`)
- **Compiler**: GCC 10.2.1 (Debian), Cython-compiled Python 3.9
- **Size**: ~1.5 MB, not stripped, with debug info
- **Module init**: `PyInit_heater_air_core`

### Class Architecture

This module implements a custom **air/chamber heater control system** for Klipper.

| Class | Purpose |
|-------|---------|
| `Heater_air` | Individual air heater controller with PWM output, temperature monitoring, safety limits |
| `AIR_ControlBangBang` | Bang-bang (on/off) temperature control algorithm |
| `PrinterAirHeater` | Top-level heater manager; registers heaters, sensors, handles G-code commands |

### Constants (from strings)

| Constant Name | Purpose |
|---------------|---------|
| `AIR_AMBIENT_TEMP` | Assumed ambient temperature baseline |
| `AIR_KELVIN_TO_CELSIUS` | Kelvin to Celsius conversion factor (273.15) |
| `AIR_MAX_HEAT_TIME` | Maximum continuous heating time (safety limit) |
| `AIR_PID_PARAM_BASE` | Base PID parameter value (suggests PID support exists or is planned) |

### Key Config Parameters (from strings)

- `heater_name` -- name of the heater section
- `sensor_type` -- temperature sensor type
- `control` -- control algorithm selection (bang-bang)
- `max_temp`, `min_temp` -- temperature safety limits
- `max_power` / `heater_max_power` -- maximum PWM duty cycle
- `smooth_time` / `inv_smooth_time` -- temperature smoothing window
- `pwm_cycle_time` -- PWM cycle time
- `air_pin` -- GPIO pin for the heater
- `en_pin` / `out_en_pin` -- enable pin for the heater
- `mini_air_temp` -- minimum air temperature threshold
- `min_extrude_temp` -- minimum temperature for extrusion (can_extrude)

### G-code Commands

| Command | Help Text |
|---------|-----------|
| `SET_AIR_TEMPERATURE` | "Sets a air temperature" |
| `TURN_OFF_HEATERS` | "Turn off all heaters" |

---

### Heater_air

The main heater control class. Manages a single air heater including PWM output, temperature reading, and safety monitoring.

#### __init__(self, config, sensor)

**Signature**: 3 args (self + config + sensor)

**Reconstructed logic**:
1. Gets the printer object from config
2. Gets the heater name from config (`get_name()`)
3. Reads configuration parameters:
   - `max_power` (float)
   - `max_temp`, `min_temp` (float, temperature range)
   - `smooth_time` (float, for temperature smoothing)
   - `pwm_cycle_time` (float)
   - `air_pin` (via `pins.setup_pin`)
   - `en_pin` / `out_en_pin` (enable pin)
4. Sets up PWM output via `setup_cycle_time` and `setup_max_duration`
5. Initializes state variables:
   - `target_temp = 0`
   - `smoothed_temp = 0`
   - `last_temp = 0`
   - `last_temp_time = 0`
   - `last_pwm_value = 0`
   - `next_pwm_time = 0`
   - `is_shutdown = False`
   - `isenabled = False`
6. Sets `control` to an `AIR_ControlBangBang` instance
7. Registers `temperature_callback` with the sensor
8. Registers the `SET_AIR_TEMPERATURE` G-code command

#### set_temp(self, degrees)

**Signature**: 2 args (self + degrees)

**Reconstructed logic**:
1. Validates that `degrees` is within `[min_temp, max_temp]` range
2. If out of range, raises `command_error` with: `"Requested temperature (%.1f) out of range (%.1f:%.1f)"`
3. Sets `self.target_temp = degrees`
4. Triggers a temperature update on the control algorithm

#### temperature_callback(self, read_time, temp)

**Signature**: 3 args (self + read_time + temp)

**Reconstructed logic**:
1. Receives a temperature reading from the sensor at the given time
2. Updates `self.last_temp = temp`
3. Updates `self.last_temp_time = read_time`
4. Computes smoothed temperature using exponential smoothing:
   - `time_diff = read_time - last_temp_time`
   - `adj_time = min(time_diff * inv_smooth_time, 1.0)`
   - `smoothed_temp = smoothed_temp + (temp - smoothed_temp) * adj_time`
5. Calls `self.control.temperature_update(read_time, temp, self.target_temp)` to run the control loop
6. Format string for stats: `"%s: target=%.0f temp=%.1f pwm=%.3f"`

#### cmd_SET_AIR_TEMPERATURE(self, gcmd)

**Signature**: 2 args (self + gcmd)

**Reconstructed logic**:
1. Parses `TARGET` parameter from G-code command (float, default 0)
2. Calls `self.set_temp(target)`
3. If target is non-zero, may also call `set_en(True)` to enable the heater
4. Updates the printer state

#### set_pwm(self, print_time, value)

**Signature**: 3 args (self + print_time + value)

**Reconstructed logic**:
1. Clamps `value` to `[0, max_power]`
2. If `print_time < next_pwm_time`, returns early (prevents too-frequent updates)
3. Updates `next_pwm_time = print_time + pwm_delay`
4. Sends PWM value to the MCU: `mcu_pwm.set_pwm(print_time, value)`
5. Updates `last_pwm_value = value`

#### set_en(self, val)

**Signature**: 2 args (self + val)

**Reconstructed logic**:
1. Sets the enable pin to `val` (True/False)
2. Logs: `"MKS_DEBUG_AIR:set en val:%s"` -- debug output for enable state changes
3. Updates `self.isenabled = val`
4. If disabling, may set PWM to 0

#### get_temp(self, eventtime)

Returns tuple of `(smoothed_temp, target_temp)`.

#### get_status(self, eventtime)

Returns dict with: `temperature`, `target`, `power` (last_pwm_value / max_power)

#### stats(self, eventtime)

Returns stats string: `"%s: target=%.0f temp=%.1f pwm=%.3f"`

#### _handle_shutdown(self)

Emergency shutdown handler. Sets PWM to 0, sets `is_shutdown = True`.

#### check_busy(self, eventtime)

Returns True if the heater is actively heating toward a target.

#### alter_target(self, target)

Modifies the target temperature. Used for external control adjustments.

#### set_control(self, control) / get_smooth_time / get_pwm_delay / get_max_power / get_name

Simple accessor methods for heater properties.

---

### AIR_ControlBangBang

Implements bang-bang (hysteresis-based on/off) temperature control. This is a simple control algorithm where the heater is fully on below a threshold and fully off above it.

#### __init__(self, heater, config)

**Signature**: 3 args (self + heater + config)

**Reconstructed logic**:
1. Stores reference to the parent `heater`
2. Reads `max_power` from the heater configuration
3. Sets `self.heater = heater`
4. Reads the temperature hysteresis threshold from config
5. Initializes `self.heating = True` (or based on initial state)

**Note**: The standard Klipper bang-bang uses `max_delta` as the hysteresis band (default 2.0 degrees).

#### temperature_update(self, read_time, temp, target_temp)

**Signature**: 4 args (self + read_time + temp + target_temp)

**Reconstructed logic** (reconstructed from the 3,384-byte function):
1. Evaluates current temperature vs. target:
   - If `temp >= target_temp + max_delta`: turn heater **OFF**
     - `self.heating = False`
     - Call `heater.set_pwm(read_time, 0.0)`
   - If `temp <= target_temp - max_delta`: turn heater **ON**
     - `self.heating = True`
     - Call `heater.set_pwm(read_time, self.max_power)`
   - If within the dead band: maintain current state
     - If `self.heating`: keep PWM at `max_power`
     - If not heating: keep PWM at 0
2. The `max_delta` value creates a hysteresis band to prevent rapid on/off cycling

**Control flow**: This is a classic bang-bang controller with hysteresis. The heater state only changes when temperature crosses the band edges, not within the dead band.

#### check_busy(self, eventtime)

Returns True if the heater is currently trying to reach temperature (i.e., the target is non-zero and temperature hasn't stabilized).

---

### PrinterAirHeater

Top-level heater management class. Registered as the `heater_air` component with Klipper.

#### __init__(self, config)

**Signature**: 2 args (self + config)

**Reconstructed logic**:
1. Initializes storage:
   - `self.heaters = {}` -- dict of registered heaters
   - `self.available_heaters = []`
   - `self.available_sensors = []`
   - `self.available_monitors = []`
   - `self.sensor_factories = {}`
   - `self.gcode_id_to_sensor = {}`
   - `self.have_load_sensors = False`
2. Gets printer object
3. Registers event handler for `klippy:ready` -> `_handle_ready`
4. Registers `TURN_OFF_HEATERS` G-code command

#### setup_heater(self, config, sensor=None)

**Signature**: 2-3 args (self + config + optional sensor)

**Reconstructed logic**:
1. Gets the heater name from config
2. Checks if heater is already registered; if so, raises `"Heater %s already registered"`
3. If `sensor` is not provided, calls `setup_sensor(config)` to create one
4. Creates a `Heater_air` instance with the config and sensor
5. Registers the heater in `self.heaters` and `self.available_heaters`
6. Returns the heater object

#### setup_sensor(self, config)

**Signature**: 2 args (self + config)

**Reconstructed logic**:
1. Reads `sensor_type` from config
2. Looks up sensor factory in `self.sensor_factories`
3. If not found, loads sensor types from `temperature_sensors.cfg` (via `get_prefix_sections`)
4. If still not found, raises `"Unknown temperature sensor '%s'"`
5. Creates and returns the sensor object using the factory
6. Calls `sensor.setup_callback(self.temperature_callback)` to register the temp reading callback

#### set_temperature(self, heater, target_temp, wait=False)

**Signature**: 3-4 args (self + heater + target_temp + optional wait)

**Reconstructed logic**:
1. Calls `heater.set_temp(target_temp)` to set the target
2. If `wait` is True:
   - Uses a lambda callback with `register_lookahead_callback`
   - Calls `_wait_for_temperature(heater)` to block until temperature is reached

#### _wait_for_temperature(self, heater)

**Signature**: 2 args (self + heater)

**Reconstructed logic**:
1. Gets the reactor (event loop) from the printer
2. Enters a polling loop:
   - Calls `heater.get_temp()` to get `(smoothed_temp, target_temp)`
   - Computes `temp_diff = abs(smoothed_temp - target_temp)`
   - If `temp_diff` is within tolerance (likely 1-2 degrees), exits the wait
   - If target is 0, exits immediately
   - Calls `heater.check_busy(eventtime)` to determine if still actively heating
   - Pauses (using reactor.pause) for a short interval before re-checking
3. Outputs status: `"%s:%.1f /%.1f"` (current_temp / target_temp)

#### set_air_output(self, heater_name, power)

**Generator/coroutine** (has scope struct `__pyx_scope_struct__set_air_output`)

**Reconstructed logic**:
1. Looks up the heater by name
2. Sets the PWM output directly (bypassing the control algorithm)
3. Uses a lambda callback for deferred execution

#### _handle_ready(self)

Called on `klippy:ready` event. Initializes the heater system after all config is loaded.

#### lookup_heater(self, heater_name)

Looks up a heater by name. Raises `"Unknown heater '%s'"` if not found.

#### register_sensor(self, config, sensor) / register_monitor(self, config)

Registers temperature sensors and monitors.

#### get_all_heaters(self)

Returns list of all registered heater names.

#### get_status(self, eventtime)

Returns dict with: `available_heaters`, `available_sensors`, `available_monitors`

#### turn_off_all_heaters(self)

Sets target temperature to 0 for all registered heaters.

#### load_config(printer)

Module-level function. Registered as the config loader. Creates and returns a `PrinterAirHeater` instance.

---

## Summary of Key Algorithms

### Weight Probe Trigger Mechanism (air.so)

1. The probe uses a **frequency-based weight/strain sensor** (likely a load cell with oscillator)
2. As the nozzle contacts the bed, force on the sensor changes its oscillation frequency
3. Frequency readings are compared against a `target_adc_value` threshold
4. When frequency exceeds the threshold, `REASON_ENDSTOP_HIT` is triggered via `MCU_trsync`
5. Temperature drift compensation adjusts the raw frequency before comparison

### Calibration Process (air.so)

1. User runs `WEIGH_CALIBRATE` G-code
2. Manual probe establishes the Z=0 reference point
3. Automated moves step through multiple Z heights
4. At each height, frequency readings are collected and averaged
5. A monotonically increasing frequency-vs-height curve is built
6. `bisect` + linear interpolation converts frequencies to heights at runtime
7. Validation ensures data quality (monotonic, complete)

### Air Heater Control (heater_air_core.so)

1. **Bang-bang control**: Simple on/off with hysteresis band (`max_delta`)
   - Below `(target - max_delta)`: full power ON
   - Above `(target + max_delta)`: power OFF
   - Within band: maintain current state
2. **Temperature smoothing**: Exponential moving average with configurable `smooth_time`
3. **PWM rate limiting**: Updates throttled by `pwm_delay` to prevent excessive MCU traffic
4. **Safety**: Temperature range validation, max heat time, shutdown handler
5. **Enable pin**: Separate enable/disable control (Qidi hardware-specific)

---

## Notable Findings

1. **Source paths reveal development history**:
   - `air.so` was developed in `/home/mks/cry_studio/air` (note: "cry_studio")
   - `heater_air_core.so` was developed in `/home/mks/studio/heater_air`

2. **Debug output**: `"MKS_DEBUG_AIR:set en val:%s"` shows active debugging/logging for the enable pin

3. **The probe is a strain gauge / load cell type**: Uses frequency-based measurement, not a standard mechanical or inductive probe. The "weigh" terminology and frequency-to-height calibration strongly suggest a load cell with an oscillator circuit.

4. **Only bang-bang control implemented**: Despite `AIR_PID_PARAM_BASE` being referenced, no PID controller class exists in the binary. The air heater uses simple on/off control, likely because chamber heating doesn't need tight control.

5. **The module naming convention**: The `air` module handles both the chamber/air probe AND is named for the air sensor system. The weight-based probe is integrated into the air management system, suggesting the probe sensor shares hardware with the air/chamber system.
