# AI论文辅助系统 - Vue3前端

基于Vue3 + Element Plus的学术论文辅助系统前端，完全复刻原Tkinter界面布局和功能。

## ✨ 特性

- 🎨 **忠实还原**：完全按照原Tkinter界面布局（三栏式：论文列表、树形结构、大纲面板）
- 🔐 **用户认证**：完整的登录/退出功能
- 📝 **论文管理**：上传PPT、编辑、保存、删除论文
- 🤖 **AI辅助**：智能内容生成和修改
- 📚 **知识库**：PDF上传、检索、管理（对应原test.py界面）
- 🎯 **Prompt模板**：自定义AI生成模板

## 🚀 快速开始

### 前置要求

- Node.js 20.19.0+
- 后端API服务已启动 (http://localhost:8000)

### 安装依赖

```bash
cd AIM-web
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问：http://localhost:5173

### 生产构建

```bash
npm run build
```

## 📁 项目结构

```
AIM-web/
├── src/
│   ├── api/
│   │   └── index.js          # API服务封装
│   ├── components/
│   │   └── EditNodeDialog.vue # 节点编辑对话框
│   ├── views/
│   │   ├── Login.vue         # 登录页面
│   │   ├── MainLayout.vue    # 主界面（三栏布局）
│   │   └── KnowledgeBase.vue # 知识库管理（对应test.py）
│   ├── App.vue               # 根组件
│   ├── main.js               # 入口文件
│   └── router.js             # 路由配置
├── public/
├── package.json
└── vite.config.js
```

## 🎯 界面对照

### 原Tkinter布局 → Vue3实现

```
┌─────────────────────────────────────────────┐
│ 学术论文助手            用户信息 [退出登录]  │  ← 顶部标题栏
├───────┬─────────────────────┬───────────────┤
│  A区  │        B区          │     C区       │
│       │                     │               │
│ 论文  │    树形结构显示     │   论文大纲    │
│ 列表  │   (可展开/编辑)     │   (可编辑)    │
│       │                     │               │
│ [删除]│                     │               │
│ [知识]│                     │               │
│ [上传]│                     │               │
│ [保存]│                     │               │
├───────┴─────────────────────┴───────────────┤
│ 状态栏: 就绪                                 │
└─────────────────────────────────────────────┘
```

## 🔑 功能清单

### 1. 登录页面
- [x] 用户名密码登录
- [x] JWT Token认证
- [x] 自动跳转

### 2. 主界面（MainLayout.vue）

#### A区 - 论文列表 (20%)
- [x] 显示用户所有论文
- [x] 点击选择论文
- [x] 高亮当前选中
- [x] 删除论文按钮
- [x] 提交知识按钮（跳转知识库）
- [x] 上传PPT按钮
- [x] 保存论文按钮

#### B区 - 树形结构 (60%)
- [x] 显示论文章节树
- [x] 可展开/折叠节点
- [x] 右键菜单（编辑/展开）
- [x] 节点内容标识

#### C区 - 大纲面板 (20%)
- [x] 显示论文大纲
- [x] 状态标记（✓/✗）
- [x] 右键菜单（编辑/删除/标记/插入）

### 3. 节点编辑对话框（EditNodeDialog.vue）

#### 左侧
- [x] 显示已有内容
- [x] 显示生成内容

#### 中间
- [x] 目录范围选择
- [x] 提取参考文字
- [x] 知识库检索
- [x] 显示检索结果

#### 右侧
- [x] Prompt模板编辑
- [x] 使用$$占位符

#### 功能按钮
- [x] 生成按钮（AI生成）
- [x] 修改按钮（AI修改）
- [x] 保存按钮
- [x] 取消按钮

### 4. 知识库管理（KnowledgeBase.vue）

对应原test.py的EnhancedKnowledgeBaseApp界面：

- [x] 上传PDF文件
- [x] 文件名验证
- [x] 上传进度显示
- [x] 知识库检索
- [x] 查看知识来源
- [x] 删除指定来源
- [x] 清空知识库
- [x] 标签页切换（检索结果/知识库内容）
- [x] 状态栏提示

## 🔗 API接口

所有API调用已封装在 `src/api/index.js`：

- **认证**: authAPI (login, getUserInfo)
- **论文**: paperAPI (getList, getDetail, uploadPPT, create, update, delete)
- **AI**: aiAPI (generate, modify)
- **知识库**: knowledgeAPI (search, uploadPDF, getSources, delete, clear)
- **Prompt**: promptAPI (get, save)

## 🎨 UI组件库

- **Element Plus**: 主要UI组件
- 可选使用Ant Design Vue

## ⚙️ 配置说明

### API地址配置

在 `src/api/index.js` 中修改：

```javascript
const api = axios.create({
  baseURL: 'http://localhost:8000/api', // 修改为实际后端地址
  timeout: 60000
})
```

## 🐛 常见问题

### 1. 跨域问题

如果遇到CORS错误，确保后端已配置：

```python
# app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Token过期

Token默认7天有效期，过期后会自动跳转登录页。

### 3. PPT上传失败

- 检查文件格式（仅支持.ppt和.pptx）
- 确保后端PPT解析服务正常

### 4. 知识库检索无结果

- 确保已上传PDF文件
- 检查向量数据库是否正常

## 📝 开发说明

### 添加新页面

1. 在 `src/views/` 创建新组件
2. 在 `router.js` 添加路由
3. 需要认证的页面添加 `meta: { requiresAuth: true }`

### 调用API

```javascript
import { paperAPI } from '@/api'

// 获取论文列表
const response = await paperAPI.getList()
if (response.success) {
  // 处理数据
}
```

### 全局状态

如需复杂状态管理，可集成Pinia：

```bash
npm install pinia
```

## 🎯 与原Tkinter的对应

| 原Tkinter功能 | Vue3实现 | 文件位置 |
|--------------|---------|----------|
| main_sxs1.py 主窗口 | MainLayout.vue | src/views/ |
| test.py 知识库窗口 | KnowledgeBase.vue | src/views/ |
| A区论文列表 | panel-a | MainLayout.vue |
| B区树形结构 | panel-b (el-tree) | MainLayout.vue |
| C区大纲面板 | panel-c | MainLayout.vue |
| 编辑对话框 | EditNodeDialog.vue | src/components/ |
| on_upload_knowledage() | openKnowledgeBase() | MainLayout.vue |

## 📦 依赖说明

```json
{
  "vue": "^3.5.22",           // Vue3核心
  "vue-router": "^4.5.1",     // 路由
  "element-plus": "^2.11.4",  // UI组件库
  "@element-plus/icons-vue": "^2.3.2", // 图标
  "axios": "^1.12.2"          // HTTP客户端
}
```

## 🚀 部署

### 生产构建

```bash
npm run build
```

生成的文件在 `dist/` 目录。

### 部署到服务器

将 `dist/` 目录内容部署到Web服务器（Nginx/Apache等）。

### 环境变量

可创建 `.env.production` 配置生产环境API地址：

```
VITE_API_BASE_URL=https://your-api-domain.com/api
```

## 🎉 总结

Vue3前端完全复刻了原Tkinter界面的布局和功能：

- ✅ 三栏布局（A区20% + B区60% + C区20%）
- ✅ 所有按钮和功能位置一致
- ✅ 知识库管理独立页面（对应test.py弹窗）
- ✅ 完整的用户认证流程
- ✅ 现代化的交互体验

与原Tkinter相比的优势：

- 🌐 Web访问，跨平台
- 📱 响应式设计
- 🎨 更美观的UI
- ⚡ 更好的性能
- 🔧 易于维护和扩展

开始使用：`npm run dev`
