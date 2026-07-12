<template>
  <div class="reading-mode">
    <!-- 左侧：论文正文 -->
    <div class="reading-paper">
      <div class="paper-title-block">
        <h1 class="paper-main-title">{{ paperTitle }}</h1>
      </div>

      <div v-if="!sections.length" class="empty-hint">该论文暂无内容</div>

      <div class="paper-body">
        <ReadingSection
          v-for="section in sections"
          :key="section.id"
          :section="section"
          :level="1"
          :active-id="activeSectionId"
          @select="handleSelectSection"
        />
      </div>
    </div>

    <!-- 右侧：提示词面板 -->
    <div class="reading-prompt">
      <div class="prompt-header">
        <h3>章节提示词</h3>
        <p class="current-section">
          当前章节：
          <span v-if="activeSection">{{ activeSection.title }}</span>
          <span v-else class="muted">请在左侧点击章节标题</span>
        </p>
      </div>

      <div class="prompt-body">
        <template v-if="activeSection">
          <div class="prompt-select-block">
            <el-select
              v-model="selectedFolder"
              placeholder="选择收藏夹"
              clearable
              style="width: 100%; margin-bottom: 10px"
              @change="handleFolderChange"
            >
              <el-option
                v-for="folder in folders"
                :key="folder.id"
                :label="folder.folder_name"
                :value="folder.id"
              />
            </el-select>

            <el-select
              v-model="selectedPrompt"
              placeholder="选择 Prompt 模板"
              clearable
              :disabled="!selectedFolder"
              style="width: 100%; margin-bottom: 10px"
              @change="handlePromptChange"
            >
              <el-option
                v-for="prompt in folderPrompts"
                :key="prompt.id"
                :label="prompt.prompt_name"
                :value="prompt.id"
              />
            </el-select>

            <div class="prompt-actions">
              <el-button
                type="primary"
                size="small"
                :disabled="!selectedPrompt"
                @click="handleBindPrompt"
              >
                绑定到此章节
              </el-button>
              <el-button
                type="danger"
                size="small"
                :disabled="!activeSection.promptId"
                @click="handleUnbindPrompt"
              >
                解除绑定
              </el-button>
            </div>
          </div>

          <el-divider content-position="left">提示词内容</el-divider>

          <div v-if="previewContent" class="prompt-preview">
            <div class="prompt-preview-name" v-if="previewName">
             {{ previewName }}
            </div>
            <pre class="prompt-preview-text">{{ previewContent }}</pre>
          </div>
          <div v-else class="empty-hint small">
            该章节尚未绑定提示词，请从上方选择后绑定
          </div>
        </template>

        <div v-else class="empty-hint">请先在左侧选择一个章节</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from "vue";
import { ElMessage } from "element-plus";
import { userPromptAPI } from "@/api";

// 递归章节渲染子组件（内联定义）
const ReadingSection = {
  name: "ReadingSection",
  props: {
    section: { type: Object, required: true },
    level: { type: Number, default: 1 },
    activeId: { type: [String, Number], default: null },
  },
  emits: ["select"],
  setup(props, { emit }) {
    const headingTag = computed(() => {
      const lvl = Math.min(props.level, 6);
      return `h${lvl}`;
    });

    const isActive = computed(
      () => String(props.section.id) === String(props.activeId)
    );

    const onClick = () => emit("select", props.section);

    return () => {
      const children = [];

      // 标题
      children.push(
        h(
          headingTag.value,
          {
            class: [
              "reading-heading",
              `reading-heading-l${props.level}`,
              { "reading-heading-active": isActive.value },
            ],
            onClick,
          },
          [
            h("span", props.section.title || "（无标题）"),
            props.section.promptId
              ? h("span", { class: "bound-mark", title: "已绑定提示词" }, " （已绑定）")
              : null,
          ]
        )
      );

      // 正文
      if (props.section.content) {
        children.push(
          h(
            "p",
            { class: "reading-content" },
            props.section.content
          )
        );
      }

      // 子章节
      if (props.section.children && props.section.children.length) {
        props.section.children.forEach((child) => {
          children.push(
            h(ReadingSection, {
              key: child.id,
              section: child,
              level: props.level + 1,
              activeId: props.activeId,
              onSelect: (s) => emit("select", s),
            })
          );
        });
      }

      return h("div", { class: "reading-section-block" }, children);
    };
  },
};

