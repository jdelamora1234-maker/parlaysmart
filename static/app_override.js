// Override startAnalysis para funcionar con backend FastAPI
const originalStartAnalysis = window.startAnalysis;

window.startAnalysis = async function() {
  const inp = document.getElementById('searchInput');
  const query = inp ? inp.value.trim() : '';
  
  if (!query) {
    const errEl = document.getElementById('searchError');
    if (errEl) errEl.textContent = 'Escribe el partido que quieres analizar.';
    return;
  }
  
  const parts = query.split('vs').map(s => s.trim());
  if (parts.length !== 2 || !parts[0] || !parts[1]) {
    const errEl = document.getElementById('searchError');
    if (errEl) errEl.textContent = 'Formato: Equipo1 vs Equipo2';
    return;
  }
  
  const [team_a, team_b] = parts;
  
  // Mostrar loading
  const loadingView = document.getElementById('view-loading');
  if (loadingView) loadingView.style.display = 'block';
  
  try {
    const url = `/analyze?team_a=${encodeURIComponent(team_a)}&team_b=${encodeURIComponent(team_b)}&team_a_xg=1.8&team_b_xg=0.9`;
    const res = await fetch(url);
    
    if (!res.ok) throw new Error('Error del servidor');
    
    const data = await res.json();
    
    // Mostrar resultados
    renderAnalysisResults(data, team_a, team_b);
    
    if (loadingView) loadingView.style.display = 'none';
    const resultsView = document.getElementById('view-results');
    if (resultsView) resultsView.style.display = 'block';
    
  } catch(err) {
    if (loadingView) loadingView.style.display = 'none';
    const errEl = document.getElementById('searchError');
    if (errEl) errEl.textContent = 'Error: ' + err.message;
  }
};

function renderAnalysisResults(data, team_a, team_b) {
  // Poblar header del partido
  const hTeamA = document.getElementById('hTeamA');
  const hTeamB = document.getElementById('hTeamB');
  if (hTeamA) hTeamA.textContent = team_a;
  if (hTeamB) hTeamB.textContent = team_b;
  
  // Poblar probabilidades
  const probs = data.probabilities || {};
  const hProbA = document.getElementById('hProbA');
  const hProbD = document.getElementById('hProbD');
  const hProbB = document.getElementById('hProbB');
  if (hProbA) hProbA.textContent = `${(probs.home * 100).toFixed(1)}%`;
  if (hProbD) hProbD.textContent = `${(probs.draw * 100).toFixed(1)}%`;
  if (hProbB) hProbB.textContent = `${(probs.away * 100).toFixed(1)}%`;
  
  // Poblar parlays en la sección de parlays
  const parlaysGrid = document.getElementById('parlaysGrid');
  if (parlaysGrid) {
    const parlays = data.parlays || {};
    parlaysGrid.innerHTML = '';
    
    const parlay_types = [
      {key: 'ultra_conservador', title: '🟢 Ultra Conservador', color: 'green'},
      {key: 'conservador', title: '🔵 Conservador', color: 'blue'},
      {key: 'balanceado', title: '🟡 Balanceado', color: 'yellow'},
      {key: 'riesgoso', title: '🔴 Riesgoso', color: 'red'}
    ];
    
    parlay_types.forEach(pt => {
      const parlay = parlays[pt.key];
      if (!parlay) return;
      
      const card = document.createElement('div');
      card.className = 'parlay-card';
      card.innerHTML = `
        <div class="parlay-header" style="color: ${pt.color}">${pt.title}</div>
        <div class="parlay-content">
          <strong>Picks:</strong>
          <ul>${parlay.picks.map(p => `<li>${p}</li>`).join('')}</ul>
          <strong>Momio Total:</strong> ${parlay.momio_total}<br>
          <strong>Ganancia x $1000:</strong> ${parlay.ganancia_$1000}<br>
          <strong>Confianza:</strong> ${parlay.confianza}%
        </div>
      `;
      parlaysGrid.appendChild(card);
    });
  }
}
