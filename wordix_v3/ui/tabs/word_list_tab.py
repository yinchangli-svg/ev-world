"""词库管理Tab"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class WordListTab(tk.Frame):
    """词库管理页面"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_page = 1

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        tk.Label(self, text="词库管理", font=("微软雅黑", 16, "bold")).pack(pady=5)

        # 搜索和等级选择
        row1 = tk.Frame(self)
        row1.pack(fill="x", padx=20, pady=2)

        tk.Label(row1, text="等级：", font=("微软雅黑", 12)).pack(side="left", padx=2)
        self.level_comb = ttk.Combobox(row1, values=self.app.level_names, width=18, state="readonly")
        self.level_comb.current(0)
        self.level_comb.pack(side="left", padx=5)

        tk.Label(row1, text="搜索：", font=("微软雅黑", 12)).pack(side="left", padx=2)
        self.search_entry = tk.Entry(row1, width=18, font=("微软雅黑", 12))
        self.search_entry.pack(side="left", padx=5)
        tk.Button(row1, text="🔍", font=("微软雅黑", 12, "bold"), width=3,
                  command=self.search_word).pack(side="left")

        # 操作按钮
        row2 = tk.Frame(self)
        row2.pack(fill="x", padx=20, pady=5)

        tk.Button(row2, text="📥 导出", font=("微软雅黑", 11, "bold"),
                  command=self.export_words).pack(side="left", padx=5)
        tk.Button(row2, text="📤 导入", font=("微软雅黑", 11, "bold"),
                  command=self.import_words).pack(side="left", padx=5)

        lbl_temp = tk.Label(row2, text="下载模板", fg="blue", cursor="hand2",
                            font=("微软雅黑", 10, "underline"))
        lbl_temp.pack(side="left", padx=5)
        lbl_temp.bind("<Button-1>", lambda e: self.download_template())

        tk.Button(row2, text="🧠 加入记忆计划", font=("微软雅黑", 11, "bold"),
                  bg="#dceaff", command=self.add_to_memory).pack(side="left", padx=10)

        # 绑定等级变化
        self.level_comb.bind("<<ComboboxSelected>>", self.on_level_change)
        self.search_entry.bind("<Return>", lambda e: self.search_word())

        # 单词列表
        self.tree = ttk.Treeview(self, columns=("w", "uk", "us", "m", "l"),
                                 show="headings", height=15)
        self.tree.heading("w", text="单词")
        self.tree.heading("uk", text="英音")
        self.tree.heading("us", text="美音")
        self.tree.heading("m", text="释义")
        self.tree.heading("l", text="等级")
        self.tree.column("w", width=120)
        self.tree.column("uk", width=90)
        self.tree.column("us", width=90)
        self.tree.column("m", width=320)
        self.tree.column("l", width=120)
        self.tree.pack(padx=20, pady=10, fill="x")

        # 分页
        page_frame = tk.Frame(self)
        page_frame.pack(fill="x", padx=20, pady=5)
        self.page_label = tk.Label(page_frame, text="第 1 页", font=("微软雅黑", 11))
        self.page_label.pack(side="left", padx=10)

        tk.Button(page_frame, text="上一页", command=self.prev_page, width=10).pack(side="left", padx=5)
        tk.Button(page_frame, text="下一页", command=self.next_page, width=10).pack(side="left", padx=5)

        # 绑定双击朗读
        self.tree.bind("<Double-1>", self.on_tree_click)

        # 初始加载
        self.refresh_words()

        tk.Label(self, text="💡 双击朗读单词｜选中可加入记忆计划", font=("微软雅黑", 11)).pack()

    def on_level_change(self, event):
        """等级改变"""
        idx = self.level_comb.current()
        self.app.current_level_id.set(self.app.level_ids[idx])
        self.current_page = 1
        self.refresh_words()

    def refresh_words(self):
        """刷新单词列表"""
        level_id = self.app.level_ids[self.level_comb.current()]
        data, total, total_page = self.app.word_service.get_words_page(level_id, self.current_page, self.app.page_size)

        self.tree.delete(*self.tree.get_children())
        for row in data:
            self.tree.insert("", "end", values=row)

        self.page_label.config(text=f"第 {self.current_page}/{total_page} 页 | 本等级：{total} 个")

    def search_word(self):
        """搜索单词"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            self.refresh_words()
            return

        level_id = self.app.level_ids[self.level_comb.current()]
        res = self.app.word_service.search_word(level_id, keyword)

        if res:
            self.tree.delete(*self.tree.get_children())
            self.tree.insert("", "end", values=res)
            messagebox.showinfo("查找成功", f"找到单词：{keyword}")
        else:
            messagebox.showwarning("未找到", "该等级下无此单词")

    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_words()

    def next_page(self):
        """下一页"""
        level_id = self.app.level_ids[self.level_comb.current()]
        _, _, total_page = self.app.word_service.get_words_page(level_id, self.current_page, self.app.page_size)
        if self.current_page < total_page:
            self.current_page += 1
            self.refresh_words()

    def on_tree_click(self, event):
        """双击朗读"""
        item = self.tree.selection()
        if item:
            word = self.tree.item(item[0], "values")[0]
            self.app.speak(word)

    def export_words(self):
        """导出单词"""
        level_id = self.app.level_ids[self.level_comb.current()]
        level_name = self.app.level_names[self.level_comb.current()]
        self.app.import_export.export_words(level_id, level_name)

    def import_words(self):
        """导入单词"""
        path = filedialog.askopenfilename(filetypes=[("Excel 文件", "*.xlsx;*.xls")])
        if path:
            level_id = self.app.level_ids[self.level_comb.current()]
            self.app.import_export.import_words(level_id, path)
            self.refresh_words()

    def download_template(self):
        """下载模板"""
        self.app.import_export.download_template()

    def add_to_memory(self):
        """添加到记忆计划"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选中表格中的单词")
            return
        word = self.tree.item(sel[0], "values")[0]
        self.app.memory_service.add_word(word)
        messagebox.showinfo("成功", f"「{word}」已加入艾宾浩斯记忆复习计划")
