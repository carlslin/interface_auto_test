#!/bin/bash
# =============================================================================
# MySQL环境搭建脚本
# =============================================================================
# 
# 本脚本用于在macOS/Linux系统上搭建MySQL环境，支持Docker和本地安装两种方式
# 
# 使用方法：
#   chmod +x scripts/setup_mysql.sh
#   ./scripts/setup_mysql.sh [docker|local]
# 
# 参数说明：
#   docker: 使用Docker安装MySQL（推荐）
#   local:  本地安装MySQL
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

# 使用Docker安装MySQL
install_mysql_docker() {
    log_info "使用Docker安装MySQL..."
    
    # 检查Docker是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker未运行，请先启动Docker"
        exit 1
    fi
    
    # 拉取MySQL镜像
    log_info "拉取MySQL镜像..."
    docker pull mysql:8.0
    
    # 创建MySQL数据目录
    mkdir -p ./mysql-data
    
    # 启动MySQL容器
    log_info "启动MySQL容器..."
    docker run -d \
        --name autotest-mysql \
        -p 3306:3306 \
        -e MYSQL_ROOT_PASSWORD=autotest123 \
        -e MYSQL_DATABASE=autotest \
        -e MYSQL_USER=autotest \
        -e MYSQL_PASSWORD=autotest123 \
        -v $(pwd)/mysql-data:/var/lib/mysql \
        mysql:8.0
    
    # 等待MySQL启动
    log_info "等待MySQL启动..."
    sleep 30
    
    # 测试连接
    if docker exec autotest-mysql mysql -uautotest -pautotest123 -e "SELECT 1;" &> /dev/null; then
        log_success "MySQL容器启动成功"
        log_info "MySQL连接信息:"
        log_info "  主机: localhost"
        log_info "  端口: 3306"
        log_info "  数据库: autotest"
        log_info "  用户名: autotest"
        log_info "  密码: autotest123"
        log_info "  根用户密码: autotest123"
    else
        log_error "MySQL容器启动失败"
        exit 1
    fi
}

# 本地安装MySQL (macOS)
install_mysql_macos() {
    log_info "在macOS上安装MySQL..."
    
    # 检查Homebrew
    if ! command -v brew &> /dev/null; then
        log_error "请先安装Homebrew: https://brew.sh/"
        exit 1
    fi
    
    # 安装MySQL
    log_info "使用Homebrew安装MySQL..."
    brew install mysql
    
    # 启动MySQL服务
    log_info "启动MySQL服务..."
    brew services start mysql
    
    # 等待服务启动
    sleep 5
    
    # 设置root密码
    log_info "设置MySQL root密码..."
    mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'autotest123';" 2>/dev/null || true
    
    # 创建测试数据库和用户
    log_info "创建测试数据库和用户..."
    mysql -u root -pautotest123 -e "
        CREATE DATABASE IF NOT EXISTS autotest;
        CREATE USER IF NOT EXISTS 'autotest'@'localhost' IDENTIFIED BY 'autotest123';
        GRANT ALL PRIVILEGES ON autotest.* TO 'autotest'@'localhost';
        FLUSH PRIVILEGES;
    " 2>/dev/null || true
    
    # 测试连接
    if mysql -uautotest -pautotest123 -e "SELECT 1;" &> /dev/null; then
        log_success "MySQL安装并启动成功"
    else
        log_error "MySQL启动失败"
        exit 1
    fi
}

# 本地安装MySQL (Linux)
install_mysql_linux() {
    log_info "在Linux上安装MySQL..."
    
    # 更新包管理器
    if command -v apt-get &> /dev/null; then
        log_info "使用apt-get安装MySQL..."
        sudo apt-get update
        sudo apt-get install -y mysql-server
    elif command -v yum &> /dev/null; then
        log_info "使用yum安装MySQL..."
        sudo yum install -y mysql-server
    else
        log_error "不支持的包管理器，请手动安装MySQL"
        exit 1
    fi
    
    # 启动MySQL服务
    log_info "启动MySQL服务..."
    sudo systemctl start mysql
    sudo systemctl enable mysql
    
    # 设置root密码
    log_info "设置MySQL root密码..."
    sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'autotest123';" 2>/dev/null || true
    
    # 创建测试数据库和用户
    log_info "创建测试数据库和用户..."
    sudo mysql -u root -pautotest123 -e "
        CREATE DATABASE IF NOT EXISTS autotest;
        CREATE USER IF NOT EXISTS 'autotest'@'localhost' IDENTIFIED BY 'autotest123';
        GRANT ALL PRIVILEGES ON autotest.* TO 'autotest'@'localhost';
        FLUSH PRIVILEGES;
    " 2>/dev/null || true
    
    # 测试连接
    if mysql -uautotest -pautotest123 -e "SELECT 1;" &> /dev/null; then
        log_success "MySQL安装并启动成功"
    else
        log_error "MySQL启动失败"
        exit 1
    fi
}

