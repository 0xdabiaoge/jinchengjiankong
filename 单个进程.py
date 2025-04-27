import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import psutil
import subprocess
import threading
import datetime
import time
from ttkbootstrap import Style

class ProcessMonitorApp:
    def __init__(self, master):
        self.master = master
        self.style = Style(theme='flatly')
        master.title("进程监控器 v4.0")
        self.setup_ui()
        self.monitor_thread = None
        self.running = False

    def setup_ui(self):
        # 进程选择区
        ttk.Label(self.master, text="监控进程:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.process_listbox = tk.Listbox(self.master, width=35, height=8)
        self.process_listbox.grid(row=0, column=1, padx=10, pady=5, rowspan=2)
        ttk.Button(self.master, text="刷新列表", command=self.refresh_processes, bootstyle="info").grid(row=0, column=2, padx=5)

        # 程序路径选择
        ttk.Label(self.master, text="启动程序:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.path_entry = ttk.Entry(self.master, width=35)
        self.path_entry.grid(row=2, column=1, padx=10, pady=5)
        ttk.Button(self.master, text="浏览", command=self.select_program, bootstyle="secondary").grid(row=2, column=2, padx=5)

        # 控制按钮
        self.start_btn = ttk.Button(self.master, text="启动监控", command=self.start_monitoring, bootstyle="success")
        self.start_btn.grid(row=3, column=1, pady=15)
        self.stop_btn = ttk.Button(self.master, text="停止监控", state="disabled", command=self.stop_monitoring, bootstyle="danger")
        self.stop_btn.grid(row=3, column=2, pady=15)

        # 日志区
        self.log_text = tk.Text(self.master, height=12, width=65)
        self.log_text.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

        self.refresh_processes()

    def refresh_processes(self):
        """刷新进程列表"""
        self.process_listbox.delete(0, tk.END)
        processes = []
        for proc in psutil.process_iter(['name', 'pid', 'status']):
            try:
                if proc.info['status'] != psutil.STATUS_ZOMBIE:
                    processes.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
            except psutil.NoSuchProcess:
                continue
        for p in sorted(processes, key=lambda x: x.lower()):
            self.process_listbox.insert(tk.END, p)

    def get_selected_process(self):
        """获取选中进程名称"""
        if selections := self.process_listbox.curselection():
            return self.process_listbox.get(selections[0]).split(' (PID: ')[0]
        return None

    def select_program(self):
        """选择可执行文件"""
        if path := filedialog.askopenfilename(filetypes=[("可执行文件", "*.exe")]):
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def log_message(self, message):
        """记录日志"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def start_monitoring(self):
        """启动永久监控"""
        if not (proc_name := self.get_selected_process()):
            return messagebox.showerror("错误", "请先选择要监控的进程")
        if not (exe_path := self.path_entry.get().strip()):
            return messagebox.showerror("错误", "请选择要启动的程序路径")

        self.running = True
        self.monitor_thread = threading.Thread(
            target=self.monitor_loop,
            args=(proc_name, exe_path),
            daemon=True
        )
        self.monitor_thread.start()
        
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.log_message("永久监控已启动")

    def monitor_loop(self, proc_name, exe_path):
        """永久监控循环"""
        while self.running:
            process_exists = False
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == proc_name:
                    process_exists = True
                    break
            
            if not process_exists:
                try:
                    subprocess.Popen(exe_path)
                    self.log_message(f"进程 {proc_name} 已重新启动")
                except Exception as e:
                    self.log_message(f"启动失败: {str(e)}")
            
            time.sleep(5)  # 每5秒检测一次

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.log_message("监控已停止")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("750x550")  # 调整窗口大小
    ProcessMonitorApp(root)
    root.mainloop()
