"""
数据生成器模块
使用Faker库生成测试数据
"""

import random
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from faker import Faker
from faker.providers import BaseProvider
import uuid


class CustomProvider(BaseProvider):
    """自定义数据提供者"""
    
    def api_key(self) -> str:
        """生成API密钥"""
        return f"ak-{uuid.uuid4().hex[:16]}"
        
    def user_id(self) -> str:
        """生成用户ID"""
        return str(random.randint(10000, 99999))
        
    def order_number(self) -> str:
        """生成订单号"""
        return f"ORD{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        
    def status_code(self) -> int:
        """生成常见HTTP状态码"""
        codes = [200, 201, 204, 400, 401, 403, 404, 500]
        return random.choice(codes)


class DataFaker:
    """数据生成器"""
    
    def __init__(self, locale: str = "zh_CN"):
        """
        初始化数据生成器
        
        Args:
            locale: 本地化设置
        """
        self.faker = Faker(locale)
        self.faker.add_provider(CustomProvider)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 常用数据模板
        self.templates = {
            "user": {
                "id": "user_id",
                "name": "name",
                "email": "email",
                "phone": "phone_number",
                "age": "random_int:18:80",
                "address": "address",
                "created_at": "datetime"
            },
            "product": {
                "id": "uuid4",
                "name": "word",
                "price": "random_int:1:1000",
                "description": "sentence",
                "category": "word",
                "stock": "random_int:0:100"
            },
            "order": {
                "order_number": "order_number",
                "user_id": "user_id",
                "total_amount": "random_int:10:500",
                "status": "random_element:pending,processing,completed,cancelled",
                "created_at": "datetime"
            }
        }
        
    def generate_by_type(self, data_type: str, **kwargs) -> Any:
        """
        根据类型生成数据
        
        Args:
            data_type: 数据类型
            **kwargs: 额外参数
            
        Returns:
            Any: 生成的数据
        """
        try:
            # 处理带参数的类型 (如 random_int:1:100)
            if ":" in data_type:
                parts = data_type.split(":")
                base_type = parts[0]
                params = parts[1:]
                
                if base_type == "random_int":
                    min_val = int(params[0]) if len(params) > 0 else 0
                    max_val = int(params[1]) if len(params) > 1 else 100
                    return self.faker.random_int(min=min_val, max=max_val)
                elif base_type == "random_element":
                    elements = params[0].split(",") if len(params) > 0 else ["a", "b", "c"]
                    return self.faker.random_element(elements=elements)
                elif base_type == "random_float":
                    min_val = float(params[0]) if len(params) > 0 else 0.0
                    max_val = float(params[1]) if len(params) > 1 else 100.0
                    return round(random.uniform(min_val, max_val), 2)
                    
            # 基础类型生成
            if hasattr(self.faker, data_type):
                return getattr(self.faker, data_type)()
            else:
                self.logger.warning(f"未知的数据类型: {data_type}")
                return f"unknown_type_{data_type}"
                
        except Exception as e:
            self.logger.error(f"生成数据失败: {data_type} - {str(e)}")
            return None
            
    def generate_from_template(self, template_name: str, count: int = 1) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        根据模板生成数据
        
        Args:
            template_name: 模板名称
            count: 生成数量
            
        Returns:
            Union[Dict[str, Any], List[Dict[str, Any]]]: 生成的数据
        """
        if template_name not in self.templates:
            self.logger.error(f"模板不存在: {template_name}")
            return {} if count == 1 else []
            
        template = self.templates[template_name]
        
        def generate_single():
            result = {}
            for field, data_type in template.items():
                result[field] = self.generate_by_type(data_type)
            return result
            
        if count == 1:
            return generate_single()
        else:
            return [generate_single() for _ in range(count)]
            
    def generate_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据JSON Schema生成数据
        
        Args:
            schema: JSON Schema
            
        Returns:
            Dict[str, Any]: 生成的数据
        """
        def generate_value(prop_schema: Dict[str, Any]) -> Any:
            prop_type = prop_schema.get("type", "string")
            
            if prop_type == "string":
                if "enum" in prop_schema:
                    return random.choice(prop_schema["enum"])
                elif "format" in prop_schema:
                    format_type = prop_schema["format"]
                    if format_type == "email":
                        return self.faker.email()
                    elif format_type == "date":
                        return self.faker.date()
                    elif format_type == "date-time":
                        return self.faker.iso8601()
                    elif format_type == "uuid":
                        return str(self.faker.uuid4())
                else:
                    min_length = prop_schema.get("minLength", 1)
                    max_length = prop_schema.get("maxLength", 20)
                    return self.faker.pystr(min_chars=min_length, max_chars=max_length)
                    
            elif prop_type == "integer":
                minimum = prop_schema.get("minimum", 0)
                maximum = prop_schema.get("maximum", 1000)
                return self.faker.random_int(min=minimum, max=maximum)
                
            elif prop_type == "number":
                minimum = prop_schema.get("minimum", 0.0)
                maximum = prop_schema.get("maximum", 1000.0)
                return round(random.uniform(minimum, maximum), 2)
                
            elif prop_type == "boolean":
                return self.faker.boolean()
                
            elif prop_type == "array":
                items_schema = prop_schema.get("items", {"type": "string"})
                min_items = prop_schema.get("minItems", 1)
                max_items = prop_schema.get("maxItems", 5)
                count = random.randint(min_items, max_items)
                return [generate_value(items_schema) for _ in range(count)]
                
            elif prop_type == "object":
                if "properties" in prop_schema:
                    return self.generate_from_schema(prop_schema)
                else:
                    return {}
                    
            return None
            
        result = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # 生成必需字段
        for field in required:
            if field in properties:
                result[field] = generate_value(properties[field])
                
        # 随机生成一些可选字段
        optional_fields = [f for f in properties.keys() if f not in required]
        selected_optional = random.sample(
            optional_fields, 
            min(len(optional_fields), random.randint(0, len(optional_fields)))
        )
        
        for field in selected_optional:
            result[field] = generate_value(properties[field])
            
        return result
        
    def generate_test_data_set(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成测试数据集
        
        Args:
            config: 生成配置
            
        Returns:
            Dict[str, Any]: 测试数据集
        """
        dataset = {}
        
        for data_name, data_config in config.items():
            try:
                if "template" in data_config:
                    # 使用模板生成
                    template_name = data_config["template"]
                    count = data_config.get("count", 1)
                    dataset[data_name] = self.generate_from_template(template_name, count)
                    
                elif "schema" in data_config:
                    # 使用Schema生成
                    schema = data_config["schema"]
                    count = data_config.get("count", 1)
                    if count == 1:
                        dataset[data_name] = self.generate_from_schema(schema)
                    else:
                        dataset[data_name] = [self.generate_from_schema(schema) for _ in range(count)]
                        
                elif "type" in data_config:
                    # 使用类型生成
                    data_type = data_config["type"]
                    count = data_config.get("count", 1)
                    if count == 1:
                        dataset[data_name] = self.generate_by_type(data_type)
                    else:
                        dataset[data_name] = [self.generate_by_type(data_type) for _ in range(count)]
                        
            except Exception as e:
                self.logger.error(f"生成数据集失败: {data_name} - {str(e)}")
                dataset[data_name] = None
                
        return dataset
        
    def add_template(self, name: str, template: Dict[str, str]):
        """
        添加自定义模板
        
        Args:
            name: 模板名称
            template: 模板定义
        """
        self.templates[name] = template
        self.logger.info(f"添加模板: {name}")
        
    def get_available_types(self) -> List[str]:
        """获取可用的数据类型"""
        basic_types = [
            "name", "email", "phone_number", "address", "word", "sentence",
            "text", "uuid4", "date", "datetime", "time", "url", "ipv4",
            "user_agent", "currency_code", "country", "city", "boolean"
        ]
        
        param_types = [
            "random_int:min:max", "random_float:min:max", "random_element:a,b,c"
        ]
        
        custom_types = [
            "api_key", "user_id", "order_number", "status_code"
        ]
        
        return basic_types + param_types + custom_types