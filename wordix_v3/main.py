import sys
from pathlib import Path

# 将 wordix_v3 目录加入Python搜索路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
"""Wordix v3.0 主程序入口"""
import tkinter as tk
from tkinter import ttk

from config import VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_RESIZABLE
from database import init_database
from ui.app_window import AppWindow


def main():
    """主函数"""
    # 初始化数据库
    print("正在初始化数据库...")
    init_database()
    print("✅ 数据库初始化完成")

    # 创建主窗口
    print("正在启动应用程序...")
    root = tk.Tk()
    app = AppWindow(root)

    print(f"🚀 Wordix {VERSION} 已启动")

    # 启动主循环
    root.mainloop()


if __name__ == "__main__":
    main()
