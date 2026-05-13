# 前端重构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将车牌识别系统前端重构为简约白 + 侧边导航 + 科技蓝风格，带有精致的按钮动画效果。

**Architecture:** 保持现有三文件结构（index.html / style.css / app.js），不引入框架。CSS 通过自定义属性管理主题色，HTML 重构为侧边导航布局，JS 更新 DOM 操作匹配新结构。

**Tech Stack:** 原生 HTML + CSS + JavaScript，无第三方依赖。

---

### Task 1: CSS 变量与基础样式重置

**Files:**
- Modify: `web/style.css:1-11`

- [ ] **Step 1: 替换 CSS 文件开头，添加变量定义和重置样式**

将 `web/style.css` 的前 11 行替换为：

```css
:root {
  --color-primary: #2563eb;
  --color-primary-dark: #1d4ed8;
  --color-primary-light: #3b82f6;
  --color-primary-bg: #eff6ff;
  --color-success: #16a34a;
  --color-success-bg: #dcfce7;
  --color-danger: #ef4444;
  --color-danger-bg: #fef2f2;
  --color-text: #1e293b;
  --color-text-secondary: #64748b;
  --color-text-muted: #94a3b8;
  --color-bg: #f8fafc;
  --color-border: #e2e8f0;
  --color-border-hover: #cbd5e1;
  --color-card: #ffffff;
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 14px rgba(37,99,235,0.25);
  --shadow-lg: 0 8px 24px rgba(37,99,235,0.4);
  --sidebar-width: 64px;
  --transition-fast: 0.2s ease;
  --transition-normal: 0.25s ease;
  --transition-slow: 0.3s ease;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
}
```

- [ ] **Step 2: 在浏览器中打开页面，确认无报错**

在浏览器中打开 `web/index.html`，按 F12 检查 Console 无报错。页面样式会暂时错乱，这是正常的。

- [ ] **Step 3: 提交**

```bash
git add web/style.css
git commit -m "refactor: add CSS variables and reset base styles"
```

---

### Task 2: 动画关键帧

**Files:**
- Modify: `web/style.css`（在 body 规则之后添加）

- [ ] **Step 1: 添加所有动画关键帧**

在 `web/style.css` 的 `body` 规则之后添加：

```css
/* ===== 动画关键帧 ===== */
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(37,99,235,0.4), var(--shadow-md); }
  50% { box-shadow: 0 0 0 8px rgba(37,99,235,0), var(--shadow-md); }
}

@keyframes pulse-red {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4), 0 4px 14px rgba(239,68,68,0.25); }
  50% { box-shadow: 0 0 0 8px rgba(239,68,68,0), 0 4px 14px rgba(239,68,68,0.25); }
}

@keyframes shimmer {
  0% { left: -150%; }
  100% { left: 150%; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes progress {
  0% { width: 0%; }
  50% { width: 70%; }
  100% { width: 100%; }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
```

- [ ] **Step 2: 提交**

```bash
git add web/style.css
git commit -m "refactor: add animation keyframes for buttons"
```

---

### Task 3: 侧边导航栏样式

**Files:**
- Modify: `web/style.css`（在动画之后添加）

- [ ] **Step 1: 添加侧边导航栏样式**

在动画关键帧之后添加：

```css
/* ===== 侧边导航栏 ===== */
.app-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--color-card);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0;
  gap: 8px;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  z-index: 100;
}

.sidebar-logo {
  width: 36px;
  height: 36px;
  background: var(--color-primary);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 12px;
}

.nav-item {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--color-text-muted);
  background: transparent;
  border: none;
}

.nav-item:hover {
  background: var(--color-bg);
  color: var(--color-text-secondary);
}

.nav-item.active {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

.nav-item svg {
  width: 20px;
  height: 20px;
}

.nav-spacer {
  flex: 1;
}
```

- [ ] **Step 2: 提交**

```bash
git add web/style.css
git commit -m "refactor: add sidebar navigation styles"
```

---

### Task 4: 主内容区和顶部栏样式

**Files:**
- Modify: `web/style.css`（在侧边导航之后添加）

