"""
Mock数据管理器
负责管理Mock路由和响应数据
"""

import json
import re
import uuid
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from urllib.parse import parse_qs
from datetime import datetime


class MockDataManager:
    """Mock数据管理器"""
    
    def __init__(self):
        """初始化Mock数据管理器"""
        self.routes: Dict[str, Dict[str, Any]] = {}
        self.data: Dict[str, Any] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def add_route(self, route_config: Dict[str, Any]) -> str:
        """
        添加路由
        
        Args:
            route_config: 路由配置
            
        Returns:
            str: 路由ID
        """
        route_id = route_config.get("id") or str(uuid.uuid4())
        method = route_config.get("method", "GET").upper()
        path = route_config.get("path", "/")
        
        # 标准化路径
        if not path.startswith("/"):
            path = "/" + path
            
        route_data = {
            "id": route_id,
            "method": method,
            "path": path,
            "response": route_config.get("response", {}),
            "conditions": route_config.get("conditions", {}),
            "created_at": datetime.now().isoformat()
        }
        
        self.routes[route_id] = route_data
        self.logger.info(f"添加路由: {method} {path} (ID: {route_id})")
        return route_id
        
    def update_route(self, route_id: str, route_config: Dict[str, Any]):
        """
        更新路由
        
        Args:
            route_id: 路由ID
            route_config: 路由配置
        """
        if route_id not in self.routes:
            raise ValueError(f"路由不存在: {route_id}")
            
        # 保留原有的ID和创建时间
        original_route = self.routes[route_id]
        route_config["id"] = route_id
        route_config["created_at"] = original_route.get("created_at")
        route_config["updated_at"] = datetime.now().isoformat()
        
        self.routes[route_id] = route_config
        self.logger.info(f"更新路由: {route_id}")
        
    def delete_route(self, route_id: str):
        """
        删除路由
        
        Args:
            route_id: 路由ID
        """
        if route_id not in self.routes:
            raise ValueError(f"路由不存在: {route_id}")
            
        del self.routes[route_id]
        self.logger.info(f"删除路由: {route_id}")
        
    def get_route(self, route_id: str) -> Optional[Dict[str, Any]]:
        """
        获取路由
        
        Args:
            route_id: 路由ID
            
        Returns:
            Optional[Dict[str, Any]]: 路由数据
        """
        return self.routes.get(route_id)
        
    def get_all_routes(self) -> List[Dict[str, Any]]:
        """获取所有路由"""
        return list(self.routes.values())
        
    def find_response(self, method: str, path: str, request_obj=None) -> Optional[Dict[str, Any]]:
        """
        查找匹配的响应
        
        Args:
            method: HTTP方法
            path: 请求路径
            request_obj: 请求对象
            
        Returns:
            Optional[Dict[str, Any]]: 响应数据
        """
        method = method.upper()
        
        # 查找精确匹配的路由
        for route in self.routes.values():
            if self._match_route(route, method, path, request_obj):
                response = route["response"]
                
                # 处理动态响应
                if isinstance(response, dict) and "dynamic" in response:
                    return self._generate_dynamic_response(response, request_obj)
                else:
                    return response
                    
        return None
        
    def _match_route(self, route: Dict[str, Any], method: str, path: str, request_obj=None) -> bool:
        """
        检查路由是否匹配
        
        Args:
            route: 路由配置
            method: HTTP方法
            path: 请求路径
            request_obj: 请求对象
            
        Returns:
            bool: 是否匹配
        """
        # 检查HTTP方法
        if route.get("method", "GET").upper() != method:
            return False
            
        # 检查路径匹配
        route_path = route.get("path", "/")
        if not self._match_path(route_path, path):
            return False
            
        # 检查额外条件
        conditions = route.get("conditions", {})
        if conditions and request_obj:
            if not self._match_conditions(conditions, request_obj):
                return False
                
        return True
        
    def _match_path(self, route_path: str, request_path: str) -> bool:
        """
        检查路径是否匹配
        
        Args:
            route_path: 路由路径（可能包含通配符）
            request_path: 请求路径
            
        Returns:
            bool: 是否匹配
        """
        # 精确匹配
        if route_path == request_path:
            return True
            
        # 通配符匹配
        if "*" in route_path:
            # 将通配符转换为正则表达式
            pattern = route_path.replace("*", ".*")
            pattern = f"^{pattern}$"
            return bool(re.match(pattern, request_path))
            
        # 路径参数匹配 (如 /user/{id})
        if "{" in route_path and "}" in route_path:
            # 将路径参数转换为正则表达式
            pattern = re.sub(r'\{[^}]+\}', r'[^/]+', route_path)
            pattern = f"^{pattern}$"
            return bool(re.match(pattern, request_path))
            
        return False
        
    def _match_conditions(self, conditions: Dict[str, Any], request_obj) -> bool:
        """
        检查请求条件是否匹配
        
        Args:
            conditions: 条件配置
            request_obj: 请求对象
            
        Returns:
            bool: 是否匹配
        """
        try:
            # 检查查询参数
            if "query_params" in conditions:
                query_conditions = conditions["query_params"]
                request_args = getattr(request_obj, 'args', {})
                
                for param, expected_value in query_conditions.items():
                    actual_value = request_args.get(param)
                    if actual_value != expected_value:
                        return False
                        
            # 检查请求头
            if "headers" in conditions:
                header_conditions = conditions["headers"]
                request_headers = getattr(request_obj, 'headers', {})
                
                for header, expected_value in header_conditions.items():
                    actual_value = request_headers.get(header)
                    if actual_value != expected_value:
                        return False
                        
            # 检查请求体
            if "body" in conditions:
                body_conditions = conditions["body"]
                
                if hasattr(request_obj, 'get_json'):
                    request_body = request_obj.get_json() or {}
                    
                    for field, expected_value in body_conditions.items():
                        if field not in request_body or request_body[field] != expected_value:
                            return False
                            
            return True
        except Exception as e:
            self.logger.error(f"条件匹配失败: {str(e)}")
            return False
            
    def _generate_dynamic_response(self, response_config: Dict[str, Any], request_obj=None) -> Any:
        """
        生成动态响应
        
        Args:
            response_config: 响应配置
            request_obj: 请求对象
            
        Returns:
            Any: 动态响应数据
        """
        dynamic_type = response_config.get("dynamic", "template")
        
        if dynamic_type == "template":
            # 模板响应
            template = response_config.get("template", {})
            return self._process_template(template, request_obj)
            
        elif dynamic_type == "function":
            # 函数响应
            func_name = response_config.get("function")
            if func_name in self._dynamic_functions:
                return self._dynamic_functions[func_name](request_obj)
                
        elif dynamic_type == "data":
            # 数据驱动响应
            data_key = response_config.get("data_key")
            if data_key in self.data:
                return self.data[data_key]
                
        # 默认返回静态响应
        return response_config.get("default", {})
        
    def _process_template(self, template: Dict[str, Any], request_obj=None) -> Union[Dict[str, Any], str, List[Any]]:
        """
        处理响应模板
        
        Args:
            template: 响应模板
            request_obj: 请求对象
            
        Returns:
            Union[Dict[str, Any], str, List[Any]]: 处理后的响应
        """
        import copy
        result = copy.deepcopy(template)
        
        # 替换模板变量
        context = {
            "timestamp": datetime.now().isoformat(),
            "uuid": str(uuid.uuid4()),
            "random_id": str(uuid.uuid4())[:8]
        }
        
        # 添加请求信息到上下文
        if request_obj:
            if hasattr(request_obj, 'args'):
                context.update({f"query_{k}": v for k, v in request_obj.args.items()})
            if hasattr(request_obj, 'get_json'):
                body = request_obj.get_json() or {}
                context.update({f"body_{k}": v for k, v in body.items()})
                
        # 递归替换模板变量
        def replace_variables(obj):
            if isinstance(obj, str):
                for key, value in context.items():
                    obj = obj.replace(f"{{{key}}}", str(value))
                return obj
            elif isinstance(obj, dict):
                return {k: replace_variables(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_variables(item) for item in obj]
            else:
                return obj
                
        return replace_variables(result)
        
    def set_data(self, data: Dict[str, Any]):
        """
        设置数据
        
        Args:
            data: 数据
        """
        self.data.update(data)
        self.logger.info(f"设置数据: {len(data)} 个键")
        
    def get_data(self, key: str) -> Any:
        """
        获取数据
        
        Args:
            key: 数据键
            
        Returns:
            Any: 数据值
        """
        return self.data.get(key)
        
    def get_all_data(self) -> Dict[str, Any]:
        """获取所有数据"""
        return self.data.copy()
        
    def reset(self):
        """重置所有数据"""
        self.routes.clear()
        self.data.clear()
        self.logger.info("重置Mock数据")
        
    @property
    def _dynamic_functions(self) -> Dict[str, Callable]:
        """动态函数映射"""
        return {
            "current_time": lambda req: {"timestamp": datetime.now().isoformat()},
            "echo_request": lambda req: {
                "method": req.method if req else "GET",
                "path": req.path if req else "/",
                "query": dict(req.args) if req and hasattr(req, 'args') else {},
                "body": req.get_json() if req and hasattr(req, 'get_json') else {}
            },
            "random_user": lambda req: {
                "id": str(uuid.uuid4())[:8],
                "name": f"User_{uuid.uuid4().hex[:6]}",
                "email": f"user_{uuid.uuid4().hex[:6]}@example.com"
            }
        }