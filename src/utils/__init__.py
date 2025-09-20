"""工具函数模块

提供测试框架所需的各种工具函数：
- 配置管理和环境切换
- 响应数据验证
- 测试数据生成
- 数据持久化管理

主要组件：
- ConfigLoader: 配置加载器，管理多环境配置
- ResponseValidator: 响应验证器，验证API响应数据
- DataFaker: 数据生成器，使用Faker生成测试数据
- DataManager: 数据管理器，管理测试数据和环境变量

使用示例:
    from src.utils import ConfigLoader, ResponseValidator, DataFaker
    
    # 加载配置
    config = ConfigLoader()
    config.set_environment('test')
    
    # 验证响应
    validator = ResponseValidator()
    validator.validate_status_code(response.status_code, 200)
    
    # 生成测试数据
    faker = DataFaker()
    user_data = faker.generate_from_template('user')
"""

from .config_loader import ConfigLoader
from .validator import ResponseValidator
from .data_faker import DataFaker
from .data_manager import DataManager

__all__ = ["ConfigLoader", "ResponseValidator", "DataFaker", "DataManager"]