#!/usr/bin/env python3
"""
专门调试前端图谱显示问题
"""

import requests
import json
import time

def test_api_and_save_response():
    """测试API并保存响应数据"""
    print("=" * 60)
    print("测试API并保存完整响应")
    print("=" * 60)
    
    api_url = "http://localhost:8000/api/v1/qa/query"
    
    request_data = {
        "query": "什么是回溯算法？",
        "query_type": "concept_explanation", 
        "session_id": "debug_frontend"
    }
    
    print(f"发送请求到: {api_url}")
    print(f"请求数据: {json.dumps(request_data, ensure_ascii=False)}")
    
    try:
        response = requests.post(api_url, json=request_data, timeout=30)
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 保存完整响应
            with open('frontend_debug_response.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 完整响应已保存到: frontend_debug_response.json")
            
            # 检查关键字段
            print(f"\n关键字段检查:")
            print(f"  response_id: {data.get('response_id', 'N/A')}")
            print(f"  query: {data.get('query', 'N/A')}")
            print(f"  entities: {data.get('entities', [])}")
            print(f"  status: {data.get('status', 'N/A')}")
            
            # 重点检查graph_data
            graph_data = data.get('graph_data')
            print(f"\n图谱数据详细分析:")
            
            if graph_data is None:
                print(f"  ❌ graph_data字段不存在或为null")
                return False
            
            print(f"  ✅ graph_data字段存在")
            print(f"  类型: {type(graph_data)}")
            
            # 检查必要的子字段
            required_fields = ['nodes', 'edges', 'center_node', 'layout_type']
            for field in required_fields:
                value = graph_data.get(field)
                print(f"  {field}: {type(value)} = {value if field != 'nodes' else f'数组长度{len(value) if isinstance(value, list) else 0}'}")
            
            # 检查nodes数组
            nodes = graph_data.get('nodes')
            if not isinstance(nodes, list):
                print(f"  ❌ nodes不是数组类型")
                return False
            
            if len(nodes) == 0:
                print(f"  ❌ nodes数组为空")
                return False
            
            print(f"  ✅ nodes数组有效，包含{len(nodes)}个节点")
            
            # 显示前几个节点
            print(f"\n  节点示例:")
            for i, node in enumerate(nodes[:3]):
                print(f"    节点{i+1}: {json.dumps(node, ensure_ascii=False)}")
            
            # 检查edges数组
            edges = graph_data.get('edges', [])
            print(f"\n  边数组: {len(edges)}条边")
            if edges:
                print(f"  边示例: {json.dumps(edges[0], ensure_ascii=False)}")
            
            # 前端显示条件验证
            print(f"\n前端显示条件验证:")
            condition1 = graph_data is not None
            condition2 = isinstance(nodes, list)
            condition3 = len(nodes) > 0
            
            print(f"  条件1 (graph_data存在): {condition1}")
            print(f"  条件2 (nodes是数组): {condition2}")
            print(f"  条件3 (nodes长度>0): {condition3}")
            
            final_result = condition1 and condition2 and condition3
            print(f"  最终判断: {'✅ 应该显示图谱' if final_result else '❌ 不应该显示图谱'}")
            
            return final_result
            
        else:
            print(f"❌ API请求失败")
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到后端服务 {api_url}")
        print(f"请确保后端服务正在运行:")
        print(f"  cd web_app/backend")
        print(f"  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def create_minimal_test_html():
    """创建最小化的测试HTML页面"""
    print("\n" + "=" * 60)
    print("创建最小化测试页面")
    print("=" * 60)
    
    html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>图谱显示测试</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .test-section { margin: 20px 0; padding: 15px; border: 1px solid #ccc; }
        .graph-container { height: 400px; border: 2px solid #007bff; background: #f8f9fa; }
        .success { color: green; }
        .error { color: red; }
        .info { color: blue; }
    </style>
</head>
<body>
    <h1>知识图谱显示测试</h1>
    
    <div class="test-section">
        <h2>1. API响应测试</h2>
        <button onclick="testAPI()">测试API响应</button>
        <div id="api-result"></div>
    </div>
    
    <div class="test-section">
        <h2>2. 图谱数据验证</h2>
        <button onclick="validateGraphData()">验证图谱数据</button>
        <div id="validation-result"></div>
    </div>
    
    <div class="test-section">
        <h2>3. 前端显示条件测试</h2>
        <button onclick="testDisplayConditions()">测试显示条件</button>
        <div id="condition-result"></div>
    </div>
    
    <div class="test-section">
        <h2>4. 模拟图谱容器</h2>
        <div class="graph-container" id="graph-container">
            <p style="text-align: center; padding-top: 180px;">图谱将在这里显示</p>
        </div>
    </div>

    <script>
        let currentGraphData = null;
        
        async function testAPI() {
            const resultDiv = document.getElementById('api-result');
            resultDiv.innerHTML = '<p class="info">正在测试API...</p>';
            
            try {
                const response = await fetch('http://localhost:8000/api/v1/qa/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: '什么是回溯算法？',
                        query_type: 'concept_explanation',
                        session_id: 'test_html'
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    currentGraphData = data.graph_data;
                    
                    resultDiv.innerHTML = `
                        <p class="success">✅ API响应成功</p>
                        <p>响应ID: ${data.response_id || 'N/A'}</p>
                        <p>查询: ${data.query || 'N/A'}</p>
                        <p>实体: ${JSON.stringify(data.entities || [])}</p>
                        <p>图谱数据: ${data.graph_data ? '存在' : '不存在'}</p>
                    `;
                } else {
                    resultDiv.innerHTML = `<p class="error">❌ API响应失败: ${response.status}</p>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<p class="error">❌ API请求失败: ${error.message}</p>`;
            }
        }
        
        function validateGraphData() {
            const resultDiv = document.getElementById('validation-result');
            
            if (!currentGraphData) {
                resultDiv.innerHTML = '<p class="error">❌ 请先测试API获取图谱数据</p>';
                return;
            }
            
            let validation = [];
            
            // 检查graph_data存在
            validation.push(`graph_data存在: ${currentGraphData !== null ? '✅' : '❌'}`);
            
            // 检查nodes
            const nodes = currentGraphData.nodes;
            validation.push(`nodes是数组: ${Array.isArray(nodes) ? '✅' : '❌'}`);
            validation.push(`nodes长度>0: ${Array.isArray(nodes) && nodes.length > 0 ? '✅' : '❌'}`);
            
            // 检查edges
            const edges = currentGraphData.edges;
            validation.push(`edges是数组: ${Array.isArray(edges) ? '✅' : '❌'}`);
            
            // 检查其他字段
            validation.push(`center_node: ${currentGraphData.center_node || 'N/A'}`);
            validation.push(`layout_type: ${currentGraphData.layout_type || 'N/A'}`);
            
            resultDiv.innerHTML = `
                <div>
                    ${validation.map(v => `<p>${v}</p>`).join('')}
                    <h4>完整图谱数据:</h4>
                    <pre style="background: #f5f5f5; padding: 10px; overflow: auto; max-height: 200px;">
${JSON.stringify(currentGraphData, null, 2)}
                    </pre>
                </div>
            `;
        }
        
        function testDisplayConditions() {
            const resultDiv = document.getElementById('condition-result');
            
            if (!currentGraphData) {
                resultDiv.innerHTML = '<p class="error">❌ 请先测试API获取图谱数据</p>';
                return;
            }
            
            // 模拟前端显示条件
            const condition1 = currentGraphData !== null;
            const condition2 = Array.isArray(currentGraphData.nodes);
            const condition3 = currentGraphData.nodes && currentGraphData.nodes.length > 0;
            
            const shouldDisplay = condition1 && condition2 && condition3;
            
            resultDiv.innerHTML = `
                <div>
                    <h4>前端显示条件 (来自MessageItem.tsx):</h4>
                    <p>response.graph_data: ${condition1 ? '✅' : '❌'}</p>
                    <p>Array.isArray(response.graph_data.nodes): ${condition2 ? '✅' : '❌'}</p>
                    <p>response.graph_data.nodes.length > 0: ${condition3 ? '✅' : '❌'}</p>
                    <h4>最终判断:</h4>
                    <p style="font-size: 18px; font-weight: bold;" class="${shouldDisplay ? 'success' : 'error'}">
                        ${shouldDisplay ? '✅ 应该显示知识图谱面板' : '❌ 不会显示知识图谱面板'}
                    </p>
                    ${shouldDisplay ? `
                        <p>节点数量: ${currentGraphData.nodes.length}</p>
                        <p>边数量: ${currentGraphData.edges ? currentGraphData.edges.length : 0}</p>
                    ` : ''}
                </div>
            `;
            
            // 如果应该显示，更新图谱容器
            if (shouldDisplay) {
                const container = document.getElementById('graph-container');
                container.innerHTML = `
                    <div style="padding: 20px;">
                        <h3>✅ 图谱应该在这里显示</h3>
                        <p>节点数量: ${currentGraphData.nodes.length}</p>
                        <p>边数量: ${currentGraphData.edges.length}</p>
                        <p>中心节点: ${currentGraphData.center_node}</p>
                        <p style="color: #666;">实际的图谱组件会在React应用中渲染</p>
                    </div>
                `;
                container.style.background = '#d4edda';
                container.style.borderColor = '#28a745';
            }
        }
    </script>
</body>
</html>'''
    
    with open('graph_test.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ 测试页面已创建: graph_test.html")
    print("请在浏览器中打开此文件进行测试")

def check_frontend_console_errors():
    """检查前端可能的控制台错误"""
    print("\n" + "=" * 60)
    print("前端控制台错误检查指南")
    print("=" * 60)
    
    print("请按以下步骤检查前端错误:")
    print("1. 打开浏览器开发者工具 (F12)")
    print("2. 切换到 Console 标签")
    print("3. 清空控制台")
    print("4. 在前端发送一个查询")
    print("5. 观察是否有红色错误信息")
    
    print("\n常见错误类型:")
    print("- UnifiedGraphVisualization组件加载失败")
    print("- React组件渲染错误")
    print("- JavaScript语法错误")
    print("- 网络请求CORS错误")
    print("- 状态更新错误")
    
    print("\n如果发现错误，请:")
    print("1. 复制完整的错误信息")
    print("2. 检查错误发生的文件和行号")
    print("3. 确认相关组件是否正确导入")

def main():
    """主函数"""
    print("🔍 开始专门调试前端图谱显示问题...")
    
    # 测试API并保存响应
    api_success = test_api_and_save_response()
    
    # 创建测试页面
    create_minimal_test_html()
    
    # 提供检查指南
    check_frontend_console_errors()
    
    print("\n" + "=" * 60)
    print("🎯 调试步骤总结")
    print("=" * 60)
    
    if api_success:
        print("✅ 后端API正常，图谱数据格式正确")
        print("\n下一步调试:")
        print("1. 打开 graph_test.html 验证数据格式")
        print("2. 检查前端控制台是否有JavaScript错误")
        print("3. 确认React组件是否正确接收数据")
        print("4. 检查UnifiedGraphVisualization组件是否正常工作")
    else:
        print("❌ 后端API有问题，请先修复后端")
        print("1. 确保后端服务正在运行")
        print("2. 检查后端日志中的错误信息")
        print("3. 确认图谱生成逻辑是否正确")

if __name__ == "__main__":
    main()
