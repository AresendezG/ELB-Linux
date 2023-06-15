import xml.etree.ElementTree as ET
import os
import json

class SeqConfig:
    
    test_count = 0

    def __init__(self) -> None:
        
        pass

    def ReadSeq_Settings_XML(self, xmlfile) -> list:  
        # Reset the test counter
        self.test_count = 0
        # create element tree object
        tree = ET.parse(xmlfile)
        # get root element
        root = tree.getroot()
        # create empty list for tests
        tests = []
  
        # iterate news items
        print("Event:\tSteps Count in Sequence: {}".format(len(root.findall("step"))))
        for item in root.findall('step'):
            # empty test_step
            test_step = {}
            test_step['test_name'] = item.attrib['name']
            test_step['index'] = self.test_count
            # iterate child elements of item
            for child in item:
                test_step['retries'] = child.attrib['retries']
                test_step['flow'] = child.attrib['flow']
            # append news dictionary to news items list
            tests.append(test_step)
            ++self.test_count      
        # return news items list
        return tests
    
    def ReadSeq_Settings_JSON(self, limits_file:str, all_limits:dict = None) -> list:
        # {'test_name': 'uut_serial_num', 'index': 0, 'retries': '1', 'flow': 'cont'}
        flow = []
        if (all_limits == None):
            self.test_count = 0
            if (os.path.isfile(limits_file)):
                with open(limits_file, 'r') as f:
                    all_limits = json.load(f)
            else:
                print("ERROR:\tTest Limits File does not exist")
                raise FileNotFoundError
        for item in all_limits:
            if (all_limits[item]['settings']['run']):
                try:
                    test_step = {}
                    test_step['test_name'] = item
                    test_step['index'] = self.test_count
                    test_step['retries'] = all_limits[item]['settings']['attempts']
                    test_step['flow'] = all_limits[item]['settings']['flow_cont']
                    print(item)
                    flow.append(test_step)
                    del test_step
                    self.test_count = self.test_count+1
                except KeyError:
                    print("-****************-")
                    print(f"Error: The limits file {limits_file} cannot be read, it has an invalid format.")
                    print("-****************-")
                    raise KeyError
        
        self.test_count = self.test_count+1
        # Return the list with the test execution flow
        return flow

    def ReadSeq_fromJSON(self, limits_file:str) -> list:
        counter = 0
        ret_list:list = []
        if (os.path.isfile(limits_file)):
            with open(limits_file, 'r') as f:
                all_limits = json.load(f)
        else:
            print("ERROR:\tTest Limits File does not exist")
            raise FileNotFoundError
        
        for item in all_limits:
            if (all_limits[item]['settings']['run']):
                try:
                    for step in all_limits[item]["step_list"]:
                        step_list = []
                        step_list.append(counter)
                        step_list.append(all_limits[item]["step_list"][step]["test_name"])
                        if (all_limits[item]["step_list"][step]["numeric"]):
                            step_list.append(all_limits[item]["step_list"][step]["low_limit"])
                            step_list.append("NOTRUN")
                            step_list.append(all_limits[item]["step_list"][step]["high_limit"])
                        else:
                            step_list.append(all_limits[item]["step_list"][step]["expected_data"])
                            step_list.append("NOTRUN")
                            step_list.append(all_limits[item]["step_list"][step]["expected_data"])
                        counter = counter+1
                        ret_list.append(step_list)
                except:
                    pass
        
        return ret_list