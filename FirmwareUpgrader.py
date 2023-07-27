from program_manager import ProgramControl
# Script to RUN repeatability

arguments = [
    "ZP3923110080", 
    "750-152172",
    "09",
    "debugconfigs/limits_fwupgrade.json",
    "debugconfigs/settings.json"
            ]


loopstorun = 5

# Launch program
for i in range(loopstorun):
    Main = ProgramControl(arguments)
    result = Main.run_program()
    print(f"Execution {i} Result: {result}")
    s = input("Insert other ELB and Press Key to Continue")
    Main = None