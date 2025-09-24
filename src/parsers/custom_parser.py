#!/usr/bin/env python3
"""
自定义格式解析器基类
提供可扩展的解析器架构，支持新格式的快速接入
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging


class BaseParser(ABC):
    """解析器基类，定义标准接口"""
    
    def __init__(self):
        """初始化解析器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.spec: Dict[str, Any] = {}
        self.version: str = ""
        self.base_url: str = ""
    
    @abstractmethod
    def load_from_file(self, file_path: str) -> bool:
        """从文件加载文档"""
        pass
    
    @abstractmethod
    def load_from_url(self, url: str) -> bool:
        """从URL加载文档"""
        pass
    
    @abstractmethod
    def get_api_info(self) -> Dict[str, Any]:
        """获取API基本信息"""
        pass
    
    @abstractmethod
    def get_all_paths(self) -> List[Dict[str, Any]]:
        """获取所有路径信息"""
        pass
    
    def validate_spec(self) -> bool:
        """验证文档格式"""
        return bool(self.spec)


class InsomiaParser(BaseParser):
    """Insomnia Workspace解析器"""
    
    def load_from_file(self, file_path: str) -> bool:
        """加载Insomnia workspace文件"""
        try:
            import json
            from pathlib import Path
            
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.error(f"文件不存在: {file_path}")
                return False
                
            with open(file_path, 'r', encoding='utf-8') as f:
                self.spec = json.load(f)
            
            # 验证Insomnia格式
            if self.spec.get('_type') == 'export':
                self.logger.info("成功加载Insomnia workspace文件")
                return True
            else:
                self.logger.error("不是有效的Insomnia workspace文件")
                return False
                
        except Exception as e:
            self.logger.error(f"加载Insomnia文件失败: {e}")
            return False
    
    def load_from_url(self, url: str) -> bool:
        """从URL加载（Insomnia不支持直接URL加载）"""
        self.logger.warning("Insomnia不支持直接从URL加载，请先下载文件")
        return False
    
    def get_api_info(self) -> Dict[str, Any]:
        """获取API信息"""
        return {
            "title": "Insomnia Workspace",
            "version": "1.0.0",
            "description": "",
            "base_url": "",
            "spec_version": "insomnia"
        }
    
    def get_all_paths(self) -> List[Dict[str, Any]]:
        """获取所有请求"""
        paths = []
        if not self.spec:
            return paths
            
        # 遍历Insomnia workspace中的请求
        resources = self.spec.get('resources', [])
        for resource in resources:
            if resource.get('_type') == 'request':
                request_data = resource.get('body', {})
                method = resource.get('method', 'GET')
                url = resource.get('url', '')
                
                paths.append({
                    'path': url,
                    'method': method,
                    'summary': resource.get('name', url),
                    'description': resource.get('description', ''),
                    'parameters': self._extract_parameters(resource),
                    'request_body': self._extract_request_body(request_data)
                })
        
        return paths
    
    def _extract_parameters(self, resource: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取请求参数"""
        parameters = []
        url = resource.get('url', '')
        
        # 提取URL参数
        if '{' in url and '}' in url:
            import re
            url_params = re.findall(r'\{([^}]+)\}', url)
            for param in url_params:
                parameters.append({
                    'name': param,
                    'in': 'path',
                    'required': True,
                    'schema': {'type': 'string'}
                })
        
        return parameters
    
    def _extract_request_body(self, body_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """提取请求体"""
        if not body_data:
            return None
            
        mime_type = body_data.get('mimeType', 'application/json')
        text = body_data.get('text', '')
        
        if mime_type == 'application/json' and text:
            try:
                import json
                return json.loads(text)
            except json.JSONDecodeError:
                return {'raw': text}
        
        return {'raw': text, 'mimeType': mime_type}


class APIBlueprintParser(BaseParser):
    """API Blueprint格式解析器"""
    
    def load_from_file(self, file_path: str) -> bool:
        """加载API Blueprint文件"""
        try:
            from pathlib import Path
            
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.error(f"文件不存在: {file_path}")
                return False
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的API Blueprint格式验证
            if 'FORMAT:' in content or 'API Blueprint' in content:
                self.spec = {'content': content, 'format': 'apiblueprint'}
                self.logger.info("成功加载API Blueprint文件")
                return True
            else:
                self.logger.error("不是有效的API Blueprint文件")
                return False
                
        except Exception as e:
            self.logger.error(f"加载API Blueprint文件失败: {e}")
            return False
    
    def load_from_url(self, url: str) -> bool:
        """从URL加载（API Blueprint不支持直接URL加载）"""
        self.logger.warning("API Blueprint不支持直接从URL加载，请先下载文件")
        return False
    
    def get_api_info(self) -> Dict[str, Any]:
        """获取API信息"""
        return {
            "title": "API Blueprint",
            "version": "1.0.0",
            "description": "",
            "base_url": "",
            "spec_version": "apiblueprint"
        }
    
    def get_all_paths(self) -> List[Dict[str, Any]]:
        """获取所有路径"""
        return []


class RAMLParser(BaseParser):
    """RAML格式解析器"""
    
    def load_from_file(self, file_path: str) -> bool:
        """加载RAML文件"""
        try:
            import yaml
            from pathlib import Path
            
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.error(f"文件不存在: {file_path}")
                return False
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 验证RAML格式
            if content.strip().startswith('#%RAML'):
                self.spec = yaml.safe_load(content)
                self.logger.info("成功加载RAML文件")
                return True
            else:
                self.logger.error("不是有效的RAML文件")
                return False
                
        except Exception as e:
            self.logger.error(f"加载RAML文件失败: {e}")
            return False
    
    def load_from_url(self, url: str) -> bool:
        """从URL加载（RAML不支持直接URL加载）"""
        self.logger.warning("RAML不支持直接从URL加载，请先下载文件")
        return False
    
    def get_api_info(self) -> Dict[str, Any]:
        """获取API信息"""
        return {
            "title": "RAML API",
            "version": "1.0.0",
            "description": "",
            "base_url": "",
            "spec_version": "raml"
        }
    
    def get_all_paths(self) -> List[Dict[str, Any]]:
        """获取所有路径"""
        return []


class GraphQLParser(BaseParser):
    """GraphQL Schema解析器"""
    
    def load_from_file(self, file_path: str) -> bool:
        """加载GraphQL Schema文件"""
        try:
            from pathlib import Path
            
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.error(f"文件不存在: {file_path}")
                return False
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的GraphQL Schema验证
            if 'type' in content or 'schema' in content or 'query' in content:
                self.spec = {'content': content, 'format': 'graphql'}
                self.logger.info("成功加载GraphQL Schema文件")
                return True
            else:
                self.logger.error("不是有效的GraphQL Schema文件")
                return False
                
        except Exception as e:
            self.logger.error(f"加载GraphQL Schema文件失败: {e}")
            return False
    
    def load_from_url(self, url: str) -> bool:
        """从URL加载Schema（GraphQL不支持直接URL加载）"""
        self.logger.warning("GraphQL不支持直接从URL加载，请先下载文件")
        return False
    
    def get_api_info(self) -> Dict[str, Any]:
        """获取API信息"""
        return {
            "title": "GraphQL API",
            "version": "1.0.0",
            "description": "",
            "base_url": "",
            "spec_version": "graphql"
        }
    
    def get_all_paths(self) -> List[Dict[str, Any]]:
        """获取所有查询/变更"""
        return []


class ParserFactory:
    """解析器工厂类"""
    
    _parsers = {
        'openapi': 'src.parsers.openapi_parser.OpenAPIParser',
        'swagger': 'src.parsers.openapi_parser.OpenAPIParser',
        'postman': 'src.parsers.postman_parser.PostmanParser',
        'insomnia': 'InsomiaParser',
        'apiblueprint': 'APIBlueprintParser',
        'raml': 'RAMLParser',
        'graphql': 'GraphQLParser'
    }
    
    @classmethod
    def create_parser(cls, format_type: str) -> Optional[BaseParser]:
        """创建指定格式的解析器"""
        parser_class = cls._parsers.get(format_type.lower())
        if not parser_class:
            return None
        
        try:
            if '.' in parser_class:
                # 动态导入现有解析器
                module_path, class_name = parser_class.rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                parser_cls = getattr(module, class_name)
            else:
                # 本模块中的解析器
                parser_cls = globals()[parser_class]
            
            return parser_cls()
        except Exception as e:
            logging.error(f"创建解析器失败: {format_type} - {e}")
            return None
    
    @classmethod
    def detect_format(cls, file_path: str) -> Optional[str]:
        """自动检测文档格式"""
        import json
        import yaml
        from pathlib import Path
        
        file_obj = Path(file_path)
        
        try:
            # 根据文件扩展名初步判断
            if file_obj.suffix.lower() in ['.yaml', '.yml']:
                with open(file_obj, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                    
                if 'openapi' in content:
                    return 'openapi'
                elif 'swagger' in content:
                    return 'swagger'
                elif '#%RAML' in str(content):
                    return 'raml'
                    
            elif file_obj.suffix.lower() == '.json':
                with open(file_obj, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    
                if 'info' in content and 'item' in content:
                    return 'postman'
                elif 'openapi' in content:
                    return 'openapi'
                elif 'swagger' in content:
                    return 'swagger'
                elif '_type' in content and content['_type'] == 'export':
                    return 'insomnia'
                    
            elif file_obj.suffix.lower() in ['.apib', '.md']:
                # API Blueprint 检测
                with open(file_obj, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('FORMAT:') or 'API Blueprint' in first_line:
                        return 'apiblueprint'
                        
            elif file_obj.suffix.lower() in ['.graphql', '.gql']:
                return 'graphql'
                
        except Exception as e:
            logging.error(f"格式检测失败: {file_path} - {e}")
            
        return None