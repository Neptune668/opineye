// ===== API 封装 =====
const API_BASE = '/api';

async function apiGet(path) {
  const r = await fetch(API_BASE + path);
  return r.json();
}

async function apiPost(path, body) {
  const r = await fetch(API_BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  });
  return r.json();
}

// ===== 工具 =====
const $ = (sel) => document.querySelector(sel);

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

// ===== 页面导航 =====
const PAGES = ['console', 'search', 'forum', 'graph', 'config', 'system'];

document.querySelectorAll('.nav-item').forEach((item) => {
  item.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach((n) => n.classList.remove('active'));
    item.classList.add('active');
    const page = item.dataset.page;
    document.querySelectorAll('.page').forEach((p) => p.classList.remove('active'));
    $('#page-' + page).classList.add('active');
    // 进入页面时刷新数据
    if (page === 'console' || page === 'system') loadStatus();
    if (page === 'forum') loadForumLog();
  });
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
  cards.innerHTML = Object.entries(apps).map(([name, app]) => `
    <div class="card">
      <div class="card-header">
        <span class="card-title">${labels[name] || name}</span>
        <span class="status-badge status-${app.status}">${app.status}</span>
      </div>
      <div class="card-actions">
        <button class="btn primary" onclick="startApp('${name}')">启动</button>
        <button class="btn danger" onclick="stopApp('${name}')">停止</button>
        <button class="btn" onclick="viewOutput('${name}')">输出</button>
      </div>
    </div>
  `).join('');
}

async function startApp(name) {
  await apiGet(`/start/${name}`);
  loadStatus();
}
async function stopApp(name) {
  await apiGet(`/stop/${name}`);
  loadStatus();
}
async function viewOutput(name) {
  const res = await apiGet(`/output/${name}`);
  alert(`【${name}】输出：\n${res.data?.output_text || '(空)'}`);
}

// ===== 主题检索 =====
$('#btn-search').addEventListener('click', async () => {
  const query = $('#search-query').value.trim();
  const sources = Array.from($('#search-sources').selectedOptions).map((o) => o.value);
  if (!query) { alert('请输入主题词'); return; }
  const res = await apiPost('/search', { query, source_types: sources });
  const d = res.data;
  if (!d) { $('#search-result').innerHTML = `<div class="empty">检索失败：${res.message}</div>`; return; }

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
  await apiGet('/forum/start');
  loadForumLog();
});
$('#btn-forum-stop').addEventListener('click', async () => {
  await apiGet('/forum/stop');
  loadForumLog();
});
$('#btn-forum-refresh').addEventListener('click', loadForumLog);

async function loadForumLog() {
  const res = await apiGet('/forum/log');
  const entries = res.data?.entries || [];
  $('#forum-log').textContent = entries.map((e) => `${e.ts} [${e.event_type}] (${e.task_status}) ${e.message}`).join('\n') || '(无日志)';
}

$('#btn-forum-history').addEventListener('click', async () => {
  const date = $('#forum-date').value;
  if (!date) { alert('请选择日期'); return; }
  const res = await apiPost('/forum/log/history', { date });
  const entries = res.data?.entries || [];
  $('#forum-history').textContent = entries.map((e) => `${e.ts} [${e.event_type}] ${e.message}`).join('\n') || '(无历史日志)';
});

// ===== 图谱查看 =====
$('#btn-graph-latest').addEventListener('click', async () => {
  const res = await apiGet('/graph/latest');
  renderGraph(res.data);
});
$('#btn-graph-load').addEventListener('click', async () => {
  const id = $('#graph-report-id').value.trim();
  if (!id) { alert('请输入 report_id'); return; }
  const res = await apiGet(`/graph/${id}`);
  renderGraph(res.data);
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
  const res = await apiGet('/config');
  $('#config-editor').value = JSON.stringify(res.data, null, 2);
});
$('#btn-config-save').addEventListener('click', async () => {
  try {
    const data = JSON.parse($('#config-editor').value);
    const res = await apiPost('/config', data);
    if (res.code === 0) { alert('保存成功'); } else { alert('保存失败：' + res.message); }
  } catch (e) { alert('配置 JSON 格式错误：' + e.message); }
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

// 系统启停按钮（首页）
$('#btn-system-start').addEventListener('click', async () => {
  await apiPost('/system/start');
  loadStatus();
});
$('#btn-system-shutdown').addEventListener('click', async () => {
  await apiPost('/system/shutdown');
  loadStatus();
});

// ===== WebSocket 实时消息 =====
function initWs() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${proto}//${location.host}/ws`);
  ws.onopen = () => {
    $('#ws-indicator').textContent = '● 实时消息已连接';
    $('#ws-indicator').classList.remove('off');
    $('#ws-indicator').classList.add('on');
  };
  ws.onclose = () => {
    $('#ws-indicator').textContent = '● 实时消息未连接';
    $('#ws-indicator').classList.remove('on');
    $('#ws-indicator').classList.add('off');
  };
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'app_status' || msg.type === 'system_status') {
      loadStatus();
      loadSystemStatus();
    }
    if (msg.type === 'forum_log') {
      loadForumLog();
    }
  };
}

// ===== 初始化 =====
loadStatus();
loadSystemStatus();
initWs();
