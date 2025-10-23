# Better Business Builder - Production Deployment Guide

**Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved.**

**Version:** 1.0.0
**Last Updated:** October 23, 2025
**Status:** Production Ready

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Initialization](#database-initialization)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment-optional)
6. [Monitoring & Logging](#monitoring--logging)
7. [Backup & Disaster Recovery](#backup--disaster-recovery)
8. [Security Hardening](#security-hardening)
9. [Performance Tuning](#performance-tuning)
10. [Troubleshooting](#troubleshooting)
11. [Scaling Guide](#scaling-guide)

---

## Pre-Deployment Checklist

### ✅ Technical Requirements
- [ ] Python 3.9+ installed and tested
- [ ] Docker 24.0+ and Docker Compose 2.0+ installed
- [ ] PostgreSQL 14+ installed or Docker image ready
- [ ] Redis 7+ installed or Docker image ready
- [ ] SSL/TLS certificates obtained (Let's Encrypt or your provider)
- [ ] Domain name configured with DNS records
- [ ] Load balancer configured (Nginx, HAProxy, or cloud provider)

### ✅ Security Requirements
- [ ] All secrets changed from defaults (.env.production)
- [ ] SSH keys generated for deployment
- [ ] Firewall rules configured
- [ ] API rate limiting configured
- [ ] CORS origins configured for your domain
- [ ] Database backups tested
- [ ] SSL certificates installed and verified

### ✅ Dependencies & Libraries
- [ ] Run: `pip install -e .` to install package
- [ ] Run: `pip install -r requirements-prod.txt` for production deps
- [ ] Verify all imports work: `python -c "from bbb import *"`
- [ ] Run security audit: `pip-audit`

### ✅ Testing
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Run security tests: `pytest tests/test_security_owasp.py -v`
- [ ] Performance tests: `pytest tests/performance/ -v`
- [ ] Load testing: `locust -f tests/load_tests.py`

### ✅ Configuration
- [ ] Database URL configured correctly
- [ ] Redis URL configured correctly
- [ ] Email SMTP settings configured
- [ ] Stripe API keys configured (if using payments)
- [ ] Sentry DSN configured (if using error tracking)
- [ ] Logging level set appropriately

---

## Environment Setup

### 1. Create Production Environment

```bash
# Clone repository (if using GitHub)
git clone https://github.com/yourusername/blank-business-builder.git
cd blank-business-builder

# Or use local repository
cd /Users/noone/Blank_Business_Builder\ \(aka\ BBB\)

# Create virtual environment
python3 -m venv venv_prod
source venv_prod/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -e .
pip install -r requirements-prod.txt
```

### 2. Configure Environment Variables

```bash
# Copy production environment file
cp .env.example .env.production

# Edit with your settings
nano .env.production

# Critical variables to update:
# - SECRET_KEY (use: openssl rand -hex 32)
# - DATABASE_URL (PostgreSQL connection string)
# - REDIS_URL (Redis connection string)
# - STRIPE_SECRET_KEY / STRIPE_PUBLIC_KEY
# - SMTP_PASSWORD (email app password)
# - CORS_ORIGINS (your domain)
```

### 3. Generate Secure Keys

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate database password
openssl rand -base64 32

# Generate Redis password
openssl rand -base64 24
```

### 4. Verify Configuration

```bash
# Test imports
python -c "from bbb.main import app; print('✅ App imports successfully')"

# Test database connection
python -c "from bbb.database import engine; engine.connect(); print('✅ Database connected')"

# Test Redis connection
python -c "import redis; redis.from_url('redis://localhost:6379').ping(); print('✅ Redis connected')"
```

---

## Database Initialization

### 1. Create Database

```bash
# Option A: Using PostgreSQL CLI
psql -U postgres -c "CREATE DATABASE bbb_production OWNER bbb_user;"

# Option B: Using Docker
docker run --rm -e POSTGRES_USER=bbb_user -e POSTGRES_PASSWORD=your_password postgres psql -h localhost -U postgres -c "CREATE DATABASE bbb_production OWNER bbb_user;"
```

### 2. Run Migrations

```bash
# Initialize Alembic (if not already done)
alembic init -t async ./alembic

# Generate migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Verify migrations
alembic current
alembic history
```

### 3. Create Initial Data

```bash
# Create admin user
python -c "from bbb.database import create_admin; create_admin(email='admin@yourdomain.com', password='secure_password')"

# Seed initial data (optional)
python scripts/seed_data.py
```

### 4. Database Backup

```bash
# Create backup
pg_dump -U bbb_user -d bbb_production -F custom -f /backups/bbb_$(date +%Y%m%d_%H%M%S).dump

# Verify backup
pg_restore --list /backups/bbb_latest.dump
```

---

## Docker Deployment

### 1. Build Docker Image

```bash
# Build production image
docker build -f Dockerfile.production -t bbb:latest .

# Tag for registry
docker tag bbb:latest yourdockerhub/bbb:latest
docker tag bbb:latest yourdockerhub/bbb:1.0.0

# Push to registry (optional)
docker push yourdockerhub/bbb:latest
```

### 2. Deploy with Docker Compose

```bash
# Copy environment file
cp .env.production .env

# Create necessary directories
mkdir -p logs uploads backups
mkdir -p monitoring/{grafana-dashboards,grafana-datasources}

# Start services
docker-compose -f docker-compose.production.yml up -d

# Verify services
docker-compose -f docker-compose.production.yml ps
docker-compose -f docker-compose.production.yml logs api

# Run migrations in container
docker-compose -f docker-compose.production.yml exec api alembic upgrade head
```

### 3. Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check API endpoints
curl http://localhost:8000/docs

# Check metrics
curl http://localhost:8000/metrics

# Check Flower (Celery monitoring)
open http://localhost:5555

# Check Grafana
open http://localhost:3000
```

---

## Kubernetes Deployment (Optional)

### 1. Create Kubernetes Manifests

```bash
# Create namespace
kubectl create namespace bbb-production

# Create secrets from .env.production
kubectl create secret generic bbb-secrets \
  --from-env-file=.env.production \
  -n bbb-production

# Create ConfigMap
kubectl create configmap bbb-config \
  --from-literal=ENVIRONMENT=production \
  -n bbb-production
```

### 2. Deploy Services

```bash
# Deploy database
kubectl apply -f k8s/postgres-deployment.yaml -n bbb-production

# Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml -n bbb-production

# Deploy API
kubectl apply -f k8s/api-deployment.yaml -n bbb-production

# Deploy Celery Worker
kubectl apply -f k8s/celery-worker-deployment.yaml -n bbb-production

# Deploy Monitoring
kubectl apply -f k8s/prometheus-deployment.yaml -n bbb-production
kubectl apply -f k8s/grafana-deployment.yaml -n bbb-production
```

### 3. Verify Kubernetes Deployment

```bash
# Check pods
kubectl get pods -n bbb-production

# Check services
kubectl get svc -n bbb-production

# Check logs
kubectl logs -f deployment/bbb-api -n bbb-production

# Port forward for testing
kubectl port-forward svc/bbb-api 8000:8000 -n bbb-production
```

---

## Monitoring & Logging

### 1. Access Monitoring Dashboards

```bash
# Prometheus
open http://localhost:9090

# Grafana (default: admin/admin)
open http://localhost:3000

# Flower (Celery monitoring)
open http://localhost:5555
```

### 2. Configure Sentry for Error Tracking

```bash
# Create Sentry project
# https://sentry.io/signup/

# Add DSN to .env.production
SENTRY_DSN=https://your-sentry-dsn@sentry.io/123456

# Test Sentry integration
python -c "from bbb.monitoring import test_sentry; test_sentry()"
```

### 3. Configure Log Aggregation

```bash
# Option A: Using ELK Stack
# Configure Filebeat to collect logs:
# /var/log/bbb/app.log -> Elasticsearch -> Kibana

# Option B: Using Datadog
# Install Datadog Agent and configure
datadog-agent integration install -y postgres redis

# Verify logs are being collected
curl http://elasticsearch:9200/_cat/indices
```

---

## Backup & Disaster Recovery

### 1. Automated Backups

```bash
# Create backup script
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -U $DB_USER -d $DB_NAME -F custom -f $BACKUP_DIR/bbb_db_$TIMESTAMP.dump

# Redis backup
redis-cli BGSAVE

# Copy Redis dump
cp /data/dump.rdb $BACKUP_DIR/redis_dump_$TIMESTAMP.rdb

# Compress backups
tar -czf $BACKUP_DIR/bbb_backup_$TIMESTAMP.tar.gz $BACKUP_DIR/bbb_db_$TIMESTAMP.dump $BACKUP_DIR/redis_dump_$TIMESTAMP.rdb

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/bbb_backup_$TIMESTAMP.tar.gz s3://your-backup-bucket/
EOF

chmod +x scripts/backup.sh

# Schedule with cron
0 2 * * * /path/to/scripts/backup.sh
```

### 2. Restore from Backup

```bash
# List available backups
ls -lh /backups/

# Restore database
pg_restore -U bbb_user -d bbb_production /backups/bbb_db_20251023_020000.dump

# Restore Redis
redis-cli SHUTDOWN
cp /backups/redis_dump_20251023_020000.rdb /data/dump.rdb
redis-server --daemonize yes
```

### 3. Test Disaster Recovery

```bash
# Monthly DR drill
# 1. Backup current database
# 2. Delete production data (in test environment)
# 3. Restore from backup
# 4. Verify data integrity
# 5. Document any issues
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
# Allow only necessary ports
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw allow 5432/tcp    # PostgreSQL (internal only)
ufw allow 6379/tcp    # Redis (internal only)

# Enable firewall
ufw enable
```

### 2. SSL/TLS Configuration

```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# Or use Let's Encrypt
certbot certonly --standalone -d yourdomain.com

# Update Nginx configuration with certificate paths
```

### 3. Secrets Management

```bash
# Never commit secrets
echo ".env.production" >> .gitignore

# Use secure vault
# Option A: HashiCorp Vault
vault kv put secret/bbb SECRET_KEY=... DATABASE_URL=...

# Option B: AWS Secrets Manager
aws secretsmanager create-secret --name bbb/production --secret-string file://.env.production

# Option C: Kubernetes Secrets
kubectl create secret generic bbb-secrets --from-env-file=.env.production
```

### 4. Run Security Scan

```bash
# Dependency vulnerabilities
pip-audit

# OWASP vulnerability scan
pytest tests/test_security_owasp.py -v

# Code analysis
pylint bbb/
mypy bbb/

# Penetration testing
pytest tests/test_security_pentest.py -v
```

---

## Performance Tuning

### 1. Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_businesses_user_id ON businesses(user_id);
CREATE INDEX idx_campaigns_business_id ON marketing_campaigns(business_id);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- Vacuum and analyze
VACUUM ANALYZE;
```

### 2. Redis Optimization

```bash
# Configure for production
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET tcp-backlog 511
redis-cli CONFIG SET timeout 0
redis-cli CONFIG SET databases 16

# Monitor performance
redis-cli INFO stats
redis-cli MONITOR
```

### 3. Application Tuning

```python
# In bbb/config.py
DATABASE_POOL_SIZE = 20        # Connection pool size
DATABASE_MAX_OVERFLOW = 10     # Max overflow connections
CACHE_TTL = 3600               # Cache time-to-live
WORKER_PROCESSES = 4           # Gunicorn workers
```

### 4. Load Testing

```bash
# Install Locust
pip install locust

# Create test file
cat > tests/load_tests.py << 'EOF'
from locust import HttpUser, task

class LoadTestUser(HttpUser):
    @task
    def get_health(self):
        self.client.get("/health")
EOF

# Run load test
locust -f tests/load_tests.py -u 100 -r 10 --host http://localhost:8000
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'bbb'"

```bash
# Solution 1: Install package
pip install -e .

# Solution 2: Fix PYTHONPATH
export PYTHONPATH=/path/to/src:$PYTHONPATH

# Solution 3: Check Python path
python -c "import sys; print(sys.path)"
```

### Issue: Database Connection Refused

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check credentials
psql -h localhost -U bbb_user -d bbb_production

# Check connection string
echo $DATABASE_URL
```

### Issue: Redis Connection Timeout

```bash
# Check Redis is running
redis-cli ping

# Check Redis configuration
redis-cli CONFIG GET maxmemory

# Clear Redis cache
redis-cli FLUSHALL
```

### Issue: High CPU Usage

```bash
# Check top processes
top -n 1 -b | head -15

# Profile application
python -m cProfile -s cumulative -o stats.prof bbb/main.py

# Analyze profile
python -m pstats stats.prof
```

### Issue: Out of Memory

```bash
# Check memory usage
free -h

# Check Docker container memory
docker stats bbb-api

# Increase memory limit
docker-compose -f docker-compose.production.yml exec api \
  docker update --memory 4g bbb-api
```

---

## Scaling Guide

### 1. Horizontal Scaling

```bash
# Deploy multiple API instances
docker-compose -f docker-compose.production.yml up -d --scale api=3

# Or with Kubernetes
kubectl scale deployment bbb-api --replicas=5 -n bbb-production

# Monitor scaling
kubectl get pods -n bbb-production
```

### 2. Database Scaling

```sql
-- Enable Read Replicas (PostgreSQL)
-- Primary: Master database
-- Replicas: Read-only copies for load distribution

-- Connection pooling
-- Use PgBouncer for connection management
```

### 3. Caching Strategy

```python
# Use Redis for frequently accessed data
@cache(ttl=3600)
def get_user_businesses(user_id):
    return db.query(Business).filter_by(user_id=user_id).all()

# Cache invalidation
redis.delete(f"user_businesses:{user_id}")
```

### 4. CDN for Static Assets

```bash
# Configure CloudFront or similar
# Upload static files to S3
aws s3 sync static/ s3://your-bucket/static/

# Configure Nginx to serve from CDN
```

---

## Maintenance Schedule

### Daily
- [ ] Monitor error logs
- [ ] Check disk space
- [ ] Verify backup completion

### Weekly
- [ ] Review performance metrics
- [ ] Check security logs
- [ ] Update dependencies (security patches)

### Monthly
- [ ] Full backup test/restore
- [ ] Performance analysis
- [ ] Security audit
- [ ] Database optimization

### Quarterly
- [ ] Disaster recovery drill
- [ ] Load testing
- [ ] Security penetration testing
- [ ] Capacity planning

---

## Support & Emergency Contacts

- **Critical Issues:** Page on-call engineer (PagerDuty)
- **Security Issues:** security@corporationoflight.com
- **General Support:** support@yourdomain.com

---

## Deployment Checklist

- [ ] Environment configured
- [ ] Database initialized and tested
- [ ] All secrets configured
- [ ] SSL certificates installed
- [ ] Docker images built and tagged
- [ ] Docker Compose verified
- [ ] Health checks passing
- [ ] Monitoring dashboards accessible
- [ ] Backup scripts tested
- [ ] Security scan completed
- [ ] Load test passed
- [ ] Team trained on runbooks
- [ ] Incident response plan reviewed

---

**Status:** ✅ Production Ready
**Version:** 1.0.0
**Last Reviewed:** October 23, 2025
**Next Review:** January 23, 2026
