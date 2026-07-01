"""艾宾浩斯记忆服务"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import MemoryRepository


class MemoryService:
    """记忆计划业务逻辑服务"""

    def __init__(self):
        self.repo = MemoryRepository()

    def add_word(self, word):
        """添加单词到记忆计划

        Args:
            word: 单词文本
        """
        self.repo.add_word_to_memory_plan(word)

    def review_word(self, word, is_remembered):
        """复习单词

        Args:
            word: 单词文本
            is_remembered: True记住，False遗忘

        Returns:
            bool: 更新成功返回True
        """
        return self.repo.review_memory_word(word, is_remembered)

    def get_due_words(self):
        """获取待复习单词

        Returns:
            list: 待复习单词列表
        """
        return self.repo.get_due_memory_words()

    def get_status(self, word):
        """获取单词记忆状态

        Args:
            word: 单词文本

        Returns:
            dict or None: 记忆状态信息
        """
        return self.repo.get_word_memory_status(word)
