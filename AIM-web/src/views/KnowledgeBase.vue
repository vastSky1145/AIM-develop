<template>
  <div class="knowledge-base">
    <!-- 头部 -->
    <div class="kb-header">
      <h1>知识库系统</h1>
      <div class="kb-actions">
        <el-button type="primary" @click="router.push('/')">返回主页</el-button>
      </div>
    </div>
    
    <!-- 工具栏 -->
    <div class="kb-toolbar">
      <el-space>
        <el-button type="primary" icon="Upload" @click="uploadDialogVisible = true">
          上传PDF
        </el-button>
        
        <el-button type="success" icon="View" @click="viewSources">查看知识库</el-button>
        <el-button type="danger" icon="Delete" @click="handleDelete">删除内容</el-button>
      </el-space>
    </div>
    
    <!-- 搜索区域 -->
    <div class="kb-search">
      <el-input
        v-model="searchQuery"
        placeholder="输入关键词搜索知识库..."
        size="large"
        clearable
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button icon="Search" @click="handleSearch" :loading="searching">搜索</el-button>
        </template>
      </el-input>
    </div>
    
    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="kb-tabs">
      <!-- 检索结果 -->
      <el-tab-pane label="检索结果" name="search">
        <div class="tab-content">
          <div v-if="searchResults.length === 0" class="empty-state">
            <el-empty description="在上方输入关键词开始检索" />
          </div>
          
          <div v-else class="result-list">
            <el-card 
              v-for="(item, index) in searchResults" 
              :key="index"
              class="result-item"
              shadow="hover"
            >
              <template #header>
                <div class="result-header">
                  <span class="result-title">结果 {{ index + 1 }}</span>
                </div>
              </template>
              <div class="result-content">{{ item.content }}</div>
              <div class="result-meta">
                <el-tag type="info" size="small">来源: {{ item.source }}</el-tag>
              </div>
            </el-card>
          </div>
        </div>
      </el-tab-pane>
      
      <!-- 知识库内容 -->
      <el-tab-pane label="知识库内容" name="sources">
        <div class="tab-content">
          <div v-if="sources.length === 0" class="empty-state">
            <el-empty description="知识库为空，请上传PDF文件" />
          </div>
          
          <div v-else class="source-list">
            <el-card
              v-for="(source, index) in sources"
              :key="index"
              class="source-item"
              shadow="hover"
            >
              <div class="source-info">
                <div class="source-name">
                  <el-icon><Document /></el-icon>
                  <span>{{ source.source }}</span>
                </div>
                <div class="source-count">
                  文档块数量: <el-tag type="success" size="small">{{ source.doc_count }}</el-tag>
                </div>
              </div>
              <div class="source-actions">
                <el-button type="danger" size="small" @click="deleteSource(source.source)">
                  删除
                </el-button>
              </div>
            </el-card>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 状态栏 -->
    <div class="kb-status">
      <span :class="['status-text', statusType]">{{ statusText }}</span>
    </div>
    
    <!-- 上传 PDF 对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传 PDF"
      width="500px"
      :close-on-click-modal="!uploading"
      :close-on-press-escape="!uploading"
    >
      <el-upload
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :file-list="pendingFiles"
        multiple
        accept=".pdf"
        :disabled="uploading"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处 或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">仅支持 .pdf 格式的文件，可一次选择多个</div>
        </template>
      </el-upload>

      <div v-if="uploading" class="upload-progress">
        <el-progress :percentage="uploadProgress" :status="uploadStatus" />
        <p class="progress-text">{{ progressText }}</p>
      </div>

      <template #footer>
        <el-button :disabled="uploading" @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="confirmUpload">
          {{ uploading ? '上传中...' : '开始上传' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Upload, UploadFilled, View, Search, Delete } from '@element-plus/icons-vue'
import { knowledgeAPI } from '@/api'

const router = useRouter()

// 搜索相关
const searchQuery = ref('')
const searching = ref(false)
const searchResults = ref([])

// 标签页
const activeTab = ref('search')

// 知识库来源
const sources = ref([])

// 状态栏
const statusText = ref('系统就绪 | 可上传PDF或进行知识检索')
const statusType = ref('success')

// 上传相关
const uploadDialogVisible = ref(false)
const uploading = ref(false)
const pendingFiles = ref([])
const currentIndex = ref(0)
const currentFileName = ref('')
const uploadProgress = ref(0)
const uploadStatus = ref('')
const progressText = ref('')

// 搜索知识库
const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  
  searching.value = true
  updateStatus('正在检索...', 'warning')
  
  try {
    const response = await knowledgeAPI.search({
      query: searchQuery.value,
      k: 6
    })
    
    if (response.success) {
      searchResults.value = response.data.documents || []
      updateStatus(`找到 ${searchResults.value.length} 个结果`, 'success')
      activeTab.value = 'search'
      
      if (searchResults.value.length === 0) {
        ElMessage.info('未找到相关结果')
      }
    }
  } catch (error) {
    console.error('检索失败:', error)
    ElMessage.error('检索失败')
    updateStatus('检索失败', 'error')
  } finally {
    searching.value = false
  }
}

