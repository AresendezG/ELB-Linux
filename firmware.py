from smbus2 import SMBus
from gpio_ctrl import GPIO_CONTROL
from log_management import LOG_Manager, MessageType
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
    log_mgr = None

    def __init__(self, settings:dict, gpio_ctrl_handler:GPIO_CONTROL, log_handler: LOG_Manager) -> None:
        
        # Pass log handler to local control
        self.log_mgr = log_handler
        try: 
            # Settings coming from the TCP Client or the locals settins.json file
            self.expected_fw = settings['expected_fw']
            self.fw_file = settings['fw_file_path'] + settings['fw_file']
            self.i2c_address = settings['i2c_default_add']
            # Verify that FW File specified in settings file works
            if (not os.path.isfile(self.fw_file)):
                self.log_mgr.print_message("ERROR: Firmware File does not exist", MessageType.FAIL, True)
                self.log_mgr.print_message("Raising a FileNotFound Exception and terminating Execution", MessageType.WARNING, True)
                raise FileNotFoundError
        except:
            # Config settings are invalid, terminate execution
            self.log_mgr.print_message("ERROR:\t Wrong or Invalid Configuration Settings", MessageType.FAIL, True)
            self.log_mgr.print_message("Terminating Execution", MessageType.WARNING, True)
            raise FileExistsError
        # Pass the handler of GPIOs to the local gpioctrl 
        self.gpioctrl = gpio_ctrl_handler
        self.gpioctrl.config_pins_todefault()
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
        try:
            self.i2cbus.close()
            print("Event:\tClosing i2c Bus")
        except AttributeError:
            pass
        except:
            print("Error during i2c Bus shutdown, FirmwareLoader Module")


    def __get_current_fw(self) -> list:
        self.i2cbus = SMBus(self.rpi_i2cbus)
        self.i2cbus.open(self.rpi_i2cbus)
        # UUT Readiness
        time.sleep(2)
        self.i2cbus.write_i2c_block_data(self.i2c_address, 127, [3])
        # Validate retimer host 0x18
        retimer = self.validate_i2c_host_retimer()
        time.sleep(0.5)
        self.i2cbus.write_i2c_block_data(self.i2c_address, 127, [3])
        fw = self.i2cbus.read_i2c_block_data(self.i2c_address, 39, 2)
        fw_str = "{}.{}".format(fw[0], fw[1])
        self.log_mgr.print_message("Firmware Version before Upgrade: {}".format(fw_str), MessageType.EVENT, True)
        return [fw_str, retimer]
    

    def __wait_for_retimer(self):
        print("Wait for Retimer: ")
        counter = 0
        timeout = 10
        # Wait for Retimer to finish upgrade
        try:
            retdata = self.i2cbus.read_block_data(self.i2c_address, 3, 1)
            while ((retdata[0] & 0x0e) == 0 and counter < timeout):
                GPIO_CONTROL.wait_effect(timeout=1, printmsg=False)
                retdata = self.i2cbus.read_block_data(self.i2c_address, 3, 1)
                #print(retdata[0] & 0x0e)
                counter = counter+1
        except:
            return


    # Requires the settings file to determine the filename of the FW to upgrade
    def __fw_upgrade(self) -> list:
        # OpenOCD Command example (pending to change the interface)
        '''
        # Program cmd for the RPI Pico
        openocd -f interface/raspberrypi-swd.cfg -f target/rp2040.cfg -c "program i2c_comm.hex verify reset exit"
        # Dump Flash from the ELB
        openocd -f interface/raspberrypi-swd.cfg -f target/psoc6.cfg -c init -c "reset halt" -c "flash read_bank 0 Firmware_Dump_full.hex 0 0x100000" -c "reset" -c shutdown
        # Program fw on the ELB
        openocd -f interface/raspberrypi-swd.cfg -f target/psoc6.cfg -c init -c "reset halt" -c "program ELB_FWRelease113_ID.hex reset exit"
        '''
        # Define the OpenOCD command to run
        cmd = f'openocd -f interface/raspberrypi-swd.cfg -f target/psoc6.cfg -c init -c "reset" -c "program {self.fw_file} reset exit"'
        self.log_mgr.log_to_file(f"Attempt to program UUT with: {self.fw_file}")
        self.log_mgr.log_to_file(cmd)
        # Run the OpenOCD command and capture the output
        try:
            output = subprocess.check_output(cmd, shell=True)
            self.log_mgr.print_message("Successfull Programming", MessageType.EVENT, True)
            out_list = True
        except:
            self.log_mgr.print_message("ERROR:\t Unable to Load FW into UUT", MessageType.FAIL, True)
            out_list = False

        # Post programming
        if (out_list):
            self.log_mgr.log_to_file("Programming Complete. Waiting for post-programming")
            # Hold the reset pin for at least 2 seconds
            self.gpioctrl.reset_uut(2)
            # Needs at least 10 seconds to fully upgrade
            GPIO_CONTROL.wait_effect(10)
            # Try to reach the uC again via i2c
            self.i2cbus.open(self.rpi_i2cbus)
            self.log_mgr.log_to_file("Opening i2c Bus after Upgrade")
            GPIO_CONTROL.wait_effect(10)
            # wait for retimer to be ready
            self.__wait_for_retimer()            
        return out_list

    def fw_verification(self) -> list:
        try:
            [fw_str, retimer] = self.__get_current_fw()
            self.old_fw = fw_str
            if (fw_str != self.expected_fw):
                # FW Missmatch, trying to upgrade:
                self.i2cbus.close()
                # Try to upgrade the firmware via OpenOCD and SWD Protocol
                prog = self.__fw_upgrade()
                if (prog):
                    # Read new FW Version
                    [fw_str, retimer] = self.__get_current_fw()
                else:
                    self.log_mgr.print_message("FAILURE:\t Unable to verify FW Version", MessageType.FAIL, True)
                    fw_str = "ERROR"
                    retimer = "ERROR"
            return [fw_str, retimer]
        except OSError as error:
            self.log_mgr.log_to_file("OSERROR Exception triggered, most likely unable to read FW version")
            self.log_mgr.log_to_file(f"Exception number: {error.errno}")
            self.log_mgr.log_to_file(f"Exception Filename: {error.filename}")
            # Retrying to program the FW anyways
            self.log_mgr.log_to_file("Forcing SWD Programming")
            # Old FW unable to be read
            self.old_fw = "0.0"
            if (self.__fw_upgrade()):
                [fw_str, retimer] = self.__get_current_fw()
            else:
                fw_str = "ERROR"
                retimer = "ERROR"

        return [fw_str, retimer]


    





