"""DouYinSparkFlow 一键部署工具"""
import os
import sys
import json
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DOCS_INDEX = os.path.join(BASE_DIR, "docs", "index.html")
TASK_NAME = "DouYinSparkFlow"


def run_cmd(cmd, log_func):
    """后台执行命令并输出日志"""
    def worker():
        log_func(f">>> {' '.join(cmd)}\n")
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                cwd=BASE_DIR, shell=True,
            )
            for line in proc.stdout:
                log_func(line)
            proc.wait()
            log_func(f">>> 完成，退出码 {proc.returncode}\n\n")
        except Exception as e:
            log_func(f">>> 执行失败: {e}\n\n")
    threading.Thread(target=worker, daemon=True).start()


class SetupApp:
    def __init__(self, root):
        self.root = root
        root.title("DouYinSparkFlow 一键部署")
        root.geometry("640x620")
        root.resizable(False, False)

        # 步骤 1：安装依赖
        ttk.Button(root, text="1. 安装依赖（pip + Chromium）",
                   command=self.install_deps).pack(fill="x", padx=20, pady=(20, 5))

        # 步骤 2：打开配置生成器
        ttk.Button(root, text="2. 打开配置生成器网页",
                   command=self.open_generator).pack(fill="x", padx=20, pady=5)

        # 获取 Cookies 入口
        ttk.Button(root, text="   打开抖音创作者中心（登录获取 Cookies）",
                   command=self.open_douyin).pack(fill="x", padx=20, pady=5)

        # 步骤 3：粘贴配置
        ttk.Label(root, text="3. 粘贴 CONFIG JSON（配置生成器里复制）：").pack(anchor="w", padx=20, pady=(10, 0))
        self.config_text = scrolledtext.ScrolledText(root, height=8)
        self.config_text.pack(fill="x", padx=20, pady=5)

        # 如果有 config.json 就预填
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    self.config_text.insert("1.0", f.read())
            except Exception:
                pass

        ttk.Button(root, text="保存配置到 config.json",
                   command=self.save_config).pack(fill="x", padx=20, pady=5)

        # 步骤 4：定时任务
        frame = ttk.Frame(root)
        frame.pack(fill="x", padx=20, pady=(10, 5))
        ttk.Label(frame, text="4. 每天运行时间 (HH:MM)：").pack(side="left")
        self.time_var = tk.StringVar(value="21:30")
        ttk.Entry(frame, textvariable=self.time_var, width=8).pack(side="left", padx=5)
        ttk.Button(frame, text="设置定时任务", command=self.set_schedule).pack(side="left", padx=10)
        ttk.Button(frame, text="取消定时任务", command=self.remove_schedule).pack(side="left")

        # 步骤 5：立即运行
        ttk.Button(root, text="5. 立即运行续火花",
                   command=self.run_now).pack(fill="x", padx=20, pady=5)

        # 日志
        ttk.Label(root, text="日志输出：").pack(anchor="w", padx=20, pady=(10, 0))
        self.log_text = scrolledtext.ScrolledText(root, height=14, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(5, 20))

    def log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def install_deps(self):
        self.log("开始安装依赖...\n")
        run_cmd("pip install -r requirements.txt", self.log)
        run_cmd("playwright install chromium", self.log)

    def open_generator(self):
        if not os.path.exists(DOCS_INDEX):
            messagebox.showerror("错误", f"未找到配置生成器: {DOCS_INDEX}")
            return
        webbrowser.open("file:///" + DOCS_INDEX.replace("\\", "/"))
        self.log(f"已打开配置生成器: {DOCS_INDEX}\n")

    def open_douyin(self):
        webbrowser.open("https://creator.douyin.com/")
        self.log("已打开抖音创作者中心，登录后用 Cookie-Editor 导出 Cookies\n")

    def save_config(self):
        content = self.config_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("提示", "请先粘贴 CONFIG JSON")
            return
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            messagebox.showerror("错误", f"JSON 格式错误: {e}")
            return
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(content)
            self.log(f"配置已保存到 {CONFIG_FILE}\n")
            messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")

    def set_schedule(self):
        t = self.time_var.get().strip()
        try:
            h, m = t.split(":")
            h, m = int(h), int(m)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "时间格式应为 HH:MM，如 21:30")
            return

        python = sys.executable
        main = os.path.join(BASE_DIR, "main.py")
        cmd = (
            f'schtasks /create /tn "{TASK_NAME}" /tr "\\"{python}\\" \\"{main}\\"" '
            f'/sc daily /st {t} /f'
        )
        self.log(f">>> {cmd}\n")
        run_cmd(cmd, self.log)
        self.log(f"定时任务已设置：每天 {t}\n")

    def remove_schedule(self):
        cmd = f'schtasks /delete /tn "{TASK_NAME}" /f'
        self.log(f">>> {cmd}\n")
        run_cmd(cmd, self.log)

    def run_now(self):
        python = sys.executable
        main = os.path.join(BASE_DIR, "main.py")
        cmd = f'"{python}" "{main}"'
        self.log(f">>> 立即运行: {cmd}\n")
        run_cmd(cmd, self.log)


if __name__ == "__main__":
    root = tk.Tk()
    app = SetupApp(root)
    root.mainloop()
