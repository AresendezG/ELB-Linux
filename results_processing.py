import os
import json
from log_management import LOG_Manager, MessageType
from i2c_types import LedMode


class ResultsManager:

    # Get track of all the tests reported to the test log
    test_counter = 0
    # Create a dict to hold all the test limits
    all_limits:dict
    # Init the limits contained in the Limits file
    def __init__(self, limits_file:str, log_handler:LOG_Manager) -> None:
        # Validate and load all the results file
        if (os.path.isfile(limits_file)):
            with open(limits_file, 'r') as f:
                self.all_limits = json.load(f)
        else:
            print("ERROR:\tTest Limits File does not exist")
            raise FileNotFoundError
        # This object should've been initialized by the Program manager
        self.log_mgr = log_handler
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
    def ProcessResults(self, seqname:str, results: list) -> list:
        seq_result = True
        # Each step of the sequence will be a PASS (true) or FAIL (false)
        step_result_list = []
        # Each step will create a list with the test name, result, test type, etc
        log_results_list = []
        test_counter = self.test_counter
        # get the list of results for this group of tests from the JSON limits file
        try:
            # Find if this group of tests has a defined group of limits
            seq_limits_list = self.all_limits[seqname]["step_list"]
            for item in range (len(results)):
                try:
                    # Get individual test limits based on the test name
                    test_limits = seq_limits_list[results[item][0]]
                    # This step is enabled to be reported and its a numeric result
                    if (test_limits['report'] and test_limits['numeric']):
                        # Determine if measurements is within limits
                        test_status = self.__DetermineTestStatus(test_limits['high_limit'],results[item][1],test_limits['low_limit'])
                        # Log a new line to the results file
                        self.log_mgr.print_numeric_console(self.test_counter,test_status[0],test_limits['test_name'],test_limits['high_limit'],results[item][1],test_limits['low_limit'])
                        log_line = ["NUM", self.test_counter,test_status[0],test_limits['test_name'],test_limits['high_limit'],results[item][1],test_limits['low_limit']]
                    # This step is enabled for report and non-numeric result
                    elif (test_limits['report'] and (not test_limits['numeric'])):
                        # Determine a pass or fail for non_numeric checks
                        test_status = self.__DetermineStatus_NonNumeric(test_limits['expected_data'], results[item][1])
                        # Log a non-numeric to the results file
                        self.log_mgr.print_nonnumeric_console(self.test_counter,test_status[0],test_limits['test_name'],test_limits['expected_data'],results[item][1])
                        log_line = ["P/F", self.test_counter,test_status[0],test_limits['test_name'],test_limits['expected_data'],results[item][1]]
                    # Process the next test result and increase counter
                    step_result_list.append(test_status[1])
                    item = item+1
                    self.test_counter = self.test_counter+1
                    log_results_list.append(log_line)
                except:
                    print("ERROR:\tNo Test Limit defined for {}".format(results[item][0]))
        except:
            print("Warning:\tSequence {} has no defined Test Limits".format(seqname))
        
        # Determine the status of the sequence if all of the steps passed or not
        seq_result = all(step_result_list)
        # If the test failed, reset the counter as this result might not be logged
        if (not seq_result):
            self.test_counter = test_counter
        # Return the sequence result, and a list with the log lines. The program mgr will decide if this list is logged or not
        return [seq_result, log_results_list]
        

    # trim strings to max of 16 characters
    def trim_str(inputstr:str, size:int) -> str:
        if (len(inputstr) <= size):
            # pad with empty chars 
            outstr = inputstr+"".join(" " for x in range(size-len(inputstr)))
        elif (len(inputstr) > size):
            # truncate
            outstr = inputstr[0:size]
        return outstr

    def create_pn2(uut_pn:str, uut_rev:str):
        pn2_hex = [ord(x) for x in uut_pn[0:12]]+[ord(x) for x in "REV "]+[ord(x) for x in uut_rev]
        if len(pn2_hex)>32: # 32 bytes
           pn2_hex = pn2_hex[0:32]
        return pn2_hex

    def process_remote_inputs(self, userinput) -> list:
        print(userinput)
        results_list = []
        for item in userinput:
            results_list.append([item['test_name'], item['result']])
        return results_list

    def include_sn_limits(self, uut_serial:str, uut_pn:str, uut_rev:str) -> dict:
        # copy to local dict to manipulate data
        updated_all_limits = self.all_limits
        # Create same strings as those programmed into the UUT
        uut_serial_formatted = ResultsManager.trim_str(uut_serial, 16) # call is as static fnc
        uut_pn_formatted = ResultsManager.trim_str(uut_pn, 16)
        uut_rev_formatted = ResultsManager.trim_str(uut_rev, 2)
        uut_pn2_hex = ResultsManager.create_pn2(uut_pn, uut_rev)
        uut_pn2_str = "".join(chr(x) for x in uut_pn2_hex)
        # Update the keys in the ALL LIMITS read from the json file 
        try:
            # keys for the programming uut-sn sequence
            updated_all_limits['prog_uut_sn']['step_list']['serial']['expected_data'] = uut_serial
            updated_all_limits['prog_uut_sn']['step_list']['partnum']['expected_data'] = uut_pn
            updated_all_limits['prog_uut_sn']['step_list']['rev']['expected_data'] = uut_rev
            # keys for the read sn sequence 
            updated_all_limits['uut_serial_num']['step_list']['serial']['expected_data'] = uut_serial_formatted
            updated_all_limits['uut_serial_num']['step_list']['part_num']['expected_data'] = uut_pn_formatted
            updated_all_limits['uut_serial_num']['step_list']['rev']['expected_data'] = uut_rev_formatted
            updated_all_limits['uut_serial_num']['step_list']['pn2_str']['expected_data'] = uut_pn2_str
            # Update all_limits in this object for future results processing
            self.all_limits = updated_all_limits
            self.log_mgr.print_message("Updated SN/PN/REV Limits",MessageType.EVENT, True)
            # return all_limits to caller for the flow control
            return updated_all_limits
        except KeyError:
            self.log_mgr.print_message("Incorrect or Missing Parameters in the Sequence File",MessageType.FAIL)
            raise KeyError

    def Add_SN_ToLimits(self, uut_serial:str, uut_pn:str, uut_rev:str) -> dict:
            
        # Create same strings as those programmed into the UUT
        uut_serial = ResultsManager.trim_str(uut_serial, 16) # call is as static fnc
        uut_pn = ResultsManager.trim_str(uut_pn, 16)
        uut_rev = ResultsManager.trim_str(uut_rev, 2)
        uut_pn2_hex = ResultsManager.create_pn2(uut_pn, uut_rev)
        uut_pn2_str = "".join(chr(x) for x in uut_pn2_hex)
        # Create a dict with the dynamic parameters
        serialnum_dict:dict = {
            'uut_serial_num':{
                    "step_list":
                    {
                        "serial":
                        {
                        "test_name": "SERIAL_NUMBER_READBACK",
                    "expected_data": uut_serial,
                           "report":True,
                          "numeric":False
                        },
                        "part_num":
                        {
                        "test_name": "PART_NUMBER_READBACK",
                    "expected_data": uut_pn,
                           "report":True,
                          "numeric":False
                        },
                        "rev":
                        {
                        "test_name": "REV_READBACK",
                    "expected_data": uut_rev,
                           "report":True,
                          "numeric":False
                        },
                        "partnum2":
                        {
                        "test_name": "PART_NUMBER_2_READBACK",
                    "expected_data": uut_pn2_str,
                           "report":True,
                          "numeric":False
                        }           
                      }
                    },
                    "settings":
                    {
                        "run":True,
                        "retries":True,
                        "attempts":3
                    }
                    }
        # Append the newly created dict to the all limits dict
        self.all_limits.update(serialnum_dict)
        return self.all_limits
    

