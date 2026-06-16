import tkinter as tk
from tkinter import ttk, Frame, Label, Button, Entry, Text, messagebox, filedialog
import sqlite3
import pyttsx3
import pandas as pd
import os
import random

# ======================
# 版本 v1.4 新增背诵+拼写测试
# ======================
VERSION = "v1.4 | Wordix单词单机版（背诵+拼写测试+发音+等级+导入导出）"
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
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
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
# 工具函数（优化数据库连接，避免锁表）
# ======================
def get_level_options():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT id, name FROM levels ORDER BY sort")
    data = c.fetchall()
    conn.close()
    return data

def get_level_id_by_name(name):
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT id FROM levels WHERE name=?", (name,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

def save_word_to_db(word_data):
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
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
    offset = (page_num - 1) * page_size
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('''SELECT w.word, w.uk_phonetic, w.us_phonetic, w.meaning, l.name
                 FROM words w
                 LEFT JOIN levels l ON w.level_id = l.id
                 WHERE w.level_id=?
                 LIMIT ? OFFSET ?''', (level_id, page_size, offset))
    data = c.fetchall()
    c.execute('''SELECT COUNT(*) FROM words WHERE level_id=?''', (level_id,))
    total = c.fetchone()[0]
    total_page = (total + page_size - 1) // page_size
    conn.close()
    return data, total, total_page

def search_word_in_db_by_level(level_id, word):
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('''SELECT w.word, w.uk_phonetic, w.us_phonetic, w.meaning, l.name
                 FROM words w
                 LEFT JOIN levels l ON w.level_id = l.id
                 WHERE w.level_id=? AND w.word=?''', (level_id, word))
    res = c.fetchone()
    conn.close()
    return res

# 【v1.4新增】获取当前等级所有单词（背诵/拼写测试用）
def get_all_words_by_level(level_id):
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('''SELECT word, uk_phonetic, us_phonetic, pos, meaning, example, translation
                 FROM words WHERE level_id=?''', (level_id,))
    all_words = c.fetchall()
    conn.close()
    return all_words

# ======================
# 导入导出核心函数
# ======================
def export_current_level_words(level_id, level_name):
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
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
# 主窗口初始化
# ======================
init_database()
root = tk.Tk()
root.title(f"Wordix 词根单词学习 · {VERSION}")
root.geometry("960x760")
root.resizable(False, False)

style = ttk.Style()
style.configure("Big.TButton", font=("微软雅黑",13,"bold"), padding=12)
style.configure("Mid.TButton", font=("微软雅黑",11), padding=6)

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

# 分页全局变量
current_page = 1
page_size = 10

# ==============================================
# 1. 首页 Tab
# ==============================================
tab_home = ttk.Frame(tab_control)
tab_control.add(tab_home, text="首页")
Label(tab_home, text="🔥 Wordix 词根单词学习系统", font=("微软雅黑",22,"bold")).pack(pady=30)
Label(tab_home, text=VERSION, font=("微软雅黑",12)).pack(pady=5)
tips = """功能清单：
1. 单词录入：录入音标、词性、例句，按等级分类存储
2. 词库管理：搜索、分页、Excel导入导出、下载模板
3. 单词背诵：随机翻卡记忆，看单词背释义
4. 拼写测试：释义自测拼写，统计正确率
全部数据本地SQLite存储，无需联网"""
Label(tab_home, text=tips, font=("微软雅黑",11), justify="left").pack(pady=20)

# ==============================================
# 2. 单词录入 Tab
# ==============================================
tab_add_word = ttk.Frame(tab_control)
tab_control.add(tab_add_word, text="单词录入")

Label(tab_add_word, text="单词录入", font=("微软雅黑",16,"bold")).pack(pady=15)
f = Frame(tab_add_word)
f.pack(padx=40)

entry_word = Entry(f, width=30, font=("微软雅黑",11))
entry_uk = Entry(f, width=30, font=("微软雅黑",11))
entry_us = Entry(f, width=30, font=("微软雅黑",11))
entry_pos = Entry(f, width=30, font=("微软雅黑",11))
entry_meaning = Entry(f, width=30, font=("微软雅黑",11))

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
    Label(f, text=t, width=10, anchor="e", font=("微软雅黑",11)).grid(row=i, column=0, pady=6)
    e.grid(row=i, column=1, pady=6)

