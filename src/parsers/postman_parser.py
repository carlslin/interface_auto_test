"""
Postman Collection解析器
负责解析Postman Collection v2.1格式的文档
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path


class PostmanParser:
    """Postman Collection解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.collection: Dict[str, Any] = {}
        
    def load_from_file(self, file_path: str) -> bool:
        """
        从文件加载Postman Collection
        
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
                self.collection = json.load(f)
                    
            return self._validate_collection()
        except Exception as e:
            self.logger.error(f"加载文件失败: {file_path} - {str(e)}")
            return False
            
    def _validate_collection(self) -> bool:
        """验证Collection格式"""
        try:
            # 检查基本结构
            if 'info' not in self.collection:
                self.logger.error("无效的Postman Collection：缺少info字段")
                return False
                
            if 'item' not in self.collection:
                self.logger.error("无效的Postman Collection：缺少item字段")
                return False
                
            schema = self.collection.get('info', {}).get('schema')
            if not schema or 'v2' not in schema:
                self.logger.warning("可能不支持的Postman Collection版本")
                
            self.logger.info("成功解析Postman Collection")
            return True
        except Exception as e:
            self.logger.error(f"Collection验证失败: {str(e)}")
            return False
            
    def get_api_info(self) -> Dict[str, Any]:
        """获取API基本信息"""
        info = self.collection.get('info', {})
        return {
            "title": info.get('name', 'Unknown Collection'),
            "version": info.get('version', '1.0.0'),
            "description": info.get('description', ''),
            "base_url": self._extract_base_url(),
            "spec_version": "postman_v2"
        }
        
    def _extract_base_url(self) -> str:
        """提取基础URL"""
        # 从变量中提取
        variables = self.collection.get('variable', [])
        for var in variables:
            if var.get('key') in ['baseUrl', 'base_url', 'host']:
                return var.get('value', '')
                
        # 从第一个请求中提取
        items = self.collection.get('item', [])
        if items:
            first_request = self._find_first_request(items)
            if first_request:
                url = first_request.get('url', {})
                if isinstance(url, dict):
                    host = url.get('host', [])
                    if host:
                        protocol = url.get('protocol', 'http')
                        return f"{protocol}://{'.'.join(host)}"
                        
        return ""
        
    def _find_first_request(self, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """查找第一个请求"""
        for item in items:
            if 'request' in item:
                return item['request']
            elif 'item' in item:
                # 递归查找文件夹中的请求
                result = self._find_first_request(item['item'])
                if result:
                    return result
        return None
        
    def get_all_paths(self) -> List[Dict[str, Any]]:
        """获取所有路径信息"""
        paths = []
        items = self.collection.get('item', [])
        self._extract_requests(items, paths)
        return paths
        
    def _extract_requests(self, items: List[Dict[str, Any]], paths: List[Dict[str, Any]], folder_path: str = ""):
        """递归提取请求"""
        for item in items:
            if 'request' in item:
                # 这是一个请求项
                path_info = self._parse_request(item, folder_path)
                if path_info:
                    paths.append(path_info)
            elif 'item' in item:
                # 这是一个文件夹
                folder_name = item.get('name', '')
                new_folder_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
                self._extract_requests(item['item'], paths, new_folder_path)
                
    def _parse_request(self, item: Dict[str, Any], folder_path: str) -> Dict[str, Any]:
        """解析单个请求"""
        try:
            request = item.get('request', {})
            
            # 解析URL
            url_info = self._parse_url(request.get('url', {}))
            
            # 解析请求体
            body_info = self._parse_request_body(request.get('body', {}))
            
            # 解析头部
            headers = self._parse_headers(request.get('header', []))
            
            request_info = {
                "path": url_info['path'],
                "method": request.get('method', 'GET').upper(),
                "operation_id": item.get('name', '').replace(' ', '_'),
                "summary": item.get('name', ''),
                "description": item.get('description', ''),
                "tags": [folder_path] if folder_path else [],
                "parameters": {
                    "query": url_info['query_params'],
                    "path": url_info['path_params'],
                    "header": headers
                },
                "request_body": body_info,
                "responses": {}  # Postman Collection通常不包含响应定义
            }
            
            return request_info
        except Exception as e:
            self.logger.error(f"解析请求失败: {item.get('name', 'Unknown')} - {str(e)}")
            return {}
            
    def _parse_url(self, url: Any) -> Dict[str, Any]:
        """解析URL"""
        url_info = {
            "path": "/",
            "query_params": [],
            "path_params": []
        }
        
        if isinstance(url, str):
            # 简单字符串URL
            url_info["path"] = url
        elif isinstance(url, dict):
            # 详细URL对象
            path_parts = url.get('path', [])
            if path_parts:
                url_info["path"] = "/" + "/".join(str(part) for part in path_parts)
            
            # 解析查询参数
            query = url.get('query', [])
            for param in query:
                if isinstance(param, dict):
                    param_info = {
                        "name": param.get('key', ''),
                        "description": param.get('description', ''),
                        "required": not param.get('disabled', False),
                        "value": param.get('value', '')
                    }
                    url_info["query_params"].append(param_info)
                    
            # 解析路径参数（从路径中提取{{variable}}格式）
            for part in path_parts:
                part_str = str(part)
                if part_str.startswith('{{') and part_str.endswith('}}'):
                    param_name = part_str[2:-2]
                    param_info = {
                        "name": param_name,
                        "description": f"Path parameter: {param_name}",
                        "required": True,
                        "value": ""
                    }
                    url_info["path_params"].append(param_info)
                    
        return url_info
        
    def _parse_request_body(self, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析请求体"""
        if not body:
            return None
            
        mode = body.get('mode', 'raw')
        body_info = {
            "description": "",
            "required": True,
            "content_types": [],
            "schema": {},
            "example": None
        }
        
        if mode == 'raw':
            raw_data = body.get('raw', '')
            body_info["content_types"] = ['application/json']
            body_info["example"] = raw_data
            
            # 尝试解析JSON
            try:
                json_data = json.loads(raw_data)
                body_info["schema"] = self._infer_schema_from_example(json_data)
            except:
                body_info["content_types"] = ['text/plain']
                
        elif mode == 'formdata':
            formdata = body.get('formdata', [])
            body_info["content_types"] = ['application/x-www-form-urlencoded']
            
        elif mode == 'urlencoded':
            urlencoded = body.get('urlencoded', [])
            body_info["content_types"] = ['application/x-www-form-urlencoded']
            
        return body_info
        
    def _parse_headers(self, headers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解析请求头"""
        header_list = []
        
        for header in headers:
            if isinstance(header, dict) and not header.get('disabled', False):
                header_info = {
                    "name": header.get('key', ''),
                    "description": header.get('description', ''),
                    "required": True,
                    "value": header.get('value', '')
                }
                header_list.append(header_info)
                
        return header_list
        
    def _infer_schema_from_example(self, example: Any) -> Dict[str, Any]:
        """从示例数据推断JSON Schema"""
        if isinstance(example, dict):
            properties = {}
            for key, value in example.items():
                properties[key] = self._infer_schema_from_example(value)
            return {
                "type": "object",
                "properties": properties
            }
        elif isinstance(example, list):
            if example:
                return {
                    "type": "array",
                    "items": self._infer_schema_from_example(example[0])
                }
            else:
                return {"type": "array"}
        elif isinstance(example, str):
            return {"type": "string", "example": example}
        elif isinstance(example, int):
            return {"type": "integer", "example": example}
        elif isinstance(example, float):
            return {"type": "number", "example": example}
        elif isinstance(example, bool):
            return {"type": "boolean", "example": example}
        else:
            return {"type": "string"}