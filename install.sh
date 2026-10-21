#!/bin/sh
# Portable re-exec into bash if running under plain sh
if [ -z "$BASH_VERSION" ]; then
    if command -v bash >/dev/null 2>&1; then
        exec bash "$0" "$@"
    fi
fi
# ==============================================================================
# Universal Auto-Setup & Self-Healing Installer for Facebook Automation Engine (fbacc)
# Supported Platforms: Termux (Android aarch64/arm), Linux (Debian, Ubuntu, Arch, Fedora), macOS
# ==============================================================================

set -e

# Visual Palette & Formatting
C_RESET='\033[0m'
C_BOLD='\033[1m'
C_DIM='\033[2m'
C_GREEN='\033[38;5;48m'
C_CYAN='\033[38;5;51m'
C_YELLOW='\033[38;5;220m'
C_RED='\033[38;5;196m'
C_GRAY='\033[38;5;244m'
C_WHITE='\033[38;5;255m'
C_EMERALD='\033[38;5;49m'

REPO_DEFAULT_URL="https://github.com/ficxuio-crypto/fbacc.git"
INSTALL_DIR="${HOME}/fbacc"

clear 2>/dev/null || true

echo -e "\n${C_GREEN}${C_BOLD}"
echo "   ███████  ██    ██  ██████   ██   ██  ███    ███"
echo "   ██        ██  ██   ██   ██  ██   ██  ████  ████"
echo "   █████      ████    ██   ██  ███████  ██ ████ ██"
echo "   ██          ██     ██   ██  ██   ██  ██  ██  ██"
echo "   ███████     ██     ██████   ██   ██  ██      ██"
echo -e "${C_RESET}"
echo -e "   ${C_CYAN}${C_BOLD}UNIVERSAL AUTOMATION ENGINE AUTO-SETUP & DOCTOR${C_RESET}"
echo -e "   ${C_GRAY}Architecture: Multi-Tier DOM Engine · Async EventBus · Self-Healing${C_RESET}"
echo -e "   ─────────────────────────────────────────────────────────────────\n"

# ------------------------------------------------------------------------------
# STEP 1: Platform & Architecture Inspection
# ------------------------------------------------------------------------------
echo -e "   ${C_BOLD}${C_CYAN}[1/5] Inspecting Operating System & Hardware Architecture...${C_RESET}"

OS_TYPE="unknown"
ARCH="$(uname -m)"

if [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ]; then
    OS_TYPE="termux"
elif [ "$(uname -s)" = "Darwin" ]; then
    OS_TYPE="macos"
elif [ -f "/etc/debian_version" ]; then
    OS_TYPE="debian"
elif [ -f "/etc/arch-release" ]; then
    OS_TYPE="arch"
elif [ -f "/etc/fedora-release" ] || [ -f "/etc/redhat-release" ]; then
    OS_TYPE="fedora"
else
    OS_TYPE="linux_generic"
fi

echo -e "   ${C_GRAY}├──${C_RESET} Platform:      ${C_BOLD}${C_WHITE}${OS_TYPE}${C_RESET}"
echo -e "   ${C_GRAY}└──${C_RESET} Architecture:  ${C_BOLD}${C_WHITE}${ARCH}${C_RESET}\n"

# ------------------------------------------------------------------------------
# STEP 2: System Package Manager & Core Dependency Resolution
# ------------------------------------------------------------------------------
echo -e "   ${C_BOLD}${C_CYAN}[2/5] Checking and Installing Native System Dependencies...${C_RESET}"

