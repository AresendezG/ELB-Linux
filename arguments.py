import argparse
from log_management import MessageType

class UserArguments:

    # Default names for the config files
    def_settings_file = "configs/settings.json"
    def_limits_file = "configs/limits.json"
    def_seq_file = "configs/seqconfig.xml"


    def __init__(self) -> None:
        pass

    def __get_user_args(self) -> list:
        parser = argparse.ArgumentParser(description="Juniper Active ELB TestCommand")
        parser.add_argument('-s', '--settings', type=str, required=False,
            help="(Optional) /path/tp/settings.json Settings file")
        parser.add_argument('-l', '--limits', type=str, required=False,
            help="(Optional) /path/to/limits.json Custom Test Limits File")
        parser.add_argument('-x', '--sequence', type=str, required=False,
            help="(Optional) /path/to/sequence.xml Custom Sequence File to change the execution order")
        parser.add_argument('-t', '--tcpmode', type=str, required=False,
            help="(Optional) [true] Execute the program in TCP/IP mode")

        args = parser.parse_args()

        settings = args.settings
        limits = args.limits
        sequence = args.sequence
        tcp_mode = args.tcpmode

        return [settings, limits, sequence, tcp_mode]


    # receives an input string, and returns the second element after the split
    def __split_return_after(self, input_str:str, splitchar:str) -> str:
        elementsin_str = input_str.split(splitchar)
        return elementsin_str[1]

    def __find_str(self, input_array:list, expected:str) -> int:
        for index in range(len(input_array)):
            if (input_array[index].__contains__(expected)):
                return index
        return -1
    

    def __validate_ext(self, param_file:str, default_file:str, expected_file_ext:str) -> str:
        if (param_file != None):
            if (param_file.__contains__(expected_file_ext)):
                return param_file
            else:
                print(f"Warning: User passed invalid Param File. Executing default {default_file}")
                return default_file
        else:
            return default_file


    def __scan_uut(self) -> list:
        user_input = "NONE"        
        # allow user multiple faiures
        while (user_input != 'c'):
            # Read input string using the scanner
            user_input = input(f"{MessageType.USER}SCAN Bottom UUT Label for SN, REV and PN: >> {MessageType.ENDC}")
            elements_input = user_input.split(' ')
            if (len(elements_input) != 3):
                print("ERROR. Scan Again the Label or type [c] + Enter key to exit")
            else:                
                try:
                    rev_str = self.__split_return_after(elements_input[self.__find_str(elements_input,'Rev:')], ':')
                    sn_str = self.__split_return_after(elements_input[self.__find_str(elements_input,'SN:')], ':')
                    pn_str = self.__split_return_after(elements_input[self.__find_str(elements_input,'PN:')], ':')
                    return [sn_str, pn_str, rev_str, True]
                
                except KeyboardInterrupt:
                    print("User has cancelled the execution")
                    return [None, None, None, False]
                except:
                    print("ERROR. Scan Again the Label or type [c] + Enter key to exit")
        # User cancelled the execution, return an empty list
        return [None, None, None, False]



    def parse_args(self, argv:list) -> list:
        
        # Find for settings arg
        [settings, limits, sequence, tcp_mode] = self.__get_user_args()
        # Validate settings file:
        settings_file = self.__validate_ext(settings, self.def_settings_file, ".json")
        # Validate sequence file
        seq_file = self.__validate_ext(sequence, self.def_seq_file, ".xml")
        limits_file = self.__validate_ext(limits, self.def_limits_file, ".json")
        
        # Request user to scan UUT if the program is running in console mode
        if (tcp_mode != None):
            [sn_str, pn_str, rev_str, execution] = self.__scan_uut()
            if (execution):
                return [sn_str, rev_str, pn_str, seq_file, limits_file, settings_file]
            else:
                return None
        # Execution is TCP/IP mode, UUT info coming from the TCP service
        else:
            return ["TCPMODE", seq_file, limits_file, settings_file]