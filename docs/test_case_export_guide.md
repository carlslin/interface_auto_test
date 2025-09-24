# 📤 测试用例导出指南

## 概述

测试用例导出功能允许您将生成的测试用例导出为多种格式，便于团队协作、文档管理和测试执行。

## 支持的导出格式

### 1. Excel格式 (.xlsx)
- **用途**: 便于测试人员查看和管理
- **特性**: 
  - 表格化数据展示
  - 自动调整列宽
  - 包含汇总信息工作表
  - 支持数据筛选和排序

### 2. Markdown格式 (.md)
- **用途**: 便于文档化和展示
- **特性**:
  - 清晰的文档结构
  - 目录导航
  - 详细的测试步骤
  - GitHub/GitLab友好

### 3. JSON格式 (.json)
- **用途**: 便于程序处理和集成
- **特性**:
  - 结构化数据
  - 包含元数据信息
  - 版本控制友好
  - 易于解析和处理

### 4. CSV格式 (.csv)
- **用途**: 便于数据分析和导入其他工具
- **特性**:
  - 通用数据格式
  - Excel兼容
  - 支持UTF-8编码
  - 轻量级文件

### 5. XML格式 (.xml)
- **用途**: 符合TestCase标准，与测试管理工具集成
- **特性**:
  - 标准化格式
  - 工具兼容性好
  - 支持复杂数据结构
  - 可扩展性强

## 快速开始

### 1. 从API文档导出测试用例
```bash
# 基础导出（默认Excel格式）
python3 -m src.cli.main generate export-cases \
    -i examples/petstore-openapi.yaml \
    -o test_cases.xlsx

# 指定格式导出
python3 -m src.cli.main generate export-cases \
    -i examples/petstore-openapi.yaml \
    -o test_cases.md \
    -f markdown \
    --include-metadata
```

### 2. 生成测试脚本时同时导出
```bash
python3 -m src.cli.main generate tests \
    -i examples/petstore-openapi.yaml \
    -o generated_tests/ \
    -f python \
    --export-format excel
```

### 3. 编程方式使用
```python
from src.exporters.test_case_exporter import TestCaseExporter

exporter = TestCaseExporter()

# 定义测试用例
test_cases = [
    {
        "name": "用户登录测试",
        "description": "验证用户登录功能",
        "method": "POST",
        "url": "/api/auth/login",
        "priority": "High",
        "category": "认证测试",
        # ... 更多字段
    }
]

# 导出为Excel
excel_path = exporter.export_test_cases(
    test_cases=test_cases,
    output_path="exports/test_cases.xlsx",
    format_type="excel",
    include_metadata=True
)

print(f"Excel文件已导出: {excel_path}")
```

## 测试用例数据结构

### 核心字段
```json
{
  "test_id": "TC_001",
  "test_name": "用户登录测试",
  "description": "验证用户登录功能的正确性",
  "priority": "High",
  "category": "认证测试",
  "method": "POST",
  "url": "/api/auth/login",
  "headers": "Content-Type: application/json\nAuthorization: Bearer token",
  "parameters": "email: user@example.com\npassword: your-password-here",
  "request_body": "{\n  \"email\": \"user@example.com\",\n  \"password\": \"password123\"\n}",
  "expected_status": 200,
  "expected_response": "{\n  \"token\": \"jwt_token\",\n  \"user_id\": 123\n}",
  "assertions": "• 验证响应状态码为200\n• 验证返回JWT token\n• 验证token格式正确",
  "pre_conditions": "用户账号已注册且激活",
  "test_steps": "1. 发送POST请求到：/api/auth/login\n2. 设置请求头：Content-Type: application/json\n3. 设置请求体：{...}\n4. 执行请求\n5. 验证响应状态码为：200\n6. 验证：返回JWT token",
  "expected_result": "登录成功，返回有效的JWT token",
  "tags": "auth, login",
  "created_by": "系统生成",
  "created_time": "2024-01-20 10:30:00"
}
```

