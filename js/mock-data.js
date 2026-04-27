/**
 * NOUKOU — Données mockées alignées sur pipeline_gps.py V1
 * 
 * Reproduit fidèlement :
 * - detect_zone_togo() par latitude
 * - SOL_MOYEN_PAR_ZONE (HarvestStat)
 * - CULTURES_PAR_ZONE (filtre agronomique)
 * - Score adaptation (40% précip + 30% pH + 20% zone + 10% texture)
 * - YIELD_MOYEN_TOGO (rendements moyens nationaux)
 * - Architecture hybride RF + Ridge
 *
 * Quand le backend sera déployé, remplacer fetchRecommendation()
 * par un fetch('/api/recommend', {method:'POST', body: {lat, lon}})
 */

// ============================================================
// DÉTECTION ZONE — identique à pipeline_gps.py
// ============================================================
function detectZone(lat, lon) {
  if (lat >= 10.0) return "Savanes";
  if (lat >= 9.0)  return "Kara";
  if (lat >= 8.0)  return "Centrale";
  if (lat >= 7.0)  return "Plateaux";
  return "Maritime";
}

// ============================================================
// PROFILS SOL PAR ZONE — SOL_MOYEN_PAR_ZONE (HarvestStat)
// ============================================================
const SOL_MOYEN_PAR_ZONE = {
  "Maritime":  { soil_ph: 6.1, clay_pct: 28.0, soc_gkg: 0.64, cec_cmol_kg: 6.4 },
  "Plateaux":  { soil_ph: 5.8, clay_pct: 22.0, soc_gkg: 0.70, cec_cmol_kg: 7.2 },
  "Centrale":  { soil_ph: 5.9, clay_pct: 20.0, soc_gkg: 0.65, cec_cmol_kg: 8.0 },
  "Kara":      { soil_ph: 6.3, clay_pct: 21.0, soc_gkg: 0.60, cec_cmol_kg: 7.2 },
  "Savanes":   { soil_ph: 6.0, clay_pct: 17.0, soc_gkg: 0.45, cec_cmol_kg: 5.5 },
};

// ============================================================
// CULTURES AUTORISÉES PAR ZONE — pipeline_gps.py
// ============================================================
const CULTURES_PAR_ZONE = {
  "Savanes":   ["Maize","Sorghum","Millet","Cowpea","Groundnuts (In Shell)","Yams","Onion","Tomato","Pepper"],
  "Kara":      ["Maize","Sorghum","Millet","Cowpea","Groundnuts (In Shell)","Yams","Cotton","Tomato","Cabbage","Onion"],
  "Centrale":  ["Maize","Sorghum","Yams","Cassava","Groundnuts (In Shell)","Cowpea","Cotton","Tomato","Okra","Sweet potato"],
  "Plateaux":  ["Maize","Cassava","Yams","Rice","Beans (mixed)","Soybean","Cotton","Cowpea","Tomato","Eggplant","Pepper","Sweet potato"],
  "Maritime":  ["Maize","Cassava","Rice","Beans (mixed)","Soybean","Cowpea","Tomato","Okra","Eggplant","Sweet potato"],
};

// ============================================================
// MAPPINGS CULTURES EN→FR — CULTURE_MAP_ETENDU
// ============================================================
const CULTURE_MAP = {
  "Maize": "Maïs",
  "Sorghum": "Sorgho",
  "Millet": "Mil",
  "Cassava": "Manioc",
  "Yams": "Igname",
  "Rice": "Riz",
  "Groundnuts (In Shell)": "Arachide",
  "Beans (mixed)": "Haricot",
  "Cowpea": "Niébé",
  "Cotton": "Coton",
  "Soybean": "Soja",
  "Tomato": "Tomate",
  "Onion": "Oignon",
  "Pepper": "Piment",
  "Okra": "Gombo",
  "Cabbage": "Chou",
  "Eggplant": "Aubergine",
  "Sesame": "Sésame",
  "Sweet potato": "Patate douce",
};

const CULTURE_ICONS = {
  "Igname": "🍠",
  "Manioc": "🌿",
  "Maïs": "🌽",
  "Riz": "🌾",
  "Sorgho": "🌾",
  "Mil": "🌾",
  "Arachide": "🥜",
  "Soja": "🫘",
  "Niébé": "🫘",
  "Haricot": "🫘",
  "Coton": "🌿",
  "Tomate": "🍅",
  "Piment": "🌶️",
  "Oignon": "🧅",
  "Gombo": "🌿",
  "Chou": "🥬",
  "Aubergine": "🍆",
  "Patate douce": "🍠",
  "Sésame": "🌱",
};

