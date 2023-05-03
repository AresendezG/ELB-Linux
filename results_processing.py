import os
import json
from log_management import LOG_Manager

class ResultsManager:

    # Get track of all the tests reported to the test log
    test_counter = 0

    # Init the limits contained in the Limits file
    def __init__(self, limits_file:str, results_file_handler:LOG_Manager) -> None:
        # Validate and load all the results file
        if (os.path.isfile(limits_file)):
            with open(limits_file, 'r') as f:
                self.all_limits = json.load(f)
        else:
            print("ERROR:\tTest Limits File does not exist")
            raise FileNotFoundError
        # This object should've been initialized by the Program manager
        self.results_log = results_file_handler

        pass
    
    
    # Verify if the measurement is within limits or not
    def __DetermineTestStatus(self, highlimit:str, measurement, lowlimit) -> list:
        hl = float(highlimit)
        ll = float(lowlimit)
        meas = float(measurement)
        if (meas >= ll and meas <= hl):
            return ["PASS", True]
        else:
            return ["FAIL", False]
        
    def __DetermineStatus_NonNumeric(self, expected:str, uut_response:str) -> list:
        if (expected == uut_response):
            return ["PASS", True]
        else:
            return ["FAIL", False]


    # Will determine if the given bunch of results pass or fail
    def ProcessResults(self, seqname:str, results: list) -> bool:
        seq_result = True
        # get the list of results for this group of tests from the JSON limits file
        try:
            # Find if this group of tests has a defined group of limits
            seq_limits_list = self.all_limits[seqname]
            for item in range (len(results)):
                try:
                    # Get individual test limits based on the test name
                    test_limits = seq_limits_list[results[item][0]]
                    # if the giving result is enabled to be reported and its a numeric result
                    if (test_limits['report'] and test_limits['numeric']):
                        # Determine if measurements is within limits
                        test_status = self.__DetermineTestStatus(test_limits['high_limit'],results[item][1],test_limits['low_limit'])
                        # Log a new line to the results file
                        self.results_log.logresult(self.test_counter,test_status[0],test_limits['test_name'],test_limits['high_limit'],results[item][1],test_limits['low_limit'])
                        # This will change to FAIL if the measurement is not within limits
                    elif (test_limits['report'] and (not test_limits['numeric'])):
                        # Determine a pass or fail for non_numeric checks
                        test_status = self.__DetermineStatus_NonNumeric(test_limits['expected_data'], results[item][1])
                        # Log a non-numeric to the results file
                        self.results_log.logresult_nonnumeric(self.test_counter,test_status[0],test_limits['test_name'],test_limits['expected_data'],results[item][1])
                    # Process the next test result and increase counter
                    seq_result = test_status[1]
                    item = item+1
                    self.test_counter = self.test_counter+1
                except:
                    print("ERROR:\tNo Test Limit defined for {}".format(results[item][0]))
        except:
            print("Warning:\tSequence {} has no defined Test Limits".format(seqname))
        return seq_result

    def Validate_UUT_Serial(self, uut_serial:str, expected_serial:str) -> bool:
        result = True
        if (uut_serial == expected_serial):
            self.results_log.logresult("UUT Serial,{}".format(uut_serial))
        else:
            print("Fail:\Wrong Serial Number\tExpected: {}\tRead: {}".format(expected_serial, uut_serial))
            result = False
        return result