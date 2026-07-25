# dashboards/ - Grafana Dashboard Configurations

This directory contains Grafana dashboard configurations for the game project's observability stack.

## Available Dashboards

| Dashboard | File | Description |
|-----------|------|-------------|
| Game Dashboard | `game-dashboard.json` | Overall system overview with HTTP metrics and business metrics |
| Review Efficiency Dashboard | `review-efficiency-dashboard.json` | WP3 审核效率看板：自动通过率/耗时 P95/人工介入率/积压量 + 规则归因与安全护栏 |

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

**Review Efficiency Dashboard** (WP3)
- L1 核心 KPI：自动审核通过率 (K1)、审核耗时 P95 (K2)、人工介入率 (K3)、审核积压量 (A4)
- L2 趋势：通过率/人工介入率趋势、审核结果分布趋势（按 result）
- L3 耗时分布：耗时 P50/P95（by review_type）、耗时热力图
- L4 规则归因：各规则判定分布（by rule×result，A3）、安全误放护栏（A1）

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