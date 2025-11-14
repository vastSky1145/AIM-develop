<template>
  <div class="edit-node-dialog">
    <el-row :gutter="20">
      <!-- 左侧：已有内容和生成内容 -->
      <el-col :span="12">
        <div class="section">
          <h3>已有内容</h3>
          <el-input
            v-model="existingText"
            type="textarea"
            :rows="10"
            placeholder="节点的现有内容"
          />
        </div>
        
        <div class="section">
          <h3>节点标题</h3>
          <el-input
            v-model="nodeData.title"
            type="textarea"
            :rows="1"
            placeholder="节点的标题"
          />
        </div>
        <div class="section">
          <h3>生成内容</h3>
          <el-input
            v-model="generatedContent"
            type="textarea"
            :rows="15"
            placeholder="AI生成的内容将显示在这里"
          />
          <!-- :readonly="!generatedContent" -->
        </div>
      </el-col>
      
      <!-- 中间：知识库和参考章节 -->
      <el-col :span="6">
        <div class="section">
          <h3>目录范围选择</h3>
          <el-select v-model="startSection" placeholder="起始目录" style="width: 100%; margin-bottom: 10px;">
            <el-option
              v-for="section in sectionOptions"
              :key="section.id"
              :label="`${section.id} - ${section.title}`"
              :value="section.id"
            />
          </el-select>
          
          <el-select v-model="endSection" placeholder="结束目录" style="width: 100%; margin-bottom: 10px;">
            <el-option
              v-for="section in sectionOptions"
              :key="section.id"
              :label="`${section.id} - ${section.title}`"
              :value="section.id"
            />
          </el-select>
          
          <el-button type="primary" size="small" @click="extractReference" style="width: 100%;">
            提取参考文字
          </el-button>
        </div>
        
        <div class="section">
          <h3>参考章节</h3>
          <el-input
            v-model="sectionText"
            type="textarea"
            :rows="8"
            placeholder="提取的参考章节内容"
          />
        </div>
        
        <div class="section">
          <h3>知识库内容</h3>
          <el-input
            v-model="kbContent"
            type="textarea"
            :rows="8"
            placeholder="从知识库检索的内容"
          />
          <el-button type="success" size="small" @click="searchKnowledge" style="width: 100%; margin-top: 10px;">
            检索知识库
          </el-button>
        </div>
      </el-col>
      
      <!-- 右侧：Prompt模板 -->
      <el-col :span="6">
        <div class="section">
          <h3>Prompt 模板</h3>
          
          <!-- 新增：收藏夹选择 -->
          <el-select 
            v-model="selectedFolder" 
            placeholder="选择收藏夹"
            @change="handleFolderChange"
            clearable
            style="width: 100%; margin-bottom: 10px;">
            <el-option
              v-for="folder in folders"
              :key="folder.id"
              :label="folder.folder_name"
              :value="folder.id"
            />
          </el-select>
          
          <!-- 新增：Prompt选择 -->
          <el-select 
            v-model="selectedPrompt" 
            placeholder="选择Prompt模板"
            @change="handlePromptChange"
            clearable
            :disabled="!selectedFolder"
            style="width: 100%; margin-bottom: 10px;">
            <el-option
              v-for="prompt in folderPrompts"
              :key="prompt.id"
              :label="prompt.prompt_name"
              :value="prompt.id"
            />
          </el-select>
          
          <p class="hint">已有内容和知识库内容用$$占位</p>
          <el-input
            v-model="promptTemplate"
            type="textarea"
            :rows="20"
            placeholder="输入Prompt模板..."
          />
        </div>
      </el-col>
    </el-row>
    
    <!-- 底部按钮 -->
    <div class="dialog-footer">
      <el-button @click="$emit('close')">取消</el-button>
      <el-button type="warning" @click="handleModify">修改</el-button>
      <el-button type="primary" :loading="generating" @click="handleGenerate">
        {{ generating ? '生成中...' : '生成' }}
      </el-button>
      <el-button type="success" @click="handleSave">保存</el-button>
    </div>
    
    <!-- 评分弹窗 -->
    <el-dialog
      v-model="ratingDialogVisible"
      title="内容生成评价"
      width="500px"
      draggable
      overflow
      :close-on-click-modal="false"
    >
      <div class="rating-content">
        <div class="rating-item">
          <label>请为本次生成内容评分：</label>
          <el-rate
            v-model="ratingForm.score"
            :max="10"
            show-score
            score-template="{value} 分"
            style="margin-top: 10px;"
          />
          <p class="rating-hint">1-10分，分数越高表示内容质量越好</p>
        </div>
        
        <div class="rating-item">
          <label>评价与建议（可选）：</label>
          <el-input
            v-model="ratingForm.comment"
            type="textarea"
            :rows="4"
            placeholder="请描述您对生成内容的评价，或提出改进建议..."
            style="margin-top: 10px;"
          />
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="skipRating">跳过</el-button>
          <el-button type="primary" @click="submitRating">提交评价</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { aiAPI, knowledgeAPI, promptAPI, userPromptAPI } from '@/api'