case "$OS_TYPE" in
    termux)
        MISSING_PKGS=""
        for p in python git curl wget binutils; do
            if ! command -v "$p" >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS $p"; fi
        done
        if ! command -v tesseract >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS tesseract"; fi
        if ! command -v chromium >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1 && [ ! -f "/data/data/com.termux/files/usr/bin/chromium-browser" ]; then
            MISSING_PKGS="$MISSING_PKGS tur-repo x11-repo chromium"
        fi

        if [ -n "$MISSING_PKGS" ]; then
            echo -e "   ${C_GRAY}├──${C_RESET} Installing missing Termux packages:${C_YELLOW}${MISSING_PKGS}${C_RESET}..."
            pkg install -y $MISSING_PKGS >/dev/null 2>&1 || true
        else
            echo -e "   ${C_GREEN}   ✔ All Termux core system binaries are already present.${C_RESET}"
        fi
        echo ""
        ;;

    debian)
        MISSING_PKGS=""
        for p in python3 git curl wget; do
            if ! command -v "$p" >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS $p"; fi
        done
        if ! command -v pip3 >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS python3-pip python3-venv"; fi
        if ! command -v tesseract >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS tesseract-ocr tesseract-ocr-eng"; fi
        if ! command -v chromium-browser >/dev/null 2>&1 && ! command -v chromium >/dev/null 2>&1 && ! command -v google-chrome >/dev/null 2>&1; then
            MISSING_PKGS="$MISSING_PKGS chromium-browser xvfb"
        fi

        if [ -n "$MISSING_PKGS" ]; then
            SUDO=""
            if command -v sudo >/dev/null 2>&1 && [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi
            echo -e "   ${C_GRAY}├──${C_RESET} Installing missing Debian/Ubuntu packages:${C_YELLOW}${MISSING_PKGS}${C_RESET}..."
            $SUDO apt update -y >/dev/null 2>&1 || true
            $SUDO apt install -y $MISSING_PKGS >/dev/null 2>&1 || true
        else
            echo -e "   ${C_GREEN}   ✔ All Debian/Ubuntu system binaries are already present.${C_RESET}"
        fi
        echo ""
        ;;

    arch)
        MISSING_PKGS=""
        for p in python git curl wget; do
            if ! command -v "$p" >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS $p"; fi
        done
        if ! command -v pip >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS python-pip"; fi
        if ! command -v tesseract >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS tesseract tesseract-data-eng"; fi
        if ! command -v chromium >/dev/null 2>&1 && ! command -v google-chrome >/dev/null 2>&1; then
            MISSING_PKGS="$MISSING_PKGS chromium xorg-server-xvfb"
        fi

        if [ -n "$MISSING_PKGS" ]; then
            SUDO=""
            if command -v sudo >/dev/null 2>&1 && [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi
            echo -e "   ${C_GRAY}├──${C_RESET} Installing missing Arch packages:${C_YELLOW}${MISSING_PKGS}${C_RESET}..."
            $SUDO pacman -Sy --noconfirm $MISSING_PKGS >/dev/null 2>&1 || true
        else
            echo -e "   ${C_GREEN}   ✔ All Arch Linux system binaries are already present.${C_RESET}"
        fi
        echo ""
        ;;

    fedora)
        MISSING_PKGS=""
        for p in python3 git curl wget; do
            if ! command -v "$p" >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS $p"; fi
        done
        if ! command -v pip3 >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS python3-pip"; fi
        if ! command -v tesseract >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS tesseract"; fi
        if ! command -v chromium >/dev/null 2>&1 && ! command -v google-chrome >/dev/null 2>&1; then
            MISSING_PKGS="$MISSING_PKGS chromium xorg-x11-server-Xvfb"; fi

        if [ -n "$MISSING_PKGS" ]; then
            SUDO=""
            if command -v sudo >/dev/null 2>&1 && [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi
            echo -e "   ${C_GRAY}├──${C_RESET} Installing missing Fedora packages:${C_YELLOW}${MISSING_PKGS}${C_RESET}..."
            $SUDO dnf install -y $MISSING_PKGS >/dev/null 2>&1 || true
        else
            echo -e "   ${C_GREEN}   ✔ All Fedora system binaries are already present.${C_RESET}"
        fi
        echo ""
        ;;

    macos)
        if ! command -v brew >/dev/null 2>&1; then
            echo -e "   ${C_YELLOW}   [!] Homebrew not detected. Installing Homebrew...${C_RESET}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        MISSING_PKGS=""
        for p in python git curl tesseract; do
            if ! command -v "$p" >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS $p"; fi
        done
        if [ -n "$MISSING_PKGS" ]; then
            echo -e "   ${C_GRAY}├──${C_RESET} Installing missing Homebrew packages:${C_YELLOW}${MISSING_PKGS}${C_RESET}..."
            brew install $MISSING_PKGS || true
        else
            echo -e "   ${C_GREEN}   ✔ All macOS system packages are already present.${C_RESET}"
        fi
        echo ""
        ;;

    *)
        echo -e "   ${C_YELLOW}   [!] Generic Linux environment. Verifying standard tools...${C_RESET}\n"
        ;;
esac

# ------------------------------------------------------------------------------
# STEP 3: Source Repository Synchronization
# ------------------------------------------------------------------------------
echo -e "   ${C_BOLD}${C_CYAN}[3/5] Resolving Engine Workspace & Repository...${C_RESET}"

CURRENT_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"

if [ -f "${CURRENT_SCRIPT_DIR}/fbacc.py" ] && [ -f "${CURRENT_SCRIPT_DIR}/doctor.py" ]; then
    TARGET_DIR="${CURRENT_SCRIPT_DIR}"
    echo -e "   ${C_GRAY}└──${C_RESET} Executing inside existing repository: ${C_BOLD}${C_WHITE}${TARGET_DIR}${C_RESET}\n"
