#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI决策中心 - 框架的智能大脑

这是AI与框架深度融合的核心组件，负责统一的智能决策和学习
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class Decision:
    """AI决策结果"""
    decision_id: str
    decision_type: str
    recommendations: List[Dict[str, Any]]
    confidence: float
    reasoning: str
    context: Dict[str, Any]
    timestamp: datetime


class AIKnowledgeBase:
    """
    AI知识库 - 存储和管理所有AI学习到的知识
    
    负责积累和管理测试相关的知识和经验，包括：
    - 成功案例：存储成功的测试策略和配置
    - 失败案例：记录失败的原因和解决方案
    - API模式：识别和存储常见的API设计模式
    - 测试策略：优化的测试方法和策略
    """
    
    def __init__(self, storage_path: str = "./data/ai_knowledge"):
        """
        初始化AI知识库
        
        Args:
            storage_path: 知识库存储路径，用于持久化存储学习到的知识
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 加载各类知识数据
        # 如果文件不存在，则使用默认值初始化
        self.success_cases = self._load_knowledge("success_cases.json", [])    # 成功案例列表
        self.failure_cases = self._load_knowledge("failure_cases.json", [])    # 失败案例列表  
        self.api_patterns = self._load_knowledge("api_patterns.json", {})      # API模式字典
        self.test_strategies = self._load_knowledge("test_strategies.json", {}) # 测试策略字典
        
        logger.info("AI知识库初始化完成")
    
    def _load_knowledge(self, filename: str, default_value):
        """加载知识文件"""
        file_path = self.storage_path / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载知识文件失败: {e}")
        return default_value
    
    def _save_knowledge(self, filename: str, data):
        """保存知识文件"""
        file_path = self.storage_path / filename
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存知识文件失败: {e}")
    
    def learn_from_success(self, context: Dict[str, Any], result: Dict[str, Any]):
        """从成功案例中学习"""
        success_case = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "result": result
        }
        self.success_cases.append(success_case)
        self._save_knowledge("success_cases.json", self.success_cases)
        logger.info("学习成功案例")
    
    def learn_from_failure(self, context: Dict[str, Any], error: Dict[str, Any], solution: Dict[str, Any]):
        """从失败案例中学习"""
        failure_case = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "error": error,
            "solution": solution
        }
        self.failure_cases.append(failure_case)
        self._save_knowledge("failure_cases.json", self.failure_cases)
        logger.info("学习失败案例")
    
    def query_similar_cases(self, current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查询相似案例"""
        similar_cases = []
        
        # 简化相似度计算
        for case in self.success_cases[-20:]:  # 最近20个案例
            similarity = self._calculate_similarity(current_context, case["context"])
            if similarity > 0.6:
                similar_cases.append({
                    "case": case,
                    "similarity": similarity,
                    "type": "success"
                })
        
        similar_cases.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_cases[:5]  # 返回前5个最相似的
    
    def _calculate_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """计算上下文相似度"""
        similarity = 0.0
        
        # 比较API类型
        if context1.get("api_type") == context2.get("api_type"):
            similarity += 0.4
        
        # 比较复杂度
        if context1.get("complexity") == context2.get("complexity"):
            similarity += 0.3
        
        # 比较接口数量级别
        count1 = context1.get("api_count", 0)
        count2 = context2.get("api_count", 0)
        if count1 > 0 and count2 > 0:
            count_similarity = 1 - abs(count1 - count2) / max(count1, count2)
            similarity += count_similarity * 0.3
        
        return similarity


