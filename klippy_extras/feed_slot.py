import time
import json
import os

from . import echelon_stepper
from . import bus
from . import fm17550

import logging

# 材质映射
material_mapping = {
    1: "PLA", 2: "PLA Matte", 3: "PLA Metal", 4: "PLA Silk", 5: "PLA-CF", 6: "PLA-Wood",
    7: "RESERVED", 8: "RESERVED", 9: "RESERVED", 10: "RESERVED", 11: "ABS", 12: "ABS-GF",
    13: "ABS-Metal", 14: "RESERVED", 15: "RESERVED", 16: "RESERVED", 17: "RESERVED", 18: "ASA",
    19: "ASA-AERO", 20: "RESERVED", 21: "RESERVED", 22: "RESERVED", 23: "RESERVED", 24: "PA",
    25: "PA-CF", 26: "RESERVED", 27: "RESERVED", 28: "RESERVED", 29: "RESERVED", 30: "PAHT-CF",
    31: "PAHT-GF", 32: "RESERVED", 33: "RESERVED", 34: "PC/ABS-FR", 35: "RESERVED", 36: "RESERVED",
    37: "PET-CF", 38: "PET-GF", 39: "RESERVED", 40: "RESERVED", 41: "PETG", 42: "RESERVED",
    43: "RESERVED", 44: "PPS-CF", 45: "RESERVED", 46: "RESERVED", 47: "PVA", 48: "RESERVED",
    49: "RESERVED", 50: "TPU"
}

# 颜色映射
color_mapping = {
    1: "#FAFAFA", 2: "#060606", 3: "#D9E3ED", 4: "#5CF30F", 5: "#63E492", 6: "#2850FF",
    7: "#FE98FE", 8: "#DFD628", 9: "#228332", 10: "#99DEFF", 11: "#1714B0", 12: "#CEC0FE",
    13: "#CADE4B", 14: "#1353AB", 15: "#5EA9FD", 16: "#A878FF", 17: "#FE717A", 18: "#FF362D",
    19: "#E2DFCD", 20: "#898F9B", 21: "#6E3812", 22: "#CAC59F", 23: "#F28636", 24: "#B87F2B"
}

# 检查编号是否在有效范围内
def is_valid_id(mapping, id):
    return id in mapping

# 根据编号获取材质
def get_material_by_id(material_id):
    if not is_valid_id(material_mapping, material_id):
        return "Invalid material ID"
    return material_mapping[material_id]

# 根据编号获取颜色值
def get_color_by_id(color_id):
    if not is_valid_id(color_mapping, color_id):
        return "Invalid color ID"
    return color_mapping[color_id]

class RFIDHelper:
    def __init__(self, config):
        self.name = config.get_name().split()[-1]
        self.printer = config.get_printer()
        self.spi = bus.MCU_SPI_from_config(config, 0, default_speed=5000000)
        self.mcu = self.spi.get_mcu()
        self.oid = self.mcu.create_oid()

        self.fm17550_read_card_raw = None

        self.fm17550_read_card = None

        self.mcu.add_config_cmd("query_fm17550 oid=%d rest_ticks=0" % (self.oid), on_restart=True)
        self.mcu.add_config_cmd("config_fm17550 oid=%d spi_oid=%d" % (self.oid, self.spi.get_oid()))
        self.mcu.register_config_callback(self._build_config)

        self.gcode = gcode = self.printer.lookup_object('gcode')
        gcode.register_mux_command('RFID_READ', "SLOT", 
                                    self.name, self.cmd_READ_CARD)

    def _build_config(self):
        cmdqueue = self.spi.get_command_queue()
        self.fm17550_read_card = self.mcu.lookup_query_command(
            "fm17550_read_card_cb oid=%c",
            "fm17550_read_card_return oid=%c status=%c data=%*s",
            oid=self.oid, cq=cmdqueue
        )

    def read_card(self):
        params = self.fm17550_read_card.send([self.oid])
        self.fm17550_read_card_raw = params
        return params

    def cmd_READ_CARD(self, gcmd):
        params = self.read_card()

        if params['status'] == 2 or params['status'] == 0:
            raise self.printer.command_error("Cannot read card info!\n")


        data = params['data']
        if len(data) < 16:
            raise self.printer.command_error("The card info data is error!\n")

        self.gcode.respond_raw("%s" % (params, ))

        # 材质：
        material_str = get_material_by_id(data[0])
        # 颜色：
        color = get_color_by_id(data[1])
        # 厂商：
        manufacturer = data[2]
       

        self.gcode.respond_raw(f"Manufacturer: {manufacturer}")
        self.gcode.respond_raw(f"Color: {color}")
        self.gcode.respond_raw(f"Material string: {material_str}")


        

