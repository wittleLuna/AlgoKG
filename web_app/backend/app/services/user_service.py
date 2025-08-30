"""
用户服务 - 处理用户相关的业务逻辑
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.user import (
    User, UserCreate, UserUpdate, UserInDB, UserLogin, 
    UserStats, UserProfile, UserRole, UserStatus,
    Favorite, FavoriteCreate, SearchHistory, SearchHistoryCreate,
    Session, SessionCreate, SessionUpdate, Message, MessageCreate
)
from app.core.auth import get_password_hash, verify_password
import logging

logger = logging.getLogger(__name__)


class UserService:
    """用户服务类"""
    
    def __init__(self, db_path: str = "data/users.db"):
        # 确保数据目录存在
        import os
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 用户表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        hashed_password TEXT NOT NULL,
                        full_name TEXT,
                        avatar_url TEXT,
                        bio TEXT,
                        role TEXT DEFAULT 'user',
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login_at TIMESTAMP,
                        login_count INTEGER DEFAULT 0
                    )
                """)
                
                # 收藏表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS favorites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        item_type TEXT NOT NULL,
                        item_id TEXT NOT NULL,
                        title TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        UNIQUE(user_id, item_type, item_id)
                    )
                """)
                
                # 搜索历史表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS search_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        query TEXT NOT NULL,
                        search_type TEXT NOT NULL,
                        results_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # 会话表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        message_count INTEGER DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # 消息表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        message_type TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    )
                """)
                
                conn.commit()
                logger.info("数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def create_user(self, user_data: UserCreate) -> UserInDB:
        """创建新用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查用户名和邮箱是否已存在
                cursor.execute(
                    "SELECT id FROM users WHERE username = ? OR email = ?",
                    (user_data.username, user_data.email)
                )
                if cursor.fetchone():
                    raise ValueError("用户名或邮箱已存在")
                
                # 创建用户
                hashed_password = get_password_hash(user_data.password)
                cursor.execute("""
                    INSERT INTO users (username, email, hashed_password, full_name, avatar_url, bio)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_data.username,
                    user_data.email,
                    hashed_password,
                    user_data.full_name,
                    user_data.avatar_url,
                    user_data.bio
                ))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                # 获取创建的用户
                return self.get_user_by_id(user_id)
                
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            raise
    
    def get_user_by_id(self, user_id: int) -> Optional[UserInDB]:
        """根据ID获取用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return UserInDB(**dict(row))
                return None
                
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """根据用户名获取用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                
                if row:
                    return UserInDB(**dict(row))
                return None
                
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """根据邮箱获取用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                row = cursor.fetchone()
                
                if row:
                    return UserInDB(**dict(row))
                return None
                
        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """验证用户登录"""
        try:
            # 支持用户名或邮箱登录
            user = self.get_user_by_username(username)
            if not user:
                user = self.get_user_by_email(username)
            
            if not user:
                return None
            
            if not verify_password(password, user.hashed_password):
                return None
            
            # 更新登录信息
            self.update_login_info(user.id)
            
            return user
            
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return None
    
    def update_login_info(self, user_id: int):
        """更新用户登录信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users 
                    SET last_login_at = CURRENT_TIMESTAMP, 
                        login_count = login_count + 1
                    WHERE id = ?
                """, (user_id,))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"更新登录信息失败: {e}")
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserInDB]:
        """更新用户信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建更新字段
                update_fields = []
                values = []
                
                if user_data.full_name is not None:
                    update_fields.append("full_name = ?")
                    values.append(user_data.full_name)
                
                if user_data.avatar_url is not None:
                    update_fields.append("avatar_url = ?")
                    values.append(user_data.avatar_url)
                
                if user_data.bio is not None:
                    update_fields.append("bio = ?")
                    values.append(user_data.bio)
                
                if not update_fields:
                    return self.get_user_by_id(user_id)
                
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                values.append(user_id)
                
                cursor.execute(f"""
                    UPDATE users SET {', '.join(update_fields)}
                    WHERE id = ?
                """, values)
                
                conn.commit()
                
                return self.get_user_by_id(user_id)
                
        except Exception as e:
            logger.error(f"更新用户信息失败: {e}")
            return None

    def get_user_stats(self, user_id: int) -> UserStats:
        """获取用户统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 获取各种统计数据
                cursor.execute("SELECT COUNT(*) FROM favorites WHERE user_id = ?", (user_id,))
                total_favorites = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM sessions WHERE user_id = ?", (user_id,))
                total_sessions = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(DISTINCT query) FROM search_history WHERE user_id = ?", (user_id,))
                total_questions = cursor.fetchone()[0]

                # 获取最后活动时间
                cursor.execute("""
                    SELECT MAX(created_at) FROM (
                        SELECT created_at FROM search_history WHERE user_id = ?
                        UNION ALL
                        SELECT created_at FROM favorites WHERE user_id = ?
                        UNION ALL
                        SELECT updated_at FROM sessions WHERE user_id = ?
                    )
                """, (user_id, user_id, user_id))

                last_activity_str = cursor.fetchone()[0]
                last_activity = None
                if last_activity_str:
                    last_activity = datetime.fromisoformat(last_activity_str)

                return UserStats(
                    total_questions=total_questions,
                    total_sessions=total_sessions,
                    total_favorites=total_favorites,
                    total_uploads=0,  # 暂时设为0，后续实现上传功能时更新
                    last_activity=last_activity
                )

        except Exception as e:
            logger.error(f"获取用户统计信息失败: {e}")
            return UserStats()

    def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """获取用户详细资料"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None

            stats = self.get_user_stats(user_id)

            # 转换为User模型（去除敏感信息）
            user_dict = user.dict()
            del user_dict['hashed_password']
            user_public = User(**user_dict)

            return UserProfile(**user_public.dict(), stats=stats)

        except Exception as e:
            logger.error(f"获取用户资料失败: {e}")
            return None

    # 收藏相关方法
    def add_favorite(self, user_id: int, favorite_data: FavoriteCreate) -> Optional[Favorite]:
        """添加收藏"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO favorites
                    (user_id, item_type, item_id, title, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id,
                    favorite_data.item_type,
                    favorite_data.item_id,
                    favorite_data.title,
                    favorite_data.description
                ))

                favorite_id = cursor.lastrowid
                conn.commit()

                return self.get_favorite_by_id(favorite_id)

        except Exception as e:
            logger.error(f"添加收藏失败: {e}")
            return None

    def get_favorite_by_id(self, favorite_id: int) -> Optional[Favorite]:
        """根据ID获取收藏"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM favorites WHERE id = ?", (favorite_id,))
                row = cursor.fetchone()

                if row:
                    return Favorite(**dict(row))
                return None

        except Exception as e:
            logger.error(f"获取收藏失败: {e}")
            return None

    def get_user_favorites(self, user_id: int, item_type: Optional[str] = None,
                          limit: int = 50, offset: int = 0) -> List[Favorite]:
        """获取用户收藏列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if item_type:
                    cursor.execute("""
                        SELECT * FROM favorites
                        WHERE user_id = ? AND item_type = ?
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    """, (user_id, item_type, limit, offset))
                else:
                    cursor.execute("""
                        SELECT * FROM favorites
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    """, (user_id, limit, offset))

                rows = cursor.fetchall()
                return [Favorite(**dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"获取用户收藏列表失败: {e}")
            return []

    def remove_favorite(self, user_id: int, item_type: str, item_id: str) -> bool:
        """移除收藏"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    DELETE FROM favorites
                    WHERE user_id = ? AND item_type = ? AND item_id = ?
                """, (user_id, item_type, item_id))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"移除收藏失败: {e}")
            return False

    # 搜索历史相关方法
    def add_search_history(self, user_id: int, search_data: SearchHistoryCreate) -> Optional[SearchHistory]:
        """添加搜索历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO search_history
                    (user_id, query, search_type, results_count)
                    VALUES (?, ?, ?, ?)
                """, (
                    user_id,
                    search_data.query,
                    search_data.search_type,
                    search_data.results_count
                ))

                history_id = cursor.lastrowid
                conn.commit()

                return self.get_search_history_by_id(history_id)

        except Exception as e:
            logger.error(f"添加搜索历史失败: {e}")
            return None

    def get_search_history_by_id(self, history_id: int) -> Optional[SearchHistory]:
        """根据ID获取搜索历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM search_history WHERE id = ?", (history_id,))
                row = cursor.fetchone()

                if row:
                    return SearchHistory(**dict(row))
                return None

        except Exception as e:
            logger.error(f"获取搜索历史失败: {e}")
            return None

    def get_user_search_history(self, user_id: int, search_type: Optional[str] = None,
                               limit: int = 50, offset: int = 0) -> List[SearchHistory]:
        """获取用户搜索历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if search_type:
                    cursor.execute("""
                        SELECT * FROM search_history
                        WHERE user_id = ? AND search_type = ?
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    """, (user_id, search_type, limit, offset))
                else:
                    cursor.execute("""
                        SELECT * FROM search_history
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    """, (user_id, limit, offset))

                rows = cursor.fetchall()
                return [SearchHistory(**dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"获取用户搜索历史失败: {e}")
            return []

    def clear_search_history(self, user_id: int, search_type: Optional[str] = None) -> bool:
        """清空搜索历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if search_type:
                    cursor.execute("""
                        DELETE FROM search_history
                        WHERE user_id = ? AND search_type = ?
                    """, (user_id, search_type))
                else:
                    cursor.execute("""
                        DELETE FROM search_history WHERE user_id = ?
                    """, (user_id,))

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"清空搜索历史失败: {e}")
            return False

    # 会话管理相关方法
    def create_session(self, user_id: int, session_data: SessionCreate) -> Optional[Session]:
        """创建新会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO sessions (user_id, title, description)
                    VALUES (?, ?, ?)
                """, (
                    user_id,
                    session_data.title,
                    session_data.description
                ))

                session_id = cursor.lastrowid
                conn.commit()

                return self.get_session_by_id(session_id)

        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return None

    def get_session_by_id(self, session_id: int) -> Optional[Session]:
        """根据ID获取会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()

                if row:
                    return Session(**dict(row))
                return None

        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None

    def get_user_sessions(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Session]:
        """获取用户会话列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM sessions
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))

                rows = cursor.fetchall()
                return [Session(**dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"获取用户会话列表失败: {e}")
            return []

    def update_session(self, session_id: int, session_data: SessionUpdate) -> Optional[Session]:
        """更新会话信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 构建更新字段
                update_fields = []
                values = []

                if session_data.title is not None:
                    update_fields.append("title = ?")
                    values.append(session_data.title)

                if session_data.description is not None:
                    update_fields.append("description = ?")
                    values.append(session_data.description)

                if not update_fields:
                    return self.get_session_by_id(session_id)

                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                values.append(session_id)

                cursor.execute(f"""
                    UPDATE sessions SET {', '.join(update_fields)}
                    WHERE id = ?
                """, values)

                conn.commit()

                return self.get_session_by_id(session_id)

        except Exception as e:
            logger.error(f"更新会话信息失败: {e}")
            return None

    def delete_session(self, session_id: int, user_id: int) -> bool:
        """删除会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 先删除会话中的所有消息
                cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))

                # 再删除会话（确保只能删除自己的会话）
                cursor.execute("""
                    DELETE FROM sessions
                    WHERE id = ? AND user_id = ?
                """, (session_id, user_id))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False

    def get_user_stats(self, user_id: int) -> UserStats:
        """获取用户统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 获取各种统计数据
                cursor.execute("SELECT COUNT(*) FROM favorites WHERE user_id = ?", (user_id,))
                total_favorites = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM sessions WHERE user_id = ?", (user_id,))
                total_sessions = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(DISTINCT query) FROM search_history WHERE user_id = ?", (user_id,))
                total_questions = cursor.fetchone()[0]

                # 获取最后活动时间
                cursor.execute("""
                    SELECT MAX(created_at) FROM (
                        SELECT created_at FROM search_history WHERE user_id = ?
                        UNION ALL
                        SELECT created_at FROM favorites WHERE user_id = ?
                        UNION ALL
                        SELECT updated_at FROM sessions WHERE user_id = ?
                    )
                """, (user_id, user_id, user_id))

                last_activity_str = cursor.fetchone()[0]
                last_activity = None
                if last_activity_str:
                    last_activity = datetime.fromisoformat(last_activity_str)

                return UserStats(
                    total_questions=total_questions,
                    total_sessions=total_sessions,
                    total_favorites=total_favorites,
                    total_uploads=0,  # 暂时设为0，后续实现上传功能时更新
                    last_activity=last_activity
                )

        except Exception as e:
            logger.error(f"获取用户统计信息失败: {e}")
            return UserStats()

    def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """获取用户详细资料"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None

            stats = self.get_user_stats(user_id)

            # 转换为User模型（去除敏感信息）
            user_dict = user.dict()
            del user_dict['hashed_password']
            user_public = User(**user_dict)

            return UserProfile(**user_public.dict(), stats=stats)

        except Exception as e:
            logger.error(f"获取用户资料失败: {e}")
            return None

    # 收藏相关方法
    def add_favorite(self, user_id: int, favorite_data: FavoriteCreate) -> Optional[Favorite]:
        """添加收藏"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO favorites
                    (user_id, item_type, item_id, title, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id,
                    favorite_data.item_type,
                    favorite_data.item_id,
                    favorite_data.title,
                    favorite_data.description
                ))

                favorite_id = cursor.lastrowid
                conn.commit()

                return self.get_favorite_by_id(favorite_id)

        except Exception as e:
            logger.error(f"添加收藏失败: {e}")
            return None

    def get_favorite_by_id(self, favorite_id: int) -> Optional[Favorite]:
        """根据ID获取收藏"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM favorites WHERE id = ?", (favorite_id,))
                row = cursor.fetchone()

                if row:
                    return Favorite(**dict(row))
                return None

        except Exception as e:
            logger.error(f"获取收藏失败: {e}")
            return None

    def get_user_favorites(self, user_id: int, item_type: Optional[str] = None,
                          limit: int = 50, offset: int = 0) -> List[Favorite]:
        """获取用户收藏列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if item_type:
                    cursor.execute("""
                        SELECT * FROM favorites
                        WHERE user_id = ? AND item_type = ?
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    """, (user_id, item_type, limit, offset))
                else:
                    cursor.execute("""
                        SELECT * FROM favorites
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    """, (user_id, limit, offset))

                rows = cursor.fetchall()
                return [Favorite(**dict(row)) for row in rows]

        except Exception as e:
            logger.error(f"获取用户收藏列表失败: {e}")
            return []

    def remove_favorite(self, user_id: int, item_type: str, item_id: str) -> bool:
        """移除收藏"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    DELETE FROM favorites
                    WHERE user_id = ? AND item_type = ? AND item_id = ?
                """, (user_id, item_type, item_id))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"移除收藏失败: {e}")
            return False
