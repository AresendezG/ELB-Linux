#from log_management import LOG_Manager
#from program_manager import ProgramControl
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
    #Main = ProgramControl(arguments)
    #result = Main.run_program()
    #print(f"Execution Result: {result}")
else:
    try:
        tcp_srv = tcp_launcher(arguments[1], arguments[2])
        tcp_srv.launch_tcp()
    except KeyboardInterrupt:
        print("Finishing Execution due to detected interrupt")



#'''