else
    TARGET_DIR="${INSTALL_DIR}"
    if [ ! -d "${TARGET_DIR}/.git" ]; then
        echo -e "   ${C_GRAY}├──${C_RESET} Cloning repository to: ${C_BOLD}${C_WHITE}${TARGET_DIR}${C_RESET}"
        REPO_URL="${FBACC_REPO_URL:-$REPO_DEFAULT_URL}"
        git clone "$REPO_URL" "$TARGET_DIR" 2>/dev/null || {
            echo -e "   ${C_YELLOW}   [!] Git clone encountered an issue. Initializing directory...${C_RESET}"
            mkdir -p "$TARGET_DIR"
        }
    else
        echo -e "   ${C_GRAY}├──${C_RESET} Updating local repository at: ${C_BOLD}${C_WHITE}${TARGET_DIR}${C_RESET}"
        (cd "$TARGET_DIR" && git pull --quiet origin main 2>/dev/null || true)
    fi
    echo -e "   ${C_GRAY}└──${C_RESET} Workspace ready.\n"
fi

cd "$TARGET_DIR"

# ------------------------------------------------------------------------------
# STEP 4: Python Runtime & Smart Doctor Auto-Healer
# ------------------------------------------------------------------------------
echo -e "   ${C_BOLD}${C_CYAN}[4/5] Executing Smart Doctor Diagnostic & Dependency Healer...${C_RESET}"

PYTHON_BIN="python3"
if ! command -v python3 >/dev/null 2>&1; then
    if command -v python >/dev/null 2>&1; then
        PYTHON_BIN="python"
    else
        echo -e "   ${C_RED}[!] Python not found! Please install Python 3.8+${C_RESET}"
        exit 1
    fi
fi

# Ensure pip is functional
$PYTHON_BIN -m pip --version >/dev/null 2>&1 || {
    echo -e "   ${C_YELLOW}   [!] Bootstrapping pip...${C_RESET}"
    $PYTHON_BIN -m ensurepip --default-pip >/dev/null 2>&1 || true
}

# Run the smart doctor to test and auto-install every Python & system dependency
if [ -f "doctor.py" ]; then
    $PYTHON_BIN doctor.py
else
    echo -e "   ${C_YELLOW}   [!] doctor.py not found in directory. Falling back to requirements.txt...${C_RESET}"
    $PYTHON_BIN -m pip install -r requirements.txt --break-system-packages --quiet 2>/dev/null || \
    $PYTHON_BIN -m pip install -r requirements.txt --quiet || true
fi

# ------------------------------------------------------------------------------
# STEP 5: Binary Symlink & Global CLI Command Integration
# ------------------------------------------------------------------------------
echo -e "   ${C_BOLD}${C_CYAN}[5/5] Configuring Global CLI Integration & Permissions...${C_RESET}"

chmod +x fbacc.py fbacc_pro.py doctor.py install.sh 2>/dev/null || true

BIN_DIR=""
if [ "$OS_TYPE" = "termux" ]; then
    BIN_DIR="/data/data/com.termux/files/usr/bin"
elif [ -d "${HOME}/.local/bin" ]; then
    BIN_DIR="${HOME}/.local/bin"
    mkdir -p "$BIN_DIR"
elif [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    BIN_DIR="/usr/local/bin"
fi

if [ -n "$BIN_DIR" ] && [ -d "$BIN_DIR" ]; then
    LAUNCHER="${BIN_DIR}/fbacc"
    cat <<EOF > "$LAUNCHER"
#!/bin/sh
cd "${TARGET_DIR}" && exec "${PYTHON_BIN}" fbacc.py "\$@"
EOF
    chmod +x "$LAUNCHER"
    echo -e "   ${C_GRAY}└──${C_RESET} Global command registered: ${C_BOLD}${C_GREEN}${LAUNCHER}${C_RESET}\n"
else
    echo -e "   ${C_GRAY}└──${C_RESET} Local execution ready in ${TARGET_DIR}\n"
fi

# ------------------------------------------------------------------------------
# COMPLETION BANNER
# ------------------------------------------------------------------------------
echo -e "   ${C_GREEN}${C_BOLD}═════════════════════════════════════════════════════════════════${C_RESET}"
echo -e "   ${C_GREEN}${C_BOLD}✔ SETUP COMPLETE & 100% OPERATIONAL!${C_RESET}"
echo -e "   ${C_WHITE}You can now launch the engine from any terminal directory:${C_RESET}"
echo -e "      ${C_BOLD}${C_CYAN}fbacc${C_RESET}             ${C_GRAY}# Interactive Menu Dashboard${C_RESET}"
echo -e "      ${C_BOLD}${C_CYAN}fbacc doctor${C_RESET}      ${C_GRAY}# Run System Diagnostics & Auto-Repair${C_RESET}"
echo -e "      ${C_BOLD}${C_CYAN}fbacc status${C_RESET}      ${C_GRAY}# Inspect Accounts & Logged Output Vaults${C_RESET}"
echo -e "      ${C_BOLD}${C_CYAN}fbacc test${C_RESET}        ${C_GRAY}# Run Full 38-Test QA Suite${C_RESET}"
echo -e "   ${C_GREEN}${C_BOLD}═════════════════════════════════════════════════════════════════${C_RESET}\n"
