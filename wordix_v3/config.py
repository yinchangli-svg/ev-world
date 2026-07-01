"""配置文件 - 全局常量和配置"""
import os

# ======================
# 版本信息
# ======================
VERSION = "v3.0 | Wordix单词单机版（一词多义+有序背诵+拼写测试+单词本+单次计分+发音+等级+导入导出+艾宾浩斯间隔记忆）"

# ======================
# 路径配置
# ======================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(SCRIPT_DIR, "wordix.xdb")

# ======================
# 艾宾浩斯间隔配置（单位：分钟）
# ======================
EBBINGHAUS_INTERVALS = [
    5,        # level 0 初次学习后5分钟
    30,       # level 1 30分钟
    12 * 60,  # level 2 12小时
    24 * 60,  # level 3 1天
    2 * 24 * 60,  # level 4 2天
    4 * 24 * 60,  # level 5 4天
    7 * 24 * 60,  # level 6 7天
    15 * 24 * 60, # level 7 15天
    30 * 24 * 60, # level 8 30天
    999999999     # level 9 永久熟记，不再复习
]
MAX_MEM_LEVEL = len(EBBINGHAUS_INTERVALS) - 1

# ======================
# 游戏配置
# ======================
GAME_WIDTH = 900
GAME_HEIGHT = 500
WORD_COLORS = ["red", "blue", "green", "purple", "orange", "brown"]

# 难度速度映射
GAME_SPEED_MAP = {1: 1.0, 2: 1.8, 3: 2.8}

# 生成频率映射（毫秒）
GAME_SPAWN_INTERVAL_MAP = {1: 2500, 2: 1800, 3: 1200}

# ======================
# 等级数据
# ======================
LEVEL_DATA = [
    ('小学3-4年级', 10),
    ('小学5-6年级', 20),
    ('初中7-9年级', 30),
    ('高中必修', 40),
    ('高中选择性必修', 50),
    ('大学四级', 60),
    ('大学六级', 70),
    ('托福', 80),
    ('雅思', 90)
]

# ======================
# 页面配置
# ======================
DEFAULT_PAGE_SIZE = 10

# ======================
# UI样式配置
# ======================
STYLE_BIG_BUTTON = {"font": ("微软雅黑", 13, "bold"), "padding": 12}
STYLE_MID_BUTTON = {"font": ("微软雅黑", 11), "padding": 6}

# 窗口配置
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 860
WINDOW_RESIZABLE = (False, False)
