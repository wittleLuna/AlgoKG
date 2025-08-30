#!/usr/bin/env python3
"""
调试当前节点详情问题
"""

import requests
import json
import urllib.parse

def test_common_node_formats():
    """测试常见的节点ID格式"""
    print("🔍 测试常见节点ID格式...")
    
    # 基于您看到的错误，测试可能的节点ID
    test_cases = [
        # 基于QA服务可能生成的格式
        {"id": "neo4j_不同的子序列", "type": "Problem", "desc": "QA服务格式"},
        {"id": "不同的子序列", "type": "Problem", "desc": "直接题目名"},
        {"id": "problem_不同的子序列", "type": "Problem", "desc": "problem前缀"},
        
        # 测试其他可能的题目
        {"id": "neo4j_两数之和", "type": "Problem", "desc": "两数之和"},
        {"id": "两数之和", "type": "Problem", "desc": "两数之和直接"},
        
        # 测试算法节点
        {"id": "neo4j_动态规划", "type": "Algorithm", "desc": "动态规划算法"},
        {"id": "动态规划", "type": "Algorithm", "desc": "动态规划直接"},
        
        # 测试数据结构节点
        {"id": "neo4j_数组", "type": "DataStructure", "desc": "数组数据结构"},
        {"id": "数组", "type": "DataStructure", "desc": "数组直接"},
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"测试 {i}: {case['desc']}")
        print('='*50)
        
        node_id = case['id']
        node_type = case['type']
        
        encoded_id = urllib.parse.quote(node_id, safe='')
        url = f"http://localhost:8000/api/v1/graph/unified/node/{encoded_id}/details?node_type={node_type}"
        
        print(f"节点ID: {node_id}")
        print(f"节点类型: {node_type}")
        print(f"请求URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict):
                    if 'error' in data:
                        print(f"❌ API错误: {data['error']}")
                    elif 'basic_info' in data:
                        print(f"✅ 成功获取数据")
                        print(f"标题: {data['basic_info'].get('title', 'N/A')}")
                        print(f"字段数: {len(data)}")
                        print(f"算法数: {len(data.get('algorithms', []))}")
                        print(f"数据结构数: {len(data.get('data_structures', []))}")
                    else:
                        print(f"⚠️ 数据格式异常: {list(data.keys())}")
                else:
                    print(f"⚠️ 响应不是字典: {type(data)}")
                    
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"错误内容: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ 连接失败 - 确保后端运行在 http://localhost:8000")
            break
        except Exception as e:
            print(f"❌ 请求异常: {e}")

def check_backend_logs():
    """检查后端日志"""
    print(f"\n{'='*50}")
    print("检查后端服务状态")
    print('='*50)
    
    try:
        # 测试基本连接
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常运行")
        else:
            print(f"⚠️ 后端服务状态异常: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务")
        print("请确保运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False
    
    return True

def test_neo4j_direct():
    """直接测试Neo4j API"""
    print(f"\n{'='*50}")
    print("测试Neo4j直接API")
    print('='*50)
    
    # 测试一些常见题目
    test_titles = ["不同的子序列", "两数之和", "三数之和", "最长公共子序列"]
    
    for title in test_titles:
        encoded_title = urllib.parse.quote(title)
        url = f"http://localhost:8000/api/v1/graph/problem/{encoded_title}/detail"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Neo4j中找到: {title}")
                return title  # 返回第一个找到的题目
            elif response.status_code == 404:
                print(f"❌ Neo4j中未找到: {title}")
            else:
                print(f"⚠️ {title} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ 测试 {title} 失败: {e}")
    
    return None

def main():
    print("🔧 调试当前节点详情问题")
    print("="*60)
    
    # 1. 检查后端服务
    if not check_backend_logs():
        return
    
    # 2. 测试Neo4j直接API
    found_title = test_neo4j_direct()
    
    # 3. 测试常见节点格式
    test_common_node_formats()
    
    print(f"\n{'='*60}")
    print("🎯 问题分析")
    print('='*60)
    
    if found_title:
        print(f"✅ Neo4j中存在题目数据，例如: {found_title}")
        print("问题可能在于:")
        print("1. 前端传递的节点ID格式不正确")
        print("2. 统一图谱服务的ID解析逻辑有问题")
        print("3. 节点类型不匹配")
    else:
        print("❌ Neo4j中可能没有相关题目数据")
        print("建议:")
        print("1. 检查Neo4j数据库连接")
        print("2. 确认数据是否已正确导入")
        print("3. 查看后端日志中的详细错误")
    
    print(f"\n💡 下一步调试:")
    print("1. 查看浏览器控制台中的具体错误信息")
    print("2. 检查前端发送的实际节点ID")
    print("3. 查看后端日志中的详细错误")
    print("4. 确认点击的节点ID格式")

if __name__ == "__main__":
    main()
