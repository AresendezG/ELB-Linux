from log_management import MessageType

class ArgumentsProcess:

    # define default names for the config files
    def_settings_file = "settings.json"
    def_limits_file = "limits.json"
    def_seq_file = "seqconfig.xml"

    def __init__(self) -> None:
        
        pass

    def find_index(self, param:str, arg:list) -> list:

        for i in range(len(arg)):
            try:
                index = arg.index(param)
            except:
                index = -1
                pass
        return index

    def validate_ext(self, index_set:int, argv:list, expected_ext:str, default_file:str) -> str:
        if (index_set >= 0):
            if (argv[index_set + 1].__contains__(expected_ext)):
                file_str = argv[index_set + 1]
            else:
                file_str = default_file
        else:
            print(f"No arg found. Using {default_file} as default")
            file_str = default_file
        return file_str

    def validate_uut(self, index:int, argv:list) -> list:
        if (index >= 0):
            try:
                uut_sn = argv[index + 1]
                uut_pn = argv[index + 2]
                uut_rv = argv[index + 3]
                return [uut_sn, uut_pn, uut_rv]
            except:
                print("Wrong Settings on the UUT Information. Try Again.")
                raise IndexError
        else:
            print("Warning:\t No UUT info, User needs to Scan UUT")
            [uut_sn, uut_pn, uut_rv, valid_sn] = self.scan_uut()
            if (valid_sn):
                return [uut_sn, uut_pn, uut_rv]
            else:
                print("ERROR:\t User Cancelled execution")
                raise IndexError
        pass

    # receives an input string, and returns the second element after the split
    def __split_return_after(self, input_str:str, splitchar:str) -> str:
        elementsin_str = input_str.split(splitchar)
        return elementsin_str[1]

    def __find_str(self, input_array:list, expected:str) -> int:
        for index in range(len(input_array)):
            if (input_array[index].__contains__(expected)):
                return index
        return -1
    

    def scan_uut(self) -> list:
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
                except:
                    print("ERROR. Scan Again the Label or type [c] + Enter key to exit")
        # User cancelled the execution, return an empty list
        return [None, None, None, False]


    def parse_args(self, argv:list) -> list:
        
        # Find for settings arg
        index_set = self.find_index('-x', argv)
        index_lim = self.find_index('-l', argv)
        index_seq = self.find_index('-s', argv)
        index_uut = self.find_index('-u', argv)

        # process index parameter
        settings_file = self.validate_ext(index_set, argv, ".json", self.def_settings_file)
        limits_file = self.validate_ext(index_lim, argv, ".json", self.def_limits_file)
        seq_file = self.validate_ext(index_seq, argv, ".xml", self.def_seq_file)

        [uut_sn, uut_pn, uut_rv] = self.validate_uut(index_uut, argv)

        print(f"Using Settings File: {settings_file}")
        print(f"Using Limits File: {limits_file}")
        print(f"Using UUT SN: {uut_sn}")
        
        # Expected list from the program_manager 
        
        '''
            # Define all of the input parameters
            self.sn = self.input_args[1]
            self.rev = self.input_args[2]
            self.partnum = self.input_args[3]
            self.seq_file = self.input_args[4]
            self.limits_file = self.input_args[5]
            self.config_file = self.input_args[6]
        
        '''
        return [uut_sn, uut_rv, uut_pn, seq_file, limits_file, settings_file]

        