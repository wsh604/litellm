#!/bin/bash

# 默认值
DEFAULT_HOST="localhost"
DEFAULT_USER="root"
DEFAULT_DIR="/root/app"
DEFAULT_COMPOSE_FILE="docker-compose.wuban.yml"

# 显示使用方法
usage() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -h, --host        服务器地址 (默认: $DEFAULT_HOST)"
    echo "  -u, --user        SSH用户名 (默认: $DEFAULT_USER)"
    echo "  -p, --password    SSH密码 (必需)"
    echo "  -d, --dir         远程部署目录 (默认: $DEFAULT_DIR)"
    echo "  -f, --file        Docker compose文件名 (默认: $DEFAULT_COMPOSE_FILE)"
    echo "  --help            显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 -h 192.168.1.100 -u root -p password123 -d /app"
    exit 1
}

# 检查expect是否安装
if ! command -v expect &> /dev/null; then
    echo "错误: 请先安装expect"
    echo "Ubuntu/Debian: sudo apt-get install expect"
    echo "CentOS: sudo yum install expect"
    echo "MacOS: brew install expect"
    exit 1
fi

# 解析命令行参数
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -h|--host) REMOTE_HOST="$2"; shift ;;
        -u|--user) REMOTE_USER="$2"; shift ;;
        -p|--password) REMOTE_PASS="$2"; shift ;;
        -d|--dir) REMOTE_DIR="$2"; shift ;;
        -f|--file) COMPOSE_FILE="$2"; shift ;;
        --help) usage ;;
        *) echo "未知参数: $1"; usage ;;
    esac
    shift
done

# 检查必需参数
if [ -z "$REMOTE_PASS" ]; then
    echo "错误: 必须提供密码"
    usage
fi

# 设置默认值
REMOTE_HOST=${REMOTE_HOST:-$DEFAULT_HOST}
REMOTE_USER=${REMOTE_USER:-$DEFAULT_USER}
REMOTE_DIR=${REMOTE_DIR:-$DEFAULT_DIR}
COMPOSE_FILE=${COMPOSE_FILE:-$DEFAULT_COMPOSE_FILE}
ARCHIVE_NAME="app.tar.gz"

# 检查compose文件是否存在
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "错误: Docker Compose 文件 '$COMPOSE_FILE' 不存在"
    exit 1
fi

# 显示配置信息
echo "部署配置:"
echo "主机: $REMOTE_HOST"
echo "用户: $REMOTE_USER"
echo "目录: $REMOTE_DIR"
echo "Compose文件: $COMPOSE_FILE"
echo

# 创建部署包
echo "正在创建部署包..."
tar -czf $ARCHIVE_NAME \
    --exclude="node_modules" \
    --exclude=".git" \
    --exclude=$ARCHIVE_NAME \
    --exclude="*.log" \
    .

# 使用expect脚本执行远程操作
echo "开始远程部署..."
./remote_deploy.exp "$REMOTE_HOST" "$REMOTE_USER" "$REMOTE_PASS" "$REMOTE_DIR" "$ARCHIVE_NAME" "$COMPOSE_FILE"
STATUS=$?

# 清理本地打包文件
echo "清理本地文件..."
rm $ARCHIVE_NAME

if [ $STATUS -eq 0 ]; then
    echo "部署完成！"
else
    echo "部署失败！"
    exit 1
fi 