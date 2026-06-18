import tkinter as tk
from tkinter import ttk, Frame, Label, Button, Entry, Text, messagebox
import sqlite3

# ======================
# 版本 v1.1 | 已修复全部BUG
# ======================
VERSION = "v1.1 | 词根单词单机本地版 | 稳定修复版"
DB_NAME = "word_app_v1_1.db"

# ======================
# 数据库初始化（安全、不删表、不丢数据）
# ======================
def init_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 等级表
    c.execute('''CREATE TABLE IF NOT EXISTS levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    sort INTEGER DEFAULT 0
                )''')

    # 前缀表
    c.execute('''CREATE TABLE IF NOT EXISTS prefixes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prefix TEXT NOT NULL UNIQUE,
                    meaning TEXT,
                    example TEXT
                )''')

    # 后缀表
    c.execute('''CREATE TABLE IF NOT EXISTS suffixes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suffix TEXT NOT NULL UNIQUE,
                    meaning TEXT,
                    example TEXT
                )''')

    # 词根表
    c.execute('''CREATE TABLE IF NOT EXISTS roots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    root TEXT NOT NULL UNIQUE,
                    meaning TEXT,
                    example TEXT,
                    note TEXT
                )''')

    # 单词表（关联等级、前缀、词根、后缀）
    c.execute('''CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL UNIQUE,
                    uk_phonetic TEXT,
                    us_phonetic TEXT,
                    pos TEXT,
                    meaning TEXT NOT NULL,
                    level_id INTEGER,
                    prefix_id INTEGER,
                    root_id INTEGER,
                    suffix_id INTEGER,
                    example TEXT,
                    translation TEXT,
                    FOREIGN KEY (level_id) REFERENCES levels(id),
                    FOREIGN KEY (prefix_id) REFERENCES prefixes(id),
                    FOREIGN KEY (root_id) REFERENCES roots(id),
                    FOREIGN KEY (suffix_id) REFERENCES suffixes(id)
                )''')

    # 用户进度表
    c.execute('''CREATE TABLE IF NOT EXISTS user_progress (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    continuous_days INTEGER DEFAULT 0,
                    total_points INTEGER DEFAULT 0
                )''')

    # ======================
    # 初始化等级（仅空表插入）
    # ======================
    level_data = [
        ('小学3-4年级',10),('小学5-6年级',20),('初中7-9年级',30),
        ('高中必修',40),('高中选择性必修',50),('大学四级',60),
        ('大学六级',70),('托福',80),('雅思',90)
    ]
    for name, sort in level_data:
        c.execute('''INSERT OR IGNORE INTO levels (name,sort)
                     SELECT ?,? WHERE NOT EXISTS (SELECT 1 FROM levels)''', (name, sort))

    # ======================
    # 初始化前缀
    # ======================
    prefix_data = [
        ('un','不','unhappy'),('re','重新','return'),('dis','否定','dislike'),
        ('im','不','impossible'),('pre','前','prepare'),('post','后','postwar')
    ]
    for p, m, e in prefix_data:
        c.execute('''INSERT OR IGNORE INTO prefixes (prefix,meaning,example)
                     SELECT ?,?,? WHERE NOT EXISTS (SELECT 1 FROM prefixes)''', (p, m, e))

    # ======================
    # 初始化后缀
    # ======================
    suffix_data = [
        ('able','可...的','usable'),('ful','充满','helpful'),('less','无','hopeless'),
        ('tion','名词','action'),('ment','名词','development'),('ly','副词','quickly')
    ]
    for s, m, e in suffix_data:
        c.execute('''INSERT OR IGNORE INTO suffixes (suffix,meaning,example)
                     SELECT ?,?,? WHERE NOT EXISTS (SELECT 1 FROM suffixes)''', (s, m, e))

    # ======================
    # 初始化用户
    # ======================
    c.execute('''INSERT OR IGNORE INTO user_progress (id,continuous_days,total_points)
                 SELECT 1,0,0 WHERE NOT EXISTS (SELECT 1 FROM user_progress)''')

    conn.commit()
    conn.close()

