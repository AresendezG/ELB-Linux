import os
import json
import time
from log_management import LOG_Manager, MessageType
from Sequencer import SeqConfig
from firmware import ELBFirmware
from i2c_comm import ELB_i2c
from results_processing import ResultsManager
from i2c_types import MOD_Rates
from gpio_ctrl import GPIO_CONTROL

# This class will define how the program flows

class ProgramControl:  
    
    # Dummy SN to prevent Emtpy SNs 
    sn = "JNPRSN0102"
    # Read from the config file
    seq_file = ""
    limits_file = ""
    # Execution time between sequences, default 1, modified by settings file
    time_between_seq = 1
    test_settings = None
    # Object to handle the log to files
    log_mgr = None
    # Object to handle the i2c communication with UUT
    i2c_comm = None

    # Define the stuff that needs to happen for this object runs 
    def __init__(self, args) -> None:
        print("Message: \tInit Test Program")
        self.input_args = args
        self.__ValidateArgs()
        self.__StartLog()
        # Read flow config needs to happen first to create the flow template
        self.__Read_FlowConfig()
        # Launch the results processing object with a reference to the log_mgr object and the path for limits file
        self.results_mgr = ResultsManager(log_handler=self.log_mgr, limits_file=self.limits_file)
        # Include the Serial number as new test limits to the result-manager object
        self.results_mgr.include_sn_limits(uut_serial=self.sn, uut_pn=self.partnum, uut_rev=self.rev)
        # Launch the GPIO controller
        self.gpioctrl = GPIO_CONTROL(self.log_mgr)
        pass
    
    def __StartLog(self) -> None:
        try:
            # Start Logfile handler. This is also the console rich handler.
            self.log_mgr = LOG_Manager(self.log_path)
            if (self.log_mgr.create_log_files(self.sn)):
                return
            else:
                print("Stopping since the Logfiles could not be created!")
                raise RuntimeError
        except:
            print("ERROR: \tUnable to Start the Logfiles. Verify settings")
            # We dont want executions with empty lofgiles. Stop Here.
            raise RuntimeError    

    def __ValidateArgs(self):
        
        if (len(self.input_args) < 5):
            print("ERROR:\tWrong Parameter Settings")
            print("Message:\tVerify the arguments of Limits File and Config File")
            raise FileExistsError
        else:
            # Define all of the input parameters
            self.sn = self.input_args[0]
            self.rev = self.input_args[1]
            self.partnum = self.input_args[2]
            self.limits_file = self.input_args[3]
            self.settings_file = self.input_args[4]
            # Read the settings from the Settings.JSON file
            self.__Read_Settings()
        return
    
    # Reading the test settings from the settings.json file
    def __Read_Settings(self):
        if (os.path.isfile(self.settings_file)):
            with open(self.settings_file, 'r') as f:
                self.settings = json.load(f)
            # Define Mod rate for PRBS
            self.prbs_modrate = getattr(MOD_Rates, self.settings['modrate'])
            # Define i2c address of the UUT
            self.i2c_address = self.settings['i2c_default_add']
        else:
            print("ERROR:\tConfiguration File does not exist")
            raise FileNotFoundError
        try: 
            # Read settings from the config file
            self.log_path = self.settings['log_path']
            self.time_between_seq = self.settings['seq_sync_time']

        except:
            print("ERROR:\tWrong Configuration settings")
            raise FileExistsError
    
    # Reading the flow-control from a json file with the sequence and test limits
    def __Read_FlowConfig(self):
        SeqHandler = SeqConfig()
        try:
            # Testflow will include SN prog and FW upgrade as theyre defined in the template
            self.test_flow = SeqHandler.ReadSeq_Settings_JSON(self.limits_file)
            self.test_count = SeqHandler.test_count
        except:
            self.log_mgr.print_message(f"Unable to read Sequence JSON File {self.limits_file}. Stopping Execution", MessageType.FAIL, True)
            raise RuntimeError
    
    def __RunTest(self, test_fnc:object, retries:int, test_name:str) -> bool:
        
        for i in range(retries):
            results = test_fnc()
            processed_results = self.results_mgr.ProcessResults(test_name, results)
            # If result of the sequence is pass, then log and exit
            if (processed_results[0]):
                self.log_mgr.log_sequence_results(processed_results[1])
                # This sequence passed, thus returing to program
                return True
            if (i < retries-1):
                self.log_mgr.print_message(f"Failed {test_name}. Retry: {i+1}", MessageType.WARNING) 
            # If not, still log the results at the last attempt
            else:
                self.log_mgr.print_message(f"Failed {test_name}. No More Retries", MessageType.FAIL) 
                self.log_mgr.log_sequence_results(processed_results[1])
        # Sequence ran out of retries, returning false
        return False
    
    def run_program(self) -> bool:
        # Run Detection check
        self.log_mgr.log_to_file("Event:\tRunning Detection")
        uut_detection = self.gpioctrl.detect_uut(180)
        overall_result = True
        if uut_detection:
            self.log_mgr.log_to_file("UUT Detected. Running FW Upgrade")
            # Firmware Upgrade and SN Programming will execute first
            #self.__FirmwareUpgrade()
            # Firmware Upgrade completed or Not required, launch i2c Communication
            self.i2c_comm = ELB_i2c(self.prbs_modrate, self.i2c_address, self.gpioctrl, self.log_mgr, self.settings)
            self.i2c_comm.define_uut_sn([self.sn, self.partnum, self.rev])
            #self.__Program_UUT_SN()   
            # For each test in the TestFlow 
            for test in self.test_flow:
                # Read the testname from the xml config
                test_name = test['test_name']
                retries = int(test['retries'])
                flow_ctrl = test['flow']
                # get a reference of the test to be run    
                try:
                    test_fnc_ref = getattr(self.i2c_comm, test_name)
                    seqresult = self.__RunTest(test_fnc_ref, retries, test_name)
                    # If sequence failed, and seqconfig is not configd to continue, stop execution
                    if (not seqresult and not flow_ctrl):
                        self.log_mgr.print_message(f"FAILURE at {test_name}. Stopping Execution", MessageType.FAIL)
                        self.i2c_comm.uut_cleanup()
                        return False
                    time.sleep(self.time_between_seq) 
                except AttributeError:
                    #print("ERROR:\t Unable to find Test: {}".format(test_name))
                    self.log_mgr.print_message("Test {} Not Found".format(test_name), MessageType.WARNING, True)
            self.log_mgr.print_message("All Tests Completed", MessageType.EVENT, True)
            self.i2c_comm.uut_cleanup()
            self.gpioctrl.config_pins_todefault()
            self.log_mgr.close_logs()
            return seqresult
        else:
            self.log_mgr.print_message("User did not inserted the ELB. No test were executed", MessageType.WARNING, True)
        return

    