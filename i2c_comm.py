import asyncio
import time
from smbus2 import SMBus
from i2c_types import LedMode

class ELB_Linux:
    #-- Class variables definitions
    #define i2c BUS to be used
    DEVICE_BUS = 1
    DEV_ADD = 0x50
    #define bus object
    bus = None

    #function declaration

    def __init__(self) -> None:
        print("Init SMBus")
        self.bus = SMBus(self.DEVICE_BUS)
        print("i2c Bus started at address: {}",self.DEV_ADD)
        pass

    def __checfw_ver(self) -> list:
        # Write Page 3
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])        
        # Retrieve data from registers
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 182, 4)
        retdata = [x for x in retdata]
        dsp_ver = ((retdata[0]<<24) + (retdata[1]<<16) + (retdata[2]<<8) + retdata[3])
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 186, 4)
        retdata = [x for x in retdata]
        dsp_id = ((retdata[0]<<24) + (retdata[1]<<16) + (retdata[2]<<8) + retdata[3])
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 190, 1)
        retdata = [x for x in retdata]
        dsp_rev = retdata[0]
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 39, 2)  
        return [dsp_ver, dsp_id, dsp_rev]

    def __get_uut_sn(self) -> list:
        # write page 0
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0])
        # read SN from reg166  
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 166, 16)
        serial_array = [x for x in retdata] #array that holds the serialnumber
        serial_str = "".join(chr(x) for x in serial_array)
        # read PN from reg148
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 148, 16)
        pn_array = [x for x in retdata] #array that holds the part number
        part_number = "".join(chr(x) for x in pn_array)
        # read revision from reg164
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 164, 2)
        revision = [x for x in retdata] # array that holds the rev number
        return [serial_str, part_number, revision]
    
    # Function to test the temperature 
    def ReadTempFnc(self, regaddress: int) -> float:
         #Can be refactored too
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, regaddress, 2)
        retdata = [x for x in retdata]
        temp = ((retdata[0]<<8) + retdata[1])/256 #temp ADC is most likely 256 levels? 
        return temp
    
    # Function to read voltages
    def ReadVoltageFnc(self, regaddress: int) -> float:
        #Read a voltage level and log to the test results file
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, regaddress, 2)
        retdata = [x for x in retdata]
        # Get the voltage level from the given registry
        vcc = ((retdata[0]<<8) + retdata[1])*0.0001
        return vcc


    async def led_sequence(self):
        # write page 3
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])
        # flash LEDs
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.BOTH_FLASH)
        await asyncio.sleep(5)
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.GREEN_ON)
        await asyncio.sleep(5)
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.RED_ON)
        await asyncio.sleep(5)
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.LED_OFF)

    def VoltageSequence(self):
        print("VCC Voltage: ")
        vcc = self.ReadVoltageFnc(168)
        print(vcc)
        print("VBATT Voltage")
        vbatt = self.ReadVoltageFnc(180)
        print(vbatt)        


    def main(self):
        print("Getting the FWversion:")
        [dsp_ver, dsp_id, dsp_rev] = self.__checfw_ver()
        print("DSP Version: ",dsp_ver)
        print("DSP ID: ", dsp_id)
        print("Getting UUT's SN: ")
        [serial_number, part_number, revision] = self.__get_uut_sn()
        print("Serial Number: ",serial_number)
        print("Part Number: ",part_number)
        print("Revision: ",revision)
        self.VoltageSequence()        
        print("LEDs Routine")
        self.led_sequence()
        # bus = SMBus()



