"""
=============================================================================
接口自动化测试框架 - DeepSeek AI 客户端模块
=============================================================================

本模块提供了与DeepSeek AI API的完整集成，支持智能化的接口测试功能。
DeepSeek是一个强大的AI模型，能够理解代码、生成测试用例、分析API文档等。

主要功能：
1. 智能测试用例生成 - 根据API文档自动生成测试用例
2. 代码质量分析 - 分析测试代码质量并提供改进建议
3. 智能断言生成 - 自动生成合适的断言逻辑
4. 测试数据生成 - 生成符合业务逻辑的测试数据
5. 自然语言交互 - 支持自然语言描述测试需求
6. 错误诊断 - 智能分析测试失败原因

技术特性：
- 支持流式和非流式响应
- 完整的错误处理和重试机制
- 请求和响应的详细日志记录
- 支持多种模型和参数配置
- 自动化的token使用统计

API文档: https://api-docs.deepseek.com/zh-cn/

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

from __future__ import annotations

import json
import logging
import requests
import time
from typing import Dict, Any, List, Optional, Generator, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class AIModel(Enum):
    """AI模型枚举"""
    DEEPSEEK_CHAT = "deepseek-chat"           # 通用对话模型
    DEEPSEEK_CODER = "deepseek-coder"         # 代码生成模型
    DEEPSEEK_REASONER = "deepseek-reasoner"   # 推理模型


class FinishReason(Enum):
    """完成原因枚举"""
    STOP = "stop"                    # 正常完成
    LENGTH = "length"                # 达到最大长度
    CONTENT_FILTER = "content_filter"  # 内容过滤
    FUNCTION_CALL = "function_call"  # 函数调用


@dataclass
class AIResponse:
    """
    AI响应数据类
    
    用于封装DeepSeek AI API的响应数据，包含完整的响应信息：
    - 响应内容：AI生成的内容
    - 使用统计：token使用情况
    - 模型信息：使用的模型和完成原因
    - 错误信息：如果请求失败的错误详情
    
    Attributes:
        success: 请求是否成功
        content: AI生成的内容
        usage: token使用统计信息
        model: 使用的AI模型
        finish_reason: 完成原因
        error: 错误信息（如果请求失败）
        response_time: 响应时间（秒）
        request_id: 请求ID（用于追踪）
    """
    success: bool
    content: str
    usage: Dict[str, Any] = field(default_factory=dict)
    model: str = ""
    finish_reason: str = ""
    error: Optional[str] = None
    response_time: float = 0.0
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'success': self.success,
            'content': self.content,
            'usage': self.usage,
            'model': self.model,
            'finish_reason': self.finish_reason,
            'error': self.error,
            'response_time': self.response_time,
            'request_id': self.request_id
        }


class DeepSeekClient:
    """
    DeepSeek AI客户端 - 接口自动化测试的AI增强核心
    
    本客户端提供了与DeepSeek AI API的完整集成，支持智能化的接口测试功能。
    通过AI能力，可以大幅提升测试用例的质量和覆盖率。
    
    主要功能：
    1. 智能测试生成: 根据API文档自动生成高质量的测试用例
    2. 代码质量分析: 分析测试代码并提供改进建议
    3. 智能断言生成: 自动生成合适的断言逻辑
    4. 测试数据生成: 生成符合业务逻辑的测试数据
    5. 自然语言交互: 支持自然语言描述测试需求
    6. 错误诊断: 智能分析测试失败原因
    
    技术特性：
    - 支持流式和非流式响应
    - 完整的错误处理和重试机制
    - 请求和响应的详细日志记录
    - 支持多种模型和参数配置
    - 自动化的token使用统计
    
    使用示例：
        client = DeepSeekClient("your-api-key")
        
        # 生成测试用例
        response = client.generate_test_cases(api_doc, "用户管理API")
        
        # 分析代码质量
        analysis = client.analyze_code_quality(test_code)
        
        # 生成测试数据
        data = client.generate_test_data("用户信息", {"name": "string", "age": "integer"})
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        """
        初始化DeepSeek客户端
        
        初始化过程包括：
        - 设置API密钥和基础URL
        - 配置HTTP会话和请求头
        - 初始化日志记录器
        - 设置默认参数
        
        Args:
            api_key: DeepSeek API密钥，从DeepSeek平台获取
            base_url: API基础URL，默认为官方地址
        
        Raises:
            ValueError: API密钥为空或格式不正确
            ConnectionError: 无法连接到DeepSeek API服务
        """
        # 验证API密钥
        if not api_key or not api_key.strip():
            raise ValueError("API密钥不能为空")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 配置HTTP会话
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'InterfaceAutoTest/1.0'
        })
        
        # 设置请求超时和重试
        self.session.timeout = 60
        self.max_retries = 3
        
        # 默认模型配置
        self.default_model = AIModel.DEEPSEEK_CHAT.value
        self.default_temperature = 0.3  # 较低的温度确保输出稳定性
        self.default_max_tokens = 4000  # 足够的token数量
        
        # 使用统计
        self.usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'successful_requests': 0,
            'failed_requests': 0
        }
        
        self.logger.info(f"DeepSeek客户端初始化完成，使用模型: {self.default_model}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> AIResponse:
        """
        发送聊天完成请求
        
        这是与DeepSeek AI交互的核心方法，支持多种参数配置和响应模式。
        方法会自动处理请求重试、错误处理和响应解析。
        
        Args:
            messages: 对话消息列表，格式为 [{"role": "user", "content": "消息内容"}]
            model: 使用的模型名称，可选值：
                  - "deepseek-chat": 通用对话模型（默认）
                  - "deepseek-coder": 代码生成模型
                  - "deepseek-reasoner": 推理模型
            temperature: 创造性参数，范围0.0-2.0：
                        - 0.0: 完全确定性输出
                        - 0.3: 平衡创造性和稳定性（默认）
                        - 1.0: 标准创造性
                        - 2.0: 高创造性
            max_tokens: 最大生成token数，默认4000
            stream: 是否使用流式响应，默认False
            
        Returns:
            AIResponse: 包含完整响应信息的AI响应对象
        
        Raises:
            ValueError: 消息格式不正确或参数无效
            ConnectionError: 网络连接失败
            TimeoutError: 请求超时
        
        使用示例:
            # 基本对话
            messages = [{"role": "user", "content": "请生成一个用户登录的测试用例"}]
            response = client.chat_completion(messages)
            
            # 使用特定模型
            response = client.chat_completion(messages, model="deepseek-coder")
            
            # 调整创造性
            response = client.chat_completion(messages, temperature=0.7)
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature or self.default_temperature,
            "max_tokens": max_tokens or self.default_max_tokens,
            "stream": stream
        }
        
        try:
            self.logger.debug(f"发送请求到 DeepSeek API: {url}")
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # 解析响应
            if 'choices' in result and len(result['choices']) > 0:
                choice = result['choices'][0]
                return AIResponse(
                    success=True,
                    content=choice['message']['content'],
                    usage=result.get('usage', {}),
                    model=result.get('model', model or self.default_model),
                    finish_reason=choice.get('finish_reason', 'stop')
                )
            else:
                return AIResponse(
                    success=False,
                    content="",
                    usage={},
                    model=model or self.default_model,
                    finish_reason="error",
                    error="响应格式异常"
                )
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败: {e}")
            return AIResponse(
                success=False,
                content="",
                usage={},
                model=model or self.default_model,
                finish_reason="error",
                error=f"请求异常: {str(e)}"
            )
        except Exception as e:
            self.logger.error(f"处理异常: {e}")
            return AIResponse(
                success=False,
                content="",
                usage={},
                model=model or self.default_model,
                finish_reason="error",
                error=f"处理异常: {str(e)}"
            )
    
    def generate_code(
        self,
        prompt: str,
        language: str = "python",
        context: Optional[str] = None
    ) -> AIResponse:
        """
        生成代码
        
        Args:
            prompt: 代码生成提示
            language: 编程语言
            context: 上下文信息
            
        Returns:
            AIResponse: 生成的代码响应
        """
        system_message = f"""你是一个专业的{language}程序员，专门编写高质量、可维护的代码。
请根据用户的需求生成相应的代码，确保：
1. 代码结构清晰，逻辑合理
2. 包含必要的注释和文档
3. 遵循最佳编程实践
4. 考虑错误处理和边界条件
5. 代码可读性和可维护性强"""

        messages = [
            {"role": "system", "content": system_message}
        ]
        
        if context:
            messages.append({
                "role": "user",
                "content": f"上下文信息：\n{context}\n\n"
            })
        
        messages.append({
            "role": "user",
            "content": f"请生成{language}代码：\n{prompt}"
        })
        
        return self.chat_completion(messages, temperature=0.2)
    
    def review_code(
        self,
        code: str,
        language: str = "python",
        focus_areas: Optional[List[str]] = None
    ) -> AIResponse:
        """
        代码审查
        
        Args:
            code: 待审查的代码
            language: 编程语言
            focus_areas: 重点关注的方面
            
        Returns:
            AIResponse: 代码审查结果
        """
        focus_prompt = ""
        if focus_areas:
            focus_prompt = f"\n特别关注以下方面：{', '.join(focus_areas)}"
        
        system_message = f"""你是一个经验丰富的{language}代码审查专家。
请对提供的代码进行全面的质量审查，从以下方面分析：
1. 代码逻辑和正确性
2. 性能优化建议
3. 安全性问题
4. 可维护性和可读性
5. 最佳实践遵循情况
6. 潜在的bug和边界条件{focus_prompt}

请提供具体的改进建议和优化方案。"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"请审查以下{language}代码：\n\n```{language}\n{code}\n```"}
        ]
        
        return self.chat_completion(messages, temperature=0.1)
    
    def analyze_api_doc(
        self,
        api_doc: str,
        doc_format: str = "openapi"
    ) -> AIResponse:
        """
        分析API文档
        
        Args:
            api_doc: API文档内容
            doc_format: 文档格式 (openapi, postman, etc.)
            
        Returns:
            AIResponse: API分析结果
        """
        system_message = f"""你是一个API文档分析专家，专门分析{doc_format}格式的API文档。
请对提供的API文档进行全面分析，包括：
1. API接口概览和分类
2. 关键功能点识别
3. 参数和响应结构分析
4. 潜在的测试场景识别
5. 边界条件和异常情况分析
6. 安全性和认证机制
7. 测试用例生成建议

请提供结构化的分析结果。"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"请分析以下{doc_format}格式的API文档：\n\n{api_doc}"}
        ]
        
        return self.chat_completion(messages, temperature=0.2)
    
    def generate_test_cases(
        self,
        api_spec: Dict[str, Any],
        test_type: str = "functional"
    ) -> AIResponse:
        """
        生成测试用例
        
        Args:
            api_spec: API规范信息
            test_type: 测试类型 (functional, performance, security, etc.)
            
        Returns:
            AIResponse: 生成的测试用例
        """
        spec_str = json.dumps(api_spec, ensure_ascii=False, indent=2)
        
        system_message = f"""你是一个专业的API测试专家，专门设计{test_type}测试用例。
