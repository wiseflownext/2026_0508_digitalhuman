#!/bin/bash
set -e

PROJECT_NAME="digitalhuman"
DEPLOY_DIR="/opt/digitalhuman/server"

echo "[rollback] 开始回滚 ${PROJECT_NAME}"

# 1. 查历史镜像
echo "[rollback] 可用镜像版本："
docker images | grep ${PROJECT_NAME} | grep -v latest

# 2. 获取最新非 latest 的 tag
LAST_TAG=$(docker images | grep ${PROJECT_NAME} | grep -v latest | awk '{print $2}' | head -1)
if [ -z "$LAST_TAG" ]; then
  echo "[rollback] ❌ 没有找到可回滚的镜像版本"
  exit 1
fi

echo "[rollback] 准备回滚到: ${PROJECT_NAME}:${LAST_TAG}"

# 3. 切换镜像 tag
docker tag ${PROJECT_NAME}:${LAST_TAG} ${PROJECT_NAME}:latest

# 4. 重启服务
cd "$DEPLOY_DIR" || { echo "[rollback] 目录不存在: $DEPLOY_DIR"; exit 1; }
docker-compose down
docker-compose up -d
echo "[rollback] ✅ 回滚完成，当前版本: ${LAST_TAG}"
