// PARLAYSMART -- Logic

// Register Service Worker (PWA)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/static/sw.js').catch(() => {}));
}

// ===== LOGIN =====
function checkAuth() {
  fetch('/today-matches?date=check', { credentials: 'include' })
    .then(function(r) {
      if (r.status !== 401) { hideLogin(); }
      // si es 401, el login ya es visible, no hacemos nada
    })
    .catch(function() {
      // error de red - mantener login visible
    });
}

function showLogin() {
  var ls = document.getElementById('loginScreen');
  if (ls) ls.style.display = 'flex';
}

function hideLogin() {
  var ls = document.getElementById('loginScreen');
  if (ls) ls.style.display = 'none';
}

function doLogin() {
  var inp = document.getElementById('loginCodeInput');
  var err = document.getElementById('loginError');
  var code = inp ? inp.value.trim() : '';
  if (!code) { if (err) err.textContent = 'Ingresa el codigo'; return; }
  var btn = document.querySelector('.login-btn');
  if (btn) btn.textContent = 'Verificando...';
  fetch('/login', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: code })
  }).then(function(r) { return r.json().then(function(d) { return { ok: r.ok, d: d }; }); })
    .then(function(res) {
      if (res.ok) {
        hideLogin();
        if (err) err.textContent = '';

        // Guardar estado de admin
        const isAdmin = res.d.is_admin === true;
        localStorage.setItem('isAdmin', isAdmin ? 'true' : 'false');
        window.isAdmin = isAdmin;

        console.log('Login success:', { isAdmin, is_admin: res.d.is_admin });

        // Solo mostrar botón Admin si es admin
        var adminBtn = document.getElementById('adminBtn');
        if (adminBtn) {
          adminBtn.style.display = isAdmin ? 'inline-flex' : 'none';
          console.log('Admin button display:', adminBtn.style.display);
        }
      } else {
        if (err) err.textContent = res.d.error || 'Codigo incorrecto o expirado';
        if (inp) inp.value = '';
      }
      if (btn) btn.textContent = 'Entrar';
    })
    .catch(function() {
      if (err) err.textContent = 'Error de conexion';
      if (btn) btn.textContent = 'Entrar';
    });
}

function doLogout() {
  fetch('/logout', { method: 'POST', credentials: 'include' })
    .then(() => {
      localStorage.clear();
      sessionStorage.clear();
      showLogin();
      var logoutBtn = document.getElementById('logoutBtn');
      if (logoutBtn) logoutBtn.style.display = 'none';
    })
    .catch(err => console.error('Logout error:', err));
}

let analysisData = null;

//  UTILS 
const $ = id => document.getElementById(id);
const qs = sel => document.querySelector(sel);
const qsa = sel => document.querySelectorAll(sel);

function showView(id) {
  qsa('.view').forEach(v => v.classList.remove('active'));
  $(id).classList.add('active');
}

function switchPage(pageId, el) {
  qsa('.page, .result-page').forEach(p => p.classList.remove('active'));
  var pg = $('page-' + pageId);
  if (pg) pg.classList.add('active');
  qsa('.snav-item, .ptab, .mob-tab, .rsn-btn').forEach(n => n.classList.remove('active'));
  if (el) el.classList.add('active');
}

function goHome() {
  showView('view-landing');
  var inp = $('searchInput') || $('queryInput');
  if (inp) inp.value = '';
}

function setExample(text) {
  var inp = $('searchInput') || $('queryInput');
  if (inp) inp.value = text;
  qsa('.snav').forEach(b => b.classList.remove('active'));
}
function setExampleAndGo(text) {
  var inp = $('searchInput') || $('queryInput');
  if (inp) inp.value = text;
  startAnalysis();
}

function quickSearch(text) {
  var inp = $('searchInput') || $('queryInput');
  if (inp) inp.value = text;
  startAnalysis();
}

function setSport(s) {
  qsa('.snav').forEach(function(b) {
    if (b.textContent.trim().includes(s)) b.classList.add('active');
    else b.classList.remove('active');
  });
}

function toggleSidebar() {}

// ===== HISTORIAL =====
var HISTORY_KEY = 'parlaysmart_historial';
var MAX_HISTORY = 15;

function saveToHistory(label, type, sport, data) {
  try {
    var hist = getHistorial();
    hist = hist.filter(function(h) { return h.label !== label; });
    hist.unshift({ id: Date.now().toString(), label: label, type: type, sport: sport || 'Futbol', date: new Date().toISOString().slice(0,10), data: data });
    if (hist.length > MAX_HISTORY) hist = hist.slice(0, MAX_HISTORY);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(hist));
    renderHistorial();
  } catch(e) { console.warn('Historial error:', e); }
}

function getHistorial() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); }
  catch(e) { return []; }
}

function renderHistorial() {
  var container = $('historialList');
  if (!container) return;
  var hist = getHistorial();
  if (!hist.length) {
    container.innerHTML = '<div class="hist-empty">Sin analisis aun.<br>Analiza un partido para guardarlo aqui.</div>';
    return;
  }
  container.innerHTML = hist.map(function(h) {
    var short = h.label.length > 26 ? h.label.slice(0,24) + '...' : h.label;
    return '<div class="hist-item" onclick="openFromHistory(\'' + h.id + '\')" title="' + esc(h.label) + '">' +
      '<div class="hist-item-label">' + esc(short) + '</div>' +
      '<div class="hist-item-meta">' + esc(h.date) + ' &middot; ' + esc(h.sport || 'Futbol') + (h.type === 'multi' ? ' &middot; multi' : '') + '</div>' +
    '</div>';
  }).join('');
}

function openFromHistory(id) {
  var hist = getHistorial();
  var entry = hist.find(function(h) { return h.id === id; });
  if (!entry) return;
  var d = entry.data;
  d._from_history = true;
  d._history_label = entry.label;
  d._history_date = entry.date;
  if (entry.type === 'multi') {
    multiAnalysisData = d;
    renderMultiResults(d);
    showView('view-multi-results');
  } else {
    analysisData = d;
    renderResults(d);
    switchPage('overview', null);
    showView('view-results');
    setTimeout(function() { animateBars(d); }, 300);
  }
}

function clearHistorial() {
  if (!confirm('Borrar todo el historial de analisis?')) return;
  localStorage.removeItem(HISTORY_KEY);
  renderHistorial();
  renderHistorialView();
}

function deleteHistorialEntry(id, e) {
  e.stopPropagation();
  var hist = getHistorial().filter(function(h) { return h.id !== id; });
  localStorage.setItem(HISTORY_KEY, JSON.stringify(hist));
  renderHistorial();
  renderHistorialView();
}

function renderHistorialView() {
  var container = document.getElementById('histViewList');
  if (!container) return;
  var hist = getHistorial();
  if (!hist.length) {
    container.innerHTML = '<div class="hv-empty">Aun no tienes analisis guardados.<br>Cada partido que analices se guarda automaticamente aqui para verlo gratis despues.</div>';
    return;
  }
  var typeIcon = { single: '&#9917;', multi: '&#128200;' };
  container.innerHTML = hist.map(function(h) {
    var mi = (h.data && h.data.match_info) || {};
    var fp = (h.data && h.data.final_prediction) || {};
    var prlys = (h.data && h.data.parlays) || {};
    var parlayNames = Object.values(prlys).map(function(p) { return p.name || ''; }).filter(Boolean).slice(0,2);
    var conf = fp.confidence_score ? fp.confidence_score + '/10' : '';
    var sport = h.sport || mi.sport || 'Futbol';
    var matches = h.type === 'multi' ? (h.data && h.data.matches ? h.data.matches.length : '?') + ' partidos' : '';
    return '<div class="hv-card" onclick="openFromHistory(\'' + h.id + '\')">' +
      '<div class="hv-card-top">' +
        '<div class="hv-icon">' + (typeIcon[h.type] || '&#9917;') + '</div>' +
        '<div class="hv-card-info">' +
          '<div class="hv-label">' + esc(h.label) + '</div>' +
          '<div class="hv-meta">' +
            '<span class="hv-date">' + esc(h.date) + '</span>' +
            '<span class="hv-sport">' + esc(sport) + '</span>' +
            (matches ? '<span class="hv-multi">' + matches + '</span>' : '') +
            (conf ? '<span class="hv-conf">Confianza: ' + conf + '</span>' : '') +
          '</div>' +
          (parlayNames.length ? '<div class="hv-parlays">' + parlayNames.map(function(n){ return '<span class="hv-parlay-tag">' + esc(n) + '</span>'; }).join('') + '</div>' : '') +
        '</div>' +
        '<div class="hv-card-right">' +
          '<span class="hv-free-tag">GRATIS</span>' +
          '<button class="hv-del" onclick="deleteHistorialEntry(\'' + h.id + '\',event)" title="Eliminar">&#10005;</button>' +
        '</div>' +
      '</div>' +
    '</div>';
  }).join('');
}

function esc(s) {
  if (!s) return '';
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function pct(n) { return Math.round(Number(n)||0) + '%'; }
function fmt(n, d=2) { return (Number(n)||0).toFixed(d); }

//  LOADING 
function animateLoading() {
  const delays = [0, 4000, 9000, 15000, 22000];
  const pcts   = [15, 35, 55, 78, 93];
  [1,2,3,4,5].forEach((s, i) => {
    setTimeout(() => {
      if (i > 0) {
        const prev = $('lstep-' + (s-1));
        if (prev) { prev.classList.remove('active'); prev.classList.add('done'); }
      }
      const el = $('lstep-' + s);
      if (el) el.classList.add('active');
      const bar = $('loadingBar');
      if (bar) bar.style.width = pcts[i] + '%';
    }, delays[i]);
  });
}

function resetLoading() {
  [1,2,3,4,5].forEach(s => {
    const el = $('lstep-' + s);
    if (el) { el.classList.remove('active','done'); }
  });
  const bar = $('loadingBar');
  if (bar) bar.style.width = '0%';
}

//  START ANALYSIS 
// collect all match queries from landing inputs
function getAllMatchQueries() {
  var queries = [];
  var inp = $('searchInput') || $('queryInput');
  var q1 = inp ? inp.value.trim() : '';
  if (q1) queries.push(q1);
  document.querySelectorAll('.extra-match-input').forEach(function(inp) {
    var v = inp.value.trim();
    if (v) queries.push(v);
  });
  return queries;
}

function addMatchInput() {
  var wrap = $('extraMatchesWrap');
  var existing = wrap.querySelectorAll('.extra-match-row').length;
  var num = existing + 2; // partido 2, 3, 4...

  var row = document.createElement('div');
  row.className = 'extra-match-row';
  row.innerHTML =
    '<span class="extra-match-num">' + num + '</span>' +
    '<input class="extra-match-input" type="text" placeholder="Ej: America vs Chivas, Liga MX, hoy" ' +
      'onkeydown="if(event.key===\'Enter\') startAnalysis()">' +
    '<button class="extra-match-remove" onclick="removeMatchInput(this)" title="Quitar">x</button>';
  wrap.appendChild(row);

  // Re-number all rows
  renumberMatchRows();

  // Show hint and update button
  $('multiSearchHint').style.display = 'inline';
  updateMultiAnalyzeBanner();

  // Focus new input
  row.querySelector('.extra-match-input').focus();
}

function removeMatchInput(btn) {
  var row = btn.closest('.extra-match-row');
  if (row) row.remove();
  renumberMatchRows();
  updateMultiAnalyzeBanner();
  if ($('extraMatchesWrap').querySelectorAll('.extra-match-row').length === 0) {
    $('multiSearchHint').style.display = 'none';
  }
}

function renumberMatchRows() {
  $('extraMatchesWrap').querySelectorAll('.extra-match-num').forEach(function(el, i) {
    el.textContent = i + 2;
  });
}

function updateMultiAnalyzeBanner() {
  var count = getAllMatchQueries().length;
  var btn = $('mainAnalyzeBtn');
  if (!btn) return;
  if (count > 1) {
    btn.textContent = 'ANALIZAR ' + count + ' PARTIDOS ->';
    btn.style.background = 'var(--green)';
    btn.style.color = '#000';
  } else {
    btn.textContent = 'ANALIZAR  ->';
    btn.style.background = '';
    btn.style.color = '';
  }
}

async function startAnalysis() {
  var queries = getAllMatchQueries();
  var errEl = $('searchError');

  if (queries.length === 0) {
    errEl.textContent = 'Escribe el partido que quieres analizar.';
    return;
  }
  errEl.textContent = '';

  // Multiple matches -> multi-analyze
  if (queries.length > 1) {
    var matches = queries.map(function(q, i) {
      return { id: 'manual_' + i, team_home: q, team_away: '', league_name: '', time_mx: '', query_text: q };
    });
    selectedMatches = {};
    matches.forEach(function(m) { selectedMatches[m.id] = m; });
    if ($('multiLoadCount')) $('multiLoadCount').textContent = matches.length;
    showView('view-multi-loading');
    animateMultiLoading();
    var dateStr = new Date().toISOString().slice(0,10);
    try {
      var res = await fetch('/multi-analyze', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ matches: matches, date: dateStr, raw_queries: queries, sport: window.currentSport || 'Futbol' })
      });
      var data = await res.json();
      if (data.error) throw new Error(data.error);
      multiAnalysisData = data;
      renderMultiResults(data);
      showView('view-multi-results');
      // Guardar en historial
      var matchLabels = (data.matches || []).map(function(m) {
        return (m.team_home || m.team_a || '?');
      }).join(' / ');
      var multiLabel = matchLabels || (queries.length + ' partidos');
      saveToHistory(multiLabel, 'multi', 'Multi', data);
    } catch(err) {
      showView('view-landing');
      errEl.textContent = 'Error: ' + err.message;
    }
    return;
  }

  // Single match -> original flow
  var query = queries[0];
  resetLoading();
  showView('view-loading');
  animateLoading();

  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({query, sport: window.currentSport || 'Futbol'})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error del servidor');

    analysisData = data;
    renderResults(data);
    switchPage('overview', null);
    showView('view-results');
    setTimeout(() => animateBars(data), 300);
    // Guardar en historial
    var mi = data.match_info || {};
    var label = mi.team_a && mi.team_b ? mi.team_a + ' vs ' + mi.team_b : query;
    saveToHistory(label, 'single', mi.sport || 'Futbol', data);

  } catch(err) {
    showView('view-landing');
    $('searchError').textContent = ' ' + err.message;
  }
}

//  RENDER ALL 
function renderResults(d) {
  const mi   = d.match_info || {};
  const mm   = d.math_models || {};
  const comb = mm.combined  || {};
  const pois = mm.poisson   || {};
  const mc   = mm.monte_carlo || {};
  const elo  = mm.elo       || {};
  const fair = mm.fair_odds || {};
  const fp   = d.final_prediction || {};
  const sta  = d.stats_team_a || {};
  const stb  = d.stats_team_b || {};
  const h2h  = d.head_to_head || {};
  const plrs = d.players || {};
  const ctx  = d.context || {};
  const ws   = d.weather_stadium || {};
  const ref  = d.referee || {};
  const psy  = d.psychological || {};
  const news = d.news || {};
  const bm   = d.betting_market || {};
  const mkts = d.markets || {};
  const prlys= d.parlays || {};

  const teamA = mi.team_a || 'Local';
  const teamB = mi.team_b || 'Visitante';

  const probA = comb.home_win || pois.home_win || 33;
  const probD = comb.draw     || pois.draw     || 34;
  const probB = comb.away_win || pois.away_win || 33;

  // Badge de cache / historial
  var cachedBadge = document.getElementById('cachedBadge');
  if (cachedBadge) cachedBadge.remove();
  if (d._from_history) {
    var badge = document.createElement('div');
    badge.id = 'cachedBadge';
    badge.className = 'hist-badge';
    badge.textContent = 'Del historial (' + (d._history_date || '') + ') - sin costo';
    var hdr = document.querySelector('.match-header');
    if (hdr) hdr.insertBefore(badge, hdr.firstChild);
  } else if (d._cached) {
    var badge = document.createElement('div');
    badge.id = 'cachedBadge';
    badge.className = 'cached-badge';
    badge.textContent = 'Guardado hoy - sin costo';
    var hdr = document.querySelector('.match-header');
    if (hdr) hdr.insertBefore(badge, hdr.firstChild);
  }

  //  MATCH CARD HEADER
  $('hComp').textContent = mi.competition || '';
  $('hDate').textContent = mi.date || '';
  $('hTeamA').textContent = teamA;
  $('hTeamB').textContent = teamB;
  $('hLikelyScore').textContent = pois.most_likely_score ? 'Marcador probable: ' + pois.most_likely_score : '';

  $('hProbA').textContent = pct(probA);
  $('hProbD').textContent = pct(probD);
  $('hProbB').textContent = pct(probB);
  $('fairOddsA').textContent = fair.home_win ? 'Momio justo: ' + fair.home_win : '';
  $('fairOddsD').textContent = fair.draw     ? 'Momio justo: ' + fair.draw     : '';
  $('fairOddsB').textContent = fair.away_win ? 'Momio justo: ' + fair.away_win : '';

  // Sidebar match info
  if ($('sidebarMatchInfo')) $('sidebarMatchInfo').innerHTML = `
    <div style="font-weight:600;color:var(--text);margin-bottom:4px">${esc(teamA)}</div>
    <div style="font-size:10px;color:var(--red);margin-bottom:4px">VS</div>
    <div style="font-weight:600;color:var(--text);margin-bottom:8px">${esc(teamB)}</div>
    ${mi.competition ? `<div>${esc(mi.competition)}</div>` : ''}
    ${mi.date ? `<div>${esc(mi.date)}</div>` : ''}
    ${fp.confidence_score ? `<div style="margin-top:6px;color:var(--gold)">Confianza: ${fp.confidence_score}/10</div>` : ''}
  `;

  renderOverview(d, teamA, teamB, probA, probD, probB, fp, pois, comb);
  renderStats(sta, stb, h2h, teamA, teamB);
  renderPlayers(plrs, teamA, teamB);
  renderContext(ctx, ws, ref, psy, news, teamA, teamB);
  renderModels(comb, pois, mc, elo, fair, d, teamA, teamB);
  renderMarkets(mkts, bm);
  renderMexicanOdds(d);
  renderParlays(prlys, teamA, teamB);

  // Record prediction for accuracy tracking
  const winner = fp.winner === 'A' ? teamA : fp.winner === 'B' ? teamB : 'Empate';
  recordPrediction(teamA, teamB, winner, fp.confidence_score || 6);
  renderAccuracyBadge();
  renderAccuracyCard();
}

