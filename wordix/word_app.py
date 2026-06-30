import tkinter as tk
from tkinter import ttk, Frame, Label, Button, Entry, Text, messagebox, filedialog
import sqlite3
import pyttsx3
import pandas as pd
import os
import random
import time
from datetime import datetime, timedelta

# ======================
# 版本 v3.0 新增艾宾浩斯遗忘曲线间隔重复记忆
# ======================
VERSION = "v3.0 | Wordix单词单机版（一词多义+有序背诵+拼写测试+单词本+单次计分+发音+等级+导入导出+艾宾浩斯间隔记忆）"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(SCRIPT_DIR, "wordix.xdb")

# ======================
# 艾宾浩斯全局配置（单位：分钟）
# ======================
EBBINGHAUS_INTERVALS = [
    5,        # level 0 初次学习后5分钟
    30,       # level 1 30分钟
    12 * 60,  # level 2 12小时
    24 * 60,  # level 3 1天
    2 * 24 * 60,  # level 4 2天
    4 * 24 * 60,  # level 5 4天
    7 * 24 * 60,  # level 6 7天
    15 * 24 * 60, # level 7 15天
    30 * 24 * 60, # level 8 30天
    999999999     # level 9 永久熟记，不再复习
]
MAX_MEM_LEVEL = len(EBBINGHAUS_INTERVALS) - 1

# ======================
# 初始化发音引擎
# ======================
engine = pyttsx3.init()

def speak_word(text):
    if text.strip():
        engine.say(text.strip())
        engine.runAndWait()

# ======================
# 数据库初始化（新增艾宾浩斯计划表）
# ======================
def init_database():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()

    # 等级表
    c.execute('''CREATE TABLE IF NOT EXISTS levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    sort INTEGER DEFAULT 0
                )''')

    # 单词主表（移除UNIQUE约束，支持一词多义）
    c.execute('''CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    uk_phonetic TEXT,
                    us_phonetic TEXT,
                    level_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (level_id) REFERENCES levels(id)
                )''')

    # 词性和释义表（一对多关系）
    c.execute('''CREATE TABLE IF NOT EXISTS word_senses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    pos TEXT NOT NULL,
                    meaning TEXT NOT NULL,
                    example TEXT,
                    translation TEXT,
                    frequency INTEGER DEFAULT 0,
                    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
                )''')

    # 单词本表
    c.execute('''CREATE TABLE IF NOT EXISTS word_book (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    note TEXT,
                    mastered INTEGER DEFAULT 0,
                    UNIQUE(word)
                )''')

    # 新增：艾宾浩斯记忆复习计划表
    c.execute('''CREATE TABLE IF NOT EXISTS memory_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL UNIQUE,
                    mem_level INTEGER DEFAULT 0,
                    last_review_ts INTEGER DEFAULT 0,
                    next_review_ts INTEGER DEFAULT 0,
                    create_ts INTEGER DEFAULT 0
                )''')

    # 创建索引提升查询性能
    c.execute('''CREATE INDEX IF NOT EXISTS idx_words_word ON words(word)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_word_senses_word_id ON word_senses(word_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_memory_word ON memory_schedule(word)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_memory_next_ts ON memory_schedule(next_review_ts)''')

    # 初始化等级数据
    level_data = [
        ('小学3-4年级', 10), ('小学5-6年级', 20), ('初中7-9年级', 30),
        ('高中必修', 40), ('高中选择性必修', 50), ('大学四级', 60),
        ('大学六级', 70), ('托福', 80), ('雅思', 90)
    ]
    for name, sort in level_data:
        c.execute('''INSERT OR IGNORE INTO levels (name, sort)
                      VALUES (?, ?)''', (name, sort))

    conn.commit()
    conn.close()

# ======================
# 艾宾浩斯记忆核心工具函数
# ======================
def get_now_ts():
    """获取当前时间戳（秒）"""
    return int(time.time())

def calc_next_review_ts(base_ts, minute_gap):
    """计算下次复习时间戳"""
    return base_ts + minute_gap * 60

