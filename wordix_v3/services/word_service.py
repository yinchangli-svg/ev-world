"""单词服务层 - 业务逻辑"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wordix_v3.database import WordRepository


class WordService:
    """单词业务逻辑服务"""

    def __init__(self):
        self.repo = WordRepository()

    def get_levels(self):
        """获取所有等级

        Returns:
            list: [(id, name), ...]
        """
        return self.repo.get_level_options()

    def save_word(self, word, uk, us, level_id, senses_list):
        """保存单词

        Args:
            word: 单词文本
            uk: 英式音标
            us: 美式音标
            level_id: 等级ID
            senses_list: 释义列表 [(pos, meaning, example, translation), ...]

        Returns:
            tuple: (success: bool, message: str)
        """
        if not word or not senses_list:
            return False, "单词和释义不能为空"

        success = self.repo.save_word_with_senses(word, uk, us, level_id, senses_list)
        if success:
            return True, f"单词「{word}」保存成功，共 {len(senses_list)} 个释义"
        else:
            return False, "保存失败"

    def get_words_page(self, level_id, page, page_size=10):
        """获取分页单词列表

        Args:
            level_id: 等级ID
            page: 页码
            page_size: 每页数量

        Returns:
            tuple: (data, total, total_page)
        """
        return self.repo.load_words_by_level_and_page(level_id, page, page_size)

    def search_word(self, level_id, word):
        """搜索单词

        Args:
            level_id: 等级ID
            word: 要搜索的单词

        Returns:
            tuple or None: 单词信息
        """
        return self.repo.search_word_by_level(level_id, word)

    def get_all_words(self, level_id):
        """获取指定等级的所有单词

        Args:
            level_id: 等级ID

        Returns:
            list: 单词列表
        """
        return self.repo.get_all_words_by_level(level_id)

    def get_word_details(self, word):
        """获取单词详情

        Args:
            word: 单词文本

        Returns:
            dict or None: 单词详细信息
        """
        return self.repo.get_word_full_details(word)
