#!/bin/bash
# QMS 部署验证脚本
# Deployment Verification Script

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
TOTAL=0

# Function to print test result
print_test() {
    TOTAL=$((TOTAL + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} $2"
        FAILED=$((FAILED + 1))
    fi
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}QMS Deployment Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test 1: Check Docker
echo -e "${YELLOW}[1/15] Checking Docker...${NC}"
docker --version > /dev/null 2>&1
print_test $? "Docker is installed"

# Test 2: Check Docker Compose
echo -e "${YELLOW}[2/15] Checking Docker Compose...${NC}"
docker compose version > /dev/null 2>&1
print_test $? "Docker Compose is installed"

# Test 3: Check containers
echo -e "${YELLOW}[3/15] Checking containers...${NC}"
docker ps | grep -q qms_postgres
print_test $? "PostgreSQL container is running"

docker ps | grep -q qms_redis
print_test $? "Redis container is running"

docker ps | grep -q qms_backend_stable
print_test $? "Backend (Stable) container is running"

docker ps | grep -q qms_backend_preview
print_test $? "Backend (Preview) container is running"

docker ps | grep -q qms_frontend_stable
print_test $? "Frontend (Stable) container is running"

docker ps | grep -q qms_frontend_preview
print_test $? "Frontend (Preview) container is running"

docker ps | grep -q qms_nginx
print_test $? "Nginx container is running"

docker ps | grep -q qms_celery_worker
print_test $? "Celery Worker container is running"

docker ps | grep -q qms_celery_beat
print_test $? "Celery Beat container is running"

# Test 4: Check backend health
echo -e "${YELLOW}[4/15] Checking backend health...${NC}"
curl -f http://localhost:8000/health > /dev/null 2>&1
print_test $? "Backend (Stable) health check passed"

curl -f http://localhost:8001/health > /dev/null 2>&1
print_test $? "Backend (Preview) health check passed"

# Test 5: Check nginx health
echo -e "${YELLOW}[5/15] Checking nginx health...${NC}"
curl -f http://localhost/health > /dev/null 2>&1
print_test $? "Nginx health check passed"

# Test 6: Check database connection
echo -e "${YELLOW}[6/15] Checking database connection...${NC}"
docker compose exec -T postgres psql -U qms_user -d qms_db -c "SELECT 1;" > /dev/null 2>&1
print_test $? "Database connection successful"

# Test 7: Check Redis connection
echo -e "${YELLOW}[7/15] Checking Redis connection...${NC}"
docker compose exec -T redis redis-cli ping > /dev/null 2>&1
print_test $? "Redis connection successful"

# Test 8: Check API documentation
echo -e "${YELLOW}[8/15] Checking API documentation...${NC}"
curl -f http://localhost:8000/docs > /dev/null 2>&1
print_test $? "API documentation is accessible"

# Test 9: Check database migrations
echo -e "${YELLOW}[9/15] Checking database migrations...${NC}"
docker compose exec -T backend-stable alembic current > /dev/null 2>&1
print_test $? "Database migrations are up to date"

# Test 10: Check frontend access
echo -e "${YELLOW}[10/15] Checking frontend access...${NC}"
curl -f http://localhost/ > /dev/null 2>&1
print_test $? "Frontend (Stable) is accessible"

# Test 11: Check API endpoints
echo -e "${YELLOW}[11/15] Checking API endpoints...${NC}"
curl -f http://localhost:8000/api/v1/auth/captcha > /dev/null 2>&1
print_test $? "Captcha API endpoint is working"

# Test 12: Check Celery worker
echo -e "${YELLOW}[12/15] Checking Celery worker...${NC}"
docker compose logs celery-worker | grep -q "celery@" > /dev/null 2>&1
print_test $? "Celery worker is running"

# Test 13: Check Celery beat
echo -e "${YELLOW}[13/15] Checking Celery beat...${NC}"
docker compose logs celery-beat | grep -q "beat" > /dev/null 2>&1
print_test $? "Celery beat is running"

# Test 14: Check disk space
echo -e "${YELLOW}[14/15] Checking disk space...${NC}"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    print_test 0 "Disk space is sufficient ($DISK_USAGE% used)"
else
    print_test 1 "Disk space is low ($DISK_USAGE% used)"
fi

# Test 15: Check memory usage
echo -e "${YELLOW}[15/15] Checking memory usage...${NC}"
MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ "$MEMORY_USAGE" -lt 90 ]; then
    print_test 0 "Memory usage is normal ($MEMORY_USAGE% used)"
else
    print_test 1 "Memory usage is high ($MEMORY_USAGE% used)"
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verification Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total Tests: ${TOTAL}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Deployment is successful.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please check the logs.${NC}"
    exit 1
fi