请根据提供的API规范生成全面的测试用例，包括：
1. 正常流程测试用例
2. 边界值测试用例
3. 异常情况测试用例
4. 安全性测试用例
5. 性能测试场景
6. 数据验证测试

每个测试用例应包含：
- 测试目标和描述
- 前置条件
- 测试步骤
- 预期结果
- 断言验证点
- 测试数据示例"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"请为以下API规范生成{test_type}测试用例：\n\n{spec_str}"}
        ]
        
        return self.chat_completion(messages, temperature=0.3)
    
    def optimize_test_data(
        self,
        data_schema: Dict[str, Any],
        test_scenarios: List[str]
    ) -> AIResponse:
        """
        优化测试数据
        
        Args:
            data_schema: 数据模式
            test_scenarios: 测试场景列表
            
        Returns:
            AIResponse: 优化的测试数据
        """
        schema_str = json.dumps(data_schema, ensure_ascii=False, indent=2)
        scenarios_str = '\n'.join([f"- {scenario}" for scenario in test_scenarios])
        
        system_message = """你是一个测试数据生成专家，专门为API测试创建高质量的测试数据。
请根据数据模式和测试场景生成优化的测试数据，确保：
1. 数据覆盖各种边界条件
2. 包含正常和异常数据组合
3. 考虑真实业务场景
4. 数据格式正确且有意义
5. 包含性能测试所需的大数据集
6. 安全测试相关的特殊数据"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"数据模式：\n{schema_str}\n\n测试场景：\n{scenarios_str}\n\n请生成优化的测试数据。"}
        ]
        
        return self.chat_completion(messages, temperature=0.4)
    
    def suggest_assertions(
        self,
        api_endpoint: Dict[str, Any],
        response_examples: List[Dict[str, Any]]
    ) -> AIResponse:
        """
        建议断言验证
        
        Args:
            api_endpoint: API端点信息
            response_examples: 响应示例
            
        Returns:
            AIResponse: 建议的断言
        """
        endpoint_str = json.dumps(api_endpoint, ensure_ascii=False, indent=2)
        examples_str = json.dumps(response_examples, ensure_ascii=False, indent=2)
        
        system_message = """你是一个API测试专家，专门设计全面的断言验证策略。
