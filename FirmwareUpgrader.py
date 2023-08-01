from program_manager import ProgramControl
from log_management import LOG_Manager

# Launch the test but only using the firmware upgrade steps

arguments = [
    "FWUPGRADE", 
    "750-152172",
    "09",
    "debugconfigs/limits_fwupgrade.json",
    "debugconfigs/settings.json"
            ]

# Create object to store the serial numbers of those UUTs upgraded

LogMgr = LOG_Manager("/tmp/elb/logs/")

loopstorun = input('How many UUTs to Upgrade? ')
if (LogMgr.create_fwupgrade_log()):
    LogMgr.print_fwupgrade_headers("0.84")
    logs = True
else:
    logs = False

# Run the firmware upgrade script
for i in range(int(loopstorun)):
    Main = ProgramControl(arguments)
    result = Main.run_program()
    updated_uut = Main.sn
    print(f"Execution {i} Result: {result}")
    # store the most recent UUT
    if (logs):
        LogMgr.log_new_uut_fwupgrade(updated_uut)
    Main = None
    s = input("Remove UUT from Fixture and press <ENTER>")

# Close the upgrade list file
LogMgr.close_uut_fwupgrade_file()