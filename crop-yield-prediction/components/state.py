"""Helpers to find the most recent prediction (this session first, else the latest saved record)."""
from __future__ import annotations

import streamlit as st

import database
import model_service as ms


def record_to_result(rec: dict) -> dict:
    area = float(rec["area"])
    row = {"Crop": rec["crop"], "Season": rec["season"], "State": rec["state"], "Crop_Year": int(rec["crop_year"]),
           "Area": area, "Annual_Rainfall": float(rec["annual_rainfall"]),
           "Fertilizer": float(rec["fertilizer"]), "Pesticide": float(rec["pesticide"])}
    y = float(rec["predicted_yield"])
    return {
        "row": row, "yield": y, "production": float(rec.get("production") or y * area),
        "fert_rate": float(rec.get("fertilizer_rate") or rec["fertilizer"] / area),
        "pest_rate": float(rec.get("pesticide_rate") or rec["pesticide"] / area),
        "yield_unit": ms.yield_unit(rec["crop"]), "yield_unit_short": ms.yield_unit_short(rec["crop"]),
        "production_unit": ms.production_unit(rec["crop"]), "created_at": rec.get("created_at"),
    }


def latest_result() -> dict | None:
    res = st.session_state.get("last_result")
    if res:
        return res
    try:
        recs = database.get_predictions(limit=1)
    except Exception:
        return None
    return record_to_result(recs[0]) if recs else None
