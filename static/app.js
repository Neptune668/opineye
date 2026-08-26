// ===== 状态与常量 =====
const API_BASE = '/api';
const TOKEN_KEY = 'opineye_token';
const USER_KEY = 'opineye_user';

// 角色中文名
const ROLE_LABELS = {
  admin: '系统管理员',
  operator: '操作用户',
  viewer: '报告查看人',
};

// 每种角色可见的页面（data-page 值）
const ROLE_PAGES = {
  // 系统管理员：全部页面
  admin: ['console', 'search', 'forum', 'graph', 'config', 'system'],
  // 操作用户：控制台 + 检索 + 论坛 + 图谱（无配置、无系统状态）
  operator: ['console', 'search', 'forum', 'graph'],
  // 报告查看人：图谱 + 论坛（只读）+ 控制台（只读状态）
  viewer: ['console', 'graph', 'forum'],
};

let currentUser = null;

// ===== 用户信息存取 =====
function getToken() {
  return localStorage.getItem(TOKEN_KEY) || '';
}
function saveUser(data) {
  currentUser = data;
  localStorage.setItem(USER_KEY, JSON.stringify(data));
  localStorage.setItem(TOKEN_KEY, data.token);
}
function clearUser() {
  currentUser = null;
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(TOKEN_KEY);
}
function loadUserFromStorage() {
  const raw = localStorage.getItem(USER_KEY);
  if (raw) {
    try { currentUser = JSON.parse(raw); } catch (e) { currentUser = null; }
  }
}

// ===== API 封装（携带 Authorization 头）=====
async function request(method, path, body) {
  let r;
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = 'Bearer ' + token;
  try {
    r = await fetch(API_BASE + path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (e) {
    throw new Error('无法连接服务器，请检查服务是否启动');
  }
  // 401：登录失效，跳回登录页
  if (r.status === 401) {
    clearUser();
    showLogin();
    throw new Error('登录已失效，请重新登录');
  }
  const data = await r.json().catch(() => ({}));
  if (data.code !== 0) {
    throw new Error(data.message || `请求失败（code=${data.code}）`);
  }
  return data;
}

function apiGet(path) {
  return request('GET', path);
}
function apiPost(path, body) {
  return request('POST', path, body || {});
}

function showError(msg) {
  alert(msg);
}

// ===== 工具 =====
const $ = (sel) => document.querySelector(sel);

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

// ===== 登录 / 登出 =====
function showLogin() {
  $('#app').classList.add('hidden');
  $('#login-screen').classList.remove('hidden');
}

function showApp() {
  $('#login-screen').classList.add('hidden');
  $('#app').classList.remove('hidden');
}

// 登录 / 注册 tab 切换
document.querySelectorAll('.login-tab').forEach((tab) => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.login-tab').forEach((t) => t.classList.remove('active'));
    tab.classList.add('active');
    const isLogin = tab.dataset.tab === 'login';
    $('#login-form').classList.toggle('hidden', !isLogin);
    $('#register-form').classList.toggle('hidden', isLogin);
    $('#login-error').textContent = '';
  });
});

function setLoginError(msg) {
  $('#login-error').textContent = msg;
}

$('#btn-login').addEventListener('click', async () => {
  const username = $('#login-username').value.trim();
  const password = $('#login-password').value;
  if (!username || !password) { setLoginError('请输入用户名和密码'); return; }
  try {
    const res = await apiPost('/login', { username, password });
    saveUser(res.data);
    setLoginError('');
    enterApp();
  } catch (e) {
    setLoginError(e.message);
  }
});

$('#btn-register').addEventListener('click', async () => {
  const username = $('#reg-username').value.trim();
  const password = $('#reg-password').value;
  const role = $('#reg-role').value;
  if (!username || !password) { setLoginError('请输入用户名和密码'); return; }
  try {
    const res = await apiPost('/register', { username, password, role });
    // 注册成功后自动登录
    const loginRes = await apiPost('/login', { username, password });
    saveUser(loginRes.data);
    setLoginError('');
    enterApp();
  } catch (e) {
    setLoginError(e.message);
  }
});

// 回车触发登录
$('#login-password').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') $('#btn-login').click();
});
$('#reg-password').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') $('#btn-register').click();
});

$('#btn-logout').addEventListener('click', () => {
  clearUser();
  stopWs();
  showLogin();
  // 重置登录表单
  $('#login-username').value = '';
  $('#login-password').value = '';
});

