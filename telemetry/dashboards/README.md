# dashboards/ - Grafana Dashboard Configurations

This directory contains Grafana dashboard configurations for the game project's observability stack.

## Available Dashboards

| Dashboard | File | Description |
|-----------|------|-------------|
| Game Dashboard | `game-dashboard.json` | Overall system overview with HTTP metrics and business metrics |

## Dashboard Structure

### Game Dashboard

The main dashboard includes the following panels:

**Service Health**
- Service status grid (all 8 services)
- Active connections per service
- Health check latency

**HTTP Metrics**
- Total requests per service
- Request rate (QPS)
- Error rate per service
- P95/P99 latency per service

**Vote Service**
- Vote submissions per hour
- Vote cycle transitions
- Vote cycles by status
- Vote candidates by status

**Content Service**
- Content package operations
- Releases and rollbacks
- Packages by status

**Generation Service**
- Generation requests
- Generated objects by type
- Generation success rate

**Review Service**
- Review records by result
- Review operations
- Reviews by risk level

**Player Service**
- Total players
- Player operations
- Player quests by status

**Event Bus**
- Events published/consumed
- Event processing latency

**Workers**
- Task executions
- Task failure rate
- Task retry rate

## Adding New Dashboards

1. Create the dashboard in Grafana
2. Export as JSON
3. Save to this directory with a descriptive name
4. Update this README with the new dashboard details

## Versioning

Dashboards follow semantic versioning. Include version information in the dashboard title.

## Related Resources

- Prometheus configuration: `infra/prometheus/prometheus.yml`
- Grafana provisioning: `infra/grafana/provisioning/`
- Metrics definitions: `telemetry/metrics/metrics.yaml`