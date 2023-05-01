import sys
from log_management import LOG_Manager
from program_manager import ProgramControl
from debug import i2c_PicoInterface

Main = ProgramControl(sys.argv)
Main.run_program()

'''
print("Debug i2c communication with Pico")
pico_debug = i2c_PicoInterface()
# Validate firmware and retimer
pico_debug.validate_firmware()
pico_debug.read_fw_ver()
pico_debug.read_sn()
pico_debug.read_partnum()
pico_debug.write_new_sn("RPICO1234")
pico_debug.read_sn()
'''