btn_speak.grid(row=0, column=2, padx=10, pady=6)

Label(f, text="英文例句：", font=("微软雅黑",11)).grid(row=10, column=0, sticky="ne", pady=6)
txt_example = Text(f, width=28, height=3, font=("微软雅黑",10))
txt_example.grid(row=10, column=1, pady=6)

Label(f, text="中文翻译：", font=("微软雅黑",11)).grid(row=11, column=0, sticky="ne", pady=6)
txt_trans = Text(f, width=28, height=3, font=("微软雅黑",10))
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
# 3. 词库管理 Tab（修复Treeview增加音标列）
# ==============================================
tab_table = ttk.Frame(tab_control)
tab_control.add(tab_table, text="词库管理")

Label(tab_table, text="词库管理", font=("微软雅黑",16,"bold")).pack(pady=5)

# 第一行：等级 + 搜索
row1 = Frame(tab_table)
row1.pack(fill="x", padx=20, pady=2)
Label(row1, text="等级：", font=("微软雅黑",12)).pack(side="left", padx=2)
level_comb = ttk.Combobox(row1, textvariable=current_level_name, values=level_names, width=18, state="readonly")
level_comb.pack(side="left", padx=5)

Label(row1, text="搜索：", font=("微软雅黑",12)).pack(side="left", padx=2)
search_entry = Entry(row1, width=18, font=("微软雅黑",12))
search_entry.pack(side="left", padx=5)

Button(row1, text="🔍", font=("微软雅黑", 12, "bold"), width=3,
       command=lambda: search_word()).pack(side="left")

# 第二行：导入导出模板按钮
row2 = Frame(tab_table)
row2.pack(fill="x", padx=20, pady=5)

Button(row2, text="📥 导出", font=("微软雅黑", 11, "bold"),
       command=lambda: export_current_level_words(current_level_id.get(), current_level_name.get())
      ).pack(side="left", padx=5)

Button(row2, text="📤 导入", font=("微软雅黑", 11, "bold"),
       command=lambda: import_words_excel(current_level_id.get())
      ).pack(side="left", padx=5)

lbl_temp = Label(row2, text="下载导入模板", fg="blue", cursor="hand2", font=("微软雅黑",10,"underline"))
lbl_temp.pack(side="left", padx=5)
lbl_temp.bind("<Button-1>", lambda e: download_import_template())

# 等级切换事件
def on_level_change(event):
    idx = level_comb.current()
    current_level_id.set(level_ids[idx])
    global current_page
    current_page = 1
    refresh_words()

level_comb.bind("<<ComboboxSelected>>", on_level_change)

# 搜索逻辑
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

# 单词列表（新增英/美音标列）
tree = ttk.Treeview(tab_table, columns=("w","uk","us","m","l"), show="headings", height=15)
tree.heading("w", text="单词")
tree.heading("uk", text="英音")
tree.heading("us", text="美音")
tree.heading("m", text="释义")
tree.heading("l", text="等级")
tree.column("w", width=120)
tree.column("uk", width=90)
tree.column("us", width=90)
tree.column("m", width=300)
tree.column("l", width=120)
tree.pack(padx=20, pady=10, fill="x")

# 分页控件
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
    _, _, total_page = load_words_by_level_and_page(current_level_id.get(), current_page, page_size)
    if current_page < total_page:
        current_page += 1
        refresh_words()

btn_prev = Button(page_frame, text="上一页", command=prev_page, width=10)
btn_prev.pack(side="left", padx=5)
btn_next = Button(page_frame, text="下一页", command=next_page, width=10)
btn_next.pack(side="left", padx=5)

# 双击单词朗读
def on_tree_click(event):
    item = tree.selection()
    if item:
        word = tree.item(item[0], "values")[0]
        speak_word(word)
tree.bind("<Double-1>", on_tree_click)
tree.bind("<Return>", on_tree_click)

# 刷新列表
def refresh_words():
    data, total, total_page = load_words_by_level_and_page(current_level_id.get(), current_page, page_size)
    tree.delete(*tree.get_children())
    for row in data:
        tree.insert("", "end", values=row)
    page_label.config(text=f"第 {current_page}/{total_page} 页 | 本等级：{total} 个")

