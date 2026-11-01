"""Model + dataset access. Pure Python (no Streamlit imports) so it is easy to test.

The trained pipeline expects the 8 features in model_metadata.json. The training data stores
Fertilizer and Pesticide as TOTAL kg for the area, so the UI collects kg/ha and converts here.
"""
from __future__ import annotations

import functools
import json
import math
import warnings
from typing import Any

import joblib
import numpy as np
import pandas as pd

import config


class ModelUnavailable(Exception):
    """Raised when the model/metadata cannot be loaded or does not match its schema."""


# ----------------------------------------------------------------------------- loading
@functools.lru_cache(maxsize=1)
def get_metadata() -> dict:
    if not config.META_PATH.exists():
        raise ModelUnavailable(f"Model metadata not found: {config.META_PATH}")
    try:
        return json.loads(config.META_PATH.read_text(encoding="utf-8"))
    except Exception as exc:  # corrupt JSON
        raise ModelUnavailable(f"Could not read model metadata: {exc}") from exc


@functools.lru_cache(maxsize=1)
def get_model():
    """Load the trained pipeline and verify it matches the metadata feature schema."""
    meta = get_metadata()
    if not config.MODEL_PATH.exists():
        raise ModelUnavailable(f"Model file not found: {config.MODEL_PATH}")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            model = joblib.load(config.MODEL_PATH)
        except Exception as exc:
            raise ModelUnavailable(
                f"The model file could not be loaded ({type(exc).__name__}: {exc}). "
                "Make sure scikit-learn==1.8.0 is installed (see requirements.txt)."
            ) from exc
    version_warnings = [str(w.message) for w in caught if "version" in str(w.message).lower()]
    names = getattr(model, "feature_names_in_", None)
    if names is not None and list(names) != list(meta["features"]):
        raise ModelUnavailable(
            f"Model features {list(names)} do not match metadata {meta['features']}."
        )
    model._cropyield_version_warnings = version_warnings  # type: ignore[attr-defined]
    return model


def version_warnings() -> list[str]:
    try:
        return list(getattr(get_model(), "_cropyield_version_warnings", []))
    except ModelUnavailable:
        return []


