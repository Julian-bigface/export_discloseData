import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkcalendar import DateEntry
import pandas as pd
import threading
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from Util.JsonStore import JsonStore

class NodePriceTab:
    """
    节点电价页面（多日）
    - 从 DataCrawler 调用 collect_multi_days_prices(start, end)
    - UI 结构与 DisclosureTab 一致：参数设置 / 日志 / 结果预览
    """
    def __init__(self, parent, crawler, cookie_var):
        self.crawler = crawler
        self.cookie_var = cookie_var
        self.data_df = pd.DataFrame()

        # 节点存储
        self.node_store = JsonStore("nodes.json")

        self.frame = ttk.Frame(parent)
        self.create_input_section()
        self.create_log_section()
        self.create_result_section()

    # ---------- UI: 参数设置 ----------
    def create_input_section(self):
        input_frame = ttk.LabelFrame(self.frame, text="参数设置", padding="10")
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        # 日期范围
        ttk.Label(input_frame, text="开始日期:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.start_date = DateEntry(
            input_frame, width=12, background="darkblue", foreground="white",
            borderwidth=2, date_pattern="yy-mm-dd"
        )
        self.start_date.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(input_frame, text="结束日期:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.end_date = DateEntry(
            input_frame, width=12, background="darkblue", foreground="white",
            borderwidth=2, date_pattern="yy-mm-dd"
        )
        self.end_date.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        # 默认：当天
        today = datetime.today()
        self.start_date.set_date(today.strftime("%y-%m-%d"))
        self.end_date.set_date(today.strftime("%y-%m-%d"))

        # 按钮区
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=8)

        self.fetch_button = ttk.Button(btn_frame, text="开始爬取", command=self.start_crawl)
        self.fetch_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(btn_frame, text="保存数据", command=self.save_data, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.plot_button = ttk.Button(btn_frame, text="显示图表", command=self.show_plot, state=tk.DISABLED)
        self.plot_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(btn_frame, text="清除日志", command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.node_button = ttk.Button(btn_frame, text="节点管理", command=self.open_node_manager)
        self.node_button.pack(side=tk.LEFT, padx=5)

    # ---------- UI: 日志 ----------
    def create_log_section(self):
        log_frame = ttk.LabelFrame(self.frame, text="日志信息", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, height=6)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.config(state=tk.DISABLED)

        # 进度条
        self.progress = ttk.Progressbar(self.frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X,padx=5,pady=5)

        self.log("欢迎使用节点电价爬取工具")
        self.log("请选择日期范围后点击“开始爬取”")

    # ---------- UI: 结果表格 ----------
    def create_result_section(self):
        result_frame = ttk.LabelFrame(self.frame, text="节点电价数据预览", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.result_tree = ttk.Treeview(result_frame, columns=("时间",), show="headings", height=12)

        # 竖向滚动条
        scrollbar_y = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscroll=scrollbar_y.set)

        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

    # region---------- 节点管理 ----------
    def open_node_manager(self):
        win = tk.Toplevel(self.frame)
        win.title("节点管理")
        win.geometry("650x450")

        # -------- 工具栏按钮 --------
        toolbar = ttk.Frame(win)
        toolbar.pack(fill=tk.X, pady=5)

        ttk.Button(toolbar, text="新增", style="Toolbutton.TButton", command=lambda: add_node()).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="修改", style="Toolbutton.TButton", command=lambda: edit_node()).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="删除", style="Toolbutton.TButton", command=lambda: delete_node()).pack(side=tk.LEFT, padx=3)

        # -------- 节点列表 --------
        columns = ("节点名称", "节点ID")
        node_tree = ttk.Treeview(win, columns=columns, show="headings", height=15)
        for col in columns:
            node_tree.heading(col, text=col)
            node_tree.column(col, width=280 if col == "节点名称" else 320, anchor=tk.CENTER)
        node_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(node_tree, orient=tk.VERTICAL, command=node_tree.yview)
        node_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 载入当前节点
        self.node_store = JsonStore("nodes.json")#每次打开重新读取一次
        for name, node_id in self.node_store.get_all().items():
            node_tree.insert("", tk.END, values=(name, node_id))

        # -------- 功能函数 --------
        def add_node():
            sub = tk.Toplevel(win)
            sub.title("新增节点")
            sub.geometry("400x200")

            tk.Label(sub, text="节点名称:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
            name_entry = tk.Entry(sub, width=35)
            name_entry.grid(row=0, column=1, padx=10, pady=10)

            tk.Label(sub, text="节点ID:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
            id_entry = tk.Entry(sub, width=35)
            id_entry.grid(row=1, column=1, padx=10, pady=10)

            def save():
                name, node_id = name_entry.get().strip(), id_entry.get().strip()
                if name and node_id:
                    self.node_store.set(name, node_id)  # ✅ 存入 JSON
                    node_tree.insert("", tk.END, values=(name, node_id))
                    sub.destroy()

            ttk.Button(sub, text="保存", command=save).grid(row=2, column=0, columnspan=2, pady=15)

        def delete_node():
            selected = node_tree.selection()
            if not selected:
                messagebox.showwarning("提示", "请先选择一个节点")
                return

            item = node_tree.item(selected[0])
            name, node_id = item["values"]

            if messagebox.askyesno("确认删除", f"确定要删除节点：{name}?"):
                self.node_store.delete(name)  # ✅ 删除 JSON
                node_tree.delete(selected[0])

        def edit_node():
            selected = node_tree.selection()
            if not selected:
                messagebox.showwarning("提示", "请先选择一个节点")
                return

            item = node_tree.item(selected[0])
            old_name, old_id = item["values"]

            sub = tk.Toplevel(win)
            sub.title("修改节点")
            sub.geometry("400x200")

            tk.Label(sub, text="节点名称:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
            name_entry = tk.Entry(sub, width=35)
            name_entry.insert(0, old_name)
            name_entry.grid(row=0, column=1, padx=10, pady=10)

            tk.Label(sub, text="节点ID:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
            id_entry = tk.Entry(sub, width=35)
            id_entry.insert(0, old_id)
            id_entry.grid(row=1, column=1, padx=10, pady=10)

            def save():
                new_name, new_id = name_entry.get().strip(), id_entry.get().strip()
                if new_name and new_id:
                    # 删除旧的，保存新的
                    if old_name in self.node_store.get_all():
                        self.node_store.delete(old_name)
                    self.node_store.set(new_name, new_id)

                    # 更新 Treeview
                    node_tree.item(selected[0], values=(new_name, new_id))
                    sub.destroy()

            ttk.Button(sub, text="保存修改", command=save).grid(row=2, column=0, columnspan=2, pady=15)
    # endregion

    # ---------- 日志函数 ----------
    def log(self, message: str):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_area.config(state=tk.DISABLED)
        self.log_area.see(tk.END)

    def clear_log(self):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.log("日志已清除")

    # ---------- 爬取逻辑 ----------
    def start_crawl(self):
        # 更新 Cookie
        cookie = "CAMSID=" + self.cookie_var.get().strip()
        if not cookie or cookie == "CAMSID=":
            messagebox.showerror("输入错误", "必须提供有效的 CAMSID Cookie")
            return
        self.crawler.update_cookie(cookie)

        # 读取日期
        start_date = self.start_date.get_date().strftime("%Y-%m-%d")
        end_date = self.end_date.get_date().strftime("%Y-%m-%d")
        if start_date > end_date:
            messagebox.showerror("日期错误", "结束日期不能早于开始日期")
            return

        # 禁用按钮
        self.fetch_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.plot_button.config(state=tk.DISABLED)

        # 清空表格
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        self.data_df = pd.DataFrame()
        self.log(f"开始爬取 {start_date} 至 {end_date} 的节点电价数据...")

        thread = threading.Thread(
            target=self.crawl_data,
            args=(start_date, end_date),
            daemon=True
        )
        thread.start()

    def crawl_data(self, start_date: str, end_date: str):
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)

            node_ids = self.node_store.get_all()
            if not node_ids:
                self.log(f"节点列表为空，请添加所需节点")
                return
            self.progress.config(maximum=2*len(node_ids))#设置最大值

            def update_progress(value,log=None):
                self.frame.after(0,lambda:self.progress.config(value=value))
                if log is not None:
                    self.log(log)

            df = self.crawler.collect_multi_days_prices(start, end, node_ids, progress_callback=update_progress)
            self.data_df = df
            self.frame.after(0, self.update_results)

        except Exception as e:
            self.log(f"获取失败：{e}")
            self.frame.after(0, lambda: self.fetch_button.config(state=tk.NORMAL))

    # ---------- 更新表格 ----------
    def update_results(self):
        # 设置列
        columns = ["时间"] + list(self.data_df.columns)
        self.result_tree["columns"] = columns
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=110 if col == "时间" else 100, anchor=tk.CENTER)

        # 插入数据（最多显示前 300 行，避免卡顿）
        self.result_tree.delete(*self.result_tree.get_children())
        preview_df = self.data_df.head(300) if len(self.data_df) > 300 else self.data_df
        for idx, row in preview_df.iterrows():
            ts = pd.to_datetime(idx)
            values = [ts.strftime("%Y-%m-%d %H:%M")] + [("" if pd.isna(v) else v) for v in row.tolist()]
            self.result_tree.insert("", tk.END, values=values)

        # 统计信息
        self.log(f"数据爬取完成：共 {len(self.data_df)} 条 15 分钟数据点")
        if len(self.data_df) > 0:
            self.log(f"时间范围：{self.data_df.index.min()} ~ {self.data_df.index.max()}")

        # 启用按钮
        self.save_button.config(state=tk.NORMAL)
        self.plot_button.config(state=tk.NORMAL)
        self.fetch_button.config(state=tk.NORMAL)

    # ---------- 保存 ----------
    def save_data(self):
        if self.data_df.empty:
            messagebox.showerror("保存错误", "没有数据可保存")
            return

        start_date = self.start_date.get_date().strftime("%Y%m%d")
        end_date = self.end_date.get_date().strftime("%Y%m%d")
        file_path = filedialog.asksaveasfilename(
            initialfile=f"节点电价_{start_date}_to_{end_date}.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        if not file_path:
            return

        try:
            self.data_df.to_excel(file_path, index=True, index_label="时间")
            self.log(f"数据已保存到: {file_path}")
            messagebox.showinfo("保存成功", f"数据已保存到:\n{file_path}")
        except Exception as e:
            self.log(f"保存失败：{e}")
            messagebox.showerror("保存错误", f"保存失败：{e}")

    # ---------- 图表 ----------
    def show_plot(self):
        if self.data_df.empty:
            messagebox.showerror("图表错误", "没有数据可显示")
            return

        try:
            # 准备数据
            df = self.data_df.copy()
            df.index = pd.to_datetime(df.index)

            # 字体
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False

            # 分组：日前 vs 实时
            day_ahead_cols = [c for c in df.columns if "日前" in c]
            real_time_cols = [c for c in df.columns if "实时" in c]

            # 窗口
            plot_window = tk.Toplevel(self.frame)
            plot_window.title("节点电价趋势图")
            plot_window.geometry("1200x800")

            # 子图：日前、实时
            n_rows = 1 if len(real_time_cols) == 0 or len(day_ahead_cols) == 0 else 2
            fig, axes = plt.subplots(n_rows, 1, figsize=(12, 6 * n_rows), sharex=True)
            if n_rows == 1:
                axes = [axes]

            # 日前
            if day_ahead_cols:
                ax = axes[0]
                df[day_ahead_cols].plot(ax=ax)  # 自动多条曲线
                ax.set_title("日前电价（元/千瓦时）")
                ax.set_ylabel("价格")
                ax.grid(True)
                ax.legend(loc="best", fontsize=9)

            # 实时
            if real_time_cols:
                ax = axes[-1] if n_rows == 2 else axes[0]
                df[real_time_cols].plot(ax=ax)
                ax.set_title("实时电价（元/千瓦时）")
                ax.set_ylabel("价格")
                ax.grid(True)
                ax.legend(loc="best", fontsize=9)

            fig.autofmt_xdate()

            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            self.log("图表已显示")

        except Exception as e:
            self.log(f"图表生成失败：{e}")
            messagebox.showerror("图表错误", f"图表生成失败：{e}")