refresh_words()
Label(tab_table, text="💡 双击 / 回车 朗读单词｜导入导出支持Excel", font=("微软雅黑",11)).pack()

# ==============================================
# 【v1.4 新增4. 单词背诵 Tab（记忆模式）】
# ==============================================
tab_memorize = ttk.Frame(tab_control)
tab_control.add(tab_memorize, text="单词背诵")

# 背诵全局变量
mem_word_list = []
current_mem_word = None
is_show_detail = tk.BooleanVar(value=False)

# 顶部标题
Label(tab_memorize, text="随机单词背诵卡", font=("微软雅黑",16,"bold")).pack(pady=10)

# 卡片主显示区
card_frame = Frame(tab_memorize, bd=2, relief="solid", width=800, height=380)
card_frame.pack(padx=30, pady=10, fill="x")
card_frame.pack_propagate(False)

# 单词大字
lbl_mem_word = Label(card_frame, text="请点击「下一个单词」", font=("微软雅黑",30,"bold"), wraplength=750)
lbl_mem_word.pack(pady=40)

# 详情区域（音标/释义/例句，默认隐藏）
detail_frame = Frame(card_frame)
lbl_uk = Label(detail_frame, text="英音：", font=("微软雅黑",12))
lbl_us = Label(detail_frame, text="美音：", font=("微软雅黑",12))
lbl_pos = Label(detail_frame, text="词性：", font=("微软雅黑",12))
lbl_mean = Label(detail_frame, text="释义：", font=("微软雅黑",12))
lbl_ex = Label(detail_frame, text="例句：", font=("微软雅黑",11), wraplength=720)
lbl_trans = Label(detail_frame, text="例句翻译：", font=("微软雅黑",11), wraplength=720)

def refresh_memorize_card():
    global mem_word_list, current_mem_word
    # 加载当前等级全部单词
    mem_word_list = get_all_words_by_level(current_level_id.get())
    if not mem_word_list:
        lbl_mem_word.config(text="当前等级无单词，请先录入！")
        detail_frame.pack_forget()
        return
    # 随机取词
    current_mem_word = random.choice(mem_word_list)
    word, uk, us, pos, mean, ex, trans = current_mem_word
    # 重置为只显示单词
    is_show_detail.set(False)
    lbl_mem_word.config(text=word)
    detail_frame.pack_forget()

def flip_card():
    if not current_mem_word:
        return
    word, uk, us, pos, mean, ex, trans = current_mem_word
    if is_show_detail.get():
        # 隐藏详情
        is_show_detail.set(False)
        lbl_mem_word.config(text=word)
        detail_frame.pack_forget()
    else:
        # 展示全部详情
        is_show_detail.set(True)
        lbl_mem_word.config(text=word)
        lbl_uk.config(text=f"英音：{uk}")
        lbl_us.config(text=f"美音：{us}")
        lbl_pos.config(text=f"词性：{pos}")
        lbl_mean.config(text=f"释义：{mean}")
        lbl_ex.config(text=f"例句：{ex}")
        lbl_trans.config(text=f"翻译：{trans}")
        detail_frame.pack(pady=10)
        lbl_uk.pack()
        lbl_us.pack()
        lbl_pos.pack()
        lbl_mean.pack()
        lbl_ex.pack(pady=3)
        lbl_trans.pack(pady=3)

def speak_mem_word():
    if current_mem_word:
        speak_word(current_mem_word[0])

# 按钮区
mem_btn_frame = Frame(tab_memorize)
mem_btn_frame.pack(pady=10)
ttk.Button(mem_btn_frame, text="🔊 朗读单词", style="Mid.TButton", command=speak_mem_word).grid(row=0,column=0,padx=8)
ttk.Button(mem_btn_frame, text="翻面查看释义", style="Mid.TButton", command=flip_card).grid(row=0,column=1,padx=8)
ttk.Button(mem_btn_frame, text="下一个单词", style="Mid.TButton", command=refresh_memorize_card).grid(row=0,column=2,padx=8)

Label(tab_memorize, text="操作提示：切换上方等级可更换背诵词库", font=("微软雅黑",10)).pack(pady=5)

# 初始化背诵卡片
refresh_memorize_card()

