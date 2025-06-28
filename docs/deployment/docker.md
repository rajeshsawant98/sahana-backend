# Docker Deployment Guide

Deploy Sahana Backend using Docker for consistent and portable deployments.

## Prerequisites

- Docker installed and running
- Docker Compose (optional, for development)
- Firebase credentials file

## Building the Docker Image

### Option 1: Using the provided Dockerfile

```bash
# Build the image
docker build -t sahana-backend .

# Run the container
docker run -p 8000:8000 --env-file .env sahana-backend
```

### Option 2: Docker Compose (Recommended for Development)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  sahana-backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./firebase_cred.json:/app/firebase_cred.json:ro
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/app/firebase_cred.json
    restart: unless-stopped
```

Run with Docker Compose:

```bash
docker-compose up -d
```

## Environment Variables for Docker

Create a `.env` file for Docker deployment:

```env
# Application
PORT=8000
HOST=0.0.0.0

# JWT Configuration
JWT_SECRET_KEY=your_production_jwt_secret
JWT_REFRESH_SECRET_KEY=your_production_refresh_secret

# Google Services
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Firebase (Docker path)
GOOGLE_APPLICATION_CREDENTIALS=/app/firebase_cred.json

# External APIs
TICKETMASTER_API_KEY=your_ticketmaster_api_key
```

## Production Deployment

### Using Docker Hub

1. **Build and tag for production:**

```bash
docker build -t your-username/sahana-backend:latest .
docker push your-username/sahana-backend:latest
```

2. **Deploy on production server:**

```bash
# Pull the image
docker pull your-username/sahana-backend:latest

# Run with production configuration
docker run -d \
  --name sahana-backend \
  -p 80:8000 \
  --env-file .env.production \
  -v /path/to/firebase_cred.json:/app/firebase_cred.json:ro \
  --restart unless-stopped \
  your-username/sahana-backend:latest
```

### Multi-stage Build (Optimized)

For smaller production images, use multi-stage builds:

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Container Health Checks

Add health checks to your Dockerfile:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

## Docker Compose for Full Stack

Complete setup with additional services:

```yaml
version: '3.8'

services:
  sahana-backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./firebase_cred.json:/app/firebase_cred.json:ro
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - sahana-backend
    restart: unless-stopped

volumes:
  redis_data:
```

## Cloud Deployment

### Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/sahana-backend

# Deploy to Cloud Run
gcloud run deploy sahana-backend \
  --image gcr.io/YOUR_PROJECT_ID/sahana-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "JWT_SECRET_KEY=your_secret" \
  --max-instances 10
```

### AWS ECS

Deploy using AWS ECS with Fargate:

1. Push image to ECR
2. Create ECS task definition
3. Create ECS service
4. Configure load balancer

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name sahana-backend \
  --image your-username/sahana-backend:latest \
  --dns-name-label sahana-backend \
  --ports 8000 \
  --environment-variables JWT_SECRET_KEY=your_secret
```

## Monitoring and Logging

### Docker Logging

Configure logging driver:

```yaml
services:
  sahana-backend:
    build: .
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Health Monitoring

Use Docker Compose with health checks:

```yaml
services:
  sahana-backend:
    build: .
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

## Security Considerations

### Production Security

- Use non-root user in container
- Scan images for vulnerabilities
- Use secrets management for sensitive data
- Enable HTTPS/TLS termination
- Implement proper firewall rules

### Example secure Dockerfile:

```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r sahana && useradd -r -g sahana sahana

WORKDIR /app

# Install dependencies as root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code and change ownership
COPY . .
RUN chown -R sahana:sahana /app

# Switch to non-root user
USER sahana

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Docker Issues

**Container exits immediately**: Check logs with `docker logs container-name`

**Port binding errors**: Ensure port 8000 is not already in use

**Environment variables not loading**: Verify `.env` file format and location

**Firebase connection issues**: Ensure credentials file is properly mounted

### Debug Container

Run container in interactive mode for debugging:

```bash
docker run -it --entrypoint /bin/bash sahana-backend
```
