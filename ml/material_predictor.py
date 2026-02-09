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

#     return material
import joblib
import numpy as np
from pathlib import Path

# ======================
# LOAD MODEL & ENCODERS
# ======================

BASE_DIR = Path(__file__).resolve().parent

model = joblib.load(BASE_DIR / "material_model.pkl")
orientation_encoder = joblib.load(BASE_DIR / "orientation_encoder.pkl")
material_encoder = joblib.load(BASE_DIR / "material_encoder.pkl")

print("🧠 Material ML model & encoders loaded")


# ======================
# RULE-BASED OVERRIDES
# ======================

def apply_material_rules(features: dict):
    """
    Deterministic architectural rules.
    Returns material string or None if ML should decide.
    """

    # -------------------------
    # GLASS (FORCED)
    # -------------------------
    layer = features.get("layer", "")
    if "glaz" in layer or "glass" in layer:
        return "glass"

    # -------------------------
    # EXTERIOR STRUCTURAL WALLS
    # -------------------------
    if features.get("is_exterior") == 1:
        return "concrete"

    # -------------------------
    # WET AREAS
    # -------------------------
    if features.get("adj_bathroom") == 1:
        return "tile"

    if features.get("adj_kitchen") == 1:
        return "tile"

    # -------------------------
    # THIN INTERIOR PARTITIONS
    # -------------------------
    if features.get("thickness", 0) < 0.15:
        return "gypsum"

    return None


# ======================
# MAIN MATERIAL PREDICTOR
# ======================

def predict_material(features: dict):
    """
    Hybrid material prediction:
    1️⃣ Rule-based architectural logic
    2️⃣ ML model fallback (XGBoost)

    Expected features:
    {
        length: float,
        thickness: float,
        height: float,
        orientation: "horizontal" | "vertical",
        is_exterior: 0 | 1,
        layer: str (optional, for rules)
    }
    """

    # -------------------------
    # RULE PASS
    # -------------------------
    rule_material = apply_material_rules(features)
    if rule_material:
        print(f"🧠 Rule-based material: {rule_material}")
        return rule_material

    # -------------------------
    # ENCODE ORIENTATION
    # -------------------------
    orientation = features.get("orientation", "horizontal")

    if orientation in orientation_encoder.classes_:
        orientation_enc = orientation_encoder.transform([orientation])[0]
    else:
        orientation_enc = 0

    # -------------------------
    # BUILD FEATURE VECTOR (⚠️ EXACTLY 5 FEATURES)
    # -------------------------
    X = np.array([[
        features.get("length", 0.0),
        features.get("thickness", 0.0),
        features.get("height", 0.0),
        orientation_enc,
        features.get("is_exterior", 0)
    ]])

    # -------------------------
    # ML PREDICTION
    # -------------------------
    try:
        pred = model.predict(X)[0]
        material = material_encoder.inverse_transform([pred])[0]
        print(f"🧠 ML-based material: {material}")
        return material

    except Exception as e:
        print(f"❌ ML prediction failed, fallback to concrete: {e}")
        return "concrete"
