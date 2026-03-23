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
