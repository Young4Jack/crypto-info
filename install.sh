#!/bin/bash
# Crypto-info 一键安装脚本（Linux/Mac）
# 适用于预编译的 Release 包
# 用法: chmod +x install.sh && ./install.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_step() {
    echo -e "${CYAN}==>${NC} $1"
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if [ -f /etc/debian_version ]; then
            DISTRO="debian"
        elif [ -f /etc/redhat-release ]; then
            DISTRO="redhat"
        elif [ -f /etc/arch-release ]; then
            DISTRO="arch"
        else
            DISTRO="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="mac"
        DISTRO="macos"
    else
        print_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    print_info "检测到操作系统: $OS ($DISTRO)"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查Python版本
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
            print_success "Python $PYTHON_VERSION 已安装"
            return 0
        else
            print_warning "Python 版本 $PYTHON_VERSION 过低，需要 3.11+"
            return 1
        fi
    else
        print_warning "未检测到 Python"
        return 1
    fi
}

# 安装Python
install_python() {
    print_step "正在安装 Python 3.11+..."

    if [ "$OS" = "mac" ]; then
        if command_exists brew; then
            brew install python@3.11
            if [ ! -f /usr/local/bin/python3 ]; then
                ln -sf /usr/local/opt/python@3.11/bin/python3.11 /usr/local/bin/python3
            fi
        else
            print_error "请先安装 Homebrew: https://brew.sh/"
            exit 1
        fi
    elif [ "$OS" = "linux" ]; then
        if [ "$DISTRO" = "debian" ]; then
            sudo apt-get update
            sudo apt-get install -y software-properties-common
            sudo add-apt-repository -y ppa:deadsnakes/ppa
            sudo apt-get update
            sudo apt-get install -y python3.11 python3.11-venv python3.11-pip
            sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
        elif [ "$DISTRO" = "redhat" ]; then
            sudo dnf install -y python3.11 python3.11-pip
        elif [ "$DISTRO" = "arch" ]; then
            sudo pacman -S --noconfirm python python-pip
        else
            print_error "无法自动安装 Python，请手动安装 Python 3.11+"
            exit 1
        fi
    fi

    if check_python_version; then
        print_success "Python 安装成功"
    else
        print_error "Python 安装失败"
        exit 1
    fi
}

# 检查端口是否被占用
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 1
    fi
    return 0
}

# 配置向导
configure_ports() {
    echo ""
    echo "============================================================"
    echo "        安装配置"
    echo "============================================================"
    echo ""

    # 读取当前配置
    if [ -f "backend/config.json" ]; then
        CURRENT_BACKEND=$(python3 -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('backend_port', 8000))")
        CURRENT_FRONTEND=$(python3 -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('frontend_port', 5173))")
    else
        CURRENT_BACKEND=8000
        CURRENT_FRONTEND=5173
    fi

    echo "📍 当前端口配置："
    echo "   后端 API 端口: $CURRENT_BACKEND"
    echo "   前端 Web 端口: $CURRENT_FRONTEND"
    echo ""

    read -p "是否修改端口配置? (y/n): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        read -p "后端 API 端口 [$CURRENT_BACKEND]: " NEW_BACKEND
        read -p "前端 Web 端口 [$CURRENT_FRONTEND]: " NEW_FRONTEND

        NEW_BACKEND=${NEW_BACKEND:-$CURRENT_BACKEND}
        NEW_FRONTEND=${NEW_FRONTEND:-$CURRENT_FRONTEND}

        # 检查端口是否被占用
        if ! check_port $NEW_BACKEND; then
            print_error "端口 $NEW_BACKEND 已被占用"
            exit 1
        fi

        if ! check_port $NEW_FRONTEND; then
            print_error "端口 $NEW_FRONTEND 已被占用"
            exit 1
        fi

        # 更新配置文件
        python3 << EOF
import json
with open('backend/config.json', 'r') as f:
    config = json.load(f)
config['system_settings']['backend_port'] = $NEW_BACKEND
config['system_settings']['frontend_port'] = $NEW_FRONTEND
with open('backend/config.json', 'w') as f:
    json.dump(config, f, indent=2)
EOF

        echo ""
        print_success "端口配置已更新："
        echo "   后端 API 端口: $NEW_BACKEND"
        echo "   前端 Web 端口: $NEW_FRONTEND"
    else
        # 检查默认端口是否被占用
        if ! check_port $CURRENT_BACKEND; then
            print_error "默认端口 $CURRENT_BACKEND 已被占用，请选择其他端口"
            exit 1
        fi

        if ! check_port $CURRENT_FRONTEND; then
            print_error "默认端口 $CURRENT_FRONTEND 已被占用，请选择其他端口"
            exit 1
        fi

        print_info "使用默认端口配置"
    fi
    echo ""
}

