# backend/predictor/train_model.py
import os
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from xgboost import XGBClassifier

# We’ll train ONLY on features we can compute live in predictor.py
SERVE_FEATURES = [
    "AIRLINE_CODE", "ORIGIN_CODE", "DEST_CODE",   # strings (IATA codes)
    "DEP_HOUR", "DAY_OF_WEEK", "MONTH",
    "IS_MORNING", "IS_AFTERNOON", "IS_EVENING", "IS_NIGHT",
    "ORIGIN_PRECIP", "DEST_PRECIP",
    "ORIGIN_SNOW", "DEST_SNOW",
    "ORIGIN_HEAVY_WIND", "DEST_HEAVY_WIND",
    "TEMP_DIFF",
]

def load_training_data():
    # Use your existing preprocessing to engineer time + weather features
    from backend.predictor.data_preprocessing import preprocess_flight_data

    base = os.path.dirname(__file__)
    flights_csv  = os.path.join(base, "data", "flight_sample_2019-2023.csv")
    weather_csv  = os.path.join(base, "data", "weather_airport_2019-2023.csv")

    df = preprocess_flight_data(flights_csv, weather_csv)

    # Align names with what the live API sends (IATA strings)
    # If your CSV already has these as strings, this just copies them.
    df["AIRLINE_CODE"] = df["AIRLINE"]
    df["ORIGIN_CODE"]  = df["ORIGIN"]
    df["DEST_CODE"]    = df["DEST"]

    # Train split (simple cutoff just to be concrete)
    train = df[df["FL_DATE"] < "2022-01-01"].copy()
    X = train[SERVE_FEATURES].copy()
    y = train["ARR_DELAYED"].astype(int)
    return X, y

def train_and_save_model():
    X, y = load_training_data()

    categorical = ["AIRLINE_CODE", "ORIGIN_CODE", "DEST_CODE"]
    numeric     = [c for c in X.columns if c not in categorical]

    preprocess = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
            ("num", Pipeline([("imp", SimpleImputer(strategy="median"))]), numeric),
        ],
        remainder="drop",
    )

    model = XGBClassifier(
        n_estimators=300, max_depth=8, learning_rate=0.08,
        subsample=0.9, colsample_bytree=0.9, tree_method="hist",
        random_state=42, n_jobs=-1,
    )

    pipe = Pipeline([("prep", preprocess), ("clf", model)])
    pipe.fit(X, y)

    artifact = {
        "pipeline": pipe,
        "feature_order": X.columns.tolist(),  # <- API will use this exact order
        "version": "2025-08-13-xgb-bundle-v1",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "flight_delay_pipeline.joblib")
    joblib.dump(artifact, out_path)
    print(f"Saved model bundle to {out_path}")

if __name__ == "__main__":
    train_and_save_model()