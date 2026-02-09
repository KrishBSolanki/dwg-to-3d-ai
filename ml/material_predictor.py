# import joblib
# import pandas as pd

# model = joblib.load("ml/material_model.pkl")
# layer_encoder = joblib.load("ml/layer_encoder.pkl")
# material_encoder = joblib.load("ml/material_encoder.pkl")


# def predict_material(feature_dict):
#     df = pd.DataFrame([feature_dict])

#     df["layer"] = layer_encoder.transform(df["layer"])

#     y_pred = model.predict(df)[0]
#     material = material_encoder.inverse_transform([y_pred])[0]

#     return materialimport joblib
import numpy as np
from pathlib import Path
import joblib


# ======================
# LOAD MODEL & ENCODERS
# ======================

BASE_DIR = Path(__file__).resolve().parent

model = joblib.load(BASE_DIR / "material_model.pkl")
orientation_encoder = joblib.load(BASE_DIR / "orientation_encoder.pkl")
material_encoder = joblib.load(BASE_DIR / "material_encoder.pkl")

print("🧠 Material ML model & encoders loaded")


# ======================
# RULE CONFIDENCE SYSTEM
# ======================

def rule_candidates(features: dict):
    """
    Return (material, confidence) pairs instead of hard overrides.
    Confidence ∈ [0, 1].
    """

    candidates = []

    layer = features.get("layer", "")

    # -------------------------
    # GLASS (VERY STRONG)
    # -------------------------
    if "glaz" in layer or "glass" in layer:
        candidates.append(("glass", 0.95))

    # -------------------------
    # EXTERIOR WALLS (STRONG)
    # -------------------------
    if features.get("is_exterior") == 1:
        candidates.append(("concrete", 0.75))

    # -------------------------
    # WET AREAS (MEDIUM)
    # -------------------------
    if features.get("adj_bathroom") == 1 or features.get("adj_kitchen") == 1:
        candidates.append(("tile", 0.65))

    # -------------------------
    # THIN PARTITIONS (MEDIUM)
    # -------------------------
    if features.get("thickness", 0) < 0.18:
        candidates.append(("gypsum", 0.6))

    return candidates


# ======================
# MAIN MATERIAL PREDICTOR
# ======================

def predict_material(features: dict):
    """
    Production-grade hybrid material prediction.

    Decision order:
    1️⃣ Strong rule (confidence ≥ 0.9)
    2️⃣ ML prediction
    3️⃣ Medium rule arbitration
    4️⃣ Safe fallback
    """

    # -------------------------
    # RULE CANDIDATES
    # -------------------------
    candidates = rule_candidates(features)

    for material, conf in candidates:
        if conf >= 0.9:
            print(f"🧠 Strong rule material: {material}")
            return material

    # -------------------------
    # ML PREDICTION
    # -------------------------
    try:
        orientation = features.get("orientation", "horizontal")
        if orientation in orientation_encoder.classes_:
            orientation_enc = orientation_encoder.transform([orientation])[0]
        else:
            orientation_enc = 0

        X = np.array([[
            features.get("length", 0.0),
            features.get("thickness", 0.0),
            features.get("height", 0.0),
            orientation_enc,
            features.get("is_exterior", 0)
        ]])

        pred = model.predict(X)[0]
        ml_material = material_encoder.inverse_transform([pred])[0]
        print(f"🧠 ML-based material: {ml_material}")

    except Exception as e:
        print(f"❌ ML failed ({e}), fallback to concrete")
        return "concrete"

    # -------------------------
    # ARBITRATION (SMART PART)
    # -------------------------
    if candidates:
        # pick highest-confidence rule
        rule_material, rule_conf = max(candidates, key=lambda x: x[1])

        if rule_conf >= 0.7:
            print(f"🧠 Rule-preferred material: {rule_material}")
            return rule_material

    # -------------------------
    # DEFAULT TO ML
    # -------------------------
    return ml_material