# 安装系统服务
install_service() {
    print_step "安装系统服务..."

    if [ "$OS" = "linux" ]; then
        # 安装 systemd 服务
        sudo cp scripts/crypto-info.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable crypto-info
        print_success "systemd 服务已安装并启用开机自启"
    elif [ "$OS" = "mac" ]; then
        # 安装 launchd 服务
        mkdir -p ~/Library/LaunchAgents
        cp scripts/com.crypto-info.plist ~/Library/LaunchAgents/
        launchctl load ~/Library/LaunchAgents/com.crypto-info.plist
        print_success "launchd 服务已安装并启动"
    fi
}

# 安装命令行工具
install_cli() {
    print_step "安装命令行工具..."

    sudo cp scripts/crypto-info /usr/local/bin/crypto-info
    sudo chmod +x /usr/local/bin/crypto-info

    print_success "命令行工具已安装"
}

# 主安装流程
main() {
    echo ""
    echo "============================================================"
    echo "        Crypto-info 数字货币价格监控系统"
    echo "        一键安装脚本 v1.0.0"
    echo "============================================================"
    echo ""

    # 检测操作系统
    detect_os

    # 设置工作目录
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"

    print_info "工作目录: $(pwd)"
    echo ""

    # 检查是否已安装
    if [ -d "/opt/crypto-info" ]; then
        print_warning "检测到已安装的 Crypto-info"
        read -p "是否重新安装? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "取消安装"
            exit 0
        fi
        # 停止现有服务
        if command_exists crypto-info; then
            crypto-info stop 2>/dev/null || true
        fi
        sudo rm -rf /opt/crypto-info
    fi

    # 检查并安装Python
    if ! check_python_version; then
        read -p "是否自动安装 Python 3.11+? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_python
        else
            print_error "请手动安装 Python 3.11+ 后重新运行此脚本"
            exit 1
        fi
    fi

    # 配置向导
    configure_ports

    # 安装后端依赖
    print_step "安装后端依赖..."
    cd backend

    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        print_info "创建 Python 虚拟环境..."
        python3 -m venv venv
    fi

    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q

    print_success "后端依赖安装完成"
    cd ..

    # 初始化数据库
    print_step "初始化数据库..."
    cd backend
    if [ -f "alembic.ini" ]; then
        alembic upgrade head 2>/dev/null || true
    fi
    python -m app.init_db
    cd ..

    print_success "数据库初始化完成"

    # 复制到安装目录
    print_step "安装到 /opt/crypto-info..."
    sudo mkdir -p /opt/crypto-info
    sudo cp -r . /opt/crypto-info/
    sudo chmod +x /opt/crypto-info/scripts/*.sh
    sudo chmod +x /opt/crypto-info/scripts/crypto-info

    # 创建日志目录
    sudo mkdir -p /opt/crypto-info/backend/logs

    print_success "文件安装完成"

    # 安装系统服务
    install_service

    # 安装命令行工具
    install_cli

    # 获取本机IP
    if [[ "$OS" == "mac" ]]; then
        LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "127.0.0.1")
    else
        LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
    fi

    # 读取端口配置
    BACKEND_PORT=$(python3 -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('backend_port', 8000))")
    FRONTEND_PORT=$(python3 -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('frontend_port', 5173))")

    # 安装完成
    echo ""
    echo "============================================================"
    echo "             ✅ 安装完成！"
    echo "============================================================"
    echo ""
    echo "📍 访问地址:"
    echo "   本地访问: http://localhost:$FRONTEND_PORT"
    echo "   局域网访问: http://$LOCAL_IP:$FRONTEND_PORT"
    echo "   API文档: http://localhost:$BACKEND_PORT/docs"
    echo ""
    echo "🔧 服务管理命令:"
    echo "   crypto-info start    - 启动服务"
    echo "   crypto-info stop     - 停止服务"
    echo "   crypto-info restart  - 重启服务"
    echo "   crypto-info status   - 查看状态"
    echo "   crypto-info logs     - 查看日志"
    if [ "$OS" = "linux" ]; then
        echo "   crypto-info enable   - 开机自启"
        echo "   crypto-info disable  - 关闭自启"
    fi
    echo ""
    echo "🔐 默认账户:"
    echo "   邮箱: admin@crypto.local"
    echo "   用户名: admin"
    echo "   密码: admin123"
    echo ""
    echo "⚠️  请登录后立即修改默认密码！"
    echo "============================================================"
    echo ""

    # 询问是否立即启动
    read -p "是否立即启动服务? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        if [ "$OS" = "linux" ]; then
            sudo systemctl start crypto-info
        elif [ "$OS" = "mac" ]; then
            /opt/crypto-info/scripts/wrapper.sh &
        fi
        sleep 3
        crypto-info status
    fi
}

# 运行主函数
main
