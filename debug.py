import sys 
import xml
from Sequencer import SeqConfig
import sys
import time
#from i2c_comm import ELB_i2c
#from i2c_types import MOD_Rates
from log_management import LOG_Manager
# from firmware import ELBFirmware
from results_processing import ResultsManager
from arguments import UserArguments

class DummyClass:
    def __init__(self) -> None:
        print("Event:\tCreating a dummy class! jejeje")
        pass

    def temp_sensors(self) -> list:
        print("Test:\tExecuting TempSensors Test")
        return [1, 2, 3, 4]
    
    def ins_count(self) -> list:
        print("Executing ins Count Test")
        return [0, 10]

    def power_loads(self) -> list:
        print("Test:\tExecuting PowerLoad Test")
        return [0.2, 0.3, 0.5]
    

class i2c_PicoInterface:

    def __init__(self) -> None:
        from smbus2 import SMBus
        self.pico_address = 0x17
        self.RPI_BUS = 1
        self.i2cbus = SMBus(self.RPI_BUS)
        print("Opening Comm with RPI Pico at {}".format(self.pico_address))

    def __del__(self) -> None:
        # self.i2cbus.write_i2c_block_data(self.pico_address, 0xff, [0])
        self.i2cbus.close()
        print("Closed i2c Bus")

    def validate_firmware(self) -> bool:
        print("Event:\tClosing i2c Bus")
        self.i2cbus.close()
        fwupgrader = ELBFirmware("settings.json")
        [fw_version, retimer] = fwupgrader.fw_verification()
        print("FW Version: {}".format(fw_version))
        print("Retimer hostcheck: {}".format(retimer))
        self.i2cbus.open(self.RPI_BUS)

    def read_sn(self) -> str:        
        print("Event:\tTrying to read Pico SN")
        self.__enable_command()
        data = self.i2cbus.read_i2c_block_data(self.pico_address, 166, 8)
        serial_array = [x for x in data] #array that holds the serialnumber
        serial_str = "".join(chr(x) for x in serial_array)
        print("Serial: {}".format(serial_str))
        return serial_str
    
    def __enable_command(self):
        print("MSG:\tSending Enable cmd")
        self.i2cbus.write_i2c_block_data(self.pico_address, 127, [3])
        print("check for cmd ack status...")
        time.sleep(1)
        pass

    def __disable_command(self):
        print("Disable command")
        self.i2cbus.write_i2c_block_data(self.pico_address, 0xff, [0])
        time.sleep(2)
    
    def read_partnum(self) -> str:
        self.__enable_command()
        print("Event:\tRead Part Number")
        data = self.i2cbus.read_i2c_block_data(self.pico_address, 148, 5)
        pn_array = [x for x in data]
        pn_str = "".join(chr(x) for x in pn_array)
        print("Part Number: {}".format(pn_str))
        return pn_str

    def write_new_sn(self, serial:str) -> None:
        print("Event:\tSend Enable cmd")
        self.__enable_command()
        print("Event:\tEnable to manipulate memory")
        time.sleep(2)
        serial_list = [ord(x) for x in serial]
        self.i2cbus.write_i2c_block_data(self.pico_address, 166, serial_list)
        print("Event\tNew Serial is: {}".format(serial))
        self.__disable_command()
        pass

    def read_fw_ver(self) -> str:
        print("Event:\tTrying to read Pico FW Version")
        self.__enable_command()
        data = self.i2cbus.read_i2c_block_data(self.pico_address, 39, 2)
        fwver = "{}.{}".format(data[0], data[1])
        print("FW Version: {}".format(fwver))
        return fwver


def __main__():
    
    '''
        test_name = test['test_name']
        retries = int(test['retries'])
        flow_ctrl = test['flow']
    '''
    sn = "ZP00203003"
    pn = "750-219993"
    rv = "09"

    LogMgrObject = LOG_Manager("test_results/")
    LogMgrObject.create_log_files(sn)
    SeqObject = SeqConfig()
    ResObject = ResultsManager("configs/limits.json", LogMgrObject)
    seq_xml = SeqObject.ReadSeq_Settings_XML('configs/seqconfig.xml')
    print("Launch Logfile Manager")    
    # read the limits template
    flow_json = SeqObject.ReadSeq_Settings_JSON('configs/limits.json')
    print("This is flow_json")
    print(flow_json)
    # These are template limits (created during object constructor):
    template_limits = ResObject.all_limits
    print("These are template limits")
    for item in template_limits:
        print(item)
        try:
            print(template_limits[item]['step_list']['serial']['expected_data'])
            print(template_limits[item]['step_list']['rev']['expected_data'])
            print(template_limits[item]['step_list']['part_num']['expected_data'])
        except:
            pass
    # update the flow object with the SN
    ResObject.include_sn_limits(sn, pn, rv)
    new_limits = ResObject.all_limits
    print("These are updated Limits")
    for item in new_limits:
        print(item)
        try:
            print(new_limits[item]['step_list']['serial']['expected_data'])
            print(new_limits[item]['step_list']['rev']['expected_data'])
            print(new_limits[item]['step_list']['part_num']['expected_data'])
        except:
            pass
    print("Flow ctrl remains the same:")
    print(flow_json)
    # Accessing ind elements
    for test in flow_json: 
        test_name = test['test_name']
        retries = int(test['retries'])
        flow_ctrl = test['flow']
        print(f"Items in {test_name} are: Retries={retries}, flow_ctrl={flow_ctrl}")
    

__main__()

          
        