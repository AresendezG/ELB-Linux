from smbus2 import SMBus
from i2c_comm import ELB_Linux

i2c_comm = ELB_Linux()

print("--- ELB Testing Script --- ")
i2c_comm.main()