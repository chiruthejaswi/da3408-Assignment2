"""
Runs inside a single pod of the Kubernetes Indexed Job. Validates exactly
ONE shard, determined by the JOB_COMPLETION_INDEX environment variable,
which Kubernetes automatically injects into every pod of an Indexed Job
(completionMode: Indexed) -- no manual index-passing needed.

Reports the invalid-row count as a structured log line on stdout, which is
how results are collected (via `kubectl logs` / the Kubernetes API), rather
than via a shared volume -- see collect_results.py and the write-up for why.
"""
import csv
import os
import re
import sys
import time

REQUIRED_FIELDS = ["name", "email", "signup_date"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SHARD_DIR = os.environ.get("SHARD_DIR", "/shards")


def is_row_invalid(row: dict) -> bool:
    for field in REQUIRED_FIELDS:
        if not row.get(field, "").strip():
            return True
    email = row["email"]
    if email != email.strip():
        return True  # stray leading/trailing whitespace
    if not EMAIL_RE.match(email):
        return True
    return False


def main():
    index = os.environ.get("JOB_COMPLETION_INDEX")
    if index is None:
        print("ERROR: JOB_COMPLETION_INDEX not set -- this must run as part "
              "of an Indexed Job (completionMode: Indexed).", file=sys.stderr)
        sys.exit(1)
    index = int(index)

    # Downward API fields -- identify which pod, on which node, did this work.
    pod_name = os.environ.get("POD_NAME", "unknown-pod")
    node_name = os.environ.get("NODE_NAME", "unknown-node")
    namespace = os.environ.get("POD_NAMESPACE", "unknown-namespace")

    shard_path = os.path.join(SHARD_DIR, f"shard_{index}.csv")

    # Artificial delay -- simulates real validation work taking noticeable
    # time, so that `kubectl get pods -o wide` can catch multiple pods in
    # the Running state AT THE SAME INSTANT. Without this, validation of a
    # small CSV finishes in well under a second, and a kubectl snapshot
    # can't distinguish true concurrency from very fast sequential runs.
    print(f"Starting validation of shard {index} (simulated workload: 20s)...", flush=True)
    time.sleep(20)

    total_rows = 0
    invalid_rows = 0
    with open(shard_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            if is_row_invalid(row):
                invalid_rows += 1

    # One structured line per pod -- easy to grep/parse when collecting
    # results from many pods' logs.
    print(f"RESULT shard_index={index} shard_file={shard_path} "
          f"total_rows={total_rows} invalid_rows={invalid_rows} "
          f"pod={pod_name} node={node_name} namespace={namespace}")


if __name__ == "__main__":
    main()
