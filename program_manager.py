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
        self.__Read_FlowConfig()
        # Launch the results processing object with a reference to the log_mgr object
        self.results_mgr = ResultsManager(self.limits_file, self.log_mgr)
        # Define as testlimit the serial number, partnumber and revision
        self.results_mgr.Add_SN_ToLimits(self.sn, self.partnum, self.rev)
        # Launch the GPIO controller
        self.gpioctrl = GPIO_CONTROL(self.log_mgr)
        pass
    
    def __StartLog(self) -> None:
        try:
            # Start Logfile handler. This is also the console rich handler.
            self.log_mgr = LOG_Manager(self.sn, self.log_path)
        except:
            print("ERROR: \tUnable to Start the Logfiles. Verify settings")
            # We dont want executions with empty lofgiles. Stop Here.
            raise RuntimeError    

    def __ValidateArgs(self):
        
        if (len(self.input_args) < 5):
            print("ERROR: \tWrong Parameter Settings")
            print("Message: \tTo run this program you need at least 6 parameters")
            raise FileExistsError
        else:
            # Define all of the input parameters
            self.sn = self.input_args[0]
            self.rev = self.input_args[1]
            self.partnum = self.input_args[2]
            self.seq_file = self.input_args[3]
            self.limits_file = self.input_args[4]
            self.config_file = self.input_args[5]
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
            self.log_mgr.print_message("ERROR: Unable to read Sequence XML File. Stopping Execution", MessageType.FAIL)
            self.log_mgr.log_to_file("ERROR:\tUnable to read the sequence XML Config File. Stopping")
            raise RuntimeError
    
    # Fnc to handle the firmware upgrade of the UUT
    def __FirmwareUpgrade(self):
        self.log_mgr.print_message("Firmware Programming", MessageType.EVENT, True)
        fwhandler = ELBFirmware(self.config_file, self.gpioctrl, self.log_mgr)
        # Verify the firmware version and try to upgrade it
        [fw_ver, retimer] = fwhandler.fw_verification()
        self.log_mgr.log_to_file("FW Version Before Upgrade: {}".format(fwhandler.old_fw))
        self.log_mgr.log_to_file("FW Version After Upgrade: {}".format(fw_ver))
        self.log_mgr.log_to_file("Retimer HostAddress: {}".format(retimer))
    
    def __Program_UUT_SN(self):
        self.log_mgr.print_message("Serial Number Programming", MessageType.WARNING, True)
        # Read the old SN (if any)
        old_uut_data = self.i2c_comm.uut_serial_num()
        old_sn_str:str
        old_sn_str = old_uut_data[0][1]
        # Data in the SN register is Juniper format, thus this is a re-test
        if (old_sn_str[0:2] == "ZP"):
            self.log_mgr.print_message("UUT has a valid SN already Programmed", MessageType.WARNING, True)
            self.log_mgr.print_message("Old UUT SN: {}".format(old_sn_str), MessageType.WARNING, True)
        self.i2c_comm.write_uut_sn(self.sn, self.partnum, self.rev)
        self.log_mgr.print_message("New SN: {}".format(self.sn), MessageType.EVENT, True)
        self.log_mgr.print_message("Revision {}".format(self.rev), MessageType.EVENT, True)
        self.log_mgr.print_message("Part Number: {}".format(self.partnum), MessageType.EVENT, True)
        # Wait 2 seconds to sync up 
        time.sleep(2)
    
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
            self.__FirmwareUpgrade()
            # Firmware Upgrade completed or Not required, launch i2c Communication
            self.i2c_comm = ELB_i2c(self.prbs_modrate, self.i2c_address, self.gpioctrl, self.log_mgr)
            self.__Program_UUT_SN()   
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
                    if (not seqresult and flow_ctrl != "cont"):
                        self.log_mgr.print_message(f"FAILURE at {test_name}. Stopping Execution", MessageType.FAIL)
                        return False
                    time.sleep(self.time_between_seq) 
                except AttributeError:
                    #print("ERROR:\t Unable to find Test: {}".format(test_name))
                    self.log_mgr.print_message("Test {} Not Found".format(test_name), MessageType.WARNING, True)
        else:
            self.log_mgr.print_message("User did not inserted the ELB. No test were executed", MessageType.WARNING, True)
        return

    