const props = defineProps({
  paperTitle: {
    type: String,
    default: "",
  },
  sections: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update-sections", "save"]);

// 当前选中章节
const activeSectionId = ref(null);
const activeSection = ref(null);

// 提示词收藏夹
const folders = ref([]);
const selectedFolder = ref("");
const folderPrompts = ref([]);
const selectedPrompt = ref("");

// 预览
const previewContent = ref("");
const previewName = ref("");

// 选择章节
const handleSelectSection = (section) => {
  activeSectionId.value = section.id;
  activeSection.value = section;

  // 重置选择器
  selectedFolder.value = "";
  folderPrompts.value = [];
  selectedPrompt.value = "";

  // 显示已绑定的提示词
  if (section.promptId) {
    previewName.value = section.promptName || "";
    previewContent.value = section.promptContent || "（提示词内容未缓存，请重新选择绑定以刷新）";
  } else {
    previewName.value = "";
    previewContent.value = "";
  }
};

// 加载收藏夹
const loadFolders = async () => {
  try {
    const response = await userPromptAPI.getFolders();
    if (response.success) {
      folders.value = response.data || [];
    }
  } catch (error) {
    console.error("加载收藏夹失败:", error);
  }
};

// 收藏夹切换
const handleFolderChange = async (folderId) => {
  selectedPrompt.value = "";
  folderPrompts.value = [];
  if (!folderId) return;

  try {
    const response = await userPromptAPI.getPromptsByFolder(folderId);
    if (response.success) {
      folderPrompts.value = response.data || [];
    }
  } catch (error) {
    console.error("加载 Prompt 列表失败:", error);
    ElMessage.error("加载 Prompt 列表失败");
  }
};

// Prompt 切换（预览）
const handlePromptChange = (promptId) => {
  if (!promptId) {
    return;
  }
  const p = folderPrompts.value.find((item) => item.id === promptId);
  if (p) {
    previewName.value = p.prompt_name;
    previewContent.value = p.prompt_content;
  }
};

// 绑定提示词
const handleBindPrompt = () => {
  if (!activeSection.value || !selectedPrompt.value) return;

  const p = folderPrompts.value.find((item) => item.id === selectedPrompt.value);
  if (!p) return;

  activeSection.value.promptId = p.id;
  activeSection.value.promptName = p.prompt_name;
  activeSection.value.promptContent = p.prompt_content;

  previewName.value = p.prompt_name;
  previewContent.value = p.prompt_content;

  ElMessage.success(`已将提示词「${p.prompt_name}」绑定到章节「${activeSection.value.title}」`);
  console.log("绑定的章节内容是:", activeSection);
  emit("save");
};

// 解除绑定
const handleUnbindPrompt = () => {
  if (!activeSection.value) return;

  delete activeSection.value.promptId;
  delete activeSection.value.promptName;
  delete activeSection.value.promptContent;

  previewName.value = "";
  previewContent.value = "";
  selectedPrompt.value = "";

  ElMessage.success("已解除提示词绑定");
  emit("save");
};

onMounted(() => {
  loadFolders();
});
</script>

<style scoped>
.reading-mode {
  display: flex;
  height: 100%;
  overflow: hidden;
}

/* 左侧论文正文 */
.reading-paper {
  flex: 1;
  overflow-y: auto;
  padding: 40px 60px;
  background: #fff;
}

.paper-title-block {
  text-align: center;
  margin-bottom: 32px;
  border-bottom: 2px solid #eee;
  padding-bottom: 20px;
}

.paper-main-title {
  font-size: 28px;
  color: #222;
  margin: 0;
  font-weight: 700;
}

.paper-body {
  max-width: 820px;
  margin: 0 auto;
  line-height: 1.9;
  color: #333;
}

/* 右侧提示词面板 */
.reading-prompt {
  width: 35%;
  min-width: 320px;
  max-width: 480px;
  border-left: 1px solid #e0e0e0;
  background: #fafafa;
  display: flex;
  flex-direction: column;
}

.prompt-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
  background: #fff;
}

.prompt-header h3 {
  margin: 0 0 8px 0;
  font-size: 15px;
  color: #333;
}

.current-section {
  margin: 0;
  font-size: 13px;
  color: #555;
}

.current-section span {
  font-weight: 600;
  color: #1890ff;
}

.current-section .muted {
  color: #999;
  font-weight: normal;
}

.prompt-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.prompt-select-block {
  margin-bottom: 16px;
}

.prompt-actions {
  display: flex;
  gap: 8px;
}

.prompt-preview {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 12px;
}

.prompt-preview-name {
  font-weight: 600;
  font-size: 13px;
  color: #1890ff;
  margin-bottom: 8px;
}

.prompt-preview-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: "Consolas", "Monaco", monospace;
  font-size: 12px;
  color: #444;
  line-height: 1.6;
}

.empty-hint {
  text-align: center;
  color: #999;
  padding: 40px 20px;
  font-size: 14px;
}

.empty-hint.small {
  padding: 20px;
  font-size: 13px;
}
</style>

<style>
/* 非 scoped：作用于 h() 渲染出来的章节标题（渲染函数生成的 DOM 不带 scoped 属性） */
.reading-section-block {
  margin-bottom: 4px;
}

.reading-heading {
  cursor: pointer;
  transition: color 0.2s, background 0.2s;
  scroll-margin-top: 20px;
  padding: 2px 6px;
  border-radius: 4px;
}

.reading-heading:hover {
  background: #f0f7ff;
  color: #1890ff;
}

.reading-heading-active {
  background: #e6f7ff;
  color: #1890ff;
  border-left: 3px solid #1890ff;
  padding-left: 8px;
}

.reading-heading-l1 {
  font-size: 22px;
  font-weight: 700;
  margin-top: 28px;
  margin-bottom: 12px;
}

.reading-heading-l2 {
  font-size: 18px;
  font-weight: 600;
  margin-top: 22px;
  margin-bottom: 10px;
}

.reading-heading-l3 {
  font-size: 16px;
  font-weight: 600;
  margin-top: 18px;
  margin-bottom: 8px;
}

.reading-heading-l4,
.reading-heading-l5,
.reading-heading-l6 {
  font-size: 14px;
  font-weight: 600;
  margin-top: 14px;
  margin-bottom: 6px;
}

.bound-mark {
  font-size: 13px;
}

.reading-content {
  margin: 0 0 16px 0;
  text-indent: 2em;
  white-space: pre-wrap;
  word-break: break-word;
  text-align: justify;
}
</style>