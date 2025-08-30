# AlgoKG部署指南

## 部署架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    负载均衡层 (Nginx)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   前端服务    │  │   前端服务    │  │   前端服务    │         │
│  │  (React)    │  │  (React)    │  │  (React)    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   后端服务    │  │   后端服务    │  │   后端服务    │         │
│  │  (FastAPI)  │  │  (FastAPI)  │  │  (FastAPI)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Neo4j     │  │    Redis     │  │  文件存储    │         │
│  │   集群       │  │   集群       │  │   (NFS)     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 1. 开发环境部署

### 1.1 前置要求

**系统要求**:
- OS: Ubuntu 20.04+ / macOS 10.15+ / Windows 10+
- RAM: 8GB+ (推荐16GB+)
- Storage: 50GB+ 可用空间
- Network: 稳定的互联网连接

**软件依赖**:
- Docker 20.10+
- Docker Compose 2.0+
- Node.js 18+
- Python 3.9+
- Git 2.30+

### 1.2 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/your-org/algokg-platform.git
cd algokg-platform

# 2. 环境配置
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量

# 3. 启动所有服务
docker-compose up -d

# 4. 等待服务启动完成
docker-compose logs -f

# 5. 访问应用
# 前端: http://localhost:3000
# 后端API: http://localhost:8000
# Neo4j浏览器: http://localhost:7474
# API文档: http://localhost:8000/docs
```

### 1.3 环境变量配置

创建 `.env` 文件:
```bash
# 应用配置
APP_NAME=AlgoKG智能问答系统
VERSION=1.0.0
DEBUG=true
LOG_LEVEL=INFO

# 数据库配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
REDIS_URL=redis://localhost:6379

# API配置
QWEN_API_KEY=your_qwen_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key

# 安全配置
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# 文件路径
MODELS_PATH=./models
DATA_PATH=./data
```

### 1.4 数据初始化

```bash
# 1. 初始化Neo4j数据库
docker-compose exec backend python scripts/init_neo4j.py

# 2. 加载知识图谱数据
docker-compose exec backend python backend/neo4j_loader/extractor2_modified.py

# 3. 训练GNN模型 (可选，已有预训练模型)
docker-compose exec backend python gnn_model/train_multitask_gat2v.py

# 4. 验证数据加载
docker-compose exec backend python scripts/verify_data.py
```

## 2. 生产环境部署

### 2.1 Kubernetes部署

#### 2.1.1 命名空间创建
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: algokg
```

#### 2.1.2 配置管理
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: algokg-config
  namespace: algokg
data:
  APP_NAME: "AlgoKG智能问答系统"
  LOG_LEVEL: "INFO"
  NEO4J_URI: "bolt://neo4j-service:7687"
  REDIS_URL: "redis://redis-service:6379"
```

#### 2.1.3 密钥管理
```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: algokg-secrets
  namespace: algokg
type: Opaque
data:
  NEO4J_PASSWORD: <base64-encoded-password>
  QWEN_API_KEY: <base64-encoded-api-key>
  SECRET_KEY: <base64-encoded-secret>
```

#### 2.1.4 前端部署
```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: algokg
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: algokg/frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: REACT_APP_API_URL
          value: "https://api.algokg.com"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: algokg
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 3000
  type: ClusterIP
```

#### 2.1.5 后端部署
```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: algokg
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: algokg/backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: algokg-config
        - secretRef:
            name: algokg-secrets
        volumeMounts:
        - name: models-volume
          mountPath: /app/models
        - name: data-volume
          mountPath: /app/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: models-volume
        persistentVolumeClaim:
          claimName: models-pvc
      - name: data-volume
        persistentVolumeClaim:
          claimName: data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: algokg
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

#### 2.1.6 数据库部署
```yaml
# neo4j-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: algokg
spec:
  serviceName: neo4j-service
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.0
        ports:
        - containerPort: 7474
        - containerPort: 7687
        env:
        - name: NEO4J_AUTH
          valueFrom:
            secretKeyRef:
              name: algokg-secrets
              key: NEO4J_AUTH
        volumeMounts:
        - name: neo4j-data
          mountPath: /data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
  volumeClaimTemplates:
  - metadata:
      name: neo4j-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j-service
  namespace: algokg
spec:
  selector:
    app: neo4j
  ports:
  - name: http
    port: 7474
    targetPort: 7474
  - name: bolt
    port: 7687
    targetPort: 7687
  type: ClusterIP
```

### 2.2 Nginx配置

```nginx
# nginx.conf
upstream frontend {
    server frontend-service:80;
}

upstream backend {
    server backend-service:8000;
}

server {
    listen 80;
    server_name algokg.com www.algokg.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name algokg.com www.algokg.com;

    ssl_certificate /etc/ssl/certs/algokg.crt;
    ssl_certificate_key /etc/ssl/private/algokg.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # 前端静态文件
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API接口
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 健康检查
    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        proxy_pass http://frontend;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

### 2.3 监控和日志

#### 2.3.1 Prometheus配置
```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'algokg-backend'
    static_configs:
      - targets: ['backend-service:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j-service:2004']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-service:9121']
    scrape_interval: 30s
