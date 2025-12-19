#!/bin/bash
# ========================================
# 夸克资源站 - 一键更新重启脚本
# 使用方法: ./update.sh
# ========================================

# 配置
PROJECT_DIR="/opt/quark-share"
VENV_DIR="$PROJECT_DIR/venv"
PORT=5001

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  夸克资源站 - 更新脚本${NC}"
echo -e "${YELLOW}========================================${NC}"

# 进入项目目录
cd $PROJECT_DIR || { echo -e "${RED}错误: 找不到项目目录 $PROJECT_DIR${NC}"; exit 1; }

# 拉取最新代码
echo -e "\n${GREEN}[1/4] 拉取最新代码...${NC}"
git pull
if [ $? -ne 0 ]; then
    echo -e "${RED}错误: Git 拉取失败${NC}"
    exit 1
fi

# 激活虚拟环境并更新依赖
echo -e "\n${GREEN}[2/4] 检查并更新依赖...${NC}"
source $VENV_DIR/bin/activate
pip install -r requirements.txt -q

# 停止旧服务
echo -e "\n${GREEN}[3/4] 停止旧服务...${NC}"
pkill -f "gunicorn.*app:app" 2>/dev/null
sleep 1

# 启动新服务
echo -e "\n${GREEN}[4/4] 启动新服务...${NC}"
gunicorn -w 2 -b 0.0.0.0:$PORT app:app --daemon
sleep 1

# 检查是否启动成功
if pgrep -f "gunicorn.*app:app" > /dev/null; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ 更新完成！服务已在端口 $PORT 运行${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "\n${RED}========================================${NC}"
    echo -e "${RED}❌ 启动失败，请检查日志${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi