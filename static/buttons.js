/**
 * FUNCIONALIDAD DE BOTONES - ParlaySmart
 * Implementación de: agregar partidos, guardar parlays, filtros, deportes
 */

// ==================== DEPORTES ====================
let currentSport = 'Futbol';

function setSport(sport) {
  currentSport = sport;
  localStorage.setItem('currentSport', sport);

  document.querySelectorAll('.snav').forEach(btn => btn.classList.remove('active'));
  if (event && event.target) event.target.classList.add('active');

  // Actualizar el header para mostrar deporte seleccionado
  const header = document.querySelector('.analysis-header') ||
                 document.querySelector('.search-header') ||
                 document.querySelector('.header');

  if (header) {
    let sportEmoji = {
      'Futbol': '⚽',
      'Americano': '🏈',
      'Basquet': '🏀',
      'Beisbol': '⚾',
      'Tenis': '🎾',
      'MMA / UFC': '🥊',
      'Hockey': '🏒'
    }[sport] || '🎯';

    // Actualizar el texto visible
    document.querySelectorAll('.sport-label, .current-sport, h2, h3').forEach(el => {
      if (el.textContent.includes('Que partido') || el.textContent.includes('analizar')) {
        el.textContent = `${sportEmoji} ${sport} - ¿Qué partido quieres analizar?`;
      }
    });
  }

  // Agregar deporte al input si existe
  const searchInput = document.getElementById('searchInput') ||
                      document.getElementById('queryInput') ||
                      document.querySelector('input[placeholder*="partido"]');

  if (searchInput && searchInput.value === '') {
    searchInput.placeholder = `Ej: Team A vs Team B (${sport})`;
  }

  console.log(`✅ Deporte cambió a: ${sport}`);
  showNotification(`🎯 Analizando: ${sport}`);
}

// ==================== MÚLTIPLES PARTIDOS ====================
let matchCount = 1;

function addMatch() {
  matchCount++;
  const container = document.getElementById('matchesContainer') || createMatchesContainer();
  
  const newMatch = document.createElement('div');
  newMatch.className = 'match-input-group';
  newMatch.id = `match-${matchCount}`;
  newMatch.innerHTML = `
    <input type="text" class="match-input" placeholder="Ej: Real Madrid vs Barcelona" data-match-id="${matchCount}">
    <button class="btn-remove-match" onclick="removeMatch(${matchCount})">✕</button>
  `;
  
  container.appendChild(newMatch);
  console.log(`✅ Partido #${matchCount} agregado`);
}

function removeMatch(id) {
  const match = document.getElementById(`match-${id}`);
  if (match) {
    match.remove();
    matchCount--;
    console.log(`✅ Partido #${id} eliminado`);
  }
}

function createMatchesContainer() {
  const container = document.createElement('div');
  container.id = 'matchesContainer';
  container.className = 'matches-container';
  
  const analysisSection = document.querySelector('.analysis-section');
  if (analysisSection) {
    analysisSection.insertBefore(container, analysisSection.firstChild);
  }
  
  return container;
}

// ==================== GUARDAR PARLAYS ====================
let savedParlays = JSON.parse(localStorage.getItem('savedParlays') || '[]');

function saveParlay(parlay) {
  const id = Date.now();
  const parlay_obj = {
    id: id,
    date: new Date().toLocaleString('es-AR'),
    sport: currentSport,
    ...parlay
  };
  
  savedParlays.push(parlay_obj);
  localStorage.setItem('savedParlays', JSON.stringify(savedParlays));
  
  showNotification('✅ Parlay guardado en "MIS PARLAYS"');
  console.log(`✅ Parlay ${id} guardado`);
  updateMyParlaysView();
}

function removeSavedParlay(id) {
  savedParlays = savedParlays.filter(p => p.id !== id);
  localStorage.setItem('savedParlays', JSON.stringify(savedParlays));
  updateMyParlaysView();
  console.log(`✅ Parlay ${id} eliminado`);
}

