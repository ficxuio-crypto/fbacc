#!/bin/sh
# Portable re-exec into bash if running under plain sh
if [ -z "$BASH_VERSION" ]; then
    if command -v bash >/dev/null 2>&1; then
        exec bash "$0" "$@"
    fi
fi
# ==============================================================================
# Universal Auto-Setup & Installer for Facebook Automation Engine (fbacc)
# Supported Platforms: Termux (Android aarch64/arm), Linux (Debian, Ubuntu, Arch, Fedora), macOS
# ==============================================================================

set -e

C_RESET='\033[0m'
C_BOLD='\033[1m'
C_GREEN='\033[38;5;48m'
C_CYAN='\033[38;5;51m'
C_YELLOW='\033[38;5;226m'
C_RED='\033[38;5;196m'
C_GRAY='\033[38;5;244m'

REPO_DEFAULT_URL="https://github.com/theblackkinggamer/fbacc.git"
INSTALL_DIR="${HOME}/fbacc"

echo -e "\n${C_GREEN}${C_BOLD}"
echo "   ███████  ██    ██  ██████   ██   ██  ███    ███"
echo "   ██        ██  ██   ██   ██  ██   ██  ████  ████"
echo "   █████      ████    ██   ██  ███████  ██ ████ ██"
echo "   ██          ██     ██   ██  ██   ██  ██  ██  ██"
echo "   ███████     ██     ██████   ██   ██  ██      ██"
echo -e "${C_RESET}"
echo -e "   ${C_CYAN}${C_BOLD}UNIVERSAL AUTOMATION ENGINE AUTO-SETUP${C_RESET}"
echo -e "   ${C_GRAY}Architecture: Multi-Tier DOM Engine · Async EventBus · Cross-Platform${C_RESET}"
echo -e "   ─────────────────────────────────────────────────────────────────\n"

# 1. Platform Detection
OS_TYPE="unknown"
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

echo -e "   ${C_GREEN}[+] Detected Operating System:${C_RESET} ${C_BOLD}${OS_TYPE}${C_RESET}"

# 2. Package Installation by OS (only installs missing system packages)
echo -e "   ${C_CYAN}[+] Checking system dependencies...${C_RESET}"

case "$OS_TYPE" in
    termux)
        if ! command -v python3 >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1; then
            echo -e "   ${C_CYAN}[+] Installing Termux packages...${C_RESET}"
            pkg install -y python git curl wget tur-repo x11-repo chromium tesseract || true
        else
            echo -e "   ${C_GREEN}[+] Termux core packages already present.${C_RESET}"
        fi
        ;;
    debian)
        if ! command -v python3 >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1 || ! command -v pip3 >/dev/null 2>&1; then
            SUDO=""
            if command -v sudo >/dev/null 2>&1; then SUDO="sudo"; fi
            $SUDO apt update -y
            $SUDO apt install -y python3 python3-pip python3-venv git curl wget chromium-browser chromium-chromedriver tesseract-ocr || \
            $SUDO apt install -y python3 python3-pip python3-venv git curl wget chromium tesseract-ocr || true
        else
            echo -e "   ${C_GREEN}[+] Debian/Ubuntu core packages already present.${C_RESET}"
        fi
        ;;
    arch)
        if ! command -v python3 >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1; then
            SUDO=""
            if command -v sudo >/dev/null 2>&1; then SUDO="sudo"; fi
            $SUDO pacman -Sy --noconfirm python python-pip git curl wget chromium tesseract || true
        else
            echo -e "   ${C_GREEN}[+] Arch core packages already present.${C_RESET}"
        fi
        ;;
    fedora)
        if ! command -v python3 >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1; then
            SUDO=""
            if command -v sudo >/dev/null 2>&1; then SUDO="sudo"; fi
            $SUDO dnf install -y python3 python3-pip git curl wget chromium chromedriver tesseract || true
        else
            echo -e "   ${C_GREEN}[+] Fedora core packages already present.${C_RESET}"
        fi
        ;;
    macos)
        if ! command -v brew >/dev/null 2>&1; then
            echo -e "   ${C_YELLOW}[!] Homebrew not detected. Installing Homebrew...${C_RESET}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        if ! command -v python3 >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1; then
            brew install python git tesseract || true
        else
            echo -e "   ${C_GREEN}[+] macOS core packages already present.${C_RESET}"
        fi
        ;;
    *)
        echo -e "   ${C_YELLOW}[!] Generic Linux detected; ensure python3, pip, and git are installed.${C_RESET}"
        ;;
