from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from contextlib import asynccontextmanager
import os
import traceback
import secrets
from datetime import datetime, timedelta
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import jwt, JWTError

# SQLAlchemy
from sqlalchemy import create_engine, Column, String, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Import du pipeline ML existant
try:
    from pipeline_gps import recommend_for_gps, load_models, load_catalogue
except ImportError as e:
    print(f"Erreur import pipeline_gps: {e}")

load_dotenv()

# ============================================================
# DATABASE SETUP — SQLite local / PostgreSQL sur Railway
# ============================================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./noukou_users.db")

# Railway renvoie parfois "postgres://" (ancien format), on corrige
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite a besoin de check_same_thread=False
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ── Modèle utilisateur ──────────────────────────────────────
class UserModel(Base):
    __tablename__ = "users"

    email        = Column(String(255), primary_key=True, index=True)
    name         = Column(String(120), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# AUTH CONFIG
# ============================================================
JWT_SECRET      = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM   = "HS256"
JWT_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# ============================================================
# LIFESPAN : Chargement des modèles ML + création des tables
# ============================================================
MODELS_LOADED = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODELS_LOADED

    # Créer les tables si elles n'existent pas
    print("Initialisation de la base de données...")
    Base.metadata.create_all(bind=engine)
    print("Tables créées / vérifiées.")

    print("Démarrage de l'API NOUKOU...")
    try:
        print("Chargement des modèles ML (RandomForest, Ridge)...")
        load_models()
        print("Chargement du catalogue des variétés (Excel)...")
        load_catalogue()
        MODELS_LOADED = True
        print("Tous les modèles sont chargés avec succès.")
    except Exception as e:
        print(f"Erreur lors du chargement des modèles : {e}")
        MODELS_LOADED = False

    yield
    print("Arrêt de l'API NOUKOU.")

# ============================================================
# INITIALISATION FASTAPI
# ============================================================
app = FastAPI(
    title="NOUKOU-Predict API",
    description="Moteur IA de recommandation agricole — CUBE Togo",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# SCHÉMAS PYDANTIC
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

class RegisterRequest(BaseModel):
    name:     str = Field(..., min_length=2, max_length=80)
    email:    str = Field(...)
    password: str = Field(..., min_length=8)

class LoginRequest(BaseModel):
    email:    str
    password: str

# ============================================================
# ENDPOINTS AUTH
# ============================================================

@app.post("/api/auth/register", summary="Créer un compte")
def register(req: RegisterRequest):
    """Crée un nouvel utilisateur et retourne un JWT."""
    email = req.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Email invalide.")

    db = SessionLocal()
    try:
        existing = db.query(UserModel).filter(UserModel.email == email).first()
        if existing:
            raise HTTPException(status_code=409, detail="Un compte avec cet email existe déjà.")

        user = UserModel(
            email=email,
            name=req.name.strip(),
            password_hash=pwd_context.hash(req.password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    finally:
        db.close()

    token = create_token({"sub": email, "name": req.name.strip()})
    return {"token": token, "user": {"name": req.name.strip(), "email": email}}


@app.post("/api/auth/login", summary="Se connecter")
def login(req: LoginRequest):
    """Authentifie l'utilisateur et retourne un JWT."""
    email = req.email.strip().lower()

    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.email == email).first()
    finally:
        db.close()

    # Message générique : ne pas révéler si l'email existe
    if not user or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants incorrects.")

    token = create_token({"sub": email, "name": user.name})
    return {"token": token, "user": {"name": user.name, "email": email}}


# ============================================================
# ENDPOINTS PRINCIPAUX
# ============================================================

@app.get("/health")
def health_check():
    """Vérifie la santé de l'API."""
    return {
        "status": "ok" if MODELS_LOADED else "degraded",
        "model_loaded": MODELS_LOADED
    }

@app.get("/api/zones")
def get_zones():
    """Liste des zones agro-écologiques du Togo."""
    return {
        "success": True,
        "zones": [
            {"nom": "Savanes",   "climat_type": "Sec",      "cultures_phares": ["Maïs", "Sorgho", "Oignon"]},
            {"nom": "Kara",      "climat_type": "Semi-sec", "cultures_phares": ["Igname", "Maïs", "Coton"]},
            {"nom": "Centrale",  "climat_type": "Tropical", "cultures_phares": ["Igname", "Manioc", "Soja"]},
            {"nom": "Plateaux",  "climat_type": "Humide",   "cultures_phares": ["Café", "Cacao", "Banane", "Manioc"]},
            {"nom": "Maritime",  "climat_type": "Côtier",   "cultures_phares": ["Maïs", "Maraîchage", "Riz"]}
        ]
    }

@app.post("/api/analyse")
def analyse_parcelle(request: AnalyseRequest):
    """
    Endpoint principal — Lance le pipeline_gps (Modèle A + Modèle B).
    """
    if not MODELS_LOADED:
        return {"success": False, "error": "Les modèles IA ne sont pas correctement chargés sur le serveur."}

    try:
        top3, zone, clim, sol = recommend_for_gps(
            lat=request.lat,
            lon=request.lon,
            token=None,
            top_n=3
        )
        return {
            "success": True,
            "zone": zone,
            "climat": {
                "precip_annuel": clim.get("precip_annuel", 0),
                "temp_moyenne":  clim.get("temp_moyenne", 0),
                "humidity_rel":  clim.get("humidity_rel", 0)
            },
            "sol": {
                "soil_ph":  sol.get("soil_ph", 0),
                "clay_pct": sol.get("clay_pct", 0),
                "soc_gkg":  sol.get("soc_gkg", 0)
            },
            "recommandations": top3
        }
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": f"Erreur interne lors de la prédiction: {str(e)}"}


# ============================================================
# GUIDE DE TEST LOCAL
# ============================================================
# 1. Copier .env.example en .env et remplir les credentials
# 2. pip install -r requirements.txt
# 3. uvicorn app:app --reload --host 0.0.0.0 --port 8000
# 4. http://localhost:8000/docs  (Swagger auto-généré)
# Sur Railway : ajouter la variable DATABASE_URL (PostgreSQL plugin)
