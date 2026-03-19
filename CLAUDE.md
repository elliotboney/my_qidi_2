# Qidi Q2 3D Printer Configuration Repo

## Project Overview
This repo tracks custom/modified Klipper configuration files for a Qidi Q2 3D printer, preserving changes from factory defaults. It is NOT a software project — it's a configuration management repo.

## Printer Details
- **Printer:** Qidi Q2 — fully enclosed CoreXY, Klipper firmware, Fluidd web UI
- **Build Volume:** 270x270x260mm
- **Firmware:** Klipper (on Armbian Linux, user `mks`)
- **Web Interface:** Fluidd
- **API Server:** Moonraker
- **Multi-Material:** Qidi Box (4-slot AMS-style system)
- **SSH Credentials:** user `mks`, password `makerbase`

## Repository Structure
- `printer_data/config/` — All Klipper/Moonraker/Crowsnest config files
  - `printer.cfg` — Main printer config (includes other cfgs)
  - `gcode_macro.cfg` — G-code macros (print start/end, filament handling)
  - `moonraker.conf` — Moonraker API server config
  - `crowsnest.conf` — Webcam streaming config
  - `box.cfg` — Qidi Box main config + filament macros (includes box1.cfg)
  - `box1-4.cfg` — Individual Box unit hardware definitions
  - `plr.cfg` — Power loss recovery
  - `drying.conf` — Filament drying profiles (temp/time per material)
  - `officiall_filas_list.cfg` — Official filament presets
  - `MCU_ID.cfg` — Main MCU serial ID
  - `saved_variables.cfg` — Klipper runtime saved state
  - `Adaptive_Mesh.cfg` — Adaptive bed mesh macro
  - `KAMP_Settings.cfg` — KAMP settings
  - Symlinks: `fluidd.cfg`, `timelapse.cfg`, `KAMP/` → submodules
- `Qidi_Box.md` — Documentation on the Qidi Box system

## Git Submodules
- `Klipper-Adaptive-Meshing-Purging/` — KAMP (adaptive bed mesh + purging)
- `fluidd-config/` — Official Fluidd macros/config
- `moonraker-timelapse/` — Timelapse video component for Moonraker

## Config File Format
- `.cfg` files are Klipper config format (INI-style with `[section]` headers, G-code macros use Jinja2 templating)
- `.conf` files are used by Moonraker and Crowsnest (also INI-style)
- Macros reference `printer.save_variables.variables` for persistent state

## Key Paths on the Printer
- Config directory: `/home/mks/printer_data/config/`
- Klipper socket: `/home/mks/printer_data/comms/klippy.sock`
- Timelapse output: `~/printer_data/timelapse/`
- PLR scripts: `/home/mks/scripts/plr/`

## Known Issues
- `UNLOAD_FILAMENT` macro in `box.cfg` had a bug: `G1 E25 F300` should be `G1 E-25 F300` (missing negative sign causes filament push instead of retract)
- PLA/PETG printing with enclosed chamber can soften filament in PTFE tubes — keep top cover open

## Working on This Repo
- Changes here are meant to be deployed to the printer via SSH or an update script (planned)
- Be careful with `saved_variables.cfg` — it contains runtime state that changes during printing
- Config files use `[include]` directives — check `printer.cfg` for the include chain
- Symlinks in `printer_data/config/` point to submodule directories
