# AlgoKG Web应用 Makefile

.PHONY: help install dev test build clean docker-build docker-run stop

# 默认目标
help:
	@echo "AlgoKG智能问答Web应用"
	@echo "======================"
	@echo ""
	@echo "可用命令:"
	@echo "  install     - 安装所有依赖"
	@echo "  dev         - 启动开发环境"
	@echo "  test        - 运行系统测试"
	@echo "  build       - 构建生产版本"
	@echo "  clean       - 清理临时文件"
	@echo "  docker-build - 构建Docker镜像"
	@echo "  docker-run  - 运行Docker容器"
	@echo "  stop        - 停止所有服务"
	@echo ""

# 安装依赖
install:
	@echo "📦 安装依赖..."
	@echo "安装后端依赖..."
	cd backend && python -m venv venv && \
	(. venv/bin/activate || venv\Scripts\activate.bat) && \
	pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install
	@echo "✅ 依赖安装完成"

# 启动开发环境
dev:
	@echo "🚀 启动开发环境..."
	@if [ -f scripts/start-dev.sh ]; then \
		chmod +x scripts/start-dev.sh && ./scripts/start-dev.sh; \
	elif [ -f scripts/start-dev.bat ]; then \
		scripts/start-dev.bat; \
	else \
		echo "❌ 启动脚本不存在"; \
	fi

# 运行测试
test:
	@echo "🧪 运行系统测试..."
	python scripts/test-system.py

# 构建生产版本
build:
	@echo "🏗️  构建生产版本..."
	@echo "构建前端..."
	cd frontend && npm run build
	@echo "✅ 构建完成"

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	rm -rf backend/venv
	rm -rf backend/__pycache__
	rm -rf backend/app/__pycache__
	rm -rf frontend/node_modules
	rm -rf frontend/build
	rm -f stop-dev.sh
	docker-compose down --volumes --remove-orphans
	@echo "✅ 清理完成"

# 构建Docker镜像
docker-build:
	@echo "🐳 构建Docker镜像..."
	docker-compose build
	@echo "✅ Docker镜像构建完成"

# 运行Docker容器
docker-run:
	@echo "🐳 启动Docker容器..."
	docker-compose up -d
	@echo "✅ Docker容器启动完成"
	@echo ""
	@echo "📱 前端地址: http://localhost:3000"
	@echo "🔧 后端API: http://localhost:8000"
	@echo "📊 API文档: http://localhost:8000/docs"
	@echo "🗄️  Neo4j浏览器: http://localhost:7474"

# 停止所有服务
stop:
	@echo "🛑 停止所有服务..."
	@if [ -f stop-dev.sh ]; then ./stop-dev.sh; fi
	docker-compose stop
	@echo "✅ 所有服务已停止"

# 查看日志
logs:
	@echo "📋 查看服务日志..."
	docker-compose logs -f

# 重启服务
restart: stop docker-run

# 健康检查
health:
	@echo "🏥 检查服务健康状态..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "后端服务不可用"
	@curl -s http://localhost:3000 > /dev/null && echo "✅ 前端服务正常" || echo "❌ 前端服务不可用"

# 数据库初始化
init-db:
	@echo "🗄️  初始化数据库..."
	docker-compose exec neo4j cypher-shell -u neo4j -p 123456 "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Problem) REQUIRE n.id IS UNIQUE;"
	docker-compose exec neo4j cypher-shell -u neo4j -p 123456 "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Algorithm) REQUIRE n.name IS UNIQUE;"
	@echo "✅ 数据库初始化完成"

# 备份数据
backup:
	@echo "💾 备份数据..."
	mkdir -p backups
	docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/tmp/neo4j-backup.dump
	docker cp $$(docker-compose ps -q neo4j):/tmp/neo4j-backup.dump backups/neo4j-backup-$$(date +%Y%m%d-%H%M%S).dump
	@echo "✅ 数据备份完成"

# 恢复数据
restore:
	@echo "📥 恢复数据..."
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "❌ 请指定备份文件: make restore BACKUP_FILE=path/to/backup.dump"; \
		exit 1; \
	fi
	docker-compose stop neo4j
	docker cp $(BACKUP_FILE) $$(docker-compose ps -q neo4j):/tmp/restore.dump
	docker-compose exec neo4j neo4j-admin load --from=/tmp/restore.dump --database=neo4j --force
	docker-compose start neo4j
	@echo "✅ 数据恢复完成"
