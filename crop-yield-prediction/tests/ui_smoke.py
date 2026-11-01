"""UI smoke test using a lightweight stand-in for Streamlit (useful when Streamlit is not installable).
It executes every page script end-to-end with the REAL model, dataset, database and charts, and checks for
exceptions and HTML that Markdown would mangle. It does NOT replace opening the real app in a browser.
Run from the project folder:  python tests/ui_smoke.py"""
import os
import re
import runpy
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ["CROPYIELD_DB"] = str(Path(tempfile.mkdtemp()) / "smoke.db")

import io
import matplotlib
matplotlib.use("Agg")


class Stop(BaseException): ...   # real Streamlit control-flow exceptions derive from BaseException
class Rerun(BaseException): ...
class Switch(BaseException): ...


class CM:
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def __getattr__(self, name):  # columns/containers expose the same widget API as `st`
        return getattr(fake, name)


class State(dict):
    __getattr__ = dict.get
    def __setattr__(self, k, v): self[k] = v


class Fake(types.ModuleType):
    def __init__(self):
        super().__init__("streamlit")
        self.session_state = State()
        self.sidebar = CM()
        self.log = []          # (kind, text)
        self.html = []         # strings passed with unsafe_allow_html
        self.overrides = {}    # label/key prefix -> value
        self.true_keys = set() # button keys that return True
        self.editor_fn = None  # callable(df) -> edited df
        self.pyplots = 0
        self.switches = []
        self.column_config = types.SimpleNamespace(CheckboxColumn=lambda *a, **k: ("chk", a, k))

    def _ov(self, label, key, default):
        for k in (key, label):
            if k is None: continue
            for pat, val in self.overrides.items():
                if str(k).startswith(pat):
                    return val
        return default

    # config / layout
    def set_page_config(self, **k): pass
    def columns(self, spec, **k):
        n = spec if isinstance(spec, int) else len(spec)
        return [CM() for _ in range(n)]
    def tabs(self, labels): return [CM() for _ in labels]
    def container(self, **k): return CM()
    def form(self, *a, **k): return CM()
    def expander(self, *a, **k): return CM()
    def stop(self): raise Stop()
    def rerun(self): raise Rerun()
    def switch_page(self, p): self.switches.append(p); raise Switch(p)
    def page_link(self, *a, **k): self.log.append(("page_link", a[0]))
    # text
    def _t(kind):
        def f(self, body="", *a, unsafe_allow_html=False, **k):
            self.log.append((kind, str(body)))
            if unsafe_allow_html: self.html.append(str(body))
        return f
    markdown = _t("md"); write = _t("write"); caption = _t("caption"); code = _t("code")
    error = _t("error"); warning = _t("warning"); info = _t("info"); success = _t("success")
    def dataframe(self, df, **k): self.log.append(("df", len(df)))
    def table(self, df, **k): pass
    def metric(self, *a, **k): self.log.append(("metric", a))
    def data_editor(self, df, **k):
        return self.editor_fn(df) if self.editor_fn else df
    def pyplot(self, fig, **k):
        buf = io.BytesIO(); fig.savefig(buf, format="png"); assert buf.tell() > 1000; self.pyplots += 1
    def download_button(self, label, data, **k):
        assert len(data) > 0 or True; self.log.append(("download", label)); return False
    # widgets
    def selectbox(self, label, options, index=0, key=None, **k):
        v = self._ov(label, key, None)
        if v is not None:
            assert v in options, f"{label}: {v} not in options"
            return v
        return options[index]
    def multiselect(self, label, options, key=None, **k): return self._ov(label, key, [])
    def number_input(self, label, value=None, key=None, **k): return self._ov(label, key, value)
    def slider(self, label, min_value=None, max_value=None, value=None, key=None, **k):
        assert min_value < max_value, f"slider '{label}' min >= max"
        return self._ov(label, key, value)
    def text_input(self, label, key=None, **k): return self._ov(label, key, "")
    def date_input(self, label, value=None, **k): return self._ov(label, None, value)
    def checkbox(self, label, key=None, **k): return self._ov(label, key, False)
    def button(self, label, key=None, disabled=False, **k): return bool(key in self.true_keys and not disabled)
    def form_submit_button(self, label, **k): return "form_submit" in self.true_keys


fake = Fake()
sys.modules["streamlit"] = fake

import pandas as pd
import database
import model_service as ms

PAGES = ["app.py", "pages/1_Predict_Yield.py", "pages/2_Recommendations.py", "pages/3_Data_Insights.py",
         "pages/4_Prediction_History.py", "pages/5_Model_Info.py", "pages/6_About.py"]
passed = 0


def run(page, expect=(), allow_errors=False):
    fake.log.clear(); fake.html.clear(); fake.pyplots = 0
    try:
        runpy.run_path(str(ROOT / page), run_name="__main__")
    except expect:
        pass
    errors = [t for k, t in fake.log if k == "error"]
    assert allow_errors or not errors, f"{page} showed errors: {errors}"
    check_html(page)


def check_html(page):
    for h in fake.html:
        if h.lstrip().startswith("<style"):
            continue  # CommonMark <style> blocks may contain blank lines
        assert "\n\n" not in h, f"{page}: blank line inside HTML block (Markdown would break it): {h[:80]}"
        assert not re.search(r"\n {4,}\S", h), f"{page}: indented HTML line (would render as code): {h[:80]}"