# 创建MySQL配置文件
create_mysql_config() {
    log_info "创建MySQL配置文件..."
    
    cat > ./config/mysql.yaml << EOF
# MySQL数据库配置
database:
  type: "mysql"
  mysql:
    host: "localhost"
    port: 3306
    database: "autotest"
    username: "autotest"
    password: "autotest123"
    charset: "utf8mb4"
    max_connections: 20
    connect_timeout: 10
    read_timeout: 30
    write_timeout: 30
    autocommit: true
    pool_size: 10
    pool_recycle: 3600
    pool_pre_ping: true
EOF
    
    log_success "MySQL配置文件已创建: ./config/mysql.yaml"
}

# 测试MySQL连接
test_mysql_connection() {
    log_info "测试MySQL连接..."
    
    # 测试基本连接
    if mysql -uautotest -pautotest123 -e "SELECT 1;" &> /dev/null; then
        log_success "MySQL连接测试成功"
    else
        log_error "MySQL连接测试失败"
        exit 1
    fi
    
    # 测试基本操作
    log_info "测试MySQL基本操作..."
    mysql -uautotest -pautotest123 -e "
        USE autotest;
        CREATE TABLE IF NOT EXISTS test_table (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        INSERT INTO test_table (name) VALUES ('test');
        SELECT * FROM test_table;
        DROP TABLE test_table;
    " &> /dev/null
    
    if [ $? -eq 0 ]; then
        log_success "MySQL读写测试成功"
    else
        log_error "MySQL读写测试失败"
        exit 1
    fi
    
    log_info "测试数据已清理"
}

# 显示MySQL信息
show_mysql_info() {
    log_info "MySQL服务信息:"
    echo "  版本: $(mysql -uautotest -pautotest123 -e "SELECT VERSION();" -s -N 2>/dev/null || echo 'Unknown')"
    echo "  数据库: autotest"
    echo "  用户: autotest"
    echo "  连接数: $(mysql -uautotest -pautotest123 -e "SHOW STATUS LIKE 'Threads_connected';" -s -N 2>/dev/null | awk '{print $2}' || echo 'Unknown')"
    echo "  运行时间: $(mysql -uautotest -pautotest123 -e "SHOW STATUS LIKE 'Uptime';" -s -N 2>/dev/null | awk '{print $2}' || echo 'Unknown')"
}

# 主函数
main() {
    echo "============================================================================="
    echo "MySQL环境搭建脚本"
    echo "============================================================================="
    
    # 检查系统
    check_system
    
    # 获取安装方式
    INSTALL_METHOD=${1:-"docker"}
    
    case $INSTALL_METHOD in
        "docker")
            if check_docker; then
                install_mysql_docker
            else
                log_error "Docker未安装，无法使用Docker方式安装MySQL"
                log_info "请安装Docker或使用本地安装方式: ./scripts/setup_mysql.sh local"
                exit 1
            fi
            ;;
        "local")
            if [[ "$SYSTEM" == "macos" ]]; then
                install_mysql_macos
            elif [[ "$SYSTEM" == "linux" ]]; then
                install_mysql_linux
            fi
            ;;
        *)
            log_error "不支持的安装方式: $INSTALL_METHOD"
            log_info "支持的方式: docker, local"
            exit 1
            ;;
    esac
    
    # 创建配置文件
    create_mysql_config
    
    # 测试连接
    test_mysql_connection
    
    # 显示信息
    show_mysql_info
    
    echo ""
    log_success "MySQL环境搭建完成！"
    log_info "接下来可以运行测试脚本: python3 scripts/test_mysql.py"
}

# 运行主函数
main "$@"
