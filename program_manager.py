from log_management import LOG_Manager
from Sequencer import SeqConfig
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
        #TODO:
        # Launch the i2c Comm and the GPIO manager?
        self.__Read_FlowConfig()
        #self.test_config = 
        pass
    
    # Cleanup
    def __delete__(self) -> None:
        pass

    def __StartLog(self) -> None:
        try:
            # Start Logfile
            self.logger = LOG_Manager(self.sn, "c:\\Tmp\\TestLog\\")
        except:
            print("ERROR:\tUnable to Start the Logfile. Verify settings")    

    def __ValidateArgs(self):
        
        if (len(self.input_args) < 4):
            print("ERROR:\tWrong Parameter Settings")
            print("Message:\tTo run this program you need 4 parameters")
        else:
                self.sn = self.input_args[1]
                self.seq_file = self.input_args[2]
                self.limits_file = self.input_args[3]
        return
    
    def __Read_FlowConfig(self):
        try:
            xml_handler = SeqConfig()
            self.test_flow = xml_handler.ReadSeq_Settings(self.seq_file)
            self.test_count = xml_handler.test_count
        except:
            self.logger.logtofile("ERROR:\tUnable to read the sequence XML Config File")

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
                print("ERROR:\t Unable to find a test named{}".format(test_name))
                self.logger.logtofile("ERROR:\tTest {} Not Found".format(test_name))

        return
