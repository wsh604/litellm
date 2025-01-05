#!/bin/bash

echo "Starting Prisma reset process..."

# 1. 删除所有生成的文件
echo "Cleaning up generated files..."
rm -rf venv/lib/python3.10/site-packages/prisma
rm -rf .prisma
rm -rf ~/.cache/prisma-python

# 2. 卸载 prisma
echo "Uninstalling prisma..."
venv/bin/pip uninstall -y prisma

# 3. 重新安装 prisma
echo "Reinstalling prisma..."
venv/bin/pip install prisma

# 4. 进入 schema 所在目录
echo "Changing to schema directory..."
cd litellm/proxy

# 5. 重新生成 prisma 文件
echo "Regenerating Prisma files..."
../../venv/bin/python -m prisma generate
../../venv/bin/python -m prisma db push --accept-data-loss

# 6. 返回根目录
cd ../..

# 重新生成 Prisma client
prisma generate
# 如果需要重新应用数据库迁移
prisma migrate reset --force
prisma migrate dev --name optional_models

echo "Prisma reset completed!" 