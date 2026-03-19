# Qidi Box Multi-Material System

The [Qidi Box](https://us.qidi3d.com/products/qidi-box) is a smart, sealed filament management system for multi-material and multi-color 3D printing. It handles automatic filament switching, drying, and spool management.

## Specifications

| Spec | Detail |
|------|--------|
| Filament Slots | 4 per unit (up to 4 units / 16 slots chained) |
| Filament Diameter | 1.75mm |
| Max Drying Temperature | 65°C (dries while printing) |
| Power Consumption | 245W |
| Dimensions | 357 x 300 x 234 mm |
| Net Weight | 4.35 kg |
| Shell Material | ABS/PC |
| Compatible Printers | Plus4, Q2, MAX4 (each requires specific BOX Hub & signal cable) |
| Price | ~$228 USD |

## Features

- **Multi-Material Printing** - 4 filament slots per unit, chain up to 4 units for 16 materials
- **Active Drying** - Sealed chambers with real-time 65°C drying during printing, with desiccant support
- **Hardened Steel Extrusion** - Handles carbon fiber, fiberglass, and composite filaments
- **NFC Filament Recognition** - Automatically detects and configures Qidi-branded filament settings
- **Run-out & Tangle Detection** - Auto-switches to backup spool to keep prints running
- **Auto-Reload** - Seamless spool switching for large/long prints
- **Safety Systems** - Dual temperature sensors, smart PTC fuse, auto power cutoff on abnormal temps
- **Humidity Monitoring** - Real-time temperature and humidity display per chamber

## Supported Materials

PLA, PETG, ABS, ASA, PA, PC, PVA (dried), BVOH (dried), PP, POM, HIPS, TPU 64D, and various CF/GF composites.

## Setup Notes (Q2)

- Place the Box on top of or beside the printer
- Connect PTFE tubes (cut to length as needed), control cable, and power cable
- **Update printer firmware to latest version before first use**
- When printing PLA or PETG, place the Box beside the printer and **keep the top cover open** — enclosed chamber heat can soften filament and cause jams
- The Box comes with a built-in upgrade kit for the Q2; no additional accessories needed

## Spool Compatibility

- Supported spool width: **50–72 mm**
- Supported spool diameter: **195–202 mm**
- **Cardboard spools are NOT compatible** — they cause excessive wear on the active drive shaft. Use a spool adapter if you must use them
- Some 195mm diameter spools may have dimensional inconsistencies; a spool adapter is recommended

## Common Issues

### Filament Loading/Unloading Errors

The most frequently reported issue. The Box fails to load or unload filament and shows an error code. After the error, the load option may be greyed out with only "retry unload" available, which often fails again.

**Known firmware bug:** The `UNLOAD_FILAMENT` macro in `box.cfg` may contain `G1 E25 F300` (extrude 25mm) instead of `G1 E-25 F300` (retract 25mm) — a missing negative sign that pushes filament forward instead of pulling it back during unload.

### Chamber Heat Affecting Filament

When printing low-temp materials (PLA/PETG) with the enclosure closed, chamber heat can soften filament inside the PTFE tubes, causing jams and failed prints. Keep the top cover open for these materials.

### QDE Error Codes

Qidi uses QDE error codes for Box diagnostics. Full list available on the [Qidi Wiki QDE Code List](https://wiki.qidi3d.com/en/QIDIBOX/qde-code).

## Relevant Config Files

- [box.cfg](printer_data/config/box.cfg) - Main Box config, MCU definition, and filament macros
- [box1.cfg](printer_data/config/box1.cfg) - Box unit 1 hardware definitions
- [box2.cfg](printer_data/config/box2.cfg) - Box unit 2 hardware definitions
- [box3.cfg](printer_data/config/box3.cfg) - Box unit 3 hardware definitions
- [box4.cfg](printer_data/config/box4.cfg) - Box unit 4 hardware definitions
- [drying.conf](printer_data/config/drying.conf) - Filament drying profiles per material
- [officiall_filas_list.cfg](printer_data/config/officiall_filas_list.cfg) - Official filament presets

## Links

- [Qidi Box Product Page (US)](https://us.qidi3d.com/products/qidi-box)
- [Qidi Box Wiki](https://wiki.qidi3d.com/en/QIDIBOX)
- [Qidi Box Notes & Tips](https://wiki.qidi3d.com/en/QIDIBOX/notes-QIDIBOX)
- [QDE Error Code List](https://wiki.qidi3d.com/en/QIDIBOX/qde-code)
- [Qidi Box Guide (Blog)](https://qidi3d.com/blogs/news/qidi-box-guide-multi-color-filament-system)
- [Qidi Product Support](https://qidi3d.com/pages/product-support)

---

## My Fixes & Improvements

<!-- Add your own notes below about what you've done to improve Box performance -->
