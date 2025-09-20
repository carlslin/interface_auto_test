"""
数据验证器模块
负责验证API响应数据的格式和内容
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from jsonschema import validate, ValidationError, Draft7Validator
from jsonschema.exceptions import SchemaError


class ResponseValidator:
    """响应验证器"""
    
    def __init__(self):
        """初始化响应验证器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def validate_status_code(self, actual: int, expected: Union[int, List[int]]) -> bool:
        """
        验证状态码
        
        Args:
            actual: 实际状态码
            expected: 期望状态码或状态码列表
            
        Returns:
            bool: 验证结果
        """
        if isinstance(expected, int):
            expected = [expected]
        
        is_valid = actual in expected
        if not is_valid:
            self.logger.error(f"状态码验证失败: 期望 {expected}, 实际 {actual}")
        return is_valid
        
    def validate_response_time(self, actual: float, max_time: float) -> bool:
        """
        验证响应时间
        
        Args:
            actual: 实际响应时间(秒)
            max_time: 最大允许响应时间(秒)
            
        Returns:
            bool: 验证结果
        """
        is_valid = actual <= max_time
        if not is_valid:
            self.logger.error(f"响应时间验证失败: 期望 ≤{max_time}s, 实际 {actual}s")
        return is_valid
        
    def validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        验证JSON数据结构
        
        Args:
            data: 待验证的数据
            schema: JSON Schema
            
        Returns:
            bool: 验证结果
        """
        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            self.logger.error(f"JSON Schema验证失败: {e.message}")
            return False
        except SchemaError as e:
            self.logger.error(f"JSON Schema格式错误: {e.message}")
            return False
        except Exception as e:
            self.logger.error(f"JSON Schema验证异常: {str(e)}")
            return False
            
    def validate_field_exists(self, data: Dict[str, Any], field_path: str) -> bool:
        """
        验证字段是否存在
        
        Args:
            data: 数据
            field_path: 字段路径，支持点号分隔的嵌套路径
            
        Returns:
            bool: 验证结果
        """
        try:
            fields = field_path.split('.')
            current_data = data
            
            for field in fields:
                if isinstance(current_data, dict) and field in current_data:
                    current_data = current_data[field]
                else:
                    self.logger.error(f"字段不存在: {field_path}")
                    return False
                    
            return True
        except Exception as e:
            self.logger.error(f"字段验证异常: {str(e)}")
            return False
            
    def validate_field_value(self, data: Dict[str, Any], field_path: str, 
                           expected_value: Any, comparison: str = "equal") -> bool:
        """
        验证字段值
        
        Args:
            data: 数据
            field_path: 字段路径
            expected_value: 期望值
            comparison: 比较方式 (equal, not_equal, greater, less, contains, not_contains)
            
        Returns:
            bool: 验证结果
        """
        try:
            # 首先检查字段是否存在
            if not self.validate_field_exists(data, field_path):
                return False
                
            # 获取字段值
            fields = field_path.split('.')
            actual_value = data
            for field in fields:
                actual_value = actual_value[field]
                
            # 根据比较方式进行验证
            if comparison == "equal":
                is_valid = actual_value == expected_value
            elif comparison == "not_equal":
                is_valid = actual_value != expected_value
            elif comparison == "greater":
                is_valid = actual_value > expected_value
            elif comparison == "less":
                is_valid = actual_value < expected_value
            elif comparison == "contains":
                is_valid = expected_value in actual_value
            elif comparison == "not_contains":
                is_valid = expected_value not in actual_value
            else:
                self.logger.error(f"不支持的比较方式: {comparison}")
                return False
                
            if not is_valid:
                self.logger.error(f"字段值验证失败: {field_path} {comparison} {expected_value}, 实际值: {actual_value}")
                
            return is_valid
        except Exception as e:
            self.logger.error(f"字段值验证异常: {str(e)}")
            return False
            
    def validate_field_type(self, data: Dict[str, Any], field_path: str, expected_type: str) -> bool:
        """
        验证字段类型
        
        Args:
            data: 数据
            field_path: 字段路径
            expected_type: 期望类型 (string, number, integer, boolean, array, object, null)
            
        Returns:
            bool: 验证结果
        """
        try:
            if not self.validate_field_exists(data, field_path):
                return False
                
            # 获取字段值
            fields = field_path.split('.')
            actual_value = data
            for field in fields:
                actual_value = actual_value[field]
                
            # 类型映射
            type_map = {
                "string": str,
                "number": (int, float),
                "integer": int,
                "boolean": bool,
                "array": list,
                "object": dict,
                "null": type(None)
            }
            
            if expected_type not in type_map:
                self.logger.error(f"不支持的类型: {expected_type}")
                return False
                
            expected_python_type = type_map[expected_type]
            is_valid = isinstance(actual_value, expected_python_type)
            
            if not is_valid:
                self.logger.error(f"字段类型验证失败: {field_path} 期望类型 {expected_type}, 实际类型 {type(actual_value).__name__}")
                
            return is_valid
        except Exception as e:
            self.logger.error(f"字段类型验证异常: {str(e)}")
            return False
            
    def validate_array_length(self, data: Dict[str, Any], field_path: str, 
                            min_length: Optional[int] = None, max_length: Optional[int] = None) -> bool:
        """
        验证数组长度
        
        Args:
            data: 数据
            field_path: 字段路径
            min_length: 最小长度
            max_length: 最大长度
            
        Returns:
            bool: 验证结果
        """
        try:
            if not self.validate_field_exists(data, field_path):
                return False
                
            # 获取字段值
            fields = field_path.split('.')
            actual_value = data
            for field in fields:
                actual_value = actual_value[field]
                
            if not isinstance(actual_value, (list, str)):
                self.logger.error(f"字段 {field_path} 不是数组或字符串类型")
                return False
                
            actual_length = len(actual_value)
            
            # 验证最小长度
            if min_length is not None and actual_length < min_length:
                self.logger.error(f"数组长度验证失败: {field_path} 最小长度 {min_length}, 实际长度 {actual_length}")
                return False
                
            # 验证最大长度
            if max_length is not None and actual_length > max_length:
                self.logger.error(f"数组长度验证失败: {field_path} 最大长度 {max_length}, 实际长度 {actual_length}")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"数组长度验证异常: {str(e)}")
            return False
            
    def validate_multiple_conditions(self, data: Dict[str, Any], 
                                   conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证多个条件
        
        Args:
            data: 数据
            conditions: 条件列表，每个条件包含验证类型和参数
            
        Returns:
            Dict[str, Any]: 验证结果汇总
        """
        results = {
            "total": len(conditions),
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for i, condition in enumerate(conditions):
            try:
                condition_type = condition.get("type")
                condition_name = condition.get("name", f"condition_{i+1}")
                
                if condition_type == "field_exists":
                    result = self.validate_field_exists(data, condition["field_path"])
                elif condition_type == "field_value":
                    result = self.validate_field_value(
                        data, condition["field_path"], 
                        condition["expected_value"], 
                        condition.get("comparison", "equal")
                    )
                elif condition_type == "field_type":
                    result = self.validate_field_type(data, condition["field_path"], condition["expected_type"])
                elif condition_type == "array_length":
                    result = self.validate_array_length(
                        data, condition["field_path"],
                        condition.get("min_length"), 
                        condition.get("max_length")
                    )
                elif condition_type == "json_schema":
                    result = self.validate_json_schema(data, condition["schema"])
                else:
                    result = False
                    self.logger.error(f"不支持的验证类型: {condition_type}")
                    
                if result:
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                    
                results["details"].append({
                    "name": condition_name,
                    "type": condition_type,
                    "result": result
                })
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "name": condition.get("name", f"condition_{i+1}"),
                    "type": condition.get("type", "unknown"),
                    "result": False,
                    "error": str(e)
                })
                self.logger.error(f"条件验证异常: {str(e)}")
                
        results["success_rate"] = results["passed"] / results["total"] if results["total"] > 0 else 0
        return results