# 《醒与悟》五册 PDF 转 GitBook 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将五册 PDF 的全量原文整理为可由 GitBook 直接读取的中文书稿，在不改写、不概括、不删减正文的前提下，只调整目录、标题层级、段落、列表、图片引用和页面导航。

**Architecture:** 先逐页提取带坐标、字号和字体信息的文本块与图片，再依据原始目录、字号层级和分页结构生成每册独立 Markdown 章节。保留逐页原始文本快照作为核验基准，通过规范化字符比对、章节链接检查和图片引用检查验证内容完整性。

**Tech Stack:** Python 3、PyMuPDF、Markdown、GitBook、Git

---

### Task 1: 审计 PDF 输入

**Files:**
- Read: `/Users/bytedance/Downloads/醒与悟 5 册/1.pdf`
- Read: `/Users/bytedance/Downloads/醒与悟 5 册/2.pdf`
- Read: `/Users/bytedance/Downloads/醒与悟 5 册/3.pdf`
- Read: `/Users/bytedance/Downloads/醒与悟 5 册/4.pdf`
- Read: `/Users/bytedance/Downloads/醒与悟 5 册/5.pdf`
- Create: `tools/pdf_audit.py`
- Create: `build/audit.json`

- [ ] 创建隔离的 Python 虚拟环境并安装 PyMuPDF。
- [ ] 逐册记录页数、元数据、每页字符数、字体层级、图片数和书签目录。
- [ ] 标记无文本页、疑似扫描页、重复页眉页脚和页码模式。
- [ ] 将审计结果写入 `build/audit.json`，不提交临时构建目录。

### Task 2: 建立保真提取器

**Files:**
- Create: `tools/extract_book.py`
- Create: `tools/text_fidelity.py`
- Create: `.gitignore`
- Create: `source-text/book-1.txt`
- Create: `source-text/book-2.txt`
- Create: `source-text/book-3.txt`
- Create: `source-text/book-4.txt`
- Create: `source-text/book-5.txt`

- [ ] 按 PDF 阅读顺序提取每页文字，保留完整正文和原始标点。
- [ ] 将每册逐页文本快照写入 `source-text/`，用明确分页标记隔开，作为校对依据。
- [ ] 基于字体大小、粗细、原始书签和短行特征识别标题，仅添加 Markdown 标记，不改动标题文字。
- [ ] 识别连续正文段落、列表和独立引文，只改变空行与 Markdown 语法。
- [ ] 提取正文图片到 `docs/.gitbook/assets/book-N/`，按原页顺序引用。

### Task 3: 生成五册 GitBook 书稿

**Files:**
- Modify: `docs/README.md`
- Modify: `docs/SUMMARY.md`
- Create: `docs/book-1/README.md`
- Create: `docs/book-2/README.md`
- Create: `docs/book-3/README.md`
- Create: `docs/book-4/README.md`
- Create: `docs/book-5/README.md`
- Create: `docs/book-N/*.md`

- [ ] 每册建立卷首页，保留 PDF 中的原始书名、署名、序言和目录内容。
- [ ] 以原始一级篇章为文件边界；篇章过长时按原始二级标题继续拆分。
- [ ] 生成五册及其章节的 GitBook 导航，章节顺序与原稿一致。
- [ ] 统一中文排版：标题前后空行、自然段空行、列表缩进、图片独占一行。
- [ ] 不添加原稿中不存在的正文、摘要、解释或编者按。

### Task 4: 内容完整性与结构验证

**Files:**
- Create: `tools/verify_books.py`
- Create: `build/verification.json`

- [ ] 比较 PDF 原始提取文本与 GitBook 正文的规范化字符序列，仅忽略空白、Markdown 标记和分页标记。
- [ ] 对无法一一匹配的字符差异输出具体册、页码、上下文，逐项修复。
- [ ] 检查 `SUMMARY.md` 的全部相对链接存在且大小写一致。
- [ ] 检查全部本地图片引用存在、无孤立资源。
- [ ] 检查 Markdown 标题层级无跳级，代码围栏和表格语法闭合。
- [ ] 最终验证要求：五册均无缺页，正文字符比对无未解释差异，链接与图片检查零错误。

### Task 5: 提交与推送

**Files:**
- Modify: repository working tree

- [ ] 确认仓库本地身份为 `cychai <chaichunyan@msn.com>`。
- [ ] 运行 `git diff --check`，确认无空白错误。
- [ ] 提交书稿、资源、核验脚本和必要的原文快照。
- [ ] 使用仓库配置的 `~/.ssh/id_rsa` 推送到 `origin/main`。
- [ ] 比对本地 `HEAD` 与远端 `refs/heads/main` 一致。
