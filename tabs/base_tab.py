import pandas as pd

class BaseTab(ttk.Frame):
    def __init__(self,parent,crawler,cookie_var,tab_name):
        super().__init__()
        self.crawler = crawler
        self.cookie_var = cookie_var
        self.tab_name = tab_name
        self.data_df = pd.DataFrame()

    def create_common_ui(self):
        """创建公共UI组件"""
        #region 页面通用框架
        # 输入区域
        self.input_frame = ttk.LabelFrame(self, text="参数设置", padding="10")
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)

        # 日志区域
        self.log_frame = ttk.LabelFrame(self, text="日志信息", padding="10")
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_area = scrolledtext.ScrolledText(self.log_frame, height=6)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.config(state=tk.DISABLED)

        # 结果区域
        self.result_frame = ttk.LabelFrame(self, text=f"{self.tab_name}数据预览", padding="10")
        self.result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 按钮框架
        self.button_frame = ttk.Frame(self.input_frame)
        self.button_frame.grid(row=10, column=0, columnspan=4, pady=10)
        # endregion

        #region 通用按钮
        self.fetch_button = ttk.Button(self.button_frame, text="开始爬取", command=self.start_crawl)
        self.fetch_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(self.button_frame, text="保存数据", command=self.save_data, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(self.button_frame, text="清除日志", command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        #endregion

        self.log(f"欢迎使用{self.tab_name}功能")

    #region 子类抽象方法
    @abstractmethod
    def create_specific_ui(self):
        """子类必须实现：创建特定的UI组件"""
        pass

    @abstractmethod
    def get_crawl_params(self) -> Dict[str, Any]:
        """子类必须实现：获取爬取参数"""
        pass

    @abstractmethod
    def execute_crawl(self, params: Dict[str, Any]):
        """子类必须实现：执行爬取逻辑"""
        pass

    @abstractmethod
    def get_save_dataframes(self) -> Dict[str, pd.DataFrame]:
        """子类必须实现：获取要保存的数据框"""
        pass

    @abstractmethod
    def generate_filename(self) -> str:
        """子类必须实现：生成文件名"""
        pass
    #endregion

    def create_date_selector(self, row, label_text="选择日期:", start_date=datetime.today(),end_date=None):
        """创建日期选择器（公共方法）"""
        #todo 将该类抽象成组件
        ttk.Label(self.input_frame, text=label_text).grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        date_entry = DateEntry(
            self.input_frame, width=12, background='darkblue',
            foreground='white', borderwidth=2, date_pattern='yy-mm-dd'
        )
        date_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        if default_date:
            date_entry.set_date(default_date.strftime('%y-%m-%d'))

        return date_entry

    def create_region_selector(self, row):
        """创建地区选择器（公共方法）"""
        ttk.Label(self.input_frame, text="选择地区:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        region_combo = ttk.Combobox(
            self.input_frame,
            values=list(self.crawler.region_codes.keys()),
            state="readonly"
        )
        region_combo.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        region_combo.current(4)  # 默认选择贵州
        return region_combo

    def create_treeview(self, columns):
        """创建树形视图（公共方法）"""
        tree = ttk.Treeview(self.result_frame, columns=columns, show="headings", height=10)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(self.result_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        return tree

    def log(self, message):
        """日志记录（公共方法）"""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_area.config(state=tk.DISABLED)
        self.log_area.see(tk.END)

    def clear_log(self):
        """清除日志（公共方法）"""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.log("日志已清除")

    def start_crawl(self):
        """开始爬取（公共方法）"""
        # 验证Cookie
        cookie = "CAMSID=" + self.cookie_var.get().strip()
        if not cookie:
            messagebox.showerror("输入错误", "必须提供有效的CAMSID Cookie")
            return
        self.crawler.update_cookie(cookie)

        # 获取参数
        params = self.get_crawl_params()
        if not params.get("valid", True):
            return

        # 禁用按钮
        self.fetch_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)

        # 清空结果
        if hasattr(self, 'result_tree'):
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

        self.data_df = pd.DataFrame()
        self.log(f"开始爬取{self.tab_name}数据...")

        # 在新线程中执行爬取
        thread = threading.Thread(target=self._crawl_wrapper, args=(params,), daemon=True)
        thread.start()

    def _crawl_wrapper(self, params):
        """爬取包装器（处理线程安全）"""
        try:
            self.execute_crawl(params)
        except Exception as e:
            self.log(f"爬取过程中发生错误: {str(e)}")
            self.after(0, lambda: self.fetch_button.config(state=tk.NORMAL))

    def update_results(self, data_df):
        """更新结果显示（公共方法）"""
        self.data_df = data_df

        # 更新树形视图
        if hasattr(self, 'result_tree'):
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

            sample_df = data_df.head(100) if len(data_df) > 100 else data_df
            for idx, row in sample_df.iterrows():
                values = [idx] + [row.get(col, '') for col in self.result_tree['columns'][1:]]
                self.result_tree.insert("", tk.END, values=values)

        # 启用按钮
        self.save_button.config(state=tk.NORMAL)
        self.fetch_button.config(state=tk.NORMAL)
        self.log(f"数据爬取完成：共 {len(data_df)} 条记录")

    def save_data(self):
        """保存数据（公共方法）"""
        try:
            dataframes = self.get_save_dataframes()
            if not dataframes or all(df.empty for df in dataframes.values()):
                messagebox.showerror("保存错误", "没有数据可保存")
                return

            filename = self.generate_filename()
            file_path = filedialog.asksaveasfilename(
                initialfile=filename,
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
            )

            if not file_path:
                return

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in dataframes.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name=sheet_name, index=True, index_label='时间')

            self.log(f"数据已保存到: {file_path}")

        except PermissionError:
            error_msg = f"错误：文件可能正在被其他程序占用，请关闭文件后重试\n{file_path}"
            messagebox.showerror("保存失败", error_msg)
            self.log(error_msg)
        except Exception as e:
            error_msg = f"保存过程中发生错误: {str(e)}"
            messagebox.showerror("保存失败", error_msg)
            self.log(error_msg)
            self.log(f"完整错误信息: {traceback.format_exc()}")