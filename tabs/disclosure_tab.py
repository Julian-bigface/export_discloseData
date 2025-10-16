import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkcalendar import DateEntry
import pandas as pd
import threading
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DisclosureTab:
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

        ttk.Label(input_frame, text="选择地区:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.region_combo = ttk.Combobox(input_frame, values=list(self.crawler.region_codes.keys()), state="readonly")
        self.region_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.region_combo.current(4)

        ttk.Label(input_frame, text="开始日期:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.start_date = DateEntry(input_frame, width=12, background='darkblue',
                                    foreground='white', borderwidth=2, date_pattern='yy-mm-dd')
        self.start_date.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(input_frame, text="结束日期:").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        self.end_date = DateEntry(input_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, date_pattern='yy-mm-dd')
        self.end_date.grid(row=2, column=3, padx=5, pady=5, sticky=tk.W)

        today = datetime.today()
        self.start_date.set_date((today + timedelta(days=1)).strftime('%y-%m-%d'))
        self.end_date.set_date((today + timedelta(days=1)).strftime('%y-%m-%d'))

        ttk.Label(input_frame, text="火电开机容量(MW):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.fire_volume = tk.StringVar(value="17170")
        fire_entry = ttk.Entry(input_frame, textvariable=self.fire_volume, width=10)
        fire_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=4, column=0, columnspan=4, pady=10)

        self.fetch_button = ttk.Button(button_frame, text="开始爬取", command=self.start_crawl)
        self.fetch_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(button_frame, text="保存数据", command=self.save_data, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.plot_button = ttk.Button(button_frame, text="显示图表", command=self.show_plot, state=tk.DISABLED)
        self.plot_button.pack(side=tk.LEFT, padx=5)

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

        columns = ("时间", "统调负荷", "新能源总出力（周）","非市场机组电源不含新能源总出力预测",
                   "正备用", "负备用", "火电竞价空间", "负荷率", "西电东送")
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

        region = self.region_combo.get()
        start_date = self.start_date.get_date().strftime("%Y-%m-%d")
        end_date = self.end_date.get_date().strftime("%Y-%m-%d")

        if start_date > end_date:
            messagebox.showerror("日期错误", "结束日期不能早于开始日期")
            return

        try:
            self.crawler.fire_volume = float(self.fire_volume.get())
        except ValueError:
            messagebox.showerror("输入错误", "火电容量必须是数字")
            return

        self.fetch_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.plot_button.config(state=tk.DISABLED)

        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        self.data_df = pd.DataFrame()
        self.log(f"开始爬取 {region} 地区 {start_date} 至 {end_date} 的数据...")
        thread = threading.Thread(target=self.crawl_data, args=(start_date, end_date, region), daemon=True)
        thread.start()

    def crawl_data(self, start_date, end_date, region):
        for result, W2E_result, is_final in self.crawler.get_public_information_by_date_range(start_date, end_date, region):
            if isinstance(result, pd.DataFrame):
                self.data_df = result
                self.powerData_WestToEast_df = W2E_result
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
            values = (idx, row.get('统调负荷', ''),row.get('新能源总出力（周）', ''), row.get('非市场机组电源不含新能源总出力预测', ''),
                      row.get('正备用', ''), row.get('负备用', ''), row.get('火电竞价空间', ''), row.get('负荷率', ''), row.get('西电东送', ''))
            self.result_tree.insert("", tk.END, values=values)

        self.save_button.config(state=tk.NORMAL)
        self.plot_button.config(state=tk.NORMAL)
        self.fetch_button.config(state=tk.NORMAL)

    def save_data(self):
        try:
            if self.data_df.empty:
                messagebox.showerror("保存错误", "没有数据可保存")
                return
            region = self.region_combo.get()
            start_date = self.start_date.get_date().strftime("%Y%m%d")
            end_date = self.end_date.get_date().strftime("%Y%m%d")
            file_path = filedialog.asksaveasfilename(
                initialfile=f"{region}_{start_date}_to_{end_date}_披露数据.xlsx",
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
            )
            if not file_path:
                return
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                self.data_df.to_excel(writer, sheet_name='信息披露', index=True, index_label='时间')
                self.powerData_WestToEast_df.to_excel(writer, sheet_name='西电东送', index=True, index_label='区域')
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

    def show_plot(self):
        if self.data_df.empty:
            messagebox.showerror("图表错误", "没有数据可显示")
            return
        plot_window = tk.Toplevel(self.frame)
        plot_window.title("电力市场披露信息趋势图")
        plot_window.geometry("1200x800")
        fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
        df = self.data_df.copy()
        df.index = pd.to_datetime(df.index)
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        if '统调负荷' in df.columns:
            df['统调负荷'].plot(ax=axes[0], label='统调负荷', color='blue')
        if '非市场机组电源不含新能源总出力预测' in df.columns:
            df['非市场机组电源不含新能源总出力预测'].plot(ax=axes[0], label='非市场机组电源不含新能源总出力预测', color='red')
        if '新能源总出力（周）' in df.columns:
            df['新能源总出力（周）'].plot(ax=axes[0], label='新能源总出力', color='green')
        axes[0].set_title("负荷与出力趋势")
        axes[0].set_ylabel("功率 (MW)")
        axes[0].grid(True)
        axes[0].legend()
        if '正备用' in df.columns:
            df['正备用'].plot(ax=axes[1], label='正备用', color='purple')
        if '负备用' in df.columns:
            df['负备用'].plot(ax=axes[1], label='负备用', color='orange')
        axes[1].set_title("备用容量趋势")
        axes[1].set_ylabel("功率 (MW)")
        axes[1].grid(True)
        axes[1].legend()
        if '火电竞价空间' in df.columns:
            df['火电竞价空间'].plot(ax=axes[2], label='火电竞价空间', color='brown')
        if '西电东送' in df.columns:
            df['西电东送'].plot(ax=axes[2], label='西电东送', color='cyan')
        axes[2].set_title("火电与西电东送趋势")
        axes[2].set_ylabel("功率 (MW)")
        axes[2].grid(True)
        axes[2].legend()
        fig.autofmt_xdate()
        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.log("图表已显示")
