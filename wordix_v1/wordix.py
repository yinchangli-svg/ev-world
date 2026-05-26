import tkinter as tk
from tkinter import ttk, Frame, Label, Button, Entry, Text, messagebox, filedialog
import sqlite3
import pyttsx3
import pandas as pd
import os

# ======================
# 版本 v1 + 音标朗读 + 等级筛选同步 + 导入导出
# ======================
VERSION = "v1.3 | 玩转单词单机版（发音+等级+导入导出）"
DB_NAME = "wordix.db"

# ======================
# 初始化发音引擎
# ======================
engine = pyttsx3.init()

def speak_word(text):
    if text.strip():
        engine.say(text.strip())
        engine.runAndWait()

# ======================
# 数据库初始化
# ======================
def init_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    sort INTEGER DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL UNIQUE,
                    uk_phonetic TEXT,
                    us_phonetic TEXT,
                    pos TEXT,
                    meaning TEXT NOT NULL,
                    level_id INTEGER,
                    example TEXT,
                    translation TEXT,
                    FOREIGN KEY (level_id) REFERENCES levels(id)
                )''')
    level_data = [
        ('小学3-4年级',10),('小学5-6年级',20),('初中7-9年级',30),
        ('高中必修',40),('高中选择性必修',50),('大学四级',60),
        ('大学六级',70),('托福',80),('雅思',90)
    ]
    for name, sort in level_data:
        c.execute('''INSERT OR IGNORE INTO levels (name, sort)
                      VALUES (?, ?)''', (name, sort))
    conn.commit()
    conn.close()

# ======================
# 工具函数
# ======================
def get_level_options():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, name FROM levels ORDER BY sort")
        data = c.fetchall()
    finally:
        conn.close()
    return data

def get_level_id_by_name(name):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM levels WHERE name=?", (name,))
        res = c.fetchone()
    finally:
        conn.close()
    return res[0] if res else None

def save_word_to_db(word_data):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO words
                     (word, uk_phonetic, us_phonetic, pos, meaning, level_id, example, translation)
                     VALUES (?,?,?,?,?,?,?,?)''', word_data)
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def load_words_by_level_and_page(level_id, page_num, page_size=10):
    try:
        offset = (page_num - 1) * page_size
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT w.word, w.meaning, l.name
                     FROM words w
                     LEFT JOIN levels l ON w.level_id = l.id
                     WHERE w.level_id=?
                     LIMIT ? OFFSET ?''', (level_id, page_size, offset))
        data = c.fetchall()
        c.execute('''SELECT COUNT(*) FROM words WHERE level_id=?''', (level_id,))
        total = c.fetchone()[0]
        total_page = (total + page_size - 1) // page_size
    finally:
        conn.close()
    return data, total, total_page

def search_word_in_db_by_level(level_id, word):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''SELECT w.word, w.meaning, l.name
                     FROM words w
                     LEFT JOIN levels l ON w.level_id = l.id
                     WHERE w.level_id=? AND w.word=?''', (level_id, word))
        res = c.fetchone()
    finally:
        conn.close()
    return res

# ======================
# 导入导出核心函数
# ======================
def export_current_level_words(level_id, level_name):
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql(f"""
            SELECT word, uk_phonetic, us_phonetic, pos, meaning, example, translation
            FROM words WHERE level_id = {level_id}
        """, conn)

        if df.empty:
            messagebox.showwarning("提示", "当前等级暂无单词可导出")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")],
            initialfile=f"{level_name}_单词导出.xlsx"
        )
        if not path:
            return

        df.to_excel(path, index=False)
        messagebox.showinfo("成功", f"已导出 {len(df)} 个单词！")
    except Exception as e:
        messagebox.showerror("错误", f"导出失败：{str(e)}")
    finally:
        conn.close()

def download_import_template():
    template = {
        "word": ["apple"],
        "uk_phonetic": ["ˈæpl"],
        "us_phonetic": ["ˈæpl"],
        "pos": ["n."],
        "meaning": ["苹果"],
        "example": ["This is an apple."],
        "translation": ["这是一个苹果。"]
    }
    df = pd.DataFrame(template)
    path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel 模板", "*.xlsx")],
        initialfile="单词导入模板.xlsx"
    )
    if path:
        df.to_excel(path, index=False)
        messagebox.showinfo("成功", "导入模板已下载完成！")

