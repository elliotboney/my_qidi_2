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
| [printer.cfg](printer_data/config/printer.cfg) | Main Klipper printer configuration (kinematics, steppers, heaters, probe, bed mesh, etc.) |
| [gcode_macro.cfg](printer_data/config/gcode_macro.cfg) | Custom G-code macros for print start/end, filament handling, and utility functions |
| [moonraker.conf](printer_data/config/moonraker.conf) | [Moonraker](https://moonraker.readthedocs.io/) API server configuration (authorization, timelapse, file manager) |
| [crowsnest.conf](printer_data/config/crowsnest.conf) | [Crowsnest](https://github.com/mainsail-crew/crowsnest) webcam/streaming daemon configuration |
| [MCU_ID.cfg](printer_data/config/MCU_ID.cfg) | Main MCU serial ID definition |
| [box.cfg](printer_data/config/box.cfg) | Qidi Box multi-material system configuration and filament macros |
| [box1.cfg](printer_data/config/box1.cfg) | Box unit 1 hardware definitions |
| [box2.cfg](printer_data/config/box2.cfg) | Box unit 2 hardware definitions |
| [box3.cfg](printer_data/config/box3.cfg) | Box unit 3 hardware definitions |
| [box4.cfg](printer_data/config/box4.cfg) | Box unit 4 hardware definitions |
| [plr.cfg](printer_data/config/plr.cfg) | Power loss recovery macros and configuration |
| [drying.conf](printer_data/config/drying.conf) | Filament drying profiles (temperature/time settings per material type) |
| [officiall_filas_list.cfg](printer_data/config/officiall_filas_list.cfg) | Official filament preset definitions (temperatures, material types) |
| [saved_variables.cfg](printer_data/config/saved_variables.cfg) | Klipper saved variables (runtime state persisted across restarts) |
| [Adaptive_Mesh.cfg](printer_data/config/Adaptive_Mesh.cfg) | Adaptive bed mesh calibration macro (probes only the print area) |
| [KAMP_Settings.cfg](printer_data/config/KAMP_Settings.cfg) | KAMP configuration settings (mesh margin, purge settings, etc.) |
| [fluidd.cfg](printer_data/config/fluidd.cfg) | Fluidd client macros (symlink to fluidd-config submodule) |
| [timelapse.cfg](printer_data/config/timelapse.cfg) | Timelapse Klipper macros (symlink to moonraker-timelapse submodule) |
| [KAMP/](printer_data/config/KAMP) | KAMP configuration directory (symlink to KAMP submodule) |

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
