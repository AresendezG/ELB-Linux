import os
import json

class ResultsManager:

    item = 0

    def __init__(self, limits_file:str, results_file_handler:object) -> None:
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
                    # if the limit is enabled to be reported...
                    if (test_limits['report']):
                        # Determine if measurements is within limits
                        test_status = self.__DetermineTestStatus(test_limits['high_limit'],results[item][1],test_limits['low_limit'])
                        self.results_log.logresult(item,test_status[0],test_limits['test_name'],test_limits['high_limit'],results[item][1],test_limits['low_limit'])
                        # This will change to FAIL if the measurement is not within limits
                        seq_result = test_status[1]
                        ++item
                except:
                    print("ERROR: No Test Limit defined for {}".format(results[item][0]))
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