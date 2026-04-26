from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from contextlib import asynccontextmanager
import os
import traceback
from dotenv import load_dotenv

# Import du pipeline ML existant
try:
    from pipeline_gps import recommend_for_gps, load_models, load_catalogue
except ImportError as e:
    print(f"Erreur import pipeline_gps: {e}")

load_dotenv()

# Variables globales d'état
MODELS_LOADED = False

# ============================================================
# LIFESPAN : Chargement asynchrone des modèles au démarrage
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODELS_LOADED
    print("Démarrage de l'API NOUKOU...")
    try:
        print("Chargement des modèles ML en mémoire (RandomForest, Ridge)...")
        load_models()
        print("Chargement du catalogue des variétés (Excel)...")
        load_catalogue()
        MODELS_LOADED = True
        print("Tous les modeles sont charges avec succes.")
    except Exception as e:
        print(f"Erreur lors du chargement des modeles : {e}")
        # On ne plante pas l'API, on permet au healthcheck de signaler le pb.
        MODELS_LOADED = False
    
    yield
    print("Arrêt de l'API NOUKOU.")

# ============================================================
# INITIALISATION FASTAPI
# ============================================================
app = FastAPI(
    title="NOUKOU-Predict API",
    description="Moteur IA de recommandation agricole — CUBE Togo",
    version="1.0.0",
    lifespan=lifespan
)

# CORS pour autoriser le frontend (local ou distant)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# SCHÉMAS PYDANTIC (Validation des entrées)
# ============================================================
class AnalyseRequest(BaseModel):
    lat: float = Field(..., description="Latitude GPS")
    lon: float = Field(..., description="Longitude GPS")

    @validator('lat')
    def validate_lat(cls, v):
        if not (6.0 <= v <= 11.2):
            raise ValueError("Latitude hors des frontières du Togo (6.0 à 11.2)")
        return v

    @validator('lon')
    def validate_lon(cls, v):
        if not (0.0 <= v <= 1.9):
            raise ValueError("Longitude hors des frontières du Togo (0.0 à 1.9)")
        return v

# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/health")
def health_check():
    """Endpoint pour vérifier la santé de l'API (utile pour Railway/Render)."""
    return {
        "status": "ok" if MODELS_LOADED else "degraded",
        "model_loaded": MODELS_LOADED
    }

@app.get("/api/zones")
def get_zones():
    """Retourne la liste des 5 zones agro-écologiques du Togo."""
    return {
        "success": True,
        "zones": [
            {"nom": "Savanes", "climat_type": "Sec", "cultures_phares": ["Maïs", "Sorgho", "Oignon"]},
            {"nom": "Kara", "climat_type": "Semi-sec", "cultures_phares": ["Igname", "Maïs", "Coton"]},
            {"nom": "Centrale", "climat_type": "Tropical", "cultures_phares": ["Igname", "Manioc", "Soja"]},
            {"nom": "Plateaux", "climat_type": "Humide", "cultures_phares": ["Café", "Cacao", "Banane", "Manioc"]},
            {"nom": "Maritime", "climat_type": "Côtier", "cultures_phares": ["Maïs", "Maraîchage", "Riz"]}
        ]
    }

@app.post("/api/analyse")
def analyse_parcelle(request: AnalyseRequest):
    """
    Endpoint principal. Lance le pipeline_gps (Modèle A + Modèle B) 
    pour générer la recommandation.
    """
    if not MODELS_LOADED:
        return {"success": False, "error": "Les modèles IA ne sont pas correctement chargés sur le serveur."}
    
    try:
        # Appel du pipeline
        top3, zone, clim, sol = recommend_for_gps(
            lat=request.lat, 
            lon=request.lon,
            token=None,  # Utilisera les identifiants .env ou fallback
            top_n=3
        )
        
        return {
            "success": True,
            "zone": zone,
            "climat": {
                "precip_annuel": clim.get("precip_annuel", 0),
                "temp_moyenne": clim.get("temp_moyenne", 0),
                "humidity_rel": clim.get("humidity_rel", 0)
            },
            "sol": {
                "soil_ph": sol.get("soil_ph", 0),
                "clay_pct": sol.get("clay_pct", 0),
                "soc_gkg": sol.get("soc_gkg", 0)
            },
            "recommandations": top3
        }

    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": f"Erreur interne lors de la prédiction: {str(e)}"}


# ============================================================
# GUIDE DE TEST LOCAL
# ============================================================
# POUR TESTER EN LOCAL :
# 1. Copier .env.example en .env et remplir les credentials
# 2. pip install -r requirements.txt
# 3. uvicorn app:app --reload --host 0.0.0.0 --port 8000
# 4. Ouvrir http://localhost:8000/docs (Swagger auto-généré)
# 5. Tester POST /api/analyse avec body: {"lat": 7.533, "lon": 1.124}
# 6. Résultat attendu : igname #1, manioc #2, maïs #3 (zone Plateaux)
# 7. Tester GET /health → {"status": "ok", "model_loaded": true}
