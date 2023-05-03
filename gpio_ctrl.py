import RPi.GPIO as GPIO
import time
import itertools, sys
from i2c_types import GPIO_PINS


class GPIO_CONTROL:

    spinner = itertools.cycle(['-', '/', '|', '\\'])
    
    def __init__(self) -> None:
        # Define GPIO map
        GPIO.setmode(GPIO.BCM)
        # Reset the GPIO config
        GPIO.cleanup()
        # Disable channel warning
        GPIO.setwarnings(False)
        # Define inputs for the RPI and Outs for the ELB
        GPIO.setup(GPIO_PINS.INT_L, GPIO.IN)
        GPIO.setup(GPIO_PINS.PRESENT_L, GPIO.IN)
        # Define outputs for the RPI and Outs for the ELB 
        GPIO.setup(GPIO_PINS.LPMODE, GPIO.OUT)
        GPIO.setup(GPIO_PINS.MODSEL, GPIO.OUT)
        GPIO.setup(GPIO_PINS.RESET_L, GPIO.OUT)

        self.config_pins_todefault()
        print("MSG: Configured the GPIOs to default")

        GPIO.setup(17, GPIO.OUT)
        self.p = GPIO.PWM(17, 1)  # channel=17 1Hz to create the PPS
        self.p.start(0)
        print("MSG: Configured the PPS")
        time.sleep(2)
        pass

    def __del__(self):
        print("MSG: Cleaning GPIO Config")
        self.config_pins_todefault()
        self.p.stop()
        time.sleep(2)
    
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
            print("USER:\tInsert the ELB to the Fixture to Start Test")
        while (detected != 0 and counter < timeout_ctr):
            sys.stdout.write(next(self.spinner))   
            sys.stdout.flush()                
            sys.stdout.write('\b')           
            detected = self.read_gpio(GPIO_PINS.INT_L)
            counter = counter + 1
            time.sleep(0.25)
        if self.read_gpio(GPIO_PINS.INT_L) != 0:
            print("ERROR:\tUser did not inserted the ELB before Timeout expired!")
            return False
        else:
            return True
            

