"""单词本服务"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wordix_v3.database import WordBookRepository


class WordBookService:
    """单词本业务逻辑服务"""
    
    def __init__(self):
        self.repo = WordBookRepository()
    
    def add_word(self, word, note=""):
        """添加单词到单词本
        
        Args:
            word: 单词文本
            note: 备注说明
            
        Returns:
            bool: 添加成功返回True
        """
        return self.repo.add_word_to_word_book(word, note)
    
    def get_words(self):
        """获取单词本中的所有单词
        
        Returns:
            list: 单词列表
        """
        return self.repo.get_word_book_words()
    
    def remove_word(self, word):
        """从单词本移除单词
        
        Args:
            word: 单词文本
            
        Returns:
            bool: 删除成功返回True
        """
        return self.repo.remove_from_word_book(word)
    
    def mark_mastered(self, word):
        """标记单词为已掌握
        
        Args:
            word: 单词文本
            
        Returns:
            bool: 标记成功返回True
        """
        return self.repo.mark_word_as_mastered(word)
