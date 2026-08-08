"""数据库管理模块 - 初始化和连接管理"""
import sqlite3
from config import DB_NAME, LEVEL_DATA


def get_connection():
    """获取数据库连接

    Returns:
        sqlite3.Connection: 数据库连接对象
    """
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_database():
    """初始化数据库表结构

    创建所有必要的表和索引：
    - levels: 等级表
    - words: 单词主表
    - word_senses: 词性和释义表（一对多关系）
    - word_book: 单词本表
    - memory_schedule: 艾宾浩斯记忆复习计划表

    并初始化默认的等级数据
    """
    conn = get_connection()
    c = conn.cursor()

    try:
        # ======================
        # 1. 创建等级表
        # ======================
        c.execute('''CREATE TABLE IF NOT EXISTS levels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        sort INTEGER DEFAULT 0
                    )''')

        # ======================
        # 2. 创建单词主表
        # ======================
        c.execute('''CREATE TABLE IF NOT EXISTS words (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        word TEXT NOT NULL,
                        uk_phonetic TEXT,
                        us_phonetic TEXT,
                        level_id INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (level_id) REFERENCES levels(id)
                    )''')

        # ======================
        # 3. 创建词性和释义表（一对多关系）
        # ======================
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

        # ======================
        # 4. 创建单词本表
        # ======================
        c.execute('''CREATE TABLE IF NOT EXISTS word_book (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        word TEXT NOT NULL,
                        added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        note TEXT,
                        mastered INTEGER DEFAULT 0,
                        UNIQUE(word)
                    )''')

        # ======================
        # 5. 创建艾宾浩斯记忆复习计划表
        # ======================
        c.execute('''CREATE TABLE IF NOT EXISTS memory_schedule (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        word TEXT NOT NULL UNIQUE,
                        mem_level INTEGER DEFAULT 0,
                        last_review_ts INTEGER DEFAULT 0,
                        next_review_ts INTEGER DEFAULT 0,
                        create_ts INTEGER DEFAULT 0
                    )''')

        # ======================
        # 6. 创建索引提升查询性能
        # ======================
        c.execute('''CREATE INDEX IF NOT EXISTS idx_words_word ON words(word)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_word_senses_word_id ON word_senses(word_id)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_memory_word ON memory_schedule(word)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_memory_next_ts ON memory_schedule(next_review_ts)''')

        # ======================
        # 7. 初始化等级数据
        # ======================
        for name, sort in LEVEL_DATA:
            c.execute('''INSERT OR IGNORE INTO levels (name, sort)
                          VALUES (?, ?)''', (name, sort))

        # 提交事务
        conn.commit()

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
