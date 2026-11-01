"""Basic offline integrity check for the bundled CropYield AI model."""
import json
from pathlib import Path
import joblib
import pandas as pd

ROOT = Path(__file__).parent
meta = json.loads((ROOT / "models" / "model_metadata.json").read_text(encoding="utf-8"))
model = joblib.load(ROOT / "models" / "crop_yield_model.joblib")
row = {
    "Crop": "Rice", "Season": "Kharif", "State": "Odisha", "Crop_Year": 2026,
    "Area": 2.0, "Annual_Rainfall": 1200.6, "Fertilizer": 100.0, "Pesticide": 2.0,
}
pred = float(model.predict(pd.DataFrame([row], columns=meta["features"]))[0])
assert pd.notna(pred) and pred >= 0, f"Invalid prediction: {pred}"
print(f"Model OK | {meta['model_name']} | sample rice yield: {pred:.3f} tonnes/ha")
