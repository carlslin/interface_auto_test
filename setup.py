from setuptools import setup, find_packages

setup(
    name="interface-autotest-framework",
    version="1.0.0",
    description="接口自动化测试框架，支持从接口文档生成自动化脚本并具备 mock 能力",
    author="Interface AutoTest Framework",
    author_email="autotest@example.com",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "flask>=3.0.0",
        "pyyaml>=6.0.1",
        "click>=8.1.7",
        "jinja2>=3.1.2",
        "jsonschema>=4.20.0",
        "faker>=20.1.0",
        "pytest>=7.4.3",
        "pytest-html>=4.1.1",
        "pytest-json-report>=1.5.0",
        "pydantic>=2.5.0",
        "swagger-spec-validator>=3.0.3",
        "httpx>=0.25.2",
        "rich>=13.7.0",
        "tabulate>=0.9.0",
        "openpyxl>=3.1.2",
        "python-multipart>=0.0.6",
        "watchdog>=3.0.0"
    ],
    entry_points={
        'console_scripts': [
            'autotest=src.cli.main:cli',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)