- [ ] **Step 1: 添加主内容区和顶部栏样式**

```css
/* ===== 主内容区 ===== */
.main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 24px;
  background: var(--color-card);
  border-bottom: 1px solid var(--color-border);
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.top-bar-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-badge {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.status-badge.connected {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.status-badge.disconnected {
  background: #fff2e8;
  color: #ea580c;
}

.fps-display {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: monospace;
}

.content-area {
  flex: 1;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}
```

- [ ] **Step 2: 提交**

```bash
git add web/style.css
git commit -m "refactor: add main content area and top bar styles"
```

---

### Task 5: 视频区和按钮样式

**Files:**
- Modify: `web/style.css`（在主内容区之后添加）

- [ ] **Step 1: 添加视频区和按钮样式**

```css
/* ===== 视频区 ===== */
.video-section {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 16px;
}

.video-wrapper {
  position: relative;
}

.video-container {
  width: 100%;
  height: 240px;
  background: #0f172a;
  border-radius: var(--radius-lg);
  overflow: hidden;
  position: relative;
}

.video-container img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.video-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--color-text-muted);
  font-size: 13px;
}

.video-overlay-tl {
  position: absolute;
  top: 10px;
  left: 10px;
  background: var(--color-danger);
  color: white;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 600;
}

.video-overlay-tr {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0,0,0,0.5);
  color: white;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 10px;
  font-family: monospace;
}

/* ===== 按钮 ===== */
.btn-group {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.btn {
  border: none;
  border-radius: var(--radius-md);
  padding: 12px 24px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
  letter-spacing: 0.3px;
}

.btn svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.btn:active {
  transform: translateY(1px);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* 主按钮 */
.btn-primary {
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary-light) 100%);
  color: white;
  box-shadow: var(--shadow-md);
  animation: pulse 2.5s ease-in-out infinite;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn-primary:hover:not(:disabled) .btn-shimmer {
  animation: shimmer 1.5s ease-in-out infinite;
}

.btn-shimmer {
  position: absolute;
  top: 0;
  left: -150%;
  width: 80%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
  transform: skewX(-25deg);
}

/* 次级按钮 */
.btn-secondary {
  background: var(--color-card);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.btn-secondary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  border-color: var(--color-border-hover);
  color: var(--color-text);
}

/* 图标按钮（暂停等） */
.btn-icon {
  background: var(--color-bg);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  padding: 12px 16px;
}

.btn-icon:hover:not(:disabled) {
  background: var(--color-card);
  border-color: var(--color-border-hover);
}

/* 停止按钮 */
.btn-danger {
  background: linear-gradient(135deg, #dc2626 0%, var(--color-danger) 100%);
  color: white;
  animation: pulse-red 2.5s ease-in-out infinite;
}

.btn-danger:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(239,68,68,0.4);
}

/* 加载状态 */
.btn-loading {
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary) 100%);
  color: rgba(255,255,255,0.8);
  cursor: wait;
  animation: none;
  box-shadow: 0 2px 8px rgba(37,99,235,0.15);
}

.btn-loading .btn-spinner {
  width: 16px;
  height: 16px;
  border: 2.5px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.btn-loading .btn-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: rgba(255,255,255,0.5);
  animation: progress 2s ease-in-out infinite;
}

/* 设置按钮 */
.btn-settings {
  background: var(--color-bg);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-settings:hover {
  background: var(--color-card);
  border-color: var(--color-border-hover);
}

/* 自动模式指示灯 */
.auto-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 8px;
}

.auto-dot {
  width: 8px;
  height: 8px;
  background: var(--color-success);
  border-radius: 50%;
  animation: blink 1.5s ease-in-out infinite;
}

.auto-label {
  font-size: 12px;
  color: var(--color-success);
  font-weight: 500;
}
```

- [ ] **Step 2: 提交**

```bash
git add web/style.css
git commit -m "refactor: add video section and button styles with animations"
```

---

### Task 6: 识别结果、统计卡片和历史表格样式

