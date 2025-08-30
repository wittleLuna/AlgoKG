# AlgoKG 智能问答Web应用

基于现有的多智能体问答系统构建的现代化Web应用，提供高级感的用户界面和强交互性体验。

## 系统架构

```
web_app/
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI应用入口
│   │   ├── api/            # API路由
│   │   │   ├── __init__.py
│   │   │   ├── qa.py       # 问答API
│   │   │   └── graph.py    # 图谱API
│   │   ├── models/         # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── request.py  # 请求模型
│   │   │   └── response.py # 响应模型
│   │   ├── services/       # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── qa_service.py
│   │   │   └── graph_service.py
│   │   └── core/           # 核心配置
│   │       ├── __init__.py
│   │       ├── config.py
│   │       └── deps.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React前端
│   ├── public/
│   ├── src/
│   │   ├── components/     # 组件
│   │   │   ├── common/     # 通用组件
│   │   │   ├── qa/         # 问答相关组件
│   │   │   └── graph/      # 图谱可视化组件
│   │   ├── pages/          # 页面
│   │   ├── services/       # API服务
│   │   ├── hooks/          # 自定义Hooks
│   │   ├── utils/          # 工具函数
│   │   └── styles/         # 样式文件
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml      # 容器编排
```

## 技术栈

### 后端
- **FastAPI**: 高性能异步Web框架
- **Pydantic**: 数据验证和序列化
- **WebSocket**: 实时通信支持
- **Neo4j**: 图数据库
- **Redis**: 缓存和会话管理

### 前端
- **React 18**: 现代化前端框架
- **TypeScript**: 类型安全
- **Ant Design**: 企业级UI组件库
- **React Query**: 数据获取和缓存
- **D3.js/Vis.js**: 图谱可视化
- **Socket.io**: 实时通信

## 核心功能

### 1. 智能问答
- 实时推理路径展示
- 多轮对话支持
- 上下文理解

### 2. 交互式内容
- 可点击的概念和题目链接
- 动态内容加载
- 智能推荐

### 3. 图谱可视化
- 动态知识图谱展示
- 交互式节点探索
- 路径高亮显示

### 4. 用户体验
- 响应式设计
- 暗黑/明亮主题切换
- 加载动画和过渡效果
- 键盘快捷键支持

## 快速开始

### 方式一：使用启动脚本（推荐）

**Linux/macOS:**
```bash
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh
```

**Windows:**
```cmd
scripts\start-dev.bat
```

### 方式二：使用Makefile
```bash
# 安装依赖
make install

# 启动开发环境
make dev

# 运行测试
make test

# 查看所有可用命令
make help
```

### 方式三：使用Docker
```bash
# 启动所有服务
docker-compose up -d

# 或使用Makefile
make docker-run
```

## 开发环境配置

### 环境要求
- Python 3.8+
- Node.js 16+
- Docker & Docker Compose
- Neo4j 5.x
- Redis 7.x

### 环境变量配置
1. 复制环境变量模板：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，配置必要的环境变量：
   - Neo4j数据库连接信息
   - Redis连接信息
   - API密钥（如Qwen API Key）
   - 模型和数据文件路径

### 手动启动各服务

**启动数据库服务:**
```bash
docker-compose up -d neo4j redis
```

