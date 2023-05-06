import os
import datetime
     

    # Console Messages
class MessageType:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    USER = '\033[94m' #BLUE
    OKCYAN = '\033[96m'
    EVENT = '\033[96m' #CYAN
    OKGREEN = '\033[92m'
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED 
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class LOG_Manager():
    
    def __init__(self, uut_serial: str, def_path: str) -> None:
        
        # Var definitions
        self.default_path = def_path
        self.logfile = None     # Handler of the plaintxt logfile
        self.resultsfile = None # Handler of the results logfile
        self.logfilename = ""
        self.ext_logfile = ".txt"
        self.ext_results = ".csv"
        self.serial = uut_serial        
        self.logfiletime = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        # Validate serial number
        if (not isinstance(uut_serial, str) or len(uut_serial) < 1):
            raise TypeError("ERROR: Expected a Serial Number as Parameter")        
        dir_status = self.__validate_def_path()
        files_status = self.__OpenLogFiles()
        
        if (dir_status and files_status):
            self.__init_logfile()
            pass
        else:
            raise FileExistsError
        
    
    def __del__(self):
        print("Mesaage:\tClosing Logfiles")
        self.logfile.close()
        self.resultsfile.close()
        pass

    # Validate default paths
    def __validate_def_path(self) -> bool:
        if not os.path.exists(self.default_path):
        # Try to create the default dir if it does not exist
            try:
                os.makedirs(self.default_path)
                return True
        # for whatever reason, OS has rejected the creation of the default dir    
            except:
                return False
        else:
            return True 

    def __OpenLogFiles(self) -> bool:
        # Update the results logfile
        self.logfilename = "ELB_"+self.serial+"_"+self.logfiletime+self.ext_logfile
        self.resultsfilename = "ELB_"+self.serial+"_"+self.logfiletime+self.ext_results

        # check if file exists
        filecnt = 0
        while os.path.isfile(self.default_path+self.logfilename):
            filecnt = filecnt + 1
            # print warning
            print("Warning: File already exist: {}\n".format(self.default_path+self.logfilename))
            # create unique file name
            self.logfilename = "ELB_"+self.serial+"_"+self.logfiletime+"_"+str(filecnt)+self.ext_logfile
            self.resultsfilename = "ELB_"+self.serial+"_"+self.logfiletime+"_"+str(filecnt)+self.ext_results
        
        # create files
        try: 
            self.logfile = open(self.default_path+self.logfilename, "w")
            self.resultsfile = open(self.default_path+self.resultsfilename, "w")
            print("Event: Opened {}\n".format(self.default_path+self.logfilename))
            print("Event: Opened {}\n".format(self.default_path+self.resultsfilename))
            return True
        except:
            print("ERROR: Unable to open Logfiles!")
            return False

    def __init_logfile(self):
        self.logtofile("Juniper Electric Loopback Test Log\n")
        self.logtofile("=====================\n")
        self.logtofile("Test Date: {}\n".format(self.logfiletime))
        self.logtofile("UUT SN: "+self.serial)
        self.resultsfile.write("Juniper Electric Loopback TestResults\n")
        self.resultsfile.write("Test Date,{}\n".format(self.logfiletime))
        self.resultsfile.write("UUT SN,{}\n".format(self.serial))
        self.resultsfile.write("Index,Result,Test Name,High Limit,Measurement,Low Limit\n")


    def logtofile(self, line: str):
        print(line) # Use same fnc to display info to screen
        self.logfile.write(line + "\n") # Append new Line
        return


    def log_sequence_results(self, loglines:list):
        
        for item in range(len(loglines)):
            if (loglines[item][0] == "NUM"):
                self.log_numeric_tofile(loglines[item][1:])
            elif (loglines[item][0] == "P/F"):
                self.log_nonnumeric_tofile(loglines[item][1:])
        pass


    def logresult_numeric(self, testindex:int, result: str, testname:str, highlim: str, measurement:str, lowlim: str):
        # print in console
        self.print_numeric_console(testindex, result, testname, highlim, measurement, lowlim)
        # Log to file
        self.log_numeric_tofile(testindex, result, testname, highlim, measurement, lowlim)
        pass

    def print_numeric_console(self, testindex:int, result: str, testname:str, highlim: str, measurement:str, lowlim: str):
        # Format the result to Green or Red for pass or fail
        colored_result = self.format_test_for_console(result)
        # Display in Scientific Notation only for BER resulys
        if (float(measurement) < 1e-6 and float(measurement) > 0):
            str_to_log_console = "{}\t{}\t{}\t{:e}\t{:e}\t{:.1f}".format(testindex, colored_result, testname, highlim, measurement, lowlim)
        else:
            str_to_log_console = "{}\t{}\t{}\t{:.4f}\t{:.4f}\t{:.4f}".format(testindex, colored_result, testname, highlim, measurement, lowlim)
        # Print info to console
        print(str_to_log_console)
        pass

    def log_numeric_tofile(self, inputlist:list = None, testindex = 0, result = "NUM", testname = "TESTNAME", highlim = "0.0", measurement = "1.0", lowlim = "2.0"):

        # All parameters passed as list:
        if (inputlist != None):
            try:
                testindex = inputlist[0]
                result = inputlist[1]
                testname = inputlist[2]
                highlim = inputlist[3]
                measurement = inputlist[4]
                lowlim = inputlist[5]            
            except:
                self.print_message("Wrong List of Parameters to log. Ignoring result",MessageType.WARNING)
                return

        # Display in Scientific Notation only for BER resulys
        if (float(measurement) < 1e-6 and float(measurement) > 0):
            str_to_log_file = "{},{},{},{:e},{:e},{:.1f}\n".format(testindex, result, testname, highlim, measurement, lowlim)
        else:
            str_to_log_file = "{},{},{},{:.4f},{:.4f},{:.4f}\n".format(testindex, result, testname, highlim, measurement, lowlim)
        # Log the line to file
        self.resultsfile.write(str_to_log_file)
        pass

    def logresult_nonnumeric(self, testindex:int, result:str, testname:str, expected_data:str, read_data:str):
        # Print formatted to console
        self.print_nonnumeric_console(testindex, result, testname, expected_data, read_data)
        # Log to file
        self.log_nonnumeric_tofile(testindex, result, testname, expected_data, read_data)
        pass

    def print_nonnumeric_console(self, testindex:int, result:str, testname:str, expected_data:str, read_data:str):
        # Format the result to Green or Red for pass or fail
        result = self.format_test_for_console(result)
        # Display to console in Tab Separated format
        str_to_log = "{}\t{}\t{}\tExp: {}\tRead: {}".format(testindex, result, testname, expected_data, read_data)
        print(str_to_log)
        pass

    def log_nonnumeric_tofile(self, inputlist:list = None, testindex = 0, result:str = "P/F", testname:str = "TESTNAME", expected_data:str = "DATA", read_data:str = "DATA"):
        # All parameters passed as list:
        if (inputlist != None):
            try:
                testindex = inputlist[0]
                result = inputlist[1]
                testname = inputlist[2]
                expected_data = inputlist[3]
                read_data = inputlist[4]          
            except:
                self.print_message("Wrong List of Parameters to log. Ignoring result",MessageType.WARNING)
                return
        # log to results file in comma separated
        str_to_log = "{},{},{},Exp: {},Read: {},NonNumeric\n".format(testindex, result, testname, expected_data, read_data)
        self.resultsfile.write(str_to_log)
        pass


    # Print to console with text characters
    def print_message(self, message:str, mesg_type:MessageType, logtofile:bool = False):

        message_to_print = ""
        if (mesg_type == MessageType.WARNING):
            message_to_print = "Warning: \t"
        elif (mesg_type == MessageType.FAIL):
            message_to_print = "ERROR: \t"
        elif (mesg_type == MessageType.EVENT):
            message_to_print = "Event: \t"
        elif (mesg_type == MessageType.USER):
            message_to_print = "USER INPUT: \t"
        #Concatenate Everything
        print(f"{mesg_type}{message_to_print+message}{MessageType.ENDC}")
        # Caller decides if this goes to file or not. Default is not
        if (logtofile):
            self.logfile.write(message_to_print+message + "\n") # Append new Line
        pass

    def print_led_menu(self):
        # Prints a fixed menu to the console for the LED test
        # create colored messages
        flash = f"{MessageType.WARNING}[f]{MessageType.ENDC}-Flash"
        off = f"{MessageType.BOLD}[o]{MessageType.ENDC}-OFF"
        green = f"{MessageType.OKGREEN}[g]{MessageType.ENDC}-Green"
        red = f"{MessageType.FAIL}[f]{MessageType.ENDC}-Red"
        # create the formated string
        str_to_print = (f"{MessageType.USER}USER INPUT:\t{flash}\t{off}\t{green}\t{red}")
        # print to console
        print(str_to_print)


    # print PASS on Green and FAILs on Red
    def format_test_for_console(self, status:str) -> str:
        if (status == "PASS"):
            mesg_type = MessageType.OKGREEN
        elif(status == "FAIL"):
            mesg_type = MessageType.FAIL
        else:
            mesg_type = MessageType.ENDC
        return (f"{mesg_type}{status}{MessageType.ENDC}")