**Files:**
- Modify: `web/style.css`（在按钮之后添加）

- [ ] **Step 1: 添加右侧信息面板和表格样式**

```css
/* ===== 信息面板 ===== */
.info-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 识别结果卡片 */
.result-card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 16px;
  flex: 1;
}

.result-label {
  font-size: 11px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.plate-number {
  font-size: 28px;
  color: var(--color-primary);
  font-weight: 700;
  font-family: monospace;
  letter-spacing: 2px;
}

.result-meta {
  display: flex;
  gap: 16px;
  margin-top: 10px;
}

.meta-item {
  display: flex;
  flex-direction: column;
}

.meta-label {
  font-size: 10px;
  color: var(--color-text-muted);
}

.meta-value {
  font-size: 13px;
  color: var(--color-text);
  font-weight: 500;
}

.meta-value.success {
  color: var(--color-success);
}

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 14px;
}

.stat-label {
  font-size: 10px;
  color: var(--color-text-muted);
}

.stat-value {
  font-size: 22px;
  color: var(--color-text);
  font-weight: 700;
}

.stat-value.success {
  color: var(--color-success);
}

/* 结果占位符 */
.result-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80px;
  color: var(--color-text-muted);
  font-size: 13px;
}

/* ===== 历史表格 ===== */
.history-card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-bg);
}

.history-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
}

.history-count {
  font-size: 11px;
  color: var(--color-text-muted);
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.history-table thead {
  background: var(--color-bg);
}

.history-table th {
  padding: 10px 16px;
  text-align: left;
  color: var(--color-text-secondary);
  font-weight: 500;
  font-size: 11px;
}

.history-table td {
  padding: 10px 16px;
  border-bottom: 1px solid #f1f5f9;
}

.history-table .col-plate {
  color: var(--color-primary);
  font-weight: 600;
  font-family: monospace;
}

.history-table .col-confidence {
  color: var(--color-success);
}

.history-table .col-time {
  color: var(--color-text-muted);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-top: 1px solid var(--color-bg);
}

.pagination span {
  font-size: 11px;
  color: var(--color-text-muted);
  cursor: pointer;
}

.pagination .page-info {
  color: var(--color-text);
  font-weight: 500;
  cursor: default;
}
```

- [ ] **Step 2: 提交**

```bash
git add web/style.css
git commit -m "refactor: add result cards, stats, and history table styles"
```

---

### Task 7: 设置弹窗样式

**Files:**
- Modify: `web/style.css`（在历史表格之后添加）

- [ ] **Step 1: 添加设置弹窗样式**

```css
/* ===== 设置弹窗 ===== */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal.hidden {
  display: none;
}

.modal-content {
  background: var(--color-card);
  border-radius: var(--radius-lg);
  width: 450px;
  max-width: 90%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--color-border);
}

.modal-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.btn-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--color-text-muted);
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.btn-close:hover {
  background: var(--color-bg);
  color: var(--color-text);
}

.modal-body {
  padding: 20px;
}

.modal-body hr {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 16px 0;
}

.modal-body h3 {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text);
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  transition: all var(--transition-fast);
  background: var(--color-card);
  color: var(--color-text);
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}

.form-group input::placeholder {
  color: var(--color-text-muted);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-border);
}

.modal-footer .btn-primary {
  animation: none;
  padding: 8px 20px;
  font-size: 13px;
}

.modal-footer .btn-secondary {
  padding: 8px 20px;
  font-size: 13px;
}
```

- [ ] **Step 2: 删除旧的冗余样式**

删除 `web/style.css` 中以下已废弃的样式规则（如果有）：
- `.container`
- `header`
- `header h1`
- `.header-actions`
- `main`
- `.panel`
- `.panel h2`
- `.panel-header`
- `.panel-header h2`
- `.fps-badge`
- `.btn-primary:hover:not(:disabled)` 等旧按钮样式
- `.btn-success`
- `.btn-danger`
- `.btn-small`
- `.side-panels`
- `.result-content`
- `.result-item`
- `.result-item .plate-number`
- `.result-item .plate-info`
- `.table-container`
- `table`
- `th, td`