// ===== 进入应用：按角色渲染菜单 =====
function enterApp() {
  const role = currentUser.role;
  $('#user-name').textContent = currentUser.username;
  $('#user-role').textContent = ROLE_LABELS[role] || role;

  // 渲染导航：仅显示该角色可见的页面
  const allowedPages = ROLE_PAGES[role] || ROLE_PAGES.viewer;
  document.querySelectorAll('.nav-item').forEach((item) => {
    const page = item.dataset.page;
    if (allowedPages.includes(page)) {
      item.style.display = '';
    } else {
      item.style.display = 'none';
    }
  });

  showApp();

  // 默认进入第一个可见页面
  const firstPage = allowedPages[0] || 'console';
  showPage(firstPage);

  initWs();
}

// ===== 页面导航 =====
function showPage(page) {
  document.querySelectorAll('.nav-item').forEach((n) => {
    n.classList.toggle('active', n.dataset.page === page);
  });
  document.querySelectorAll('.page').forEach((p) => p.classList.remove('active'));
  $('#page-' + page).classList.add('active');
  // 进入页面时刷新数据
  if (page === 'console' || page === 'system') { loadStatus(); loadSystemStatus(); }
  if (page === 'forum') loadForumLog();
  if (page === 'graph') { /* 由用户手动加载 */ }
}

document.querySelectorAll('.nav-item').forEach((item) => {
  item.addEventListener('click', () => showPage(item.dataset.page));
});

// ===== 控制台首页 =====
async function loadStatus() {
  const res = await apiGet('/status');
  const apps = res.data || {};
  const cards = $('#app-cards');
  const labels = {
    topic_search: '主题检索', media_search: '多媒体检索', forum_collect: '论坛采集',
    insight: '洞察分析', report: '报告生成', graph: '图谱查询',
  };
  // operator 及以上可启停应用；viewer 只读
  const canOperate = currentUser && currentUser.role !== 'viewer';
  cards.innerHTML = Object.entries(apps).map(([name, app]) => `
    <div class="card">
      <div class="card-header">
        <span class="card-title">${labels[name] || name}</span>
        <span class="status-badge status-${app.status}">${app.status}</span>
      </div>
      <div class="card-actions">
        ${canOperate ? `
          <button class="btn primary" onclick="startApp('${name}')">启动</button>
          <button class="btn danger" onclick="stopApp('${name}')">停止</button>
        ` : ''}
        <button class="btn" onclick="viewOutput('${name}')">输出</button>
        <button class="btn" onclick="viewTestLog('${name}')">测试日志</button>
      </div>
    </div>
  `).join('');
}

async function startApp(name) {
  try {
    await apiGet(`/start/${name}`);
    loadStatus();
  } catch (e) { showError(e.message); }
}
async function stopApp(name) {
  try {
    await apiGet(`/stop/${name}`);
    loadStatus();
  } catch (e) { showError(e.message); }
}
function showAppOutput(title, content) {
  $('#output-title').textContent = title;
  const view = $('#app-output-view');
  view.textContent = content || '(空)';
  view.scrollTop = view.scrollHeight;
}

async function viewOutput(name) {
  try {
    const res = await apiGet(`/output/${name}`);
    showAppOutput(`【${name}】输出`, res.data?.output_text || '(空)');
  } catch (e) { showError(e.message); }
}
async function viewTestLog(name) {
  try {
    const res = await apiGet(`/test_log/${name}`);
    const lines = res.data?.lines || [];
    showAppOutput(`【${name}】测试日志（末尾 ${lines.length} 行）`, lines.join('\n') || '(空)');
  } catch (e) { showError(e.message); }
}

