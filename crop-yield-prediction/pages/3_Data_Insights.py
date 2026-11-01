"""Data Insights page: functional charts built from the real dataset."""
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import config
import model_service as ms
from components import cards, charts
from components.sidebar import setup_page

meta, df = setup_page("Data Insights", "📊")
cards.page_header("📊", "Data Insights", "Explore the dataset to understand crop yield patterns. Charts describe past records, not cause and effect.")


def show(fig) -> None:
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def pick_n(label: str, total: int, default: int, key: str) -> int:
    """Slider for 'how many to show'; avoids Streamlit's min==max slider error on tiny selections."""
    if total <= 3:
        return total
    top = min(30, total)
    return st.slider(label, 3, top, min(default, top), key=key)


def need(n: int, minimum: int = 3) -> bool:
    if n < minimum:
        st.info(f"Not enough data for this chart with the current filters ({n} record(s); at least {minimum} needed). Try widening the filters.")
        return False
    return True


# ------------------------------------------------------------------ filters
with st.container(key="card_filters"):
    f1, f2, f3, f4 = st.columns([1.2, 1.5, 1.3, 1.5])
    crops = sorted(df.Crop.unique())
    crop = f1.selectbox("Crop (for state, season, rainfall, fertilizer, trend and distribution charts)", crops,
                        index=crops.index("Rice") if "Rice" in crops else 0)
    sel_states = f2.multiselect("State / UT (empty = all)", sorted(df.State.unique()))
    sel_seasons = f3.multiselect("Season (empty = all)", sorted(df.Season.unique()))
    y0, y1 = int(df.Crop_Year.min()), int(df.Crop_Year.max())
    years = f4.slider("Year range", y0, y1, (y0, y1))

base = df[df.Crop_Year.between(years[0], years[1])]
if sel_states:
    base = base[base.State.isin(sel_states)]
if sel_seasons:
    base = base[base.Season.isin(sel_seasons)]
sub = base[base.Crop == crop]
unit_short = ms.yield_unit_short(crop)
ylabel = f"Yield ({unit_short})"
st.caption(f"{len(base):,} records match the filters; {len(sub):,} are {crop} records.")

tabs = st.tabs(["Yield by Crop", "Yield by State", "Yield by Season", "Rainfall vs Yield", "Fertilizer vs Yield", "Yield Trend", "Dataset Overview"])

# ------------------------------------------------------------------ 1 crops
with tabs[0]:
    tonne_crops = [c for c in base.Crop.unique() if ms.yield_unit(c) == "tonnes per hectare"]
    other_crops = sorted(set(base.Crop.unique()) - set(tonne_crops))
    avg = base[base.Crop.isin(tonne_crops)].groupby("Crop").Yield.mean().sort_values(ascending=False)
    left, right = st.columns(2)
    with left:
        if need(len(avg), 1):
            top_n = pick_n("How many crops to show", len(avg), 10, "topn")
            show(charts.bar_by_category(avg.head(top_n), "Average yield by crop", "Yield (tonnes/ha)", horizontal=True))
    with right:
        if need(len(sub), 5):
            show(charts.histogram(sub.Yield, f"Distribution of yield ({crop})", ylabel))
    if other_crops:
        st.caption("Not in the left chart because their yield is not in tonnes/ha in the source data: "
                   + ", ".join(f"{c} ({ms.yield_unit_short(c)})" for c in other_crops) + ". Averages are unweighted means of recorded yields.")

# ------------------------------------------------------------------ 2 states
with tabs[1]:
    if need(len(sub), 1):
        by_state = sub.groupby("State").Yield.agg(["mean", "count"]).sort_values("mean", ascending=False)
        n = pick_n("How many states to show", len(by_state), 15, "topstate")
        show(charts.bar_by_category(by_state["mean"].head(n), f"Average {crop} yield by state", ylabel, horizontal=True))
        st.caption("Records per state: " + ", ".join(f"{s} ({int(c)})" for s, c in by_state["count"].head(n).items()))

# ------------------------------------------------------------------ 3 seasons
with tabs[2]:
    groups = {s: g.Yield for s, g in sub.groupby("Season") if len(g) >= 1}
    if groups and need(len(sub), 3):
        show(charts.boxplot(groups, f"{crop} yield by growing season", ylabel))
        st.caption("Box = middle 50% of records, line = median. Many crops are only grown in one or two seasons.")

# ------------------------------------------------------------------ 4 rainfall
with tabs[3]:
    d = sub.dropna(subset=["Annual_Rainfall", "Yield"])
    if need(len(d), 10):
        show(charts.scatter(d.Annual_Rainfall, d.Yield, f"Rainfall vs {crop} yield", "Annual rainfall (mm)", ylabel))
        r = charts.spearman(d.Annual_Rainfall, d.Yield)
        if r is not None:
            st.caption(f"Rank correlation: {r:+.2f} (−1 to +1; near 0 = no consistent relationship). Correlation does not prove rainfall causes yield changes.")

# ------------------------------------------------------------------ 5 fertilizer
with tabs[4]:
    d = sub.dropna(subset=["Fertilizer_per_ha", "Yield"])
    if need(len(d), 10):
        show(charts.scatter(d.Fertilizer_per_ha, d.Yield, f"Fertilizer vs {crop} yield", "Fertilizer (kg/ha = total ÷ area)", ylabel))
        r = charts.spearman(d.Fertilizer_per_ha, d.Yield)
        lo, hi = df.Fertilizer_per_ha.min(), df.Fertilizer_per_ha.max()
        st.caption((f"Rank correlation: {r:+.2f}. " if r is not None else "")
                   + f"Per-hectare fertilizer in this dataset only spans {lo:,.0f}-{hi:,.0f} kg/ha, so it cannot reveal how yield responds to very low or very high application.")

# ------------------------------------------------------------------ 6 trend
with tabs[5]:
    t = sub.groupby("Crop_Year").Yield.mean()
    if need(len(t), 2):
        show(charts.line(t.index.astype(int), t.values, f"Average {crop} yield by year", "Year", ylabel))
        st.caption("Each point is the mean of recorded yields for that year after applying the filters; the set of states in each year can differ.")

# ------------------------------------------------------------------ 7 overview
with tabs[6]:
    st.markdown("#### Filtered data")
    if len(sub):
        show_cols = ["Crop", "State", "Season", "Crop_Year", "Area", "Annual_Rainfall", "Fertilizer_per_ha", "Pesticide_per_ha", "Yield"]
        st.dataframe(sub[show_cols].head(500), use_container_width=True, hide_index=True)
        st.download_button("⬇ Download filtered data (CSV)", sub[show_cols].to_csv(index=False).encode("utf-8"),
                           file_name=f"cropyield_{crop.replace('/', '-')}_filtered.csv", mime="text/csv")
        st.markdown("#### Summary statistics")
        st.dataframe(sub[["Area", "Annual_Rainfall", "Fertilizer_per_ha", "Pesticide_per_ha", "Yield"]].describe().T.round(3),
                     use_container_width=True)
    else:
        st.info("No records match the current filters.")

st.markdown("### Dataset Summary")
k = st.columns(5)
items = [("🗄️", f"{len(df):,}", "Crop Records"), ("🌿", df.Crop.nunique(), "Crops"), ("📍", df.State.nunique(), "States / UTs"),
         ("📅", f"{y0}-{y1}", "Years"), ("⚙️", len(meta["features"]), "Model Features")]
for col, (ico, val, lab) in zip(k, items):
    with col:
        st.markdown(cards.stat_card(ico, val, lab), unsafe_allow_html=True)
