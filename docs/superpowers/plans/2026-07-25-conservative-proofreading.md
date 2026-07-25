# 《醒与悟》五册保守校稿实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 逐册纠正可由 PDF 原页确认的错字、OCR 误识别和排版问题，清除不必要空格并重建自然段，同时完整保留李牧之原作观点。

**Architecture:** 从 PDF 的文字坐标、段首缩进、行距和 OCR 结果重建段落结构，而非直接沿用固定版面换行。文字修订通过“原页—修改前—修改后”记录追踪；观点保护检查确保修订不引入内容删改。

**Tech Stack:** Python 3、PyMuPDF、RapidOCR、Markdown、GitBook、Git

---

### Task 1: 建立排版与校稿规则测试

**Files:**
- Create: `tests/test_proofreading.py`
- Create: `tools/proofreading.py`

- [ ] 测试删除中文字符之间的非语义空格。
- [ ] 测试删除中文标点前后的异常空格，同时保留英文词组空格。
- [ ] 测试连续版面行合并为自然段。
- [ ] 测试标题、页码注释、图片折叠块和 Markdown 结构不被合并。
- [ ] 测试问答、编号列表和新段首保持独立段落。

### Task 2: 校订第一、二、五册文本版

**Files:**
- Modify: `docs/book-1/*.md`
- Modify: `docs/book-2/*.md`
- Modify: `docs/book-5/*.md`
- Create: `build/proofreading-book-{1,2,5}.json`

- [ ] 根据 PDF 页面文字块和段首缩进重建自然段。
- [ ] 合并固定行宽与跨页造成的断句。
- [ ] 清除中文间、数字与量词间、标点附近的异常空格。
- [ ] 对照原页抽查标题、问答、列表、署名和日期。
- [ ] 记录所有文字级变更及原书页码。

### Task 3: 校订第三册扫描版

**Files:**
- Modify: `docs/book-3/*.md`
- Create: `build/proofreading-book-3.json`

- [ ] 用原页影像逐页复核 OCR 文本。
- [ ] 修正高置信度可确认的 OCR 错字和漏识别标点。
- [ ] 依据图像中的缩进和题号重建问答与自然段。
- [ ] 对无法确认的字保持现状并记录为待人工复核项，不猜测修改。

### Task 4: 校订第四册扫描文本层

**Files:**
- Modify: `docs/book-4/*.md`
- Create: `build/proofreading-book-4.json`

- [ ] 对照原页影像复核隐藏 OCR 文本层。
- [ ] 修正能够从原图确认的常见误识别字。
- [ ] 清除重复页眉页脚、孤立页码和错误断行。
- [ ] 维持 59 篇原有顺序和标题，原页影像继续保留。

### Task 5: 内容保护复核与校订说明

**Files:**
- Create: `docs/PROOFREADING.md`
- Modify: `docs/README.md`
- Modify: `docs/SUMMARY.md`
- Create: `build/proofreading-report.json`

- [ ] 注明作者李牧之及本次保守校订范围。
- [ ] 复核否定词、数字、人名、结论和语气未被排版算法改变。
- [ ] 汇总各册修订数量和待人工复核项。
- [ ] 将校订说明加入 GitBook 导航。

### Task 6: 全书验证、提交与推送

**Files:**
- Modify: repository working tree

- [ ] 验证 967 页页面标记和 307 张扫描原页影像仍完整。
- [ ] 验证全部 Markdown 链接和图片引用存在。
- [ ] 扫描连续中文间异常空格、孤立页码和明显断行残留。
- [ ] 运行全部测试和 `git diff --check`。
- [ ] 以 `cychai <chaichunyan@msn.com>` 提交并通过 SSH 推送 `main`。
- [ ] 确认远端 `main` 与本地 `HEAD` 一致。
