{ if current_extruder != next_extruder }
    M118 Changing Filament G-Code Start: flush lengths 1:{flush_length_1}, 2:{flush_length_2}, 3:{flush_length_3}, 4:{flush_length_4}
    G1 Z{max_layer_z + 3.0} F1200
    TOOL_CHANGE_START F=[current_extruder] T=[next_extruder]
    BUFFER_MONITORING ENABLE=0
    DISABLE_ALL_SENSOR
    M106 S255
    MOVE_TO_TRASH
    {if long_retractions_when_cut[previous_extruder]}
        G1 E-{retraction_distances_when_cut[previous_extruder]} F{old_filament_e_feedrate}
    {else}
        G1 E-10 F{old_filament_e_feedrate}
    {endif}
    M400
    CUT_FILAMENT T=[current_extruder]
    MOVE_TO_TRASH
    M106 P2 S0
    UNLOAD_T[current_extruder]
    T[next_extruder]
    {if nozzle_temperature_range_high[current_extruder] >= nozzle_temperature_range_high[next_extruder]}
        M104 S{nozzle_temperature_range_high[current_extruder]}
    {else}
        M104 S{nozzle_temperature_range_high[next_extruder]}
    {endif}
    ; FLUSH_START
    M106 S25
    G1 E80 F300
    ; FLUSH_END
    {if long_retractions_when_cut[previous_extruder]}
        G1 E{retraction_distances_when_cut[previous_extruder]} F{old_filament_e_feedrate}
    {endif}
    {if flush_length_1 > 1}
        M118 flush_length_1 > 1 flush start
        ; FLUSH_START
        {if flush_length_1 > 23.7}
            G1 E23.7 F{old_filament_e_feedrate}
            G1 E{(flush_length_1 - 23.7) * 0.02} F50
            G1 E{(flush_length_1 - 23.7) * 0.23} F{old_filament_e_feedrate}
            G1 E{(flush_length_1 - 23.7) * 0.02} F50
            G1 E{(flush_length_1 - 23.7) * 0.23} F{new_filament_e_feedrate}
            G1 E{(flush_length_1 - 23.7) * 0.02} F50
            G1 E{(flush_length_1 - 23.7) * 0.23} F{new_filament_e_feedrate}
            G1 E{(flush_length_1 - 23.7) * 0.02} F50
            G1 E{(flush_length_1 - 23.7) * 0.23} F{new_filament_e_feedrate}
        {else}
            G1 E{flush_length_1} F{old_filament_e_feedrate}
        {endif}
        G1 E-[old_retract_length_toolchange] F1800
        ; FLUSH_END
    {endif}
    {if flush_length_2 > 1}
        M118 flush_length_2 > 1 flush start
        ; FLUSH_START
        G1 X92 F9000
        G1 E[old_retract_length_toolchange] F300
        G1 E{flush_length_2 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_2 * 0.02} F50
        G1 E{flush_length_2 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_2 * 0.02} F50
        G1 E{flush_length_2 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_2 * 0.02} F50
        G1 E{flush_length_2 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_2 * 0.02} F50
        G1 E{flush_length_2 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_2 * 0.02} F50
        G1 E-[new_retract_length_toolchange] F1800
        ; FLUSH_END
    {endif}
    {if flush_length_3 > 1}
        M118 flush_length_3 > 1 flush start
        ; FLUSH_START
        G1 X85 F9000
        G1 E[new_retract_length_toolchange] F300
        G1 E{flush_length_3 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_3 * 0.02} F50
        G1 E{flush_length_3 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_3 * 0.02} F50
        G1 E{flush_length_3 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_3 * 0.02} F50
        G1 E{flush_length_3 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_3 * 0.02} F50
        G1 E{flush_length_3 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_3 * 0.02} F50
        G1 E-[new_retract_length_toolchange] F1800
        ; FLUSH_END
    {endif}
    {if flush_length_4 > 1}
        M118 flush_length_4 > 1 flush start
        ; FLUSH_START
        G1 X92 F9000
        G1 E[new_retract_length_toolchange] F300
        G1 E{flush_length_4 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_4 * 0.02} F50
        G1 E{flush_length_4 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_4 * 0.02} F50
        G1 E{flush_length_4 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_4 * 0.02} F50
        G1 E{flush_length_4 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_4 * 0.02} F50
        G1 E{flush_length_4 * 0.18} F{new_filament_e_feedrate}
        G1 E{flush_length_4 * 0.02} F50
        G1 E-[new_retract_length_toolchange] F1800
        ; FLUSH_END
    {endif}
    M400
    M106 S255
    M104 S[new_filament_temp]
    INIT_SYNC_BUFFER_STATE
    BUFFER_MONITORING ENABLE=1
    G1 E10 F25 
    M109 S[new_filament_temp]
    G1 E-5 F1800
    CLEAR_OOZE
    TOOL_CHANGE_END
    G1 Y270 F8000
    M106 S0
    G1 E2 F1800
    ENABLE_ALL_SENSOR
    M118 Changing Filament G-Code END
{endif}