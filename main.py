from smbus2 import SMBus
from i2c_comm import ELB_i2c

i2c_comm = ELB_i2c()

print("--- ELB Testing Script --- ")


    def main(self):
        print("Getting the FWversion:")
        [dsp_ver, dsp_id, dsp_rev, fwver] = self.__checfw_ver()
        print("DSP Version: ",dsp_ver)
        print("DSP ID: ", dsp_id)
        print("Getting UUT's SN: ")
        [serial_number, part_number, revision] = self.__get_uut_sn()
        print("Serial Number: ",serial_number)
        print("Part Number: ",part_number)
        print("Revision: ",revision)
        print("Firmware version: {}.{}".format(fwver[0], fwver[1]))
        self.Get_AllVoltages()
        self.Get_AllTemps()
        print("ePPS Data:")
        [freq, duty, dutyms] = self.Get_Alll_EPPSData()
        print("ePPS Frequency: ",freq)
        print("ePPS Duty %",duty)
        print("ePPS Duty ms",dutyms)
        self.Get_Alll_EPPSData()        
        print("LEDs Routine")
        self.led_sequence()
        # bus = SMBus()
