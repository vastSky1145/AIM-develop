---
name: Prompt版本控制功能实现计划
overview: ""
todos:
  - id: e3d2204e-cd40-4f18-b5ea-4382507793c7
    content: 创建schemas/user_prompt.py，定义收藏夹和Prompt的数据模型
    status: pending
  - id: 851e279a-f83c-4b67-a92e-62b5c77a0e6d
    content: 扩展mongodb.py，添加PromptFolderDatabase类实现数据库操作
    status: pending
  - id: f1ca6049-d6fa-4ac2-ac05-da9819a3db91
    content: 创建routers/user_prompts.py，实现收藏夹和Prompt的API路由
    status: pending
  - id: fcc83e6f-6e0b-44a2-83f6-ba467cdc2231
    content: 在app.py中注册新的路由模块
    status: pending
  - id: 9a923b2c-939d-4376-b3db-1cf97625c615
    content: 在src/api/index.js中添加userPromptAPI封装
    status: pending
  - id: 67682f1d-4fb4-4ed9-9c76-6df3f52ea54d
    content: 修改EditNodeDialog.vue，添加收藏夹和Prompt下拉列表
    status: pending
  - id: debc9c3a-5eda-4c18-a5bc-78e96f2f2c55
    content: 创建src/views/PromptManage.vue，实现Prompt管理页面
    status: pending
  - id: 730ceda9-a69a-4182-8b40-700c2919cea4
    content: 在router.js中添加Prompt管理页面路由
    status: pending
isProject: false
---

# Prompt版本控制功能实现计划

## 一、数据库设计（MongoDB）

### 新增：Prompt版本集合（prompt_versions）

```javascript
{
  _id: ObjectId,
  prompt_id: String,           // 关联的Prompt ID
  version_number: Number,      // 版本号（1, 2, 3...）
  user_id: String,            // 用户ID
  folder_id: String,          // 所属收藏夹ID（快照时）
  prompt_name: String,        // Prompt名称（快照）
  prompt_content: String,     // Prompt内容（完整快照）
  description: String,        // Prompt描述（快照）
  tags: [String],            // 标签（快照）
  change_description: String, // 本次修改说明（必填）
  created_at: DateTime,      // 创建时间
  is_rollback: Boolean       // 是否由回滚操作创建
}
```

### 修改：user_prompts集合

添加字段：

- `current_version: Number` - 当前版本号
- `total_versions: Number` - 总版本数

## 二、后端API实现

### 1. 扩展mongodb.py - PromptVersionDatabase类

新增方法：

- `create_version()` - 创建版本快照
- `get_versions_by_prompt()` - 获取Prompt的所有版本
- `get_version_by_id()` - 获取特定版本详情
- `rollback_to_version()` - 回滚到指定版本
- `compare_versions()` - 对比两个版本

### 2. 修改现有Prompt操作逻辑

**创建Prompt时**：

- 自动创建初始版本（version 1）
- change_description: "初始创建"

**更新Prompt时**：

- 创建新版本快照（version_number++）
- 要求提供change_description（必填）
- 更新current_version和total_versions

### 3. 新增路由（routers/user_prompts.py）

版本控制相关：

- `GET /api/user-prompts/versions/{prompt_id}` - 获取版本历史列表
- `GET /api/user-prompts/versions/detail/{version_id}` - 获取版本详情
- `POST /api/user-prompts/versions/rollback/{prompt_id}` - 回滚到指定版本
- `GET /api/user-prompts/versions/compare` - 对比两个版本

### 4. 更新schemas/user_prompt.py

新增模型：

- `VersionResponse` - 版本响应
- `VersionCompareRequest` - 版本对比请求
- `VersionCompareResponse` - 版本对比响应

修改模型：

- `PromptUpdate` 添加 `change_description: str` 必填字段
- `PromptResponse` 添加 `current_version` 和 `total_versions`

## 三、前端实现

### 1. 修改PromptManage.vue

#### 在Prompt卡片上添加版本信息显示

```vue
<div class="card-footer">
  <div class="prompt-tags">...</div>
  <div class="version-info">
    <el-tag size="small" type="warning">v{{ prompt.current_version }}</el-tag>
    <el-button 
      type="text" 
      size="small" 
      @click="showVersionHistory(prompt)"
    >
      查看历史
    </el-button>
  </div>
  <span class="prompt-time">...</span>
</div>
```

#### 修改Prompt编辑对话框

在提交时要求填写修改说明：

```vue
<el-form-item label="修改说明" required v-if="isEditPrompt">
  <el-input
    v-model="promptForm.change_description"
    type="textarea"
    :rows="2"
    placeholder="请描述本次修改的内容和原因..."
  />
</el-form-item>
```

#### 新增版本历史对话框

