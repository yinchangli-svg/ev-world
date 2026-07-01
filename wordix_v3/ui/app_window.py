"""主窗口框架 - 整合所有功能Tab"""
import tkinter as tk
from tkinter import ttk, messagebox

from wordix_v3.config import (
    VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_RESIZABLE,
    STYLE_BIG_BUTTON, STYLE_MID_BUTTON
)
from wordix_v3.services import WordService, MemoryService, WordBookService, ImportExportService
from wordix_v3.utils import speak_word


class AppWindow:
    """应用程序主窗口"""

    def __init__(self, root):
        self.root = root
        self.root.title(f"Wordix 词根单词学习 · {VERSION}")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(*WINDOW_RESIZABLE)

        # 初始化服务层
        self.word_service = WordService()
        self.memory_service = MemoryService()
        self.wordbook_service = WordBookService()
        self.import_export = ImportExportService()

        # 设置UI样式
        self.setup_styles()

        # 创建全局变量
        self.setup_global_vars()

        # 创建Tab控件
        self.setup_tabs()

        # 绑定全局事件
        self.bind_global_events()

    def setup_styles(self):
        """设置UI样式"""
        style = ttk.Style()
        style.configure("Big.TButton", **STYLE_BIG_BUTTON)
        style.configure("Mid.TButton", **STYLE_MID_BUTTON)

    def setup_global_vars(self):
        """设置全局变量"""
        # 获取等级列表
        levels = self.word_service.get_levels()
        self.level_ids = [item[0] for item in levels]
        self.level_names = [item[1] for item in levels]

        # 当前选中的等级
        self.current_level_id = tk.IntVar(value=self.level_ids[0] if self.level_ids else 0)
        self.current_level_name = tk.StringVar(value=self.level_names[0] if self.level_names else "")

        # 分页相关
        self.current_page = 1
        self.page_size = 10

    def setup_tabs(self):
        """创建所有Tab页面"""
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(expand=1, fill="both", padx=10, pady=10)

        # TODO: 在这里创建各个Tab（需要从原 word_app.py 迁移）
        # 示例：
        # from ui.tabs.home_tab import HomeTab
        # self.home_tab = HomeTab(self.tab_control, self)
        # self.tab_control.add(self.home_tab, text="首页")

        # 临时创建一个简单的首页提示
        tab_home = ttk.Frame(self.tab_control)
        self.tab_control.add(tab_home, text="首页")

        tk.Label(tab_home, text="🔥 Wordix 词根单词学习系统",
                 font=("微软雅黑", 22, "bold")).pack(pady=30)
        tk.Label(tab_home, text=VERSION, font=("微软雅黑", 12)).pack(pady=5)

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
        tk.Label(tab_home, text=tips, font=("微软雅黑", 11), justify="left").pack(pady=20)

        tk.Label(tab_home, text="⚠️ 重构进行中... 更多功能即将推出",
                 font=("微软雅黑", 14, "bold"), fg="blue").pack(pady=30)
        tk.Label(tab_home, text="当前可使用原版 wordix/word_app.py",
                 font=("微软雅黑", 12), fg="red").pack()

    def bind_global_events(self):
        """绑定全局事件"""
        # 可以在这里添加全局快捷键等
        pass

    def get_current_level_id(self):
        """获取当前选中的等级ID"""
        return self.current_level_id.get()

    def get_current_level_name(self):
        """获取当前选中的等级名称"""
        return self.current_level_name.get()

    def speak(self, text):
        """朗读文本（便捷方法）"""
        speak_word(text)
