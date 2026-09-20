from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
from typing import Optional

app = FastAPI(title="Arogya Triage API")

# Load model and scaler
try:
    model = joblib.load("triage_model.joblib")
    scaler = joblib.load("scaler.joblib")
except Exception as e:
    print(f"Error loading model/scaler: {e}")
    model = None
    scaler = None

class TriageRequest(BaseModel):
    age: int
    sex: int # 1: Male, 2: Female (per dataset)
    mental: int
    pain: int
    nrs_pain: int
    sbp: float
    dbp: float
    hr: float
    rr: float
    bt: float
    saturation: float

@app.get("/")
def read_root():
    return {"status": "Triage API is running"}

@app.post("/predict")
def predict_triage(request: TriageRequest):
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Model not loaded on server")

    # Prepare feature vector
    features = np.array([[
        request.age, request.sex, request.mental, request.pain,
        request.nrs_pain, request.sbp, request.dbp, request.hr,
        request.rr, request.bt, request.saturation
    ]])

    # Scale features
    scaled_features = scaler.transform(features)

    # Predict
    prediction = model.predict(scaled_features)[0]

    # Mapping KTAS levels to descriptions
    ktas_map = {
        1: "Critical (Immediate)",
        2: "Urgent (Very Urgent)",
        3: "Standard (Urgent)",
        4: "Low (Less Urgent)",
        5: "Non-Urgent"
    }

    return {
        "priority_level": int(prediction),
        "description": ktas_map.get(prediction, "Unknown"),
        "recommendation": "Immediate assistance required" if prediction <= 2 else "Routine care"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
