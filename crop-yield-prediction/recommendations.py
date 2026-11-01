"""Recommendations. Each item is tagged:
  'data'    -> derived from the dataset / model output for THIS prediction
  'general' -> widely-used agronomy guidance that the model does NOT support or verify
No fertilizer or pesticide product/dose prescriptions are produced.
"""
from __future__ import annotations

import model_service as ms

DATA, GENERAL = "data", "general"


def key_insights(result: dict, stats: dict) -> list[str]:
    """Model/dataset-derived statements about a prediction."""
    row, y, u = result["row"], result["yield"], result["yield_unit_short"]
    crop, state, season = row["Crop"], row["State"], row["Season"]
    out: list[str] = []
    ref = stats.get("cs_mean") or stats.get("crop_mean")
    ref_name = f"{crop} in {state}" if stats.get("cs_mean") else f"{crop} across India"
    if ref:
        diff = (y - ref) / ref * 100 if ref else 0
        if abs(diff) < 10:
            out.append(f"The predicted yield ({y:,.2f} {u}) is close to the dataset average for {ref_name} ({ref:,.2f} {u}).")
        else:
            way = "above" if diff > 0 else "below"
            out.append(f"The predicted yield ({y:,.2f} {u}) is about {abs(diff):.0f}% {way} the dataset average for {ref_name} ({ref:,.2f} {u}).")
    if "crop_p25" in stats:
        pos = "within" if stats["crop_p25"] <= y <= stats["crop_p75"] else "outside"
        out.append(f"It is {pos} the typical middle half of recorded {crop} yields "
                   f"({stats['crop_p25']:,.2f}-{stats['crop_p75']:,.2f} {u}).")
    if "rain_range" in stats:
        lo, hi = stats["rain_range"]
        r = row["Annual_Rainfall"]
        out.append(f"Rainfall ({r:,.0f} mm) is {'within' if lo <= r <= hi else 'outside'} the {lo:,.0f}-{hi:,.0f} mm "
                   f"range recorded for {crop}; the typical value is {stats['rain_median']:,.0f} mm.")
    if "fert_range" in stats:
        lo, hi = stats["fert_range"]
        f = result["fert_rate"]
        out.append(f"Fertilizer ({f:,.1f} kg/ha) is {'within' if lo <= f <= hi else 'outside'} the range in the data "
                   f"({lo:,.0f}-{hi:,.0f} kg/ha). This says nothing about whether it is agronomically optimal.")
    if "css_n" not in stats:
        out.append(f"The dataset has no {crop} records for {state} in the {season} season, so this estimate is less well supported.")
    return out


def grouped_recommendations(result: dict | None = None, stats: dict | None = None) -> dict[str, list[tuple[str, str]]]:
    """Three groups of (tag, text). With a result, a few data-derived items are added."""
    soil_water = [
        (GENERAL, "Test your soil (pH, organic matter, nutrients) before deciding on any nutrient programme."),
        (GENERAL, "Prepare land well and sow on time for your region and season; late sowing commonly reduces yield."),
        (GENERAL, "Match irrigation to crop stage and rainfall; make sure fields drain so roots do not sit in water."),
        (GENERAL, "Mulching, residue retention and organic matter help soils hold moisture and nutrients."),
    ]
    inputs = [
        (GENERAL, "Base fertilizer decisions on a soil test and local extension recommendations, not on this model."),
        (GENERAL, "Prefer balanced nutrition (N, P, K and secondary nutrients) over repeated single-nutrient applications."),
        (GENERAL, "Use integrated pest management: scout fields regularly and treat only when thresholds are reached."),
        (GENERAL, "Always follow the product label and local regulations when handling agrochemicals."),
    ]
    crop_mgmt = [
        (GENERAL, "Use certified, locally adapted seed and recommended spacing for the crop and season."),
        (GENERAL, "Monitor for pests and diseases weekly during critical growth stages."),
        (GENERAL, "Rotate crops where practical to reduce disease build-up and improve soil health."),
        (GENERAL, "Plan harvest timing and post-harvest handling to avoid avoidable losses."),
    ]
    if result and stats:
        row = result["row"]
        if "rain_range" in stats:
            lo, hi = stats["rain_range"]
            r = row["Annual_Rainfall"]
            if r < lo or r < stats["rain_median"] * 0.6:
                soil_water.insert(0, (DATA, f"Rainfall ({r:,.0f} mm) is low compared with the typical {stats['rain_median']:,.0f} mm "
                                            f"recorded for {row['Crop']}; check irrigation availability."))
            elif r > hi or r > stats["rain_median"] * 1.6:
                soil_water.insert(0, (DATA, f"Rainfall ({r:,.0f} mm) is high compared with the typical {stats['rain_median']:,.0f} mm "
                                            f"recorded for {row['Crop']}; check drainage and waterlogging risk."))
            else:
                soil_water.insert(0, (DATA, f"Rainfall ({r:,.0f} mm) is within the range recorded for {row['Crop']} "
                                            f"({lo:,.0f}-{hi:,.0f} mm)."))
        if "fert_range" in stats:
            lo, hi = stats["fert_range"]
            f = result["fert_rate"]
            msg = ("within" if lo <= f <= hi else "outside")
            inputs.insert(0, (DATA, f"Your fertilizer rate ({f:,.1f} kg/ha) is {msg} the {lo:,.0f}-{hi:,.0f} kg/ha range seen for "
                                    f"{row['Crop']} in the data; predictions outside that range are less reliable."))
        if "css_mean" in stats:
            crop_mgmt.insert(0, (DATA, f"Recorded {row['Crop']} yields for {row['State']} in the {row['Season']} season average "
                                       f"{stats['css_mean']:,.2f} {result['yield_unit_short']} ({stats['css_n']} records)."))
    return {"Soil and water management": soil_water, "Input management": inputs, "Crop management": crop_mgmt}


CONSIDERATIONS = [
    "Actual yield varies with soil type, weather extremes, seed variety, pests and farm management, none of which are model inputs.",
    "This is a machine-learning estimate from historical state/district-level records, not a guaranteed harvest.",
    "For precise recommendations, consult your local agricultural extension service or Krishi Vigyan Kendra.",
    "Soil testing and crop advisory services give field-specific guidance that this app cannot.",
]
