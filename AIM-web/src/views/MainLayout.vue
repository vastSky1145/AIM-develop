<template>
  <div class="main-layout">
    <!-- 顶部标题栏 -->
    <div class="header">
      <div class="title">
        <h1>📚 学术论文助手</h1>
      </div>
      <div class="user-info">
        <span>用户: {{ userInfo.username }}</span>
        <el-button type="warning" size="small" @click="handleChangePassword"
          >修改密码</el-button
        >
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
            type="info"
            size="small"
            @click="openPromptManage"
            style="width: 100%; margin-bottom: 8px"
          >
            Prompt管理
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
            draggable
            :allow-drop="allowDrop"
            :allow-drag="allowDrag"
            @node-click="handleNodeClick"
            @node-contextmenu="handleNodeRightClick"
            @node-drag-start="handleDragStart"
            @node-drag-end="handleDragEnd"
            @node-drop="handleDrop"
            class="paper-tree"
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <span class="node-label">
                  <span>{{ node.label }}</span>
                  <span v-if="data.content" class="node-has-content">📄</span>
                </span>
                <span class="node-actions">
                  <el-button
                    type="primary"
                    size="small"
                    link
                    @click.stop="handleAppendNode(data)"
                    title="添加子节点"
                  >
                    <el-icon><Plus /></el-icon>
                  </el-button>
                  <el-button
                    type="success"
                    size="small"
                    link
                    @click.stop="handleInsertBefore(node, data)"
                    title="在前面插入节点"
                  >
                    <el-icon><Top /></el-icon>
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click.stop="handleRemoveNode(node, data)"
                    title="删除节点"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </span>
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

    <!-- 上传 PDF 论文对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传 PDF 论文"
      width="500px"
      :close-on-click-modal="!uploading"
      :close-on-press-escape="!uploading"
    >
      <el-upload
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".pdf"
        :disabled="uploading"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处 或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">仅支持 .pdf 格式的文件</div>
        </template>
      </el-upload>

      <div style="margin-top: 16px">
        <el-divider content-position="left">解析方式</el-divider>
        <el-radio-group
          v-model="parseMethod"
          :disabled="uploading"
          style="display: flex; flex-direction: column; gap: 8px"
        >
          <el-radio value="agent">
            <span style="font-weight: 600">Agent 智能解析</span>
            <span style="color: #888; font-size: 12px; margin-left: 6px"
              >（LLM 语义理解，精度高，耗时 1-3 分钟）</span
            >
          </el-radio>
          <el-radio value="fast">
            <span style="font-weight: 600">快速解析</span>
            <span style="color: #888; font-size: 12px; margin-left: 6px"
              >（字符串匹配，速度快，依赖格式规范）</span
            >
          </el-radio>
        </el-radio-group>
      </div>

      <div v-if="uploading" style="margin-top: 16px">
        <template v-if="parseMethod === 'agent'">
          <el-progress
            :percentage="uploadProgress"
            :stroke-width="8"
            status="striped"
            striped
            striped-flow
            :duration="8"
          />
          <p style="text-align: center; color: #666; margin-top: 8px; font-size: 13px">
            {{ uploadProgressText }}
          </p>
        </template>
        <template v-else>
          <p style="text-align: center; color: #666; font-size: 13px">
            {{ uploadProgressText || "正在解析中，请稍候..." }}
          </p>
        </template>
      </div>

      <template #footer>
        <el-button :disabled="uploading" @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="confirmUpload">
          <template v-if="uploading">
            {{ parseMethod === "agent" ? "Agent 解析中..." : "解析中..." }}
          </template>
          <template v-else>确定上传</template>
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

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="changePasswordDialogVisible"
      title="修改密码"
      width="400px"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
      >
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            placeholder="请输入旧密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码（至少6位）"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="changePasswordDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="changingPassword"
          @click="confirmChangePassword"
        >
          {{ changingPassword ? "修改中..." : "确定修改" }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { UploadFilled, Plus, Top, Delete } from "@element-plus/icons-vue";
import { paperAPI, authAPI } from "@/api";
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
const uploadProgress = ref(0);
const uploadProgressText = ref("");
const parseMethod = ref("agent"); // 'agent' | 'fast'
let _pollTimer = null;

// 编辑相关
const editDialogVisible = ref(false);
const currentEditNode = ref(null);

// 修改密码相关
const changePasswordDialogVisible = ref(false);
const changingPassword = ref(false);
const passwordFormRef = ref(null);
const passwordForm = reactive({
  oldPassword: "",
  newPassword: "",
  confirmPassword: "",
});

// 密码验证规则
const validateConfirmPassword = (rule, value, callback) => {
  if (value === "") {
    callback(new Error("请再次输入新密码"));
  } else if (value !== passwordForm.newPassword) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
};

const passwordRules = {
  oldPassword: [
    { required: true, message: "请输入旧密码", trigger: "blur" },
    { min: 6, message: "密码至少6位", trigger: "blur" },
  ],
  newPassword: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 6, message: "密码至少6位", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请再次输入新密码", trigger: "blur" },
    { validator: validateConfirmPassword, trigger: "blur" },
  ],
};

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

