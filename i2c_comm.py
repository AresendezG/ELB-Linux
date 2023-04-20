import asyncio
import time
from i2c_types import LedMode, TempSensors, VoltageSensors, VoltReadings
from smbus2 import SMBus


class ELB_i2c:
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
        fwver = retdata  
        return [dsp_ver, dsp_id, dsp_rev, fwver]

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
    def __ReadTempFnc(self, regaddress: int) -> float:
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, regaddress, 2)
        retdata = [x for x in retdata]
        temp = ((retdata[0]<<8) + retdata[1])/256 #calculate temp value from sensor 
        return temp
    
    # Function to read voltages
    def __ReadVoltageFnc(self, regaddress: int) -> float:
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, regaddress, 2)
        retdata = [x for x in retdata]
        vcc = ((retdata[0]<<8) + retdata[1])*0.0001 # calculate voltage from the sensor
        return vcc
    
    def __ReadEPPS_Data(self, regaddress: int, data_size: int) -> int:
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, regaddress, data_size)
        retdata = [x for x in retdata]
        val = 0
        for x in retdata:
            val = (val<<8) + x
        return val

    # ------ Sequences ---------------
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

    def Get_AllVoltages(self) -> list:
        vcc = self.__ReadVoltageFnc(VoltageSensors.VCC)
        print("Reading VCC Voltage: {:.4f}".format(vcc))
        vcctx = self.__ReadVoltageFnc(VoltageSensors.VCCTX)
        print("Reading VCC_TX Voltage: {:.4f}".format(vcctx))
        vccrx = self.__ReadVoltageFnc(VoltageSensors.VCCRX)
        print("Reading VCC_RX Voltage: {:.4f}".format(vccrx))
        vbatt = self.__ReadVoltageFnc(VoltageSensors.VBATT)
        print("Reading VBATT Voltage: {:.4f}".format(vbatt))
        return [vcc, vcctx, vccrx, vbatt]

    def Get_AllTemps(self) -> list:
        uc_temp = self.__ReadTempFnc(TempSensors.UC)
        print("Temp Sensor uC: {:.4f}".format(uc_temp))
        rt_temp = self.__ReadTempFnc(TempSensors.RTMR)
        print("Temp Sensor RTMR: {:.4f}".format(rt_temp))
        pcb_rt_temp = self.__ReadTempFnc(TempSensors.PCB_RT)
        print("Temp Sensor RTMR PCB {:.4f}".format(pcb_rt_temp))
        pcb_pl_temp = self.__ReadTempFnc(TempSensors.PCB_PL)
        print("Temp Sensor PowerLoad PCB {:.4f}".format(pcb_pl_temp))
        shell_f_temp = self.__ReadTempFnc(TempSensors.SHELL_F)
        print("Temp Shell F {:.4f}".format(shell_f_temp))       
        shell_r_temp = self.__ReadTempFnc(TempSensors.SHELL_R)
        print("Temp Shell F {:.4f}".format(shell_r_temp))
        return [uc_temp, rt_temp, pcb_rt_temp, pcb_pl_temp, shell_f_temp, shell_r_temp]  
    

    def Get_Alll_EPPSData(self) -> list:
        # write page 3
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])
        # ePPS Start capture:
        self.bus.write_i2c_block_data(self.DEV_ADD, 164, [0x01])
        self.timesleep(5)
        retdata=[0]
        while retdata[0] == 0:
            retdata = self.bus.read_i2c_block_data(self.DEV_ADD,156,1)
            retdata = [x for x in retdata]
        # Get ePPS results
        freq = self.__ReadEPPS_Data(157, 4)
        duty_percent = self.__ReadEPPS_Data(161, 1)
        duty_ms = self.__ReadEPPS_Data(162, 2)
        return [freq, duty_percent, duty_ms]


    def main(self):
        print("Getting the FWversion:")
        [dsp_ver, dsp_id, dsp_rev] = self.__checfw_ver()
        print("DSP Version: ",dsp_ver)
        print("DSP ID: ", dsp_id)
        print("Getting UUT's SN: ")
        [serial_number, part_number, revision, fwver] = self.__get_uut_sn()
        print("Serial Number: ",serial_number)
        print("Part Number: ",part_number)
        print("Revision: ",revision)
        print("Firmware version {}.{}".format(fwver[0], fwver[1]))
        self.Get_AllVoltages()        
        print("LEDs Routine")
        self.led_sequence()
        # bus = SMBus()



