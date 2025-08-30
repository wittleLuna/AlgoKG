#!/usr/bin/env python3
"""
AlgoKG Web应用系统测试脚本
测试前后端API连接、数据库连接等核心功能
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, Any

class SystemTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = []
    
    async def test_backend_health(self) -> bool:
        """测试后端健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ 后端健康检查通过: {data.get('status', 'unknown')}")
                        return True
                    else:
                        print(f"❌ 后端健康检查失败: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 后端连接失败: {e}")
            return False
    
    async def test_frontend_availability(self) -> bool:
        """测试前端可用性"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.frontend_url) as response:
                    if response.status == 200:
                        print("✅ 前端服务可访问")
                        return True
                    else:
                        print(f"❌ 前端访问失败: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 前端连接失败: {e}")
            return False
    
    async def test_api_endpoints(self) -> bool:
        """测试主要API端点"""
        endpoints = [
            ("/", "GET", "根路径"),
            ("/api/v1/graph/statistics", "GET", "图谱统计"),
        ]
        
        all_passed = True
        
        async with aiohttp.ClientSession() as session:
            for endpoint, method, description in endpoints:
                try:
                    url = f"{self.backend_url}{endpoint}"
                    async with session.request(method, url) as response:
                        if response.status == 200:
                            print(f"✅ {description} API测试通过")
                        else:
                            print(f"❌ {description} API测试失败: HTTP {response.status}")
                            all_passed = False
                except Exception as e:
                    print(f"❌ {description} API测试异常: {e}")
                    all_passed = False
        
        return all_passed
    
    async def test_qa_functionality(self) -> bool:
        """测试问答功能"""
        test_query = {
            "query": "请解释动态规划的概念",
            "session_id": "test_session"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/v1/qa/query",
                    json=test_query,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("integrated_response"):
                            print("✅ 问答功能测试通过")
                            return True
                        else:
                            print("❌ 问答功能返回数据异常")
                            return False
                    else:
                        print(f"❌ 问答功能测试失败: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 问答功能测试异常: {e}")
            return False
    
    async def test_graph_functionality(self) -> bool:
        """测试图谱功能"""
        test_query = {
            "entity_name": "动态规划",
            "entity_type": "Algorithm",
            "depth": 2,
            "limit": 10
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/v1/graph/query",
                    json=test_query,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("nodes") and data.get("edges"):
                            print("✅ 图谱功能测试通过")
                            return True
                        else:
                            print("❌ 图谱功能返回数据异常")
                            return False
                    else:
                        print(f"❌ 图谱功能测试失败: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 图谱功能测试异常: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始系统测试...")
        print("=" * 50)
        
        tests = [
            ("后端健康检查", self.test_backend_health),
            ("前端可用性", self.test_frontend_availability),
            ("API端点", self.test_api_endpoints),
            ("问答功能", self.test_qa_functionality),
            ("图谱功能", self.test_graph_functionality),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 测试: {test_name}")
            try:
                result = await test_func()
                if result:
                    passed += 1
                self.test_results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
                self.test_results.append((test_name, False))
        
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")
        print(f"✅ 通过: {passed}/{total}")
        print(f"❌ 失败: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 所有测试通过！系统运行正常")
            return True
        else:
            print("\n⚠️  部分测试失败，请检查系统配置")
            return False

async def main():
    """主函数"""
    print("AlgoKG Web应用系统测试")
    print("=" * 50)
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    await asyncio.sleep(5)
    
    tester = SystemTester()
    success = await tester.run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 测试过程中发生异常: {e}")
        sys.exit(1)
