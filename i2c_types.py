
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

# Configuration: current sensors reg addresses
class CurrentSensors:
	VCC		= 174
	VCC_RX	= 176
	VCC_TX	= 178

class EPPS_Data:
	DATA = 1

class MOD_Rates:
	NRZ_25G = 	[0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30] 
	PAM4_25G =  [0x21, 0x21, 0x21, 0x21, 0x21, 0x21, 0x21, 0x21]
	PAM4_50G =  [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11] 


class PowerLoad_Modes:
	LOADS_OFF	=	[0x00, 0x00, 0x00]
	LOADS_1		=	[0x08, 0x02, 0x01]
	LOADS_2		= 	[0x02, 0x08, 0x02]
	LOADS_3		= 	[0x04, 0x01, 0x04]
	LOADS_4		= 	[0x01, 0x04, 0x00]
	