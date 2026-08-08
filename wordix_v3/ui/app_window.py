"""主窗口框架 - 整合所有功能Tab"""
import tkinter as tk
from tkinter import ttk, messagebox

from config import (
    VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_RESIZABLE,
    STYLE_BIG_BUTTON, STYLE_MID_BUTTON
)
from services import WordService, MemoryService, WordBookService, ImportExportService
from utils import speak_word


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

        # 1. 首页
        from ui.tabs.home_tab import HomeTab
        self.home_tab = HomeTab(self.tab_control, self)
        self.tab_control.add(self.home_tab, text="首页")

        # 2. 单词录入
        from ui.tabs.add_word_tab import AddWordTab
        self.add_word_tab = AddWordTab(self.tab_control, self)
        self.tab_control.add(self.add_word_tab, text="单词录入")

        # 3. 词库管理
        from ui.tabs.word_list_tab import WordListTab
        self.word_list_tab = WordListTab(self.tab_control, self)
        self.tab_control.add(self.word_list_tab, text="词库管理")

        # 4. 单词背诵
        from ui.tabs.memorize_tab import MemorizeTab
        self.memorize_tab = MemorizeTab(self.tab_control, self)
        self.tab_control.add(self.memorize_tab, text="单词背诵")

        # 5. 拼写测试
        from ui.tabs.spell_tab import SpellTab
        self.spell_tab = SpellTab(self.tab_control, self)
        self.tab_control.add(self.spell_tab, text="拼写测试")

        # 6. 单词本
        from ui.tabs.wordbook_tab import WordBookTab
        self.wordbook_tab = WordBookTab(self.tab_control, self)
        self.tab_control.add(self.wordbook_tab, text="📖 单词本")

        # 7. 艾宾浩斯复习
        from ui.tabs.ebbinghaus_tab import EbbinghausTab
        self.ebbinghaus_tab = EbbinghausTab(self.tab_control, self)
        self.tab_control.add(self.ebbinghaus_tab, text="🧠 艾宾浩斯")

        # 8. 单词消除游戏
        from ui.tabs.game_tab import GameTab
        self.game_tab = GameTab(self.tab_control, self)
        self.tab_control.add(self.game_tab, text="🎮 单词消除")

    def bind_global_events(self):
        """绑定全局事件"""
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