请根据API端点信息和响应示例，建议详细的断言验证点，包括：
1. 状态码验证
2. 响应头验证
3. 响应体结构验证
4. 数据类型验证
5. 业务逻辑验证
6. 性能指标验证
7. 安全性验证

请提供具体的验证代码和逻辑。"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"API端点：\n{endpoint_str}\n\n响应示例：\n{examples_str}\n\n请建议详细的断言验证策略。"}
        ]
        
        return self.chat_completion(messages, temperature=0.2)
    
    def explain_error(
        self,
        error_message: str,
        code_context: Optional[str] = None
    ) -> AIResponse:
        """
        解释错误信息
        
        Args:
            error_message: 错误信息
            code_context: 相关代码上下文
            
        Returns:
            AIResponse: 错误解释和解决方案
        """
        context_prompt = ""
        if code_context:
            context_prompt = f"\n\n相关代码：\n```python\n{code_context}\n```"
        
        system_message = """你是一个专业的调试专家，专门帮助开发者理解和解决各种错误。
请对提供的错误信息进行详细分析，包括：
1. 错误原因分析
2. 可能的触发条件
3. 具体的解决方案
4. 预防措施建议
5. 相关最佳实践

请提供清晰易懂的解释和可操作的解决步骤。"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"错误信息：\n{error_message}{context_prompt}\n\n请分析并提供解决方案。"}
        ]
        
        return self.chat_completion(messages, temperature=0.1)
    
    def validate_api_key(self) -> bool:
        """
        验证API密钥是否有效
        
        Returns:
            bool: 密钥是否有效
        """
        try:
            response = self.chat_completion([
                {"role": "user", "content": "Hello"}
            ], max_tokens=10)
            return response.success
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict: 模型信息
        """
        return {
            "default_model": self.default_model,
            "base_url": self.base_url,
            "max_tokens": self.default_max_tokens,
            "temperature": self.default_temperature,
            "api_key_valid": self.validate_api_key()
        }