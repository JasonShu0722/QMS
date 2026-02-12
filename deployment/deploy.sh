#!/bin/bash
# QMS 质量管理系统 - 生产环境部署脚本
# Production Deployment Script for QMS System

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_ROOT}/.env.production"
BACKUP_DIR="${PROJECT_ROOT}/deployment/backup"
LOG_FILE="${PROJECT_ROOT}/deployment/deploy_$(date +%Y%m%d_%H%M%S).log"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is installed: $(docker --version)"
    
    # Check Docker Compose
    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose is installed: $(docker compose version)"
    
    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file not found: $ENV_FILE"
        print_info "Please copy .env.example to .env.production and configure it."
        exit 1
    fi
    print_success "Environment file found: $ENV_FILE"
    
    # Check if required environment variables are set
    source "$ENV_FILE"
    if [ -z "${DB_PASSWORD:-}" ] || [ "${DB_PASSWORD}" = "CHANGE_ME_STRONG_PASSWORD_HERE" ]; then
        print_error "DB_PASSWORD is not configured in $ENV_FILE"
        exit 1
    fi
    if [ -z "${SECRET_KEY:-}" ] || [ "${SECRET_KEY}" = "CHANGE_ME_GENERATE_STRONG_SECRET_KEY_HERE" ]; then
        print_error "SECRET_KEY is not configured in $ENV_FILE"
        exit 1
    fi
    print_success "Required environment variables are configured"
}

# Function to backup database
backup_database() {
    print_info "Creating database backup..."
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="${BACKUP_DIR}/qms_db_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    if docker ps | grep -q qms_postgres; then
        docker exec qms_postgres pg_dump -U qms_user qms_db > "$BACKUP_FILE"
        print_success "Database backup created: $BACKUP_FILE"
    else
        print_warning "PostgreSQL container not running, skipping backup"
    fi
}

# Function to stop existing services
stop_services() {
    print_info "Stopping existing services..."
    cd "$PROJECT_ROOT"
    docker compose down
    print_success "Services stopped"
}

# Function to build and start services
start_services() {
    print_info "Building and starting services..."
    cd "$PROJECT_ROOT"
    
    # Build images
    print_info "Building Docker images..."
    docker compose build --no-cache
    
    # Start services
    print_info "Starting services..."
    docker compose up -d
    
    print_success "Services started"
}

# Function to run database migrations
run_migrations() {
    print_info "Running database migrations..."
    
    # Wait for database to be ready
    print_info "Waiting for database to be ready..."
    sleep 10
    
    # Run migrations
    docker compose exec -T backend-stable alembic upgrade head
    
    if [ $? -eq 0 ]; then
        print_success "Database migrations completed successfully"
    else
        print_error "Database migrations failed"
        exit 1
    fi
}

# Function to verify services
verify_services() {
    print_info "Verifying services..."
    
    # Check if all containers are running
    EXPECTED_CONTAINERS=(
        "qms_postgres"
        "qms_redis"
        "qms_backend_stable"
        "qms_backend_preview"
        "qms_frontend_stable"
        "qms_frontend_preview"
        "qms_nginx"
        "qms_celery_worker"
        "qms_celery_beat"
    )
    
    for container in "${EXPECTED_CONTAINERS[@]}"; do
        if docker ps | grep -q "$container"; then
            print_success "Container running: $container"
        else
            print_error "Container not running: $container"
            docker logs "$container" | tail -20
            exit 1
        fi
    done
    
    # Check backend health
    print_info "Checking backend health..."
    sleep 5
    
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_success "Backend (Stable) is healthy"
    else
        print_error "Backend (Stable) health check failed"
        docker logs qms_backend_stable | tail -20
        exit 1
    fi
    
    if curl -f http://localhost:8001/health &> /dev/null; then
        print_success "Backend (Preview) is healthy"
    else
        print_error "Backend (Preview) health check failed"
        docker logs qms_backend_preview | tail -20
        exit 1
    fi
    
    # Check nginx health
    if curl -f http://localhost/health &> /dev/null; then
        print_success "Nginx is healthy"
    else
        print_error "Nginx health check failed"
        docker logs qms_nginx | tail -20
        exit 1
    fi
}

# Function to run functional tests
run_functional_tests() {
    print_info "Running functional verification tests..."
    
    # Test database connection
    print_info "Testing database connection..."
    docker compose exec -T backend-stable python -c "
from app.core.database import engine
import asyncio
async def test_db():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('Database connection successful')
asyncio.run(test_db())
" || print_error "Database connection test failed"
    
    # Test Redis connection
    print_info "Testing Redis connection..."
    docker compose exec -T redis redis-cli -a "$REDIS_PASSWORD" ping | grep -q PONG && \
        print_success "Redis connection successful" || \
        print_error "Redis connection test failed"
    
    print_success "Functional tests completed"
}

# Function to display deployment summary
display_summary() {
    print_info "=========================================="
    print_info "QMS Deployment Summary"
    print_info "=========================================="
    print_info "Deployment Time: $(date)"
    print_info "Environment: Production"
    print_info ""
    print_info "Service URLs:"
    print_info "  - Stable Environment: http://localhost (or https://qms.company.com)"
    print_info "  - Preview Environment: http://localhost (or https://preview.company.com)"
    print_info "  - Backend API (Stable): http://localhost:8000"
    print_info "  - Backend API (Preview): http://localhost:8001"
    print_info "  - API Documentation: http://localhost:8000/docs"
    print_info ""
    print_info "Container Status:"
    docker compose ps
    print_info ""
    print_info "Logs Location: $LOG_FILE"
    print_info "=========================================="
}

# Main deployment flow
main() {
    print_info "Starting QMS Production Deployment..."
    print_info "Log file: $LOG_FILE"
    
    # Step 1: Check prerequisites
    check_prerequisites
    
    # Step 2: Backup database (if exists)
    backup_database
    
    # Step 3: Stop existing services
    stop_services
    
    # Step 4: Start services
    start_services
    
    # Step 5: Run database migrations
    run_migrations
    
    # Step 6: Verify services
    verify_services
    
    # Step 7: Run functional tests
    run_functional_tests
    
    # Step 8: Display summary
    display_summary
    
    print_success "QMS Production Deployment Completed Successfully!"
}

# Run main function
main "$@"