//  OVERVIEW 
function renderOverview(d, teamA, teamB, probA, probD, probB, fp, pois, comb) {
  const winner = fp.winner==='A' ? teamA : fp.winner==='B' ? teamB : 'Empate';
  const winColor = fp.winner==='A' ? 'var(--green)' : fp.winner==='B' ? 'var(--blue)' : 'var(--gold)';

  // Prediction
  $('cardPrediction').innerHTML = `
    <div class="pcard-title">Prediccin final</div>
    <div class="pred-winner" style="color:${winColor}">${esc(winner)}</div>
    <div class="pred-sub">Confianza ${fp.confidence_score||''}/10</div>
    <div class="pred-text">${esc(fp.summary||'')}</div>
  `;

  // Confidence
  const cs = Number(fp.confidence_score)||6;
  const stars = Array.from({length:5},(_,i)=>i < Math.round(cs/2) ? '':'');
  const confTxt = cs>=8?'Muy alta':cs>=6?'Moderada':cs>=4?'Baja':'Incierta';
  $('cardConfidence').innerHTML = `
    <div class="pcard-title">Nivel de confianza</div>
    <div style="display:flex;align-items:baseline;gap:4px;margin-bottom:6px">
      <div class="conf-big">${cs}</div>
      <div class="conf-slash">/10</div>
    </div>
    <div class="conf-stars">${stars.map(s=>`<span style="color:${s===''?'var(--gold)':'var(--bg-card2)'}">${s}</span>`).join('')}</div>
    <div class="conf-desc">${confTxt}</div>
  `;

  // Value bet
  $('cardValue').innerHTML = `
    <div class="pcard-title">Value Bet</div>
    <div class="value-tag"> Value encontrado</div>
    <div class="value-text">${esc(fp.value_bet || 'Sin valor claro identificado en este partido.')}</div>
  `;

  // Probs big
  const btts = pois.btts || comb.btts || 0;
  const over = pois.over_2_5 || comb.over_2_5 || 0;
  const over35 = pois.over_3_5 || 0;
  $('probsBig').innerHTML = `
    <div class="probs-big-row">
      <div class="prob-big-item p-home">
        <div class="pb-label">${esc(teamA)} gana</div>
        <div class="pb-val">${pct(probA)}</div>
        <div class="pb-bar"><div class="pb-fill" data-w="${probA}" style="width:0%"></div></div>
        <div class="pb-sub">Gana como local</div>
      </div>
      <div class="prob-big-item p-draw">
        <div class="pb-label">Empate</div>
        <div class="pb-val">${pct(probD)}</div>
        <div class="pb-bar"><div class="pb-fill" data-w="${probD}" style="width:0%"></div></div>
        <div class="pb-sub">Termina igualado</div>
      </div>
      <div class="prob-big-item p-away">
        <div class="pb-label">${esc(teamB)} gana</div>
        <div class="pb-val">${pct(probB)}</div>
        <div class="pb-bar"><div class="pb-fill" data-w="${probB}" style="width:0%"></div></div>
        <div class="pb-sub">Gana como visitante</div>
      </div>
    </div>
    <div class="extra-stats" style="margin-top:12px">
      <div class="extra-stat"><div class="es-val" style="color:var(--purple)">${pct(btts)}</div><div class="es-label">Ambos anotan</div></div>
      <div class="extra-stat"><div class="es-val" style="color:var(--purple)">${pct(over)}</div><div class="es-label">Ms de 2.5 goles</div></div>
      <div class="extra-stat"><div class="es-val" style="color:var(--purple)">${pct(over35)}</div><div class="es-label">Ms de 3.5 goles</div></div>
      <div class="extra-stat"><div class="es-val" style="color:var(--gold)">${esc(pois.most_likely_score||'')}</div><div class="es-label">Marcador ms probable</div></div>
    </div>
  `;

  // Risks
  const risks = fp.main_risks || [];
  $('risksList').innerHTML = risks.length
    ? risks.map((r,i)=>`<div class="risk-item"><div class="risk-num">${i+1}</div><div class="risk-text">${esc(r)}</div></div>`).join('')
    : '<div class="notes-text" style="color:var(--text3)">No se identificaron riesgos crticos para este partido.</div>';
}

//  STATS 
function renderStats(sta, stb, h2h, teamA, teamB) {

  // ---- SOFASCORE-style bar helper ----
  // valor A | ====BARRA==== | valor B   (crece desde el centro hacia afuera)
  function statBar(lbl, a, b, higherWins, unit) {
    var av = Number(a) || 0, bv = Number(b) || 0;
    var total = av + bv;
    // porcentaje proporcional (de 0 a 100)
    var pA = total > 0 ? Math.round(av / total * 100) : 50;
    var pB = total > 0 ? Math.round(bv / total * 100) : 50;
    var aWin = higherWins ? av >= bv : (bv === 0 || av <= bv);
    var bWin = higherWins ? bv > av  : (av === 0 || bv < av);
    var u = unit || '';
    var aCol = aWin ? 'var(--green)' : 'rgba(255,255,255,.35)';
    var bCol = bWin ? 'var(--blue)'  : 'rgba(255,255,255,.35)';
    var aValCol = aWin ? '#fff' : 'var(--text3)';
    var bValCol = bWin ? '#fff' : 'var(--text3)';
    return '<div class="sf-stat-row">' +
      '<span class="sf-val sf-val-a" style="color:' + aValCol + '">' + (av || '--') + u + '</span>' +
      '<div class="sf-bar-wrap">' +
        '<div class="sf-bar-inner">' +
          '<div class="sf-bar-a" style="width:' + pA + '%;background:' + aCol + '"></div>' +
          '<div class="sf-bar-b" style="width:' + pB + '%;background:' + bCol + '"></div>' +
        '</div>' +
        '<div class="sf-lbl">' + lbl + '</div>' +
      '</div>' +
      '<span class="sf-val sf-val-b" style="color:' + bValCol + '">' + (bv || '--') + u + '</span>' +
    '</div>';
  }

  function statGroup(icon, title, rows) {
    return '<div class="sf-group">' +
      '<div class="sf-group-title">' + (icon ? '<span class="sf-group-icon">' + icon + '</span>' : '') + title + '</div>' +
      rows.join('') +
    '</div>';
  }

  // ---- H2H ----
  var h2hLast = (h2h.last_5_h2h || []).map(function(m) {
    if (typeof m === 'string') return '<div class="h2h-res-item">' + esc(m) + '</div>';
    return '<div class="h2h-res-item">' +
      '<span class="h2h-res-date">' + esc(m.date || '') + '</span>' +
      '<span class="h2h-res-teams">' + esc(m.home || '') + ' <strong>' + esc(m.score || '') + '</strong> ' + esc(m.away || '') + '</span>' +
      '<span class="h2h-res-comp">' + esc(m.competition || '') + '</span>' +
    '</div>';
  }).join('');
  // fallback to old field
  if (!h2hLast && (h2h.last_results || h2h.last_3_results)) {
    var arr = h2h.last_results || h2h.last_3_results || [];
    h2hLast = arr.map(function(r){ return '<div class="h2h-res-item">' + esc(r) + '</div>'; }).join('');
  }

  $('h2hSection').innerHTML =
    '<div class="stat-group-title">Historial directo</div>' +
    '<div class="h2h-row">' +
      '<div class="h2h-stat"><div class="h2h-val">' + (h2h.team_a_wins ?? '--') + '</div><div class="h2h-lbl">' + esc(teamA) + '</div></div>' +
      '<div class="h2h-stat"><div class="h2h-val" style="color:var(--text3)">' + (h2h.total_meetings || '') + '</div><div class="h2h-lbl">Totales</div></div>' +
      '<div class="h2h-stat"><div class="h2h-val" style="color:var(--text3)">' + (h2h.draws ?? '--') + '</div><div class="h2h-lbl">Empates</div></div>' +
      '<div class="h2h-stat"><div class="h2h-val">' + (h2h.team_b_wins ?? '--') + '</div><div class="h2h-lbl">' + esc(teamB) + '</div></div>' +
    '</div>' +
    (h2h.avg_goals_per_game ? '<div class="h2h-extra"><span>Promedio goles: <strong>' + fmt(h2h.avg_goals_per_game, 1) + '</strong></span>' +
      (h2h.btts_in_h2h != null ? '<span>BTTS: <strong>' + h2h.btts_in_h2h + ' de ' + (h2h.total_meetings || '?') + '</strong></span>' : '') +
      (h2h.over_2_5_in_h2h != null ? '<span>+2.5 goles: <strong>' + h2h.over_2_5_in_h2h + ' partidos</strong></span>' : '') +
    '</div>' : '') +
    (h2h.notable_pattern || h2h.trend ? '<div class="h2h-trend">' + esc(h2h.notable_pattern || h2h.trend || '') + '</div>' : '') +
    (h2hLast ? '<div class="h2h-results-title">Ultimos partidos entre ellos</div><div class="h2h-results">' + h2hLast + '</div>' : '');

  // ---- STATS COMPARACION estilo Sofascore ----
  var sfHeader =
    '<div class="sf-teams-header">' +
      '<span class="sf-team-a">' + esc(teamA) + '</span>' +
      '<span class="sf-vs-center">ESTADISTICAS</span>' +
      '<span class="sf-team-b">' + esc(teamB) + '</span>' +
    '</div>';

  $('statsCompare').innerHTML = sfHeader +
    statGroup('&#9917;', 'Ataque', [
      statBar('Goles anotados / p', sta.goals_scored_avg, stb.goals_scored_avg, true),
      statBar('xG (goles esperados)', sta.xg_avg, stb.xg_avg, true),
      statBar('Tiros totales / p', sta.shots_per_game, stb.shots_per_game, true),
      statBar('Tiros al arco / p', sta.shots_on_target_per_game, stb.shots_on_target_per_game, true),
      statBar('Goles 1er tiempo', sta.avg_goals_first_half, stb.avg_goals_first_half, true),
      statBar('Goles 2do tiempo', sta.avg_goals_second_half, stb.avg_goals_second_half, true),
      statBar('Corners / p', sta.corners_per_game, stb.corners_per_game, true),
    ]) +
    statGroup('&#128737;', 'Defensa', [
      statBar('Goles recibidos / p', sta.goals_conceded_avg, stb.goals_conceded_avg, false),
      statBar('xGA (goles esperados contra)', sta.xga_avg, stb.xga_avg, false),
      statBar('Porterias en cero (%)', sta.clean_sheets_pct, stb.clean_sheets_pct, true, '%'),
      statBar('Posesion (%)', sta.possession_avg, stb.possession_avg, true, '%'),
    ]) +
    statGroup('&#128100;', 'Disciplina', [
      statBar('Faltas / p', sta.fouls_per_game, stb.fouls_per_game, false),
      statBar('Amarillas / p', sta.yellow_cards_avg, stb.yellow_cards_avg, false),
      statBar('Rojas / p', sta.red_cards_avg, stb.red_cards_avg, false),
    ]) +
    statGroup('&#128200;', 'Mercados', [
      statBar('BTTS - ambos anotan (%)', sta.btts_rate, stb.btts_rate, true, '%'),
      statBar('+2.5 goles (%)', sta.over_2_5_rate, stb.over_2_5_rate, true, '%'),
      statBar('+1.5 goles (%)', sta.over_1_5_rate, stb.over_1_5_rate, true, '%'),
      statBar('Marca primero (%)', sta.first_goal_rate, stb.first_goal_rate, true, '%'),
      statBar('Remonta (%)', sta.comeback_rate, stb.comeback_rate, true, '%'),
    ]) +
    statGroup('&#127942;', 'Temporada', [
      statBar('Puntos / partido', sta.points_per_game, stb.points_per_game, true),
      statBar('Forma (1-10)', sta.form_rating, stb.form_rating, true),
    ]);

  // ---- FORMA + RECORDS ----
  function formGoals(last5g, last5c, label) {
    if (!last5g || !last5c || !last5g.length) return '';
    return '<div class="form-goals-row">' +
      '<span class="fgr-label">' + label + '</span>' +
      last5g.map(function(g, i) {
        var gc = last5c[i] || 0;
        return '<span class="fgr-game"><span class="fgr-gf">' + g + '</span><span class="fgr-sep">-</span><span class="fgr-ga">' + gc + '</span></span>';
      }).join('') +
    '</div>';
  }

  $('formSection').innerHTML = [
    [teamA, sta], [teamB, stb]
  ].map(function(pair) {
    var name = pair[0], s = pair[1];
    var col = name === teamA ? 'var(--green)' : 'var(--blue)';
    return '<div class="form-card">' +
      '<div class="form-card-header">' +
        '<span class="form-team" style="color:' + col + '">' + esc(name) + '</span>' +
        (s.league_position ? '<span class="form-pos">#' + s.league_position + ' en liga</span>' : '') +
        (s.form_rating ? '<span class="form-rtg">Forma: ' + fmt(s.form_rating, 1) + '/10</span>' : '') +
      '</div>' +
      '<div class="form-badges">' + (s.last_5 || []).slice(0, 5).map(function(r) {
        return '<div class="form-badge badge-' + r + '">' + r + '</div>';
      }).join('') + '</div>' +
      formGoals(s.last_5_goals_scored, s.last_5_goals_conceded, 'GF-GC') +
      '<div class="form-records">' +
        (s.season_record ? '<span class="form-rec-item"><span class="form-rec-lbl">Temporada</span><span class="form-rec-val">' + esc(s.season_record) + '</span></span>' : '') +
        (s.home_record ? '<span class="form-rec-item"><span class="form-rec-lbl">Casa</span><span class="form-rec-val">' + esc(s.home_record) + '</span></span>' : '') +
        (s.away_record ? '<span class="form-rec-item"><span class="form-rec-lbl">Fuera</span><span class="form-rec-val">' + esc(s.away_record) + '</span></span>' : '') +
        (s.clean_sheets != null ? '<span class="form-rec-item"><span class="form-rec-lbl">PC cero</span><span class="form-rec-val">' + s.clean_sheets + '</span></span>' : '') +
      '</div>' +
      (s.current_streak ? '<div class="form-streak">' + esc(s.current_streak) + '</div>' : '') +
      (s.tactical_system ? '<div class="form-tactic"><span class="form-tactic-lbl">Esquema:</span> ' + esc(s.tactical_system) + (s.attacking_style ? ' - ' + esc(s.attacking_style) : '') + '</div>' : '') +
      (s.injury_impact ? '<div class="form-injury injury-' + (s.injury_impact||'').toLowerCase().split('/')[0] + '">Impacto lesiones: ' + esc(s.injury_impact) + '</div>' : '') +
    '</div>';
  }).join('') +
  // Notas propias del usuario
  '<div class="user-notes-card">' +
    '<div class="user-notes-title">Mis notas de analisis</div>' +
    '<textarea class="user-notes-area" id="userStatsNotes" placeholder="Escribe aqui tu propia lectura de las estadisticas, factores que consideras importantes, dudas..."></textarea>' +
    '<div class="user-notes-hint">Solo visible para ti, no se guarda al servidor.</div>' +
  '</div>';

  // Restaurar notas si existen en localStorage
  var notesKey = 'psnotes_' + teamA + '_' + teamB;
  var savedNotes = localStorage.getItem(notesKey);
  var notesEl = document.getElementById('userStatsNotes');
  if (notesEl) {
    if (savedNotes) notesEl.value = savedNotes;
    notesEl.addEventListener('input', function() {
      localStorage.setItem(notesKey, notesEl.value);
    });
  }
}

