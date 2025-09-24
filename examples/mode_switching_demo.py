#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模式切换示例

演示如何在不同的测试模式之间灵活切换
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.base_test import BaseTest
from src.utils.config_loader import ConfigLoader


class ModeSwitchingDemo(BaseTest):
    """模式切换演示类"""
    
    def demo_mode_switching(self):
        """演示模式切换功能"""
        print("🔄 模式切换演示")
        print("=" * 50)
        
        # 获取当前模式信息
        current_info = self.get_current_mode_info()
        print(f"📊 当前模式信息:")
        for key, value in current_info.items():
            print(f"  {key}: {value}")
        
        print("\n🧪 测试不同模式:")
        
        # 1. 测试自动模式
        print("\n1️⃣ 切换到自动模式")
        self.switch_to_auto_mode()
        self._make_test_request("auto")
        
        # 2. 测试Mock模式
        print("\n2️⃣ 切换到Mock模式")
        self.switch_to_mock_mode()
        self._make_test_request("mock")
        
        # 3. 测试真实模式
        print("\n3️⃣ 切换到真实模式")
        self.switch_to_real_mode()
        self._make_test_request("real")
        
        # 4. 演示带回退的请求
        print("\n4️⃣ 演示自动回退功能")
        self.switch_to_auto_mode()
        result = self.make_request_with_fallback("GET", "/api/test")
        print(f"回退请求结果: {result.success}")
        
    def _make_test_request(self, mode_name):
        """发送测试请求"""
        try:
            result = self.make_request("GET", "/api/health", test_name=f"test_{mode_name}_mode")
            print(f"  ✅ {mode_name}模式请求成功: {result.status_code}")
        except Exception as e:
            print(f"  ❌ {mode_name}模式请求失败: {e}")
    
    def run_tests(self):
        """运行演示"""
        self.demo_mode_switching()
        summary = self.get_test_summary()
        # 返回符合基类期望的格式
        return [{
            'test_name': 'mode_switching_demo',
            'total': summary['total'],
            'success': summary['success'],
            'failed': summary['failed'],
            'success_rate': summary['success_rate']
        }]


def main():
    """主函数"""
    print("🚀 接口自动化测试框架 - 模式切换演示")
    print("=" * 60)
    
    # 创建演示实例
    demo = ModeSwitchingDemo()
    
    # 运行演示
    summary_list = demo.run_tests()
    summary = demo.get_test_summary()  # 获取真正的汇总信息
    
    # 显示结果
    print("\n📊 演示结果:")
    print(f"总请求数: {summary['total']}")
    print(f"成功数: {summary['success']}")
    print(f"失败数: {summary['failed']}")
    print(f"成功率: {summary['success_rate']:.2%}")
    
    print("\n💡 使用建议:")
    print("1. 开发阶段：使用 auto 模式，让系统智能选择")
    print("2. 离线测试：使用 mock 模式，无需真实接口")
    print("3. 集成测试：使用 real 模式，直接测试真实接口")
    print("4. 生产验证：使用 real 模式，禁用mock回退")


if __name__ == "__main__":
    main()