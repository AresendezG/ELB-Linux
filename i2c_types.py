
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


# Configuration: GPIO regs
class ELB_GPIOs:
    # ELB Inputs
	GPIO_IN_REG		=   141
	LPMODE_LOW     	=   [0, 0x02]
	LPMODE_HIGH		=	[1, 0x02]
	MODSEL_LOW		=	[0, 0x01]
	MODSEL_HIGH	   	=   [1, 0x01]
	RESET_L_LOW    	=   [0, 0x04]
	RESET_L_HIGH	=	[1, 0x04]
    # ELB Outputs
	INT_L_HIGH      =   [0x00]
	PRESENT_L_LOW   =   [0x00]
	INT_L_LOW		=	[0x01]
	PRESENT_L_HIGH	=	[0x02]

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
	
class GPIO_PINS:
    #ELB PIN        #RPI Pin
    LPMODE      =   20
    MODSEL      =   13
    RESET_L     =   16
    # Inputs for the Pi
    INT_L       =   26
    PRESENT_L   =   19


# Console Messages
class con_colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
