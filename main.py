import sys
from log_management import LOG_Manager
from program_manager import ProgramControl
from debug import i2c_PicoInterface

#Main = ProgramControl(sys.argv)
#Main.run_program()

print("Debug i2c communication with Pico")
pico_debug = i2c_PicoInterface()
pico_debug.read_fw_ver()
pico_debug.read_sn()
