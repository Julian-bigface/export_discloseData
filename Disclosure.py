import pandas as pd
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime, timedelta
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from tkcalendar import DateEntry  # 需要安装: pip install tkcalendar
import DataCrawler


class DisclosureApp:
    """电力市场数据爬取工具"""

    def __init__(self, root):
        self.root = root
        self.root.title("电力市场数据爬取工具")
        self.root.geometry("1100x800")  # 增加高度以容纳更多功能

        # 初始化数据爬取器
        self.crawler = DataCrawler.DataCrawler()

        # 设置主题样式
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # 创建全局Cookie区域
        self.create_global_cookie_section()

        # 创建主框架和标签页
        self.create_main_tabs()

        # 初始化变量
        self.data_df = pd.DataFrame()
        self.current_station_data = None
        self.current_area_data = None

    def create_global_cookie_section(self):
        """创建全局Cookie输入区域"""
        cookie_frame = ttk.Frame(self.root)
        cookie_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(cookie_frame, text="全局CAMSID Cookie:").pack(side=tk.LEFT)
        self.cookie_var = tk.StringVar(value="BD0BC4CA235BFE5A5E9A0CA0657A4B25")
        cookie_entry = ttk.Entry(cookie_frame, textvariable=self.cookie_var, width=100)
        cookie_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

    def create_main_tabs(self):
        """创建主标签页"""
        self.tab_control = ttk.Notebook(self.root)

        # 信息披露标签页
        self.disclosure_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.disclosure_tab, text="信息披露")
        self.create_disclosure_tab()

        # 场站数据标签页
        self.station_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.station_tab, text="场站电量电价")
        self.create_station_tab()

        self.tab_control.pack(expand=1, fill="both")

    # region 信息披露爬取标签页
    def create_disclosure_tab(self):
        """创建信息披露标签页"""
        # 主框架
        main_frame = ttk.Frame(self.disclosure_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 输入区域
        self.create_disclosure_input_section(main_frame)

        # 日志区域
        self.create_log_section(main_frame)

        # 结果展示区域
        self.create_result_section(main_frame)

    def create_disclosure_input_section(self, parent):
        """创建信息披露输入区域"""
        input_frame = ttk.LabelFrame(parent, text="参数设置", padding="10")
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        # 地区选择
        ttk.Label(input_frame, text="选择地区:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.region_combo = ttk.Combobox(input_frame, values=list(self.crawler.region_codes.keys()), state="readonly")
        self.region_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.region_combo.current(4)  # 默认选择贵州

        # 日期范围选择
        ttk.Label(input_frame, text="开始日期:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.start_date = DateEntry(input_frame, width=12, background='darkblue',
                                    foreground='white', borderwidth=2, date_pattern='yy-mm-dd')
        self.start_date.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(input_frame, text="结束日期:").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        self.end_date = DateEntry(input_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, date_pattern='yy-mm-dd')
        self.end_date.grid(row=2, column=3, padx=5, pady=5, sticky=tk.W)

        # 设置默认日期（D+1）披露数据表
        today = datetime.today()
        self.start_date.set_date((today + timedelta(days=1)).strftime('%y-%m-%d'))
        self.end_date.set_date((today + timedelta(days=1)).strftime('%y-%m-%d'))

        # 火电容量设置
        ttk.Label(input_frame, text="火电开机容量(MW):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.fire_volume = tk.StringVar(value="17170")
        fire_entry = ttk.Entry(input_frame, textvariable=self.fire_volume, width=10)
        fire_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

        # 按钮区域
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=4, column=0, columnspan=4, pady=10)

        self.fetch_button = ttk.Button(button_frame, text="开始爬取", command=self.start_disclosure_crawl_thread)
        self.fetch_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(button_frame, text="保存数据", command=self.save_disclosure_data,
                                      state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.plot_button = ttk.Button(button_frame, text="显示图表", command=self.show_disclosure_plot,
                                      state=tk.DISABLED)
        self.plot_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(button_frame, text="清除日志", command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT, padx=5)

    def create_log_section(self, parent):
        """创建日志区域"""
        log_frame = ttk.LabelFrame(parent, text="日志信息", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, height=6)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.config(state=tk.DISABLED)

        # 添加初始日志
        self.log("欢迎使用电力市场信息披露爬取工具")
        self.log("请设置参数后点击'开始爬取'按钮")

    def create_result_section(self, parent):
        """创建信息披露结果展示区域"""
        result_frame = ttk.LabelFrame(parent, text="信息披露数据预览", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建表格
        columns = ("时间", "统调负荷", "新能源总出力", "非市场化机组总出力",
                   "正备用", "负备用", "火电竞价空间", "负荷率", "西电东送")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=10)

        # 设置列标题
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=80, anchor=tk.CENTER)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscroll=scrollbar.set)

        # 布局
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    # endregion

    # region 场站数据标签页
    def create_station_tab(self):
        """创建场站数据标签页"""
        # 主框架
        main_frame = ttk.Frame(self.station_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 输入区域
        self.create_station_input_section(main_frame)

        # 日志区域
        self.create_station_log_section(main_frame)

        # 结果展示区域
        self.create_station_result_section(main_frame)

    def create_station_input_section(self, parent):
        """创建场站数据输入区域"""
        input_frame = ttk.LabelFrame(parent, text="场站数据参数设置", padding="10")
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        # 场站选择
        ttk.Label(input_frame, text="选择场站:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.station_combo = ttk.Combobox(input_frame, values=list(self.crawler.station_ids.keys()), state="readonly")
        self.station_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.station_combo.current(0)  # 默认选择第一个场站

        # 日期选择
        ttk.Label(input_frame, text="选择日期:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.station_date = DateEntry(input_frame, width=12, background='darkblue',
                                      foreground='white', borderwidth=2, date_pattern='yy-mm-dd')
        self.station_date.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.station_date.set_date((datetime.today() - timedelta(days=1)).strftime('%y-%m-%d'))


        # 按钮区域
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=10)

        self.station_fetch_button = ttk.Button(button_frame, text="获取场站数据",
                                               command=self.start_station_crawl_thread)
        self.station_fetch_button.pack(side=tk.LEFT, padx=5)

        self.station_save_button = ttk.Button(button_frame, text="保存场站数据", command=self.save_station_data,
                                              state=tk.DISABLED)
        self.station_save_button.pack(side=tk.LEFT, padx=5)

        self.station_plot_button = ttk.Button(button_frame, text="显示场站图表", command=self.show_station_plot,
                                              state=tk.DISABLED)
        self.station_plot_button.pack(side=tk.LEFT, padx=5)

        self.add_station_button = ttk.Button(button_frame, text="添加场站", command=self.add_station)
        self.add_station_button.pack(side=tk.LEFT, padx=5)

    def create_station_log_section(self, parent):
        """创建场站数据日志区域"""
        log_frame = ttk.LabelFrame(parent, text="场站数据日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.station_log_area = scrolledtext.ScrolledText(log_frame, height=6)
        self.station_log_area.pack(fill=tk.BOTH, expand=True)
        self.station_log_area.config(state=tk.DISABLED)

        # 添加初始日志
        self.station_log("欢迎使用场站数据爬取功能")
        self.station_log("请选择场站和日期后点击'获取场站数据'按钮")

    def create_station_result_section(self, parent):
        """创建场站数据结果展示区域"""
        result_frame = ttk.LabelFrame(parent, text="场站数据预览", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建场站数据表格
        station_columns = ("时间", "日前电量", "日前电价", "实时电量", "实时电价")
        self.station_tree = ttk.Treeview(result_frame, columns=station_columns, show="headings", height=8)

        # 设置列标题
        for col in station_columns:
            self.station_tree.heading(col, text=col)
            self.station_tree.column(col, width=80, anchor=tk.CENTER)

        # 创建区域均价表格
        area_columns = ("区域", "发电侧日前均价", "用电侧日前均价", "发电侧实时均价", "用电侧实时均价")
        self.area_tree = ttk.Treeview(result_frame, columns=area_columns, show="headings", height=4)

        # 设置列标题
        for col in area_columns:
            self.area_tree.heading(col, text=col)
            self.area_tree.column(col, width=100, anchor=tk.CENTER)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL)

        # 使用Notebook管理两个表格
        self.station_notebook = ttk.Notebook(result_frame)

        station_frame = ttk.Frame(self.station_notebook)
        area_frame = ttk.Frame(self.station_notebook)

        self.station_notebook.add(station_frame, text="场站数据")
        self.station_notebook.add(area_frame, text="区域均价")

        self.station_tree.pack(fill=tk.BOTH, expand=True)
        self.area_tree.pack(fill=tk.BOTH, expand=True)

        self.station_notebook.pack(fill=tk.BOTH, expand=True)
    # endregion

    # region 信息披露爬取方法
    def log(self, message):
        """在日志区域添加消息"""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_area.config(state=tk.DISABLED)
        self.log_area.see(tk.END)  # 自动滚动到底部

    def clear_log(self):
        """清除日志"""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.log("日志已清除")

    def start_disclosure_crawl_thread(self):
        """启动爬取线程"""
        # 更新Cookie
        cookie = "CAMSID="+self.cookie_var.get().strip()
        if not cookie:
            messagebox.showerror("输入错误", "必须提供有效的CAMSID Cookie")
            return

        self.crawler.update_cookie(cookie)

        # 获取输入参数
        region = self.region_combo.get()
        start_date = self.start_date.get_date().strftime("%Y-%m-%d")
        end_date = self.end_date.get_date().strftime("%Y-%m-%d")

        # 验证日期
        if start_date > end_date:
            messagebox.showerror("日期错误", "结束日期不能早于开始日期")
            return

        # 更新火电容量
        try:
            self.crawler.fire_volume = float(self.fire_volume.get())
        except ValueError:
            messagebox.showerror("输入错误", "火电容量必须是数字")
            return

        # 禁用按钮
        self.fetch_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.plot_button.config(state=tk.DISABLED)

        # 清空结果树
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        # 清空数据
        self.data_df = pd.DataFrame()

        # 启动线程
        self.log(f"开始爬取 {region} 地区 {start_date} 至 {end_date} 的数据...")
        thread = threading.Thread(
            target=self.crawl_disclosure_data,
            args=(start_date, end_date, region),
            daemon=True
        )
        thread.start()

    def crawl_disclosure_data(self, start_date, end_date, region):
        """爬取数据"""
        # 使用生成器逐步获取数据
        for result, is_final in self.crawler.get_public_information_by_date_range(start_date, end_date, region):
            if isinstance(result, pd.DataFrame):
                # 最终结果是一个DataFrame
                self.data_df = result
                self.root.after(0, self.update_disclosure_results)
            elif isinstance(result, str) and is_final:
                # 最终结果是一个错误消息
                self.log(result)
                self.root.after(0, self.enable_fetch_button)
            else:
                # 中间进度消息
                self.log(result)

        # 如果没有数据，启用按钮
        if self.data_df.empty:
            self.root.after(0, self.enable_fetch_button)

    def update_disclosure_results(self):
        """更新结果展示区域"""
        # 清空现有数据
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        # 添加新数据（只显示前100行，避免卡顿）
        sample_df = self.data_df.head(100) if len(self.data_df) > 100 else self.data_df

        for idx, row in sample_df.iterrows():
            values = (
                idx,
                row.get('统调负荷', ''),
                row.get('新能源总出力（日）', ''),
                row.get('非市场化机组总出力', ''),
                row.get('正备用', ''),
                row.get('负备用', ''),
                row.get('火电竞价空间', ''),
                row.get('负荷率', ''),
                row.get('西电东送', '')
            )
            self.result_tree.insert("", tk.END, values=values)

        # 显示统计信息
        if not self.data_df.empty:
            start_time = self.data_df.index.min()
            end_time = self.data_df.index.max()
            num_records = len(self.data_df)

            self.log(f"数据爬取完成: 共 {num_records} 条记录")
            self.log(f"时间范围: {start_time} 至 {end_time}")

            # 显示各列的平均值
            for col in ['统调负荷', '新能源总出力（日）', '非市场化机组总出力', '火电竞价空间', '西电东送']:
                if col in self.data_df.columns:
                    try:
                        avg_value = self.data_df[col].mean()
                        self.log(f"{col} 平均值: {avg_value:.2f} MW")
                    except:
                        pass

        # 启用按钮
        self.save_button.config(state=tk.NORMAL)
        self.plot_button.config(state=tk.NORMAL)
        self.fetch_button.config(state=tk.NORMAL)

    def enable_fetch_button(self):
        """启用爬取按钮"""
        self.fetch_button.config(state=tk.NORMAL)
        self.log("数据爬取过程已结束")

    def save_disclosure_data(self):
        """保存数据到Excel文件"""
        if self.data_df.empty:
            messagebox.showerror("保存错误", "没有数据可保存")
            return

        # 生成文件名
        region = self.region_combo.get()
        start_date = self.start_date.get_date().strftime("%Y%m%d")
        end_date = self.end_date.get_date().strftime("%Y%m%d")

        # 弹出保存对话框
        file_path = filedialog.asksaveasfilename(
            initialfile=f"{region}_{start_date}_to_{end_date}_披露数据.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            # 保存数据
            self.data_df.to_excel(file_path, index=True, index_label='时间')
            self.log(f"数据已保存到: {file_path}")
            messagebox.showinfo("保存成功", f"数据已保存到:\n{file_path}")
        except Exception as e:
            self.log(f"保存失败: {str(e)}")
            messagebox.showerror("保存错误", f"保存失败: {str(e)}")

    def show_disclosure_plot(self):
        """显示数据图表"""
        if self.data_df.empty:
            messagebox.showerror("图表错误", "没有数据可显示")
            return

        try:
            # 创建新窗口
            plot_window = tk.Toplevel(self.root)
            plot_window.title("电力市场披露信息趋势图")
            plot_window.geometry("1200x800")

            # 创建图表
            fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)

            # 准备数据
            df = self.data_df.copy()
            df.index = pd.to_datetime(df.index)

            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置黑体
            plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

            # 绘制负荷相关曲线
            if '统调负荷' in df.columns:
                df['统调负荷'].plot(ax=axes[0], label='统调负荷', color='blue')
            if '新能源总出力（日）' in df.columns:
                df['新能源总出力（日）'].plot(ax=axes[0], label='新能源总出力', color='green')
            if '非市场化机组总出力' in df.columns:
                df['非市场化机组总出力'].plot(ax=axes[0], label='非市场化机组总出力', color='red')

            axes[0].set_title("负荷与出力趋势")
            axes[0].set_ylabel("功率 (MW)")
            axes[0].grid(True)
            axes[0].legend()

            # 绘制备用曲线
            if '正备用' in df.columns:
                df['正备用'].plot(ax=axes[1], label='正备用', color='purple')
            if '负备用' in df.columns:
                df['负备用'].plot(ax=axes[1], label='负备用', color='orange')

            axes[1].set_title("备用容量趋势")
            axes[1].set_ylabel("功率 (MW)")
            axes[1].grid(True)
            axes[1].legend()

            # 绘制火电相关曲线
            if '火电竞价空间' in df.columns:
                df['火电竞价空间'].plot(ax=axes[2], label='火电竞价空间', color='brown')
            if '西电东送' in df.columns:
                df['西电东送'].plot(ax=axes[2], label='西电东送', color='cyan')

            axes[2].set_title("火电与西电东送趋势")
            axes[2].set_ylabel("功率 (MW)")
            axes[2].grid(True)
            axes[2].legend()

            # 格式化x轴日期
            fig.autofmt_xdate()

            # 在Tkinter窗口中显示图表
            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            self.log("图表已显示")

        except Exception as e:
            self.log(f"图表生成失败: {str(e)}")
            messagebox.showerror("图表错误", f"图表生成失败: {str(e)}")
    # endregion

    # region 场站数据爬取方法
    def station_log(self, message):
        """在场站数据日志区域添加消息"""
        self.station_log_area.config(state=tk.NORMAL)
        self.station_log_area.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.station_log_area.config(state=tk.DISABLED)
        self.station_log_area.see(tk.END)

    def start_station_crawl_thread(self):
        """启动场站数据爬取线程"""
        # 更新Cookie
        cookie = "CAMSID="+self.cookie_var.get().strip()
        if not cookie:
            messagebox.showerror("输入错误", "必须提供有效的CAMSID Cookie")
            return

        self.crawler.update_cookie(cookie)

        # 获取输入参数
        station_name = self.station_combo.get()
        run_time = self.station_date.get_date().strftime("%Y-%m-%d")

        # 禁用按钮
        self.station_fetch_button.config(state=tk.DISABLED)
        self.station_save_button.config(state=tk.DISABLED)
        self.station_plot_button.config(state=tk.DISABLED)

        # 清空结果树
        for item in self.station_tree.get_children():
            self.station_tree.delete(item)
        for item in self.area_tree.get_children():
            self.area_tree.delete(item)

        # 启动线程
        self.station_log(f"开始获取 {station_name} {run_time} 的场站数据...")
        thread = threading.Thread(
            target=self.crawl_station_data,
            args=(station_name, run_time),
            daemon=True
        )
        thread.start()

    def crawl_station_data(self, station_name, run_time):
        """爬取场站数据"""
        try:
            station_df, area_df, error = self.crawler.get_station_data(station_name, run_time)

            # 不管有无错误，都先更新 UI
            self.current_station_data = station_df
            self.current_area_data = area_df

            self.root.after(0, lambda: self.update_station_results(station_df, area_df))

            # 错误信息单独处理
            if error:
                self.station_log(error)

        except Exception as e:
            self.station_log(f"获取场站数据失败: {str(e)}")
        finally:
            # 保证按钮总能恢复
            self.root.after(0, self.enable_station_fetch_button)

    def update_station_results(self, station_df, area_df):
        """更新场站数据结果展示区域"""
        # 清空现有数据
        for item in self.station_tree.get_children():
            self.station_tree.delete(item)
        for item in self.area_tree.get_children():
            self.area_tree.delete(item)

        # 添加场站数据
        sample_df = station_df.head(100) if len(station_df) > 100 else station_df
        for idx, row in sample_df.iterrows():
            values = (
                idx,
                row.get('日前电量', ''),
                row.get('日前电价', ''),
                row.get('实时电量', ''),
                row.get('实时电价', '')
            )
            self.station_tree.insert("", tk.END, values=values)

        # 添加区域均价数据
        for idx, row in area_df.iterrows():
            values = (
                idx,
                row.get('发电侧_日前平均电价', ''),
                row.get('用电侧_日前平均电价', ''),
                row.get('发电侧_实时平均电价', ''),
                row.get('用电侧_实时平均电价', '')
            )
            self.area_tree.insert("", tk.END, values=values)

        # 显示统计信息
        self.station_log(f"场站数据获取完成: 共 {len(station_df)} 条记录")

        # 启用按钮
        self.station_save_button.config(state=tk.NORMAL)
        self.station_plot_button.config(state=tk.NORMAL)
        self.station_fetch_button.config(state=tk.NORMAL)

    def enable_station_fetch_button(self):
        """启出场站数据获取按钮"""
        self.station_fetch_button.config(state=tk.NORMAL)
        self.station_log("场站数据获取过程已结束")

    def save_station_data(self):
        """保存场站数据到Excel文件"""
        if self.current_station_data is None or self.current_area_data is None:
            messagebox.showerror("保存错误", "没有数据可保存")
            return

        # 生成文件名
        station_name = self.station_combo.get()
        run_time = self.station_date.get_date().strftime("%Y%m%d")
        default_filename = f"{station_name}_{run_time}_场站数据.xlsx"

        # 弹出保存对话框
        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            # 保存数据
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                self.current_station_data.to_excel(writer, sheet_name='场站数据', index=True, index_label='时间')
                self.current_area_data.to_excel(writer, sheet_name='区域均价', index=True, index_label='区域')

            self.station_log(f"场站数据已保存到: {file_path}")
            messagebox.showinfo("保存成功", f"场站数据已保存到:\n{file_path}")
        except Exception as e:
            self.station_log(f"保存失败: {str(e)}")
            messagebox.showerror("保存错误", f"保存失败: {str(e)}")

    def show_station_plot(self):
        """显示场站数据图表"""
        if self.current_station_data is None:
            messagebox.showerror("图表错误", "没有数据可显示")
            return

        try:
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置黑体
            plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

            # 创建新窗口
            plot_window = tk.Toplevel(self.root)
            plot_window.title("场站数据趋势图")
            plot_window.geometry("1200x800")

            # 创建图表
            fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

            # 准备数据
            df = self.current_station_data.copy()
            df.index = pd.to_datetime(df.index)

            # 绘制电量曲线
            if '日前电量' in df.columns:
                df['日前电量'].plot(ax=axes[0], label='日前电量', color='blue')
            if '实时电量' in df.columns:
                df['实时电量'].plot(ax=axes[0], label='实时电量', color='green')

            axes[0].set_title("电量趋势")
            axes[0].set_ylabel("电量 (MWh)")
            axes[0].grid(True)
            axes[0].legend()

            # 绘制电价曲线
            if '日前电价' in df.columns:
                df['日前电价'].plot(ax=axes[1], label='日前电价', color='red')
            if '实时电价' in df.columns:
                df['实时电价'].plot(ax=axes[1], label='实时电价', color='purple')

            axes[1].set_title("电价趋势")
            axes[1].set_ylabel("电价 (元/MWh)")
            axes[1].grid(True)
            axes[1].legend()

            # 格式化x轴日期
            fig.autofmt_xdate()

            # 在Tkinter窗口中显示图表
            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            self.station_log("场站数据图表已显示")

        except Exception as e:
            self.station_log(f"图表生成失败: {str(e)}")
            messagebox.showerror("图表错误", f"图表生成失败: {str(e)}")

    def add_station(self):
        """添加新场站"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加场站")
        dialog.geometry("400x200")

        ttk.Label(dialog, text="场站名称:").grid(row=0, column=0, padx=10, pady=10)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="场站ID:").grid(row=1, column=0, padx=10, pady=10)
        id_entry = ttk.Entry(dialog, width=30)
        id_entry.grid(row=1, column=1, padx=10, pady=10)

        def save_station():
            name = name_entry.get().strip()
            station_id = id_entry.get().strip()

            if not name or not station_id:
                messagebox.showerror("输入错误", "场站名称和ID不能为空")
                return

            if name in self.crawler.station_ids:
                messagebox.showerror("错误", f"场站 '{name}' 已存在")
                return

            self.crawler.station_ids[name] = station_id
            self.station_combo['values'] = list(self.crawler.station_ids.keys())
            messagebox.showinfo("成功", f"场站 '{name}' 已添加")
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="保存", command=save_station).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    # endregion


if __name__ == "__main__":
    root = tk.Tk()
    app = DisclosureApp(root)
    root.mainloop()