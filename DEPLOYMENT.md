# KS AI Platform - Deployment Guide

This guide covers deploying the KS AI platform to production environments as specified: Frontend to Vercel, Backend to EC2, Database to RDS, and Vector DB to Qdrant.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Vercel        │    │   AWS EC2        │    │   AWS RDS       │
│   (Frontend)    │────▶   (Backend)      │────▶   (PostgreSQL)  │
│   Next.js App   │    │   FastAPI + Nginx│    │   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Qdrant Cloud  │
                       │   (Vector DB)   │
                       └─────────────────┘
```

## 📋 Prerequisites

- **AWS Account** with EC2, RDS, and S3 access
- **Vercel Account** for frontend deployment  
- **Qdrant Cloud Account** (or self-hosted Qdrant)
- **Domain Name** (optional, for custom domain)
- **SSL Certificate** (for HTTPS)

## 🗄️ Step 1: Database Setup (AWS RDS)

### Create RDS PostgreSQL Instance

1. **Login to AWS Console** → RDS → Create Database
2. **Engine**: PostgreSQL 15.x
3. **Templates**: Production (or Dev/Test for testing)
4. **DB Instance Identifier**: `ks-ai-db`
5. **Master Username**: `ks_admin`
6. **Master Password**: Generate secure password
7. **Instance Class**: `db.t3.micro` (for testing) or `db.t3.small` (production)
8. **Storage**: 20GB SSD (expandable)
9. **VPC**: Default (or create custom VPC)
10. **Public Access**: Yes (for initial setup, restrict later)
11. **Security Groups**: Allow PostgreSQL (5432) from your IP and EC2

### Initialize Database

```bash
# Connect to RDS instance
psql -h your-rds-endpoint.amazonaws.com -U ks_admin -d postgres

# Create database
CREATE DATABASE ks_ai;
```

### Environment Variables
```bash
DATABASE_URL=postgresql://ks_admin:password@your-rds-endpoint.amazonaws.com:5432/ks_ai
```

## 🔍 Step 2: Vector Database (Qdrant)

### Option A: Qdrant Cloud (Recommended)

1. **Sign up** at [cloud.qdrant.io](https://cloud.qdrant.io)
2. **Create cluster**: 
   - **Name**: ks-ai-vectors
   - **Region**: Same as your EC2 region
   - **Configuration**: Starter (1GB) or Standard
3. **Get credentials**: API endpoint and API key
4. **Environment Variables**:
   ```bash
   QDRANT_HOST=your-cluster-id.cloud.qdrant.io
   QDRANT_PORT=6333
   QDRANT_API_KEY=your-api-key-here
   ```

### Option B: Self-hosted Qdrant on EC2

```bash
# On separate EC2 instance
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

## 🖥️ Step 3: Backend Deployment (AWS EC2)

### Launch EC2 Instance

1. **AMI**: Ubuntu Server 22.04 LTS
2. **Instance Type**: t3.medium (minimum for production)
3. **Key Pair**: Create/use existing key pair
4. **Security Groups**:
   - SSH (22): Your IP
   - HTTP (80): 0.0.0.0/0  
   - HTTPS (443): 0.0.0.0/0
   - Custom (8000): 0.0.0.0/0 (API)

### Setup EC2 Instance

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt install -y git

# Clone repository
git clone https://github.com/your-org/ks-ai-platform.git
cd ks-ai-platform
```

### Configure Environment

```bash
# Create production environment file
cp .env.example .env.production

# Edit with production values
nano .env.production
```

**Production Environment Variables**:
```bash
# Database
DATABASE_URL=postgresql://ks_admin:password@your-rds-endpoint.amazonaws.com:5432/ks_ai

# Qdrant
QDRANT_HOST=your-cluster-id.cloud.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=your-qdrant-api-key

# JWT (Generate secure secret)
JWT_SECRET=your-super-secure-jwt-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=ks-ai-content-bucket

# Admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=secure-admin-password-here

# CORS (Update with your frontend domain)
CORS_ORIGINS=["https://your-frontend-domain.vercel.app", "https://yourdomain.com"]

# Application
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Deploy Backend

