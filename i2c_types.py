
# Configuration: start address is 129, following byte is the LED behavior
class LedMode:	
	RED_ON         =[0x01]       
	GREEN_ON       =[0x10]     
	RED_FLASH      =[0x02]        
	GREEN_FLASH    =[0x20]
	BOTH_ON        =[0x11]   
	BOTH_FLASH     =[0x22]
	LED_OFF        =[0x00]

# Configuration: voltage sensors addresses 
class VoltageSensors:
	VCC = 	168
	VCCTX = 172
	VCCRX = 170
	VBATT = 180

# Configuration: temperature sensors addresses
class TempSensors:
	UC 		= 146
	RTMR 	= 144
	PCB_RT	= 150
	PCB_PL	= 154
	SHELL_F	= 148
	SHELL_R	= 152 

class EPPS_Data:
	DATA = 1