//  PLAYERS 
function renderPlayers(plrs, teamA, teamB) {
  $('playersTeamATitle').textContent = teamA;
  $('playersTeamBTitle').textContent = teamB;

  function buildList(absences, inForm, fatigue) {
    let html = '';
    if (absences?.length) {
      html += `<div class="player-group-title"> Bajas / Lesiones</div>`;
      html += absences.map(p=>`<div class="player-item">${esc(p)}</div>`).join('');
    }
    if (inForm?.length) {
      html += `<div class="player-group-title"> En forma</div>`;
      html += inForm.map(p=>`<div class="player-item">${esc(p)}</div>`).join('');
    }
    if (fatigue) {
      const cls = fatigue.toLowerCase().includes('alto')?'fat-alto':fatigue.toLowerCase().includes('medio')?'fat-medio':'fat-bajo';
      html += `<div style="margin-top:10px"><div style="font-size:11px;color:var(--text3);margin-bottom:5px">Riesgo de fatiga</div><span class="fatigue-badge ${cls}">${esc(fatigue)}</span></div>`;
    }
    return html || '<div class="notes-text" style="color:var(--text3)">Sin informacin disponible.</div>';
  }

  $('playersTeamA').innerHTML = buildList(plrs.team_a_key_absences, plrs.team_a_in_form, plrs.fatigue_risk_a);
  $('playersTeamB').innerHTML = buildList(plrs.team_b_key_absences, plrs.team_b_in_form, plrs.fatigue_risk_b);
  $('playersNotes').textContent = plrs.notes || '';
}

//  CONTEXT 
function renderContext(ctx, ws, ref, psy, news, teamA, teamB) {
  const infoRow = (key,val) => val ? `<div class="info-row"><span class="info-key">${key}</span><span class="info-val">${esc(String(val))}</span></div>` : '';

  $('matchImportance').innerHTML = [
    infoRow('Importancia', ctx.match_importance),
    infoRow('Fase', ctx.stage),
    ctx.rest_days_team_a ? infoRow(`Das descanso ${teamA}`, ctx.rest_days_team_a) : '',
    ctx.rest_days_team_b ? infoRow(`Das descanso ${teamB}`, ctx.rest_days_team_b) : '',
    ctx.team_a_must_win ? `<div class="info-row"><span class="info-key">${esc(teamA)}</span><span class="info-val"><span class="must-win">DEBE GANAR</span></span></div>` : '',
    ctx.team_b_must_win ? `<div class="info-row"><span class="info-key">${esc(teamB)}</span><span class="info-val"><span class="must-win">DEBE GANAR</span></span></div>` : '',
  ].join('') || '<div class="notes-text" style="color:var(--text3)">Sin datos.</div>';

  $('weatherSection').innerHTML = [
    ws.temperature_celsius!==undefined ? infoRow('Temperatura', ws.temperature_celsius+'C') : '',
    infoRow('Prob. lluvia', ws.rain_probability !== undefined ? ws.rain_probability+'%' : ''),
    infoRow('Viento', ws.wind_kmh !== undefined ? ws.wind_kmh+' km/h' : ''),
    infoRow('Condicin cancha', ws.pitch_condition),
    infoRow('Ventaja local', ws.home_advantage_rating ? ws.home_advantage_rating+'/10' : ''),
    ws.notes ? `<div style="margin-top:8px;font-size:12px;color:var(--text3)">${esc(ws.notes)}</div>` : '',
  ].join('') || '<div class="notes-text" style="color:var(--text3)">Sin datos.</div>';

  $('refereeSection').innerHTML = [
    ref.name && ref.name!=='nombre si disponible' ? infoRow('rbitro', ref.name) : '',
    infoRow('Tarjetas amarillas/pdo.', ref.yellow_cards_avg ? fmt(ref.yellow_cards_avg,1) : ''),
    infoRow('Faltas/partido', ref.fouls_per_game ? fmt(ref.fouls_per_game,1) : ''),
    infoRow('Estilo', ref.style),
    ref.notes ? `<div style="margin-top:8px;font-size:12px;color:var(--text3)">${esc(ref.notes)}</div>` : '',
  ].join('') || '<div class="notes-text" style="color:var(--text3)">Sin datos.</div>';

  $('psychSection').innerHTML = [
    infoRow(`Moral ${teamA}`, psy.team_a_morale),
    infoRow(`Moral ${teamB}`, psy.team_b_morale),
    infoRow('Factor rivalidad', psy.rivalry_factor),
    psy.key_psychological_factor ? `<div style="margin-top:10px;padding:10px 14px;background:var(--bg-card2);border-radius:6px;border-left:3px solid var(--gold);font-size:13px;color:var(--text2)">${esc(psy.key_psychological_factor)}</div>` : '',
  ].join('') || '<div class="notes-text" style="color:var(--text3)">Sin datos.</div>';

  const newsA = news.team_a_news||[], newsB = news.team_b_news||[];
  $('newsSection').innerHTML = `
    <div class="news-two-col">
      <div>
        <div class="news-col-title">${esc(teamA)}</div>
        ${newsA.length ? newsA.map(n=>`<div class="news-item">${esc(n)}</div>`).join('') : '<div class="notes-text" style="color:var(--text3)">Sin noticias.</div>'}
      </div>
      <div>
        <div class="news-col-title">${esc(teamB)}</div>
        ${newsB.length ? newsB.map(n=>`<div class="news-item">${esc(n)}</div>`).join('') : '<div class="notes-text" style="color:var(--text3)">Sin noticias.</div>'}
      </div>
    </div>
    ${news.press_conference_notes ? `<div class="press-note">${esc(news.press_conference_notes)}</div>` : ''}
  `;
}

//  MODELS 
function renderModels(comb, pois, mc, elo, fair, d, teamA, teamB) {
  // Combined
  const cmRows = [
    [teamA+' gana', comb.home_win, 'var(--green)'],
    ['Empate', comb.draw, 'var(--gold)'],
    [teamB+' gana', comb.away_win, 'var(--blue)'],
    ['Ms de 2.5 goles', comb.over_2_5||pois.over_2_5, 'var(--purple)'],
    ['Ambos anotan', comb.btts||pois.btts, 'var(--purple)'],
  ];
  $('combinedModel').innerHTML = cmRows.map(([key,val,color])=>`
    <div class="cm-row">
      <span class="cm-key">${key}</span>
      <div class="cm-bar"><div class="cm-fill" style="width:${Math.round(Number(val)||0)}%;background:${color}"></div></div>
      <span class="cm-val" style="color:${color}">${pct(val)}</span>
    </div>
  `).join('');

  // Fair odds
  $('fairOdds').innerHTML = [
    [teamA, comb.home_win, fair.home_win],
    ['Empate', comb.draw, fair.draw],
    [teamB, comb.away_win, fair.away_win],
    ['Ms de 2.5', pois.over_2_5, fair.over_2_5],
    ['Ambos anotan', pois.btts, fair.btts],
  ].map(([mkt,prob,odds])=>`
    <div class="fo-row">
      <span class="fo-market">${mkt}</span>
      <span class="fo-prob">${pct(prob)} prob.</span>
      <span class="fo-odds">${odds||''}</span>
    </div>
  `).join('');

  // Poisson matrix
  renderPoissonMatrix(d, teamA, teamB);

  // Monte Carlo
  const topScores = mc.top_scores || [];
  if (topScores.length) {
    const maxP = Math.max(...topScores.map(s=>s.pct||0), 0.01);
    $('monteCarloSection').innerHTML = topScores.slice(0,8).map(s=>`
      <div class="mc-row">
        <span class="mc-score">${esc(s.score)}</span>
        <div class="mc-bar-wrap"><div class="mc-bar" style="width:${Math.round((s.pct/maxP)*100)}%"></div></div>
        <span class="mc-pct">${fmt(s.pct,1)}%</span>
      </div>
    `).join('');
  } else {
    $('monteCarloSection').innerHTML = '<div class="notes-text" style="color:var(--text3)">Sin datos de simulacin.</div>';
  }

  // Elo
  const eloH = d.elo_home || 1700, eloA = d.elo_away || 1700;
  $('eloSection').innerHTML = `
    <div class="elo-compare">
      <div class="elo-team">
        <div class="elo-name">${esc(teamA)}</div>
        <div class="elo-score">${eloH}</div>
        <div class="elo-prob">${pct(elo.home_win)} de ganar</div>
      </div>
      <div class="elo-vs">VS</div>
      <div class="elo-team">
        <div class="elo-name">${esc(teamB)}</div>
        <div class="elo-score">${eloA}</div>
        <div class="elo-prob">${pct(elo.away_win)} de ganar</div>
      </div>
    </div>
  `;
}

function renderPoissonMatrix(d, teamA, teamB) {
  const pois = (d.math_models||{}).poisson || {};
  const matrix = pois.score_matrix;
  if (!matrix) { $('poissonMatrix').innerHTML = '<div class="notes-text" style="color:var(--text3)">Sin datos.</div>'; return; }

  const maxGoals = matrix.length - 1;
  let maxVal = 0;
  for (let i=0;i<=maxGoals;i++) for(let j=0;j<=maxGoals;j++) if(matrix[i][j]>maxVal) maxVal=matrix[i][j];

  let html = '<div class="poisson-scroll"><table class="poisson-table"><thead><tr>';
  html += `<th style="font-size:9px">${esc(teamA)}<br>${esc(teamB)}</th>`;
  for(let j=0;j<=maxGoals;j++) html+=`<th>${j}</th>`;
  html+='</tr></thead><tbody>';
  for(let i=0;i<=maxGoals;i++){
    html+=`<tr><th>${i}</th>`;
    for(let j=0;j<=maxGoals;j++){
      const v=matrix[i][j]||0, intensity=maxVal>0?v/maxVal:0;
      const isTop=v===maxVal;
      const bg=isTop?`rgba(227,28,37,${intensity.toFixed(2)})`:`rgba(79,172,254,${(intensity*.85).toFixed(2)})`;
      const tc=intensity>.55?'#fff':'var(--text3)';
      html+=`<td style="background:${bg};color:${tc}${isTop?';border:2px solid var(--red)':''}">${(v*100).toFixed(1)}%</td>`;
    }
    html+='</tr>';
  }
  html+='</tbody></table></div>';
  $('poissonMatrix').innerHTML = html;
}

//  MARKETS 
function renderMarkets(mkts, bm) {
  const names = {
    match_result:'1X2  Resultado', double_chance:'Doble oportunidad',
    btts:'Ambos anotan', over_2_5:'Ms de 2.5 goles', under_2_5:'Menos de 2.5 goles',
    over_3_5:'Ms de 3.5 goles', cards_over_3_5:'Ms de 3.5 tarjetas',
    corners_over_9_5:'Ms de 9.5 crners', scorer:'Goleador'
  };
  $('marketsGrid').innerHTML = Object.entries(mkts).map(([key,m])=>{
    const c = Number(m.confidence)||5;
    const pick = key==='scorer' ? (m.player||m.pick||'') : (m.pick||'');
    return `<div class="mkt-card">
      <div class="mkt-name">${names[key]||key}</div>
      <div class="mkt-pick">${esc(String(pick).toUpperCase())}</div>
      <div class="mkt-conf-bar"><div class="mkt-conf-fill cf-${c}" style="width:${c*10}%"></div></div>
      <div class="mkt-conf-text">Confianza: ${c}/10</div>
      <div class="mkt-reason">${esc(m.reasoning||'')}</div>
    </div>`;
  }).join('') || '<div class="notes-text" style="color:var(--text3)">Sin datos.</div>';

  $('bestOddsSection').innerHTML = `
    <div class="best-odds-row">
      <div class="bo-item"><div class="bo-label">Local</div><div class="bo-val">${bm.current_odds_a||bm.opening_odds_a||''}</div><div class="bo-book">${esc(bm.best_book_a||'')}</div></div>
      <div class="bo-item"><div class="bo-label">Empate</div><div class="bo-val">${bm.current_odds_draw||bm.opening_odds_draw||''}</div><div class="bo-book">${esc(bm.best_book_draw||'')}</div></div>
      <div class="bo-item"><div class="bo-label">Visitante</div><div class="bo-val">${bm.current_odds_b||bm.opening_odds_b||''}</div><div class="bo-book">${esc(bm.best_book_b||'')}</div></div>
    </div>
  `;
  $('oddsMovement').innerHTML = [
    bm.odds_movement ? `<p>${esc(bm.odds_movement)}</p>` : '',
    bm.sharp_money_on ? `<p style="margin-top:8px"><strong style="color:var(--red)">Dinero inteligente:</strong> ${esc(bm.sharp_money_on)}</p>` : ''
  ].join('') || '<span style="color:var(--text3)">Sin datos de movimiento.</span>';
}

//  PARLAYS
var RISK_LABELS = {
  ultra_conservative: { label: 'Ultra Conservador', color: 'var(--green)',  dot: '#22c55e' },
  conservative:       { label: 'Conservador',       color: 'var(--blue)',   dot: '#4facfe' },
  balanced:           { label: 'Balanceado',         color: 'var(--gold)',   dot: '#f5a623' },
  risky:              { label: 'Riesgoso',           color: 'var(--red)',    dot: '#e31c25' },
};

function renderParlays(prlys, teamA, teamB) {
  const order = ['ultra_conservative','conservative','balanced','risky'];
  const matchLabel = (teamA||'') + (teamB ? ' vs ' + teamB : '');

  $('parlaysGrid').innerHTML = order.map(key=>{
    const p = prlys[key]; if(!p) return '';
    const ri = RISK_LABELS[key] || { label: key, color: 'var(--text2)', dot: '#888' };
    const prob = Number(p.win_probability) || 0;
    const odds = Number(p.combined_odds) || 1;
    const ev = Number(p.expected_value) || 0;
    const evClass = ev >= 0 ? 'pf-pos' : 'pf-neg';
    const evText  = (ev >= 0 ? '+' : '') + fmt(ev * 100, 0) + '%';
    const regKey  = 'sp_' + key;
    _mpStore(regKey, { name: p.name||key, riskColor: key, combinedOdds: odds, selections: p.selections||[], matchLabel });

    // Arco de probabilidad SVG
    const r = 28, circ = 2 * Math.PI * r;
    const dash = (prob / 100) * circ;

    return `<div class="parlay-card2" data-odds="${odds}">
      <div class="pc2-header" style="border-left:3px solid ${ri.dot}">
        <div class="pc2-title-block">
          <div class="pc2-name" style="color:${ri.color}">${esc(p.name || ri.label)}</div>
          ${p.strategy ? `<div class="pc2-strategy">${esc(p.strategy)}</div>` : ''}
        </div>
        <div class="pc2-prob-ring">
          <svg width="70" height="70" viewBox="0 0 70 70">
            <circle cx="35" cy="35" r="${r}" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="6"/>
            <circle cx="35" cy="35" r="${r}" fill="none" stroke="${ri.dot}" stroke-width="6"
              stroke-dasharray="${dash.toFixed(1)} ${circ.toFixed(1)}"
              stroke-dashoffset="${(circ * 0.25).toFixed(1)}"
              stroke-linecap="round" transform="rotate(-90 35 35)"/>
            <text x="35" y="39" text-anchor="middle" fill="${ri.dot}" font-size="13" font-weight="800">${Math.round(prob)}%</text>
          </svg>
          <div class="pc2-prob-label">prob.</div>
        </div>
      </div>

      <div class="pc2-sels">
        ${(p.selections||[]).map(s=>`
          <div class="pc2-sel">
            <div class="pc2-sel-info">
              <span class="pc2-sel-market">${esc(s.market||'')}</span>
              <span class="pc2-sel-pick">${esc(s.pick||'')}</span>
              ${s.reasoning ? `<span class="pc2-sel-reason">${esc(s.reasoning)}</span>` : ''}
            </div>
            <span class="pc2-sel-odd">${fmt(s.odds||0)}</span>
          </div>
        `).join('')}
      </div>

      <div class="pc2-footer">
        <div class="pc2-foot-block">
          <div class="pc2-foot-lbl">Momio total</div>
          <div class="pc2-foot-val" style="color:var(--gold)">${fmt(odds)}</div>
        </div>
        <div class="pc2-foot-block">
          <div class="pc2-foot-lbl">Valor esp.</div>
          <div class="pc2-foot-val ${evClass}">${evText}</div>
        </div>
        <div class="pc2-foot-block pc2-calc-block">
          <div class="pc2-foot-lbl">Ganas</div>
          <div class="pc2-calc-win" id="pcwin_${key}">--</div>
        </div>
      </div>

      <button class="bet-this-btn" onclick="betParlay('${regKey}')">Aposte este</button>
    </div>`;
  }).join('');

  // calcular con valor actual si ya hay algo escrito
  updateAllParlayCalc();
}

