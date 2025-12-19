#!/bin/bash
# 查看服务状态脚本

echo "========================================="
echo "  夸克资源站 - 服务状态"
echo "========================================="

if pgrep -f "gunicorn.*app:app" > /dev/null; then
    echo "状态: ✅ 运行中"
    echo ""
    echo "进程信息:"
    ps aux | grep -E "gunicorn.*app:app" | grep -v grep
    echo ""
    echo "端口监听:"
    netstat -tlnp 2>/dev/null | grep -E ":500[0-9]" || ss -tlnp | grep -E ":500[0-9]"
else
    echo "状态: ❌ 未运行"
fi