def import_words_excel(level_id):
    path = filedialog.askopenfilename(
        filetypes=[("Excel 文件", "*.xlsx;*.xls")]
    )
    if not path:
        return

    try:
        df = pd.read_excel(path)
        required = {"word", "meaning"}
        if not required.issubset(df.columns):
            messagebox.showerror("错误", "模板错误！必须包含 word 和 meaning 列")
            return

        success = 0
        fail = 0
        for _, row in df.iterrows():
            word = str(row["word"]).strip()
            meaning = str(row["meaning"]).strip()
            if not word or not meaning:
                fail += 1
                continue

            data = (
                word,
                str(row.get("uk_phonetic", "")).strip(),
                str(row.get("us_phonetic", "")).strip(),
                str(row.get("pos", "")).strip(),
                meaning,
                level_id,
                str(row.get("example", "")).strip(),
                str(row.get("translation", "")).strip()
            )
            if save_word_to_db(data):
                success += 1
            else:
                fail += 1

        messagebox.showinfo("导入完成", f"成功：{success} 个\n重复/失败：{fail} 个")
        refresh_words()
    except Exception as e:
        messagebox.showerror("错误", f"导入失败：{str(e)}")

# ======================
# 主窗口
# ======================
init_database()
root = tk.Tk()
root.title(f"词根单词 · {VERSION}")
root.geometry("920x720")
root.resizable(False, False)

style = ttk.Style()
style.configure("Big.TButton", font=("微软雅黑",13,"bold"), padding=12)

tab_control = ttk.Notebook(root)
tab_control.pack(expand=1, fill="both", padx=10, pady=10)

# ==============================================
# 全局等级变量
# ==============================================
level_list = get_level_options()
level_ids = [item[0] for item in level_list]
level_names = [item[1] for item in level_list]

current_level_id = tk.IntVar(value=level_ids[0] if level_ids else 0)
current_level_name = tk.StringVar(value=level_names[0] if level_names else "")

# ==============================================
# 首页
# ==============================================
tab_home = ttk.Frame(tab_control)
tab_control.add(tab_home, text="首页")
Label(tab_home, text="🔥 词根单词学习系统", font=("微软雅黑",22,"bold")).pack(pady=30)
Label(tab_home, text=VERSION, font=("微软雅黑",12)).pack()

# ==============================================
# 单词录入
# ==============================================
tab_add_word = ttk.Frame(tab_control)
tab_control.add(tab_add_word, text="单词录入")

Label(tab_add_word, text="单词录入", font=("微软雅黑",16,"bold")).pack(pady=15)
f = Frame(tab_add_word)
f.pack(padx=40)

entry_word = Entry(f, width=30)
entry_uk = Entry(f, width=30)
entry_us = Entry(f, width=30)
entry_pos = Entry(f, width=30)
entry_meaning = Entry(f, width=30)

cb_level = ttk.Combobox(f, textvariable=current_level_name, values=level_names, width=27, state="readonly")
cb_level.configure(state="disabled")

btn_speak = Button(f, text="🔊 朗读单词", font=("微软雅黑",10,"bold"),
                   command=lambda: speak_word(entry_word.get()))

rows = [
    ("单词：", entry_word),
    ("英音标：", entry_uk),
    ("美音标：", entry_us),
    ("词性：", entry_pos),
    ("中文释义：", entry_meaning),
    ("等级：", cb_level),
]

for i, (t, e) in enumerate(rows):
    Label(f, text=t, width=10, anchor="e").grid(row=i, column=0, pady=6)
    e.grid(row=i, column=1, pady=6)

btn_speak.grid(row=0, column=2, padx=10, pady=6)

Label(f, text="英文例句：").grid(row=10, column=0, sticky="ne", pady=6)
txt_example = Text(f, width=28, height=3)
txt_example.grid(row=10, column=1, pady=6)

Label(f, text="中文翻译：").grid(row=11, column=0, sticky="ne", pady=6)
txt_trans = Text(f, width=28, height=3)
txt_trans.grid(row=11, column=1, pady=6)

def save_word():
    word = entry_word.get().strip()
    meaning = entry_meaning.get().strip()
    if not word or not meaning:
        messagebox.showwarning("提示","单词和释义不能为空")
        return

    level_id = current_level_id.get()
    data = (
        word,
        entry_uk.get().strip(),
        entry_us.get().strip(),
        entry_pos.get().strip(),
        meaning,
        level_id,
        txt_example.get("1.0", tk.END).strip(),
        txt_trans.get("1.0", tk.END).strip()
    )

    if save_word_to_db(data):
        messagebox.showinfo("成功",f"单词已保存到：{current_level_name.get()}")
        entry_word.delete(0,tk.END)
        entry_uk.delete(0,tk.END)
        entry_us.delete(0,tk.END)
        entry_pos.delete(0,tk.END)
        entry_meaning.delete(0,tk.END)
        txt_example.delete("1.0",tk.END)
        txt_trans.delete("1.0",tk.END)
        refresh_words()
    else:
        messagebox.showerror("失败","单词已存在")

ttk.Button(tab_add_word, text="保存单词", style="Big.TButton", command=save_word).pack(pady=15)

