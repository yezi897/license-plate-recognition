const API_BASE = '';

// 状态
let currentPage = 1;
let isConnected = false;

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
        statusIndicator.className = 'status connected';
        btnConnect.textContent = '断开连接';
        btnCapture.disabled = false;
        videoPlaceholder.style.display = 'none';
        videoStream.src = `${API_BASE}/api/stream`;
    } else {
        statusIndicator.textContent = '未连接';
        statusIndicator.className = 'status disconnected';
        btnConnect.textContent = '连接设备';
        btnCapture.disabled = true;
        videoStream.src = '';
        videoPlaceholder.style.display = 'block';
    }
}

async function toggleConnection() {
    if (isConnected) {
        await fetch(`${API_BASE}/api/disconnect`, { method: 'POST' });
        isConnected = false;
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

async function captureAndRecognize() {
    btnCapture.disabled = true;
    btnCapture.textContent = '识别中...';
    resultContent.innerHTML = '<p class="placeholder">正在识别...</p>';

    try {
        const res = await fetch(`${API_BASE}/api/capture`, { method: 'POST' });
        const data = await res.json();

        if (data.status === 'ok' && data.result) {
            resultContent.innerHTML = `
                <div class="result-item">
                    <div class="plate-number">${data.result.plate_number}</div>
                    <div class="plate-info">
                        <p>颜色: ${data.result.color}</p>
                        <p>置信度: ${data.result.confidence}%</p>
                    </div>
                </div>
            `;
            loadHistory();
        } else if (data.image) {
            resultContent.innerHTML = `
                <div class="result-item">
                    <p class="placeholder">${data.message || '未识别到车牌'}</p>
                </div>
            `;
        } else {
            resultContent.innerHTML = `<p class="placeholder">${data.message || '识别失败'}</p>`;
        }
    } catch (e) {
        resultContent.innerHTML = `<p class="placeholder">识别出错: ${e.message}</p>`;
    }

    btnCapture.disabled = false;
    btnCapture.textContent = '📸 拍照识别';
}

async function loadHistory() {
    try {
        const res = await fetch(`${API_BASE}/api/history?page=${currentPage}&per_page=10`);
        const data = await res.json();

        historyBody.innerHTML = '';
        data.records.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.plate_number}</td>
                <td>${record.color}</td>
                <td>${record.confidence}%</td>
                <td>${new Date(record.created_at).toLocaleString('zh-CN')}</td>
            `;
            historyBody.appendChild(row);
        });

        const totalPages = Math.ceil(data.total / data.per_page);
        pageInfo.textContent = `第 ${currentPage} 页 / 共 ${totalPages} 页`;
        btnPrev.disabled = currentPage <= 1;
        btnNext.disabled = currentPage >= totalPages;
    } catch (e) {
        console.error('加载历史记录失败:', e);
    }
}

function changePage(delta) {
    currentPage += delta;
    loadHistory();
}

async function loadConfig() {
    try {
        const res = await fetch(`${API_BASE}/api/config`);
        const config = await res.json();
        document.getElementById('input-port').value = config.serial_port || '';
        document.getElementById('input-baud').value = config.baud_rate || 921600;
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