class AILearningEngine:
    """AI学习引擎 - 持续学习和改进"""
    
    def __init__(self, knowledge_base: AIKnowledgeBase):
        self.knowledge_base = knowledge_base
        self.learning_active = False
        
    async def start_continuous_learning(self):
        """启动持续学习"""
        self.learning_active = True
        logger.info("启动AI持续学习引擎")
        
        while self.learning_active:
            try:
                await self._learning_cycle()
                await asyncio.sleep(3600)  # 每小时学习一次
            except Exception as e:
                logger.error(f"学习循环出错: {e}")
                await asyncio.sleep(300)
    
    def stop_continuous_learning(self):
        """停止持续学习"""
        self.learning_active = False
        logger.info("停止AI持续学习引擎")
    
    async def _learning_cycle(self):
        """学习循环"""
        logger.info("执行学习周期")
        
        # 分析最近的案例
        recent_successes = self.knowledge_base.success_cases[-10:]
        recent_failures = self.knowledge_base.failure_cases[-5:]
        
        # 更新策略
        if recent_successes:
            self._update_strategies_from_successes(recent_successes)
        
        if recent_failures:
            self._learn_from_failures(recent_failures)
    
    def _learn_from_failures(self, failures: List[Dict]):
        """从失败案例中学习"""
        for case in failures:
            context = case["context"]
            error = case["error"]
            
            # 记录常见错误模式
            error_type = error.get("type", "unknown")
            if error_type not in self.knowledge_base.api_patterns:
                self.knowledge_base.api_patterns[error_type] = {
                    "failure_count": 0,
                    "prevention_strategies": []
                }
            self.knowledge_base.api_patterns[error_type]["failure_count"] += 1
    
    def _update_strategies_from_successes(self, successes: List[Dict]):
        """从成功案例更新策略"""
        for case in successes:
            context = case["context"]
            result = case["result"]
            
            if result.get("success_rate", 0) > 0.9:
                # 记录高成功率的配置
                config_key = f"{context.get('completion_level')}_{context.get('api_count', 0)//10}"
                if config_key not in self.knowledge_base.test_strategies:
                    self.knowledge_base.test_strategies[config_key] = {
                        "success_count": 0,
                        "recommended_config": context
                    }
                self.knowledge_base.test_strategies[config_key]["success_count"] += 1


