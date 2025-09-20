#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能测试运行器 - AI驱动的测试执行器

集成AI决策能力，实现智能化的测试调度、执行和优化
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

# 添加项目根目录到Python路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.runners.test_runner import TestRunner
from src.ai.ai_decision_center import AIDecisionCenter, Decision

logger = logging.getLogger(__name__)


@dataclass
class IntelligentTestResult:
    """智能测试结果"""
    test_result: Dict[str, Any]
    ai_insights: Dict[str, Any]
    optimization_suggestions: List[Dict[str, Any]]
    execution_metrics: Dict[str, Any]
    decision_tracking: List[str]


class IntelligentTestScheduler:
    """智能测试调度器"""
    
    def __init__(self, ai_decision_center: AIDecisionCenter):
        self.ai_decision_center = ai_decision_center
        
    async def create_optimal_schedule(self, test_suite: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """创建最优测试调度"""
        context = {
            "operation_type": "test_scheduling",
            "test_count": len(test_suite.get("tests", [])),
            "complexity": analysis.get("complexity", "medium"),
            "estimated_duration": analysis.get("estimated_duration", 300),
            "resource_constraints": analysis.get("constraints", {})
        }
        
        # AI决策最优调度策略
        decision = await self.ai_decision_center.make_intelligent_decision(context)
        
        # 基于AI推荐创建调度
        schedule = self._create_schedule_from_decision(test_suite, decision)
        
        return {
            "schedule": schedule,
            "ai_decision": decision,
            "optimization_applied": True
        }
    
    def _create_schedule_from_decision(self, test_suite: Dict[str, Any], decision: Decision) -> Dict[str, Any]:
        """基于AI决策创建调度"""
        tests = test_suite.get("tests", [])
        
        # 获取AI推荐的配置
        recommended_action = decision.recommendations[0]["action"] if decision.recommendations else {}
        
        parallel_workers = recommended_action.get("parallel_workers", 4)
        timeout = recommended_action.get("timeout", 30)
        
        # 智能分组测试
        test_groups = self._group_tests_intelligently(tests, parallel_workers)
        
        return {
            "test_groups": test_groups,
            "parallel_workers": parallel_workers,
            "timeout_per_test": timeout,
            "retry_failed": True,
            "ai_optimized": True,
            "estimated_total_time": self._estimate_total_time(test_groups, timeout)
        }
    
    def _group_tests_intelligently(self, tests: List[Dict], workers: int) -> List[List[Dict]]:
        """智能分组测试"""
        # 按复杂度排序
        sorted_tests = sorted(tests, key=lambda t: t.get("complexity_score", 1), reverse=True)
        
        # 分组策略：复杂测试分散到不同组
        groups = [[] for _ in range(workers)]
        group_loads = [0] * workers
        
        for test in sorted_tests:
            # 选择负载最轻的组
            min_load_group = min(range(workers), key=lambda i: group_loads[i])
            groups[min_load_group].append(test)
            group_loads[min_load_group] += test.get("complexity_score", 1)
        
        return [group for group in groups if group]  # 过滤空组
    
    def _estimate_total_time(self, test_groups: List[List[Dict]], timeout: int) -> int:
        """估算总执行时间"""
        max_group_time = 0
        for group in test_groups:
            group_time = sum(test.get("estimated_time", timeout) for test in group)
            max_group_time = max(max_group_time, group_time)
        return max_group_time


class AdaptiveTestExecutor:
    """自适应测试执行器"""
    
    def __init__(self, ai_decision_center: AIDecisionCenter):
        self.ai_decision_center = ai_decision_center
        self.execution_metrics = {}
        
    async def execute_with_adaptation(self, schedule: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """自适应执行测试"""
        execution_start = time.time()
        results = []
        adaptations_made = []
        
        test_groups = schedule["schedule"]["test_groups"]
        parallel_workers = schedule["schedule"]["parallel_workers"]
        
        logger.info(f"开始智能测试执行: {len(test_groups)} 个组, {parallel_workers} 并发")
        
        # 并发执行测试组
        tasks = []
        for i, group in enumerate(test_groups):
            task = asyncio.create_task(
                self._execute_test_group(group, i, schedule["schedule"])
            )
            tasks.append(task)
        
        # 等待所有组完成，同时监控和自适应
        group_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, result in enumerate(group_results):
            if isinstance(result, Exception):
                logger.error(f"测试组 {i} 执行失败: {result}")
                # AI决策如何处理失败
                adaptation = await self._handle_execution_failure(i, result, schedule)
                adaptations_made.append(adaptation)
            else:
                results.append(result)
        
        execution_time = time.time() - execution_start
        
        return {
            "results": results,
            "execution_time": execution_time,
            "adaptations_made": adaptations_made,
            "ai_optimized": True,
            "schedule_used": schedule
        }
    
    async def _execute_test_group(self, group: List[Dict], group_id: int, schedule_config: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试组"""
        logger.info(f"执行测试组 {group_id}: {len(group)} 个测试")
        
        group_results = []
        start_time = time.time()
        
        for test in group:
            try:
                # 执行单个测试（这里简化为模拟）
                test_result = await self._execute_single_test(test, schedule_config)
                group_results.append(test_result)
                
                # 实时监控和自适应
                if self._should_adapt(test_result):
                    adaptation = await self._adapt_execution_strategy(test_result, schedule_config)
                    if adaptation:
                        schedule_config.update(adaptation)
                        logger.info(f"应用自适应调整: {adaptation}")
                
            except Exception as e:
                logger.error(f"测试 {test.get('name', 'unknown')} 执行失败: {e}")
                group_results.append({
                    "test_name": test.get("name", "unknown"),
                    "success": False,
                    "error": str(e),
                    "execution_time": 0
                })
        
        execution_time = time.time() - start_time
        
        return {
            "group_id": group_id,
            "results": group_results,
            "execution_time": execution_time,
            "success_rate": sum(1 for r in group_results if r.get("success", False)) / len(group_results)
        }
    
    async def _execute_single_test(self, test: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个测试（模拟）"""
        test_name = test.get("name", "unknown")
        complexity = test.get("complexity_score", 1)
        
        # 模拟测试执行时间
        execution_time = complexity * config.get("timeout_per_test", 30) / 10
        await asyncio.sleep(min(execution_time, 5))  # 最多等待5秒（演示用）
        
        # 模拟成功率（复杂度越高，失败概率越大）
        success_probability = max(0.7, 1 - complexity * 0.1)
        success = time.time() % 1 < success_probability
        
        return {
            "test_name": test_name,
            "success": success,
            "execution_time": execution_time,
            "response_time": execution_time * 0.8,
            "complexity": complexity
        }
    
    def _should_adapt(self, test_result: Dict[str, Any]) -> bool:
        """判断是否需要自适应调整"""
        # 如果测试失败或执行时间过长，考虑调整
        if not test_result.get("success", True):
            return True
        
        if test_result.get("execution_time", 0) > 60:  # 超过1分钟
            return True
        
        return False
    
    async def _adapt_execution_strategy(self, test_result: Dict[str, Any], current_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """自适应调整执行策略"""
        context = {
            "operation_type": "execution_adaptation",
            "test_result": test_result,
            "current_config": current_config,
            "adaptation_trigger": "performance_issue" if test_result.get("execution_time", 0) > 60 else "failure"
        }
        
        # AI决策如何调整
        decision = await self.ai_decision_center.make_intelligent_decision(context)
        
        if decision.recommendations:
            adaptation = decision.recommendations[0]["action"]
            logger.info(f"AI建议自适应调整: {adaptation}")
            return adaptation
        
        return None
    
    async def _handle_execution_failure(self, group_id: int, error: Exception, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """处理执行失败"""
        context = {
            "operation_type": "failure_handling",
            "group_id": group_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "schedule": schedule
        }
        
        # AI决策如何处理失败
        decision = await self.ai_decision_center.make_intelligent_decision(context)
        
        return {
            "group_id": group_id,
            "adaptation_applied": decision.recommendations[0] if decision.recommendations else None,
            "ai_reasoning": decision.reasoning
        }


class IntelligentTestRunner(TestRunner):
    """智能测试运行器 - 具备AI决策能力的测试执行器"""
    
    def __init__(self, config_path: Optional[str] = None):
        super().__init__()
        self.ai_decision_center = AIDecisionCenter()
        self.intelligent_scheduler = IntelligentTestScheduler(self.ai_decision_center)
        self.adaptive_executor = AdaptiveTestExecutor(self.ai_decision_center)
        self.ai_active = False
        
    async def start_ai_engine(self):
        """启动AI引擎"""
        if not self.ai_active:
            await self.ai_decision_center.start()
            self.ai_active = True
            logger.info("AI测试引擎已启动")
    
    def stop_ai_engine(self):
        """停止AI引擎"""
        if self.ai_active:
            self.ai_decision_center.stop()
            self.ai_active = False
            logger.info("AI测试引擎已停止")
    
    async def intelligent_run(self, test_suite: Dict[str, Any]) -> IntelligentTestResult:
        """智能测试执行"""
        if not self.ai_active:
            await self.start_ai_engine()
        
        execution_start = time.time()
        decision_tracking = []
        
        try:
            # 1. AI分析测试套件
            logger.info("AI分析测试套件...")
            analysis = await self._ai_analyze_test_suite(test_suite)
            decision_tracking.append(f"测试套件分析完成: 复杂度 {analysis['complexity']}")
            
            # 2. 智能调度测试
            logger.info("智能调度测试...")
            schedule_result = await self.intelligent_scheduler.create_optimal_schedule(test_suite, analysis)
            decision_tracking.append(f"智能调度完成: {schedule_result['ai_decision'].confidence:.2f} 置信度")
            
            # 3. 自适应执行
            logger.info("自适应执行测试...")
            execution_result = await self.adaptive_executor.execute_with_adaptation(schedule_result, analysis)
            decision_tracking.append(f"执行完成: {len(execution_result['adaptations_made'])} 次自适应调整")
            
            # 4. AI结果分析
            logger.info("AI分析测试结果...")
            ai_insights = await self._ai_analyze_results(execution_result, analysis)
            decision_tracking.append("AI洞察分析完成")
            
            # 5. 生成优化建议
            optimization_suggestions = await self._generate_optimization_suggestions(
                execution_result, analysis, ai_insights
            )
            decision_tracking.append(f"生成 {len(optimization_suggestions)} 条优化建议")
            
            total_execution_time = time.time() - execution_start
            
            return IntelligentTestResult(
                test_result=execution_result,
                ai_insights=ai_insights,
                optimization_suggestions=optimization_suggestions,
                execution_metrics={
                    "total_execution_time": total_execution_time,
                    "ai_decision_time": analysis.get("decision_time", 0),
                    "adaptation_count": len(execution_result.get("adaptations_made", [])),
                    "ai_confidence": schedule_result["ai_decision"].confidence
                },
                decision_tracking=decision_tracking
            )
            
        except Exception as e:
            logger.error(f"智能测试执行失败: {e}")
            raise
    
    async def _ai_analyze_test_suite(self, test_suite: Dict[str, Any]) -> Dict[str, Any]:
        """AI分析测试套件"""
        tests = test_suite.get("tests", [])
        
        context = {
            "operation_type": "test_suite_analysis",
            "test_count": len(tests),
            "test_types": list(set(test.get("type", "unknown") for test in tests)),
            "has_complex_tests": any(test.get("complexity_score", 1) > 3 for test in tests)
        }
        
        decision_start = time.time()
        decision = await self.ai_decision_center.make_intelligent_decision(context)
        decision_time = time.time() - decision_start
        
        # 计算复杂度
        avg_complexity = sum(test.get("complexity_score", 1) for test in tests) / len(tests) if tests else 1
        
        if avg_complexity > 3:
            complexity = "high"
        elif avg_complexity > 2:
            complexity = "medium"
        else:
            complexity = "low"
        
        return {
            "complexity": complexity,
            "test_count": len(tests),
            "estimated_duration": len(tests) * 30,  # 每个测试30秒估算
            "ai_decision": decision,
            "decision_time": decision_time,
            "constraints": {
                "memory_intensive": avg_complexity > 2.5,
                "network_dependent": True
            }
        }
    
    async def _ai_analyze_results(self, execution_result: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """AI分析测试结果"""
        results = execution_result.get("results", [])
        
        # 计算总体统计
        total_tests = sum(len(group["results"]) for group in results)
        successful_tests = sum(
            sum(1 for test in group["results"] if test.get("success", False))
            for group in results
        )
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # AI洞察分析
        insights = {
            "overall_success_rate": success_rate,
            "total_tests": total_tests,
            "execution_efficiency": self._calculate_efficiency(execution_result, analysis),
            "failure_patterns": self._analyze_failure_patterns(results),
            "performance_insights": self._analyze_performance(results),
            "ai_value_added": {
                "adaptations_successful": len(execution_result.get("adaptations_made", [])) > 0,
                "schedule_optimized": execution_result.get("ai_optimized", False),
                "predicted_vs_actual": self._compare_prediction_vs_actual(analysis, execution_result)
            }
        }
        
        return insights
    
    async def _generate_optimization_suggestions(
        self, 
        execution_result: Dict[str, Any], 
        analysis: Dict[str, Any], 
        insights: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成优化建议"""
        suggestions = []
        
        # 基于成功率的建议
        if insights["overall_success_rate"] < 0.8:
            suggestions.append({
                "type": "quality_improvement",
                "priority": "high",
                "title": "提升测试成功率",
                "description": f"当前成功率 {insights['overall_success_rate']:.1%}，建议优化失败的测试用例",
                "action": "review_failed_tests"
            })
        
        # 基于性能的建议
        if insights["execution_efficiency"] < 0.7:
            suggestions.append({
                "type": "performance_optimization",
                "priority": "medium",
                "title": "优化执行效率",
                "description": f"执行效率 {insights['execution_efficiency']:.1%}，建议调整并发配置",
                "action": "optimize_parallelism"
            })
        
        # 基于AI自适应的建议
        if len(execution_result.get("adaptations_made", [])) > 3:
            suggestions.append({
                "type": "stability_improvement",
                "priority": "medium",
                "title": "提升执行稳定性",
                "description": "执行过程中进行了多次自适应调整，建议优化初始配置",
                "action": "improve_initial_config"
            })
        
        return suggestions
    
    def _calculate_efficiency(self, execution_result: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """计算执行效率"""
        actual_time = execution_result.get("execution_time", 0)
        estimated_time = analysis.get("estimated_duration", 1)
        
        if actual_time <= estimated_time:
            return 1.0
        else:
            return estimated_time / actual_time
    
    def _analyze_failure_patterns(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析失败模式"""
        failures = []
        for group in results:
            for test in group["results"]:
                if not test.get("success", True):
                    failures.append(test)
        
        if not failures:
            return {"pattern": "no_failures", "count": 0}
        
        # 简单的失败模式分析
        error_types = {}
        for failure in failures:
            error = failure.get("error", "unknown")
            error_types[error] = error_types.get(error, 0) + 1
        
        most_common = max(error_types.items(), key=lambda x: x[1]) if error_types else ("none", 0)
        
        return {
            "pattern": most_common[0],
            "count": len(failures),
            "distribution": error_types
        }
    
    def _analyze_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析性能表现"""
        all_execution_times = []
        for group in results:
            for test in group["results"]:
                if test.get("execution_time"):
                    all_execution_times.append(test["execution_time"])
        
        if not all_execution_times:
            return {"average_time": 0, "max_time": 0, "min_time": 0}
        
        return {
            "average_time": sum(all_execution_times) / len(all_execution_times),
            "max_time": max(all_execution_times),
            "min_time": min(all_execution_times),
            "time_distribution": "normal" if max(all_execution_times) / min(all_execution_times) < 3 else "varied"
        }
    
    def _compare_prediction_vs_actual(self, analysis: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """比较预测与实际结果"""
        predicted_time = analysis.get("estimated_duration", 0)
        actual_time = execution_result.get("execution_time", 0)
        
        accuracy = 1 - abs(predicted_time - actual_time) / max(predicted_time, 1)
        
        return {
            "time_prediction_accuracy": max(0, accuracy),
            "predicted_time": predicted_time,
            "actual_time": actual_time
        }


# 演示函数
async def demo_intelligent_test_runner():
    """演示智能测试运行器"""
    print("🤖 智能测试运行器演示")
    print("=" * 50)
    
    # 创建智能测试运行器
    runner = IntelligentTestRunner()
    
    try:
        # 模拟测试套件
        test_suite = {
            "name": "电商API测试套件",
            "tests": [
                {"name": "用户登录测试", "type": "auth", "complexity_score": 2},
                {"name": "商品查询测试", "type": "query", "complexity_score": 1},
                {"name": "订单创建测试", "type": "transaction", "complexity_score": 3},
                {"name": "支付处理测试", "type": "payment", "complexity_score": 4},
                {"name": "库存更新测试", "type": "update", "complexity_score": 2},
            ]
        }
        
        print(f"📋 测试套件: {test_suite['name']}")
        print(f"🔢 测试数量: {len(test_suite['tests'])}")
        
        # 执行智能测试
        result = await runner.intelligent_run(test_suite)
        
        # 显示结果
        print(f"\n✅ 智能测试执行完成!")
        print(f"📊 总执行时间: {result.execution_metrics['total_execution_time']:.2f}秒")
        print(f"🎯 AI置信度: {result.execution_metrics['ai_confidence']:.2f}")
        print(f"🔄 自适应调整: {result.execution_metrics['adaptation_count']}次")
        print(f"📈 成功率: {result.ai_insights['overall_success_rate']:.1%}")
        
        print("\n🧠 AI决策跟踪:")
        for i, decision in enumerate(result.decision_tracking, 1):
            print(f"   {i}. {decision}")
        
        print(f"\n💡 优化建议: {len(result.optimization_suggestions)}条")
        for suggestion in result.optimization_suggestions:
            print(f"   • {suggestion['title']} ({suggestion['priority']}优先级)")
            
    except Exception as e:
        print(f"❌ 演示执行失败: {e}")
    finally:
        runner.stop_ai_engine()


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_intelligent_test_runner())