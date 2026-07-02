"""单词本Tab"""
import tkinter as tk
from tkinter import ttk, messagebox


class WordBookTab(tk.Frame):
    """单词本页面"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.word_list = []
        self.index = 0
        self.is_show_detail = tk.BooleanVar(value=False)

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        tk.Label(self, text="📖 我的单词本", font=("微软雅黑", 18, "bold")).pack(pady=10)

        # 统计信息
        stat_frame = tk.Frame(self)
        stat_frame.pack(pady=5)
        self.lbl_count = tk.Label(stat_frame, text="单词总数：0", font=("微软雅黑", 12))
        self.lbl_count.pack(side="left", padx=10)

        self.pos_label = tk.Label(self, text="0/0", font=("微软雅黑", 12))
        self.pos_label.pack()

        # 卡片区域
        card_frame = tk.Frame(self, bd=2, relief="solid", width=800, height=380)
        card_frame.pack(padx=30, pady=10, fill="x")
        card_frame.pack_propagate(False)

        self.lbl_word = tk.Label(card_frame, text="点击「加载单词本」查看单词",
                                 font=("微软雅黑", 28, "bold"), wraplength=750)
        self.lbl_word.pack(pady=50)

        # 详情区域
        self.detail_frame = tk.Frame(card_frame)
        self.lbl_uk = tk.Label(self.detail_frame, text="英音：", font=("微软雅黑", 12))
        self.lbl_us = tk.Label(self.detail_frame, text="美音：", font=("微软雅黑", 12))
        self.lbl_senses = tk.Label(self.detail_frame, text="释义：", font=("微软雅黑", 12))
        self.lbl_note = tk.Label(self.detail_frame, text="备注：", font=("微软雅黑", 11, "bold"), fg="blue")
        self.lbl_time = tk.Label(self.detail_frame, text="添加时间：", font=("微软雅黑", 10))

        # 按钮区域
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        btn_row1 = tk.Frame(btn_frame)
        btn_row1.pack(pady=5)
        ttk.Button(btn_row1, text="加载单词本", style="Mid.TButton",
                   command=self.load_wordbook).grid(row=0, column=0, padx=6)
        ttk.Button(btn_row1, text="➕ 添加单词", style="Mid.TButton",
                   command=self.add_word).grid(row=0, column=1, padx=6)
        ttk.Button(btn_row1, text="上一个", style="Mid.TButton",
                   command=self.prev).grid(row=0, column=2, padx=6)
        ttk.Button(btn_row1, text="下一个", style="Mid.TButton",
                   command=self.next).grid(row=0, column=3, padx=6)
        ttk.Button(btn_row1, text="翻面查看释义", style="Mid.TButton",
                   command=self.flip_card).grid(row=0, column=4, padx=6)
        ttk.Button(btn_row1, text="🔊 朗读", style="Mid.TButton",
                   command=self.speak).grid(row=0, column=5, padx=6)

        btn_row2 = tk.Frame(btn_frame)
        btn_row2.pack(pady=5)
        ttk.Button(btn_row2, text="✅ 已掌握", style="Mid.TButton",
                   command=self.mark_mastered).grid(row=0, column=0, padx=6)
        ttk.Button(btn_row2, text="🗑️ 删除", style="Mid.TButton",
                   command=self.remove_word).grid(row=0, column=1, padx=6)

        tk.Label(self, text="💡 拼写测试答错自动加入｜也可手动添加｜点击「已掌握」移除",
                 font=("微软雅黑", 10), fg="blue").pack(pady=5)

    def load_wordbook(self):
        """加载单词本"""
        self.word_list = self.app.wordbook_service.get_words()
        self.index = 0
        self.lbl_count.config(text=f"单词总数：{len(self.word_list)}")

        if self.word_list:
            messagebox.showinfo("加载成功", f"已加载 {len(self.word_list)} 个单词")

        self.refresh_display()

    def refresh_display(self):
        """刷新显示"""
        if not self.word_list:
            self.lbl_word.config(text="单词本为空，快去添加重点单词吧！")
            self.pos_label.config(text="0/0")
            self.detail_frame.pack_forget()
            return

        word_data = self.word_list[self.index]
        self.is_show_detail.set(False)
        self.lbl_word.config(text=word_data[0])
        self.detail_frame.pack_forget()
        self.pos_label.config(text=f"{self.index + 1}/{len(self.word_list)}")

    def flip_card(self):
        """翻面"""
        if not self.word_list:
            return

        word_data = self.word_list[self.index]
        word, uk, us, meanings, added_time, note, mastered = word_data

        if self.is_show_detail.get():
            self.is_show_detail.set(False)
            self.lbl_word.config(text=word)
            self.detail_frame.pack_forget()
        else:
            self.is_show_detail.set(True)

            uk_text = f"英音：{uk}" if uk else "英音：暂无"
            us_text = f"美音：{us}" if us else "美音：暂无"
            meanings_text = f"释义：{meanings}" if meanings else "释义：暂无"
            note_text = f"备注：{note}" if note else "备注：无"
            time_text = f"添加时间：{added_time}"

            self.lbl_uk.config(text=uk_text)
            self.lbl_us.config(text=us_text)
            self.lbl_senses.config(text=meanings_text)
            self.lbl_note.config(text=note_text)
            self.lbl_time.config(text=time_text)

            self.detail_frame.pack(pady=10)
            self.lbl_uk.pack()
            self.lbl_us.pack()
            self.lbl_senses.pack(pady=5)
            self.lbl_note.pack(pady=3)
            self.lbl_time.pack(pady=3)

    def prev(self):
        """上一个"""
        if not self.word_list:
            messagebox.showinfo("提示", "请先加载单词本")
            return
        if self.index <= 0:
            messagebox.showinfo("提示", "已经是第一个单词")
            return
        self.index -= 1
        self.refresh_display()

    def next(self):
        """下一个"""
        if not self.word_list:
            messagebox.showinfo("提示", "请先加载单词本")
            return
        if self.index >= len(self.word_list) - 1:
            messagebox.showinfo("提示", "已经是最后一个单词")
            return
        self.index += 1
        self.refresh_display()

    def speak(self):
        """朗读"""
        if self.word_list:
            self.app.speak(self.word_list[self.index][0])

    def add_word(self):
        """手动添加单词"""
        dialog = tk.Toplevel(self)
        dialog.title("添加单词到单词本")
        dialog.geometry("400x200")
        dialog.transient(self.master)
        dialog.grab_set()

        tk.Label(dialog, text="请输入单词：", font=("微软雅黑", 11)).pack(pady=10)
        entry_word = tk.Entry(dialog, width=30, font=("微软雅黑", 12))
        entry_word.pack(pady=5)
        entry_word.focus()

        tk.Label(dialog, text="备注（可选）：", font=("微软雅黑", 11)).pack(pady=5)
        entry_note = tk.Entry(dialog, width=30, font=("微软雅黑", 12))
        entry_note.pack(pady=5)

        def confirm():
            word = entry_word.get().strip()
            note = entry_note.get().strip()

            if not word:
                messagebox.showwarning("提示", "单词不能为空")
                return

            if self.app.wordbook_service.add_word(word, note):
                messagebox.showinfo("成功", f"「{word}」已添加到单词本")
                dialog.destroy()
                self.load_wordbook()
            else:
                messagebox.showerror("失败", "添加失败")

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="确定", style="Mid.TButton", command=confirm).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="取消", style="Mid.TButton", command=dialog.destroy).grid(row=0, column=1, padx=10)

        entry_word.bind("<Return>", lambda e: confirm())

    def remove_word(self):
        """删除单词"""
        if not self.word_list:
            messagebox.showinfo("提示", "请先加载单词本")
            return

        current_word = self.word_list[self.index][0]

        if messagebox.askyesno("确认删除", f"确定要将「{current_word}」从单词本中移除吗？"):
            if self.app.wordbook_service.remove_word(current_word):
                messagebox.showinfo("成功", f"已移除「{current_word}」")
                self.word_list.pop(self.index)
                if self.index >= len(self.word_list):
                    self.index = max(0, len(self.word_list) - 1)
                self.lbl_count.config(text=f"单词总数：{len(self.word_list)}")
                self.refresh_display()

    def mark_mastered(self):
        """标记已掌握"""
        if not self.word_list:
            messagebox.showinfo("提示", "请先加载单词本")
            return

        current_word = self.word_list[self.index][0]

        if messagebox.askyesno("确认标记", f"确定已将「{current_word}」掌握了吗？\n该单词将从单词本中移除"):
            if self.app.wordbook_service.mark_mastered(current_word):
                messagebox.showinfo("太棒了！", f"🎉 恭喜掌握「{current_word}」！")
                self.word_list.pop(self.index)
                if self.index >= len(self.word_list):
                    self.index = max(0, len(self.word_list) - 1)
                self.lbl_count.config(text=f"单词总数：{len(self.word_list)}")
                self.refresh_display()
