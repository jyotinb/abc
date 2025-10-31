#!/bin/bash

echo "📦 Collecting Code Files for Customization"
echo "==========================================="

BACKUP_DIR="/root/code-backup-$(date +%Y%m%d_%H%M%S)"
PROJECT_DIR="/iot/greenhouse-iot-platform"

mkdir -p "$BACKUP_DIR"

# ============================================
# BACKEND FILES
# ============================================
echo "📂 Backend Files..."
mkdir -p "$BACKUP_DIR/backend"

# Core files
cp "$PROJECT_DIR/backend/app/main.py" "$BACKUP_DIR/backend/" 2>/dev/null
cp "$PROJECT_DIR/backend/app/database.py" "$BACKUP_DIR/backend/" 2>/dev/null
cp "$PROJECT_DIR/backend/app/config.py" "$BACKUP_DIR/backend/" 2>/dev/null
cp "$PROJECT_DIR/backend/app/deps.py" "$BACKUP_DIR/backend/" 2>/dev/null

# Models
mkdir -p "$BACKUP_DIR/backend/models"
cp "$PROJECT_DIR/backend/app/models/"*.py "$BACKUP_DIR/backend/models/" 2>/dev/null

# API Routes
mkdir -p "$BACKUP_DIR/backend/api"
cp "$PROJECT_DIR/backend/app/api/"*.py "$BACKUP_DIR/backend/api/" 2>/dev/null

# Schemas
mkdir -p "$BACKUP_DIR/backend/schemas"
cp "$PROJECT_DIR/backend/app/schemas/"*.py "$BACKUP_DIR/backend/schemas/" 2>/dev/null

# Config files
cp "$PROJECT_DIR/backend/requirements.txt" "$BACKUP_DIR/backend/" 2>/dev/null
cp "$PROJECT_DIR/backend/Dockerfile" "$BACKUP_DIR/backend/" 2>/dev/null
cp "$PROJECT_DIR/backend/.env" "$BACKUP_DIR/backend/env.txt" 2>/dev/null

echo "✅ Backend files collected"

# ============================================
# FRONTEND FILES
# ============================================
echo "📂 Frontend Files..."
mkdir -p "$BACKUP_DIR/frontend"

# Main React files
cp "$PROJECT_DIR/greenhouse-frontend/src/components/AdminDashboard.jsx" "$BACKUP_DIR/frontend/" 2>/dev/null
cp "$PROJECT_DIR/greenhouse-frontend/src/App.js" "$BACKUP_DIR/frontend/" 2>/dev/null
cp "$PROJECT_DIR/greenhouse-frontend/src/App.css" "$BACKUP_DIR/frontend/" 2>/dev/null
cp "$PROJECT_DIR/greenhouse-frontend/src/index.js" "$BACKUP_DIR/frontend/" 2>/dev/null

# Config files
cp "$PROJECT_DIR/greenhouse-frontend/package.json" "$BACKUP_DIR/frontend/" 2>/dev/null
cp "$PROJECT_DIR/greenhouse-frontend/.env" "$BACKUP_DIR/frontend/env.txt" 2>/dev/null

# Copy other components if they exist
if [ -d "$PROJECT_DIR/greenhouse-frontend/src/components" ]; then
    mkdir -p "$BACKUP_DIR/frontend/components"
    cp "$PROJECT_DIR/greenhouse-frontend/src/components/"*.jsx "$BACKUP_DIR/frontend/components/" 2>/dev/null
    cp "$PROJECT_DIR/greenhouse-frontend/src/components/"*.js "$BACKUP_DIR/frontend/components/" 2>/dev/null
fi

echo "✅ Frontend files collected"

# ============================================
# DOCKER & CONFIG FILES
# ============================================
echo "📂 Docker & Config Files..."
cp "$PROJECT_DIR/docker-compose.yml" "$BACKUP_DIR/" 2>/dev/null

echo "✅ Docker files collected"

# ============================================
# DATABASE SCHEMA
# ============================================
echo "📂 Database Schema..."
PGPASSWORD=greenhouse123 pg_dump -h localhost -U greenhouse -d greenhouse_iot \
  --schema-only \
  --no-owner \
  --no-privileges \
  -f "$BACKUP_DIR/database_schema.sql" 2>/dev/null

echo "✅ Database schema exported"

# ============================================
# CREATE FILE LIST
# ============================================
cat > "$BACKUP_DIR/FILE_LIST.txt" << 'LIST'
Code Files for Customization
=============================

BACKEND FILES (Python/FastAPI):
├── main.py                  - Main application entry point
├── database.py              - Database connection & session
├── config.py                - Configuration settings
├── deps.py                  - Dependencies (auth, etc)
├── requirements.txt         - Python packages
├── Dockerfile               - Docker build config
├── env.txt                  - Environment variables
├── models/                  - Database models (SQLAlchemy)
│   ├── user.py
│   ├── company.py
│   ├── device.py
│   ├── zone.py
│   ├── zone_topic.py
│   └── telemetry.py
├── api/                     - API route handlers
│   ├── auth.py
│   ├── users.py
│   ├── companies.py
│   ├── devices.py
│   ├── zones.py
│   └── zone_topics.py
└── schemas/                 - Pydantic schemas (validation)
    ├── user.py
    ├── company.py
    ├── device.py
    └── zone.py

FRONTEND FILES (React):
├── AdminDashboard.jsx       - Main dashboard component
├── App.js                   - React app entry point
├── App.css                  - Global styles
├── index.js                 - React DOM render
├── package.json             - npm dependencies
├── env.txt                  - Environment variables
└── components/              - Other React components
    └── *.jsx

DOCKER & CONFIG:
├── docker-compose.yml       - Docker services config

DATABASE:
└── database_schema.sql      - PostgreSQL schema

KEY FILES TO SHARE FOR CUSTOMIZATION:
=====================================
1. AdminDashboard.jsx        - For UI changes
2. api/*.py                  - For API endpoint changes
3. models/*.py               - For database model changes
4. main.py                   - For app-level changes
5. database_schema.sql       - For database structure

MOST FREQUENTLY CUSTOMIZED:
===========================
- AdminDashboard.jsx         - UI/UX changes
- api/devices.py             - Device management logic
- api/zones.py               - Zone management logic
- models/device.py           - Device data structure
- models/zone.py             - Zone data structure
LIST

echo "✅ File list created"

# ============================================
# SUMMARY
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CODE FILES COLLECTED!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Location: $BACKUP_DIR"
echo ""
echo "📋 Files Collected:"
find "$BACKUP_DIR" -type f | wc -l | xargs echo "   Total files:"
echo ""
echo "📄 Key Files:"
echo "   Backend:  $(find $BACKUP_DIR/backend -type f -name '*.py' | wc -l) Python files"
echo "   Frontend: $(find $BACKUP_DIR/frontend -type f \( -name '*.js' -o -name '*.jsx' \) | wc -l) React files"
echo ""
echo "💾 To download these files:"
echo "   cd $BACKUP_DIR"
echo "   tar -czf code-files.tar.gz *"
echo "   # Then download: code-files.tar.gz"
echo ""
echo "📤 Or copy individual files you want to share:"
echo "   cat $BACKUP_DIR/FILE_LIST.txt"
echo ""
