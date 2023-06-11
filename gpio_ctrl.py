import RPi.GPIO as GPIO
import time
import itertools, sys
from i2c_types import GPIO_PINS
from log_management import LOG_Manager, MessageType


class GPIO_CONTROL:

    spinner = itertools.cycle(['-', '/', '|', '\\'])
    userled_cycle = itertools.cycle([GPIO.LOW, GPIO.HIGH])
    # Handler of the Logger Object
    log_mgr = None
    
    def __init__(self, log_handler: LOG_Manager) -> None:
        # Define GPIO map
        GPIO.setmode(GPIO.BCM)
        # Disable channel warning
        GPIO.setwarnings(False)
        # Define inputs for the RPI and Outs for the ELB
        GPIO.setup(GPIO_PINS.INT_L, GPIO.IN)
        GPIO.setup(GPIO_PINS.PRESENT_L, GPIO.IN)
        # Define outputs for the RPI and Outs for the ELB 
        GPIO.setup(GPIO_PINS.LPMODE, GPIO.OUT)
        GPIO.setup(GPIO_PINS.MODSEL, GPIO.OUT)
        GPIO.setup(GPIO_PINS.RESET_L, GPIO.OUT)
        # Define USER LED as Output for the RPI
        GPIO.setup(GPIO_PINS.LED_FIX, GPIO.OUT)
        # pass control of the logger object to local object
        self.log_mgr = log_handler

        self.config_pins_todefault()
        self.log_mgr.print_message("Configured the GPIOs to default",MessageType.WARNING)

        GPIO.setup(17, GPIO.OUT)
        #self.p = GPIO.PWM(17, 1)  # channel=17 1Hz to create the PPS
        #self.p.start(0)
        print("MSG: Configured the PPS")
        time.sleep(2)
        pass

    def __del__(self):
        self.log_mgr.print_message("Cleaning GPIO Config", MessageType.WARNING)
        self.config_pins_todefault()
        #self.p.stop()
        time.sleep(2)
        # Reset the GPIO config
        GPIO.cleanup()
    
    def read_gpio(self, pin: GPIO_PINS) -> bool:
        status = GPIO.input(pin)
        return status

    def write_gpio(self, pin: GPIO_PINS, status: bool):
        if status:
            GPIO.output(pin, GPIO.HIGH)
        else:
            GPIO.output(pin, GPIO.LOW)
        return
    
    def config_pins_todefault(self):
        # Setting up all outs to the way they're supposed to be 
        # GPIO.output(GPIO_PINS.LPMODE, GPIO.LOW)
        GPIO.output(GPIO_PINS.MODSEL, GPIO.LOW)
        GPIO.output(GPIO_PINS.RESET_L, GPIO.HIGH)
        GPIO.output(GPIO_PINS.LED_FIX, GPIO.LOW)


    def reset_uut(self, wait_time: int):
        GPIO.output(GPIO_PINS.RESET_L, GPIO.LOW)
        time.sleep(2)
        GPIO.output(GPIO_PINS.RESET_L, GPIO.HIGH)

    def detect_uut(self, timeout_s:int) -> bool:
        timeout_ctr = timeout_s * 4
        counter:int = 0
        # INT_L is pull to GND when ELB is inserted into the fixture
        detected = self.read_gpio(GPIO_PINS.INT_L)
        if detected != 0:
            self.log_mgr.print_message("Insert the ELB to the Fixture to Start Test", MessageType.USER)
        while (detected != 0 and counter < timeout_ctr):
            sys.stdout.write(next(self.spinner))   
            sys.stdout.flush()                
            sys.stdout.write('\b')           
            detected = self.read_gpio(GPIO_PINS.INT_L)
            counter = counter + 1
            time.sleep(0.25)
        if (counter >= timeout_ctr):
            self.log_mgr.print_message("FAIL: ELB Not Detected before Timeout Expired!", MessageType.FAIL)
            return False
        else:
            return True
        
    # To be queried while the program is running in TCP mode
    def detect_uut_tcp(self, timeout:int) -> bool:
        timeout_ctr = timeout * 4
        counter:int = 0
        # INT_L is pull to GND when ELB is inserted into the fixture
        detected = self.read_gpio(GPIO_PINS.INT_L)
        if detected == 0:
            return True
        while (detected != 0 and counter < timeout_ctr):
            self.write_gpio(GPIO_PINS.LED_FIX, next(self.userled_cycle))
            detected = self.read_gpio(GPIO_PINS.INT_L)
            counter = counter + 1
            time.sleep(0.25)
        if (counter >= timeout_ctr):
            self.log_mgr.print_message("FAIL: ELB Not Detected before Timeout Expired", MessageType.FAIL)
            self.write_gpio(GPIO_PINS.LED_FIX, GPIO.LOW)
            return False
        else:
            self.write_gpio(GPIO_PINS.LED_FIX, GPIO.HIGH)
            return True


    def wait_effect(timeout:int, printmsg:bool = True):
        spinner = itertools.cycle(['-', '/', '|', '\\'])
        counter = 0
        timeout_total = timeout*4
        if (printmsg):
            print(f"Wait for: {timeout} Seconds")
        while(counter < timeout_total):
            sys.stdout.write(next(spinner))   
            sys.stdout.flush()                
            sys.stdout.write('\b')           
            counter = counter + 1
            time.sleep(0.25)
        return

