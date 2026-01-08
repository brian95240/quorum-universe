#!/bin/bash
#
# Quorum Universe - One-Line Deployment Script
# Usage: curl -sSL https://raw.githubusercontent.com/quorum-universe/quorum-universe/main/deploy.sh | bash
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    QUORUM UNIVERSE DEPLOYMENT                     ║"
echo "║           Ambient Intelligence System Installation                ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
echo -e "${GREEN}→ Detected OS: ${OS}${NC}"

# Check Python version
check_python() {
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ $(echo "$PYTHON_VERSION >= 3.11" | bc -l) -eq 1 ]]; then
            PYTHON_CMD="python3"
        else
            echo -e "${RED}✗ Python 3.11+ required. Found: ${PYTHON_VERSION}${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ Python 3 not found. Please install Python 3.11+${NC}"
        exit 1
    fi
    echo -e "${GREEN}→ Using Python: ${PYTHON_CMD}${NC}"
}

check_python

# Check Node.js
check_node() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        if [[ $NODE_VERSION -ge 18 ]]; then
            echo -e "${GREEN}→ Node.js version: $(node -v)${NC}"
        else
            echo -e "${YELLOW}⚠ Node.js 18+ recommended. Found: $(node -v)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Node.js not found. Dashboard will not be available.${NC}"
    fi
}

check_node

# Set installation directory
INSTALL_DIR="${QUORUM_INSTALL_DIR:-$HOME/quorum_universe}"
echo -e "${GREEN}→ Installation directory: ${INSTALL_DIR}${NC}"

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${CYAN}→ Updating existing installation...${NC}"
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo -e "${CYAN}→ Cloning repository...${NC}"
    git clone https://github.com/quorum-universe/quorum-universe.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Create virtual environment
echo -e "${CYAN}→ Setting up Python virtual environment...${NC}"
$PYTHON_CMD -m venv venv

# Activate virtual environment
if [[ "$OS" == "windows" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install Python dependencies
echo -e "${CYAN}→ Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Initialize configuration
echo -e "${CYAN}→ Initializing Quorum Universe configuration...${NC}"
$PYTHON_CMD quorum_core/apex_config.py

# Run tests
echo -e "${CYAN}→ Running closed-loop tests...${NC}"
$PYTHON_CMD quorum_core/closed_loop_test_suite.py

# Configure delta sync
echo -e "${CYAN}→ Configuring delta sync (default: weekly)...${NC}"
mkdir -p ~/.quorum/config
mkdir -p ~/.quorum/deltas
cat > ~/.quorum/config/update_interval << DELTAEOF
{
  "interval": "weekly",
  "daily_hour": 3,
  "weekly_day": 0,
  "monthly_day": 1
}
DELTAEOF
echo -e "${GREEN}→ Delta sync configured (weekly updates at 3 AM Sunday)${NC}"

# Install dashboard dependencies (if Node.js available)
if command -v node &> /dev/null && [ -d "quorum-dashboard" ]; then
    echo -e "${CYAN}→ Installing dashboard dependencies...${NC}"
    cd quorum-dashboard
    if command -v pnpm &> /dev/null; then
        pnpm install
    elif command -v npm &> /dev/null; then
        npm install
    fi
    cd ..
fi

# Create systemd service (Linux only)
if [[ "$OS" == "linux" ]] && command -v systemctl &> /dev/null; then
    echo -e "${CYAN}→ Creating systemd service...${NC}"
    
    SERVICE_FILE="/etc/systemd/system/quorum-universe.service"
    
    sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=Quorum Universe API Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python quorum_core/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    echo -e "${GREEN}→ Systemd service created. Enable with: sudo systemctl enable quorum-universe${NC}"
fi

# Print success message
echo ""
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              QUORUM UNIVERSE INSTALLATION COMPLETE                ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${CYAN}To start the API server:${NC}"
echo "  cd $INSTALL_DIR"
echo "  source venv/bin/activate"
echo "  python quorum_core/api_server.py"
echo ""
echo -e "${CYAN}To start the React dashboard:${NC}"
echo "  cd $INSTALL_DIR/quorum-dashboard"
echo "  pnpm dev"
echo ""
echo -e "${CYAN}To start the Admin dashboard (mobile-friendly):${NC}"
echo "  python 'Source Code/admin_dashboard.py'"
echo ""
echo -e "${CYAN}To sync knowledge deltas:${NC}"
echo "  python quorum_core/delta_sync.py sync"
echo "  python quorum_core/delta_sync.py set-interval --interval daily"
echo ""
echo -e "${CYAN}API will be available at:${NC} http://localhost:8000"
echo -e "${CYAN}Dashboard will be available at:${NC} http://localhost:3000"
echo ""
echo -e "${GREEN}Documentation: https://docs.quorum-universe.io${NC}"
echo ""
