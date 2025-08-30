# 🔧 重复弹窗问题修复

## 🎯 问题描述

点击内嵌知识图谱的节点时，会出现两个弹窗：

### 第一个弹窗（正常）
- **来源**: InlineKnowledgeGraph组件的节点详情抽屉
- **内容**: 完整的节点详情信息
  - 基本信息（名称、类型、难度、平台、描述）
  - 相关算法、数据结构
  - 复杂度分析
  - 相关题目
- **样式**: 480px宽度的右侧抽屉

### 第二个弹窗（需要禁用）
- **来源**: UnifiedGraphVisualization组件的内置节点详情
- **内容**: 简单的节点信息
  ```
  用最少数量的箭引爆气球
  Problem
  属性信息
  from_qa_context: true
  is_recommended: false
  连接信息
  该节点与 1 个节点相连
  ```
- **样式**: 简单的弹窗

## 🔧 修复方案

### 1. 完善disableBuiltinNodeDetail逻辑

虽然我们已经设置了`disableBuiltinNodeDetail={true}`，但UnifiedGraphVisualization组件仍然会显示内置的节点详情Drawer。

### 2. 修改UnifiedGraphVisualization组件

#### 禁用内置节点详情渲染
```typescript
{/* 节点详情抽屉 - 只在未禁用时显示 */}
{!disableBuiltinNodeDetail && renderNodeDetails()}
```

#### 确保状态不被设置
```typescript
if (!disableBuiltinNodeDetail) {
  // 获取并显示节点详情
  try {
    const response = await fetch(`/api/v1/graph/unified/node/${encodeURIComponent(nodeData.id)}/details?node_type=${nodeData.type}`);
    if (response.ok) {
      const details = await response.json();
      setNodeDetails({ ...nodeData, details });
      setShowNodeDetails(true);
    }
  } catch (error) {
    console.error('获取节点详情失败:', error);
  }
} else {
  // 禁用时确保不显示内置节点详情
  setShowNodeDetails(false);
  setNodeDetails(null);
}
```

## 🎯 修复效果

### 修复前
```
用户点击节点
    ↓
第一个弹窗：InlineKnowledgeGraph的详细抽屉
    ↓
用户关闭第一个弹窗
    ↓
第二个弹窗：UnifiedGraphVisualization的简单弹窗 ❌
```

### 修复后
```
用户点击节点
    ↓
第一个弹窗：InlineKnowledgeGraph的详细抽屉
    ↓
用户关闭弹窗
    ↓
完成，没有第二个弹窗 ✅
```

## 📋 技术细节

### InlineKnowledgeGraph配置
```typescript
<UnifiedGraphVisualization
  data={graphData}
  height="100%"
  showControls={true}
  onNodeClick={handleNodeClick}
  defaultDataSources={['neo4j', 'embedding']}
  showAnimation={showAnimation}
  disableBuiltinNodeDetail={true}  // 关键配置
/>
```

### 事件处理流程
1. **用户点击节点** → 触发UnifiedGraphVisualization的handleNodeClick
2. **调用外部回调** → 调用InlineKnowledgeGraph的handleNodeClick
3. **InlineKnowledgeGraph处理** → 获取详情并显示抽屉
4. **UnifiedGraphVisualization跳过** → 因为disableBuiltinNodeDetail=true

### 状态管理
- **InlineKnowledgeGraph**: 管理自己的节点详情状态
  - `selectedNode`: 当前选中的节点
  - `nodeDetailVisible`: 抽屉是否可见
  - `nodeDetailInfo`: 节点详情数据
- **UnifiedGraphVisualization**: 在禁用模式下不管理节点详情状态
  - `showNodeDetails`: 强制设为false
  - `nodeDetails`: 强制设为null

## 🚀 测试验证

### 测试步骤
1. 在前端发送概念查询
2. 展开内嵌知识图谱
3. 点击任意节点
4. 查看是否只出现一个详细的节点信息抽屉
5. 关闭抽屉
6. 确认没有第二个简单弹窗出现

### 预期结果
- ✅ 只显示一个节点详情抽屉
- ✅ 抽屉包含完整的节点信息
- ✅ 关闭抽屉后没有其他弹窗
- ✅ 用户体验流畅

## 🎉 总结

这个修复解决了重复弹窗的问题：

### 修复内容
1. **条件渲染**: 只在未禁用时渲染内置节点详情
2. **状态清理**: 禁用时主动清理相关状态
3. **事件隔离**: 确保只有InlineKnowledgeGraph处理节点详情

### 用户体验改进
- **单一弹窗**: 避免用户困惑
- **完整信息**: 保留详细的节点信息
- **流畅交互**: 点击-查看-关闭的流程更自然

### 技术优势
- **清晰职责**: InlineKnowledgeGraph专门负责节点详情
- **配置灵活**: 通过props控制是否启用内置详情
- **向后兼容**: 不影响独立图谱页面的功能

**状态**: 🎯 **已修复完成，等待测试验证**
