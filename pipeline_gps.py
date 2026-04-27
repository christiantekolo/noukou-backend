#!/usr/bin/env python3
"""
pipeline_gps.py — NOUKOU-Predict V1
GPS → Recommandations cultures + variétés certifiées

Auteur : TEKOLO Ékoué Christian
Projet : NOUKOU-Predict / CUBE Togo / D-CLIC OIF
Version : V1 — Avril 2026

INSTALLATION :
    pip install -r requirements.txt

CONFIGURATION (créer un fichier .env à la racine) :
    ISDA_USERNAME=ton_email_isda
    ISDA_PASSWORD=ton_mot_de_passe_isda

USAGE RAPIDE :
    from pipeline_gps import recommend_for_gps, get_isda_token
    token = get_isda_token()
    top3, zone, clim, sol = recommend_for_gps(7.533, 1.124, token)
"""

import os, time, warnings
import numpy as np
import pandas as pd
import joblib
import requests

warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURATION — CHEMINS
# ============================================================
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR      = os.path.join(BASE_DIR, "models")
DATA_DIR        = os.path.join(BASE_DIR, "data")
DATASET_V4_PATH = os.path.join(DATA_DIR, "NOUKOU_Predict_Dataset_v4.xlsx")
if not os.path.exists(DATASET_V4_PATH):
        DATASET_V4_PATH = os.path.join(BASE_DIR, "NOUKOU_Predict_Dataset_v4.xlsx")

# ============================================================
# iSDA AFRICA — AUTHENTIFICATION
# NOTE DÉVELOPPEUR : configurer via fichier .env ou Streamlit Secrets
# Ne jamais mettre les credentials en dur dans ce fichier
# ============================================================
ISDA_BASE_URL = "https://api.isda-africa.com"
ISDA_USERNAME = os.environ.get("ISDA_USERNAME", "")
ISDA_PASSWORD = os.environ.get("ISDA_PASSWORD", "")
_isda_token_cache = {"token": None, "expires": 0}

def get_isda_token():
    """Obtenir/renouveler le token iSDA (cache 50 min)."""
    now = time.time()
    if _isda_token_cache["token"] and now < _isda_token_cache["expires"]:
        return _isda_token_cache["token"]
    r = requests.post(
        f"{ISDA_BASE_URL}/login",
        data={"username": ISDA_USERNAME, "password": ISDA_PASSWORD},
        timeout=15
    )
    r.raise_for_status()
    token = r.json().get("access_token")
    _isda_token_cache["token"]   = token
    _isda_token_cache["expires"] = now + 50 * 60
    return token

# ============================================================
# MAPPINGS CULTURE & ZONE
# ============================================================
CULTURE_MAP = {
    "Maize"                 : "maïs",
    "Sorghum"               : "sorgho",
    "Millet"                : "mil",
    "Cassava"               : "manioc",
    "Yams"                  : "igname",
    "Rice"                  : "riz",
    "Groundnuts (In Shell)" : "arachide",
    "Beans (mixed)"         : "haricot",
    "Cowpea"                : "niébé",
    "Cotton"                : "coton",
    "Soybean"               : "soja",
}

ZONE_MAP = {
    "Savanes"  : "Z1",
    "Kara"     : "Z2",
    "Centrale" : "Z3",
    "Plateaux" : "Z4",
    "Maritime" : "Z5",
}

CULTURE_MAP_ETENDU = {
    **CULTURE_MAP,
    "Tomato"       : "tomate",
    "Onion"        : "oignon",
    "Pepper"       : "piment",
    "Okra"         : "gombo",
    "Cabbage"      : "chou",
    "Eggplant"     : "aubergine",
    "Sesame"       : "sésame",
    "Sweet potato" : "patate douce",
}

CULTURES_MARAICHERES_EN = {
    "Tomato", "Onion", "Pepper", "Okra",
    "Cabbage", "Eggplant", "Sesame", "Sweet potato",
}

