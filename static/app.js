function analyzeMatch() {
  const input = document.getElementById('teamInput').value.trim();
  if (!input) {
    showError('Por favor ingresa dos equipos (ej: Barcelona vs Real Madrid)');
    return;
  }

  const [teamA, teamB] = input.split('vs').map(t => t.trim());
  if (!teamA || !teamB) {
    showError('Formato: Equipo1 vs Equipo2');
    return;
  }

  showLoading(true);
  hideError();

  fetch(`/analyze?team_a=${encodeURIComponent(teamA)}&team_b=${encodeURIComponent(teamB)}&team_a_xg=1.8&team_b_xg=0.9`)
    .then(res => {
      if (!res.ok) throw new Error('Error en el servidor');
      return res.json();
    })
    .then(data => {
      showResults(teamA, teamB, data);
      showLoading(false);
    })
    .catch(err => {
      showError('Error: ' + err.message);
      showLoading(false);
    });
}

function showLoading(show) {
  document.getElementById('loading').classList.toggle('hidden', !show);
}

function showError(msg) {
  const err = document.getElementById('error');
  err.textContent = msg;
  err.classList.remove('hidden');
}

function hideError() {
  document.getElementById('error').classList.add('hidden');
}

function showResults(teamA, teamB, data) {
  document.getElementById('matchTitle').textContent = `${teamA} vs ${teamB}`;
  
  const probs = data.probabilities || {};
  document.getElementById('probTeamA').textContent = teamA;
  document.getElementById('probTeamAVal').textContent = `${(probs.home * 100).toFixed(1)}%`;
  document.getElementById('probDrawVal').textContent = `${(probs.draw * 100).toFixed(1)}%`;
  document.getElementById('probTeamB').textContent = teamB;
  document.getElementById('probTeamBVal').textContent = `${(probs.away * 100).toFixed(1)}%`;

  const parlays = data.parlays || {};
  
  renderParlay('parlay-ultra', parlays.ultra_conservador);
  renderParlay('parlay-conservador', parlays.conservador);
  renderParlay('parlay-balanceado', parlays.balanceado);
  renderParlay('parlay-riesgoso', parlays.riesgoso);

  document.querySelector('.search-box').classList.add('hidden');
  document.getElementById('results').classList.remove('hidden');
}

function renderParlay(elementId, parlay) {
  const elem = document.getElementById(elementId);
  if (!parlay) {
    elem.textContent = 'Sin datos';
    return;
  }

  let html = '';
  if (parlay.picks) {
    html += '<strong>Picks:</strong><ul>';
    parlay.picks.forEach(pick => {
      html += `<li>${pick}</li>`;
    });
    html += '</ul>';
  }
  if (parlay.odds) {
    html += `<strong>Momio:</strong> ${parlay.odds}<br>`;
  }
  if (parlay.momio_total) {
    html += `<strong>Momio total:</strong> ${parlay.momio_total}<br>`;
  }
  if (parlay.probability) {
    html += `<strong>Probabilidad:</strong> ${parlay.probability}<br>`;
  }
  
  elem.innerHTML = html;
}

function reset() {
  document.querySelector('.search-box').classList.remove('hidden');
  document.getElementById('results').classList.add('hidden');
  document.getElementById('teamInput').value = '';
}
