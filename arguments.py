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
            print("Pass the following arguments -u [UUTSN] [UUT-PN] [UUT-REV]")
            raise IndexError
        pass

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

        