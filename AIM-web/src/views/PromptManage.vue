<template>
  <div class="prompt-manage">
    <!-- 头部 -->
    <div class="pm-header">
      <h1>📝 Prompt模板管理</h1>
      <el-button type="primary" @click="$router.push('/')">返回主页</el-button>
    </div>
    
    <!-- 主内容区 -->
    <div class="pm-content">
      <!-- 左侧：收藏夹列表 -->
      <div class="pm-sidebar">
        <div class="sidebar-header">
          <h3>收藏夹</h3>
          <el-button type="primary" size="small" @click="showCreateFolderDialog">
            新建
          </el-button>
        </div>
        
        <div class="folder-list">
          <div
            v-for="folder in folders"
            :key="folder.id"
            :class="['folder-item', { active: selectedFolderId === folder.id }]"
            @click="selectFolder(folder)"
            @contextmenu.prevent="handleFolderRightClick($event, folder)"
          >
            <div class="folder-info">
              <el-icon><Folder /></el-icon>
              <span class="folder-name">{{ folder.folder_name }}</span>
              <el-tag size="small" type="info">{{ folder.prompt_count }}</el-tag>
            </div>
          </div>
          
          <div v-if="folders.length === 0" class="empty-tip">
            暂无收藏夹，点击"新建"创建
          </div>
        </div>
      </div>
      
      <!-- 右侧：Prompt列表 -->
      <div class="pm-main">
        <div class="main-toolbar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索Prompt..."
            clearable
            style="width: 300px;"
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
          
          <el-button 
            type="primary" 
            :icon="Plus"
            @click="showCreatePromptDialog"
            :disabled="!selectedFolderId"
          >
            新建Prompt
          </el-button>
        </div>
        
        <div class="prompt-list">
          <el-empty v-if="prompts.length === 0" description="暂无Prompt模板" />
          
          <div
            v-for="prompt in prompts"
            :key="prompt.id"
            class="prompt-card"
          >
            <div class="card-header">
              <h4>{{ prompt.prompt_name }}</h4>
              <div class="card-actions">
                <el-button type="primary" size="small" @click="editPrompt(prompt)">
                  编辑
                </el-button>
                <el-button type="danger" size="small" @click="deletePrompt(prompt)">
                  删除
                </el-button>
              </div>
            </div>
            
            <div class="card-body">
              <p v-if="prompt.description" class="prompt-desc">
                {{ prompt.description }}
              </p>
              <div class="prompt-content-preview">
                {{ prompt.prompt_content.substring(0, 150) }}
                <span v-if="prompt.prompt_content.length > 150">...</span>
              </div>
            </div>
            
            <div class="card-footer">
              <div class="prompt-tags">
                <el-tag
                  v-for="tag in prompt.tags"
                  :key="tag"
                  size="small"
                  type="success"
                >
                  {{ tag }}
                </el-tag>
              </div>
              <span class="prompt-time">
                {{ formatTime(prompt.updated_at) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 收藏夹编辑对话框 -->
    <el-dialog
      v-model="folderDialogVisible"
      :title="isEditFolder ? '编辑收藏夹' : '新建收藏夹'"
      width="500px"
    >
      <el-form :model="folderForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="folderForm.folder_name" placeholder="请输入收藏夹名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="folderForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入收藏夹描述（可选）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="folderDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFolder">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- Prompt编辑对话框 -->
    <el-dialog
      v-model="promptDialogVisible"
      :title="isEditPrompt ? '编辑Prompt' : '新建Prompt'"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form :model="promptForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="promptForm.prompt_name" placeholder="请输入Prompt名称" />
        </el-form-item>
        
        <el-form-item label="所属收藏夹" required>
          <el-select v-model="promptForm.folder_id" placeholder="选择收藏夹" style="width: 100%;">
            <el-option
              v-for="folder in folders"
              :key="folder.id"
              :label="folder.folder_name"
              :value="folder.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="内容" required>
          <el-input
            v-model="promptForm.prompt_content"
            type="textarea"
            :rows="12"
            placeholder="请输入Prompt内容"
          />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input
            v-model="promptForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入Prompt描述（可选）"
          />
        </el-form-item>
        
        <el-form-item label="标签">
          <el-select
            v-model="promptForm.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入后按回车添加标签"
            style="width: 100%;"
          >
            <el-option
              v-for="tag in commonTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="promptDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPrompt">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 收藏夹右键菜单 -->
    <el-dropdown
      trigger="contextmenu"
      :style="{ position: 'absolute', left: contextMenuX + 'px', top: contextMenuY + 'px' }"
      v-if="contextMenuVisible"
      @command="handleFolderCommand"
    >
      <span style="display: none;"></span>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="edit">编辑</el-dropdown-item>
          <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Folder } from '@element-plus/icons-vue'
import { userPromptAPI } from '@/api'
import { useRouter } from 'vue-router'

const router = useRouter()

// 数据状态
const folders = ref([])
const selectedFolderId = ref('')
const prompts = ref([])
const searchKeyword = ref('')

// 收藏夹对话框
const folderDialogVisible = ref(false)
const isEditFolder = ref(false)
const currentFolder = ref(null)
const folderForm = ref({
  folder_name: '',
  description: ''
})

// Prompt对话框
const promptDialogVisible = ref(false)
const isEditPrompt = ref(false)
const currentPrompt = ref(null)
const promptForm = ref({
  folder_id: '',
  prompt_name: '',
  prompt_content: '',
  description: '',
  tags: []
})

// 常用标签
const commonTags = ref(['学术写作', '引言', '方法', '结论', '讨论', '综述'])

// 右键菜单
const contextMenuVisible = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

// ============ 收藏夹操作 ============

// 加载收藏夹列表
const loadFolders = async () => {
  try {
    const response = await userPromptAPI.getFolders()
    if (response.success) {
      folders.value = response.data || []
      
      // 如果之前有选中的收藏夹，尝试保持选中状态
      if (selectedFolderId.value) {
        const stillExists = folders.value.find(f => f.id === selectedFolderId.value)
        if (stillExists) {
          loadPrompts(selectedFolderId.value)
        } else {
          selectedFolderId.value = ''
          prompts.value = []
        }
      }
    }
  } catch (error) {
    console.error('加载收藏夹失败:', error)
    ElMessage.error('加载收藏夹失败')
  }
}

// 选择收藏夹
const selectFolder = (folder) => {
  selectedFolderId.value = folder.id
  searchKeyword.value = ''
  loadPrompts(folder.id)
}

// 显示创建收藏夹对话框
const showCreateFolderDialog = () => {
  isEditFolder.value = false
  currentFolder.value = null
  folderForm.value = {
    folder_name: '',
    description: ''
  }
  folderDialogVisible.value = true
}

// 显示编辑收藏夹对话框
const showEditFolderDialog = (folder) => {
  isEditFolder.value = true
  currentFolder.value = folder
  folderForm.value = {
    folder_name: folder.folder_name,
    description: folder.description || ''
  }
  folderDialogVisible.value = true
}

// 提交收藏夹
const submitFolder = async () => {
  if (!folderForm.value.folder_name.trim()) {
    ElMessage.warning('请输入收藏夹名称')
    return
  }
  
  try {
    if (isEditFolder.value) {
      // 更新收藏夹
      const response = await userPromptAPI.updateFolder(currentFolder.value.id, folderForm.value)
      if (response.success) {
        ElMessage.success('收藏夹更新成功')
        folderDialogVisible.value = false
        loadFolders()
      }
    } else {
      // 创建收藏夹
      const response = await userPromptAPI.createFolder(folderForm.value)
      if (response.success) {
        ElMessage.success('收藏夹创建成功')
        folderDialogVisible.value = false
        loadFolders()
      }
    }
  } catch (error) {
    console.error('保存收藏夹失败:', error)
    ElMessage.error(error.detail || '保存收藏夹失败')
  }
}

// 删除收藏夹
const deleteFolderConfirm = async (folder) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除收藏夹"${folder.folder_name}"吗？这将同时删除其下的所有Prompt模板。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await userPromptAPI.deleteFolder(folder.id)
    if (response.success) {
      ElMessage.success('收藏夹删除成功')
      if (selectedFolderId.value === folder.id) {
        selectedFolderId.value = ''
        prompts.value = []
      }
      loadFolders()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除收藏夹失败:', error)
      ElMessage.error(error.detail || '删除收藏夹失败')
    }
  }
}

