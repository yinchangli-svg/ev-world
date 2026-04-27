import tkinter as tk
from tkinter import ttk, Frame, Label, Button, Entry, Text, messagebox
import sqlite3
import random
from datetime import date

# ======================
# 版本 v1.2.1 | 单词录入界面修复
# ======================
VERSION = "v1.2.1 | 词根单词单机本地版 | 稳定完整版"

# ======================
# 统一数据库名
# ======================
DB_NAME = "wordapp.db"

# ======================
# 数据库初始化
# ======================
def init_db():
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

    # 单词表
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

    # 用户进度
    c.execute('''CREATE TABLE IF NOT EXISTS user_progress (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    continuous_days INTEGER DEFAULT 0,
                    total_points INTEGER DEFAULT 0
                )''')

    # 例句
    c.execute('''CREATE TABLE IF NOT EXISTS examples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    en_sentence TEXT NOT NULL,
                    cn_sentence TEXT NOT NULL,
                    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
                )''')

    # 每日学习
    c.execute('''CREATE TABLE IF NOT EXISTS daily_study (
                    study_date DATE PRIMARY KEY,
                    target_count INTEGER DEFAULT 20,
                    done_count INTEGER DEFAULT 0
                )''')

    # 单词掌握
    c.execute('''CREATE TABLE IF NOT EXISTS word_mastery (
                    word_id INTEGER PRIMARY KEY,
                    is_mastered INTEGER DEFAULT 0,
                    study_count INTEGER DEFAULT 0,
                    wrong_count INTEGER DEFAULT 0,
                    last_review DATE,
                    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
                )''')

    # 错题本
    c.execute('''CREATE TABLE IF NOT EXISTS wrong_book (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    wrong_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
                )''')

    # 勋章
    c.execute('''CREATE TABLE IF NOT EXISTS medals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    icon TEXT,
                    is_unlocked INTEGER DEFAULT 0
                )''')

    # 初始化等级
    level_data = [
        ('小学3-4年级', 10), ('小学5-6年级', 20), ('初中7-9年级', 30),
        ('高中必修', 40), ('高中选择性必修', 50), ('大学四级', 60),
        ('大学六级', 70), ('托福', 80), ('雅思', 90)
    ]
    for name, sort in level_data:
        c.execute('INSERT OR IGNORE INTO levels (name, sort) VALUES (?,?)', (name, sort))

    # 初始化前缀
    prefix_data = [
        ('un', '不', 'unhappy'), ('re', '重新', 'return'), ('dis', '否定', 'dislike'),
        ('im', '不', 'impossible'), ('pre', '前', 'prepare'), ('post', '后', 'postwar')
    ]
    for p, m, e in prefix_data:
        c.execute('INSERT OR IGNORE INTO prefixes (prefix, meaning, example) VALUES (?,?,?)', (p, m, e))

    # 初始化后缀
    suffix_data = [
        ('able', '可...的', 'usable'), ('ful', '充满', 'helpful'), ('less', '无', 'hopeless'),
        ('tion', '名词', 'action'), ('ment', '名词', 'development'), ('ly', '副词', 'quickly')
    ]
    for s, m, e in suffix_data:
        c.execute('INSERT OR IGNORE INTO suffixes (suffix, meaning, example) VALUES (?,?,?)', (s, m, e))

    # 初始化用户
    c.execute('INSERT OR IGNORE INTO user_progress (id, continuous_days, total_points) VALUES (1,0,0)')

    conn.commit()
    conn.close()

# ======================
# 工具函数
# ======================
def get_level_list():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name FROM levels ORDER BY sort")
    data = c.fetchall()
    conn.close()
    return data

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

def get_level_id(name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM levels WHERE name=?", (name,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

def get_id_from_choice(choices, value):
    try:
        idx = choices.index(value)
        return idx if idx > 0 else None
    except:
        return None

def save_root(root, meaning, example, note):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO roots (root, meaning, example, note) VALUES (?,?,?,?)",
                  (root, meaning, example, note))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def load_all_roots():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT root, meaning, example FROM roots")
    data = c.fetchall()
    conn.close()
    return data

