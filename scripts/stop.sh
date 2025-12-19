#!/bin/bash
# 停止服务脚本
echo "正在停止服务..."
pkill -f "gunicorn.*app:app"
echo "✅ 服务已停止"