import time
import random
import itertools
from results_processing import ResultsManager as FormatSN
from i2c_types import GPIO_PINS
from gpio_ctrl import GPIO_CONTROL
from i2c_types import LedMode, MOD_Rates, PowerLoad_Modes, ELB_GPIOs
from i2c_types import CurrentSensors, TempSensors, VoltageSensors
from log_management import LOG_Manager, MessageType
from firmware import ELBFirmware
from smbus2 import SMBus



class ELB_i2c:
    #-- Class variables definitions
    # Define i2c Bus as Main
    DEVICE_BUS = 1
    # Define ELB default i2c Address:
    DEV_ADD = 0x50
    # Define bus object
    bus = None
    # Define GPIO Controller
    gpioctrl = None
    # Determine if UUT is in high power mode
    high_power = False
    # Determine if UUT has started the PRBS Routine
    prbs_started = False
    cleanup_run = False

    # interactive 
    led_status = itertools.cycle([[LedMode.GREEN_ON, "LED GREEN ON"], [LedMode.RED_FLASH, "LED FLASH MODE"], [LedMode.RED_ON, "LED RED ON"], [LedMode.LED_OFF, "LED OFF"]])

    # UUT Variables
    # Expected SN, PN and RV based on User Input
    serial = "" 
    part_number = ""
    rev = ""
    sn_defined = False

    # SN in UUT's memory (used for FW Upgrade)
    uut_read_sn = ""
    #function declaration

    def __init__(self, prbs_modrate: MOD_Rates, i2c_add: int, gpio_ctrl_handler:GPIO_CONTROL, log_handler:LOG_Manager, configs:dict = None) -> None:
        self.log_mgr = log_handler
        self.log_mgr.print_message("Initialize SMBus", MessageType.EVENT)
        self.bus = SMBus(self.DEVICE_BUS)
        self.log_mgr.print_message("i2c Communication with host at address: {}".format(self.DEV_ADD), MessageType.EVENT)
        # Start object to handle RPI GPIOs
        self.gpioctrl = gpio_ctrl_handler
        self.log_mgr.print_message("GPIO Control Started",MessageType.EVENT)
        # Define the PRBS Mod Rate from the program manager as it is a setting
        self.prbs_modrate = prbs_modrate 
        # Define i2c address from the program manager 
        self.DEV_ADD = i2c_add
        # Configurations dict read from the configs file or passed by the client
        self.configs = configs
        pass
    
    # Cleanup
    def __del__(self):
        self.uut_cleanup()

    #----- Internal functions------------
    # Function to test the temperature 
    def __ReadTempFnc(self, regaddress: int) -> float:
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, regaddress, 2)
        retdata = [x for x in retdata]
        temp = ((retdata[0]<<8) + retdata[1])/256 #calculate temp value from sensor 
        return temp
    
    # Function to read voltages
    def __ReadVoltageFnc(self, regaddress: int) -> float:
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, regaddress, 2)
        retdata = [x for x in retdata]
        vcc = ((retdata[0]<<8) + retdata[1])*0.0001 # calculate voltage from the sensor
        return vcc
    
    def __ReadEPPS_Data(self, regaddress: int, data_size: int) -> int:
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, regaddress, data_size)
        retdata = [x for x in retdata]
        val = 0
        for x in retdata:
            val = (val<<8) + x
        return val
    
    def __ReadCurrentSensor(self, regaddress: int) -> float:
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, regaddress, 2)
        retdata = [x for x in retdata]
        curr = ((retdata[0]<<8) + retdata[1])*0.001
        return curr
    
    def __SetPL_ReadSensor(self, powermode: PowerLoad_Modes) -> list:
        # Write the PowerLoad setting to UUT
        self.bus.write_i2c_block_data(self.DEV_ADD, 135, powermode)
        time.sleep(2) # wait 2 seconds for sensor stabilization
        i_vcc = self.__ReadCurrentSensor(CurrentSensors.VCC)
        i_vcc_rx = self.__ReadCurrentSensor(CurrentSensors.VCC_RX)
        i_vcc_tx = self.__ReadCurrentSensor(CurrentSensors.VCC_TX)
        return [i_vcc, i_vcc_rx, i_vcc_tx]
    
    def __TestGPIO_ELB_Out(self, elb_pin: ELB_GPIOs, fixt_pin: GPIO_PINS) -> bool: #Returns pass/fail for both Low and High status
        # enable/disable the ELB GPIO
        self.bus.write_i2c_block_data(self.DEV_ADD, 142, elb_pin)
        time.sleep(0.05)
        # read RPI gpio status
        gpio_status = self.gpioctrl.read_gpio(fixt_pin)
        return gpio_status
    
    def __TestGPIO_ELB_In(self, elb_pin: ELB_GPIOs, fixt_pin: GPIO_PINS) -> bool:
        # enable/disable the RPi GPIOs
        self.gpioctrl.write_gpio(fixt_pin, elb_pin[0])
        time.sleep(0.01)
        # read ELB gpio status
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, ELB_GPIOs.GPIO_IN_REG, 1)
        retdata = [x for x in retdata]
        gpio_status = retdata[0]&elb_pin[1]
        return gpio_status
    
    def __led_user_input(self) -> LedMode:

        print("Inspect the LED and input the corresponding option:")
        self.log_mgr.print_led_menu()
        print("Press c to fail the test")
        u_input = input("Select: ")
        while (u_input != 'c'):
            if (u_input.lower() == 'f'):
                return LedMode.BOTH_FLASH
            if (u_input.lower() == 'o'):
                return LedMode.LED_OFF
            if (u_input.lower() == 'g'):
                return LedMode.GREEN_ON
            if (u_input.lower() == 'r'):
                return LedMode.RED_ON
            print('Wrong Option Selected. Press c to Fail the test')
            self.log_mgr.print_led_menu()
              
        return LedMode.BOTH_ON
        
    def __disable_prbs(self):
        print("Event:\t Shutdown PRBS")
        # write page 0x13
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0x13])
        # disable host side gen
        self.bus.write_i2c_block_data(self.DEV_ADD, 144, [0x00])
        # disable host side chk
        self.bus.write_i2c_block_data(self.DEV_ADD, 160, [0x00])
        pass

    def __reset_powerloads(self):
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0x03])
        print("Event: \tSet Loads OFF and LowPower Mode")
        self.bus.write_i2c_block_data(self.DEV_ADD, 26, [0x30])
        self.bus.write_i2c_block_data(self.DEV_ADD, 135, PowerLoad_Modes.LOADS_OFF)
        pass

    def __collect_prbs_results(self) -> list:
        self.log_mgr.print_message("Report PRBS Results", MessageType.EVENT)
        lol_status = [-1] * 8
        # get prbs results
        # write page 0x14            
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0x14])
        # diag sel input lan ber
        self.bus.write_i2c_block_data(self.DEV_ADD, 128, [0x00])
        time.sleep(1)
        self.bus.write_i2c_block_data(self.DEV_ADD, 128, [0x01])
        time.sleep(8)
        # read host chk lol
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 138, 1)
        retdata = [x for x in retdata]
        hostchklol = retdata[0]
        print("host chk lol 0x{:2x}\n".format(hostchklol))
        # read host chk prbs
        hostchkber = [0.0] * 8
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 192, 16)
        retdata = [x for x in retdata]

        for ln in range(8):
            u16 = (retdata[ln*2] << 8) | retdata[(ln*2)+1]
            s = (u16 & 0xf800)>>11
            man = u16 & 0x07ff
            # hostchkber is an array that holds the Bit error rate
            if man == 0:
                hostchkber[ln] = ["ber_{}".format(ln), 0.0]
            else:
                hostchkber[ln] = ["ber_{}".format(ln), man * (10 ** (s-24))]
            print("Lane: {}\tBER: {} {} {}\tman: {}\ts: {}".format(ln,hostchkber[ln][1],retdata[ln*2],retdata[(ln*2)+1],man,s))
            lol_status[ln] = ["LOL_{}".format(ln), hostchklol & (1<<ln)]
            
        # Return a single list
        return (lol_status + hostchkber)

    # ------ Sequences (can be called from outside the object) ---------------

    # Define the class variables only, no inteface with the UUT yet
    def define_uut_sn(self, uut_data:list) -> None:
        self.serial = uut_data[0]
        self.part_number = uut_data[1]
        self.rev = uut_data[2]
        self.sn_defined = True
        return

    # Fnc to handle the firmware upgrade of the UUT
    def run_firmware_upgrade(self) -> list:
        self.log_mgr.print_message("Running UUT Firmware Verification", MessageType.EVENT, True)
        self.bus.close()
        fwhandler = ELBFirmware(self.configs, self.gpioctrl, self.log_mgr)
        # Verify the firmware version and try to upgrade it
        [fw_ver, retimer] = fwhandler.fw_verification()
        self.log_mgr.log_to_file("FW Version Before Upgrade: {}".format(fwhandler.old_fw))
        self.log_mgr.log_to_file("FW Version After Upgrade: {}".format(fw_ver))
        self.log_mgr.log_to_file("Retimer HostAddress: {}".format(retimer))
        self.bus.open(self.DEVICE_BUS)
        # Return old FW Version as float to allow any version to be reported 
        return [["fw_before", float(fwhandler.old_fw)], ["fw_after", fw_ver], ["ret_host", retimer[0]]]
    
    def prog_uut_sn(self) -> list:
        # This function reads the OLD sn if any and Programs the new SN. 
        if(self.sn_defined):
            self.log_mgr.print_message("Serial Number Programming", MessageType.WARNING, True)
            # Read the old SN (if any)
            old_uut_data = self.uut_serial_num()
            old_sn_str:str
            old_sn_str = old_uut_data[0][1]
            # Data in the SN register is Juniper format, thus this is a re-test
            if (old_sn_str[0:2] == "ZP"):
                self.log_mgr.print_message("UUT has a valid SN already Programmed", MessageType.WARNING, True)
                self.log_mgr.print_message("Old UUT SN: {}".format(old_sn_str), MessageType.WARNING, True)
            self.write_uut_sn(self.serial, self.part_number, self.rev)
            self.log_mgr.print_message(f"New SN: {self.serial}", MessageType.EVENT, True)
            self.log_mgr.print_message(f"Revision: {self.rev}", MessageType.EVENT, True)
            self.log_mgr.print_message(f"Part Number: {self.part_number}", MessageType.EVENT, True)
            return [["old_sn", old_sn_str],["prog_serial", self.serial],["prog_partnum", self.part_number],["prog_rev", self.rev]]
        else:
            print("Error: Serial Number not been defined")
            raise KeyError

    def uut_serial_num(self) -> list:
        self.log_mgr.print_message("Readback of UUT SN", MessageType.EVENT, True)
        # write page 0
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0])
        # read SN from reg166  
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 166, 16)
        serial_array = [x for x in retdata] #array that holds the serialnumber
        serial_str = "".join(chr(x) for x in serial_array)
        # read PN from reg148
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 148, 16)
        pn_array = [x for x in retdata] #array that holds the part number
        part_number = "".join(chr(x) for x in pn_array)
        # read revision from reg164
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 164, 2)
        revision = [x for x in retdata] # array that holds the rev number
        rev_str = "".join(chr(x) for x in revision)
        # Read PN-2 from register 224. Per Write sn algorithm, it will be only 18 bytes
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 224, 18)
        pn2 = [x for x in retdata] # array that holds the rev number
        pn2_str = "".join(chr(x) for x in pn2)
        print("Part_Number2 : "+pn2_str)
        # This assignation is used only for firmware-upgrade only scripts (reads from UUT without modifying it)
        self.uut_read_sn = serial_str
        return [["serial",serial_str], ["part_num",part_number], ["rev",rev_str], ["pn2_str", pn2_str]]
    
    
    def write_uut_sn(self, serial: str, part_number: str, rev: str):
        self.log_mgr.print_message("Writing SN to ELB", MessageType.EVENT)
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])
        # write password
        self.bus.write_i2c_block_data(self.DEV_ADD, 122, [0, 0, 16, 17])
        # write page 0
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0]) 
    
        # Format serial string to 16 bytes
        serial = FormatSN.trim_str(serial, 16)
        # Convert from string to list of hex bytes
        serial_list = [ord(x) for x in serial]
        self.bus.write_i2c_block_data(self.DEV_ADD, 166, serial_list)
        
        # Format Part Number string to 16 bytes
        part_number = FormatSN.trim_str(part_number, 16)
        # Convert from string to list of hex bytes
        part_number_hex = [ord(x) for x in part_number]
        self.bus.write_i2c_block_data(self.DEV_ADD, 148, part_number_hex) 
        
        # Format REV to 2 bytes only        
        rev = FormatSN.trim_str(rev, 2)
        # convert rev str into list of bytes
        rev_hex = [ord(x) for x in rev]
        self.bus.write_i2c_block_data(self.DEV_ADD, 164, rev_hex)
        # Format PartNumber 2 (includes rev) and return a list of bytes
        pn2_hex = FormatSN.create_pn2(part_number, rev)
        #print(pn2_hex)
        self.bus.write_i2c_block_data(self.DEV_ADD, 224, pn2_hex) 
        # save sn, write password
        self.bus.write_i2c_block_data(self.DEV_ADD, 122, [0, 0, 0, 16])
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])
        time.sleep(1)
        print("Event:\tReset UUT for 2 seconds")
        self.gpioctrl.reset_uut(2)
        # Let UUT some recovery time
        print("Waiting 5 Seconds for recovery")
        time.sleep(5)
        pass

    def uut_fw_version(self) -> list:

        self.log_mgr.print_message("Get UUT FW Version", MessageType.EVENT)
        # Write Page 3
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])        
        # Retrieve data from registers
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 182, 4)
        retdata = [x for x in retdata]
        dsp_ver = ((retdata[0]<<24) + (retdata[1]<<16) + (retdata[2]<<8) + retdata[3])
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 186, 4)
        retdata = [x for x in retdata]
        dsp_id = ((retdata[0]<<24) + (retdata[1]<<16) + (retdata[2]<<8) + retdata[3])
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 190, 1)
        retdata = [x for x in retdata]
        dsp_rev = retdata[0]
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 39, 2)
        fwver = retdata  
        print("DSP Version: ",dsp_ver)
        print("DSP ID: ",dsp_id)
        print("DSP Rev: ",dsp_rev)
        print("FW Version: {}.{}".format(fwver[0], fwver[1]))
        fwver_str = "{}.{}".format(fwver[0], fwver[1])
        return [["dsp_version",dsp_ver], 
                ["dsp_id",dsp_id], 
                ["dsp_rev",dsp_rev], 
                ["fwver",fwver_str]]

    def gpio_all(self) -> list: #returns an array of the GPIO test results
        self.log_mgr.print_message("Test All GPIOs",MessageType.EVENT)
        # Write Page 3
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])     
        self.bus.write_i2c_block_data(self.DEV_ADD, 143, [0x01])
        time.sleep(1)
        # --- Outputs
        pin_intl_low        = self.__TestGPIO_ELB_Out(ELB_GPIOs.INT_L_LOW, GPIO_PINS.INT_L)
        pin_intl_high       = self.__TestGPIO_ELB_Out(ELB_GPIOs.INT_L_HIGH, GPIO_PINS.INT_L)
        pin_presentl_low    = self.__TestGPIO_ELB_Out(ELB_GPIOs.PRESENT_L_LOW, GPIO_PINS.PRESENT_L)
        pin_presentl_high   = self.__TestGPIO_ELB_Out(ELB_GPIOs.PRESENT_L_HIGH, GPIO_PINS.PRESENT_L)
        # -- Inputs
        pin_modsel_low  = self.__TestGPIO_ELB_In(ELB_GPIOs.MODSEL_LOW, GPIO_PINS.MODSEL)
        pin_modsel_high = self.__TestGPIO_ELB_In(ELB_GPIOs.MODSEL_HIGH, GPIO_PINS.MODSEL)
        pin_lpmode_low  = self.__TestGPIO_ELB_In(ELB_GPIOs.LPMODE_LOW, GPIO_PINS.LPMODE)
        pin_lpmode_high = self.__TestGPIO_ELB_In(ELB_GPIOs.LPMODE_HIGH, GPIO_PINS.LPMODE)
        pin_resetl_low  = self.__TestGPIO_ELB_In(ELB_GPIOs.RESET_L_LOW, GPIO_PINS.RESET_L)
        pin_resetl_high = self.__TestGPIO_ELB_In(ELB_GPIOs.RESET_L_HIGH, GPIO_PINS.RESET_L)
        results = [ 
                   ["intl_low",pin_intl_low],
                   ["intl_high",pin_intl_high], 
                   ["presentl_low",pin_presentl_low], 
                   ["presentl_high",pin_presentl_high], 
                   ["modsel_low",pin_modsel_low], 
                   ["modsel_high",pin_modsel_high], 
                   ["lpmode_low",pin_lpmode_low], 
                   ["lpmode_high",pin_lpmode_high], 
                   ["resetl_low",pin_resetl_low], 
                   ["resetl_high",pin_resetl_high]]
        # Configure the pins back to the expected mode
        self.gpioctrl.config_pins_todefault()
        # no test mode
        self.bus.write_i2c_block_data(self.DEV_ADD, 143, [0x00])
        return results

    def leds_verification_static(self):
        self.log_mgr.print_message("Running LED Sequence", MessageType.EVENT)
        # write page 3
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])
        # flash LEDs
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.BOTH_FLASH)
        time.sleep(5)
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.GREEN_ON)
        time.sleep(5)
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.RED_ON)
        time.sleep(5)
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.LED_OFF)

    def leds_verification_random(self) -> list:
        self.log_mgr.print_message("Running LED Sequence Interactive", MessageType.EVENT, True)
        seq_results = []
        print("Sequence Interactive Mode. Operator Input Required")
        # write page 3
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])

        # create a list of possible LED behaviors
        led_possible_status = [[LedMode.LED_OFF,"led_off"], [LedMode.GREEN_ON,"led_green"], [LedMode.RED_ON,"led_red"], [LedMode.BOTH_FLASH,"led_flash"]]
        # Shuffle the possible states 
        random.shuffle(led_possible_status)

        for status in range(len(led_possible_status)):
            # Change status of the LED
            self.bus.write_i2c_block_data(self.DEV_ADD, 129, led_possible_status[status][0])
            user_input = self.__led_user_input()
            # Ask the user to inspect the LED
            if (user_input == led_possible_status[status][0]):
                result = "PASS"
            else:
                result = "FAIL"
            self.log_mgr.log_to_file(f"LED Test {led_possible_status[status][1]} User Input: {user_input} Expected: {led_possible_status[status][0]}")
            # Append result for each of the possible status to the results list
            seq_results.append([led_possible_status[status][1], result])
        # Turn off LED
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.LED_OFF)
        return seq_results


    def led_remote(self) -> list:
        current_led_status = next(self.led_status)
        # Enable cms
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])
        # flash LEDs
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, current_led_status[0])
        print(current_led_status[0])
        return [["LED", current_led_status[1]],[None, None]]


    def volt_sensors(self) -> list:
        self.log_mgr.print_message("Voltage Sensor Reading", MessageType.EVENT, True)
        # write page 3
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])
        vcc = self.__ReadVoltageFnc(VoltageSensors.VCC)
        print("Reading VCC Voltage: {:.4f}".format(vcc))
        vcctx = self.__ReadVoltageFnc(VoltageSensors.VCCTX)
        print("Reading VCC_TX Voltage: {:.4f}".format(vcctx))
        vccrx = self.__ReadVoltageFnc(VoltageSensors.VCCRX)
        print("Reading VCC_RX Voltage: {:.4f}".format(vccrx))
        vbatt = self.__ReadVoltageFnc(VoltageSensors.VBATT)
        print("Reading VBATT Voltage: {:.4f}".format(vbatt))
        return [["vcc",vcc], ["vcc_tx",vcctx], ["vcc_rx",vccrx], ["vbatt",vbatt]]

    def temp_sensors(self) -> list:
        self.log_mgr.print_message("Temp Sensors Reading",MessageType.EVENT, True)
        # write page 3
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])
        uc_temp = self.__ReadTempFnc(TempSensors.UC)
        print("Temp Sensor uC: {:.4f}".format(uc_temp))
        rt_temp = self.__ReadTempFnc(TempSensors.RTMR)
        print("Temp Sensor RTMR: {:.4f}".format(rt_temp))
        pcb_rt_temp = self.__ReadTempFnc(TempSensors.PCB_RT)
        print("Temp Sensor RTMR PCB {:.4f}".format(pcb_rt_temp))
        pcb_pl_temp = self.__ReadTempFnc(TempSensors.PCB_PL)
        print("Temp Sensor PowerLoad PCB {:.4f}".format(pcb_pl_temp))
        shell_f_temp = self.__ReadTempFnc(TempSensors.SHELL_F)
        print("Temp Shell F {:.4f}".format(shell_f_temp))       
        shell_r_temp = self.__ReadTempFnc(TempSensors.SHELL_R)
        print("Temp Shell F {:.4f}".format(shell_r_temp))
        return [["uc_temp",uc_temp], ["retimer_temp",rt_temp], ["pcb_rt",pcb_rt_temp], ["pcb_pl",pcb_pl_temp], ["shell_f",shell_f_temp], ["shell_r",shell_r_temp]]  
    
    def epps_signal(self) -> list:
        self.log_mgr.print_message("Measuring ePPS Signal",MessageType.EVENT, True)
        # write page 3
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])
        # ePPS Start capture:
        self.bus.write_i2c_block_data(self.DEV_ADD, 164, [0x01])
        time.sleep(5)
        retdata=[0]
        while retdata[0] == 0:
            retdata = self.bus.read_i2c_block_data(self.DEV_ADD,156,1)
            retdata = [x for x in retdata]
        # Get ePPS results
        freq = self.__ReadEPPS_Data(157, 4)
        duty_percent = self.__ReadEPPS_Data(161, 1)
        duty_ms = self.__ReadEPPS_Data(162, 2)
        return [["freq",freq], ["duty_percent",duty_percent], ["duty_ms",duty_ms]]

    def ins_count(self) -> list:
        self.log_mgr.print_message("Insertion Counter", MessageType.EVENT, True)
        # Read the insertion counter
        # write page 0x03
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0x03])
        # read accum
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 132, 2)
        retdata = [x for x in retdata]
        ins_accum = ((retdata[0]<<8) + retdata[1])
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 131, 1)
        retdata = [x for x in retdata]
        ins_nibb = retdata[0]
        return [["ins_accum",ins_accum], ["ins_nible",ins_nibb]]

    def prbs_start(self) -> list: 
        # Check first if UUT is in High Power mode
        if (not self.high_power):
            print("Warning: \tUUT not in HighPower")
            self.bus.write_i2c_block_data(self.DEV_ADD, 135, PowerLoad_Modes.LOADS_OFF)
            # put in hi power mode
            print("Event: \tSetting up Hi Power mode")
            self.bus.write_i2c_block_data(self.DEV_ADD, 26, [0x20])
            self.high_power = True
        # start prbs!!!!!!!!!!!!!!!!!!!!
        self.log_mgr.print_message("Start of PRBS", MessageType.EVENT, True)
        # write page 0x10
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0x10])
        # Write command to set mod mode
        self.bus.write_i2c_block_data(self.DEV_ADD, 145, self.prbs_modrate)
        eqlns = [[6,0,3],[6,0,3],[6,0,3],[6,0,3],[6,0,3],[6,0,3],[6,0,3],[6,0,3]]
        # set working eqs
        for lns2 in range(4):
            # set pre
            self.bus.write_i2c_block_data(self.DEV_ADD, 162+lns2, [eqlns[lns2*2][0]+(eqlns[lns2*2+1][0]<<4)])
            # set post
            self.bus.write_i2c_block_data(self.DEV_ADD, 166+lns2, [eqlns[lns2*2][1]+(eqlns[lns2*2+1][1]<<4)])
            # set amp
            self.bus.write_i2c_block_data(self.DEV_ADD, 170+lns2, [eqlns[lns2*2][2]+(eqlns[lns2*2+1][2]<<4)])
         # enable cfg
        self.bus.write_i2c_block_data(self.DEV_ADD, 144, [0xff])
        time.sleep(5)
        # write page 0x13
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0x13])
        self.bus.write_i2c_block_data(self.DEV_ADD, 180, [0, 0, 0, 0])
        # write page 0x13
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0x13])
        # config host side gen
        self.bus.write_i2c_block_data(self.DEV_ADD, 144, [0, 0, 0, 0])        
        # config host side gen prbs31
        self.bus.write_i2c_block_data(self.DEV_ADD, 148, [0x11, 0x11, 0x11, 0x11])
        # enable host side gen
        self.bus.write_i2c_block_data(self.DEV_ADD, 144, [0xff])
        # config host side chk
        self.bus.write_i2c_block_data(self.DEV_ADD, 160, [0, 0, 0, 0])
        # config host side chk prbs31
        self.bus.write_i2c_block_data(self.DEV_ADD, 164, [0x11, 0x11, 0x11, 0x11])
        # enable host side chk
        self.bus.write_i2c_block_data(self.DEV_ADD, 160, [0xff])
        # diag sel
        # write page 0x14
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0x14])
        # diag sel input lan ber
        self.bus.write_i2c_block_data(self.DEV_ADD, 128, [0x00])
        time.sleep(1)
        self.bus.write_i2c_block_data(self.DEV_ADD, 128, [0x01])
        time.sleep(5)
        # read host chk lol
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 138, 1)
        retdata = [x for x in retdata]
        hostchklol = retdata[0]
        print("host check lol 0x{:2x}\n".format(hostchklol))
        self.prbs_started = True
        return [["host_check", int(hostchklol)], ["NDF", None]]

    def prbs_results(self) -> list:
        # Can only return valid data if the PRBS has started previously
        if (self.prbs_started):
            prbs_results = self.__collect_prbs_results()
        else:
            print("Warning: \tNo Previous PRBS Start. Starting it now")
            self.prbs_start()
            print("Event:\tWaiting 60 seconds for PRBS Results")
            time.sleep(60)
            prbs_results = self.__collect_prbs_results()        
        return prbs_results

    def power_loads(self) -> list:
        self.log_mgr.print_message("Power Load Test", MessageType.EVENT, True)
        # load/current all on/off
        # all loads off
        # put in low power mode
        print("Event: \tPower Load OFF and LowPower Mode")
        self.bus.write_i2c_block_data(self.DEV_ADD, 26, [0x30])
        self.bus.write_i2c_block_data(self.DEV_ADD, 135, PowerLoad_Modes.LOADS_OFF)
        time.sleep(5)
        # get base vcccurr
        # read currents
        print("Event: \tReading Base Current:")
        i_vcc_base = self.__ReadCurrentSensor(174)
        print("Base Current: {:.4f}".format(i_vcc_base))
        # Load settings #1
        [i_vcc_0p8, i_vcc_rx_4p0, i_vcc_tx_1p6] = self.__SetPL_ReadSensor(PowerLoad_Modes.LOADS_1)
        # Load settings #2
        [i_vcc_1p6, i_vcc_rx_1p6, i_vcc_tx_4p0] = self.__SetPL_ReadSensor(PowerLoad_Modes.LOADS_2) 
        # Load settings #3
        [i_vcc_3p2, i_vcc_rx_3p2, i_vcc_tx_0p8] = self.__SetPL_ReadSensor(PowerLoad_Modes.LOADS_3)   
        # Load settings $4
        [i_vcc, i_vcc_rx_0p8, i_vcc_tx_3p2] = self.__SetPL_ReadSensor(PowerLoad_Modes.LOADS_4)
        # all loads off
        self.bus.write_i2c_block_data(self.DEV_ADD, 135, PowerLoad_Modes.LOADS_OFF)
        # put in hi power mode
        print("Event: \tSetting up Hi Power mode")
        self.bus.write_i2c_block_data(self.DEV_ADD, 26, [0x20])
        time.sleep(10)
        self.high_power = True
        currents = [["i_vcc_base",i_vcc_base], ["i_vcc_0p8",(i_vcc_0p8-i_vcc_base)],   ["i_vcc_1p6",(i_vcc_1p6-i_vcc_base)],   ["i_vcc_3p2",(i_vcc_3p2 - i_vcc_base)],
                    ["i_rx_4p0",i_vcc_rx_4p0], ["i_rx_0p8",i_vcc_rx_0p8], ["i_rx_1p6",i_vcc_rx_1p6], ["i_rx_3p2",i_vcc_rx_3p2],
                    ["i_tx_4p0",i_vcc_tx_4p0], ["i_tx_0p8",i_vcc_tx_0p8], ["i_tx_1p6",i_vcc_tx_1p6], ["i_tx_3p2",i_vcc_tx_3p2]]        
        return currents

    def uut_cleanup(self) -> list:
        if (not self.cleanup_run):
            self.log_mgr.print_message("UUT Cleanup", MessageType.EVENT, True)
            try:
                self.__disable_prbs()
                self.__reset_powerloads()
                self.cleanup_run = True
                return ["cleanup", "done"]
            except:
                self.log_mgr.print_message("UUT Cleanup Failed. Verify system before Testing", MessageType.FAIL, True)
            pass
        else:
            return [None]