function updateMyParlaysView() {
  const container = document.getElementById('myParlaysContainer');
  if (!container) return;
  
  if (savedParlays.length === 0) {
    container.innerHTML = '<div class="empty-state">Sin parlays guardados aun.</div>';
    return;
  }
  
  container.innerHTML = savedParlays.map(p => `
    <div class="saved-parlay">
      <div class="parlay-meta">
        <span>${p.sport}</span>
        <span>${p.date}</span>
      </div>
      <div class="parlay-content">
        <p><strong>${p.winner || 'N/A'}</strong> - Confianza: ${p.confidence || 'N/A'}%</p>
        <p>Odds: ${p.odds || 'N/A'} | Prob: ${p.prob || 'N/A'}%</p>
      </div>
      <button onclick="removeSavedParlay(${p.id})" class="btn-delete">🗑️</button>
    </div>
  `).join('');
}

// ==================== FILTROS ====================
let selectedFilter = 'today';

function setFilter(filter) {
  selectedFilter = filter;
  localStorage.setItem('selectedFilter', filter);
  
  document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
  
  filterHistory();
  console.log(`✅ Filtro: ${filter}`);
}

function filterHistory() {
  const historyItems = document.querySelectorAll('.history-item');
  const now = new Date();
  
  historyItems.forEach(item => {
    const itemDate = new Date(item.dataset.date || now);
    let show = false;
    
    switch(selectedFilter) {
      case 'today':
        show = itemDate.toDateString() === now.toDateString();
        break;
      case 'week':
        const weekAgo = new Date(now.getTime() - 7*24*60*60*1000);
        show = itemDate >= weekAgo;
        break;
      case 'month':
        show = itemDate.getMonth() === now.getMonth() && itemDate.getFullYear() === now.getFullYear();
        break;
      case 'all':
        show = true;
        break;
    }
    
    item.style.display = show ? 'block' : 'none';
  });
}

// ==================== VISTAS ====================
function openTodayView() {
  console.log('✅ Vista: HOY');
  setFilter('today');
  showView('view-history');
}

function openTournamentView() {
  console.log('✅ Vista: TORNEO');
  showView('view-tournament');
}

function openAdminPanel() {
  // Solo admins pueden ver el panel de keys
  const isAdmin = localStorage.getItem('isAdmin') === 'true' || window.isAdmin === true;

  if (!isAdmin) {
    showNotification('❌ Solo administradores pueden gestionar keys');
    console.warn('Acceso denegado: Usuario no es admin');
    return;
  }

  console.log('✅ Abriendo Panel de Keys (Admin)');
  const panel = document.getElementById('adminPanel');
  if (panel) panel.style.display = 'flex';
}

function closeAdminPanel() {
  const panel = document.getElementById('adminPanel');
  if (panel) panel.style.display = 'none';
}

function showView(viewId) {
  document.querySelectorAll('.view').forEach(v => v.style.display = 'none');
  const view = document.getElementById(viewId);
  if (view) view.style.display = 'flex';
}

// ==================== NOTIFICACIONES ====================
function showNotification(msg) {
  const notif = document.createElement('div');
  notif.className = 'notification';
  notif.textContent = msg;
  document.body.appendChild(notif);
  
  setTimeout(() => {
    notif.classList.add('show');
  }, 100);
  
  setTimeout(() => {
    notif.remove();
  }, 3000);
}

// ==================== INICIALIZACIÓN ====================
document.addEventListener('DOMContentLoaded', function() {
  // Restaurar deporte guardado
  const saved_sport = localStorage.getItem('currentSport');
  if (saved_sport) currentSport = saved_sport;
  
  // Restaurar filtro guardado
  const saved_filter = localStorage.getItem('selectedFilter');
  if (saved_filter) selectedFilter = saved_filter;
  
  // Cargar parlays guardados
  updateMyParlaysView();
  
  console.log('✅ BOTONES FUNCIONALES INICIALIZADOS');
});

// Exportar para uso en app.js
window.ParlaySmart = {
  setSport,
  addMatch,
  removeMatch,
  saveParlay,
  removeSavedParlay,
  setFilter,
  openTodayView,
  openTournamentView,
  openAdminPanel,
  closeAdminPanel,
  showNotification
};