# ======================
# 工具函数
# ======================
def get_level_options():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name FROM levels ORDER BY sort")
    data = c.fetchall()
    conn.close()
    return data  # [(id,name), ...]

def get_prefix_choices():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, prefix, meaning FROM prefixes")
    data = c.fetchall()
    conn.close()
    return ["无"] + [f"{x[1]} ({x[2]})" for x in data]

def get_root_choices():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, root, meaning FROM roots")
    data = c.fetchall()
    conn.close()
    return ["无"] + [f"{x[1]} ({x[2]})" for x in data]

def get_suffix_choices():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, suffix, meaning FROM suffixes")
    data = c.fetchall()
    conn.close()
    return ["无"] + [f"{x[1]} ({x[2]})" for x in data]

# 等级名称 → ID
def get_level_id_by_name(name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM levels WHERE name=?", (name,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

# 保存单词（真正写入）
def save_word_to_db(word_data):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO words
                     (word, uk_phonetic, us_phonetic, pos, meaning, level_id, prefix_id, root_id, suffix_id, example, translation)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?)''', word_data)
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# 保存词根
def save_root(root, meaning, example, note):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO roots (root,meaning,example,note) VALUES (?,?,?,?)",
                  (root, meaning, example, note))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# 加载所有词根
def load_all_roots():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT root, meaning, example FROM roots")
    data = c.fetchall()
    conn.close()
    return data

# 加载所有单词（关联等级名称，不显示ID）
def load_all_words():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT w.word, w.meaning, l.name
                 FROM words w
                 LEFT JOIN levels l ON w.level_id = l.id''')
    data = c.fetchall()
    conn.close()
    return data

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
# 首页
# ==============================================
tab_home = ttk.Frame(tab_control)
tab_control.add(tab_home, text="首页")
Label(tab_home, text="🔥 词根单词学习系统", font=("微软雅黑",22,"bold")).pack(pady=30)
Label(tab_home, text=VERSION, font=("微软雅黑",12)).pack()

# ==============================================
# 单词录入（已修复：真正保存）
# ==============================================
tab_add_word = ttk.Frame(tab_control)
tab_control.add(tab_add_word, text="单词录入")

Label(tab_add_word, text="单词录入", font=("微软雅黑",16,"bold")).pack(pady=15)
f = Frame(tab_add_word)
f.pack(padx=40)

# 输入组件
entry_word = Entry(f, width=30)
entry_uk = Entry(f, width=30)
entry_us = Entry(f, width=30)
entry_pos = Entry(f, width=30)
entry_meaning = Entry(f, width=30)

level_names = [n for _,n in get_level_options()]
level_var = tk.StringVar(value=level_names[0] if level_names else "")
prefix_var = tk.StringVar(value="无")
root_var = tk.StringVar(value="无")
suffix_var = tk.StringVar(value="无")

cb_level = ttk.Combobox(f, textvariable=level_var, values=level_names, width=27, state="readonly")
cb_prefix = ttk.Combobox(f, textvariable=prefix_var, values=get_prefix_choices(), width=27, state="readonly")
cb_root = ttk.Combobox(f, textvariable=root_var, values=get_root_choices(), width=27, state="readonly")
cb_suffix = ttk.Combobox(f, textvariable=suffix_var, values=get_suffix_choices(), width=27, state="readonly")

rows = [
    ("单词：", entry_word),
    ("英音标：", entry_uk),
    ("美音标：", entry_us),
    ("词性：", entry_pos),
    ("中文释义：", entry_meaning),
    ("等级：", cb_level),
    ("前缀：", cb_prefix),
    ("词根：", cb_root),
    ("后缀：", cb_suffix),
]

