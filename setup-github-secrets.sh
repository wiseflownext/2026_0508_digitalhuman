#!/bin/bash
# GitHub Secrets 配置脚本 - 数字人项目
# 运行方式: bash setup-github-secrets.sh
# 前提: gh auth login

set -e

REPO="wiseflownext/2026_0508_digitalhuman"

echo "=== GitHub Secrets 配置脚本 ==="
echo "仓库: $REPO"
echo ""

# 1. SERVER_HOST
echo "[1/5] SERVER_HOST"
gh secret set SERVER_HOST -r "$REPO" -v "121.40.172.33"

# 2. SERVER_SSH_KEY (从本机 ~/.ssh/id_ed25519_wiseflownext 读取)
echo "[2/5] SERVER_SSH_KEY"
SSH_KEY_FILE="$HOME/.ssh/id_ed25519_wiseflownext"
if [ ! -f "$SSH_KEY_FILE" ]; then
  echo "❌ 找不到 SSH 私钥: $SSH_KEY_FILE"
  echo "请手动上传私钥内容到 GitHub Secrets > SERVER_SSH_KEY"
else
  KEY_CONTENT=$(cat "$SSH_KEY_FILE")
  gh secret set SERVER_SSH_KEY -r "$REPO" --body "$KEY_CONTENT"
fi

# 3. ARK_API_KEY
echo "[3/5] ARK_API_KEY (火山引擎 API Key)"
echo -n "请输入 ARK_API_KEY: "
read -s ARK_API_KEY
echo ""
gh secret set ARK_API_KEY -r "$REPO" -v "$ARK_API_KEY"

# 4. ARK_SEEDANCE_ENDPOINT
echo "[4/5] ARK_SEEDANCE_ENDPOINT"
echo -n "请输入 ARK_SEEDANCE_ENDPOINT: "
read -s ENDPOINT
echo ""
gh secret set ARK_SEEDANCE_ENDPOINT -r "$REPO" -v "$ENDPOINT"

# 5. OSS
echo "[5/5] OSS_ACCESS_KEY_ID"
echo -n "OSS_ACCESS_KEY_ID: "
read -s OSS_ID
echo ""
gh secret set OSS_ACCESS_KEY_ID -r "$REPO" -v "$OSS_ID"

echo "OSS_ACCESS_KEY_SECRET"
echo -n "OSS_ACCESS_KEY_SECRET: "
read -s OSS_SECRET
echo ""
gh secret set OSS_ACCESS_KEY_SECRET -r "$REPO" -v "$OSS_SECRET"

echo ""
echo "✅ GitHub Secrets 配置完成！"
echo ""
echo "下一步: 访问 https://github.com/$REPO/settings/branches"
echo "  - 为 master 分支添加 Branch Protection Rule"
echo "  - 开启 Require pull request before merging"
