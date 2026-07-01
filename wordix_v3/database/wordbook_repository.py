"""单词本数据访问层 - 处理单词本相关的数据库操作"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wordix_v3.database.db_manager import get_connection


class WordBookRepository:
    """单词本数据仓库"""

    @staticmethod
    def add_word_to_word_book(word, note=""):
        """添加单词到单词本

        Args:
            word: 单词文本
            note: 备注说明

        Returns:
            bool: 添加成功返回True
        """
        try:
            conn = get_connection()
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

    @staticmethod
    def get_word_book_words():
        """获取单词本中的所有单词（未掌握的）

        Returns:
            list: [(word, uk, us, meanings, added_time, note, mastered), ...]
        """
        conn = get_connection()
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

    @staticmethod
    def remove_from_word_book(word):
        """从单词本中移除单词

        Args:
            word: 单词文本

        Returns:
            bool: 删除成功返回True
        """
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute('DELETE FROM word_book WHERE word = ?', (word,))
            conn.commit()
            return True
        except Exception as e:
            print(f"从单词本删除失败: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def mark_word_as_mastered(word):
        """标记单词为已掌握

        Args:
            word: 单词文本

        Returns:
            bool: 标记成功返回True
        """
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute('UPDATE word_book SET mastered = 1 WHERE word = ?', (word,))
            conn.commit()
            return True
        except Exception as e:
            print(f"标记已掌握失败: {e}")
            return False
        finally:
            conn.close()