# ============================================================
# CULTURES AUTORISÉES PAR ZONE — filtre agronomique
# ============================================================
CULTURES_PAR_ZONE = {
    "Savanes"  : ["Maize","Sorghum","Millet","Cowpea",
                  "Groundnuts (In Shell)","Yams",
                  "Onion","Tomato","Pepper"],
    "Kara"     : ["Maize","Sorghum","Millet","Cowpea",
                  "Groundnuts (In Shell)","Yams","Cotton",
                  "Tomato","Onion"],
    "Centrale" : ["Maize","Sorghum","Yams","Cassava",
                  "Groundnuts (In Shell)","Cowpea","Cotton",
                  "Tomato","Okra","Sweet potato"],
    "Plateaux" : ["Maize","Cassava","Yams","Rice",
                  "Beans (mixed)","Soybean","Cotton","Cowpea",
                  "Tomato","Eggplant","Pepper","Sweet potato",
                  "Cabbage"],
    "Maritime" : ["Maize","Cassava","Rice",
                  "Beans (mixed)","Soybean","Cowpea",
                  "Tomato","Okra","Eggplant","Sweet potato",
                  "Cabbage"],
}

# ============================================================
# YIELDS DE RÉFÉRENCE — cultures maraîchères (pas de Modèle B)
# Sources documentées — voir rapport TEKOLO Avril 2026
# ============================================================
YIELD_REFERENCE_CULTURES_MARAICHERES = {
    "Tomato"       : 7.5,   # ITRA Togo via SciDev.Net 2019
    "Onion"        : 9.0,   # MFFR Togo 2022 filière Savanes
    "Pepper"       : 3.5,   # FAOSTAT Ghana + estimation WA
    "Okra"         : 2.5,   # FAOSTAT 2006 WCA moyenne
    "Cabbage"      : 9.0,   # Univ. Lomé 2021 + Kara/Savanes
    "Eggplant"     : 5.0,   # Estimation Niger/Bénin
    "Sesame"       : 0.30,  # ITRA Sotouboua — ScienceDirect 2024
    "Sweet potato" : 5.5,   # ITRA PDCO + FCI/World Bank SSA
}

# Rendements moyens nationaux Togo — normalisation Modèle B
YIELD_MOYEN_TOGO = {
    "Maize":1.16, "Sorghum":0.87, "Millet":0.65,
    "Cassava":5.13, "Yams":8.48, "Rice":1.55,
    "Groundnuts (In Shell)":0.55, "Beans (mixed)":0.42,
    "Cowpea":0.46, "Cotton":0.82, "Soybean":0.46,
    "Tomato":7.5, "Onion":9.0, "Pepper":3.5,
    "Okra":2.5, "Cabbage":9.0, "Eggplant":5.0,
    "Sesame":0.30, "Sweet potato":4.5,
}

# Rendement minimum absolu pour recommander une culture
YIELD_MINI_RECOMMANDATION = {
    "default"      : 0.50,
    "Yams"         : 5.00,
    "Cassava"      : 3.00,
    "Sweet potato" : 2.00,
    "Tomato"       : 3.00,
    "Onion"        : 4.00,
    "Cabbage"      : 4.00,
}

# Précipitations minimales absolues par culture
PRECIP_MINI_ZONE = {
    "Yams":900, "Cassava":900, "Rice":1000,
    "Soybean":800, "Cotton":700,
    "Tomato":600, "Onion":0,
    "Cabbage":500, "Sweet potato":700,
}

# ============================================================
# PROFILS SOL PAR ZONE — FALLBACK HARVESTSTAT TOGO
# Source : moyennes calculées sur données HarvestStat 127 zones
# ============================================================
SOL_MOYEN_PAR_ZONE = {
    "Maritime" : {"soil_ph":6.1,"clay_pct":28.0,"soc_gkg":0.64,"cec_cmol_kg":6.4},
    "Plateaux" : {"soil_ph":5.8,"clay_pct":22.0,"soc_gkg":0.70,"cec_cmol_kg":7.2},
    "Centrale" : {"soil_ph":5.9,"clay_pct":20.0,"soc_gkg":0.65,"cec_cmol_kg":8.0},
    "Kara"     : {"soil_ph":6.3,"clay_pct":21.0,"soc_gkg":0.60,"cec_cmol_kg":7.2},
    "Savanes"  : {"soil_ph":6.0,"clay_pct":17.0,"soc_gkg":0.45,"cec_cmol_kg":5.5},
}

