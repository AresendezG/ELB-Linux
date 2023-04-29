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
            self.logger = LOG_Manager(self.sn, "c:\\Tmp\\TestLog")
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
            self.logger("ERROR:\tUnable to read the sequence XML Config File")

    def __RunTest(self, test_fnc, retries:int):
        
        for i in range(retries):
            results = test_fnc()
        pass
    
    def run_program(self):
        print("Event:\tTesting Start Start")
        executed = 0
        # pending = self.test_count
        for test in self.test_flow:
            if  test['name'] == "voltage":
                self.logger("Event:\tExecuting Voltage Test")
                self.__RunTest(self.i2c_comm.voltagefnc(), 2)
                
            elif test['name'] == "current":
                self.logger("Event:\tExecuting Current test")
                self.__RunTest(self.i2c_comm.currentfnc(), 2)
            else:
                self.logger("Event:\tUndefined test found")


        return
