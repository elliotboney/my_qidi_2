; Initialize Qidi Box multi-filament system and select the initial tool
ORCA_QIDI_BOX T=[initial_tool] 

; Pass total layer count to Klipper for progress tracking in Fluidd
SET_PRINT_STATS_INFO TOTAL_LAYER=[total_layer_count]

; Run the main print start macro - heats bed, hotend, and chamber to target temps
PRINT_START BED=[bed_temperature_initial_layer_single] HOTEND=[nozzle_temperature_initial_layer] CHAMBER=[chamber_temperature] EXTRUDER=[initial_no_support_extruder]


; Select the initial tool/extruder
T[initial_tool]

; Wait for all moves to finish
M400





; VERSION 0.2 of this:
; Initialize Qidi Box multi-filament system and select the initial tool
ORCA_QIDI_BOX T=[initial_tool] 

; Pass total layer count to Klipper for progress tracking in Fluidd
SET_PRINT_STATS_INFO TOTAL_LAYER=[total_layer_count]

; Set the materials for the PRINT_END functions
SET_MATERIAL_VAR MATERIALS="{initial_filament_type[0]} {initial_filament_type[1]}"

; Run the main print start macro - heats bed, hotend, and chamber to target temps
PRINT_START BED=[bed_temperature_initial_layer_single] HOTEND=[nozzle_temperature_initial_layer] CHAMBER=[chamber_temperature] EXTRUDER=[initial_no_support_extruder] PRESSURE_ADVANCE={pressure_advance[0]} MESH_MIN={first_layer_print_min[0]},{first_layer_print_min[1]} MESH_MAX={first_layer_print_max[0]},{first_layer_print_max[1]}


; Select the initial tool/extruder
; T[initial_tool] ; Dont think we need this?

; Wait for all moves to finish
M400