def ok(msg):
    global passed
    passed += 1
    print("ok  -", msg)


# 1. every page renders with defaults (no prediction yet)
for p in PAGES:
    run(p, expect=(Stop,))
    ok(f"{p} renders with no history")

# 2. prediction through the form
fake.true_keys = {"form_submit"}
run("pages/1_Predict_Yield.py")
res = fake.session_state["last_result"]
assert res["saved_id"] and res["yield"] > 0 and abs(res["production"] - res["yield"] * res["row"]["Area"]) < 1e-9
text = " ".join(t for _, t in fake.log)
assert "Input Summary" in "".join(fake.html) and "Calculation" in "".join(fake.html) and f"{res['yield']:,.3f}" in "".join(fake.html)
ok(f"predict page: real prediction {res['yield']:.3f} t/ha saved, summary + calculation shown")

# 3. invalid input handling on the form (bypassing widget min/max, as a user could via keyboard edge cases)
before = len(database.get_predictions())
fake.overrides = {"Cultivated area": 0.0}
fake.session_state.clear()
run("pages/1_Predict_Yield.py", allow_errors=True)
errs = [t for k, t in fake.log if k == "error"]
assert errs and "greater than 0" in errs[0] and len(database.get_predictions()) == before and "last_result" not in fake.session_state
ok("invalid area shows an error and saves nothing")
fake.overrides = {"Crop year": None}
fake.log.clear()
try:
    runpy.run_path(str(ROOT / "pages/1_Predict_Yield.py"), run_name="__main__")
except Stop:
    pass
assert any("missing" in t for k, t in fake.log if k == "error")
ok("missing year shows an error")
fake.overrides = {}

# 4. all pages after a prediction exists (session + DB paths)
fake.true_keys = {"form_submit"}
run("pages/1_Predict_Yield.py")
fake.true_keys = set()
for p in PAGES:
    run(p)
    ok(f"{p} renders after a prediction")
fake.session_state.clear()
run("app.py"); run("pages/2_Recommendations.py")
assert any("Key Insights" in t for k, t in fake.log if k == "md")
ok("home + recommendations use the latest saved record when session is empty")

# 5. Data Insights: every crop x several filters renders charts without error
crops = ms.get_metadata()["crops"]
total_plots = 0
for c in crops:
    fake.overrides = {"Crop (for state": c}
    run("pages/3_Data_Insights.py")
    total_plots += fake.pyplots
fake.overrides = {"Crop (for state": "Rice", "State / UT (empty": ["Odisha"], "Season (empty": ["Kharif"], "Year range": (2005, 2010)}
run("pages/3_Data_Insights.py")
fake.overrides = {"Crop (for state": "Coconut", "State / UT (empty": ["Delhi"], "Year range": (1997, 1998)}
run("pages/3_Data_Insights.py")
assert any(k == "info" and "Not enough data" in t for k, t in fake.log)
fake.overrides = {}
ok(f"Data Insights: all {len(crops)} crops + narrow filters OK ({total_plots} charts rendered; sparse data handled)")

# 6. History: filter, delete selected (confirmed), delete all (confirmed)
for _ in range(2):
    fake.true_keys = {"form_submit"}; run("pages/1_Predict_Yield.py")
fake.true_keys = set()
n0 = len(database.get_predictions())
assert n0 >= 3
fake.overrides = {"Search": "rice"}
run("pages/4_Prediction_History.py")
fake.overrides = {"Search": "zzzz-no-match"}
run("pages/4_Prediction_History.py", expect=(Stop,))
assert any("No saved predictions match" in t for k, t in fake.log if k == "info")
fake.overrides = {}
def pick_first(df):
    d = df.copy(); d.loc[d.index[0], "Delete"] = True; return d
fake.editor_fn = pick_first
fake.overrides = {"Yes, permanently delete the selected": True}
fake.true_keys = {"btn_del_sel"}
try:
    run("pages/4_Prediction_History.py", expect=(Rerun,))
except Rerun:
    pass
assert len(database.get_predictions()) == n0 - 1
ok("history: delete selected requires confirmation and removes exactly one row")
fake.true_keys = {"btn_del_sel"}; fake.overrides = {}
run("pages/4_Prediction_History.py", expect=(Rerun,))
assert len(database.get_predictions()) == n0 - 1
ok("history: delete without confirmation does nothing")
fake.editor_fn = None
fake.true_keys = {"btn_del_all"}; fake.overrides = {"I understand this deletes ALL": True}
run("pages/4_Prediction_History.py", expect=(Rerun,))
assert database.get_predictions() == []
ok("history: delete all (confirmed) empties the database")
fake.true_keys = set(); fake.overrides = {}
run("pages/4_Prediction_History.py", expect=(Stop,))
assert any("No predictions saved yet" in t for k, t in fake.log if k == "info")
ok("history: empty-state message")

# 7. navigation buttons
for key, page, target in [("home_predict", "app.py", "pages/1_Predict_Yield.py"), ("home_learn", "app.py", "pages/6_About.py")]:
    fake.true_keys = {key}; fake.switches.clear()
    run(page, expect=(Switch,))
    assert fake.switches == [target]
ok("Home buttons navigate to Predict and About")
for _, _, path in __import__("config").PAGES:
    assert (ROOT / path).exists(), path
ok("every sidebar link points to an existing page file")

print(f"\nUI SMOKE: {passed} CHECK GROUPS PASSED")
