"""Central configuration for CropYield AI (paths, units, labels, colours)."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "crop_yield.csv"
MODEL_PATH = ROOT / "models" / "crop_yield_model.joblib"
META_PATH = ROOT / "models" / "model_metadata.json"
DIAG_PATH = ROOT / "models" / "model_diagnostics.json"
DB_PATH = Path(os.environ.get("CROPYIELD_DB", ROOT / "crop_yield.db"))
ASSETS = ROOT / "assets"
CROP_IMG_DIR = ASSETS / "crop_images"
BANNER_CANDIDATES = [ASSETS / "farm_banner.jpg", ASSETS / "farm_banner.jpeg", ASSETS / "farm_banner.png"]

# Crops whose yield is NOT tonnes/ha in the source data (source conventions).
# Coconut is recorded in nuts; cotton(lint), jute and mesta are recorded in bales.
NON_TONNE_UNITS = {
    "Coconut": ("nuts per hectare", "nuts"),
    "Cotton(lint)": ("bales per hectare", "bales"),
    "Jute": ("bales per hectare", "bales"),
    "Mesta": ("bales per hectare", "bales"),
}

# Home-page gallery: (label shown, dataset crop name or None, image file stem)
GALLERY = [
    ("Rice", "Rice", "rice"), ("Wheat", "Wheat", "wheat"), ("Maize", "Maize", "maize"),
    ("Cotton", "Cotton(lint)", "cotton"), ("Sugarcane", "Sugarcane", "sugarcane"),
    ("Other Crops", None, "other"),
]

# Plain-language labels / units / help for every model feature (order comes from model metadata).
FEATURE_INFO = {
    "Crop": ("Crop", "category", "Crop category exactly as recorded in the training data."),
    "Season": ("Growing season", "category", "Season category from the source data (Kharif, Rabi, Summer, Autumn, Winter, Whole Year)."),
    "State": ("State / UT", "category", "Indian state or union territory of the historical record."),
    "Crop_Year": ("Crop year", "year", "Calendar year of the record. The model saw 1997-2020 only."),
    "Area": ("Cultivated area", "hectares (ha)", "Area under the crop. Used by the model AND to scale yield into total production."),
    "Annual_Rainfall": ("Annual rainfall", "millimetres (mm)", "Total yearly rainfall for the state/year."),
    "Fertilizer": ("Fertilizer (total)", "kilograms (kg)", "Model input = rate (kg/ha) x area (ha). The training data stores totals, not rates."),
    "Pesticide": ("Pesticide (total)", "kilograms (kg)", "Model input = rate (kg/ha) x area (ha). The training data stores totals, not rates."),
}

# Colours
GREEN_DARK = "#0b3d2e"
GREEN = "#12804a"
GREEN_LIGHT = "#e6f5ec"
TEAL = "#17a2a2"
AMBER = "#f59e0b"
CHART_COLORS = ["#3fae5a", "#f28c28", "#f6c945", "#4da3f0", "#a66ee0", "#17a2a2", "#e8605d", "#7a8b99"]

PAGES = [  # (label, icon, script path relative to app.py) in sidebar order
    ("Home", "🏠", "app.py"),
    ("Predict Yield", "🌱", "pages/1_Predict_Yield.py"),
    ("History", "🕘", "pages/4_Prediction_History.py"),
    ("Data Insights", "📊", "pages/3_Data_Insights.py"),
    ("Model Info", "🧠", "pages/5_Model_Info.py"),
    ("Recommendations", "💡", "pages/2_Recommendations.py"),
    ("About", "ℹ️", "pages/6_About.py"),
]
