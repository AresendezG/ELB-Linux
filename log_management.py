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
    
    def __init__(self, def_path: str) -> None:
        # Var definitions
        self.logs_path = def_path
        self.logfile = None     # Handler of the plaintxt logfile
        self.resultsfile = None # Handler of the results logfile
        self.logfilename = ""
        self.ext_logfile = ".txt"
        self.ext_results = ".csv"
        self.files_closed = True
        pass        
        
    
    def __del__(self):
        print("Message:\tClosing Active Logfiles")

        pass

    # Validate default paths
    def __validate_def_path(self) -> bool:
        if not os.path.exists(self.logs_path):
        # Try to create the default dir if it does not exist
            try:
                os.makedirs(self.logs_path)
                return True
        # for whatever reason, OS has rejected the creation of the default dir    
            except:
                return False
        else:
            return True 

    def __create_logfile_handlers(self) -> bool:
        log_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logs_path = self.logs_path + "/"+self.serial+"/"+ log_time
        if (self.__validate_def_path()):
            # Update the results logfile
            self.logfilename =     "/ELB_"+log_time+"_"+self.serial+self.ext_logfile
            self.resultsfilename = "/ELB_"+log_time+"_"+self.serial+self.ext_results

            # check if file exists
            filecnt = 0
            while os.path.isfile(self.logs_path+self.logfilename):
                filecnt = filecnt + 1
                # print warning
                print("Warning: File already exist: {}\n".format(self.logs_path+self.logfilename))
                # create unique file name
                self.logfilename =     "/ELB_"+self.serial+"_"+log_time+"_"+str(filecnt)+self.ext_logfile
                self.resultsfilename = "/ELB_"+self.serial+"_"+log_time+"_"+str(filecnt)+self.ext_results
            # create files
            try: 
                self.logfile = open(self.logs_path+self.logfilename, "w")
                self.resultsfile = open(self.logs_path+self.resultsfilename, "w")
                print("Event: Opened {}\n".format(self.logs_path+self.logfilename))
                print("Event: Opened {}\n".format(self.logs_path+self.resultsfilename))
                return True
            except:
                print("ERROR: Unable to open Logfiles!")
                return False
        else:
            return False

    def __print_logfile_header(self) -> bool:
        log_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.log_to_file("Juniper Electric Loopback Test Log\n")
        self.log_to_file("=====================\n")
        self.log_to_file(f"Test Date: {log_time}\n")
        self.log_to_file(f"UUT SN: {self.serial}")
        self.resultsfile.write("Juniper Electric Loopback TestResults\n")
        self.resultsfile.write(f"Test Date,{log_time}\n")
        self.resultsfile.write(f"UUT SN,{self.serial}\n")
        self.resultsfile.write("Index,Result,Test Name,High Limit,Measurement,Low Limit\n")
        self.files_closed = False
        return True


    def create_log_files(self, serial:str) -> bool:
        self.serial = serial
        # Validate serial number
        if (len(serial) < 1):
            raise TypeError("ERROR: Expected a Serial Number as Parameter")        
        files_status = self.__create_logfile_handlers()
        if (files_status):
            self.start_time = datetime.datetime.now()
            return self.__print_logfile_header()
        else:
            raise FileExistsError("ERROR: Unable to Create the LogFiles")


    def log_to_file(self, line: str):
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
        pass


    # print PASS on Green and FAILs on Red
    def format_test_for_console(self, status:str) -> str:
        if (status == "PASS"):
            mesg_type = MessageType.OKGREEN
        elif(status == "FAIL"):
            mesg_type = MessageType.FAIL
        else:
            mesg_type = MessageType.ENDC
        return (f"{mesg_type}{status}{MessageType.ENDC}")


    def close_logs(self):
        if(self.files_closed):
            return
        else:
            try:
                self.logfile.close()
                self.resultsfile.close()
                os.chmod(self.logs_path+self.logfilename,0o777)
                os.chmod(self.logs_path+self.resultsfilename,0o777)
                self.files_closed = True
            except:
                return

    ''' 
    This part of the class implements a file storage method for the "Firmware Upgrade" mode
    which is a special mode to only run the firmware-upgrade and firmware verification
    
    '''
    # Create a log file to track the list of UUTs with the firmware upgraded 
    def create_fwupgrade_log(self) -> bool:
        log_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logs_path = self.logs_path + "/fwupgrade/"
        if (self.__validate_def_path()):
            # Update the results logfile
            self.fwup_logfilename =     "/FWUpgrade_"+log_time+self.ext_logfile
            try: 
                self.fwup_file = open(self.logs_path+self.fwup_logfilename, "w")
                print("Event: Opened {}\n".format(self.logs_path+self.fwup_logfilename))
                return True
            except:
                print("ERROR: Unable to open Logfiles!")
            return False
        else:
            return False

    # Log data in the firmware upgrade list
    def __log_fwupgrade_file(self, line:str):
        print(line)
        self.fwup_file.write(line+"\n")
        return
    
    def print_fwupgrade_headers(self, fw_version:str):
        log_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.__log_fwupgrade_file("Firmware Upgrade Session")
        self.__log_fwupgrade_file(f"Date: {log_time}")
        self.__log_fwupgrade_file(f"New Firmware: {fw_version}")
        return
    # Log the UUT SN into the firmware upgrade list
    def log_new_uut_fwupgrade(self, uutsn:str):
        log_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.__log_fwupgrade_file(f"UUT SN: {uutsn}")
        self.__log_fwupgrade_file(f"Completion Time: {log_time}")
        return
    # close the file for the firmware upgrade list
    def close_uut_fwupgrade_file(self):
        try:
            self.fwup_file.close()
            os.chmod(self.logs_path+self.fwup_logfilename,0o777)
        except:
            return
        return