// 收藏夹右键菜单
const handleFolderRightClick = (event, folder) => {
  currentFolder.value = folder
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  contextMenuVisible.value = true
  
  // 点击其他地方关闭菜单
  setTimeout(() => {
    document.addEventListener('click', () => {
      contextMenuVisible.value = false
    }, { once: true })
  }, 100)
}

const handleFolderCommand = (command) => {
  if (command === 'edit') {
    showEditFolderDialog(currentFolder.value)
  } else if (command === 'delete') {
    deleteFolderConfirm(currentFolder.value)
  }
}

// ============ Prompt操作 ============

// 加载Prompts
const loadPrompts = async (folderId) => {
  try {
    const response = await userPromptAPI.getPromptsByFolder(folderId)
    if (response.success) {
      prompts.value = response.data || []
    }
  } catch (error) {
    console.error('加载Prompt列表失败:', error)
    ElMessage.error('加载Prompt列表失败')
  }
}

// 搜索Prompts
const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    if (selectedFolderId.value) {
      loadPrompts(selectedFolderId.value)
    }
    return
  }
  
  try {
    const response = await userPromptAPI.searchPrompts(searchKeyword.value)
    if (response.success) {
      prompts.value = response.data || []
      selectedFolderId.value = '' // 搜索时取消选中收藏夹
      ElMessage.success(`找到${prompts.value.length}个Prompt`)
    }
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error('搜索失败')
  }
}

