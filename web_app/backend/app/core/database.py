"""
数据库连接和管理模块
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import sqlite3
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """简单的数据库管理器，使用 SQLite 作为存储"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认数据库路径
            db_dir = Path(__file__).parent.parent.parent / "data"
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / "algokg.db"
        
        self.db_path = str(db_path)
        self._local = threading.local()
        self._init_database()
    
    def _get_connection(self):
        """获取线程本地的数据库连接"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    @contextmanager
    def get_db_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = self._get_connection()
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.commit()
    
    def _init_database(self):
        """初始化数据库表"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 创建笔记表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    processed_content TEXT,
                    note_type TEXT DEFAULT 'general',
                    file_format TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    file_path TEXT,
                    tags TEXT DEFAULT '[]',
                    description TEXT,
                    is_public BOOLEAN DEFAULT FALSE,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    analysis_data TEXT DEFAULT '{}'
                )
            """)
            
            # 创建用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建管理员表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    role TEXT DEFAULT 'admin',
                    permissions TEXT DEFAULT '[]',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    session_data TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("数据库初始化完成")
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """执行查询并返回结果"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            columns = [description[0] for description in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新操作并返回影响的行数"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')

# 全局数据库实例
_db_manager = None

def get_database() -> DatabaseManager:
    """获取数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def init_database():
    """初始化数据库"""
    db = get_database()
    logger.info("数据库连接已建立")
    return db

# 便捷函数
def get_db_connection():
    """获取数据库连接"""
    return get_database().get_db_connection()

def execute_query(query: str, params: tuple = None) -> List[Dict]:
    """执行查询"""
    return get_database().execute_query(query, params)

def execute_update(query: str, params: tuple = None) -> int:
    """执行更新"""
    return get_database().execute_update(query, params)
