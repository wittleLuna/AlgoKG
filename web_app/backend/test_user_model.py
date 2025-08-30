#!/usr/bin/env python3
"""
测试用户模型
"""

from app.models.user import UserCreate

def test_user_create():
    # 测试正常数据
    test_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    }
    
    try:
        user = UserCreate(**test_data)
        print("✅ 用户模型创建成功:")
        print(f"  用户名: {user.username}")
        print(f"  邮箱: {user.email}")
        print(f"  密码长度: {len(user.password)}")
        print(f"  真实姓名: {user.full_name}")
        return True
    except Exception as e:
        print(f"❌ 用户模型创建失败: {e}")
        return False

def test_invalid_data():
    # 测试无效数据
    invalid_data_sets = [
        {"username": "ab", "email": "test@example.com", "password": "password123"},  # 用户名太短
        {"username": "testuser", "email": "invalid-email", "password": "password123"},  # 邮箱格式错误
        {"username": "testuser", "email": "test@example.com", "password": "123"},  # 密码太短
    ]
    
    for i, data in enumerate(invalid_data_sets):
        try:
            user = UserCreate(**data)
            print(f"❌ 测试 {i+1} 应该失败但成功了: {data}")
        except Exception as e:
            print(f"✅ 测试 {i+1} 正确失败: {e}")

if __name__ == "__main__":
    print("测试用户模型...")
    test_user_create()
    print("\n测试无效数据...")
    test_invalid_data()
