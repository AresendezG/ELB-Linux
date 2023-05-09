from program_manager import ProgramControl
# Script to RUN repeatability

arguments = [
    "ZP3923110080", 
    "750-152172",
    "09",
    "configs/seqconfig.xml",
    "configs/limits.json",
    "configs/settings.json"
            ]
Main = ProgramControl(arguments)

# Launch program
for i in range(10):
    
    result = Main.run_program()
    print(f"Execution {i} Result: {result}")