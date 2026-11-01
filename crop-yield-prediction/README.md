# CropYield AI

Streamlit app that predicts crop yield and total production from the bundled Extra Trees model, explains the result,
saves history in SQLite, and visualises the dataset.

## Run on Windows (Python 3.11 or newer)
Double-click `run_windows.bat`, or in a terminal inside this folder:

```bat
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```
Open http://localhost:8501.

## Run on macOS / Linux
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Pages
Home · Predict Yield · History · Data Insights · Model Info · Recommendations · About

## How inputs map to the model
The model was trained on 8 features: Crop, Season, State, Crop_Year, Area, Annual_Rainfall, Fertilizer, Pesticide.
In the training CSV, Fertilizer and Pesticide are **total kg for the whole area**. The form asks for **kg/ha** and multiplies by
area before calling the model. Yield is tonnes/ha for most crops; Coconut is nuts/ha and Cotton(lint), Jute and Mesta are bales/ha
(source conventions). Production = yield x area.

## Tests (no Streamlit needed for the first two)
```bash
python tests/test_core.py     # real model, dataset, SQLite, validation, recommendations
python tests/ui_smoke.py      # runs every page against a stand-in Streamlit module
python test_model.py          # original model integrity check
python evaluate_model.py      # regenerates models/model_diagnostics.json from the saved model
```

## Images
`assets/farm_banner.jpg` and `assets/crop_images/*.png` are generated illustrations (`python make_assets.py`).
To use real photographs, replace those files with your own (same names); the app picks them up automatically.

## Notes
- Metrics are from the original random 80/20 split; see the Model Info page for caveats (coconut dominates RMSE/R2).
- Predictions are estimates, not guaranteed harvest outcomes.
