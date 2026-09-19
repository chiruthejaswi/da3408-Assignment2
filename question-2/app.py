import hashlib
import os
import time

import joblib
import redis
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")

# Redis connection settings. REDIS_HOST defaults to "cache" -- the Compose
# service name -- so this works unmodified inside docker-compose; override
# with REDIS_HOST=localhost for a local, non-container run.
REDIS_HOST = os.environ.get("REDIS_HOST", "cache")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "300"))
CACHE_KEY_PREFIX = "spam_cache:"

app = FastAPI(title="Spam Detection API")

model = None
redis_client = None


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    label: str
    cached: bool
    latency_ms: float


def cache_key(text: str) -> str:
    # Hash the raw text so arbitrary length/characters never break the Redis key.
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"{CACHE_KEY_PREFIX}{digest}"


@app.on_event("startup")
def load_model():
    global model, redis_client
    model = joblib.load(MODEL_PATH)
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=2,
    )


@app.get("/healthz")
def healthz():
    if model is None:
        return JSONResponse(status_code=503, content={"status": "loading"})
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    start = time.perf_counter()
    key = cache_key(req.text)

    # Try the cache first.
    try:
        cached_label = redis_client.get(key)
    except redis.exceptions.RedisError:
        # Redis being unreachable should degrade to "always compute", not crash the API.
        cached_label = None

    if cached_label is not None:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return PredictResponse(label=cached_label, cached=True, latency_ms=elapsed_ms)

    # Cache miss: run the actual model.
    label = model.predict([req.text])[0]

    try:
        redis_client.setex(key, CACHE_TTL_SECONDS, label)
    except redis.exceptions.RedisError:
        pass  # caching is best-effort; a Redis outage shouldn't break predictions

    elapsed_ms = (time.perf_counter() - start) * 1000
    return PredictResponse(label=label, cached=False, latency_ms=elapsed_ms)
