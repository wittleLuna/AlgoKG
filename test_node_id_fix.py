#!/usr/bin/env python3
"""
测试节点ID格式修复
"""

import requests
import json

def test_node_id_formats():
    """测试不同格式的节点ID"""
    print("🔍 测试节点ID格式修复...")
    
    # 测试不同格式的节点ID
    test_cases = [
        {
            "name": "内嵌图谱格式",
            "node_id": "neo4j_用最少数量的箭引爆气球",
            "node_type": "Problem",
            "expected_title": "用最少数量的箭引爆气球"
        },
        {
            "name": "独立面板格式",
            "node_id": "problem_climbing_stairs",
            "node_type": "Problem", 
            "expected_title": "climbing stairs"
        },
        {
            "name": "算法节点",
            "node_id": "neo4j_回溯算法",
            "node_type": "Algorithm",
            "expected_title": "回溯算法"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试用例 {i}: {test_case['name']}")
        print('='*60)
        
        node_id = test_case['node_id']
        node_type = test_case['node_type']
        
        url = f"http://localhost:8000/api/v1/graph/unified/node/{requests.utils.quote(node_id)}/details?node_type={node_type}"
        print(f"请求URL: {url}")
        print(f"节点ID: {node_id}")
        print(f"节点类型: {node_type}")
        print(f"期望提取的名称: {test_case['expected_title']}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ API响应成功")
                print(f"响应数据类型: {type(data)}")
                print(f"响应是否为空: {len(data) == 0}")
                
                if data:
                    print(f"响应字段: {list(data.keys())}")
                    
                    # 检查是否有错误
                    if 'error' in data:
                        print(f"❌ API返回错误: {data['error']}")
                    else:
                        print(f"✅ 成功获取节点详情")
                        
                        # 显示部分数据
                        if 'basic_info' in data:
                            basic_info = data['basic_info']
                            print(f"基本信息: {basic_info}")
                        else:
                            print(f"数据结构: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")
                else:
                    print(f"❌ 响应数据为空")
                
                # 保存响应
                filename = f"node_detail_test_{i}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"完整响应已保存到: {filename}")
                
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时")
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到后端服务")
        except Exception as e:
            print(f"❌ 请求失败: {e}")

def test_original_problem():
    """测试原始问题的节点"""
    print(f"\n" + "="*60)
    print("测试原始问题节点")
    print("="*60)
    
    # 这是您遇到问题的具体节点
    node_id = "neo4j_用最少数量的箭引爆气球"
    node_type = "Problem"
    
    url = f"http://localhost:8000/api/v1/graph/unified/node/{requests.utils.quote(node_id)}/details?node_type={node_type}"
    
    print(f"测试具体问题节点:")
    print(f"  节点ID: {node_id}")
    print(f"  节点类型: {node_type}")
    print(f"  请求URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and len(data) > 0 and 'error' not in data:
                print(f"✅ 修复成功！节点详情获取正常")
                print(f"响应字段: {list(data.keys())}")
                return True
            else:
                print(f"❌ 仍然有问题:")
                if 'error' in data:
                    print(f"  错误信息: {data['error']}")
                else:
                    print(f"  响应为空或格式异常")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试节点ID格式修复...")
    
    # 检查后端服务
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常运行")
        else:
            print("❌ 后端服务异常")
            return
    except:
        print("❌ 无法连接到后端服务")
        print("请确保后端服务正在运行:")
        print("  cd web_app/backend")
        print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # 测试不同格式的节点ID
    test_node_id_formats()
    
    # 测试原始问题
    success = test_original_problem()
    
    print(f"\n" + "="*60)
    print("🎯 测试总结")
    print("="*60)
    
    if success:
        print("✅ 节点ID格式修复成功！")
        print("\n现在应该能够:")
        print("1. 在内嵌图谱中点击节点")
        print("2. 正常显示节点详情抽屉")
        print("3. 看到完整的节点信息而不是空数据")
        
        print(f"\n💡 修复说明:")
        print("- 修改了UnifiedGraphService.get_node_details方法")
        print("- 支持处理neo4j_前缀的节点ID")
        print("- 兼容原有的problem_前缀格式")
        print("- 添加了详细的日志记录")
    else:
        print("❌ 修复可能不完整，需要进一步调试")
        print("\n请检查:")
        print("1. 后端日志中的错误信息")
        print("2. Neo4j数据库连接状态")
        print("3. 节点名称是否在数据库中存在")

if __name__ == "__main__":
    main()
