-- 单词等级表（小学3-4、初中、高中、四级等）
DROP TABLE IF EXISTS levels;
CREATE TABLE levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,  -- 如：小学3-4年级、初中、大学四级
    sort INTEGER DEFAULT 0      -- 排序用
);

-- 单词主表
DROP TABLE IF EXISTS words;
CREATE TABLE words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,   -- 单词
    uk_phonetic TEXT,            -- 英音标
    us_phonetic TEXT,            -- 美音标
    audio_path TEXT,             -- 本地读音文件路径
    pos TEXT,                    -- 词性 n. v. adj. adv.
    meaning TEXT NOT NULL,       -- 中文释义
    level_id INTEGER,            -- 所属等级
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (level_id) REFERENCES levels(id),
);

-- 例句表
DROP TABLE IF EXISTS examples;
CREATE TABLE examples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    en_sentence TEXT NOT NULL,   -- 英文例句
    cn_sentence TEXT NOT NULL,   -- 中文翻译
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
);

-- 初始化等级数据（你要求的全学段）
INSERT INTO levels (name, sort) VALUES
('小学3-4年级', 10),
('小学5-6年级', 20),
('初中7-9年级', 30),
('高中必修', 40),
('高中选择性必修', 50),
('大学四级', 60),
('大学六级', 70),
('托福', 80),
('雅思', 90);
