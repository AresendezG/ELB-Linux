import sys
from log_management import LOG_Manager
from program_manager import ProgramControl


Main = ProgramControl(sys.argv)
Main.run_program()