// ==================== 拖拽相关函数 ====================

// 判断是否允许放置
const allowDrop = (draggingNode, dropNode, type) => {
  // type: 'prev' | 'inner' | 'next'
  // 允许所有类型的放置
  return true;
};

// 判断是否允许拖拽
const allowDrag = (draggingNode) => {
  // 允许所有节点拖拽
  return true;
};

// 拖拽开始
const handleDragStart = (node, event) => {
  console.log("拖拽开始:", node.data.title);
  updateStatus(`正在拖拽: ${node.data.title}`, "warning");
};

// 拖拽结束
const handleDragEnd = (draggingNode, dropNode, dropType, event) => {
  console.log("拖拽结束:", draggingNode.data.title);
  updateStatus("拖拽结束", "success");
};

// 拖拽成功放置
const handleDrop = (draggingNode, dropNode, dropType, event) => {
  console.log("拖拽放置:", {
    dragging: draggingNode.data.title,
    drop: dropNode.data.title,
    type: dropType,
  });
  updateStatus(`节点已移动到 ${dropNode.data.title} ${dropType === 'inner' ? '内部' : dropType === 'prev' ? '之前' : '之后'}`, "success");
  ElMessage.success("节点位置已更新");
};

// ==================== 节点增删函数 ====================

// 生成唯一节点 ID
let nodeIdCounter = 1;
const generateNodeId = () => {
  return `node-${Date.now()}-${nodeIdCounter++}`;
};

// 添加子节点
const handleAppendNode = (data) => {
  ElMessageBox.prompt("请输入新节点标题", "添加子节点", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    inputPattern: /\S+/,
    inputErrorMessage: "节点标题不能为空",
  })
    .then(({ value }) => {
      const newChild = {
        id: generateNodeId(),
        title: value,
        children: [],
        content: "",
      };
      if (!data.children) {
        data.children = [];
      }
      data.children.push(newChild);
      ElMessage.success(`已添加子节点: ${value}`);
      updateStatus(`已添加子节点: ${value}`, "success");
    })
    .catch(() => {
      // 取消操作
    });
};

// 在节点前插入
const handleInsertBefore = (node, data) => {
  ElMessageBox.prompt("请输入新节点标题", "插入节点", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    inputPattern: /\S+/,
    inputErrorMessage: "节点标题不能为空",
  })
    .then(({ value }) => {
      const newNode = {
        id: generateNodeId(),
        title: value,
        children: [],
        content: "",
      };
      
      const parent = node.parent;
      const children = parent.data.children || parent.data;
      const index = children.findIndex((d) => d.id === data.id);
      
      if (index !== -1) {
        children.splice(index, 0, newNode);
        ElMessage.success(`已插入节点: ${value}`);
        updateStatus(`已插入节点: ${value}`, "success");
      }
    })
    .catch(() => {
      // 取消操作
    });
};

// 删除节点
const handleRemoveNode = (node, data) => {
  ElMessageBox.confirm(`确定要删除节点"${data.title}"吗？`, "删除确认", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning",
  })
    .then(() => {
      const parent = node.parent;
      const children = parent.data.children || parent.data;
      const index = children.findIndex((d) => d.id === data.id);
      
      if (index !== -1) {
        children.splice(index, 1);
        ElMessage.success(`已删除节点: ${data.title}`);
        updateStatus(`已删除节点: ${data.title}`, "success");
      }
    })
    .catch(() => {
      // 取消操作
    });
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

const _stopPoll = () => {
  if (_pollTimer) {
    clearInterval(_pollTimer);
    _pollTimer = null;
  }
};