// ============================================================
// RENDEMENTS MOYENS NATIONAUX — YIELD_MOYEN_TOGO
// ============================================================
const YIELD_MOYEN_TOGO = {
  "Maize": 1.16, "Sorghum": 0.87, "Millet": 0.65,
  "Cassava": 5.13, "Yams": 8.48, "Rice": 1.55,
  "Groundnuts (In Shell)": 0.55, "Beans (mixed)": 0.42,
  "Cowpea": 0.46, "Cotton": 0.82, "Soybean": 0.46,
  "Tomato": 7.5, "Onion": 9.0, "Pepper": 3.5,
  "Okra": 2.5, "Cabbage": 9.0, "Eggplant": 5.0,
  "Sesame": 0.30, "Sweet potato": 4.5,
};

// ============================================================
// CATALOGUE VARIÉTÉS MOCK (extraits du catalogue MAHVDR 2024)
// ============================================================
const VARIETES_CATALOGUE = {
  "Maize": [
    { variete: "EVDT-97 STR C1", score_adaptation: 80, cycle_jours: 95, rendement_opt_kgha: 4000, inscrit_2024: true, tolerances: "Striga, sécheresse modérée" },
    { variete: "Ikenne 8149-SR", score_adaptation: 78, cycle_jours: 90, rendement_opt_kgha: 3500, inscrit_2024: true, tolerances: "Striga résistant" },
    { variete: "TZPB-SR-W", score_adaptation: 75, cycle_jours: 110, rendement_opt_kgha: 5000, inscrit_2024: true, tolerances: "Rouille, helminthosporiose" },
  ],
  "Sorghum": [
    { variete: "Sorvato 1", score_adaptation: 84, cycle_jours: 120, rendement_opt_kgha: 3000, inscrit_2024: true, tolerances: "Sécheresse, Striga" },
    { variete: "ICSV 1049", score_adaptation: 82, cycle_jours: 110, rendement_opt_kgha: 2800, inscrit_2024: true, tolerances: "Anthracnose" },
  ],
  "Millet": [
    { variete: "IKMP-5", score_adaptation: 87, cycle_jours: 85, rendement_opt_kgha: 2000, inscrit_2024: true, tolerances: "Sécheresse, mildiou" },
    { variete: "Souna 3", score_adaptation: 82, cycle_jours: 90, rendement_opt_kgha: 1800, inscrit_2024: true, tolerances: "Précocité" },
  ],
  "Cassava": [
    { variete: "TMS 30572", score_adaptation: 88, cycle_jours: 270, rendement_opt_kgha: 30000, inscrit_2024: true, tolerances: "Mosaïque, bactériose" },
    { variete: "Gbazekoute", score_adaptation: 85, cycle_jours: 300, rendement_opt_kgha: 25000, inscrit_2024: true, tolerances: "Adaptation locale" },
    { variete: "RB 89509", score_adaptation: 80, cycle_jours: 240, rendement_opt_kgha: 28000, inscrit_2024: true, tolerances: "Mosaïque résistant" },
  ],
  "Yams": [
    { variete: "TDr-95/19177", score_adaptation: 90, cycle_jours: 180, rendement_opt_kgha: 20000, inscrit_2024: true, tolerances: "Nématodes, anthracnose" },
    { variete: "Kratchi", score_adaptation: 88, cycle_jours: 200, rendement_opt_kgha: 22000, inscrit_2024: true, tolerances: "Adaptation zone forestière" },
    { variete: "Gnagnin", score_adaptation: 85, cycle_jours: 210, rendement_opt_kgha: 18000, inscrit_2024: true, tolerances: "Stockage longue durée" },
  ],
  "Rice": [
    { variete: "IR 841", score_adaptation: 82, cycle_jours: 120, rendement_opt_kgha: 5000, inscrit_2024: true, tolerances: "Verse, piriculariose" },
    { variete: "NERICA-L-19", score_adaptation: 79, cycle_jours: 110, rendement_opt_kgha: 4500, inscrit_2024: true, tolerances: "Pluvial strict" },
  ],
  "Groundnuts (In Shell)": [
    { variete: "TS 32-1", score_adaptation: 78, cycle_jours: 90, rendement_opt_kgha: 2500, inscrit_2024: true, tolerances: "Rosette, cercosporiose" },
    { variete: "RMP-12", score_adaptation: 75, cycle_jours: 95, rendement_opt_kgha: 2200, inscrit_2024: true, tolerances: "Aflatoxine résistant" },
  ],
  "Cowpea": [
    { variete: "Vita 7", score_adaptation: 80, cycle_jours: 70, rendement_opt_kgha: 1500, inscrit_2024: true, tolerances: "Thrips, bruches" },
    { variete: "KVx 61-1", score_adaptation: 76, cycle_jours: 65, rendement_opt_kgha: 1200, inscrit_2024: true, tolerances: "Précocité extrême" },
  ],
  "Cotton": [
    { variete: "STAM-59-A", score_adaptation: 82, cycle_jours: 160, rendement_opt_kgha: 1500, inscrit_2024: true, tolerances: "Jassides" },
    { variete: "FK-37", score_adaptation: 80, cycle_jours: 155, rendement_opt_kgha: 2000, inscrit_2024: true, tolerances: "Bactériose" },
  ],
  "Soybean": [
    { variete: "TGx 1835-10E", score_adaptation: 77, cycle_jours: 100, rendement_opt_kgha: 2000, inscrit_2024: true, tolerances: "Rouille asiatique" },
  ],
  "Beans (mixed)": [
    { variete: "BAT 477", score_adaptation: 76, cycle_jours: 85, rendement_opt_kgha: 1800, inscrit_2024: true, tolerances: "Sécheresse" },
  ],
  "Tomato": [
    { variete: "Tropimech", score_adaptation: 76, cycle_jours: 75, rendement_opt_kgha: 15000, inscrit_2024: true, tolerances: "Flétrissement bactérien" },
  ],
  "Sweet potato": [
    { variete: "TIS 2498", score_adaptation: 79, cycle_jours: 120, rendement_opt_kgha: 12000, inscrit_2024: true, tolerances: "Charançon" },
  ],
};

