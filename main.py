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

    print("Calling Current Test")
    current_results = i2c_comm.CurrentSequence()
else:
    print("ERROR: Unable to create logfiles. Test stopped")
