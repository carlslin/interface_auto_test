#!/usr/bin/env python3
"""
=============================================================================
CLI命令完整流程集成测试脚本
=============================================================================

本脚本测试CLI命令的完整流程，包括：
- 配置管理命令
- API文档解析命令
- 测试生成命令
- Mock服务器命令
- 测试执行命令
- 报告生成命令

使用方法：
    python3 scripts/cli_integration_test.py [--verbose]

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import sys
import time
import json
import logging
import tempfile
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class CLIIntegrationTester:
    """CLI集成测试器"""
    
    def __init__(self, verbose: bool = False):
        """
        初始化测试器
        
        Args:
            verbose: 是否详细输出
        """
        self.verbose = verbose
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 测试结果
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
        
        # 测试数据目录
        self.test_data_dir = None
        
    def log_test_result(self, test_name: str, success: bool, message: str = "", execution_time: float = 0):
        """记录测试结果"""
        self.test_results['total_tests'] += 1
        if success:
            self.test_results['passed_tests'] += 1
            status = "✅"
        else:
            self.test_results['failed_tests'] += 1
            status = "❌"
        
        self.logger.info(f"{status} {test_name}: {'通过' if success else '失败'} ({execution_time:.3f}s)")
        if message and not success:
            self.logger.error(f"   错误: {message}")
        
        self.test_results['test_details'].append({
            'name': test_name,
            'success': success,
            'message': message,
            'execution_time': execution_time
        })
    
    def setup_test_data(self) -> bool:
        """设置测试数据"""
        try:
            # 创建临时测试目录
            self.test_data_dir = tempfile.mkdtemp()
            
            # 创建测试OpenAPI文档
            openapi_content = """
openapi: 3.0.0
info:
  title: CLI Test API
  version: 1.0.0
  description: API for CLI integration testing
servers:
  - url: http://localhost:8080
    description: Test server
paths:
  /users:
    get:
      summary: Get all users
      operationId: getUsers
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
    post:
      summary: Create user
      operationId: createUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserInput'
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
  /users/{id}:
    get:
      summary: Get user by ID
      operationId: getUserById
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found
    put:
      summary: Update user
      operationId: updateUser
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserInput'
      responses:
        '200':
          description: Updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
    delete:
      summary: Delete user
      operationId: deleteUser
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: Deleted
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
          format: int64
        name:
          type: string
        email:
          type: string
          format: email
        age:
          type: integer
          minimum: 0
          maximum: 150
      required:
        - id
        - name
        - email
    UserInput:
      type: object
      properties:
        name:
          type: string
        email:
          type: string
          format: email
        age:
          type: integer
          minimum: 0
          maximum: 150
      required:
        - name
        - email