# ============================================================
# DÉTECTION ZONE TOGO PAR LATITUDE
# ============================================================
def detect_zone_togo(lat, lon):
    if lat >= 10.0: return "Savanes"
    elif lat >= 9.0: return "Kara"
    elif lat >= 8.0: return "Centrale"
    elif lat >= 7.0: return "Plateaux"
    else: return "Maritime"

# ============================================================
# SNAP INLAND — PROTECTION ZONES CÔTIÈRES
# ============================================================
def snap_to_land(lat, lon):
    """
    Corriger les coordonnées proches du littoral
    avant appel iSDA (qui ne couvre pas la mer).
    """
    if lat < 6.5 and lon > 1.45:
        return lat, 1.40, True, "snap_inland_coastal"
    return lat, lon, False, None

# ============================================================
# SOL — iSDA AFRICA avec fallback HarvestStat
# ============================================================
def _get_soil_raw(lat, lon, token):
    """Appel brut iSDA Africa — usage interne."""
    headers  = {"Authorization": f"Bearer {token}"} if token else {}
    prop_map = {
        "ph"                       : ("soil_ph",     1),
        "carbon_organic"           : ("soc_gkg",     10),
        "clay_content"             : ("clay_pct",    1),
        "cation_exchange_capacity" : ("cec_cmol_kg", 10),
    }
    result = {}
    for prop, (col, div) in prop_map.items():
        for attempt in range(3):
            try:
                r = requests.get(
                    f"{ISDA_BASE_URL}/isdasoil/v2/soilproperty",
                    params={"lat":lat,"lon":lon,
                            "property":prop,"depth":"0-20"},
                    headers=headers, timeout=20)
                if r.status_code == 400:
                    raise ValueError("hors couverture iSDA")
                r.raise_for_status()
                val = (r.json().get("property",{})
                         .get(prop,[{}])[0]
                         .get("value",{}).get("value", None))
                if val is not None:
                    result[col] = round(val / div, 2)
                    break
            except ValueError:
                break
            except Exception:
                if attempt == 2:
                    break
                time.sleep(1.5)
    return result

def get_soil_safe(lat, lon, token=None):
    """
    Données sol avec 3 niveaux de défense :
    1. Snap inland si coordonnées côtières
    2. Appel iSDA avec vérification plausibilité
    3. Fallback moyennes HarvestStat par zone
    """
    zone = detect_zone_togo(lat, lon)
    lat_c, lon_c, snapped, snap_reason = snap_to_land(lat, lon)

    if token is None:
        try:
            token = get_isda_token()
        except Exception:
            pass

    try:
        soil    = _get_soil_raw(lat_c, lon_c, token)
        ph_ok   = 4.0 <= soil.get("soil_ph", 0) <= 9.0
        clay_ok = 3   <= soil.get("clay_pct", 0) <= 80
        if len(soil) < 4 or not ph_ok or not clay_ok:
            raise ValueError("valeurs iSDA hors plage")
        soil["_source"] = "isda_africa"
        if snapped:
            soil["_note"] = f"GPS snapé depuis ({lat:.3f},{lon:.3f})"
        return soil
    except Exception:
        fb = SOL_MOYEN_PAR_ZONE.get(zone,
             SOL_MOYEN_PAR_ZONE["Centrale"]).copy()
        fb["_source"] = f"fallback_harveststat_{zone}"
        fb["_note"]   = (
            f"iSDA indisponible — moyennes HarvestStat Togo "
            f"zone {zone}. Précision réduite."
        )
        return fb