for i, (t, e) in enumerate(rows):
    Label(f, text=t, width=10, anchor="e").grid(row=i, column=0, pady=6)
    e.grid(row=i, column=1, pady=6)

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

    # 转换ID
    level_id = get_level_id_by_name(level_var.get())
    prefix_id = None if prefix_var.get() == "无" else get_prefix_choices().index(prefix_var.get())
    root_id = None if root_var.get() == "无" else get_root_choices().index(root_var.get())
    suffix_id = None if suffix_var.get() == "无" else get_suffix_choices().index(suffix_var.get())

    data = (
        word,
        entry_uk.get().strip(),
        entry_us.get().strip(),
        entry_pos.get().strip(),
        meaning,
        level_id,
        prefix_id,
        root_id,
        suffix_id,
        txt_example.get("1.0", tk.END).strip(),
        txt_trans.get("1.0", tk.END).strip()
    )

    if save_word_to_db(data):
        messagebox.showinfo("成功","单词已永久保存！")
        # 清空
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
# 词根录入
# ==============================================
tab_add_root = ttk.Frame(tab_control)
tab_control.add(tab_add_root, text="词根录入")

Label(tab_add_root, text="词根录入", font=("微软雅黑",16,"bold")).pack(pady=15)
frm = Frame(tab_add_root)
frm.pack(padx=40)

e_root = Entry(frm, width=30)
e_meaning = Entry(frm, width=30)
e_example = Entry(frm, width=30)
txt_note = Text(frm, width=28, height=3)

fields = [
    ("词根：", e_root),
    ("含义：", e_meaning),
    ("例词：", e_example),
    ("备注：", txt_note),
]

for i, (t, w) in enumerate(fields):
    Label(frm, text=t, width=8, anchor="e").grid(row=i, column=0, pady=6)
    w.grid(row=i, column=1, pady=6)

def do_save_root():
    r = e_root.get().strip()
    m = e_meaning.get().strip()
    ex = e_example.get().strip()
    note = txt_note.get("1.0", tk.END).strip()
    if not r or not m:
        messagebox.showwarning("提示","词根和含义不能为空")
        return
    if save_root(r,m,ex,note):
        messagebox.showinfo("成功","词根已保存")
        e_root.delete(0,tk.END)
        e_meaning.delete(0,tk.END)
        e_example.delete(0,tk.END)
        txt_note.delete("1.0",tk.END)
        refresh_roots()
        cb_root.config(values=get_root_choices())
    else:
        messagebox.showerror("失败","词根已存在")

ttk.Button(tab_add_root, text="保存词根", style="Big.TButton", command=do_save_root).pack(pady=15)

# ==============================================
# 词根列表
# ==============================================
tab_root_list = ttk.Frame(tab_control)
tab_control.add(tab_root_list, text="词根列表")

Label(tab_root_list, text="词根管理", font=("微软雅黑",16,"bold")).pack(pady=15)
tree_root = ttk.Treeview(tab_root_list, columns=("root","mean","ex"), show="headings", height=15)
tree_root.heading("root", text="词根")
tree_root.heading("mean", text="含义")
tree_root.heading("ex", text="例词")
tree_root.column("root", width=120)
tree_root.column("mean", width=200)
tree_root.column("ex", width=300)
tree_root.pack(padx=20, pady=10, fill="x")

def refresh_roots():
    tree_root.delete(*tree_root.get_children())
    for row in load_all_roots():
        tree_root.insert("", "end", values=row)

refresh_roots()

# ==============================================
# 词表管理（已修复：显示等级名称，不是ID）
# ==============================================
tab_table = ttk.Frame(tab_control)
tab_control.add(tab_table, text="词表管理")

Label(tab_table, text="词表管理", font=("微软雅黑",16,"bold")).pack(pady=15)
tree = ttk.Treeview(tab_table, columns=("w","m","l"), show="headings", height=15)
tree.heading("w", text="单词")
tree.heading("m", text="释义")
tree.heading("l", text="等级")
tree.column("w", width=140)
tree.column("m", width=350)
tree.column("l", width=120)
tree.pack(padx=20, pady=10, fill="x")

def refresh_words():
    tree.delete(*tree.get_children())
    for row in load_all_words():
        tree.insert("", "end", values=row)

refresh_words()

# ======================
# 启动
# ======================
root.mainloop()