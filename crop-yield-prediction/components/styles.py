"""Global CSS. Colours are set explicitly on labels/inputs/buttons so nothing becomes unreadable."""
BASE_CSS = """
<style>
html, body, [data-testid="stAppViewContainer"] { background:#f4f8f5; }
[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:1.4rem; padding-bottom:2.5rem; max-width:1280px; }
h1,h2,h3,h4 { color:#12352a; letter-spacing:-.01em; }
p, li, label, [data-testid="stMarkdownContainer"] { color:#1f3b31; }

/* ---------- sidebar ---------- */
[data-testid="stSidebarNav"] { display:none !important; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0b3d2e 0%,#07281f 100%); min-width:236px; }
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarUserContent"] { padding-top:1rem; }
.cy-brand { display:flex; align-items:center; gap:.6rem; margin:.2rem 0 1.2rem .2rem; }
.cy-brand .leaf { font-size:1.7rem; line-height:1; }
.cy-brand .name { color:#ffffff; font-weight:800; font-size:1.25rem; letter-spacing:.01em; }
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
  border-radius:.6rem; padding:.55rem .7rem; margin-bottom:.15rem; color:#e9f6ee; background:transparent; }
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p { color:#e9f6ee !important; font-weight:500; }
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover { background:rgba(255,255,255,.10); }
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] { background:#1b6b45; }
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] p { color:#fff !important; font-weight:700; }
.cy-side-foot { color:#9cc7b1; font-size:.75rem; margin-top:1.2rem; line-height:1.5; }

/* ---------- headers ---------- */
.cy-head { display:flex; align-items:center; gap:.9rem; margin:.1rem 0 1rem 0; }
.cy-head .ico { font-size:2.3rem; line-height:1; }
.cy-head h1 { margin:0; font-size:1.9rem; font-weight:800; color:#12352a; }
.cy-head p { margin:.1rem 0 0 0; color:#4d6a5d; font-size:.98rem; }

/* ---------- cards (st.container(key="card_*")) ---------- */
div[class*="st-key-card_"] { background:#ffffff; border:1px solid #e1ece5; border-radius:1rem;
  padding:1.1rem 1.25rem; box-shadow:0 2px 10px rgba(18,53,42,.06); }
div[class*="st-key-card_results"] { background:#eaf7ef; }
.cy-card-title { font-weight:800; font-size:1.05rem; color:#12352a; margin:0 0 .6rem 0; }
.cy-box { background:#fff; border:1px solid #e1ece5; border-radius:.9rem; padding:.9rem 1rem; box-shadow:0 2px 8px rgba(18,53,42,.05); }
.cy-box h4 { margin:.1rem 0 .55rem 0; font-size:1rem; }
.cy-stat { background:#fff; border:1px solid #e1ece5; border-radius:.9rem; padding:.85rem .6rem; text-align:center; box-shadow:0 2px 8px rgba(18,53,42,.06); }
.cy-stat .ico { font-size:1.5rem; }
.cy-stat .val { font-size:1.55rem; font-weight:800; color:#12352a; line-height:1.15; }
.cy-stat .lab { font-weight:700; font-size:.88rem; color:#26463a; }
.cy-stat .sub { font-size:.74rem; color:#6b8579; }
.cy-metric { background:#ffffff; border:1px solid #d3e8da; border-radius:.9rem; padding:.9rem 1rem; }
.cy-metric .lab { color:#4d6a5d; font-size:.85rem; font-weight:600; }
.cy-metric .val { color:#0f7a43; font-size:2.2rem; font-weight:800; line-height:1.1; }
.cy-metric .unit { color:#33564a; font-size:.85rem; }
.cy-metric .sub { color:#7b9387; font-size:.74rem; margin-top:.2rem; }
.cy-table { width:100%; border-collapse:collapse; font-size:.86rem; }
.cy-table td { padding:.38rem .55rem; border-bottom:1px solid #edf3ef; color:#1f3b31; }
.cy-table td:first-child { color:#5a7468; width:46%; }
.cy-table tr:last-child td { border-bottom:none; }
.cy-calc { background:#f4f8f5; border-radius:.6rem; padding:.55rem .75rem; margin-bottom:.5rem; }
.cy-calc .k { color:#5a7468; font-size:.78rem; } .cy-calc .v { color:#12352a; font-weight:700; }
.cy-crop { background:#fff; border:1px solid #e1ece5; border-radius:.9rem; text-align:center; padding:.6rem .3rem .5rem; }
.cy-crop img { width:78px; height:78px; object-fit:contain; }
.cy-crop div { font-weight:700; font-size:.85rem; color:#26463a; }
.cy-insights { background:#e6f5ec; border:1px solid #cfe8d8; border-radius:1rem; padding:1rem 1.3rem; }
.cy-consider { background:#fff6e8; border:1px solid #f6dfb8; border-radius:1rem; padding:1rem 1.3rem; }
.cy-list { list-style:none; padding:0; margin:0; }
.cy-list li { padding:.3rem 0 .3rem 1.7rem; position:relative; font-size:.93rem; color:#1f3b31; }
.cy-list li::before { content:"✔"; position:absolute; left:0; color:#12804a; font-weight:800; }
.cy-consider .cy-list li::before { content:"◆"; color:#e08a00; }
.tag { display:inline-block; font-size:.66rem; font-weight:800; letter-spacing:.04em; border-radius:.8rem; padding:.05rem .5rem; margin-right:.4rem; vertical-align:middle; }
.tag.data { background:#d7f0e0; color:#0c6a3a; } .tag.general { background:#e8edf3; color:#46586b; }
.cy-warn { background:#fff6e8; border:1px solid #f6dfb8; border-radius:.7rem; padding:.55rem .8rem; color:#6b4a06; font-size:.86rem; margin:.3rem 0; }
.cy-disclaimer { background:#fff6e8; border:1px solid #f6dfb8; border-radius:.7rem; padding:.6rem .9rem; color:#6b4a06; font-size:.85rem; }

/* ---------- hero (st.container(key="hero")) ---------- */
.st-key-hero { border-radius:1.1rem; padding:2.2rem 2.4rem 1.8rem 2.4rem; min-height:330px; background-size:cover; background-position:center;
  box-shadow:0 6px 22px rgba(18,53,42,.18); margin-bottom:1rem; }
.st-key-hero h1.hero-title { font-size:3.1rem; font-weight:800; color:#0f2f24; margin:0; text-shadow:0 1px 8px rgba(255,255,255,.55); }
.st-key-hero .hero-sub { font-size:1.3rem; font-weight:700; color:#0f2f24; margin:.1rem 0 .6rem 0; text-shadow:0 1px 6px rgba(255,255,255,.6); }
.st-key-hero .hero-text { max-width:520px; color:#13392c; font-size:1rem; font-weight:500; text-shadow:0 1px 6px rgba(255,255,255,.65); }

/* ---------- inputs & buttons (always readable) ---------- */
label, [data-testid="stWidgetLabel"] p { color:#1f3b31 !important; font-weight:600; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="base-input"] { background:#ffffff !important; }
input, textarea { color:#16342a !important; }
div.stButton > button, div.stFormSubmitButton > button, div.stDownloadButton > button {
  border-radius:.6rem; font-weight:700; min-height:2.6rem; border:1px solid #b9d8c5; color:#12352a; background:#ffffff; }
div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
  background:#12804a; color:#ffffff; border:0; width:100%; }
div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button[kind="primary"]:hover { background:#0c6a3a; color:#fff; }
div.stButton > button[kind="primary"] p, div.stFormSubmitButton > button[kind="primary"] p { color:#ffffff !important; }
.stTabs [data-baseweb="tab"] { background:#ffffff; border-radius:.6rem .6rem 0 0; padding:.5rem 1rem; color:#33564a; }
.stTabs [aria-selected="true"] { color:#12804a !important; font-weight:700; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border:1px solid #e1ece5; border-radius:.7rem; }
</style>
"""


def hero_css(banner_b64: str | None) -> str:
    if banner_b64:
        bg = (".st-key-hero{background-image:linear-gradient(90deg,rgba(255,255,255,.55) 0%,rgba(255,255,255,.15) 55%,rgba(255,255,255,0) 100%),"
              f"url('data:image/jpeg;base64,{banner_b64}');}}")
    else:
        bg = ".st-key-hero{background:linear-gradient(120deg,#cfe9d6,#8fcf9b);}"
    return f"<style>{bg}</style>"
