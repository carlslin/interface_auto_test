# MySQL环境搭建指南

## 📋 概述

本指南详细介绍了如何为接口自动化测试框架搭建MySQL环境，包括安装、配置、测试和集成等完整流程。

## 🎯 环境要求

### 系统要求
- **操作系统**: macOS 10.14+, Ubuntu 18.04+, CentOS 7+
- **Python版本**: Python 3.8+
- **内存**: 至少1GB可用内存
- **磁盘**: 至少500MB可用空间

### 软件依赖
- **MySQL服务器**: 8.0+
- **Python包**: pymysql>=1.0.0
- **可选**: Docker (用于容器化部署)

## 🚀 快速开始

### 方法1: 使用自动化脚本（推荐）

```bash
# 1. 给脚本执行权限
chmod +x scripts/setup_mysql.sh

# 2. 使用Docker安装（推荐）
./scripts/setup_mysql.sh docker

# 3. 或使用本地安装
./scripts/setup_mysql.sh local

# 4. 运行测试
python3 scripts/test_mysql.py
```

### 方法2: 手动安装

#### macOS安装
```bash
# 使用Homebrew安装
brew install mysql

# 启动MySQL服务
brew services start mysql

# 设置root密码
mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'autotest123';"

# 创建测试数据库和用户
mysql -u root -pautotest123 -e "
    CREATE DATABASE IF NOT EXISTS autotest;
    CREATE USER IF NOT EXISTS 'autotest'@'localhost' IDENTIFIED BY 'autotest123';
    GRANT ALL PRIVILEGES ON autotest.* TO 'autotest'@'localhost';
    FLUSH PRIVILEGES;
"

# 验证安装
mysql -uautotest -pautotest123 -e "SELECT 1;"
```

#### Ubuntu/Debian安装
```bash
# 更新包管理器
sudo apt-get update

# 安装MySQL
sudo apt-get install mysql-server

# 启动MySQL服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全配置
sudo mysql_secure_installation

# 创建测试数据库和用户
sudo mysql -e "
    CREATE DATABASE IF NOT EXISTS autotest;
    CREATE USER IF NOT EXISTS 'autotest'@'localhost' IDENTIFIED BY 'autotest123';
    GRANT ALL PRIVILEGES ON autotest.* TO 'autotest'@'localhost';
    FLUSH PRIVILEGES;
"

# 验证安装
mysql -uautotest -pautotest123 -e "SELECT 1;"
```

#### CentOS/RHEL安装
```bash
# 安装MySQL
sudo yum install mysql-server

# 启动MySQL服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 设置root密码
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'autotest123';"

# 创建测试数据库和用户
sudo mysql -u root -pautotest123 -e "
    CREATE DATABASE IF NOT EXISTS autotest;
    CREATE USER IF NOT EXISTS 'autotest'@'localhost' IDENTIFIED BY 'autotest123';
    GRANT ALL PRIVILEGES ON autotest.* TO 'autotest'@'localhost';
    FLUSH PRIVILEGES;
"

# 验证安装
mysql -uautotest -pautotest123 -e "SELECT 1;"
```

## 🐳 Docker部署

### 基本部署
```bash
# 拉取MySQL镜像
docker pull mysql:8.0

# 启动MySQL容器
docker run -d \
  --name autotest-mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=autotest123 \
  -e MYSQL_DATABASE=autotest \
  -e MYSQL_USER=autotest \
  -e MYSQL_PASSWORD=autotest123 \
  mysql:8.0

# 验证部署
docker exec autotest-mysql mysql -uautotest -pautotest123 -e "SELECT 1;"
```

### 持久化部署
```bash
# 创建数据目录
mkdir -p ./mysql-data

# 启动带持久化的MySQL容器
docker run -d \
  --name autotest-mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=autotest123 \
  -e MYSQL_DATABASE=autotest \
  -e MYSQL_USER=autotest \
  -e MYSQL_PASSWORD=autotest123 \
  -v $(pwd)/mysql-data:/var/lib/mysql \
  mysql:8.0
```