// 查看知识库
const viewSources = async () => {
  updateStatus('正在加载知识库...', 'warning')
  
  try {
    const response = await knowledgeAPI.getSources()
    
    if (response.success) {
      sources.value = response.data || []
      updateStatus(`共 ${sources.value.length} 个来源`, 'success')
      activeTab.value = 'sources'
      
      if (sources.value.length === 0) {
        ElMessage.info('知识库为空')
      }
    }
  } catch (error) {
    console.error('加载知识库失败:', error)
    ElMessage.error('加载知识库失败')
    updateStatus('加载失败', 'error')
  }
}

const syncPendingFiles = (fileList) => {
  pendingFiles.value = fileList
}

const handleFileChange = (file, fileList) => {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    ElMessage.error('只支持PDF文件')
    syncPendingFiles(fileList.filter((item) => item.uid !== file.uid))
    return
  }

  if (file.name.includes(' ')) {
    ElMessage.error('文件名不能包含空格')
    syncPendingFiles(fileList.filter((item) => item.uid !== file.uid))
    return
  }

  syncPendingFiles(fileList)
}

const handleFileRemove = (file, fileList) => {
  syncPendingFiles(fileList)
}

const confirmUpload = async () => {
  if (pendingFiles.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }

  const total = pendingFiles.value.length
  uploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = ''
  currentIndex.value = 0
  currentFileName.value = ''
  updateStatus('正在上传...', 'warning')

  let successCount = 0
  let stopped = false

  try {
    for (const file of pendingFiles.value) {
      currentFileName.value = file.name
      progressText.value = `当前 ${currentIndex.value + 1}/${total} · ${file.name}`

      const response = await knowledgeAPI.uploadPDF(file.raw)

      if (!response.success) {
        uploadStatus.value = 'exception'
        progressText.value = '上传失败'
        ElMessage.error(response.message || `上传失败：${file.name}`)
        updateStatus('上传失败', 'error')
        stopped = true
        break
      }

      successCount += 1
      currentIndex.value = successCount
      uploadProgress.value = Math.round((successCount / total) * 100)
    }

    if (!stopped && successCount === total) {
      uploadStatus.value = 'success'
      uploadProgress.value = 100
      progressText.value = '上传成功！'
      ElMessage.success(`成功上传 ${successCount} 个 PDF`)
      updateStatus('上传成功', 'success')

      setTimeout(() => {
        uploadDialogVisible.value = false
        viewSources()
      }, 1500)
    }
  } catch (error) {
    console.error('上传PDF失败:', error)
    uploadStatus.value = 'exception'
    progressText.value = '上传失败'
    ElMessage.error(error.detail || error.message || '上传PDF失败')
    updateStatus('上传失败', 'error')
  } finally {
    uploading.value = false
    pendingFiles.value = []
    currentIndex.value = 0
    currentFileName.value = ''
  }
}

// 删除来源
const deleteSource = async (source) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除来源"${source}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await knowledgeAPI.delete({ source })
    
    if (response.success) {
      ElMessage.success('删除成功')
      viewSources() // 刷新列表
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 删除操作
const handleDelete = async () => {
  try {
    const action = await ElMessageBox.confirm(
      '请选择删除方式',
      '删除知识',
      {
        distinguishCancelAndClose: true,
        confirmButtonText: '清空知识库',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 清空知识库
    await ElMessageBox.confirm(
      '此操作不可恢复！确定要清空整个知识库吗？',
      '最终确认',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    const response = await knowledgeAPI.clear()
    
    if (response.success) {
      ElMessage.success('知识库已清空')
      sources.value = []
      searchResults.value = []
      updateStatus('知识库已清空', 'success')
    }
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 更新状态
const updateStatus = (text, type = 'success') => {
  statusText.value = text
  statusType.value = type
}

// 初始化
onMounted(() => {
  updateStatus('系统就绪 | 可上传PDF或进行知识检索', 'success')
})
</script>

<style scoped>
.knowledge-base {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.kb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.kb-header h1 {
  margin: 0;
  font-size: 24px;
}

.kb-toolbar {
  padding: 15px 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

.kb-search {
  padding: 15px 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

.kb-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  overflow: hidden;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
}

.tab-content {
  padding: 20px;
  min-height: 400px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.result-list, .source-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.result-item, .source-item {
  transition: all 0.3s;
}

.result-item:hover, .source-item:hover {
  transform: translateY(-2px);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-title {
  font-weight: 600;
  color: #333;
}

.result-content {
  line-height: 1.8;
  color: #666;
  margin-bottom: 15px;
}

.result-meta {
  display: flex;
  gap: 10px;
}

.source-item :deep(.el-card__body) {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.source-info {
  flex: 1;
}

.source-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.source-count {
  font-size: 14px;
  color: #666;
}

.kb-status {
  padding: 12px 20px;
  background: white;
  border-top: 1px solid #e0e0e0;
  font-size: 14px;
}

.status-text.success {
  color: #52c41a;
}

.status-text.warning {
  color: #faad14;
}

.status-text.error {
  color: #f5222d;
}

.upload-progress {
  padding: 20px;
}

.progress-text {
  text-align: center;
  margin-top: 15px;
  color: #666;
}
</style>