const confirmUpload = async () => {
  if (!uploadFile.value) {
    ElMessage.warning("请先选择文件");
    return;
  }

  uploading.value = true;
  uploadProgress.value = 10;
  uploadProgressText.value = "正在上传文件...";
  updateStatus(
    `正在上传 PDF（${parseMethod.value === "agent" ? "Agent 解析" : "快速解析"}）...`,
    "warning"
  );

  try {
    if (parseMethod.value === "agent") {
      const submitResp = await paperAPI.uploadPDF(uploadFile.value);
      if (!submitResp.success) throw new Error(submitResp.message || "上传失败");

      const taskId = submitResp.data.task_id;
      uploadProgress.value = 20;
      uploadProgressText.value =
        "Agent 正在分析文档结构，请耐心等待（约 1-3 分钟）...";

      await new Promise((resolve, reject) => {
        _pollTimer = setInterval(async () => {
          try {
            const pollResp = await paperAPI.getTaskStatus(taskId);
            const task = pollResp.data;

            if (task.status === "completed") {
              _stopPoll();
              uploadProgress.value = 100;
              uploadProgressText.value = "解析完成！";
              resolve(task.data);
            } else if (task.status === "failed") {
              _stopPoll();
              reject(new Error(task.error || "Agent 解析失败"));
            } else {
              if (uploadProgress.value < 90) uploadProgress.value += 2;
              if (task.progress) uploadProgressText.value = task.progress;
            }
          } catch (e) {
            _stopPoll();
            reject(e);
          }
        }, 3000);
      });
    } else {
      uploadProgressText.value = "字符串匹配解析中，请稍候...";
      const resp = await paperAPI.uploadPDFFast(uploadFile.value);
      if (!resp.success) throw new Error(resp.message || "快速解析失败");
    }

    ElMessage.success("PDF 解析完成，论文已保存");
    uploadDialogVisible.value = false;
    uploadFile.value = null;
    await loadPapers();
    updateStatus("PDF 解析完成", "success");
  } catch (error) {
    console.error("PDF 上传/解析失败:", error);
    ElMessage.error(error.detail || error.message || "PDF 上传失败");
    updateStatus("解析失败", "error");
  } finally {
    _stopPoll();
    uploading.value = false;
    uploadProgress.value = 0;
    uploadProgressText.value = "";
  }
};

onUnmounted(() => {
  _stopPoll();
});

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

// 打开Prompt管理
const openPromptManage = () => {
  router.push("/prompt-manage");
};

// 更新状态
const updateStatus = (text, type = "success") => {
  statusText.value = text;
  statusType.value = type;
};

// 打开修改密码对话框
const handleChangePassword = () => {
  // 重置表单
  passwordForm.oldPassword = "";
  passwordForm.newPassword = "";
  passwordForm.confirmPassword = "";
  changePasswordDialogVisible.value = true;
};

// 确认修改密码
const confirmChangePassword = async () => {
  if (!passwordFormRef.value) return;

  try {
    // 验证表单
    await passwordFormRef.value.validate();

    changingPassword.value = true;
    updateStatus("正在修改密码...", "warning");

    const response = await authAPI.changePassword({
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword,
    });

    if (response.success) {
      ElMessage.success("密码修改成功，请重新登录");
      changePasswordDialogVisible.value = false;

      // 清除登录信息，跳转到登录页
      localStorage.removeItem("token");
      localStorage.removeItem("userInfo");
      
      setTimeout(() => {
        router.push("/login");
      }, 1500);
    } else {
      ElMessage.error(response.message || "密码修改失败");
      updateStatus("修改失败", "error");
    }
  } catch (error) {
    if (error.detail) {
      ElMessage.error(error.detail);
    } else if (error instanceof Error) {
      // 表单验证错误
      console.log("表单验证失败:", error);
    } else {
      ElMessage.error("密码修改失败");
    }
    updateStatus("修改失败", "error");
  } finally {
    changingPassword.value = false;
  }
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

.node-label {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-has-content {
  font-size: 12px;
}

.node-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s ease;
  margin-left: 8px;
}

.tree-node:hover .node-actions {
  opacity: 1;
}

.node-actions .el-button {
  padding: 2px 4px;
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

/* 拖拽状态样式 */
:deep(.el-tree-node.is-drop-inner > .el-tree-node__content) {
  background-color: #e6f7ff;
  border: 1px dashed #1890ff;
}

:deep(.el-tree-node__content:hover) {
  background-color: #f5f5f5;
}

:deep(.el-tree-node.is-dragging > .el-tree-node__content) {
  opacity: 0.6;
  background-color: #e6f7ff;
}

/* 拖拽占位线样式 */
:deep(.el-tree__drop-indicator) {
  height: 2px;
  background-color: #1890ff;
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
