from smbus2 import SMBus
import subprocess
import time
import json
import os


class ELBFirmware:
    
    # Raspberry Pi i2c Bus port
    rpi_i2cbus = 1
    # Containers for before and after fw versions
    old_fw = ""
    new_fw = ""
    # Settings from the settings file
    expected_fw = ""
    fw_file = ""
    i2c_address = ""
    # i2c Bus handler
    i2cbus = None

    def __init__(self, settings_file) -> None:
        
        # Already validated, just double verification...
        if (os.path.isfile(settings_file)):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        else:
            print("ERROR:\tConfiguration File does not exist")
            raise FileNotFoundError
        try: 
            # Read settings from the config file
            self.expected_fw = settings['expected_fw']
            self.fw_file = settings['fw_file']
            self.i2c_address = settings['i2c_default_add']
            # Verify that FW File specified in settings file works
            if (not os.path.isfile(self.fw_file)):
                print("ERROR:\tFirmware File does not exist")
                raise FileNotFoundError
        except:
            print("ERROR:\tWrong Configuration settings")
            raise FileExistsError
        pass
    
    # Implement a timeout for the retimer
    def validate_i2c_host_retimer(self) -> int:
        # check i2c comm, read 0x0 => 0x18
        retdata = self.i2cbus.read_i2c_block_data(self.i2c_address, 0, 1)
        # Wait for retimer to be active
        while len(retdata) == 0:
            time.sleep(0.01)
            retdata = self.i2cbus.read_i2c_block_data(self.i2c_address, 0, 1)
        return retdata

    def __del__(self):
        self.i2cbus.close()
        print("Event:\tClosing i2c Bus")

    def __get_current_fw(self) -> list:
        self.i2cbus = SMBus(self.rpi_i2cbus)
        self.i2cbus.open(self.rpi_i2cbus)
        time.sleep(0.5)
        self.i2cbus.write_i2c_block_data(self.i2c_address, 127, [3])
        # Validate retimer host 0x18
        retimer = self.validate_i2c_host_retimer()
        time.sleep(0.5)
        self.i2cbus.write_i2c_block_data(self.i2c_address, 127, [3])
        fw = self.i2cbus.read_i2c_block_data(self.i2c_address, 39, 2)
        fw_str = "{}.{}".format(fw[0], fw[1])
        print("Event:\tFirmware Version before Upgrade: {}".format(fw_str))
        return [fw_str, retimer]
    
    def fw_upgrade(self) -> list:
        # OpenOCD Command example (pending to change the interface)
        '''
        openocd -f interface/raspberrypi-swd.cfg -f target/rp2040.cfg -c "program i2c_comm.hex verify reset exit"

        '''
        # Define the OpenOCD command to run
        cmd = 'openocd -f interface/raspberrypi-swd.cfg -f target/rp2040.cfg -c "program {} verify reset exit"'.format(self.fw_file)
        print("Event:\tTrying to program UUT with the following commands:")
        print(cmd)
        # Run the OpenOCD command and capture the output
        try:
            output = subprocess.check_output(cmd, shell=True)
            # Print the output
            print(output)
            #prog_completed = output.find("Programming Finished")
            #verified = output.find("Verified OK")
            #reset = output.find("Resetting Target")
            print("Event:\tSuccessfull Programming")
            out_list = [True, True, True]
        except:
            print("ERROR:\tUnable to Load FW into UUT")
            out_list = [False, False, False]

        return out_list

    def fw_verification(self) -> list:
        [fw_str, retimer] = self.__get_current_fw()
        
        if (fw_str != self.expected_fw):
            self.old_fw = fw_str
            # FW Missmatch, trying to upgrade
            self.i2cbus.close()
            # Try to upgrade the firmware via OpenOCD and SWD Protocol
            [prog, verify, reset] = self.fw_upgrade()
            if (prog and verify):
                time.sleep(1)
                # Try to reach the uC again via i2c
                self.i2cbus.open(self.rpi_i2cbus)
                time.sleep(1)
                # Read new FW Version
                [fw_str, retimer] = self.__get_current_fw()
            else:
                print("FAIL:\tFW Upgrade not completed")
                fw_str = "ERROR"
                retimer = "ERROR"
        
        return [fw_str, retimer]






