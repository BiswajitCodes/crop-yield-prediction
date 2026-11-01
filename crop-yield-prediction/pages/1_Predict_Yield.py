"""Predict Crop Yield page."""
import streamlit as st

import database
import model_service as ms
import recommendations as rec
from components import cards
from components.sidebar import setup_page

meta, df = setup_page("Predict Yield", "🌱")
cards.page_header("🌱", "Predict Crop Yield", "Enter the field details below to estimate crop yield and total production.")
defaults = ms.default_inputs()
crops, states, seasons = meta["crops"], meta["states"], meta["seasons"]

left, right = st.columns([1, 1.5], gap="large")

# ------------------------------------------------------------------ form
with left:
    with st.container(key="card_form"):
        st.markdown('<div class="cy-card-title">1. Input Field Details</div>', unsafe_allow_html=True)
        with st.form("predict_form"):
            crop = st.selectbox("Crop", crops, index=crops.index("Rice") if "Rice" in crops else 0,
                                help="Crop category exactly as recorded in the training data (55 options).")
            state = st.selectbox("State / UT", states, index=states.index("Odisha") if "Odisha" in states else 0,
                                 help="Indian state or union territory.")
            season = st.selectbox("Growing season", seasons, index=seasons.index("Kharif") if "Kharif" in seasons else 0,
                                  help="Season category from the source data.")
            year = st.number_input("Crop year", min_value=1900, max_value=2100, value=int(defaults["year"]), step=1,
                                   help="Calendar year. The model was trained on 1997-2020; later years are treated like the latest years it saw.")
            area = st.number_input("Cultivated area (hectares)", min_value=0.01, max_value=100000000.0, value=2.0, step=0.5,
                                   format="%.2f", help="Area under the crop in hectares (1 ha = 10,000 m²). Total production = yield × area.")
            rainfall = st.number_input("Annual rainfall (mm)", min_value=0.0, max_value=20000.0, value=float(defaults["rainfall"]),
                                       step=25.0, format="%.1f", help="Total rainfall for the year in millimetres. Dataset median shown by default.")
            fert = st.number_input("Fertilizer use (kg/ha)", min_value=0.0, max_value=5000.0, value=float(defaults["fert"]),
                                   step=5.0, format="%.1f",
                                   help="Fertilizer applied per hectare. The app multiplies by area because the model was trained on total kg.")
            pest = st.number_input("Pesticide use (kg/ha)", min_value=0.0, max_value=500.0, value=float(defaults["pest"]),
                                   step=0.05, format="%.2f",
                                   help="Pesticide applied per hectare. The app multiplies by area because the model was trained on total kg.")
            submitted = st.form_submit_button("🌱 Predict Crop Yield", type="primary")

if submitted:
    errors, warns = ms.validate_inputs(crop, state, season, year, area, rainfall, fert, pest)
    if errors:
        with right:
            for e in errors:
                st.error(e)
    else:
        try:
            result = ms.run_prediction(crop, state, season, year, area, rainfall, fert, pest)
            result["warnings"] = warns
            result["stats"] = ms.reference_stats(crop, state, season)
            try:
                result["saved_id"] = database.save_prediction({
                    **result["row"], "predicted_yield": result["yield"], "production": result["production"],
                    "fertilizer_rate": result["fert_rate"], "pesticide_rate": result["pest_rate"],
                    "yield_unit": result["yield_unit"], "production_unit": result["production_unit"]})
                result["save_error"] = None
            except Exception as exc:
                result["saved_id"], result["save_error"] = None, str(exc)
            st.session_state["last_result"] = result
        except ms.ModelUnavailable as exc:
            with right:
                st.error(f"The model is unavailable: {exc}")
        except Exception as exc:
            with right:
                st.error(f"Prediction failed: {exc}")

