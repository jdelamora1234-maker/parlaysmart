// ParlaySmart v2026 - App simplificado para FastAPI backend

const $ = id => document.getElementById(id);

function startAnalysis() {
  const inp = $('searchInput');
  const query = inp ? inp.value.trim() : '';
  
  if (!query) {
    showError('Escribe el partido que quieres analizar');
    return;
  }
  
  const parts = query.split('vs').map(s => s.trim());
  if (parts.length !== 2 || !parts[0] || !parts[1]) {
    showError('Formato: Equipo1 vs Equipo2');
    return;
  }
  
  hideError();
  showView('view-loading');
  
  const [team_a, team_b] = parts;
  const url = `/analyze?team_a=${encodeURIComponent(team_a)}&team_b=${encodeURIComponent(team_b)}&team_a_xg=1.8&team_b_xg=0.9`;
  
  fetch(url)
    .then(r => {
      if (!r.ok) throw new Error('Error del servidor');
      return r.json();
    })
    .then(data => {
      renderResults(data, team_a, team_b);
      showView('view-results');
    })
    .catch(err => {
      showView('view-landing');
      showError(err.message);
    });
}

function renderResults(data, team_a, team_b) {
  if (!data.parlays) return;
  
  // Match header
  $('hTeamA').textContent = team_a;
  $('hTeamB').textContent = team_b;
  $('hDate').textContent = new Date().toLocaleDateString();
  
  const probs = data.probabilities || {};
  $('hProbA').textContent = `${(probs.home * 100).toFixed(1)}%`;
  $('hProbD').textContent = `${(probs.draw * 100).toFixed(1)}%`;
  $('hProbB').textContent = `${(probs.away * 100).toFixed(1)}%`;
  
  $('matchTitle').textContent = `${team_a} vs ${team_b}`;
  
  // Parlays
  const parlays = data.parlays || {};
  renderParlay('parlay-ultra', parlays.ultra_conservador);
  renderParlay('parlay-conservador', parlays.conservador);
  renderParlay('parlay-balanceado', parlays.balanceado);
  renderParlay('parlay-riesgoso', parlays.riesgoso);
}

function renderParlay(elemId, parlay) {
  if (!parlay) return;
  const elem = $(elemId);
  if (!elem) return;
  
  let html = '';
  if (parlay.picks) {
    html += '<strong>Picks:</strong><ul>';
    parlay.picks.forEach(p => {
      html += `<li>${p}</li>`;
    });
    html += '</ul>';
  }
  if (parlay.momio_total) {
    html += `<strong>Momio:</strong> ${parlay.momio_total}<br>`;
  }
  if (parlay.ganancia_$1000) {
    html += `<strong>Ganancia x $1000:</strong> ${parlay.ganancia_$1000}<br>`;
  }
  
  elem.innerHTML = html;
}

function showView(viewId) {
  document.querySelectorAll('.view').forEach(v => {
    v.style.display = 'none';
  });
  const v = $(viewId);
  if (v) v.style.display = 'block';
}

function showError(msg) {
  const err = $('searchError');
  if (err) err.textContent = msg;
}

function hideError() {
  const err = $('searchError');
  if (err) err.textContent = '';
}

function goHome() {
  showView('view-landing');
  const inp = $('searchInput');
  if (inp) inp.value = '';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  showView('view-landing');
});
