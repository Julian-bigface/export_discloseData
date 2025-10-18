import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from typing import Optional, Callable, Tuple


class DatePicker(ttk.Frame):
    """   日期选择组件   """
    def __init__(self, parent,
                 mode: str = "single",  # "single" 或 "range"
                 label_text: str = "日期选择:",
                 default_start: Optional[str] = datetime.today(),  # 新增：默认开始日期 "YYYY-MM-DD"
                 default_end: Optional[str] = datetime.today(),  # 新增：默认结束日期 "YYYY-MM-DD"
                 on_change: Optional[Callable] = None,
                 **kwargs):
        """
        参数:
        - parent: 父组件
        - mode: 模式 ("single" 或 "range")，创建后不可切换
        - label_text: 标签文本
        - on_change: 日期变化时的回调函数
        """
        super().__init__(parent, **kwargs)

        self.mode = mode
        self.default_start = default_start
        self.default_end = default_end
        self.on_change = on_change
        self.setup_ui(label_text)

        # 设置默认日期
        self._set_default_dates()

        # 绑定日期变化事件
        self._bind_date_events()

    def setup_ui(self, label_text):
        """设置UI - 所有内容在一排"""
        # 标签
        if label_text:
            ttk.Label(self, text=label_text).grid(row=0, column=0, padx=(0, 5), pady=0, sticky=tk.W)

        if self.mode == "single":
            # 单日模式：标签 + 一个日期选择器
            self.single_date = DateEntry(
                self,
                width=12,
                background='darkblue',
                foreground='white',
                borderwidth=2,
                date_pattern='yy-mm-dd'
            )
            self.single_date.grid(row=0, column=1, padx=5, pady=0, sticky=tk.W)

            # 多日模式的组件设为None
            self.range_start = None
            self.range_end = None
            self.range_separator = None

        else:
            # 多日模式：标签 + 开始日期 + "至" + 结束日期
            self.range_start = DateEntry(
                self,
                width=12,
                background='darkblue',
                foreground='white',
                borderwidth=2,
                date_pattern='yy-mm-dd'
            )
            self.range_start.grid(row=0, column=1, padx=5, pady=0, sticky=tk.W)

            self.range_separator = ttk.Label(self, text="至")
            self.range_separator.grid(row=0, column=2, padx=5, pady=0, sticky=tk.W)

            self.range_end = DateEntry(
                self,
                width=12,
                background='darkblue',
                foreground='white',
                borderwidth=2,
                date_pattern='yyyy-mm-dd'
            )
            self.range_end.grid(row=0, column=3, padx=5, pady=0, sticky=tk.W)

            # 单日模式的组件设为None
            self.single_date = None

    def _set_default_dates(self):
        """设置默认日期"""
        today = datetime.today().strftime("%y-%m-%d")

        if self.mode == "single":
            # 单日模式：使用默认值或今天
            if self.default_start:
                try:
                    date_obj = self.default_start.strftime("%y-%m-%d")
                    self.single_date.set_date(date_obj)
                except ValueError:
                    self.single_date.set_date(today)  # 默认值无效时使用今天
            else:
                self.single_date.set_date(today)  # 没有默认值时使用今天

        else:
            # 范围模式
            if self.default_start:
                try:
                    start_obj = self.default_start.strftime("%y-%m-%d")
                    self.range_start.set_date(start_obj)
                except ValueError:
                    self.range_start.set_date(today)  # 默认值无效时使用今天
            else:
                self.range_start.set_date(today)  # 没有默认值时使用今天

            if self.default_end:
                try:
                    end_obj = self.default_end.strftime("%y-%m-%d")
                    self.range_end.set_date(end_obj)
                except ValueError:
                    self.range_end.set_date(today)  # 默认值无效时使用今天
            else:
                self.range_end.set_date(today)  # 没有默认值时使用今天

    def _bind_date_events(self):
        """绑定日期变化事件"""
        if self.mode == "single" and self.single_date:
            self.single_date.bind("<<DateEntrySelected>>", self._on_date_change)
        else:
            if self.range_start:
                self.range_start.bind("<<DateEntrySelected>>", self._on_date_change)
            if self.range_end:
                self.range_end.bind("<<DateEntrySelected>>", self._on_date_change)

    def _on_date_change(self, event=None):
        """日期变化回调"""
        if self.on_change:
            self.on_change()

    def get_dates(self) -> Tuple[str, str]:
        """
        获取日期范围
        返回: (start_date, end_date)
        - 单日模式: start_date和end_date相同
        - 范围模式: 实际的开始和结束日期
        """
        if self.mode == "single":
            single_date = self.single_date.get_date().strftime("%Y-%m-%d")
            return single_date, single_date
        else:
            start_date = self.range_start.get_date().strftime("%Y-%m-%d")
            end_date = self.range_end.get_date().strftime("%Y-%m-%d")
            return start_date, end_date

    def get_dates_for_filename(self) -> Tuple[str, str]:
        """
        获取用于文件名的日期格式
        返回: (start_date_str, end_date_str) 格式: YYYYMMDD
        """
        start_date, end_date = self.get_dates()
        start_str = start_date.replace("-", "")
        end_str = end_date.replace("-", "")
        return start_str, end_str

    def set_single_date(self, date_str: str):
        """设置单日日期（仅单日模式有效）"""
        if self.mode == "single" and self.single_date:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                self.single_date.set_date(date_obj)
            except ValueError:
                pass

    def set_date_range(self, start_str: str, end_str: str):
        """设置日期范围（仅多日模式有效）"""
        if self.mode == "range":
            try:
                start_obj = datetime.strptime(start_str, "%Y-%m-%d")
                end_obj = datetime.strptime(end_str, "%Y-%m-%d")
                self.range_start.set_date(start_obj)
                self.range_end.set_date(end_obj)
            except ValueError:
                pass

    def is_valid(self) -> bool:
        """验证日期是否有效"""
        start_date, end_date = self.get_dates()

        if self.mode == "range":
            start_obj = datetime.strptime(start_date, "%Y-%m-%d")
            end_obj = datetime.strptime(end_date, "%Y-%m-%d")
            return start_obj <= end_obj

        return True

    def get_date_description(self) -> str:
        """获取日期描述文本"""
        start_date, end_date = self.get_dates()

        if self.mode == "single":
            return f"日期: {start_date}"
        else:
            if start_date == end_date:
                return f"日期: {start_date}"
            else:
                return f"日期范围: {start_date} 至 {end_date}"