"""艾宾浩斯记忆数据访问层 - 处理记忆计划相关的数据库操作"""
import sys
import os
import time

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wordix_v3.database.db_manager import get_connection
from wordix_v3.config import EBBINGHAUS_INTERVALS, MAX_MEM_LEVEL


class MemoryRepository:
    """记忆计划数据仓库"""

    @staticmethod
    def get_now_ts():
        """获取当前时间戳（秒）

        Returns:
            int: 当前时间戳
        """
        return int(time.time())

    @staticmethod
    def calc_next_review_ts(base_ts, minute_gap):
        """计算下次复习时间戳

        Args:
            base_ts: 基准时间戳
            minute_gap: 间隔分钟数

        Returns:
            int: 下次复习时间戳
        """
        return base_ts + minute_gap * 60

    @staticmethod
    def add_word_to_memory_plan(word):
        """将单词加入艾宾浩斯记忆计划

        Args:
            word: 单词文本
        """
        now = MemoryRepository.get_now_ts()
        first_gap = EBBINGHAUS_INTERVALS[0]  # 5分钟
        next_ts = MemoryRepository.calc_next_review_ts(now, first_gap)

        conn = get_connection()
        c = conn.cursor()
        c.execute('''INSERT OR IGNORE INTO memory_schedule
                     (word, mem_level, last_review_ts, next_review_ts, create_ts)
                     VALUES (?, 0, ?, ?, ?)''', (word, now, next_ts, now))
        conn.commit()
        conn.close()

    @staticmethod
    def review_memory_word(word, is_remembered):
        """复习单词后更新记忆计划

        Args:
            word: 单词文本
            is_remembered: True记住（升档），False遗忘（重置）

        Returns:
            bool: 更新成功返回True
        """
        now = MemoryRepository.get_now_ts()
        conn = get_connection()
        c = conn.cursor()

        # 获取当前档位
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

        new_next_ts = MemoryRepository.calc_next_review_ts(now, new_gap)
        c.execute('''UPDATE memory_schedule
                     SET mem_level = ?, last_review_ts = ?, next_review_ts = ?
                     WHERE word = ?''', (new_level, now, new_next_ts, word))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def get_due_memory_words():
        """获取当前已到复习时间的单词（待复习）

        Returns:
            list: [(word, mem_level, next_review_ts, uk, us, meanings), ...]
        """
        now = MemoryRepository.get_now_ts()
        conn = get_connection()
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

    @staticmethod
    def get_word_memory_status(word):
        """查询单词记忆等级与下次复习时间

        Args:
            word: 单词文本

        Returns:
            dict or None: {level, level_name, last_review, next_review}
        """
        from datetime import datetime

        conn = get_connection()
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
