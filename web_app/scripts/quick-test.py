#!/usr/bin/env python3
"""
快速测试脚本 - 验证后端API是否正常工作
"""

import asyncio
import aiohttp
import json

async def test_backend():
    """测试后端API"""
    base_url = "http://localhost:8000"
    
    print("🧪 测试后端API...")
    
    async with aiohttp.ClientSession() as session:
        # 测试健康检查
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 健康检查通过: {data}")
                else:
                    print(f"❌ 健康检查失败: {response.status}")
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
        
        # 测试问答API
        try:
            test_query = {
                "query": "请解释动态规划的概念",
                "session_id": "test_session"
            }
            
            async with session.post(
                f"{base_url}/api/v1/qa/query",
                json=test_query,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 问答API测试通过")
                    print(f"   回答: {data.get('integrated_response', '')[:100]}...")
                else:
                    print(f"❌ 问答API测试失败: {response.status}")
        except Exception as e:
            print(f"❌ 问答API测试异常: {e}")
        
        # 测试图谱API
        try:
            graph_query = {
                "entity_name": "动态规划",
                "entity_type": "Algorithm",
                "depth": 2,
                "limit": 10
            }
            
            async with session.post(
                f"{base_url}/api/v1/graph/query",
                json=graph_query,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 图谱API测试通过")
                    print(f"   节点数: {len(data.get('nodes', []))}")
                    print(f"   边数: {len(data.get('edges', []))}")
                else:
                    print(f"❌ 图谱API测试失败: {response.status}")
        except Exception as e:
            print(f"❌ 图谱API测试异常: {e}")
    
    print("\n🎉 后端测试完成！")
    return True

if __name__ == "__main__":
    asyncio.run(test_backend())
