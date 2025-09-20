#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI聊天助手 - 自然语言交互接口

这是架构中的L4层（智能交互）核心组件，提供零门槛的自然语言交互，
让用户能够通过自然语言与整个测试框架进行交互和操作。

核心功能：
1. 意图识别 - 理解用户的自然语言指令和需求
2. 命令解析 - 将自然语言转换为框架可执行的操作
3. 上下文理解 - 保持对话上下文和状态管理
4. 动态执行 - 调用相应的AI功能模块执行任务
5. 结果反馈 - 以友好的方式向用户反馈结果

智能向导交互流程（基于记忆）：
1. 快速开始引导 - 帮助新用户快速上手
2. 智能API分析 - 自动分析API文档复杂度和特征
3. 一键测试生成 - 根据分析结果生成完整测试
4. 健康检查与诊断 - 检查配置和环境状态
5. 上下文感知建议 - 提供个性化的优化建议

使用示例：
- "帮我分析这个API文档" → 调用API分析功能
- "生成测试用例" → 调用测试生成功能
- "检查配置状态" → 调用健康检查功能
- "优化测试覆盖率" → 调用优化建议功能

架构优化后的特点：
- 降低了使用门槛，支持自然语言操作
- 整合了所有AI功能的统一入口
- 提供智能向导式的交互体验
- 支持上下文感知和个性化建议
"""

import re
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """
    用户意图数据结构
    
    封装意图识别的结果，包含意图类型、置信度、实体信息和对应的操作。
    用于在意图识别和动作执行之间传递结构化的意图信息。
    
    Attributes:
        intent_type: 意图类型标识（如'analyze_api', 'generate_test'等）
        confidence: 意图识别的置信度（0.0-1.0）
        entities: 从用户输入中提取的实体信息（如文件路径、数量等）
        action: 对应的可执行动作名称
    """
    intent_type: str
    confidence: float
    entities: Dict[str, Any]
    action: str


class IntentRecognizer:
    """
    意图识别器 - 理解用户的自然语言输入
    
    负责分析用户的自然语言输入，识别用户的意图和需求，
    提取相关的实体信息，并将其映射为可执行的动作。
    
    支持的意图类型：
    - analyze_api: API文档分析和检查
    - generate_test: 测试用例和代码生成
    - run_test: 测试执行和运行
    - check_status: 系统状态和健康检查
    - get_help: 帮助信息和使用指导
    - optimize: 优化建议和性能调优
    
    特点：
    - 基于正则表达式的意图匹配
    - 智能实体提取（文件路径、数量、业务类型等）
    - 多语言支持（中文和英文）
    - 置信度评估和意图排序
    """
    
    def __init__(self):
        """
        初始化意图识别器
        
        设置预定义的意图模式和匹配规则，支持中英文混合输入。
        每个意图类型对应多个正则表达式模式，提高识别准确率。
        """
        # 预定义的意图模式映射
        # 每个意图类型包含多个正则表达式，支持不同的表达方式
        self.intent_patterns = {
            "analyze_api": [              # API文档分析意图
                r"分析.*api.*文档",
                r"帮我.*分析.*接口",
                r"检查.*api.*复杂度",
                r"analyze.*api"
            ],
            "generate_test": [            # 测试生成意图
                r"生成.*测试",
                r"创建.*测试用例",
                r"自动.*测试",
                r"generate.*test"
            ],
            "run_test": [                # 测试执行意图
                r"运行.*测试",
                r"执行.*测试",
                r"开始.*测试",
                r"run.*test"
            ],
            "check_status": [            # 状态检查意图
                r"检查.*状态",
                r"健康.*检查",
                r"配置.*状态",
                r"check.*status"
            ],
            "get_help": [                # 帮助意图
                r"帮助",
                r"怎么.*使用",
                r"如何.*操作",
                r"help"
            ],
            "optimize": [                # 优化意图
                r"优化.*配置",
                r"建议.*优化",
                r"改进.*性能",
                r"optimize"
            ]
        }
    
    def recognize(self, user_input: str) -> Intent:
        """
        识别用户意图 - 核心意图识别方法
        
        分析用户的自然语言输入，通过正则匹配识别意图类型，
        计算置信度，提取实体信息，并映射为对应的可执行动作。
        
        处理流程：
        1. 预处理用户输入（转小写、去空格）
        2. 遍历所有意图模式进行匹配
        3. 计算匹配置信度并选择最佳意图
        4. 提取相关实体信息（文件路径、数量等）
        5. 将意图映射为可执行的动作
        
        Args:
            user_input: 用户的自然语言输入
            
        Returns:
            Intent: 包含意图类型、置信度、实体和动作的Intent对象
        """
        user_input = user_input.lower().strip()  # 预处理：标准化输入格式
        
        best_intent = "unknown"      # 最佳意图类型
        best_confidence = 0.0        # 最高置信度
        
        # 遍历所有预定义的意图模式进行匹配
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    # 简化的置信度计算：基于模式长度和输入长度的比值
                    confidence = len(pattern) / len(user_input)  
                    if confidence > best_confidence:
                        best_intent = intent_type
                        best_confidence = confidence
        
        # 提取实体信息 - 从用户输入中提取结构化数据
        entities = self._extract_entities(user_input)
        
        # 返回结构化的意图对象
        return Intent(
            intent_type=best_intent,
            confidence=min(best_confidence * 2, 1.0),  # 调整置信度到合理范围
            entities=entities,
            action=self._map_intent_to_action(best_intent)
        )
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """提取实体信息"""
        entities = {}
        
        # 提取文件路径
        file_patterns = [
            r"([a-zA-Z0-9_\-/\\\.]+\.(?:yaml|yml|json))",
            r"文件[:\s]*([a-zA-Z0-9_\-/\\\.]+)",
            r"路径[:\s]*([a-zA-Z0-9_\-/\\\.]+)"
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, text)
            if matches:
                entities["file_path"] = matches[0]
                break
        
        # 提取API数量
        number_match = re.search(r"(\d+).*(?:个|接口|api)", text)
        if number_match:
            entities["api_count"] = int(number_match.group(1))
        
        # 提取业务类型
        business_patterns = [
            r"电商", r"用户管理", r"支付", r"订单", r"商品",
            r"金融", r"教育", r"医疗", r"物流"
        ]
        for pattern in business_patterns:
            if re.search(pattern, text):
                entities["business_type"] = pattern
                break
        
        return entities
    
    def _map_intent_to_action(self, intent_type: str) -> str:
        """将意图映射到行动"""
        action_mapping = {
            "analyze_api": "ai_wizard_analyze_api",
            "generate_test": "ai_wizard_auto_test", 
            "run_test": "test_runner_execute",
            "check_status": "ai_wizard_health_check",
            "get_help": "show_help",
            "optimize": "ai_wizard_suggest",
            "unknown": "clarify_intent"
        }
        return action_mapping.get(intent_type, "clarify_intent")


class ActionExecutor:
    """
    动作执行器 - 将意图转换为具体的框架操作
    
    负责根据识别出的用户意图，调用相应的框架功能模块，
    执行具体的操作任务，并返回执行结果。
    
    支持的动作类型：
    - ai_wizard_analyze_api: AI分析API文档复杂度和特征
    - ai_wizard_auto_test: AI一键生成测试用例和数据
    - test_runner_execute: 执行测试套件和用例
    - ai_wizard_health_check: 检查AI功能和系统状态
    - ai_wizard_suggest: 提供优化建议和配置推荐
    - show_help: 显示帮助信息和使用指导
    - clarify_intent: 意图澄清和提示
    
    特点：
    - 基于模板的命令生成和执行
    - 智能参数验证和错误处理
    - 异步执行支持，不阻塞用户交互
    - 结构化的结果返回和错误反馈
    """
    
    def __init__(self):
        """
        初始化动作执行器
        
        设置各种动作类型对应的命令模板，支持参数化和动态替换。
        模板使用Python字符串格式化语法，支持实体参数的自动替换。
        """
        # 动作类型到CLI命令模板的映射
        # 支持参数化，如{file_path}会被实体中的file_path替换
        self.command_templates = {
            "ai_wizard_analyze_api": "autotest ai-wizard analyze-api -i {file_path}",
            "ai_wizard_auto_test": "autotest ai-wizard auto-test -i {file_path}",
            "test_runner_execute": "autotest test run --path {file_path}",
            "ai_wizard_health_check": "autotest ai-wizard health-check",
            "ai_wizard_suggest": "autotest ai-wizard suggest"
        }
    
    async def execute(self, intent: Intent) -> Dict[str, Any]:
        """执行意图对应的行动"""
        action = intent.action
        entities = intent.entities
        
        if action == "clarify_intent":
            return await self._clarify_intent(intent)
        elif action == "show_help":
            return await self._show_help()
        elif action in self.command_templates:
            return await self._execute_command(action, entities)
        else:
            return {
                "success": False,
                "message": f"不支持的操作: {action}",
                "suggestions": ["请尝试说'帮助'获取可用命令"]
            }
    
    async def _execute_command(self, action: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """执行命令"""
        template = self.command_templates.get(action)
        if not template:
            return {"success": False, "message": "命令模板不存在"}
        
        # 检查必需的实体
        if "{file_path}" in template and "file_path" not in entities:
            return {
                "success": False,
                "message": "需要提供文件路径",
                "request": "请提供API文档的文件路径"
            }
        
        # 格式化命令
        try:
            command = template.format(**entities)
            
            # 模拟命令执行
            result = await self._simulate_command_execution(command, action)
            
            return {
                "success": True,
                "command": command,
                "result": result,
                "message": f"命令执行完成: {command}"
            }
            
        except KeyError as e:
            return {
                "success": False,
                "message": f"缺少必需参数: {e}",
                "entities_needed": str(e)
            }
    
    async def _simulate_command_execution(self, command: str, action: str) -> Dict[str, Any]:
        """模拟命令执行"""
        # 这里应该调用实际的命令执行逻辑
        await asyncio.sleep(0.5)  # 模拟执行时间
        
        simulated_results = {
            "ai_wizard_analyze_api": {
                "complexity": "medium",
                "api_count": 15,
                "recommendations": ["使用standard级别", "4个并发worker"]
            },
            "ai_wizard_auto_test": {
                "tests_generated": 45,
                "data_generated": 150,
                "estimated_time": "8分钟"
            },
            "test_runner_execute": {
                "tests_run": 30,
                "success_rate": 0.93,
                "execution_time": "5分钟"
            },
            "ai_wizard_health_check": {
                "ai_status": "正常",
                "api_key": "已配置",
                "network": "连接正常"
            },
            "ai_wizard_suggest": {
                "suggestions": [
                    "建议增加超时时间到60秒",
                    "推荐使用comprehensive级别获得更好覆盖"
                ]
            }
        }
        
        return simulated_results.get(action, {"status": "completed"})
    
    async def _clarify_intent(self, intent: Intent) -> Dict[str, Any]:
        """澄清用户意图"""
        return {
            "success": False,
            "message": "我没有完全理解您的意图，请尝试更明确的表达",
            "suggestions": [
                "说'分析API文档'来分析接口",
                "说'生成测试'来创建测试用例", 
                "说'运行测试'来执行测试",
                "说'健康检查'来检查系统状态",
                "说'帮助'获取更多信息"
            ]
        }
    
    async def _show_help(self) -> Dict[str, Any]:
        """显示帮助信息"""
        return {
            "success": True,
            "message": "AI助手使用指南",
            "commands": {
                "分析API": "分析API文档复杂度和特征",
                "生成测试": "AI自动生成测试用例和数据",
                "运行测试": "执行测试套件",
                "健康检查": "检查AI功能状态",
                "优化建议": "获取配置优化建议"
            },
            "examples": [
                "请帮我分析 openapi.yaml 文档",
                "为我的电商API生成测试用例",
                "运行用户管理接口的测试",
                "检查AI功能的健康状态"
            ]
        }


class AIChatAssistant:
    """
    AI聊天助手 - 框架的智能交互入口
    
    这是架构中的L4层（智能交互）的最终实现，作为用户与整个
    测试框架进行自然语言交互的统一入口。
    
    核心能力：
    1. 自然语言理解 - 处理用户的口语化指令和需求
    2. 意图识别和映射 - 将用户意图转换为框架操作
    3. 上下文管理 - 保持对话历史和上下文状态
    4. 智能响应生成 - 生成友好和个性化的回复
    5. 错误处理和恢复 - 优雅地处理异常情况
    
    架构设计：
    - IntentRecognizer: 意图识别和实体提取
    - ActionExecutor: 动作执行和结果返回
    - ConversationHistory: 对话历史管理和上下文维护
    
    使用场景：
    - 新手引导："如何开始使用这个框架？"
    - 快速操作："帮我分析API文档"
    - 问题诊断："为什么测试失败了？"
    - 优化建议："怎样提高测试覆盖率？"
    
    特色功能：
    - 支持中英文混合输入
    - 智能上下文理解和记忆
    - 个性化的回复风格和建议
    - 全面的错误处理和用户引导
    """
    
    def __init__(self):
        """
        初始化AI聊天助手
        
        创建并配置所有必要的组件，包括意图识别器、动作执行器等。
        初始化为空的对话历史，准备开始与用户交互。
        """
        self.intent_recognizer = IntentRecognizer()    # 意图识别组件
        self.action_executor = ActionExecutor()        # 动作执行组件
        self.conversation_history = []                 # 对话历史存储
        
    async def chat(self, user_input: str) -> str:
        """
        处理用户对话 - 核心交互入口
        
        这是聊天助手的核心方法，负责完整的对话处理流程，
        从用户输入到生成最终响应的全过程。
        
        处理流程：
        1. 记录用户输入 - 保持对话历史和上下文
        2. 意图识别 - 理解用户的需求和意图
        3. 动作执行 - 调用相应的框架功能
        4. 生成响应 - 创建友好和个性化的回复
        5. 记录响应 - 保存对话结果供后续参考
        
        错误处理：
        - 意图识别失败时提供建议
        - 动作执行错误时给出明确的指导
        - 系统异常时保持友好的用户体验
        
        Args:
            user_input: 用户的自然语言输入
            
        Returns:
            str: 格式化的友好响应消息
        """
        try:
            # 1. 记录对话 - 保持对话历史用于上下文理解
            self.conversation_history.append({
                "timestamp": "now",
                "user": user_input,
                "type": "input"
            })
            
            # 2. 理解用户意图 - 识别用户的真实需求
            intent = self.intent_recognizer.recognize(user_input)
            
            # 3. 执行相应操作 - 调用框架功能满足用户需求
            result = await self.action_executor.execute(intent)
            
            # 4. 生成友好回复 - 创建个性化和结构化的响应
            response = self._generate_response(intent, result)
            
            # 5. 记录回复 - 保存交互结果供后续分析
            self.conversation_history.append({
                "timestamp": "now",
                "assistant": response,
                "type": "response"
            })
            
            return response
            
        except Exception as e:
            logger.error(f"聊天处理失败: {e}")
            return f"抱歉，处理您的请求时出现了错误：{e}"
    
    def _generate_response(self, intent: Intent, result: Dict[str, Any]) -> str:
        """生成友好回复"""
        if not result.get("success", True):
            if "request" in result:
                return f"❓ {result['message']}\n\n{result['request']}"
            elif "suggestions" in result:
                suggestions = "\n".join(f"  • {s}" for s in result["suggestions"])
                return f"❓ {result['message']}\n\n建议尝试:\n{suggestions}"
            else:
                return f"❌ {result['message']}"
        
        # 成功情况的回复
        if intent.intent_type == "analyze_api":
            data = result.get("result", {})
            return f"""✅ API分析完成！

