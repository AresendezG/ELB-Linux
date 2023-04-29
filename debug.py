
import sys 
import xml
from Sequencer import SeqConfig
import sys
#from smbus2 import SMBus
#from i2c_comm import ELB_i2c
#from i2c_types import MOD_Rates
from log_management import LOG_Manager


class DummyClass:
    def __init__(self) -> None:
        print("Event:\tCreating a dummy class! jejeje")
        pass

    def voltagefnc(self) -> list:
        print("Test:\tYoure executing voltage fnc")
        return [1, 2, 3, 4]
    
    def currentfnc(self) -> list:
        print("Test:\tYou're executing a current fnc")
        return [0.2, 0.3, 0.5]