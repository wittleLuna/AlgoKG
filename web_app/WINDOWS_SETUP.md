# Windows 环境快速启动指南

由于Windows批处理文件的编码问题，建议使用以下方法启动应用：

## 方法一：使用PowerShell脚本（推荐）

1. 以管理员身份打开PowerShell
2. 导航到项目目录：
   ```powershell
   cd F:\algokg_platform\web_app
   ```
3. 执行启动脚本：
   ```powershell
   .\scripts\start-dev.ps1
   ```

如果遇到执行策略问题，先运行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 方法二：使用简单批处理脚本

```cmd
cd F:\algokg_platform\web_app
.\scripts\start-simple.bat
```

## 方法三：手动启动（最可靠）

### 1. 准备环境文件
```cmd
cd F:\algokg_platform\web_app
copy .env.example .env
```

### 2. 启动数据库服务
```cmd
docker-compose up -d neo4j redis
```

### 3. 启动后端服务
打开新的命令行窗口：
```cmd
cd F:\algokg_platform\web_app\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 启动前端服务
再打开一个新的命令行窗口：
```cmd
cd F:\algokg_platform\web_app\frontend
npm install
npm start
```

## 访问地址

启动成功后，访问以下地址：
- 前端应用: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- Neo4j浏览器: http://localhost:7474 (用户名: neo4j, 密码: 123456)

## 常见问题

### 1. Docker未启动
确保Docker Desktop正在运行

### 2. 端口被占用
检查8000、3000、7474、7687、6379端口是否被其他程序占用

### 3. Python虚拟环境问题
如果遇到虚拟环境问题，删除venv文件夹重新创建：
```cmd
rmdir /s venv
python -m venv venv
```

### 4. Node.js依赖问题
如果npm install失败，尝试清理缓存：
```cmd
npm cache clean --force
rmdir /s node_modules
npm install
```

## 停止服务

1. 关闭前端和后端的命令行窗口
2. 停止Docker服务：
   ```cmd
   docker-compose stop
   ```
