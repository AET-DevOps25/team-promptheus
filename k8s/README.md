# Kubernetes Deployment Instructions

## Prerequisites

We require a [prometheus operator](https://github.com/prometheus-operator/kube-prometheus) to be installed

```bash
git clone https://github.com/prometheus-operator/kube-prometheus.git
cd kube-prometheus
kubectl create -f manifests/setup
until kubectl get servicemonitors --all-namespaces ; do date; sleep 1; echo ""; done
kubectl create -f manifests/
```

## Installation

Then we can apply our own configuration

```bash
sudo k3s kubectl apply -f k8s -R
```
