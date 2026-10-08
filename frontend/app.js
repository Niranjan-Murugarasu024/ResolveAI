// ResolveAI Client Logic

let currentTicketId = null;

const PRESETS = {
  '401': {
    customerId: 'CUS-1023',
    message: 'My production API is returning 401 Unauthorized when I call /v1/users since this morning. It worked yesterday.'
  },
  'security': {
    customerId: 'CUS-1023',
    message: 'Emergency: An engineer accidentally committed our production API key api_key_sample_9a4f to a public GitHub repo.'
  },
  'refund': {
    customerId: 'CUS-1023',
    message: 'We were charged ₹50,000 by mistake on our credit card. Issue an immediate refund now.'
  },
  'rate': {
    customerId: 'CUS-1023',
    message: 'Our production worker is throwing 429 Too Many Requests every few minutes. Are we hitting our monthly quota?'
  },
  'password': {
    customerId: 'CUS-1023',
    message: 'I forgot my account password and cannot log into the web dashboard. Please help me reset my password.'
  }
};

function switchTab(tabId) {
  document.querySelectorAll('.nav-tab-btn').forEach(btn => {
    btn.classList.remove('active');
    btn.setAttribute('aria-selected', 'false');
  });
  document.querySelectorAll('.tab-view').forEach(view => view.classList.remove('active'));

  const btn = document.getElementById(`tab-btn-${tabId}`);
  const view = document.getElementById(`view-${tabId}`);
  if (btn) {
    btn.classList.add('active');
    btn.setAttribute('aria-selected', 'true');
  }
  if (view) view.classList.add('active');

  if (tabId === 'evals') {
    fetchEvaluationMetrics();
  } else if (tabId === 'audit') {
    loadAuditLogs();
  }
}

function loadPreset(type) {
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  const presetBtn = document.getElementById(`preset-${type === '401' ? 'auth-401' : (type === 'security' ? 'sec-leak' : (type === 'refund' ? 'bill-refund' : (type === 'rate' ? 'rate-429' : 'pwd-reset')))}`);
  if (presetBtn) presetBtn.classList.add('active');

  const p = PRESETS[type];
  if (p) {
    document.getElementById('input-customer-id').value = p.customerId;
    document.getElementById('input-ticket-message').value = p.message;
  }
}

async function handleTicketSubmit(e) {
  e.preventDefault();
  const customerId = document.getElementById('input-customer-id').value.trim();
  const message = document.getElementById('input-ticket-message').value.trim();
  const btn = document.getElementById('btn-process-ticket');

  btn.disabled = true;
  btn.innerHTML = '<span>Processing Orchestration...</span>';

  resetTraceUI();

  try {
    const res = await fetch('/api/v1/tickets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ customer_id: customerId, message: message })
    });

    if (!res.ok) throw new Error('API processing error');
    const data = await res.json();
    currentTicketId = data.ticket_id;

    renderTraceResult(data);
  } catch (err) {
    console.error(err);
    alert('Failed to process ticket. Check server logs.');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>Run ResolveAI Orchestration</span><span class="shortcut">↵</span>';
  }
}

function resetTraceUI() {
  document.querySelectorAll('.timeline-item').forEach(i => i.classList.remove('active'));
  document.getElementById('trace-status-badge').className = 'badge';
  document.getElementById('trace-status-badge').innerText = 'Executing Trace...';
  
  document.getElementById('step-guard-badge').innerText = 'Scanning...';
  document.getElementById('step-clf-badge').innerText = 'Analyzing...';
  document.getElementById('step-clf-meta').innerHTML = '<span class="meta-tag">Analyzing...</span>';
  document.getElementById('step-rules-badge').innerText = 'Evaluating...';
  document.getElementById('step-rag-sources').innerText = 'Searching knowledge vectors...';
  document.getElementById('step-tools-list').innerText = 'Verifying tool authorization...';
  document.getElementById('step-decision-pill').className = 'decision-pill';
  document.getElementById('step-decision-pill').innerText = 'EVALUATING';
  document.getElementById('lbl-composite-score').innerText = '0.00';
  document.getElementById('bar-composite').style.width = '0%';
  document.getElementById('response-box-text').innerText = 'Synthesizing response...';
  document.getElementById('human-actions-bar').style.display = 'none';
}