```vue
<el-dialog 
  v-model="versionHistoryVisible"
  title="版本历史"
  width="1000px"
>
  <!-- 左侧：版本列表 -->
  <div class="version-history-layout">
    <div class="version-list">
      <div 
        v-for="version in versions"
        :key="version._id"
        :class="['version-item', { active: selectedVersion?.id === version.id }]"
        @click="selectVersion(version)"
      >
        <div class="version-header">
          <el-tag size="small">v{{ version.version_number }}</el-tag>
          <span v-if="version.is_rollback" class="rollback-badge">回滚</span>
        </div>
        <div class="version-time">{{ formatTime(version.created_at) }}</div>
        <div class="version-change">{{ version.change_description }}</div>
      </div>
    </div>
    
    <!-- 右侧：版本详情和对比 -->
    <div class="version-detail">
      <el-tabs v-model="versionTab">
        <el-tab-pane label="版本内容" name="content">
          <div class="version-content">
            <h4>{{ selectedVersion?.prompt_name }}</h4>
            <p>{{ selectedVersion?.description }}</p>
            <div class="tags">
              <el-tag v-for="tag in selectedVersion?.tags" :key="tag">
                {{ tag }}
              </el-tag>
            </div>
            <pre>{{ selectedVersion?.prompt_content }}</pre>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="与当前版本对比" name="compare">
          <div class="version-diff">
            <!-- 使用diff库显示差异 -->
          </div>
        </el-tab-pane>
      </el-tabs>
      
      <div class="version-actions">
        <el-button 
          type="primary" 
          @click="rollbackToVersion"
          :disabled="selectedVersion?.version_number === currentPrompt?.current_version"
        >
          回滚到此版本
        </el-button>
      </div>
    </div>
  </div>
</el-dialog>
```

### 2. 更新API封装（api/index.js）

在userPromptAPI中添加：

```javascript
// 版本控制
getVersions(promptId) {
  return api.get(`/user-prompts/versions/${promptId}`)
},
getVersionDetail(versionId) {
  return api.get(`/user-prompts/versions/detail/${versionId}`)
},
rollbackVersion(promptId, data) {
  return api.post(`/user-prompts/versions/rollback/${promptId}`, data)
},
compareVersions(promptId, versionId1, versionId2) {
  return api.get(`/user-prompts/versions/compare?prompt_id=${promptId}&version1=${versionId1}&version2=${versionId2}`)
}
```

### 3. 安装diff库（可选）

如需要高级的差异对比显示：

```bash
npm install diff
```

在版本对比时使用：

```javascript
import * as Diff from 'diff'

const diff = Diff.diffWords(version1.content, version2.content)
```

## 四、实现细节

### 版本创建时机

1. **创建Prompt**：

   - version_number = 1
   - change_description = "初始创建"

2. **更新Prompt**：

   - 检查内容是否有实质性变化
   - 如果有变化，要求填写change_description
   - version_number = current_version + 1

3. **回滚Prompt**：

   - 创建新版本（不覆盖历史）
   - is_rollback = true
   - change_description = "回滚到版本 {version_number}: {原版本的change_description}"

### 数据完整性

- 版本快照包含Prompt的所有字段（完整备份）
- 即使Prompt被删除，版本历史也保留（可选择是否级联删除）
- 版本号连续递增，不允许跳号

### 性能优化

- 版本列表分页加载（每页20条）
- 版本内容懒加载（点击时才加载详情）
- 考虑对旧版本进行归档压缩（未来优化）

## 五、用户体验设计

### 修改Prompt流程

1. 用户点击"编辑"
2. 修改Prompt内容
3. **必须填写"修改说明"（新增必填项）**
4. 提交保存
5. 系统创建新版本快照

### 查看版本历史流程

1. 在Prompt卡片上点击"查看历史"按钮
2. 打开版本历史对话框
3. 左侧显示版本时间线列表
4. 点击版本查看详情或对比差异
5. 可选择回滚到任意历史版本

### 回滚操作

1. 选择要回滚的版本
2. 点击"回滚到此版本"
3. 确认对话框提示影响
4. 回滚后创建新版本（标记为rollback）
5. 保留原有版本历史不变

## 六、数据导出功能（为AI训练准备）

### 导出接口

`GET /api/user-prompts/export-training-data`

导出格式：

```json
{
  "prompts": [
    {
      "prompt_id": "xxx",
      "versions": [
        {
          "version": 1,
          "content": "...",
          "change_description": "初始创建",
          "timestamp": "..."
        },
        {
          "version": 2,
          "content": "...",
          "change_description": "优化了引言部分的逻辑",
          "timestamp": "..."
        }
      ]
    }
  ]
}
```

用于AI模型训练：

- 学习Prompt的演化模式
- 理解修改意图和描述
- 生成改进建议

## 文件清单

**后端新增/修改**：

1. `mongodb.py` - 添加PromptVersionDatabase类
2. `schemas/user_prompt.py` - 添加版本相关模型
3. `routers/user_prompts.py` - 添加版本控制路由，修改更新逻辑

**前端修改**：

1. `src/views/PromptManage.vue` - 添加版本历史功能
2. `src/api/index.js` - 添加版本API封装

**可选依赖**：

1. `npm install diff` - 用于版本差异对比显示