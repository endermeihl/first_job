#!/bin/bash

# 小红书视频下载工具启动脚本

echo "================================"
echo "小红书视频下载工具"
echo "================================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3,请先安装Python3"
    exit 1
fi

# 检查依赖是否安装
if [ ! -d "venv" ]; then
    echo "检测到虚拟环境不存在,正在创建..."
    python3 -m venv venv
fi

echo "激活虚拟环境..."
source venv/bin/activate

echo "检查并安装依赖..."
pip install -q -r requirements.txt

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p downloads

# 启动服务
echo ""
echo "================================"
echo "正在启动服务..."
echo "Web界面: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "================================"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