const props = defineProps({
  nodeData: {
    type: Object,
    required: true
  },
  paperSections: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['save', 'close'])

// 已有内容
const existingText = ref('')

// 生成内容
const generatedContent = ref('')
const generating = ref(false)
const generatedId = ref('') // 本次生成的ID

// 知识库内容
const kbContent = ref('')

// 章节参考
const sectionText = ref('')
const startSection = ref('')
const endSection = ref('')

// Prompt模板
const promptTemplate = ref('')

// 用户Prompt管理
const folders = ref([])
const selectedFolder = ref('')
const folderPrompts = ref([])
const selectedPrompt = ref('')

// 评分弹窗相关
const ratingDialogVisible = ref(false)
const ratingForm = ref({
  score: 5,
  comment: ''
})

// 章节选项
const sectionOptions = computed(() => {
  const flattenSections = (sections, result = []) => {
    sections.forEach(section => {
      result.push({
        id: section.id,
        title: section.title
      })
      if (section.children && section.children.length > 0) {
        flattenSections(section.children, result)
      }
    })
    return result
  }
  
  return flattenSections(props.paperSections)
})

// 初始化已有内容
const initExistingText = () => {
  let text = `title = ${props.nodeData.title}\n\n`
  if (props.nodeData.content) {
    text += `content{${props.nodeData.content}}`
  }
  existingText.value = text
}

// 加载Prompt模板
const loadPromptTemplate = async () => {
  try {
    const pptId = props.nodeData.id || 'ppt1.1'
    const response = await promptAPI.get(pptId)
    
    if (response.success) {
      promptTemplate.value = response.data.prompt_json
    }
  } catch (error) {
    console.error('加载Prompt模板失败:', error)
    // 使用默认模板
    promptTemplate.value = `你是一个研究视频传输的专家，是一个美国教授。 请将下述已有内容
$$
补全为完整的段落.
要求保持子目录组织结构不变。
补全段落时以下面的知识库位参考资料
$$。
写作逻辑要和以下章节的逻辑内容呼应
$$。
补全段落时要求生成的内容是对已有内容的补充，不改变已有内容的目录结构，可以适当对已有内容的句子扩充，但要保证句子之间逻辑结构和原来一致，扩充内容不要超过1句。知识库中的知识只能作为参考，总结归纳其中语义相关的知识作为参照，而不是直接引用。知识库中出现的图表，若已有内容中没有，则认为该知识不相关，不能作为参考。生成内容和知识库中的原句不可以一样。 latex公式不要编译。要求英文撰写。凝练成逻辑严密的一段话。不要目录结构，不要出现目录编号。生成的文字中要包括已有内容里对图或者表的引用。要求语言风格比较学术化。`
  }
}

// 加载用户收藏夹列表
const loadUserFolders = async () => {
  try {
    const response = await userPromptAPI.getFolders()
    if (response.success) {
      folders.value = response.data || []
    }
  } catch (error) {
    console.error('加载收藏夹列表失败:', error)
  }
}

// 收藏夹选择变化
const handleFolderChange = async (folderId) => {
  if (!folderId) {
    folderPrompts.value = []
    selectedPrompt.value = ''
    return
  }
  
  try {
    const response = await userPromptAPI.getPromptsByFolder(folderId)
    if (response.success) {
      folderPrompts.value = response.data || []
      selectedPrompt.value = ''
    }
  } catch (error) {
    console.error('加载Prompt列表失败:', error)
    ElMessage.error('加载Prompt列表失败')
  }
}

// Prompt选择变化
const handlePromptChange = (promptId) => {
  if (!promptId) {
    return
  }
  
  const selectedPromptData = folderPrompts.value.find(p => p.id === promptId)
  if (selectedPromptData) {
    promptTemplate.value = selectedPromptData.prompt_content
    ElMessage.success('已加载Prompt模板')
  }
}

// 检索知识库
const searchKnowledge = async () => {
  if (!existingText.value.trim()) {
    ElMessage.warning('没有可用于检索的内容')
    return
  }
  
  try {
    const response = await knowledgeAPI.search({
      query: existingText.value,
      k: 6
    })
    
    if (response.success) {
      const docs = response.data.documents || []
      if (docs.length > 0) {
        kbContent.value = docs.map((doc, i) => `第${i+1}条知识:\n${doc.content}`).join('\n\n')
        ElMessage.success(`检索到 ${docs.length} 条相关知识`)
      } else {
        ElMessage.info('未找到相关知识')
        kbContent.value = ''
      }
    }
  } catch (error) {
    console.error('检索知识库失败:', error)
    ElMessage.error('检索知识库失败')
  }
}

// 提取参考文字
const extractReference = () => {
  if (!startSection.value || !endSection.value) {
    ElMessage.warning('请选择起始和结束目录')
    return
  }
  
  // 使用 DFS 提取从起始到结束节点的所有内容（包括中间节点）
  const collected = []
  let foundStart = false
  
  const dfs = (section) => {
    const sid = section.id || ''
    
    // 找到起始节点
    if (sid === startSection.value) {
      foundStart = true
    }
    
    // 如果已找到起始节点，开始收集
    if (foundStart) {
      collected.push(section)
    }
    
    // 如果到达结束节点，返回 true 停止搜索
    if (sid === endSection.value) {
      return true
    }
    
    // 递归搜索子节点
    if (section.children && section.children.length > 0) {
      for (const child of section.children) {
        if (dfs(child)) {
          return true
        }
      }
    }
    
    return false
  }
  
  // 遍历所有顶层节点
  for (const section of props.paperSections) {
    if (dfs(section)) {
      break
    }
  }
  
  // 构建提取的文本
  if (collected.length > 0) {
    let text = ''
    for (const sec of collected) {
      text += `${sec.title}\n`
      if (sec.content) {
        text += `${sec.content}\n\n`
      } else {
        text += '\n'
      }
    }
    sectionText.value = text.trim()
    ElMessage.success(`参考文字提取成功，共提取 ${collected.length} 个节点`)
  } else {
    ElMessage.error('提取失败，未找到指定的目录范围')
  }
}

// 生成内容
const handleGenerate = async () => {
  if (!promptTemplate.value.trim()) {
    ElMessage.warning('请输入Prompt模板')
    return
  }
  
  generating.value = true
  
  try {
    const response = await aiAPI.generate({
      existing_text: existingText.value,//现有文本
      kb_content: kbContent.value,//知识库内容
      section_text: sectionText.value,//章节参考内容
      prompt_template: promptTemplate.value//Prompt模板
    })
    
    if (response.success) {
      generatedContent.value = response.data.generated_content
      generatedId.value = response.data.generated_id //本次生成的id
      ElMessage.success('内容生成成功')
      // 弹出评分弹窗
      showRatingDialog()
    }
  } catch (error) {
    console.error('生成内容失败:', error)
    ElMessage.error(error.detail || '生成内容失败')
  } finally {
    generating.value = false
  }
}

// 修改内容
const handleModify = async () => {
  if (!generatedContent.value) {
    ElMessage.warning('请先生成内容')
    return
  }
  
  const instruction = await ElMessageBox.prompt('请输入修改指令', '修改内容', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputPlaceholder: '例如：请将这段话改得更专业'
  }).catch(() => null)
  
  if (!instruction) return
  
  try {
    const response = await aiAPI.modify({
      original_content: generatedContent.value,
      modification_instruction: instruction.value
    })
    
    if (response.success) {
      generatedContent.value = response.data.generated_content
      generatedId.value = response.data.generated_id //本次生成的id
      ElMessage.success('内容修改成功')
      // 弹出评分弹窗
      showRatingDialog()
    }
  } catch (error) {
    console.error('修改内容失败:', error)
    ElMessage.error('修改内容失败')
  }
}

