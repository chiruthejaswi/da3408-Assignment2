"""
Collects each pod's RESULT line via the Kubernetes API (pod log retrieval),
NOT a shared volume.

Why not a shared volume: minikube's default StorageClass ("standard") is
backed by the hostPath / local-path provisioner, which allocates storage on
whichever single node the volume's first consumer pod happens to land on.
It is not a real network filesystem, so it does not reliably support
ReadWriteMany across pods scheduled on DIFFERENT nodes -- and with
parallelism: 4 across a 2-node cluster, this Job's pods are expected to be
spread across both nodes. A pod on node B writing to a hostPath volume
provisioned on node A would not be visible to a pod on node A (and vice
versa) without extra infrastructure (e.g. an NFS provisioner), which is out
of scope for this exercise. Reading logs via the Kubernetes API instead
works uniformly regardless of which node a pod ran on, since the API server
retrieves each pod's log through its kubelet, not through shared disk.

Usage:
    pip install kubernetes
    python3 collect_results.py [--namespace default] [--job-name signup-validation]
"""
import argparse
import re
import sys

from kubernetes import client, config

RESULT_RE = re.compile(
    r"RESULT shard_index=(\d+) shard_file=\S+ total_rows=(\d+) invalid_rows=(\d+) "
    r"pod=(\S+) node=(\S+) namespace=(\S+)"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", default="default")
    parser.add_argument("--job-name", default="signup-validation")
    args = parser.parse_args()

    # Works both from your machine (via ~/.kube/config, e.g. after
    # `minikube start`) and from inside a pod (via in-cluster config).
    try:
        config.load_kube_config()
    except Exception:
        config.load_incluster_config()

    v1 = client.CoreV1Api()

    pods = v1.list_namespaced_pod(
        namespace=args.namespace,
        label_selector=f"job-name={args.job_name}",
    )

    if not pods.items:
        print(f"No pods found for job '{args.job_name}' in namespace "
              f"'{args.namespace}'. Has the Job been applied and started?",
              file=sys.stderr)
        sys.exit(1)

    results = {}
    for pod in pods.items:
        pod_name = pod.metadata.name
        try:
            log = v1.read_namespaced_pod_log(name=pod_name, namespace=args.namespace)
        except client.exceptions.ApiException as e:
            print(f"WARNING: could not read logs for pod {pod_name}: {e}", file=sys.stderr)
            continue

        match = RESULT_RE.search(log)
        if not match:
            print(f"WARNING: no RESULT line found yet in logs for pod {pod_name} "
                  f"(it may still be running).", file=sys.stderr)
            continue

        shard_index, total_rows, invalid_rows, reported_pod, node, namespace = match.groups()
        results[int(shard_index)] = {
            "pod": reported_pod,
            "node": node,
            "total_rows": int(total_rows),
            "invalid_rows": int(invalid_rows),
        }

    print(f"{'shard':>5} {'pod':<22} {'node':<20} {'total_rows':>10} {'invalid_rows':>13}")
    total_invalid = 0
    total_rows_sum = 0
    for idx in sorted(results):
        r = results[idx]
        print(f"{idx:>5} {r['pod']:<22} {r['node']:<20} {r['total_rows']:>10} {r['invalid_rows']:>13}")
        total_invalid += r["invalid_rows"]
        total_rows_sum += r["total_rows"]

    print(f"\nCollected {len(results)}/8 shard results via the Kubernetes API (pod logs).")
    print(f"Total rows validated: {total_rows_sum}")
    print(f"Total invalid rows found: {total_invalid}")


if __name__ == "__main__":
    main()
