
import sys 
import xml
from Sequencer import SeqConfig
import sys
import time
#from i2c_comm import ELB_i2c
#from i2c_types import MOD_Rates
from log_management import LOG_Manager


class DummyClass:
    def __init__(self) -> None:
        print("Event:\tCreating a dummy class! jejeje")
        pass

    def temp_sensors(self) -> list:
        print("Test:\tExecuting TempSensors Test")
        return [1, 2, 3, 4]
    
    def ins_count(self) -> list:
        print("Executing ins Count Test")
        return [0, 10]

    def power_loads(self) -> list:
        print("Test:\tExecuting PowerLoad Test")
        return [0.2, 0.3, 0.5]
    

class i2c_PicoInterface:

    def __init__(self) -> None:
        from smbus2 import SMBus
        self.pico_address = 0x17
        self.RPI_BUS = 1
        self.i2cbus = SMBus(self.RPI_BUS)
        print("Opening Comm with RPI Pico at {}".format(self.pico_address))


    def read_sn(self) -> str:
        print("Event:\tTrying to read Pico SN")
        self.i2cbus.write_i2c_block_data(self.pico_address, 127, [3])
        print("check for cmd ack status...")
        time.sleep(5)
        data = self.i2cbus.read_i2c_block_data(self.pico_address, 166, 8)
        serial_array = [x for x in data] #array that holds the serialnumber
        serial_str = "".join(chr(x) for x in serial_array)
        print("Serial: {}".format(serial_str))
        return serial_str
    
    def read_fw_ver(self) -> str:
        print("Event:\tTrying to read Pico FW Version")
        self.i2cbus.write_i2c_block_data(self.pico_address, 127, [3])
        print("check for cmd ack status...")
        time.sleep(5)
        data = self.i2cbus.read_i2c_block_data(self.pico_address, 39, 2)
        fwver = "{}.{}".format(data[0], data[1])
        print("FW Version: {}".format(fwver))
        return fwver

