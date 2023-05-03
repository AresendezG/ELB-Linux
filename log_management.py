import os
import datetime

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
        self.resultsfile.write("UUT SN,{}".format(self.serial))
        self.resultsfile.write("Result,Test Name,High Limit,Measurement,Low Limit\n")


    def logtofile(self, line: str):
        print(line) # Use same fnc to display info to screen
        self.logfile.write(line + "\n") # Append new Line
        return

    def logresult(self, testindex:int, result: str, testname:str, measurement:str, highlim: str, lowlim: str):
        # display numeric tests in tabseparated
        str_to_log = "{}\t{}\t{}\t{}\t{}\t{}\n".format(testindex, result, testname, highlim, measurement, lowlim)
        print(str_to_log)
        # log to results file in comma separated
        self.resultsfile.write(str_to_log)
        pass