function updateAllParlayCalc() {
  var inp = document.getElementById('parlayStakeGlobal');
  var stake = inp ? (parseFloat(inp.value) || 0) : 0;
  document.querySelectorAll('.parlay-card2[data-odds]').forEach(function(card) {
    var odds = parseFloat(card.dataset.odds) || 0;
    var key  = card.querySelector('.bet-this-btn') ?
      card.querySelector('.bet-this-btn').getAttribute('onclick').replace("betParlay('sp_","").replace("')","") : '';
    var winEl = card.querySelector('.pc2-calc-win');
    if (!winEl) return;
    if (stake > 0 && odds > 0) {
      var win = Math.round(stake * odds);
      winEl.textContent = '$' + win.toLocaleString('es-MX');
      winEl.style.color = 'var(--green)';
    } else {
      winEl.textContent = '--';
      winEl.style.color = 'var(--text3)';
    }
  });
  // tambien iparlay chips en multi
  document.querySelectorAll('.iparlay-chip[data-odds]').forEach(function(card) {
    var odds  = parseFloat(card.dataset.odds) || 0;
    var winEl = card.querySelector('.ipc-win');
    if (!winEl) return;
    if (stake > 0 && odds > 0) {
      winEl.textContent = '$' + Math.round(stake * odds).toLocaleString('es-MX');
      winEl.style.color = 'var(--green)';
    } else {
      winEl.textContent = '--';
      winEl.style.color = 'var(--text3)';
    }
  });
}

//  ANIMATE 
function animateBars(d) {
  document.querySelectorAll('.pb-fill[data-w]').forEach(el => {
    el.style.width = (el.dataset.w||0) + '%';
  });
  document.querySelectorAll('.cm-fill').forEach(el => {
    // already set inline
  });
}

// ---- MEXICAN ODDS ----
function renderMexicanOdds(data) {
  const mo = data.mexican_odds;
  const mi = data.match_info || {};
  if (!mo) { $('mexicanOddsCard').style.display = 'none'; return; }

  const books = [
    { key: 'playdouit', name: 'PlayDouit', dot: 'dot-playdoit', featured: true },
    { key: 'caliente',  name: 'Caliente',  dot: 'dot-caliente' },
    { key: '1xbet',     name: '1xBet',     dot: 'dot-1xbet' },
  ];

  // Leer momios del formato plano (playdouit_home, caliente_home, etc.)
  const rows = books.map(b => {
    const prefix = b.key + '_';
    const hv = mo[prefix + 'home'] || 0;
    const dv = mo[prefix + 'draw'] || 0;
    const av = mo[prefix + 'away'] || 0;
    const featClass = b.featured ? ' class="odds-row-featured"' : '';
    if (!hv && !dv && !av) return '<tr' + featClass + '><td><div class="mex-book-logo"><div class="mex-dot ' + b.dot + '"></div>' + b.name + (b.featured ? '<span class="odds-principal-tag">Principal</span>' : '') + '</div></td><td class="mex-na" colspan="5">Sin datos aun</td></tr>';
    const h = hv > 0 ? fmt(hv) : '--';
    const d = dv > 0 ? fmt(dv) : '--';
    const a = av > 0 ? fmt(av) : '--';
    return '<tr' + featClass + '><td><div class="mex-book-logo"><div class="mex-dot ' + b.dot + '"></div>' + b.name + (b.featured ? '<span class="odds-principal-tag">Principal</span>' : '') + '</div></td><td class="mex-odds-home">' + h + '</td><td class="mex-odds-draw">' + d + '</td><td class="mex-odds-away">' + a + '</td><td class="mex-odds-extra">--</td><td class="mex-odds-extra">--</td></tr>';
  }).join('');

  const teamA = esc(mi.team_a || 'Local');
  const teamB = esc(mi.team_b || 'Visitante');
  const bestVal = mo.best_value_pick ? '<div class="mex-best-value">Mejor valor: ' + esc(mo.best_value_pick) + '</div>' : '';

  $('mexicanOddsSection').innerHTML =
    '<div class="poisson-scroll"><table class="mex-odds-table">' +
    '<thead><tr><th>Casa</th><th>1 ' + teamA + '</th><th>X Empate</th><th>2 ' + teamB + '</th><th>+2.5</th><th>BTTS</th></tr></thead>' +
    '<tbody>' + rows + '</tbody></table></div>' + bestVal;
}

// ---- PARLAY BUILDER ----
const parlayBuilder = { matches: [] };

function addToParlay() {
  if (!analysisData) return;
  const mi = analysisData.match_info || {};
  const teamA = mi.team_a || 'Local';
  const teamB = mi.team_b || 'Visitante';
  const matchId = teamA + '_' + teamB + '_' + Date.now();

  // Collect top selections from markets
  const markets = analysisData.markets || {};
  const mathM   = analysisData.math_models || {};
  const fair    = mathM.fair_odds || {};
  const sels = [];

  const mktMap = {
    match_result: { label: 'Resultado', getOdds: (p) => p.pick === 'A' ? fair.home_win : p.pick === 'B' ? fair.away_win : fair.draw },
    btts:         { label: 'BTTS',      getOdds: () => fair.btts },
    over_2_5:     { label: 'Over 2.5',  getOdds: () => fair.over_2_5 },
    double_chance:{ label: 'Doble oportunidad', getOdds: () => 1.30 },
  };

  Object.entries(mktMap).forEach(([key, cfg]) => {
    const m = markets[key];
    if (!m) return;
    const odds = cfg.getOdds(m) || 1.50;
    sels.push({ market: cfg.label, pick: m.pick, odds: parseFloat(odds) || 1.50, confidence: m.confidence || 6 });
  });

  parlayBuilder.matches.push({ id: matchId, teamA, teamB, comp: mi.competition || '', sels, selectedSels: [0] });

  $('btnAddParlay').textContent = 'Agregado!';
  $('btnAddParlay').classList.add('added');
  setTimeout(() => {
    $('btnAddParlay').textContent = '+ Agregar al Parlay';
    $('btnAddParlay').classList.remove('added');
  }, 2000);

  renderParlayBuilder();
  showParlayBuilder();
}

function removeFromParlay(id) {
  parlayBuilder.matches = parlayBuilder.matches.filter(m => m.id !== id);
  renderParlayBuilder();
  if (parlayBuilder.matches.length === 0) hideParlayBuilder();
}

function toggleSelInParlay(matchId, selIdx) {
  const match = parlayBuilder.matches.find(m => m.id === matchId);
  if (!match) return;
  const idx = match.selectedSels.indexOf(selIdx);
  if (idx === -1) match.selectedSels.push(selIdx);
  else match.selectedSels.splice(idx, 1);
  renderParlayBuilder();
}

function renderParlayBuilder() {
  const matches = parlayBuilder.matches;
  $('pbCount').textContent = matches.length + (matches.length === 1 ? ' partido' : ' partidos');
  $('pbFabCount').textContent = matches.length;

  if (matches.length === 0) {
    $('pbMatches').innerHTML = '<div class="pb-empty">Agrega partidos desde la vista de resultados para construir tu parlay personalizado.</div>';
    $('pbTotalOdds').textContent = '--';
    $('pbTotalProb').textContent = '--';
    return;
  }

  $('pbMatches').innerHTML = matches.map(m => {
    const chipsHtml = m.sels.map((s, i) => {
      const isSel = m.selectedSels.includes(i);
      return '<span class="pb-sel-chip ' + (isSel ? 'selected' : '') + '" onclick="toggleSelInParlay(\'' + m.id + '\',' + i + ')">' +
        esc(s.market) + ': ' + esc(s.pick) + '<span class="chip-odds">' + fmt(s.odds) + '</span></span>';
    }).join('');
    return '<div class="pb-match-item">' +
      '<div class="pb-match-teams"><span>' + esc(m.teamA) + ' vs ' + esc(m.teamB) + '</span><span class="pb-match-remove" onclick="removeFromParlay(\'' + m.id + '\')">x</span></div>' +
      '<div class="pb-match-pick">' + esc(m.comp) + '</div>' +
      '<div class="pb-match-sels">' + chipsHtml + '</div>' +
      '</div>';
  }).join('');

  // Calculate combined odds from selected picks
  let combined = 1.0;
  let totalConf = 1.0;
  let selCount = 0;
  matches.forEach(m => {
    m.selectedSels.forEach(i => {
      const s = m.sels[i];
      if (s) { combined *= s.odds; selCount++; totalConf *= (s.confidence / 10); }
    });
  });

  $('pbTotalOdds').textContent = selCount > 0 ? fmt(combined) : '--';
  const prob = selCount > 0 ? Math.round(totalConf * 100) : 0;
  $('pbTotalProb').textContent = selCount > 0 ? prob + '%' : '--';
  updateBetCalc();
}

function showParlayBuilder() {
  $('parlayBuilderFloat').style.display = 'flex';
  $('pbFab').style.display = 'none';
}
function hideParlayBuilder() {
  $('parlayBuilderFloat').style.display = 'none';
  if (parlayBuilder.matches.length > 0) $('pbFab').style.display = 'flex';
}
function toggleParlayBuilder() {
  const pb = $('parlayBuilderFloat');
  if (pb.style.display === 'none') showParlayBuilder();
  else hideParlayBuilder();
}
function clearParlay() {
  parlayBuilder.matches = [];
  renderParlayBuilder();
  hideParlayBuilder();
}

// ---- BET CALCULATOR ----
function updateBetCalc() {
  const stakeEl = $('pbStake');
  const winEl   = $('pbWinAmount');
  if (!stakeEl || !winEl) return;

  const stake = parseFloat(stakeEl.value) || 0;
  const oddsEl = $('pbTotalOdds');
  const oddsText = oddsEl ? oddsEl.textContent : '';
  const odds = parseFloat(oddsText) || 0;

  if (stake <= 0 || odds <= 0) {
    winEl.textContent = '--';
    return;
  }
  const totalReturn = stake * odds;
  const profit = totalReturn - stake;
  winEl.innerHTML = '$' + totalReturn.toLocaleString('es-MX', {minimumFractionDigits:0, maximumFractionDigits:0}) +
    ' <span class="pb-win-profit">(+$' + profit.toLocaleString('es-MX', {minimumFractionDigits:0, maximumFractionDigits:0}) + ' ganancia)</span>';
}

// ---- ACCURACY TRACKER ----
const ACC_KEY = 'parlaysmart_accuracy';
let currentAccId = null;

function getAccData() {
  try { return JSON.parse(localStorage.getItem(ACC_KEY) || '[]'); } catch(e) { return []; }
}
function saveAccData(data) {
  localStorage.setItem(ACC_KEY, JSON.stringify(data));
}

function recordPrediction(teamA, teamB, prediction, confidence) {
  const data = getAccData();
  const id = Date.now().toString();
  data.unshift({ id, date: new Date().toISOString().slice(0,10), teamA, teamB, prediction, confidence, result: null });
  if (data.length > 100) data.length = 100;
  saveAccData(data);
  currentAccId = id;
  return id;
}

function markResult(won) {
  if (!currentAccId) return;
  const data = getAccData();
  const entry = data.find(function(e) { return e.id === currentAccId; });
  if (entry) { entry.result = won; saveAccData(data); }
  renderAccuracyBadge();
  renderAccuracyCard();
}

function getAccStats() {
  const data = getAccData();
  const marked = data.filter(function(e) { return e.result !== null; });
  const won = marked.filter(function(e) { return e.result === true; }).length;
  const pct = marked.length ? Math.round(won / marked.length * 100) : null;
  return { total: data.length, marked: marked.length, won: won, lost: marked.length - won, pct: pct };
}

function renderAccuracyBadge() {
  const el = $('accuracyBadge');
  if (!el) return;
  const s = getAccStats();
  if (s.pct !== null) {
    const color = s.pct >= 60 ? '#00c896' : s.pct >= 40 ? '#f0b429' : '#e31c25';
    el.textContent = s.pct + '% efectividad (' + s.won + '/' + s.marked + ')';
    el.style.display = 'inline-flex';
    el.style.color = color;
  } else if (s.total > 0) {
    el.textContent = s.total + ' predicciones sin marcar';
    el.style.display = 'inline-flex';
    el.style.color = '';
  } else {
    el.style.display = 'none';
  }
}

function renderAccuracyCard() {
  const curEl   = $('accCurrentMatch');
  const statsEl = $('accStatsRow');
  if (!curEl || !statsEl) return;

  const s = getAccStats();
  const data = getAccData();
  const current = currentAccId ? data.find(function(e) { return e.id === currentAccId; }) : null;

  // Current prediction mark section
  if (current) {
    const wonActive  = current.result === true  ? ' active' : '';
    const lostActive = current.result === false ? ' active' : '';
    curEl.innerHTML =
      '<div class="acc-question">Prediccion IA: <span>' + esc(current.prediction) + '</span></div>' +
      '<div class="acc-mark-btns">' +
        '<button class="acc-btn acc-btn-won' + wonActive + '" onclick="markResult(true)">Acerte</button>' +
        '<button class="acc-btn acc-btn-lost' + lostActive + '" onclick="markResult(false)">Falle</button>' +
      '</div>';
  } else {
    curEl.innerHTML = '<div class="acc-no-data">Analiza un partido para marcar si acertaste.</div>';
  }

  // Stats row
  if (s.marked === 0) {
    statsEl.innerHTML = '<div class="acc-no-data">Marca tus resultados para ver tu efectividad.</div>';
    return;
  }
  const pctClass = s.pct >= 60 ? 'acc-pct-green' : s.pct >= 40 ? 'acc-pct-gold' : 'acc-pct-red';
  statsEl.innerHTML =
    '<div class="acc-stat"><div class="acc-stat-val ' + pctClass + '">' + s.pct + '%</div><div class="acc-stat-label">Efectividad</div></div>' +
    '<div class="acc-stat"><div class="acc-stat-val acc-pct-green">' + s.won + '</div><div class="acc-stat-label">Aciertos</div></div>' +
    '<div class="acc-stat"><div class="acc-stat-val acc-pct-red">' + s.lost + '</div><div class="acc-stat-label">Fallos</div></div>';
}

function showAccuracyModal() {
  const modal = $('accModal');
  if (!modal) return;
  const body  = $('accModalBody');
  const data  = getAccData();
  const s     = getAccStats();

  const pctClass = s.pct !== null ? (s.pct >= 60 ? '#00c896' : s.pct >= 40 ? '#f0b429' : '#e31c25') : '#888';
  let html = '<div class="acc-modal-summary">' +
    '<div><div class="acc-ms-val" style="color:' + pctClass + '">' + (s.pct !== null ? s.pct + '%' : '--') + '</div><div class="acc-ms-label">Efectividad</div></div>' +
    '<div><div class="acc-ms-val" style="color:#00c896">' + s.won + '</div><div class="acc-ms-label">Aciertos</div></div>' +
    '<div><div class="acc-ms-val" style="color:#e31c25">' + s.lost + '</div><div class="acc-ms-label">Fallos</div></div>' +
    '</div>';

  if (data.length === 0) {
    html += '<div class="acc-no-data">No hay predicciones guardadas aun.</div>';
  } else {
    html += data.map(function(e) {
      const resultHtml = e.result === true
        ? '<span class="acc-hist-result acc-hist-won">Acerte</span>'
        : e.result === false
          ? '<span class="acc-hist-result acc-hist-lost">Falle</span>'
          : '<button class="acc-hist-result acc-hist-pend" onclick="markFromModal(\'' + e.id + '\',true)">Marcar</button>';
      return '<div class="acc-hist-item">' +
        '<div>' +
          '<div class="acc-hist-match">' + esc(e.teamA) + ' vs ' + esc(e.teamB) + '</div>' +
          '<div class="acc-hist-pred">IA predijo: ' + esc(e.prediction) + ' (conf. ' + (e.confidence||'?') + '/10)</div>' +
          '<div class="acc-hist-date">' + esc(e.date) + '</div>' +
        '</div>' +
        resultHtml +
        '</div>';
    }).join('');
  }

  body.innerHTML = html;
  modal.style.display = 'flex';
}

function markFromModal(id, won) {
  const data = getAccData();
  const entry = data.find(function(e) { return e.id === id; });
  if (entry) { entry.result = won; saveAccData(data); }
  renderAccuracyBadge();
  renderAccuracyCard();
  showAccuracyModal();
}

function closeAccModal(event) {
  if (event.target === $('accModal')) $('accModal').style.display = 'none';
}

// Init accuracy badge on page load
window.addEventListener('DOMContentLoaded', function() {
  renderAccuracyBadge();
});

// ========================================================
//  PARTIDOS DE HOY -- SOFASCORE VIEW
// ========================================================

var todayData = null;
var selectedMatches = {};  // id -> match object

function openTodayView() {
  showView('view-today');
  var label = $('todayDateLabel');
  if (label) {
    var d = new Date();
    label.textContent = d.toLocaleDateString('es-MX', { weekday:'long', day:'numeric', month:'long' });
  }
  if (!todayData) {
    loadTodayMatches();
  } else {
    renderTodayMatches(todayData);
  }
}

function loadTodayMatches() {
  $('todayLoading').style.display = 'block';
  $('todayError').style.display   = 'none';
  $('todayLeagues').style.display = 'none';

  var dateStr = new Date().toISOString().slice(0,10);
  fetch('/today-matches?date=' + dateStr)
    .then(function(r) { return r.json(); })
    .then(function(data) {
      todayData = data;
      $('todayLoading').style.display = 'none';
      renderTodayMatches(data);
    })
    .catch(function(err) {
      $('todayLoading').style.display  = 'none';
      $('todayError').style.display    = 'block';
      $('todayErrorText').textContent  = 'Error: ' + err.message;
    });
}

