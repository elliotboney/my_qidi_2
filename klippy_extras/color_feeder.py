import logging
import json
import os

class ColorFeederDetectHelper:
    def __init__(self, config, _detect_handler):
        self.printer = printer = config.get_printer()
        self.buttons = printer.load_object(config, 'buttons')
        self.gcode = gcode = self.printer.lookup_object('gcode')
        self.detect_pin = detect_pin = config.get('detect_pin')

        self._detect_handler = _detect_handler

        self.buttons.register_buttons([detect_pin], self._detect_handler)

    # def _detect_handler(self, eventtime, state):
    #     self.gcode.respond_raw("state == %s" % (state, ))


class ColorFeeder:
    def __init__(self, config):
        self.printer = printer = config.get_printer()
        self.gcode = gcode = self.printer.lookup_object('gcode')

        # 将限位作为一个
        self.detect_button = ColorFeederDetectHelper(config, self._detect_handler)

        self.enabled = True
        self.box_list = {}
        self.slots_info = {}        


        for index, slot in enumerate(config.getlist('slots')):
            # 打印 slot 及其 index
            self.box_list[f"T{index}"] = slot
            logging.info(f"import slot index: {index}, slot: {slot} ")


        self._current_feed = None

        data = self.load_from_json("/home/mks/color_feeder.json")
        self._current_feed = data.get('color_feeder')

        self._current_feed_state = "undetected"

        self._is_feeding = False

        gcode.register_command('B0', self.cmd_BOX_IN)
        gcode.register_command('B1', self.cmd_B1)
        gcode.register_command('BOX_OUT', self.cmd_BOX_OUT)
        gcode.register_command('BOX_MODIFY_LIST', self.cmd_BOX_MODIFY_LIST)
        gcode.register_command('LOG_BOX_INFO', self.cmd_LOG_BOX_INFO)

        
    
    def load_from_json(self, filename):
        """从JSON文件读取字典."""
        if not os.path.exists(filename):
            print(f"文件 {filename} 不存在。")
            return None
        with open(filename, 'r') as json_file:
            data = json.load(json_file)
        return data

    def _detect_handler(self, eventtime, state):
        if state == 1:
            self._current_feed_state = "detected"
        else:
            self._current_feed_state = "undetected"
        self.gcode.respond_raw("state == %s" % (self._current_feed_state, ))

    def cmd_B1(self, gcmd):
        index = gcmd.get_int('T')
        slot_index = 'T' + str(index)
        slot = self.box_list[slot_index]
        if self._current_feed_state == "detected":
            if self._current_feed == slot:
        #         # 进1000
                script = "ECHELON_SP STEPPER=" + slot + "\nECHELON_STEPPER STEPPER=" + slot + " MOVE=1000"
                self.gcode.run_script_from_command(script)
            else:
                script = "ECHELON_INVERT STEPPER=" + slot + "\nECHELON_SP STEPPER=" + slot + "\nECHELON_STEPPER_HOMING STEPPER=" + slot + " MOVE=-800 RETRACT=1 PDI=-50\nECHELON_INVERT STEPPER=" + slot
                self.gcode.run_script_from_command(script)
        else:
            script = "ECHELON_SP STEPPER=" + slot + "\nECHELON_STEPPER_HOMING STEPPER=" + slot + " MOVE=1000 RETRACT=2 PDI=500\n"  
            self.gcode.run_script_from_command(script)

    # def cmd_BOX_INVERT(self, gcmd):



    def cmd_BOX_IN(self, gcmd):
        index = gcmd.get_int('T')
        slot_index = 'T' + str(index)
        self._current_feed = slot = self.box_list[slot_index]
        self.gcode.respond_raw("BOX_IN T%s %s" % (index, slot, ))
        script = "ECHELON_SP STEPPER=" + slot + "\nECHELON_STEPPER STEPPER=" + slot + " MOVE=500"  
        self.gcode.run_script_from_command(script)

    def cmd_BOX_OUT(self, gcmd):
        if self._current_feed_state == 'detected':
            if self._current_feed != None:
                script = "ECHELON_INVERT STEPPER=" + self._current_feed + "\nECHELON_SP STEPPER=" + self._current_feed + "\nECHELON_STEPPER_HOMING STEPPER=" + self._current_feed + " MOVE=-800 RETRACT=1 PDI=-50\nECHELON_INVERT STEPPER=" + self._current_feed
                # script = "ECHELON_SP STEPPER=" + self._current_feed + "\nECHELON_STEPPER STEPPER=" + self._current_feed + " MOVE=-50"  
                self.gcode.run_script_from_command(script)


    def cmd_BOX_MODIFY_LIST(self, gcmd):
        key = gcmd.get('KEY')
        value = gcmd.get('VALUE')
        self.box_list[key] = value
        self.gcode.respond_info(f"{self.box_list}")

    def cmd_LOG_BOX_INFO(self, gcmd):
        self.get_all_slot_info(0)
        logging.info(f"{self.slots_info}")

    def get_all_slot_info(self, eventtime):
        for t_name, slot_name in self.box_list.items():
            object = 'feed_slot ' + slot_name
            status = self.printer.lookup_object(object).get_status(eventtime)
            self.slots_info[t_name] = status

    def get_status(self, eventtime):
        self.get_all_slot_info(eventtime)
        return {
            'map': self.box_list,
            'current_feed': self._current_feed,
            'current_feed_state': self._current_feed_state, 
            'slots_info': self.slots_info
        }

def load_config(config):
    return ColorFeeder(config)