# ============================================================
# CLIMAT — NASA POWER
# ============================================================
def get_climate_from_gps(lat, lon):
    """Données climatiques historiques via NASA POWER API."""
    url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
    params = {
        "parameters": "PRECTOTCORR,T2M,RH2M,ALLSKY_SFC_SW_DWN",
        "community": "AG",
        "longitude": lon,
        "latitude" : lat,
        "format"   : "JSON"
    }
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            p = r.json()["properties"]["parameter"]
            return {
                "precip_annuel": round(float(p["PRECTOTCORR"].get("ANN",0))*365, 1),
                "temp_moyenne" : round(float(p["T2M"].get("ANN", 27.0)), 2),
                "humidity_rel" : round(float(p["RH2M"].get("ANN", 70.0)), 2),
                "solar_rad"    : round(float(p["ALLSKY_SFC_SW_DWN"].get("ANN",18.5)), 3),
            }
        except Exception:
            time.sleep(2 ** attempt)
    # Fallback si NASA indisponible
    return {"precip_annuel":1150.0,"temp_moyenne":27.0,
            "humidity_rel":70.0,"solar_rad":18.5}

# ============================================================
# CHARGEMENT DES MODÈLES ML (cache en mémoire)
# ============================================================
_models_cache = {}

def load_models():
    """Charger les modèles .pkl une seule fois (mise en cache)."""
    global _models_cache
    if _models_cache:
        return _models_cache
    _models_cache["rf"]    = joblib.load(
        os.path.join(MODELS_DIR, "yield_rf_model_togo.pkl"))
    _models_cache["ridge"] = joblib.load(
        os.path.join(MODELS_DIR, "yield_ridge_savanes_togo.pkl"))
    cols = joblib.load(
        os.path.join(MODELS_DIR, "feature_columns_togo.pkl"))
    _models_cache["num_cols"] = cols["num_cols"]
    _models_cache["cat_cols"] = cols["cat_cols"]
    return _models_cache

def predict_hybrid(X_new, regions):
    """RF pour 4 régions + Ridge pour Savanes.
    NOTE: Le modèle prédit en espace log1p. On applique expm1 pour
    revenir en T/ha réel (voir yield_model_meta.json → target_transform).
    """
    m    = load_models()
    pred = np.zeros(len(X_new))
    reg  = np.array(regions)
    sav  = reg == "Savanes"
    if sav.any():
        pred[sav]  = m["ridge"].predict(
            X_new.iloc[list(np.where(sav)[0])])
    if (~sav).any():
        pred[~sav] = m["rf"].predict(
            X_new.iloc[list(np.where(~sav)[0])])
    # Transformation inverse : log1p → expm1 pour revenir en T/ha
    pred = np.expm1(pred)
    # Sécurité : empêcher les valeurs négatives
    pred = np.maximum(pred, 0.0)
    return pred

# ============================================================
# FEATURE ENGINEERING (identique au notebook d'entraînement)
# ============================================================
YEAR_MIN = 1995
YEAR_MAX = 2022

