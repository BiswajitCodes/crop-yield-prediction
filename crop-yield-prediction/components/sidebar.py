"""Common page setup: page config, CSS, branded sidebar navigation, and model/dataset checks."""
from __future__ import annotations

import streamlit as st

import config
import database
import model_service as ms
from components import cards, styles


def setup_page(title: str, icon: str = "🌱"):
    """Must be the first Streamlit call on every page. Returns (metadata, dataframe)."""
    st.set_page_config(page_title=f"{title} | CropYield AI", page_icon=icon, layout="wide",
                       initial_sidebar_state="expanded")
    st.markdown(styles.BASE_CSS, unsafe_allow_html=True)
    _sidebar()
    try:
        database.init_db()
    except Exception as exc:
        st.warning(f"Prediction history is unavailable (database error: {exc}). Predictions will still work.")
    try:
        meta = ms.get_metadata()
        ms.get_model()  # fails early with a friendly message if the model is missing/incompatible
        df = ms.get_dataset()
    except ms.ModelUnavailable as exc:
        st.error(f"The model or dataset could not be loaded.\n\n{exc}")
        st.info("Fix: keep `models/crop_yield_model.joblib`, `models/model_metadata.json` and `data/crop_yield.csv` "
                "in the project folder and install the pinned requirements. If the model is truly missing, run "
                "`python train_model.py` once (it retrains from the CSV).")
        st.stop()
    return meta, df


def _sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="cy-brand"><div class="leaf">🍃</div><div class="name">CropYield AI</div></div>',
                    unsafe_allow_html=True)
        for label, icon, path in config.PAGES:
            st.page_link(path, label=label, icon=icon)
        st.markdown('<div class="cy-side-foot">Estimates from historical Indian crop records.<br>'
                    'Not a guarantee of harvest.</div>', unsafe_allow_html=True)
