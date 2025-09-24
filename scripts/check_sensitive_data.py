#!/usr/bin/env python3
"""
敏感信息检查脚本
用于检查项目中是否包含敏感信息
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class SensitiveDataChecker:
    """敏感信息检查器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.sensitive_patterns = {
            # API Keys
            'api_key': [
                r'sk-[a-zA-Z0-9]{20,}',  # OpenAI/DeepSeek API Key
                r'pk_[a-zA-Z0-9]{20,}',  # Stripe API Key
                r'[a-zA-Z0-9]{32,}',     # Generic API Key
            ],
            # Passwords
            'password': [
                r'password\s*[:=]\s*["\']?[^"\'\s]{8,}["\']?',
                r'pwd\s*[:=]\s*["\']?[^"\'\s]{8,}["\']?',
                r'pass\s*[:=]\s*["\']?[^"\'\s]{8,}["\']?',
            ],
            # Tokens
            'token': [
                r'token\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',
                r'bearer\s+[a-zA-Z0-9]{20,}',
                r'jwt\s*[:=]\s*["\']?[a-zA-Z0-9._-]{20,}["\']?',
            ],
            # Database URLs
            'database': [
                r'mysql://[^@]+@[^/]+',
                r'postgresql://[^@]+@[^/]+',
                r'mongodb://[^@]+@[^/]+',
                r'redis://[^@]+@[^/]+',
            ],
            # Email addresses
            'email': [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            ],
            # IP addresses (private)
            'private_ip': [
                r'192\.168\.\d+\.\d+',
                r'10\.\d+\.\d+\.\d+',
                r'172\.(1[6-9]|2\d|3[01])\.\d+\.\d+',
            ],
            # Phone numbers
            'phone': [
                r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
                r'\+86[0-9]{11}',
            ],
            # Credit card numbers
            'credit_card': [
                r'\b[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}[-\s]?[0-9]{4}\b',
            ],
        }
        
        # 允许的文件扩展名
        self.allowed_extensions = {
            '.py', '.yaml', '.yml', '.json', '.md', '.txt', '.cfg', '.ini',
            '.toml', '.sh', '.bat', '.ps1', '.dockerfile', '.gitignore'
        }
        
        # 排除的目录
        self.excluded_dirs = {
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            'venv', 'env', '.venv', '.env', 'build', 'dist', 'target',
            '.idea', '.vscode', '.vs'
        }
        
        # 排除的文件
        self.excluded_files = {
            '.gitignore', '.gitattributes', 'LICENSE', 'CHANGELOG.md',
            'sensitive_data_report.md', 'check_sensitive_data.py'
        }
    
    def check_file(self, file_path: Path) -> List[Dict[str, any]]:
        """
        检查单个文件中的敏感信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[Dict]: 发现的敏感信息列表
        """
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for category, patterns in self.sensitive_patterns.items():
                        for pattern in patterns:
                            matches = re.finditer(pattern, line, re.IGNORECASE)
                            for match in matches:
                                # 检查是否是示例或占位符
                                if self._is_example_or_placeholder(match.group()):
                                    continue
                                
                                issues.append({
                                    'file': str(file_path),
                                    'line': line_num,
                                    'category': category,
                                    'content': line.strip(),
                                    'match': match.group(),
                                    'severity': self._get_severity(category)
                                })
        
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
        
        return issues
    
    def _is_example_or_placeholder(self, text: str) -> bool:
        """检查是否是示例或占位符"""
        example_patterns = [
            r'your-', r'example\.', r'localhost', r'127\.0\.0\.1',
            r'sk-your-', r'your_api_key', r'your_token', r'your_password',
            r'<.*>', r'\[.*\]', r'\{.*\}', r'placeholder', r'example',
            r'test-', r'demo-', r'sample-', r'mock-',
            r'password\s*=\s*[a-zA-Z_][a-zA-Z0-9_]*',  # 变量赋值
            r'password\s*[:=]\s*["\']?[a-zA-Z_][a-zA-Z0-9_]*["\']?',  # 配置中的变量
            r'get\s*\(\s*["\']password["\']',  # 配置获取
            r'\.password\s*=',  # 对象属性赋值
        ]
        
        for pattern in example_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _get_severity(self, category: str) -> str:
        """获取严重程度"""
        high_severity = {'api_key', 'password', 'token', 'database', 'credit_card'}
        medium_severity = {'email', 'phone'}
        low_severity = {'private_ip'}
        
        if category in high_severity:
            return 'HIGH'
        elif category in medium_severity:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def scan_project(self) -> Dict[str, List[Dict[str, any]]]:
        """
        扫描整个项目
        
        Returns:
            Dict: 按严重程度分组的敏感信息
        """
        all_issues = []
        
        for file_path in self._get_files_to_scan():
            issues = self.check_file(file_path)
            all_issues.extend(issues)
        
        # 按严重程度分组
        grouped_issues = {
            'HIGH': [],
            'MEDIUM': [],
            'LOW': []
        }
        
        for issue in all_issues:
            grouped_issues[issue['severity']].append(issue)
        
        return grouped_issues
    
    def _get_files_to_scan(self):
        """获取需要扫描的文件列表"""
        files = []
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                # 检查文件扩展名
                if file_path.suffix.lower() not in self.allowed_extensions:
                    continue
                
                # 检查是否在排除目录中
                if any(part in self.excluded_dirs for part in file_path.parts):
                    continue
                
                # 检查是否是排除文件
                if file_path.name in self.excluded_files:
                    continue
                
                files.append(file_path)
        
        return files
    
    def generate_report(self, issues: Dict[str, List[Dict[str, any]]]) -> str:
        """生成检查报告"""
        report = []
        report.append("# 敏感信息检查报告")
        report.append("")
        
        total_issues = sum(len(issues[severity]) for severity in issues)
        
        if total_issues == 0:
            report.append("✅ **检查通过**: 未发现敏感信息")
            return "\n".join(report)
        
        report.append(f"## 检查结果总览")
        report.append(f"- 🔴 **高危**: {len(issues['HIGH'])} 个")
        report.append(f"- 🟡 **中危**: {len(issues['MEDIUM'])} 个")
        report.append(f"- 🟢 **低危**: {len(issues['LOW'])} 个")
        report.append(f"- 📊 **总计**: {total_issues} 个")
        report.append("")
        
        for severity in ['HIGH', 'MEDIUM', 'LOW']:
            if not issues[severity]:
                continue
            
            severity_emoji = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}[severity]
            report.append(f"## {severity_emoji} {severity} 级别问题")
            report.append("")
            
            for issue in issues[severity]:
                report.append(f"### 文件: `{issue['file']}`")
                report.append(f"- **行号**: {issue['line']}")
                report.append(f"- **类型**: {issue['category']}")
                report.append(f"- **匹配内容**: `{issue['match']}`")
                report.append(f"- **完整行**: `{issue['content']}`")
                report.append("")
        
        report.append("## 建议")
        report.append("")
        report.append("1. **立即处理高危问题**: 移除或替换真实的敏感信息")
        report.append("2. **使用环境变量**: 将敏感信息存储在环境变量中")
        report.append("3. **使用占位符**: 在示例代码中使用明显的占位符")
        report.append("4. **定期检查**: 定期运行此脚本检查敏感信息")
        
        return "\n".join(report)


def main():
    """主函数"""
    checker = SensitiveDataChecker()
    
    print("🔍 开始扫描敏感信息...")
    issues = checker.scan_project()
    
    report = checker.generate_report(issues)
    
    # 输出报告
    print("\n" + "="*50)
    print(report)
    print("="*50)
    
    # 保存报告到文件
    report_file = Path("sensitive_data_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 详细报告已保存到: {report_file}")
    
    # 如果有高危问题，返回非零退出码
    if issues['HIGH']:
        print("\n❌ 发现高危敏感信息，请立即处理！")
        sys.exit(1)
    else:
        print("\n✅ 敏感信息检查通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()
