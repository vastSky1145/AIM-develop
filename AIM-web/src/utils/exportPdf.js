/**
 * 论文导出 PDF 工具
 *
 * 使用 html2pdf.js（html2canvas + jsPDF）将论文章节树渲染为一份排版好的
 * 隐藏 DOM，再截图分页生成 PDF 并触发下载。
 *
 * 注意：content 为纯文本（可能夹杂未渲染的 LaTeX 原文），按原文输出，不做公式渲染。
 */
import html2pdf from "html2pdf.js";

// 文件名过滤非法字符，与导出 JSON 保持一致
const sanitizeFilename = (name) => (name || "paper").replace(/[\\/:*?"<>|]/g, "_");

// 章节标题层级编号，如 1、1.1、1.1.1...
const buildHeading = (title, numberPrefix, level) => {
  const heading = document.createElement(level <= 4 ? `h${Math.min(level + 1, 4)}` : "h5");
  heading.className = `pdf-heading pdf-heading-l${level}`;
  heading.textContent = numberPrefix ? `${numberPrefix} ${title || "（无标题）"}` : title || "（无标题）";
  return heading;
};

// 递归构建章节 DOM，numberPrefix 形如 "1"、"1.1"
const buildSectionNodes = (sections, level, parentPrefix, container) => {
  (sections || []).forEach((section, index) => {
    const numberPrefix = parentPrefix ? `${parentPrefix}.${index + 1}` : `${index + 1}`;

    container.appendChild(buildHeading(section.title, numberPrefix, level));

    if (section.content) {
      const p = document.createElement("p");
      p.className = "pdf-content";
      p.textContent = section.content;
      container.appendChild(p);
    }

    if (section.children && section.children.length) {
      buildSectionNodes(section.children, level + 1, numberPrefix, container);
    }
  });
};

// 构建整篇论文的 HTML 容器（挂载在屏幕外，供 html2pdf 截图）
const buildPaperHtml = (paperTitle, sections) => {
  const wrapper = document.createElement("div");
  wrapper.className = "pdf-export-root";
  wrapper.style.cssText = [
    "position: fixed",
    "left: -9999px",
    "top: 0",
    "width: 800px",
    "background: #fff",
    "color: #000",
    "font-family: 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif",
    "padding: 10px",
    "box-sizing: border-box",
  ].join(";");

  const titleEl = document.createElement("h1");
  titleEl.className = "pdf-paper-title";
  titleEl.textContent = paperTitle || "未命名论文";
  titleEl.style.cssText =
    "text-align: center; font-size: 24px; margin-bottom: 24px; page-break-inside: avoid;";
  wrapper.appendChild(titleEl);

  const style = document.createElement("style");
  style.textContent = `
    .pdf-heading {
      page-break-inside: avoid;
      break-inside: avoid;
      margin: 16px 0 8px 0;
      font-weight: 600;
      color: #111;
    }
    .pdf-heading-l1 { font-size: 20px; }
    .pdf-heading-l2 { font-size: 18px; }
    .pdf-heading-l3 { font-size: 16px; }
    .pdf-heading-l4,
    .pdf-heading-l5 { font-size: 15px; }
    .pdf-content {
      margin: 0 0 14px 0;
      font-size: 14px;
      line-height: 1.8;
      text-indent: 2em;
      text-align: justify;
      white-space: pre-wrap;
      word-break: break-word;
    }
  `;
  wrapper.appendChild(style);

  buildSectionNodes(sections, 1, "", wrapper);

  return wrapper;
};

/**
 * 导出论文为 PDF 并触发浏览器下载
 * @param {string} paperTitle 论文标题
 * @param {Array} sections 章节树（treeData）
 * @returns {Promise<void>}
 */
export const exportPaperToPdf = async (paperTitle, sections) => {
  const wrapper = buildPaperHtml(paperTitle, sections);
  document.body.appendChild(wrapper);

  try {
    await html2pdf()
      .set({
        margin: [15, 15, 15, 15],
        filename: `${sanitizeFilename(paperTitle)}.pdf`,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        pagebreak: { mode: ["css", "legacy"] },
      })
      .from(wrapper)
      .save();
  } finally {
    document.body.removeChild(wrapper);
  }
};
