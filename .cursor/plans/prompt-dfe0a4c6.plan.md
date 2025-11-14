<!-- dfe0a4c6-50eb-4b6d-802a-4e50e8512ea8 d5f1f4e4-f007-4786-a020-e51fddd8d0e1 -->
# Prompt管理功能实现计划

## 一、数据库设计（MongoDB）

### 1. 收藏夹集合（prompt_folders）

```javascript
{
  _id: ObjectId,
  user_id: String,           // 用户ID
  folder_name: String,        // 收藏夹名称
  description: String,        // 描述
  created_at: DateTime,       // 创建时间
  updated_at: DateTime        // 更新时间
}
```

### 2. Prompt集合（user_prompts）

```javascript
{
  _id: ObjectId,
  user_id: String,           // 用户ID
  folder_id: String,         // 所属收藏夹ID
  prompt_name: String,       // Prompt名称
  prompt_content: String,    // Prompt内容
  description: String,       // 描述
  tags: [String],           // 标签数组
  created_at: DateTime,     // 创建时间
  updated_at: DateTime      // 更新时间
}
```

## 二、后端API实现

### 1. 创建schemas（schemas/user_prompt.py）

- FolderCreate/FolderUpdate/FolderResponse
- PromptCreate/PromptUpdate/PromptResponse
- FolderWithPromptsResponse

### 2. 扩展mongodb.py

- 添加PromptFolderDatabase类
- 实现收藏夹的CRUD操作
- 实现prompt的CRUD操作

### 3. 创建路由（routers/user_prompts.py）

收藏夹相关：

- `GET /api/user-prompts/folders` - 获取用户的所有收藏夹
- `POST /api/user-prompts/folders` - 创建收藏夹
- `PUT /api/user-prompts/folders/{folder_id}` - 更新收藏夹
- `DELETE /api/user-prompts/folders/{folder_id}` - 删除收藏夹

Prompt相关：

- `GET /api/user-prompts/list` - 获取指定收藏夹下的所有prompts
- `POST /api/user-prompts/create` - 创建prompt
- `PUT /api/user-prompts/update/{prompt_id}` - 更新prompt
- `DELETE /api/user-prompts/delete/{prompt_id}` - 删除prompt
- `GET /api/user-prompts/search` - 搜索prompts

### 4. 注册路由到app.py

## 三、前端EditNodeDialog.vue修改

在第91行下方添加两个下拉列表：

```vue
<div class="section">
  <h3>Prompt 模板</h3>
  
  <!-- 新增：收藏夹选择 -->
  <el-select 
    v-model="selectedFolder" 
    placeholder="选择收藏夹"
    @change="handleFolderChange"
    style="width: 100%; margin-bottom: 10px;">
    <el-option
      v-for="folder in folders"
      :key="folder._id"
      :label="folder.folder_name"
      :value="folder._id"
    />
  </el-select>
  
  <!-- 新增：Prompt选择 -->
  <el-select 
    v-model="selectedPrompt" 
    placeholder="选择Prompt模板"
    @change="handlePromptChange"
    style="width: 100%; margin-bottom: 10px;">
    <el-option
      v-for="prompt in folderPrompts"
      :key="prompt._id"
      :label="prompt.prompt_name"
      :value="prompt._id"
    />
  </el-select>
  
  <p class="hint">已有内容和知识库内容用$$占位</p>
  <el-input type="textarea" :rows="25" v-model="promptTemplate" />
</div>
```

实现逻辑：

- onMounted时加载用户的收藏夹列表
- 选择收藏夹时，加载该收藏夹下的prompt列表
- 选择prompt时，自动填充到promptTemplate

## 四、前端创建PromptManage.vue

### 布局设计