保留所有新添加的样式。

- [ ] **Step 3: 提交**

```bash
git add web/style.css
git commit -m "refactor: add modal styles and remove old CSS rules"
```

---

### Task 8: 重构 HTML 结构

**Files:**
- Modify: `web/index.html`（完全重写）

- [ ] **Step 1: 重写 index.html**

用以下内容替换整个 `web/index.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>车牌识别系统</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="app-layout">
    <!-- 侧边导航栏 -->
    <nav class="sidebar">
      <div class="sidebar-logo">L</div>
      <button class="nav-item active" data-page="monitor" title="实时监控">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>
      </button>
      <button class="nav-item" data-page="history" title="识别历史">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      </button>
      <div class="nav-spacer"></div>
      <button class="nav-item" data-page="settings" title="设置">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
      </button>
    </nav>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 顶部栏 -->
      <div class="top-bar">
        <div class="top-bar-left">
          <h1 class="top-bar-title">实时监控</h1>
          <span id="status-indicator" class="status-badge disconnected">未连接</span>
        </div>
        <div class="top-bar-right">
          <span id="fps-display" class="fps-display">FPS: --</span>
          <button id="btn-settings" class="btn-settings">设置</button>
        </div>
      </div>

      <!-- 内容区 -->
      <div class="content-area">
        <!-- 视频 + 信息 -->
        <div class="video-section">
          <!-- 视频区 -->
          <div class="video-wrapper">
            <div class="video-container">
              <img id="video-stream" src="" alt="视频流">
              <div id="video-placeholder" class="video-placeholder">请先连接串口设备</div>
              <div class="video-overlay-tl" id="live-badge" style="display:none;">LIVE</div>
              <div class="video-overlay-tr" id="resolution-badge" style="display:none;">1280x720</div>
            </div>
            <div class="btn-group">
              <button id="btn-connect" class="btn btn-primary">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>
                <span>连接设备</span>
                <div class="btn-shimmer"></div>
              </button>
              <button id="btn-capture" class="btn btn-primary" disabled>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>
                <span>拍照识别</span>
                <div class="btn-shimmer"></div>
              </button>
              <button id="btn-auto" class="btn btn-secondary" disabled>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
                <span>自动识别</span>
              </button>
              <button id="btn-stream-toggle" class="btn btn-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
              </button>
              <div class="auto-indicator" id="auto-indicator" style="display:none;">
                <div class="auto-dot"></div>
                <span class="auto-label">自动识别中</span>
              </div>
            </div>
          </div>

          <!-- 信息面板 -->
          <div class="info-panel">
            <div class="result-card">
              <div class="result-label">识别结果</div>
              <div id="result-content">
                <div class="result-placeholder">等待识别...</div>
              </div>
            </div>
            <div class="stats-row">
              <div class="stat-card">
                <div class="stat-label">今日识别</div>
                <div id="stat-today" class="stat-value">0</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">平均置信度</div>
                <div id="stat-confidence" class="stat-value success">--</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 历史记录 -->
        <div class="history-card">
          <div class="history-header">
            <span class="history-title">识别历史</span>
            <span id="history-count" class="history-count"></span>
          </div>
          <table class="history-table">
            <thead>
              <tr>
                <th>车牌号</th>
                <th>颜色</th>
                <th>置信度</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody id="history-body"></tbody>
          </table>
          <div class="pagination">
            <span id="btn-prev">上一页</span>
            <span id="page-info" class="page-info">第 1 页</span>
            <span id="btn-next">下一页</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 设置弹窗 -->
  <div id="settings-modal" class="modal hidden">
    <div class="modal-content">
      <div class="modal-header">
        <h2>系统设置</h2>
        <button id="btn-close-modal" class="btn-close">&times;</button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label>串口端口</label>
          <input type="text" id="input-port" placeholder="COM3">
        </div>
        <div class="form-group">
          <label>波特率</label>
          <input type="number" id="input-baud" value="115200">
        </div>
        <hr>
        <h3>百度云 API 配置</h3>
        <div class="form-group">
          <label>App ID</label>
          <input type="text" id="input-app-id" placeholder="百度云 App ID">
        </div>
        <div class="form-group">
          <label>API Key</label>
          <input type="text" id="input-api-key" placeholder="百度云 API Key">
        </div>
        <div class="form-group">
          <label>Secret Key</label>
          <input type="password" id="input-secret-key" placeholder="百度云 Secret Key">
        </div>
      </div>
      <div class="modal-footer">
        <button id="btn-save-config" class="btn btn-primary">保存</button>
        <button id="btn-cancel-config" class="btn btn-secondary">取消</button>
      </div>
    </div>
  </div>

  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: 在浏览器中打开页面，确认布局正确**

侧边导航栏应出现在左侧，主内容区在右侧。样式可能还不完美，但结构应该正确。

- [ ] **Step 3: 提交**

```bash
git add web/index.html
git commit -m "refactor: rewrite HTML with sidebar navigation layout"
```

---

### Task 9: 更新 JavaScript — DOM 引用和事件绑定

**Files:**
- Modify: `web/app.js:1-57`

- [ ] **Step 1: 更新 DOM 引用和事件绑定**

将 `web/app.js` 的第 1-57 行替换为：

```javascript
const API_BASE = '';

