#!/usr/bin/env python3
"""
长连接功能演示示例

展示如何在接口自动化测试框架中使用长连接：
1. 配置长连接参数
2. 复用连接进行多次请求
3. 监控连接状态
4. 性能对比测试
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.base_test import BaseTest


class PersistentConnectionDemo(BaseTest):
    """长连接演示测试类"""
    
    def __init__(self):
        super().__init__()
        
    def run_tests(self) -> List[Dict[str, Any]]:
        """运行演示测试
        
        Returns:
            List[Dict[str, Any]]: 测试结果列表
        """
        print("🔌 长连接功能演示")
        print("=" * 60)
        
        # 显示连接配置信息
        self.show_connection_info()
        
        # 测试连接复用性能
        self.test_connection_reuse_performance()
        
        # 测试长连接稳定性
        self.test_connection_stability()
        
        print("\n" + "=" * 60)
        print("✅ 长连接演示完成")
        
        # 返回测试结果
        summary = self.get_test_summary()
        return [{
            "test_class": self.__class__.__name__,
            "total_tests": summary["total"],
            "success_count": summary["success"],
            "failed_count": summary["failed"],
            "success_rate": summary["success_rate"],
            "test_results": [{
                "test_name": result.test_name,
                "method": result.method,
                "url": result.url,
                "status_code": result.status_code,
                "response_time": result.response_time,
                "success": result.success,
                "error_message": result.error_message
            } for result in summary["results"]]
        }]
        
    def show_connection_info(self):
        """显示连接配置信息"""
        print("\n📋 连接配置信息:")
        
        info = self.request_handler.get_connection_info()
        print(f"   长连接启用: {'✅' if info['keep_alive_enabled'] else '❌'}")
        print(f"   请求超时: {info['timeout']}秒")
        print(f"   会话头部: {len(info['session_headers'])}个")
        
        if 'pool_connections' in info:
            print(f"   连接池大小: {info['pool_connections']}")
            print(f"   单主机最大连接: {info['pool_maxsize']}")
            
    def test_connection_reuse_performance(self):
        """测试连接复用性能"""
        print("\n⚡ 连接复用性能测试:")
        
        # 模拟多次请求到同一服务器
        base_url = "http://httpbin.org"  # 使用公共测试API
        request_count = 5
        
        start_time = time.time()
        
        for i in range(request_count):
            try:
                result = self.make_request(
                    method="GET",
                    url=f"{base_url}/delay/1",  # 1秒延迟的接口
                    test_name=f"connection_reuse_test_{i+1}"
                )
                
                print(f"   请求{i+1}: 状态码={result.status_code}, "
                      f"响应时间={result.response_time:.3f}s")
                      
            except Exception as e:
                print(f"   请求{i+1}: 失败 - {str(e)}")
                
        total_time = time.time() - start_time
        print(f"   总耗时: {total_time:.3f}s")
        print(f"   平均每请求: {total_time/request_count:.3f}s")
        
    def test_connection_stability(self):
        """测试长连接稳定性"""
        print("\n🔗 长连接稳定性测试:")
        
        # 测试在间隔较长时间后连接是否仍然有效
        stable_requests = [
            {"delay": 0, "desc": "立即请求"},
            {"delay": 2, "desc": "2秒后请求"},
            {"delay": 5, "desc": "5秒后请求"}
        ]
        
        for req in stable_requests:
            if req["delay"] > 0:
                print(f"   等待{req['delay']}秒...")
                time.sleep(req["delay"])
                
            try:
                result = self.make_request(
                    method="GET",
                    url="http://httpbin.org/get",
                    test_name=f"stability_test_{req['delay']}s"
                )
                
                print(f"   {req['desc']}: ✅ 成功 (状态码={result.status_code})")
                
            except Exception as e:
                print(f"   {req['desc']}: ❌ 失败 - {str(e)}")
                
    def compare_with_without_keepalive(self):
        """对比启用和禁用长连接的性能"""
        print("\n📊 长连接性能对比:")
        
        # 这里可以创建两个不同配置的请求处理器进行对比
        # 由于配置限制，此处仅作演示说明
        
        print("   说明: 长连接通常能带来以下性能提升:")
        print("   - 减少TCP握手时间 (约节省50-200ms)")
        print("   - 降低服务器连接开销")
        print("   - 提高并发请求效率")
        print("   - 适合频繁请求同一服务器的场景")


def demo_persistent_connection_config():
    """演示长连接配置"""
    print("\n⚙️ 长连接配置说明:")
    print("-" * 40)
    
    config_example = """
# config/default.yaml
global:
  timeout: 30           # 请求超时时间
  keep_alive: true      # 启用长连接
  pool_connections: 10  # 连接池大小
  pool_maxsize: 10      # 单主机最大连接数
  
environments:
  production:
    # 生产环境建议更保守的连接配置
    pool_connections: 5
    pool_maxsize: 5
    timeout: 15
"""
    
    print("配置示例:")
    print(config_example)
    
    print("配置说明:")
    print("• keep_alive: 启用HTTP Keep-Alive")
    print("• pool_connections: 维护的连接池数量")
    print("• pool_maxsize: 单个主机的最大连接数")
    print("• timeout: 连接和读取超时时间")


def main():
    """主函数"""
    print("🎯 接口自动化测试框架 - 长连接功能演示")
    
    # 显示配置说明
    demo_persistent_connection_config()
    
    # 运行演示测试
    demo = PersistentConnectionDemo()
    demo.run_tests()
    
    # 显示最佳实践
    print("\n💡 长连接最佳实践:")
    print("1. 🌐 对于频繁请求同一服务器的场景，启用长连接")
    print("2. ⚡ 合理设置连接池大小，避免资源浪费")
    print("3. ⏰ 设置适当的超时时间，平衡性能和资源利用")
    print("4. 🔧 在测试完成后调用 teardown_class() 清理连接")
    print("5. 📊 监控连接状态，及时发现连接问题")
    
    # 资源清理
    demo.teardown_class()
    print("\n🧹 资源清理完成")


if __name__ == "__main__":
    main()