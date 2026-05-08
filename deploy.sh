#!/bin/bash
set -e

PROJECT_NAME="digitalhuman"
DEPLOY_DIR="/opt/digitalhuman/server"
PORT=18092
HEALTH_URL="http://localhost:${PORT}/api/health"
MAX_WAIT=60

echo "[deploy] 开始部署 ${PROJECT_NAME}"

# 1. 进入部署目录
cd "$DEPLOY_DIR" || { echo "[deploy] 目录不存在: $DEPLOY_DIR"; exit 1; }

# 2. git 配置（ubuntu 用户需要）
sudo -u ubuntu git config --global user.email "deploy@wiseflownext.com"
sudo -u ubuntu git config --global user.name "Deploy Bot"

# 3. 切换 master 并拉取最新代码
sudo -u ubuntu git checkout master
sudo -u ubuntu git pull origin master

# 4. 构建 Docker 镜像
sudo docker build -t ${PROJECT_NAME}:latest .
TAG=$(date +%Y%m%d-%H%M%S)
sudo docker tag ${PROJECT_NAME}:latest ${PROJECT_NAME}:${TAG}
echo "[deploy] 镜像构建完成: ${PROJECT_NAME}:${TAG}"

# 5. 重启服务
cd "$DEPLOY_DIR"
sudo docker-compose down || true
sudo docker-compose up -d
echo "[deploy] 容器启动完成"

# 6. 健康检查
echo "[deploy] 等待服务就绪（最多 ${MAX_WAIT}s）..."
for i in $(seq 1 $MAX_WAIT); do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ]; then
    echo "[deploy] ✅ 健康检查通过 (HTTP 200)"
    exit 0
  fi
  echo "[deploy] 等待中... $((i*2))s (HTTP $HTTP_CODE)"
  sleep 2
done

echo "[deploy] ❌ 健康检查失败（${MAX_WAIT}s 内未响应）"
sudo docker logs ${PROJECT_NAME}-server --tail 20
exit 1
