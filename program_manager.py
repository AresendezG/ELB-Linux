import os
import json
from log_management import LOG_Manager
from Sequencer import SeqConfig
from firmware import ELBFirmware
from debug import DummyClass

# This class will define how the program flows

class ProgramControl:  
    
    sn = ""
    seq_file = ""
    limits_file = ""
    test_settings = None
    logger = None
    i2c_comm = None

    # Define the stuff that needs to happen for this prog runs 
    def __init__(self, args) -> None:
        print("Message:\tStart Program Execution")
        self.i2c_comm = DummyClass()
        self.input_args = args
        self.__ValidateArgs()
        self.__StartLog()
        # por hacer:
        # Launch the i2c Comm and the GPIO manager?
        self.__Read_FlowConfig()
        self.__Verify_Firmware()
        #self.test_config = 
        pass
    
    # Cleanup
    def __delete__(self) -> None:
        pass

    def __StartLog(self) -> None:
        try:
            # Start Logfile
            self.logger = LOG_Manager(self.sn, self.log_path)
        except:
            print("ERROR:\tUnable to Start the Logfile. Verify settings")    

    def __ValidateArgs(self):
        
        if (len(self.input_args) < 5):
            print("ERROR:\tWrong Parameter Settings")
            print("Message:\tTo run this program you need 4 parameters")
        else:
                self.sn = self.input_args[1]
                self.seq_file = self.input_args[2]
                self.limits_file = self.input_args[3]
                self.config_file = self.input_args[4]
                self.__Read_Settings()
        return
    

    def __Read_Settings(self):
        if (os.path.isfile(self.config_file)):
            with open(self.config_file, 'r') as f:
                settings = json.load(f)
        else:
            print("ERROR:\tConfiguration File does not exist")
            raise FileNotFoundError
        try: 
            # Read settings from the config file
            self.log_path = settings['log_path']

        except:
            print("ERROR:\tWrong Configuration settings")
            raise FileExistsError

    def __Read_FlowConfig(self):
        try:
            xml_handler = SeqConfig()
            self.test_flow = xml_handler.ReadSeq_Settings(self.seq_file)
            self.test_count = xml_handler.test_count
        except:
            self.logger.logtofile("ERROR:\tUnable to read the sequence XML Config File")

    def __Verify_Firmware(self):
        fwhandler = ELBFirmware(self.config_file)
        # Verify the firmware version and try to upgrade it
        [fw_ver, retimer] = fwhandler.fw_verification()
        self.logger.logtofile("FW Version Before: {}".format(fwhandler.current_fw))
        self.logger.logtofile("FW Version After Upgrade: {}".format(fw_ver))
        self.logger.logtofile("Retimer HostAddress: {}".format(retimer))

    def __RunTest(self, test_fnc:object, retries:int):
        
        for i in range(retries):
            results = test_fnc()
        pass
    
    def run_program(self):
        
        print("Event:\tFirmware Prog & Verify")
                
        print("Event:\tTest Start")
        executed = 0
        # For each test in the TestFlow 
        for test in self.test_flow:
            # Read the testname from the xml config
            test_name = test['test_name']
            retries = int(test['retries'])
            # get a reference of the test     
            try:
                test_fnc_ref = getattr(self.i2c_comm, test_name)
                self.__RunTest(test_fnc_ref, retries) 
            except AttributeError:
                #print("ERROR:\t Unable to find Test: {}".format(test_name))
                self.logger.logtofile("ERROR:\tTest {} Not Found".format(test_name))

        return
