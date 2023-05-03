import os
import json
import time
from log_management import LOG_Manager
from Sequencer import SeqConfig
from firmware import ELBFirmware
from i2c_comm import ELB_i2c
from results_processing import ResultsManager
from i2c_types import MOD_Rates
from gpio_ctrl import GPIO_CONTROL

# This class will define how the program flows

class ProgramControl:  
    
    # Dummy SN to prevent Emtpy 
    sn = "JNPRSN0102"
    # Read from the config file
    seq_file = ""
    limits_file = ""
    # Execution time between sequences, default 1, modified by settings file
    time_between_seq = 1
    test_settings = None
    # Object to handle the log to files
    logger = None
    # Object to handle the i2c communication with UUT
    i2c_comm = None


    # Define the stuff that needs to happen for this prog runs 
    def __init__(self, args) -> None:
        print("Message: \tInit Test Program")
        self.input_args = args
        self.__ValidateArgs()
        self.__StartLog()
        # por hacer:
        # Launch the i2c Comm and the GPIO manager?
        self.__Read_FlowConfig()
        # Firmware not ready yet!
        #self.__Verify_Firmware()
        # Launch the results processing object with a reference to the logger object
        self.results_mgr = ResultsManager(self.limits_file, self.logger)
        # Launch the GPIO controller
        self.gpioctrl = GPIO_CONTROL()
        pass
    
    def __StartLog(self) -> None:
        try:
            # Start Logfile
            self.logger = LOG_Manager(self.sn, self.log_path)
        except:
            print("ERROR: \tUnable to Start the Logfile. Verify settings")    

    def __ValidateArgs(self):
        
        if (len(self.input_args) < 5):
            print("ERROR: \tWrong Parameter Settings")
            print("Message: \tTo run this program you need at least 6 parameters")
            raise FileExistsError
        else:
            # Define all of the input parameters
            self.sn = self.input_args[1]
            self.rev = self.input_args[2]
            self.partnum = self.input_args[3]
            self.seq_file = self.input_args[4]
            self.limits_file = self.input_args[5]
            self.config_file = self.input_args[6]
            # Read the settings from the Json file
            self.__Read_Settings()
        return
    
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
    
    # Reading the flow-control from the seqconfig.xml file 
    def __Read_FlowConfig(self):
        try:
            xml_handler = SeqConfig()
            self.test_flow = xml_handler.ReadSeq_Settings(self.seq_file)
            self.test_count = xml_handler.test_count
        except:
            self.logger.logtofile("ERROR:\tUnable to read the sequence XML Config File")
    
    # Fnc to handle the firmware upgrade of the UUT
    def __FirmwareUpgrade(self):
        fwhandler = ELBFirmware(self.config_file, self.gpioctrl)
        # Verify the firmware version and try to upgrade it
        [fw_ver, retimer] = fwhandler.fw_verification()
        self.logger.logtofile("FW Version Before Upgrade: {}".format(fwhandler.old_fw))
        self.logger.logtofile("FW Version After Upgrade: {}".format(fw_ver))
        self.logger.logtofile("Retimer HostAddress: {}".format(retimer))
    
    def __Program_UUT_SN(self):
        print("Event: \tSerial Number Programming")
        # Read the old SN (if any)
        old_uut_data = self.i2c_comm.uut_serial_num()
        old_sn_str:str
        old_sn_str = old_uut_data[0][1]
        # Data in the SN register is Juniper format, thus this is a re-test
        if (old_sn_str[0:2] == "ZP"):
            self.logger.logtofile("Warning: \tUUT has a valid SN Programmed")
            self.logger.logtofile("Old UUT SN: {}".format(old_sn_str))
        self.i2c_comm.write_uut_sn(self.sn, self.partnum, self.rev)
        self.logger.logtofile("Wrote SN: {}".format(self.sn))
        self.logger.logtofile("Wrote Rev: {}".format(self.rev))
        self.logger.logtofile("Wrote Part Number: {}".format(self.partnum))
        # Wait 2 seconds to sync up 
        time.sleep(2)
    
    def __RunTest(self, test_fnc:object, retries:int, test_name:str):
        
        for i in range(retries):
            results = test_fnc()
            self.results_mgr.ProcessResults(test_name, results)
        pass
    
    def run_program(self):
        # Run Detection check
        self.logger.logtofile("Event:\tRunning Detection")
        uut_detection = self.gpioctrl.detect_uut(120)
        if uut_detection:
            self.logger.logtofile("UUT Detected. Running FW Upgrade")
            # Firmware Upgrade and SN Programming will execute first
            print("Event: \tFirmware Programming")
            self.__FirmwareUpgrade()
            # Firmware Upgrade completed or Not required, launch i2c Communication
            self.i2c_comm = ELB_i2c(self.prbs_modrate, self.i2c_address, self.gpioctrl)
            self.__Program_UUT_SN()   
            # For each test in the TestFlow 
            for test in self.test_flow:
                # Read the testname from the xml config
                test_name = test['test_name']
                retries = int(test['retries'])
                # get a reference of the test     
                try:
                    test_fnc_ref = getattr(self.i2c_comm, test_name)
                    results = self.__RunTest(test_fnc_ref, retries, test_name)
                    time.sleep(self.time_between_seq) 
                except AttributeError:
                    #print("ERROR:\t Unable to find Test: {}".format(test_name))
                    self.logger.logtofile("ERROR:\tTest {} Not Found".format(test_name))
        else:
            self.logger.logtofile("ERROR: \tUser did not inserted the ELB. No test were executed")
        return

    