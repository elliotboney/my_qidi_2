# Qidi Q2 Documentation

## G-Code Command Reference

- [gcode_commands.md](gcode_commands.md) — Complete reference of all custom G-code commands registered by klippy_extras modules (Python + .so), with parameters, descriptions, and data mappings (material IDs, color IDs)

## Klippy Extras (.so Module Analysis)

Reverse-engineered documentation of Qidi's proprietary Cython-compiled Klipper modules.

- [klippy_extras_analysis.md](klippy_extras_analysis.md) — Master reference: all modules, classes, methods, G-code commands, constants, and error codes

### Detailed Decompilation Reports

| Report | Modules | Highlights |
|--------|---------|------------|
| [box_extras_analysis.md](klippy_extras_decompiled/box_extras_analysis.md) | box_extras.so | Core Box coordinator: 26+ G-code commands, drying system, tool change (3 modes), ooze/wipe, RFID init |
| [box_stepper_analysis.md](klippy_extras_decompiled/box_stepper_analysis.md) | box_stepper.so | Filament motion: 4-stage slot load, 19 error codes, toolhead shaking, auto-reload with RFID priority |
| [box_detect_analysis.md](klippy_extras_decompiled/box_detect_analysis.md) | box_detect.so | USB auto-detection: pyudev serial scanning, config templates, V1-to-V2 firmware auto-upgrade |
| [air_and_heater_analysis.md](klippy_extras_decompiled/air_and_heater_analysis.md) | air.so, heater_air_core.so | Weight probe (frequency-based, drift compensation) + chamber heater (bang-bang control) |
| [sensors_and_io_analysis.md](klippy_extras_decompiled/sensors_and_io_analysis.md) | cs1237.so, hx711.so, aht20_f.so, buttons_irq.so, box_rfid.so | ADC drivers, I2C temp sensor, IRQ buttons, FM17550 NFC/RFID reader |

---

*Analysis performed 2026-03-22 using radare2 6.1.2 with r2dec/r2ghidra decompiler plugins.*
