#!/bin/bash

# Pre-deployment checklist for Railway
# Run this before deploying to catch common issues

set -e

echo "🔍 AI-HR Pre-Deployment Checklist"
echo "=================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Check if .env exists
echo "1️⃣  Checking environment files..."
if [ -f "src/backend/.env" ]; then
    check_pass ".env file exists"

    # Check for OPENAI_API_KEY
    if grep -q "OPENAI_API_KEY=sk-" src/backend/.env; then
        check_pass "OPENAI_API_KEY is set"
    else
        check_fail "OPENAI_API_KEY not found or invalid"
    fi
else
    check_fail ".env file not found in src/backend/"
fi

echo ""

# 2. Check Docker files
echo "2️⃣  Checking Docker configuration..."
if [ -f "docker-compose.yml" ]; then
    check_pass "docker-compose.yml exists"
else
    check_fail "docker-compose.yml not found"
fi

if [ -f "docker/backend.Dockerfile" ]; then
    check_pass "Backend Dockerfile exists"
else
    check_fail "Backend Dockerfile not found"
fi

if [ -f "docker/frontend.Dockerfile" ]; then
    check_pass "Frontend Dockerfile exists"
else
    check_fail "Frontend Dockerfile not found"
fi

if [ -f ".dockerignore" ]; then
    check_pass ".dockerignore exists"
else
    check_warn ".dockerignore not found (recommended for faster builds)"
fi

echo ""

# 3. Check Python dependencies
echo "3️⃣  Checking dependencies..."
if [ -f "src/backend/requirements.txt" ]; then
    check_pass "Backend requirements.txt exists"

    # Check for key dependencies
    if grep -q "fastapi" src/backend/requirements.txt; then
        check_pass "FastAPI dependency found"
    else
        check_fail "FastAPI not in requirements.txt"
    fi

    if grep -q "openai" src/backend/requirements.txt; then
        check_pass "OpenAI dependency found"
    else
        check_fail "OpenAI not in requirements.txt"
    fi
else
    check_fail "Backend requirements.txt not found"
fi

if [ -f "src/frontend/requirements.txt" ]; then
    check_pass "Frontend requirements.txt exists"

    if grep -q "streamlit" src/frontend/requirements.txt; then
        check_pass "Streamlit dependency found"
    else
        check_fail "Streamlit not in requirements.txt"
    fi
else
    check_fail "Frontend requirements.txt not found"
fi

echo ""

# 4. Check Railway configuration
echo "4️⃣  Checking Railway configuration..."
if [ -f "railway.toml" ]; then
    check_pass "railway.toml exists"
else
    check_warn "railway.toml not found (optional, but recommended)"
fi

if [ -f ".env.railway.example" ]; then
    check_pass ".env.railway.example exists"
else
    check_warn ".env.railway.example not found (helpful for documentation)"
fi

echo ""

# 5. Check source files
echo "5️⃣  Checking source files..."
if [ -f "src/backend/main.py" ]; then
    check_pass "Backend main.py exists"
else
    check_fail "Backend main.py not found"
fi

if [ -f "src/frontend/app_candidate.py" ]; then
    check_pass "Candidate app exists"
else
    check_fail "Candidate app not found"
fi

if [ -f "src/frontend/app_hr.py" ]; then
    check_pass "HR app exists"
else
    check_fail "HR app not found"
fi

echo ""

# 6. Check for common issues
echo "6️⃣  Checking for common issues..."

# Check if there are any todos or fixmes
TODO_COUNT=$(grep -r "TODO\|FIXME" src/ --exclude-dir=__pycache__ 2>/dev/null | wc -l | tr -d ' ')
if [ "$TODO_COUNT" -gt 0 ]; then
    check_warn "Found $TODO_COUNT TODO/FIXME comments in code"
else
    check_pass "No TODO/FIXME comments found"
fi

# Check for hardcoded localhost
LOCALHOST_COUNT=$(grep -r "localhost\|127.0.0.1" src/ --exclude-dir=__pycache__ 2>/dev/null | wc -l | tr -d ' ')
if [ "$LOCALHOST_COUNT" -gt 5 ]; then
    check_warn "Found $LOCALHOST_COUNT references to localhost (make sure they're in env vars)"
else
    check_pass "Localhost usage looks OK"
fi

# Check for secrets in code
if grep -r "sk-proj-\|sk-" src/ --exclude-dir=__pycache__ --exclude="*.env*" 2>/dev/null | grep -v ".example" > /dev/null; then
    check_fail "Potential API keys found in source code (should be in .env only)"
else
    check_pass "No hardcoded API keys found"
fi

echo ""
echo "=================================="
echo "Summary:"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 All critical checks passed! Ready to deploy.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Commit and push to GitHub"
    echo "2. Follow DEPLOYMENT.md instructions"
    echo "3. Deploy on Railway"
    exit 0
else
    echo -e "${RED}⚠️  Some checks failed. Please fix issues before deploying.${NC}"
    exit 1
fi
