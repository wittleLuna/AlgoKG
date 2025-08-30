#!/bin/bash

# AlgoKG Web应用开发环境启动脚本

set -e

echo "🚀 启动AlgoKG智能问答Web应用开发环境..."

# 检查必要的工具
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ 错误: $1 未安装"
        exit 1
    fi
}

echo "📋 检查依赖..."
check_command docker
check_command docker-compose
check_command node
check_command python3

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置必要的环境变量"
fi

# 启动基础服务（Neo4j, Redis）
echo "🗄️  启动数据库服务..."
docker-compose up -d neo4j redis

# 等待服务启动
echo "⏳ 等待数据库服务启动..."
sleep 10

# 检查Neo4j连接
echo "🔍 检查Neo4j连接..."
until docker-compose exec neo4j cypher-shell -u neo4j -p 123456 "RETURN 1" &> /dev/null; do
    echo "等待Neo4j启动..."
    sleep 5
done
echo "✅ Neo4j已就绪"

# 检查Redis连接
echo "🔍 检查Redis连接..."
until docker-compose exec redis redis-cli ping &> /dev/null; do
    echo "等待Redis启动..."
    sleep 2
done
echo "✅ Redis已就绪"

# 启动后端服务
echo "🔧 启动后端服务..."
cd backend
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

echo "🚀 启动FastAPI服务器..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ..

# 启动前端服务
echo "🎨 启动前端服务..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

echo "🚀 启动React开发服务器..."
npm start &
FRONTEND_PID=$!

cd ..

# 创建停止脚本
cat > stop-dev.sh << EOF
#!/bin/bash
echo "🛑 停止开发服务..."
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
docker-compose stop
echo "✅ 开发环境已停止"
EOF

chmod +x stop-dev.sh

echo ""
echo "🎉 AlgoKG Web应用开发环境启动完成！"
echo ""
echo "📱 前端地址: http://localhost:3000"
echo "🔧 后端API: http://localhost:8000"
echo "📊 API文档: http://localhost:8000/docs"
echo "🗄️  Neo4j浏览器: http://localhost:7474"
echo ""
echo "💡 使用 ./stop-dev.sh 停止所有服务"
echo ""

# 等待用户中断
trap 'echo ""; echo "🛑 正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; docker-compose stop; exit 0' INT

echo "按 Ctrl+C 停止所有服务..."
wait
