"""单词消除游戏Tab"""
import tkinter as tk
from tkinter import ttk, messagebox
import random

from config import GAME_WIDTH, GAME_HEIGHT, WORD_COLORS, GAME_SPEED_MAP, GAME_SPAWN_INTERVAL_MAP
from ui.widgets.falling_word import FallingWord


class GameTab(tk.Frame):
    """单词消除游戏页面"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # 游戏状态
        self.game_running = False
        self.words_pool = []
        self.score = 0
        self.level = 1
        self.current_falling_words = []
        self.game_timer = None
        self.spawn_timer = None

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        # 头部
        header = tk.Frame(self)
        header.pack(fill="x", padx=20, pady=10)
        tk.Label(header, text="🎮 单词消除游戏", font=("微软雅黑", 18, "bold")).pack(side="left", padx=10)

        # 控制区
        control_frame = tk.Frame(self)
        control_frame.pack(fill="x", padx=20, pady=5)

        # 难度选择
        diff_frame = tk.Frame(control_frame)
        diff_frame.pack(side="left", padx=10)
        tk.Label(diff_frame, text="难度等级：", font=("微软雅黑", 11)).pack(side="left")

        self.level_var = tk.IntVar(value=1)
        for lvl in [1, 2, 3]:
            rb = tk.Radiobutton(diff_frame, text=f"{lvl}级", variable=self.level_var, value=lvl,
                               font=("微软雅黑", 10), command=self.update_level)
            rb.pack(side="left", padx=5)

        # 分数显示
        score_frame = tk.Frame(control_frame)
        score_frame.pack(side="right", padx=10)
        self.lbl_score = tk.Label(score_frame, text="得分：0", font=("微软雅黑", 14, "bold"), fg="green")
        self.lbl_score.pack()

        # 游戏画布
        canvas_container = tk.Frame(self, bd=2, relief="solid", width=GAME_WIDTH, height=GAME_HEIGHT)
        canvas_container.pack(pady=10)
        canvas_container.pack_propagate(False)

        self.canvas = tk.Canvas(canvas_container, width=GAME_WIDTH, height=GAME_HEIGHT, bg="#f0f0f0")
        self.canvas.pack()

        # 输入框
        input_frame = tk.Frame(self)
        input_frame.pack(pady=5)

        tk.Label(input_frame, text="当前输入：", font=("微软雅黑", 12)).pack(side="left", padx=5)
        self.game_entry = tk.Entry(input_frame, width=40, font=("微软雅黑", 16, "bold"),
                                  justify="center", state="disabled")
        self.game_entry.pack(side="left", padx=10)

        tk.Label(self, text="👆 点击输入框后直接输入单词，按回车确认",
                font=("微软雅黑", 11), fg="blue").pack(pady=3)

        self.status_label = tk.Label(self, text="点击「开始游戏」启动", font=("微软雅黑", 11))
        self.status_label.pack(pady=3)

        # 绑定回车键
        self.game_entry.bind("<Return>", self.check_input)

        # 按钮
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="开始游戏", style="Big.TButton",
                  command=self.start_game).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="停止游戏", style="Big.TButton",
                  command=self.stop_game).grid(row=0, column=1, padx=10)

        tk.Label(self, text="💡 玩法：单词从顶部下落，看到单词后在输入框输入并按回车\n"
                           "✓ 正确：+1分  |  ✗ 错误或超出屏幕：-1分\n"
                           "⚡ 难度越高，下落越快",
                font=("微软雅黑", 10), justify="left").pack(pady=5)

    def update_level(self):
        """更新难度等级"""
        self.level = self.level_var.get()

    def start_game(self):
        """开始游戏"""
        if self.game_running:
            return

        # 获取单词池
        level_id = self.app.get_current_level_id()
        self.words_pool = self.app.word_service.get_all_words(level_id)

        if not self.words_pool:
            messagebox.showwarning("提示", "当前等级暂无单词，请先录入！")
            return

        # 重置状态
        self.game_running = True
        self.score = 0
        self.current_falling_words.clear()
        self.update_score()

        # 清空画布
        self.canvas.delete("all")
        self.canvas.config(bg="#f0f0f0")

        # 启用输入框
        self.game_entry.config(state="normal")
        self.game_entry.delete(0, tk.END)
        self.game_entry.focus_set()

        self.status_label.config(text="游戏进行中... 在上方输入框输入单词后按回车", fg="green")

        # 开始生成单词
        self.spawn_next_word()

        # 启动游戏循环
        self.game_loop()

    def spawn_next_word(self):
        """生成下一个单词"""
        if not self.game_running or not self.words_pool:
            return

        word_data = random.choice(self.words_pool)
        falling_word = FallingWord(self.canvas, word_data, self.level)
        self.current_falling_words.append(falling_word)

        # 安排下一次生成
        spawn_interval = GAME_SPAWN_INTERVAL_MAP.get(self.level, 2500)
        if self.game_running:
            self.spawn_timer = self.canvas.after(spawn_interval, self.spawn_next_word)

    def game_loop(self):
        """游戏主循环"""
        if not self.game_running:
            return

        # 移动所有下落单词
        words_to_remove = []
        for fw in self.current_falling_words:
            if not fw.is_destroyed:
                fw.move()

                # 检查是否超出屏幕
                if fw.is_out_of_screen():
                    fw.destroy()
                    words_to_remove.append(fw)
                    self.score -= 1
                    self.update_score()

        # 移除超出的单词
        for fw in words_to_remove:
            self.current_falling_words.remove(fw)

        # 继续循环
        if self.game_running:
            self.game_timer = self.canvas.after(50, self.game_loop)

    def check_input(self, event=None):
        """检查输入"""
        if not self.game_running:
            return

        user_input = self.game_entry.get().strip().lower()

        if not user_input:
            return

        # 清空输入框
        self.game_entry.delete(0, tk.END)
        self.game_entry.focus_set()

        # 查找匹配的单词
        matched_word = None
        for fw in self.current_falling_words:
            if not fw.is_destroyed and fw.word.lower() == user_input:
                matched_word = fw
                break

        if matched_word:
            # 拼写正确
            matched_word.destroy()
            self.current_falling_words.remove(matched_word)
            self.score += 1
            self.update_score()
            self.status_label.config(text=f"✅ 正确！+1分", fg="green")
        else:
            # 拼写错误
            self.score -= 1
            self.update_score()
            self.status_label.config(text=f"❌ 错误！-1分", fg="red")
            self.canvas.after(1000, lambda: self.status_label.config(
                text="游戏进行中... 在上方输入框输入单词后按回车", fg="green"))

    def update_score(self):
        """更新分数"""
        self.lbl_score.config(text=f"得分：{self.score}")

    def stop_game(self):
        """停止游戏"""
        self.game_running = False

        # 取消定时器
        if self.game_timer:
            self.canvas.after_cancel(self.game_timer)
        if self.spawn_timer:
            self.canvas.after_cancel(self.spawn_timer)

        # 清空画布
        self.canvas.delete("all")
        self.current_falling_words.clear()

        # 禁用输入框
        self.game_entry.config(state="disabled")
        self.game_entry.delete(0, tk.END)

        self.status_label.config(text="游戏已停止", fg="blue")