function renderTodayMatches(data) {
  var container = $('todayLeagues');
  container.innerHTML = '';
  var leagues = data.leagues || [];

  if (leagues.length === 0) {
    container.innerHTML = '<div style="padding:60px 20px;text-align:center;color:var(--text3);font-size:14px">No se encontraron partidos para hoy</div>';
    container.style.display = 'block';
    return;
  }

  // Sort leagues by priority
  leagues.sort(function(a,b) { return (a.league_priority||99) - (b.league_priority||99); });

  leagues.forEach(function(league) {
    var matches = league.matches || [];
    if (matches.length === 0) return;

    var groupEl = document.createElement('div');
    groupEl.className = 'league-group';

    // Header
    var headerEl = document.createElement('div');
    headerEl.className = 'league-header';
    headerEl.innerHTML =
      '<span class="league-flag">' + esc(league.league_flag || '') + '</span>' +
      '<span class="league-name">' + esc(league.league_name) + '</span>' +
      '<span class="league-count">' + matches.length + ' partido' + (matches.length !== 1 ? 's' : '') + '</span>';
    groupEl.appendChild(headerEl);

    // Match rows
    matches.forEach(function(m) {
      m.league_name = league.league_name;
      m.league_flag = league.league_flag;
      groupEl.appendChild(buildMatchRow(m));
    });

    container.appendChild(groupEl);
  });

  container.style.display = 'block';
  updateSelBar();
}

function buildMatchRow(m) {
  var el = document.createElement('div');
  el.className = 'match-row' + (selectedMatches[m.id] ? ' selected' : '');
  el.id = 'mrow-' + m.id;

  var isLive = m.status === 'live';
  var formHome = (m.form_home || []).slice(-5);
  var formAway = (m.form_away || []).slice(-5);

  function formDots(arr) {
    return arr.map(function(r) {
      var c = r === 'W' ? 'W' : r === 'D' ? 'D' : 'L';
      return '<div class="form-dot form-dot-' + c + '" title="' + r + '"></div>';
    }).join('');
  }

  var oddsHtml = '';
  if (m.odds_home || m.odds_draw || m.odds_away) {
    oddsHtml = '<div class="match-odds-mini">' +
      (m.odds_home ? '<div class="mo-btn"><div class="mo-label">1</div><div class="mo-val">' + fmt(m.odds_home) + '</div></div>' : '') +
      (m.odds_draw ? '<div class="mo-btn"><div class="mo-label">X</div><div class="mo-val">' + fmt(m.odds_draw) + '</div></div>' : '') +
      (m.odds_away ? '<div class="mo-btn"><div class="mo-label">2</div><div class="mo-val">' + fmt(m.odds_away) + '</div></div>' : '') +
      '</div>';
  }

  var matchQuery = encodeURIComponent(m.team_home + ' vs ' + m.team_away);
  var matchQueryEs = encodeURIComponent(m.team_home + ' vs ' + m.team_away + ' en vivo');

  el.innerHTML =
    '<div class="match-time-col">' +
      '<div class="match-time">' + esc(m.time_mx || '--:--') + '</div>' +
      '<div class="match-status-dot' + (isLive ? ' live' : '') + '"></div>' +
    '</div>' +
    '<div class="match-teams-col">' +
      '<div class="match-team-row">' +
        '<div class="match-team-name">' + esc(m.team_home) + '</div>' +
        '<div class="match-team-form">' + formDots(formHome) + '</div>' +
      '</div>' +
      '<div class="match-vs">VS</div>' +
      '<div class="match-team-row">' +
        '<div class="match-team-name">' + esc(m.team_away) + '</div>' +
        '<div class="match-team-form">' + formDots(formAway) + '</div>' +
      '</div>' +
      (m.hot_note ? '<div class="match-hot-note">' + esc(m.hot_note) + '</div>' : '') +
    '</div>' +
    '<div class="match-odds-col">' +
      oddsHtml +
      '<button class="match-tv-btn" title="Donde ver este partido" data-home="' + esc(m.team_home) + '" data-away="' + esc(m.team_away) + '">TV</button>' +
      '<div class="match-check"><span class="match-check-icon">OK</span></div>' +
    '</div>';

  // Click on TV button shows stream modal, rest of row selects match
  el.addEventListener('click', function(e) {
    var tvBtn = e.target.closest('.match-tv-btn');
    if (tvBtn) {
      e.stopPropagation();
      showStreamModal(m.team_home, m.team_away, m.league_name || '', m.time_mx || '');
    } else {
      toggleMatchSelect(m);
    }
  });
  return el;
}

// ---- STREAMING MODAL ----
var STREAM_SITES = [
  { name: 'Futbol Libre',   icon: 'FL',  color: '#00c896', url: 'https://futbol-libres.su/',            search: 'https://futbol-libres.su/' },
  { name: 'Pirlo TV',       icon: 'PR',  color: '#4facfe', url: 'https://pirlotv.fi/',                  search: 'https://pirlotv.fi/' },
  { name: 'Roja Directa',   icon: 'RD',  color: '#e31c25', url: 'https://www.rojadirecta.me/',          search: 'https://www.rojadirecta.me/' },
  { name: 'Ver en Google',  icon: 'G',   color: '#f0b429', url: null,                                   search: null, google: true },
  { name: 'YouTube',        icon: 'YT',  color: '#ff0000', url: null,                                   search: null, youtube: true },
];

function showStreamModal(teamHome, teamAway, league, time) {
  var existing = $('streamModal');
  if (existing) existing.remove();

  var matchLabel = teamHome + ' vs ' + teamAway;
  var query      = encodeURIComponent(teamHome + ' vs ' + teamAway + ' en vivo gratis');
  var queryYT    = encodeURIComponent(teamHome + ' vs ' + teamAway + ' en vivo');

  var sitesHtml = STREAM_SITES.map(function(s) {
    var href;
    if (s.google) {
      href = 'https://www.google.com/search?q=' + query;
    } else if (s.youtube) {
      href = 'https://www.youtube.com/results?search_query=' + queryYT;
    } else {
      href = s.search;
    }
    return '<a class="stream-site-btn" href="' + href + '" target="_blank" rel="noopener">' +
      '<span class="stream-site-icon" style="background:' + s.color + '18;color:' + s.color + ';border-color:' + s.color + '40">' + s.icon + '</span>' +
      '<span class="stream-site-name">' + s.name + '</span>' +
      '<span class="stream-site-arrow">-&gt;</span>' +
      '</a>';
  }).join('');

  var modal = document.createElement('div');
  modal.id = 'streamModal';
  modal.className = 'stream-modal-overlay';
  modal.innerHTML =
    '<div class="stream-modal" onclick="event.stopPropagation()">' +
      '<div class="stream-modal-header">' +
        '<div class="stream-modal-title">' +
          '<div class="stream-match-label">' + esc(matchLabel) + '</div>' +
          '<div class="stream-match-sub">' + esc(league) + (time ? ' -- ' + esc(time) : '') + '</div>' +
        '</div>' +
        '<button class="stream-close-btn" onclick="closeStreamModal()">x</button>' +
      '</div>' +
      '<div class="stream-modal-tip">Toca un sitio para buscar el partido en vivo</div>' +
      '<div class="stream-sites">' + sitesHtml + '</div>' +
      '<div class="stream-modal-note">Copia el nombre del partido si el sitio no lo muestra automaticamente:<br>' +
        '<span class="stream-copy-text" onclick="copyMatchName(\'' + esc(matchLabel) + '\')" id="streamCopyBtn">' + esc(matchLabel) + ' -- Copiar</span>' +
      '</div>' +
    '</div>';

  modal.addEventListener('click', closeStreamModal);
  document.body.appendChild(modal);
  requestAnimationFrame(function() { modal.classList.add('visible'); });
}

function closeStreamModal() {
  var modal = $('streamModal');
  if (modal) {
    modal.classList.remove('visible');
    setTimeout(function() { if (modal.parentNode) modal.remove(); }, 200);
  }
}

function copyMatchName(text) {
  var btn = $('streamCopyBtn');
  try {
    navigator.clipboard.writeText(text).then(function() {
      if (btn) { btn.textContent = 'Copiado!'; setTimeout(function() { if (btn) btn.textContent = text + ' -- Copiar'; }, 2000); }
    });
  } catch(e) {
    if (btn) btn.select && btn.select();
  }
}

function toggleMatchSelect(m) {
  if (selectedMatches[m.id]) {
    delete selectedMatches[m.id];
  } else {
    selectedMatches[m.id] = m;
  }
  var row = $('mrow-' + m.id);
  if (row) {
    if (selectedMatches[m.id]) row.classList.add('selected');
    else row.classList.remove('selected');
  }
  updateSelBar();
}

function updateSelBar() {
  var count = Object.keys(selectedMatches).length;
  var bar   = $('todaySelBar');
  var countEl = $('selBarCount');
  if (count > 0) {
    bar.style.display = 'flex';
    countEl.textContent = count + ' partido' + (count !== 1 ? 's' : '') + ' seleccionado' + (count !== 1 ? 's' : '');
  } else {
    bar.style.display = 'none';
  }
}

function clearTodaySelection() {
  selectedMatches = {};
  document.querySelectorAll('.match-row.selected').forEach(function(el) { el.classList.remove('selected'); });
  updateSelBar();
}

// ========================================================
//  MULTI-MATCH ANALYSIS
// ========================================================

var multiAnalysisData = null;
var activeParlaySidebar = 0;

function analyzeSelectedMatches() {
  var matches = Object.values(selectedMatches);
  if (matches.length === 0) return;

  $('multiLoadCount').textContent = matches.length;
  showView('view-multi-loading');
  animateMultiLoading();

  var dateStr = new Date().toISOString().slice(0,10);
  fetch('/multi-analyze', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ matches: matches, date: dateStr })
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.error) throw new Error(data.error);
    multiAnalysisData = data;
    renderMultiResults(data);
    showView('view-multi-results');
  })
  .catch(function(err) {
    showView('view-today');
    alert('Error en el analisis: ' + err.message);
  });
}

function animateMultiLoading() {
  var delays = [0, 8000, 18000, 28000];
  var pcts   = [20, 45, 70, 90];
  [1,2,3,4].forEach(function(s, i) {
    setTimeout(function() {
      if (i > 0) {
        var prev = $('mlstep-' + (s-1));
        if (prev) { prev.classList.remove('active'); prev.classList.add('done'); }
      }
      var el = $('mlstep-' + s);
      if (el) el.classList.add('active');
      var bar = $('multiLoadBar');
      if (bar) bar.style.width = pcts[i] + '%';
    }, delays[i]);
  });
}

var mrActiveTab = 0;

function renderMultiResults(data) {
  var matches = data.matches || [];

  // Convertir parlays de objeto a array si es necesario
  var parlaysObj = data.parlays_combinados || data.parlays || [];
  var parlays = Array.isArray(parlaysObj) ? parlaysObj : Object.values(parlaysObj || {});

  mrActiveTab = 0;

  $('mrSubtitle').textContent = matches.length + ' partidos analizados';

  // Construir tabs
  var tabsHtml = matches.map(function(m, i) {
    var label = esc(m.team_home || '') + ' vs ' + esc(m.team_away || '');
    return '<button class="mr-tab' + (i === 0 ? ' active' : '') + '" onclick="switchMrTab(' + i + ')">' + label + '</button>';
  }).join('') +
  '<button class="mr-tab mr-tab-all' + (matches.length === 0 ? ' active' : '') + '" onclick="switchMrTab(' + matches.length + ')">Todos juntos</button>';
  $('mrTabs').innerHTML = tabsHtml;

  // Construir contenido de cada tab de partido
  var matchTabsHtml = matches.map(function(m, i) {
    return '<div class="mr-tab-panel" id="mrPanel-' + i + '" style="' + (i === 0 ? '' : 'display:none') + '">' +
      buildMrMatchCard(m) +
    '</div>';
  }).join('');

  // Tab "Todos juntos"
  var bsp = data.best_single_pick || {};
  var avoid = data.matches_to_avoid || [];
  var riskMap = { 1: 'pl-1', 3: 'pl-3', 5: 'pl-5', 8: 'pl-8' };
  var parlaysHtml = parlays.map(function(p) {
    var cls = riskMap[p.risk_level] || 'pl-5';
    var sels = (p.selections || []).map(function(s) {
      return '<div class="parlay-sel">' +
        '<div><div class="sel-market">' + esc(s.market || '') + '</div>' +
        '<div class="sel-pick">' + esc(s.match || '') + '</div>' +
        '<div class="sel-pick" style="color:var(--gold)">' + esc(s.pick || '') + '</div>' +
        (s.ego_note ? '<div class="sel-reason" style="color:var(--purple)">Ego: ' + esc(s.ego_note) + '</div>' : '') +
        '</div><div class="sel-odds">' + fmt(s.odds || 0) + '</div></div>';
    }).join('');
    return '<div class="parlay-card ' + cls + '">' +
      '<div class="parlay-head"><span class="parlay-name">' + esc(p.name) + '</span></div>' +
      '<div class="parlay-strategy">' + esc(p.strategy || '') + '</div>' +
      '<div class="parlay-sels">' + sels + '</div>' +
      '<div class="parlay-footer">' +
        '<div><div class="pf-label">Momio total</div><div class="pf-val">' + fmt(p.combined_odds || 0) + '</div></div>' +
        '<div><div class="pf-label">Prob.</div><div class="pf-val">' + (p.win_probability || 0) + '%</div></div>' +
        '<div><div class="pf-label">Sugerido</div><div class="pf-val pf-pos" style="font-size:10px">' + esc(p.stake_suggestion || '--') + '</div></div>' +
      '</div></div>';
  }).join('');

  var allTabHtml = '<div class="mr-tab-panel" id="mrPanel-' + matches.length + '" style="display:none">' +
    (data.ego_summary ? '<div class="ego-banner" style="margin-bottom:16px"><div style="font-size:12px;font-weight:700;color:var(--purple);margin-bottom:6px">Resumen psicologico del dia</div><div style="font-size:13px;color:var(--text2)">' + esc(data.ego_summary) + '</div></div>' : '') +
    (bsp.match ? '<div class="best-single-card" style="margin-bottom:16px"><div class="bsc-badge">Mejor pick del dia</div><div class="bsc-match">' + esc(bsp.match) + '</div><div class="bsc-pick">' + esc(bsp.pick || '') + '</div>' + (bsp.odds ? '<div class="bsc-odds">Momio: ' + fmt(bsp.odds) + '</div>' : '') + '<div class="bsc-reason">' + esc(bsp.reason || '') + '</div></div>' : '') +
    (avoid.length ? '<div style="background:rgba(227,28,37,.08);border:1px solid rgba(227,28,37,.2);border-radius:8px;padding:12px 16px;margin-bottom:16px"><div style="font-size:11px;font-weight:800;color:var(--red);margin-bottom:8px">EVITAR</div>' + avoid.map(function(a){ return '<div style="font-size:12px;color:var(--text2);margin-bottom:4px">' + esc(a.match||a) + (a.reason?' -- '+esc(a.reason):'') + '</div>'; }).join('') + '</div>' : '') +
    '<div style="font-size:12px;font-weight:800;color:var(--text3);text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px">Parlays combinados (' + parlays.length + ')</div>' +
    '<div class="mr-bet-row" style="margin-bottom:16px"><span style="font-size:13px;color:var(--text2)">Tu apuesta $</span><input type="number" id="mrStake" class="pb-bet-input" placeholder="100" min="0" step="50" oninput="updateMultiBetCalc()" style="width:100px;margin:0 8px"><span id="mrWinRow" style="display:none;font-size:13px;color:var(--green)">Ganas: <strong id="mrWinAmount"></strong></span></div>' +
    parlaysHtml +
  '</div>';

  $('mrTabContent').innerHTML = matchTabsHtml + allTabHtml;
  updateMultiBetCalc();
}

function switchMrTab(idx) {
  var panels = document.querySelectorAll('.mr-tab-panel');
  var tabs   = document.querySelectorAll('.mr-tab');
  panels.forEach(function(p, i) { p.style.display = i === idx ? '' : 'none'; });
  tabs.forEach(function(t, i)   { t.classList.toggle('active', i === idx); });
  mrActiveTab = idx;
}

