# Multi-stage build 
# We will use the full Python 3.11 image because it already includes the tools needed to install and run libraries like scikit-learn,
# pandas, and NumPy, which may require additional system tools to build and run properly.
FROM python:3.11 AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

COPY generate_dataset.py train.py spam_dataset.csv ./
# Making the installed packages importable for training
ENV PYTHONPATH=/install/lib/python3.11/site-packages
RUN python train.py

# runtime 
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy only the installed site-packages 
COPY --from=builder /install /usr/local

# Copy only what's needed to serve requests: app code + trained artifact.
COPY app.py .
COPY --from=builder /app/model.joblib .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
