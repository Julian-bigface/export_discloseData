import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import traceback
from typing import Dict, List, Optional, Callable, Any


class SaveButton(ttk.Button):
    """
    可复用的保存按钮组件

    特性：
    - 支持多种数据源（DataProvider、函数、字典）
    - 自动状态管理（有数据时启用，无数据时禁用）
    - 灵活的配置选项
    - 完整的错误处理
    - 可定制的回调函数
    """

    def __init__(self, parent,
                 get_data_func: Callable[[], Dict[str, pd.DataFrame]],
                 get_filename_func: Callable[[], str] = None,
                 log_func: Optional[Callable[[str], None]] = None,
                 **kwargs):
        """
        参数:
        - parent: 父组件
        - get_data_func: 获取数据的函数，返回 {sheet名: DataFrame}
        - get_filename_func: 获取文件名的函数（可选）
        - log_func: 日志函数（可选）
        """
        # 设置默认文本
        kwargs.setdefault('text', '保存数据')

        super().__init__(parent, command=self._save_data, **kwargs)

        self.get_data_func = get_data_func
        self.get_filename_func = get_filename_func
        self.log_func = log_func

        # 初始状态为禁用
        self.config(state=tk.DISABLED)

    def update_state(self):
        """更新按钮状态：有数据时启用，无数据时禁用"""
        try:
            data = self.get_data_func()
            has_data = data and any(not df.empty for df in data.values())
            self.config(state=tk.NORMAL if has_data else tk.DISABLED)
        except:
            self.config(state=tk.DISABLED)

    def _save_data(self):
        """执行保存操作"""
        try:
            # 获取数据
            dataframes = self.get_data_func()
            if not dataframes or all(df.empty for df in dataframes.values()):
                messagebox.showerror("保存错误", "没有数据可保存")
                return

            # 获取文件名
            if self.get_filename_func:
                default_filename = self.get_filename_func()
            else:
                default_filename = "data"

            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                initialfile=default_filename,
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
            )

            if not file_path:
                return

            # 保存数据
            self._save_to_excel(dataframes, file_path)

            # 记录日志
            if self.log_func:
                self.log_func(f"数据已保存到: {file_path}")

        except Exception as e:
            self._handle_error(e)

    def _save_to_excel(self, dataframes: Dict[str, pd.DataFrame], file_path: str):
        """保存到Excel文件"""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in dataframes.items():
                    if not df.empty:
                        # 限制sheet名称长度（Excel限制31字符）
                        safe_sheet_name = sheet_name[:31]
                        df.to_excel(writer, sheet_name=safe_sheet_name, index=True, index_label='时间')

            messagebox.showinfo("保存成功", f"数据已保存到:\n{file_path}")

        except PermissionError:
            error_msg = f"文件被占用，请关闭后重试:\n{file_path}"
            messagebox.showerror("保存失败", error_msg)
            if self.log_func:
                self.log_func(error_msg)
        except Exception as e:
            error_msg = f"保存失败: {str(e)}"
            messagebox.showerror("保存失败", error_msg)
            if self.log_func:
                self.log_func(error_msg)
                self.log_func(f"详细错误: {traceback.format_exc()}")

    def _handle_error(self, error: Exception):
        """错误处理"""
        error_msg = f"保存过程中发生错误: {str(error)}"
        messagebox.showerror("错误", error_msg)
        if self.log_func:
            self.log_func(error_msg)