function buildMrMatchCard(m) {
  var ego = m.ego_analysis || {};
  var mm  = m.math_models || {};
  var comb = mm.combined || {};
  var pois = mm.poisson  || {};
  var fp   = m.final_prediction || {};
  var mkts = m.markets || {};
  var sh   = m.stats_home || m.team_a_stats || {};
  var sa   = m.stats_away || m.team_b_stats || {};
  var h2h  = m.head_to_head || {};
  var pickColor = m.recommended_pick === 'H' ? 'var(--green)' : m.recommended_pick === 'A' ? 'var(--blue)' : 'var(--gold)';

  var probH = Math.round(comb.home_win || (mkts.home_win && mkts.home_win.prob) || 33);
  var probD = Math.round(comb.draw     || (mkts.draw && mkts.draw.prob)         || 34);
  var probA = Math.round(comb.away_win || (mkts.away_win && mkts.away_win.prob) || 33);

  function formPips(arr) {
    return (arr || []).slice(-5).map(function(r) {
      var c = r === 'W' ? 'W' : r === 'D' ? 'D' : 'L';
      return '<div class="form-pip form-pip-' + c + '">' + r + '</div>';
    }).join('');
  }

  function statRow(label, val) {
    if (!val && val !== 0) return '';
    return '<div class="mrc-stat-row"><span class="mrc-stat-label">' + label + '</span><span class="mrc-stat-val">' + val + '</span></div>';
  }

  function mktBadge(mkt) {
    if (!mkt) return '';
    var col = mkt.rec === 'si' ? 'var(--green)' : mkt.rec === 'no' ? 'var(--red)' : 'var(--text3)';
    return '<span style="color:' + col + ';font-weight:700">' + fmt(mkt.odds || 0) + '</span> <span style="font-size:10px;color:var(--text3)">(' + Math.round(mkt.prob || 0) + '%)</span>';
  }

  var egoRiskCls = 'ego-risk-' + (ego.risk_level || 'bajo').toLowerCase();
  var pressurePlayers = (ego.pressure_players || []).map(function(p) {
    return '<div style="font-size:11px;color:var(--text3);padding:1px 0">-- ' + esc(p) + '</div>';
  }).join('');

  var keyFactors = (fp.key_factors || []).map(function(f) {
    return '<li>' + esc(f) + '</li>';
  }).join('');

  var risks = (fp.risks || []).map(function(r) {
    return '<li style="color:var(--red)">' + esc(r) + '</li>';
  }).join('');

  return '<div class="mr-match-card">' +

    // HEADER
    '<div class="mrc-header">' +
      '<div class="mrc-teams">' +
        '<div class="mrc-teams-name">' + esc(m.team_home || '') + ' vs ' + esc(m.team_away || '') + '</div>' +
        '<div class="mrc-league">' + esc(m.league || '') + (m.time_mx ? ' &mdash; ' + esc(m.time_mx) : '') + '</div>' +
      '</div>' +
      '<div class="mrc-conf">' +
        '<div class="mrc-conf-val">' + (m.confidence || fp.confidence || '--') + '</div>' +
        '<div class="mrc-conf-label">confianza</div>' +
      '</div>' +
      '<div class="mrc-pick-block">' +
        '<div class="mrc-pick-label">Pick recomendado</div>' +
        '<div class="mrc-pick-val" style="color:' + pickColor + '">' + esc(m.pick_label || fp.best_bet || '') + '</div>' +
        '<div class="mrc-pick-odds">' + (m.recommended_odds ? 'Momio: ' + fmt(m.recommended_odds) : '') + '</div>' +
      '</div>' +
    '</div>' +

    // PROBABILIDADES
    (probH || probD || probA ? '<div class="mrc-probs">' +
      '<div class="mrc-prob-col">' +
        '<div class="mrc-prob-label">' + esc(m.team_home || 'Local') + '</div>' +
        '<div class="mrc-prob-bar-wrap"><div class="mrc-prob-bar" style="width:' + probH + '%;background:var(--green)"></div></div>' +
        '<div class="mrc-prob-pct">' + probH + '%</div>' +
      '</div>' +
      '<div class="mrc-prob-col">' +
        '<div class="mrc-prob-label">Empate</div>' +
        '<div class="mrc-prob-bar-wrap"><div class="mrc-prob-bar" style="width:' + probD + '%;background:var(--gold)"></div></div>' +
        '<div class="mrc-prob-pct">' + probD + '%</div>' +
      '</div>' +
      '<div class="mrc-prob-col">' +
        '<div class="mrc-prob-label">' + esc(m.team_away || 'Visitante') + '</div>' +
        '<div class="mrc-prob-bar-wrap"><div class="mrc-prob-bar" style="width:' + probA + '%;background:var(--blue)"></div></div>' +
        '<div class="mrc-prob-pct">' + probA + '%</div>' +
      '</div>' +
    '</div>' : '') +

    // CUERPO
    '<div class="mrc-body">' +

      // Forma
      '<div class="mrc-section">' +
        '<div class="mrc-section-title">Forma reciente</div>' +
        '<div style="margin-bottom:4px;font-size:11px;color:var(--text3)">' + esc(m.team_home || '') + '</div>' +
        '<div class="mrc-form-row">' + formPips(m.form_home) + '</div>' +
        '<div style="margin:6px 0 4px;font-size:11px;color:var(--text3)">' + esc(m.team_away || '') + '</div>' +
        '<div class="mrc-form-row">' + formPips(m.form_away) + '</div>' +
        (h2h.total_meetings ? '<div style="margin-top:8px;font-size:11px;color:var(--text3)">H2H: ' + h2h.home_wins + 'G-' + h2h.draws + 'E-' + h2h.away_wins + 'P (' + h2h.total_meetings + ' partidos)</div>' : '') +
      '</div>' +

      // Stats comparativas
      buildMrTeamStats(m) +

      // Mercados
      '<div class="mrc-section">' +
        '<div class="mrc-section-title">Mercados clave</div>' +
        '<div class="mrc-mkts-grid">' +
          (mkts.btts ? '<div class="mrc-mkt-row"><span class="mrc-mkt-name">BTTS</span>' + mktBadge(mkts.btts) + '</div>' : '') +
          (mkts.over_2_5 ? '<div class="mrc-mkt-row"><span class="mrc-mkt-name">Over 2.5</span>' + mktBadge(mkts.over_2_5) + '</div>' : '') +
          (mkts.over_1_5 ? '<div class="mrc-mkt-row"><span class="mrc-mkt-name">Over 1.5</span>' + mktBadge(mkts.over_1_5) + '</div>' : '') +
          (mkts.double_chance_1x ? '<div class="mrc-mkt-row"><span class="mrc-mkt-name">1X</span>' + mktBadge(mkts.double_chance_1x) + '</div>' : '') +
        '</div>' +
        (fp.reasoning ? '<div class="mrc-key-stat" style="margin-top:8px">' + esc(fp.reasoning) + '</div>' : '<div class="mrc-key-stat">' + esc(m.key_stat || '') + '</div>') +
        (fp.score ? '<div style="margin-top:6px;font-size:12px;color:var(--gold)">Marcador probable: <strong>' + esc(fp.score) + '</strong></div>' : '') +
      '</div>' +

      // Momios por casa
      buildOddsTable(m.mexican_odds, m.team_home, m.team_away) +

      // Factores clave y riesgos
      (keyFactors || risks ? '<div class="mrc-section" style="grid-column:1/-1">' +
        (keyFactors ? '<div class="mrc-section-title">Factores clave</div><ul class="mrc-factors">' + keyFactors + '</ul>' : '') +
        (risks ? '<div class="mrc-section-title" style="margin-top:8px">Riesgos</div><ul class="mrc-factors">' + risks + '</ul>' : '') +
      '</div>' : '') +

      // Ego
      '<div class="ego-block">' +
        '<div class="ego-block-title">Ego y Psicologia <span class="ego-risk-badge ' + egoRiskCls + '">Riesgo ' + esc(ego.risk_level || 'bajo') + '</span></div>' +
        (ego.star_ego_note ? '<div class="ego-note">' + esc(ego.star_ego_note) + '</div>' : '') +
        (ego.locker_room_issues && ego.locker_room_issues !== 'ninguno' ? '<div class="ego-note">Vestuario: ' + esc(ego.locker_room_issues) + '</div>' : '') +
        (ego.revenge_factor && ego.revenge_factor !== 'ninguno' ? '<div class="ego-note">Revancha: ' + esc(ego.revenge_factor) + '</div>' : '') +
        pressurePlayers +
        (ego.ego_impact_on_bet ? '<div class="ego-impact">Impacto en apuesta: ' + esc(ego.ego_impact_on_bet) + '</div>' : '') +
      '</div>' +
    '</div>' +

    buildIndividualParlays(m.individual_parlays || [], esc(m.team_home||'') + ' vs ' + esc(m.team_away||'')) +
    '</div>';
}

function buildOddsTable(odds, teamHome, teamAway) {
  if (!odds) return '';
  var houses = [
    { name: 'PlayDouit', h: odds.playdouit_home, d: odds.playdouit_draw, a: odds.playdouit_away, color: '#00c853', featured: true },
    { name: 'Caliente',  h: odds.caliente_home,  d: odds.caliente_draw,  a: odds.caliente_away,  color: '#e31c25' },
    { name: '1xBet',     h: odds['1xbet_home'],   d: odds['1xbet_draw'],   a: odds['1xbet_away'],   color: '#1a73e8' },
  ].filter(function(h) { return h.h || h.d || h.a; });
  if (!houses.length) return '';

  var rows = houses.map(function(h) {
    var featClass = h.featured ? ' odds-row-featured' : '';
    return '<tr class="' + featClass + '">' +
      '<td class="odds-casa">' +
        '<span class="odds-casa-dot" style="background:' + h.color + '"></span>' + h.name +
        (h.featured ? '<span class="odds-principal-tag">Principal</span>' : '') +
      '</td>' +
      '<td class="odds-val' + (h.h ? '' : ' odds-na') + '">' + (h.h ? fmt(h.h) : '-') + '</td>' +
      '<td class="odds-val' + (h.d ? '' : ' odds-na') + '">' + (h.d ? fmt(h.d) : '-') + '</td>' +
      '<td class="odds-val' + (h.a ? '' : ' odds-na') + '">' + (h.a ? fmt(h.a) : '-') + '</td>' +
    '</tr>';
  }).join('');

  return '<div class="odds-table-wrap">' +
    '<div class="mrc-section-title" style="padding:12px 16px 6px">Momios en casas de apuestas</div>' +
    '<table class="odds-table">' +
      '<thead><tr>' +
        '<th>Casa</th>' +
        '<th>' + esc((teamHome || 'Local').split(' ')[0]) + '</th>' +
        '<th>Empate</th>' +
        '<th>' + esc((teamAway || 'Visit.').split(' ')[0]) + '</th>' +
      '</tr></thead>' +
      '<tbody>' + rows + '</tbody>' +
    '</table>' +
    (odds.best_value ? '<div class="odds-best-value">' + esc(odds.best_value) + '</div>' : '') +
  '</div>';
}

function buildIndividualParlays(parlays, matchLabel) {
  if (!parlays || !parlays.length) return '';
  var riskDot = { green:'#22c55e', blue:'#4facfe', gold:'#f5a623', red:'#e31c25' };
  var riskVar = { green:'var(--green)', blue:'var(--blue)', gold:'var(--gold)', red:'var(--red)' };
  var ml = matchLabel || 'Partido';
  var chips = parlays.map(function(p, idx) {
    var dot = riskDot[p.risk_color] || '#888';
    var col = riskVar[p.risk_color] || 'var(--text2)';
    var odds = Number(p.combined_odds) || 0;
    var prob = Number(p.win_probability) || 0;
    var regKey = 'ip_' + idx + '_' + Date.now();
    _mpStore(regKey, { name: p.name||('Parlay '+(idx+1)), riskColor: p.risk_color||'balanced', combinedOdds: odds, selections: p.selections||[], matchLabel: ml });
    var r = 22, circ = 2 * Math.PI * r;
    var dash = (prob / 100) * circ;
    var sels = (p.selections || []).map(function(s) {
      return '<div class="pc2-sel">' +
        '<div class="pc2-sel-info">' +
          '<span class="pc2-sel-market">' + esc(s.market || '') + '</span>' +
          '<span class="pc2-sel-pick">' + esc(s.pick || '') + '</span>' +
        '</div>' +
        '<span class="pc2-sel-odd">' + fmt(s.odds || 0) + '</span>' +
      '</div>';
    }).join('');
    return '<div class="iparlay-chip parlay-card2" data-odds="' + odds + '" style="border-left:3px solid ' + dot + '">' +
      '<div class="iparlay-header">' +
        '<div style="flex:1">' +
          '<span class="iparlay-name" style="color:' + col + '">' + esc(p.name || '') + '</span>' +
          (p.strategy ? '<div class="pc2-strategy">' + esc(p.strategy) + '</div>' : '') +
        '</div>' +
        '<div class="pc2-prob-ring" style="--sz:54px">' +
          '<svg width="54" height="54" viewBox="0 0 54 54">' +
            '<circle cx="27" cy="27" r="' + r + '" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="5"/>' +
            '<circle cx="27" cy="27" r="' + r + '" fill="none" stroke="' + dot + '" stroke-width="5"' +
              ' stroke-dasharray="' + dash.toFixed(1) + ' ' + circ.toFixed(1) + '"' +
              ' stroke-dashoffset="' + (circ * 0.25).toFixed(1) + '"' +
              ' stroke-linecap="round" transform="rotate(-90 27 27)"/>' +
            '<text x="27" y="31" text-anchor="middle" fill="' + dot + '" font-size="11" font-weight="800">' + Math.round(prob) + '%</text>' +
          '</svg>' +
          '<div class="pc2-prob-label">prob.</div>' +
        '</div>' +
      '</div>' +
      '<div class="pc2-sels">' + sels + '</div>' +
      '<div class="pc2-footer">' +
        '<div class="pc2-foot-block"><div class="pc2-foot-lbl">Momio</div><div class="pc2-foot-val" style="color:var(--gold)">' + fmt(odds) + '</div></div>' +
        '<div class="pc2-foot-block"><div class="pc2-foot-lbl">Si apuestas $<span class="ipc-stake-ref"></span></div><div class="ipc-win pc2-foot-val" style="color:var(--text3)">--</div></div>' +
      '</div>' +
      '<button class="bet-this-btn" onclick="betParlay(\'' + regKey + '\')">Aposte este</button>' +
    '</div>';
  }).join('');
  return '<div class="iparlay-section">' +
    '<div class="iparlay-title">Parlays recomendados</div>' +
    chips +
  '</div>';
}

function buildMrTeamStats(m) {
  var sh = m.stats_home || {};
  var sa = m.stats_away || {};
  if (!Object.keys(sh).length && !Object.keys(sa).length) return '';

  function bar(lbl, va, vb, higherWins, unit) {
    var a = Number(va)||0, b = Number(vb)||0, mx = Math.max(a,b,0.01);
    var pA = Math.round(a/mx*100), pB = Math.round(b/mx*100);
    var u = unit||'';
    var aWin = higherWins ? a>=b : a<=b;
    var bWin = higherWins ? b>a  : b<a;
    return '<div class="mst-row">' +
      '<div class="mst-val-a" style="color:' + (aWin?'var(--green)':'var(--text3)') + '">' + (a||'--') + u + '</div>' +
      '<div class="mst-bars">' +
        '<div class="mst-bar-a" style="width:' + pA + '%"></div>' +
        '<div class="mst-label">' + lbl + '</div>' +
        '<div class="mst-bar-b" style="width:' + pB + '%"></div>' +
      '</div>' +
      '<div class="mst-val-b" style="color:' + (bWin?'var(--blue)':'var(--text3)') + '">' + (b||'--') + u + '</div>' +
    '</div>';
  }

  return '<div class="mst-wrap">' +
    '<div class="mst-header">' +
      '<span style="color:var(--green)">' + esc(m.team_home||'Local') + '</span>' +
      '<span style="color:var(--text3);font-size:10px">ESTADISTICAS</span>' +
      '<span style="color:var(--blue)">' + esc(m.team_away||'Visit.') + '</span>' +
    '</div>' +
    bar('Goles/partido', sh.goals_scored_avg, sa.goals_scored_avg, true) +
    bar('Goles recibidos/p', sh.goals_conceded_avg, sa.goals_conceded_avg, false) +
    bar('xG', sh.xg_avg, sa.xg_avg, true) +
    bar('Tiros al arco/p', sh.shots_on_target_per_game, sa.shots_on_target_per_game, true) +
    bar('Posesion', sh.possession_avg, sa.possession_avg, true, '%') +
    bar('BTTS %', sh.btts_rate, sa.btts_rate, true, '%') +
    bar('+2.5 goles %', sh.over_2_5_rate, sa.over_2_5_rate, true, '%') +
    bar('Amarillas/p', sh.yellow_cards_avg, sa.yellow_cards_avg, false) +
    (sh.home_record||sa.away_record ? '<div class="mst-records">' +
      (sh.home_record ? '<span class="mst-rec"><span class="mst-rec-lbl">Casa</span>' + esc(sh.home_record) + '</span>' : '') +
      (sa.away_record ? '<span class="mst-rec"><span class="mst-rec-lbl">Fuera</span>' + esc(sa.away_record) + '</span>' : '') +
    '</div>' : '') +
  '</div>';
}

function selectParlaySidebar(idx) {
  activeParlaySidebar = idx;
  document.querySelectorAll('.mr-parlay-chip').forEach(function(el, i) {
    if (i === idx) el.classList.add('active');
    else el.classList.remove('active');
  });
  // Update bet calc to show selected parlay's odds
  updateMultiBetCalc();
}

