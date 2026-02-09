import numpy as np
import pandas as pd
import joblib
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from pathlib import Path

"""
Industry-style retraining using weak supervision.
Schema locked to inference.
"""

# ======================
# BUILD TRAINING DATA
# ======================

data = []

# ---- Exterior concrete walls ----
for _ in range(120):
    data.append({
        "length": np.random.uniform(2.0, 6.0),
        "thickness": np.random.uniform(0.22, 0.35),
        "height": 3.0,
        "orientation": np.random.choice(["horizontal", "vertical"]),
        "is_exterior": 1,
        "material": "concrete"
    })

# ---- Interior gypsum walls ----
for _ in range(100):
    data.append({
        "length": np.random.uniform(0.5, 3.0),
        "thickness": np.random.uniform(0.08, 0.15),
        "height": 3.0,
        "orientation": np.random.choice(["horizontal", "vertical"]),
        "is_exterior": 0,
        "material": "gypsum"
    })

# ---- Bathroom / kitchen tiles ----
for _ in range(60):
    data.append({
        "length": np.random.uniform(1.0, 3.0),
        "thickness": np.random.uniform(0.15, 0.25),
        "height": 3.0,
        "orientation": np.random.choice(["horizontal", "vertical"]),
        "is_exterior": 0,
        "material": "tile"
    })

# ---- Windows ----
for _ in range(40):
    data.append({
        "length": np.random.uniform(0.8, 2.0),
        "thickness": 0.05,
        "height": 1.2,
        "orientation": np.random.choice(["horizontal", "vertical"]),
        "is_exterior": 1,
        "material": "glass"
    })

df = pd.DataFrame(data)
print(f"📊 Training samples: {len(df)}")

# ======================
# ENCODERS
# ======================

orientation_encoder = LabelEncoder()
material_encoder = LabelEncoder()

df["orientation_enc"] = orientation_encoder.fit_transform(df["orientation"])
df["material_enc"] = material_encoder.fit_transform(df["material"])

# ======================
# FEATURE MATRIX (5 FEATURES)
# ======================

X = df[[
    "length",
    "thickness",
    "height",
    "orientation_enc",
    "is_exterior"
]].values

y = df["material_enc"].values

# ======================
# TRAIN MODEL
# ======================

model = XGBClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    eval_metric="mlogloss"
)

model.fit(X, y)
print("🧠 Model trained successfully")

# ======================
# SAVE ARTIFACTS
# ======================

Path("ml").mkdir(exist_ok=True)

joblib.dump(model, "ml/material_model.pkl")
joblib.dump(orientation_encoder, "ml/orientation_encoder.pkl")
joblib.dump(material_encoder, "ml/material_encoder.pkl")

print("✅ New model & encoders saved")