esac

# 3. Source Directory Resolution
CURRENT_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"

if [ -f "${CURRENT_SCRIPT_DIR}/fbacc.py" ]; then
    TARGET_DIR="${CURRENT_SCRIPT_DIR}"
    echo -e "   ${C_GREEN}[+] Running inside existing repository:${C_RESET} ${TARGET_DIR}"
else
    TARGET_DIR="${INSTALL_DIR}"
    if [ ! -d "${TARGET_DIR}/.git" ]; then
        echo -e "   ${C_CYAN}[+] Cloning repository to:${C_RESET} ${TARGET_DIR}"
        REPO_URL="${FBACC_REPO_URL:-$REPO_DEFAULT_URL}"
        git clone "$REPO_URL" "$TARGET_DIR" || {
            echo -e "   ${C_YELLOW}[!] Git clone failed. Creating target directory directly.${C_RESET}"
            mkdir -p "$TARGET_DIR"
        }
    fi
fi

cd "$TARGET_DIR"

# 4. Python Environment & Dependency Installation
echo -e "   ${C_CYAN}[+] Installing Python dependencies...${C_RESET}"
PYTHON_BIN="python3"
if ! command -v python3 >/dev/null 2>&1; then
    if command -v python >/dev/null 2>&1; then
        PYTHON_BIN="python"
    else
        echo -e "   ${C_RED}[!] Python not found! Please install Python 3.8+${C_RESET}"
        exit 1
    fi
fi

if [ "$OS_TYPE" != "termux" ]; then
    $PYTHON_BIN -m pip install --upgrade pip --quiet || true
fi

if [ -f "requirements.txt" ]; then
    $PYTHON_BIN -m pip install -r requirements.txt --quiet --break-system-packages 2>/dev/null || \
    $PYTHON_BIN -m pip install -r requirements.txt --quiet || true
else
    $PYTHON_BIN -m pip install requests faker selenium rich Pillow phonenumbers websockets aiohttp pytesseract --quiet || true
fi

# 5. Permission & Global Symlink
chmod +x fbacc.py fbacc_pro.py install.sh 2>/dev/null || true

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
#!/usr/bin/env bash
cd "${TARGET_DIR}" && exec "${PYTHON_BIN}" fbacc.py "\$@"
EOF
    chmod +x "$LAUNCHER"
    echo -e "   ${C_GREEN}[+] Created global command:${C_RESET} ${C_BOLD}fbacc${C_RESET}"
fi

# 6. Self-Verification
echo -e "\n   ${C_CYAN}[+] Running self-test QA validation...${C_RESET}"
$PYTHON_BIN fbacc.py --test

echo -e "\n   ${C_GREEN}${C_BOLD}═════════════════════════════════════════════════════════════════${C_RESET}"
echo -e "   ${C_GREEN}${C_BOLD}✔ SETUP COMPLETE!${C_RESET}"
echo -e "   ${C_CYAN}Launch the interactive menu anytime with:${C_RESET}"
echo -e "      ${C_BOLD}fbacc${C_RESET}   ${C_GRAY}(or: cd ${TARGET_DIR} && python3 fbacc.py)${C_RESET}"
echo -e "   ${C_GREEN}${C_BOLD}═════════════════════════════════════════════════════════════════${C_RESET}\n"