// ============================================================
// SIMULATION CLIMAT (basé sur données NASA POWER typiques)
// ============================================================
const CLIMAT_PAR_ZONE = {
  "Maritime":  { precip_annuel: 1050.3, temp_moyenne: 27.5, humidity_rel: 78.1, solar_rad: 17.8 },
  "Plateaux":  { precip_annuel: 1412.5, temp_moyenne: 26.8, humidity_rel: 74.2, solar_rad: 18.2 },
  "Centrale":  { precip_annuel: 1300.8, temp_moyenne: 27.1, humidity_rel: 70.5, solar_rad: 19.0 },
  "Kara":      { precip_annuel: 1180.0, temp_moyenne: 27.8, humidity_rel: 65.3, solar_rad: 19.5 },
  "Savanes":   { precip_annuel: 980.5,  temp_moyenne: 28.5, humidity_rel: 58.7, solar_rad: 20.1 },
};

// ============================================================
// SIMULATION DU PIPELINE recommend_for_gps()
// ============================================================

/**
 * Simule le scoring d'adaptation du Modèle A
 * Pondération NOUKOU : 40 précip + 30 pH + 20 zone + 10 texture
 */
function mockScoreAdaptation(precip, ph, zone, clay_pct, varieteRow) {
  // 40 pts — Pluviométrie (plages typiques)
  const pMin = 500, pMax = 1800;
  let ptsPrecip;
  if (precip >= pMin && precip <= pMax) ptsPrecip = 40;
  else if (precip < pMin) ptsPrecip = Math.max(0, Math.round(40 * precip / pMin));
  else ptsPrecip = Math.max(0, Math.round(40 * pMax / precip));

  // 30 pts — pH (plage 5.0–7.5 typique)
  const phMin = 5.0, phMax = 7.5;
  let ptsPh;
  if (ph >= phMin && ph <= phMax) ptsPh = 30;
  else {
    const ecart = Math.min(Math.abs(ph - phMin), Math.abs(ph - phMax));
    ptsPh = Math.max(0, Math.round(30 * (1 - ecart / 2.0)));
  }

  // 20 pts — Zone (simplifié : 3 = optimal, 2 = moyen, 1 = faible)
  const ptsZone = 16 + Math.floor(Math.random() * 5); // 16-20

  // 10 pts — Texture
  let ptsTexture;
  if (clay_pct >= 20 && clay_pct <= 35) ptsTexture = 8;
  else if (clay_pct >= 15) ptsTexture = 6;
  else ptsTexture = 4;

  return ptsPrecip + ptsPh + ptsZone + ptsTexture;
}

/**
 * Simule le rendement prédit (Modèle B)
 * Ajoute un aléa réaliste autour du YIELD_MOYEN_TOGO
 */
function mockYieldPredict(cultureEn, zone) {
  const yieldMoyen = YIELD_MOYEN_TOGO[cultureEn] || 1.0;
  // Variation ±15% pour simuler le modèle ML
  const factor = 0.85 + Math.random() * 0.30;
  return Math.round(yieldMoyen * factor * 100) / 100;
}

/**
 * Simule l'appel complet à recommend_for_gps()
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @returns {Promise} - Résultats formatés identiques au backend
 */
