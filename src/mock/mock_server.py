"""
Mock服务器模块
提供HTTP Mock服务功能
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify, Response
try:
    from flask_cors import CORS
except ImportError:
    CORS = None
import threading
from pathlib import Path

from .mock_data import MockDataManager


class MockServer:
    """Mock服务器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Mock服务器
        
        Args:
            config: 服务器配置
        """
        self.config = config or self._get_default_config()
        self.app = Flask(__name__)
        self.data_manager = MockDataManager()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 启用CORS
        if self.config.get("enable_cors", True) and CORS:
            CORS(self.app)
            
        self._setup_routes()
        self._running = False
        self._server_thread = None
        
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "host": "localhost",
            "port": 5000,
            "debug": True,
            "enable_cors": True,
            "delay": 0
        }
        
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.before_request
        def before_request():
            """请求前处理"""
            # 模拟网络延迟
            delay = self.config.get("delay", 0)
            if delay > 0:
                time.sleep(delay / 1000.0)  # 转换为秒
                
        @self.app.route("/", methods=["GET"])
        def health_check():
            """健康检查"""
            return jsonify({
                "status": "running",
                "message": "Mock Server is running",
                "config": {
                    "host": self.config["host"],
                    "port": self.config["port"],
                    "routes_count": len(self.data_manager.get_all_routes())
                }
            })
            
        @self.app.route("/_mock/routes", methods=["GET"])
        def list_routes():
            """列出所有路由"""
            return jsonify(self.data_manager.get_all_routes())
            
        @self.app.route("/_mock/routes", methods=["POST"])
        def add_route():
            """添加路由"""
            try:
                route_data = request.get_json()
                if not route_data:
                    return jsonify({"error": "无效的请求数据"}), 400
                    
                self.data_manager.add_route(route_data)
                return jsonify({"message": "路由添加成功"}), 201
            except Exception as e:
                return jsonify({"error": str(e)}), 400
                
        @self.app.route("/_mock/routes/<route_id>", methods=["PUT"])
        def update_route(route_id):
            """更新路由"""
            try:
                route_data = request.get_json()
                if not route_data:
                    return jsonify({"error": "无效的请求数据"}), 400
                    
                self.data_manager.update_route(route_id, route_data)
                return jsonify({"message": "路由更新成功"})
            except Exception as e:
                return jsonify({"error": str(e)}), 400
                
        @self.app.route("/_mock/routes/<route_id>", methods=["DELETE"])
        def delete_route(route_id):
            """删除路由"""
            try:
                self.data_manager.delete_route(route_id)
                return jsonify({"message": "路由删除成功"})
            except Exception as e:
                return jsonify({"error": str(e)}), 404
                
        @self.app.route("/_mock/data", methods=["GET"])
        def get_mock_data():
            """获取Mock数据"""
            return jsonify(self.data_manager.get_all_data())
            
        @self.app.route("/_mock/data", methods=["POST"])
        def set_mock_data():
            """设置Mock数据"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "无效的数据"}), 400
                    
                self.data_manager.set_data(data)
                return jsonify({"message": "数据设置成功"})
            except Exception as e:
                return jsonify({"error": str(e)}), 400
                
        @self.app.route("/_mock/reset", methods=["POST"])
        def reset_mock():
            """重置Mock数据"""
            self.data_manager.reset()
            return jsonify({"message": "Mock数据已重置"})
            
        # 通用路由处理
        @self.app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        def handle_request(path):
            """处理所有请求"""
            return self._handle_mock_request(f"/{path}")
            
        @self.app.route("/", methods=["POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        def handle_root_request():
            """处理根路径请求"""
            return self._handle_mock_request("/")
            
    def _handle_mock_request(self, path: str) -> Response:
        """
        处理Mock请求
        
        Args:
            path: 请求路径
            
        Returns:
            Response: Flask响应对象
        """
        method = request.method
        
        # 记录请求信息
        self.logger.info(f"Mock请求: {method} {path}")
        
        try:
            # 查找匹配的路由
            mock_response = self.data_manager.find_response(method, path, request)
            
            if mock_response:
                # 构建响应
                status_code = mock_response.get("status_code", 200)
                headers = mock_response.get("headers", {})
                body = mock_response.get("body", {})
                
                # 处理动态响应
                if callable(body):
                    body = body(request)
                    
                response = jsonify(body) if isinstance(body, (dict, list)) else Response(str(body))
                response.status_code = status_code
                
                # 设置响应头
                for key, value in headers.items():
                    response.headers[key] = value
                    
                return response
            else:
                # 没有找到匹配的路由，返回404
                error_response = jsonify({
                    "error": "Not Found",
                    "message": f"No mock data found for {method} {path}",
                    "path": path,
                    "method": method
                })
                error_response.status_code = 404
                return error_response
                
        except Exception as e:
            self.logger.error(f"处理Mock请求失败: {str(e)}")
            error_response = jsonify({
                "error": "Internal Server Error",
                "message": str(e)
            })
            error_response.status_code = 500
            return error_response
            
    def add_route(self, method: str, path: str, response: Dict[str, Any]):
        """
        添加路由
        
        Args:
            method: HTTP方法
            path: 路径
            response: 响应数据
        """
        route_data = {
            "method": method.upper(),
            "path": path,
            "response": response
        }
        self.data_manager.add_route(route_data)
        
    def remove_route(self, method: str, path: str):
        """
        删除路由
        
        Args:
            method: HTTP方法
            path: 路径
        """
        route_id = f"{method.upper()}_{path}"
        self.data_manager.delete_route(route_id)
        
    def load_routes_from_file(self, file_path: str):
        """
        从文件加载路由
        
        Args:
            file_path: 文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    routes_data = json.load(f)
                else:
                    import yaml
                    routes_data = yaml.safe_load(f)
                    
            if isinstance(routes_data, list):
                for route in routes_data:
                    self.data_manager.add_route(route)
            elif isinstance(routes_data, dict) and "routes" in routes_data:
                for route in routes_data["routes"]:
                    self.data_manager.add_route(route)
                    
            self.logger.info(f"从文件加载路由成功: {file_path}")
        except Exception as e:
            self.logger.error(f"从文件加载路由失败: {file_path} - {str(e)}")
            
    def save_routes_to_file(self, file_path: str):
        """
        保存路由到文件
        
        Args:
            file_path: 文件路径
        """
        try:
            routes = self.data_manager.get_all_routes()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    json.dump({"routes": routes}, f, indent=2, ensure_ascii=False)
                else:
                    import yaml
                    yaml.dump({"routes": routes}, f, default_flow_style=False, allow_unicode=True)
                    
            self.logger.info(f"保存路由到文件成功: {file_path}")
        except Exception as e:
            self.logger.error(f"保存路由到文件失败: {file_path} - {str(e)}")
            
    def start(self, threaded: bool = True):
        """
        启动服务器
        
        Args:
            threaded: 是否在线程中运行
        """
        host = self.config["host"]
        port = self.config["port"]
        debug = self.config.get("debug", False)
        
        if threaded:
            self._server_thread = threading.Thread(
                target=lambda: self.app.run(host=host, port=port, debug=debug, use_reloader=False)
            )
            self._server_thread.daemon = True
            self._server_thread.start()
            self._running = True
            self.logger.info(f"Mock服务器已在线程中启动: http://{host}:{port}")
        else:
            self.logger.info(f"Mock服务器启动: http://{host}:{port}")
            self.app.run(host=host, port=port, debug=debug)
            
    def stop(self):
        """停止服务器"""
        self._running = False
        if self._server_thread:
            self.logger.info("Mock服务器已停止")
            
    def is_running(self) -> bool:
        """检查服务器是否运行中"""
        return self._running
        
    def get_server_url(self) -> str:
        """获取服务器URL"""
        host = self.config["host"]
        port = self.config["port"]
        return f"http://{host}:{port}"