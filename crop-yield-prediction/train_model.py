from pathlib import Path
import json
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

warnings.filterwarnings("ignore", category=UserWarning)

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "crop_yield.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "crop_yield_model.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

TARGET = "Yield"
NUMERIC_FEATURES = [
    "Crop_Year", "Area", "Annual_Rainfall", "Fertilizer", "Pesticide"
]
CATEGORICAL_FEATURES = ["Crop", "Season", "State"]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES

def normalize_columns(df):
    df.columns = [str(c).strip() for c in df.columns]
    aliases = {
        "Crop Year": "Crop_Year",
        "Year": "Crop_Year",
        "crop_year": "Crop_Year",
        "annual_rainfall": "Annual_Rainfall",
        "crop": "Crop",
        "season": "Season",
        "state": "State",
        "area": "Area",
        "production": "Production",
        "yield": "Yield",
        "fertilizer": "Fertilizer",
        "pesticide": "Pesticide",
    }
    for old, new in aliases.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
    return df

def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}\n"
            "Download the Kaggle CSV and save it as data/crop_yield.csv."
        )
    df = normalize_columns(pd.read_csv(DATA_PATH))
    required = FEATURES + [TARGET]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing columns: {missing}. Available columns: {list(df.columns)}"
        )

    df = df[required].copy()
    for col in CATEGORICAL_FEATURES:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    for col in NUMERIC_FEATURES + [TARGET]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=[TARGET, "Crop", "State", "Season"])
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df[df[TARGET] >= 0]
    df = df.drop_duplicates()
    if len(df) < 50:
        raise ValueError(f"Only {len(df)} usable rows found; check your CSV.")
    return df

def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()

    X = df[FEATURES]
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median"))
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])
    preprocess = ColumnTransformer([
        ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES)
    ])

    candidates = {
        "RandomForest": RandomForestRegressor(
            n_estimators=300, min_samples_leaf=2, max_features=0.9,
            random_state=42, n_jobs=-1
        ),
        "ExtraTrees": ExtraTreesRegressor(
            n_estimators=300, min_samples_leaf=2, max_features=0.9,
            random_state=42, n_jobs=-1
        ),
        "HistGradientBoosting": HistGradientBoostingRegressor(
            max_iter=250, learning_rate=0.08, max_leaf_nodes=31,
            l2_regularization=1.0, random_state=42
        )
    }

    results = []
    fitted = {}
    for name, estimator in candidates.items():
        # HistGradientBoosting does not accept sparse one-hot input.
        if name == "HistGradientBoosting":
            continue
        pipeline = Pipeline([("preprocess", preprocess), ("model", estimator)])
        pipeline.fit(X_train, y_train)
        pred = pipeline.predict(X_test)
        metrics = {
            "model": name,
            "MAE": float(mean_absolute_error(y_test, pred)),
            "RMSE": float(np.sqrt(mean_squared_error(y_test, pred))),
            "R2": float(r2_score(y_test, pred))
        }
        results.append(metrics)
        fitted[name] = pipeline

    best = min(results, key=lambda item: item["RMSE"])
    best_pipeline = fitted[best["model"]]
    joblib.dump(best_pipeline, MODEL_PATH)

    metadata = {
        "model_name": best["model"],
        "metrics": best,
        "dataset_rows": int(len(df)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "features": FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "target": TARGET,
        "crops": sorted(df["Crop"].dropna().astype(str).unique().tolist()),
        "states": sorted(df["State"].dropna().astype(str).unique().tolist()),
        "seasons": sorted(df["Season"].dropna().astype(str).unique().tolist()),
        "numeric_defaults": {
            col: float(df[col].median()) for col in NUMERIC_FEATURES
        }
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("\nModel comparison (lower MAE/RMSE is better; higher R² is better):")
    print(pd.DataFrame(results).sort_values("RMSE").to_string(index=False))
    print(f"\nBest model: {best['model']}")
    print(f"Saved model: {MODEL_PATH}")
    print(f"Saved metadata: {METADATA_PATH}")

if __name__ == "__main__":
    main()
