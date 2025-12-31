# 前端项目设置指南

## 环境要求

- Node.js: `^20.19.0 || >=22.12.0`
- npm 或 pnpm

## 安装步骤

### 1. 安装依赖

```bash
cd frontend
npm install
```

或使用 pnpm：

```bash
pnpm install
```

### 2. 配置环境变量

创建 `.env.development` 文件（开发环境）：

```env
VITE_API_BASE_URL=http://localhost:5000
```

创建 `.env.production` 文件（生产环境）：

```env
VITE_API_BASE_URL=https://your-production-api.com
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

### 4. 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录

### 5. 预览生产构建

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── assets/          # 静态资源
│   ├── components/      # 通用组件
│   │   ├── Chart.vue    # ECharts 图表封装
│   │   ├── Table.vue    # 数据表格组件
│   │   ├── Header.vue   # 顶部导航栏
│   │   ├── Sidebar.vue  # 侧边栏菜单
│   │   ├── NotificationBell.vue  # 通知铃铛
│   │   └── Form.vue     # 表单组件
│   ├── composables/     # Vue 组合式函数
│   │   ├── useAuth.ts   # 认证相关
│   │   ├── useFetch.ts  # 数据请求
│   │   └── usePagination.ts  # 分页逻辑
│   ├── config/          # 配置文件
│   │   ├── constants.ts # 常量定义
│   │   └── env.ts       # 环境变量
│   ├── layouts/         # 布局组件
│   │   ├── AdminLayout.vue  # 管理后台布局
│   │   └── AuthLayout.vue   # 认证页面布局
│   ├── router/          # 路由配置
│   │   └── index.ts
│   ├── services/        # API 服务
│   │   ├── http.ts      # HTTP 客户端
│   │   └── api/         # API 封装
│   │       ├── user.ts
│   │       ├── meter.ts
│   │       ├── bill.ts
│   │       ├── usage.ts
│   │       ├── query.ts
│   │       ├── system.ts
│   │       └── notification.ts
│   ├── stores/          # Pinia 状态管理
│   │   └── index.ts     # useAuthStore, useAppStore
│   ├── styles/          # 全局样式
│   │   ├── globals.css
│   │   ├── variables.css
│   │   └── components.css
│   ├── types/           # TypeScript 类型定义
│   │   └── index.ts
│   ├── utils/           # 工具函数
│   │   ├── date.ts
│   │   ├── format.ts
│   │   ├── validators.ts
│   │   └── errorCodes.ts
│   ├── views/           # 页面组件
│   │   ├── Login.vue
│   │   ├── Dashboard.vue
│   │   ├── UsageAnalysis.vue
│   │   ├── RegionAnalysis.vue
│   │   ├── Bills.vue
│   │   └── Settings.vue
│   ├── App.vue
│   └── main.ts
└── package.json
```

## 主要功能模块

### 1. 认证模块
- **登录**: 邮箱/密码登录
- **注册**: 新用户注册
- **Token 刷新**: 自动刷新 access_token
- **权限控制**: 基于角色的路由守卫

### 2. 仪表盘
- 用电统计卡片（本月用电量、电费、累计用电量、待支付账单）
- 用电趋势图（按周/月/年）
- 最近账单列表

### 3. 用电分析
- 时间范围筛选
- 多种分析维度（用电趋势、峰谷分时、同比环比）
- 可视化图表
- 数据导出功能

### 4. 账单管理
- 账单列表查询
- 多条件筛选（账期、状态、金额范围）
- 在线支付
- 批量支付
- 账单详情查看

### 5. 个人设置
- 个人信息编辑
- 密码修改
- 电表绑定/解绑
- 通知设置

## 技术栈

- **框架**: Vue 3 (Composition API)
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **UI 组件库**: Element Plus
- **图表库**: ECharts 5
- **HTTP 客户端**: Axios
- **构建工具**: Vite
- **语言**: TypeScript
- **代码规范**: ESLint + Prettier

## API 对接

所有 API 调用都通过 `services/api/` 中的封装模块进行：

```typescript
// 示例：调用用户登录 API
import { userApi } from '@/services/api/user'

const response = await userApi.login({
  mail: 'user@example.com',
  password: 'password123'
})
```

HTTP 拦截器自动处理：
- Token 注入（请求头）
- Token 过期自动刷新
- 统一错误处理
- 请求/响应日志

## 开发建议

1. **组件命名**: 使用 PascalCase
2. **文件命名**: 使用 kebab-case（除 Vue 组件）
3. **样式作用域**: 使用 `<style scoped>`
4. **类型安全**: 充分利用 TypeScript 类型检查
5. **代码复用**: 抽取通用逻辑到 composables
6. **状态管理**: 全局状态使用 Pinia store

## 常见问题

### 1. 依赖安装失败
```bash
# 清除缓存后重新安装
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### 2. 端口冲突
修改 `vite.config.ts`:
```typescript
export default defineConfig({
  server: {
    port: 3000 // 修改为其他端口
  }
})
```

### 3. API 请求 CORS 错误
确保后端配置了正确的 CORS：
```python
# Flask 后端
from flask_cors import CORS
CORS(app, origins=['http://localhost:5173'])
```

### 4. Element Plus 样式不生效
确保在 `main.ts` 中导入了样式：
```typescript
import 'element-plus/dist/index.css'
```

## 测试

```bash
# 单元测试
npm run test:unit

# E2E 测试
npm run test:e2e
```

## 部署

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/electricity-query/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend-server:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request