def add_word_to_memory_plan(word):
    """将单词加入艾宾浩斯记忆计划，初次5分钟后复习"""
    now = get_now_ts()
    first_gap = EBBINGHAUS_INTERVALS[0]
    next_ts = calc_next_review_ts(now, first_gap)
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO memory_schedule
                 (word, mem_level, last_review_ts, next_review_ts, create_ts)
                 VALUES (?, 0, ?, ?, ?)''', (word, now, next_ts, now))
    conn.commit()
    conn.close()

def review_memory_word(word, is_remembered: bool):
    """
    复习单词后更新记忆计划
    :param word: 单词
    :param is_remembered: True记住，False遗忘
    """
    now = get_now_ts()
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT mem_level FROM memory_schedule WHERE word = ?', (word,))
    res = c.fetchone()
    if not res:
        conn.close()
        return False
    cur_level = res[0]

    if is_remembered:
        # 记住：升一级
        new_level = cur_level + 1
        if new_level >= MAX_MEM_LEVEL:
            new_gap = EBBINGHAUS_INTERVALS[MAX_MEM_LEVEL]
        else:
            new_gap = EBBINGHAUS_INTERVALS[new_level]
    else:
        # 遗忘：重置回0档，重新5分钟复习
        new_level = 0
        new_gap = EBBINGHAUS_INTERVALS[0]

    new_next_ts = calc_next_review_ts(now, new_gap)
    c.execute('''UPDATE memory_schedule
                 SET mem_level = ?, last_review_ts = ?, next_review_ts = ?
                 WHERE word = ?''', (new_level, now, new_next_ts, word))
    conn.commit()
    conn.close()
    return True

def get_due_memory_words():
    """获取当前已到复习时间的单词（待复习）"""
    now = get_now_ts()
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('''SELECT ms.word, ms.mem_level, ms.next_review_ts,
                        w.uk_phonetic, w.us_phonetic,
                        GROUP_CONCAT(ws.pos || ' ' || ws.meaning, '; ') as meanings
                 FROM memory_schedule ms
                 LEFT JOIN words w ON ms.word = w.word
                 LEFT JOIN word_senses ws ON w.id = ws.word_id
                 WHERE ms.next_review_ts <= ? AND ms.mem_level < ?
                 GROUP BY ms.word
                 ORDER BY ms.next_review_ts ASC''', (now, MAX_MEM_LEVEL))
    data = c.fetchall()
    conn.close()
    return data

def get_word_memory_status(word):
    """查询单词记忆等级与下次复习时间"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('''SELECT mem_level, last_review_ts, next_review_ts
                 FROM memory_schedule WHERE word = ?''', (word,))
    res = c.fetchone()
    conn.close()
    if not res:
        return None
    mem_lv, last_ts, next_ts = res
    last_dt = datetime.fromtimestamp(last_ts).strftime("%Y-%m-%d %H:%M")
    next_dt = datetime.fromtimestamp(next_ts).strftime("%Y-%m-%d %H:%M")
    return {
        "level": mem_lv,
        "level_name": f"档位{mem_lv}({EBBINGHAUS_INTERVALS[mem_lv]}分钟间隔)",
        "last_review": last_dt,
        "next_review": next_dt
    }

# ======================
# 原有数据库工具函数（无修改）
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

def save_word_to_db_with_senses(word, uk_phonetic, us_phonetic, level_id, senses_list):
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id FROM words WHERE word=?", (word,))
        existing = c.fetchone()
        if existing:
            word_id = existing[0]
            c.execute("DELETE FROM word_senses WHERE word_id=?", (word_id,))
        else:
            c.execute('''INSERT INTO words (word, uk_phonetic, us_phonetic, level_id)
                         VALUES (?,?,?,?)''',
                      (word, uk_phonetic, us_phonetic, level_id))
            word_id = c.lastrowid
        for i, (pos, meaning, example, translation) in enumerate(senses_list):
            frequency = 100 - i * 10
            c.execute('''INSERT INTO word_senses 
                         (word_id, pos, meaning, example, translation, frequency)
                         VALUES (?,?,?,?,?,?)''',
                      (word_id, pos.strip(), meaning.strip(),
                       example.strip(), translation.strip(), frequency))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False
    finally:
        conn.close()

def save_word_to_db(word_data):
    word, uk_phonetic, us_phonetic, pos, meaning, level_id, example, translation = word_data
    senses_list = [(pos, meaning, example, translation)]
    return save_word_to_db_with_senses(word, uk_phonetic, us_phonetic, level_id, senses_list)

def load_words_by_level_and_page(level_id, page_num, page_size=10):
    offset = (page_num - 1) * page_size
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('''SELECT w.word, w.uk_phonetic, w.us_phonetic, 
                        GROUP_CONCAT(ws.pos || ' ' || ws.meaning, '; ') as meanings,
                        l.name
                 FROM words w
                 LEFT JOIN word_senses ws ON w.id = ws.word_id
                 LEFT JOIN levels l ON w.level_id = l.id
                 WHERE w.level_id=?
                 GROUP BY w.id
                 LIMIT ? OFFSET ?''', (level_id, page_size, offset))
    data = c.fetchall()
    c.execute('''SELECT COUNT(DISTINCT w.id) FROM words w WHERE w.level_id=?''', (level_id,))
    total = c.fetchone()[0]
    total_page = (total + page_size - 1) // page_size
    conn.close()
    return data, total, total_page

def search_word_in_db_by_level(level_id, word):
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('''SELECT w.word, w.uk_phonetic, w.us_phonetic, 
                        GROUP_CONCAT(ws.pos || ' ' || ws.meaning, '; ') as meanings,
                        l.name
                 FROM words w
                 LEFT JOIN word_senses ws ON w.id = ws.word_id
                 LEFT JOIN levels l ON w.level_id = l.id
                 WHERE w.level_id=? AND w.word=?
                 GROUP BY w.id''', (level_id, word))
    res = c.fetchone()
    conn.close()
    return res

def get_all_words_by_level(level_id):
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('''SELECT DISTINCT w.word, w.uk_phonetic, w.us_phonetic
                 FROM words w
                 WHERE w.level_id=?''', (level_id,))
    words = []
    for row in c.fetchall():
        word, uk, us = row
        c.execute('''SELECT pos, meaning, example, translation 
                     FROM word_senses 
                     WHERE word_id=(SELECT id FROM words WHERE word=? AND level_id=?)
                     ORDER BY frequency DESC, id ASC''', (word, level_id))
        senses = c.fetchall()
        full_meaning = "; ".join([f"{pos} {mean}" for pos, mean, _, _ in senses])
        first_example = senses[0][2] if senses and senses[0][2] else ""
        first_translation = senses[0][3] if senses and senses[0][3] else ""
        words.append((word, uk, us, "", full_meaning, first_example, first_translation))
    conn.close()
    return words

def get_word_full_details(word):
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT id, word, uk_phonetic, us_phonetic, level_id FROM words WHERE word=?", (word,))
    word_info = c.fetchone()
    if not word_info:
        return None
    c.execute('''SELECT pos, meaning, example, translation 
                 FROM word_senses 
                 WHERE word_id=? 
                 ORDER BY frequency DESC, id ASC''', (word_info[0],))
    senses = c.fetchall()
    conn.close()
    return {
        'word': word_info[1],
        'uk_phonetic': word_info[2],
        'us_phonetic': word_info[3],
        'level_id': word_info[4],
        'senses': senses
    }

def add_word_to_word_book(word, note=""):
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        c = conn.cursor()
        c.execute('''INSERT INTO word_book (word, note, added_time)
                     VALUES (?, ?, CURRENT_TIMESTAMP)
                     ON CONFLICT(word) DO UPDATE SET
                     added_time = CURRENT_TIMESTAMP''', (word, note))
        conn.commit()
        return True
    except Exception as e:
        print(f"添加到单词本失败: {e}")
        return False
    finally:
        conn.close()

def get_word_book_words():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('''SELECT b.word, w.uk_phonetic, w.us_phonetic, 
                        GROUP_CONCAT(ws.pos || ' ' || ws.meaning, '; ') as meanings,
                        b.added_time, b.note, b.mastered
                 FROM word_book b
                 LEFT JOIN words w ON b.word = w.word
                 LEFT JOIN word_senses ws ON w.id = ws.word_id
                 WHERE b.mastered = 0
                 GROUP BY b.word
                 ORDER BY b.added_time DESC''')
    words = c.fetchall()
    conn.close()
    return words

def remove_from_word_book(word):
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        c = conn.cursor()
        c.execute('DELETE FROM word_book WHERE word = ?', (word,))
        conn.commit()
        return True
    except Exception as e:
        print(f"从单词本删除失败: {e}")
        return False
    finally:
        conn.close()

def mark_word_as_mastered(word):
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        c = conn.cursor()
        c.execute('UPDATE word_book SET mastered = 1 WHERE word = ?', (word,))
        conn.commit()
        return True
    except Exception as e:
        print(f"标记已掌握失败: {e}")
        return False
    finally:
        conn.close()

# ======================
# 导入导出核心函数（无修改）
# ======================
def export_current_level_words(level_id, level_name):
    try:
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        df = pd.read_sql(f"""
            SELECT w.word, w.uk_phonetic, w.us_phonetic, 
                   ws.pos, ws.meaning, ws.example, ws.translation
            FROM words w
            LEFT JOIN word_senses ws ON w.id = ws.word_id
            WHERE w.level_id = {level_id}
            ORDER BY w.word, ws.frequency DESC
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
        messagebox.showinfo("成功", f"已导出 {len(df)} 条记录！")
    except Exception as e:
        messagebox.showerror("错误", f"导出失败：{str(e)}")
    finally:
        conn.close()

def download_import_template():
    template = {
        "word": ["order", "order", "order"],
        "uk_phonetic": ["ˈɔːdə(r)", "ˈɔːdə(r)", "ˈɔːdə(r)"],
        "us_phonetic": ["ˈɔːrdər", "ˈɔːrdər", "ˈɔːrdər"],
        "pos": ["n.", "v.", "n."],
        "meaning": ["订单", "订购", "顺序"],
        "example": ["I placed an order.", "I want to order a book.", "List them in order."],
        "translation": ["我下了一个订单。", "我想订购一本书。", "按顺序列出它们。"]
    }
    df = pd.DataFrame(template)
    path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel 模板", "*.xlsx")],
        initialfile="单词导入模板.xlsx"
    )
    if path:
        df.to_excel(path, index=False)
        messagebox.showinfo("成功", "导入模板已下载完成！（支持一词多义，同一单词多行表示不同释义）")

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
        grouped = df.groupby('word')
        success = 0
        fail = 0
        for word, group in grouped:
            try:
                first_row = group.iloc[0]
                uk = str(first_row.get("uk_phonetic", "")).strip()
                us = str(first_row.get("us_phonetic", "")).strip()
                senses_list = []
                for _, row in group.iterrows():
                    pos = str(row.get("pos", "")).strip()
                    meaning = str(row["meaning"]).strip()
                    example = str(row.get("example", "")).strip()
                    translation = str(row.get("translation", "")).strip()
                    if meaning:
                        senses_list.append((pos, meaning, example, translation))
                if senses_list:
                    if save_word_to_db_with_senses(word, uk, us, level_id, senses_list):
                        success += len(senses_list)
                    else:
                        fail += 1
                else:
                    fail += 1
            except Exception as e:
                print(f"导入单词 {word} 失败: {e}")
                fail += 1
        messagebox.showinfo("导入完成", f"成功：{success} 条释义\n失败/重复：{fail} 个单词")
        refresh_words()
    except Exception as e:
        messagebox.showerror("错误", f"导入失败：{str(e)}")

# ======================
# 主窗口初始化
# ======================
init_database()
root = tk.Tk()
root.title(f"Wordix 词根单词学习 · {VERSION}")
root.geometry("1080x860")
root.resizable(False, False)

style = ttk.Style()
style.configure("Big.TButton", font=("微软雅黑", 13, "bold"), padding=12)
style.configure("Mid.TButton", font=("微软雅黑", 11), padding=6)

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

current_page = 1
page_size = 10

# ==============================================
# 1. 首页 Tab
# ==============================================
tab_home = ttk.Frame(tab_control)
tab_control.add(tab_home, text="首页")
Label(tab_home, text="🔥 Wordix 词根单词学习系统", font=("微软雅黑", 22, "bold")).pack(pady=30)
Label(tab_home, text=VERSION, font=("微软雅黑", 12)).pack(pady=5)
tips = """功能清单：
1. 单词录入：支持一词多义、一词多词性，表格形式录入
2. 词库管理：搜索、分页、Excel导入导出（支持多义词）
3. 单词背诵：有序翻卡遍历全部单词，显示完整释义列表
4. 拼写测试：有序遍历单词自测拼写，每个单词仅计分一次
5. 📖 单词本：自动收集错题+手动添加重点单词，专门复习
6. 🧠 艾宾浩斯记忆：间隔重复科学复习，自动推送到期单词
全部数据本地SQLite存储，无需联网

✨ v3.0 新增：艾宾浩斯遗忘曲线间隔重复记忆计划
遗忘复习节点：5分钟→30分钟→12小时→1天→2天→4天→7天→15天→30天"""
Label(tab_home, text=tips, font=("微软雅黑", 11), justify="left").pack(pady=20)

# ==============================================
# 2. 单词录入 Tab（新增加入记忆计划按钮）
# ==============================================
tab_add_word = ttk.Frame(tab_control)
tab_control.add(tab_add_word, text="单词录入")

Label(tab_add_word, text="单词录入（支持一词多义）", font=("微软雅黑", 16, "bold")).pack(pady=15)
f = Frame(tab_add_word)
f.pack(padx=40)

entry_word = Entry(f, width=30, font=("微软雅黑", 11))
entry_uk = Entry(f, width=30, font=("微软雅黑", 11))
entry_us = Entry(f, width=30, font=("微软雅黑", 11))

cb_level = ttk.Combobox(f, textvariable=current_level_name, values=level_names, width=27, state="readonly")
cb_level.current(0)

btn_speak = Button(f, text="🔊 朗读单词", font=("微软雅黑", 10, "bold"),
                   command=lambda: speak_word(entry_word.get()))

rows_basic = [
    ("单词：", entry_word),
    ("英音标：", entry_uk),
    ("美音标：", entry_us),
    ("等级：", cb_level),
]

for i, (t, e) in enumerate(rows_basic):
    Label(f, text=t, width=10, anchor="e", font=("微软雅黑", 11)).grid(row=i, column=0, pady=6)
    e.grid(row=i, column=1, pady=6)

btn_speak.grid(row=0, column=2, padx=10, pady=6)

# 词性和释义表格区域
Label(f, text="词性、释义、例句（表格形式）：", font=("微软雅黑", 11, "bold")).grid(row=10, column=0, columnspan=3,
                                                                               sticky="w", pady=(15, 5))
senses_frame = Frame(f)
senses_frame.grid(row=11, column=0, columnspan=3, sticky="ew", pady=5)
senses_tree = ttk.Treeview(senses_frame, columns=("selected", "pos", "meaning", "example", "translation"),
                           show="headings", height=6)
senses_tree.heading("selected", text="✓")
senses_tree.heading("pos", text="词性")
senses_tree.heading("meaning", text="释义")
senses_tree.heading("example", text="英文例句")
senses_tree.heading("translation", text="中文翻译")
senses_tree.column("selected", width=40, anchor="center")
senses_tree.column("pos", width=60)
senses_tree.column("meaning", width=120)
senses_tree.column("example", width=200)
senses_tree.column("translation", width=200)
senses_tree.pack(side="left", fill="x", expand=True)
scrollbar = ttk.Scrollbar(senses_frame, orient="vertical", command=senses_tree.yview)
scrollbar.pack(side="right", fill="y")
senses_tree.configure(yscrollcommand=scrollbar.set)
senses_tree.tag_configure("oddrow", background="#f0f8ff")
senses_tree.tag_configure("evenrow", background="#ffffff")
senses_tree.tag_configure("newrow", background="#fffacd")
btn_frame = Frame(f)
btn_frame.grid(row=12, column=0, columnspan=3, sticky="w", pady=5)

def add_sense_row():
    item_id = senses_tree.insert("", "end", values=("☐", "", "", "", ""))
    senses_tree.item(item_id, tags=("newrow",))
    def normalize_color():
        all_items = senses_tree.get_children()
        for i, item in enumerate(all_items):
            tag = "oddrow" if i % 2 == 0 else "evenrow"
            senses_tree.item(item, tags=(tag,))
    senses_tree.after(2000, normalize_color)

def delete_selected_rows():
    selected_items = []
    for item in senses_tree.get_children():
        values = senses_tree.item(item)["values"]
        if values and values[0] == "☑":
            selected_items.append(item)
    if not selected_items:
        messagebox.showwarning("提示", "请先勾选要删除的行（点击第一列的☐变为☑）")
        return
    if messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selected_items)} 行吗？"):
        for item in selected_items:
            senses_tree.delete(item)
        refresh_row_colors()

def clear_all_rows():
    if senses_tree.get_children() and messagebox.askyesno("确认", "确定要清空所有释义吗？"):
        senses_tree.delete(*senses_tree.get_children())

def refresh_row_colors():
    all_items = senses_tree.get_children()
    for i, item in enumerate(all_items):
        tag = "oddrow" if i % 2 == 0 else "evenrow"
        senses_tree.item(item, tags=(tag,))

Button(btn_frame, text="➕ 添加一行", command=add_sense_row, font=("微软雅黑", 9), bg="#e8f5e9").pack(side="left", padx=5)
Button(btn_frame, text="🗑️ 删除选中", command=delete_selected_rows, font=("微软雅黑", 9), bg="#ffebee").pack(side="left", padx=5)
Button(btn_frame, text="🧹 清空全部", command=clear_all_rows, font=("微软雅黑", 9), bg="#fff3e0").pack(side="left", padx=5)

def toggle_selection(event):
    region = senses_tree.identify("region", event.x, event.y)
    if region != "cell":
        return
    column = senses_tree.identify_column(event.x)
    if column != "#1":
        return
    item = senses_tree.identify_row(event.y)
    if not item:
        return
    values = list(senses_tree.item(item)["values"])
    values[0] = "☑" if values[0] == "☐" else "☐"
    senses_tree.item(item, values=tuple(values))

senses_tree.bind("<Button-1>", toggle_selection)

def on_double_click(event):
    region = senses_tree.identify("region", event.x, event.y)
    if region != "cell":
        return
    column = senses_tree.identify_column(event.x)
    if column == "#1":
        return
    item = senses_tree.selection()[0] if senses_tree.selection() else senses_tree.identify_row(event.y)
    if not item:
        return
    col_idx = int(column.replace("#", "")) - 1
    bbox = senses_tree.bbox(item, column)
    if not bbox:
        return
    x, y, width, height = bbox
    current_values = list(senses_tree.item(item)["values"])
    old_value = str(current_values[col_idx])
    edit_entry = Entry(senses_tree, font=("微软雅黑", 10))
    edit_entry.place(x=x, y=y, width=width, height=height)
    edit_entry.focus()
    edit_entry.insert(0, old_value)
    edit_entry.select_range(0, tk.END)
    def save_edit(event=None):
        new_value = edit_entry.get().strip()
        updated_values = list(current_values)
        updated_values[col_idx] = new_value
        senses_tree.item(item, values=tuple(updated_values))
        edit_entry.destroy()
    def cancel_edit(event=None):
        edit_entry.destroy()
    edit_entry.bind("<Return>", save_edit)
    edit_entry.bind("<Escape>", cancel_edit)
    edit_entry.bind("<FocusOut>", lambda e: save_edit())

senses_tree.bind("<Double-1>", on_double_click)

def save_word():
    word = entry_word.get().strip()
    if not word:
        messagebox.showwarning("提示", "单词不能为空")
        return
    all_items = senses_tree.get_children()
    if not all_items:
        messagebox.showwarning("提示", "至少添加一行词性和释义")
        return
    senses_list = []
    for item in all_items:
        values = senses_tree.item(item)["values"]
        pos = str(values[1]).strip() if len(values) > 1 else ""
        meaning = str(values[2]).strip() if len(values) > 2 else ""
        example = str(values[3]).strip() if len(values) > 3 else ""
        translation = str(values[4]).strip() if len(values) > 4 else ""
        if meaning:
            senses_list.append((pos, meaning, example, translation))
    if not senses_list:
        messagebox.showwarning("提示", "至少填写一个释义")
        return
    level_id = current_level_id.get()
    uk = entry_uk.get().strip()
    us = entry_us.get().strip()
    if save_word_to_db_with_senses(word, uk, us, level_id, senses_list):
        messagebox.showinfo("成功", f"单词「{word}」已保存，共 {len(senses_list)} 个释义")
        entry_word.delete(0, tk.END)
        entry_uk.delete(0, tk.END)
        entry_us.delete(0, tk.END)
        senses_tree.delete(*senses_tree.get_children())
        refresh_words()
    else:
        messagebox.showerror("失败", "保存失败，请重试")

# 新增：保存并加入艾宾浩斯记忆计划
def save_and_add_memory():
    word = entry_word.get().strip()
    if not word:
        messagebox.showwarning("提示", "单词不能为空")
        return
    all_items = senses_tree.get_children()
    if not all_items:
        messagebox.showwarning("提示", "至少添加一行词性和释义")
        return
    senses_list = []
    for item in all_items:
        values = senses_tree.item(item)["values"]
        pos = str(values[1]).strip() if len(values) > 1 else ""
        meaning = str(values[2]).strip() if len(values) > 2 else ""
        example = str(values[3]).strip() if len(values) > 3 else ""
        translation = str(values[4]).strip() if len(values) > 4 else ""
        if meaning:
            senses_list.append((pos, meaning, example, translation))
    if not senses_list:
        messagebox.showwarning("提示", "至少填写一个释义")
        return
    level_id = current_level_id.get()
    uk = entry_uk.get().strip()
    us = entry_us.get().strip()
    if save_word_to_db_with_senses(word, uk, us, level_id, senses_list):
        add_word_to_memory_plan(word)
        messagebox.showinfo("完成", f"「{word}」已保存并加入艾宾浩斯记忆计划！5分钟后首次复习")
        entry_word.delete(0, tk.END)
        entry_uk.delete(0, tk.END)
        entry_us.delete(0, tk.END)
        senses_tree.delete(*senses_tree.get_children())
        refresh_words()
    else:
        messagebox.showerror("失败", "保存失败")

btn_save_frame = Frame(tab_add_word)
btn_save_frame.pack(pady=15)
ttk.Button(btn_save_frame, text="仅保存单词", style="Mid.TButton", command=save_word).grid(row=0, column=0, padx=10)
ttk.Button(btn_save_frame, text="保存+加入记忆计划", style="Big.TButton", command=save_and_add_memory).grid(row=0, column=1, padx=10)

example_text = """💡 使用说明：
1. 点击「➕ 添加一行」添加新的词性和释义
2. 点击第一列的 ☐ 变成 ☑ 来选中行
3. 双击单元格可直接编辑内容（除复选框列）
4. 选中行后点击「🗑️ 删除选中」批量删除
5. 点击【保存+加入记忆计划】自动加入艾宾浩斯间隔复习"""
Label(tab_add_word, text=example_text, font=("微软雅黑", 9), fg="gray", justify="left").pack(pady=10)

# ==============================================
# 3. 词库管理 Tab（新增加入记忆计划按钮）
# ==============================================
tab_table = ttk.Frame(tab_control)
tab_control.add(tab_table, text="词库管理")

Label(tab_table, text="词库管理", font=("微软雅黑", 16, "bold")).pack(pady=5)
row1 = Frame(tab_table)
row1.pack(fill="x", padx=20, pady=2)
Label(row1, text="等级：", font=("微软雅黑", 12)).pack(side="left", padx=2)
level_comb = ttk.Combobox(row1, textvariable=current_level_name, values=level_names, width=18, state="readonly")
level_comb.current(0)
level_comb.pack(side="left", padx=5)
Label(row1, text="搜索：", font=("微软雅黑", 12)).pack(side="left", padx=2)
search_entry = Entry(row1, width=18, font=("微软雅黑", 12))
search_entry.pack(side="left", padx=5)
Button(row1, text="🔍", font=("微软雅黑", 12, "bold"), width=3, command=lambda: search_word()).pack(side="left")

row2 = Frame(tab_table)
row2.pack(fill="x", padx=20, pady=5)
Button(row2, text="📥 导出", font=("微软雅黑", 11, "bold"), command=lambda: export_current_level_words(current_level_id.get(), current_level_name.get())).pack(side="left", padx=5)
Button(row2, text="📤 导入", font=("微软雅黑", 11, "bold"), command=lambda: import_words_excel(current_level_id.get())).pack(side="left", padx=5)
lbl_temp = Label(row2, text="下载导入模板", fg="blue", cursor="hand2", font=("微软雅黑", 10, "underline"))
lbl_temp.pack(side="left", padx=5)
lbl_temp.bind("<Button-1>", lambda e: download_import_template())

# 新增：选中单词加入记忆计划
def add_selected_to_memory():
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("提示", "请先选中表格中的单词")
        return
    word = tree.item(sel[0], "values")[0]
    add_word_to_memory_plan(word)
    messagebox.showinfo("成功", f"「{word}」已加入艾宾浩斯记忆复习计划")

Button(row2, text="🧠 加入记忆计划", font=("微软雅黑", 11, "bold"), bg="#dceaff", command=add_selected_to_memory).pack(side="left", padx=10)

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

tree = ttk.Treeview(tab_table, columns=("w", "uk", "us", "m", "l"), show="headings", height=15)
tree.heading("w", text="单词")
tree.heading("uk", text="英音")
tree.heading("us", text="美音")
tree.heading("m", text="释义（多个用分号分隔）")
tree.heading("l", text="等级")
tree.column("w", width=120)
tree.column("uk", width=90)
tree.column("us", width=90)
tree.column("m", width=320)
tree.column("l", width=120)
tree.pack(padx=20, pady=10, fill="x")

page_frame = Frame(tab_table)
page_frame.pack(fill="x", padx=20, pady=5)
page_label = Label(page_frame, text="第 1 页", font=("微软雅黑", 11))
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
Label(tab_table, text="💡 双击 / 回车 朗读单词｜选中单词可一键加入艾宾浩斯记忆计划", font=("微软雅黑", 11)).pack()

# ==============================================
# 4. 单词背诵 Tab（新增加入记忆计划）
# ==============================================
tab_memorize = ttk.Frame(tab_control)
tab_control.add(tab_memorize, text="单词背诵")

mem_word_list = []
mem_index = 0
is_show_detail = tk.BooleanVar(value=False)

Label(tab_memorize, text="有序单词背诵卡（支持一词多义）", font=("微软雅黑", 16, "bold")).pack(pady=10)
mem_pos_label = Label(tab_memorize, text="0/0", font=("微软雅黑", 12))
mem_pos_label.pack()

card_frame = Frame(tab_memorize, bd=2, relief="solid", width=800, height=380)
card_frame.pack(padx=30, pady=10, fill="x")
card_frame.pack_propagate(False)

lbl_mem_word = Label(card_frame, text="请点击「加载词库」", font=("微软雅黑", 30, "bold"), wraplength=750)
lbl_mem_word.pack(pady=30)

detail_frame = Frame(card_frame)
lbl_uk = Label(detail_frame, text="英音：", font=("微软雅黑", 12))
lbl_us = Label(detail_frame, text="美音：", font=("微软雅黑", 12))
lbl_senses_title = Label(detail_frame, text="释义列表：", font=("微软雅黑", 12, "bold"))
lbl_senses_content = Label(detail_frame, text="", font=("微软雅黑", 11), wraplength=720, justify="left")
lbl_ex_title = Label(detail_frame, text="\n例句：", font=("微软雅黑", 12, "bold"))
lbl_ex_content = Label(detail_frame, text="", font=("微软雅黑", 11), wraplength=720, justify="left")

def refresh_memorize_display():
    global mem_word_list, mem_index
    if not mem_word_list:
        lbl_mem_word.config(text="当前等级无单词，请先录入！")
        mem_pos_label.config(text="0/0")
        detail_frame.pack_forget()
        return
    word, uk, us, pos, mean, ex, trans = mem_word_list[mem_index]
    is_show_detail.set(False)
    lbl_mem_word.config(text=word)
    detail_frame.pack_forget()
    mem_pos_label.config(text=f"{mem_index + 1}/{len(mem_word_list)}")

def load_memorize_words():
    global mem_word_list, mem_index
    mem_word_list = get_all_words_by_level(current_level_id.get())
    mem_index = 0
    refresh_memorize_display()

def flip_card():
    if not mem_word_list:
        return
    word, uk, us, pos, mean, ex, trans = mem_word_list[mem_index]
    if is_show_detail.get():
        is_show_detail.set(False)
        lbl_mem_word.config(text=word)
        detail_frame.pack_forget()
    else:
        is_show_detail.set(True)
        lbl_mem_word.config(text=word)
        lbl_uk.config(text=f"英音：{uk if uk else '暂无'}")
        lbl_us.config(text=f"美音：{us if us else '暂无'}")
        details = get_word_full_details(word)
        if details and details['senses']:
            senses_text = ""
            examples_text = ""
            for i, (pos, meaning, example, translation) in enumerate(details['senses'], 1):
                senses_text += f"{i}. {pos} {meaning}\n"
                if example:
                    examples_text += f"{i}. {example}\n"
                    if translation:
                        examples_text += f"   {translation}\n"
            lbl_senses_content.config(text=senses_text)
            if examples_text:
                lbl_ex_content.config(text=examples_text)
                lbl_ex_title.pack()
                lbl_ex_content.pack(pady=3)
            else:
                lbl_ex_content.config(text="")
                lbl_ex_title.pack_forget()
                lbl_ex_content.pack_forget()
        else:
            lbl_senses_content.config(text="释义：暂无")
            lbl_ex_content.config(text="")
            lbl_ex_title.pack_forget()
            lbl_ex_content.pack_forget()
        detail_frame.pack(pady=10)
        lbl_uk.pack()
        lbl_us.pack()
        lbl_senses_title.pack()
        lbl_senses_content.pack(pady=5)

def speak_mem_word():
    if mem_word_list:
        speak_word(mem_word_list[mem_index][0])

def mem_prev():
    global mem_index
    if not mem_word_list:
        messagebox.showinfo("提示", "请先加载词库")
        return
    if mem_index <= 0:
        messagebox.showinfo("提示", "已经是第一个单词，无法向前翻页")
        return
    mem_index -= 1
    refresh_memorize_display()

def mem_next():
    global mem_index
    if not mem_word_list:
        messagebox.showinfo("提示", "请先加载词库")
        return
    if mem_index >= len(mem_word_list) - 1:
        messagebox.showinfo("提示", "已经是最后一个单词，无法向后翻页")
        return
    mem_index += 1
    refresh_memorize_display()

# 当前单词加入记忆计划
def mem_add_memory():
    if not mem_word_list:
        messagebox.showinfo("提示", "请先加载词库")
        return
    word = mem_word_list[mem_index][0]
    add_word_to_memory_plan(word)
    messagebox.showinfo("完成", f"「{word}」加入艾宾浩斯记忆计划")

mem_btn_frame = Frame(tab_memorize)
mem_btn_frame.pack(pady=10)
ttk.Button(mem_btn_frame, text="加载词库", style="Mid.TButton", command=load_memorize_words).grid(row=0, column=0, padx=6)
ttk.Button(mem_btn_frame, text="上一个", style="Mid.TButton", command=mem_prev).grid(row=0, column=1, padx=6)
ttk.Button(mem_btn_frame, text="下一个", style="Mid.TButton", command=mem_next).grid(row=0, column=2, padx=6)
ttk.Button(mem_btn_frame, text="翻面查看释义", style="Mid.TButton", command=flip_card).grid(row=0, column=3, padx=6)
ttk.Button(mem_btn_frame, text="🔊 朗读单词", style="Mid.TButton", command=speak_mem_word).grid(row=0, column=4, padx=6)
ttk.Button(mem_btn_frame, text="🧠 加入记忆计划", style="Mid.TButton", command=mem_add_memory).grid(row=0, column=5, padx=6)
Label(tab_memorize, text="操作提示：切换上方等级后点击「加载词库」更新背诵列表，可将当前单词加入艾宾浩斯复习", font=("微软雅黑", 10)).pack(pady=5)



# ==============================================
# 5. 拼写测试 Tab
# ==============================================
tab_spell = ttk.Frame(tab_control)
tab_control.add(tab_spell, text="拼写测试")

spell_word_pool = []
spell_idx = 0
spell_answered = dict()
correct_count = 0
wrong_count = 0

Label(tab_spell, text="释义拼写自测（有序遍历，每题仅计分一次）", font=("微软雅黑", 16, "bold")).pack(pady=10)
spell_pos_label = Label(tab_spell, text="0/0", font=("微软雅黑", 12))
spell_pos_label.pack()

spell_card = Frame(tab_spell, bd=2, relief="solid", width=850, height=200)
spell_card.pack(padx=20, pady=10, fill="x")
spell_card.pack_propagate(False)
lbl_spell_mean = Label(spell_card, text="点击「加载题库」加载单词", font=("微软雅黑", 16), wraplength=800)
lbl_spell_mean.pack(pady=60)

spell_input_frame = Frame(tab_spell)
spell_input_frame.pack(pady=10)
Label(spell_input_frame, text="请输入单词：", font=("微软雅黑", 12)).grid(row=0, column=0)
entry_spell = Entry(spell_input_frame, width=35, font=("微软雅黑", 14))
entry_spell.grid(row=0, column=1, padx=10)

lbl_spell_result = Label(tab_spell, text="", font=("微软雅黑", 13, "bold"))
lbl_spell_result.pack(pady=5)

lbl_spell_stat = Label(tab_spell, text=f"正确：{correct_count} | 错误：{wrong_count}", font=("微软雅黑", 11))
lbl_spell_stat.pack(pady=3)


def refresh_spell_display():
    global spell_word_pool, spell_idx
    if not spell_word_pool:
        lbl_spell_mean.config(text="当前等级无单词，请先录入！")
        spell_pos_label.config(text="0/0")
        return
    _, _, _, _, mean, _, _ = spell_word_pool[spell_idx]
    lbl_spell_mean.config(text=f"释义：{mean}")
    entry_spell.delete(0, tk.END)
    lbl_spell_result.config(text="")
    spell_pos_label.config(text=f"{spell_idx + 1}/{len(spell_word_pool)}")


def load_spell_words():
    global spell_word_pool, spell_idx, spell_answered, correct_count, wrong_count
    spell_word_pool = get_all_words_by_level(current_level_id.get())
    spell_idx = 0
    spell_answered.clear()
    correct_count = 0
    wrong_count = 0
    lbl_spell_stat.config(text=f"正确：{correct_count} | 错误：{wrong_count}")
    refresh_spell_display()


def spell_prev():
    global spell_idx
    if not spell_word_pool:
        messagebox.showinfo("提示", "请先加载题库")
        return
    if spell_idx <= 0:
        messagebox.showinfo("提示", "已经是第一题，无法向前翻页")
        return
    spell_idx -= 1
    refresh_spell_display()


def spell_next():
    global spell_idx
    if not spell_word_pool:
        messagebox.showinfo("提示", "请先加载题库")
        return
    if spell_idx >= len(spell_word_pool) - 1:
        messagebox.showinfo("提示", "已经是最后一题，无法向后翻页")
        return
    spell_idx += 1
    refresh_spell_display()


def check_spell_answer():
    global correct_count, wrong_count, spell_answered
    if not spell_word_pool:
        messagebox.showinfo("提示", "请先点击加载题库")
        return
    current_word = spell_word_pool[spell_idx][0]
    user_input = entry_spell.get().strip().lower()
    real_word = current_word.lower()

    if current_word in spell_answered:
        if user_input == real_word:
            lbl_spell_result.config(text="✅ 正确（已记录，分数不重复累加）", fg="green")
        else:
            lbl_spell_result.config(text=f"❌ 错误，正确单词：{current_word}（已记录）", fg="red")
        return

    spell_answered[current_word] = True
    if user_input == real_word:
        correct_count += 1
        lbl_spell_result.config(text="✅ 拼写正确！", fg="green")
    else:
        wrong_count += 1
        add_word_to_word_book(current_word, note="拼写测试错题")
        lbl_spell_result.config(text=f"❌ 错误，正确单词：{current_word}\n📝 已自动加入单词本", fg="red")

    lbl_spell_stat.config(text=f"正确：{correct_count} | 错误：{wrong_count}")


def reset_spell_stat():
    global correct_count, wrong_count, spell_answered
    correct_count = 0
    wrong_count = 0
    spell_answered.clear()
    lbl_spell_stat.config(text=f"正确：{correct_count} | 错误：{wrong_count}")
    lbl_spell_result.config(text="")


def spell_speak_ans():
    if spell_word_pool:
        speak_word(spell_word_pool[spell_idx][0])


spell_btn_frame = Frame(tab_spell)
spell_btn_frame.pack(pady=10)
ttk.Button(spell_btn_frame, text="加载题库", style="Mid.TButton", command=load_spell_words).grid(row=0, column=0,
                                                                                                 padx=4)
ttk.Button(spell_btn_frame, text="上一题", style="Mid.TButton", command=spell_prev).grid(row=0, column=1, padx=4)
ttk.Button(spell_btn_frame, text="下一题", style="Mid.TButton", command=spell_next).grid(row=0, column=2, padx=4)
ttk.Button(spell_btn_frame, text="提交答案", style="Mid.TButton", command=check_spell_answer).grid(row=0, column=3,
                                                                                                   padx=4)
ttk.Button(spell_btn_frame, text="朗读答案", style="Mid.TButton", command=spell_speak_ans).grid(row=0, column=4, padx=4)
ttk.Button(spell_btn_frame, text="重置统计", style="Mid.TButton", command=reset_spell_stat).grid(row=0, column=5,
                                                                                                 padx=4)

entry_spell.bind("<Return>", lambda e: check_spell_answer())

Label(tab_spell, text="提示：切换等级后重新「加载题库」，每个单词仅首次答题计入分数", font=("微软雅黑", 10)).pack(pady=5)

# ==============================================
# 6. 单词本 Tab
# ==============================================
tab_wordbook = ttk.Frame(tab_control)
tab_control.add(tab_wordbook, text="📖 单词本")

wordbook_list = []
wordbook_index = 0
is_show_wordbook_detail = tk.BooleanVar(value=False)

Label(tab_wordbook, text="📖 我的单词本", font=("微软雅黑", 18, "bold")).pack(pady=10)

wordbook_stat_frame = Frame(tab_wordbook)
wordbook_stat_frame.pack(pady=5)
lbl_wordbook_count = Label(wordbook_stat_frame, text="单词总数：0", font=("微软雅黑", 12))
lbl_wordbook_count.pack(side="left", padx=10)

wordbook_pos_label = Label(tab_wordbook, text="0/0", font=("微软雅黑", 12))
wordbook_pos_label.pack()

wordbook_card_frame = Frame(tab_wordbook, bd=2, relief="solid", width=800, height=380)
wordbook_card_frame.pack(padx=30, pady=10, fill="x")
wordbook_card_frame.pack_propagate(False)

lbl_wordbook_word = Label(wordbook_card_frame, text="点击「加载单词本」查看单词", font=("微软雅黑", 28, "bold"),
                          wraplength=750)
lbl_wordbook_word.pack(pady=50)

wordbook_detail_frame = Frame(wordbook_card_frame)
lbl_wordbook_uk = Label(wordbook_detail_frame, text="英音：", font=("微软雅黑", 12))
lbl_wordbook_us = Label(wordbook_detail_frame, text="美音：", font=("微软雅黑", 12))
lbl_wordbook_senses = Label(wordbook_detail_frame, text="释义：", font=("微软雅黑", 12))
lbl_wordbook_note = Label(wordbook_detail_frame, text="备注：", font=("微软雅黑", 11, "bold"), fg="blue")
lbl_wordbook_added_time = Label(wordbook_detail_frame, text="添加时间：", font=("微软雅黑", 10))


def refresh_wordbook_display():
    global wordbook_list, wordbook_index
    if not wordbook_list:
        lbl_wordbook_word.config(text="单词本为空，快去添加重点单词吧！")
        wordbook_pos_label.config(text="0/0")
        wordbook_detail_frame.pack_forget()
        return

    word_data = wordbook_list[wordbook_index]
    word = word_data[0]
    is_show_wordbook_detail.set(False)

    lbl_wordbook_word.config(text=word)
    wordbook_detail_frame.pack_forget()
    wordbook_pos_label.config(text=f"{wordbook_index + 1}/{len(wordbook_list)}")


def load_wordbook():
    global wordbook_list, wordbook_index
    wordbook_list = get_word_book_words()
    wordbook_index = 0

    lbl_wordbook_count.config(text=f"单词总数：{len(wordbook_list)}")

    if wordbook_list:
        messagebox.showinfo("加载成功", f"已加载 {len(wordbook_list)} 个单词")

    refresh_wordbook_display()


def flip_wordbook_card():
    if not wordbook_list:
        return

    word_data = wordbook_list[wordbook_index]
    word, uk, us, meanings, added_time, note, mastered = word_data

    if is_show_wordbook_detail.get():
        is_show_wordbook_detail.set(False)
        lbl_wordbook_word.config(text=word)
        wordbook_detail_frame.pack_forget()
    else:
        is_show_wordbook_detail.set(True)
        lbl_wordbook_word.config(text=word)

        uk_text = f"英音：{uk}" if uk else "英音：暂无"
        us_text = f"美音：{us}" if us else "美音：暂无"
        meanings_text = f"释义：{meanings}" if meanings else "释义：暂无"
        note_text = f"备注：{note}" if note else "备注：无"
        time_text = f"添加时间：{added_time}"

        lbl_wordbook_uk.config(text=uk_text)
        lbl_wordbook_us.config(text=us_text)
        lbl_wordbook_senses.config(text=meanings_text)
        lbl_wordbook_note.config(text=note_text)
        lbl_wordbook_added_time.config(text=time_text)

        wordbook_detail_frame.pack(pady=10)
        lbl_wordbook_uk.pack()
        lbl_wordbook_us.pack()
        lbl_wordbook_senses.pack(pady=5)
        lbl_wordbook_note.pack(pady=3)
        lbl_wordbook_added_time.pack(pady=3)


def speak_wordbook_word():
    if wordbook_list:
        speak_word(wordbook_list[wordbook_index][0])


def wordbook_prev():
    global wordbook_index
    if not wordbook_list:
        messagebox.showinfo("提示", "请先加载单词本")
        return
    if wordbook_index <= 0:
        messagebox.showinfo("提示", "已经是第一个单词，无法向前翻页")
        return
    wordbook_index -= 1
    refresh_wordbook_display()


def wordbook_next():
    global wordbook_index
    if not wordbook_list:
        messagebox.showinfo("提示", "请先加载单词本")
        return
    if wordbook_index >= len(wordbook_list) - 1:
        messagebox.showinfo("提示", "已经是最后一个单词，无法向后翻页")
        return
    wordbook_index += 1
    refresh_wordbook_display()


def add_manual_word_to_book():
    dialog = tk.Toplevel(root)
    dialog.title("添加单词到单词本")
    dialog.geometry("400x200")
    dialog.transient(root)
    dialog.grab_set()

    Label(dialog, text="请输入单词：", font=("微软雅黑", 11)).pack(pady=10)
    entry_add_word = Entry(dialog, width=30, font=("微软雅黑", 12))
    entry_add_word.pack(pady=5)
    entry_add_word.focus()

    Label(dialog, text="备注（可选）：", font=("微软雅黑", 11)).pack(pady=5)
    entry_add_note = Entry(dialog, width=30, font=("微软雅黑", 12))
    entry_add_note.pack(pady=5)

    def confirm_add():
        word = entry_add_word.get().strip()
        note = entry_add_note.get().strip()

        if not word:
            messagebox.showwarning("提示", "单词不能为空")
            return

        if add_word_to_word_book(word, note):
            messagebox.showinfo("成功", f"「{word}」已添加到单词本")
            dialog.destroy()
            load_wordbook()
        else:
            messagebox.showerror("失败", "添加失败，该单词可能已在单词本中")

    btn_frame = Frame(dialog)
    btn_frame.pack(pady=15)
    ttk.Button(btn_frame, text="确定", style="Mid.TButton", command=confirm_add).grid(row=0, column=0, padx=10)
    ttk.Button(btn_frame, text="取消", style="Mid.TButton", command=dialog.destroy).grid(row=0, column=1, padx=10)

    entry_add_word.bind("<Return>", lambda e: confirm_add())


def remove_current_wordbook_word():
    global wordbook_list, wordbook_index
    if not wordbook_list:
        messagebox.showinfo("提示", "请先加载单词本")
        return

    current_word = wordbook_list[wordbook_index][0]

    confirm = messagebox.askyesno("确认删除", f"确定要将「{current_word}」从单词本中移除吗？")
    if confirm:
        if remove_from_word_book(current_word):
            messagebox.showinfo("成功", f"已移除「{current_word}」")
            wordbook_list.pop(wordbook_index)
            if wordbook_index >= len(wordbook_list):
                wordbook_index = max(0, len(wordbook_list) - 1)
            lbl_wordbook_count.config(text=f"单词总数：{len(wordbook_list)}")
            refresh_wordbook_display()


def mark_current_wordbook_mastered():
    global wordbook_list, wordbook_index
    if not wordbook_list:
        messagebox.showinfo("提示", "请先加载单词本")
        return

    current_word = wordbook_list[wordbook_index][0]

    confirm = messagebox.askyesno("确认标记", f"确定已将「{current_word}」掌握了吗？\n该单词将从单词本中移除")
    if confirm:
        if mark_word_as_mastered(current_word):
            messagebox.showinfo("太棒了！", f"🎉 恭喜掌握「{current_word}」！")
            wordbook_list.pop(wordbook_index)
            if wordbook_index >= len(wordbook_list):
                wordbook_index = max(0, len(wordbook_list) - 1)
            lbl_wordbook_count.config(text=f"单词总数：{len(wordbook_list)}")
            refresh_wordbook_display()


wordbook_btn_frame = Frame(tab_wordbook)
wordbook_btn_frame.pack(pady=10)

btn_row1 = Frame(wordbook_btn_frame)
btn_row1.pack(pady=5)
ttk.Button(btn_row1, text="加载单词本", style="Mid.TButton", command=load_wordbook).grid(row=0, column=0, padx=6)
ttk.Button(btn_row1, text="➕ 添加单词", style="Mid.TButton", command=add_manual_word_to_book).grid(row=0, column=1,
                                                                                                   padx=6)
ttk.Button(btn_row1, text="上一个", style="Mid.TButton", command=wordbook_prev).grid(row=0, column=2, padx=6)
ttk.Button(btn_row1, text="下一个", style="Mid.TButton", command=wordbook_next).grid(row=0, column=3, padx=6)
ttk.Button(btn_row1, text="翻面查看释义", style="Mid.TButton", command=flip_wordbook_card).grid(row=0, column=4, padx=6)
ttk.Button(btn_row1, text="🔊 朗读单词", style="Mid.TButton", command=speak_wordbook_word).grid(row=0, column=5, padx=6)

btn_row2 = Frame(wordbook_btn_frame)
btn_row2.pack(pady=5)
ttk.Button(btn_row2, text="✅ 已掌握（移除）", style="Mid.TButton", command=mark_current_wordbook_mastered).grid(row=0,
                                                                                                              column=0,
                                                                                                              padx=6)
ttk.Button(btn_row2, text="🗑️ 从单词本删除", style="Mid.TButton", command=remove_current_wordbook_word).grid(row=0,
                                                                                                             column=1,
                                                                                                             padx=6)

Label(tab_wordbook, text="💡 提示：拼写测试答错的单词会自动加入单词本 | 也可手动添加重点单词 | 点击「已掌握」可将单词移出",
      font=("微软雅黑", 10), fg="blue").pack(pady=5)


# ==============================================
# 7. 🧠 艾宾浩斯复习 独立新增标签页
# ==============================================
tab_ebbinghaus = ttk.Frame(tab_control)
tab_control.add(tab_ebbinghaus, text="🧠 艾宾浩斯复习")

# 全局缓存当前待复习列表、当前下标
eb_due_list = []
eb_current_idx = 0


# ======================
# 艾宾浩斯页面核心函数
# ======================
def refresh_eb_list():
    """刷新所有到期待复习单词列表"""
    global eb_due_list, eb_current_idx
    eb_due_list = get_due_memory_words()
    eb_current_idx = 0
    lbl_eb_total.config(text=f"待复习单词：{len(eb_due_list)} 个")
    if len(eb_due_list) == 0:
        lbl_eb_word.config(text="🎉 今日无到期复习单词，稍后再来！")
        eb_detail_frame.pack_forget()
        lbl_eb_pos.config(text="0/0")
        return
    render_eb_card()

def render_eb_card():
    """渲染当前下标单词卡片"""
    global eb_due_list, eb_current_idx
    if not eb_due_list:
        return
    word, mem_lv, next_ts, uk, us, meanings = eb_due_list[eb_current_idx]
    # 更新顶部页码
    lbl_eb_pos.config(text=f"{eb_current_idx + 1}/{len(eb_due_list)}")
    # 重置详情折叠状态
    eb_show_detail_flag.set(False)
    eb_detail_frame.pack_forget()
    # 基础单词显示
    lbl_eb_word.config(text=word)
    # 档位文本
    level_min = EBBINGHAUS_INTERVALS[mem_lv]
    lbl_eb_lv.config(text=f"记忆档位：{mem_lv} 档 | 当前间隔 {level_min} 分钟")

def eb_toggle_detail():
    """展开/收起完整音标、多释义、例句"""
    global eb_due_list, eb_current_idx
    if not eb_due_list:
        return
    word, mem_lv, next_ts, uk, us, meanings = eb_due_list[eb_current_idx]
    if eb_show_detail_flag.get():
        # 收起
        eb_show_detail_flag.set(False)
        eb_detail_frame.pack_forget()
    else:
        # 展开
        eb_show_detail_flag.set(True)
        eb_detail_frame.pack(pady=10)
        lbl_eb_uk.config(text=f"英音：{uk if uk else '无'}")
        lbl_eb_us.config(text=f"美音：{us if us else '无'}")
        # 加载完整多释义
        full_info = get_word_full_details(word)
        sense_str = ""
        ex_str = ""
        if full_info and full_info["senses"]:
            for idx, (pos, mean, ex, trans) in enumerate(full_info["senses"], 1):
                sense_str += f"{idx}. {pos} {mean}\n"
                if ex:
                    ex_str += f"{idx}. {ex}\n    {trans}\n"
        lbl_eb_sense_text.config(text=sense_str)
        if ex_str.strip():
            lbl_eb_ex_title.pack()
            lbl_eb_ex_text.config(text=ex_str)
            lbl_eb_ex_text.pack(pady=4)
        else:
            lbl_eb_ex_title.pack_forget()
            lbl_eb_ex_text.pack_forget()
        lbl_eb_uk.pack()
        lbl_eb_us.pack()
        lbl_eb_lv.pack(pady=3)
        lbl_eb_sense_title.pack()
        lbl_eb_sense_text.pack(pady=3)

def eb_speak():
    """朗读当前单词"""
    global eb_due_list, eb_current_idx
    if not eb_due_list:
        return
    word = eb_due_list[eb_current_idx][0]
    speak_word(word)

def next_eb_card_after_review():
    """复习完成后切换下一张，无单词则清空界面"""
    global eb_due_list, eb_current_idx
    eb_current_idx += 1
    if eb_current_idx >= len(eb_due_list):
        # 全部复习完毕
        eb_due_list.clear()
        eb_current_idx = 0
        lbl_eb_word.config(text="✅ 所有到期单词复习完成！")
        eb_detail_frame.pack_forget()
        lbl_eb_total.config(text="待复习单词：0 个")
        lbl_eb_pos.config(text="0/0")
        messagebox.showinfo("完成", "本轮所有到期单词复习完毕！")
        return
    render_eb_card()

def eb_mark_remember():
    # 标记记住，升档
    global eb_due_list, eb_current_idx
    if not eb_due_list:
        return
    word = eb_due_list[eb_current_idx][0]
    review_memory_word(word, is_remembered=True)
    messagebox.showinfo("记住了", f"「{word}」记忆档位提升，下次复习间隔延长！")
    next_eb_card_after_review()

def eb_mark_forget():
    # 标记遗忘，重置0档
    global eb_due_list, eb_current_idx
    if not eb_due_list:
        return
    word = eb_due_list[eb_current_idx][0]
    review_memory_word(word, is_remembered=False)
    messagebox.showwarning("遗忘", f"「{word}」已重置初始档位，5分钟后再次复习！")
    next_eb_card_after_review()

# 顶部统计栏
eb_top_frame = Frame(tab_ebbinghaus)
eb_top_frame.pack(fill="x", padx=20, pady=8)
lbl_eb_total = Label(eb_top_frame, text="待复习单词：0 个", font=("微软雅黑", 12, "bold"), fg="#2060c0")
lbl_eb_pos = Label(eb_top_frame, text="0/0", font=("微软雅黑", 12))
btn_refresh_eb = ttk.Button(eb_top_frame, text="🔄 刷新待复习列表", style="Mid.TButton", command=refresh_eb_list)

lbl_eb_total.pack(side="left", padx=10)
lbl_eb_pos.pack(side="left", padx=20)
btn_refresh_eb.pack(side="right", padx=10)

# 单词卡片容器
eb_card_frame = Frame(tab_ebbinghaus, bd=3, relief="solid", width=900, height=420)
eb_card_frame.pack(padx=30, pady=15, fill="x")
eb_card_frame.pack_propagate(False)

# 卡片主单词
lbl_eb_word = Label(eb_card_frame, text="点击【刷新待复习列表】加载到期单词", font=("微软雅黑", 32, "bold"), wraplength=820)
lbl_eb_word.pack(pady=40)

# 详情容器（音标+释义+例句）
eb_detail_frame = Frame(eb_card_frame)
lbl_eb_uk = Label(eb_detail_frame, text="英音：", font=("微软雅黑", 12))
lbl_eb_us = Label(eb_detail_frame, text="美音：", font=("微软雅黑", 12))
lbl_eb_lv = Label(eb_detail_frame, text="记忆档位：", font=("微软雅黑", 11, "bold"), fg="#c04020")
lbl_eb_sense_title = Label(eb_detail_frame, text="完整释义：", font=("微软雅黑", 12, "bold"))
lbl_eb_sense_text = Label(eb_detail_frame, text="", font=("微软雅黑", 11), wraplength=800, justify="left")
lbl_eb_ex_title = Label(eb_detail_frame, text="例句：", font=("微软雅黑", 12, "bold"))
lbl_eb_ex_text = Label(eb_detail_frame, text="", font=("微软雅黑", 11), wraplength=800, justify="left")

# 底部操作按钮区
eb_btn_frame = Frame(tab_ebbinghaus)
eb_btn_frame.pack(pady=12)
btn_eb_read = ttk.Button(eb_btn_frame, text="🔊 朗读单词", style="Mid.TButton", command=eb_speak)
btn_eb_show_detail = ttk.Button(eb_btn_frame, text="📖 查看完整释义", style="Mid.TButton", command=eb_toggle_detail)
btn_eb_forget = ttk.Button(eb_btn_frame, text="❌ 忘记了（重置5分钟重学）", style="Mid.TButton", command=eb_mark_forget)
btn_eb_remember = ttk.Button(eb_btn_frame, text="✅ 记住了（拉长复习周期）", style="Big.TButton", command=eb_mark_remember)

btn_eb_read.grid(row=0, column=0, padx=6)
btn_eb_show_detail.grid(row=0, column=1, padx=6)
btn_eb_forget.grid(row=0, column=2, padx=10)
btn_eb_remember.grid(row=0, column=3, padx=10)

# 提示文字
Label(tab_ebbinghaus, text="规则：记住自动升档拉长间隔；忘记直接重置0档，5分钟后再次复习；升到30天档位永久不再推送",
      font=("微软雅黑", 10), fg="#555").pack(pady=5)

# 控制变量：是否展开释义
eb_show_detail_flag = tk.BooleanVar(value=False)


# 页面加载自动刷新一次
tab_ebbinghaus.bind("<Map>", lambda e: refresh_eb_list())




# ======================
# 主循环启动
# ======================
root.mainloop()