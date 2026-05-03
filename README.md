# Qidi Q2 Klipper Configuration

Custom and modified configuration files for the [Qidi Q2](https://qidi3dprinter.com/products/q2) 3D printer, tracked via Git to preserve changes from the factory defaults.

## About the Qidi Q2

The [Qidi Q2](https://qidi3dprinter.com/products/q2) is a fully enclosed CoreXY 3D printer running [Klipper](https://www.klipper3d.org/) firmware with a [Fluidd](https://docs.fluidd.xyz/) web interface. It features an actively heated chamber, multi-material support via the Qidi Box system, and a build volume of 270x270x260mm.

- [Qidi Official Site](https://qidi3dprinter.com/)
- [Qidi Q2 Product Page](https://qidi3dprinter.com/products/q2)
- [Qidi Wiki](https://wiki.qidi3d.com/)
- [Klipper Documentation](https://www.klipper3d.org/)
- [Fluidd Documentation](https://docs.fluidd.xyz/)
- [Moonraker Documentation](https://moonraker.readthedocs.io/)

## Configuration Files

| File | Description |
|------|-------------|
| [printer.cfg](printer_data/config/printer.cfg) | Main Klipper printer configuration (steppers, heaters, probe, etc.) |
| [gcode_macro.cfg](printer_data/config/gcode_macro.cfg) | Custom G-code macros for print start/end, filament handling, and utility functions |
| [officiall_filas_list.cfg](printer_data/config/officiall_filas_list.cfg) | Official filament preset definitions (temperatures, material types) |
| [box.cfg](printer_data/config/box.cfg) | Qidi Box multi-material system configuration and filament macros |
| [box1.cfg](printer_data/config/box1.cfg) | Box unit 1 hardware definitions |
| [box2.cfg](printer_data/config/box2.cfg) | Box unit 2 hardware definitions |
| [box3.cfg](printer_data/config/box3.cfg) | Box unit 3 hardware definitions |
| [box4.cfg](printer_data/config/box4.cfg) | Box unit 4 hardware definitions |
| [Adaptive_Mesh.cfg](printer_data/config/Adaptive_Mesh.cfg) | Adaptive bed mesh calibration macro (probes only the print area) |
| [KAMP_Settings.cfg](printer_data/config/KAMP_Settings.cfg) | KAMP configuration settings (mesh margin, purge settings, etc.) |
<!-- | [plr.cfg](printer_data/config/plr.cfg) | Power loss recovery macros and configuration | -->
<!-- | [moonraker.conf](printer_data/config/moonraker.conf) | [Moonraker](https://moonraker.readthedocs.io/) API server configuration (authorization, timelapse, file manager) | -->
<!-- | [crowsnest.conf](printer_data/config/crowsnest.conf) | [Crowsnest](https://github.com/mainsail-crew/crowsnest) webcam/streaming daemon configuration | -->
<!-- | [MCU_ID.cfg](printer_data/config/MCU_ID.cfg) | Main MCU serial ID definition | -->
| [drying.conf](printer_data/config/drying.conf) | Filament drying profiles (temperature/time settings per material type) |
<!-- | [fluidd.cfg](printer_data/config/fluidd.cfg) | Fluidd client macros (symlink to fluidd-config submodule) | -->
<!-- | [timelapse.cfg](printer_data/config/timelapse.cfg) | Timelapse Klipper macros (symlink to moonraker-timelapse submodule) | -->

## Klippy Extras

The [klippy_extras/](klippy_extras/) directory contains Qidi's custom Klipper modules, synced from the printer's `/home/mks/klipper/klippy/extras/` directory. Qidi runs a [modified fork of Klipper](https://github.com/QIDITECH/klipper) with proprietary additions — these are **not** part of mainline Klipper and include:

- **Proprietary compiled `.so` modules** (10 files) — closed-source binary extensions not in [mainline Klipper](https://github.com/Klipper3d/klipper/tree/master/klippy/extras):
  - `box_stepper.so`, `box_extras.so`, `box_rfid.so`, `box_detect.so` — Qidi Box hardware drivers
  - `air.so`, `heater_air_core.so`, `aht20_f.so` — Air/chamber heating and sensor drivers
  - `buttons_irq.so`, `cs1237.so`, `hx711.so` — Input/sensor hardware drivers
- **Qidi-added Python modules** (13 files) — custom modules not found in mainline Klipper:
  - `color_feeder.py`, `feed_slot.py`, `box_heater_fan.py` — Qidi Box multi-material logic
  - `chamber_fan.py`, `heater_air.py`, `heater_feng.py` — Chamber/air heating control
  - `echelon_stepper.py`, `closed_loop.py` — Custom stepper/motor control
  - `autotune_tmc.py`, `motor_constants.py`, `motor_database.cfg` — TMC driver autotuning
  - `gcode_shell_command.py`, `probe_air.py` — Utility extensions
Only Qidi-specific files are tracked here — upstream Klipper modules (both identical and version-drift copies) have been removed. The full set can always be synced from the printer if needed

> **Warning:** Qidi [explicitly warns](https://qidi3d.com/pages/software-firmware) against updating to mainline Klipper — their firmware depends on these custom modules, and replacing them will break printer functionality. These files are tracked here for reference and diffing against factory updates.

## Notable Customizations

### Slicer-side

- **[`slicer_configs/change_filament.gcode`](slicer_configs/change_filament.gcode) — removed redundant heat-up/cool-down on tool change.** The stock Orca filament-change script ramped the hotend to `nozzle_temperature_range_high` (the upper end of the filament's temp range) for the initial purge, then dropped back to `new_filament_temp` and waited via `M109` for the cooldown. On same-material multi-color prints this added a needless heat + cool cycle to every swap. The script now stays at `new_filament_temp` for the whole change and the trailing `M109` becomes a no-op. If you ever swap to a hotter material mid-print you'll want to revisit this.

### Print-start / Print-end overhaul (KAMP 2.0 + Smart Filter)

Adapted from the German community guide [Qidi Q2 Software Upgrade — KAMP 2.0, Lüftersteuerung, Cutterschutz, Smart Filter](https://forum.drucktipps3d.de/forum/thread/46161-guide-qidi-q2-software-upgrade-kamp-2-0-l%C3%BCftersteuerung-cutterschutz-smart-filte/?l=2) on drucktipps3d.de, with local tweaks for this printer.

- **`PRINT_START` (rewritten in `gcode_macro.cfg`)** — replaces the old `PRINT_START_V0`. Computes an adaptive bed mesh inline from slicer-supplied `MESH_MIN`/`MESH_MAX`, picks `bicubic` vs `lagrange` based on probe count, and calls `_BED_MESH_CALIBRATE` directly (`PROFILE=kamp_Q2`) instead of relying on the stock KAMP wrapper. Logs the calculated mesh bounds + algorithm to the console at start.
- **`PRINT_END` (rewritten)** — adds material-aware cool-down. Tracks which tools were actually used during the print via `MARK_TOOL_USED`, then on print end checks if any used material is hazardous (ASA / ABS / PC / PA / Nylon / Carbon / PPS). Hazardous prints wait for chamber to drop below 50 °C before activating filtering for 15 min; non-hazardous prints kick off a 5-min ventilation cycle immediately.
- **Smart filter / cool-down delayed gcodes** — `SMART_COOLING_MONITOR`, `FILTER_START_ACTION`, `FILTER_STOP` drive the chamber circulation fan after print end. `SET_MATERIAL_VAR` is called from the slicer start gcode to populate the per-tool material list.
- **`BOX_PRINT_START_2`** — replacement for the stock `BOX_PRINT_START` with extracted/adapted purge logic for cleaner Box transitions.
- **`CANCEL_PRINT` / `PAUSE` rebuilt** — now `rename_existing` the base versions instead of the old V0 commented variants. Cancel parks at the purge chute, triggers timelapse render, and does a full sensor/heater/box shutdown.
- **`smart_q2_macro.cfg` removed** — it was the staging file while porting these macros from the forum guide; everything now lives in `gcode_macro.cfg` and the include was dropped from `printer.cfg`.

## Documentation

- [Qidi Box Multi-Material System](Qidi_Box.md) - Specifications, setup notes, common issues, and fixes for the Qidi Box

## Git Submodules

This repo includes the following projects as Git submodules:

### [Klipper Adaptive Meshing & Purging (KAMP)](https://github.com/kyleisah/Klipper-Adaptive-Meshing-Purging)

A unique leveling solution for Klipper-enabled 3D printers. Instead of probing the entire bed, KAMP generates an adaptive mesh confined to the actual print area and performs intelligent nozzle purging adjacent to it. Supports various probe types (inductive, BLTouch, Klicky, Euclid, Voron Tap) and integrates with Klipper's built-in exclude object system.

### [fluidd-config](https://github.com/fluidd-core/fluidd-config)

The official Fluidd configuration package providing essential macros and settings for the Fluidd web interface. Includes customizable PAUSE, RESUME, and CANCEL_PRINT macros, flexible parking positions, temperature management during pauses, and filament runout sensor integration.

### [moonraker-timelapse](https://github.com/mainsail-crew/moonraker-timelapse)

A third-party Moonraker component that automatically creates timelapse videos of 3D print jobs. Captures frames during printing and compiles them into video, enabling easy documentation and sharing of prints.

## SSH Access

To SSH into the Qidi Q2 for editing config files or running scripts:

```bash
ssh mks@<printer-ip>
```

- **Username:** `mks`
- **Password:** `makerbase`

## Setup

After cloning, initialize the submodules:

```bash
git clone --recurse-submodules <repo-url>
# or if already cloned:
git submodule update --init --recursive
```

The config files in `printer_data/config/` use symlinks to reference the submodule contents (KAMP, fluidd.cfg, timelapse.cfg).