### Docker Compose部署
```yaml
# docker-compose.yml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    container_name: autotest-mysql
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: autotest123
      MYSQL_DATABASE: autotest
      MYSQL_USER: autotest
      MYSQL_PASSWORD: autotest123
    volumes:
      - ./mysql-data:/var/lib/mysql
    restart: unless-stopped
```

```bash
# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps
```

## ⚙️ 配置管理

### 更新项目配置
```bash
# 使用配置更新脚本
python3 scripts/update_mysql_config.py \
  --host localhost \
  --port 3306 \
  --database autotest \
  --username autotest \
  --password autotest123

# 验证配置
python3 scripts/update_mysql_config.py --validate

# 初始化数据库
python3 scripts/update_mysql_config.py --init-db

# 生成配置报告
python3 scripts/update_mysql_config.py --report
```

### 环境特定配置
```bash
# 为不同环境创建配置
python3 scripts/update_mysql_config.py \
  --env dev \
  --host dev-mysql.example.com \
  --port 3306 \
  --database autotest_dev

python3 scripts/update_mysql_config.py \
  --env test \
  --host test-mysql.example.com \
  --port 3306 \
  --database autotest_test

python3 scripts/update_mysql_config.py \
  --env prod \
  --host prod-mysql.example.com \
  --port 3306 \
  --database autotest_prod \
  --password your-secure-password
```

### 配置文件结构
```yaml
# config/default.yaml
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
```

## 🧪 测试验证

### 运行完整测试套件
```bash
# 基本测试
python3 scripts/test_mysql.py

# 详细测试
python3 scripts/test_mysql.py --verbose

# 指定MySQL服务器
python3 scripts/test_mysql.py --host 192.168.1.100 --port 3306
```

### 测试内容
- ✅ MySQL连接测试
- ✅ 基本操作测试（增删改查）
- ✅ 查询构建器测试
- ✅ 事务管理测试
- ✅ 批量操作测试
- ✅ 性能测试
- ✅ 表管理测试
- ✅ 错误处理测试

### 运行使用示例
```bash
# 运行MySQL使用示例
python3 examples/mysql_usage_demo.py
```

## 🔧 高级配置

### MySQL服务器配置
```bash
# 编辑MySQL配置文件
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# 主要配置项
[mysqld]
bind-address = 127.0.0.1
port = 3306
max_connections = 200
innodb_buffer_pool_size = 256M
innodb_log_file_size = 64M
query_cache_size = 32M
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2
```

### 安全配置
```bash
# 设置密码策略
mysql -u root -p -e "
    SET GLOBAL validate_password.policy = STRONG;
    SET GLOBAL validate_password.length = 8;
"

# 创建专用用户
mysql -u root -p -e "
    CREATE USER 'autotest'@'localhost' IDENTIFIED BY 'strong_password';
    GRANT SELECT, INSERT, UPDATE, DELETE ON autotest.* TO 'autotest'@'localhost';
    FLUSH PRIVILEGES;
"
```

### 性能优化
```bash
# 优化InnoDB设置
mysql -u root -p -e "
    SET GLOBAL innodb_buffer_pool_size = 512M;
    SET GLOBAL innodb_log_file_size = 128M;
    SET GLOBAL innodb_flush_log_at_trx_commit = 2;
"

# 优化查询缓存
mysql -u root -p -e "
    SET GLOBAL query_cache_size = 64M;
    SET GLOBAL query_cache_type = ON;
"
```

## 📊 监控和维护

### 基本监控
```bash
# 查看MySQL状态
mysql -u root -p -e "SHOW STATUS;"

# 查看连接信息
mysql -u root -p -e "SHOW PROCESSLIST;"

# 查看数据库大小
mysql -u root -p -e "
    SELECT 
        table_schema AS 'Database',
        ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
    FROM information_schema.tables
    GROUP BY table_schema;
"
```

### 性能监控
```bash
# 查看慢查询
mysql -u root -p -e "SHOW VARIABLES LIKE 'slow_query_log%';"

# 查看慢查询日志
sudo tail -f /var/log/mysql/slow.log

# 查看当前连接
mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';"
```

