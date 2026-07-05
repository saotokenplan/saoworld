# telemetry/ - Metrics, Logging & Observability

Definitions for metrics, log schemas, alerting rules, and dashboard configurations.

## Directory Structure

```
telemetry/
├── metrics/           # Metrics definitions
│   └── metrics.yaml   # All service metrics definitions
├── logs/              # Log schemas
│   └── log-schemas.yaml  # Structured log format definitions
├── alerts/            # Alerting rules
│   └── alerts.yaml    # Prometheus alert rules
└── dashboards/        # Dashboard configurations
    └── README.md      # Dashboard documentation
```

## Metrics

Metrics are defined in `metrics/metrics.yaml` using a structured YAML format. Each metric includes:
- `type`: counter, gauge, histogram, or summary
- `description`: Human-readable description
- `labels`: Key-value pairs for dimensional analysis
- `buckets`: For histograms, defines bucket boundaries

### Service Metrics

- **Service-level**: HTTP requests, duration, errors, connections
- **vote-service**: Vote submissions, cycle transitions, cycle/candidate counts by status
- **world-service**: Region operations, transitions, region counts by status
- **content-service**: Package operations, releases, rollbacks, package counts by status
- **generation-service**: Generation requests, generated objects, request counts by status
- **review-service**: Reviews, operations, review counts by risk level
- **gateway-service**: Proxy requests, rate limits, auth failures
- **player-service**: Player counts, operations, quest counts by status
- **ops-service**: Operations actions, dashboard views
- **workers**: Task executions, durations, retries
- **event-bus**: Events published/consumed, processing duration

## Log Schemas

Log schemas are defined in `logs/log-schemas.yaml`. The following log types are supported:

| Log Type | Description |
|----------|-------------|
| `request_log` | HTTP request/response logging |
| `business_log` | Business operation logging |
| `audit_log` | Audit trail logging |
| `error_log` | Error logging |
| `task_log` | Celery task logging |
| `event_log` | Event bus logging |
| `database_log` | Database query logging |
| `security_log` | Security event logging |
| `health_check_log` | Health check logging |

All logs extend `base_fields` which includes:
- `timestamp`, `level`, `service`, `request_id`, `trace_id`, `message`, `event`

## Alerts

Alerts are defined in `alerts/alerts.yaml` using Prometheus-compatible rule formats. Alert severity levels:

| Severity | Description | Response Time |
|----------|-------------|---------------|
| `critical` | Immediate action required | Immediate |
| `high` | Significant degradation | 15 minutes |
| `medium` | Potential issue | Investigation recommended |
| `low` | Informational | Monitoring only |

### Alert Categories

- **Service Health**: Service availability, degradation
- **HTTP Errors**: Error rates, rate limits
- **Latency**: P95/P99 latency thresholds
- **Database**: Connection errors, slow queries
- **Business Metrics**: Vote submissions, rollback rates, generation failures
- **Tasks**: Task failure/retry rates, long-running tasks
- **Event Bus**: Event production/consumption issues
- **Security**: Auth failures, suspicious activity
- **Resources**: CPU, memory, disk space

## Dashboards

Dashboard configurations are managed in the `dashboards/` directory. See `dashboards/README.md` for details.

## Usage

### Prometheus Configuration

Metrics are exposed at `/metrics` endpoint on each service. Configure Prometheus to scrape these endpoints:

```yaml
scrape_configs:
  - job_name: 'vote-service'
    static_configs:
      - targets: ['vote-service:8000']
  - job_name: 'world-service'
    static_configs:
      - targets: ['world-service:8001']
  - job_name: 'content-service'
    static_configs:
      - targets: ['content-service:8002']
  - job_name: 'generation-service'
    static_configs:
      - targets: ['generation-service:8003']
  - job_name: 'review-service'
    static_configs:
      - targets: ['review-service:8004']
  - job_name: 'gateway-service'
    static_configs:
      - targets: ['gateway-service:8005']
  - job_name: 'player-service'
    static_configs:
      - targets: ['player-service:8006']
  - job_name: 'ops-service'
    static_configs:
      - targets: ['ops-service:8007']
```

### Alertmanager Configuration

Import alerts from `alerts/alerts.yaml` into Prometheus Alertmanager for notification routing.

## Versioning

All files in this directory follow semantic versioning. The `version` field in each YAML file indicates the current schema version.

## Related Resources

- Grafana dashboards: `infra/grafana/dashboards/`
- Prometheus configuration: `infra/prometheus/prometheus.yml`
- Application metrics implementation: `services/*/app/core/metrics.py`