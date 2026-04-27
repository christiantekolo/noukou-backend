from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from contextlib import asynccontextmanager
import os
import traceback
import secrets
import shutil
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import jwt, JWTError

# SQLAlchemy
from sqlalchemy import create_engine, Column, String, DateTime, Text, text
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
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ── Modèle utilisateur (étendu avec profil complet) ──────────
class UserModel(Base):
    __tablename__ = "users"

    email         = Column(String(255), primary_key=True, index=True)
    name          = Column(String(120), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Champs profil optionnels
    phone         = Column(String(30),  nullable=True)
    country       = Column(String(80),  nullable=True)
    city          = Column(String(80),  nullable=True)
    bio           = Column(Text,        nullable=True)
    photo_url     = Column(String(500), nullable=True)
    profession    = Column(String(120), nullable=True)
    surface_ha    = Column(String(30),  nullable=True)   # surface agricole gérée
    updated_at    = Column(DateTime, nullable=True)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# AUTH CONFIG
# ============================================================
JWT_SECRET       = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM    = "HS256"
JWT_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré. Veuillez vous reconnecter.")

def get_current_user_email(authorization: Optional[str] = Header(None)) -> str:
    """Dépendance FastAPI — extrait et valide le JWT du header Authorization."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentification requise.")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide.")
    return email

# ============================================================
# LIFESPAN : Chargement des modèles ML + création des tables
# ============================================================
MODELS_LOADED = False

# Dossier pour les photos de profil
UPLOAD_DIR = "uploads/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODELS_LOADED

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
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir les fichiers statiques (photos de profil)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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

class ProfileUpdateRequest(BaseModel):
    name:        Optional[str] = Field(None, min_length=2, max_length=80)
    phone:       Optional[str] = Field(None, max_length=30)
    country:     Optional[str] = Field(None, max_length=80)
    city:        Optional[str] = Field(None, max_length=80)
    bio:         Optional[str] = Field(None, max_length=500)
    profession:  Optional[str] = Field(None, max_length=120)
    surface_ha:  Optional[str] = Field(None, max_length=30)

def user_to_dict(user: UserModel) -> dict:
    """Sérialise un UserModel sans exposer le hash du mot de passe."""
    return {
        "email":       user.email,
        "name":        user.name,
        "phone":       user.phone,
        "country":     user.country,
        "city":        user.city,
        "bio":         user.bio,
        "photo_url":   user.photo_url,
        "profession":  user.profession,
        "surface_ha":  user.surface_ha,
        "created_at":  user.created_at.isoformat() if user.created_at else None,
        "updated_at":  user.updated_at.isoformat() if user.updated_at else None,
    }

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
        user_data = user_to_dict(user)
    finally:
        db.close()

    token = create_token({"sub": email, "name": req.name.strip()})
    return {"token": token, "user": user_data}


@app.post("/api/auth/login", summary="Se connecter")
def login(req: LoginRequest):
    """Authentifie l'utilisateur et retourne un JWT."""
    email = req.email.strip().lower()

    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user or not pwd_context.verify(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Identifiants incorrects.")
        user_data = user_to_dict(user)
    finally:
        db.close()

    token = create_token({"sub": email, "name": user.name})
    return {"token": token, "user": user_data}


@app.get("/api/auth/me", summary="Profil de l'utilisateur connecté")
def get_me(current_email: str = Depends(get_current_user_email)):
    """Retourne les infos du profil de l'utilisateur connecté (token requis)."""
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.email == current_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
        return {"user": user_to_dict(user)}
    finally:
        db.close()


# ============================================================
# ENDPOINTS PROFIL
# ============================================================

@app.put("/api/profile/update", summary="Mettre à jour le profil")
def update_profile(req: ProfileUpdateRequest, current_email: str = Depends(get_current_user_email)):
    """Met à jour les informations du profil (token requis)."""
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.email == current_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

        if req.name       is not None: user.name       = req.name.strip()
        if req.phone      is not None: user.phone      = req.phone.strip()
        if req.country    is not None: user.country    = req.country.strip()
        if req.city       is not None: user.city       = req.city.strip()
        if req.bio        is not None: user.bio        = req.bio.strip()
        if req.profession is not None: user.profession = req.profession.strip()
        if req.surface_ha is not None: user.surface_ha = req.surface_ha.strip()
        user.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(user)
        return {"success": True, "user": user_to_dict(user)}
    finally:
        db.close()


@app.post("/api/profile/photo", summary="Uploader une photo de profil")
async def upload_photo(
    file: UploadFile = File(...),
    current_email: str = Depends(get_current_user_email)
):
    """Upload une photo de profil (JPEG/PNG, max 5 Mo). Token requis."""
    # Validation type
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez JPEG, PNG ou WebP.")

    # Validation taille (5 Mo max)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image trop grande (max 5 Mo).")

    # Nom de fichier sécurisé basé sur l'email (un seul fichier par user)
    ext = file.content_type.split("/")[1].replace("jpeg", "jpg")
    safe_name = current_email.replace("@", "_at_").replace(".", "_") + f".{ext}"
    filepath = os.path.join(UPLOAD_DIR, safe_name)

    with open(filepath, "wb") as f:
        f.write(contents)

    # URL publique (Railway sert les fichiers statiques via /uploads)
    photo_url = f"/uploads/avatars/{safe_name}"

    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.email == current_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
        user.photo_url = photo_url
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return {"success": True, "photo_url": photo_url, "user": user_to_dict(user)}
    finally:
        db.close()


# ============================================================
# ENDPOINTS PRINCIPAUX (protégés par JWT)
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
            {"nom": "Savanes",  "climat_type": "Sec",      "cultures_phares": ["Maïs", "Sorgho", "Oignon"]},
            {"nom": "Kara",     "climat_type": "Semi-sec", "cultures_phares": ["Igname", "Maïs", "Coton"]},
            {"nom": "Centrale", "climat_type": "Tropical", "cultures_phares": ["Igname", "Manioc", "Soja"]},
            {"nom": "Plateaux", "climat_type": "Humide",   "cultures_phares": ["Café", "Cacao", "Banane", "Manioc"]},
            {"nom": "Maritime", "climat_type": "Côtier",   "cultures_phares": ["Maïs", "Maraîchage", "Riz"]}
        ]
    }

@app.post("/api/analyse")
def analyse_parcelle(
    request: AnalyseRequest,
    current_email: str = Depends(get_current_user_email)   # ← JWT requis
):
    """
    Endpoint principal — Lance le pipeline_gps (Modèle A + Modèle B).
    Nécessite un token JWT valide dans le header Authorization.
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