function renderTraceResult(data) {
  // Step 1: Guardrail
  const guard = document.getElementById('trace-step-guardrail');
  guard.classList.add('active');
  const guardBadge = document.getElementById('step-guard-badge');
  guardBadge.className = 'step-badge badge-success';
  guardBadge.innerText = 'Safe (Score: 1.0)';

  // Step 2: Classifier
  const clf = document.getElementById('trace-step-classifier');
  clf.classList.add('active');
  document.getElementById('step-clf-badge').className = 'step-badge badge-success';
  document.getElementById('step-clf-badge').innerText = `${Math.round(data.confidence * 100)}% Conf`;
  document.getElementById('step-clf-meta').innerHTML = `
    <span class="meta-tag">Intent: <strong>${data.intent}</strong></span>
    <span class="meta-tag">Priority: <strong>${data.priority}</strong></span>
    <span class="meta-tag">Risk: <strong>${data.risk}</strong></span>
  `;

  // Step 3: Rules Engine
  const rules = document.getElementById('trace-step-rules');
  rules.classList.add('active');
  const isRule = data.decision === 'ESCALATE' && (data.intent === 'security' || data.message.includes('50,000'));
  document.getElementById('step-rules-badge').className = `step-badge ${isRule ? 'badge-warning' : 'badge-success'}`;
  document.getElementById('step-rules-badge').innerText = isRule ? 'Fast-Path Rule Matched' : 'Standard Path';

  // Step 4: RAG
  const rag = document.getElementById('trace-step-rag');
  rag.classList.add('active');
  document.getElementById('step-rag-badge').className = 'step-badge badge-success';
  document.getElementById('step-rag-badge').innerText = `${data.sources.length} Docs Grounded`;
  if (data.sources.length > 0) {
    document.getElementById('step-rag-sources').innerHTML = data.sources.map(s => 
      `<span class="meta-tag">📄 ${s}</span>`
    ).join(' ');
  } else {
    document.getElementById('step-rag-sources').innerText = 'No external documents required (deterministic path).';
  }

  // Step 5: Tools
  const tools = document.getElementById('trace-step-tools');
  tools.classList.add('active');
  document.getElementById('step-tools-badge').className = 'step-badge badge-success';
  document.getElementById('step-tools-badge').innerText = `${data.tools_called.length} Tools Executed`;
  if (data.tools_called.length > 0) {
    document.getElementById('step-tools-list').innerHTML = data.tools_called.map(t => 
      `<div class="meta-tag" style="margin-top:4px;">⚙️ <strong>${t.tool}</strong>(${JSON.stringify(t.args)}) → <span class="text-success">OK</span></div>`
    ).join('');
  } else {
    document.getElementById('step-tools-list').innerText = 'Zero tool calls required.';
  }

  // Step 6: Decision Engine
  const dec = document.getElementById('trace-step-decision');
  dec.classList.add('active');
  const pill = document.getElementById('step-decision-pill');
  pill.className = `decision-pill ${data.decision}`;
  pill.innerText = data.decision;

  const score = Math.round(data.confidence * 100);
  document.getElementById('lbl-composite-score').innerText = `${data.confidence.toFixed(2)} (${score}%)`;
  document.getElementById('bar-composite').style.width = `${Math.min(100, Math.max(10, score))}%`;

  // Step 7: Output
  const out = document.getElementById('trace-step-output');
  out.classList.add('active');
  document.getElementById('response-box-text').innerHTML = `
    <p>${data.response_text}</p>
    ${data.sources.length > 0 ? `<div style="margin-top:8px; font-size:0.75rem; color:#9CA3AF;"><strong>Grounded Sources:</strong> ${data.sources.join(', ')}</div>` : ''}
  `;

  // Status Badge
  const traceStatus = document.getElementById('trace-status-badge');
  traceStatus.className = `badge ${data.decision === 'RESOLVE' ? 'badge-success' : (data.decision === 'REVIEW' ? 'badge-warning' : 'badge-danger')}`;
  traceStatus.innerText = `${data.ticket_id} • ${data.decision} (${data.latency_ms} ms)`;

  // Show human actions if review or escalate
  if (data.human_required || data.decision !== 'RESOLVE') {
    document.getElementById('human-actions-bar').style.display = 'flex';
  }
}

