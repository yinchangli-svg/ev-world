"""语音合成模块 - 文本转语音"""
import platform
import subprocess
import pyttsx3


class TextToSpeech:
    """文本转语音引擎"""

    def __init__(self):
        self.engine = None
        self.system = platform.system()

        # macOS 使用原生 say 命令，性能更好
        if self.system == 'Darwin':
            self.use_native = True
            print("✅ 使用 macOS 原生语音引擎 (say)")
        else:
            self.use_native = False
            try:
                self.engine = pyttsx3.init()
                print("✅ 使用 pyttsx3 语音引擎")
            except Exception as e:
                print(f"⚠️ pyttsx3 初始化失败: {e}")
                self.engine = None

    def speak(self, text):
        """朗读文本

        Args:
            text: 要朗读的文本
        """
        if not text or not text.strip():
            return

        text = text.strip()

        if self.use_native:
            # macOS 原生 say 命令
            try:
                subprocess.run(['say', text], check=True,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"❌ 语音播放失败: {e}")
        else:
            # pyttsx3 引擎
            if self.engine:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"❌ 语音播放失败: {e}")


# 全局单例
_tts_engine = None


def _get_tts_engine():
    """获取全局 TTS 引擎单例"""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TextToSpeech()
    return _tts_engine


def speak_word(text):
    """便捷函数：朗读单词/文本

    Args:
        text: 要朗读的文本
    """
    engine = _get_tts_engine()
    engine.speak(text)
