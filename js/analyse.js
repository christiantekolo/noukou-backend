/**
 * NOUKOU — Logique de la page d'analyse de parcelle
 * GPS, carte Leaflet, affichage des résultats IA
 */

let selectedLat = null;
let selectedLon = null;
let map = null;
let marker = null;
let mapInitialized = false;

// URL du backend — changer pour la vraie URL après déploiement
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'        // dev local
  : 'https://REMPLACER-PAR-RAILWAY-URL.railway.app'; // production

// ── Tabs ──
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'tab-map' && !mapInitialized) {
      initMap();
    }
  });
});

// ── GPS Auto ──
function detectGPS() {
  const btn = document.getElementById('gps-auto-btn');
  btn.classList.add('loading');
  btn.textContent = '📡 Détection en cours...';

  if (!navigator.geolocation) {
    btn.classList.remove('loading');
    btn.textContent = '❌ Géolocalisation non supportée';
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      selectedLat = pos.coords.latitude;
      selectedLon = pos.coords.longitude;
      updateCoordsDisplay();
      btn.classList.remove('loading');
      btn.textContent = '✅ Position détectée';
      document.getElementById('launch-btn').disabled = false;
    },
    (err) => {
      btn.classList.remove('loading');
      // Fallback: utiliser Atakpamé comme position par défaut
      selectedLat = 7.533;
      selectedLon = 1.124;
      updateCoordsDisplay();
      btn.textContent = '📍 Position simulée (Atakpamé)';
      document.getElementById('launch-btn').disabled = false;
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
}

// ── Leaflet Map ──
function initMap() {
  map = L.map('map').setView([8.0, 1.1], 7);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
    maxZoom: 18,
  }).addTo(map);

  // Default marker at center of Togo
  marker = L.marker([8.0, 1.1], { draggable: true }).addTo(map);

  marker.on('dragend', () => {
    const pos = marker.getLatLng();
    selectedLat = pos.lat;
    selectedLon = pos.lng;
    updateCoordsDisplay();
    document.getElementById('launch-btn').disabled = false;
  });

  map.on('click', (e) => {
    selectedLat = e.latlng.lat;
    selectedLon = e.latlng.lng;
    marker.setLatLng(e.latlng);
    updateCoordsDisplay();
    document.getElementById('launch-btn').disabled = false;
  });

  mapInitialized = true;

  // Fix map rendering
  setTimeout(() => map.invalidateSize(), 200);
}

// ── Coords & Zone ──
function updateCoordsDisplay() {
  document.getElementById('display-lat').textContent = selectedLat.toFixed(4);
  document.getElementById('display-lon').textContent = selectedLon.toFixed(4);

  const zone = detectZone(selectedLat, selectedLon);
  const zoneDisplay = document.getElementById('zone-display');
  const zoneName = document.getElementById('zone-name');
  zoneDisplay.style.display = 'flex';
  zoneName.textContent = `Zone ${zone}`;
}

// ── Launch Analysis ──
function launchAnalysis() {
  if (selectedLat === null || selectedLon === null) return;

  const container = document.getElementById('results-container');
  container.innerHTML = `
    <div class="panel-card loader-container analysis-loader">
      <div class="loader-spinner"></div>
      <div class="loader-steps">
        <div class="loader-step active" id="step-1">
          <span class="loader-step-icon">🌐</span>
          <span class="loader-step-text">Interrogation NASA POWER (climat)...</span>
        </div>
        <div class="loader-step" id="step-2">
          <span class="loader-step-icon">🧪</span>
          <span class="loader-step-text">Analyse du sol via iSDA Africa...</span>
        </div>
        <div class="loader-step" id="step-3">
          <span class="loader-step-icon">🧠</span>
          <span class="loader-step-text">Calcul des recommandations (RF + Ridge)...</span>
        </div>
      </div>
    </div>
  `;

  // Animate loader steps
  setTimeout(() => {
    document.getElementById('step-1').classList.replace('active', 'done');
    document.getElementById('step-2').classList.add('active');
  }, 1000);
  setTimeout(() => {
    document.getElementById('step-2').classList.replace('active', 'done');
    document.getElementById('step-3').classList.add('active');
  }, 2000);

  // Appeler la nouvelle fonction de prédiction (Backend ou Fallback)
  analyserParcelle(selectedLat, selectedLon);
}

