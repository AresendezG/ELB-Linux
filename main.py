from smbus2 import SMBus
from i2c_comm import ELB_i2c
from log_management import LOG_Manager

# Change these variables for user settings
default_path = "~/elb_results/"
uut_serial = "ZP3923110084"

i2c_comm = ELB_i2c()
logs = LOG_Manager(uut_serial, default_path)

# Run the test only if the log can be created!
if (logs):
    print("--- ELB Test Script --- ")
    print("Calling GPIO Test")
    gpio_results = i2c_comm.Test_GPIO_all()
    for rsl in range(gpio_results.count()):
        logs.logtofile("GPIO Result: {}".format(gpio_results[rsl]))

print("Event: Calling GPIO Test")
gpio_results = i2c_comm.Test_GPIO_all()
for rsl in range(len(gpio_results)):
    print("GPIO Result: {}".format(gpio_results[rsl]))


print("Event: Calling Insertion Counter")
[ins_accum, ins_nibb] = i2c_comm.Get_InsertionCount()
print("Accumulate: ",ins_accum)
print("Nibble: ",ins_nibb)

print("Event: Calling Read Voltage Sensors")
volt_results = i2c_comm.Get_AllVoltages()

print("Event: Calling the Temp Sensor reading")
temp_results = i2c_comm.Get_AllTemps()

i2c_comm.Get_UUT_SN()
print("Calling Current Test")
current_results = i2c_comm.CurrentSequence()
print(current_results)



'''
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
'''