// 状态
let currentPage = 1;
let isConnected = false;
let streaming = false;
let streamTimer = null;
let fpsCounter = 0;
let fpsTimer = null;
let lastFrameTime = 0;
let autoRecognize = false;
let autoTimer = null;

// DOM 元素
const statusIndicator = document.getElementById('status-indicator');
const btnConnect = document.getElementById('btn-connect');
const btnCapture = document.getElementById('btn-capture');
const btnSettings = document.getElementById('btn-settings');
const videoStream = document.getElementById('video-stream');
const videoPlaceholder = document.getElementById('video-placeholder');
const resultContent = document.getElementById('result-content');
const historyBody = document.getElementById('history-body');
const btnPrev = document.getElementById('btn-prev');
const btnNext = document.getElementById('btn-next');
const pageInfo = document.getElementById('page-info');
const settingsModal = document.getElementById('settings-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const btnSaveConfig = document.getElementById('btn-save-config');
const btnCancelConfig = document.getElementById('btn-cancel-config');
const fpsDisplay = document.getElementById('fps-display');
const btnStreamToggle = document.getElementById('btn-stream-toggle');
const btnAuto = document.getElementById('btn-auto');
const liveBadge = document.getElementById('live-badge');
const autoIndicator = document.getElementById('auto-indicator');
const historyCount = document.getElementById('history-count');
const statToday = document.getElementById('stat-today');
const statConfidence = document.getElementById('stat-confidence');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
  checkStatus();
  loadHistory();
  loadConfig();
  bindEvents();
});

