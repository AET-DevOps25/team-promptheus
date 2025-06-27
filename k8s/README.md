# Team Promptheus Helm Chart

This Helm chart deploys the Team Promptheus application stack on Kubernetes, including all microservices, PostgreSQL database, MeiliSearch, and monitoring components.

## Prerequisites

- Kubernetes 1.21+
- Helm 3.8+
- kubectl configured to access your cluster

### 1. Install Dependencies

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm install prometheus-operator prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
```

### 2. Install Team Promptheus

#### Development Installation

```bash
helm install team-promptheus ./k8s \
  --namespace team-promptheus \
  --create-namespace \
  --values ./k8s/values-dev.yaml
```

#### Production Installation

```bash
helm install team-promptheus ./k8s \
  --namespace team-promptheus \
  --create-namespace \
  --set secrets.postgresPassword="your-secure-password" \
  --set secrets.meiliMasterKey="your-super-super-secure-key"
```
