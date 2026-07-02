"""单词录入Tab - 支持一词多义表格形式录入"""
import tkinter as tk
from tkinter import ttk, messagebox


class AddWordTab(tk.Frame):
    """单词录入页面"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        tk.Label(self, text="单词录入（支持一词多义）", font=("微软雅黑", 16, "bold")).pack(pady=15)

        # 基本信息区域
        basic_frame = tk.Frame(self)
        basic_frame.pack(padx=40, pady=5)

        # 单词输入
        tk.Label(basic_frame, text="单词：", width=10, anchor="e", font=("微软雅黑", 11)).grid(row=0, column=0, pady=6)
        self.entry_word = tk.Entry(basic_frame, width=30, font=("微软雅黑", 11))
        self.entry_word.grid(row=0, column=1, pady=6, padx=5)

        # 朗读按钮
        tk.Button(basic_frame, text="🔊 朗读", font=("微软雅黑", 10, "bold"),
                  command=self.speak_word).grid(row=0, column=2, padx=5)

        # 音标输入
        tk.Label(basic_frame, text="英音标：", width=10, anchor="e", font=("微软雅黑", 11)).grid(row=1, column=0, pady=6)
        self.entry_uk = tk.Entry(basic_frame, width=30, font=("微软雅黑", 11))
        self.entry_uk.grid(row=1, column=1, pady=6, padx=5)

        tk.Label(basic_frame, text="美音标：", width=10, anchor="e", font=("微软雅黑", 11)).grid(row=2, column=0, pady=6)
        self.entry_us = tk.Entry(basic_frame, width=30, font=("微软雅黑", 11))
        self.entry_us.grid(row=2, column=1, pady=6, padx=5)

        # 等级选择
        tk.Label(basic_frame, text="等级：", width=10, anchor="e", font=("微软雅黑", 11)).grid(row=3, column=0, pady=6)
        self.cb_level = ttk.Combobox(basic_frame, values=self.app.level_names, width=27, state="readonly")
        self.cb_level.current(0)
        self.cb_level.grid(row=3, column=1, pady=6, padx=5)

        # 释义表格区域
        tk.Label(basic_frame, text="词性、释义、例句（表格形式）：",
                 font=("微软雅黑", 11, "bold")).grid(row=4, column=0, columnspan=3, sticky="w", pady=(15, 5))

        # Treeview 表格
        table_frame = tk.Frame(basic_frame)
        table_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=5)

        self.senses_tree = ttk.Treeview(table_frame, columns=("selected", "pos", "meaning", "example", "translation"),
                                        show="headings", height=6)
        self.senses_tree.heading("selected", text="✓")
        self.senses_tree.heading("pos", text="词性")
        self.senses_tree.heading("meaning", text="释义")
        self.senses_tree.heading("example", text="英文例句")
        self.senses_tree.heading("translation", text="中文翻译")
        self.senses_tree.column("selected", width=40, anchor="center")
        self.senses_tree.column("pos", width=60)
        self.senses_tree.column("meaning", width=120)
        self.senses_tree.column("example", width=200)
        self.senses_tree.column("translation", width=200)
        self.senses_tree.pack(side="left", fill="x", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.senses_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.senses_tree.configure(yscrollcommand=scrollbar.set)

        # 表格操作按钮
        btn_frame = tk.Frame(basic_frame)
        btn_frame.grid(row=6, column=0, columnspan=3, sticky="w", pady=5)

        tk.Button(btn_frame, text="➕ 添加一行", command=self.add_sense_row,
                  font=("微软雅黑", 9), bg="#e8f5e9").pack(side="left", padx=5)
        tk.Button(btn_frame, text="🗑️ 删除选中", command=self.delete_selected_rows,
                  font=("微软雅黑", 9), bg="#ffebee").pack(side="left", padx=5)
        tk.Button(btn_frame, text="🧹 清空全部", command=self.clear_all_rows,
                  font=("微软雅黑", 9), bg="#fff3e0").pack(side="left", padx=5)

        # 绑定双击编辑和勾选
        self.senses_tree.bind("<Double-1>", self.on_double_click)
        self.senses_tree.bind("<Button-1>", self.toggle_selection)

        # 保存按钮
        save_frame = tk.Frame(self)
        save_frame.pack(pady=15)

        ttk.Button(save_frame, text="仅保存单词", style="Mid.TButton",
                   command=self.save_word).grid(row=0, column=0, padx=10)
        ttk.Button(save_frame, text="保存+加入记忆计划", style="Big.TButton",
                   command=self.save_and_add_memory).grid(row=0, column=1, padx=10)

        # 使用说明
        help_text = """💡 使用说明：
