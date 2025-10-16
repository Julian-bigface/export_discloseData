import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkcalendar import DateEntry
import pandas as pd
import threading
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DisclosureTab_real_time:
    def __init__(self, parent, crawler, cookie_var):
        self.crawler = crawler
        self.cookie_var = cookie_var
        self.data_df = pd.DataFrame()
        self.powerData_WestToEast_df = pd.DataFrame()

        self.frame = ttk.Frame(parent)
        self.create_input_section()
        self.create_log_section()
        self.create_result_section()

    def create_input_section(self):
        input_frame = ttk.LabelFrame(self.frame, text="参数设置", padding="10")
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="地区:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(input_frame, text="贵州").grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(input_frame, text="日期:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.selected_date = DateEntry(input_frame, width=12, background='darkblue',
                              foreground='white', borderwidth=2, date_pattern='yy-mm-dd')
        self.selected_date.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        # 设置默认日期为明天（保持原逻辑）
        today = datetime.today()
        self.selected_date.set_date((today + timedelta(days=1)).strftime('%y-%m-%d'))

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=4, column=0, columnspan=4, pady=10)

        self.fetch_button = ttk.Button(button_frame, text="开始爬取", command=self.start_crawl)
        self.fetch_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(button_frame, text="保存数据", command=self.save_data, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(button_frame, text="清除日志", command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT, padx=5)

    def create_log_section(self):
        log_frame = ttk.LabelFrame(self.frame, text="日志信息", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, height=6)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.config(state=tk.DISABLED)

        self.log("欢迎使用电力市场信息披露爬取工具")
        self.log("请设置参数后点击'开始爬取'按钮")

    def create_result_section(self):
        result_frame = ttk.LabelFrame(self.frame, text="信息披露数据预览", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("时间", "统调负荷", "发电总出力", "非市场化机组总出力",
                   "新能源出力", "水电总出力", "贵州总送出")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=80, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscroll=scrollbar.set)

        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_area.config(state=tk.DISABLED)
        self.log_area.see(tk.END)

    def clear_log(self):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.log("日志已清除")

    def start_crawl(self):
        cookie = "CAMSID=" + self.cookie_var.get().strip()
        if not cookie:
            messagebox.showerror("输入错误", "必须提供有效的CAMSID Cookie")
            return
        self.crawler.update_cookie(cookie)

        region = "贵州"
        selected_date = self.selected_date.get_date().strftime("%Y-%m-%d")

        self.fetch_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)

        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        self.data_df = pd.DataFrame()
        self.log(f"开始爬取 {region} 地区 {selected_date}  的数据...")
        thread = threading.Thread(target=self.crawl_data, args=(selected_date, region), daemon=True)
        thread.start()

    def crawl_data(self, selected_date, region):
        for result, is_final in self.crawler.get_real_time_public_information_by_date_range(selected_date, region):
            if isinstance(result, pd.DataFrame):
                self.data_df = result
                self.frame.after(0, self.update_results)
            elif isinstance(result, str) and is_final:
                self.log(result)
                self.frame.after(0, lambda: self.fetch_button.config(state=tk.NORMAL))
            else:
                self.log(result)
        if self.data_df.empty:
            self.frame.after(0, lambda: self.fetch_button.config(state=tk.NORMAL))

    def update_results(self):
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        sample_df = self.data_df.head(100) if len(self.data_df) > 100 else self.data_df
        for idx, row in sample_df.iterrows():
            values = (idx, row.get('统调负荷', ''), row.get('发电总出力', ''), row.get('非市场化机组总出力', ''),
                      row.get('新能源出力', ''), row.get('水电总出力', ''), row.get('省间联络线输电情况', ''))
            self.result_tree.insert("", tk.END, values=values)

        self.save_button.config(state=tk.NORMAL)
        self.fetch_button.config(state=tk.NORMAL)

    def save_data(self):
        try:
            if self.data_df.empty:
                messagebox.showerror("保存错误", "没有数据可保存")
                return
            region = "贵州"
            selected_date = self.selected_date.get_date().strftime("%Y%m%d")
            file_path = filedialog.asksaveasfilename(
                initialfile=f"{region}_{selected_date}_披露数据.xlsx",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
            )
            if not file_path:
                return
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                self.data_df.to_excel(writer, sheet_name='信息披露', index=True, index_label='时间')
            self.log(f"数据已保存到: {file_path}")
        except PermissionError:
            error_msg = f"错误：文件可能正在被其他程序占用，请关闭文件后重试\n{file_path}"
            messagebox.showerror("保存失败", error_msg)
            self.log(error_msg)

        except Exception as e:
            error_msg = f"保存过程中发生错误: {str(e)}"
            messagebox.showerror("保存失败", error_msg)
            self.log(error_msg)
            # 记录完整错误信息（调试用）
            self.log(f"完整错误信息: {traceback.format_exc()}")