### 扩展字段（包含元数据时）
```json
{
  "test_suite": "用户认证测试套件",
  "automation_level": "完全自动化",
  "execution_type": "API",
  "estimated_time": "30秒",
  "dependencies": "用户注册接口"
}
```

## 导出配置选项

### TestCaseExporter参数

#### export_test_cases()
```python
def export_test_cases(
    test_cases: List[Dict[str, Any]],     # 测试用例列表
    output_path: Union[str, Path],        # 输出文件路径
    format_type: str = 'excel',           # 导出格式
    include_metadata: bool = True         # 是否包含元数据
) -> str:
```

**format_type选项**:
- `excel`: Excel格式 (.xlsx)
- `csv`: CSV格式 (.csv)
- `json`: JSON格式 (.json)
- `markdown`: Markdown格式 (.md)
- `xml`: XML格式 (.xml)

**include_metadata选项**:
- `True`: 包含详细的元数据信息
- `False`: 只包含核心测试信息

## 各种格式的特色功能

### Excel格式特色
```python
# Excel导出会自动：
# 1. 调整列宽以适应内容
# 2. 创建汇总信息工作表
# 3. 设置表格格式
# 4. 支持数据筛选

# 需要安装依赖
pip install pandas openpyxl
```

### Markdown格式特色
```markdown
# 📋 API测试用例文档

**导出时间**: 2024-01-20 10:30:00
**测试用例总数**: 25

## 📚 测试用例目录
- [TC_001](#tc_001) - 用户登录测试
- [TC_002](#tc_002) - 用户注册测试

## TC_001
### 🎯 用户登录测试

#### 📝 基本信息
- **测试ID**: TC_001
- **优先级**: High
- **分类**: 认证测试

#### 🌐 请求信息
- **方法**: `POST`
- **URL**: `/api/auth/login`
```

### JSON格式特色
```json
{
  "export_info": {
    "export_time": "2024-01-20T10:30:00",
    "total_cases": 25,
    "format": "JSON",
    "version": "1.0"
  },
  "test_cases": [
    {
      "test_id": "TC_001",
      "test_name": "用户登录测试",
      // ... 详细测试用例数据
    }
  ]
}
```

### XML格式特色
```xml
<?xml version='1.0' encoding='utf-8'?>
<testsuite name="API自动化测试用例" tests="25" timestamp="2024-01-20T10:30:00">
  <testcase name="用户登录测试" classname="APITest" time="30">
    <description>验证用户登录功能的正确性</description>
    <steps>1. 发送POST请求到：/api/auth/login...</steps>
    <expected_result>登录成功，返回有效的JWT token</expected_result>
    <request method="POST" url="/api/auth/login">...</request>
    <properties>
      <property name="priority" value="High"/>
      <property name="test_id" value="TC_001"/>
    </properties>
  </testcase>
</testsuite>
```

## 统计和汇总功能

### 生成测试用例统计
```python
exporter = TestCaseExporter()
summary = exporter.generate_test_summary(test_cases)

print(f"总测试用例数: {summary['total_cases']}")
print(f"优先级分布: {summary['priorities']}")
print(f"HTTP方法分布: {summary['methods']}")
print(f"分类分布: {summary['categories']}")
print(f"系统生成数量: {summary['creation_stats']['created_by_system']}")
```

### 输出示例
```
总测试用例数: 25
优先级分布: {'High': 8, 'Medium': 12, 'Low': 5}
HTTP方法分布: {'GET': 10, 'POST': 8, 'PUT': 4, 'DELETE': 3}
分类分布: {'认证测试': 5, '用户管理': 8, 'API测试': 12}
系统生成数量: 20
```

## 自定义导出模板

### 扩展导出器
```python
from src.exporters.test_case_exporter import TestCaseExporter

class CustomTestCaseExporter(TestCaseExporter):
    def _format_custom_field(self, test_case):
        """自定义字段格式化"""
        return f"自定义: {test_case.get('custom_field', '')}"
    
    def export_custom_format(self, test_cases, output_path):
        """自定义导出格式"""
        # 实现自定义导出逻辑
        pass
```

### 自定义