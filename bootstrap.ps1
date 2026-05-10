# LockIn - Day 1 Bootstrap Script (Windows PowerShell)
# Run from the repo root: .\bootstrap.ps1

$ErrorActionPreference = "Stop"

# Force UTF-8 output so any non-ASCII characters render correctly
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  [!]  $Message" -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  [X]  $Message" -ForegroundColor Red
}

function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# ---------------------------------------------------------------------------
# 1. Prerequisite checks
# ---------------------------------------------------------------------------

Write-Step "Checking prerequisites..."

$missingPrereqs = @()

if (Test-Command "node") {
    $nodeVersion = (node --version) -replace 'v',''
    $nodeMajor = [int]($nodeVersion.Split('.')[0])
    if ($nodeMajor -lt 20) {
        Write-Fail "Node $nodeVersion found, but 20+ is required"
        $missingPrereqs += "Node 20+ - install from https://nodejs.org/"
    } else {
        Write-Ok "Node $nodeVersion"
    }
} else {
    Write-Fail "Node not found"
    $missingPrereqs += "Node 20+ - install from https://nodejs.org/"
}

if (Test-Command "python") {
    $pythonVersion = (python --version) -replace 'Python ',''
    $pythonMajor = [int]($pythonVersion.Split('.')[0])
    $pythonMinor = [int]($pythonVersion.Split('.')[1])
    if ($pythonMajor -lt 3 -or ($pythonMajor -eq 3 -and $pythonMinor -lt 12)) {
        Write-Fail "Python $pythonVersion found, but 3.12+ is required"
        $missingPrereqs += "Python 3.12+ - install from https://www.python.org/downloads/"
    } else {
        Write-Ok "Python $pythonVersion"
    }
} else {
    Write-Fail "Python not found"
    $missingPrereqs += "Python 3.12+ - install from https://www.python.org/downloads/"
}

if (Test-Command "docker") {
    try {
        $null = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Docker Desktop is running"
        } else {
            Write-Warn "Docker is installed but not running - start Docker Desktop"
            $missingPrereqs += "Start Docker Desktop, then re-run this script"
        }
    } catch {
        Write-Warn "Docker is installed but not running - start Docker Desktop"
        $missingPrereqs += "Start Docker Desktop, then re-run this script"
    }
} else {
    Write-Fail "Docker not found"
    $missingPrereqs += "Docker Desktop - install from https://www.docker.com/products/docker-desktop"
}

if (Test-Command "pnpm") {
    Write-Ok "pnpm $(pnpm --version)"
} else {
    Write-Warn "pnpm not found - installing now via npm..."
    npm install -g pnpm
    if ($LASTEXITCODE -ne 0) {
        $missingPrereqs += "pnpm - run 'npm install -g pnpm' manually"
    } else {
        Write-Ok "pnpm installed"
    }
}

if ($missingPrereqs.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing prerequisites:" -ForegroundColor Red
    foreach ($p in $missingPrereqs) {
        Write-Host "  - $p"
    }
    Write-Host ""
    Write-Host "Install the items above, then re-run this script." -ForegroundColor Yellow
    exit 1
}

# ---------------------------------------------------------------------------
# 2. Initialize Turborepo
# ---------------------------------------------------------------------------

Write-Step "Initializing Turborepo..."

if (Test-Path "turbo.json") {
    Write-Ok "Turborepo already initialized - skipping"
} else {
    pnpm dlx create-turbo@latest . --package-manager pnpm --skip-install
    Write-Ok "Turborepo initialized"
}

# ---------------------------------------------------------------------------
# 3. Create monorepo directory structure
# ---------------------------------------------------------------------------

Write-Step "Creating directory structure..."

