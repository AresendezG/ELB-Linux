import os
import json
from log_management import LOG_Manager, MessageType
from i2c_comm import ELB_i2c
from i2c_types import MOD_Rates
from gpio_ctrl import GPIO_CONTROL
from results_processing import ResultsManager
# This class will define how the program flows

class ProgramControl:  
    
    # Object to handle the log to files
    log_mgr = None
    # Object to handle the i2c communication with UUT
    i2ctests = None
    test_started = False
    # Variable to check the status of the test result
    seq_result = False

    def __init__(self) -> None:
        pass
    
    def __del__(self):
        try:
            self.end_test()
        except:
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
        # Input parameters coming from the test client
        self.sn = self.input_args['serial']
        self.rev = self.input_args['rev']
        self.partnum = self.input_args['partnum']
        self.configs = self.input_args['config'] # JSON Object with configuration values
        self.limits_filename = self.input_args['limits'] # File path of the "limits file"

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

    # Reading the test settings from the configs JSON object sent by Client
    def __Read_Settings(self):
        try: 
            # Define Mod rate for PRBS
            self.prbs_modrate = getattr(MOD_Rates, self.configs['modrate'])
            # Define i2c address of the UUT
            self.i2c_address = self.configs['i2c_default_add']
            # Read settings from the config file
            self.log_path = self.configs['log_path']
            # Wait time between executing sequences 
            self.time_between_seq = self.configs['seq_sync_time']
            # Get the script file path
            self.limits_filepath = self.configs['scripts_path'] + self.limits_filename
        except:
            print("ERROR:\tWrong Configuration settings")
            raise FileExistsError
        

    def start_test(self, in_settings:str) -> str:
        try:
            if (not self.test_started):
                cmd_settings = in_settings.strip('\n')
                self.input_args = json.loads(cmd_settings)
                self.__ValidateArgs()
                # Creates the Logmanager Object to log the results
                self.__StartLog(self.sn)
                # Launch the result processing object, requires the Limits File path sent by the Client
                #    self.results_processor = ResultsManager(self.log_mgr, limits_file=self.limits_filepath)
                # Launch the GPIO controller
                self.gpioctrl = GPIO_CONTROL(self.log_mgr)
                # Launch the i2c tests Object:
                self.i2ctests = ELB_i2c(self.prbs_modrate, self.i2c_address, self.gpioctrl, self.log_mgr, self.configs)
                # Update the expected SN,PN and Rev  in the i2ccom object
                self.i2ctests.define_uut_sn([self.sn, self.partnum, self.rev])
                # Dynamically create new limits to include the expected SN
                # self.results_processor.include_sn_limits(self.sn, self.partnum, self.rev)
                # Run UUT detection
                self.test_started = self.gpioctrl.detect_uut_tcp(60)
                return "TEST_START_CORRECT"
            else:
                return "TEST_RUNNING"
        except KeyError:
            print("ERROR:\tInvalid Settings")
            return "INVALID_SETTINGS"
        except:
            return "RUNTIME_ERROR_NOT_CORRECT"


    def run_test(self, details:str) -> str:
        try:
            clean_details = details.strip('\n')
            test_details = json.loads(clean_details)
            # Get settings from the TCP client
            test_name = test_details['testname']
            log_test = bool(test_details['log_test'])
            interactive = test_details['interactive']
            test_fnc_ref = getattr(self.i2ctests, test_name)
            results = test_fnc_ref()
            # Returns the raw results to the TCP Client
            ret_json = json.dumps(results)
            return ret_json
        except KeyError:
            return "ERROR-TEST-INVALID"
        except TypeError:
            return "ERROR-NOT-VALID-TEST"
        except:
            return "ERROR-UNKNOWN"

    def end_test(self) -> str:
        # Cleanup 
        self.i2ctests.uut_cleanup()
        self.log_mgr.close_logs()
        # Delete objects
        del self.log_mgr 
        del self.gpioctrl
        del self.i2ctests
        self.test_started = False
        # seq_result should be true if none of the sequences failed the test
        return str(self.seq_result)