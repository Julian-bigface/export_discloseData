import tkinter as tk
from tkinter import ttk
from tabs.disclosure_tab import DisclosureTab
from tabs.station_tab import StationTab
from tabs.node_price_tab import NodePriceTab
from tabs.Real_time_information_disclosure_tab import DisclosureTab_real_time

import DataCrawler

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("电力市场数据爬取工具")
        self.root.geometry("1100x800")

        # 全局数据爬取器
        self.crawler = DataCrawler.DataCrawler()

        # 样式
        style = ttk.Style()
        style.theme_use("clam")

        # 全局 Cookie
        self.cookie_var = tk.StringVar(value="BD0BC4CA235BFE5A5E9A0CA0657A4B25")
        self.create_global_cookie_section()

        # 标签页
        tab_control = ttk.Notebook(self.root)

        disclosure_tab = DisclosureTab(tab_control, self.crawler, self.cookie_var)
        tab_control.add(disclosure_tab.frame, text="信息披露")

        Real_time_information_disclosure_tab = DisclosureTab_real_time(tab_control, self.crawler, self.cookie_var)  # 新增
        tab_control.add(Real_time_information_disclosure_tab.frame, text="信息披露（实时）")  # 新增

        station_tab = StationTab(tab_control, self.crawler, self.cookie_var)
        tab_control.add(station_tab.frame, text="场站电量电价")

        node_price_tab = NodePriceTab(tab_control, self.crawler, self.cookie_var)  # 新增
        tab_control.add(node_price_tab.frame, text="节点电价")  # 新增

        tab_control.pack(expand=1, fill="both")

    def create_global_cookie_section(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(frame, text="全局CAMSID Cookie:").pack(side=tk.LEFT)
        entry = ttk.Entry(frame, textvariable=self.cookie_var, width=100)
        entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