class AIDecisionCenter:
    """
    AI决策中心 - 框架的智能大脑和统一决策中心
    
    这是架构中的L3层（智能决策）核心组件，作为整个框架的智能大脑，
    负责为框架的所有操作提供AI驱动的智能决策支持。
    
    核心功能：
    1. 智能决策引擎 - 基于上下文和历史数据的智能决策
    2. 知识库管理 - 积累和管理测试相关的知识和经验  
    3. 学习引擎 - 从测试结果和用户反馈中持续学习
    4. 预测引擎 - 预测测试风险和优化机会
    5. 策略推荐 - 推荐最优的测试策略和配置
    
    架构优化亮点：
    - 整合原有的API分析和代码审查功能
    - 提供统一的智能决策入口
    - 支持多种决策场景和上下文
    """
    
    def __init__(self, storage_path: str = "./data/ai_knowledge"):
        """
        初始化AI决策中心
        
        Args:
            storage_path: 知识库存储路径，用于持久化存储AI学习的知识
        """
        # 初始化各个智能组件
        # 这些组件构成了AI决策中心的核心智能
        self.knowledge_base = AIKnowledgeBase(storage_path)      # 知识库：存储和管理测试知识
        self.learning_engine = AILearningEngine(self.knowledge_base)  # 学习引擎：从数据中学习模式
        self.decision_history = []                               # 决策历史：记录所有决策过程
        
        logger.info("AI决策中心初始化完成")
    
    async def start(self):
        """启动AI决策中心"""
        await self.learning_engine.start_continuous_learning()
        logger.info("AI决策中心已启动")
    
    def stop(self):
        """停止AI决策中心"""
        self.learning_engine.stop_continuous_learning()
        logger.info("AI决策中心已停止")
    
    async def make_intelligent_decision(self, context: Dict[str, Any]) -> Decision:
        """基于上下文做出智能决策"""
        decision_id = f"decision_{int(time.time() * 1000)}"
        
        try:
            # 1. 分析复杂度
            complexity = self._assess_complexity(context)
            
            # 2. 查询相似案例
            similar_cases = self.knowledge_base.query_similar_cases(context)
            
            # 3. 生成推荐
            recommendations = self._generate_recommendations(context, complexity, similar_cases)
            
            # 4. 计算置信度
            confidence = self._calculate_confidence(similar_cases, complexity)
            
            # 5. 生成推理说明
            reasoning = self._generate_reasoning(complexity, similar_cases, recommendations)
            
            decision = Decision(
                decision_id=decision_id,
                decision_type=context.get("operation_type", "unknown"),
                recommendations=recommendations,
                confidence=confidence,
                reasoning=reasoning,
                context=context,
                timestamp=datetime.now()
            )
            
            self.decision_history.append(decision)
            logger.info(f"AI决策完成: {decision_id}, 置信度: {confidence:.2f}")
            
            return decision
            
        except Exception as e:
            logger.error(f"AI决策失败: {e}")
            return self._get_default_decision(decision_id, context)
    
    def _assess_complexity(self, context: Dict[str, Any]) -> str:
        """评估复杂度"""
        score = 0
        
        # API数量
        api_count = context.get("api_count", 0)
        if api_count > 50:
            score += 3
        elif api_count > 20:
            score += 2
        elif api_count > 5:
            score += 1
        
        # 补全级别
        level = context.get("completion_level", "standard")
        if level == "enterprise":
            score += 3
        elif level == "comprehensive":
            score += 2
        
        if score >= 5:
            return "critical"
        elif score >= 3:
            return "high"
        elif score >= 1:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(self, context: Dict[str, Any], complexity: str, similar_cases: List[Dict]) -> List[Dict[str, Any]]:
        """生成推荐"""
        recommendations = []
        
        # 基于复杂度的推荐
        if complexity in ["high", "critical"]:
            recommendations.append({
                "type": "configuration",
                "priority": "high",
                "title": "高复杂度优化建议",
                "description": "检测到高复杂度任务，建议使用保守配置",
                "action": {
                    "completion_level": "comprehensive",
                    "parallel_workers": 6,
                    "timeout": 60
                }
            })
        
        # 基于成功案例的推荐
        if similar_cases:
            best_case = max(similar_cases, key=lambda x: x["case"]["result"].get("success_rate", 0))
            recommendations.append({
                "type": "experience",
                "priority": "medium",
                "title": "基于成功经验的推荐",
                "description": f"类似案例的最佳配置",
                "action": best_case["case"]["context"]
            })
        
        return recommendations
    
    def _calculate_confidence(self, similar_cases: List[Dict], complexity: str) -> float:
        """计算置信度"""
        base_confidence = 0.7
        
        # 相似案例越多，置信度越高
        if similar_cases:
            case_boost = min(0.2, len(similar_cases) * 0.05)
            base_confidence += case_boost
        
        # 复杂度越低，置信度越高
        complexity_penalty = {
            "low": 0.0,
            "medium": 0.05,
            "high": 0.15,
            "critical": 0.25
        }
        base_confidence -= complexity_penalty.get(complexity, 0.1)
        
        return max(0.3, min(0.95, base_confidence))
    
    def _generate_reasoning(self, complexity: str, similar_cases: List[Dict], recommendations: List[Dict]) -> str:
        """生成推理说明"""
        parts = []
        
        parts.append(f"任务复杂度评估为: {complexity}")
        
        if similar_cases:
            success_rate = sum(case["case"]["result"].get("success_rate", 0) for case in similar_cases) / len(similar_cases)
            parts.append(f"基于{len(similar_cases)}个相似案例，平均成功率: {success_rate:.1%}")
        
        if recommendations:
            parts.append(f"生成了{len(recommendations)}条智能建议")
        
        return " | ".join(parts)
    
    def _get_default_decision(self, decision_id: str, context: Dict[str, Any]) -> Decision:
        """获取默认决策"""
        return Decision(
            decision_id=decision_id,
            decision_type=context.get("operation_type", "unknown"),
            recommendations=[{
                "type": "default",
                "priority": "medium",
                "title": "默认配置",
                "description": "使用安全的默认配置",
                "action": {
                    "completion_level": "standard",
                    "parallel_workers": 4,
                    "timeout": 30
                }
            }],
            confidence=0.5,
            reasoning="使用默认配置作为安全选择",
            context=context,
            timestamp=datetime.now()
        )
    
    def record_decision_outcome(self, decision_id: str, success: bool, result: Dict[str, Any]):
        """记录决策结果用于学习"""
        decision = next((d for d in self.decision_history if d.decision_id == decision_id), None)
        if not decision:
            return
        
        if success:
            self.knowledge_base.learn_from_success(decision.context, result)
        else:
            self.knowledge_base.learn_from_failure(
                decision.context, 
                result.get("error", {}), 
                result.get("solution", {})
            )


# 使用示例
async def demo_ai_decision_center():
    """演示AI决策中心"""
    decision_center = AIDecisionCenter()
    
    try:
        # 启动决策中心
        await decision_center.start()
        
        # 模拟一个决策请求
        context = {
            "operation_type": "api_testing",
            "api_count": 25,
            "completion_level": "standard",
            "business_context": "电商平台用户管理API",
            "api_type": "REST"
        }
        
        # 做出智能决策
        decision = await decision_center.make_intelligent_decision(context)
        
        print("🧠 AI决策结果:")
        print(f"   决策ID: {decision.decision_id}")
        print(f"   置信度: {decision.confidence:.2f}")
        print(f"   推理: {decision.reasoning}")
        print(f"   推荐数量: {len(decision.recommendations)}")
        
        for i, rec in enumerate(decision.recommendations, 1):
            print(f"   推荐{i}: {rec['title']} (优先级: {rec['priority']})")
        
        # 模拟记录结果
        decision_center.record_decision_outcome(
            decision.decision_id,
            success=True,
            result={"success_rate": 0.95, "execution_time": 180}
        )
        
    finally:
        decision_center.stop()


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_ai_decision_center())