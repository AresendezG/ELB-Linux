import asyncio
import time
from results_processing import ResultsManager as FormatSN
from i2c_types import GPIO_PINS
from gpio_ctrl import GPIO_CONTROL
from i2c_types import LedMode, MOD_Rates, PowerLoad_Modes, ELB_GPIOs
from i2c_types import CurrentSensors, TempSensors, VoltageSensors
from i2c_types import con_colors as MessageType
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

    #function declaration

    def __init__(self, prbs_modrate: MOD_Rates, i2c_add: int, gpio_ctrl_handler:GPIO_CONTROL) -> None:
        print("Event:\tInitialize SMBus")
        self.bus = SMBus(self.DEVICE_BUS)
        print("Event:\ti2c Communication with host at address: {}".format(self.DEV_ADD))
        # Start object to handle RPI GPIOs
        self.gpioctrl = gpio_ctrl_handler
        print("Event:\tGPIO Control Started")
        # Define the PRBS Mod Rate from the program manager as it is a setting
        self.prbs_modrate = prbs_modrate 
        # Define i2c address from the program manager 
        self.DEV_ADD = i2c_add
        pass
    
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
        time.sleep(0.01)
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
    
    def write_uut_sn(self, serial: str, part_number: str, rev: str):
        self.__print_messages(MessageType.WARNING,"Event:\tWriting SN to ELB")
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
        self.bus.write_i2c_block_data(self.DEV_ADD, 224, pn2_hex) 
        # save sn, write password
        self.bus.write_i2c_block_data(self.DEV_ADD, 122, [0, 0, 0, 16])
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])
        time.sleep(1)
        print("Event: \tReset UUT to Write SN and Wait 2 seconds")
        self.gpioctrl.reset_uut(2)
        # Let UUT some recovery time
        time.sleep(2)
        pass

    # ------ Sequences ---------------

    def uut_fw_version(self) -> list:
        # f"{bcolors.WARNING}Warning: No active frommets remain. Continue?{bcolors.ENDC}"
        # print(f"{con_colors.WARNING}Event: \tGet UUT FW Version {con_colors.ENDC}")
        self.__print_messages(MessageType.WARNING,"Event: \tGet UUT FW Version")
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


    # Full GPIO Sequence
    def gpio_all(self) -> list: #returns an array of the GPIO test results
        self.__print_messages(MessageType.WARNING,"Event: \tTest All GPIOs")
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
        results = [["intl_high",pin_intl_high], 
                   ["intl_low",pin_intl_low], 
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

    def leds_verification(self):
        self.__print_messages(MessageType.WARNING,"Event: \tRunning LED Sequence")
        # write page 3
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [3])
        # flash LEDs
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.BOTH_FLASH)
        time.sleep(5)
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.GREEN_ON)
        time.sleep(5)
        self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.RED_ON)
        time.sleep(5)
        #self.bus.write_i2c_block_data(self.DEV_ADD, 129, LedMode.LED_OFF)

    def volt_sensors(self) -> list:
        self.__print_messages(MessageType.WARNING,"Event: \tVoltage Sensor Reading")
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
        self.__print_messages(MessageType.WARNING,"Event: \tTemp Sensors Reading")
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
        self.__print_messages(MessageType.WARNING,"Event: \tMeasuring ePPS Signal")
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

    def uut_serial_num(self) -> list:
        self.__print_messages(MessageType.WARNING,"Event: \tReadback of UUT SN")
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
        # Read PN-2 from register 224
        retdata = self.bus.read_i2c_block_data(self.DEV_ADD, 224, 32)
        pn2 = [x for x in retdata] # array that holds the rev number
        pn2_str = "".join(chr(x) for x in pn2)
        #print("Serial Number: "+serial_str)
        return [["serial",serial_str], ["part_num",part_number], ["rev",rev_str], ["partnum2", pn2_str]]
    
    def ins_count(self) -> list:
        self.__print_messages(MessageType.WARNING,"Event: \tInsertion Counter")
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
        self.__print_messages(MessageType.WARNING,"Event: \tStart of PRBS")
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
        print("host chk lol 0x{:2x}\n".format(hostchklol))
        self.prbs_started = True
        return [None]

    def __collect_prbs_results(self) -> list:
        self.__print_messages(MessageType.WARNING,"Event: \tReport PRBS Results")
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
        # write page 0x13
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0x13])
        # disable host side gen
        self.bus.write_i2c_block_data(self.DEV_ADD, 144, [0x00])
        # disable host side chk
        self.bus.write_i2c_block_data(self.DEV_ADD, 160, [0x00])
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
            
        # write page 0x13
        self.bus.write_i2c_block_data(self.DEV_ADD, 127, [0x13])
        # disable host side gen
        self.bus.write_i2c_block_data(self.DEV_ADD, 144, [0x00])
        # disable host side chk
        self.bus.write_i2c_block_data(self.DEV_ADD, 160, [0x00])
        # Return a single list
        return (lol_status + hostchkber)

    def prbs_results(self) -> list:
        # Can only return valid data if the PRBS has started previously
        if (self.prbs_started):
            prbs_results = self.__collect_prbs_results()
        else:
            print("Warning: \tNo Previous PRBS Start. Starting it now")
            self.prbs_start()
            print("Event:\tWaiting 20 seconds for PRBS Results")
            time.sleep(20)
            prbs_results = self.__collect_prbs_results()        
        return prbs_results

    def power_loads(self) -> list:
        self.__print_messages(MessageType.WARNING, "Event: \tPower Load Test")
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
        currents = [["i_vcc_base",i_vcc_base], ["i_vcc_0p8",i_vcc_0p8], ["i_vcc_1p6",i_vcc_1p6], ["i_vcc_3p2",i_vcc_3p2],
                    ["i_rx_4p0",i_vcc_rx_4p0], ["i_rx_0p8",i_vcc_rx_0p8], ["i_rx_1p6",i_vcc_rx_1p6], ["i_rx_3p2",i_vcc_rx_3p2],
                    ["i_tx_4p0",i_vcc_tx_4p0], ["i_tx_0p8",i_vcc_tx_0p8], ["i_tx_1p6",i_vcc_tx_1p6], ["i_tx_3p2",i_vcc_tx_3p2]]        
        return currents


    def __print_messages(self, message_type:MessageType, message:str) -> None:
        print(f"{message_type}{message}{MessageType.ENDC}")
        pass

