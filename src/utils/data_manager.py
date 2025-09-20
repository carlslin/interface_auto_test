"""
数据管理器模块
负责管理测试数据、环境变量和配置数据
"""

from __future__ import annotations

import os
import json
import yaml
import csv
import sqlite3
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime


class DataManager:
    """数据管理器"""
    
    def __init__(self, data_dir: str = "./data"):
        """
        初始化数据管理器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._cache: Dict[str, Any] = {}
        self._init_database()
        
    def _init_database(self):
        """初始化SQLite数据库"""
        db_path = self.data_dir / "testdata.db"
        self.db_path = str(db_path)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建测试数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, name)
                )
            """)
            
            # 创建环境变量表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS environment_vars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    env_name TEXT NOT NULL,
                    var_name TEXT NOT NULL,
                    var_value TEXT NOT NULL,
                    var_type TEXT DEFAULT 'string',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(env_name, var_name)
                )
            """)
            
            # 创建测试历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_name TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration REAL,
                    details TEXT,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
    def load_data_file(self, file_path: str, category: Optional[str] = None) -> Dict[str, Any] | List[Dict[str, Any]]:
        """
        加载数据文件
        
        Args:
            file_path: 文件路径
            category: 数据分类
            
        Returns:
            Dict[str, Any]: 加载的数据
        """
        file_obj = Path(file_path)
        
        if not file_obj.exists():
            self.logger.error(f"数据文件不存在: {file_path}")
            return {}
            
        try:
            if file_obj.suffix.lower() in ['.json']:
                with open(file_obj, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif file_obj.suffix.lower() in ['.yaml', '.yml']:
                with open(file_obj, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            elif file_obj.suffix.lower() in ['.csv']:
                data = self._load_csv_file(file_obj)
            else:
                # 尝试按文本文件读取
                with open(file_obj, 'r', encoding='utf-8') as f:
                    data = {"content": f.read()}
                    
            # 缓存数据
            cache_key = category or file_obj.stem
            self._cache[cache_key] = data
            
            self.logger.info(f"数据文件加载成功: {file_path}")
            return data
            
        except Exception as e:
            self.logger.error(f"加载数据文件失败: {file_path} - {str(e)}")
            return {}
            
    def _load_csv_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """加载CSV文件"""
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(dict(row))
        return data
        
    def save_data(self, category: str, name: str, data: Any, 
                  description: Optional[str] = None) -> bool:
        """
        保存数据到数据库
        
        Args:
            category: 数据分类
            name: 数据名称
            data: 数据内容
            description: 描述
            
        Returns:
            bool: 是否保存成功
        """
        try:
            data_json = json.dumps(data, ensure_ascii=False)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO test_data 
                    (category, name, data, description, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (category, name, data_json, description, datetime.now()))
                conn.commit()
                
            # 更新缓存
            cache_key = f"{category}.{name}"
            self._cache[cache_key] = data
            
            self.logger.info(f"数据保存成功: {category}.{name}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存数据失败: {category}.{name} - {str(e)}")
            return False
            
    def get_data(self, category: str, name: Optional[str] = None) -> Any:
        """
        获取数据
        
        Args:
            category: 数据分类
            name: 数据名称（可选）
            
        Returns:
            Any: 数据内容
        """
        if name:
            cache_key = f"{category}.{name}"
            
            # 先从缓存查找
            if cache_key in self._cache:
                return self._cache[cache_key]
                
            # 从数据库查找
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT data FROM test_data 
                        WHERE category = ? AND name = ?
                    """, (category, name))
                    
                    row = cursor.fetchone()
                    if row:
                        data = json.loads(row[0])
                        self._cache[cache_key] = data
                        return data
                        
            except Exception as e:
                self.logger.error(f"获取数据失败: {category}.{name} - {str(e)}")
                
        else:
            # 获取分类下的所有数据
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT name, data FROM test_data 
                        WHERE category = ?
                    """, (category,))
                    
                    result = {}
                    for row in cursor.fetchall():
                        name, data_json = row
                        result[name] = json.loads(data_json)
                        
                    return result
                    
            except Exception as e:
                self.logger.error(f"获取分类数据失败: {category} - {str(e)}")
                
        return None
        
    def list_categories(self) -> List[str]:
        """列出所有数据分类"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT category FROM test_data ORDER BY category")
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"列出分类失败: {str(e)}")
            return []
            
    def list_data_names(self, category: str) -> List[str]:
        """列出指定分类下的所有数据名称"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM test_data 
                    WHERE category = ? ORDER BY name
                """, (category,))
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"列出数据名称失败: {category} - {str(e)}")
            return []
            
    def delete_data(self, category: str, name: Optional[str] = None) -> bool:
        """
        删除数据
        
        Args:
            category: 数据分类
            name: 数据名称（可选，不指定则删除整个分类）
            
        Returns:
            bool: 是否删除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if name:
                    cursor.execute("""
                        DELETE FROM test_data 
                        WHERE category = ? AND name = ?
                    """, (category, name))
                    
                    # 清除缓存
                    cache_key = f"{category}.{name}"
                    if cache_key in self._cache:
                        del self._cache[cache_key]
                        
                else:
                    cursor.execute("""
                        DELETE FROM test_data WHERE category = ?
                    """, (category,))
                    
                    # 清除相关缓存
                    keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{category}.")]
                    for key in keys_to_remove:
                        del self._cache[key]
                        
                conn.commit()
                
            self.logger.info(f"数据删除成功: {category}{f'.{name}' if name else ''}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除数据失败: {category}{f'.{name}' if name else ''} - {str(e)}")
            return False
            
    def set_environment_variable(self, env_name: str, var_name: str, 
                                var_value: str, var_type: str = "string",
                                description: Optional[str] = None) -> bool:
        """
        设置环境变量
        
        Args:
            env_name: 环境名称
            var_name: 变量名
            var_value: 变量值
            var_type: 变量类型
            description: 描述
            
        Returns:
            bool: 是否设置成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO environment_vars 
                    (env_name, var_name, var_value, var_type, description, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (env_name, var_name, var_value, var_type, description, datetime.now()))
                conn.commit()
                
            self.logger.info(f"环境变量设置成功: {env_name}.{var_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置环境变量失败: {env_name}.{var_name} - {str(e)}")
            return False
            
    def get_environment_variables(self, env_name: str) -> Dict[str, Any]:
        """
        获取环境变量
        
        Args:
            env_name: 环境名称
            
        Returns:
            Dict[str, Any]: 环境变量字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT var_name, var_value, var_type 
                    FROM environment_vars 
                    WHERE env_name = ?
                """, (env_name,))
                
                variables = {}
                for row in cursor.fetchall():
                    var_name, var_value, var_type = row
                    
                    # 根据类型转换值
                    if var_type == "integer":
                        variables[var_name] = int(var_value)
                    elif var_type == "float":
                        variables[var_name] = float(var_value)
                    elif var_type == "boolean":
                        variables[var_name] = var_value.lower() in ("true", "1", "yes")
                    elif var_type == "json":
                        variables[var_name] = json.loads(var_value)
                    else:
                        variables[var_name] = var_value
                        
                return variables
                
        except Exception as e:
            self.logger.error(f"获取环境变量失败: {env_name} - {str(e)}")
            return {}
            
    def export_data(self, output_file: str, category: Optional[str] = None,
                   format: str = "json") -> bool:
        """
        导出数据
        
        Args:
            output_file: 输出文件路径
            category: 数据分类（可选）
            format: 导出格式
            
        Returns:
            bool: 是否导出成功
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if category:
                    cursor.execute("""
                        SELECT category, name, data, description, created_at 
                        FROM test_data WHERE category = ?
                    """, (category,))
                else:
                    cursor.execute("""
                        SELECT category, name, data, description, created_at 
                        FROM test_data
                    """)
                
                export_data = []
                for row in cursor.fetchall():
                    category, name, data, description, created_at = row
                    export_data.append({
                        "category": category,
                        "name": name,
                        "data": json.loads(data),
                        "description": description,
                        "created_at": created_at
                    })
                    
            if format.lower() == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            elif format.lower() == "yaml":
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"不支持的导出格式: {format}")
                
            self.logger.info(f"数据导出成功: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出数据失败: {str(e)}")
            return False
            
    def import_data(self, input_file: str) -> bool:
        """
        导入数据
        
        Args:
            input_file: 输入文件路径
            
        Returns:
            bool: 是否导入成功
        """
        try:
            input_path = Path(input_file)
            
            if not input_path.exists():
                self.logger.error(f"导入文件不存在: {input_path}")
                return False
                
            if input_path.suffix.lower() == ".json":
                with open(input_path, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
            elif input_path.suffix.lower() in [".yaml", ".yml"]:
                with open(input_path, 'r', encoding='utf-8') as f:
                    import_data = yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的导入格式: {input_path.suffix}")
                
            # 导入数据
            imported_count = 0
            for item in import_data:
                if self.save_data(
                    item["category"], 
                    item["name"], 
                    item["data"], 
                    item.get("description")
                ):
                    imported_count += 1
                    
            self.logger.info(f"数据导入成功: {imported_count} 条记录")
            return True
            
        except Exception as e:
            self.logger.error(f"导入数据失败: {str(e)}")
            return False
            
    def record_test_history(self, test_name: str, environment: str, 
                          status: str, duration: Optional[float] = None,
                          details: Optional[str] = None) -> bool:
        """
        记录测试历史
        
        Args:
            test_name: 测试名称
            environment: 环境名称
            status: 测试状态
            duration: 执行时长
            details: 详细信息
            
        Returns:
            bool: 是否记录成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO test_history 
                    (test_name, environment, status, duration, details)
                    VALUES (?, ?, ?, ?, ?)
                """, (test_name, environment, status, duration, details))
                conn.commit()
                
            return True
            
        except Exception as e:
            self.logger.error(f"记录测试历史失败: {str(e)}")
            return False
            
    def get_test_history(self, test_name: Optional[str] = None, 
                        environment: Optional[str] = None, 
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取测试历史
        
        Args:
            test_name: 测试名称（可选）
            environment: 环境名称（可选）
            limit: 返回记录数限制
            
        Returns:
            List[Dict[str, Any]]: 测试历史记录
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM test_history WHERE 1=1"
                params = []
                
                if test_name:
                    query += " AND test_name = ?"
                    params.append(test_name)
                    
                if environment:
                    query += " AND environment = ?"
                    params.append(environment)
                    
                query += " ORDER BY executed_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"获取测试历史失败: {str(e)}")
            return []
            
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        self.logger.info("缓存已清除")