FROM python:3.11-slim
WORKDIR /app

# No third-party dependencies -- validate.py only uses the standard library.
COPY validate.py .
COPY shards/ /shards/

# No CMD args needed: JOB_COMPLETION_INDEX and the Downward API env vars
# are injected by Kubernetes at pod creation time (see k8s-job.yaml).
CMD ["python3", "validate.py"]
