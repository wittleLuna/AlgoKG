#!/usr/bin/env python3
"""
调试特定节点的详情获取问题
"""

import requests
import json
import urllib.parse

def test_specific_node():
    """测试具体的节点"""
    print("🔍 测试具体节点: 不同的子序列")
    
    # 测试不同的节点ID格式
    test_cases = [
        {
            "node_id": "不同的子序列",
            "node_type": "Problem",
            "description": "直接使用题目名称"
        },
        {
            "node_id": "neo4j_不同的子序列", 
            "node_type": "Problem",
            "description": "neo4j_前缀格式"
        },
        {
            "node_id": "problem_不同的子序列",
            "node_type": "Problem", 
            "description": "problem_前缀格式"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}: {test_case['description']}")
        print('='*60)
        
        node_id = test_case['node_id']
        node_type = test_case['node_type']
        
        # URL编码节点ID
        encoded_node_id = urllib.parse.quote(node_id, safe='')
        url = f"http://localhost:8000/api/v1/graph/unified/node/{encoded_node_id}/details?node_type={node_type}"
        
        print(f"节点ID: {node_id}")
        print(f"编码后: {encoded_node_id}")
        print(f"请求URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应数据类型: {type(data)}")
                print(f"响应是否为空: {len(data) == 0 if isinstance(data, dict) else 'N/A'}")
                
                if data:
                    print(f"响应字段: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                    if isinstance(data, dict):
                        if 'error' in data:
                            print(f"❌ API返回错误: {data['error']}")
                        elif 'basic_info' in data:
                            print(f"✅ 成功获取节点详情")
                            basic_info = data['basic_info']
                            print(f"标题: {basic_info.get('title', 'N/A')}")
                            print(f"类型: {basic_info.get('type', 'N/A')}")
                            print(f"描述: {basic_info.get('description', 'N/A')}")
                            print(f"难度: {basic_info.get('difficulty', 'N/A')}")
                            print(f"平台: {basic_info.get('platform', 'N/A')}")
                            
                            # 检查其他字段
                            other_fields = ['algorithms', 'data_structures', 'techniques', 'related_problems', 'complexity', 'solutions', 'insights']
                            for field in other_fields:
                                if field in data and data[field]:
                                    print(f"{field}: {len(data[field]) if isinstance(data[field], list) else 'Present'}")
                        else:
                            print(f"⚠️ 响应格式异常:")
                            print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
                    else:
                        print(f"⚠️ 响应不是字典格式: {data}")
                else:
                    print(f"❌ 响应数据为空")
                
                # 保存完整响应
                filename = f"node_debug_{i}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"完整响应已保存到: {filename}")
                
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"错误响应: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到后端服务 (确保后端在 http://localhost:8000 运行)")
        except Exception as e:
            print(f"❌ 请求失败: {e}")

def test_neo4j_direct():
    """直接测试Neo4j API"""
    print(f"\n{'='*60}")
    print("直接测试Neo4j API")
    print('='*60)
    
    # 测试Neo4j中是否存在这个题目
    url = "http://localhost:8000/api/v1/graph/problem/不同的子序列/detail"
    
    print(f"测试URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Neo4j中找到题目数据")
            print(f"响应字段: {list(data.keys())}")
            
            if 'basic_info' in data:
                basic_info = data['basic_info']
                print(f"标题: {basic_info.get('title', 'N/A')}")
                print(f"难度: {basic_info.get('difficulty', 'N/A')}")
                print(f"平台: {basic_info.get('platform', 'N/A')}")
        elif response.status_code == 404:
            print(f"❌ Neo4j中未找到题目: 不同的子序列")
        else:
            print(f"❌ Neo4j API错误: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ Neo4j API测试失败: {e}")

def test_search_similar_titles():
    """搜索相似的题目标题"""
    print(f"\n{'='*60}")
    print("搜索相似的题目标题")
    print('='*60)
    
    # 搜索包含"子序列"的题目
    search_terms = ["子序列", "不同", "序列"]
    
    for term in search_terms:
        print(f"\n搜索关键词: {term}")
        url = f"http://localhost:8000/api/v1/graph/search?keyword={urllib.parse.quote(term)}&limit=5"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    print(f"找到 {len(data)} 个相关题目:")
                    for item in data[:3]:  # 只显示前3个
                        title = item.get('title', 'N/A')
                        print(f"  - {title}")
                else:
                    print(f"未找到包含 '{term}' 的题目")
            else:
                print(f"搜索失败: {response.status_code}")
        except Exception as e:
            print(f"搜索错误: {e}")

def main():
    print("🔧 调试节点详情获取问题")
    print("="*60)
    
    # 测试具体节点
    test_specific_node()
    
    # 测试Neo4j直接API
    test_neo4j_direct()
    
    # 搜索相似标题
    test_search_similar_titles()
    
    print(f"\n{'='*60}")
    print("🎯 调试总结")
    print('='*60)
    
    print("请检查以下几点:")
    print("1. 后端服务是否正常运行在 http://localhost:8000")
    print("2. Neo4j数据库中是否存在 '不同的子序列' 这道题")
    print("3. 题目名称是否完全匹配（包括标点符号、空格等）")
    print("4. 统一图谱服务的节点ID解析是否正确")
    
    print(f"\n💡 可能的解决方案:")
    print("1. 检查Neo4j数据库中的实际题目名称")
    print("2. 确认节点ID格式是否正确")
    print("3. 查看后端日志中的详细错误信息")
    print("4. 验证数据库连接和查询是否正常")

if __name__ == "__main__":
    main()
