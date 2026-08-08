"""首页Tab"""
import tkinter as tk
from tkinter import ttk

from config import VERSION


class HomeTab(tk.Frame):
    """首页"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        tk.Label(self, text="🔥 Wordix 词根单词学习系统",
                 font=("微软雅黑", 22, "bold")).pack(pady=30)
        tk.Label(self, text=VERSION, font=("微软雅黑", 12)).pack(pady=5)

        tips = """
功能清单：
1. 单词录入：支持一词多义、一词多词性，表格形式录入
2. 词库管理：搜索、分页、Excel导入导出（支持多义词）
3. 单词背诵：有序翻卡遍历全部单词，显示完整释义列表
4. 拼写测试：有序遍历单词自测拼写，每个单词仅计分一次
5. 📖 单词本：自动收集错题+手动添加重点单词，专门复习
6. 🧠 艾宾浩斯记忆：间隔重复科学复习，自动推送到期单词
7. 🎮 单词消除游戏：寓教于乐，边玩边学

全部数据本地SQLite存储，无需联网

✨ v3.0 新增：艾宾浩斯遗忘曲线间隔重复记忆计划
遗忘复习节点：5分钟→30分钟→12小时→1天→2天→4天→7天→15天→30天
        """
        tk.Label(self, text=tips, font=("微软雅黑", 11), justify="left").pack(pady=20)
