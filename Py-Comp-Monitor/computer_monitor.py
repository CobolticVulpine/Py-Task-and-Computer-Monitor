import customtkinter as ctk
import psutil
import platform
import ctypes
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import winreg
import subprocess
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import os
import socket

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def system_info():
    subprocess.run("msinfo32.exe")

def task_manager():
    subprocess.run("taskmgr.exe")

def computer_manager():
    subprocess.run("compmgmt.msc")

class SystemManager(ctk.CTk):
    favicon = "favicon.ico"

    def __init__(self):
        super().__init__()

        self.is_admin = self.check_admin()
        status_title = "Administrator" if self.is_admin else "Standard User"
        self.title(f"Task and Computer Monitor: {status_title}")
        self.geometry("1400x900")

        self.is_admin = self.check_admin()

        header = ctk.CTkFrame(self, height=60)
        header.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkButton(header,
              text="Toggle Theme",
              command=self.toggle_theme).pack(side="right", padx=10)

        title = ctk.CTkLabel(header, text="Task and Computer Monitor", font=("Segoe UI", 22, "bold"))
        title.pack(side="left", padx=15)

        status = "Administrator" if self.is_admin else "Standard User"
        color = "#4CAF50" if self.is_admin else "#F44336"

        admin_label = ctk.CTkLabel(header, text=f"Privilege: {status}", text_color=color, font=("Segoe UI", 14))
        admin_label.pack(side="right", padx=15)

        self.iconbitmap(self.favicon)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.tabs.add("Processes")
        self.tabs.add("Disk Management")
        self.tabs.add("Performance")
        self.tabs.add("Process Monitor")
        self.tabs.add("Startup Manager")
        self.tabs.add("GPU Monitor")
        self.tabs.add("System Info")

        self.create_process_tab()
        self.create_disk_tab()
        self.create_performance_tab()
        self.create_process_monitor_tab()
        self.create_startup_tab()
        self.create_gpu_tab()
        self.create_system_info_tab()

    def check_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def create_process_tab(self):
        frame = self.tabs.tab("Processes")

        columns = ("PID", "Name", "CPU %", "Memory %")
        self.process_table = ttk.Treeview(frame, columns=columns, show="headings")

        for col in columns:
            self.process_table.heading(col, text=col)

        self.process_table.column("PID", anchor="w", width=25)
        self.process_table.column("Name", anchor="w", width=350)
        self.process_table.column("CPU %", anchor="center", width=120)
        self.process_table.column("Memory %", anchor="center", width=120)

        self.process_table.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.pid_entry = ctk.CTkEntry(btn_frame, placeholder_text="Enter PID")
        self.pid_entry.pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="Refresh", command=self.refresh_processes).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="End Process", command=self.end_process).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="System Info", command=system_info).pack(side="right", padx=10)
        ctk.CTkButton(btn_frame, text="Task Manager", command=task_manager).pack(side="right", padx=10)
        ctk.CTkButton(btn_frame, text="Computer Manager", command=computer_manager).pack(side="right", padx=10)

        self.refresh_processes()

    def refresh_processes(self):
        self.process_table.delete(*self.process_table.get_children())
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                self.process_table.insert("", "end", values=(
                    proc.info['pid'],
                    proc.info['name'],
                    f"{proc.info['cpu_percent']:.1f}",
                    f"{proc.info['memory_percent']:.2f}"
                ))
            except:
                pass

    def end_process(self):
        if not self.is_admin:
            messagebox.showerror("Permission Denied", "Administrator privileges required.")
            return
        pid = self.pid_entry.get()
        if pid.isdigit():
            try:
                psutil.Process(int(pid)).terminate()
                self.refresh_processes()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def create_disk_tab(self):
        frame = self.tabs.tab("Disk Management")

        columns = ("Device", "Mountpoint", "File System", "Total (GB)", "Used %")
        self.disk_table = ttk.Treeview(frame, columns=columns, show="headings")

        for col in columns:
            self.disk_table.heading(col, text=col)

        self.disk_table.column("Device", anchor="center", width=150)
        self.disk_table.column("Mountpoint", anchor="center", width=150)
        self.disk_table.column("File System", anchor="center", width=120)
        self.disk_table.column("Total (GB)", anchor="center", width=150)
        self.disk_table.column("Used %", anchor="center", width=100)

        self.disk_table.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkButton(frame, text="Refresh Disks", command=self.refresh_disks).pack(pady=5)

        self.refresh_disks()

    def refresh_disks(self):
        self.disk_table.delete(*self.disk_table.get_children())
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                self.disk_table.insert("", "end", values=(
                    partition.device,
                    partition.mountpoint,
                    partition.fstype,
                    f"{usage.total / (1024**3):.2f}",
                    f"{usage.percent:.1f}"
                ))
            except:
                pass

    def create_performance_tab(self):
        frame = self.tabs.tab("Performance")

        self.disk_history = deque([0]*60, maxlen=60)
        self.net_history = deque([0]*60, maxlen=60)

        fig, self.ax = plt.subplots(2, 1, figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(fig, master=frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.update_perf_graph()

    def update_perf_graph(self):
        disk = psutil.disk_io_counters()
        net = psutil.net_io_counters()

        self.disk_history.append(disk.read_bytes / (1024**2))
        self.net_history.append(net.bytes_sent / (1024**2))

        self.ax[0].clear()
        self.ax[1].clear()

        self.ax[0].plot(self.disk_history)
        self.ax[0].set_title("Disk Read (MB)")

        self.ax[1].plot(self.net_history)
        self.ax[1].set_title("Network Sent (MB)")

        self.canvas.draw()
        self.after(1000, self.update_perf_graph)

    def create_process_monitor_tab(self):
        frame = self.tabs.tab("Process Monitor")

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", pady=10)

        self.monitor_pid_entry = ctk.CTkEntry(top, placeholder_text="Enter PID")
        self.monitor_pid_entry.pack(side="left", padx=5)

        ctk.CTkButton(top, text="Start Monitoring", command=self.start_pid_monitor).pack(side="left", padx=5)

        self.pid_history = deque([0]*60, maxlen=60)

        fig, self.pid_ax = plt.subplots(figsize=(8, 4))
        self.pid_canvas = FigureCanvasTkAgg(fig, master=frame)
        self.pid_canvas.get_tk_widget().pack(fill="both", expand=True)

    def start_pid_monitor(self):
        try:
            self.selected_pid = int(self.monitor_pid_entry.get())
            self.update_pid_graph()
        except:
            pass

    def update_pid_graph(self):
        try:
            p = psutil.Process(self.selected_pid)
            cpu = p.cpu_percent()
            self.pid_history.append(cpu)

            self.pid_ax.clear()
            self.pid_ax.plot(self.pid_history)
            self.pid_ax.set_title(f"CPU Usage - PID {self.selected_pid}")

            self.pid_canvas.draw()
            self.after(1000, self.update_pid_graph)
        except:
            pass

    def create_startup_tab(self):
        frame = self.tabs.tab("Startup Manager")

        columns = ("Name", "Path")
        self.startup_table = ttk.Treeview(frame, columns=columns, show="headings")

        for col in columns:
            self.startup_table.heading(col, text=col)
            self.startup_table.column(col, anchor="w", width=600)

        self.startup_table.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_startup_items()

    def load_startup_items(self):
        self.startup_table.delete(*self.startup_table.get_children())
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
            i = 0
            while True:
                name, value, _ = winreg.EnumValue(key, i)
                self.startup_table.insert("", "end", values=(name, value))
                i += 1
        except:
            pass

    def create_gpu_tab(self):
        frame = self.tabs.tab("GPU Monitor")

        self.gpu_label = ctk.CTkLabel(frame, text="Detecting GPU...", font=("Segoe UI", 16))
        self.gpu_label.pack(pady=20)

        self.update_gpu_info()

    def update_gpu_info(self):
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                 "--format=csv,noheader,nounits"]
            )
            util, mem_used, mem_total = output.decode().strip().split(", ")
            self.gpu_label.configure(
                text=f"GPU Usage: {util}% | Memory: {mem_used}/{mem_total} MB"
            )
        except:
            self.gpu_label.configure(
                text="NVIDIA GPU not detected or nvidia-smi unavailable."
            )

        self.after(2000, self.update_gpu_info)

    def create_system_info_tab(self):
        frame = self.tabs.tab("System Info")

        def get_ip_address():
            try:
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except:
                return "N/A"

        info = f"""
        User: {os.getlogin()}
        Node Name: {platform.node()}
        OS: {platform.system()}
        Release: {platform.release()}
        Processor: {platform.processor()}
        CPU Cores: {psutil.cpu_count(logical=False)}
        Logical CPUs: {psutil.cpu_count()}
        Memory: {psutil.virtual_memory().total / (1024**3):.2f} GB
        Kernal: {platform.version()}
        IP: {get_ip_address()}
        """

        label = ctk.CTkLabel(frame, text=info, justify="left", font=("Consolas", 24))
        label.pack(padx=20, pady=20)

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new)

if __name__ == "__main__":
    app = SystemManager()
    app.mainloop()