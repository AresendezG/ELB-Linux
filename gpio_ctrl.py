import RPi.GPIO as GPIO
from i2c_types import GPIO_PINS

class GPIO_CONTROL:
    def __init__(self) -> None:
        GPIO.setmode(GPIO.BCM)
        # Define inputs for the RPI and Outs for the ELB
        GPIO.setup(GPIO_PINS.INT_L, GPIO.IN)
        GPIO.setup(GPIO_PINS.PRESENT_L, GPIO.IN)
        # Define outputs for the RPI and Outs for the 
        GPIO.setup(GPIO_PINS.LPMODE, GPIO.OUT)
        GPIO.setup(GPIO_PINS.MODSEL, GPIO.OUT)
        GPIO.setup(GPIO_PINS.RESET_L, GPIO.OUT)
        pass

    def __del__(self):
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
    

