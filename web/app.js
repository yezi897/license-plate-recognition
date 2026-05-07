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

async function checkStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/status`);
        const data = await res.json();
        isConnected = data.serial_connected;
        updateStatusUI();
    } catch (e) {
        console.error('获取状态失败:', e);
    }
}

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

// ===== 实时预览流控制 =====
function startStream() {
    if (streaming) return;
    streaming = true;
    fpsCounter = 0;
    if (btnStreamToggle) btnStreamToggle.textContent = '暂停预览';
    if (fpsDisplay) fpsDisplay.textContent = 'FPS: --';
    fetchNextFrame();
    // FPS 计数器
    fpsTimer = setInterval(() => {
        if (fpsDisplay) fpsDisplay.textContent = `FPS: ${fpsCounter}`;
        fpsCounter = 0;
    }, 1000);
}

function stopStream() {
    streaming = false;
    if (streamTimer) {
        clearTimeout(streamTimer);
        streamTimer = null;
    }
    if (fpsTimer) {
        clearInterval(fpsTimer);
        fpsTimer = null;
    }
    if (btnStreamToggle) btnStreamToggle.textContent = '开始预览';
    if (fpsDisplay) fpsDisplay.textContent = 'FPS: --';
}

function toggleStream() {
    if (streaming) {
        stopStream();
    } else {
        startStream();
    }
}

async function fetchNextFrame() {
    if (!streaming || !isConnected) return;

    try {
        const res = await fetch(`${API_BASE}/api/stream/frame`);
        if (!res.ok) {
            // 连接断开或错误
            streamTimer = setTimeout(fetchNextFrame, 1000);
            return;
        }

        const blob = await res.blob();
        if (blob.size > 0) {
            // 释放旧的 object URL 防止内存泄漏
            if (videoStream.src && videoStream.src.startsWith('blob:')) {
                URL.revokeObjectURL(videoStream.src);
            }
            videoStream.src = URL.createObjectURL(blob);
            fpsCounter++;
        }
    } catch (e) {
        // 网络错误，稍后重试
    }

    if (streaming) {
        // 立即请求下一帧（串口驱动会控制实际速率）
        streamTimer = setTimeout(fetchNextFrame, 50);
    }
}

// ===== 连接控制 =====
async function toggleConnection() {
    if (isConnected) {
        stopStream();
        await fetch(`${API_BASE}/api/disconnect`, { method: 'POST' });
        isConnected = false;
        videoStream.src = '';
    } else {
        try {
            const res = await fetch(`${API_BASE}/api/connect`, { method: 'POST' });
            const data = await res.json();
            if (data.status === 'ok') {
                isConnected = true;
            } else {
                alert('连接失败: ' + data.message);
            }
        } catch (e) {
            alert('连接失败: ' + e.message);
        }
    }
    updateStatusUI();
}

// ===== 拍照识别 =====
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
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
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

// ===== 历史记录 =====
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

function changePage(delta) {
    currentPage += delta;
    loadHistory();
}

// ===== 自动识别 =====
function toggleAutoRecognize() {
    if (autoRecognize) {
        stopAutoRecognize();
    } else {
        startAutoRecognize();
    }
}

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

// ===== 配置管理 =====
async function loadConfig() {
    try {
        const res = await fetch(`${API_BASE}/api/config`);
        const config = await res.json();
        document.getElementById('input-port').value = config.serial_port || '';
        document.getElementById('input-baud').value = config.baud_rate || 115200;
        document.getElementById('input-app-id').value = config.baidu_app_id || '';
        document.getElementById('input-api-key').value = config.baidu_api_key || '';
        document.getElementById('input-secret-key').value = config.baidu_secret_key || '';
    } catch (e) {
        console.error('加载配置失败:', e);
    }
}

async function saveConfig() {
    const config = {
        serial_port: document.getElementById('input-port').value,
        baud_rate: parseInt(document.getElementById('input-baud').value),
        baidu_app_id: document.getElementById('input-app-id').value,
        baidu_api_key: document.getElementById('input-api-key').value,
        baidu_secret_key: document.getElementById('input-secret-key').value
    };

    try {
        const res = await fetch(`${API_BASE}/api/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const data = await res.json();
        if (data.status === 'ok') {
            settingsModal.classList.add('hidden');
            alert('配置已保存');
        }
    } catch (e) {
        alert('保存失败: ' + e.message);
    }
}
