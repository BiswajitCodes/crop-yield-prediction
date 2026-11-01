"""Recommendations page."""
import streamlit as st

import model_service as ms
import recommendations as rec
from components import cards
from components.sidebar import setup_page
from components.state import latest_result

meta, df = setup_page("Recommendations", "💡")
cards.page_header("💡", "Recommendations",
                  "Suggestions to support productivity. Items are labelled as coming from your data or as general guidance.")

res = latest_result()
stats = None
if res:
    row = res["row"]
    stats = ms.reference_stats(row["Crop"], row["State"], row["Season"])
    st.markdown(f"Based on your latest prediction: **{cards.esc(row['Crop'])}**, {cards.esc(row['State'])}, {cards.esc(row['Season'])} "
                f"{row['Crop_Year']} → **{res['yield']:,.2f} {res['yield_unit_short']}**.")
    st.markdown("### ✅ Key Insights (derived from the dataset and model output)")
    st.markdown(f'<div class="cy-insights">{cards.check_list(rec.key_insights(res, stats))}</div>', unsafe_allow_html=True)
else:
    st.info("No prediction available yet, so only general guidance is shown. Make a prediction to see insights tailored to your inputs.")
    if st.button("🌱 Go to Predict Yield", key="recs_to_predict"):
        st.switch_page("pages/1_Predict_Yield.py")

st.write("")
groups = rec.grouped_recommendations(res, stats)
cols = st.columns(len(groups))
for col, (title, items) in zip(cols, groups.items()):
    with col:
        st.markdown(f'<div class="cy-box"><h4>{cards.esc(title)}</h4>{cards.tagged_list(items)}</div>', unsafe_allow_html=True)

st.write("")
st.markdown(f'<div class="cy-consider"><h4 style="margin:0 0 .4rem 0">⚠️ Considerations</h4>{cards.check_list(rec.CONSIDERATIONS)}</div>',
            unsafe_allow_html=True)
st.caption("**FROM YOUR DATA** = computed from the dataset or the model output for your prediction. "
           "**GENERAL GUIDANCE** = widely-used agronomy advice the model does not verify. "
           "This app does not give fertilizer or pesticide product or dose prescriptions.")