// 显示评分弹窗
const showRatingDialog = () => {
  // 重置评分表单
  ratingForm.value = {
    score: 5,
    comment: ''
  }
  ratingDialogVisible.value = true
}

// 提交评分
const submitRating = async () => {
  if (!generatedId.value) {
    ElMessage.warning('未找到生成记录ID')
    return
  }
  
  try {
    const response = await aiAPI.submitRating({
      generated_id: generatedId.value,
      score: ratingForm.value.score,
      comment: ratingForm.value.comment
    })
    
    if (response.success) {
      ElMessage.success('评分提交成功，感谢您的反馈！')
      ratingDialogVisible.value = false
    }
  } catch (error) {
    console.error('提交评分失败:', error)
    ElMessage.error('提交评分失败')
  }
}

// 跳过评分
const skipRating = () => {
  ratingDialogVisible.value = false
}

// 保存
const handleSave = () => {
  if (!generatedContent.value) {
    ElMessage.warning('没有可保存的内容')
    return
  }
  
  emit('save', {
    ...props.nodeData,
    content: generatedContent.value
  })
}

// 初始化
onMounted(() => {
  initExistingText()
  loadPromptTemplate()
  loadUserFolders()
})
</script>

<style scoped>
.edit-node-dialog {
  max-height: 70vh;
  overflow-y: auto;
}

.section {
  margin-bottom: 20px;
}

.section h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.hint {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

:deep(.el-textarea__inner) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

.rating-content {
  padding: 10px 0;
}

.rating-item {
  margin-bottom: 20px;
}

.rating-item label {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.rating-hint {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
  margin-bottom: 0;
}
</style>

