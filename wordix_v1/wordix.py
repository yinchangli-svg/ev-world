import tkinter as tk
from tkinter import ttk, Frame, Label, Button, Entry, Text, messagebox
import sqlite3
import pyttsx3  # 内置发音引擎，无需联网 / 无需额外安装

# ======================
# 版本 v1 + 音标朗读功能
# ======================
VERSION = "v1 | 玩转单词单机版（带发音）"
DB_NAME = "wordix.db"

# ======================
# 初始化发音引擎
# ======================
engine = pyttsx3.init()

# 朗读英文单词
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

    # 等级表
    c.execute('''CREATE TABLE IF NOT EXISTS levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    sort INTEGER DEFAULT 0
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
                    example TEXT,
                    translation TEXT,
                    FOREIGN KEY (level_id) REFERENCES levels(id)
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
        c.execute('''INSERT OR IGNORE INTO levels (name, sort)
                      VALUES (?, ?)''', (name, sort))
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
                     (word, uk_phonetic, us_phonetic, pos, meaning, level_id,
                     example, translation)
                     VALUES (?,?,?,?,?,?,?,?)''', word_data)
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

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

# 分页查询单词
def load_words_by_page(page_num, page_size=10):
    offset = (page_num - 1) * page_size
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT w.word, w.meaning, l.name
                 FROM words w
                 LEFT JOIN levels l ON w.level_id = l.id
                 LIMIT ? OFFSET ?''', (page_size, offset))
    data = c.fetchall()
    # 获取总条数
    c.execute('''SELECT COUNT(*) FROM words''')
    total = c.fetchone()[0]
    conn.close()
    total_page = (total + page_size - 1) // page_size
    return data, total, total_page

# 精确查找单词
def search_word_in_db(word):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT w.word, w.meaning, l.name
                 FROM words w
                 LEFT JOIN levels l ON w.level_id = l.id
                 WHERE w.word = ?''', (word,))
    res = c.fetchone()
    conn.close()
    return res

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
# 单词录入（新增：发音按钮）
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

cb_level = ttk.Combobox(f, textvariable=level_var, values=level_names, width=27, state="readonly")

# 发音按钮
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

# 朗读按钮放在单词输入框同一行
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

    # 转换ID
    level_id = get_level_id_by_name(level_var.get())

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
# 词库管理（新增：查找功能 + 分页功能）
# ==============================================
tab_table = ttk.Frame(tab_control)
tab_control.add(tab_table, text="词库管理")

Label(tab_table, text="词库管理", font=("微软雅黑",16,"bold")).pack(pady=5)

# ====================== 搜索框区域 ======================
search_frame = Frame(tab_table)
search_frame.pack(fill="x", padx=20, pady=5)
Label(search_frame, text="查找单词：", font=("微软雅黑",12)).pack(side="left", padx=5)
search_entry = Entry(search_frame, width=25, font=("微软雅黑",12))
search_entry.pack(side="left", padx=5)

# 分页全局变量
current_page = 1
page_size = 10

# 搜索功能（回车触发）
def search_word():
    keyword = search_entry.get().strip()
    if not keyword:
        refresh_words()
        return
    res = search_word_in_db(keyword)
    if res:
        tree.delete(*tree.get_children())
        tree.insert("", "end", values=res)
        # 自动选中找到的行
        tree.selection_set(tree.get_children()[0])
        messagebox.showinfo("查找成功", f"找到单词：{keyword}")
    else:
        messagebox.showwarning("未找到", f"词库中不存在单词：{keyword}")

search_entry.bind("<Return>", lambda e: search_word())
Button(search_frame, text="搜索", command=search_word, width=8).pack(side="left", padx=5)

# ====================== 单词列表 ======================
tree = ttk.Treeview(tab_table, columns=("w","m","l"), show="headings", height=15)
tree.heading("w", text="单词")
tree.heading("m", text="释义")
tree.heading("l", text="等级")
tree.column("w", width=140)
tree.column("m", width=350)
tree.column("l", width=120)
tree.pack(padx=20, pady=10, fill="x")

# ====================== 分页控件 ======================
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
    _, _, total_page = load_words_by_page(current_page, page_size)
    if current_page < total_page:
        current_page += 1
        refresh_words()

btn_prev = Button(page_frame, text="上一页", command=prev_page, width=10)
btn_prev.pack(side="left", padx=5)
btn_next = Button(page_frame, text="下一页", command=next_page, width=10)
btn_next.pack(side="left", padx=5)


# 选中朗读
def on_tree_click(event):
    item = tree.selection()
    if item:
        word = tree.item(item[0], "values")[0]
        speak_word(word)

tree.bind("<Double-1>", on_tree_click)  # 双击朗读
tree.bind("<Return>", on_tree_click)    # 回车朗读


# 刷新分页列表
def refresh_words():
    data, total, total_page = load_words_by_page(current_page, page_size)
    tree.delete(*tree.get_children())
    for row in data:
        tree.insert("", "end", values=row)
    page_label.config(text=f"第 {current_page}/{total_page} 页  总计：{total} 个单词")



refresh_words()

# 提示标签
Label(tab_table, text="💡 双击单词 / 按回车 即可发音", font=("微软雅黑",11)).pack()

# ======================
# 启动
# ======================
root.mainloop()