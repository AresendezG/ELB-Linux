import os
import json
from log_management import LOG_Manager, MessageType
from debug_libs.dummy_i2c_comm import ELB_i2c
from i2c_types import MOD_Rates
from debug_libs.dummy_gpio import GPIO_CONTROL

# This class will define how the program flows

class ProgramControl:  
    
    # Object to handle the log to files
    log_mgr = None
    # Object to handle the i2c communication with UUT
    i2ctests = None
    test_started = False

    def __init__(self) -> None:
        pass
    
    def __StartLog(self, serial:str) -> None:
        try:
            # Start Logfile handler. This is also the console rich handler.
            self.log_mgr = LOG_Manager(self.log_path)
            self.log_mgr.create_log_files(serial)
        except:
            print("ERROR:\tUnable to Start the Logfiles. Verify settings")
            # We dont want executions with empty lofgiles. Stop Here.
            raise RuntimeError    

    def __ValidateArgs(self):
        # Define all of the input parameters
        self.sn = self.input_args['serial']
        self.rev = self.input_args['rev']
        self.partnum = self.input_args['partnum']
        self.config_file = self.input_args['config']

        # Validate SN, Rev, Partnum
        self.__validate_param(self.sn, "Serial", 5)
        self.__validate_param(self.rev,"Revision", 1)
        self.__validate_param(self.partnum, "Part Number", 5)

        # Read the settings from the Json file
        self.__Read_Settings()
        return
    
    def __validate_param(self, param:str, para_name:str, min_len:int) -> bool:
        if (len(param) > min_len):
            return True
        else:
            print(f"Invalid Lenght of Parameter {para_name}")
            raise KeyError

    # Reading the test settings from the settings.json file
    def __Read_Settings(self):
        if (os.path.isfile(self.config_file)):
            with open(self.config_file, 'r') as f:
                settings = json.load(f)
            # Define Mod rate for PRBS
            self.prbs_modrate = getattr(MOD_Rates, settings['modrate'])
            # Define i2c address of the UUT
            self.i2c_address = settings['i2c_default_add']
        else:
            print("ERROR:\tConfiguration File does not exist")
            raise FileNotFoundError
        try: 
            # Read settings from the config file
            self.log_path = settings['log_path']
            self.time_between_seq = settings['seq_sync_time']
        except:
            print("ERROR:\tWrong Configuration settings")
            raise FileExistsError
    

    def start_test(self, in_settings:str) -> bool:
        try:
            if (not self.test_started):
                cmd_settings = in_settings.strip('\n')
                self.input_args = json.loads(cmd_settings)
                self.__ValidateArgs()
                self.__StartLog(self.sn)
                # Launch the GPIO controller
                self.gpioctrl = GPIO_CONTROL(self.log_mgr)
                # Launch the i2c test group:
                self.i2ctests = ELB_i2c(self.prbs_modrate, self.i2c_address, self.gpioctrl, self.log_mgr, self.config_file)
                self.test_started = True
                return True
            else:
                return False
        except KeyError:
            print("ERROR:\tInvalid Settings")
            return False
        except:
            return False

    def run_test(self, details:str) -> str:
        try:
            test_details = json.loads(details)
            test_name = test_details['testname']
            test_fnc_ref = getattr(self.i2ctests, test_name)
            results = test_fnc_ref()
            ret_json = json.dumps(results)
            return ret_json
        except KeyError:
            return "ERROR-TEST-INVALID"
        except TypeError:
            return "ERROR-NOT-VALID-TEST"
        except:
            return "ERROR-UNKNOWN"

    def end_test(self, details:str) -> str:
        # Cleanup 
        self.i2ctests.uut_cleanup()
        self.log_mgr.close_logs()
        self.test_started = False
        return "CLEANUP_DONE"