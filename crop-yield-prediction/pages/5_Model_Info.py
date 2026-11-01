"""Model Information page. Every number comes from model_metadata.json, model_diagnostics.json, the model object or the CSV."""
import pandas as pd
import streamlit as st

import config
import model_service as ms
from components import cards
from components.sidebar import setup_page

meta, df = setup_page("Model Info", "🧠")
cards.page_header("🧠", "Model Information", "How the prediction model was built, what it uses, and how far to trust it.")
model = ms.get_model()
diag = ms.get_diagnostics()
m = meta.get("metrics", {})

for w in ms.version_warnings():
    st.warning(f"Library version notice while loading the model: {w}")

# ------------------------------------------------------------------ overview
est = model.named_steps.get("model") if hasattr(model, "named_steps") else None
n_trees = getattr(est, "n_estimators", None)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(cards.stat_card("🌳", meta.get("model_name", "Model"), "Model type", "Extra Trees regression" + (f" · {n_trees} trees" if n_trees else "")), unsafe_allow_html=True)
with c2:
    st.markdown(cards.stat_card("🧪", f"{meta.get('train_rows', 0):,}", "Training rows", "random 80% split"), unsafe_allow_html=True)
with c3:
    st.markdown(cards.stat_card("✅", f"{meta.get('test_rows', 0):,}", "Test rows", "random 20% hold-out"), unsafe_allow_html=True)
with c4:
    st.markdown(cards.stat_card("⚙️", len(meta["features"]), "Input features", "Production is not an input"), unsafe_allow_html=True)

st.markdown("### How it was trained")
st.markdown(
    "1. **Load and clean** the historical crop CSV (trim text, drop rows without a yield, remove duplicates).\n"
    "2. **Split** randomly into 80% training and 20% test rows (`random_state=42`).\n"
    "3. **Prepare inputs:** numbers use median-filling; categories (crop, state, season) use most-frequent-filling then one-hot encoding.\n"
    "4. **Compare** Random Forest and Extra Trees; the one with the lowest RMSE on the test rows was saved.\n"
    "5. **Predict** yield per hectare. The app then multiplies by area to get total production.")

st.markdown("### Input features and units")
rows = []
for f in meta["features"]:
    label, unit, helptxt = config.FEATURE_INFO.get(f, (f, "", ""))
    kind = "number" if f in meta["numeric_features"] else "category"
    rows.append({"Feature (in model)": f, "Meaning": label, "Type": kind, "Unit": unit, "Notes": helptxt})
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
st.caption("Target = Yield (tonnes per hectare for most crops; nuts/ha for Coconut and bales/ha for Cotton, Jute and Mesta per the source's conventions).")

st.markdown("### Dataset coverage")
d1, d2, d3, d4 = st.columns(4)
d1.metric("Records", f"{len(df):,}")
d2.metric("Crops", df.Crop.nunique())
d3.metric("States / UTs", df.State.nunique())
d4.metric("Years", f"{int(df.Crop_Year.min())}-{int(df.Crop_Year.max())}")
st.caption("Source: the India crop-yield CSV bundled in `data/crop_yield.csv` (a Kaggle-style dataset referenced by `train_model.py`; "
           "its original source link is not stored in this project). Records are state-level yearly figures, not individual farms.")

# ------------------------------------------------------------------ metrics
st.markdown("### Accuracy on held-out test rows")
a, b, c = st.columns(3)
a.metric("MAE", f"{m.get('MAE', float('nan')):.3f}")
b.metric("RMSE", f"{m.get('RMSE', float('nan')):.3f}")
c.metric("R²", f"{m.get('R2', float('nan')):.4f}")
st.markdown(
    "- **MAE** (mean absolute error): on average the prediction is off by this many yield units.\n"
    "- **RMSE** (root mean squared error): like MAE but punishes big misses more; a large RMSE next to a small MAE means a few rows are badly off.\n"
    "- **R²**: share of the variation in yield the model explains (1.0 = perfect, 0 = no better than guessing the average).")
if diag:
    ex = diag["excluding_coconut"]
    st.warning(
        f"**Read these headline numbers with care.** Coconut yields are in nuts per hectare (around 8,600) while most crops are a few tonnes, "
        f"so coconut dominates MAE, RMSE and R². Re-evaluating the saved model on the same test rows **without coconut** gives "
        f"MAE {ex['MAE']:.3f}, RMSE {ex['RMSE']:.3f} and R² {ex['R2']:.3f} ({ex['n']:,} rows). That is a fairer picture for typical crops.")
    pc = pd.DataFrame(diag["per_crop"]).T.reset_index().rename(columns={"index": "Crop", "MAE": "Mean abs. error", "n": "Test rows", "mean_actual": "Mean actual yield"})
    pc["Crop unit"] = pc["Crop"].map(ms.yield_unit_short)
    st.markdown("#### Error by crop (test rows)")
    st.dataframe(pc.sort_values("Mean abs. error").round(3), use_container_width=True, hide_index=True)
    st.caption(diag.get("note", ""))
else:
    st.info("Per-crop diagnostics are not available. Run `python evaluate_model.py` to generate them from the saved model.")

st.markdown("### Limitations and responsible use")
st.markdown(
    "- **Random split:** the same state, crop and neighbouring years appear in both training and test rows, so these scores are likely optimistic for future years or unseen regions.\n"
    "- **Fertilizer and pesticide:** the dataset's per-hectare values sit in narrow bands "
    f"({df.Fertilizer_per_ha.min():,.0f}-{df.Fertilizer_per_ha.max():,.0f} kg/ha and {df.Pesticide_per_ha.min():,.2f}-{df.Pesticide_per_ha.max():,.2f} kg/ha), "
    "so the model cannot learn how yield truly responds to input changes. Do not use it to choose application rates.\n"
    "- **Area:** records are state/district totals (smallest record: "
    f"{df.Area.min():,.1f} ha), so predictions for a single small field are extrapolation.\n"
    f"- **Years:** trained on {int(df.Crop_Year.min())}-{int(df.Crop_Year.max())}; future years are treated like the latest year.\n"
    "- **Missing factors:** soil, temperature, irrigation, seed variety, pests and management are not inputs.\n"
    "- **Mixed units:** yield units differ by crop; compare crops only when their units match.\n"
    "- Treat every output as an estimate to inform planning, never as a guaranteed harvest.")