```
┌─────────────────────────────────────────┐
│  📝 Prompt管理          [返回主页]       │
├──────────┬──────────────────────────────┤
│ 收藏夹   │       Prompt列表              │
│ (25%)    │       (75%)                   │
│          │                               │
│ [新建]   │  搜索框                       │
│          │  [新建Prompt]                 │
│ 收藏夹1  │                               │
│ 收藏夹2  │  ┌─────────────────────────┐ │
│ ...      │  │ Prompt卡片1             │ │
│          │  │ - 标题                  │ │
│          │  │ - 描述                  │ │
│          │  │ - 标签                  │ │
│          │  │ [编辑] [删除]           │ │
│          │  └─────────────────────────┘ │
│          │                               │
│          │  ┌─────────────────────────┐ │
│          │  │ Prompt卡片2             │ │
│          │  └─────────────────────────┘ │
└──────────┴──────────────────────────────┘
```

### 主要功能

1. **左侧收藏夹列表**

   - 显示所有收藏夹
   - 新建收藏夹（对话框）
   - 点击选中收藏夹
   - 右键菜单：编辑、删除

2. **右侧Prompt列表**

   - 搜索框（按名称搜索）
   - 新建Prompt按钮
   - Prompt卡片展示（名称、描述、标签）
   - 编辑/删除按钮

3. **编辑对话框**

   - 收藏夹编辑：名称、描述
   - Prompt编辑：名称、内容、描述、标签

## 五、前端API封装（api/index.js）

添加userPromptAPI模块：

```javascript
export const userPromptAPI = {
  // 收藏夹
  getFolders() {
    return api.get('/user-prompts/folders')
  },
  createFolder(data) {
    return api.post('/user-prompts/folders', data)
  },
  updateFolder(folderId, data) {
    return api.put(`/user-prompts/folders/${folderId}`, data)
  },
  deleteFolder(folderId) {
    return api.delete(`/user-prompts/folders/${folderId}`)
  },
  
  // Prompts
  getPromptsByFolder(folderId) {
    return api.get(`/user-prompts/list?folder_id=${folderId}`)
  },
  createPrompt(data) {
    return api.post('/user-prompts/create', data)
  },
  updatePrompt(promptId, data) {
    return api.put(`/user-prompts/update/${promptId}`, data)
  },
  deletePrompt(promptId) {
    return api.delete(`/user-prompts/delete/${promptId}`)
  },
  searchPrompts(keyword) {
    return api.get(`/user-prompts/search?keyword=${keyword}`)
  }
}
```

## 六、路由配置（router.js）

添加路由：

```javascript
{
  path: '/prompt-manage',
  name: 'PromptManage',
  component: () => import('./views/PromptManage.vue'),
  meta: { requiresAuth: true }
}
```

可选：在MainLayout中添加入口按钮

## 技术要点

- 使用Element Plus的el-select、el-card、el-tag等组件
- 使用el-dialog实现编辑对话框
- 使用el-dropdown实现右键菜单
- 响应式数据管理（ref/reactive）
- 适当的加载状态和错误处理
- 删除操作需要确认对话框

## 文件清单

**后端新增/修改**：

1. `schemas/user_prompt.py` (新建)
2. `routers/user_prompts.py` (新建)
3. `mongodb.py` (修改，添加PromptFolderDatabase类)
4. `app.py` (修改，注册新路由)

**前端新增/修改**：

1. `src/components/EditNodeDialog.vue` (修改)
2. `src/views/PromptManage.vue` (新建)
3. `src/api/index.js` (修改)
4. `src/router.js` (修改)

### To-dos

- [ ] 创建schemas/user_prompt.py，定义收藏夹和Prompt的数据模型
- [ ] 扩展mongodb.py，添加PromptFolderDatabase类实现数据库操作
- [ ] 创建routers/user_prompts.py，实现收藏夹和Prompt的API路由
- [ ] 在app.py中注册新的路由模块
- [ ] 在src/api/index.js中添加userPromptAPI封装
- [ ] 修改EditNodeDialog.vue，添加收藏夹和Prompt下拉列表
- [ ] 创建src/views/PromptManage.vue，实现Prompt管理页面
- [ ] 在router.js中添加Prompt管理页面路由