from smbus2 import SMBus
from i2c_comm import ELB_i2c
from log_management import LOG_Manager

# Change these variables for user settings
default_path = "../test_results/"
uut_serial = "ZP3923110084"

i2c_comm = ELB_i2c()
try:
    # Run tests only if Logfiles can be created!
    logs = LOG_Manager(uut_serial, default_path)

    logs.logtofile("--- ELB Test Script --- ")

    logs.logtofile("Event: Calling GPIO Test")
    gpio_results = i2c_comm.Test_GPIO_all()
    for rsl in range(len(gpio_results)):
        logs.logtofile("GPIO Result: {}".format(gpio_results[rsl]))

    logs.logtofile("Event: Reading UUT SN")
    i2c_comm

    logs.logtofile("Event: Calling Insertion Counter")
    [ins_accum, ins_nibb] = i2c_comm.Get_InsertionCount()
    logs.logtofile("Accumulate: {}".format(ins_accum))
    logs.logtofile("Nibble: ",ins_nibb)  
    logs.logtofile("Event: Calling Read Voltage Sensors")
    volt_results = i2c_comm.Get_AllVoltages()

    logs.logtofile("Event: Calling the Temp Sensor reading")
    temp_results = i2c_comm.Get_AllTemps()
    i2c_comm.Get_UUT_SN()
    logs.logtofile("Calling Current Test")
    current_results = i2c_comm.CurrentSequence()
    logs.logtofile(current_results)

except:
    print("ERROR: Exception occurred during th handilig")
    #todo: create a file that logs the exception details