function updateMultiBetCalc() {
  var stakeEl = document.getElementById('mrStake');
  var winEl   = document.getElementById('mrWinAmount');
  var winRow  = document.getElementById('mrWinRow');
  if (!stakeEl || !winEl) return;

  var stake = parseFloat(stakeEl.value) || 0;
  var parlays = multiAnalysisData ? (multiAnalysisData.parlays || []) : [];
  var bestOdds = parlays.reduce(function(best, p) { return Math.max(best, p.combined_odds || 0); }, 0);
  var odds = bestOdds;

  if (stake > 0 && odds > 0) {
    var totalReturn = stake * odds;
    var profit = totalReturn - stake;
    winEl.textContent = '$' + totalReturn.toLocaleString('es-MX', {maximumFractionDigits:0}) +
      ' (ganancia $' + profit.toLocaleString('es-MX', {maximumFractionDigits:0}) + ')';
    if (winRow) winRow.style.display = 'block';
  } else {
    if (winRow) winRow.style.display = 'none';
  }
}

// Inicializar historial al cargar
document.addEventListener('DOMContentLoaded', function() {
  renderHistorial();
});

// ===== MIS PARLAYS TRACKER =====
var MP_KEY = 'parlaysmart_mis_parlays';
// Registry for parlay data referenced by bet buttons
window._mpReg = {};
function _mpStore(key, data) { window._mpReg[key] = data; }
function betParlay(key) {
  var d = window._mpReg[key];
  if (!d) return;
  addMyParlay(d.name, d.riskColor, d.combinedOdds, d.selections, d.matchLabel);
}

function getMisParlays() {
  try { return JSON.parse(localStorage.getItem(MP_KEY) || '[]'); } catch(e) { return []; }
}
function saveMisParlays(arr) {
  localStorage.setItem(MP_KEY, JSON.stringify(arr));
}

function addMyParlay(parlayName, riskColor, combinedOdds, selections, matchLabel) {
  var odds = Number(combinedOdds) || 0;
  var sKey = JSON.stringify(JSON.stringify(selections));

  var modal = document.createElement('div');
  modal.className = 'mp-stake-modal';
  modal.id = 'mpStakeModal';
  modal.innerHTML =
    '<div class="mp-stake-box">' +
      '<div class="mp-stake-header">' +
        '<div class="mp-stake-title">Registrar apuesta</div>' +
        '<button class="mp-stake-close" onclick="document.getElementById(\'mpStakeModal\').remove()">&#10005;</button>' +
      '</div>' +
      '<div class="mp-stake-parlay-name">' + esc(parlayName) + '</div>' +
      '<div class="mp-stake-match">' + esc(matchLabel) + '</div>' +
      '<div class="mp-stake-odds-row">' +
        '<span class="mp-stake-odds-lbl">Momio combinado</span>' +
        '<span class="mp-stake-odds-val">x' + fmt(odds) + '</span>' +
      '</div>' +
      '<div class="mp-stake-field-lbl">Cuanto apostaste?</div>' +
      '<div class="mp-stake-field-row">' +
        '<span class="mp-stake-currency">$</span>' +
        '<input class="mp-stake-input" type="number" id="mpStakeIn" placeholder="0" min="0" oninput="mpCalcLive(' + odds + ')">' +
        '<span class="mp-stake-mxn">MXN</span>' +
      '</div>' +
      '<div class="mp-stake-calc" id="mpStakeCalc" style="display:none">' +
        '<div class="mp-calc-row">' +
          '<span>Apuesta</span><span id="mpCalcStake">$0</span>' +
        '</div>' +
        '<div class="mp-calc-row">' +
          '<span>Pago total</span><span id="mpCalcTotal" style="color:var(--gold)">$0</span>' +
        '</div>' +
        '<div class="mp-calc-row mp-calc-profit-row">' +
          '<span>Ganancia neta</span><span id="mpCalcProfit" style="color:var(--green)">$0</span>' +
        '</div>' +
      '</div>' +
      '<div class="mp-stake-btns">' +
        '<button class="mp-stake-skip" onclick="saveMyParlay(\'' + esc(parlayName) + '\',\'' + riskColor + '\',' + odds + ',' + sKey + ',\'' + esc(matchLabel) + '\',0)">Sin monto</button>' +
        '<button class="mp-stake-ok" onclick="saveMyParlay(\'' + esc(parlayName) + '\',\'' + riskColor + '\',' + odds + ',' + sKey + ',\'' + esc(matchLabel) + '\',parseFloat(document.getElementById(\'mpStakeIn\').value)||0)">Guardar apuesta</button>' +
      '</div>' +
    '</div>';
  document.body.appendChild(modal);
  setTimeout(function(){ var i = document.getElementById('mpStakeIn'); if(i) i.focus(); }, 100);
}

function mpCalcLive(odds) {
  var inp = document.getElementById('mpStakeIn');
  var calc = document.getElementById('mpStakeCalc');
  if (!inp || !calc) return;
  var stake = parseFloat(inp.value) || 0;
  if (stake <= 0) { calc.style.display = 'none'; return; }
  var total  = Math.round(stake * odds);
  var profit = total - stake;
  calc.style.display = 'block';
  document.getElementById('mpCalcStake').textContent  = '$' + stake.toLocaleString('es-MX');
  document.getElementById('mpCalcTotal').textContent  = '$' + total.toLocaleString('es-MX');
  document.getElementById('mpCalcProfit').textContent = '+$' + profit.toLocaleString('es-MX');
}

function saveMyParlay(parlayName, riskColor, combinedOdds, selectionsJson, matchLabel, stake) {
  var modal = document.getElementById('mpStakeModal');
  if (modal) modal.remove();
  var arr = getMisParlays();
  arr.unshift({
    id: Date.now().toString(),
    matchLabel: matchLabel,
    date: new Date().toISOString().slice(0,10),
    parlayName: parlayName,
    riskColor: riskColor,
    combinedOdds: combinedOdds,
    stake: stake || 0,
    selections: JSON.parse(selectionsJson),
    result: null,
    profit: null
  });
  saveMisParlays(arr);
  refreshMpSidebar();
  // Feedback visual
  var btn = document.activeElement;
  if (btn) { btn.textContent = 'Registrado!'; setTimeout(function(){ btn.textContent = 'Aposte este'; }, 1500); }
}

function markMpResult(id, won) {
  var arr = getMisParlays();
  var entry = arr.find(function(x) { return x.id === id; });
  if (!entry) return;
  entry.result = won;
  if (won && entry.stake > 0) {
    entry.profit = Math.round((entry.stake * entry.combinedOdds) - entry.stake);
  } else if (!won && entry.stake > 0) {
    entry.profit = -entry.stake;
  } else {
    entry.profit = null;
  }
  saveMisParlays(arr);
  renderMyParlays();
  refreshMpSidebar();
}

function undoMpResult(id) {
  var arr = getMisParlays();
  var entry = arr.find(function(x) { return x.id === id; });
  if (!entry) return;
  entry.result = null;
  entry.profit = null;
  saveMisParlays(arr);
  renderMyParlays();
  refreshMpSidebar();
}

function deleteMpEntry(id) {
  var arr = getMisParlays().filter(function(x) { return x.id !== id; });
  saveMisParlays(arr);
  renderMyParlays();
  refreshMpSidebar();
}

function confirmClearParlays() {
  if (confirm('Borrar todo el historial de parlays?')) {
    saveMisParlays([]);
    renderMyParlays();
    refreshMpSidebar();
  }
}

function renderMyParlays() {
  var arr = getMisParlays();
  var list = document.getElementById('mpList');
  var sub  = document.getElementById('mpSubtitle');
  if (!list) return;

  var total    = arr.length;
  var won      = arr.filter(function(x){ return x.result === true; }).length;
  var lost     = arr.filter(function(x){ return x.result === false; }).length;
  var pend     = arr.filter(function(x){ return x.result === null; }).length;
  var decided  = won + lost;
  var rate     = decided > 0 ? Math.round(won / decided * 100) : null;
  var invested = arr.reduce(function(s,x){ return s + (x.stake||0); }, 0);
  var returned = arr.filter(function(x){ return x.result === true && x.stake > 0; })
                    .reduce(function(s,x){ return s + Math.round(x.stake * x.combinedOdds); }, 0);
  var profit   = returned - arr.filter(function(x){ return x.result !== null && x.stake > 0; })
                                .reduce(function(s,x){ return s + x.stake; }, 0);

  // Actualizar barra financiera
  var el = function(id){ return document.getElementById(id); };
  if (el('mpStatTotal'))    el('mpStatTotal').textContent    = total;
  if (el('mpStatWon'))      el('mpStatWon').textContent      = won;
  if (el('mpStatLost'))     el('mpStatLost').textContent     = lost;
  if (el('mpStatPending'))  el('mpStatPending').textContent  = pend;
  if (el('mpStatRate'))     el('mpStatRate').textContent     = rate !== null ? rate + '%' : '--%';
  if (el('mpStatInvested')) el('mpStatInvested').textContent = '$' + invested.toLocaleString('es-MX');
  if (el('mpStatReturned')) el('mpStatReturned').textContent = '$' + returned.toLocaleString('es-MX');
  if (el('mpStatProfit')) {
    var pEl = el('mpStatProfit');
    pEl.textContent  = (profit >= 0 ? '+$' : '-$') + Math.abs(profit).toLocaleString('es-MX');
    pEl.style.color  = profit > 0 ? 'var(--green)' : profit < 0 ? 'var(--red)' : 'var(--text2)';
  }
  // Barra W/L
  if (el('mpWlFill')) {
    el('mpWlFill').style.width = (rate !== null ? rate : 0) + '%';
  }
  if (sub) sub.innerHTML = total + ' parlay' + (total !== 1 ? 's' : '') +
    (rate !== null ? ' &middot; <strong style="color:var(--green)">' + rate + '% acierto</strong>' : '');

  if (!arr.length) {
    list.innerHTML = '<div class="mp-empty">Aun no has registrado ningun parlay.<br><br>En cualquier analisis presiona <strong>"Aposte este"</strong> en el parlay que elegiste.</div>';
    return;
  }

  var riskCol = { ultra_conservative:'#22c55e', conservative:'#4facfe', balanced:'#f5a623', risky:'#e31c25',
                  green:'#22c55e', blue:'#4facfe', gold:'#f5a623', red:'#e31c25' };

  list.innerHTML = arr.map(function(p) {
    var dot = riskCol[p.riskColor] || '#888';
    var isWon  = p.result === true;
    var isLost = p.result === false;
    var isPend = p.result === null;

    // Bloque financiero de la tarjeta
    var stakeStr   = p.stake > 0 ? '$' + p.stake.toLocaleString('es-MX') : 'Sin monto';
    var potWin     = p.stake > 0 ? Math.round(p.stake * (p.combinedOdds||1)) : 0;
    var potWinStr  = potWin > 0 ? '$' + potWin.toLocaleString('es-MX') : '--';
    var profitStr  = '';
    var profitCol  = 'var(--text3)';
    if (isWon && p.stake > 0) {
      var g = Math.round(p.stake * p.combinedOdds) - p.stake;
      profitStr = '+$' + g.toLocaleString('es-MX') + ' ganancia';
      profitCol = 'var(--green)';
    } else if (isLost && p.stake > 0) {
      profitStr = '-$' + p.stake.toLocaleString('es-MX') + ' perdido';
      profitCol = 'var(--red)';
    }

    // Selecciones resumidas
    var sels = (p.selections || []).slice(0, 3).map(function(s) {
      var pick = s.pick || s.market || (typeof s === 'string' ? s : '');
      var odd  = s.odds ? ' <span style="color:var(--gold)">@' + s.odds + '</span>' : '';
      return '<span class="mp-sel-chip">' + esc(pick) + odd + '</span>';
    }).join('');
    if ((p.selections||[]).length > 3) sels += '<span class="mp-sel-more">+' + ((p.selections.length)-3) + '</span>';

    // Estado
    var stateClass = isPend ? 'mp-state-pend' : isWon ? 'mp-state-won' : 'mp-state-lost';
    var stateText  = isPend ? 'Pendiente' : isWon ? '&#10003; Gane' : '&#10007; Perdi';

    // Botones de accion
    var actHtml = '';
    if (isPend) {
      actHtml = '<div class="mp-result-btns">' +
        '<button class="mp-rbtn mp-rbtn-won" onclick="markMpResult(\'' + p.id + '\',true)">&#10003; Gane este</button>' +
        '<button class="mp-rbtn mp-rbtn-lost" onclick="markMpResult(\'' + p.id + '\',false)">&#10007; Perdi este</button>' +
      '</div>';
    } else {
      actHtml = '<button class="mp-rbtn mp-rbtn-undo" onclick="undoMpResult(\'' + p.id + '\')">Deshacer resultado</button>';
    }

    return '<div class="mpv-card ' + stateClass + '">' +
      // Header
      '<div class="mpv-card-top">' +
        '<div class="mpv-card-left">' +
          '<div class="mpv-parlay-name" style="border-left:3px solid ' + dot + ';padding-left:8px">' + esc(p.parlayName) + '</div>' +
          '<div class="mpv-match">' + esc(p.matchLabel) + '</div>' +
          '<div class="mpv-date">' + esc(p.date) + '</div>' +
        '</div>' +
        '<div class="mpv-card-right">' +
          '<div class="mpv-state ' + stateClass + '">' + stateText + '</div>' +
          '<div class="mpv-odds">x' + fmt(p.combinedOdds||0) + '</div>' +
        '</div>' +
      '</div>' +
      // Recuento financiero
      '<div class="mpv-finance">' +
        '<div class="mpv-fin-block">' +
          '<div class="mpv-fin-lbl">Apueste</div>' +
          '<div class="mpv-fin-val">' + stakeStr + '</div>' +
        '</div>' +
        '<div class="mpv-fin-arrow">&#8594;</div>' +
        '<div class="mpv-fin-block">' +
          '<div class="mpv-fin-lbl">' + (isPend ? 'Ganarias' : isWon ? 'Cobre' : 'Perdi') + '</div>' +
          '<div class="mpv-fin-val" style="color:' + (isLost ? 'var(--red)' : isPend ? 'var(--gold)' : 'var(--green)') + '">' +
            (isLost ? '-$' + p.stake.toLocaleString('es-MX') : potWinStr) +
          '</div>' +
        '</div>' +
        (profitStr ? '<div class="mpv-fin-profit" style="color:' + profitCol + '">' + profitStr + '</div>' : '') +
      '</div>' +
      // Selecciones
      (sels ? '<div class="mpv-sels">' + sels + '</div>' : '') +
      // Acciones
      '<div class="mpv-actions">' +
        actHtml +
        '<button class="mpv-del" onclick="deleteMpEntry(\'' + p.id + '\')" title="Eliminar">&#128465;</button>' +
      '</div>' +
    '</div>';
  }).join('');
}

function refreshMpSidebar() {
  var arr = getMisParlays();
  var badge = document.getElementById('mpBadge');
  var mini  = document.getElementById('mpMiniStats');
  if (badge) badge.textContent = arr.length || '';
  if (!mini) return;
  if (!arr.length) { mini.textContent = 'Sin parlays registrados aun.'; return; }
  var won  = arr.filter(function(x){ return x.result === true; }).length;
  var lost = arr.filter(function(x){ return x.result === false; }).length;
  var pend = arr.filter(function(x){ return x.result === null; }).length;
  var rate = (won+lost) > 0 ? Math.round(won/(won+lost)*100) + '% acierto' : 'sin resultados aun';
  mini.innerHTML = won + ' ganados &middot; ' + lost + ' perdidos &middot; ' + pend + ' pendientes<br><strong style="color:var(--green)">' + rate + '</strong>';
}

// Inicializar al cargar
document.addEventListener('DOMContentLoaded', function() {
  renderHistorial();
  refreshMpSidebar();
  checkAuth();
});

// ========================================================
//  PARTIDOS DE LA SEMANA -- landing page
// ========================================================

var _wmCache = {};
var _wmActiveDate = null;

var _WM_DAYS_ES = ['Dom','Lun','Mar','Mie','Jue','Vie','Sab'];
var _WM_MONTHS_ES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];

function _wmDateStr(offset) {
  var d = new Date();
  d.setDate(d.getDate() + offset);
  var y = d.getFullYear();
  var m = String(d.getMonth() + 1).padStart(2, '0');
  var day = String(d.getDate()).padStart(2, '0');
  return y + '-' + m + '-' + day;
}

function _wmDayLabel(offset) {
  var d = new Date();
  d.setDate(d.getDate() + offset);
  if (offset === 0) return 'Hoy';
  if (offset === 1) return 'Man';
  return _WM_DAYS_ES[d.getDay()] + ' ' + d.getDate();
}

function initWeekMatches() {
  var tabs = document.getElementById('wmDayTabs');
  var headerDays = document.getElementById('wmHeaderDays');
  if (!tabs) return;
  tabs.innerHTML = '';
  if (headerDays) headerDays.innerHTML = '';
  for (var i = 0; i < 6; i++) {
    (function(offset) {
      var btn = document.createElement('button');
      btn.className = 'wm-tab' + (offset === 0 ? ' active' : '');
      btn.textContent = _wmDayLabel(offset);
      btn.onclick = function() {
        document.querySelectorAll('.wm-tab').forEach(function(b) { b.classList.remove('active'); });
        btn.classList.add('active');
        _wmSelectedLeague = null;
        wmLoadDay(_wmDateStr(offset));
      };
      tabs.appendChild(btn);
      // Mini chips en el header (solo primeros 4)
      if (headerDays && offset < 4) {
        var chip = document.createElement('span');
        chip.className = 'wm-hdr-chip' + (offset === 0 ? ' active' : '');
        chip.textContent = _wmDayLabel(offset);
        headerDays.appendChild(chip);
      }
    })(i);
  }
}

