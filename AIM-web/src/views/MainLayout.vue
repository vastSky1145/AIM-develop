<template>
  <div class="main-layout">
    <!-- 顶部标题栏 -->
    <div class="header">
      <div class="title">
        <h1>📚 学术论文助手</h1>
      </div>
      <div class="user-info">
        <span>用户: {{ userInfo.username }}</span>
        <el-button type="danger" size="small" @click="handleLogout"
          >退出登录</el-button
        >
      </div>
    </div>

    <!-- 三栏布局 -->
    <div class="content-wrapper">
      <!-- A区：论文列表 (20%) -->
      <div class="panel panel-a">
        <div class="panel-header">
          <h3>用户{{ userInfo.username }}已有的论文</h3>
          <!-- 刷新论文列表 -->
          <el-button type="primary" size="small" @click="loadPapers"
            >刷新论文列表</el-button
          >
        </div>

        <div class="panel-content">
          <div class="paper-list">
            <div class="list-header">Title:</div>
            <div
              v-for="(paper, index) in papers"
              :key="paper.paper_title"
              class="paper-item"
              :class="{
                active: selectedPaper?.paper_title === paper.paper_title,
              }"
              @click="selectPaper(paper)"
            >
              第{{ index + 1 }}篇: {{ paper.paper_title }}
            </div>

            <div v-if="papers.length === 0" class="empty-hint">
              暂无论文，请上传PPT
            </div>
          </div>
        </div>

        <div class="panel-footer">
          <el-button
            type="danger"
            size="small"
            @click="handleDeletePaper"
            style="width: 100%; margin-bottom: 8px"
          >
            删除论文
          </el-button>
          <el-button
            type="success"
            size="small"
            @click="openKnowledgeBase"
            style="width: 100%; margin-bottom: 8px"
          >
            提交知识
          </el-button>
          <el-button
            type="primary"
            size="small"
            @click="handleUploadPPT"
            style="width: 100%; margin-bottom: 8px"
          >
            上传PDF
            <!-- 暂时改动：上传PPT改为上传PDF -->
          </el-button>
          <el-button
            type="warning"
            size="small"
            @click="handleSavePaper"
            style="width: 100%"
          >
            保存论文
          </el-button>
        </div>
      </div>

      <!-- B区：论文树形结构 (60%) -->
      <div class="panel panel-b">
        <div class="tree-container">
          <el-tree
            ref="treeRef"
            :data="treeData"
            node-key="id"
            default-expand-all
            :props="treeProps"
            @node-click="handleNodeClick"
            @node-contextmenu="handleNodeRightClick"
            class="paper-tree"
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <span>{{ node.label }}</span>
                <span v-if="data.content" class="node-has-content">📄</span>
              </span>
            </template>
          </el-tree>

          <div v-if="!treeData.length" class="empty-tree">
            请点击左侧论文查看内容
          </div>
        </div>
      </div>

      <!-- C区：大纲面板 (20%) -->
      <div class="panel panel-c">
        <div class="panel-header">
          <h3>论文大纲</h3>
        </div>

        <div class="panel-content">
          <div class="outline-list">
            <div
              v-for="(section, index) in outlineSections"
              :key="index"
              class="outline-item"
              @contextmenu.prevent="
                handleOutlineRightClick($event, section, index)
              "
            >
              <span class="status-icon">{{
                section.completed ? "✓" : "✗"
              }}</span>
              <span class="section-title">{{ section.title }}</span>
            </div>

            <div v-if="!outlineSections.length" class="empty-hint">
              暂无大纲
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部状态栏 -->
    <div class="status-bar">
      <span :class="['status-text', statusType]">{{ statusText }}</span>
    </div>

    <!-- 上传PPT对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传PPT" width="500px">
      <el-upload
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".pdf"
      >
      <!-- 暂时改动：accept=".ppt,.pptx"改为accept=".pdf" -->
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处 或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">仅支持 .pdf 格式的文件</div>
          <!-- 暂时改动：accept=".ppt,.pptx"改为accept=".pdf" -->
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="confirmUpload">
          {{ uploading ? "上传中..." : "确定上传" }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑节点对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑内容"
      width="80%"
      top="5vh"
    >
      <EditNodeDialog
        v-if="editDialogVisible"
        :node-data="currentEditNode"
        :paper-sections="selectedPaper?.sections || []"
        @save="handleSaveNode"
        @close="editDialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";
import { paperAPI } from "@/api";
import EditNodeDialog from "@/components/EditNodeDialog.vue";
import { parse } from "pptxtojson";

const router = useRouter();

// 用户信息
const userInfo = ref(JSON.parse(localStorage.getItem("userInfo") || "{}"));

// 论文列表
const papers = ref([]);
const selectedPaper = ref(null);

// 树形数据
const treeData = ref([]);
const treeProps = {
  label: "title",
  children: "children",
};

// 大纲数据
const outlineSections = ref([]);

// 状态栏
const statusText = ref("就绪");
const statusType = ref("success");

// 上传相关
const uploadDialogVisible = ref(false);
const uploading = ref(false);
const uploadFile = ref(null);

// 编辑相关
const editDialogVisible = ref(false);
const currentEditNode = ref(null);

// 加载论文列表
const loadPapers = async () => {
  try {
    const response = await paperAPI.getList();
    if (response.success) {
      console.log(response);
      papers.value = response.data || [];
      updateStatus("论文列表加载成功", "success");
    }
  } catch (error) {
    console.error("加载论文列表失败:", error);
    ElMessage.error("加载论文列表失败");
  }
};

// 选择论文
const selectPaper = async (paper) => {
  selectedPaper.value = paper;

  // 转换为树形结构
  if (paper.sections && paper.sections.length > 0) {
    treeData.value = paper.sections.map((section, index) => ({
      ...section,
      id: section.id || `section-${index}`,
    }));

    // 更新大纲（只显示第一级）
    outlineSections.value = paper.sections.map((section) => ({
      title: section.title,
      completed: false,
    }));
  } else {
    treeData.value = [];
    outlineSections.value = [];
  }

  updateStatus(`已加载论文: ${paper.paper_title}`, "success");
};

// 节点点击
const handleNodeClick = (data) => {
  console.log("点击节点:", data);
};

// 节点右键
const handleNodeRightClick = (event, data, node) => {
  event.preventDefault();

  ElMessageBox.confirm("选择操作", "节点操作", {
    distinguishCancelAndClose: true,
    confirmButtonText: "编辑",
    cancelButtonText: "展开全部",
  })
    .then(() => {
      // 编辑
      currentEditNode.value = data;
      editDialogVisible.value = true;
    })
    .catch((action) => {
      if (action === "cancel") {
        // 展开全部子节点
        expandAllChildren(node);
      }
    });
};

// 展开所有子节点
const expandAllChildren = (node) => {
  node.expanded = true;
  if (node.childNodes) {
    node.childNodes.forEach((child) => expandAllChildren(child));
  }
};

// 大纲右键
const handleOutlineRightClick = (event, section, index) => {
  const items = [
    { label: "编辑", action: "edit" },
    { label: "删除", action: "delete" },
    { label: "标记", action: "mark" },
    { label: "插入", action: "insert" },
  ];

  // 这里可以实现自定义右键菜单
  ElMessageBox.confirm("请选择操作", "大纲操作", {
    distinguishCancelAndClose: true,
    confirmButtonText: "编辑",
    cancelButtonText: "取消",
  }).then(() => {
    // 编辑大纲项
    console.log("编辑大纲:", section);
  });
};

// 上传PPT
const handleUploadPPT = () => {
  uploadDialogVisible.value = true;
};

const handleFileChange = (file) => {
  uploadFile.value = file.raw;
  console.log("选择文件:", uploadFile.value);
};

const confirmUpload = async () => {
  if (!uploadFile.value) {
    ElMessage.warning("请先选择文件");
    return;
  }

  uploading.value = true;
  updateStatus("正在上传和解析PPT...", "warning");


  try {
    // const response = await paperAPI.uploadPPT(uploadFile.value)
    const response = await paperAPI.uploadPDF(uploadFile.value)
    // 暂时改动：uploadPPT改为uploadPDF

    if (response.success) {
      ElMessage.success('PPT上传成功')
      uploadDialogVisible.value = false
      uploadFile.value = null

      // 重新加载论文列表
      await loadPapers()
      updateStatus('PPT解析完成', 'success')
    } else {
      ElMessage.error(response.message || 'PPT上传失败')
      updateStatus('上传失败', 'error')
    }
  } catch (error) {
    console.error('上传PPT失败:', error)
    ElMessage.error(error.detail || 'PPT上传失败')
    updateStatus('上传失败', 'error')
  } finally {
    uploading.value = false
  }
};

// 删除论文
const handleDeletePaper = async () => {
  if (!selectedPaper.value) {
    ElMessage.warning("请先选择要删除的论文");
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除论文《${selectedPaper.value.paper_title}》吗？`,
      "确认删除",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }
    );

    const response = await paperAPI.delete({
      paper_title: selectedPaper.value.paper_title,
      uid: userInfo.value.user_id,
    });

    if (response.success) {
      ElMessage.success("论文删除成功");
      selectedPaper.value = null;
      treeData.value = [];
      outlineSections.value = [];
      await loadPapers();
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除论文失败:", error);
      ElMessage.error(error.detail || "删除论文失败");
    }
  }
};

// 保存论文
const handleSavePaper = async () => {
  if (!selectedPaper.value) {
    ElMessage.warning("请先选择论文");
    return;
  }

  try {
    const response = await paperAPI.update({
      paper_title: selectedPaper.value.paper_title,
      uid: userInfo.value.user_id,
      sections: treeData.value,
    });

    if (response.success) {
      ElMessage.success("论文保存成功");
      updateStatus("保存成功", "success");
    }
  } catch (error) {
    console.error("保存论文失败:", error);
    ElMessage.error("保存论文失败");
  }
};

// 保存节点编辑
// const handleSaveNode = async (nodeData) => {
//   console.log('保存节点:', nodeData)
//   editDialogVisible.value = false
//   ElMessage.success('节点保存成功')
// }
const handleSaveNode = async (updatedNode) => {
  const patchNode = (nodes) =>
    nodes.map((node) => {
      if (node.id === updatedNode.id) {
        return { ...node, ...updatedNode };
      }
      if (node.children?.length) {
        return { ...node, children: patchNode(node.children) };
      }
      return node;
    });

  treeData.value = patchNode(treeData.value);
  editDialogVisible.value = false;
  ElMessage.success("节点保存成功");
};

// 打开知识库
const openKnowledgeBase = () => {
  router.push("/knowledge");
};

// 更新状态
const updateStatus = (text, type = "success") => {
  statusText.value = text;
  statusType.value = type;
};

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm("确定要退出登录吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });

    localStorage.removeItem("token");
    localStorage.removeItem("userInfo");
    router.push("/login");
  } catch (error) {
    // 取消
  }
};

// 初始化
onMounted(() => {
  loadPapers();
});
</script>

<style scoped>
.main-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header .title h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.content-wrapper {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.panel {
  display: flex;
  flex-direction: column;
  background: white;
  border-right: 1px solid #e0e0e0;
}

.panel-a {
  width: 20%;
  min-width: 250px;
}

.panel-b {
  flex: 1;
}

.panel-c {
  width: 20%;
  min-width: 200px;
  border-right: none;
}

.panel-header {
  padding: 15px;
  border-bottom: 1px solid #e0e0e0;
  background: #fafafa;
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.panel-footer {
  padding: 10px;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
}

.panel-c {
  width: 20%;
  min-width: 200px;
  border-right: none;
}

.panel-header {
  padding: 15px;
  border-bottom: 1px solid #e0e0e0;
  background: #fafafa;
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.panel-footer {
  padding: 10px;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
  padding-bottom: 18px;
}

.paper-list {
  font-size: 14px;
}

.list-header {
  font-weight: bold;
  margin-bottom: 10px;
  padding: 5px;
}

.paper-item {
  padding: 10px;
  margin-bottom: 5px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
  word-wrap: break-word;
}

.paper-item:hover {
  background: #f0f0f0;
}

.paper-item.active {
  background: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.tree-container {
  height: 100%;
  overflow-y: auto;
}

.paper-tree {
  font-size: 14px;
}

.tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
  padding-right: 8px;
}

.node-has-content {
  font-size: 12px;
}

.empty-tree,
.empty-hint {
  text-align: center;
  color: #999;
  padding: 40px 20px;
  font-size: 14px;
}

.outline-list {
  font-size: 14px;
}

.outline-item {
  padding: 10px;
  margin-bottom: 5px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}

.outline-item:hover {
  background: #f0f0f0;
}

.status-icon {
  font-size: 12px;
}

.section-title {
  flex: 1;
}

.status-bar {
  padding: 8px 20px;
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

:deep(.el-tree-node__content) {
  height: 32px;
  font-size: 14px;
}

:deep(.el-upload-dragger) {
  padding: 40px;
}
</style>


<style>
.panel-footer .el-button {
  margin-left: 0; /* 统一所有按钮左边距为0 */
}
</style>