# ==============================================
# 【v1.4 新增5. 拼写测试 Tab（听写自测）】
# ==============================================
tab_spell = ttk.Frame(tab_control)
tab_control.add(tab_spell, text="拼写测试")

# 拼写测试全局变量
spell_word_pool = []
current_spell_word = None
correct_count = 0
wrong_count = 0

Label(tab_spell, text="释义拼写自测", font=("微软雅黑",16,"bold")).pack(pady=10)

# 题目展示
spell_card = Frame(tab_spell, bd=2, relief="solid", width=850, height=220)
spell_card.pack(padx=20, pady=10, fill="x")
spell_card.pack_propagate(False)
lbl_spell_mean = Label(spell_card, text="点击「开始测试」加载单词", font=("微软雅黑",16), wraplength=800)
lbl_spell_mean.pack(pady=60)

# 输入框区域
spell_input_frame = Frame(tab_spell)
spell_input_frame.pack(pady=10)
Label(spell_input_frame, text="请输入单词：", font=("微软雅黑",12)).grid(row=0,column=0)
entry_spell = Entry(spell_input_frame, width=35, font=("微软雅黑",14))
entry_spell.grid(row=0,column=1,padx=10)

# 结果提示
lbl_spell_result = Label(tab_spell, text="", font=("微软雅黑",13,"bold"))
lbl_spell_result.pack(pady=5)

# 统计文本
lbl_spell_stat = Label(tab_spell, text=f"正确：{correct_count} | 错误：{wrong_count}", font=("微软雅黑",11))
lbl_spell_stat.pack(pady=3)

# 逻辑函数
def load_spell_words():
    global spell_word_pool, current_spell_word
    spell_word_pool = get_all_words_by_level(current_level_id.get())
    if not spell_word_pool:
        lbl_spell_mean.config(text="当前等级无单词，请先录入！")
        return False
    pick_next_spell()
    return True

def pick_next_spell():
    global current_spell_word
    current_spell_word = random.choice(spell_word_pool)
    _, _, _, _, mean, _, _ = current_spell_word
    lbl_spell_mean.config(text=f"释义：{mean}")
    entry_spell.delete(0, tk.END)
    lbl_spell_result.config(text="")

def check_spell_answer():
    global correct_count, wrong_count
    if not current_spell_word:
        messagebox.showinfo("提示", "请先点击开始测试")
        return
    user_input = entry_spell.get().strip().lower()
    real_word = current_spell_word[0].lower()
    if user_input == real_word:
        correct_count += 1
        lbl_spell_result.config(text="✅ 拼写正确！", fg="green")
    else:
        wrong_count += 1
        lbl_spell_result.config(text=f"❌ 错误，正确单词：{current_spell_word[0]}", fg="red")
    # 更新统计
    lbl_spell_stat.config(text=f"正确：{correct_count} | 错误：{wrong_count}")
    # 自动切换下一题
    root.after(1200, pick_next_spell)

def reset_spell_stat():
    global correct_count, wrong_count
    correct_count = 0
    wrong_count = 0
    lbl_spell_stat.config(text=f"正确：{correct_count} | 错误：{wrong_count}")
    lbl_spell_result.config(text="")

# 按钮区
spell_btn_frame = Frame(tab_spell)
spell_btn_frame.pack(pady=10)
ttk.Button(spell_btn_frame, text="开始测试", style="Mid.TButton", command=load_spell_words).grid(row=0,column=0,padx=6)
ttk.Button(spell_btn_frame, text="提交答案", style="Mid.TButton", command=check_spell_answer).grid(row=0,column=1,padx=6)
ttk.Button(spell_btn_frame, text="重置统计", style="Mid.TButton", command=reset_spell_stat).grid(row=0,column=2,padx=6)
ttk.Button(spell_btn_frame, text="朗读标准答案", style="Mid.TButton", command=lambda: speak_word(current_spell_word[0] if current_spell_word else "")).grid(row=0,column=3,padx=6)

# 回车提交答案
entry_spell.bind("<Return>", lambda e: check_spell_answer())

Label(tab_spell, text="提示：切换上方等级后重新点击「开始测试」更换题库", font=("微软雅黑",10)).pack(pady=5)

# ======================
# 主循环启动
# ======================
root.mainloop()