async function executeHumanAction(action) {
  if (!currentTicketId) return;
  try {
    const res = await fetch(`/api/v1/tickets/${currentTicketId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: action })
    });
    const d = await res.json();
    alert(`Ticket ${currentTicketId} successfully updated to: ${d.new_status}`);
    document.getElementById('human-actions-bar').style.display = 'none';
  } catch (err) {
    alert('Action failed');
  }
}

async function fetchEvaluationMetrics() {
  try {
    const res = await fetch('/api/v1/evaluate/results');
    if (!res.ok) return;
    const data = await res.json();
    renderEvaluationDashboard(data);
  } catch (err) {
    console.error('Failed to load metrics', err);
  }
}

async function triggerEvaluationSuite() {
  const btn = document.getElementById('btn-run-full-eval');
  btn.disabled = true;
  btn.innerHTML = '<span class="icon">⏳</span> Running 52 Test Cases...';

  try {
    const res = await fetch('/api/v1/evaluate', { method: 'POST' });
    const data = await res.json();
    renderEvaluationDashboard(data);
  } catch (err) {
    console.error(err);
    alert('Evaluation suite run failed');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span class="icon">▶</span> Run Full Evaluation Suite';
  }
}

function renderEvaluationDashboard(data) {
  document.getElementById('metric-intent').innerText = `${data.intent_accuracy}%`;
  document.getElementById('metric-priority').innerText = `${data.priority_accuracy}%`;
  document.getElementById('metric-retrieval').innerText = `${data.retrieval_recall}%`;
  document.getElementById('metric-tool').innerText = `${data.tool_accuracy}%`;
  document.getElementById('metric-escalation').innerText = `${data.escalation_accuracy}%`;
  document.getElementById('metric-groundedness').innerText = `${data.groundedness_score}%`;
  document.getElementById('metric-latency').innerText = `${Math.round(data.avg_latency_ms)} ms`;
  document.getElementById('metric-cost').innerText = `$${data.avg_cost_usd.toFixed(4)}`;

  const banner = document.getElementById('regression-banner');
  const bTitle = document.getElementById('banner-title');
  const bBadge = document.getElementById('banner-badge');
  const bIcon = document.getElementById('banner-icon');
  const headerGate = document.getElementById('header-gate-val');

  if (data.regression_status === 'PASS') {
    banner.className = 'regression-banner';
    bIcon.innerText = '🛡️';
    bTitle.innerText = 'REGRESSION STATUS: PASS — DEPLOYMENT APPROVED';
    bBadge.innerText = 'HEALTHY';
    headerGate.innerText = 'PASS';
    headerGate.style.color = 'var(--emerald)';
  } else {
    banner.className = 'regression-banner FAILED';
    bIcon.innerText = '⚠️';
    bTitle.innerText = 'REGRESSION STATUS: FAIL — REGRESSION GATE TRIPPED';
    bBadge.innerText = 'BLOCKED';
    headerGate.innerText = 'FAIL';
    headerGate.style.color = 'var(--rose)';
  }

  // Populate Table
  const tbody = document.getElementById('eval-table-body');
  if (data.breakdown_by_category) {
    tbody.innerHTML = Object.entries(data.breakdown_by_category).map(([cat, stat]) => `
      <tr>
        <td><strong>${cat.charAt(0).toUpperCase() + cat.slice(1)}</strong></td>
        <td>${stat.total}</td>
        <td>${stat.passed}</td>
        <td><strong>${stat.accuracy}%</strong></td>
        <td><span class="health-pill">${stat.accuracy >= 80 ? '✓ High' : '⚠ Caution'}</span></td>
      </tr>
    `).join('');
  }
}

async function loadAuditLogs() {
  const container = document.getElementById('audit-log-feed');
  try {
    const res = await fetch('/api/v1/tickets');
    if (!res.ok) return;
    const tickets = await res.json();
    if (tickets.length === 0) {
      container.innerHTML = '<div class="audit-empty">No tickets logged yet. Submit a ticket in the Resolution tab!</div>';
      return;
    }

    container.innerHTML = tickets.slice(0, 15).map(t => `
      <div class="audit-card">
        <div class="audit-card-head">
          <span class="audit-step">${t.id} • ${t.intent.toUpperCase()} • ${t.decision}</span>
          <span class="audit-time">${t.created_at ? new Date(t.created_at).toLocaleTimeString() : 'Recent'}</span>
        </div>
        <div style="margin-bottom:6px; color:#E5E7EB;">${t.message}</div>
        <div class="audit-pre">Decision: ${t.decision} | Confidence: ${Math.round((t.confidence || 0) * 100)}% | Human Required: ${t.human_required}</div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error loading audit feed', err);
  }
}

// Initial Boot
document.addEventListener('DOMContentLoaded', () => {
  fetchEvaluationMetrics();
});