### 维护操作
```bash
# 优化表
mysql -u root -p -e "OPTIMIZE TABLE autotest.test_cases;"

# 备份数据库
mysqldump -u root -p autotest > autotest_backup.sql

# 恢复数据库
mysql -u root -p autotest < autotest_backup.sql

# 重启服务
sudo systemctl restart mysql
```

## 🚨 故障排除

### 常见问题

#### 1. 连接被拒绝
```bash
# 检查MySQL服务状态
sudo systemctl status mysql

# 检查端口占用
netstat -tlnp | grep 3306

# 检查防火墙
sudo ufw status
```

#### 2. 认证失败
```bash
# 重置root密码
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';"

# 检查用户权限
mysql -u root -p -e "SELECT user, host FROM mysql.user;"
```

#### 3. 性能问题
```bash
# 查看慢查询
mysql -u root -p -e "SHOW VARIABLES LIKE 'slow_query_log%';"

# 查看连接数
mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';"

# 优化配置
mysql -u root -p -e "SET GLOBAL max_connections = 200;"
```

### 日志分析
```bash
# 查看MySQL错误日志
sudo tail -f /var/log/mysql/error.log

# 查看系统日志
sudo journalctl -u mysql -f
```

## 🔒 安全最佳实践

### 1. 网络安全
- 使用防火墙限制访问
- 绑定到特定IP地址
- 使用SSL/TLS加密连接

### 2. 认证安全
- 设置强密码策略
- 定期更换密码
- 使用专用用户和最小权限

### 3. 数据安全
- 启用二进制日志
- 定期备份数据
- 监控异常访问

## 📈 性能调优

### 1. 内存优化
```bash
# 设置合适的缓冲池大小
SET GLOBAL innodb_buffer_pool_size = 512M;

# 优化查询缓存
SET GLOBAL query_cache_size = 64M;
```

### 2. 连接优化
```bash
# 设置最大连接数
SET GLOBAL max_connections = 200;

# 设置连接超时
SET GLOBAL wait_timeout = 600;
```

### 3. 存储优化
```bash
# 优化InnoDB设置
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
SET GLOBAL innodb_log_file_size = 128M;
```

## 🎯 集成测试

### 1. 框架集成测试
```python
# 测试数据库管理器
from src.utils.database_manager import DatabaseManager

config = {
    'database': {
        'type': 'mysql',
        'mysql': {
            'host': 'localhost',
            'port': 3306,
            'database': 'autotest',
            'username': 'autotest',
            'password': 'autotest123'
        }
    }
}

db_manager = DatabaseManager(config)
db_manager.connect()

# 测试基本操作
result = db_manager.execute_query("SELECT 1")
print(result.data)  # 应该输出: [{'1': 1}]
```

### 2. 性能基准测试
```bash
# 运行性能测试
python3 scripts/test_mysql.py --verbose

# 查看测试结果
cat mysql_test_report.md
```

## 📚 参考资源

### 官方文档
- [MySQL官方文档](https://dev.mysql.com/doc/)
- [MySQL命令参考](https://dev.mysql.com/doc/refman/8.0/en/sql-statements.html)
- [MySQL配置参考](https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html)

### 项目文档
- [数据库管理器文档](src/utils/database_manager.py)
- [MySQL使用示例](examples/mysql_usage_demo.py)
- [配置管理脚本](scripts/update_mysql_config.py)

### 社区资源
- [MySQL最佳实践](https://dev.mysql.com/doc/mysql-best-practices/en/)
- [MySQL性能调优](https://dev.mysql.com/doc/refman/8.0/en/optimization.html)
- [MySQL安全指南](https://dev.mysql.com/doc/refman/8.0/en/security.html)

## 🎉 总结

通过本指南，您应该能够：

1. ✅ 成功安装和配置MySQL服务器
2. ✅ 集成MySQL到接口自动化测试框架
3. ✅ 运行完整的测试套件验证功能
4. ✅ 配置环境特定的MySQL设置
5. ✅ 监控和维护MySQL服务
6. ✅ 解决常见的故障问题
7. ✅ 优化MySQL性能和安全

现在您可以开始使用MySQL数据库功能来存储和管理接口自动化测试的数据了！🚀
