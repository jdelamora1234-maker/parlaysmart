// PARLAYSMART — Logic

// Register Service Worker (PWA)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/static/sw.js').catch(() => {}));
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
  qsa('.page').forEach(p => p.classList.remove('active'));
  $('page-' + pageId).classList.add('active');
  qsa('.snav-item, .ptab, .mob-tab').forEach(n => {
    if (n.dataset.page === pageId) n.classList.add('active');
    else n.classList.remove('active');
  });
  qs('.pages-container')?.scrollTo(0, 0);
}

function goHome() {
  showView('view-landing');
  $('queryInput').value = '';
}

function setExample(text) {
  $('queryInput').value = text;
  qsa('.snav').forEach(b => b.classList.remove('active'));
}
function setExampleAndGo(text) {
  $('queryInput').value = text;
  startAnalysis();
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
async function startAnalysis() {
  const query = $('queryInput').value.trim();
  const errEl = $('searchError');

  if (!query) {
    errEl.textContent = 'Escribe el partido que quieres analizar.';
    return;
  }
  errEl.textContent = '';

  resetLoading();
  showView('view-loading');
  animateLoading();

  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({query})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Error del servidor');

    analysisData = data;
    renderResults(data);
    switchPage('overview', null);
    showView('view-results');
    setTimeout(() => animateBars(data), 300);

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
  $('sidebarMatchInfo').innerHTML = `
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
  // H2H
  $('h2hSection').innerHTML = `
    <div class="h2h-row">
      <div class="h2h-stat"><div class="h2h-val">${h2h.team_a_wins??''}</div><div class="h2h-lbl">${esc(teamA)}</div></div>
      <div class="h2h-stat"><div class="h2h-val">${h2h.draws??''}</div><div class="h2h-lbl">Empates</div></div>
      <div class="h2h-stat"><div class="h2h-val">${h2h.team_b_wins??''}</div><div class="h2h-lbl">${esc(teamB)}</div></div>
    </div>
    ${h2h.avg_goals_per_game ? `<div style="text-align:center;font-size:12px;color:var(--text3);margin-top:6px">Promedio de goles: ${fmt(h2h.avg_goals_per_game,1)} por partido</div>` : ''}
    ${h2h.trend ? `<div class="h2h-trend">${esc(h2h.trend)}</div>` : ''}
    ${(h2h.last_results||[]).length ? `<div class="h2h-results">${h2h.last_results.map(r=>`<div class="h2h-res-item">${esc(r)}</div>`).join('')}</div>` : ''}
  `;

  // Compare
  const rows = [
    ['Goles anotados/partido', sta.goals_scored_avg, stb.goals_scored_avg],
    ['Goles recibidos/partido', sta.goals_conceded_avg, stb.goals_conceded_avg],
    ['xG promedio', sta.xg_avg, stb.xg_avg],
    ['xGA promedio', sta.xga_avg, stb.xga_avg],
    ['Tiros al arco/partido', sta.shots_on_target_per_game, stb.shots_on_target_per_game],
    ['Posesin %', sta.possession_avg, stb.possession_avg],
    ['Rating de forma', sta.form_rating, stb.form_rating],
  ];
  $('statsCompare').innerHTML = `
    <div class="sc-header"><span>${esc(teamA)}</span><span>Estadstica</span><span>${esc(teamB)}</span></div>
    ${rows.map(([lbl,a,b])=>{
      const av=Number(a)||0, bv=Number(b)||0, mx=Math.max(av,bv,0.01);
      const pA=Math.round(av/mx*100), pB=Math.round(bv/mx*100);
      return `<div class="stat-row">
        <div style="text-align:right">
          <div class="stat-val-a" style="color:${av>=bv?'var(--green)':'var(--text2)'}">${fmt(av,1)}</div>
          <div class="stat-bars" style="justify-content:flex-end"><div class="sbar-a" style="width:${pA}%;max-width:70px"></div></div>
        </div>
        <div class="stat-label">${lbl}</div>
        <div>
          <div class="stat-val-b" style="color:${bv>av?'var(--blue)':'var(--text2)'}">${fmt(bv,1)}</div>
          <div class="stat-bars"><div class="sbar-b" style="width:${pB}%;max-width:70px"></div></div>
        </div>
      </div>`;
    }).join('')}
  `;

  // Form
  $('formSection').innerHTML = [
    [teamA, sta.last_5, sta.form_rating, sta.current_streak],
    [teamB, stb.last_5, stb.form_rating, stb.current_streak],
  ].map(([name, form, rating, streak])=>`
    <div class="form-row">
      <div class="form-team">${esc(name)}</div>
      <div class="form-badges">${(form||[]).slice(0,5).map(r=>'<div class="form-badge badge-'+r+'">'+r+'</div>').join('')}</div>
      <div class="form-rating">${rating ? 'Forma: ' + rating + '/10' : ''}${streak ? ' - ' + esc(streak) : ''}</div>
    </div>
  `).join('');
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
function renderParlays(prlys, teamA, teamB) {
  const order = ['ultra_conservative','conservative','balanced','risky'];
  const emojis = {ultra_conservative:'',conservative:'',balanced:'',risky:''};

  $('parlaysGrid').innerHTML = order.map(key=>{
    const p = prlys[key]; if(!p) return '';
    const lvl = p.risk_level||1;
    const ev = Number(p.expected_value)||0;
    const evClass = ev>=0?'pf-pos':'pf-neg';
    const evText = ev>=0?'+'+fmt(ev*100,0)+'%':fmt(ev*100,0)+'%';

    return `<div class="parlay-card pl-${lvl}">
      <div class="parlay-head">
        <div class="parlay-name">${emojis[key]} ${esc(p.name||key)}</div>
        <div class="parlay-risk-badge">Riesgo ${lvl}/10</div>
      </div>
      ${p.strategy?`<div class="parlay-strategy">${esc(p.strategy)}</div>`:''}
      <div class="parlay-sels">
        ${(p.selections||[]).map(s=>`
          <div class="parlay-sel">
            <div>
              <div class="sel-market">${esc(s.market||'')}</div>
              <div class="sel-pick">${esc(s.pick||'')}</div>
              <div class="sel-reason">${esc(s.reasoning||'')}${s.risk?`<span style="color:var(--red)">  ${esc(s.risk)}</span>`:''}</div>
            </div>
            <div class="sel-odds">${fmt(s.odds||1.5)}</div>
          </div>
        `).join('')}
      </div>
      <div class="parlay-footer">
        <div><div class="pf-label">Momio combinado</div><div class="pf-val">${fmt(p.combined_odds||1)}</div></div>
        <div><div class="pf-label">Prob. ganar</div><div class="pf-val">${pct(p.win_probability)}</div></div>
        <div><div class="pf-label">Valor esp.</div><div class="pf-val ${evClass}">${evText}</div></div>
      </div>
    </div>`;
  }).join('');
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
    { key: 'playdoit', name: 'PlayDouit', dot: 'dot-playdoit' },
    { key: 'caliente', name: 'Caliente',  dot: 'dot-caliente' },
    { key: 'codere',   name: 'Codere',    dot: 'dot-codere' },
    { key: '1xbet',    name: '1xBet',     dot: 'dot-1xbet' },
  ];

  const rows = books.map(b => {
    const o = mo[b.key];
    if (!o || !o.available) return '<tr><td><div class="mex-book-logo"><div class="mex-dot ' + b.dot + '"></div>' + b.name + '</div></td><td class="mex-na" colspan="5">No disponible</td></tr>';
    const h = o.home > 0 ? fmt(o.home) : '—';
    const d = o.draw > 0 ? fmt(o.draw) : '—';
    const a = o.away > 0 ? fmt(o.away) : '—';
    const ov = o.over_2_5 > 0 ? fmt(o.over_2_5) : '—';
    const bt = o.btts > 0 ? fmt(o.btts) : '—';
    return '<tr><td><div class="mex-book-logo"><div class="mex-dot ' + b.dot + '"></div>' + b.name + '</div></td><td class="mex-odds-home">' + h + '</td><td class="mex-odds-draw">' + d + '</td><td class="mex-odds-away">' + a + '</td><td class="mex-odds-extra">' + ov + '</td><td class="mex-odds-extra">' + bt + '</td></tr>';
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
    $('pbTotalOdds').textContent = '—';
    $('pbTotalProb').textContent = '—';
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

  $('pbTotalOdds').textContent = selCount > 0 ? fmt(combined) : '—';
  const prob = selCount > 0 ? Math.round(totalConf * 100) : 0;
  $('pbTotalProb').textContent = selCount > 0 ? prob + '%' : '—';
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
