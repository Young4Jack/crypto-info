#!/bin/bash
# Crypto-info 本地启动脚本（使用代理服务器模式）

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印函数
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[✓]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }

# 检查并创建虚拟环境
check_venv() {
    if [ ! -d "backend/venv" ]; then
        print_warning "虚拟环境不存在，正在创建..."
        python3 -m venv backend/venv
        source backend/venv/bin/activate
        print_info "安装依赖..."
        pip install -r backend/requirements.txt -q
        print_success "虚拟环境创建完成"
    fi
    source backend/venv/bin/activate
}

# 检查并安装依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 读取 requirements.txt 并检查每个包
    MISSING=0
    while IFS= read -r package; do
        # 跳过空行和注释
        [[ -z "$package" || "$package" =~ ^# ]] && continue
        
        # 提取包名（去掉版本号和特殊字符）
        PKG_NAME=$(echo "$package" | sed 's/[>=<~!].*//' | sed 's/\[.*\]//' | tr '[:upper:]' '[:lower:]')
        
        # 处理特殊情况：Pillow -> PIL, python-jose -> jose, python-multipart -> multipart
        case "$PKG_NAME" in
            pillow) IMPORT_NAME="PIL" ;;
            python-jose) IMPORT_NAME="jose" ;;
            python-multipart) IMPORT_NAME="multipart" ;;
            python-dateutil) IMPORT_NAME="dateutil" ;;
            *) IMPORT_NAME="${PKG_NAME//-/_}" ;;
        esac
        
        # 检查包是否安装
        if ! python -c "import $IMPORT_NAME" 2>/dev/null; then
            print_warning "缺少依赖: $package"
            MISSING=1
        fi
    done < backend/requirements.txt
    
    # 如果有缺失依赖，重新安装
    if [ $MISSING -eq 1 ]; then
        print_warning "发现缺失依赖，正在安装..."
        pip install -r backend/requirements.txt -q
        print_success "依赖安装完成"
    else
        print_success "依赖检查通过"
    fi
}

# 检查并初始化数据库
check_database() {
    if [ ! -f "backend/crypto.db" ]; then
        print_warning "数据库不存在，正在初始化..."
        cd backend
        python -m app.init_db
        cd ..
        print_success "数据库初始化完成"
    fi
}

# 检查前端
check_frontend() {
    if [ ! -d "frontend/dist" ]; then
        print_error "前端未编译"
        echo "    请先运行: cd frontend && npm run build"
        exit 1
    fi
    print_success "前端检查通过"
}

# 检查是否已在运行
check_running() {
    if [ -f ".backend.pid" ]; then
        PID=$(cat .backend.pid)
        if ps -p $PID > /dev/null 2>&1; then
            print_warning "后端服务已在运行 (PID: $PID)"
            exit 1
        fi
    fi
    
    if [ -f ".proxy.pid" ]; then
        PID=$(cat .proxy.pid)
        if ps -p $PID > /dev/null 2>&1; then
            print_warning "代理服务已在运行 (PID: $PID)"
            exit 1
        fi
    fi
}

# 主流程
main() {
    echo ""
    echo "============================================================"
    echo "        Crypto-info 开发环境启动"
    echo "============================================================"
    echo ""
    
    # 1. 检查前端
    check_frontend
    
    # 2. 检查虚拟环境
    check_venv
    
    # 3. 检查依赖
    check_dependencies
    
    # 4. 检查数据库
    check_database
    
    # 5. 强制清理残留进程（不管脚本是否认为在运行）
    pkill -f "python.*run.py" 2>/dev/null
    pkill -f "python.*proxy.py" 2>/dev/null
    rm -f .backend.pid .proxy.pid
    sleep 2
    
    # 6. 读取端口配置
    BACKEND_PORT=$(python -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('backend_port', 8000))" 2>/dev/null || echo "8000")
    FRONTEND_PORT=$(python -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('frontend_port', 5173))" 2>/dev/null || echo "5173")
    
    # 7. 确认端口已释放
    if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "后端端口 $BACKEND_PORT 仍被占用，强制 kill..."
        fuser -k $BACKEND_PORT/tcp 2>/dev/null
        sleep 2
    fi
    if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "前端端口 $FRONTEND_PORT 仍被占用，强制 kill..."
        fuser -k $FRONTEND_PORT/tcp 2>/dev/null
        sleep 2
    fi
    
    # 8. 启动服务
    echo ""
    print_info "启动服务..."
    
    # 启动后端
    cd backend
    nohup python run.py >> ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    echo $BACKEND_PID > .backend.pid
    echo "   后端 PID: $BACKEND_PID"
    
    # 等待后端启动
    sleep 3
    
    # 验证后端是否启动成功
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        print_success "后端服务启动成功 (PID: $BACKEND_PID)"
    else
        print_error "后端服务启动失败，查看日志: cat backend.log"
        exit 1
    fi
    
    # 启动代理
    cd scripts
    nohup python3 proxy.py >> ../proxy.log 2>&1 &
    PROXY_PID=$!
    cd ..
    echo $PROXY_PID > .proxy.pid
    echo "   代理 PID: $PROXY_PID"
    
    # 等待代理启动
    sleep 2
    
    # 验证代理是否启动成功
    if ps -p $PROXY_PID > /dev/null 2>&1; then
        print_success "代理服务启动成功 (PID: $PROXY_PID)"
    else
        print_error "代理服务启动失败，查看日志: cat proxy.log"
        exit 1
    fi
    
    # 获取本机IP
    if [[ "$OSTYPE" == "darwin"* ]]; then
        LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "127.0.0.1")
    else
        LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
    fi
    
    echo ""
    echo "============================================================"
    echo "        ✅ Crypto-info 启动成功！"
    echo "============================================================"
    echo ""
    echo "📍 本地访问: http://localhost:$FRONTEND_PORT"
    echo "📍 局域网访问: http://$LOCAL_IP:$FRONTEND_PORT"
    echo "📚 API文档: http://localhost:$BACKEND_PORT/docs"
    echo ""
    echo "停止服务: ./dev-stop.sh"
    echo "============================================================"
}

main
