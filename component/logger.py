import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from typing import Optional, Callable


class logger(ttk.LabelFrame):
    """    日志组件    """
    def __init__(self, parent, title: str = "日志信息", height: int = 8, **kwargs):
        """
        参数:
        - parent: 父组件
        - title: 日志框标题
        - height: 日志区域高度（行数）
        """
        super().__init__(parent, text=title, padding="10", **kwargs)

        self.height = height
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        # 日志文本区域
        self.log_area = scrolledtext.ScrolledText(self, height=self.height)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.config(state=tk.DISABLED)

        # 工具栏
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(fill=tk.X, pady=(5, 0))

        # 复制按钮
        self.copy_btn = ttk.Button(self.toolbar, text="复制日志", command=self.copy)
        self.copy_btn.pack(side=tk.RIGHT, padx=(0, 5))

        # 清除按钮
        self.clear_btn = ttk.Button(self.toolbar, text="清除日志", command=self.clear)
        self.clear_btn.pack(side=tk.RIGHT, padx=(0, 5))

    def log(self, message: str, level: str = "INFO"):
        """
        记录日志
        参数:
        - message: 日志消息
        - level: 日志级别 (INFO, WARNING, ERROR, SUCCESS)
        """
        # 根据级别添加前缀和颜色
        level_colors = {
            "INFO": ("ℹ", "black"),
            "WARNING": ("⚠", "orange"),
            "ERROR": ("✗", "red"),
            "SUCCESS": ("✓", "green")
        }
        timestamp = datetime.now().strftime("%H:%M:%S")

        prefix, color = level_colors.get(level, ("•", "black"))
        formatted_message = f"{timestamp} {prefix} {message}"

        # 插入日志
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"{formatted_message}\n")

        # 应用颜色（最后一行）
        if color != "black":
            start_index = f"{int(self.log_area.index('end-1c').split('.')[0]) - 1}.0"
            end_index = f"{start_index.split('.')[0]}.end"
            self.log_area.tag_add(level, start_index, end_index)
            self.log_area.tag_config(level, foreground=color)

        self.log_area.config(state=tk.DISABLED)
        self.log_area.see(tk.END)  # 自动滚动到底部

    #region 日志打印
    def info(self, message: str):
        """信息日志"""
        self.log(message, "INFO")

    def warning(self, message: str):
        """警告日志"""
        self.log(message, "WARNING")

    def error(self, message: str):
        """错误日志"""
        self.log(message, "ERROR")

    def success(self, message: str):
        """成功日志"""
        self.log(message, "SUCCESS")
    #endregion

    def clear(self):
        """清除所有日志"""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.info("日志已清除")

    def copy(self):
        """复制所有日志到剪贴板"""
        self.log_area.config(state=tk.NORMAL)
        content = self.log_area.get(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)

        self.clipboard_clear()
        self.clipboard_append(content.strip())
        self.info("日志已复制到剪贴板")

    def get_logs(self) -> str:
        """获取所有日志内容"""
        self.log_area.config(state=tk.NORMAL)
        content = self.log_area.get(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)
        return content.strip()