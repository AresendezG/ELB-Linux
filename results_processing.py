import os
import json

class ResultsManager:

    item = 0

    def __init__(self, limits_file) -> None:
        if (os.path.isfile(limits_file)):
            with open(limits_file, 'r') as f:
                self.all_limits = json.load(f)
        else:
            print("ERROR:\tTest Limits File does not exist")
            raise FileNotFoundError
        pass
    
    # Will determine if the given bunch of results pass or fail
    def ProcessResults(self, seqname:str, results: list) -> bool:
        seq_result = True
        # get the list of results for this sequence from the JSON
        try:
            seq_limits_list = self.all_limits[seqname]
            for item in range (len(results)):
                try:
                    # Get individual test limits based on the test name
                    test_limits = seq_limits_list[results[item][0]]
                    # if the limit is enabled to be reported...
                    if (test_limits['report']):
                        print("{},{},{},{},{}".format(test_limits['test_name'],test_limits['high_limit'],results[item][1],test_limits['low_limit'], item))
                        ++item
                except:
                    print("ERROR: No Test Limit defined for {}".format(results[item][0]))
        except:
            print("Warning:\tSequence {} has no defined Test Limits".format(seqname))
        return seq_result