# ==============================================
# 词库管理（已修复：全部按钮可见）
# ==============================================
tab_table = ttk.Frame(tab_control)
tab_control.add(tab_table, text="词库管理")

Label(tab_table, text="词库管理", font=("微软雅黑",16,"bold")).pack(pady=5)

# ====================== 第一行：等级 + 搜索 ======================
row1 = Frame(tab_table)
row1.pack(fill="x", padx=20, pady=2)
Label(row1, text="等级：", font=("微软雅黑",12)).pack(side="left", padx=2)
level_comb = ttk.Combobox(row1, textvariable=current_level_name, values=level_names, width=18, state="readonly")
level_comb.pack(side="left", padx=5)

Label(row1, text="搜索：", font=("微软雅黑",12)).pack(side="left", padx=2)
search_entry = Entry(row1, width=18, font=("微软雅黑",12))
search_entry.pack(side="left", padx=5)
#Button(row1, text="搜索", command=lambda: search_word()).pack(side="left")

# 🔍 搜索按钮（放大镜图标）
Button(row1, text="🔍", font=("微软雅黑", 12, "bold"), width=3,
       command=lambda: search_word()).pack(side="left")

# ====================== 第二行：图标按钮 ======================
row2 = Frame(tab_table)
row2.pack(fill="x", padx=20, pady=5)

# 📥 导出 = 下载图标
Button(row2, text="📥 导出", font=("微软雅黑", 11, "bold"),
       command=lambda: export_current_level_words(current_level_id.get(), current_level_name.get())
      ).pack(side="left", padx=5)

# 📤 导入 = 上传图标
Button(row2, text="📤 导入", font=("微软雅黑", 11, "bold"),
       command=lambda: import_words_excel(current_level_id.get())
      ).pack(side="left", padx=5)

# 蓝色链接
lbl_temp = Label(row2, text="下载导入模板", fg="blue", cursor="hand2", font=("微软雅黑",10,"underline"))
lbl_temp.pack(side="left", padx=5)
lbl_temp.bind("<Button-1>", lambda e: download_import_template())

# 分页
current_page = 1
page_size = 10

def on_level_change(event):
    idx = level_comb.current()
    current_level_id.set(level_ids[idx])
    global current_page
    current_page = 1
    refresh_words()

level_comb.bind("<<ComboboxSelected>>", on_level_change)

def search_word():
    keyword = search_entry.get().strip()
    if not keyword:
        refresh_words()
        return
    res = search_word_in_db_by_level(current_level_id.get(), keyword)
    if res:
        tree.delete(*tree.get_children())
        tree.insert("", "end", values=res)
        tree.selection_set(tree.get_children()[0])
        messagebox.showinfo("查找成功", f"找到单词：{keyword}")
    else:
        messagebox.showwarning("未找到", "该等级下无此单词")

search_entry.bind("<Return>", lambda e: search_word())

# ====================== 单词列表 ======================
tree = ttk.Treeview(tab_table, columns=("w","m","l"), show="headings", height=15)
tree.heading("w", text="单词")
tree.heading("m", text="释义")
tree.heading("l", text="等级")
tree.column("w", width=140)
tree.column("m", width=350)
tree.column("l", width=120)
tree.pack(padx=20, pady=10, fill="x")

# ====================== 分页 ======================
page_frame = Frame(tab_table)
page_frame.pack(fill="x", padx=20, pady=5)

page_label = Label(page_frame, text="第 1 页", font=("微软雅黑",11))
page_label.pack(side="left", padx=10)

def prev_page():
    global current_page
    if current_page > 1:
        current_page -= 1
        refresh_words()

def next_page():
    global current_page
    _, _, total_page = load_words_by_level_and_page(current_level_id.get(), current_page, page_size)
    if current_page < total_page:
        current_page += 1
        refresh_words()

btn_prev = Button(page_frame, text="上一页", command=prev_page, width=10)
btn_prev.pack(side="left", padx=5)
btn_next = Button(page_frame, text="下一页", command=next_page, width=10)
btn_next.pack(side="left", padx=5)

def on_tree_click(event):
    item = tree.selection()
    if item:
        word = tree.item(item[0], "values")[0]
        speak_word(word)

tree.bind("<Double-1>", on_tree_click)
tree.bind("<Return>", on_tree_click)

def refresh_words():
    data, total, total_page = load_words_by_level_and_page(current_level_id.get(), current_page, page_size)
    tree.delete(*tree.get_children())
    for row in data:
        tree.insert("", "end", values=row)
    page_label.config(text=f"第 {current_page}/{total_page} 页 | 本等级：{total} 个")

refresh_words()
Label(tab_table, text="💡 双击 / 回车 发音｜导入导出支持 Excel", font=("微软雅黑",11)).pack()

# ======================
# 启动
# ======================
root.mainloop()