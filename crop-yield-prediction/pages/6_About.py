"""About page."""
import streamlit as st

from components import cards
from components.sidebar import setup_page

meta, df = setup_page("About", "ℹ️")
cards.page_header("ℹ️", "About CropYield AI", "A beginner-friendly machine-learning project for estimating crop yield from historical Indian crop records.")

st.markdown("### What it does")
st.markdown("Enter a crop, location, season, year, area, rainfall and fertilizer/pesticide use. The app asks the trained model for a yield "
            "per hectare, multiplies by area for total production, explains the result in plain language and saves it to local history.")

st.markdown("### Pages")
st.markdown("- **Home:** dataset summary and your latest prediction\n- **Predict Yield:** validated input form and results\n"
            "- **History:** saved predictions with search, CSV export and confirmed deletion\n- **Data Insights:** charts from the real dataset\n"
            "- **Model Info:** model type, features, accuracy and limitations\n- **Recommendations:** insights from your data plus general farming guidance")

st.markdown("### Technology")
st.write("Python · Streamlit · Pandas · NumPy · scikit-learn (Extra Trees) · Joblib · SQLite · Matplotlib · custom CSS")

st.markdown("### Data privacy")
st.write("Everything runs on your computer. Prediction history is stored in a local SQLite file (`crop_yield.db`) and is never uploaded.")

st.markdown("### Responsible use")
st.markdown(f'<div class="cy-disclaimer">{cards.esc(cards.DISCLAIMER)} Consult local agricultural experts before making fertilizer, pesticide or irrigation decisions.</div>',
            unsafe_allow_html=True)

st.markdown("### Run on Windows")
st.code("run_windows.bat", language="bat")
st.caption("Or manually: `py -3 -m venv .venv`, `.venv\\Scripts\\activate`, `pip install -r requirements.txt`, `streamlit run app.py`.")