function fetchRecommendation(lat, lon) {
  return new Promise((resolve) => {
    const zone = detectZone(lat, lon);
    const climat = { ...CLIMAT_PAR_ZONE[zone] };
    const sol = { ...SOL_MOYEN_PAR_ZONE[zone] };
    const culturesZone = CULTURES_PAR_ZONE[zone] || [];

    // Ajouter léger aléa au climat pour réalisme
    climat.precip_annuel += Math.round((Math.random() - 0.5) * 100);
    climat.temp_moyenne += Math.round((Math.random() - 0.5) * 1.5 * 10) / 10;

    // Calculer recommandations pour chaque culture de la zone
    const resultats = [];
    for (const cultureEn of culturesZone) {
      const cultureFr = CULTURE_MAP[cultureEn] || cultureEn;
      const varietes = VARIETES_CATALOGUE[cultureEn] || [];
      if (varietes.length === 0) continue;

      const yieldPredit = mockYieldPredict(cultureEn, zone);
      const yieldRef = YIELD_MOYEN_TOGO[cultureEn] || yieldPredit;
      const yieldRatio = Math.min(1.5, yieldRef > 0 ? yieldPredit / yieldRef : 1.0);

      const scoreA = mockScoreAdaptation(
        climat.precip_annuel, sol.soil_ph, zone, sol.clay_pct, varietes[0]
      );
      const scoreB = Math.round((yieldRatio / 1.5) * 100);
      const poidsB = 0.40;
      const poidsA = 0.60;
      const scoreFinal = Math.round(poidsA * scoreA + poidsB * scoreB);

      const niveau = scoreFinal >= 80 ? "Optimal" : scoreFinal >= 60 ? "Suboptimal" : "Risqué";

      resultats.push({
        culture: cultureEn,
        culture_fr: cultureFr,
        score_final: scoreFinal,
        score_adaptation: scoreA,
        yield_predit_tha: yieldPredit,
        rendement_relatif: Math.round(yieldRatio * 100) / 100,
        niveau: niveau,
        varietes_top3: varietes.slice(0, 3).map(v => ({
          ...v,
          score_adaptation: mockScoreAdaptation(
            climat.precip_annuel, sol.soil_ph, zone, sol.clay_pct, v
          )
        })),
      });
    }

    // Trier par score_final desc, prendre top 3
    resultats.sort((a, b) => b.score_final - a.score_final || b.yield_predit_tha - a.yield_predit_tha);

    const result = {
      zone: zone,
      coordonnees: { lat: lat.toFixed(4), lon: lon.toFixed(4) },
      climat: climat,
      sol: sol,
      recommandations: resultats.slice(0, 3),
      metadata: {
        model_version: "NOUKOU-Predict V1",
        architecture: "Hybride RF + Ridge",
        r2_model: zone === "Savanes" ? 0.253 : 0.845,
        sources: {
          climat: "NASA POWER API (climatologie)",
          sol: `Moyennes HarvestStat zone ${zone}`,
          varietes: "Catalogue MAHVDR 2024 (109 variétés)",
        }
      }
    };

    // Simuler délai 3 secondes du vrai pipeline
    setTimeout(() => resolve(result), 3000);
  });
}

// ============================================================
// GESTION DU PORTFOLIO (localStorage avec isolation par utilisateur)
// ============================================================
function _getStorageKey() {
  const userStr = localStorage.getItem('noukou_user') || sessionStorage.getItem('noukou_user');
  let email = 'default';
  try {
    if (userStr) {
      const u = JSON.parse(userStr);
      if (u.email) email = u.email;
    }
  } catch(e) {}
  return 'noukou_portfolio_' + email;
}

function saveAnalysis(analysisData) {
  const key = _getStorageKey();
  const portfolio = JSON.parse(localStorage.getItem(key) || '[]');
  const entry = {
    id: Date.now().toString(36) + Math.random().toString(36).substr(2, 5),
    date: new Date().toISOString(),
    ...analysisData
  };
  portfolio.unshift(entry);
  localStorage.setItem(key, JSON.stringify(portfolio));
  return entry;
}

function getPortfolio() {
  const key = _getStorageKey();
  return JSON.parse(localStorage.getItem(key) || '[]');
}

function deleteAnalysis(id) {
  const key = _getStorageKey();
  let portfolio = getPortfolio();
  portfolio = portfolio.filter(a => a.id !== id);
  localStorage.setItem(key, JSON.stringify(portfolio));
  return portfolio;
}

function getAnalysisById(id) {
  const portfolio = getPortfolio();
  return portfolio.find(a => a.id === id);
}

// ============================================================
// AUTH — handled by auth-guard.js (do NOT redefine logout here)
// ============================================================
// Les fonctions mockLogin, mockRegister, getCurrentUser et logout
// sont désormais gérées par auth-guard.js qui utilise le vrai JWT.
// Ne pas les redéfinir ici pour éviter les conflits.

