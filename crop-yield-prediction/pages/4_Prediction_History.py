"""Prediction History page: SQLite-backed search, filter, export and confirmed deletion."""
from datetime import date

import pandas as pd
import streamlit as st

import database
from components import cards
from components.sidebar import setup_page
import model_service as ms

meta, df = setup_page("History", "🕘")
cards.page_header("🕘", "Prediction History", "Predictions saved on this computer. Search, filter, export or delete them.")

if "hist_ver" not in st.session_state:
    st.session_state["hist_ver"] = 0
if st.session_state.get("hist_msg"):
    st.success(st.session_state.pop("hist_msg"))

try:
    records = database.get_predictions(limit=100000)
except Exception as exc:
    st.error(f"Could not read the history database: {exc}")
    st.stop()

if not records:
    st.info("No predictions saved yet. Make a prediction on the **Predict Yield** page and it will appear here.")
    if st.button("🌱 Go to Predict Yield", key="hist_to_predict"):
        st.switch_page("pages/1_Predict_Yield.py")
    st.stop()

hist = pd.DataFrame(records)
hist["created_dt"] = pd.to_datetime(hist["created_at"], errors="coerce")

# ------------------------------------------------------------------ filters
with st.container(key="card_hist_filters"):
    c1, c2, c3, c4 = st.columns([1.6, 1.3, 1.3, 1.6])
    search = c1.text_input("Search (crop, state or season)", placeholder="e.g. Rice or Odisha")
    crops_sel = c2.multiselect("Crop", sorted(hist["crop"].unique()))
    seasons_sel = c3.multiselect("Season", sorted(hist["season"].unique()))
    dmin, dmax = hist["created_dt"].min().date(), hist["created_dt"].max().date()
    date_sel = c4.date_input("Date range", value=(dmin, dmax), min_value=dmin, max_value=dmax)

view = hist
if search.strip():
    s = search.strip().lower()
    view = view[view[["crop", "state", "season"]].astype(str).apply(lambda col: col.str.lower().str.contains(s, regex=False)).any(axis=1)]
if crops_sel:
    view = view[view["crop"].isin(crops_sel)]
if seasons_sel:
    view = view[view["season"].isin(seasons_sel)]
if isinstance(date_sel, (tuple, list)) and len(date_sel) == 2:
    view = view[view["created_dt"].dt.date.between(date_sel[0], date_sel[1])]

# ------------------------------------------------------------------ display table
def unit_of(crop):
    return ms.yield_unit_short(crop)

display = pd.DataFrame({
    "Delete": False,
    "ID": view["id"],
    "Date / time": view["created_at"],
    "Crop": view["crop"],
    "State / UT": view["state"],
    "Season": view["season"],
    "Year": view["crop_year"],
    "Area (ha)": view["area"].round(2),
    "Rainfall (mm)": view["annual_rainfall"].round(1),
    "Fertilizer (kg/ha)": view["fertilizer_rate"].round(1),
    "Pesticide (kg/ha)": view["pesticide_rate"].round(3),
    "Yield": view["predicted_yield"].round(3),
    "Yield unit": view["crop"].map(unit_of),
    "Production": view["production"].round(3),
    "Production unit": view["crop"].map(ms.production_unit),
}).reset_index(drop=True)

st.caption(f"Showing {len(display):,} of {len(hist):,} saved predictions. Tick **Delete** on rows you want to remove.")
if display.empty:
    st.info("No saved predictions match these filters.")
    st.stop()

key = f"hist_editor_{st.session_state['hist_ver']}_{abs(hash((search, tuple(crops_sel), tuple(seasons_sel), str(date_sel))))}"
edited = st.data_editor(
    display, key=key, hide_index=True, use_container_width=True,
    disabled=[c for c in display.columns if c != "Delete"],
    column_config={"Delete": st.column_config.CheckboxColumn("Delete", help="Tick to select this record for deletion")},
)

# ------------------------------------------------------------------ export
export = display.drop(columns=["Delete"])
st.download_button("⬇ Export shown rows to CSV", export.to_csv(index=False).encode("utf-8"),
                   file_name=f"cropyield_history_{date.today().isoformat()}.csv", mime="text/csv")

# ------------------------------------------------------------------ safe deletion
st.markdown("#### Delete records")
selected_ids = [int(i) for i in edited.loc[edited["Delete"], "ID"].tolist()]
d1, d2 = st.columns(2)
with d1:
    st.markdown(f"**Selected rows:** {len(selected_ids)}")
    ok_sel = st.checkbox("Yes, permanently delete the selected rows", key=f"ok_sel_{st.session_state['hist_ver']}")
    if st.button("🗑 Delete selected", key="btn_del_sel", disabled=not (ok_sel and selected_ids)):
        try:
            n = database.delete_predictions(selected_ids)
        except Exception as exc:
            n = None
            st.error(f"Could not delete: {exc}")
        if n is not None:
            st.session_state["hist_ver"] += 1
            last = st.session_state.get("last_result") or {}
            if last.get("saved_id") in selected_ids:
                st.session_state.pop("last_result", None)
            st.session_state["hist_msg"] = f"Deleted {n} record(s)."
            st.rerun()
with d2:
    st.markdown(f"**All saved rows:** {len(hist):,}")
    ok_all = st.checkbox("I understand this deletes ALL history and cannot be undone", key=f"ok_all_{st.session_state['hist_ver']}")
    if st.button("🗑 Delete all history", key="btn_del_all", disabled=not ok_all):
        try:
            n = database.clear_predictions()
        except Exception as exc:
            n = None
            st.error(f"Could not delete: {exc}")
        if n is not None:
            st.session_state["hist_ver"] += 1
            st.session_state.pop("last_result", None)
            st.session_state["hist_msg"] = f"Deleted all {n} record(s)."
            st.rerun()