// ===== 主题检索 =====
$('#btn-search').addEventListener('click', async () => {
  const query = $('#search-query').value.trim();
  const sources = Array.from($('#search-sources').selectedOptions).map((o) => o.value);
  if (!query) { alert('请输入主题词'); return; }
  let res;
  try {
    res = await apiPost('/search', { query, source_types: sources });
  } catch (e) {
    $('#search-result').innerHTML = `<div class="empty">检索失败：${escapeHtml(e.message)}</div>`;
    return;
  }
  const d = res.data;
  if (!d) { $('#search-result').innerHTML = `<div class="empty">检索失败：${escapeHtml(res.message)}</div>`; return; }

  const a = d.analysis;
  const senti = a.sentiment;
  $('#search-result').innerHTML = `
    <h3>检索结果</h3>
    <p><b>task_id：</b>${escapeHtml(d.task_id)}　<b>report_id：</b>${escapeHtml(d.report.report_id)}</p>
    <div class="stat-grid">
      <div class="stat-item"><div class="stat-label">情绪倾向</div><div class="stat-value">${escapeHtml(senti.overall)}</div></div>
      <div class="stat-item"><div class="stat-label">正向/中性/负向</div><div class="stat-value">${senti.positive}/${senti.neutral}/${senti.negative}</div></div>
      <div class="stat-item"><div class="stat-label">来源数</div><div class="stat-value">${d.sources.length}</div></div>
    </div>
    <h3>事件概述</h3><p>${escapeHtml(a.overview)}</p>
    <h3>时间线</h3><ul>${a.timeline.map((e) => `<li>${new Date(e.ts * 1000).toLocaleString()} - ${escapeHtml(e.title)}</li>`).join('')}</ul>
    <h3>传播渠道</h3><pre class="log-view">${JSON.stringify(a.channels, null, 2)}</pre>
    <h3>主要观点</h3><ul>${a.viewpoints.map((v) => `<li>${escapeHtml(v)}</li>`).join('')}</ul>
    <h3>风险判断</h3><ul>${a.risks.map((r) => `<li>${escapeHtml(r)}</li>`).join('')}</ul>
    <h3>重点证据</h3><ul>${a.evidence.map((e) => `<li><b>${escapeHtml(e.title)}</b> ${e.url ? `<a href="${escapeHtml(e.url)}" target="_blank">链接</a>` : ''} - ${escapeHtml(e.summary || '')}</li>`).join('')}</ul>
  `;
});

// ===== 论坛监控 =====
$('#btn-forum-start').addEventListener('click', async () => {
  try {
    await apiGet('/forum/start');
    loadForumLog();
  } catch (e) { showError(e.message); }
});
$('#btn-forum-stop').addEventListener('click', async () => {
  try {
    await apiGet('/forum/stop');
    loadForumLog();
  } catch (e) { showError(e.message); }
});
$('#btn-forum-refresh').addEventListener('click', () => { loadForumLog().catch((e) => showError(e.message)); });

async function loadForumLog() {
  const res = await apiGet('/forum/log');
  const entries = res.data?.entries || [];
  const view = $('#forum-log');
  view.textContent = entries.map((e) => `${e.ts} [${e.event_type}] (${e.task_status}) ${e.message}`).join('\n') || '(无日志)';
  view.scrollTop = view.scrollHeight;
}

$('#btn-forum-history').addEventListener('click', async () => {
  const date = $('#forum-date').value;
  if (!date) { alert('请选择日期'); return; }
  try {
    const res = await apiPost('/forum/log/history', { date });
    const entries = res.data?.entries || [];
    const view = $('#forum-history');
    view.textContent = entries.map((e) => `${e.ts} [${e.event_type}] ${e.message}`).join('\n') || '(无历史日志)';
    view.scrollTop = view.scrollHeight;
  } catch (e) { showError(e.message); }
});

// ===== 图谱查看 =====
async function loadLatestGraph() {
  try {
    const res = await apiGet('/graph/latest');
    renderGraph(res.data);
  } catch (e) { showError(e.message); }
}

async function loadGraphByReport(reportId) {
  try {
    const res = await apiGet(`/graph/${reportId}`);
    renderGraph(res.data);
  } catch (e) { showError(e.message); }
}

$('#btn-graph-latest').addEventListener('click', loadLatestGraph);
$('#btn-graph-load').addEventListener('click', () => {
  const id = $('#graph-report-id').value.trim();
  if (!id) { alert('请输入 report_id'); return; }
  loadGraphByReport(id);
});
$('#btn-graph-query').addEventListener('click', async () => {
  const reportId = $('#graph-query-report').value.trim();
  const nodeId = $('#graph-query-node').value.trim();
  const relationType = $('#graph-query-relation').value.trim();
  if (!reportId) { alert('请输入查询 report_id'); return; }
  const body = { report_id: reportId };
  if (nodeId) body.node_id = nodeId;
  if (relationType) body.relation_type = relationType;
  try {
    const res = await apiPost('/graph/query', body);
    renderGraph(res.data);
  } catch (e) { showError(e.message); }
});

