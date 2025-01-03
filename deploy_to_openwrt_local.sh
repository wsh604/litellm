#!/bin/bash

# 设置错误时退出
set -e

# 定义帮助信息
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -s, --skip-build    Skip image building step"
    echo "  -k, --skip-save     Skip image saving step"
    echo "  -h, --help          Show this help message"
}

# 初始化参数
SKIP_BUILD=false
SKIP_SAVE=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -k|--skip-save)
            SKIP_SAVE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# 加载环境变量
if [ -f "deploy.env" ]; then
    eval $(grep -v '^#' deploy.env | sed 's/[[:space:]]*#.*$//' | xargs -0)
else
    echo "Error: deploy.env file not found!"
    exit 1
fi

echo "Starting deployment process..."

# 1. 本地构建镜像
if [ "$SKIP_BUILD" = false ]; then
    echo "Building Docker image..."
    docker buildx build --platform linux/arm64 --load -t litellm-microcache -f Dockerfile.wuban_arm64 .
else
    echo "Skipping build step..."
fi

# 2. 保存镜像到文件
if [ "$SKIP_SAVE" = false ]; then
    echo "Saving image to file..."
    docker save litellm-microcache > litellm-microcache.tar
else
    echo "Skipping save step..."
    # 检查文件是否存在
    if [ ! -f "litellm-microcache.tar" ]; then
        echo "Error: litellm-microcache.tar not found!"
        exit 1
    fi
fi

# 3. 分块传输镜像到 OpenWrt
echo "Copying image to OpenWrt..."
FILE_SIZE=$(stat -f %z litellm-microcache.tar)
# 转换文件大小为人类可读格式
HUMAN_SIZE=$(echo "scale=2; $FILE_SIZE/1024/1024" | bc)
echo "Image size: ${HUMAN_SIZE}MB"

# 设置分块大小(100MB)和临时目录
CHUNK_SIZE=$((100*1024*1024))
CHUNKS_COUNT=$((($FILE_SIZE + $CHUNK_SIZE - 1)/$CHUNK_SIZE))
TEMP_DIR="/tmp/litellm_chunks"
mkdir -p $TEMP_DIR

echo "Splitting image into $CHUNKS_COUNT chunks..."
split -b $CHUNK_SIZE litellm-microcache.tar "$TEMP_DIR/chunk_"

# 创建远程临时目录
sshpass -p "$OPENWRT_PASSWORD" ssh -o StrictHostKeyChecking=no root@$OPENWRT_HOST "mkdir -p /tmp/litellm_chunks"

# 传输每个分块
total_chunks=$(ls $TEMP_DIR/chunk_* | wc -l)
current_chunk=0

for chunk in $TEMP_DIR/chunk_*; do
    current_chunk=$((current_chunk + 1))
    chunk_name=$(basename $chunk)
    echo "Transferring chunk $current_chunk of $total_chunks..."
    
    sshpass -p "$OPENWRT_PASSWORD" scp -v $chunk root@$OPENWRT_HOST:/tmp/litellm_chunks/$chunk_name
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to transfer chunk $chunk_name"
        exit 1
    fi
done

# 在远程主机上合并文件
echo "Merging chunks on remote host..."
sshpass -p "$OPENWRT_PASSWORD" ssh -o StrictHostKeyChecking=no root@$OPENWRT_HOST "
    cat /tmp/litellm_chunks/chunk_* > /tmp/litellm-microcache.tar
    rm -rf /tmp/litellm_chunks
"

# 验证文件大小
REMOTE_SIZE=$(sshpass -p "$OPENWRT_PASSWORD" ssh -o StrictHostKeyChecking=no root@$OPENWRT_HOST "stat -c%s /tmp/litellm-microcache.tar")
if [ "$FILE_SIZE" = "$REMOTE_SIZE" ]; then
    echo "File transfer completed and verified successfully"
    # 清理本地临时文件
    rm -rf $TEMP_DIR
else
    echo "Error: File size mismatch!"
    echo "Local size: $FILE_SIZE"
    echo "Remote size: $REMOTE_SIZE"
    exit 1
fi

# 4. 在 OpenWrt 上加载和运行镜像
echo "Deploying to OpenWrt..."
sshpass -p "$OPENWRT_PASSWORD" ssh -o StrictHostKeyChecking=no root@$OPENWRT_HOST << EOF
    # 加载镜像
    echo "Loading image on OpenWrt..."
    docker load < /tmp/litellm-microcache.tar
    rm /tmp/litellm-microcache.tar

    # 停止并删除旧容器
    echo "Stopping and removing old container..."
    docker stop litellm 2>/dev/null || true
    docker rm litellm 2>/dev/null || true

    # 启动新容器
    docker run -d \
        --name litellm \
        --network host \
        --add-host=host.docker.internal:host-gateway \
        -v /homateos/data/app/litemllm/config/lite_config.yaml:/app/lite_config.yaml \
        -v /homateos/data/app/litemllm/sqlite:/app/sqlite \
        -v /homateos/data/app/litemllm/files:/app/files \
        -e DATABASE_URL="$DATABASE_URL" \
        -e STORE_MODEL_IN_DB="$STORE_MODEL_IN_DB" \
        -e WUBAN_RPC_URL="$WUBAN_RPC_URL" \
        -e FILE_UPLOAD_BASE_DIR="$FILE_UPLOAD_BASE_DIR" \
        -e PORT=$PORT \
        -e OPENAI_API_KEY="$OPENAI_API_KEY" \
        -e TOGETHER_API_KEY="$TOGETHER_API_KEY" \
        -e LITELLM_MASTER_KEY="$LITELLM_MASTER_KEY" \
        -e LITELLM_SALT_KEY="$LITELLM_SALT_KEY" \
        -e LITELLM_API_KEY="$LITELLM_API_KEY" \
        -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
        -e ZHIPU_API_KEY="$ZHIPU_API_KEY" \
        -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
        --restart always \
        litellm-microcache \
        --config /app/lite_config.yaml

    # 监控启动过程
    echo "Monitoring container startup..."
    TIMEOUT=60
    START_TIME=$(date +%s)
    
    while true; do
        if docker logs -f litellm 2>&1 | grep -q "Application startup complete"; then
            echo "Service started successfully!"
            if docker logs -f litellm 2>&1 | grep -q "Uvicorn running on http://0.0.0.0:4000"; then
                echo "Service is ready to accept connections!"
                break
            fi
        fi
        
        CURRENT_TIME=$(date +%s)
        if [ $((CURRENT_TIME - START_TIME)) -gt $TIMEOUT ]; then
            echo "Service startup timed out after $TIMEOUT seconds"
            echo "Last few lines of logs:"
            docker logs --tail 50 litellm
            exit 1
        fi
        
        sleep 1
    done

    # 检查容器状态
    CONTAINER_STATUS=$(docker inspect -f '{{.State.Status}}' litellm)
    if [ "$CONTAINER_STATUS" != "running" ]; then
        echo "Container is not running. Status: $CONTAINER_STATUS"
        echo "Container logs:"
        docker logs litellm
        exit 1
    fi
    
    echo "Deployment completed successfully!"
EOF

# 5. 清理本地临时文件
rm litellm-microcache.tar

# 检查部署结果
if [ $? -eq 0 ]; then
    echo "Deployment completed successfully!"
else
    echo "Deployment failed!"
    exit 1
fi