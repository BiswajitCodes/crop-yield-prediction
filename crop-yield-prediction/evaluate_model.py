"""Re-evaluate the bundled model on the SAME held-out split used by train_model.py
(test_size=0.2, random_state=42) and write models/model_diagnostics.json.
Nothing is retrained; the saved model is only used to predict."""
import json
import warnings
import joblib
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

import config
import train_model as tm

warnings.filterwarnings("ignore", category=FutureWarning)


def metrics(y, p):
    return {"MAE": float(mean_absolute_error(y, p)), "RMSE": float(np.sqrt(mean_squared_error(y, p))),
            "R2": float(r2_score(y, p)), "n": int(len(y))}


def main():
    meta = json.loads(config.META_PATH.read_text(encoding="utf-8"))
    df = tm.load_data()
    X, y = df[tm.FEATURES], df[tm.TARGET]
    _, Xte, _, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    model = joblib.load(config.MODEL_PATH)
    p = model.predict(Xte)
    overall = metrics(yte, p)
    recorded = meta["metrics"]
    for k in ("MAE", "RMSE", "R2"):
        assert abs(overall[k] - recorded[k]) < 1e-6, f"{k} differs from recorded metadata: {overall[k]} vs {recorded[k]}"
    mask = (Xte["Crop"] != "Coconut").values
    per_crop = {}
    for crop in sorted(Xte["Crop"].unique()):
        m = (Xte["Crop"] == crop).values
        if m.sum() >= 5:
            per_crop[crop] = {"MAE": float(mean_absolute_error(yte[m], p[m])), "n": int(m.sum()),
                              "mean_actual": float(yte[m].mean())}
    out = {
        "note": "Computed by evaluate_model.py with the saved model on the original random 80/20 split (random_state=42).",
        "overall": overall,
        "excluding_coconut": metrics(yte[mask], p[mask]),
        "per_crop": per_crop,
    }
    config.DIAG_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Wrote", config.DIAG_PATH)
    print("overall", overall)
    print("excluding coconut", out["excluding_coconut"])


if __name__ == "__main__":
    main()
