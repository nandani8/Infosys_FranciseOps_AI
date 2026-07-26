"""
config.py — FranchiseOps AI (v3 FINAL)
All secrets from Colab userdata. KMEANS_MODEL_PATH = kmeans_outlets.joblib (spec compliant).
"""
import os

def _get_secret(key):
    try:
        from google.colab import userdata
        val = userdata.get(key)
        if val: return val
    except Exception:
        pass
    return os.environ.get(key, "")

try:
    from __main__ import (STORAGE_DIR, NGROK_AUTHTOKEN, HF_TOKEN,
                          KAGGLE_USERNAME, KAGGLE_KEY, EMAIL_PASSWORD,
                          ADMIN_EMAIL, ADMIN_PASSWORD, EMAIL_ID,JWT_SECRET_KEY)
except ImportError:
    STORAGE_DIR    = ("/content/drive/MyDrive/FranchiseOps_AI"
                      if os.path.exists("/content/drive/MyDrive") else
                      os.path.abspath("./data/FranchiseOps_AI"))
    NGROK_AUTHTOKEN = _get_secret("NGROK_AUTHTOKEN")
    NGROK_AUTH_TOKEN = NGROK_AUTHTOKEN # Alias for launch cell compatibility
    HF_TOKEN        = _get_secret("HF_TOKEN")
    JWT_SECRET_KEY = _get_secret("JWT_SECRET_KEY")
    KAGGLE_USERNAME = _get_secret("KAGGLE_USERNAME")
    KAGGLE_KEY      = _get_secret("KAGGLE_KEY")
    EMAIL_PASSWORD  = _get_secret("EMAIL_PASSWORD").replace(" ", "")
    EMAIL_ID        = _get_secret("EMAIL_ID")
    JWT_SECRET_KEY  = _get_secret("JWT_SECRET_KEY") or "franchiseops-dev-secret-changeme"
    ADMIN_EMAIL     = _get_secret("ADMIN_EMAIL_ID")  or "infosys@ai"
    ADMIN_PASSWORD  = _get_secret("ADMIN_PASSWORD")  or "admin@123"
EMAIL_PASSWORD = (EMAIL_PASSWORD or "").replace(" ", "")
os.makedirs(STORAGE_DIR, exist_ok=True)
DB_PATH          = os.path.join(STORAGE_DIR, "franchiseops.db")
MODELS_DIR       = os.path.join(STORAGE_DIR, "models")
KAGGLE_CACHE_DIR = os.path.join(MODELS_DIR, "kaggle_cache")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(KAGGLE_CACHE_DIR, exist_ok=True)

# Model paths (filenames match Infosys spec exactly)
AGENT1_MODEL_PATH = os.path.join(MODELS_DIR, "attrition_lr.joblib")
KMEANS_MODEL_PATH = os.path.join(MODELS_DIR, "kmeans_outlets.joblib")   # spec: kmeans_outlets
AGENT2_MODEL_PATH = KMEANS_MODEL_PATH                                    # alias
AGENT2_REG_PATH   = os.path.join(MODELS_DIR, "revenue_rf.joblib")
AGENT3_MODEL_PATH = os.path.join(MODELS_DIR, "inventory_demand_gb.joblib")
