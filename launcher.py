from program_manager import ProgramControl
# Script to RUN repeatability


# Launch program
Main = ProgramControl(arguments)
result = Main.run_program()
print(f"Execution Result: {result}")