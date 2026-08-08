"""艾宾浩斯复习Tab"""
import tkinter as tk
from tkinter import ttk, messagebox

from config import EBBINGHAUS_INTERVALS


class EbbinghausTab(tk.Frame):
    """艾宾浩斯复习页面"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.due_list = []
        self.current_idx = 0
        self.show_detail_flag = tk.BooleanVar(value=False)

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        # 顶部统计栏
        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", padx=20, pady=8)

        self.lbl_total = tk.Label(top_frame, text="待复习单词：0 个",
                                  font=("微软雅黑", 12, "bold"), fg="#2060c0")
        self.lbl_pos = tk.Label(top_frame, text="0/0", font=("微软雅黑", 12))
        btn_refresh = ttk.Button(top_frame, text="🔄 刷新待复习列表",
                                 style="Mid.TButton", command=self.refresh_list)

        self.lbl_total.pack(side="left", padx=10)
        self.lbl_pos.pack(side="left", padx=20)
        btn_refresh.pack(side="right", padx=10)

        # 单词卡片
        card_frame = tk.Frame(self, bd=3, relief="solid", width=900, height=420)
        card_frame.pack(padx=30, pady=15, fill="x")
        card_frame.pack_propagate(False)

        self.lbl_word = tk.Label(card_frame, text="点击【刷新待复习列表】加载到期单词",
                                 font=("微软雅黑", 32, "bold"), wraplength=820)
        self.lbl_word.pack(pady=40)

        # 详情区域
        self.detail_frame = tk.Frame(card_frame)
        self.lbl_uk = tk.Label(self.detail_frame, text="英音：", font=("微软雅黑", 12))
        self.lbl_us = tk.Label(self.detail_frame, text="美音：", font=("微软雅黑", 12))
        self.lbl_level = tk.Label(self.detail_frame, text="记忆档位：",
                                  font=("微软雅黑", 11, "bold"), fg="#c04020")
        self.lbl_sense_title = tk.Label(self.detail_frame, text="完整释义：",
                                        font=("微软雅黑", 12, "bold"))
        self.lbl_sense_text = tk.Label(self.detail_frame, text="",
                                       font=("微软雅黑", 11), wraplength=800, justify="left")
        self.lbl_ex_title = tk.Label(self.detail_frame, text="例句：",
                                     font=("微软雅黑", 12, "bold"))
        self.lbl_ex_text = tk.Label(self.detail_frame, text="",
                                    font=("微软雅黑", 11), wraplength=800, justify="left")

        # 底部按钮
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=12)

        ttk.Button(btn_frame, text="🔊 朗读单词", style="Mid.TButton",
                   command=self.speak).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frame, text="📖 查看完整释义", style="Mid.TButton",
                   command=self.toggle_detail).grid(row=0, column=1, padx=6)
        ttk.Button(btn_frame, text="❌ 忘记了（重置）", style="Mid.TButton",
                   command=self.mark_forget).grid(row=0, column=2, padx=10)
        ttk.Button(btn_frame, text="✅ 记住了（升档）", style="Big.TButton",
                   command=self.mark_remember).grid(row=0, column=3, padx=10)

        tk.Label(self, text="规则：记住自动升档拉长间隔；忘记直接重置0档，5分钟后再次复习；升到30天档位永久不再推送",
                 font=("微软雅黑", 10), fg="#555").pack(pady=5)

        # 页面显示时自动刷新
        self.bind("<Map>", lambda e: self.refresh_list())

    def refresh_list(self):
        """刷新的待复习列表"""
        self.due_list = self.app.memory_service.get_due_words()
        self.current_idx = 0
        self.lbl_total.config(text=f"待复习单词：{len(self.due_list)} 个")

        if len(self.due_list) == 0:
            self.lbl_word.config(text="🎉 今日无到期复习单词，稍后再来！")
            self.detail_frame.pack_forget()
            self.lbl_pos.config(text="0/0")
            return

        self.render_card()

    def render_card(self):
        """渲染当前单词卡片"""
        if not self.due_list:
            return

        word_data = self.due_list[self.current_idx]
        word, mem_lv, next_ts, uk, us, meanings = word_data

        # 更新页码
        self.lbl_pos.config(text=f"{self.current_idx + 1}/{len(self.due_list)}")

        # 重置详情状态
        self.show_detail_flag.set(False)
        self.detail_frame.pack_forget()

        # 显示单词
        self.lbl_word.config(text=word)

        # 档位信息
        level_min = EBBINGHAUS_INTERVALS[mem_lv]
        self.lbl_level.config(text=f"记忆档位：{mem_lv} 档 | 当前间隔 {level_min} 分钟")

    def toggle_detail(self):
        """展开/收起详情"""
        if not self.due_list:
            return

        word_data = self.due_list[self.current_idx]
        word, mem_lv, next_ts, uk, us, meanings = word_data

        if self.show_detail_flag.get():
            # 收起
            self.show_detail_flag.set(False)
            self.detail_frame.pack_forget()
        else:
            # 展开
            self.show_detail_flag.set(True)
            self.detail_frame.pack(pady=10)

            self.lbl_uk.config(text=f"英音：{uk if uk else '无'}")
            self.lbl_us.config(text=f"美音：{us if us else '无'}")

            # 加载完整释义
            full_info = self.app.word_service.get_word_details(word)
            sense_str = ""
            ex_str = ""

            if full_info and full_info['senses']:
                for idx, (pos, mean, ex, trans) in enumerate(full_info['senses'], 1):
                    sense_str += f"{idx}. {pos} {mean}\n"
                    if ex:
                        ex_str += f"{idx}. {ex}\n    {trans}\n"

            self.lbl_sense_text.config(text=sense_str)

            if ex_str.strip():
                self.lbl_ex_title.pack()
                self.lbl_ex_text.config(text=ex_str)
                self.lbl_ex_text.pack(pady=4)
            else:
                self.lbl_ex_title.pack_forget()
                self.lbl_ex_text.pack_forget()

            self.lbl_uk.pack()
            self.lbl_us.pack()
            self.lbl_level.pack(pady=3)
            self.lbl_sense_title.pack()
            self.lbl_sense_text.pack(pady=3)

    def speak(self):
        """朗读"""
        if self.due_list:
            word = self.due_list[self.current_idx][0]
            self.app.speak(word)

    def mark_remember(self):
        """标记记住"""
        if not self.due_list:
            return

        word = self.due_list[self.current_idx][0]
        self.app.memory_service.review_word(word, is_remembered=True)
        messagebox.showinfo("记住了", f"「{word}」记忆档位提升，下次复习间隔延长！")
        self.next_card()

    def mark_forget(self):
        """标记遗忘"""
        if not self.due_list:
            return

        word = self.due_list[self.current_idx][0]
        self.app.memory_service.review_word(word, is_remembered=False)
        messagebox.showwarning("遗忘", f"「{word}」已重置初始档位，5分钟后再次复习！")
        self.next_card()

    def next_card(self):
        """切换到下一张卡片"""
        self.current_idx += 1

        if self.current_idx >= len(self.due_list):
            # 全部完成
            self.due_list.clear()
            self.current_idx = 0
            self.lbl_word.config(text="✅ 所有到期单词复习完成！")
            self.detail_frame.pack_forget()
            self.lbl_total.config(text="待复习单词：0 个")
            self.lbl_pos.config(text="0/0")
            messagebox.showinfo("完成", "本轮所有到期单词复习完毕！")
            return

        self.render_card()