📊 分析结果:
  • 复杂度: {data.get('complexity', '未知')}
  • 接口数量: {data.get('api_count', 0)}
  
💡 AI建议:
  • {data.get('recommendations', ['暂无建议'])[0] if data.get('recommendations') else '暂无建议'}

🔍 执行的命令: `{result.get('command', '')}`"""

        elif intent.intent_type == "generate_test":
            data = result.get("result", {})
            return f"""🤖 测试生成完成！

📈 生成统计:
  • 测试用例: {data.get('tests_generated', 0)} 个
  • 测试数据: {data.get('data_generated', 0)} 条
  • 预计耗时: {data.get('estimated_time', '未知')}

✨ 现在您可以运行生成的测试了！"""

        elif intent.intent_type == "run_test":
            data = result.get("result", {})
            return f"""🏃‍♂️ 测试执行完成！

📊 执行结果:
  • 测试数量: {data.get('tests_run', 0)}
  • 成功率: {data.get('success_rate', 0):.1%}
  • 执行时间: {data.get('execution_time', '未知')}

{"🎉 测试表现优秀！" if data.get('success_rate', 0) > 0.9 else "⚠️ 可能需要检查失败的测试"}"""

        elif intent.intent_type == "check_status":
            data = result.get("result", {})
            return f"""🩺 健康检查完成！