```

#### 2.3.2 Grafana仪表板
```json
{
  "dashboard": {
    "title": "AlgoKG监控仪表板",
    "panels": [
      {
        "title": "API请求率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "响应时间",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Neo4j连接数",
        "type": "singlestat",
        "targets": [
          {
            "expr": "neo4j_database_pool_total_used",
            "legendFormat": "Used connections"
          }
        ]
      }
    ]
  }
}
```

## 3. 部署脚本

### 3.1 自动化部署脚本
```bash
#!/bin/bash
# deploy.sh

set -e

# 配置变量
NAMESPACE="algokg"
IMAGE_TAG=${1:-latest}
ENVIRONMENT=${2:-production}

echo "开始部署 AlgoKG 到 $ENVIRONMENT 环境..."

# 1. 创建命名空间
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# 2. 应用配置
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# 3. 部署数据库
kubectl apply -f k8s/neo4j-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml

# 4. 等待数据库就绪
kubectl wait --for=condition=ready pod -l app=neo4j -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s

# 5. 部署应用
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# 6. 等待应用就绪
kubectl wait --for=condition=ready pod -l app=backend -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app=frontend -n $NAMESPACE --timeout=300s

# 7. 配置Ingress
kubectl apply -f k8s/ingress.yaml

# 8. 验证部署
kubectl get pods -n $NAMESPACE
kubectl get services -n $NAMESPACE

echo "部署完成！"
echo "前端地址: https://algokg.com"
echo "API地址: https://algokg.com/api"
echo "健康检查: https://algokg.com/health"
```

### 3.2 数据备份脚本
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# 备份Neo4j数据
kubectl exec -n algokg neo4j-0 -- neo4j-admin dump --database=neo4j --to=/tmp/neo4j-backup.dump
kubectl cp algokg/neo4j-0:/tmp/neo4j-backup.dump $BACKUP_DIR/neo4j-backup.dump

# 备份Redis数据
kubectl exec -n algokg redis-0 -- redis-cli BGSAVE
kubectl cp algokg/redis-0:/data/dump.rdb $BACKUP_DIR/redis-backup.rdb

# 备份模型文件
kubectl cp algokg/backend-0:/app/models $BACKUP_DIR/models

echo "备份完成: $BACKUP_DIR"
```

### 3.3 健康检查脚本
```bash
#!/bin/bash
# health_check.sh

NAMESPACE="algokg"
FAILED=0

# 检查Pod状态
echo "检查Pod状态..."
kubectl get pods -n $NAMESPACE

# 检查服务健康
echo "检查服务健康..."
BACKEND_HEALTH=$(kubectl exec -n $NAMESPACE deployment/backend -- curl -s http://localhost:8000/health | jq -r '.status')
if [ "$BACKEND_HEALTH" != "healthy" ]; then
    echo "❌ 后端服务不健康"
    FAILED=1
else
    echo "✅ 后端服务健康"
fi

# 检查数据库连接
NEO4J_STATUS=$(kubectl exec -n $NAMESPACE neo4j-0 -- cypher-shell "RETURN 1" 2>/dev/null && echo "ok" || echo "failed")
if [ "$NEO4J_STATUS" != "ok" ]; then
    echo "❌ Neo4j连接失败"
    FAILED=1
else
    echo "✅ Neo4j连接正常"
fi

REDIS_STATUS=$(kubectl exec -n $NAMESPACE redis-0 -- redis-cli ping 2>/dev/null || echo "failed")
if [ "$REDIS_STATUS" != "PONG" ]; then
    echo "❌ Redis连接失败"
    FAILED=1
else
    echo "✅ Redis连接正常"
fi

if [ $FAILED -eq 1 ]; then
    echo "❌ 健康检查失败"
    exit 1
else
    echo "✅ 所有服务健康"
    exit 0
fi
```

## 4. 故障排除

### 4.1 常见问题

**问题1: Neo4j连接失败**
```bash
# 检查Neo4j状态
kubectl logs -n algokg neo4j-0

# 检查网络连接
kubectl exec -n algokg backend-0 -- nc -zv neo4j-service 7687

# 重启Neo4j
kubectl rollout restart statefulset/neo4j -n algokg
```

**问题2: 内存不足**
```bash
# 检查资源使用
kubectl top pods -n algokg

# 调整资源限制
kubectl patch deployment backend -n algokg -p '{"spec":{"template":{"spec":{"containers":[{"name":"backend","resources":{"limits":{"memory":"4Gi"}}}]}}}}'
```

**问题3: 模型加载失败**
```bash
# 检查模型文件
kubectl exec -n algokg backend-0 -- ls -la /app/models/

# 重新下载模型
kubectl exec -n algokg backend-0 -- python scripts/download_models.py
```

### 4.2 日志查看
```bash
# 查看所有Pod日志
kubectl logs -n algokg -l app=backend --tail=100

# 实时查看日志
kubectl logs -n algokg -f deployment/backend

# 查看特定时间段日志
kubectl logs -n algokg backend-0 --since=1h
```

### 4.3 性能调优
```bash
# 调整副本数
kubectl scale deployment backend --replicas=5 -n algokg

# 配置HPA
kubectl autoscale deployment backend --cpu-percent=70 --min=3 --max=10 -n algokg

# 查看HPA状态
kubectl get hpa -n algokg
```

这个部署指南提供了从开发环境到生产环境的完整部署方案，包括容器化、Kubernetes编排、监控配置和故障排除等内容。
