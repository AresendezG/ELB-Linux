import RPi.GPIO as GPIO
import time
from i2c_types import GPIO_PINS


class GPIO_CONTROL:
    def __init__(self) -> None:
        GPIO.setmode(GPIO.BCM)
        # Reset the GPIO config
        GPIO.cleanup()
        

        # Define inputs for the RPI and Outs for the ELB
        GPIO.setup(GPIO_PINS.INT_L, GPIO.IN)
        GPIO.setup(GPIO_PINS.PRESENT_L, GPIO.IN)
        # Define outputs for the RPI and Outs for the 
        GPIO.setup(GPIO_PINS.LPMODE, GPIO.OUT)
        GPIO.setup(GPIO_PINS.MODSEL, GPIO.OUT)
        GPIO.setup(GPIO_PINS.RESET_L, GPIO.OUT)

        # Setting up all outs to High
        GPIO.output(GPIO_PINS.LPMODE, GPIO.LOW)
        GPIO.output(GPIO_PINS.MODSEL, GPIO.LOW)
        GPIO.output(GPIO_PINS.RESET_L, GPIO.HIGH)
        print("MSG: Configuring the GPIOs to default")
        time.sleep(2)
        pass

    def __del__(self):
        print("MSG: Cleaning GPIO Config")
        GPIO.output(GPIO_PINS.LPMODE, GPIO.LOW)
        GPIO.output(GPIO_PINS.MODSEL, GPIO.LOW)
        GPIO.output(GPIO_PINS.RESET_L, GPIO.HIGH)
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
    
    def reset_uut(self, wait_time: int):
        GPIO.output(GPIO_PINS.RESET_L, GPIO.LOW)
        time.sleep(2)
        GPIO.output(GPIO_PINS.RESET_L, GPIO.HIGH)
    

