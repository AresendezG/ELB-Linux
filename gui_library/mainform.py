import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from Sequencer import SeqConfig

class MainForm(tk.Tk):
    def __init__(self):
        
        super().__init__()

        # Variable definitions
        self.test_flow:list
        self.scriptloaded:bool = False

        self.title("ELB Linux TestClient")
        self.geometry("483x707")

        self.menu_bar = tk.Menu(self)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open Connection", command=self.open_con_btn_Click)
        self.file_menu.add_command(label="Close Connection", command=self.close_con_btn_Click)
        self.menu_bar.add_cascade(label="Connection", menu=self.file_menu)

        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.settings_menu.add_command(label="Connection Settings", command=self.sett_btn_Click)
        self.settings_menu.add_command(label="Load Test Script", command=self.load_script_btn_Click)
        self.settings_menu.add_command(label="Reload Last Script", command=self.reload_script_btn_Click)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)

        self.data_menu = tk.Menu(self.menu_bar, tearoff=0)
        #self.data_menu.add_command(label="Copy Results Grid", command=self.copy_grid_btn_Click)
        #self.data_menu.add_command(label="Export to CSV", command=self.export_grid_btn_Click)
        self.menu_bar.add_cascade(label="Data Operations", menu=self.data_menu)

        self.config(menu=self.menu_bar)

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill="both")

        self.connection_frame = ttk.Frame(self.main_frame)
        self.connection_frame.pack(pady=8)

        # frame1 
        self.con_status_frame = ttk.Frame(self.connection_frame)
        self.con_status_frame.pack(fill="both", side="left")
        self.cn_lbl = ttk.Label(self.con_status_frame, text="Connection Status:")
        self.cn_lbl.pack(expand=True, side = "top")
        self.connection_status_label = ttk.Label(self.con_status_frame, text="NOT_CONNECTED")
        self.connection_status_label.pack(expand=True, side = "bottom")
        
        # frame2
        self.con_host_frame = ttk.Frame(self.connection_frame)
        self.con_host_frame.pack(fill="both", side="left")
        self.cnh_lbl = ttk.Label(self.con_host_frame, text="Connection Host:")
        self.cnh_lbl.pack(expand=True, side = "top")
        self.connection_host_label = ttk.Label(self.con_host_frame, text="NOT_CONNECTED")
        self.connection_host_label.pack(expand=True, side = "bottom")

        # Frame3
        self.btns_frame = ttk.Frame(self.connection_frame)
        self.btns_frame.pack(fill="both", side="right")
        self.start_btn = ttk.Button(self.btns_frame, text="Start Test", command=self.start_btn_Click)
        self.start_btn.pack(expand=False, side="top")
        self.end_btn = ttk.Button(self.btns_frame, text="Abort", command=self.end_btn_Click)
        self.end_btn.pack(expand=False, side="bottom")        

        self.results_frame = ttk.Frame(self.main_frame)
        self.results_frame.pack(pady=8)

        self.results_label = ttk.Label(self.results_frame, text="Results")
        self.results_label.pack()

        self.ResultsGrid = ttk.Treeview(self.results_frame, columns=("TestIndex", "TestName", "LowLimit", "Measure", "HighLimit", "Status"))
        self.ResultsGrid.heading("TestIndex", text="Test Index")
        self.ResultsGrid.heading("TestName", text="Test Name")
        self.ResultsGrid.heading("LowLimit", text="Low Limit")
        self.ResultsGrid.heading("Measure", text="Measure")
        self.ResultsGrid.heading("HighLimit", text="High Limit")
        self.ResultsGrid.heading("Status", text="Status")
        self.ResultsGrid.pack()

    def open_con_btn_Click(self):
        pass

    def close_con_btn_Click(self):
        pass

    def sett_btn_Click(self):
        pass

    def load_script_btn_Click(self):
        script_json_path = filedialog.askopenfilename()
        # User selected a new JSON file
        if (script_json_path.endswith(".json")):
            self.ResultsGrid.delete(*self.ResultsGrid.get_children())
            # External objects
            seq_mgr = SeqConfig()
            print("Valid Script File")
            self.test_flow = seq_mgr.ReadSeq_Settings_JSON(script_json_path)
            step_list = seq_mgr.ReadSeq_fromJSON(script_json_path)
            # Populate the TestResults Grid with the script
            for item in step_list:
                self.ResultsGrid.insert("", "end", values=(item[0], item[1], item[2], item[3], item[4], "NOT RUN"))
            self.ResultsGrid.update()
            self.scriptloaded = True
            return
        else:
            print("Invalid!") 

        pass

    def reload_script_btn_Click(self):
        pass

    def start_btn_Click(self):
        pass

    def end_btn_Click(self):
        pass