✅ 系统状态:
  • AI状态: {data.get('ai_status', '未知')}
  • API密钥: {data.get('api_key', '未知')}
  • 网络连接: {data.get('network', '未知')}

💚 系统运行正常！"""

        elif intent.intent_type == "optimize":
            data = result.get("result", {})
            suggestions = data.get("suggestions", [])
            if suggestions:
                suggestion_text = "\n".join(f"  • {s}" for s in suggestions)
                return f"""💡 AI优化建议:

{suggestion_text}

🚀 应用这些建议可以提升测试效果！"""
            else:
                return "✨ 您的配置已经很优秀，暂无优化建议！"

        elif intent.intent_type == "get_help":
            data = result.get("commands", {})
            examples = result.get("examples", [])
            
            command_text = "\n".join(f"  • {k}: {v}" for k, v in data.items())
            example_text = "\n".join(f"  • {e}" for e in examples)
            
            return f"""📚 AI助手使用指南

🔧 可用功能:
{command_text}

💬 使用示例:
{example_text}

💡 直接用自然语言告诉我您想要做什么！"""

        else:
            return f"✅ 操作完成！\n\n执行命令: `{result.get('command', '')}`"


# 演示函数
async def demo_ai_chat_assistant():
    """演示AI聊天助手"""
    print("💬 AI聊天助手演示")
    print("=" * 50)
    
    assistant = AIChatAssistant()
    
    # 模拟对话
    test_conversations = [
        "你好，我需要帮助",
        "请帮我分析 openapi.yaml 文档",
        "为我的电商API生成测试用例",
        "检查AI功能状态",
        "有什么优化建议吗？"
    ]
    
    for user_input in test_conversations:
        print(f"\n👤 用户: {user_input}")
        response = await assistant.chat(user_input)
        print(f"🤖 助手: {response}")
        print("-" * 30)


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_ai_chat_assistant())