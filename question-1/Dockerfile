# --- Multi-stage build ---

# ---------- Stage 1: builder ----------
# Uses the full python:3.11 image (has gcc/g++, headers, apt package DB, etc.)
# because scikit-learn/pandas/numpy need a build toolchain to compile their
# native extensions when installing from wheels/sdists and to run training.
FROM python:3.11 AS builder

WORKDIR /app

COPY requirements.txt .
# Install into an isolated prefix so we can copy just the installed
# packages (not pip's cache, not the compiler toolchain) into the final stage.
RUN pip install --prefix=/install -r requirements.txt

COPY generate_dataset.py train.py spam_dataset.csv ./
# Make the just-installed packages importable for the training step
ENV PYTHONPATH=/install/lib/python3.11/site-packages
RUN python train.py

# ---------- Stage 2: runtime ----------
# Slim base: no compilers, no apt cache, no build headers -- just the
# Python interpreter and the OS libs needed to *run* (not build) the wheels.
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy only the installed site-packages (built in the builder stage)
COPY --from=builder /install /usr/local

# Copy only what's needed to serve requests: app code + trained artifact.
# Explicitly NOT copied: gcc/g++/build-essential, pip's download/wheel cache,
# apt lists, the raw spam_dataset.csv, train.py/generate_dataset.py.
COPY app.py .
COPY --from=builder /app/model.joblib .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
