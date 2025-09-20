"""解析器模块

提供API文档解析功能，支持多种文档格式：
- OpenAPI/Swagger 3.0规范解析
- Postman Collection v2.1格式解析

主要功能：
- 解析API文档并提取接口信息
- 标准化接口数据格式
- 生成测试数据模板
- 支持文件和URL加载

使用示例:
    from src.parsers import OpenAPIParser, PostmanParser
    
    # 解析OpenAPI文档
    parser = OpenAPIParser()
    parser.load_from_file('api-spec.yaml')
    paths = parser.get_all_paths()
    
    # 解析Postman Collection
    postman_parser = PostmanParser()
    postman_parser.load_from_file('collection.json')
    api_info = postman_parser.get_api_info()
"""

from .openapi_parser import OpenAPIParser
from .postman_parser import PostmanParser

__all__ = ["OpenAPIParser", "PostmanParser"]