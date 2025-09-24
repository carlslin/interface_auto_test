#!/usr/bin/env python3
"""
性能监控模块
提供性能监控、指标收集和报告功能
"""

import time
import psutil
import logging
import threading
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: datetime
    function_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    success: bool
    error_message: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000, enable_system_monitoring: bool = True):
        """
        初始化性能监控器
        
        Args:
            max_history: 最大历史记录数
            enable_system_monitoring: 是否启用系统监控
        """
        self.max_history = max_history
        self.enable_system_monitoring = enable_system_monitoring
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 性能指标存储
        self.metrics_history: deque = deque(maxlen=max_history)
        self.function_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_calls': 0,
            'total_time': 0.0,
            'success_count': 0,
            'error_count': 0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'avg_time': 0.0,
            'memory_usage': deque(maxlen=100),
            'cpu_usage': deque(maxlen=100)
        })
        
        # 系统监控
        self.system_metrics: deque = deque(maxlen=100)
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        
        # 性能阈值配置
        self.thresholds = {
            'execution_time': 5.0,  # 5秒
            'memory_usage': 100 * 1024 * 1024,  # 100MB
            'cpu_usage': 80.0,  # 80%
            'error_rate': 0.1  # 10%
        }
        
        if self.enable_system_monitoring:
            self.start_system_monitoring()
    
    def start_system_monitoring(self, interval: float = 5.0):
        """
        启动系统监控
        
        Args:
            interval: 监控间隔（秒）
        """
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._system_monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info("系统监控已启动")
    
    def stop_system_monitoring(self):
        """停止系统监控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
        self.logger.info("系统监控已停止")
    
    def _system_monitoring_loop(self, interval: float):
        """系统监控循环"""
        while self.monitoring_active:
            try:
                # 收集系统指标
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                system_metric = {
                    'timestamp': datetime.now(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used': memory.used,
                    'memory_available': memory.available,
                    'disk_percent': disk.percent,
                    'disk_used': disk.used,
                    'disk_free': disk.free
                }
                
                self.system_metrics.append(system_metric)
                
                # 检查系统健康状态
                self._check_system_health(system_metric)
                
            except Exception as e:
                self.logger.error(f"系统监控错误: {e}")
            
            time.sleep(interval)
    
    def _check_system_health(self, metrics: Dict[str, Any]):
        """检查系统健康状态"""
        warnings = []
        
        if metrics['cpu_percent'] > self.thresholds['cpu_usage']:
            warnings.append(f"CPU使用率过高: {metrics['cpu_percent']:.1f}%")
        
        if metrics['memory_percent'] > 90:
            warnings.append(f"内存使用率过高: {metrics['memory_percent']:.1f}%")
        
        if metrics['disk_percent'] > 90:
            warnings.append(f"磁盘使用率过高: {metrics['disk_percent']:.1f}%")
        
        if warnings:
            self.logger.warning(f"系统健康警告: {'; '.join(warnings)}")
    
    def monitor_function(self, func: Callable) -> Callable:
        """
        函数性能监控装饰器
        
        Args:
            func: 要监控的函数
            
        Returns:
            装饰后的函数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            start_cpu = psutil.cpu_percent()
            
            success = True
            error_message = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss
                end_cpu = psutil.cpu_percent()
                
                execution_time = end_time - start_time
                memory_usage = end_memory - start_memory
                cpu_usage = end_cpu - start_cpu
                
                # 记录性能指标
                self._record_metrics(
                    func.__name__,
                    execution_time,
                    memory_usage,
                    cpu_usage,
                    success,
                    error_message
                )
        
        return wrapper
    
    def _record_metrics(self, function_name: str, execution_time: float, 
                       memory_usage: float, cpu_usage: float, 
                       success: bool, error_message: Optional[str] = None):
        """记录性能指标"""
        # 创建指标对象
        metric = PerformanceMetrics(
            timestamp=datetime.now(),
            function_name=function_name,
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            success=success,
            error_message=error_message
        )
        
        # 添加到历史记录
        self.metrics_history.append(metric)
        
        # 更新函数统计
        stats = self.function_stats[function_name]
        stats['total_calls'] += 1
        stats['total_time'] += execution_time
        
        if success:
            stats['success_count'] += 1
        else:
            stats['error_count'] += 1
        
        stats['min_time'] = min(stats['min_time'], execution_time)
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['avg_time'] = stats['total_time'] / stats['total_calls']
        
        stats['memory_usage'].append(memory_usage)
        stats['cpu_usage'].append(cpu_usage)
        
        # 检查性能阈值
        self._check_performance_thresholds(metric)
    
    def _check_performance_thresholds(self, metric: PerformanceMetrics):
        """检查性能阈值"""
        warnings = []
        
        if metric.execution_time > self.thresholds['execution_time']:
            warnings.append(f"执行时间过长: {metric.execution_time:.3f}s")
        
        if metric.memory_usage > self.thresholds['memory_usage']:
            warnings.append(f"内存使用过多: {metric.memory_usage / 1024 / 1024:.1f}MB")
        
        if metric.cpu_usage > self.thresholds['cpu_usage']:
            warnings.append(f"CPU使用率过高: {metric.cpu_usage:.1f}%")
        
        if warnings:
            self.logger.warning(f"性能警告 [{metric.function_name}]: {'; '.join(warnings)}")
    
    def get_function_stats(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取函数统计信息
        
        Args:
            function_name: 函数名，如果为None则返回所有函数的统计
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        if function_name:
            return self.function_stats.get(function_name, {})
        
        return dict(self.function_stats)
    
    def get_system_metrics(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取系统指标
        
        Args:
            last_n: 获取最近N条记录，如果为None则返回所有记录
            
        Returns:
            List[Dict[str, Any]]: 系统指标列表
        """
        metrics = list(self.system_metrics)
        if last_n:
            return metrics[-last_n:]
        return metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        total_metrics = len(self.metrics_history)
        if total_metrics == 0:
            return {'message': '暂无性能数据'}
        
        # 计算总体统计
        total_execution_time = sum(m.execution_time for m in self.metrics_history)
        total_memory_usage = sum(m.memory_usage for m in self.metrics_history)
        success_count = sum(1 for m in self.metrics_history if m.success)
        error_count = total_metrics - success_count
        
        # 获取最慢的函数
        slowest_functions = sorted(
            self.function_stats.items(),
            key=lambda x: x[1]['avg_time'],
            reverse=True
        )[:5]
        
        # 获取错误率最高的函数
        error_prone_functions = sorted(
            self.function_stats.items(),
            key=lambda x: x[1]['error_count'] / x[1]['total_calls'] if x[1]['total_calls'] > 0 else 0,
            reverse=True
        )[:5]
        
        return {
            'total_metrics': total_metrics,
            'total_execution_time': total_execution_time,
            'average_execution_time': total_execution_time / total_metrics,
            'total_memory_usage': total_memory_usage,
            'average_memory_usage': total_memory_usage / total_metrics,
            'success_rate': success_count / total_metrics,
            'error_rate': error_count / total_metrics,
            'slowest_functions': [
                {
                    'function': name,
                    'avg_time': stats['avg_time'],
                    'total_calls': stats['total_calls']
                }
                for name, stats in slowest_functions
            ],
            'error_prone_functions': [
                {
                    'function': name,
                    'error_rate': stats['error_count'] / stats['total_calls'] if stats['total_calls'] > 0 else 0,
                    'total_calls': stats['total_calls']
                }
                for name, stats in error_prone_functions
            ],
            'system_metrics_count': len(self.system_metrics)
        }
    
    def export_metrics(self, file_path: str, format: str = 'json') -> bool:
        """
        导出性能指标
        
        Args:
            file_path: 导出文件路径
            format: 导出格式 ('json' 或 'csv')
            
        Returns:
            bool: 是否导出成功
        """
        try:
            if format == 'json':
                data = {
                    'summary': self.get_performance_summary(),
                    'function_stats': dict(self.function_stats),
                    'system_metrics': list(self.system_metrics),
                    'export_time': datetime.now().isoformat()
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            elif format == 'csv':
                import csv
                
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'timestamp', 'function_name', 'execution_time', 
                        'memory_usage', 'cpu_usage', 'success', 'error_message'
                    ])
                    
                    for metric in self.metrics_history:
                        writer.writerow([
                            metric.timestamp.isoformat(),
                            metric.function_name,
                            metric.execution_time,
                            metric.memory_usage,
                            metric.cpu_usage,
                            metric.success,
                            metric.error_message or ''
                        ])
            
            else:
                raise ValueError(f"不支持的导出格式: {format}")
            
            self.logger.info(f"性能指标已导出: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出性能指标失败: {e}")
            return False
    
    def clear_metrics(self):
        """清空性能指标"""
        self.metrics_history.clear()
        self.function_stats.clear()
        self.system_metrics.clear()
        self.logger.info("性能指标已清空")
    
    def set_thresholds(self, **kwargs):
        """设置性能阈值"""
        for key, value in kwargs.items():
            if key in self.thresholds:
                self.thresholds[key] = value
                self.logger.info(f"性能阈值已更新: {key} = {value}")


# 全局性能监控器实例
_global_monitor: Optional[PerformanceMonitor] = None


def get_global_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def monitor_performance(func: Callable) -> Callable:
    """
    全局性能监控装饰器
    
    Args:
        func: 要监控的函数
        
    Returns:
        装饰后的函数
    """
    monitor = get_global_monitor()
    return monitor.monitor_function(func)