**启动后端服务:**
```bash
cd backend  # cd F:\algokg_platform\web_app\backend
python -m venv venv # .\venv\Scripts\Activate.ps1
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**启动前端服务:**
```bash
cd frontend   # cd F:\algokg_platform\web_app\frontend
npm install
npm start
```

## 系统测试

运行自动化测试脚本：
```bash
python scripts/test-system.py
```

或使用Makefile：
```bash
make test
```

## 访问地址

启动成功后，可以通过以下地址访问：

- 🌐 **前端应用**: http://localhost:3000
- 🔧 **后端API**: http://localhost:8000
- 📚 **API文档**: http://localhost:8000/docs
- 🗄️ **Neo4j浏览器**: http://localhost:7474 (用户名: neo4j, 密码: 123456)
- 📊 **Redis**: localhost:6379

## 项目结构详解

```
web_app/
├── backend/                    # FastAPI后端
│   ├── app/
│   │   ├── main.py            # 应用入口
│   │   ├── api/               # API路由
│   │   │   ├── qa.py          # 问答API
│   │   │   └── graph.py       # 图谱API
│   │   ├── models/            # 数据模型
│   │   ├── services/          # 业务逻辑
│   │   └── core/              # 核心配置
│   ├── requirements.txt       # Python依赖
│   └── Dockerfile            # 后端Docker配置
├── frontend/                  # React前端
│   ├── src/
│   │   ├── components/        # React组件
│   │   │   ├── common/        # 通用组件
│   │   │   ├── qa/            # 问答组件
│   │   │   └── graph/         # 图谱组件
│   │   ├── services/          # API服务
│   │   ├── store/             # 状态管理
│   │   └── types/             # TypeScript类型
│   ├── package.json           # 前端依赖
│   └── Dockerfile            # 前端Docker配置
├── scripts/                   # 脚本文件
│   ├── start-dev.sh          # Linux/macOS启动脚本
│   ├── start-dev.bat         # Windows启动脚本
│   └── test-system.py        # 系统测试脚本
├── docker-compose.yml         # Docker编排配置
├── Makefile                  # 构建脚本
├── .env.example              # 环境变量模板
└── README.md                 # 项目文档
```

## 核心功能特性

### 🤖 智能问答系统
- **多智能体协作**: 分析器、知识检索器、概念解释器、相似题目查找器、整合器
- **实时推理路径**: 可视化AI思考过程，展示每个智能体的工作状态
- **上下文理解**: 支持多轮对话，理解用户意图
- **流式响应**: 实时返回推理过程，提升用户体验

### 🔗 交互式内容链接
- **智能识别**: 自动识别文本中的算法、数据结构、题目等可点击内容
- **概念跳转**: 点击概念直接触发新一轮问答
- **题目链接**: 点击题目名称查看详细信息和相关图谱
- **智能推荐**: 基于当前内容推荐相关概念和题目

### 🕸️ 动态知识图谱
- **多种布局**: 支持层次布局、力导向布局、环形布局
- **交互式探索**: 点击节点查看详情，拖拽调整位置
- **实时分析**: 计算图谱指标，识别重要节点
- **动画效果**: 支持节点动画，增强视觉体验
- **过滤功能**: 按节点类型、关系类型过滤显示

### 📊 图谱分析面板
- **统计指标**: 节点数量、边数量、度分布等
- **中心性分析**: 识别图中最重要的节点
- **聚类分析**: 发现知识点之间的聚类关系
- **路径分析**: 查找节点间的最短路径

### 🎨 现代化UI设计
- **响应式设计**: 适配桌面和移动设备
- **暗黑/明亮主题**: 支持主题切换
- **流畅动画**: 丰富的过渡效果和加载动画
- **无障碍支持**: 符合WCAG标准的无障碍设计

## API文档

启动后端服务后，访问以下地址查看详细的API文档：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要API端点

#### 问答相关
- `POST /api/v1/qa/query` - 问答查询
- `POST /api/v1/qa/query/stream` - 流式问答查询
- `POST /api/v1/qa/similar-problems` - 获取相似题目
- `POST /api/v1/qa/concept/click` - 处理概念点击

#### 图谱相关
- `POST /api/v1/graph/query` - 查询知识图谱
- `GET /api/v1/graph/problem/{title}/graph` - 获取题目图谱
- `GET /api/v1/graph/concept/{name}/graph` - 获取概念图谱
- `GET /api/v1/graph/statistics` - 获取图谱统计信息

## 部署指南

### 开发环境部署
使用上述快速开始方式即可。

### 生产环境部署

1. **构建生产版本**:
   ```bash
   make build
   ```

2. **使用Docker部署**:
   ```bash
   # 构建镜像
   make docker-build

   # 启动服务
   make docker-run
   ```

3. **使用Nginx反向代理**:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:3000;
       }

       location /api/ {
           proxy_pass http://localhost:8000;
       }
   }
   ```

### 性能优化建议

1. **数据库优化**:
   - 为Neo4j创建适当的索引
   - 配置Redis缓存策略
   - 定期清理过期数据

2. **应用优化**:
   - 启用Gzip压缩
   - 配置CDN加速静态资源
   - 使用负载均衡器

3. **监控和日志**:
   - 配置应用监控（如Prometheus + Grafana）
   - 设置日志收集和分析
   - 配置告警机制

## 故障排除

### 常见问题

1. **端口冲突**:
   - 检查8000、3000、7474、7687、6379端口是否被占用
   - 修改docker-compose.yml中的端口映射

2. **数据库连接失败**:
   - 确认Neo4j和Redis服务正常启动
   - 检查.env文件中的连接配置
   - 查看docker-compose logs

3. **前端无法访问后端**:
   - 检查CORS配置
   - 确认API_URL环境变量正确
   - 查看浏览器网络面板

4. **模型文件缺失**:
   - 确认模型文件路径配置正确
   - 检查文件是否存在且有读取权限

### 日志查看
```bash
# 查看所有服务日志
make logs

# 查看特定服务日志
docker-compose logs backend
docker-compose logs frontend
docker-compose logs neo4j
```

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 创建Issue
- 发送邮件
- 加入讨论群

---

**AlgoKG智能问答系统** - 让算法学习更智能、更高效！
