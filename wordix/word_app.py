import tkinter as tk
from tkinter import ttk, Frame, Label, Button, Entry, Text, messagebox
import sqlite3
import random
from datetime import date

# ======================
# 数据库初始化
# ======================
def init_db():
    conn = sqlite3.connect("wordapp.db")
    c = conn.cursor()
    c.executescript('''
 
    CREATE TABLE IF NOT EXISTS levels (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, sort INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS roots (id INTEGER PRIMARY KEY AUTOINCREMENT, root TEXT NOT NULL UNIQUE, meaning TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS affixes (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, affix TEXT NOT NULL, meaning TEXT NOT NULL, UNIQUE(affix, type));
    CREATE TABLE IF NOT EXISTS words (id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT NOT NULL UNIQUE, uk_phonetic TEXT, us_phonetic TEXT, audio_path TEXT, pos TEXT, meaning TEXT NOT NULL, level_id INTEGER, root_id INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (level_id) REFERENCES levels(id), FOREIGN KEY (root_id) REFERENCES roots(id));
    CREATE TABLE IF NOT EXISTS examples (id INTEGER PRIMARY KEY AUTOINCREMENT, word_id INTEGER NOT NULL, en_sentence TEXT NOT NULL, cn_sentence TEXT NOT NULL, FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS user_progress (id INTEGER PRIMARY KEY DEFAULT 1, continuous_days INTEGER DEFAULT 0, last_study_date DATE, total_points INTEGER DEFAULT 0, current_level_id INTEGER DEFAULT 1, CONSTRAINT only_one_row CHECK (id = 1));
    CREATE TABLE IF NOT EXISTS daily_study (study_date DATE PRIMARY KEY, target_count INTEGER DEFAULT 20, done_count INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS word_mastery (word_id INTEGER PRIMARY KEY, is_mastered INTEGER DEFAULT 0, study_count INTEGER DEFAULT 0, wrong_count INTEGER DEFAULT 0, last_review DATE, FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS wrong_book (id INTEGER PRIMARY KEY AUTOINCREMENT, word_id INTEGER NOT NULL, wrong_time DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS medals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, condition TEXT NOT NULL, icon TEXT, is_unlocked INTEGER DEFAULT 0);
    ''')
    # INSERT INTO levels (name, sort) VALUES ('小学3-4年级',10),('小学5-6年级',20),('初中7-9年级',30),('高中必修',40),('高中选择性必修',50),('大学四级',60),('大学六级',70),('托福',80),('雅思',90);
    # INSERT INTO user_progress (id, continuous_days, total_points) VALUES (1,0,0);
   

    # 初始化等级数据（仅表为空时插入）
    c.execute('''INSERT OR IGNORE INTO levels (name, sort) 
                SELECT '小学3-4年级', 10 WHERE NOT EXISTS (SELECT 1 FROM levels)''')
    c.execute('''INSERT OR IGNORE INTO levels (name, sort) 
                SELECT '小学5-6年级', 20 WHERE NOT EXISTS (SELECT 1 FROM levels)''')
    c.execute('''INSERT OR IGNORE INTO levels (name, sort) 
                SELECT '初中7-9年级', 30 WHERE NOT EXISTS (SELECT 1 FROM levels)''')
    c.execute('''INSERT OR IGNORE INTO levels (name, sort) 
                SELECT '高中必修', 40 WHERE NOT EXISTS (SELECT 1 FROM levels)''')
    c.execute('''INSERT OR IGNORE INTO levels (name, sort) 
                SELECT '高中选择性必修', 50 WHERE NOT EXISTS (SELECT 1 FROM levels)''')
    c.execute('''INSERT OR IGNORE INTO levels (name, sort) 
                SELECT '大学四级', 60 WHERE NOT EXISTS (SELECT 1 FROM levels)''')
    c.execute('''INSERT OR IGNORE INTO levels (name, sort) 
                SELECT '大学六级', 70 WHERE NOT EXISTS (SELECT 1 FROM levels)''')
    c.execute('''INSERT OR IGNORE INTO levels (name, sort) 
                SELECT '托福', 80 WHERE NOT EXISTS (SELECT 1 FROM levels)''')
    c.execute('''INSERT OR IGNORE INTO levels (name, sort) 
                SELECT '雅思', 90 WHERE NOT EXISTS (SELECT 1 FROM levels)''')

    # 初始化用户进度（仅表为空时插入）
    c.execute('''INSERT OR IGNORE INTO user_progress (id, continuous_days, total_points) 
                SELECT 1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM user_progress)''')
    conn.commit()
    conn.close()

# ======================
# 工具函数
# ======================
def get_level_list():
    conn = sqlite3.connect("wordapp.db")
    c = conn.cursor()
    c.execute("SELECT name FROM levels ORDER BY sort")
    res = [i[0] for i in c.fetchall()]
    conn.close()
    return res

def get_random_word():
    conn = sqlite3.connect("wordapp.db")
    c = conn.cursor()
    c.execute('SELECT w.id, w.word, w.meaning FROM words w ORDER BY RANDOM() LIMIT 1')
    word = c.fetchone()
    conn.close()
    return word