def get_features_from_gps(lat, lon, culture_en,
                           token=None, verbose=False):
    """Extraire le vecteur de features pour le Modèle B."""
    zone  = detect_zone_togo(lat, lon)
    clim  = get_climate_from_gps(lat, lon)
    soil  = get_soil_safe(lat, lon, token)

    now_year       = 2025
    harvest_month  = 10
    planting_month = 3 if zone in ["Plateaux","Maritime"] else 5
    cycle_dur      = max(1, harvest_month - planting_month)

    row = {
        "culture"              : culture_en,
        "Item"                 : culture_en,
        "Crop"                 : culture_en,
        "admin_1"              : zone,
        "lat"                  : lat,
        "lon"                  : lon,
        "precip_annuel"        : clim["precip_annuel"],
        "temp_moyenne"         : clim["temp_moyenne"],
        "solar_rad"            : clim["solar_rad"],
        "humidity_rel"         : clim["humidity_rel"],
        "soil_ph"              : soil["soil_ph"],
        "clay_pct"             : soil["clay_pct"],
        "soc_gkg"              : soil["soc_gkg"],
        "cec_cmol_kg"          : soil["cec_cmol_kg"],
        "cycle_duration"       : cycle_dur,
        "planting_month_sin"   : np.sin(2*np.pi*planting_month/12),
        "planting_month_cos"   : np.cos(2*np.pi*planting_month/12),
        "harvest_month_sin"    : np.sin(2*np.pi*harvest_month/12),
        "harvest_month_cos"    : np.cos(2*np.pi*harvest_month/12),
        "rain_per_cycle"       : clim["precip_annuel"] / cycle_dur,
        "temp_x_precip"        : clim["temp_moyenne"] * clim["precip_annuel"],
        "humidity_x_temp"      : clim["humidity_rel"] * clim["temp_moyenne"],
        "soil_index"           : soil["clay_pct"] * soil["soc_gkg"],
        "year_trend"           : (now_year-YEAR_MIN)/(YEAR_MAX-YEAR_MIN),
        "aridity_index"        : clim["precip_annuel"]/(clim["temp_moyenne"]+10),
        "log_precip"           : np.log1p(clim["precip_annuel"]),
        "precip_deficit"       : max(0, 800-clim["precip_annuel"])/800,
        "heat_stress"          : max(0, clim["temp_moyenne"]-30),
        "water_heat_efficiency": clim["precip_annuel"]/clim["temp_moyenne"],
        "rain_intensity"       : clim["precip_annuel"]/12,
        "humidity_deficit"     : max(0, 75-clim["humidity_rel"]),
        "evapo_proxy"          : clim["temp_moyenne"]*(1-clim["humidity_rel"]/100),
        "arid_stress"          : (max(0, 75-clim["humidity_rel"]) *
                                   max(0.1, max(0, clim["temp_moyenne"]-30))),
        "humidity_precip_ratio": clim["humidity_rel"]/np.log1p(clim["precip_annuel"]),
    }

    m = load_models()
    
    # Construction robuste des features pour éviter le crash du modèle (One-Hot ou Categorical)
    feat_dict = {}
    for c in m["num_cols"]:
        feat_dict[c] = row.get(c, 0)
        
    for c in m["cat_cols"]:
        if c in row:
            feat_dict[c] = row[c]
        else:
            # Gestion des colonnes One-Hot (ex: 'Item_Maize', 'admin_1_Savanes')
            if "Item_" in c or "Crop_" in c or "culture_" in c:
                feat_dict[c] = 1.0 if str(row.get("culture", "")) in c else 0.0
            elif "admin_1_" in c:
                feat_dict[c] = 1.0 if str(row.get("admin_1", "")) in c else 0.0
            else:
                feat_dict[c] = 0.0  # Valeur numérique par défaut pour les dummies

    X = pd.DataFrame([feat_dict])[m["num_cols"] + m["cat_cols"]]

    return X, zone

# ============================================================
# CHARGEMENT CATALOGUE VARIÉTÉS — Modèle A
# (lazy loading avec cache)
# ============================================================
_catalogue_cache = {}

_COTON_EXTRA = [
    {"culture":"coton","variete":"STAM-59-A","cycle_jours":160,
     "pluvio_min_mm":700,"pluvio_max_mm":1200,
     "rendement_optimal_kg_ha":1500,"pH_min":5.5,"pH_max":7.5,
     "zone_agroecologique_togo":"Z1,Z2,Z3,Z4",
     "inscrit_catalogue_2024":"OUI",
     "source":"ITRA Togo / ICAT Programme Coton"},
    {"culture":"coton","variete":"STAM-F","cycle_jours":150,
     "pluvio_min_mm":700,"pluvio_max_mm":1200,
     "rendement_optimal_kg_ha":1800,"pH_min":5.5,"pH_max":7.5,
     "zone_agroecologique_togo":"Z1,Z2,Z3",
     "inscrit_catalogue_2024":"OUI",
     "source":"SOFITEX / ICAT Programme Coton Togo"},
    {"culture":"coton","variete":"FK-37","cycle_jours":155,
     "pluvio_min_mm":750,"pluvio_max_mm":1300,
     "rendement_optimal_kg_ha":2000,"pH_min":5.8,"pH_max":7.2,
     "zone_agroecologique_togo":"Z1,Z2,Z3,Z4",
     "inscrit_catalogue_2024":"OUI",
     "source":"CRRA Togo / ITRA Sotouboua"},
]

