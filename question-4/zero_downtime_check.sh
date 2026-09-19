#!/usr/bin/env bash
# Run this in a SEPARATE terminal, started BEFORE you trigger the rolling
# update, and left running through it. It hits the Service (not a pod
# directly) once per second and logs the HTTP status + reported version.
#
# Usage:
#   kubectl port-forward svc/spam-api-service 8080:80 &
#   ./zero_downtime_check.sh
#
# While this is running, in another terminal do the rolling update:
#   kubectl set image deployment/spam-api-deployment spam-api=spam-api:v2
#   kubectl rollout status deployment/spam-api-deployment
#
# A successful zero-downtime rollout looks like: every line shows HTTP 200,
# and partway through the "version" field flips from v1 to v2 with no gap.

echo "time                 http_status  version"
while true; do
  ts=$(date +"%Y-%m-%d %H:%M:%S")
  body=$(curl -s -o /tmp/healthz_body.json -w "%{http_code}" http://localhost:8080/healthz)
  version=$(python3 -c "import json;print(json.load(open('/tmp/healthz_body.json')).get('version','?'))" 2>/dev/null || echo "ERR")
  echo "$ts   $body          $version"
  sleep 1
done
