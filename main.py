import sys
#from log_management import LOG_Manager
from program_manager import ProgramControl
#from debug import i2c_PicoInterface
from arguments import ArgumentsProcess

#'''
# parse user input arguments
arg_validator = ArgumentsProcess()
arguments = arg_validator.parse_args(sys.argv)

# Launch program
Main = ProgramControl(arguments)
result = Main.run_program()
print(f"Execution Result: {result}")
#'''
