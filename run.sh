#/bin/sh
# 创建python本地环境
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi
source venv/bin/activate
# 安装依赖1
pip install -r requirements.txt
# 添加本地.env
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp ./litellm/proxy/.env.example ./litellm/proxy/.env
fi
# 配置测试数据库 local_debug/dev.db是否存在
if [ ! -f local_debug/dev.db ]; then
    echo "Creating local_debug/dev.db..."
    mkdir -p local_debug
    mkdir -p local/files
    touch local_debug/dev.db
    echo "DATABASE_URL=file:$(pwd)/local_debug/dev.db" >> ./litellm/proxy/.env
    echo "FILE_UPLOAD_BASE_DIR=$(pwd)/local_debug/files/" >> ./litellm/proxy/.env
fi
# 安装完python环境后，执行下面这个命令即可。
python -m litellm.proxy.proxy_cli --config ./litellm/proxy/config.yaml