class FeedSlotHelper:
    def __init__(self, config, stepper=None):
        self.name = config.get_name().split()[-1]
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')

        self.slot_stepper = stepper

        self.rfid_reader = RFIDHelper(config)

        # speed accel
        self.velocity = config.getfloat('velocity', 5., above=0.)
        self.accel = config.getfloat('accel', 0., minval=0.)

        # Internal state
        self.min_event_systime = self.reactor.NEVER
        self._slot_present = None
        # self._slot_enabled = True

        self.state = 'EMPTY'

        self.info_manufacturer = 0

        self.info_color = None
        self.info_material = None
        self.info_temp = None

        self.read_json_file('/home/mks/' + self.name)

        self.gcode.respond_info(f"Init slot state: {self.state}")

    def _handle_ready(self):
        self.min_event_systime = self.reactor.monotonic() + 2.

    def _note_slot_present(self, is_slot_present):

        color_feeder = self.printer.lookup_object("color_feeder")
        _is_feeding = color_feeder._is_feeding

        logging.info(f"_is_feeding ====== {_is_feeding}")

        if color_feeder._is_feeding is True:
            return

        
        toolhead = self.printer.lookup_object('toolhead')
        if is_slot_present == self._slot_present or self._slot_present == None:
            return
        self._slot_present = is_slot_present
        eventtime = self.reactor.monotonic()

        idle_timeout = self.printer.lookup_object("idle_timeout")
        is_printing = idle_timeout.get_status(eventtime)["state"] == "Printing"


        

        # 在这里做一下打印头是否有耗材

        # 正在打印，需要退出
        # if eventtime < self.min_event_systime or is_printing:
        #     return

        if is_slot_present:

            color_feeder._is_feeding = True

            script = "ECHELON_SP STEPPER=" + self.name + "\nECHELON_STEPPER STEPPER=" + self.name + " MOVE=4\n"
            self.gcode.run_script(script)
            params = self.rfid_reader.read_card()

            previous_data = None
            max_attempts = 100
            attempts = 0

            while attempts < max_attempts:

                attempts += 1
                params = self.rfid_reader.read_card()

                if not params or params['status'] == 0 or not params['data']:
                    # 如果无效数据，运行脚本并等待
                    toolhead.dwell(0.5)
                    script = f"ECHELON_SP STEPPER={self.name}\nECHELON_STEPPER STEPPER={self.name} MOVE=4\n"
                    self.gcode.run_script(script)
                    toolhead.dwell(3)
                    continue

                # 处理有效数据
                try:
                    data_bytes = params['data']
                    # data_str = data_bytes[1:].decode('utf-8').rstrip('\x00')
                    # data_dict = json.loads(data_str)
                    # logging.info(f"Decoded dictionary: {data_dict}")
                except json.JSONDecodeError as e:
                    logging.info(f"Failed to decode JSON: {e}")
                    continue

                # 比较数据
                if previous_data is None:
                    previous_data = data_bytes
                    # previous_data = data_dict  # 记录第一次读取数据
                    logging.info("First read, saving data.")
                elif previous_data == data_bytes:
                # elif previous_data == data_dict:
                    logging.info("Data matches the previous read, exiting loop.")
                    # self.info_material = data_dict['mtl']
                    # self.gcode.respond_raw(f"{self.info_material}")
                    self.gcode.respond_raw(f"{data_bytes}")

                    # 材质：
                    self.info_material = get_material_by_id(data_bytes[0])
                    # 颜色：
                    self.info_color = get_color_by_id(data_bytes[1])
                    # 厂商：
                    self.info_manufacturer = data_bytes[2]

                    self.gcode.respond_raw(f"Manufacturer: {self.info_manufacturer}")
                    self.gcode.respond_raw(f"Color: {self.info_color}")
                    #self.gcode.respond_raw(f"Temp: {self.info_temp}")
                    self.gcode.respond_raw(f"Material string: {self.info_material}")

                    self.write_json_file('/home/mks/' + self.name, self.info_color, self.info_material)
                    break
                else:
                    logging.info("Data does not match the previous read, continuing.")
                    # previous_data = data_dict
            else:
                logging.info("Reached maximum attempts without valid matching data, exiting loop.")


            '''
            while True:
                params = self.rfid_reader.read_card()
                if params is not None:
                    if params['status'] != 0:
                        if params['data'] is not None and params['data'] != 0:
                            logging.info(f"{params}")
                            data_bytes = params['data']
                            data_str = data_bytes[1:].decode('utf-8').rstrip('\x00')
                            try:
                                data_dict = json.loads(data_str)
                                logging.info("Decoded dictionary:", data_dict)
                                self.info_material = data_dict['mtl']
                                self.gcode.respond_raw("%s" % self.info_material)
                            except json.JSONDecodeError as e:
                                logging.info("Failed to decode JSON:", e)
                            break
                        else:
                            toolhead.dwell(.5)
                            script = "ECHELON_SP STEPPER=" + self.name + "\nECHELON_STEPPER STEPPER=" + self.name + " MOVE=4\n"
                            self.gcode.run_script(script)
                            toolhead.dwell(3)
                    else:
                        toolhead.dwell(.5)
                        script = "ECHELON_SP STEPPER=" + self.name + "\nECHELON_STEPPER STEPPER=" + self.name + " MOVE=4\n"
                        self.gcode.run_script(script)
                        toolhead.dwell(3)
                '''
            toolhead.dwell(1.5)
            
            self.gcode.respond_info(f"Slot state: {self.state}")
            self.min_event_systime = self.reactor.NEVER
            logging.info(f"{self.name} detected, Time {eventtime}")
            # self.slot_stepper.do_set_position(0.)
            # self.slot_stepper.do_move(40)
            script = "ECHELON_SP STEPPER=" + self.name + "\nECHELON_STEPPER STEPPER=" + self.name + " MOVE=20\nG4 P1000\n\
                        ECHELON_STEPPER_HOMING STEPPER=" + self.name + " MOVE=500"  
            self.gcode.run_script(script)
            self.state = "Loaded"
            self.gcode.respond_info(f"Slot state: {self.state}")

            color_feeder._is_feeding = False
        else:
            self.state = "EMPTY"
            self.gcode.respond_info(f"Slot state: {self.state}")

    # def _read_card(self):
    #     params = self.slot_rfidreader.read_card()
    #     self.gcode.respond_raw("%s" % params)
    #     logging.info(f"{params}")

    def read_json_file(self, file_path):
        if not os.path.exists(file_path):
            return
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                return
        self.info_color = data.get("color", None)
        self.info_material = data.get("material", None)
        self.info_temp = data.get("temperature", None)
        # result = {
        #     "color": data.get("color", None),
        #     "material": data.get("material", None),
        #     "temperature": data.get("temperature", None)
        # }

        # return result

    def write_json_file(self, file_path, color=None, material=None):
        new_data = {
            "color": color,
            "material": material
        }
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}
        else:
            existing_data = {}
        for key, value in new_data.items():
            if value is not None:  # Only update keys with non-None values
                existing_data[key] = value
        
        with open(file_path, 'w') as file:
            json.dump(existing_data, file, indent=4)
            print(f"Data successfully written to '{file_path}'.")

    def get_status(self, eventtime):
        # if self.slot_stepper._query_endstop() == True:
        #     self.state = "Busy"
        # else:
        #     if self._slot_present == False:
        #         self.state = "EMPTY"
        return {
            "slot_name": self.name,
            "slot_detected": bool(self._slot_present),
            "slot_state": self.state,
            # "last_state": self.slot_stepper.get_status
            "slot_color": self.info_color,
            "slot_material": self.info_material,
        }


