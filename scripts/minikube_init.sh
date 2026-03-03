#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="bartender"
BACKEND_IMAGE="bartender-backend:local"
FRONTEND_IMAGE="bartender-frontend:local"

info() { echo "[INFO] $*"; }
ok() { echo "[OK]   $*"; }
warn() { echo "[WARN] $*"; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[ERROR] Required command not found: $1" >&2
    exit 1
  fi
}

require_cmd minikube
require_cmd kubectl
require_cmd docker

info "Checking minikube status..."
if ! minikube status >/dev/null 2>&1; then
  warn "minikube is not running. Starting minikube..."
  minikube start
else
  ok "minikube is already running."
fi

info "Building backend image into minikube: ${BACKEND_IMAGE}"
minikube image build -t "${BACKEND_IMAGE}" ./backend
ok "Backend image built"

info "Building frontend image into minikube: ${FRONTEND_IMAGE}"
minikube image build -t "${FRONTEND_IMAGE}" ./frontend
ok "Frontend image built"

info "Applying Kubernetes manifests"
kubectl apply -k k8s/
ok "Manifests applied"

info "Restarting backend/frontend/worker deployments to roll out latest local images"
kubectl -n "${NAMESPACE}" rollout restart deploy/backend deploy/frontend deploy/worker

info "Waiting for rollouts"
kubectl -n "${NAMESPACE}" rollout status statefulset/postgres --timeout=240s
kubectl -n "${NAMESPACE}" rollout status deploy/backend --timeout=240s
kubectl -n "${NAMESPACE}" rollout status deploy/frontend --timeout=240s
kubectl -n "${NAMESPACE}" rollout status deploy/worker --timeout=240s
kubectl -n "${NAMESPACE}" rollout status deploy/prometheus --timeout=240s
kubectl -n "${NAMESPACE}" rollout status deploy/grafana --timeout=240s
kubectl -n "${NAMESPACE}" rollout status deploy/traffic-generator --timeout=240s

IP="$(minikube ip)"

ok "Deployment successful 🎉"
echo
echo "Frontend:   http://${IP}:30000"
echo "Backend:    http://${IP}:30001"
echo "Prometheus: http://${IP}:30090"
echo "Grafana:    http://${IP}:30300"
echo
echo "✅ Everything deployed successfully."