function wmLoadDay(dateStr) {
  if (_wmCache[dateStr]) { wmRender(_wmCache[dateStr], dateStr); return; }
  var content = document.getElementById('wmContent');
  if (content) content.innerHTML = '<div class="wm-loading">Cargando partidos...</div>';
  _wmActiveDate = dateStr;
  fetch('/today-matches?date=' + dateStr, { credentials: 'include' })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      _wmCache[dateStr] = data;
      if (_wmActiveDate === dateStr) wmRender(data, dateStr);
    })
    .catch(function() {
      var content2 = document.getElementById('wmContent');
      if (content2) content2.innerHTML = '<div class="wm-empty">No se pudieron cargar los partidos</div>';
    });
}

var _wmSelectedLeague = null;
var _wmCurrentData = null;
var _wmSelection = {}; // id -> match object

function wmRender(data, dateStr) {
  _wmCurrentData = data;
  var content = document.getElementById('wmContent');
  if (!content) return;
  var leagues = (data.leagues || []).filter(function(l) { return l.matches && l.matches.length; });
  if (!leagues.length) {
    content.innerHTML = '<div class="wm-empty">Sin partidos para este dia</div>';
    return;
  }

  // Ordenar ligas: ligas principales primero
  var _TOP = ['World Cup','UEFA Champions','Premier League','La Liga','Liga MX','Bundesliga','Serie A','Ligue 1','MLS','CONCACAF','Copa America','Copa MX','Liga de Expansion'];
  leagues.sort(function(a, b) {
    var ai = _TOP.findIndex(function(t) { return (a.league_name||'').indexOf(t) !== -1; });
    var bi = _TOP.findIndex(function(t) { return (b.league_name||'').indexOf(t) !== -1; });
    ai = ai === -1 ? 999 : ai;
    bi = bi === -1 ? 999 : bi;
    return ai - bi;
  });

  // Si no hay liga seleccionada, elegir la primera
  var leagueNames = leagues.map(function(l) { return l.league_name || ''; });
  if (!_wmSelectedLeague || leagueNames.indexOf(_wmSelectedLeague) === -1) {
    _wmSelectedLeague = leagueNames[0];
  }

  // Chips de ligas
  var chipsHtml = '<div class="wm-league-chips" id="wmLeagueChips">';
  leagues.forEach(function(league) {
    var lname = league.league_name || '';
    var flag = league.league_flag ? '<img src="' + league.league_flag + '" class="wm-chip-flag" onerror="this.style.display=\'none\'">' : '';
    var active = lname === _wmSelectedLeague ? ' active' : '';
    var count = (league.matches || []).length;
    chipsHtml += '<button class="wm-league-chip' + active + '" onclick="wmSelectLeague(' + JSON.stringify(lname) + ')">';
    chipsHtml += flag + lname + ' <span class="wm-chip-count">' + count + '</span></button>';
  });
  chipsHtml += '</div>';

  // Partidos de la liga seleccionada
  var selLeague = leagues.find(function(l) { return (l.league_name || '') === _wmSelectedLeague; });
  var matchesHtml = '<div class="wm-matches-list">';
  if (selLeague) {
    (selLeague.matches || []).forEach(function(m) {
      var homeTeam = (m.team_home || '').replace(/'/g, '&#39;');
      var awayTeam = (m.team_away || '').replace(/'/g, '&#39;');
      var time = m.time || '';
      var statusShort = m.status || 'NS';
      var timeBadge = '';
      if (statusShort === 'LIVE' || statusShort === '1H' || statusShort === '2H' || statusShort === 'HT' || statusShort === 'ET') {
        var min = m.elapsed ? m.elapsed + "'" : 'LIVE';
        timeBadge = '<span class="wm-live-badge">' + min + '</span>';
        if (m.score_home !== null && m.score_home !== undefined) {
          timeBadge += ' <span class="wm-score">' + m.score_home + '-' + m.score_away + '</span>';
        }
      } else if (statusShort === 'FT' || statusShort === 'AET' || statusShort === 'PEN') {
        var sc = (m.score_home !== null && m.score_home !== undefined) ? m.score_home + '-' + m.score_away : '';
        timeBadge = '<span class="wm-ft-badge">FT ' + sc + '</span>';
      }
      var mid = (m.id || (homeTeam + '_' + awayTeam)).replace(/['"]/g,'');
      var isSel = !!_wmSelection[mid];
      var selClass = isSel ? ' selected' : '';
      matchesHtml += '<button class="wm-match' + selClass + '" onclick="wmToggleMatch(' + JSON.stringify(mid) + ',' + JSON.stringify(homeTeam) + ',' + JSON.stringify(awayTeam) + ')">';
      matchesHtml += '<span class="wm-match-check">' + (isSel ? '&#10003;' : '') + '</span>';
      matchesHtml += '<span class="wm-match-time">' + (timeBadge || time) + '</span>';
      matchesHtml += '<span class="wm-match-teams">' + homeTeam + ' <span class="wm-vs">vs</span> ' + awayTeam + '</span>';
      matchesHtml += '</button>';
    });
  }
  matchesHtml += '</div>';

  content.innerHTML = chipsHtml + matchesHtml;
}

function wmSelectLeague(lname) {
  _wmSelectedLeague = lname;
  if (_wmCurrentData) wmRender(_wmCurrentData, _wmActiveDate);
}

function wmToggleMatch(mid, homeTeam, awayTeam) {
  if (_wmSelection[mid]) {
    delete _wmSelection[mid];
  } else {
    _wmSelection[mid] = { id: mid, team_home: homeTeam, team_away: awayTeam, query_text: homeTeam + ' vs ' + awayTeam };
  }
  wmUpdateSelBar();
  // Re-render solo la lista para reflejar estado
  if (_wmCurrentData) wmRender(_wmCurrentData, _wmActiveDate);
}

function wmUpdateSelBar() {
  var bar = document.getElementById('wmSelBar');
  var count = Object.keys(_wmSelection).length;
  if (!bar) return;
  if (count === 0) {
    bar.style.display = 'none';
  } else {
    bar.style.display = 'flex';
    var el = document.getElementById('wmSelCount');
    if (el) el.textContent = count + (count === 1 ? ' partido seleccionado' : ' partidos seleccionados');
  }
}

function wmClearSel() {
  _wmSelection = {};
  wmUpdateSelBar();
  if (_wmCurrentData) wmRender(_wmCurrentData, _wmActiveDate);
}

function wmAnalyzeSel() {
  var matches = Object.values(_wmSelection);
  if (!matches.length) return;
  if (matches.length === 1) {
    // Analisis individual
    var m = matches[0];
    var inp = document.getElementById('searchInput');
    if (inp) inp.value = m.query_text;
    wmClearSel();
    startAnalysis();
  } else {
    // Multi-analisis
    wmClearSel();
    analyzeMatchList(matches);
  }
}

function wmToggle() {
  var body = document.getElementById('wmBody');
  var arrow = document.getElementById('wmArrow');
  if (!body) return;
  var open = body.style.display !== 'none';
  body.style.display = open ? 'none' : 'block';
  if (arrow) arrow.style.transform = open ? '' : 'rotate(180deg)';
  if (!open && !_wmCurrentData) {
    wmLoadDay(_wmDateStr(0));
  }
}

function analyzeMatchList(matches) {
  if (!matches || !matches.length) return;
  // Usa la funcion multi-analisis existente
  selectedMatches = {};
  matches.forEach(function(m) { selectedMatches[m.id] = m; });
  analyzeSelectedMatches();
}

// Llamar initWeekMatches despues del login exitoso
var _origHideLogin = hideLogin;
hideLogin = function() {
  _origHideLogin();
  initWeekMatches();
};

// ========================================================
//  PREDICCION DE TORNEO
// ========================================================

function openTournamentView() {
  showView('view-tournament');
  document.getElementById('trnResult').style.display = 'none';
  document.getElementById('trnLoading').style.display = 'none';
  document.getElementById('trnError').textContent = '';
}

function trnQuick(text) {
  document.getElementById('trnInput').value = text;
  startTournamentPrediction();
}

async function startTournamentPrediction() {
  var inp = document.getElementById('trnInput');
  var err = document.getElementById('trnError');
  var loading = document.getElementById('trnLoading');
  var result = document.getElementById('trnResult');
  var query = inp ? inp.value.trim() : '';
  if (!query) { if (err) err.textContent = 'Escribe el nombre del torneo'; return; }
  err.textContent = '';
  result.style.display = 'none';
  loading.style.display = 'flex';

  try {
    var r = await fetch('/predict-tournament', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tournament: query })
    });
    var data = await r.json();
    loading.style.display = 'none';
    if (!r.ok) { err.textContent = data.error || 'Error al predecir'; return; }
    renderTournamentResult(data);
    result.style.display = 'block';
  } catch(e) {
    loading.style.display = 'none';
    err.textContent = 'Error de conexion';
  }
}

function renderTournamentResult(data) {
  var el = document.getElementById('trnResult');
  if (!el) return;
  var html = '';

  // Header
  html += '<div class="trn-res-title">' + (data.tournament_name || '') + '</div>';
  if (data.current_stage) html += '<div class="trn-res-stage">Fase actual: ' + data.current_stage + '</div>';

  // Ganador predicho
  if (data.predicted_winner) {
    html += '<div class="trn-winner-card">';
    html += '<div class="trn-winner-label">GANADOR PREDICHO</div>';
    html += '<div class="trn-winner-name">' + data.predicted_winner + '</div>';
    html += '<div class="trn-winner-prob">' + (data.winner_probability || '') + ' probabilidad</div>';
    if (data.winner_reason) html += '<div class="trn-winner-reason">' + data.winner_reason + '</div>';
    html += '</div>';
  }

  // Top contendientes
  if (data.top_contenders && data.top_contenders.length) {
    html += '<div class="trn-section-title">TOP CONTENDIENTES</div>';
    html += '<div class="trn-contenders">';
    data.top_contenders.forEach(function(c, i) {
      var medal = i === 0 ? '&#127947;' : i === 1 ? '&#129352;' : i === 2 ? '&#129353;' : (i+1)+'.';
      html += '<div class="trn-contender">';
      html += '<span class="trn-contender-pos">' + medal + '</span>';
      html += '<div class="trn-contender-info">';
      html += '<span class="trn-contender-name">' + (c.team || c.name || '') + '</span>';
      if (c.probability) html += '<span class="trn-contender-prob">' + c.probability + '</span>';
      if (c.reason) html += '<div class="trn-contender-reason">' + c.reason + '</div>';
      html += '</div></div>';
    });
    html += '</div>';
  }

  // Grupos / fases (si aplica)
  if (data.group_predictions && data.group_predictions.length) {
    html += '<div class="trn-section-title">PREDICCION POR GRUPOS</div>';
    html += '<div class="trn-groups">';
    data.group_predictions.forEach(function(g) {
      html += '<div class="trn-group-card">';
      html += '<div class="trn-group-name">Grupo ' + (g.group || '') + '</div>';
      if (g.teams) {
        g.teams.forEach(function(t, i) {
          var pass = i < 2 ? ' trn-advances' : '';
          html += '<div class="trn-group-team' + pass + '">';
          html += '<span class="trn-group-pos">' + (i+1) + '</span>';
          html += '<span>' + (t.team || t) + '</span>';
          if (t.points !== undefined) html += '<span class="trn-group-pts">' + t.points + ' pts</span>';
          html += '</div>';
        });
      }
      html += '</div>';
    });
    html += '</div>';
  }

  // Llave de eliminacion directa
  if (data.bracket && data.bracket.length) {
    html += '<div class="trn-section-title">LLAVE PREDICHA</div>';
    html += '<div class="trn-bracket">';
    data.bracket.forEach(function(round) {
      html += '<div class="trn-round">';
      html += '<div class="trn-round-name">' + (round.round || '') + '</div>';
      (round.matches || []).forEach(function(m) {
        var winner = m.predicted_winner || '';
        html += '<div class="trn-bracket-match">';
        html += '<span class="' + (winner === m.team_a ? 'trn-bm-win' : '') + '">' + (m.team_a || '') + '</span>';
        html += '<span class="trn-bm-vs">vs</span>';
        html += '<span class="' + (winner === m.team_b ? 'trn-bm-win' : '') + '">' + (m.team_b || '') + '</span>';
        if (m.predicted_score) html += '<span class="trn-bm-score">' + m.predicted_score + '</span>';
        html += '</div>';
      });
      html += '</div>';
    });
    html += '</div>';
  }

  // Analisis general
  if (data.analysis) {
    html += '<div class="trn-section-title">ANALISIS</div>';
    html += '<div class="trn-analysis">' + data.analysis + '</div>';
  }

  el.innerHTML = html;
}

// ========================================================
//  PANEL DE ADMIN - GESTION DE PINS
// ========================================================

function openAdminPanel() {
  document.getElementById('adminPanel').style.display = 'flex';
  adminLoadPins();
}

function closeAdminPanel() {
  document.getElementById('adminPanel').style.display = 'none';
  document.getElementById('adminNewPin').style.display = 'none';
}

function adminLoadPins() {
  var list = document.getElementById('adminPinList');
  list.innerHTML = '<div class="admin-loading">Cargando...</div>';

  const isAdmin = localStorage.getItem('isAdmin') === 'true' || window.isAdmin;

  fetch('/admin/pins', {
    credentials: 'include',
    headers: { 'X-Admin': isAdmin ? 'true' : 'false' }
  })
    .then(function(r) {
      console.log('Load PINs response status:', r.status);
      return r.json().then(function(data) {
        return { ok: r.ok, data: data };
      });
    })
    .then(function(res) {
      console.log('Load PINs response:', res);
      if (!res.ok || !res.data || !res.data.length) {
        list.innerHTML = '<div class="admin-empty">No hay PINs activos</div>';
        return;
      }
      list.innerHTML = res.data.map(function(p) {
        return '<div class="admin-pin-row">' +
          '<span class="admin-pin-num">' + p.code + '</span>' +
          '<span class="admin-pin-dur">' + p.label + '</span>' +
          '<span class="admin-pin-rem">Expira en ' + p.remaining + '</span>' +
          '<button class="admin-del-btn" onclick="adminDeletePin(\'' + p.code + '\')">&#128465;</button>' +
        '</div>';
      }).join('');
    })
    .catch(function(err) {
      console.error('Load PINs error:', err);
      list.innerHTML = '<div class="admin-empty">Error al cargar</div>';
    });
}

function adminCreatePin(days) {
  const isAdmin = localStorage.getItem('isAdmin') === 'true' || window.isAdmin;
  if (!isAdmin) {
    alert('❌ Solo administradores pueden crear PINs');
    return;
  }

  fetch('/admin/pins', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-Admin': isAdmin ? 'true' : 'false'
    },
    body: JSON.stringify({ days: days })
  })
    .then(function(r) {
      console.log('Create PIN response status:', r.status);
      return r.json().then(function(data) {
        return { ok: r.ok, data: data };
      });
    })
    .then(function(res) {
      console.log('Create PIN response:', res);
      if (res.ok) {
        document.getElementById('adminPinCode').textContent = res.data.code;
        document.getElementById('adminNewPin').style.display = 'flex';
        adminLoadPins();
      } else {
        alert('Error: ' + (res.data.error || 'Error desconocido'));
      }
    })
    .catch(function(err) {
      console.error('Create PIN error:', err);
      alert('Error: ' + err.message);
    });
}

function adminCopyPin() {
  var code = document.getElementById('adminPinCode').textContent;
  navigator.clipboard.writeText(code).then(function() {
    var btn = document.querySelector('.admin-copy-btn');
    btn.textContent = 'Copiado!';
    setTimeout(function() { btn.textContent = 'Copiar'; }, 2000);
  });
}

function adminDeletePin(code) {
  if (!confirm('¿Eliminar PIN ' + code + '?')) return;

  const isAdmin = localStorage.getItem('isAdmin') === 'true' || window.isAdmin;

  fetch('/admin/pins/' + code, {
    method: 'DELETE',
    credentials: 'include',
    headers: { 'X-Admin': isAdmin ? 'true' : 'false' }
  })
    .then(function(r) {
      console.log('Delete PIN response status:', r.status);
      return r.json().then(function(data) {
        return { ok: r.ok, data: data };
      });
    })
    .then(function(res) {
      console.log('Delete PIN response:', res);
      if (res.ok) {
        adminLoadPins();
      } else {
        alert('Error: ' + (res.data.error || 'Error desconocido'));
      }
    })
    .catch(function(err) {
      console.error('Delete PIN error:', err);
      alert('Error: ' + err.message);
    });
}

