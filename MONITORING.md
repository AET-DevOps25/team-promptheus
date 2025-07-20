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
- Tempo (traces) - if available
- Pyroscope (profiling) - if available

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

## Monitoring Your Applications

### Go Applications

```go
import (
    "github.com/prometheus/client_golang/prometheus/promhttp"
    "net/http"
)

// Expose metrics endpoint
http.Handle("/metrics", promhttp.Handler())
```

### Node.js Applications

```javascript
const prometheus = require('prom-client');

// Create a Registry to register the metrics
const register = new prometheus.Registry();

// Add a default label which is added to all metrics
register.setDefaultLabels({
  app: 'team-promptheus-app'
});

// Enable the collection of default metrics
prometheus.collectDefaultMetrics({ register });

// Expose metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});
```

### Python Applications

```python
from prometheus_client import start_http_server, Counter, generate_latest

# Start metrics server
start_http_server(8080)

# Or for Flask/FastAPI
from flask import Flask, Response
app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')
```

## Troubleshooting

### Check Component Status

```bash
# Check Helm deployment
helm status team-promptheus -n team-promptheus

# Check all monitoring pods
kubectl get pods -n team-promptheus | grep -E "(grafana|prometheus|loki|otel)"

# Check services
kubectl get services -n team-promptheus | grep -E "(grafana|prometheus|loki|otel)"

# Check ingresses
kubectl get ingresses -n team-promptheus
```

### Check Logs

```bash
# Using the deployment script
./deploy-with-monitoring.sh team-promptheus team-prompteus.local secret key logs grafana
./deploy-with-monitoring.sh team-promptheus team-prompteus.local secret key logs loki

# Or directly with kubectl
kubectl logs -l app=grafana -f -n team-promptheus
kubectl logs -l app=prometheus -f -n team-promptheus
kubectl logs -l app=loki -f -n team-promptheus
kubectl logs -l app=otel-collector -f -n team-promptheus
```

### Common Issues

#### Grafana Not Loading Dashboards

1. Check if ConfigMaps exist:
```bash
kubectl get configmap grafana-datasources grafana-dashboards-config grafana-dashboards-files -n team-promptheus
```

2. Verify ConfigMap content:
```bash
kubectl describe configmap grafana-dashboards-config -n team-promptheus
```

3. Restart Grafana:
```bash
kubectl rollout restart deployment/grafana -n team-promptheus
```

#### Prometheus Not Scraping Targets

1. Check Prometheus targets page: https://team-prompteus.local/prometheus/targets
2. Verify ServiceMonitor resources
3. Check if services are in the same namespace
4. Review Prometheus Operator configuration

#### Loki Not Receiving Logs

1. Check OTEL Collector configuration
2. Verify application is sending logs to correct endpoint
3. Check Loki logs for errors
4. Test with manual log ingestion

## Cleanup

```bash
# Remove complete application including monitoring
helm uninstall team-promptheus -n team-promptheus

# Or use the deployment script
./deploy-with-monitoring.sh team-promptheus team-prompteus.local secret key uninstall
```

## Deployment Commands

### Standard Deployment
```bash
helm install team-promptheus ./k8s \
  --namespace team-promptheus \
  --create-namespace \
  --set secrets.postgresPassword="your-secure-password" \
  --set secrets.meiliMasterKey="your-super-super-secure-key" \
  --set ingress.domain="team-prompteus.local"
```

### Using the Deployment Script
```bash
# Deploy with defaults
./deploy-with-monitoring.sh

# Deploy with custom settings
./deploy-with-monitoring.sh prod example.com secure-password secret-key

# Check status
./deploy-with-monitoring.sh team-promptheus team-prompteus.local password key status

# Upgrade
./deploy-with-monitoring.sh team-promptheus team-prompteus.local password key upgrade
```

## Security Considerations

- **Default passwords**: Change Grafana admin password in production
- **Network policies**: Consider implementing network policies to restrict access
- **RBAC**: Prometheus ServiceAccount has cluster-wide read access for service discovery
- **TLS**: Enable TLS for production deployments
- **Authentication**: Configure proper authentication for Grafana in production

## Scaling

For production environments, consider:

- **Persistent storage** for Prometheus, Loki, and Grafana data
- **High availability** deployments with multiple replicas
- **Resource limits** and requests tuning
- **External storage** backends (S3, GCS, etc.) for Loki
- **Grafana clustering** for high availability
- **Prometheus federation** or Thanos for long-term storage

Enable persistence in `values.yaml`:
```yaml
monitoring:
  grafana:
    persistence:
      enabled: true
      size: "10Gi"
  loki:
    persistence:
      enabled: true
      size: "50Gi"
```

## Support

For issues with this monitoring stack:

1. Check the troubleshooting section above
2. Review component logs using `./deploy-with-monitoring.sh ... logs <component>`
3. Use the deployment script status command: `./deploy-with-monitoring.sh ... status`
4. Check Helm deployment: `helm status team-promptheus -n team-promptheus`
5. Consult individual component documentation:
   - [Grafana Documentation](https://grafana.com/docs/)
   - [Prometheus Operator Documentation](https://prometheus-operator.dev/)
   - [Loki Documentation](https://grafana.com/docs/loki/)
   - [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
