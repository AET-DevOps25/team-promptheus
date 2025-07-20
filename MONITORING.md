# Team Promptheus Monitoring Stack

This document describes the simplified monitoring stack for Team Promptheus, which replaces the previous `grafana/otel-lgtm` container with separate, dedicated components.

## Overview

The monitoring stack consists of:

- **Grafana** - Visualization and dashboarding
- **Prometheus** - Metrics collection and storage
- **Loki** - Log aggregation and storage
- **OpenTelemetry Collector** - Telemetry data collection and routing

### Access Services Locally

```bash
# Grafana (admin/admin)
kubectl port-forward service/grafana-service 3000:3000 -n default
# Open: http://localhost:3000

# Prometheus
kubectl port-forward service/prometheus-service 9090:9090 -n default
# Open: http://localhost:9090

# Loki
kubectl port-forward service/loki-service 3100:3100 -n default
# Open: http://localhost:3100
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│ OTEL Collector  │───▶│   Prometheus    │
│                 │    │                 │    │  (Operator)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │      Loki       │    │    Grafana      │
                       │     (Logs)      │◀───│ (Visualization) │
                       └─────────────────┘    └─────────────────┘
```

## Components

### Grafana

- **Image**: `grafana/grafana:latest`
- **Port**: 3000
- **Ingress**: https://grafana-{domain}
- **Credentials**: admin/admin (configurable)
- **Configuration**: Datasources and dashboards are provisioned via ConfigMaps

#### Pre-configured Datasources:
- Prometheus (metrics from Prometheus Operator)
- Loki (logs)
- Tempo (traces)
- Pyroscope (profiling)

### Prometheus (via Prometheus Operator)

- **Managed by**: Prometheus Operator
- **Port**: 9090
- **Ingress**: https://{domain}/prometheus
- **Storage**: Configurable retention (default 7d)
- **Configuration**: Uses ServiceMonitors for auto-discovery

#### Service Discovery:
Prometheus automatically discovers services through ServiceMonitors. For manual scraping, add these annotations:
```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
```

### Loki

- **Image**: `grafana/loki:latest`
- **Port**: 3100
- **Ingress**: https://loki-{domain}
- **Storage**: Local filesystem (ephemeral, configurable for persistence)
- **Configuration**: Single-tenant mode with basic retention

### OpenTelemetry Collector

- **Image**: `otel/opentelemetry-collector-contrib:latest`
- **Ports**:
  - 4317 (OTLP gRPC)
  - 4318 (OTLP HTTP)
  - 8889 (Prometheus metrics export)
- **Function**: Collects and routes telemetry data to appropriate backends

## Application Integration

### Metrics (Prometheus)

Add annotations to your Kubernetes service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: your-app-service
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  # ... rest of service definition
```

### Logs (via OTEL Collector → Loki)

Configure your application to send logs to the OTEL Collector:

```bash
# Environment variables for your application
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector-service:4318
OTEL_SERVICE_NAME=your-service-name
OTEL_RESOURCE_ATTRIBUTES=service.version=1.0.0
```

### Traces (via OTEL Collector → Jaeger)

Send traces to the OTEL Collector:

- **HTTP**: `http://otel-collector-service:4318/v1/traces`
- **gRPC**: `otel-collector-service:4317`

## Configuration

### Helm Values Configuration

Configure monitoring components via `k8s/values.yaml`:

```yaml
monitoring:
  grafana:
    enabled: true
    adminPassword: "admin"
    persistence:
      enabled: false
      size: "1Gi"

  loki:
    enabled: true
    persistence:
      enabled: false
      size: "5Gi"

  otelCollector:
    enabled: true
```

### Custom Datasources

Edit `k8s/templates/monitoring/grafana.yml` and modify the `grafana-datasources` ConfigMap:

```yaml
data:
  datasources.yaml: |
    apiVersion: 1
    datasources:
      - name: MyCustomPrometheus
        type: prometheus
        url: http://my-prometheus:9090
        # ... other configuration
```

### Custom Dashboards

1. Export your dashboard JSON from Grafana UI
2. Add it to the `grafana-dashboards-files` ConfigMap in `k8s/templates/monitoring/grafana.yml`
3. Place dashboard files in `k8s/files/dashboards/`

### Prometheus ServiceMonitors

Create ServiceMonitor resources for automatic discovery:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-application
spec:
  selector:
    matchLabels:
      app: my-application
  endpoints:
  - port: metrics
    path: /metrics
```
