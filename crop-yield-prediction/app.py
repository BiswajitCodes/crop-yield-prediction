"""CropYield AI - Home dashboard (main Streamlit script)."""
import streamlit as st

import config
import model_service as ms
from components import cards, styles
from components.sidebar import setup_page
from components.state import latest_result

meta, df = setup_page("Home", "🌱")
st.markdown(styles.hero_css(cards.banner_b64()), unsafe_allow_html=True)

# ------------------------------------------------------------------ hero
with st.container(key="hero"):
    st.markdown('<h1 class="hero-title">CropYield AI</h1><div class="hero-sub">Smart Agriculture for a Better Tomorrow</div>'
                '<p class="hero-text">Predict crop yield and total production using machine learning trained on historical '
                'Indian crop records. Get insights and recommendations to support data-driven farming decisions.</p>',
                unsafe_allow_html=True)
    b1, b2, _ = st.columns([1.3, 1, 3])
    with b1:
        if st.button("🌱 Make a Prediction", type="primary", key="home_predict"):
            st.switch_page("pages/1_Predict_Yield.py")
    with b2:
        if st.button("Learn More", key="home_learn"):
            st.switch_page("pages/6_About.py")

# ------------------------------------------------------------------ dataset summary cards (all from the CSV)
c1, c2, c3, c4 = st.columns(4)
yrs = sorted(df.Crop_Year.dropna().astype(int).unique())
with c1:
    st.markdown(cards.stat_card("🌿", df.Crop.nunique(), "Crops Supported", "Distinct crops in the dataset"), unsafe_allow_html=True)
with c2:
    st.markdown(cards.stat_card("📍", df.State.nunique(), "States & UTs", "Across India"), unsafe_allow_html=True)
with c3:
    st.markdown(cards.stat_card("📈", df.Season.nunique(), "Seasons", ", ".join(sorted(df.Season.unique()))), unsafe_allow_html=True)
with c4:
    st.markdown(cards.stat_card("🗄️", len(yrs), "Years of Data", f"{yrs[0]}-{yrs[-1]} · {len(df):,} records"), unsafe_allow_html=True)

# ------------------------------------------------------------------ crop gallery
st.markdown("### Supported Crops")
cols = st.columns(len(config.GALLERY))
for col, (label, crop_name, stem) in zip(cols, config.GALLERY):
    with col:
        st.markdown(f'<div class="cy-crop">{cards.crop_image_tag(stem)}<div>{cards.esc(label)}</div></div>', unsafe_allow_html=True)
with st.expander(f"See all {len(meta['crops'])} crops the model supports"):
    st.write(", ".join(meta["crops"]))

# ------------------------------------------------------------------ latest prediction
st.markdown("### Latest Prediction")
res = latest_result()
if res:
    row = res["row"]
    rain_txt = "{:,.1f} mm".format(row["Annual_Rainfall"])
    details = cards.kv_table([("Season", row["Season"]), ("Crop year", str(row["Crop_Year"])), ("Rainfall", rain_txt)])
    a, b, c = st.columns([1.2, 1.2, 2])
    with a:
        st.markdown(cards.metric_card("Estimated yield", f"{res['yield']:,.3f}", res["yield_unit"]), unsafe_allow_html=True)
    with b:
        st.markdown(cards.metric_card("Total production", f"{res['production']:,.3f}", res["production_unit"],
                                      f"for {row['Area']:,.2f} ha"), unsafe_allow_html=True)
    with c:
        title = cards.esc(row["Crop"]) + " · " + cards.esc(row["State"])
        st.markdown(f'<div class="cy-box"><h4>{title}</h4>{details}</div>', unsafe_allow_html=True)
else:
    st.info("No prediction yet. Press **Make a Prediction** to create your first estimate.")

st.markdown(f'<div class="cy-disclaimer">{cards.esc(cards.DISCLAIMER)}</div>', unsafe_allow_html=True)