```bash
# Build and run production containers
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker exec -it ks_ai_api_prod alembic upgrade head

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Setup SSL (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🌐 Step 4: Frontend Deployment (Vercel)

### Prepare Frontend

1. **Push code** to GitHub/GitLab
2. **Update environment variables** in frontend:
   ```bash
   # apps/web/.env.local
   NEXT_PUBLIC_API_URL=https://your-ec2-ip-or-domain.com
   NEXT_PUBLIC_APP_URL=https://your-app-domain.vercel.app
   ```

### Deploy to Vercel

1. **Connect Repository**:
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Select `apps/web` as the root directory

2. **Configure Build Settings**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `apps/web`
   - **Build Command**: `pnpm build`
   - **Output Directory**: `.next`

3. **Environment Variables**:
   ```bash
   NEXT_PUBLIC_API_URL=https://your-api-domain.com
   NEXT_PUBLIC_APP_URL=https://your-app-domain.vercel.app
   ```

4. **Deploy**: Vercel will automatically build and deploy

### Custom Domain (Optional)

1. **Add Domain** in Vercel project settings
2. **Configure DNS** to point to Vercel:
   ```
   A record: @ → 76.76.19.19
   CNAME record: www → cname.vercel-dns.com
   ```

## 🗂️ Step 5: S3 Setup (File Storage)

### Create S3 Bucket

1. **AWS Console** → S3 → Create Bucket
2. **Bucket Name**: `ks-ai-content-bucket` (globally unique)
3. **Region**: Same as EC2
4. **Block Public Access**: Keep blocked (secure)
5. **Versioning**: Enable (recommended)

### Configure IAM

Create IAM user with S3 access:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::ks-ai-content-bucket/*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::ks-ai-content-bucket"
        }
    ]
}
```

## 🔍 Step 6: Monitoring & Security

### Application Monitoring

1. **CloudWatch** for EC2 and RDS monitoring
2. **Vercel Analytics** for frontend metrics
3. **Application logs** via Docker logs

### Security Checklist

- [ ] **RDS**: Restrict security group to EC2 only
- [ ] **EC2**: Use security groups, disable password auth
- [ ] **SSL**: Enable HTTPS for all services
- [ ] **Environment Variables**: Never commit secrets to git
- [ ] **Backups**: Enable RDS automated backups
- [ ] **Updates**: Regular security updates

### Backup Strategy

```bash
# Database backup (automated via RDS)
# Manual backup command:
pg_dump -h your-rds-endpoint.amazonaws.com -U ks_admin -d ks_ai > backup.sql

# S3 versioning enables file recovery
# Qdrant: Use snapshots feature
```

## 🚀 Step 7: Health Checks & Testing

### Health Check Endpoints

- **Backend**: `https://your-api-domain.com/health`
- **Frontend**: Vercel automatic monitoring
- **Database**: Connection test via backend

### Test Deployment

1. **API Tests**:
   ```bash
   curl https://your-api-domain.com/health
   curl https://your-api-domain.com/topics
   ```

2. **Frontend Tests**:
   - Visit your Vercel URL
   - Test language selection
   - Test chat functionality
   - Test admin login

3. **Integration Tests**:
   - Complete user journey
   - Admin content upload
   - RAG query processing

## 📊 Step 8: Performance Optimization

### Backend Optimization

- **EC2**: Use larger instance for production
- **Database**: Configure connection pooling
- **Nginx**: Enable gzip compression and caching
- **Docker**: Multi-stage builds for smaller images

### Frontend Optimization

- **Vercel**: Enable Edge Functions if needed
- **Next.js**: Image optimization enabled
- **CDN**: Automatic via Vercel

## 🔧 Maintenance & Updates

### Update Deployment

```bash
# Backend updates
cd ks-ai-platform
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Frontend updates
# Push to GitHub - Vercel auto-deploys
```

### Database Migrations

```bash
# Run new migrations
docker exec -it ks_ai_api_prod alembic upgrade head
```

### Scaling Considerations

- **EC2**: Use Load Balancer + Auto Scaling Group
- **RDS**: Read replicas for read-heavy workloads  
- **Qdrant**: Cluster mode for high availability
- **S3**: CloudFront CDN for faster file access

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection**:
   ```bash
   # Test connection
   docker exec -it ks_ai_api_prod python -c "from app.db.base import engine; print(engine.execute('SELECT 1').scalar())"
   ```

2. **Qdrant Connection**:
   ```bash
   # Test Qdrant
   curl https://your-qdrant-endpoint:6333/health
   ```

3. **CORS Issues**:
   - Update `CORS_ORIGINS` in backend environment
   - Restart backend containers

4. **SSL Issues**:
   ```bash
   # Renew certificates
   sudo certbot renew
   ```

### Monitoring Commands

```bash
# Check system resources
htop
df -h
docker stats

# Application logs
docker-compose -f docker-compose.prod.yml logs -f api
tail -f /var/log/nginx/access.log
```

---

**🎉 Congratulations!** Your KS AI platform is now deployed to production. Monitor the logs and metrics to ensure everything runs smoothly.