"""单词背诵Tab"""
import tkinter as tk
from tkinter import ttk, messagebox


class MemorizeTab(tk.Frame):
    """单词背诵页面"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.word_list = []
        self.index = 0
        self.is_show_detail = tk.BooleanVar(value=False)

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        tk.Label(self, text="有序单词背诵卡（支持一词多义）", font=("微软雅黑", 16, "bold")).pack(pady=10)

        self.pos_label = tk.Label(self, text="0/0", font=("微软雅黑", 12))
        self.pos_label.pack()

        # 卡片区域
        card_frame = tk.Frame(self, bd=2, relief="solid", width=800, height=380)
        card_frame.pack(padx=30, pady=10, fill="x")
        card_frame.pack_propagate(False)

        self.lbl_word = tk.Label(card_frame, text="请点击「加载词库」",
                                 font=("微软雅黑", 30, "bold"), wraplength=750)
        self.lbl_word.pack(pady=30)

        # 详情区域
        self.detail_frame = tk.Frame(card_frame)
        self.lbl_uk = tk.Label(self.detail_frame, text="英音：", font=("微软雅黑", 12))
        self.lbl_us = tk.Label(self.detail_frame, text="美音：", font=("微软雅黑", 12))
        self.lbl_senses = tk.Label(self.detail_frame, text="释义列表：", font=("微软雅黑", 12, "bold"))
        self.lbl_senses_content = tk.Label(self.detail_frame, text="", font=("微软雅黑", 11),
                                           wraplength=720, justify="left")

        # 按钮
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="加载词库", style="Mid.TButton",
                   command=self.load_words).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frame, text="上一个", style="Mid.TButton",
                   command=self.prev).grid(row=0, column=1, padx=6)
        ttk.Button(btn_frame, text="下一个", style="Mid.TButton",
                   command=self.next).grid(row=0, column=2, padx=6)
        ttk.Button(btn_frame, text="翻面查看释义", style="Mid.TButton",
                   command=self.flip_card).grid(row=0, column=3, padx=6)
        ttk.Button(btn_frame, text="🔊 朗读", style="Mid.TButton",
                   command=self.speak).grid(row=0, column=4, padx=6)
        ttk.Button(btn_frame, text="🧠 加入记忆", style="Mid.TButton",
                   command=self.add_memory).grid(row=0, column=5, padx=6)

    def load_words(self):
        """加载单词"""
        level_id = self.app.get_current_level_id()
        self.word_list = self.app.word_service.get_all_words(level_id)
        self.index = 0
        self.refresh_display()

    def refresh_display(self):
        """刷新显示"""
        if not self.word_list:
            self.lbl_word.config(text="当前等级无单词，请先录入！")
            self.pos_label.config(text="0/0")
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

        if self.is_show_detail.get():
            self.is_show_detail.set(False)
            self.lbl_word.config(text=self.word_list[self.index][0])
            self.detail_frame.pack_forget()
        else:
            self.is_show_detail.set(True)
            word_data = self.word_list[self.index]

            details = self.app.word_service.get_word_details(word_data[0])
            if details and details['senses']:
                senses_text = ""
                for i, (pos, meaning, example, translation) in enumerate(details['senses'], 1):
                    senses_text += f"   {i}. {pos} {meaning}\n"
                    senses_text += f"   例句：{example}\n"
                    senses_text += f"   翻译：{translation}\n\n"

                self.lbl_uk.config(text=f"英音：{word_data[1] if word_data[1] else '暂无'}")
                self.lbl_us.config(text=f"美音：{word_data[2] if word_data[2] else '暂无'}")
                self.lbl_senses_content.config(text=senses_text,justify="center",anchor="center")


                self.detail_frame.pack(pady=10)
                self.lbl_uk.pack()
                self.lbl_us.pack()
                self.lbl_senses.pack()
                self.lbl_senses_content.pack(pady=5)

    def prev(self):
        """上一个"""
        if not self.word_list:
            messagebox.showinfo("提示", "请先加载词库")
            return
        if self.index <= 0:
            messagebox.showinfo("提示", "已经是第一个单词")
            return
        self.index -= 1
        self.refresh_display()

    def next(self):
        """下一个"""
        if not self.word_list:
            messagebox.showinfo("提示", "请先加载词库")
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

    def add_memory(self):
        """加入记忆计划"""
        if not self.word_list:
            messagebox.showinfo("提示", "请先加载词库")
            return
        word = self.word_list[self.index][0]
        self.app.memory_service.add_word(word)
        messagebox.showinfo("完成", f"「{word}」加入艾宾浩斯记忆计划")
