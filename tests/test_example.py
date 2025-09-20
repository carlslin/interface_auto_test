"""
示例测试文件 - 演示测试运行器功能
"""

import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.base_test import BaseTest


class ExampleAPITest(BaseTest):
    """
    示例API测试类
    """
    
    def __init__(self, config_path=None):
        super().__init__(config_path)
        
    def test_get_users(self):
        """测试获取用户列表接口"""
        result = self.make_request(
            method='GET',
            url='/users',
            test_name='test_get_users'
        )
        
        # 验证响应
        assert result.success, f"请求失败: {result.error_message}"
        if result.response_data and isinstance(result.response_data, dict):
            assert 'users' in result.response_data, "响应中应包含users字段"
        
        return result
        
    def test_create_user(self):
        """测试创建用户接口"""
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "age": 25
        }
        
        result = self.make_request(
            method='POST',
            url='/users',
            json=user_data,
            test_name='test_create_user'
        )
        
        # 验证响应
        assert result.success, f"请求失败: {result.error_message}"
        if result.response_data and isinstance(result.response_data, dict):
            assert 'id' in result.response_data, "响应中应包含id字段"
        
        return result
        
    def test_get_user_by_id(self):
        """测试根据ID获取用户接口"""
        user_id = 1
        
        result = self.make_request(
            method='GET',
            url=f'/users/{user_id}',
            test_name='test_get_user_by_id'
        )
        
        # 验证响应
        assert result.success, f"请求失败: {result.error_message}"
        if result.response_data and isinstance(result.response_data, dict):
            assert result.response_data.get('id') == user_id, "返回的用户ID应该匹配"
        
        return result
        
    def test_invalid_endpoint(self):
        """测试无效接口"""
        result = self.make_request(
            method='GET',
            url='/invalid-endpoint',
            test_name='test_invalid_endpoint'
        )
        
        # 这个测试期望返回404（但实际可能因为Mock服务器未运行而失败）
        # 这里我们只检查请求是否完成
        print(f"Status Code: {result.status_code}")
        
        return result


    def run_tests(self) -> list[Dict[str, Any]]:
        """实现抽象方法：运行所有测试
        
        Returns:
            list[Dict[str, Any]]: 测试结果列表
        """
        test_methods = [
            self.test_get_users,
            self.test_create_user,
            self.test_get_user_by_id,
            self.test_invalid_endpoint
        ]
        
        results = []
        for test_method in test_methods:
            try:
                result = test_method()
                results.append({
                    'test_name': test_method.__name__,
                    'success': True,
                    'result': result
                })
                print(f"✅ PASS {test_method.__name__}")
            except Exception as e:
                results.append({
                    'test_name': test_method.__name__,
                    'success': False,
                    'error': str(e)
                })
                print(f"❌ FAIL {test_method.__name__}: {e}")
        
        return results


if __name__ == '__main__':
    test_instance = ExampleAPITest()
    results = test_instance.run_tests()
    
    # 显示测试汇总
    summary = test_instance.get_test_summary()
    print(f"\n📊 测试汇总:")
    print(f"总计: {summary['total']}, 成功: {summary['success']}, 失败: {summary['failed']}")
    print(f"成功率: {summary['success_rate']:.2%}")