#!/bin/bash
# Crypto-info Release 构建脚本
# 用法: ./release.sh [版本号]
# 示例: ./release.sh v1.0.0

set -e

VERSION=${1:-"v1.0.0"}
RELEASE_NAME="crypto-info-${VERSION}"
RELEASE_DIR="release/${RELEASE_NAME}"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo ""
echo "============================================================"
echo "        构建 Release: ${RELEASE_NAME}"
echo "============================================================"
echo ""

# 清理旧的 release 目录
print_info "清理旧文件..."
rm -rf release/
mkdir -p ${RELEASE_DIR}

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    print_info "安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

# 编译前端
print_info "编译前端..."
cd frontend
npm run build
cd ..

# 复制文件
print_info "复制文件..."
cp -r backend ${RELEASE_DIR}/
cp -r frontend/dist ${RELEASE_DIR}/frontend/
cp -r scripts ${RELEASE_DIR}/
cp install.sh ${RELEASE_DIR}/
cp install.bat ${RELEASE_DIR}/
cp README.md ${RELEASE_DIR}/ 2>/dev/null || true

# 清理不需要的文件
print_info "清理临时文件..."
rm -rf ${RELEASE_DIR}/backend/__pycache__
rm -rf ${RELEASE_DIR}/backend/venv
rm -f ${RELEASE_DIR}/backend/*.db
rm -f ${RELEASE_DIR}/backend/*.db-journal
rm -rf ${RELEASE_DIR}/backend/logs
rm -rf ${RELEASE_DIR}/backend/alembic/versions/__pycache__

# 设置脚本权限
chmod +x ${RELEASE_DIR}/install.sh
chmod +x ${RELEASE_DIR}/scripts/*.sh
chmod +x ${RELEASE_DIR}/scripts/crypto-info
chmod +x ${RELEASE_DIR}/scripts/proxy.py

# 打包 Linux/Mac 版本
print_info "打包 Linux/Mac 版本..."
cd release
tar -czf ${RELEASE_NAME}-linux-mac.tar.gz ${RELEASE_NAME}

# 打包 Windows 版本
print_info "打包 Windows 版本..."
if command_exists zip; then
    zip -r ${RELEASE_NAME}-windows.zip ${RELEASE_NAME}
else
    print_info "zip 命令不存在，跳过 Windows 打包"
fi

cd ..

# 计算文件大小
TARBALL_SIZE=$(du -h release/${RELEASE_NAME}-linux-mac.tar.gz | cut -f1)
if [ -f "release/${RELEASE_NAME}-windows.zip" ]; then
    ZIP_SIZE=$(du -h release/${RELEASE_NAME}-windows.zip | cut -f1)
fi

# 生成校验文件
print_info "生成校验文件..."
cd release
sha256sum ${RELEASE_NAME}-linux-mac.tar.gz > checksums.txt 2>/dev/null || shasum -a 256 ${RELEASE_NAME}-linux-mac.tar.gz > checksums.txt
if [ -f "${RELEASE_NAME}-windows.zip" ]; then
    sha256sum ${RELEASE_NAME}-windows.zip >> checksums.txt 2>/dev/null || shasum -a 256 ${RELEASE_NAME}-windows.zip >> checksums.txt
fi
cd ..

# 构建完成
echo ""
echo "============================================================"
echo "        Release 构建完成！"
echo "============================================================"
echo ""
echo "📦 生成的文件:"
echo "   release/${RELEASE_NAME}-linux-mac.tar.gz (${TARBALL_SIZE})"
if [ -f "release/${RELEASE_NAME}-windows.zip" ]; then
    echo "   release/${RELEASE_NAME}-windows.zip (${ZIP_SIZE})"
fi
echo "   release/checksums.txt"
echo ""
echo "📁 Release 目录结构:"
echo "   release/${RELEASE_NAME}/"
ls -la release/${RELEASE_NAME}/
echo ""
echo "============================================================"
echo ""
echo "下一步:"
echo "1. 测试 Release 包"
echo "2. 上传到 GitHub Release"
echo "   gh release create ${VERSION} release/*.tar.gz release/*.zip --title \"${RELEASE_NAME}\" --notes \"Release ${VERSION}\""
echo ""