# ------------------------------------------------------------------ results
with right:
    with st.container(key="card_results"):
        st.markdown('<div class="cy-card-title">2. Prediction Results</div>', unsafe_allow_html=True)
        res = st.session_state.get("last_result")
        if not res or "stats" not in res:
            st.markdown('<div class="cy-box">Fill in the field details and press <b>Predict Crop Yield</b>. '
                        'The estimate, input summary and calculation will appear here.</div>', unsafe_allow_html=True)
        else:
            row, y, total = res["row"], res["yield"], res["production"]
            m1, m2 = st.columns(2)
            with m1:
                st.markdown(cards.metric_card("Estimated Yield", f"{y:,.3f}", res["yield_unit"]), unsafe_allow_html=True)
            with m2:
                st.markdown(cards.metric_card("Total Production", f"{total:,.3f}", res["production_unit"],
                                              f"for {row['Area']:,.2f} hectares"), unsafe_allow_html=True)
            st.write("")
            s1, s2 = st.columns(2)
            with s1:
                summary = [("Crop", row["Crop"]), ("State / UT", row["State"]), ("Season", row["Season"]),
                           ("Year", str(row["Crop_Year"])), ("Area (ha)", f"{row['Area']:,.2f}"),
                           ("Rainfall (mm)", f"{row['Annual_Rainfall']:,.1f}"),
                           ("Fertilizer (kg/ha)", f"{res['fert_rate']:,.1f}"),
                           ("Pesticide (kg/ha)", f"{res['pest_rate']:,.2f}")]
                st.markdown(f'<div class="cy-box"><h4>Input Summary</h4>{cards.kv_table(summary)}</div>', unsafe_allow_html=True)
            with s2:
                st.markdown(
                    '<div class="cy-box"><h4>Calculation</h4>'
                    f'<div class="cy-calc"><div class="k">Predicted yield (model output)</div><div class="v">{y:,.3f} {cards.esc(res["yield_unit_short"])}</div></div>'
                    f'<div class="cy-calc"><div class="k">Cultivated area</div><div class="v">{row["Area"]:,.2f} ha</div></div>'
                    f'<div class="cy-calc"><div class="k">Total production = yield × area</div><div class="v">{y:,.3f} × {row["Area"]:,.2f} = {total:,.3f} {cards.esc(res["production_unit"])}</div></div>'
                    f'<div class="cy-calc"><div class="k">Values sent to the model</div><div class="v" style="font-size:.8rem">Fertilizer {row["Fertilizer"]:,.1f} kg · Pesticide {row["Pesticide"]:,.2f} kg (rate × area)</div></div>'
                    '</div>', unsafe_allow_html=True)

            # plain-language interpretation
            stats = res["stats"]
            ref = stats.get("cs_mean") or stats.get("crop_mean")
            ref_name = f"{row['Crop']} in {row['State']}" if stats.get("cs_mean") else f"{row['Crop']} across India"
            text = (f"For **{row['Crop']}** in **{row['State']}** ({row['Season']}, {row['Crop_Year']}), the model estimates about "
                    f"**{y:,.2f} {res['yield_unit']}**.")
            if ref:
                d = (y - ref) / ref * 100 if ref else 0
                rel = "about the same as" if abs(d) < 10 else (f"about {abs(d):.0f}% above" if d > 0 else f"about {abs(d):.0f}% below")
                text += f" That is {rel} the dataset average for {ref_name} ({ref:,.2f})."
            text += f" On {row['Area']:,.2f} ha this would be roughly **{total:,.2f} {res['production_unit']}** in total."
            st.markdown("#### What this means")
            st.markdown(text)

            if res.get("save_error"):
                st.warning(f"The prediction could not be saved to history: {res['save_error']}")
            else:
                st.caption("✅ Saved to local prediction history.")
            for w in res.get("warnings", []):
                st.markdown(cards.warning_box(w), unsafe_allow_html=True)

            st.markdown("#### Key insights from the dataset")
            st.markdown(f'<div class="cy-insights">{cards.check_list(rec.key_insights(res, stats))}</div>', unsafe_allow_html=True)
            c_a, c_b = st.columns(2)
            with c_a:
                if st.button("💡 See recommendations", key="to_recs"):
                    st.switch_page("pages/2_Recommendations.py")
            with c_b:
                if st.button("🕘 Open history", key="to_hist"):
                    st.switch_page("pages/4_Prediction_History.py")
            st.markdown(f'<div class="cy-disclaimer">{cards.esc(cards.DISCLAIMER)}</div>', unsafe_allow_html=True)