function bindEvents() {
  btnConnect.addEventListener('click', toggleConnection);
  btnCapture.addEventListener('click', captureAndRecognize);
  btnSettings.addEventListener('click', () => settingsModal.classList.remove('hidden'));
  btnCloseModal.addEventListener('click', () => settingsModal.classList.add('hidden'));
  btnCancelConfig.addEventListener('click', () => settingsModal.classList.add('hidden'));
  btnSaveConfig.addEventListener('click', saveConfig);
  btnPrev.addEventListener('click', () => changePage(-1));
  btnNext.addEventListener('click', () => changePage(1));
  if (btnStreamToggle) {
    btnStreamToggle.addEventListener('click', toggleStream);
  }
  if (btnAuto) {
    btnAuto.addEventListener('click', toggleAutoRecognize);
  }

  // 侧边导航
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      if (item.dataset.page === 'settings') {
        settingsModal.classList.remove('hidden');
      }
    });
  });
}
```

- [ ] **Step 2: 提交**

```bash
git add web/app.js
git commit -m "refactor: update DOM references for new HTML structure"
```

---

### Task 10: 更新 JavaScript — 连接状态和视频流

**Files:**
- Modify: `web/app.js`（`updateStatusUI` 函数）

- [ ] **Step 1: 替换 updateStatusUI 函数**

找到 `function updateStatusUI()` 及其内容，替换为：

```javascript
function updateStatusUI() {
  if (isConnected) {
    statusIndicator.textContent = '已连接';
    statusIndicator.className = 'status-badge connected';
    btnConnect.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
      <span>断开连接</span>
      <div class="btn-shimmer"></div>
    `;
    btnCapture.disabled = false;
    btnAuto.disabled = false;
    videoPlaceholder.style.display = 'none';
    if (liveBadge) liveBadge.style.display = 'block';
    startStream();
  } else {
    statusIndicator.textContent = '未连接';
    statusIndicator.className = 'status-badge disconnected';
    btnConnect.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>
      <span>连接设备</span>
      <div class="btn-shimmer"></div>
    `;
    btnCapture.disabled = true;
    btnAuto.disabled = true;
    videoPlaceholder.style.display = 'block';
    if (liveBadge) liveBadge.style.display = 'none';
    stopAutoRecognize();
    stopStream();
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add web/app.js
git commit -m "refactor: update status UI for new button structure"
```

---

### Task 11: 更新 JavaScript — 拍照识别

**Files:**
- Modify: `web/app.js`（`captureAndRecognize` 函数）

- [ ] **Step 1: 替换 captureAndRecognize 函数**

找到 `async function captureAndRecognize()` 及其内容，替换为：

```javascript
async function captureAndRecognize() {
  const wasStreaming = streaming;
  stopStream();

  btnCapture.disabled = true;
  btnCapture.className = 'btn btn-loading';
  btnCapture.innerHTML = `
    <div class="btn-spinner"></div>
    <span>识别中...</span>
    <div class="btn-progress"></div>
  `;
  btnAuto.disabled = true;
  resultContent.innerHTML = '<div class="result-placeholder">正在识别...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/capture`, { method: 'POST' });
    const data = await res.json();

    if (data.status === 'ok' && data.result) {
      showResult(data.result);
      loadHistory();
    } else if (data.image) {
      resultContent.innerHTML = `<div class="result-placeholder">${data.message || '未识别到车牌'}</div>`;
    } else {
      resultContent.innerHTML = `<div class="result-placeholder">${data.message || '识别失败'}</div>`;
    }
  } catch (e) {
    resultContent.innerHTML = `<div class="result-placeholder">识别出错: ${e.message}</div>`;
  }

  btnCapture.disabled = false;
  btnCapture.className = 'btn btn-primary';
  btnCapture.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>
    <span>拍照识别</span>
    <div class="btn-shimmer"></div>
  `;
  btnAuto.disabled = false;

  if (wasStreaming && isConnected) {
    startStream();
  }
}

function showResult(result) {
  resultContent.innerHTML = `
    <div class="plate-number">${result.plate_number}</div>
    <div class="result-meta">
      <div class="meta-item">
        <span class="meta-label">颜色</span>
        <span class="meta-value">${result.color}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">置信度</span>
        <span class="meta-value success">${result.confidence}%</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">时间</span>
        <span class="meta-value">${new Date().toLocaleTimeString('zh-CN')}</span>
      </div>
    </div>
  `;
}
```

- [ ] **Step 2: 提交**

```bash
git add web/app.js
git commit -m "refactor: update capture and result display for new UI"
```

---

### Task 12: 更新 JavaScript — 自动识别

**Files:**
- Modify: `web/app.js`（`startAutoRecognize` 和 `stopAutoRecognize` 函数）

- [ ] **Step 1: 替换自动识别函数**

找到 `function startAutoRecognize()` 和 `function stopAutoRecognize()`，替换为：

```javascript
function startAutoRecognize() {
  autoRecognize = true;
  btnAuto.className = 'btn btn-danger';
  btnAuto.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
    <span>停止识别</span>
  `;
  btnCapture.disabled = true;
  if (autoIndicator) autoIndicator.style.display = 'flex';
  autoRecognizeOnce();
}

function stopAutoRecognize() {
  autoRecognize = false;
  if (autoTimer) {
    clearTimeout(autoTimer);
    autoTimer = null;
  }
  btnAuto.className = 'btn btn-secondary';
  btnAuto.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
    <span>自动识别</span>
  `;
  btnCapture.disabled = false;
  if (autoIndicator) autoIndicator.style.display = 'none';
}
```

- [ ] **Step 2: 更新 autoRecognizeOnce 中的结果显示**

找到 `autoRecognizeOnce` 函数中的 `resultContent.innerHTML = ...` 部分，替换为使用 `showResult`：

```javascript
async function autoRecognizeOnce() {
  if (!autoRecognize || !isConnected) {
    stopAutoRecognize();
    return;
  }

  const wasStreaming = streaming;
  stopStream();

  try {
    const res = await fetch(`${API_BASE}/api/stream/recognize`);
    const data = await res.json();

    if (data.status === 'ok' && data.result) {
      showResult(data.result);
      loadHistory();
    }
  } catch (e) {
    // 网络错误，继续重试
  }

  if (autoRecognize && isConnected) {
    if (wasStreaming) startStream();
    autoTimer = setTimeout(autoRecognizeOnce, 3000);
  }
}
```

- [ ] **Step 3: 提交**

```bash
git add web/app.js
git commit -m "refactor: update auto recognize with new button states"
```

---

### Task 13: 更新 JavaScript — 历史记录和统计

**Files:**
- Modify: `web/app.js`（`loadHistory` 函数）

- [ ] **Step 1: 替换 loadHistory 函数**

找到 `async function loadHistory()` 及其内容，替换为：

```javascript
async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/history?page=${currentPage}&per_page=10`);
    const data = await res.json();

    historyBody.innerHTML = '';
    data.records.forEach(record => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td class="col-plate">${record.plate_number}</td>
        <td>${record.color}</td>
        <td class="col-confidence">${record.confidence}%</td>
        <td class="col-time">${new Date(record.created_at).toLocaleString('zh-CN')}</td>
      `;
      historyBody.appendChild(row);
    });

    const totalPages = Math.ceil(data.total / data.per_page);
    pageInfo.textContent = `第 ${currentPage} 页 / 共 ${totalPages} 页`;
    btnPrev.style.opacity = currentPage <= 1 ? '0.4' : '1';
    btnPrev.style.pointerEvents = currentPage <= 1 ? 'none' : 'auto';
    btnNext.style.opacity = currentPage >= totalPages ? '0.4' : '1';
    btnNext.style.pointerEvents = currentPage >= totalPages ? 'none' : 'auto';

    if (historyCount) {
      historyCount.textContent = `共 ${data.total} 条记录`;
    }

    // 更新统计
    if (statToday) {
      statToday.textContent = data.total || 0;
    }
    if (statConfidence && data.records.length > 0) {
      const avg = data.records.reduce((sum, r) => sum + r.confidence, 0) / data.records.length;
      statConfidence.textContent = avg.toFixed(1) + '%';
    }
  } catch (e) {
    console.error('加载历史记录失败:', e);
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add web/app.js
git commit -m "refactor: update history display with stats and new table styles"
```

---

### Task 14: 最终验证和清理

**Files:**
- None (verification only)

- [ ] **Step 1: 在浏览器中完整测试**

打开 `web/index.html`，检查：
1. 侧边导航栏显示正确，Logo 为蓝色方块
2. 顶部栏显示标题和状态
3. 视频区显示占位符
4. 按钮样式正确（渐变蓝 + 图标）
5. 识别结果区显示"等待识别..."
6. 统计卡片显示 0 和 --
7. 历史表格为空但结构正确
8. 点击设置按钮弹出弹窗
9. 弹窗表单输入框聚焦时有蓝色边框

- [ ] **Step 2: 检查 Console 无报错**

按 F12 打开开发者工具，确认 Console 中无 JavaScript 错误。

- [ ] **Step 3: 提交最终状态**

```bash
git add -A
git commit -m "refactor: complete frontend redesign with sidebar navigation and button animations"
```