def load_catalogue():
    """Charger df_varietes et df_scores depuis Excel (cache)."""
    global _catalogue_cache
    if _catalogue_cache:
        return _catalogue_cache
    # TABLE1 — variétés agronomiques
    df_v = pd.read_excel(DATASET_V4_PATH,
                          sheet_name="TABLE1_VARIETES", header=1)
    df_v = df_v[
        df_v["culture"].notna() &
        ~df_v["culture"].astype(str).str.startswith("▶") &
        ~df_v["culture"].astype(str).str.startswith("NOUKOU") &
        (df_v["culture"].astype(str) != "culture")
    ].copy().reset_index(drop=True)
    # Ajouter coton (absent de l'Excel)
    df_v = pd.concat([df_v, pd.DataFrame(_COTON_EXTRA)],
                      ignore_index=True)
    # TABLE3 — scores variété × zone
    df_s = pd.read_excel(DATASET_V4_PATH,
                          sheet_name="TABLE3_RECOMMANDATIONS", header=3)
    df_s.columns = ["culture","variete","zone_id",
                    "score_adaptation","interpretation","source"]
    df_s = df_s[df_s["variete"].notna()].copy().reset_index(drop=True)
    _catalogue_cache["df_varietes"] = df_v
    _catalogue_cache["df_scores"]   = df_s
    return _catalogue_cache

# ============================================================
# MODÈLE A — SCORING D'ADAPTATION
# Pondération NOUKOU : 40 précip + 30 pH + 20 zone + 10 texture
# ============================================================
def calcul_score_adaptation(precip_reelle, ph_reel,
                              zone_admin1, clay_pct, variete_row):
    cat       = load_catalogue()
    df_scores = cat["df_scores"]

    # 40 pts — Pluviométrie
    p_min = float(variete_row.get("pluvio_min_mm") or 500)
    p_max = float(variete_row.get("pluvio_max_mm") or 2000)
    if p_min <= precip_reelle <= p_max:
        pts_precip = 40
    elif precip_reelle < p_min:
        pts_precip = max(0, round(40 * precip_reelle / p_min))
    else:
        pts_precip = max(0, round(40 * p_max / precip_reelle))

    # 30 pts — pH
    ph_min = float(variete_row.get("pH_min") or 5.0)
    ph_max = float(variete_row.get("pH_max") or 8.0)
    if ph_min <= ph_reel <= ph_max:
        pts_ph = 30
    else:
        ecart  = min(abs(ph_reel-ph_min), abs(ph_reel-ph_max))
        pts_ph = max(0, round(30*(1-ecart/2.0)))

    # 20 pts — Zone agro-écologique (depuis TABLE3)
    zone_id     = ZONE_MAP.get(zone_admin1, "Z3")
    nom_variete = variete_row.get("variete", "")
    mask_t3     = ((df_scores["variete"] == nom_variete) &
                   (df_scores["zone_id"] == zone_id))
    match_t3    = df_scores[mask_t3]
    if not match_t3.empty:
        score_zone = int(match_t3.iloc[0]["score_adaptation"])
    else:
        zone_field = str(variete_row.get("zone_agroecologique_togo","") or "")
        score_zone = 3 if zone_id in zone_field else 1
    pts_zone = {3:20, 2:12, 1:4}.get(score_zone, 4)

    # 10 pts — Texture du sol
    sol_pref = str(variete_row.get("type_sol_prefere","") or "").lower()
    if clay_pct >= 35:
        texture_cat = "argileux"
    elif clay_pct >= 20:
        texture_cat = "limoneux"
    else:
        texture_cat = "sableux"
    if texture_cat in sol_pref:
        pts_texture = 10
    elif any(x in sol_pref for x in ["bien drainé","profond","tous types",
                                       "variés","fertile"]):
        pts_texture = 7
    else:
        pts_texture = 4

    score_total = pts_precip + pts_ph + pts_zone + pts_texture
    niveau = ("Optimal" if score_total >= 75
              else "Suboptimal" if score_total >= 50
              else "Inadapté")
    return score_total, {
        "pts_precip": pts_precip, "pts_ph": pts_ph,
        "pts_zone": pts_zone, "pts_texture": pts_texture,
        "niveau": niveau,
    }