def save_word(word_data):
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

def load_all_words():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT w.word, w.meaning, l.name
                 FROM words w LEFT JOIN levels l ON w.level_id = l.id''')
    data = c.fetchall()
    conn.close()
    return data

def get_random_word():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, word, meaning FROM words ORDER BY RANDOM() LIMIT 1')
    word = c.fetchone()
    conn.close()
    return word

def get_user_points():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    p = c.execute("SELECT total_points FROM user_progress WHERE id=1").fetchone()[0]
    conn.close()
    return p

def add_points(p):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE user_progress SET total_points = total_points + ? WHERE id=1", (p,))
    conn.commit()
    conn.close()

def add_wrong(word_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO wrong_book (word_id) VALUES (?)", (word_id,))
    conn.commit()
    conn.close()

def generate_mask(word):
    if len(word) <= 2:
        return word[0] + "__"
    return word[0] + "_" * (len(word) - 2) + word[-1]

# ======================
# 学习页
# ======================
class StudyPage:
    def __init__(self, frame):
        self.frame = frame
        self.word_list = []
        self.current_idx = -1
        self.create_widgets()
        self.load_words()
        self.show_next()

    def load_words(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''SELECT w.id, w.word, w.uk_phonetic, w.us_phonetic, w.pos, w.meaning,
                        COALESCE(r.root, "无") FROM words w
                        LEFT JOIN roots r ON w.root_id = r.id''')
            self.word_list = c.fetchall()
            conn.close()
        except:
            self.word_list = []

    def create_widgets(self):
        Label(self.frame, text="单词学习", font=("微软雅黑", 18, "bold")).pack(pady=20)
        self.card = ttk.Frame(self.frame, padding=25, relief="ridge")
        self.card.pack(padx=50, pady=15, fill="x")
        self.lb_word = Label(self.card, font=("Arial", 30, "bold"))
        self.lb_pho = Label(self.card, font=("Arial", 14))
        self.lb_pos = Label(self.card, font=("微软雅黑", 16))
        self.lb_mean = Label(self.card, font=("微软雅黑", 16), wraplength=600)
        self.lb_root = Label(self.card, font=("微软雅黑", 13), fg="#165DFF")
        for w in [self.lb_word, self.lb_pho, self.lb_pos, self.lb_mean, self.lb_root]:
            w.pack(pady=2)
        btn_box = Frame(self.frame)
        btn_box.pack(pady=25)
        ttk.Button(btn_box, text="上一词", command=self.show_prev).grid(row=0, column=0, padx=15)
        ttk.Button(btn_box, text="已掌握", command=self.do_master).grid(row=0, column=1, padx=15)
        ttk.Button(btn_box, text="下一词", command=self.show_next).grid(row=0, column=2, padx=15)

    def show(self, word):
        _id, w, uk, us, pos, m, r = word
        self.lb_word.config(text=w)
        pho = f"英 /{uk}/ " if uk else ""
        pho += f"美 /{us}/" if us else ""
        self.lb_pho.config(text=pho.strip())
        self.lb_pos.config(text=pos or "")
        self.lb_mean.config(text=m)
        self.lb_root.config(text=f"词根：{r}")

    def show_next(self):
        if not self.word_list:
            messagebox.showinfo("提示", "请先添加单词！")
            return
        self.current_idx = (self.current_idx + 1) % len(self.word_list)
        self.show(self.word_list[self.current_idx])

    def show_prev(self):
        if not self.word_list:
            messagebox.showinfo("提示", "请先添加单词！")
            return
        self.current_idx = (self.current_idx - 1) % len(self.word_list)
        self.show(self.word_list[self.current_idx])

    def do_master(self):
        if not self.word_list:
            return
        word_id = self.word_list[self.current_idx][0]
        today = str(date.today())
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO word_mastery (word_id) VALUES (?)', (word_id,))
        c.execute('UPDATE word_mastery SET is_mastered=1, study_count=study_count+1, last_review=? WHERE word_id=?', (today, word_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("成功", "已标记为已掌握")
        self.show_next()

# ======================
# 练习页
# ======================
class PracticePage:
    def __init__(self, frame):
        self.frame = frame
        self.current_word = None
        self.current_id = None
        self.answer = tk.StringVar()
        self.create_widgets()
        self.next_question()

    def create_widgets(self):
        Label(self.frame, text="单词练习 · 字母填空", font=("微软雅黑", 18, "bold")).pack(pady=15)
        self.points_label = Label(self.frame, text=f"当前积分：{get_user_points()}", font=("微软雅黑", 13))
        self.points_label.pack(pady=5)
        self.q_frame = ttk.Frame(self.frame, padding=25, relief="ridge")
        self.q_frame.pack(padx=60, pady=20, fill="x")
        self.meaning_label = Label(self.q_frame, font=("微软雅黑", 16), wraplength=600)
        self.meaning_label.pack(pady=8)
        self.mask_label = Label(self.q_frame, font=("Arial", 22, "bold"))
        self.mask_label.pack(pady=10)
        self.entry_ans = Entry(self.q_frame, textvariable=self.answer, font=("Arial", 16), width=12)
        self.entry_ans.pack(pady=8)
        ttk.Button(self.frame, text="提交答案", command=self.check_answer).pack(pady=8)
        self.result_label = Label(self.frame, font=("微软雅黑", 14))
        self.result_label.pack(pady=5)

    def next_question(self):
        self.answer.set("")
        self.result_label.config(text="")
        word = get_random_word()
        if not word:
            self.meaning_label.config(text="⚠️ 请先去单词录入添加单词！")
            self.mask_label.config(text="")
            self.entry_ans.config(state="disabled")
            return
        self.entry_ans.config(state="normal")
        self.current_id, self.current_word, meaning = word
        self.meaning_label.config(text=f"释义：{meaning}")
        self.mask_label.config(text=generate_mask(self.current_word))
        self.points_label.config(text=f"当前积分：{get_user_points()}")

    def check_answer(self):
        if not self.current_word:
            messagebox.showinfo("提示", "请先录入单词！")
            return
        user_ans = self.answer.get().strip().lower()
        correct = self.current_word.lower()
        if user_ans == correct:
            self.result_label.config(text="✅ 正确！+5分", fg="green")
            add_points(5)
        else:
            self.result_label.config(text=f"❌ 错误：{self.current_word}", fg="red")
            add_wrong(self.current_id)
        self.frame.after(1000, self.next_question)

# ======================
# 主界面
# ======================
init_db()
root = tk.Tk()
root.title(f"词根单词 · {VERSION}")
root.geometry("920x720")
root.resizable(False, False)

# 样式
style = ttk.Style()
style.configure("Big.TButton", font=("微软雅黑", 13, "bold"), padding=10)

tab = ttk.Notebook(root)
tab.pack(expand=1, fill="both", padx=10,pady=10)

# 1 首页
home = ttk.Frame(tab)
tab.add(home, text="首页")
Label(home, text="🔥 词根单词单机版", font=("微软雅黑",20,"bold")).pack(pady=100)
Label(home, text=VERSION, font=("微软雅黑",12)).pack()

# 2 学习页
study_frame = ttk.Frame(tab)
tab.add(study_frame, text="开始学习")
study = StudyPage(study_frame)

# 3 练习页
practice_frame = ttk.Frame(tab)
tab.add(practice_frame, text="单词练习")
practice = PracticePage(practice_frame)

# 4 单词录入
add_f = ttk.Frame(tab)
tab.add(add_f, text="单词录入")
Label(add_f, text="单词录入", font=("微软雅黑",18,"bold")).pack(pady=10)
f = Frame(add_f)
f.pack(padx=50)

entry_word = Entry(f, width=30)
entry_uk = Entry(f, width=30)
entry_us = Entry(f, width=30)
entry_pos = Entry(f, width=30)
entry_mean = Entry(f, width=30)

level_names = [n for _, n in get_level_list()]
level_var = tk.StringVar(value=level_names[0] if level_names else "")
prefix_var = tk.StringVar(value="无")
root_var = tk.StringVar(value="无")
suffix_var = tk.StringVar(value="无")

cb_level = ttk.Combobox(f, textvariable=level_var, values=level_names, width=27, state="readonly")
cb_prefix = ttk.Combobox(f, textvariable=prefix_var, values=get_prefix_choices(), width=27, state="readonly")
cb_root = ttk.Combobox(f, textvariable=root_var, values=get_root_choices(), width=27, state="readonly")
cb_suffix = ttk.Combobox(f, textvariable=suffix_var, values=get_suffix_choices(), width=27, state="readonly")

# ======================
# 修复：字段完全对齐
# ======================
rows = [
    ("单词：", entry_word),
    ("英音标：", entry_uk),
    ("美音标：", entry_us),
    ("词性：", entry_pos),
    ("中文释义：", entry_mean),
    ("等级：", cb_level),
    ("前缀：", cb_prefix),
    ("词根：", cb_root),
    ("后缀：", cb_suffix),
]

for i, (t, e) in enumerate(rows):
    Label(f, text=t, width=10, anchor="e").grid(row=i, column=0, pady=5)
    e.grid(row=i, column=1, pady=5)

# 例句和翻译使用正确行号
Label(f, text="英文例句：").grid(row=9, column=0, sticky="ne", pady=4)
text_en = Text(f, width=28, height=2)
text_en.grid(row=9, column=1, pady=4)

Label(f, text="中文翻译：").grid(row=10, column=0, sticky="ne", pady=4)
text_cn = Text(f, width=28, height=2)
text_cn.grid(row=10, column=1, pady=4)

def do_save_word():
    word = entry_word.get().strip()
    uk = entry_uk.get().strip()
    us = entry_us.get().strip()
    pos = entry_pos.get().strip()
    meaning = entry_mean.get().strip()
    level_name = level_var.get()
    prefix_val = prefix_var.get()
    root_val = root_var.get()
    suffix_val = suffix_var.get()
    ex = text_en.get("1.0", tk.END).strip()
    trans = text_cn.get("1.0", tk.END).strip()

    if not word or not meaning:
        messagebox.showwarning("提示", "单词和释义不能为空")
        return

    level_id = get_level_id(level_name)
    prefix_id = get_id_from_choice(get_prefix_choices(), prefix_val)
    root_id = get_id_from_choice(get_root_choices(), root_val)
    suffix_id = get_id_from_choice(get_suffix_choices(), suffix_val)

    data = (word, uk, us, pos, meaning, level_id, prefix_id, root_id, suffix_id, ex, trans)
    if save_word(data):
        messagebox.showinfo("成功", "单词保存成功")
        study.load_words()
        refresh_words()
        # 清空输入
        entry_word.delete(0, tk.END)
        entry_uk.delete(0, tk.END)
        entry_us.delete(0, tk.END)
        entry_pos.delete(0, tk.END)
        entry_mean.delete(0, tk.END)
        text_en.delete("1.0", tk.END)
        text_cn.delete("1.0", tk.END)
    else:
        messagebox.showerror("失败", "单词已存在")

ttk.Button(add_f, text="保存单词", command=do_save_word, style="Big.TButton").pack(pady=12)

# ==============================================
# 词根录入
# ==============================================
tab_add_root = ttk.Frame(tab)
tab.add(tab_add_root, text="词根录入")

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
tab_root_list = ttk.Frame(tab)
tab.add(tab_root_list, text="词根列表")

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

# 词库管理
tab_f = ttk.Frame(tab)
tab.add(tab_f, text="词库管理")
tree = ttk.Treeview(tab_f, columns=("w", "m", "l"), show="headings", height=15)
tree.heading("w", text="单词")
tree.heading("m", text="释义")
tree.heading("l", text="等级")
tree.column("w", width=160)
tree.column("m", width=420)
tree.column("l", width=140)
tree.pack(padx=20, pady=15, fill="x")

def refresh_words():
    tree.delete(*tree.get_children())
    for row in load_all_words():
        tree.insert("", "end", values=row)

refresh_words()

root.mainloop()