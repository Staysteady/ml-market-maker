# Market Maker System Monitoring Guide

## Overview
This guide covers the monitoring capabilities of the Market Maker System, including metrics collection, alerting, and troubleshooting procedures.

## Monitoring Architecture
```
┌─────────────────┐     ┌─────────────────┐
│  Model Server   │────▶│  Metrics Store  │
└─────────────────┘     └────────┬────────┘
                               ▼
┌─────────────────┐     ┌─────────────────┐
│    Grafana      │◀────│   Prometheus    │
└─────────────────┘     └────────┬────────┘
                               ▼
┌─────────────────┐     ┌─────────────────┐
│  Alert Manager  │◀────│  Alert Rules    │
└─────────────────┘     └─────────────────┘
```

## Key Metrics

### Performance Metrics
| Metric | Description | Warning Threshold | Critical Threshold |
|--------|-------------|-------------------|-------------------|
| prediction_latency_ms | Average prediction time | > 100ms | > 250ms |
| prediction_throughput | Predictions per second | < 10/s | < 5/s |
| error_rate | Failed predictions percentage | > 5% | > 10% |
| queue_utilization | Prediction queue usage | > 70% | > 90% |

### System Health Metrics
| Metric | Description | Warning Threshold | Critical Threshold |
|--------|-------------|-------------------|-------------------|
| memory_usage_mb | Memory usage in MB | > 75% | > 90% |
| cpu_usage_percent | CPU utilization | > 80% | > 95% |
| gpu_usage_percent | GPU utilization (if available) | > 80% | > 95% |
| disk_usage_percent | Storage utilization | > 80% | > 90% |

### Model Metrics
| Metric | Description | Warning Threshold | Critical Threshold |
|--------|-------------|-------------------|-------------------|
| prediction_accuracy | Model accuracy | < 85% | < 75% |
| spread_compliance | Spread within limits | < 90% | < 80% |
| model_drift | Prediction drift score | > 0.1 | > 0.2 |

## Monitoring Setup

### Prometheus Configuration
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'market_maker'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scheme: 'http'
```

### Grafana Dashboards
1. Main Overview Dashboard
   ```json
   {
     "dashboard": {
       "title": "Market Maker Overview",
       "panels": [
         {
           "title": "Prediction Latency",
           "type": "graph",
           "datasource": "Prometheus",
           "targets": [
             {
               "expr": "prediction_latency_ms"
             }
           ]
         }
       ]
     }
   }
   ```

### Alert Rules
```yaml
groups:
  - name: market_maker_alerts
    rules:
      - alert: HighLatency
        expr: prediction_latency_ms > 100
        for: 5m
        labels:
          severity: warning
      - alert: HighErrorRate
        expr: error_rate > 0.05
        for: 5m
        labels:
          severity: critical
```

## Monitoring Procedures

### Daily Checks
1. Review dashboard metrics
   ```bash
   # Check current metrics
   curl http://localhost:8000/metrics
   
   # View recent alerts
   curl http://localhost:8000/alerts
   ```

2. Verify system health
   ```bash
   # Check system status
   python scripts/health_check.py
   
   # View resource usage
   htop
   ```

3. Review logs
   ```bash
   # Check application logs
   tail -f /var/log/market-maker/app.log
   
   # Check error logs
   grep ERROR /var/log/market-maker/app.log
   ```

### Weekly Tasks
1. Review performance trends
2. Analyze error patterns
3. Update alert thresholds
4. Clean up old metrics

### Monthly Tasks
1. Performance analysis
2. Capacity planning
3. Alert rule review
4. Dashboard updates

## Alert Response Procedures

### High Latency Alert
1. Check system resources
   ```bash
   htop
   iostat
   ```

2. Review request volume
   ```sql
   SELECT COUNT(*), 
          date_trunc('minute', timestamp) as minute
   FROM predictions
   GROUP BY minute
   ORDER BY minute DESC
   LIMIT 10;
   ```

3. Check database performance
   ```sql
   SELECT * FROM pg_stat_activity;
   ```

### High Error Rate Alert
1. Check error logs
   ```bash
   tail -n 100 /var/log/market-maker/error.log
   ```

2. Verify data quality
   ```python
   python scripts/validate_data.py
   ```

3. Check model health
   ```bash
   python scripts/model_diagnostics.py
   ```

### Resource Constraints Alert
1. Identify resource pressure
   ```bash
   ps aux --sort=-%mem
   ps aux --sort=-%cpu
   ```

2. Check disk usage
   ```bash
   df -h
   du -sh /opt/market-maker/*
   ```

3. Review resource allocation
   ```bash
   cat /proc/meminfo
   nproc
   ```

## Performance Optimization

### Metric Collection
```python
# Optimize metric collection
metrics_config = {
    'collection_interval': 15,
    'batch_size': 100,
    'buffer_size': 1000
}
```

### Storage Optimization
```sql
-- Partition metrics table
CREATE TABLE metrics_partition (
    timestamp TIMESTAMP,
    metric_name TEXT,
    value FLOAT
) PARTITION BY RANGE (timestamp);

-- Create retention policy
CREATE OR REPLACE FUNCTION cleanup_old_metrics()
RETURNS void AS $$
BEGIN
    DELETE FROM metrics 
    WHERE timestamp < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;
```

### Alert Optimization
```yaml
# Alert aggregation
aggregation_rules:
  - name: prediction_errors
    window: 5m
    threshold: 10
    group_by: ['error_type']
```

## Troubleshooting Guide

### Metric Collection Issues
1. Check Prometheus connectivity
2. Verify metric endpoints
3. Review collection rates

### Dashboard Issues
1. Check Grafana logs
2. Verify data source
3. Review panel queries

### Alert Issues
1. Check alert manager
2. Verify alert rules
3. Test notification channels

## Best Practices

### Metric Collection
1. Use appropriate intervals
2. Implement buffering
3. Monitor collection overhead

### Alert Configuration
1. Set meaningful thresholds
2. Use proper time windows
3. Implement alert grouping

### Dashboard Organization
1. Group related metrics
2. Use clear visualizations
3. Include documentation 