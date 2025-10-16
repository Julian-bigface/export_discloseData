import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkcalendar import DateEntry
import pandas as pd
import threading
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from Util.JsonStore import JsonStore

class StationTab:
    def __init__(self, parent, crawler, cookie_var):
        self.crawler = crawler
        self.cookie_var = cookie_var
        self.current_station_data = None
        self.current_area_data = None

        # JSON 存储文件
        self.station_store = JsonStore("stations.json")

        self.frame = ttk.Frame(parent)
        self.create_input_section()
        self.create_log_section()
        self.create_result_section()

    def create_input_section(self):
        input_frame = ttk.LabelFrame(self.frame, text="场站数据参数设置", padding="10")
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="选择场站:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        station_names = list(self.station_store.get_all().keys())
        self.station_combo = ttk.Combobox(input_frame, values=station_names, state="readonly")
        self.station_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        if station_names:  # 只有有数据时才设置默认选中
            self.station_combo.current(0)

        ttk.Label(input_frame, text="选择日期:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.station_date = DateEntry(input_frame, width=12, background='darkblue',
                                      foreground='white', borderwidth=2, date_pattern='yy-mm-dd')
        self.station_date.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.station_date.set_date((datetime.today() - timedelta(days=1)).strftime('%y-%m-%d'))

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=10)

        self.station_fetch_button = ttk.Button(button_frame, text="获取场站数据", command=self.start_crawl)
        self.station_fetch_button.pack(side=tk.LEFT, padx=5)

        self.station_save_button = ttk.Button(button_frame, text="保存场站数据", command=self.save_data, state=tk.DISABLED)
        self.station_save_button.pack(side=tk.LEFT, padx=5)

        self.station_plot_button = ttk.Button(button_frame, text="显示场站图表", command=self.show_plot, state=tk.DISABLED)
        self.station_plot_button.pack(side=tk.LEFT, padx=5)

        self.speech_button = ttk.Button(button_frame, text="话术编辑", command=self.open_speech_editor,state=tk.DISABLED)
        self.speech_button.pack(side=tk.LEFT, padx=5)

        self.add_station_button = ttk.Button(button_frame, text="场站管理", command=self.open_station_manager)
        self.add_station_button.pack(side=tk.LEFT, padx=5)

    def create_log_section(self):
        log_frame = ttk.LabelFrame(self.frame, text="场站数据日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.station_log_area = scrolledtext.ScrolledText(log_frame, height=6)
        self.station_log_area.pack(fill=tk.BOTH, expand=True)
        self.station_log_area.config(state=tk.DISABLED)

        self.log("欢迎使用场站数据爬取功能")
        self.log("请选择场站和日期后点击'获取场站数据'按钮")

    def create_result_section(self):
        result_frame = ttk.LabelFrame(self.frame, text="场站数据预览", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建Notebook
        self.station_notebook = ttk.Notebook(result_frame)
        self.station_notebook.pack(fill=tk.BOTH, expand=True)

        # 创建场站数据标签页
        station_columns = ("时间", "日前电量", "日前电价", "实时电量", "实时电价")
        station_frame = ttk.Frame(self.station_notebook)
        self.station_tree = ttk.Treeview(station_frame, columns=station_columns, show="headings", height=8)
        for col in station_columns:
            self.station_tree.heading(col, text=col)
            self.station_tree.column(col, width=80, anchor=tk.CENTER)
        # 添加滚动条
        station_scroll = ttk.Scrollbar(station_frame, orient="vertical", command=self.station_tree.yview)
        self.station_tree.configure(yscrollcommand=station_scroll.set)

        # 布局场站表格
        self.station_tree.pack(side="left", fill="both", expand=True)
        station_scroll.pack(side="right", fill="y")

        area_columns = ("区域", "发电侧日前均价", "用电侧日前均价", "发电侧实时均价", "用电侧实时均价")
        area_frame = ttk.Frame(self.station_notebook)
        self.area_tree = ttk.Treeview(area_frame, columns=area_columns, show="headings", height=4)
        for col in area_columns:
            self.area_tree.heading(col, text=col)
            self.area_tree.column(col, width=100, anchor=tk.CENTER)

        # 添加滚动条
        area_scroll = ttk.Scrollbar(area_frame, orient="vertical", command=self.area_tree.yview)
        self.area_tree.configure(yscrollcommand=area_scroll.set)

        # 布局区域表格
        self.area_tree.pack(side="left", fill="both", expand=True)
        area_scroll.pack(side="right", fill="y")

        # 添加标签页到Notebook
        self.station_notebook.add(station_frame, text="场站数据")
        self.station_notebook.add(area_frame, text="区域均价")

    def log(self, message):
        self.station_log_area.config(state=tk.NORMAL)
        self.station_log_area.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.station_log_area.config(state=tk.DISABLED)
        self.station_log_area.see(tk.END)

    def start_crawl(self):
        cookie = "CAMSID=" + self.cookie_var.get().strip()
        if not cookie:
            messagebox.showerror("输入错误", "必须提供有效的CAMSID Cookie")
            return
        self.crawler.update_cookie(cookie)

        station_name = self.station_combo.get()
        run_time = self.station_date.get_date().strftime("%Y-%m-%d")

        self.station_fetch_button.config(state=tk.DISABLED)
        self.station_save_button.config(state=tk.DISABLED)
        self.station_plot_button.config(state=tk.DISABLED)

        for item in self.station_tree.get_children():
            self.station_tree.delete(item)
        for item in self.area_tree.get_children():
            self.area_tree.delete(item)

        self.log(f"开始获取 {station_name} {run_time} 的场站数据...")
        thread = threading.Thread(target=self.crawl_data, args=(station_name, run_time), daemon=True)
        thread.start()

    def crawl_data(self, station_name, run_time):
        try:
            unit_id = self.station_store.data[station_name]
            station_df, area_df, error = self.crawler.get_station_data(station_name, unit_id, run_time)
            self.current_station_data = station_df
            self.current_area_data = area_df
            if error:
                self.log(error)
            self.frame.after(0, lambda: self.update_results(station_df, area_df))
        except Exception as e:
            self.log(f"获取场站数据失败: {str(e)}")
        finally:
            self.frame.after(0, self.enable_fetch_button)

    def update_results(self, station_df, area_df):
        for item in self.station_tree.get_children():
            self.station_tree.delete(item)
        for item in self.area_tree.get_children():
            self.area_tree.delete(item)

        sample_df = station_df.head(100) if len(station_df) > 100 else station_df
        for idx, row in sample_df.iterrows():
            values = (idx, row.get('日前电量', ''), row.get('日前电价', ''),
                      row.get('实时电量', ''), row.get('实时电价', ''))
            self.station_tree.insert("", tk.END, values=values)

        for idx, row in area_df.iterrows():
            values = (idx, row.get('发电侧_日前平均电价', ''),
                      row.get('用电侧_日前平均电价', ''),
                      row.get('发电侧_实时平均电价', ''),
                      row.get('用电侧_实时平均电价', ''))
            self.area_tree.insert("", tk.END, values=values)

        self.log(f"场站数据获取完成: 共 {len(station_df)} 条记录")
        self.station_save_button.config(state=tk.NORMAL)
        self.station_plot_button.config(state=tk.NORMAL)
        self.station_fetch_button.config(state=tk.NORMAL)
        self.speech_button.config(state=tk.NORMAL)

    def enable_fetch_button(self):
        self.station_fetch_button.config(state=tk.NORMAL)
        self.log("场站数据获取过程已结束")

    def save_data(self):
        if self.current_station_data is None or self.current_area_data is None:
            messagebox.showerror("保存错误", "没有数据可保存")
            return

        station_name = self.station_combo.get()
        run_time = self.station_date.get_date().strftime("%Y%m%d")
        default_filename = f"{station_name}_{run_time}_场站数据.xlsx"
        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        if not file_path:
            return
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            self.current_station_data.to_excel(writer, sheet_name='场站数据', index=True, index_label='时间')
            self.current_area_data.to_excel(writer, sheet_name='区域均价', index=True, index_label='区域')
        self.log(f"场站数据已保存到: {file_path}")

    def show_plot(self):
        if self.current_station_data is None:
            messagebox.showerror("图表错误", "没有数据可显示")
            return

        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        plot_window = tk.Toplevel(self.frame)
        plot_window.title("场站数据趋势图")
        plot_window.geometry("1200x800")

        fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        df = self.current_station_data.copy()
        df.index = pd.to_datetime(df.index)

        if '日前电量' in df.columns:
            df['日前电量'].plot(ax=axes[0], label='日前电量', color='blue')
        if '实时电量' in df.columns:
            df['实时电量'].plot(ax=axes[0], label='实时电量', color='green')
        axes[0].set_title("电量趋势")
        axes[0].set_ylabel("电量 (MWh)")
        axes[0].grid(True)
        axes[0].legend()

        if '日前电价' in df.columns:
            df['日前电价'].plot(ax=axes[1], label='日前电价', color='red')
        if '实时电价' in df.columns:
            df['实时电价'].plot(ax=axes[1], label='实时电价', color='purple')
        axes[1].set_title("电价趋势")
        axes[1].set_ylabel("电价 (元/MWh)")
        axes[1].grid(True)
        axes[1].legend()

        fig.autofmt_xdate()
        canvas = FigureCanvasTkAgg(fig, master=plot_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.log("场站数据图表已显示")

    # region---------- 场站管理 ----------
    def open_station_manager(self):
        win = tk.Toplevel(self.frame)
        win.title("场站管理")
        win.geometry("650x450")

        # -------- 工具栏按钮 --------
        toolbar = ttk.Frame(win)
        toolbar.pack(fill=tk.X, pady=5)

        ttk.Button(toolbar, text="新增", style="Toolbutton.TButton", command=lambda: add_station()).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="修改", style="Toolbutton.TButton", command=lambda: edit_station()).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="删除", style="Toolbutton.TButton", command=lambda: delete_station()).pack(side=tk.LEFT, padx=3)

        # -------- 场站列表 --------
        columns = ("场站名称", "场站ID")
        station_tree = ttk.Treeview(win, columns=columns, show="headings", height=15)
        for col in columns:
            station_tree.heading(col, text=col)
            station_tree.column(col, width=280 if col == "场站名称" else 320, anchor=tk.CENTER)
        station_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(station_tree, orient=tk.VERTICAL, command=station_tree.yview)
        station_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ✅ 每次打开都重新读取 JSON
        self.station_store.load()
        for name, station_id in self.station_store.get_all().items():
            station_tree.insert("", tk.END, values=(name, station_id))

        # ✅ 同步刷新 combobox
        station_names = list(self.station_store.get_all().keys())
        self.station_combo["values"] = station_names
        if station_names:
            self.station_combo.current(0)

        # -------- 功能函数 --------
        def add_station():
            sub = tk.Toplevel(win)
            sub.title("新增场站")
            sub.geometry("400x200")

            tk.Label(sub, text="场站名称:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
            name_entry = tk.Entry(sub, width=35)
            name_entry.grid(row=0, column=1, padx=10, pady=10)

            tk.Label(sub, text="场站ID:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
            id_entry = tk.Entry(sub, width=35)
            id_entry.grid(row=1, column=1, padx=10, pady=10)

            def save():
                name, station_id = name_entry.get().strip(), id_entry.get().strip()
                if name and station_id:
                    self.station_store.set(name, station_id)  # ✅ 存入 JSON
                    station_tree.insert("", tk.END, values=(name, station_id))
                    self.station_combo["values"] = list(self.station_store.get_all().keys())
                    sub.destroy()

            ttk.Button(sub, text="保存", command=save).grid(row=2, column=0, columnspan=2, pady=15)

        def delete_station():
            selected = station_tree.selection()
            if not selected:
                messagebox.showwarning("提示", "请先选择一个场站")
                return

            item = station_tree.item(selected[0])
            name, station_id = item["values"]

            if messagebox.askyesno("确认删除", f"确定要删除场站：{name}?"):
                self.station_store.delete(name)  # ✅ 删除 JSON
                station_tree.delete(selected[0])
                self.station_combo["values"] = list(self.station_store.get_all().keys())

        def edit_station():
            selected = station_tree.selection()
            if not selected:
                messagebox.showwarning("提示", "请先选择一个场站")
                return

            item = station_tree.item(selected[0])
            old_name, old_id = item["values"]

            sub = tk.Toplevel(win)
            sub.title("修改场站")
            sub.geometry("400x200")

            tk.Label(sub, text="场站名称:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
            name_entry = tk.Entry(sub, width=35)
            name_entry.insert(0, old_name)
            name_entry.grid(row=0, column=1, padx=10, pady=10)

            tk.Label(sub, text="场站ID:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
            id_entry = tk.Entry(sub, width=35)
            id_entry.insert(0, old_id)
            id_entry.grid(row=1, column=1, padx=10, pady=10)

            def save():
                new_name, new_id = name_entry.get().strip(), id_entry.get().strip()
                if new_name and new_id:
                    if old_name in self.station_store.get_all():
                        self.station_store.delete(old_name)
                    self.station_store.set(new_name, new_id)

                    # 更新 Treeview
                    station_tree.item(selected[0], values=(new_name, new_id))
                    self.station_combo["values"] = list(self.station_store.get_all().keys())
                    sub.destroy()

            ttk.Button(sub, text="保存修改", command=save).grid(row=2, column=0, columnspan=2, pady=15)
    # endregion

    def open_speech_editor(self):
        if self.current_area_data is None or self.current_area_data.empty:
            messagebox.showerror("错误", "请先获取场站数据")
            return

        win = tk.Toplevel(self.frame)
        win.title("话术编辑")
        win.geometry("800x400")

        # 选择类型
        type_var = tk.StringVar(value="日前")
        ttk.Radiobutton(win, text="日前", variable=type_var, value="日前").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(win, text="实时", variable=type_var, value="实时").pack(anchor=tk.W, pady=2)

        # 文本框
        text_box = scrolledtext.ScrolledText(win, wrap=tk.WORD, height=15)
        text_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def generate_text():
            type_label = type_var.get()
            date_str = self.station_date.get_date().strftime("%m月%d日")
            df = self.current_area_data

            provinces = ["广东", "广西", "云南", "贵州", "海南"]
            if type_label == "日前":
                gen_side = [f"{p}{df.loc[p, '发电侧_日前平均电价']/1000:.3f}元/千瓦时" for p in provinces]
                use_side = [f"{p}{df.loc[p, '用电侧_日前平均电价']/1000:.3f}元/千瓦时" for p in provinces]
                text = f"{date_str}南方区域发电侧日前电价" + "，".join(gen_side) + "。" \
                                                                                  f"用电侧日前电价" + "，".join(
                    use_side) + "。"
            else:
                gen_side = [f"{p}{df.loc[p, '发电侧_实时平均电价']/1000:.3f}元/千瓦时" for p in provinces]
                use_side = [f"{p}{df.loc[p, '用电侧_实时平均电价']/1000:.3f}元/千瓦时" for p in provinces]
                text = f"{date_str}南方区域发电侧实时电价" + "，".join(gen_side) + "。" \
                                                                                  f"用电侧实时电价" + "，".join(
                    use_side) + "。"

            text_box.delete("1.0", tk.END)
            text_box.insert(tk.END, text)

        def copy_text():
            self.frame.clipboard_clear()
            self.frame.clipboard_append(text_box.get("1.0", tk.END).strip())
            self.frame.update()
            messagebox.showinfo("成功", "已复制到剪贴板")

        # 按钮
        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="生成", command=generate_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="复制", command=copy_text).pack(side=tk.LEFT, padx=5)