$dirs = @(
    "apps\web",
    "apps\api",
    "apps\mcp",
    "packages\shared-types",
    "packages\ui",
    "packages\events",
    "infra\docker",
    "infra\terraform",
    "docs\slices"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Ok "Directories created"

# ---------------------------------------------------------------------------
# 4. Scaffold Next.js web app
# ---------------------------------------------------------------------------

Write-Step "Scaffolding Next.js web app..."

if (Test-Path "apps\web\package.json") {
    Write-Ok "Next.js app already exists - skipping"
} else {
    Remove-Item -Path "apps\web" -Recurse -Force -ErrorAction SilentlyContinue
    pnpm dlx create-next-app@latest apps\web `
        --typescript --tailwind --eslint --app --turbopack `
        --src-dir --import-alias "@/*" --no-git --use-pnpm
    Write-Ok "Next.js app scaffolded"
}

# ---------------------------------------------------------------------------
# 5. Scaffold FastAPI backend
# ---------------------------------------------------------------------------

Write-Step "Scaffolding FastAPI backend..."

Push-Location apps\api
try {
    if (Test-Path ".venv") {
        Write-Ok "Python venv already exists - skipping creation"
    } else {
        python -m venv .venv
        Write-Ok "Python venv created"
    }

    # Activate the venv for this session
    & .\.venv\Scripts\Activate.ps1

    Write-Ok "Installing Python packages (this can take a minute)..."
    python -m pip install --upgrade pip --quiet
    pip install --quiet `
        "fastapi" `
        "uvicorn[standard]" `
        "sqlalchemy" `
        "alembic" `
        "pydantic-settings" `
        "redis" `
        "temporalio" `
        "python-jose[cryptography]" `
        "passlib[bcrypt]" `
        "httpx" `
        "pytest" `
        "pytest-asyncio"

    pip freeze | Out-File -FilePath "requirements.txt" -Encoding UTF8

    # Create the package skeleton
    $apiDirs = @("app", "app\api", "app\core", "app\db", "app\services", "app\events", "tests")
    foreach ($d in $apiDirs) {
        if (-not (Test-Path $d)) {
            New-Item -ItemType Directory -Path $d -Force | Out-Null
        }
    }

    if (-not (Test-Path "app\__init__.py")) {
        New-Item -ItemType File -Path "app\__init__.py" -Force | Out-Null
    }

    # Generate the FastAPI starter file safely using a string array (avoids
    # any chance of a here-string being terminated early by inner quotes).
    if (-not (Test-Path "app\main.py")) {
        $mainPyLines = @(
            'from fastapi import FastAPI',
            '',
            'app = FastAPI(title="LockIn API", version="0.0.1")',
            '',
            '',
            '@app.get("/health")',
            'async def health():',
            '    return {"status": "ok"}',
            ''
        )
        $mainPyLines | Out-File -FilePath "app\main.py" -Encoding UTF8
    }

    Write-Ok "FastAPI backend scaffolded"
} finally {
    Pop-Location
}

# ---------------------------------------------------------------------------
# 6. Docker Compose for local infrastructure
# ---------------------------------------------------------------------------

Write-Step "Setting up Docker Compose (Postgres + TimescaleDB + Redis)..."

$dockerComposeLines = @(
    'services:',
    '  postgres:',
    '    image: postgres:16-alpine',
    '    environment:',
    '      POSTGRES_DB: lockin',
    '      POSTGRES_USER: lockin',
    '      POSTGRES_PASSWORD: lockin_dev',
    '    ports:',
    '      - "5432:5432"',
    '    volumes:',
    '      - pgdata:/var/lib/postgresql/data',
    '',
    '  timescaledb:',
    '    image: timescale/timescaledb:latest-pg16',
    '    environment:',
    '      POSTGRES_DB: lockin_events',
    '      POSTGRES_USER: lockin',
    '      POSTGRES_PASSWORD: lockin_dev',
    '    ports:',
    '      - "5433:5432"',
    '    volumes:',
    '      - tsdata:/var/lib/postgresql/data',
    '',
    '  redis:',
    '    image: redis:7-alpine',
    '    ports:',
    '      - "6379:6379"',
    '',
    'volumes:',
    '  pgdata:',
    '  tsdata:'
)

$dockerComposeLines | Out-File -FilePath "infra\docker\docker-compose.yml" -Encoding UTF8
Write-Ok "docker-compose.yml created at infra\docker\"

# ---------------------------------------------------------------------------
# 7. Environment template
# ---------------------------------------------------------------------------

Write-Step "Creating .env.example and .env.local..."

$envLines = @(
    '# Copy to .env.local for local dev. NEVER commit real secrets.',
    'DATABASE_URL=postgresql://lockin:lockin_dev@localhost:5432/lockin',
    'TIMESCALE_URL=postgresql://lockin:lockin_dev@localhost:5433/lockin_events',
    'REDIS_URL=redis://localhost:6379',
    '',
    '# Google OAuth - create credentials at https://console.cloud.google.com',
    'GOOGLE_CLIENT_ID=',
    'GOOGLE_CLIENT_SECRET=',
    '',
    '# NextAuth - any 32+ char random string for local dev',
    'NEXTAUTH_SECRET=change-me-to-a-32-char-random-string',
    'NEXTAUTH_URL=http://localhost:3000',
    '',
    '# LLM providers (not used until slice 5+)',
    'ANTHROPIC_API_KEY=',
    'OPENAI_API_KEY='
)

$envLines | Out-File -FilePath ".env.example" -Encoding UTF8
if (-not (Test-Path ".env.local")) {
    $envLines | Out-File -FilePath ".env.local" -Encoding UTF8
}
Write-Ok ".env.example and .env.local created"

# ---------------------------------------------------------------------------
# 8. .gitignore
# ---------------------------------------------------------------------------

Write-Step "Setting up .gitignore..."

$gitignoreLines = @(
    '# Dependencies',
    'node_modules/',
    '.venv/',
    '__pycache__/',
    '*.pyc',
    '',
    '# Environment',
    '.env',
    '.env.local',
    '.env.*.local',
    '',
    '# Build outputs',
    '.next/',
    'dist/',
    'build/',
    '*.egg-info/',
    '',
    '# IDE',
    '.vscode/',
    '.idea/',
    '*.swp',
    '',
    '# OS',
    '.DS_Store',
    'Thumbs.db',
    '',
    '# Turbo',
    '.turbo/',
    '',
    '# Logs',
    '*.log',
    'npm-debug.log*',
    '',
    '# Testing',
    'coverage/',
    '.pytest_cache/'
)

$gitignoreLines | Out-File -FilePath ".gitignore" -Encoding UTF8
Write-Ok ".gitignore created"

# ---------------------------------------------------------------------------
# 9. Summary and next steps
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Green
Write-Host " Bootstrap complete!" -ForegroundColor Green
Write-Host "===============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Fill in .env.local with real values"
Write-Host "     Most importantly: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
Write-Host "     Get them at: https://console.cloud.google.com/apis/credentials"
Write-Host ""
Write-Host "  2. Start local infrastructure:"
Write-Host "     docker compose -f infra\docker\docker-compose.yml up -d"
Write-Host ""
Write-Host "  3. Verify the databases are healthy:"
Write-Host "     docker compose -f infra\docker\docker-compose.yml ps"
Write-Host ""
Write-Host "  4. Open Claude Code in this directory:"
Write-Host "     claude"
Write-Host ""
Write-Host "  5. Paste this prompt to begin slice 0:"
Write-Host "     'Read CLAUDE.md and docs/CURRENT_SLICE.md, then propose a"
Write-Host "      plan for the current slice. Do not write code yet - show"
Write-Host "      me the plan first, including file structure and any"
Write-Host "      decisions you need me to make.'"
Write-Host ""
