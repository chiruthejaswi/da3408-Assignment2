# Spam-Detection API — Docker & Kubernetes Assignment

A single spam-detection API used
as the common thread across all four questions, each exercising a different
Docker/Kubernetes skill.

## Structure

| Folder | Question | What it covers |
|---|---|---|
| `question-1` | Single-stage vs. multi-stage Docker | `Dockerfile.naive` vs. `Dockerfile`, image size comparison |
| `question-2` | Docker Compose + Redis caching | `docker-compose.yml`, cache hit/miss logic in `app.py`, benchmarked speedup |
| `question-3` | Kubernetes Indexed Job | Parallel validation of 8 CSV shards, `k8s-job.yaml`, results collected via the Kubernetes API |
| `question-4` | Kubernetes Deployment | Self-healing + zero-downtime rolling update, `k8s-deployment.yaml` |

Each folder contains its own code, Kubernetes/Docker manifests, and a
`QuestionN_Report.docx` with full command output, measured results, and
written answers to the discussion questions.

## Note on `app.py` across questions

`app.py` evolves across the assignment, per its single-application design:

- **question-1/app.py** — baseline: `/predict`, `/healthz`, no caching
- **question-2/app.py** — adds Redis caching (checks/writes cache before/after prediction)
- **question-4/app.py** — based on the question-1 baseline (no Redis), with an
  `APP_VERSION` string added to `/healthz` to demonstrate the question-4
  rolling update

Each folder's version is the one actually used to produce that question's
evidence and report.

## Environment

All Kubernetes work was run against a local `minikube` cluster (3 nodes:
1 control-plane + `minikube-m02` + `minikube-m03`); Docker Compose work was
run with Docker Desktop / a local Docker Engine. See each report for exact
commands and captured output.
