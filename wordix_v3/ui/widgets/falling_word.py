"""下落单词游戏对象"""
import tkinter as tk
import random

from config import GAME_WIDTH, GAME_HEIGHT, WORD_COLORS, GAME_SPEED_MAP


class FallingWord:
    """下落的单词类"""

    def __init__(self, canvas, word_data, level):
        self.word = word_data[0]
        self.meaning = word_data[4] if len(word_data) > 4 else ""
        self.canvas = canvas
        self.level = level

        self.x = random.randint(80, GAME_WIDTH - 200)
        self.y = -30

        self.speed = GAME_SPEED_MAP.get(level, 1.0)

        color = random.choice(WORD_COLORS)
        self.text_id = canvas.create_text(
            self.x, self.y,
            text=self.word,
            font=("微软雅黑", 16, "bold"),
            fill=color,
            anchor="w"
        )

        self.is_destroyed = False

    def move(self):
        """移动单词"""
        if not self.is_destroyed:
            self.y += self.speed
            self.canvas.coords(self.text_id, self.x, self.y)

    def is_out_of_screen(self):
        """检查是否超出屏幕"""
        return self.y > GAME_HEIGHT + 20

    def destroy(self):
        """销毁单词（打碎效果）"""
        self.is_destroyed = True
        self.canvas.delete(self.text_id)

        # 打碎效果
        for _ in range(5):
            dx = random.randint(-20, 20)
            dy = random.randint(-20, 20)
            dot = self.canvas.create_oval(
                self.x + dx, self.y + dy,
                self.x + dx + 5, self.y + dy + 5,
                fill=random.choice(WORD_COLORS)
            )
            self.canvas.after(100, lambda d=dot: self.canvas.delete(d))
