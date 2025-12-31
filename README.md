# 电力查询系统

一个基于 Vue 3 + Flask 的电力数据查询与管理系统，支持用户注册登录、电表绑定、用电数据查询、数据分析等功能。

## 📋 项目简介

本系统旨在为电力用户和管理人员提供便捷的用电数据查询和管理服务，主要功能包括：

- 👤 用户管理：注册、登录、个人信息管理
- 📊 用电查询：实时用电数据查询、历史数据分析
- 🔌 电表管理：电表绑定、解绑、状态监控
- 📈 数据分析：用电趋势分析、统计报表
- 🔐 权限管理：基于角色的访问控制
- 🌓 主题切换：浅色/深色模式支持

## 🛠️ 技术栈

### 前端
- Vue 3 + TypeScript
- Vite
- Vue Router 4
- Pinia
- Axios
- Element Plus

### 后端
- Flask
- MySQL
- SQLAlchemy
- JWT
- Flask-CORS

## ⚡ 快速开始

### 环境要求
- Node.js >= 16
- Python >= 3.8
- MySQL >= 5.7

### 安装步骤

**1. 克隆项目**
```bash
git clone <repository-url>
cd electricity_query
```

**2. 配置数据库**
```bash
# 启动 MySQL 服务
# Windows: 服务管理器中启动 MySQL
# Linux: sudo systemctl start mysql
# Mac: brew services start mysql

# 创建数据库
mysql -u root -p
CREATE DATABASE electricity_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;
```

**3. 启动后端**
```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 创建 .env 文件
echo DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/electricity_db > .env
echo JWT_SECRET_KEY=dev-secret-key-change-in-production >> .env

# 初始化数据库（首次运行）
flask db init
flask db migrate
flask db upgrade

# 启动服务
python run.py
```

**4. 启动前端**
```bash
# 新开一个终端
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

**5. 访问应用**
- 前端页面：http://localhost:5173
- 后端 API：http://localhost:5000

## 📁 项目结构

```
electricity_query/
├── frontend/              # 前端项目
│   ├── src/
│   │   ├── components/   # 公共组件
│   │   ├── views/        # 页面组件
│   │   ├── router/       # 路由配置
│   │   ├── stores/       # 状态管理
│   │   └── services/     # API 服务
│   ├── package.json
│   └── vite.config.ts
│
└── backend/              # 后端项目
    ├── app/
    │   ├── models/       # 数据模型
    │   ├── routes/       # 路由接口
    │   ├── services/     # 业务逻辑
    │   └── utils/        # 工具函数
    ├── requirements.txt
    └── run.py
```

## 🔧 配置说明

### 后端配置
在 `backend/.env` 文件中配置：
```
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/electricity_db
JWT_SECRET_KEY=your-secret-key
```

### 前端配置
在 `frontend/src/services/http.ts` 中配置 API 地址：
```typescript
const API_BASE_URL = 'http://localhost:5000/api/v1'
```

## 📄 API 文档

主要接口：

- `POST /api/v1/user/register` - 用户注册
- `POST /api/v1/user/login` - 用户登录
- `GET /api/v1/user/info` - 获取用户信息
- `POST /api/v1/user/bind-meter` - 绑定电表
- `GET /api/v1/user/meters` - 获取电表列表

## 📜 许可证

MIT License

---

**提示**：这是开发环境配置，生产环境部署请参考相关文档。
