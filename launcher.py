from program_manager import ProgramControl
# Script to RUN repeatability

arguments = [
    "ZP3923110080", 
    "750-152172",
    "09",
    "seqconfig.xml",
    "limits.json",
    "settings.json"
            ]
Main = ProgramControl(arguments)

loopstorun = 5

# Launch program
for i in range(loopstorun):

    result = Main.run_program()
    print(f"Execution {i} Result: {result}")