"""
            
            # 保存OpenAPI文档
            api_file = os.path.join(self.test_data_dir, "test_api.yaml")
            with open(api_file, 'w', encoding='utf-8') as f:
                f.write(openapi_content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"设置测试数据失败: {e}")
            return False
    
    def cleanup_test_data(self):
        """清理测试数据"""
        try:
            if self.test_data_dir and os.path.exists(self.test_data_dir):
                import shutil
                shutil.rmtree(self.test_data_dir)
        except Exception as e:
            self.logger.error(f"清理测试数据失败: {e}")
    
    def run_cli_command(self, command: List[str], timeout: int = 30) -> Dict[str, Any]:
        """
        运行CLI命令
        
        Args:
            command: 命令列表
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            # 构建完整命令
            full_command = [sys.executable, "-m", "src.cli.main"] + command
            
            # 执行命令
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=project_root
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(full_command)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'command': ' '.join(command)
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'command': ' '.join(command)
            }
    
    def test_help_commands(self) -> bool:
        """测试帮助命令"""
        start_time = time.time()
        
        try:
            # 测试主帮助命令
            result = self.run_cli_command(["--help"])
            if not result['success']:
                self.log_test_result("帮助命令测试", False, f"主帮助命令失败: {result['stderr']}", time.time() - start_time)
                return False
            
            # 测试配置帮助命令
            result = self.run_cli_command(["config", "--help"])
            if not result['success']:
                self.log_test_result("帮助命令测试", False, f"配置帮助命令失败: {result['stderr']}", time.time() - start_time)
                return False
            
            # 测试解析帮助命令
            result = self.run_cli_command(["parse", "--help"])
            if not result['success']:
                self.log_test_result("帮助命令测试", False, f"解析帮助命令失败: {result['stderr']}", time.time() - start_time)
                return False
            
            self.log_test_result("帮助命令测试", True, "", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("帮助命令测试", False, str(e), time.time() - start_time)
            return False
    
    def test_config_commands(self) -> bool:
        """测试配置命令"""
        start_time = time.time()
        
        try:
            # 测试配置显示命令
            result = self.run_cli_command(["config", "show"])
            if not result['success']:
                self.log_test_result("配置命令测试", False, f"配置显示命令失败: {result['stderr']}", time.time() - start_time)
                return False
            
            # 验证输出包含配置信息
            if "global" not in result['stdout'] and "environments" not in result['stdout']:
                self.log_test_result("配置命令测试", False, "配置显示输出不包含预期内容", time.time() - start_time)
                return False
            
            self.log_test_result("配置命令测试", True, "", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("配置命令测试", False, str(e), time.time() - start_time)
            return False
    
    def test_parse_commands(self) -> bool:
        """测试解析命令"""
        start_time = time.time()
        
        try:
            if not self.test_data_dir:
                self.log_test_result("解析命令测试", False, "测试数据目录未设置", time.time() - start_time)
                return False
            
            api_file = os.path.join(self.test_data_dir, "test_api.yaml")
            
            # 测试OpenAPI解析命令
            result = self.run_cli_command([
                "parse",
                "--input", api_file,
                "--output", self.test_data_dir
            ])
            
            if not result['success']:
                self.log_test_result("解析命令测试", False, f"OpenAPI解析命令失败: {result['stderr']}", time.time() - start_time)
                return False
            
            # 验证输出文件是否存在
            expected_files = ["parsed_api.json", "api_info.json"]
            for expected_file in expected_files:
                file_path = os.path.join(self.test_data_dir, expected_file)
                if not os.path.exists(file_path):
                    self.log_test_result("解析命令测试", False, f"预期输出文件不存在: {expected_file}", time.time() - start_time)
                    return False
            
            self.log_test_result("解析命令测试", True, "", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("解析命令测试", False, str(e), time.time() - start_time)
            return False
    
    def test_generate_commands(self) -> bool:
        """测试生成命令"""
        start_time = time.time()
        
        try:
            if not self.test_data_dir:
                self.log_test_result("生成命令测试", False, "测试数据目录未设置", time.time() - start_time)
                return False
            
            api_file = os.path.join(self.test_data_dir, "test_api.yaml")
            tests_dir = os.path.join(self.test_data_dir, "generated_tests")
            
            # 创建测试目录
            os.makedirs(tests_dir, exist_ok=True)
            
            # 测试测试用例生成命令
            result = self.run_cli_command([
                "generate",
                "tests",
                "--input", api_file,
                "--output", tests_dir,
                "--format", "pytest"
            ])
            
            if not result['success']:
                self.log_test_result("生成命令测试", False, f"测试用例生成命令失败: {result['stderr']}", time.time() - start_time)
                return False
            
            # 验证生成的测试文件
            test_files = [f for f in os.listdir(tests_dir) if f.endswith('.py')]
            if not test_files:
                self.log_test_result("生成命令测试", False, "未生成测试文件", time.time() - start_time)
                return False
            
            self.log_test_result("生成命令测试", True, f"生成了 {len(test_files)} 个测试文件", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("生成命令测试", False, str(e), time.time() - start_time)
            return False
    
    def test_mock_commands(self) -> bool:
        """测试Mock命令"""
        start_time = time.time()
        
        try:
            # 测试Mock服务器启动命令（非阻塞模式）
            result = self.run_cli_command([
                "mock",
                "start",
                "--port", "8081",
                "--daemon"
            ], timeout=10)
            
            if not result['success']:
                self.log_test_result("Mock命令测试", False, f"Mock服务器启动命令失败: {result['stderr']}", time.time() - start_time)
                return False
            
            # 等待服务器启动
            time.sleep(2)
            
            # 测试Mock路由添加命令
            result = self.run_cli_command([
                "mock",
                "add-route",
                "--method", "GET",
                "--path", "/test",
                "--response", '{"message": "test"}',
                "--port", "8081"
            ])
            
            if not result['success']:
                self.log_test_result("Mock命令测试", False, f"Mock路由添加命令失败: {result['stderr']}", time.time() - start_time)
                return False
            
            # 测试Mock服务器停止命令
            result = self.run_cli_command([
                "mock",
                "stop",
                "--port", "8081"
            ])
            
            if not result['success']:
                self.log_test_result("Mock命令测试", False, f"Mock服务器停止命令失败: {result['stderr']}", time.time() - start_time)
                return False
            
            self.log_test_result("Mock命令测试", True, "", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("Mock命令测试", False, str(e), time.time() - start_time)
            return False
    
    def test_export_commands(self) -> bool:
        """测试导出命令"""
        start_time = time.time()
        
        try:
            if not self.test_data_dir:
                self.log_test_result("导出命令测试", False, "测试数据目录未设置", time.time() - start_time)
                return False
            
            api_file = os.path.join(self.test_data_dir, "test_api.yaml")
            export_dir = os.path.join(self.test_data_dir, "exports")
            
            # 创建导出目录
            os.makedirs(export_dir, exist_ok=True)
            
            # 测试导出命令
            result = self.run_cli_command([
                "export",
                "test-cases",
                "--input", api_file,
                "--output", export_dir,
                "--format", "json"
            ])
            
            if not result['success']:
                self.log_test_result("导出命令测试", False, f"导出命令失败: {result['stderr']}", time.time() - start_time)
                return False
            
            # 验证导出文件
            export_files = os.listdir(export_dir)
            if not export_files:
                self.log_test_result("导出命令测试", False, "未生成导出文件", time.time() - start_time)
                return False
            
            self.log_test_result("导出命令测试", True, f"导出了 {len(export_files)} 个文件", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("导出命令测试", False, str(e), time.time() - start_time)
            return False
    
    def test_run_commands(self) -> bool:
        """测试运行命令"""
        start_time = time.time()
        
        try:
            if not self.test_data_dir:
                self.log_test_result("运行命令测试", False, "测试数据目录未设置", time.time() - start_time)
                return False
            
            tests_dir = os.path.join(self.test_data_dir, "generated_tests")
            
            # 检查是否有生成的测试文件
            if not os.path.exists(tests_dir) or not os.listdir(tests_dir):
                self.log_test_result("运行命令测试", True, "跳过测试（无测试文件）", time.time() - start_time)
                return True
            
            # 测试运行命令
            result = self.run_cli_command([
                "run",
                "tests",
                "--path", tests_dir,
                "--format", "console"
            ], timeout=60)
            
            if not result['success']:
                self.log_test_result("运行命令测试", False, f"测试运行命令失败: {result['stderr']}", time.time() - start_time)
                return False
            
            self.log_test_result("运行命令测试", True, "", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("运行命令测试", False, str(e), time.time() - start_time)
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.logger.info("开始CLI命令完整流程测试...")
        
        try:
            # 设置测试数据
            if not self.setup_test_data():
                self.log_test_result("测试环境设置", False, "无法设置测试数据", 0)
                return self.test_results
            
            # 运行所有测试
            tests = [
                self.test_help_commands,
                self.test_config_commands,
                self.test_parse_commands,
                self.test_generate_commands,
                self.test_mock_commands,
                self.test_export_commands,
                self.test_run_commands
            ]
            
            for test in tests:
                try:
                    test()
                except Exception as e:
                    self.logger.error(f"测试执行异常: {e}")
            
        except Exception as e:
            self.logger.error(f"测试执行异常: {e}")
        finally:
            self.cleanup_test_data()
        
        # 计算成功率
        success_rate = (self.test_results['passed_tests'] / 
                       self.test_results['total_tests'] * 100) if self.test_results['total_tests'] > 0 else 0
        
        self.test_results['success_rate'] = success_rate
        
        return self.test_results
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*70)
        print("CLI命令完整流程测试总结")
        print("="*70)
        print(f"总测试数: {self.test_results['total_tests']}")
        print(f"通过测试: {self.test_results['passed_tests']}")
        print(f"失败测试: {self.test_results['failed_tests']}")
        print(f"成功率: {self.test_results['success_rate']:.1f}%")
        
        if self.test_results['failed_tests'] > 0:
            print("\n失败的测试:")
            for test in self.test_results['test_details']:
                if not test['success']:
                    print(f"  - {test['name']}: {test['message']}")
        
        print("\n通过的测试:")
        for test in self.test_results['test_details']:
            if test['success']:
                print(f"  ✅ {test['name']}: {test['message']}")
        
        print("="*70)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CLI命令完整流程集成测试脚本')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建测试器
    tester = CLIIntegrationTester(verbose=args.verbose)
    
    # 运行测试
    results = tester.run_all_tests()
    
    # 打印总结
    tester.print_summary()
    
    # 返回退出码
    sys.exit(0 if results['failed_tests'] == 0 else 1)


if __name__ == "__main__":
    main()
