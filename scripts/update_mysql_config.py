#!/usr/bin/env python3
"""
=============================================================================
MySQL配置更新脚本
=============================================================================

本脚本用于更新项目配置文件中的MySQL设置，支持：
- 更新默认配置文件中的MySQL配置
- 创建环境特定的MySQL配置
- 验证MySQL配置的有效性
- 生成MySQL连接测试报告
- 数据库初始化和管理

使用方法：
    python3 scripts/update_mysql_config.py [--host HOST] [--port PORT] [--database DATABASE] [--username USERNAME] [--password PASSWORD]

参数说明：
    --host: MySQL主机地址，默认localhost
    --port: MySQL端口，默认3306
    --database: 数据库名，默认autotest
    --username: 用户名，默认autotest
    --password: 密码，默认autotest123
    --env: 目标环境，可选值：dev, test, prod
    --init-db: 初始化数据库

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import sys
import yaml
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.database_manager import DatabaseManager


class MySQLConfigUpdater:
    """MySQL配置更新器"""
    
    def __init__(self):
        """初始化配置更新器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
    
    def update_default_config(self, mysql_config: Dict[str, Any]) -> bool:
        """
        更新默认配置文件
        
        Args:
            mysql_config: MySQL配置字典
            
        Returns:
            bool: 更新是否成功
        """
        try:
            config_file = self.config_dir / "default.yaml"
            
            # 读取现有配置
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {}
            
            # 更新数据库配置
            if 'database' not in config:
                config['database'] = {}
            
            config['database']['type'] = 'mysql'
            config['database']['mysql'] = mysql_config
            
            # 写回配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            self.logger.info(f"默认配置文件已更新: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新默认配置失败: {e}")
            return False
    
    def create_environment_config(self, env: str, mysql_config: Dict[str, Any]) -> bool:
        """
        创建环境特定配置
        
        Args:
            env: 环境名称
            mysql_config: MySQL配置字典
            
        Returns:
            bool: 创建是否成功
        """
        try:
            config_file = self.config_dir / f"{env}.yaml"
            
            # 创建环境配置
            env_config = {
                'database': {
                    'type': 'mysql',
                    'mysql': mysql_config
                },
                'environments': {
                    env: {
                        'base_url': f"http://{env}-api.example.com",
                        'headers': {
                            'Content-Type': 'application/json'
                        }
                    }
                }
            }
            
            # 写入配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(env_config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            self.logger.info(f"环境配置文件已创建: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建环境配置失败: {e}")
            return False
    
    def validate_mysql_config(self, mysql_config: Dict[str, Any]) -> bool:
        """
        验证MySQL配置
        
        Args:
            mysql_config: MySQL配置字典
            
        Returns:
            bool: 配置是否有效
        """
        try:
            # 创建数据库管理器测试连接
            db_manager = DatabaseManager({
                'database': {
                    'type': 'mysql',
                    'mysql': mysql_config
                }
            })
            
            # 测试连接
            success = db_manager.connect()
            if success:
                db_manager.disconnect()
                self.logger.info("MySQL配置验证成功")
                return True
            else:
                self.logger.error("MySQL配置验证失败")
                return False
            
        except Exception as e:
            self.logger.error(f"MySQL配置验证失败: {e}")
            return False
    
    def initialize_database(self, mysql_config: Dict[str, Any]) -> bool:
        """
        初始化数据库
        
        Args:
            mysql_config: MySQL配置字典
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 创建数据库管理器
            db_manager = DatabaseManager({
                'database': {
                    'type': 'mysql',
                    'mysql': mysql_config
                }
            })
            
            # 连接数据库
            if not db_manager.connect():
                self.logger.error("数据库连接失败")
                return False
            
            # 创建测试用例表
            test_cases_table = """
            CREATE TABLE IF NOT EXISTS test_cases (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                api_endpoint VARCHAR(500),
                method ENUM('GET', 'POST', 'PUT', 'DELETE', 'PATCH') DEFAULT 'GET',
                request_body TEXT,
                expected_status INT DEFAULT 200,
                expected_response TEXT,
                headers JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                status ENUM('active', 'inactive', 'deprecated') DEFAULT 'active'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            result = db_manager.execute_query(test_cases_table)
            if not result.success:
                self.logger.error(f"创建test_cases表失败: {result.error}")
                return False
            
            # 创建测试执行记录表
            test_executions_table = """
            CREATE TABLE IF NOT EXISTS test_executions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                test_case_id INT,
                execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status ENUM('passed', 'failed', 'skipped', 'error') NOT NULL,
                actual_status INT,
                response_time DECIMAL(10,3),
                response_body TEXT,
                error_message TEXT,
                execution_log TEXT,
                FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            result = db_manager.execute_query(test_executions_table)
            if not result.success:
                self.logger.error(f"创建test_executions表失败: {result.error}")
                return False
            
            # 创建测试套件表
            test_suites_table = """
            CREATE TABLE IF NOT EXISTS test_suites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                status ENUM('active', 'inactive') DEFAULT 'active'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            result = db_manager.execute_query(test_suites_table)
            if not result.success:
                self.logger.error(f"创建test_suites表失败: {result.error}")
                return False
            
            # 创建测试套件关联表
            suite_cases_table = """
            CREATE TABLE IF NOT EXISTS suite_test_cases (
                id INT AUTO_INCREMENT PRIMARY KEY,
                suite_id INT,
                test_case_id INT,
                execution_order INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (suite_id) REFERENCES test_suites(id) ON DELETE CASCADE,
                FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE,
                UNIQUE KEY unique_suite_case (suite_id, test_case_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            result = db_manager.execute_query(suite_cases_table)
            if not result.success:
                self.logger.error(f"创建suite_test_cases表失败: {result.error}")
                return False
            
            # 创建API文档表
            api_documents_table = """
            CREATE TABLE IF NOT EXISTS api_documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                version VARCHAR(50),
                description TEXT,
                file_path VARCHAR(500),
                file_type ENUM('openapi', 'postman', 'swagger', 'raml') NOT NULL,
                content LONGTEXT,
                parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status ENUM('parsed', 'failed', 'pending') DEFAULT 'pending'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            result = db_manager.execute_query(api_documents_table)
            if not result.success:
                self.logger.error(f"创建api_documents表失败: {result.error}")
                return False
            
            # 创建索引
            indexes = [
                "CREATE INDEX idx_test_cases_status ON test_cases(status)",
                "CREATE INDEX idx_test_cases_endpoint ON test_cases(api_endpoint)",
                "CREATE INDEX idx_test_executions_time ON test_executions(execution_time)",
                "CREATE INDEX idx_test_executions_status ON test_executions(status)",
                "CREATE INDEX idx_test_executions_case_id ON test_executions(test_case_id)",
                "CREATE INDEX idx_api_documents_type ON api_documents(file_type)",
                "CREATE INDEX idx_api_documents_status ON api_documents(status)"
            ]
            
            for index_sql in indexes:
                result = db_manager.execute_query(index_sql)
                if not result.success:
                    self.logger.warning(f"创建索引失败: {index_sql}")
            
            # 插入示例数据
            sample_data = [
                {
                    'table': 'test_suites',
                    'data': [
                        ('基础API测试套件', '包含用户、认证等基础API的测试用例'),
                        ('高级功能测试套件', '包含复杂业务逻辑的API测试用例')
                    ]
                },
                {
                    'table': 'test_cases',
                    'data': [
                        ('获取用户列表', '测试获取用户列表API', '/api/users', 'GET', None, 200, '{"users": []}', '{}'),
                        ('创建用户', '测试创建用户API', '/api/users', 'POST', '{"name": "test", "email": "test@example.com"}', 201, '{"id": 1}', '{"Content-Type": "application/json"}'),
                        ('更新用户', '测试更新用户API', '/api/users/1', 'PUT', '{"name": "updated"}', 200, '{"id": 1}', '{"Content-Type": "application/json"}'),
                        ('删除用户', '测试删除用户API', '/api/users/1', 'DELETE', None, 204, '', '{}')
                    ]
                }
            ]
            
            for sample in sample_data:
                table_name = sample['table']
                for data in sample['data']:
                    if table_name == 'test_suites':
                        insert_sql = f"INSERT INTO {table_name} (name, description) VALUES (%s, %s)"
                    else:
                        insert_sql = f"INSERT INTO {table_name} (name, description, api_endpoint, method, request_body, expected_status, expected_response, headers) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    
                    result = db_manager.execute_query(insert_sql, data)
                    if not result.success:
                        self.logger.warning(f"插入示例数据失败: {table_name}")
            
            db_manager.disconnect()
            self.logger.info("数据库初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            return False
    
    def generate_config_report(self, mysql_config: Dict[str, Any]) -> str:
        """
        生成配置报告
        
        Args:
            mysql_config: MySQL配置字典
            
        Returns:
            str: 配置报告
        """
        report = []
        report.append("# MySQL配置报告")
        report.append("")
        report.append("## 配置信息")
        report.append(f"- 主机: {mysql_config.get('host', 'localhost')}")
        report.append(f"- 端口: {mysql_config.get('port', 3306)}")
        report.append(f"- 数据库: {mysql_config.get('database', 'autotest')}")
        report.append(f"- 用户名: {mysql_config.get('username', 'autotest')}")
        report.append(f"- 密码: {'已设置' if mysql_config.get('password') else '未设置'}")
        report.append(f"- 字符集: {mysql_config.get('charset', 'utf8mb4')}")
        report.append("")
        
        # 测试连接
        try:
            db_manager = DatabaseManager({
                'database': {
                    'type': 'mysql',
                    'mysql': mysql_config
                }
            })
            
            if db_manager.connect():
                info = db_manager.get_connection_info()
                
                report.append("## MySQL服务器信息")
                report.append(f"- 版本: {info.get('version', 'Unknown')}")
                report.append(f"- 连接ID: {info.get('connection_id', 'Unknown')}")
                report.append(f"- 当前数据库: {info.get('current_database', 'Unknown')}")
                report.append(f"- 主机: {info.get('host', 'Unknown')}")
                report.append(f"- 端口: {info.get('port', 'Unknown')}")
                report.append(f"- 用户名: {info.get('username', 'Unknown')}")
                report.append(f"- 字符集: {info.get('charset', 'Unknown')}")
                report.append("")
                
                # 获取表信息
                tables = db_manager.get_tables()
                report.append("## 数据库表信息")
                if tables:
                    report.append(f"- 表数量: {len(tables)}")
                    report.append("- 表列表:")
                    for table in tables:
                        report.append(f"  - {table}")
                else:
                    report.append("- 暂无表")
                report.append("")
                
                report.append("## 连接状态")
                report.append("✅ MySQL连接正常")
                
                db_manager.disconnect()
            else:
                report.append("## 连接状态")
                report.append("❌ MySQL连接失败")
                
        except Exception as e:
            report.append("## 连接状态")
            report.append(f"❌ MySQL连接失败: {e}")
        
        return "\n".join(report)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MySQL配置更新脚本')
    parser.add_argument('--host', default='localhost', help='MySQL主机地址')
    parser.add_argument('--port', type=int, default=3306, help='MySQL端口')
    parser.add_argument('--database', default='autotest', help='数据库名')
    parser.add_argument('--username', default='autotest', help='用户名')
    parser.add_argument('--password', default='autotest123', help='密码')
    parser.add_argument('--env', help='目标环境 (dev, test, prod)')
    parser.add_argument('--validate', action='store_true', help='验证配置')
    parser.add_argument('--init-db', action='store_true', help='初始化数据库')
    parser.add_argument('--report', action='store_true', help='生成配置报告')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建MySQL配置
    mysql_config = {
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'username': args.username,
        'password': args.password,
        'charset': 'utf8mb4',
        'max_connections': 20,
        'connect_timeout': 10,
        'read_timeout': 30,
        'write_timeout': 30,
        'autocommit': True,
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # 创建配置更新器
    updater = MySQLConfigUpdater()
    
    # 验证配置
    if args.validate:
        if updater.validate_mysql_config(mysql_config):
            print("✅ MySQL配置验证成功")
        else:
            print("❌ MySQL配置验证失败")
            sys.exit(1)
    
    # 初始化数据库
    if args.init_db:
        if updater.initialize_database(mysql_config):
            print("✅ 数据库初始化成功")
        else:
            print("❌ 数据库初始化失败")
            sys.exit(1)
    
    # 生成报告
    if args.report:
        report = updater.generate_config_report(mysql_config)
        print(report)
        
        # 保存报告到文件
        report_file = Path(__file__).parent.parent / "mysql_config_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存到: {report_file}")
    
    # 更新配置
    success = True
    
    # 更新默认配置
    if not updater.update_default_config(mysql_config):
        success = False
    
    # 创建环境配置
    if args.env:
        if not updater.create_environment_config(args.env, mysql_config):
            success = False
    
    if success:
        print("✅ MySQL配置更新成功")
    else:
        print("❌ MySQL配置更新失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
