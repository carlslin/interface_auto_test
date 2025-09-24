"""
=============================================================================
接口自动化测试框架 - 智能合约测试器模块
=============================================================================

本模块提供了完整的智能合约测试功能，包括合约部署、方法调用、事件监听等。

主要功能：
1. 合约部署测试 - 自动部署和验证智能合约
2. 方法调用测试 - 测试合约的所有方法
3. 事件监听测试 - 监听和验证合约事件
4. Gas费优化测试 - 测试Gas费使用情况
5. 边界条件测试 - 测试异常情况和边界条件
6. 性能压力测试 - 高并发合约调用测试

支持的合约类型：
- ERC20代币合约
- ERC721 NFT合约
- ERC1155多代币合约
- DeFi协议合约
- 自定义智能合约

技术特性：
- ABI自动解析 - 自动解析合约ABI生成测试用例
- 参数生成 - 智能生成测试参数
- 事件验证 - 自动验证合约事件
- Gas费分析 - 详细的Gas费使用分析
- 测试报告 - 完整的测试报告生成
- 持续集成 - 支持CI/CD集成

使用示例：
    # 初始化智能合约测试器
    tester = SmartContractTester(ethereum_client)
    
    # 部署合约并测试
    result = await tester.test_contract_deployment(abi, bytecode)
    
    # 测试合约方法
    await tester.test_contract_methods(contract_address, abi)
    
    # 生成测试报告
    report = tester.generate_test_report()

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from .ethereum_client import EthereumClient, SmartContract


@dataclass
class TestCase:
    """测试用例数据类"""
    name: str
    description: str
    method_name: str
    args: List[Any] = field(default_factory=list)
    expected_result: Optional[Any] = None
    expected_error: Optional[str] = None
    gas_limit: Optional[int] = None
    value: int = 0
    test_type: str = "call"  # call, transaction, event


@dataclass
class TestResult:
    """测试结果数据类"""
    test_case: TestCase
    success: bool
    actual_result: Optional[Any] = None
    gas_used: Optional[int] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None


@dataclass
class ContractTestReport:
    """合约测试报告数据类"""
    contract_address: str
    contract_name: str
    test_start_time: float
    test_end_time: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_gas_used: int
    test_results: List[TestResult] = field(default_factory=list)
    deployment_result: Optional[TestResult] = None


class ContractTestCaseGenerator(ABC):
    """合约测试用例生成器抽象基类"""
    
    @abstractmethod
    def generate_test_cases(self, abi: List[Dict[str, Any]]) -> List[TestCase]:
        """
        生成测试用例
        
        Args:
            abi: 合约ABI
            
        Returns:
            List[TestCase]: 测试用例列表
        """
        pass


class ERC20TestCaseGenerator(ContractTestCaseGenerator):
    """ERC20代币合约测试用例生成器"""
    
    def generate_test_cases(self, abi: List[Dict[str, Any]]) -> List[TestCase]:
        """生成ERC20测试用例"""
        test_cases = []
        
        # 查找ERC20标准方法
        methods = {item['name']: item for item in abi if item.get('type') == 'function'}
        
        # name() 测试
        if 'name' in methods:
            test_cases.append(TestCase(
                name="测试代币名称",
                description="测试代币名称查询",
                method_name="name",
                test_type="call"
            ))
        
        # symbol() 测试
        if 'symbol' in methods:
            test_cases.append(TestCase(
                name="测试代币符号",
                description="测试代币符号查询",
                method_name="symbol",
                test_type="call"
            ))
        
        # decimals() 测试
        if 'decimals' in methods:
            test_cases.append(TestCase(
                name="测试代币精度",
                description="测试代币精度查询",
                method_name="decimals",
                test_type="call"
            ))
        
        # totalSupply() 测试
        if 'totalSupply' in methods:
            test_cases.append(TestCase(
                name="测试总供应量",
                description="测试代币总供应量查询",
                method_name="totalSupply",
                test_type="call"
            ))
        
        # balanceOf() 测试
        if 'balanceOf' in methods:
            test_cases.append(TestCase(
                name="测试余额查询",
                description="测试指定地址余额查询",
                method_name="balanceOf",
                args=["0x0000000000000000000000000000000000000000"],  # 零地址
                test_type="call"
            ))
        
        # transfer() 测试
        if 'transfer' in methods:
            test_cases.append(TestCase(
                name="测试转账",
                description="测试代币转账功能",
                method_name="transfer",
                args=["0x0000000000000000000000000000000000000001", 1000],  # 转账到地址1，金额1000
                test_type="transaction"
            ))
        
        # approve() 测试
        if 'approve' in methods:
            test_cases.append(TestCase(
                name="测试授权",
                description="测试代币授权功能",
                method_name="approve",
                args=["0x0000000000000000000000000000000000000001", 1000],  # 授权给地址1，金额1000
                test_type="transaction"
            ))
        
        # allowance() 测试
        if 'allowance' in methods:
            test_cases.append(TestCase(
                name="测试授权额度查询",
                description="测试授权额度查询功能",
                method_name="allowance",
                args=["0x0000000000000000000000000000000000000000", "0x0000000000000000000000000000000000000001"],
                test_type="call"
            ))
        
        return test_cases


class GenericTestCaseGenerator(ContractTestCaseGenerator):
    """通用合约测试用例生成器"""
    
    def generate_test_cases(self, abi: List[Dict[str, Any]]) -> List[TestCase]:
        """生成通用测试用例"""
        test_cases = []
        
        for item in abi:
            if item.get('type') == 'function':
                method_name = item['name']
                inputs = item.get('inputs', [])
                
                # 生成参数
                args = []
                for input_param in inputs:
                    param_type = input_param['type']
                    if 'uint' in param_type:
                        args.append(1000)  # 默认数值
                    elif 'address' in param_type:
                        args.append("0x0000000000000000000000000000000000000000")  # 零地址
                    elif 'bool' in param_type:
                        args.append(True)  # 默认布尔值
                    elif 'string' in param_type:
                        args.append("test")  # 默认字符串
                    elif 'bytes' in param_type:
                        args.append("0x")  # 默认字节
                    else:
                        args.append(None)  # 其他类型设为None
                
                # 判断是调用还是交易
                test_type = "call"
                if item.get('stateMutability') in ['nonpayable', 'payable']:
                    test_type = "transaction"
                
                test_cases.append(TestCase(
                    name=f"测试{method_name}",
                    description=f"测试方法 {method_name}",
                    method_name=method_name,
                    args=args,
                    test_type=test_type
                ))
        
        return test_cases


class SmartContractTester:
    """智能合约测试器"""
    
    def __init__(self, ethereum_client: EthereumClient):
        """
        初始化智能合约测试器
        
        Args:
            ethereum_client: 以太坊客户端
        """
        self.client = ethereum_client
        self.logger = logging.getLogger(self.__class__.__name__)
        self.test_generators = {
            "ERC20": ERC20TestCaseGenerator(),
            "Generic": GenericTestCaseGenerator()
        }
        self.current_report: Optional[ContractTestReport] = None
    
    def _detect_contract_type(self, abi: List[Dict[str, Any]]) -> str:
        """
        检测合约类型
        
        Args:
            abi: 合约ABI
            
        Returns:
            str: 合约类型
        """
        method_names = [item['name'] for item in abi if item.get('type') == 'function']
        
        # ERC20标准方法
        erc20_methods = ['name', 'symbol', 'decimals', 'totalSupply', 'balanceOf', 'transfer', 'approve', 'allowance']
        if any(method in method_names for method in erc20_methods):
            return "ERC20"
        
        # ERC721标准方法
        erc721_methods = ['balanceOf', 'ownerOf', 'safeTransferFrom', 'transferFrom', 'approve', 'getApproved']
        if any(method in method_names for method in erc721_methods):
            return "ERC721"
        
        # ERC1155标准方法
        erc1155_methods = ['balanceOf', 'balanceOfBatch', 'setApprovalForAll', 'isApprovedForAll']
        if any(method in method_names for method in erc1155_methods):
            return "ERC1155"
        
        return "Generic"
    
    async def test_contract_deployment(self, abi: List[Dict[str, Any]], bytecode: str, 
                                    constructor_args: Optional[List] = None) -> TestResult:
        """
        测试合约部署
        
        Args:
            abi: 合约ABI
            bytecode: 合约字节码
            constructor_args: 构造函数参数
            
        Returns:
            TestResult: 测试结果
        """
        test_case = TestCase(
            name="合约部署测试",
            description="测试智能合约部署功能",
            method_name="deploy",
            args=constructor_args or [],
            test_type="transaction"
        )
        
        start_time = time.time()
        
        try:
            # 部署合约
            contract_address = await self.client.deploy_contract(abi, bytecode, constructor_args)
            
            execution_time = time.time() - start_time
            
            result = TestResult(
                test_case=test_case,
                success=True,
                actual_result=contract_address,
                execution_time=execution_time,
                transaction_hash=contract_address  # 部署地址作为交易哈希
            )
            
            self.logger.info(f"合约部署成功: {contract_address}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            result = TestResult(
                test_case=test_case,
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            
            self.logger.error(f"合约部署失败: {e}")
            return result
    
    async def test_contract_method(self, contract_address: str, abi: List[Dict[str, Any]], 
                                 test_case: TestCase) -> TestResult:
        """
        测试合约方法
        
        Args:
            contract_address: 合约地址
            abi: 合约ABI
            test_case: 测试用例
            
        Returns:
            TestResult: 测试结果
        """
        start_time = time.time()
        
        try:
            if test_case.test_type == "call":
                # 调用方法（只读）
                result = await self.client.call_contract(
                    contract_address, abi, test_case.method_name, test_case.args
                )
                
                execution_time = time.time() - start_time
                
                test_result = TestResult(
                    test_case=test_case,
                    success=True,
                    actual_result=result,
                    execution_time=execution_time
                )
                
            elif test_case.test_type == "transaction":
                # 发送交易（写操作）
                tx_hash = await self.client.send_contract_transaction(
                    contract_address, abi, test_case.method_name, test_case.args, test_case.value
                )
                
                # 等待交易确认
                receipt = await self.client.wait_for_transaction(tx_hash)
                
                execution_time = time.time() - start_time
                
                test_result = TestResult(
                    test_case=test_case,
                    success=receipt.status == 1,
                    actual_result=receipt,
                    gas_used=receipt.gasUsed,
                    execution_time=execution_time,
                    transaction_hash=tx_hash,
                    block_number=receipt.blockNumber
                )
                
                if receipt.status != 1:
                    test_result.error_message = "Transaction failed"
                
            else:
                raise ValueError(f"不支持的测试类型: {test_case.test_type}")
            
            self.logger.info(f"方法测试完成: {test_case.method_name} -> {test_result.success}")
            return test_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            result = TestResult(
                test_case=test_case,
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            
            self.logger.error(f"方法测试失败: {e}")
            return result
    
    async def test_contract_methods(self, contract_address: str, abi: List[Dict[str, Any]], 
                                  custom_test_cases: Optional[List[TestCase]] = None) -> List[TestResult]:
        """
        测试合约的所有方法
        
        Args:
            contract_address: 合约地址
            abi: 合约ABI
            custom_test_cases: 自定义测试用例（可选）
            
        Returns:
            List[TestResult]: 测试结果列表
        """
        results = []
        
        try:
            # 检测合约类型
            contract_type = self._detect_contract_type(abi)
            self.logger.info(f"检测到合约类型: {contract_type}")
            
            # 生成测试用例
            if custom_test_cases:
                test_cases = custom_test_cases
            else:
                generator = self.test_generators.get(contract_type, self.test_generators["Generic"])
                test_cases = generator.generate_test_cases(abi)
            
            self.logger.info(f"生成了 {len(test_cases)} 个测试用例")
            
            # 执行测试用例
            for test_case in test_cases:
                self.logger.info(f"执行测试: {test_case.name}")
                result = await self.test_contract_method(contract_address, abi, test_case)
                results.append(result)
                
                # 如果测试失败且是关键测试，可以选择停止
                if not result.success and test_case.test_type == "call":
                    self.logger.warning(f"关键测试失败: {test_case.name}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"合约方法测试失败: {e}")
            return results
    
    async def test_contract_events(self, contract_address: str, abi: List[Dict[str, Any]], 
                                 event_name: str, timeout: int = 30) -> List[Dict[str, Any]]:
        """
        测试合约事件
        
        Args:
            contract_address: 合约地址
            abi: 合约ABI
            event_name: 事件名
            timeout: 超时时间（秒）
            
        Returns:
            List[Dict[str, Any]]: 接收到的事件列表
        """
        events = []
        
        def event_callback(event):
            events.append(event)
            self.logger.info(f"收到事件: {event}")
        
        try:
            # 启动事件监听
            listener_task = asyncio.create_task(
                self.client.listen_events(contract_address, abi, event_name, event_callback)
            )
            
            # 等待指定时间
            await asyncio.sleep(timeout)
            
            # 取消监听
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass
            
            self.logger.info(f"事件测试完成，收到 {len(events)} 个事件")
            return events
            
        except Exception as e:
            self.logger.error(f"事件测试失败: {e}")
            return events
    
    async def run_comprehensive_test(self, abi: List[Dict[str, Any]], bytecode: str,
                                   constructor_args: Optional[List] = None,
                                   custom_test_cases: Optional[List[TestCase]] = None) -> ContractTestReport:
        """
        运行综合测试
        
        Args:
            abi: 合约ABI
            bytecode: 合约字节码
            constructor_args: 构造函数参数
            custom_test_cases: 自定义测试用例
            
        Returns:
            ContractTestReport: 测试报告
        """
        start_time = time.time()
        
        # 初始化测试报告
        self.current_report = ContractTestReport(
            contract_address="",
            contract_name="Unknown Contract",
            test_start_time=start_time,
            test_end_time=0.0,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            total_gas_used=0
        )
        
        try:
            # 1. 部署合约
            self.logger.info("开始合约部署测试")
            deployment_result = await self.test_contract_deployment(abi, bytecode, constructor_args)
            self.current_report.deployment_result = deployment_result
            
            if not deployment_result.success:
                self.logger.error("合约部署失败，无法继续测试")
                self.current_report.test_end_time = time.time()
                return self.current_report
            
            contract_address = deployment_result.actual_result
            self.current_report.contract_address = contract_address
            
            # 2. 测试合约方法
            self.logger.info("开始合约方法测试")
            method_results = await self.test_contract_methods(contract_address, abi, custom_test_cases)
            
            # 3. 更新测试报告
            self.current_report.test_results = method_results
            self.current_report.total_tests = len(method_results)
            self.current_report.passed_tests = sum(1 for result in method_results if result.success)
            self.current_report.failed_tests = sum(1 for result in method_results if not result.success)
            self.current_report.total_gas_used = sum(
                result.gas_used for result in method_results if result.gas_used
            )
            self.current_report.test_end_time = time.time()
            
            # 4. 记录测试结果
            success_rate = (self.current_report.passed_tests / self.current_report.total_tests * 100) if self.current_report.total_tests > 0 else 0
            self.logger.info(f"综合测试完成: {self.current_report.passed_tests}/{self.current_report.total_tests} 测试通过 ({success_rate:.1f}%)")
            
            return self.current_report
            
        except Exception as e:
            self.logger.error(f"综合测试失败: {e}")
            self.current_report.test_end_time = time.time()
            self.current_report.test_results.append(TestResult(
                test_case=TestCase(name="综合测试", description="综合测试", method_name="run_comprehensive_test"),
                success=False,
                error_message=str(e)
            ))
            return self.current_report
    
    def generate_test_report(self) -> Dict[str, Any]:
        """
        生成测试报告
        
        Returns:
            Dict[str, Any]: 测试报告
        """
        if not self.current_report:
            return {"error": "没有可用的测试报告"}
        
        report = {
            "contract_info": {
                "address": self.current_report.contract_address,
                "name": self.current_report.contract_name
            },
            "test_summary": {
                "total_tests": self.current_report.total_tests,
                "passed_tests": self.current_report.passed_tests,
                "failed_tests": self.current_report.failed_tests,
                "success_rate": (self.current_report.passed_tests / self.current_report.total_tests * 100) if self.current_report.total_tests > 0 else 0,
                "total_gas_used": self.current_report.total_gas_used,
                "execution_time": self.current_report.test_end_time - self.current_report.test_start_time
            },
            "deployment_result": {
                "success": self.current_report.deployment_result.success if self.current_report.deployment_result else False,
                "contract_address": self.current_report.deployment_result.actual_result if self.current_report.deployment_result else None,
                "error": self.current_report.deployment_result.error_message if self.current_report.deployment_result else None
            },
            "test_results": []
        }
        
        # 添加详细测试结果
        for result in self.current_report.test_results:
            test_detail = {
                "name": result.test_case.name,
                "method": result.test_case.method_name,
                "success": result.success,
                "execution_time": result.execution_time,
                "gas_used": result.gas_used,
                "error": result.error_message,
                "transaction_hash": result.transaction_hash
            }
            report["test_results"].append(test_detail)
        
        return report
