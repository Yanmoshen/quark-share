#!/bin/bash
# 启动服务脚本
PROJECT_DIR="/opt/quark-share"
PORT=5001

cd $PROJECT_DIR
source venv/bin/activate

echo "正在启动服务..."
gunicorn -w 2 -b 0.0.0.0:$PORT app:app --daemon

if pgrep -f "gunicorn.*app:app" > /dev/null; then
    echo "✅ 服务已启动，端口: $PORT"
else
    echo "❌ 启动失败"
fi