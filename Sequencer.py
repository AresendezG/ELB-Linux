import xml.etree.ElementTree as ET

class SeqConfig:
    
    test_count = 0

    def __init__(self) -> None:
        
        pass

    def ReadSeq_Settings(self, xmlfile) -> list:  
        # Reset the test counter
        self.test_count = 0
        # create element tree object
        tree = ET.parse(xmlfile)
        # get root element
        root = tree.getroot()
        # create empty list for tests
        tests = []
  
        # iterate news items
        print("Step count: {}".format(root.findall("step")))
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