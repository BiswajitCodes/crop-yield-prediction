"""Core tests against the REAL model, dataset and a temporary SQLite database.
Run from the project folder:  python tests/test_core.py"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
tmp = tempfile.mkdtemp()
os.environ["CROPYIELD_DB"] = str(Path(tmp) / "test.db")

import math
import sqlite3
import warnings

import pandas as pd

import config
import database
import model_service as ms
import recommendations as rec

passed = 0


def check(cond, msg):
    global passed
    assert cond, "FAIL: " + msg
    passed += 1
    print("ok  -", msg)


# --- model & schema
warnings.simplefilter("error", UserWarning)  # any sklearn version mismatch warning would fail here
model = ms.get_model()
meta = ms.get_metadata()
check(list(model.feature_names_in_) == meta["features"], "model feature names/order match metadata")
check(len(meta["crops"]) == 55 and len(meta["states"]) == 30 and len(meta["seasons"]) == 6, "metadata category counts")
warnings.simplefilter("default")

# --- real prediction + production maths
res = ms.run_prediction("Rice", "Odisha", "Kharif", 2026, 2.0, 1200.6, 100.0, 2.0)
direct = float(model.predict(pd.DataFrame([{"Crop": "Rice", "Season": "Kharif", "State": "Odisha", "Crop_Year": 2026,
                                           "Area": 2.0, "Annual_Rainfall": 1200.6, "Fertilizer": 200.0, "Pesticide": 4.0}],
                                          columns=meta["features"]))[0])
check(math.isclose(res["yield"], direct, rel_tol=1e-12), f"service prediction equals direct model call ({res['yield']:.4f})")
check(math.isclose(res["production"], res["yield"] * 2.0), "production = yield x area")
check(res["row"]["Fertilizer"] == 200.0 and res["row"]["Pesticide"] == 4.0, "per-ha rates converted to totals")
check(res["yield_unit"] == "tonnes per hectare" and res["production_unit"] == "tonnes", "tonne units for rice")
coco = ms.run_prediction("Coconut", "Kerala", "Whole Year", 2018, 100.0, 3000.0, 140.0, 0.3)
check(coco["yield"] > 1000 and coco["yield_unit"] == "nuts per hectare" and coco["production_unit"] == "nuts", "coconut uses nut units")

# --- every crop/state/season predicts finitely
bad = 0
for c in meta["crops"]:
    r = ms.run_prediction(c, "Punjab", "Rabi", 2015, 100.0, 900.0, 140.0, 0.27)
    bad += not (math.isfinite(r["yield"]) and r["yield"] >= 0)
for s in meta["states"]:
    bad += not math.isfinite(ms.run_prediction("Rice", s, "Kharif", 2015, 100.0, 900.0, 140.0, 0.27)["yield"])
for s in meta["seasons"]:
    bad += not math.isfinite(ms.run_prediction("Rice", "Assam", s, 2015, 100.0, 900.0, 140.0, 0.27)["yield"])
check(bad == 0, "all 55 crops, 30 states, 6 seasons return finite non-negative yields")

# --- validation
d = ms.default_inputs()
e, w = ms.validate_inputs("Rice", "Odisha", "Kharif", d["year"], 50000.0, d["rainfall"], d["fert"], d["pest"])
check(not e and not w, f"typical valid input -> no errors, no warnings ({w})")
e, w = ms.validate_inputs("Rice", "Odisha", "Kharif", 2026, 2.0, 1200.6, 100.0, 2.0)
check(not e and len(w) >= 3, "image-style example -> accepted with warnings (year, area, fertilizer, pesticide)")
check(ms.validate_inputs("Rice", "Odisha", "Kharif", 2020, 0.0, 1000.0, 100.0, 0.2)[0], "area 0 rejected")
check(ms.validate_inputs("Rice", "Odisha", "Kharif", 2020, 5.0, -1.0, 100.0, 0.2)[0], "negative rainfall rejected")
check(ms.validate_inputs("Rice", "Odisha", "Kharif", 2020, 5.0, 1000.0, -5.0, 0.2)[0], "negative fertilizer rejected")
check(ms.validate_inputs("Rice", "Odisha", "Kharif", None, 5.0, 1000.0, 100.0, 0.2)[0], "missing year rejected")
check(ms.validate_inputs("Rice", "Odisha", "Kharif", 2020, float("nan"), 1000.0, 100.0, 0.2)[0], "NaN area rejected")
check(ms.validate_inputs("Unobtainium", "Odisha", "Kharif", 2020, 5.0, 1000.0, 100.0, 0.2)[0], "unsupported crop rejected")
check(ms.validate_inputs("Rice", "Atlantis", "Kharif", 2020, 5.0, 1000.0, 100.0, 0.2)[0], "unsupported state rejected")
check(ms.validate_inputs("Rice", "Odisha", "Monsoon", 2020, 5.0, 1000.0, 100.0, 0.2)[0], "unsupported season rejected")
try:
    ms.predict_yield({"Crop": "Rice", "Season": "Kharif", "State": "Odisha", "Crop_Year": 2020, "Area": None,
                      "Annual_Rainfall": 1000.0, "Fertilizer": 1.0, "Pesticide": 1.0})
    check(False, "missing value should raise")
except ValueError:
    check(True, "predict_yield raises ValueError on missing value")

# --- dataset helpers
df = ms.get_dataset()
check(len(df) == meta["dataset_rows"], f"cleaned dataset rows match metadata ({len(df)})")
st = ms.reference_stats("Rice", "Odisha", "Kharif")
check(st["crop_n"] > 100 and "cs_mean" in st and "css_mean" in st, "reference stats computed from the CSV")

# --- recommendations
ins = rec.key_insights(res, st)
grp = rec.grouped_recommendations(res, st)
check(len(ins) >= 3 and set(grp) == {"Soil and water management", "Input management", "Crop management"}, "insights and 3 recommendation groups")
check(all(t in ("data", "general") for g in grp.values() for t, _ in g) and any(t == "data" for g in grp.values() for t, _ in g),
      "items tagged data vs general")
check(len(rec.grouped_recommendations(None, None)["Input management"]) >= 3, "general guidance works without a prediction")

# --- database: create, legacy migration, save, read, filter, delete
database.init_db()
check(database.get_predictions() == [], "fresh DB is empty")
ids = []
for r in (res, coco):
    ids.append(database.save_prediction({**r["row"], "predicted_yield": r["yield"], "production": r["production"],
                                         "fertilizer_rate": r["fert_rate"], "pesticide_rate": r["pest_rate"],
                                         "yield_unit": r["yield_unit"], "production_unit": r["production_unit"]}))
recs = database.get_predictions()
check(len(recs) == 2 and recs[0]["crop"] == "Coconut" and math.isclose(recs[1]["production"], res["production"]), "saved + read back (newest first)")
check(database.delete_predictions([ids[0]]) == 1 and len(database.get_predictions()) == 1, "delete one record")
check(database.delete_predictions([]) == 0, "delete with empty selection is a no-op")
check(database.clear_predictions() == 1 and database.get_predictions() == [], "clear all")

legacy = Path(tmp) / "legacy.db"
conn = sqlite3.connect(legacy)
conn.execute("""CREATE TABLE predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, crop TEXT NOT NULL,
 state TEXT NOT NULL, season TEXT NOT NULL, crop_year INTEGER NOT NULL, area REAL NOT NULL, annual_rainfall REAL NOT NULL,
 fertilizer REAL NOT NULL, pesticide REAL NOT NULL, predicted_yield REAL NOT NULL)""")
conn.execute("INSERT INTO predictions VALUES (NULL,'2026-10-31T08:00:00','Rice','Odisha','Kharif',2018,1000,1200,144000,270,2.0)")
conn.commit(); conn.close()
config.DB_PATH = legacy
database.init_db(); database.init_db()  # idempotent
old = database.get_predictions()[0]
check(old["production"] == 2000.0 and abs(old["fertilizer_rate"] - 144.0) < 1e-9, "legacy rows preserved and back-filled")

print(f"\nALL {passed} CHECKS PASSED")
