# Market Maker System Deployment Guide

## Overview
This guide covers the deployment process for the Market Maker System, including setup, configuration, and maintenance procedures.

## System Architecture
```
┌─────────────────┐     ┌─────────────────┐
│  Excel Reader   │────▶│  Data Capture   │
└─────────────────┘     └────────┬────────┘
                               ▼
┌─────────────────┐     ┌─────────────────┐
│  Model Server   │◀────│    Database     │
└────────┬────────┘     └─────────────────┘
         ▼
┌─────────────────┐     ┌─────────────────┐
│     API         │◀────│    Monitor      │
└─────────────────┘     └─────────────────┘
```

## Prerequisites
- Linux server (Ubuntu 20.04 LTS recommended)
- Python 3.8+
- PostgreSQL 12+
- NVIDIA GPU (optional)
- 8GB RAM minimum
- 4 CPU cores minimum

## Installation Steps

### 1. System Preparation
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade

# Install dependencies
sudo apt-get install python3.8 python3-pip postgresql-12 nginx
```

### 2. Database Setup
```bash
# Create database
sudo -u postgres createdb market_maker

# Initialize schema
python scripts/init_db.py
```

### 3. Application Setup
```bash
# Create application user
sudo useradd -m -s /bin/bash market_maker

# Clone repository
git clone https://github.com/your-org/market-maker.git
cd market_maker

# Install dependencies
pip install -r requirements.txt

# Copy configuration
cp config/config.example.yaml config/config.yaml
```

### 4. Configuration
Edit `config/config.yaml`:
```yaml
database:
  host: localhost
  port: 5432
  name: market_maker
  user: market_maker
  password: <secure-password>

model:
  base_dir: /opt/market-maker/models
  max_versions: 10

monitoring:
  metrics_window_minutes: 60
  alert_window_hours: 24
```

### 5. Service Setup
Create systemd service file:
```ini
[Unit]
Description=Market Maker System
After=network.target postgresql.service

[Service]
User=market_maker
WorkingDirectory=/opt/market-maker
ExecStart=/usr/bin/python3 scripts/start_system.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 6. Monitoring Setup
```bash
# Install monitoring tools
pip install prometheus_client grafana-client

# Configure Prometheus
cp config/prometheus.yml /etc/prometheus/

# Start monitoring
systemctl start prometheus grafana-server
```

## Deployment Process

### 1. Initial Deployment
```bash
# Stop service
sudo systemctl stop market-maker

# Deploy code
git pull origin main

# Apply migrations
python scripts/migrate.py

# Start service
sudo systemctl start market-maker
```

### 2. Model Deployment
```bash
# Deploy new model
python scripts/deploy_model.py --version v1.0.0

# Verify deployment
python scripts/verify_deployment.py
```

### 3. Rollback Procedure
```bash
# Rollback to previous version
python scripts/rollback.py

# Verify rollback
python scripts/verify_deployment.py
```

## Maintenance

### Backup Procedures
```bash
# Backup database
pg_dump market_maker > backup.sql

# Backup models
tar -czf models_backup.tar.gz /opt/market-maker/models/
```

### Log Management
```bash
# Configure log rotation
cp config/logrotate.conf /etc/logrotate.d/market-maker

# View logs
journalctl -u market-maker
```

### Health Checks
```bash
# Check system health
python scripts/health_check.py

# Monitor resources
htop
nvidia-smi  # if GPU enabled
```

## Security Considerations

### Network Security
- Configure firewall rules
- Use SSL/TLS for API
- Implement rate limiting

### Access Control
- Use role-based access
- Implement audit logging
- Regular security updates

### Data Protection
- Encrypt sensitive data
- Regular backups
- Secure file permissions

## Troubleshooting

### Common Issues
1. Database connection failures
2. Model loading errors
3. Resource constraints

### Debug Procedures
1. Check logs
2. Verify configurations
3. Test connectivity
4. Monitor resources

## Performance Tuning

### Database Optimization
```sql
-- Optimize queries
CREATE INDEX idx_predictions ON predictions(timestamp);
VACUUM ANALYZE;
```

### Application Settings
```yaml
# Performance tuning
queue_size: 1000
worker_threads: 4
batch_size: 32
```

### Resource Allocation
- Adjust memory limits
- Configure CPU affinity
- Optimize GPU usage 