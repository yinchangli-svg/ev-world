#!/bin/bash

# Wordix 单词学习系统 - 启动脚本
# 适用于 macOS 和 Linux

echo "=========================================="
echo "  Wordix 单词学习系统 v1.4.1"
echo "=========================================="
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    echo "请先安装 Python 3.x: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"
echo ""

# 进入脚本所在目录（确保数据库在正确位置创建）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 工作目录: $(pwd)"
echo ""

# 检查依赖
echo "📦 检查依赖..."
python3 -c "import tkinter" 2>/dev/null || {
    echo "❌ 错误: 缺少 tkinter 模块"
    echo "macOS 用户请执行: brew install python-tk"
    exit 1
}

python3 -c "import pandas" 2>/dev/null || {
    echo "⚠️  警告: 缺少 pandas 模块，正在安装..."
    pip3 install pandas openpyxl pyttsx3
}

python3 -c "import pyttsx3" 2>/dev/null || {
    echo "⚠️  警告: 缺少 pyttsx3 模块，正在安装..."
    pip3 install pyttsx3
}

echo "✅ 依赖检查完成"
echo ""

# 启动应用
echo "🚀 启动 Wordix..."
echo "=========================================="
python3 word_app.py

# 检查退出状态
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 程序正常退出"
else
    echo ""
    echo "❌ 程序异常退出，退出码: $?"
fi
