from smbus2 import SMBus
from i2c_comm import ELB_i2c

i2c_comm = ELB_i2c()

print("--- ELB Testing Script --- ")
i2c_comm.main()