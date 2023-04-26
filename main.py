from smbus2 import SMBus
from i2c_comm import ELB_i2c
from log_management import LOG_Manager

# Change these variables for user settings
default_path = "../test_results/"
uut_serial = "ZP3923110080"
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
    [serial_str, part_number, revision] = i2c_comm.Get_UUT_SN()
    logs.logtofile("UUT SerialNum: {}".format(serial_str))
    logs.logtofile("Part Number: {}".format(part_number))
    logs.logtofile("Revision: {}".format(revision))

    logs.logtofile("Event: Calling Insertion Counter")
    [ins_accum, ins_nibb] = i2c_comm.Get_InsertionCount()
    logs.logtofile("Accumulate: {}".format(ins_accum))
    logs.logtofile("Nibble: {}".format(ins_nibb))  
    
    logs.logtofile("Event: Calling Read Voltage Sensors")
    volt_results = i2c_comm.Get_AllVoltages()
    for rsl in range(len(volt_results)):
        logs.logtofile("Voltage Sensor_{} Result: {}".format(rsl, volt_results[rsl]))

    logs.logtofile("Event: Calling the Temp Sensor reading")
    temp_results = i2c_comm.Get_AllTemps()
    for rsl in range(len(temp_results)):
        logs.logtofile("Temp Sensor_{} Result: {}".format(rsl, temp_results[rsl]))

    logs.logtofile("Event: Calling the EPPS test")
    [freq, duty_percent, duty_ms] = i2c_comm.Get_Alll_EPPSData()
    logs.logtofile("Frequency: {}".format(freq))
    logs.logtofile("Duty percent: {}".format(duty_percent))
    logs.logtofile("Duty in ms: {}".format(duty_ms))
    
    logs.logtofile("Calling Current Test")
    current_results = i2c_comm.CurrentSequence()
    for rsl in range(len(current_results[0])):
        logs.logtofile("VCC Sensor_{} Result: {}".format(rsl, current_results[0][rsl]))
        logs.logtofile("VCC_RX Sensor_{} Result: {}".format(rsl, current_results[1][rsl]))
        logs.logtofile("VCC_TX Sensor_{} Result: {}".format(rsl, current_results[2][rsl]))

except KeyboardInterrupt:
    logs.logtofile("Warning: Test Aborted by User!")

except:
    print("ERROR: Exception ocurred during the Execution of the test")
    #todo: create a file that logs the exception details