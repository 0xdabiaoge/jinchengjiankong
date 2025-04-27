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
        master.title("多进程监控器 v5.0")
        
        # 存储监控配置的字典 {进程名: 程序路径}
        self.monitor_list = {}
        
        self.setup_ui()
        self.monitor_thread = None
        self.running = False

    def setup_ui(self):
        # 进程选择区
        ttk.Label(self.master, text="系统进程列表:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.process_listbox = tk.Listbox(
            self.master, 
            width=35, 
            height=8,
            selectmode=tk.MULTIPLE  # 启用多选模式
        )
        self.process_listbox.grid(row=1, column=0, padx=10, pady=5, rowspan=3)
        
        # 进程列表操作按钮
        ttk.Button(
            self.master, 
            text="刷新列表", 
            command=self.refresh_processes, 
            bootstyle="info"
        ).grid(row=0, column=1, padx=5)
        
        ttk.Button(
            self.master,
            text="设置路径",
            command=self.set_exe_paths,
            bootstyle="warning"
        ).grid(row=1, column=1, padx=5)

        # 已选进程显示区
        ttk.Label(self.master, text="监控配置列表:").grid(row=0, column=2, padx=10, pady=5)
        self.monitor_tree = ttk.Treeview(
            self.master,
            columns=("process", "path"),
            show="headings",
            height=8
        )
        self.monitor_tree.heading("process", text="进程名称")
        self.monitor_tree.heading("path", text="程序路径")
        self.monitor_tree.column("process", width=120)
        self.monitor_tree.column("path", width=280)
        self.monitor_tree.grid(row=1, column=2, padx=10, pady=5, rowspan=3)

        # 控制按钮
        self.start_btn = ttk.Button(
            self.master,
            text="启动监控",
            command=self.start_monitoring,
            bootstyle="success"
        )
        self.start_btn.grid(row=4, column=1, pady=15)
        
        self.stop_btn = ttk.Button(
            self.master,
            text="停止监控",
            state="disabled",
            command=self.stop_monitoring,
            bootstyle="danger"
        )
        self.stop_btn.grid(row=5, column=1, pady=15)

        # 日志区
        self.log_text = tk.Text(self.master, height=12, width=85)
        self.log_text.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

        # 初始加载进程列表
        self.refresh_processes()

    def refresh_processes(self):
        """刷新系统进程列表"""
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

    def set_exe_paths(self):
        """为选中的进程设置执行路径"""
        selected_indices = self.process_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("提示", "请先在左侧列表中选择进程")
            return
        
        for index in selected_indices:
            # 提取纯进程名
            full_name = self.process_listbox.get(index)
            proc_name = full_name.split(' (PID: ')[0]
            
            # 弹出路径选择对话框
            path = filedialog.askopenfilename(
                title=f"为 {proc_name} 选择启动程序",
                filetypes=[("可执行文件", "*.exe")]
            )
            
            if path:
                # 更新监控列表和Treeview
                self.monitor_list[proc_name] = path
                self.monitor_tree.insert(
                    "", 
                    "end", 
                    values=(proc_name, path)
                )

    def log_message(self, message):
        """记录日志信息"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def start_monitoring(self):
        """启动监控服务"""
        if not self.monitor_list:
            messagebox.showerror("错误", "请先配置需要监控的进程")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self.monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.log_message("监控服务已启动，正在监控以下进程：")
        for proc, path in self.monitor_list.items():
            self.log_message(f"• {proc} → {path}")

    def monitor_loop(self):
        """监控主循环"""
        while self.running:
            # 遍历所有需要监控的进程
            for proc_name, exe_path in self.monitor_list.items():
                process_exists = False
                
                # 检查进程是否存在
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'] == proc_name:
                        process_exists = True
                        break
                
                # 进程不存在时启动程序
                if not process_exists:
                    try:
                        subprocess.Popen(exe_path)
                        self.log_message(f"进程 {proc_name} 已重新启动")
                    except Exception as e:
                        self.log_message(f"错误：启动 {proc_name} 失败 ({str(e)})")
            
            time.sleep(5)  # 每5秒检测一次

    def stop_monitoring(self):
        """停止监控服务"""
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.log_message("监控服务已停止")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x700")
    ProcessMonitorApp(root)
    root.mainloop()