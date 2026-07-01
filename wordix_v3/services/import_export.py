"""导入导出服务"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from tkinter import messagebox, filedialog
from wordix_v3.database import WordRepository
from wordix_v3.database.db_manager import get_connection


class ImportExportService:
    """Excel导入导出服务"""

    def __init__(self):
        self.repo = WordRepository()

    def export_words(self, level_id, level_name):
        """导出指定等级的单词

        Args:
            level_id: 等级ID
            level_name: 等级名称
        """
        try:
            conn = get_connection()
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

    def download_template(self):
        """下载导入模板"""
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

    def import_words(self, level_id, file_path):
        """导入单词

        Args:
            level_id: 等级ID
            file_path: Excel文件路径
        """
        try:
            df = pd.read_excel(file_path)
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
                        if self.repo.save_word_with_senses(word, uk, us, level_id, senses_list):
                            success += len(senses_list)
                        else:
                            fail += 1
                    else:
                        fail += 1
                except Exception as e:
                    print(f"导入单词 {word} 失败: {e}")
                    fail += 1

            messagebox.showinfo("导入完成", f"成功：{success} 条释义\n失败/重复：{fail} 个单词")
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}")