1. 点击「➕ 添加一行」添加新的词性和释义
2. 点击第一列的 ☐ 变成 ☑ 来选中行
3. 双击单元格可直接编辑内容（除复选框列）
4. 选中行后点击「🗑️ 删除选中」批量删除
5. 点击【保存+加入记忆计划】自动加入艾宾浩斯间隔复习"""
        tk.Label(self, text=help_text, font=("微软雅黑", 9), fg="gray", justify="left").pack(pady=10)

    def speak_word(self):
        """朗读单词"""
        word = self.entry_word.get().strip()
        if word:
            self.app.speak(word)

    def add_sense_row(self):
        """添加释义行"""
        item_id = self.senses_tree.insert("", "end", values=("☐", "", "", "", ""))
        self.senses_tree.item(item_id, tags=("newrow",))
        # 2秒后刷新颜色
        self.after(2000, self.refresh_row_colors)

    def delete_selected_rows(self):
        """删除选中的行"""
        selected_items = []
        for item in self.senses_tree.get_children():
            values = self.senses_tree.item(item)["values"]
            if values and values[0] == "☑":
                selected_items.append(item)

        if not selected_items:
            messagebox.showwarning("提示", "请先勾选要删除的行（点击第一列的☐变为☑）")
            return

        if messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selected_items)} 行吗？"):
            for item in selected_items:
                self.senses_tree.delete(item)
            self.refresh_row_colors()

    def clear_all_rows(self):
        """清空所有行"""
        if self.senses_tree.get_children() and messagebox.askyesno("确认", "确定要清空所有释义吗？"):
            self.senses_tree.delete(*self.senses_tree.get_children())

    def refresh_row_colors(self):
        """刷新行颜色"""
        all_items = self.senses_tree.get_children()
        for i, item in enumerate(all_items):
            tag = "oddrow" if i % 2 == 0 else "evenrow"
            self.senses_tree.item(item, tags=(tag,))

    def toggle_selection(self, event):
        """切换选中状态"""
        region = self.senses_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = self.senses_tree.identify_column(event.x)
        if column != "#1":
            return
        item = self.senses_tree.identify_row(event.y)
        if not item:
            return

        values = list(self.senses_tree.item(item)["values"])
        values[0] = "☑" if values[0] == "☐" else "☐"
        self.senses_tree.item(item, values=tuple(values))

    def on_double_click(self, event):
        """双击编辑单元格"""
        region = self.senses_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = self.senses_tree.identify_column(event.x)
        if column == "#1":
            return

        item = self.senses_tree.selection()[0] if self.senses_tree.selection() else self.senses_tree.identify_row(
            event.y)
        if not item:
            return

        col_idx = int(column.replace("#", "")) - 1
        bbox = self.senses_tree.bbox(item, column)
        if not bbox:
            return

        x, y, width, height = bbox
        current_values = list(self.senses_tree.item(item)["values"])
        old_value = str(current_values[col_idx])

        edit_entry = tk.Entry(self.senses_tree, font=("微软雅黑", 10))
        edit_entry.place(x=x, y=y, width=width, height=height)
        edit_entry.focus()
        edit_entry.insert(0, old_value)
        edit_entry.select_range(0, tk.END)

        def save_edit(event=None):
            new_value = edit_entry.get().strip()
            updated_values = list(current_values)
            updated_values[col_idx] = new_value
            self.senses_tree.item(item, values=tuple(updated_values))
            edit_entry.destroy()

        def cancel_edit(event=None):
            edit_entry.destroy()

        edit_entry.bind("<Return>", save_edit)
        edit_entry.bind("<Escape>", cancel_edit)
        edit_entry.bind("<FocusOut>", lambda e: save_edit())

    def get_senses_from_tree(self):
        """从表格获取释义列表"""
        senses_list = []
        for item in self.senses_tree.get_children():
            values = self.senses_tree.item(item)["values"]
            pos = str(values[1]).strip() if len(values) > 1 else ""
            meaning = str(values[2]).strip() if len(values) > 2 else ""
            example = str(values[3]).strip() if len(values) > 3 else ""
            translation = str(values[4]).strip() if len(values) > 4 else ""
            if meaning:
                senses_list.append((pos, meaning, example, translation))
        return senses_list

    def save_word(self):
        """保存单词"""
        word = self.entry_word.get().strip()
        if not word:
            messagebox.showwarning("提示", "单词不能为空")
            return

        senses_list = self.get_senses_from_tree()
        if not senses_list:
            messagebox.showwarning("提示", "至少添加一行词性和释义")
            return

        level_idx = self.cb_level.current()
        level_id = self.app.level_ids[level_idx]
        uk = self.entry_uk.get().strip()
        us = self.entry_us.get().strip()

        success, message = self.app.word_service.save_word(word, uk, us, level_id, senses_list)
        if success:
            messagebox.showinfo("成功", message)
            self.clear_form()
        else:
            messagebox.showerror("失败", message)

    def save_and_add_memory(self):
        """保存并加入记忆计划"""
        word = self.entry_word.get().strip()
        if not word:
            messagebox.showwarning("提示", "单词不能为空")
            return

        senses_list = self.get_senses_from_tree()
        if not senses_list:
            messagebox.showwarning("提示", "至少添加一行词性和释义")
            return

        level_idx = self.cb_level.current()
        level_id = self.app.level_ids[level_idx]
        uk = self.entry_uk.get().strip()
        us = self.entry_us.get().strip()

        success, message = self.app.word_service.save_word(word, uk, us, level_id, senses_list)
        if success:
            # 加入记忆计划
            self.app.memory_service.add_word(word)
            messagebox.showinfo("完成", f"「{word}」已保存并加入艾宾浩斯记忆计划！5分钟后首次复习")
            self.clear_form()
        else:
            messagebox.showerror("失败", message)

    def clear_form(self):
        """清空表单"""
        self.entry_word.delete(0, tk.END)
        self.entry_uk.delete(0, tk.END)
        self.entry_us.delete(0, tk.END)
        self.senses_tree.delete(*self.senses_tree.get_children())