def get_user_points():
    conn = sqlite3.connect("wordapp.db")
    c = conn.cursor()
    p = c.execute("SELECT total_points FROM user_progress WHERE id=1").fetchone()[0]
    conn.close()
    return p

def add_points(p):
    conn = sqlite3.connect("wordapp.db")
    c = conn.cursor()
    c.execute("UPDATE user_progress SET total_points = total_points + ? WHERE id=1", (p,))
    conn.commit()
    conn.close()

def add_wrong(word_id):
    conn = sqlite3.connect("wordapp.db")
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
        self.load_words()
        self.create_widgets()
        self.show_next()

    def load_words(self):
        conn = sqlite3.connect("wordapp.db")
        c = conn.cursor()
        c.execute('SELECT w.id, w.word, w.uk_phonetic, w.us_phonetic, w.pos, w.meaning, r.root FROM words w LEFT JOIN roots r ON w.root_id=r.id')
        self.word_list = c.fetchall()
        conn.close()

    def create_widgets(self):
        Label(self.frame, text="单词学习", font=("微软雅黑",18,"bold")).pack(pady=20)
        self.card = ttk.Frame(self.frame, padding=25, relief="ridge")
        self.card.pack(padx=50, pady=15, fill="x")
        self.lb_word = Label(self.card, font=("Arial",30,"bold"))
        self.lb_pho = Label(self.card, font=("Arial",14))
        self.lb_pos = Label(self.card, font=("微软雅黑",16))
        self.lb_mean = Label(self.card, font=("微软雅黑",16), wraplength=600)
        self.lb_root = Label(self.card, font=("微软雅黑",13), fg="#165DFF")
        for w in [self.lb_word, self.lb_pho, self.lb_pos, self.lb_mean, self.lb_root]:
            w.pack(pady=2)
        btn_box = Frame(self.frame)
        btn_box.pack(pady=25)
        ttk.Button(btn_box, text="上一词", command=self.show_prev).grid(row=0,column=0,padx=15)
        ttk.Button(btn_box, text="已掌握", command=self.do_master).grid(row=0,column=1,padx=15)
        ttk.Button(btn_box, text="下一词", command=self.show_next).grid(row=0,column=2,padx=15)

    def show(self, word):
        _id, w, uk, us, pos, m, r = word
        self.lb_word.config(text=w)
        pho = f"英 /{uk}/ " if uk else ""
        pho += f"美 /{us}/" if us else ""
        self.lb_pho.config(text=pho.strip())
        self.lb_pos.config(text=pos or "")
        self.lb_mean.config(text=m)
        self.lb_root.config(text=f"词根：{r}" if r else "词根：无")

    def show_next(self):
        if not self.word_list:
            messagebox.showinfo("提示","请先去单词录入添加单词！")
            return
        self.current_idx = (self.current_idx + 1) % len(self.word_list)
        self.show(self.word_list[self.current_idx])

    def show_prev(self):
        if not self.word_list:
            messagebox.showinfo("提示","请先去单词录入添加单词！")
            return
        self.current_idx = (self.current_idx - 1) % len(self.word_list)
        self.show(self.word_list[self.current_idx])

    def do_master(self):
        if self.current_idx < 0 or not self.word_list:
            return
        word_id = self.word_list[self.current_idx][0]
        today = str(date.today())
        conn = sqlite3.connect("wordapp.db")
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO word_mastery (word_id) VALUES (?)', (word_id,))
        c.execute('UPDATE word_mastery SET is_mastered=1, study_count=study_count+1, last_review=? WHERE word_id=?', (today, word_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("成功","已标记为已掌握")
        self.show_next()

# ======================
# 练习页（已修复：读取所有单词，不受等级限制）
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
        Label(self.frame, text="单词练习 · 字母填空", font=("微软雅黑",18,"bold")).pack(pady=15)
        self.points_label = Label(self.frame, text=f"当前积分：{get_user_points()}", font=("微软雅黑",13))
        self.points_label.pack(pady=5)
        self.q_frame = ttk.Frame(self.frame, padding=25, relief="ridge")
        self.q_frame.pack(padx=60, pady=20, fill="x")
        self.meaning_label = Label(self.q_frame, font=("微软雅黑",16), wraplength=600)
        self.meaning_label.pack(pady=8)
        self.mask_label = Label(self.q_frame, font=("Arial",22,"bold"))
        self.mask_label.pack(pady=10)
        self.entry_ans = Entry(self.q_frame, textvariable=self.answer, font=("Arial",16), width=12)
        self.entry_ans.pack(pady=8)
        ttk.Button(self.frame, text="提交答案", command=self.check_answer).pack(pady=8)
        self.result_label = Label(self.frame, font=("微软雅黑",14))
        self.result_label.pack(pady=5)

    def next_question(self):
        self.answer.set("")
        self.result_label.config(text="")
        word = get_random_word()

        if not word:
            self.meaning_label.config(text="⚠️ 请先去【单词录入】添加单词！")
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
            messagebox.showinfo("提示","请先录入单词！")
            return
        user_ans = self.answer.get().strip().lower()
        correct = self.current_word.lower()
        if user_ans == correct:
            self.result_label.config(text="✅ 正确！+5分", fg="green")
            add_points(5)
        else:
            self.result_label.config(text=f"❌ 错误，答案：{self.current_word}", fg="red")
            add_wrong(self.current_id)
        self.frame.after(1000, self.next_question)

# ======================
# 单词录入
# ======================
def add_word(word, uk, us, pos, meaning, level_name, root_text, en_ex, cn_ex):
    try:
        conn = sqlite3.connect("wordapp.db")
        c = conn.cursor()
        c.execute("SELECT id FROM levels WHERE name=?", (level_name,))
        lid = c.fetchone()[0]

        rid = None
        if root_text:
            c.execute("SELECT id FROM roots WHERE root=?", (root_text,))
            r = c.fetchone()
            if r:
                rid = r[0]
            else:
                c.execute("INSERT INTO roots (root, meaning) VALUES (?,?)", (root_text, "自定义"))
                rid = c.lastrowid

        c.execute('INSERT INTO words (word,uk_phonetic,us_phonetic,pos,meaning,level_id,root_id) VALUES (?,?,?,?,?,?,?)', (word,uk,us,pos,meaning,lid,rid))
        wid = c.lastrowid
        if en_ex and cn_ex:
            c.execute("INSERT INTO examples (word_id,en_sentence,cn_sentence) VALUES (?,?,?)", (wid,en_ex,cn_ex))
        c.execute("INSERT OR IGNORE INTO word_mastery (word_id) VALUES (?)", (wid,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(e)
        return False

def save_word():
    w = entry_word.get().strip()
    uk = entry_uk.get().strip()
    us = entry_us.get().strip()
    pos = entry_pos.get().strip()
    m = entry_mean.get().strip()
    lv = level_var.get()
    rt = entry_root.get().strip()
    en = text_en.get("1.0",tk.END).strip()
    cn = text_cn.get("1.0",tk.END).strip()
    if not w or not m:
        messagebox.showwarning("提示","单词/释义不能为空")
        return
    if add_word(w,uk,us,pos,m,lv,rt,en,cn):
        messagebox.showinfo("成功","保存成功")
        study.load_words()
        clear_form()
        refresh_table()
    else:
        messagebox.showerror("错误","保存失败（重复）")

def clear_form():
    for e in [entry_word,entry_uk,entry_us,entry_pos,entry_mean,entry_root]:
        e.delete(0,tk.END)
    text_en.delete("1.0",tk.END)
    text_cn.delete("1.0",tk.END)

def refresh_table():
    tree.delete(*tree.get_children())
    conn = sqlite3.connect("wordapp.db")
    c = conn.cursor()
    c.execute('SELECT w.word,w.meaning,l.name FROM words w JOIN levels l ON w.level_id=l.id')
    for row in c.fetchall():
        tree.insert("", "end", values=row)
    conn.close()

# ======================
# 主界面
# ======================
init_db()
root = tk.Tk()
root.title("词根单词 · 单机本地版")
root.geometry("920x720")
root.resizable(False,False)

tab = ttk.Notebook(root)
tab.pack(expand=1, fill="both", padx=10,pady=10)

# 1 首页
home = ttk.Frame(tab)
tab.add(home, text="首页")
Label(home, text="🔥 词根单词单机版", font=("微软雅黑",20,"bold")).pack(pady=100)

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

entry_word = Entry(f,width=30)
entry_uk = Entry(f,width=30)
entry_us = Entry(f,width=30)
entry_pos = Entry(f,width=30)
entry_mean = Entry(f,width=30)
entry_root = Entry(f,width=30)
level_var = tk.StringVar()
cb = ttk.Combobox(f,textvariable=level_var,values=get_level_list(),state="readonly",width=27)
cb.current(0)

rows = [
 ("单词：",entry_word),("英音标：",entry_uk),("美音标：",entry_us),
 ("词性：",entry_pos),("中文释义：",entry_mean),("等级：",cb),("词根：",entry_root)
]
for i,(t,e) in enumerate(rows):
    Label(f,text=t,width=8,anchor="e").grid(row=i,column=0,pady=4)
    e.grid(row=i,column=1,pady=4)

Label(f,text="例句：").grid(row=7,column=0,sticky="ne",pady=4)
text_en = Text(f,width=28,height=2)
text_en.grid(row=7,column=1,pady=4)
Label(f,text="翻译：").grid(row=8,column=0,sticky="ne",pady=4)
text_cn = Text(f,width=28,height=2)
text_cn.grid(row=8,column=1,pady=4)
ttk.Button(add_f,text="保存单词",command=save_word).pack(pady=10)

# 5 词库管理
tab_f = ttk.Frame(tab)
tab.add(tab_f, text="词库管理")
tree = ttk.Treeview(tab_f,columns=("w","m","l"),show="headings",height=15)
tree.heading("w",text="单词")
tree.heading("m",text="释义")
tree.heading("l",text="等级")
tree.column("w",width=160)
tree.column("m",width=420)
tree.column("l",width=140)
tree.pack(padx=20,pady=15,fill="x")
refresh_table()

root.mainloop()