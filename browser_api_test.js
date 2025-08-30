// 在浏览器控制台中运行这个脚本来测试API
// 复制粘贴到浏览器控制台中执行

async function testNodeDetailAPI() {
    console.log('🔍 测试节点详情API...');
    
    const testNodeId = 'neo4j_两两交换链表中的节点';
    const nodeType = 'Problem';
    const url = `/api/v1/graph/unified/node/${encodeURIComponent(testNodeId)}/details?node_type=${nodeType}`;
    
    console.log('请求URL:', url);
    
    try {
        const response = await fetch(url);
        console.log('响应状态:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ API响应成功');
            console.log('完整响应数据:', data);
            console.log('数据类型:', typeof data);
            console.log('顶级字段:', Object.keys(data));
            
            // 检查basic_info
            console.log('basic_info存在:', 'basic_info' in data);
            console.log('basic_info值:', data.basic_info);
            console.log('basic_info类型:', typeof data.basic_info);
            
            if (data.basic_info) {
                console.log('basic_info字段:', Object.keys(data.basic_info));
                console.log('title:', data.basic_info.title);
                console.log('type:', data.basic_info.type);
            }
            
            return data;
        } else {
            console.error('❌ API请求失败:', response.status);
            const errorText = await response.text();
            console.error('错误信息:', errorText);
            return null;
        }
    } catch (error) {
        console.error('❌ 请求异常:', error);
        return null;
    }
}

// 执行测试
testNodeDetailAPI().then(data => {
    if (data) {
        console.log('🎯 测试完成，数据结构正常');
        
        // 模拟前端组件的数据访问
        console.log('模拟前端访问:');
        try {
            const title = data.basic_info?.title || '未知';
            const type = data.basic_info?.type || '未知';
            console.log('✅ 安全访问成功:', { title, type });
        } catch (err) {
            console.error('❌ 前端访问失败:', err);
        }
    } else {
        console.log('❌ 测试失败');
    }
});

console.log('📋 使用说明:');
console.log('1. 确保后端服务正在运行');
console.log('2. 在前端页面的控制台中运行此脚本');
console.log('3. 查看API响应的数据结构');
console.log('4. 确认basic_info字段是否存在');
