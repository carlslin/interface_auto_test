"""
OpenAPI/Swagger文档解析器
负责解析OpenAPI 3.0和Swagger 2.0规范文档
"""

import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from urllib.parse import urljoin


class OpenAPIParser:
    """OpenAPI文档解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.spec: Dict[str, Any] = {}
        self.version: str = ""
        self.base_url: str = ""
        
    def load_from_file(self, file_path: str) -> bool:
        """
        从文件加载OpenAPI文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否加载成功
        """
        try:
            file_obj = Path(file_path)
            
            if not file_obj.exists():
                self.logger.error(f"文件不存在: {file_path}")
                return False
                
            with open(file_obj, 'r', encoding='utf-8') as f:
                if file_obj.suffix.lower() in ['.yaml', '.yml']:
                    self.spec = yaml.safe_load(f)
                else:
                    self.spec = json.load(f)
                    
            return self._validate_and_parse()
        except Exception as e:
            self.logger.error(f"加载文件失败: {file_path} - {str(e)}")
            return False
            
    def load_from_url(self, url: str) -> bool:
        """
        从URL加载OpenAPI文档
        
        Args:
            url: 文档URL
            
        Returns:
            bool: 是否加载成功
        """
        try:
            import requests
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            if 'application/json' in response.headers.get('content-type', ''):
                self.spec = response.json()
            else:
                self.spec = yaml.safe_load(response.text)
                
            return self._validate_and_parse()
        except Exception as e:
            self.logger.error(f"从URL加载失败: {url} - {str(e)}")
            return False
            
    def load_from_dict(self, spec_dict: Dict[str, Any]) -> bool:
        """
        从字典加载OpenAPI文档
        
        Args:
            spec_dict: 文档字典
            
        Returns:
            bool: 是否加载成功
        """
        try:
            self.spec = spec_dict
            return self._validate_and_parse()
        except Exception as e:
            self.logger.error(f"从字典加载失败: {str(e)}")
            return False
            
    def _validate_and_parse(self) -> bool:
        """验证和解析文档"""
        try:
            # 检查版本
            if 'openapi' in self.spec:
                self.version = self.spec['openapi']
                if not self.version.startswith('3.'):
                    self.logger.warning(f"可能不支持的OpenAPI版本: {self.version}")
            elif 'swagger' in self.spec:
                self.version = self.spec['swagger']
                if not self.version.startswith('2.'):
                    self.logger.warning(f"可能不支持的Swagger版本: {self.version}")
            else:
                self.logger.error("无效的OpenAPI/Swagger文档：缺少版本信息")
                return False
                
            # 设置基础URL
            self._parse_base_url()
            
            self.logger.info(f"成功解析OpenAPI文档 (版本: {self.version})")
            return True
        except Exception as e:
            self.logger.error(f"文档验证失败: {str(e)}")
            return False
            
    def _parse_base_url(self):
        """解析基础URL"""
        if self.version.startswith('3.'):
            # OpenAPI 3.0
            servers = self.spec.get('servers', [])
            if servers:
                self.base_url = servers[0].get('url', '')
        else:
            # Swagger 2.0
            host = self.spec.get('host', 'localhost')
            schemes = self.spec.get('schemes', ['http'])
            base_path = self.spec.get('basePath', '')
            self.base_url = f"{schemes[0]}://{host}{base_path}"
            
    def get_api_info(self) -> Dict[str, Any]:
        """获取API基本信息"""
        info = self.spec.get('info', {})
        return {
            "title": info.get('title', 'Unknown API'),
            "version": info.get('version', '1.0.0'),
            "description": info.get('description', ''),
            "base_url": self.base_url,
            "spec_version": self.version
        }
    
    def get_full_spec(self) -> Dict[str, Any]:
        """获取完整的API规范"""
        return self.spec.copy()
        
    def get_all_paths(self) -> List[Dict[str, Any]]:
        """获取所有路径信息"""
        paths = []
        paths_spec = self.spec.get('paths', {})
        
        for path, path_item in paths_spec.items():
            for method, operation in path_item.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    path_info = self._parse_operation(path, method, operation)
                    if path_info:
                        paths.append(path_info)
                        
        return paths
        
    def _parse_operation(self, path: str, method: str, operation: Dict[str, Any]) -> Dict[str, Any]:
        """解析单个操作"""
        try:
            operation_info = {
                "path": path,
                "method": method.upper(),
                "operation_id": operation.get('operationId', f"{method}_{path}".replace('/', '_')),
                "summary": operation.get('summary', ''),
                "description": operation.get('description', ''),
                "tags": operation.get('tags', []),
                "parameters": self._parse_parameters(operation.get('parameters', [])),
                "request_body": self._parse_request_body(operation.get('requestBody')),
                "responses": self._parse_responses(operation.get('responses', {})),
                "security": operation.get('security', [])
            }
            
            return operation_info
        except Exception as e:
            self.logger.error(f"解析操作失败: {method} {path} - {str(e)}")
            return {}
            
    def _parse_parameters(self, parameters: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """解析参数"""
        parsed_params = {
            "path": [],
            "query": [],
            "header": [],
            "cookie": []
        }
        
        for param in parameters:
            param_info = {
                "name": param.get('name', ''),
                "description": param.get('description', ''),
                "required": param.get('required', False),
                "schema": param.get('schema', {}),
                "example": param.get('example')
            }
            
            param_in = param.get('in', 'query')
            if param_in in parsed_params:
                parsed_params[param_in].append(param_info)
                
        return parsed_params
        
    def _parse_request_body(self, request_body: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """解析请求体"""
        if not request_body:
            return None
            
        content = request_body.get('content', {})
        parsed_body = {
            "description": request_body.get('description', ''),
            "required": request_body.get('required', False),
            "content_types": list(content.keys()),
            "schema": {}
        }
        
        # 获取JSON schema（优先）
        for content_type in ['application/json', 'application/xml', 'text/plain']:
            if content_type in content:
                parsed_body["schema"] = content[content_type].get('schema', {})
                break
                
        return parsed_body
        
    def _parse_responses(self, responses: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """解析响应"""
        parsed_responses = {}
        
        for status_code, response in responses.items():
            response_info = {
                "description": response.get('description', ''),
                "headers": response.get('headers', {}),
                "content": {},
                "schema": {}
            }
            
            content = response.get('content', {})
            response_info["content"] = content
            
            # 获取响应schema
            for content_type in ['application/json', 'application/xml', 'text/plain']:
                if content_type in content:
                    response_info["schema"] = content[content_type].get('schema', {})
                    break
                    
            parsed_responses[status_code] = response_info
            
        return parsed_responses
        
    def get_path_by_operation_id(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """根据操作ID获取路径信息"""
        for path_info in self.get_all_paths():
            if path_info.get('operation_id') == operation_id:
                return path_info
        return None
        
    def get_paths_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """根据标签获取路径信息"""
        return [
            path_info for path_info in self.get_all_paths()
            if tag in path_info.get('tags', [])
        ]
        
    def get_components(self) -> Dict[str, Any]:
        """获取组件定义"""
        if self.version.startswith('3.'):
            return self.spec.get('components', {})
        else:
            # Swagger 2.0
            return {
                "schemas": self.spec.get('definitions', {}),
                "parameters": self.spec.get('parameters', {}),
                "responses": self.spec.get('responses', {}),
                "securitySchemes": self.spec.get('securityDefinitions', {})
            }
            
    def generate_example_request(self, path_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成示例请求"""
        example = {
            "method": path_info.get('method', 'GET'),
            "url": urljoin(self.base_url, path_info.get('path', '/')),
            "headers": {},
            "query_params": {},
            "path_params": {},
            "body": None
        }
        
        # 生成参数示例
        parameters = path_info.get('parameters', {})
        
        for param in parameters.get('query', []):
            example["query_params"][param['name']] = self._generate_example_value(param.get('schema', {}))
            
        for param in parameters.get('path', []):
            example["path_params"][param['name']] = self._generate_example_value(param.get('schema', {}))
            
        for param in parameters.get('header', []):
            example["headers"][param['name']] = self._generate_example_value(param.get('schema', {}))
            
        # 生成请求体示例
        request_body = path_info.get('request_body')
        if request_body and request_body.get('schema'):
            example["body"] = self._generate_example_value(request_body['schema'])
            
        return example
        
    def _generate_example_value(self, schema: Dict[str, Any]) -> Any:
        """根据schema生成示例值"""
        if not schema:
            return "example_value"
            
        schema_type = schema.get('type', 'string')
        
        if schema_type == 'string':
            if 'example' in schema:
                return schema['example']
            elif 'enum' in schema:
                return schema['enum'][0]
            else:
                return "example_string"
        elif schema_type == 'integer':
            return schema.get('example', 123)
        elif schema_type == 'number':
            return schema.get('example', 123.45)
        elif schema_type == 'boolean':
            return schema.get('example', True)
        elif schema_type == 'array':
            items_schema = schema.get('items', {})
            return [self._generate_example_value(items_schema)]
        elif schema_type == 'object':
            example_obj = {}
            properties = schema.get('properties', {})
            for prop_name, prop_schema in properties.items():
                example_obj[prop_name] = self._generate_example_value(prop_schema)
            return example_obj
        else:
            return None