# ============================================================
# MODÈLE A — VARIÉTÉS RECOMMANDÉES
# ============================================================
def get_varietes_recommandees(culture_en, zone_admin1,
                               precip_reelle, ph_reel,
                               clay_pct, top_n=3):
    """
    Top N variétés pour une culture — utilise CULTURE_MAP_ETENDU
    donc supporte les 19 cultures (11 ML + 8 maraîchères).
    """
    cat         = load_catalogue()
    df_varietes = cat["df_varietes"]
    culture_fr  = CULTURE_MAP_ETENDU.get(culture_en, culture_en.lower())
    mask        = df_varietes["culture"].str.lower() == culture_fr.lower()
    df_cult     = df_varietes[mask]
    if df_cult.empty:
        return []
    resultats = []
    for _, vrow in df_cult.iterrows():
        v     = vrow.to_dict()
        p_min = float(v.get("pluvio_min_mm") or 500)
        if precip_reelle < p_min * 0.70:
            continue
        score, detail = calcul_score_adaptation(
            precip_reelle, ph_reel, zone_admin1, clay_pct, v)
        inscrit_raw  = str(v.get("inscrit_catalogue_2024","") or "")
        catalogue_ok = ("OUI" in inscrit_raw.upper() or "✅" in inscrit_raw)
        resultats.append({
            "variete"           : str(v.get("variete","")),
            "culture_fr"        : culture_fr,
            "score_adaptation"  : score,
            "niveau"            : detail["niveau"],
            "detail_pts"        : detail,
            "cycle_jours"       : v.get("cycle_jours","?"),
            "rendement_opt_kgha": v.get("rendement_optimal_kg_ha","?"),
            "tolerances"        : str(v.get("tolerances_resistances",""))[:80],
            "inscrit_2024"      : catalogue_ok,
            "source"            : str(v.get("source",""))[:80],
        })
    if not resultats:
        return []
    return sorted(resultats,
                  key=lambda x: (x["score_adaptation"],
                                 int(x["inscrit_2024"])),
                  reverse=True)[:top_n]