@functools.lru_cache(maxsize=1)
def get_dataset() -> pd.DataFrame:
    """Cleaned dataset (same cleaning as train_model.py) plus per-hectare columns."""
    if not config.DATA_PATH.exists():
        raise ModelUnavailable(f"Dataset not found: {config.DATA_PATH}")
    df = pd.read_csv(config.DATA_PATH)
    df.columns = [str(c).strip() for c in df.columns]
    for c in ("Crop", "Season", "State"):
        df[c] = df[c].astype(str).str.strip()
    for c in ("Crop_Year", "Area", "Production", "Annual_Rainfall", "Fertilizer", "Pesticide", "Yield"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Yield", "Crop", "State", "Season", "Area"])
    df = df[(df["Yield"] >= 0) & (df["Area"] > 0)].drop_duplicates().reset_index(drop=True)
    df["Fertilizer_per_ha"] = df["Fertilizer"] / df["Area"]
    df["Pesticide_per_ha"] = df["Pesticide"] / df["Area"]
    return df


def get_diagnostics() -> dict | None:
    """Optional evaluation details produced by evaluate_model.py from the real model."""
    if not config.DIAG_PATH.exists():
        return None
    try:
        return json.loads(config.DIAG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


# ----------------------------------------------------------------------------- units
def yield_unit(crop: str) -> str:
    return config.NON_TONNE_UNITS.get(crop, ("tonnes per hectare", "tonnes"))[0]


def yield_unit_short(crop: str) -> str:
    return {"tonnes per hectare": "t/ha", "nuts per hectare": "nuts/ha", "bales per hectare": "bales/ha"}[yield_unit(crop)]


def production_unit(crop: str) -> str:
    return config.NON_TONNE_UNITS.get(crop, ("", "tonnes"))[1]


# ----------------------------------------------------------------------------- inputs
def build_input_row(crop, state, season, year, area, rainfall, fert_rate, pest_rate) -> dict:
    """Convert UI values (rates per ha) into the exact model input row."""
    return {
        "Crop": crop, "Season": season, "State": state, "Crop_Year": int(year),
        "Area": float(area), "Annual_Rainfall": float(rainfall),
        "Fertilizer": float(fert_rate) * float(area), "Pesticide": float(pest_rate) * float(area),
    }


def validate_inputs(crop, state, season, year, area, rainfall, fert_rate, pest_rate) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors block prediction; warnings are shown with the result."""
    meta, df = get_metadata(), get_dataset()
    errors: list[str] = []
    warns: list[str] = []

    def bad(v) -> bool:
        return v is None or (isinstance(v, float) and not math.isfinite(v))

    for label, v in (("Crop year", year), ("Cultivated area", area), ("Annual rainfall", rainfall),
                     ("Fertilizer rate", fert_rate), ("Pesticide rate", pest_rate)):
        if bad(v):
            errors.append(f"{label} is missing or not a valid number.")
    if errors:
        return errors, warns
    if crop not in meta["crops"]:
        errors.append(f"Crop '{crop}' is not supported by the trained model.")
    if state not in meta["states"]:
        errors.append(f"State / UT '{state}' is not supported by the trained model.")
    if season not in meta["seasons"]:
        errors.append(f"Season '{season}' is not supported by the trained model.")
    if area <= 0:
        errors.append("Cultivated area must be greater than 0 hectares.")
    if rainfall < 0:
        errors.append("Annual rainfall cannot be negative.")
    if fert_rate < 0 or pest_rate < 0:
        errors.append("Fertilizer and pesticide rates cannot be negative.")
    if not (1900 <= year <= 2100):
        errors.append("Crop year must be between 1900 and 2100.")
    if errors:
        return errors, warns

    yr_min, yr_max = int(df.Crop_Year.min()), int(df.Crop_Year.max())
    if year < yr_min or year > yr_max:
        warns.append(f"The model was trained on {yr_min}-{yr_max}. Tree-based models cannot extrapolate, so {year} "
                     f"is treated like the nearest year they have seen.")
    sub = df[df.Crop == crop]
    if len(sub) and (area < sub.Area.min()):
        warns.append(f"Area ({area:,.2f} ha) is smaller than any {crop} record in the dataset "
                     f"(smallest: {sub.Area.min():,.0f} ha). The data are state/district-level totals, so small-field "
                     f"predictions are extrapolation and area barely changes the predicted yield.")
    if len(sub) and not (sub.Annual_Rainfall.min() <= rainfall <= sub.Annual_Rainfall.max()):
        warns.append(f"Rainfall {rainfall:,.0f} mm is outside the range seen for {crop} "
                     f"({sub.Annual_Rainfall.min():,.0f}-{sub.Annual_Rainfall.max():,.0f} mm).")
    flo, fhi = df.Fertilizer_per_ha.min(), df.Fertilizer_per_ha.max()
    if not (flo <= fert_rate <= fhi):
        warns.append(f"Fertilizer rate {fert_rate:,.1f} kg/ha is outside the range in the training data "
                     f"({flo:,.0f}-{fhi:,.0f} kg/ha); the model has no experience there.")
    plo, phi = df.Pesticide_per_ha.min(), df.Pesticide_per_ha.max()
    if not (plo <= pest_rate <= phi):
        warns.append(f"Pesticide rate {pest_rate:,.2f} kg/ha is outside the range in the training data "
                     f"({plo:,.2f}-{phi:,.2f} kg/ha); the model has no experience there.")
    if len(sub[(sub.State == state)]) == 0:
        warns.append(f"No {crop} records exist for {state} in the dataset; the estimate relies on other states.")
    elif len(sub[(sub.State == state) & (sub.Season == season)]) == 0:
        warns.append(f"No {crop} records exist for {state} in the {season} season; treat the estimate with extra care.")
    return errors, warns


# ----------------------------------------------------------------------------- prediction
def predict_yield(row: dict) -> float:
    """Run the real trained model. Raises ModelUnavailable / ValueError on problems."""
    meta, model = get_metadata(), get_model()
    frame = pd.DataFrame([row], columns=meta["features"])
    if frame.isna().any().any():
        raise ValueError("Input contains missing values: " + ", ".join(frame.columns[frame.isna().any()]))
    value = float(model.predict(frame)[0])
    if not math.isfinite(value):
        raise ValueError("The model returned a non-finite value.")
    return max(0.0, value)


def run_prediction(crop, state, season, year, area, rainfall, fert_rate, pest_rate) -> dict:
    row = build_input_row(crop, state, season, year, area, rainfall, fert_rate, pest_rate)
    y = predict_yield(row)
    return {
        "row": row, "yield": y, "production": y * float(area),
        "fert_rate": float(fert_rate), "pest_rate": float(pest_rate),
        "yield_unit": yield_unit(crop), "yield_unit_short": yield_unit_short(crop),
        "production_unit": production_unit(crop),
    }


# ----------------------------------------------------------------------------- reference stats
def reference_stats(crop: str, state: str, season: str) -> dict:
    """Dataset-derived context for a prediction (all numbers come from the CSV)."""
    df = get_dataset()
    out: dict[str, Any] = {}
    c = df[df.Crop == crop]
    if len(c):
        out["crop_mean"], out["crop_median"], out["crop_n"] = float(c.Yield.mean()), float(c.Yield.median()), len(c)
        out["crop_p25"], out["crop_p75"] = float(c.Yield.quantile(.25)), float(c.Yield.quantile(.75))
        out["rain_range"] = (float(c.Annual_Rainfall.min()), float(c.Annual_Rainfall.max()))
        out["rain_median"] = float(c.Annual_Rainfall.median())
        out["fert_range"] = (float(c.Fertilizer_per_ha.min()), float(c.Fertilizer_per_ha.max()))
        out["pest_range"] = (float(c.Pesticide_per_ha.min()), float(c.Pesticide_per_ha.max()))
    cs = c[c.State == state]
    if len(cs):
        out["cs_mean"], out["cs_n"] = float(cs.Yield.mean()), len(cs)
    css = cs[cs.Season == season]
    if len(css):
        out["css_mean"], out["css_n"] = float(css.Yield.mean()), len(css)
    return out


def default_inputs() -> dict:
    """Dataset-based defaults (medians) for the prediction form."""
    df = get_dataset()
    return {
        "year": int(df.Crop_Year.max()),
        "rainfall": round(float(df.Annual_Rainfall.median()), 1),
        "fert": round(float(df.Fertilizer_per_ha.median()), 1),
        "pest": round(float(df.Pesticide_per_ha.median()), 2),
    }
