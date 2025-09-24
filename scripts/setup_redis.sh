#!/bin/bash
# =============================================================================
# Redis环境搭建脚本
# =============================================================================
# 
# 本脚本用于在macOS/Linux系统上搭建Redis环境，支持Docker和本地安装两种方式
# 
# 使用方法：
#   chmod +x scripts/setup_redis.sh
#   ./scripts/setup_redis.sh [docker|local]
# 
# 参数说明：
#   docker: 使用Docker安装Redis（推荐）
#   local:  本地安装Redis
# 
# 作者: 接口自动化测试框架团队
# 版本: 1.0.0
# 更新日期: 2024年12月
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统类型
check_system() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        SYSTEM="macos"
        log_info "检测到macOS系统"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        SYSTEM="linux"
        log_info "检测到Linux系统"
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
}

# 检查Docker是否安装
check_docker() {
    if command -v docker &> /dev/null; then
        log_success "Docker已安装"
        return 0
    else
        log_warning "Docker未安装"
        return 1
    fi
}

# 使用Docker安装Redis
install_redis_docker() {
    log_info "使用Docker安装Redis..."
    
    # 检查Docker是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker未运行，请先启动Docker"
        exit 1
    fi
    
    # 拉取Redis镜像
    log_info "拉取Redis镜像..."
    docker pull redis:7-alpine
    
    # 创建Redis数据目录
    mkdir -p ./redis-data
    
    # 启动Redis容器
    log_info "启动Redis容器..."
    docker run -d \
        --name autotest-redis \
        -p 6379:6379 \
        -v $(pwd)/redis-data:/data \
        redis:7-alpine \
        redis-server --appendonly yes
    
    # 等待Redis启动
    log_info "等待Redis启动..."
    sleep 3
    
    # 测试连接
    if docker exec autotest-redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis容器启动成功"
        log_info "Redis连接信息:"
        log_info "  主机: localhost"
        log_info "  端口: 6379"
        log_info "  数据库: 0"
        log_info "  密码: 无"
    else
        log_error "Redis容器启动失败"
        exit 1
    fi
}

# 本地安装Redis (macOS)
install_redis_macos() {
    log_info "在macOS上安装Redis..."
    
    # 检查Homebrew
    if ! command -v brew &> /dev/null; then
        log_error "请先安装Homebrew: https://brew.sh/"
        exit 1
    fi
    
    # 安装Redis
    log_info "使用Homebrew安装Redis..."
    brew install redis
    
    # 启动Redis服务
    log_info "启动Redis服务..."
    brew services start redis
    
    # 测试连接
    if redis-cli ping | grep -q "PONG"; then
        log_success "Redis安装并启动成功"
    else
        log_error "Redis启动失败"
        exit 1
    fi
}

# 本地安装Redis (Linux)
install_redis_linux() {
    log_info "在Linux上安装Redis..."
    
    # 更新包管理器
    if command -v apt-get &> /dev/null; then
        log_info "使用apt-get安装Redis..."
        sudo apt-get update
        sudo apt-get install -y redis-server
    elif command -v yum &> /dev/null; then
        log_info "使用yum安装Redis..."
        sudo yum install -y redis
    else
        log_error "不支持的包管理器，请手动安装Redis"
        exit 1
    fi
    
    # 启动Redis服务
    log_info "启动Redis服务..."
    sudo systemctl start redis
    sudo systemctl enable redis
    
    # 测试连接
    if redis-cli ping | grep -q "PONG"; then
        log_success "Redis安装并启动成功"
    else
        log_error "Redis启动失败"
        exit 1
    fi
}

# 创建Redis配置文件
create_redis_config() {
    log_info "创建Redis配置文件..."
    
    cat > ./config/redis.yaml << EOF
# Redis配置
redis:
  host: "localhost"
  port: 6379
  db: 0
  password: ""
  max_connections: 10
  socket_timeout: 5
  socket_connect_timeout: 5
  retry_on_timeout: true
  health_check_interval: 30
EOF
    
    log_success "Redis配置文件已创建: ./config/redis.yaml"
}

# 测试Redis连接
test_redis_connection() {
    log_info "测试Redis连接..."
    
    # 测试基本连接
    if redis-cli ping | grep -q "PONG"; then
        log_success "Redis连接测试成功"
    else
        log_error "Redis连接测试失败"
        exit 1
    fi
    
    # 测试基本操作
    log_info "测试Redis基本操作..."
    redis-cli set "test:key" "test:value"
    if redis-cli get "test:key" | grep -q "test:value"; then
        log_success "Redis读写测试成功"
    else
        log_error "Redis读写测试失败"
        exit 1
    fi
    
    # 清理测试数据
    redis-cli del "test:key"
    log_info "测试数据已清理"
}

# 显示Redis信息
show_redis_info() {
    log_info "Redis服务信息:"
    echo "  版本: $(redis-cli info server | grep redis_version | cut -d: -f2 | tr -d '\r')"
    echo "  运行模式: $(redis-cli info server | grep redis_mode | cut -d: -f2 | tr -d '\r')"
    echo "  连接数: $(redis-cli info clients | grep connected_clients | cut -d: -f2 | tr -d '\r')"
    echo "  内存使用: $(redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')"
    echo "  键数量: $(redis-cli dbsize)"
}

# 主函数
main() {
    echo "============================================================================="
    echo "Redis环境搭建脚本"
    echo "============================================================================="
    
    # 检查系统
    check_system
    
    # 获取安装方式
    INSTALL_METHOD=${1:-"docker"}
    
    case $INSTALL_METHOD in
        "docker")
            if check_docker; then
                install_redis_docker
            else
                log_error "Docker未安装，无法使用Docker方式安装Redis"
                log_info "请安装Docker或使用本地安装方式: ./scripts/setup_redis.sh local"
                exit 1
            fi
            ;;
        "local")
            if [[ "$SYSTEM" == "macos" ]]; then
                install_redis_macos
            elif [[ "$SYSTEM" == "linux" ]]; then
                install_redis_linux
            fi
            ;;
        *)
            log_error "不支持的安装方式: $INSTALL_METHOD"
            log_info "支持的方式: docker, local"
            exit 1
            ;;
    esac
    
    # 创建配置文件
    create_redis_config
    
    # 测试连接
    test_redis_connection
    
    # 显示信息
    show_redis_info
    
    echo ""
    log_success "Redis环境搭建完成！"
    log_info "接下来可以运行测试脚本: python3 scripts/test_redis.py"
}

# 运行主函数
main "$@"