# ============================================================
# FONCTION PRINCIPALE — recommend_for_gps()
# ============================================================
def recommend_for_gps(lat, lon, token=None, top_n=3, verbose=False):
    """
    GPS → Top N recommandations complètes.

    Args:
        lat, lon : coordonnées GPS de la parcelle
        token    : token iSDA (auto-obtenu si None)
        top_n    : nombre de recommandations (défaut 3)
        verbose  : afficher les détails

    Returns:
        (top_n_list, zone_str, climat_dict, sol_dict)

    Exemple:
        top3, zone, clim, sol = recommend_for_gps(7.533, 1.124)
        for r in top3:
            print(r["culture_fr"], r["yield_predit_tha"], "T/ha")
    """
    zone = detect_zone_togo(lat, lon)
    clim = get_climate_from_gps(lat, lon)
    soil = get_soil_safe(lat, lon, token)

    if verbose:
        print(f"Zone    : {zone}")
        print(f"Précip  : {clim['precip_annuel']} mm | "
              f"Temp : {clim['temp_moyenne']}°C")
        print(f"pH sol  : {soil['soil_ph']} | "
              f"Argile : {soil['clay_pct']}%")

    cultures_valides = CULTURES_PAR_ZONE.get(zone, [])
    resultats = []

    for culture_en in cultures_valides:
        # Filtre précipitation absolue
        precip_min = PRECIP_MINI_ZONE.get(culture_en, 0)
        if clim["precip_annuel"] < precip_min:
            continue

        # Modèle B — rendement prédit
        try:
            if culture_en in CULTURES_MARAICHERES_EN:
                yield_base = YIELD_REFERENCE_CULTURES_MARAICHERES.get(
                    culture_en, 2.0)
                # Appliquer un coefficient de pénalité par zone
                # Les maraîchères performent mieux en Maritime/Plateaux (irrigué)
                # et moins bien en Savanes/Kara (sec)
                zone_coeff = {
                    "Maritime": 1.0, "Plateaux": 0.95,
                    "Centrale": 0.80, "Kara": 0.65, "Savanes": 0.55
                }
                # Aussi pénaliser si le pH est loin de l'optimal (6.0-7.0)
                ph_penalty = 1.0
                if soil["soil_ph"] < 5.5 or soil["soil_ph"] > 7.5:
                    ph_penalty = 0.80
                elif soil["soil_ph"] < 5.8 or soil["soil_ph"] > 7.2:
                    ph_penalty = 0.90
                yield_predit = round(yield_base * zone_coeff.get(zone, 0.75) * ph_penalty, 2)
                source_yield = "reference_faostat_ajuste"
                poids_B      = 0.15  # poids très réduit — pas de ML
            else:
                df_feat, _ = get_features_from_gps(
                    lat, lon, culture_en, token=token, verbose=False)
                yield_predit = predict_hybrid(df_feat, [zone])[0]
                source_yield = "modele_B"
                poids_B      = 0.40
        except Exception as e:
            if verbose:
                print(f"  {culture_en} erreur Modèle B : {e}")
            yield_predit = YIELD_MOYEN_TOGO.get(culture_en, 1.0) * 0.9
            source_yield = "fallback_moyen"
            poids_B      = 0.20

        # Filtre rendement absolu minimum
        yield_mini = YIELD_MINI_RECOMMANDATION.get(
            culture_en, YIELD_MINI_RECOMMANDATION["default"])
        if yield_predit < yield_mini:
            if verbose:
                print(f"  {culture_en} exclu : "
                      f"{yield_predit:.2f} < seuil {yield_mini}")
            continue

        # Modèle A — score adaptation + variétés
        varietes = get_varietes_recommandees(
            culture_en, zone,
            clim["precip_annuel"],
            soil["soil_ph"],
            soil["clay_pct"],
            top_n=3
        )

        # Score final combiné
        poids_A     = 1.0 - poids_B
        yield_ref   = YIELD_MOYEN_TOGO.get(culture_en, yield_predit)
        
        # Rendement relatif (1.0 = moyenne nationale)
        yield_ratio = yield_predit / yield_ref if yield_ref > 0 else 1.0
        
        # Transformation en score B sur 100 :
        # - ratio 0.5 (moitié de la moyenne) -> score 40
        # - ratio 1.0 (exactement la moyenne) -> score 75
        # - ratio 1.5 (50% de plus que la moyenne) -> score 100
        score_B = min(100, max(0, round(40 + (yield_ratio - 0.5) * 70)))

        # Si pas de variété dans le catalogue, pénaliser fortement.
        # Les cultures ML avec de vraies variétés doivent TOUJOURS dominer
        # les cultures maraîchères sans données de catalogue.
        if varietes:
            score_A = varietes[0]["score_adaptation"]
        elif culture_en in CULTURES_MARAICHERES_EN:
            # Maraîchères sans catalogue : plafond bas (45) pour ne jamais
            # battre les cultures principales qui ont des variétés réelles
            score_A = min(45, score_B)
        else:
            # Autres cultures sans variétés (rare) : score neutre
            score_A = min(55, score_B)
        
        score_final = round(poids_A * score_A + poids_B * score_B)

        niveau = ("Optimal"   if score_final >= 80
                  else "Suboptimal" if score_final >= 60
                  else "Risqué")

        culture_fr = CULTURE_MAP_ETENDU.get(culture_en, culture_en.lower())
        resultats.append({
            "culture"          : culture_en,
            "culture_fr"       : culture_fr,
            "score_final"      : score_final,
            "score_adaptation" : score_A,
            "yield_predit_tha" : round(yield_predit, 2),
            "rendement_relatif": round(
                yield_predit/yield_ref if yield_ref>0 else 1.0, 2),
            "source_yield"     : source_yield,
            "niveau"           : niveau,
            "varietes_top3"    : varietes,
            "zone"             : zone,
            "precip_mm"        : clim["precip_annuel"],
            "ph_sol"           : soil["soil_ph"],
            "clay_pct"         : soil["clay_pct"],
        })

    resultats = sorted(
        resultats,
        key=lambda x: (x["score_final"], x["yield_predit_tha"]),
        reverse=True
    )
    return resultats[:top_n], zone, clim, soil
