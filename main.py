#from log_management import LOG_Manager
from program_manager import ProgramControl
#from debug import i2c_PicoInterface
from arguments import UserArguments
from tcp_service import tcp_launcher


#'''
# parse user input arguments
arg_validator = UserArguments()
arguments = arg_validator.parse_args()

# Launch program
if (arguments[0] != "TCPMODE"):
    print("Console Mode")
    Main = ProgramControl(arguments)
    result = Main.run_program()
    print(f"Execution Result: {result}")
else:
    try:
        tcp_srv = tcp_launcher(arguments[1], arguments[2])
        # Launch the TCP Server
        tcp_srv.run_tcp(None,  {'port':arguments[1], 'host':arguments[2]})
    except KeyboardInterrupt:
        print("Finishing Execution due to detected interrupt")
    except Exception as e:
        print("Exception Ocurred, details: ")
        print(e.args)
        




#'''
