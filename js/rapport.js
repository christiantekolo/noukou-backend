/**
 * NOUKOU — Rapport PDF logic
 */

document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const dataStr = params.get('data');
  
  if (dataStr) {
    try {
      const data = JSON.parse(decodeURIComponent(dataStr));
      renderRapport(data);
    } catch (e) {
      renderFallback();
    }
  } else {
    renderFallback();
  }
});

function renderRapport(data) {
  // Date
  document.getElementById('rpt-date').textContent = new Date().toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit'
  });

  // Coords
  document.getElementById('rpt-coords').textContent = 
    `${data.coordonnees.lat}°N, ${data.coordonnees.lon}°E`;

  // Profil
  document.getElementById('rpt-profil').innerHTML = `
    <div class="rapport-item"><label>Zone agro-écologique</label><p>${data.zone}</p></div>
    <div class="rapport-item"><label>Précipitations</label><p>${data.climat.precip_annuel.toFixed(0)} mm/an</p></div>
    <div class="rapport-item"><label>Température moyenne</label><p>${data.climat.temp_moyenne.toFixed(1)}°C</p></div>
    <div class="rapport-item"><label>Humidité relative</label><p>${data.climat.humidity_rel.toFixed(1)}%</p></div>
    <div class="rapport-item"><label>pH du sol</label><p>${data.sol.soil_ph}</p></div>
    <div class="rapport-item"><label>Argile</label><p>${data.sol.clay_pct}%</p></div>
    <div class="rapport-item"><label>Carbone organique</label><p>${data.sol.soc_gkg} g/kg</p></div>
    <div class="rapport-item"><label>CEC</label><p>${data.sol.cec_cmol_kg} cmol/kg</p></div>
  `;

  // Cultures
  const culturesHTML = data.recommandations.map((rec, i) => {
    const icon = CULTURE_ICONS[rec.culture_fr] || '🌱';
    const scoreColor = getScoreColor(rec.score_final);
    return `
      <div style="padding:1rem;background:rgba(255,255,255,0.02);border-radius:var(--radius-sm);margin-bottom:0.75rem;">
        <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.5rem;">
          <span style="font-size:1.5rem;">${icon}</span>
          <strong style="color:var(--text-white);font-size:1.0625rem;">#${i+1} ${rec.culture_fr}</strong>
          <span style="color:${scoreColor};font-weight:700;">${rec.score_final}/100</span>
          <span class="badge ${rec.niveau === 'Optimal' ? 'badge-green' : 'badge-orange'}">${rec.niveau}</span>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.75rem;font-size:0.8125rem;">
          <div><span style="color:var(--text-muted);">Rendement prédit</span><br><strong style="color:var(--text-white);">${rec.yield_predit_tha} T/ha</strong></div>
          <div><span style="color:var(--text-muted);">Score adaptation</span><br><strong style="color:var(--text-white);">${rec.score_adaptation}/100</strong></div>
          <div><span style="color:var(--text-muted);">Variétés</span><br><strong style="color:var(--text-white);">${rec.varietes_top3.length} certifiée(s)</strong></div>
        </div>
      </div>
    `;
  }).join('');
  document.getElementById('rpt-cultures').innerHTML = culturesHTML;

  // Variétés
  const varietesHTML = data.recommandations.map(rec => {
    const icon = CULTURE_ICONS[rec.culture_fr] || '🌱';
    const rows = rec.varietes_top3.map(v => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:0.5rem 0.75rem;background:rgba(255,255,255,0.02);border-radius:var(--radius-sm);margin-bottom:0.35rem;flex-wrap:wrap;gap:0.5rem;">
        <span style="font-weight:500;color:var(--text-light);">${v.variete}
          ${v.inscrit_2024 ? '<span class="badge badge-green" style="font-size:0.625rem;margin-left:0.25rem;">✅ Catalogue 2024</span>' : ''}
        </span>
        <span style="font-size:0.75rem;color:var(--text-muted);">🔄 ${v.cycle_jours}j · 📈 ${(v.rendement_opt_kgha/1000).toFixed(1)}T/ha max · Score: ${v.score_adaptation}/100</span>
      </div>
    `).join('');
    return `
      <div style="margin-bottom:1rem;">
        <h3 style="font-size:0.9375rem;font-weight:600;color:var(--text-white);margin-bottom:0.5rem;">${icon} ${rec.culture_fr}</h3>
        ${rows}
      </div>
    `;
  }).join('');
  document.getElementById('rpt-varietes').innerHTML = varietesHTML;
}

function renderFallback() {
  document.getElementById('rpt-date').textContent = new Date().toLocaleDateString('fr-FR');
  document.getElementById('rpt-coords').textContent = 'Non disponible';
  document.getElementById('rpt-profil').innerHTML = `
    <div class="empty-state" style="grid-column:1/-1;">
      <div class="empty-state-icon">📄</div>
      <h3>Aucune donnée de rapport</h3>
      <p>Lancez une analyse depuis la page d'analyse pour générer un rapport.</p>
      <a href="analyse.html" class="btn btn-primary" style="margin-top:1rem;">🌱 Analyser une parcelle</a>
    </div>
  `;
  document.getElementById('rpt-cultures').innerHTML = '';
  document.getElementById('rpt-varietes').innerHTML = '';
}

function downloadPDF() {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();
  
  let y = 20;
  const margin = 20;
  const pageWidth = doc.internal.pageSize.getWidth();

  // Title
  doc.setFontSize(20);
  doc.setTextColor(0, 107, 63);
  doc.text('NOUKOU — Rapport d\'analyse', margin, y);
  y += 10;
  
  doc.setFontSize(9);
  doc.setTextColor(120, 120, 120);
  doc.text(`Généré le ${new Date().toLocaleDateString('fr-FR')} — NOUKOU-Predict V1`, margin, y);
  y += 5;
  doc.setDrawColor(0, 107, 63);
  doc.line(margin, y, pageWidth - margin, y);
  y += 10;

  // Get data from URL
  const params = new URLSearchParams(window.location.search);
  const dataStr = params.get('data');
  
  if (!dataStr) {
    doc.setFontSize(12);
    doc.setTextColor(0, 0, 0);
    doc.text('Aucune donnée disponible.', margin, y);
    doc.save('NOUKOU_Rapport.pdf');
    return;
  }

  const data = JSON.parse(decodeURIComponent(dataStr));

  // Section 1: Profil
  doc.setFontSize(13);
  doc.setTextColor(0, 107, 63);
  doc.text('1. Profil de la parcelle', margin, y);
  y += 8;
  doc.setFontSize(10);
  doc.setTextColor(50, 50, 50);
  doc.text(`GPS: ${data.coordonnees.lat}°N, ${data.coordonnees.lon}°E`, margin, y); y += 5;
  doc.text(`Zone: ${data.zone}`, margin, y); y += 5;
  doc.text(`Précipitations: ${data.climat.precip_annuel.toFixed(0)} mm/an`, margin, y); y += 5;
  doc.text(`Température: ${data.climat.temp_moyenne.toFixed(1)}°C`, margin, y); y += 5;
  doc.text(`pH Sol: ${data.sol.soil_ph} | Argile: ${data.sol.clay_pct}%`, margin, y); y += 12;

  // Section 2: Cultures
  doc.setFontSize(13);
  doc.setTextColor(0, 107, 63);
  doc.text('2. Cultures recommandées', margin, y);
  y += 8;
  
  data.recommandations.forEach((rec, i) => {
    if (y > 260) { doc.addPage(); y = 20; }
    doc.setFontSize(11);
    doc.setTextColor(0, 0, 0);
    doc.text(`#${i+1} ${rec.culture_fr} — Score: ${rec.score_final}/100 (${rec.niveau})`, margin, y);
    y += 5;
    doc.setFontSize(9);
    doc.setTextColor(80, 80, 80);
    doc.text(`Rendement prédit: ${rec.yield_predit_tha} T/ha`, margin + 5, y); y += 4;
    
    rec.varietes_top3.forEach(v => {
      if (y > 270) { doc.addPage(); y = 20; }
      doc.text(`• ${v.variete} — ${v.cycle_jours}j — ${(v.rendement_opt_kgha/1000).toFixed(1)}T/ha max${v.inscrit_2024 ? ' ✓ Catalogue 2024' : ''}`, margin + 10, y);
      y += 4;
    });
    y += 4;
  });

  // Footer
  y += 5;
  doc.setFontSize(8);
  doc.setTextColor(150, 150, 150);
  doc.text('Généré par NOUKOU-Predict V1 — CUBE Togo × D-CLIC OIF — TEKOLO Ékoué Christian', margin, y);

  doc.save(`NOUKOU_Rapport_${data.zone}_${data.coordonnees.lat}.pdf`);
}
