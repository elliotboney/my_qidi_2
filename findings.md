# Macro Review Findings

Tracking doc for findings from the 2026-05-03 three-agent review of:
- Print lifecycle: `gcode_macro.cfg`, `KAMP_Settings.cfg`, `KAMP/Adaptive_Meshing.cfg`, `plr.cfg`
- Multi-material: `box.cfg`, `box1-4.cfg`
- Hardware/thermal: `printer.cfg`, `drying.conf`, `officiall_filas_list.cfg`

Plus runtime cross-check from `~/printer_data/logs/klippy.log` pulled the same day.

Severity legend: **C**ritical / **H**igh / **M**edium / **L**ow / **N**it

---

## Resolved

- [x] **F01 [C] Duplicate `[exclude_object]` section** — `printer.cfg:474` AND `gcode_macro.cfg:1494`. Would fail config load on `SAVE_CONFIG`. Fixed by Sir E before this doc was written; confirmed via clean post-restart log.
- [x] **F02 [—] M1189 Jinja `'dict object' has no attribute 'MSG'` error** — historical, lines 27629/31083 of klippy.log. Older template version. Current template tested working (`M1189 test` → ok).
- [x] **F03 [—] `Malformed command 'DEBUG_MSG ...'`** — historical, line 47134 of klippy.log. Transitional state where PRINTER_INIT delayed_gcode called a non-existent `DEBUG_MSG`. Already replaced with `M1189`.
- [x] **F04 [—] UNLOAD_FILAMENT duplicate definition removed** — `box.cfg` copy deleted by Sir E. The `G1 E25 F300` *positive* sign is **intentional, not a bug** — sequence is: CUT_FILAMENT (E-60 retract + cut) → MOVE_TO_TRASH → UNLOAD_T (box-side retract pulls top piece back to box) → `G1 E25 F300` pushes the cut stub out the nozzle → M104 S0. CLAUDE.md "Known Issue" entry was wrong; removed.
- [x] **F05 [C] PLR mesh persistence + graceful fallback** — Two-part fix:
  1. `gcode_macro.cfg` PRINT_START — after `BED_MESH_CALIBRATE`, runs `SAVE_VARIABLE profile_name='"default"'` + `SAVE_CONFIG_QD` so the adaptive mesh persists to printer.cfg without restarting Klippy.
  2. `plr.cfg:37-49` — `RESUME_INTERRUPTED` now checks if the named profile exists; falls back to `default` mesh, then to "no mesh" with a warning, instead of erroring out.
  - Side effects: every PRINT_START writes a `printer-2026MMDD_HHMMSS.cfg` backup (already gitignored via `printer-20*.cfg` pattern). Adds ~100-500ms to PRINT_START.
  - Profile name updated from `kamp_Q2` → `default` as part of F06 (KAMP wrapper saves to `default` slot since it doesn't forward PROFILE param).
- [x] **F06 [H] KAMP integration unified — switched to KAMP wrapper for adaptive mesh**:
  1. Deleted inline KAMP math (`gcode_macro.cfg:106-146`) — was duplicating ~80% of `KAMP/Adaptive_Meshing.cfg` with coarser bbox-only data.
  2. Trimmed dead console-output lines that referenced inline-only vars (`algo`, `points_x`, `x_min`, `margin`).
  3. PRINT_START now calls plain `BED_MESH_CALIBRATE` (KAMP wrapper) instead of `_BED_MESH_CALIBRATE` (raw builtin). KAMP reads per-object polygons from `printer.exclude_object.objects` — more accurate than bbox for sparse multi-part prints.
  4. Confirmed Orca emits `EXCLUDE_OBJECT_DEFINE` *before* `PRINT_START` in gcode (lines 130-140 vs 155 in tested file), so KAMP's polygon-reading logic works.
  5. Bumped `_KAMP_Settings.mesh_margin: 0 → 10` to preserve the inline path's 10mm margin.
  - Tradeoff: KAMP overwrites the `default` mesh profile every print. Existing `[bed_mesh default]` was a 3×3 auto-saved artifact, not a manually-tuned baseline, so no loss.
- [x] **F08 [H] `idle_timeout` reduced 43200s → 1800s** — `printer.cfg:460`. 30 min covers normal mid-print interventions (Box swap, RFID re-scan, walking away briefly) while still cutting heaters in time if something goes wrong.
- [x] **F11 [M] PRINT_START purge dedup** — `gcode_macro.cfg` PRINT_START now gates `EXTRUSION_AND_FLUSH` on `filament_detected and last_load_slot == value_t` (same-slot reprint). On tool-change prints `BOX_PRINT_START_2` already runs the identical 200mm purge loop as part of its load sequence, so the second flush was pure duplicate. Saves ~200mm filament per tool-change print. `CLEAR_NOZZLE` (brush scrub) and `LINE_PURGE` left alone — they do non-redundant work.
- [x] **F12 [M] M1189 logging refactor finished** — converted 12 stale `G118` calls (RESUME_PRINT, RESUME, RESUME_1, M4030, M4031, CUT_FILAMENT_1) to `M1189`. `G118` is not a real Klipper command — these had been silently dropped. Also converted 1 raw `M118` in `plr.cfg save_last_file` → `M1189`. Left untouched: 7 `M117` (LCD line writes — different purpose) and 1 `M1188 Canceled print!` (M1188 is a real defined macro at gcode_macro.cfg:12, not a typo — it's an accent-colored user message).
- [x] **F10 [H] CANCEL_PRINT now retracts before park** — added `M83 / G1 E-3 F1800` (gated on `printer.extruder.can_extrude` so it's a no-op when hotend is cold). Prevents blob welding to model on cancel-during-extrude.
- [x] **F14 [M] `M83` before E moves in UNLOAD_FILAMENT** — added `M83` between `UNLOAD_T{T}` and `G1 E25 F300`. After `EXTRUDER_UNLOAD` returns, E mode was non-obvious — `cmd_CUT_FILAMENT` (decompiled) explicitly sets M83 for the same reason.
- [x] **F25 [L] `params.T` now defaults to 0** — `gcode_macro.cfg` UNLOAD_FILAMENT: `params.T|int` → `params.T|default(0)|int`. Console-typed `UNLOAD_FILAMENT` (no T) no longer crashes after M1189 already logged.
- [x] **F13 [M] DEFERRED — original review finding was wrong.** `M104 S140` at line 174 is intentional cool-down: `BOX_PRINT_START_2` / `EXTRUSION_AND_FLUSH` / `CLEAR_NOZZLE` heat to `hotendtemp` (e.g. 220) before this point, so line 174 cools back to 140 for probing. The reviewer missed the intermediate `M109` calls. Removing it would probe at 190°C → ooze. Closed as not-a-bug.
- [x] **F07 [H] DEFERRED — leave Qidi factory `max_error: 300` alone.** Slow chamber heat-up + low max_temp (70°C) means the permissive cumulative-error window is likely intentional. Tightening to stock-Klipper 120 would risk spurious runaway trips during normal chamber climbs.
- [x] **F09 [H] DEFERRED — cold-extrude guard not needed in practice.** Real-world use is always through PRINT_END / slicer / mid-print where hotend is already hot. Manual cold-console unload is an edge case the user can manage themselves. Box-side filament motion through PTFE tubes already works reliably; not worth adding friction or surprise auto-heat.

---

## Open — Critical / High

---

## Open — Medium

- [ ] **F15 [M] Macro guard silent no-op when `enable_box == 0`** — `box.cfg:13-25` and dup. Whole body wrapped in `enable_box == 1`. UI manual unload appears to do nothing in single-spool mode. Add `{% else %} M118 Box not enabled %}`.

- [ ] **F16 [M] Z_TILT_ADJUST followed by extra G28 Z** — `gcode_macro.cfg:208`. Doubles ~30s and toggles chamber heater off/on mid-startup (homing_override disables chamber heater for G28 Z). Confirm intent.

- [ ] **F17 [M] `[heater_generic chamber]` not using Qidi proprietary `heater_air`** — `printer.cfg:298`. Q2 uses stock `[heater_generic]` + `[controller_fan chamber_fan]`. Decompiled `air_and_heater_analysis.md` describes `heater_air` as a separate registered component. May be correct for Q2 (Plus/Max use the bigger system) — confirm via `HELP HEATER_AIR_*` over SSH.

- [ ] **F18 [M] `[controller_fan chamber_fan] stepper:` is empty** — `printer.cfg:359`. Parses but means "no steppers trigger this fan." Likely intentional but trailing-empty-key style is fragile. Either remove the line or list explicit steppers.

- [ ] **F19 [M] Drying temps too hot for PETG/PLA/TPU** — `drying.conf`
  - PETG: 90°C bed / 60°C chamber / 360 min — Tg ~80°C, lengthy.
  - PLA: 70°C bed / 50°C / 360 min — Tg ~60°C, at deformation edge.
  - TPU: 90°C bed / 60°C / 720 min — most TPU softens >60°C, 12h risks fusing spool.
  - **Open question:** does the dryer "bed" temp apply to a heated plate the spool sits on, or to chamber air? Changes whether these are dangerous or fine.

- [ ] **F20 [M] Skipping CLEAR_LAST_FILE clears PLR `was_interrupted`** — `gcode_macro.cfg:874` (CANCEL_PRINT) calls CLEAR_LAST_FILE. Correct semantics for cancel. Documenting the interaction with PLR (F05 chain).

---

## Open — Low / Nit

- [ ] **F21 [L] `M84` ordering in PRINT_END** — `gcode_macro.cfg:309`. M84 fires before TIMELAPSE_RENDER and other end actions. CANCEL_PRINT puts M84 second-to-last (line 867). Cosmetic consistency.

- [ ] **F22 [L] `min_temp: -60` / `-100` defeats thermistor-disconnect detection** — `printer.cfg:295` (bed), `:309` (chamber), `:323` (chamber thermal protection). Qidi factory pattern but bad practice — disconnected thermistor floats and no shutdown triggers in that direction.

- [ ] **F23 [L] `extruder smooth_time: 0.000001`** — `printer.cfg:74`. Effectively disables thermistor smoothing. Stock default 1.0s. With MAX6675 thermocouple latency, may produce false `verify_heater` trips. Qidi-shipped oddity.

- [ ] **F24 [L] `M104 S0` after retract in UNLOAD breaks fast reload flow** — `box.cfg:22`, `gcode_macro.cfg:338`. Forces full reheat if user is swap-unload-reload. Per commit `9ee190f` deliberately preserves heat across changes — this looks regressive for the swap case but correct for user-finished-printing case. Confirm intent.

- [ ] **F26 [L] T4-T15 / UNLOAD_T4-T15 macros are dead code** — `box1.cfg:160-326`. `box_count = 1` in saved_variables → these reference slot4-slot15 which only exist in box2-4.cfg, which aren't included. Not active bugs but clutter.

- [ ] **F27 [L] PLR detect on boot is disabled** — `gcode_macro.cfg:718` `DETECT_INTERRUPTION` is commented out in `PRINTER_INIT`. PLR is currently a manual workflow.

- [ ] **F28 [L] Extruder PID/temp range checks for high-temp filaments** — `officiall_filas_list.cfg`. UltraPA-CF25 max 320°C, PET-CF/PPS-CF/PPS-GF max 350°C. Within `extruder.max_temp 375`, but confirm hotend is truly all-metal rated.

- [ ] **F29 [L] Blank filament presets** — `officiall_filas_list.cfg` fila15-17, 21-22, 28-29 all empty. Selecting blank slot fails safe via `min_extrude_temp 175` rejection. Cleanup awareness.

- [ ] **F30 [N] `chamber_circulation_fan` orphan-fan risk** — `gcode_macro.cfg:165`. PRINT_START sets `M106 P3 S255` if `chambertemp == 0`. PRINT_END/CANCEL_PRINT do clean up, but a crash between PRINT_START and PRINT_END leaves it running. Belt-and-suspenders only.

- [ ] **F31 [N] `samples_tolerance_retries:10`** — `printer.cfg:447`. Generous; typical 3-5. Stock-Qidi value. Wastes time before erroring on a noisy probe.

- [ ] **F32 [N] Date typo `2026-03-99`** — `printer.cfg:286` comment.

- [ ] **F33 [N] PETG `purge_height: 0.8` in KAMP** — `KAMP/KAMP_Settings.cfg:25`. Default Voron 0.6. Test before changing.

- [ ] **F34 [N] Inconsistent box temp sensor naming** — `box1.cfg:67,73` use `_heater_temp_a_box1` (hidden, leading `_`); box2-4 use `heater_temp_a_box2/3/4` (visible). Pure cosmetic.

- [ ] **F35 [N] Untracked `smart_q2_macro.cfg`** — full duplicate of PRINT_START/PRINT_END/CANCEL_PRINT. Currently not in any `[include]` chain. Inert today; foot-gun if someone adds an include line. Either delete, gitignore, or merge.

- [ ] **F36 [N] Old `printer-2026*.cfg` backup snapshots** — accumulating in `printer_data/config/`. Klipper doesn't include them, but they could be accidentally renamed. Move to `_backups/` subdir.

- [ ] **F37 [N] Multiple commented PID blocks** — `printer.cfg:88-94`. Cleanup opportunity, not a defect.

---

## Runtime observations (from klippy.log)

- [ ] **F38 [L] MCU 'mcu' first-connect fails on cold boot** — log lines 6510 / 9589. `Failed automated reset of MCU 'mcu'` then succeeds on retry. USB enumeration race. Common — only worth chasing if it ever fails to recover.

- [ ] **F39 [L] `Remote method 'timelapse_render' not registered`** — log line ~27680. Moonraker timelapse component hadn't registered when PRINT_END fired `TIMELAPSE_RENDER`. Retried successfully. Could harden with delay or guard.

- [ ] **F40 [—] Last bed_mesh probed full 6×6 grid** — log lines 27580+. Either no print was running or slicer didn't emit `EXCLUDE_OBJECT_DEFINE`. Worth checking on a real print to see if KAMP-adaptive is actually being driven.

---

## Open questions

1. **F19** — does the Qidi Box dryer "bed" temp apply to a heated plate the spool sits on, or to chamber air?
2. **PLR scripts** — what's inside `~/scripts/plr/plr.sh` and `~/scripts/plr/update_gcode_lines.sh`? Needed to fully review F05 / PLR resume sequence.
3. **F17** — is the Q2 chamber supposed to use Qidi's `heater_air` module, or is `heater_generic chamber` the correct stock-Q2 setup?

---

## Suggested order of attack

Everything else — schedule per appetite.
