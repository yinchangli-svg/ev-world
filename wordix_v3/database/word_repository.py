
"""单词数据访问层 - 处理单词相关的数据库操作"""

from .db_manager import get_connection


class WordRepository:
    """单词数据仓库"""
    
    @staticmethod
    def get_level_options():
        """获取所有等级选项
        
        Returns:
            list: [(id, name), ...] 等级列表
        """
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, name FROM levels ORDER BY sort")
        data = c.fetchall()
        conn.close()
        return data
    
    @staticmethod
    def get_level_id_by_name(name):
        """根据等级名称获取ID
        
        Args:
            name: 等级名称
            
        Returns:
            int or None: 等级ID，未找到返回None
        """
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM levels WHERE name=?", (name,))
        res = c.fetchone()
        conn.close()
        return res[0] if res else None
    
    @staticmethod
    def save_word_with_senses(word, uk_phonetic, us_phonetic, level_id, senses_list):
        """保存单词及其多个释义（支持一词多义）
        
        Args:
            word: 单词文本
            uk_phonetic: 英式音标
            us_phonetic: 美式音标
            level_id: 等级ID
            senses_list: 释义列表 [(pos, meaning, example, translation), ...]
            
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            conn = get_connection()
            c = conn.cursor()
            
            # 检查单词是否已存在
            c.execute("SELECT id FROM words WHERE word=?", (word,))
            existing = c.fetchone()
            
            if existing:
                word_id = existing[0]
                # 删除旧的释义
                c.execute("DELETE FROM word_senses WHERE word_id=?", (word_id,))
            else:
                # 插入新单词
                c.execute('''INSERT INTO words (word, uk_phonetic, us_phonetic, level_id)
                             VALUES (?,?,?,?)''',
                          (word, uk_phonetic, us_phonetic, level_id))
                word_id = c.lastrowid
            
            # 插入所有释义
            for i, (pos, meaning, example, translation) in enumerate(senses_list):
                frequency = 100 - i * 10  # 第一个释义频率最高
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
    
    @staticmethod
    def load_words_by_level_and_page(level_id, page_num, page_size=10):
        """分页加载指定等级的单词
        
        Args:
            level_id: 等级ID
            page_num: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            tuple: (data, total, total_page) 数据列表、总数、总页数
        """
        offset = (page_num - 1) * page_size
        conn = get_connection()
        c = conn.cursor()
        
        # 查询单词列表（合并多个释义）
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
        
        # 查询总数
        c.execute('''SELECT COUNT(DISTINCT w.id) FROM words w WHERE w.level_id=?''', (level_id,))
        total = c.fetchone()[0]
        total_page = (total + page_size - 1) // page_size
        
        conn.close()
        return data, total, total_page
    
    @staticmethod
    def search_word_by_level(level_id, word):
        """在指定等级中搜索单词
        
        Args:
            level_id: 等级ID
            word: 要搜索的单词
            
        Returns:
            tuple or None: 单词信息，未找到返回None
        """
        conn = get_connection()
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
    
    @staticmethod
    def get_all_words_by_level(level_id):
        """获取指定等级的所有单词（用于背诵和游戏）
        
        Args:
            level_id: 等级ID
            
        Returns:
            list: [(word, uk, us, pos, meaning, example, translation), ...]
        """
        conn = get_connection()
        c = conn.cursor()
        c.execute('''SELECT DISTINCT w.word, w.uk_phonetic, w.us_phonetic
                     FROM words w
                     WHERE w.level_id=?''', (level_id,))
        words = []
        for row in c.fetchall():
            word, uk, us = row
            # 获取该单词的所有释义
            c.execute('''SELECT pos, meaning, example, translation 
                         FROM word_senses 
                         WHERE word_id=(SELECT id FROM words WHERE word=? AND level_id=?)
                         ORDER BY frequency DESC, id ASC''', (word, level_id))
            senses = c.fetchall()
            
            # 合并所有释义
            full_meaning = "; ".join([f"{pos} {mean}" for pos, mean, _, _ in senses])
            first_example = senses[0][2] if senses and senses[0][2] else ""
            first_translation = senses[0][3] if senses and senses[0][3] else ""
            
            words.append((word, uk, us, "", full_meaning, first_example, first_translation))
        conn.close()
        return words
    
    @staticmethod
    def get_word_full_details(word):
        """获取单词的完整详情（所有释义）
        
        Args:
            word: 单词文本
            
        Returns:
            dict or None: {word, uk_phonetic, us_phonetic, level_id, senses}
        """
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, word, uk_phonetic, us_phonetic, level_id FROM words WHERE word=?", (word,))
        word_info = c.fetchone()
        if not word_info:
            return None
        
        # 获取所有释义
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