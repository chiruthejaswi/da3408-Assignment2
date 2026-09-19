import os

import joblib
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")

# Bumped between builds to demonstrate the Question 4 rolling update:
# v1 for the initial Deployment, v2 for the updated image tag.
APP_VERSION = "v2"

app = FastAPI(title="Spam Detection API")

model = None


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    label: str


@app.on_event("startup")
def load_model():
    global model
    model = joblib.load(MODEL_PATH)


@app.get("/healthz")
def healthz():
    if model is None:
        return JSONResponse(status_code=503, content={"status": "loading", "version": APP_VERSION})
    return {"status": "ok", "version": APP_VERSION}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    label = model.predict([req.text])[0]
    return PredictResponse(label=label)
