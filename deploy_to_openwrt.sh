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

# 使用环境变量
VERSION=${1:-$LITELLM_VERSION}
REGISTRY=$ALIYUN_REGISTRY
FULL_IMAGE_NAME="$REGISTRY/xmren/litellm-arm64:$VERSION"

echo "Starting deployment process..."
echo "Using version: $VERSION"

# 构建和推送镜像
echo "Building Docker image..."
docker buildx build --platform linux/arm64 --load -t litellm-microcache -f Dockerfile.wuban_arm64 .

echo "Logging into Aliyun Container Registry..."
echo "$ALIYUN_PASSWORD" | docker login --username=$ALIYUN_USERNAME $REGISTRY --password-stdin

# 3. 标记镜像
echo "Tagging image..."
docker tag litellm-microcache $FULL_IMAGE_NAME

# 4. 推送到阿里云
echo "Pushing image to Aliyun..."
docker push $FULL_IMAGE_NAME

# 5. 部署到 OpenWrt
echo "Deploying to OpenWrt..."
sshpass -p "$OPENWRT_PASSWORD" ssh -o StrictHostKeyChecking=no root@$OPENWRT_HOST << EOF

# 登录阿里云容器镜像服务
echo "Logging into Aliyun Container Registry on OpenWrt..."
docker login --username=$ALIYUN_USERNAME --password=$ALIYUN_PASSWORD $REGISTRY

# 拉取最新镜像
echo "Pulling latest image..."
docker pull $FULL_IMAGE_NAME

# 停止并删除旧容器
echo "Stopping and removing old container..."
docker stop litellm 2>/dev/null || true
docker rm litellm 2>/dev/null || true

# 使用环境变量启动容器
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
        $FULL_IMAGE_NAME \
        --config /app/lite_config.yaml

    # 启动容器后监控日志
    echo "Monitoring container startup..."
    TIMEOUT=60  # 设置超时时间为60秒
    START_TIME=$(date +%s)
    
    # 使用 docker logs -f 监控启动日志
    while true; do
        if docker logs -f litellm 2>&1 | grep -q "Application startup complete"; then
            echo "Service started successfully!"
            if docker logs -f litellm 2>&1 | grep -q "Uvicorn running on http://0.0.0.0:4000"; then
                echo "Service is ready to accept connections!"
                break
            fi
        fi
        
        # 检查是否超时
        CURRENT_TIME=$(date +%s)
        if [ $((CURRENT_TIME - START_TIME)) -gt $TIMEOUT ]; then
            echo "Service startup timed out after $TIMEOUT seconds"
            echo "Last few lines of logs:"
            docker logs --tail 50 litellm
            exit 1
        fi
        
        sleep 1
    done
    
    # 最后检查容器状态
    CONTAINER_STATUS=$(docker inspect -f '{{.State.Status}}' litellm)
    if [ "$CONTAINER_STATUS" != "running" ]; then
        echo "Container is not running. Status: $CONTAINER_STATUS"
        echo "Container logs:"
        docker logs litellm
        exit 1
    fi
    
    echo "Deployment completed successfully!"
EOF

# 检查 SSH 命令的返回值
if [ $? -eq 0 ]; then
    echo "Deployment completed successfully!"
else
    echo "Deployment failed!"
    exit 1
fi