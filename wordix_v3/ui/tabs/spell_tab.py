"""拼写测试Tab"""
import tkinter as tk
from tkinter import ttk, messagebox


class SpellTab(tk.Frame):
    """拼写测试页面"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.word_pool = []
        self.idx = 0
        self.answered = {}
        self.correct_count = 0
        self.wrong_count = 0

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        tk.Label(self, text="释义拼写自测（有序遍历，每题仅计分一次）",
                font=("微软雅黑", 16, "bold")).pack(pady=10)

        self.pos_label = tk.Label(self, text="0/0", font=("微软雅黑", 12))
        self.pos_label.pack()

        # 卡片区域
        card_frame = tk.Frame(self, bd=2, relief="solid", width=850, height=200)
        card_frame.pack(padx=20, pady=10, fill="x")
        card_frame.pack_propagate(False)

        self.lbl_meaning = tk.Label(card_frame, text="点击「加载题库」加载单词",
                                   font=("微软雅黑", 16), wraplength=800)
        self.lbl_meaning.pack(pady=60)

        # 输入区域
        input_frame = tk.Frame(self)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="请输入单词：", font=("微软雅黑", 12)).grid(row=0, column=0)
        self.entry_spell = tk.Entry(input_frame, width=35, font=("微软雅黑", 14))
        self.entry_spell.grid(row=0, column=1, padx=10)

        # 结果标签
        self.lbl_result = tk.Label(self, text="", font=("微软雅黑", 13, "bold"))
        self.lbl_result.pack(pady=5)

        self.lbl_stat = tk.Label(self, text=f"正确：0 | 错误：0", font=("微软雅黑", 11))
        self.lbl_stat.pack(pady=3)

        # 按钮
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="加载题库", style="Mid.TButton",
                  command=self.load_words).grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text="上一题", style="Mid.TButton",
                  command=self.prev).grid(row=0, column=1, padx=4)
        ttk.Button(btn_frame, text="下一题", style="Mid.TButton",
                  command=self.next).grid(row=0, column=2, padx=4)
        ttk.Button(btn_frame, text="提交答案", style="Mid.TButton",
                  command=self.check_answer).grid(row=0, column=3, padx=4)
        ttk.Button(btn_frame, text="朗读答案", style="Mid.TButton",
                  command=self.speak).grid(row=0, column=4, padx=4)
        ttk.Button(btn_frame, text="重置统计", style="Mid.TButton",
                  command=self.reset).grid(row=0, column=5, padx=4)

        # 绑定回车键
        self.entry_spell.bind("<Return>", lambda e: self.check_answer())

        tk.Label(self, text="提示：切换等级后重新「加载题库」，每个单词仅首次答题计入分数",
                font=("微软雅黑", 10)).pack(pady=5)

    def load_words(self):
        """加载题库"""
        level_id = self.app.get_current_level_id()
        self.word_pool = self.app.word_service.get_all_words(level_id)
        self.idx = 0
        self.answered.clear()
        self.correct_count = 0
        self.wrong_count = 0
        self.lbl_stat.config(text=f"正确：{self.correct_count} | 错误：{self.wrong_count}")
        self.refresh_display()

    def refresh_display(self):
        """刷新显示"""
        if not self.word_pool:
            self.lbl_meaning.config(text="当前等级无单词，请先录入！")
            self.pos_label.config(text="0/0")
            return

        word_data = self.word_pool[self.idx]
        self.lbl_meaning.config(text=f"释义：{word_data[4]}")
        self.entry_spell.delete(0, tk.END)
        self.lbl_result.config(text="")
        self.pos_label.config(text=f"{self.idx + 1}/{len(self.word_pool)}")

    def check_answer(self):
        """检查答案"""
        if not self.word_pool:
            messagebox.showinfo("提示", "请先点击加载题库")
            return

        current_word = self.word_pool[self.idx][0]
        user_input = self.entry_spell.get().strip().lower()
        real_word = current_word.lower()

        # 检查是否已回答过
        if current_word in self.answered:
            if user_input == real_word:
                self.lbl_result.config(text="✅ 正确（已记录，分数不重复累加）", fg="green")
            else:
                self.lbl_result.config(text=f"❌ 错误，正确单词：{current_word}（已记录）", fg="red")
            return

        # 首次回答
        self.answered[current_word] = True
        if user_input == real_word:
            self.correct_count += 1
            self.lbl_result.config(text="✅ 拼写正确！", fg="green")
        else:
            self.wrong_count += 1
            # 自动加入单词本
            self.app.wordbook_service.add_word(current_word, note="拼写测试错题")
            self.lbl_result.config(text=f"❌ 错误，正确单词：{current_word}\n📝 已自动加入单词本", fg="red")

        self.lbl_stat.config(text=f"正确：{self.correct_count} | 错误：{self.wrong_count}")

    def prev(self):
        """上一题"""
        if not self.word_pool:
            messagebox.showinfo("提示", "请先加载题库")
            return
        if self.idx <= 0:
            messagebox.showinfo("提示", "已经是第一题")
            return
        self.idx -= 1
        self.refresh_display()

    def next(self):
        """下一题"""
        if not self.word_pool:
            messagebox.showinfo("提示", "请先加载题库")
            return
        if self.idx >= len(self.word_pool) - 1:
            messagebox.showinfo("提示", "已经是最后一题")
            return
        self.idx += 1
        self.refresh_display()

    def speak(self):
        """朗读"""
        if self.word_pool:
            self.app.speak(self.word_pool[self.idx][0])

    def reset(self):
        """重置统计"""
        self.correct_count = 0
        self.wrong_count = 0
        self.answered.clear()
        self.lbl_stat.config(text=f"正确：{self.correct_count} | 错误：{self.wrong_count}")
        self.lbl_result.config(text="")