// ── Fonction d'appel à l'API (avec fallback sur le mock) ──
async function analyserParcelle(lat, lon) {
  try {
    const response = await fetch(`${API_URL}/api/analyse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat: lat, lon: lon })
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || 'Erreur serveur');
    }

    const data = await response.json();

    if (!data.success) throw new Error(data.error);

    // Enregistrement des données complètes pour la sauvegarde et le PDF
    lastAnalysisData = data;
    displayResults(data);

  } catch (error) {
    console.warn('API indisponible ou erreur, utilisation du mock :', error.message);
    // Fallback : appel à la fonction existante du fichier mock-data.js
    const mockData = await fetchRecommendation(lat, lon);
    lastAnalysisData = mockData;
    displayResults(mockData);
  }
}

// ── Display Results ──
function displayResults(data) {
  const container = document.getElementById('results-container');
  const recs = data.recommandations;

  let cardsHTML = recs.map((rec, i) => {
    const icon = CULTURE_ICONS[rec.culture_fr] || '🌱';
    const scoreColor = getScoreColor(rec.score_final);
    const rankClass = `rank-${i + 1}`;
    const niveauBadge = rec.niveau === 'Optimal'
      ? '<span class="badge badge-green">Optimal</span>'
      : rec.niveau === 'Suboptimal'
        ? '<span class="badge badge-orange">Suboptimal</span>'
        : '<span class="badge badge-red">Risqué</span>';

    const varietesHTML = rec.varietes_top3.map(v => `
      <div class="variete-item">
        <span class="variete-name">${v.variete} ${v.inscrit_2024 ? '<span class="badge badge-green" style="font-size:0.625rem;">✅ Catalogue 2024</span>' : ''}</span>
        <div class="variete-meta">
          <span>🔄 ${v.cycle_jours}j</span>
          <span>📈 ${(v.rendement_opt_kgha / 1000).toFixed(1)}T/ha max</span>
          <span>Score: ${v.score_adaptation}/100</span>
        </div>
      </div>
    `).join('');

    return `
      <div class="result-card">
        <div class="result-card-header">
          <div class="result-rank ${rankClass}">#${i + 1}</div>
          <span class="result-culture-icon">${icon}</span>
          <div class="result-culture-info">
            <h3>${rec.culture_fr}</h3>
            <div class="result-score-line">
              <span class="result-score" style="color:${scoreColor}">${rec.score_final}/100</span>
              ${niveauBadge}
            </div>
          </div>
        </div>
        <div class="result-card-body">
          <div class="result-metrics">
            <div class="result-metric">
              <label>Rendement prédit</label>
              <p>${rec.yield_predit_tha} T/ha</p>
            </div>
            <div class="result-metric">
              <label>Zone</label>
              <p>${data.zone}</p>
            </div>
            <div class="result-metric">
              <label>Adaptation</label>
              <p>${rec.score_adaptation}/100</p>
            </div>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width:${rec.score_final}%;background:${scoreColor};"></div>
          </div>
          <button class="varietes-toggle" onclick="toggleVarietes(this)">
            🌿 Variétés recommandées (${rec.varietes_top3.length}) <span class="arrow">▼</span>
          </button>
          <div class="varietes-list">${varietesHTML}</div>
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = `
    <div class="result-cards">${cardsHTML}</div>
    <div class="context-data">
      <div class="context-item">
        <div class="ctx-icon">🌧️</div>
        <div class="ctx-label">Précipitations</div>
        <div class="ctx-value">${formatNumber(data.climat.precip_annuel, 0)} mm/an</div>
      </div>
      <div class="context-item">
        <div class="ctx-icon">🌡️</div>
        <div class="ctx-label">Température</div>
        <div class="ctx-value">${formatNumber(data.climat.temp_moyenne, 1)}°C</div>
      </div>
      <div class="context-item">
        <div class="ctx-icon">🧪</div>
        <div class="ctx-label">pH Sol</div>
        <div class="ctx-value">${formatNumber(data.sol.soil_ph, 1)}</div>
      </div>
      <div class="context-item">
        <div class="ctx-icon">🏔️</div>
        <div class="ctx-label">Argile</div>
        <div class="ctx-value">${formatNumber(data.sol.clay_pct, 0)}%</div>
      </div>
    </div>
    <div class="results-actions">
      <button class="btn btn-primary" onclick="saveCurrentAnalysis()">💾 Sauvegarder</button>
      <a href="rapport.html?data=${encodeURIComponent(JSON.stringify(data))}" class="btn btn-secondary">📄 Rapport PDF</a>
    </div>
  `;
}

function toggleVarietes(btn) {
  btn.classList.toggle('open');
  const list = btn.nextElementSibling;
  list.classList.toggle('open');
}

// ── Save to portfolio ──
let lastAnalysisData = null;
const originalFetch = fetchRecommendation;

// Override to capture data
const _origFetch = window.fetchRecommendation || fetchRecommendation;
// We capture in displayResults instead
function saveCurrentAnalysis() {
  if (!lastAnalysisData) return;
  
  // Utilise la fonction saveAnalysis du fichier mock-data.js (qui gère le localStorage)
  saveAnalysis(lastAnalysisData);

  // Visual feedback
  const btn = event.target;
  btn.textContent = '✅ Sauvegardé !';
  btn.disabled = true;
  setTimeout(() => {
    btn.textContent = '💾 Sauvegarder';
    btn.disabled = false;
  }, 2000);
}
