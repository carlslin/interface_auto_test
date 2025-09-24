#!/usr/bin/env python3
"""
=============================================================================
Redis配置更新脚本
=============================================================================

本脚本用于更新项目配置文件中的Redis设置，支持：
- 更新默认配置文件中的Redis配置
- 创建环境特定的Redis配置
- 验证Redis配置的有效性
- 生成Redis连接测试报告

使用方法：
    python3 scripts/update_redis_config.py [--host HOST] [--port PORT] [--db DB] [--password PASSWORD]

参数说明：
    --host: Redis主机地址，默认localhost
    --port: Redis端口，默认6379
    --db: Redis数据库编号，默认0
    --password: Redis密码，可选
    --env: 目标环境，可选值：dev, test, prod

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

from src.utils.cache_manager import RedisCache


class RedisConfigUpdater:
    """Redis配置更新器"""
    
    def __init__(self):
        """初始化配置更新器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
    
    def update_default_config(self, redis_config: Dict[str, Any]) -> bool:
        """
        更新默认配置文件
        
        Args:
            redis_config: Redis配置字典
            
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
            
            # 更新缓存配置
            if 'cache' not in config:
                config['cache'] = {}
            
            config['cache']['type'] = 'redis'
            config['cache']['redis'] = redis_config
            
            # 写回配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            self.logger.info(f"默认配置文件已更新: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新默认配置失败: {e}")
            return False
    
    def create_environment_config(self, env: str, redis_config: Dict[str, Any]) -> bool:
        """
        创建环境特定配置
        
        Args:
            env: 环境名称
            redis_config: Redis配置字典
            
        Returns:
            bool: 创建是否成功
        """
        try:
            config_file = self.config_dir / f"{env}.yaml"
            
            # 创建环境配置
            env_config = {
                'cache': {
                    'type': 'redis',
                    'redis': redis_config
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
    
    def validate_redis_config(self, redis_config: Dict[str, Any]) -> bool:
        """
        验证Redis配置
        
        Args:
            redis_config: Redis配置字典
            
        Returns:
            bool: 配置是否有效
        """
        try:
            # 创建Redis连接测试
            cache = RedisCache(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                password=redis_config.get('password')
            )
            
            # 测试连接
            redis_client = cache._get_redis()
            redis_client.ping()
            
            self.logger.info("Redis配置验证成功")
            return True
            
        except Exception as e:
            self.logger.error(f"Redis配置验证失败: {e}")
            return False
    
    def generate_config_report(self, redis_config: Dict[str, Any]) -> str:
        """
        生成配置报告
        
        Args:
            redis_config: Redis配置字典
            
        Returns:
            str: 配置报告
        """
        report = []
        report.append("# Redis配置报告")
        report.append("")
        report.append("## 配置信息")
        report.append(f"- 主机: {redis_config.get('host', 'localhost')}")
        report.append(f"- 端口: {redis_config.get('port', 6379)}")
        report.append(f"- 数据库: {redis_config.get('db', 0)}")
        report.append(f"- 密码: {'已设置' if redis_config.get('password') else '未设置'}")
        report.append("")
        
        # 测试连接
        try:
            cache = RedisCache(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                password=redis_config.get('password')
            )
            
            redis_client = cache._get_redis()
            info = redis_client.info()
            
            report.append("## Redis服务器信息")
            report.append(f"- 版本: {info.get('redis_version', 'Unknown')}")
            report.append(f"- 运行模式: {info.get('redis_mode', 'Unknown')}")
            report.append(f"- 连接数: {info.get('connected_clients', 'Unknown')}")
            report.append(f"- 内存使用: {info.get('used_memory_human', 'Unknown')}")
            report.append(f"- 键数量: {redis_client.dbsize()}")
            report.append("")
            report.append("## 连接状态")
            report.append("✅ Redis连接正常")
            
        except Exception as e:
            report.append("## 连接状态")
            report.append(f"❌ Redis连接失败: {e}")
        
        return "\n".join(report)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Redis配置更新脚本')
    parser.add_argument('--host', default='localhost', help='Redis主机地址')
    parser.add_argument('--port', type=int, default=6379, help='Redis端口')
    parser.add_argument('--db', type=int, default=0, help='Redis数据库编号')
    parser.add_argument('--password', help='Redis密码')
    parser.add_argument('--env', help='目标环境 (dev, test, prod)')
    parser.add_argument('--validate', action='store_true', help='验证配置')
    parser.add_argument('--report', action='store_true', help='生成配置报告')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建Redis配置
    redis_config = {
        'host': args.host,
        'port': args.port,
        'db': args.db,
        'max_connections': 10,
        'socket_timeout': 5,
        'socket_connect_timeout': 5,
        'retry_on_timeout': True,
        'health_check_interval': 30
    }
    
    if args.password:
        redis_config['password'] = args.password
    
    # 创建配置更新器
    updater = RedisConfigUpdater()
    
    # 验证配置
    if args.validate:
        if updater.validate_redis_config(redis_config):
            print("✅ Redis配置验证成功")
        else:
            print("❌ Redis配置验证失败")
            sys.exit(1)
    
    # 生成报告
    if args.report:
        report = updater.generate_config_report(redis_config)
        print(report)
        
        # 保存报告到文件
        report_file = Path(__file__).parent.parent / "redis_config_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存到: {report_file}")
    
    # 更新配置
    success = True
    
    # 更新默认配置
    if not updater.update_default_config(redis_config):
        success = False
    
    # 创建环境配置
    if args.env:
        if not updater.create_environment_config(args.env, redis_config):
            success = False
    
    if success:
        print("✅ Redis配置更新成功")
    else:
        print("❌ Redis配置更新失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
