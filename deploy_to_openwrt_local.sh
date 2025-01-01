#!/bin/bash

# 设置错误时退出
set -e

# 加载环境变量
if [ -f "deploy.env" ]; then
    # 只加载非注释行且包含等号的行
    eval $(grep -v '^#' deploy.env | sed 's/[[:space:]]*#.*$//' | xargs -0)
else
    echo "Error: deploy.env file not found!"
    exit 1
fi

echo "Starting deployment process..."

# 1. 本地构建镜像
echo "Building Docker image..."
docker buildx build --platform linux/arm64 --load -t litellm-microcache -f Dockerfile.wuban_arm64 .

# 2. 保存镜像到文件
echo "Saving image to file..."
docker save litellm-microcache > litellm-microcache.tar

# 3. 传输镜像到 OpenWrt
echo "Copying image to OpenWrt..."
sshpass -p "$OPENWRT_PASSWORD" scp litellm-microcache.tar root@$OPENWRT_HOST:/tmp/

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