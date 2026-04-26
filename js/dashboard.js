/**
 * NOUKOU — Dashboard / Portfolio logic
 */

document.addEventListener('DOMContentLoaded', () => {
  const user = getCurrentUser();
  const greeting = document.getElementById('greeting');
  
  if (user && user.prenom) {
    greeting.textContent = `Bonjour, ${user.prenom} 👋`;
  }
  
  document.getElementById('today-date').textContent = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  });

  loadDashboard();
});

function loadDashboard() {
  const portfolio = getPortfolio();
  updateKPIs(portfolio);
  renderTable(portfolio);
  renderChart(portfolio);
}

function updateKPIs(portfolio) {
  document.getElementById('kpi-count').textContent = portfolio.length;

  if (portfolio.length === 0) {
    document.getElementById('kpi-top-culture').textContent = '—';
    document.getElementById('kpi-avg-score').textContent = '—';
    document.getElementById('kpi-last').textContent = '—';
    return;
  }

  // Most recommended culture
  const cultureCount = {};
  portfolio.forEach(a => {
    const c = a.culture_top || 'N/A';
    cultureCount[c] = (cultureCount[c] || 0) + 1;
  });
  const topCulture = Object.entries(cultureCount).sort((a, b) => b[1] - a[1])[0];
  document.getElementById('kpi-top-culture').textContent = topCulture ? topCulture[0] : '—';

  // Average score
  const scores = portfolio.map(a => {
    const s = a.score_top;
    if (typeof s === 'string') return parseInt(s) || 0;
    return s || 0;
  }).filter(s => s > 0);
  
  if (scores.length > 0) {
    const avg = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
    document.getElementById('kpi-avg-score').textContent = `${avg}/100`;
  }

  // Last analysis
  document.getElementById('kpi-last').textContent = timeAgo(portfolio[0].date);
}

function renderTable(portfolio) {
  const container = document.getElementById('table-body-container');
  
  if (portfolio.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📊</div>
        <h3>Aucune analyse enregistrée</h3>
        <p>Lancez votre première analyse pour constituer votre portfolio.</p>
        <a href="analyse.html" class="btn btn-primary" style="margin-top:1rem;">🌱 Analyser une parcelle</a>
      </div>
    `;
    return;
  }

  let rows = portfolio.map(a => `
    <tr>
      <td>${formatDateShort(a.date)}</td>
      <td>${a.lat ? `${parseFloat(a.lat).toFixed(3)}°N, ${parseFloat(a.lon).toFixed(3)}°E` : '—'}</td>
      <td>${a.zone || '—'}</td>
      <td><strong>${a.culture_top || '—'}</strong></td>
      <td><span style="color:${getScoreColor(parseInt(a.score_top) || 0)}">${a.score_top || '—'}</span></td>
      <td>
        <div class="table-actions">
          <button class="table-action-btn" onclick="viewAnalysis('${a.id}')">Voir</button>
          <button class="table-action-btn delete" onclick="removeAnalysis('${a.id}')">Supprimer</button>
        </div>
      </td>
    </tr>
  `).join('');

  container.innerHTML = `
    <table class="data-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Localisation</th>
          <th>Zone</th>
          <th>Culture #1</th>
          <th>Score</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderChart(portfolio) {
  const canvas = document.getElementById('scores-chart');
  if (!canvas) return;
  
  if (portfolio.length < 2) {
    document.getElementById('chart-wrapper').style.display = portfolio.length === 0 ? 'none' : 'block';
    if (portfolio.length < 2) return;
  }

  const labels = portfolio.slice().reverse().map(a => formatDateShort(a.date));
  const scores = portfolio.slice().reverse().map(a => parseInt(a.score_top) || 0);

  new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Score d\'adaptation',
        data: scores,
        borderColor: '#84ECAE',
        backgroundColor: 'rgba(132,236,174,0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#84ECAE',
        pointBorderColor: '#111F35',
        pointBorderWidth: 2,
        pointRadius: 5,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#8A9BB5', font: { size: 11 } },
        },
        y: {
          min: 0, max: 100,
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#8A9BB5', font: { size: 11 } },
        }
      }
    }
  });
}

function viewAnalysis(id) {
  const analysis = getAnalysisById(id);
  if (analysis) {
    // Redirect to analyse page or show modal
    alert(`Analyse du ${formatDate(analysis.date)}\nZone: ${analysis.zone}\nCulture: ${analysis.culture_top}\nScore: ${analysis.score_top}`);
  }
}

function removeAnalysis(id) {
  if (confirm('Supprimer cette analyse ?')) {
    deleteAnalysis(id);
    loadDashboard();
  }
}