class FeedSlot:
    def __init__(self, config):
        self.printer = printer = config.get_printer()

        self.name = config.get_name().split()[-1]

        reactor = printer.get_reactor()

        self.slot_stepper = echelon_stepper.EchelonStepper(config)
        
        self.buttons = buttons = printer.load_object(config, 'buttons')
        switch_pin = config.get('switch_pin')
        mask = buttons.register_buttons_ret([switch_pin], self._button_handler)
        self.slot_helper = FeedSlotHelper(config, self.slot_stepper)

        self.printer.register_event_handler("klippy:ready", self._handle_ready)

        ppins = self.printer.lookup_object('pins')
        self.chip_name = self._get_pin_chip_name(switch_pin)
        self.mcu = ppins.chips[self.chip_name]

        self.shift = self.find_bit_position(mask) - 1

        logging.info(f"{self.find_bit_position(mask)}\n {self.name}\033[0m")

        self.get_status = self.slot_helper.get_status

    def _handle_ready(self):
        # logging.info(f"\033[93m  {self.name} {type(self.buttons.mcu_buttons)}\n{(self.buttons.mcu_buttons['mcu'])} \033[0m")
        if hasattr(self.buttons.mcu_buttons[self.chip_name], 'oid'):
            oid = self.buttons.mcu_buttons[self.chip_name].oid
            cmdqueue = self.mcu.alloc_command_queue()
            buttons_read_cmd = self.mcu.lookup_query_command(
                "buttons_read oid=%c pos=%u",
                "buttons_read_state oid=%c state=%u",
                oid=oid, cq=cmdqueue
            )
            params = buttons_read_cmd.send([oid, self.shift])
            logging.info(f"\033[93m  {(params['state'])} \033[0m")
            if params['state'] == 1:
                self.slot_helper._slot_present = False
            else:
                self.slot_helper._slot_present = True

    def _button_handler(self, eventtime, state):
        logging.info(f"eventtime = {eventtime}, state = {state}")
        self.slot_helper._note_slot_present(state)

    def _get_pin_chip_name(self, pin_desc, can_invert=True, can_pullup=True):
        desc = pin_desc.strip()
        pullup = invert = 0
        if can_pullup and (desc.startswith('^') or desc.startswith('~')):
            pullup = 1
            if desc.startswith('~'):
                pullup = -1
            desc = desc[1:].strip()
        if can_invert and desc.startswith('!'):
            invert = 1
            desc = desc[1:].strip()
        if ':' not in desc:
            chip_name, pin = 'mcu', desc
        else:
            chip_name, pin = [s.strip() for s in desc.split(':', 1)]
        return chip_name

    def find_bit_position(self, n):
        return n.bit_length()

def load_config_prefix(config):
    return FeedSlot(config)