// 显示创建Prompt对话框
const showCreatePromptDialog = () => {
  if (!selectedFolderId.value) {
    ElMessage.warning('请先选择一个收藏夹')
    return
  }
  
  isEditPrompt.value = false
  currentPrompt.value = null
  promptForm.value = {
    folder_id: selectedFolderId.value,
    prompt_name: '',
    prompt_content: '',
    description: '',
    tags: []
  }
  promptDialogVisible.value = true
}

// 编辑Prompt
const editPrompt = (prompt) => {
  isEditPrompt.value = true
  currentPrompt.value = prompt
  promptForm.value = {
    folder_id: prompt.folder_id,
    prompt_name: prompt.prompt_name,
    prompt_content: prompt.prompt_content,
    description: prompt.description || '',
    tags: [...(prompt.tags || [])]
  }
  promptDialogVisible.value = true
}

// 提交Prompt
const submitPrompt = async () => {
  if (!promptForm.value.prompt_name.trim()) {
    ElMessage.warning('请输入Prompt名称')
    return
  }
  
  if (!promptForm.value.prompt_content.trim()) {
    ElMessage.warning('请输入Prompt内容')
    return
  }
  
  if (!promptForm.value.folder_id) {
    ElMessage.warning('请选择所属收藏夹')
    return
  }
  
  try {
    if (isEditPrompt.value) {
      // 更新Prompt
      const response = await userPromptAPI.updatePrompt(currentPrompt.value.id, promptForm.value)
      if (response.success) {
        ElMessage.success('Prompt更新成功')
        promptDialogVisible.value = false
        if (selectedFolderId.value) {
          loadPrompts(selectedFolderId.value)
        }
        loadFolders() // 刷新收藏夹统计
      }
    } else {
      // 创建Prompt
      const response = await userPromptAPI.createPrompt(promptForm.value)
      if (response.success) {
        ElMessage.success('Prompt创建成功')
        promptDialogVisible.value = false
        if (selectedFolderId.value) {
          loadPrompts(selectedFolderId.value)
        }
        loadFolders() // 刷新收藏夹统计
      }
    }
  } catch (error) {
    console.error('保存Prompt失败:', error)
    ElMessage.error(error.detail || '保存Prompt失败')
  }
}

// 删除Prompt
const deletePrompt = async (prompt) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除Prompt"${prompt.prompt_name}"吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await userPromptAPI.deletePrompt(prompt.id)
    if (response.success) {
      ElMessage.success('Prompt删除成功')
      if (selectedFolderId.value) {
        loadPrompts(selectedFolderId.value)
      }
      loadFolders() // 刷新收藏夹统计
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除Prompt失败:', error)
      ElMessage.error(error.detail || '删除Prompt失败')
    }
  }
}

// 格式化时间
const formatTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 初始化
onMounted(() => {
  loadFolders()
})
</script>

<style scoped>
.prompt-manage {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 头部 */
.pm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.pm-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

/* 主内容区 */
.pm-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 20px;
  gap: 20px;
}

/* 左侧边栏 */
.pm-sidebar {
  width: 280px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.folder-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.folder-item {
  padding: 12px 15px;
  margin-bottom: 5px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.folder-item:hover {
  background: #f0f2f5;
}

.folder-item.active {
  background: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.folder-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.folder-name {
  flex: 1;
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-tip {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 14px;
}

/* 右侧主区域 */
.pm-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.main-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.prompt-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* Prompt卡片 */
.prompt-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 15px;
  transition: all 0.3s;
  background: white;
}

.prompt-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-header h4 {
  margin: 0;
  font-size: 16px;
  color: #333;
  font-weight: 600;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.card-body {
  margin-bottom: 12px;
}

.prompt-desc {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.prompt-content-preview {
  color: #999;
  font-size: 13px;
  line-height: 1.6;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  white-space: pre-wrap;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prompt-tags {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.prompt-time {
  font-size: 12px;
  color: #999;
}

/* 滚动条样式 */
:deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #bbb;
}
</style>