function renderGraph(g) {
  if (!g || !g.nodes || g.nodes.length === 0) {
    $('#graph-view').innerHTML = '<div class="empty">暂无图谱数据</div>';
    return;
  }
  const nodes = g.nodes.map((n) =>
    `<span class="node-item node-${n.node_type}">[${n.node_type}] ${escapeHtml(n.label)}</span>`
  ).join('');
  const edges = g.edges.map((e) =>
    `<div class="edge-item">${escapeHtml(e.source)} --${escapeHtml(e.relation_type)}--> ${escapeHtml(e.target)}</div>`
  ).join('');
  $('#graph-view').innerHTML = `
    <h3>节点（${g.nodes.length}）</h3><div>${nodes}</div>
    <h3>关系（${g.edges.length}）</h3>${edges}
  `;
}

// ===== 配置管理 =====
$('#btn-config-load').addEventListener('click', async () => {
  try {
    const res = await apiGet('/config');
    $('#config-editor').value = JSON.stringify(res.data, null, 2);
  } catch (e) { showError(e.message); }
});
$('#btn-config-save').addEventListener('click', async () => {
  let data;
  try {
    data = JSON.parse($('#config-editor').value);
  } catch (e) {
    showError('配置 JSON 格式错误：' + e.message);
    return;
  }
  try {
    await apiPost('/config', data);
    alert('保存成功');
  } catch (e) { showError('保存失败：' + e.message); }
});

// ===== 系统状态 =====
async function loadSystemStatus() {
  const statusRes = await apiGet('/system/status');
  const appsRes = await apiGet('/status');
  const sys = statusRes.data?.system_status || 'offline';
  const apps = appsRes.data || {};
  const running = Object.values(apps).filter((a) => a.status === 'running').length;

  $('#system-cards').innerHTML = `
    <div class="stat-item"><div class="stat-label">系统状态</div><div class="stat-value">${sys}</div></div>
    <div class="stat-item"><div class="stat-label">运行中应用</div><div class="stat-value">${running} / ${Object.keys(apps).length}</div></div>
  ` + Object.entries(apps).map(([name, app]) => `
    <div class="stat-item"><div class="stat-label">${name}</div><div class="stat-value"><span class="status-badge status-${app.status}">${app.status}</span></div></div>
  `).join('');
}

// 系统启停按钮（首页，仅 admin）
function setSystemButtonsVisibility() {
  const isAdmin = currentUser && currentUser.role === 'admin';
  const toolbar = $('#console-toolbar');
  if (toolbar) toolbar.style.display = isAdmin ? '' : 'none';
}

// ===== WebSocket 实时消息 =====
let ws = null;
function initWs() {
  if (ws) { try { ws.close(); } catch (e) {} }
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${proto}//${location.host}/ws`);
  ws.onopen = () => {
    const indicator = $('#ws-indicator');
    if (indicator) {
      indicator.textContent = '● 实时消息已连接';
      indicator.classList.remove('off');
      indicator.classList.add('on');
    }
  };
  ws.onclose = () => {
    const indicator = $('#ws-indicator');
    if (indicator) {
      indicator.textContent = '● 实时消息未连接';
      indicator.classList.remove('on');
      indicator.classList.add('off');
    }
  };
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'app_status' || msg.type === 'system_status') {
      loadStatus().catch(() => {});
      loadSystemStatus().catch(() => {});
    }
    if (msg.type === 'forum_log') {
      loadForumLog().catch(() => {});
    }
    if (msg.type === 'app_output') {
      console.log('[app_output]', msg.payload.app_name, msg.payload.output_text);
    }
    if (msg.type === 'graph_ready') {
      console.log('[graph_ready]', msg.payload.report_id);
      loadGraphByReport(msg.payload.report_id).catch(() => {});
    }
    if (msg.type === 'error') {
      console.error('[error]', msg.payload.module_name, msg.payload.error_message);
    }
  };
}

function stopWs() {
  if (ws) { try { ws.close(); } catch (e) {} ws = null; }
}

// ===== 解析 URL 路径：支持 /graph-viewer 与 /graph-viewer/{report_id} =====
function handleGraphViewerRoute() {
  const m = location.pathname.match(/^\/graph-viewer(?:\/([^/]+))?/);
  if (!m) return;
  showPage('graph');
  if (m[1]) {
    $('#graph-report-id').value = m[1];
    loadGraphByReport(m[1]);
  } else {
    loadLatestGraph();
  }
}

// ===== 初始化 =====
loadUserFromStorage();

if (currentUser && getToken()) {
  // 已有登录态，直接进入应用（可先校验 token）
  enterApp();
  setSystemButtonsVisibility();
} else {
  showLogin();
}
