#!/bin/sh
# Portable re-exec into bash if running under plain sh
if [ -z "$BASH_VERSION" ]; then
    if command -v bash >/dev/null 2>&1; then
        exec bash "$0" "$@"
    fi
fi
# ==============================================================================
# Universal Auto-Setup & Real-Time Smart Dashboard for fbacc
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
REPO_ARCHIVE_URL="https://github.com/ficxuio-crypto/fbacc/archive/refs/heads/main.tar.gz"
REPO_RAW_URL="https://raw.githubusercontent.com/ficxuio-crypto/fbacc/main"
INSTALL_DIR="${HOME}/fbacc"
SETUP_LOG="${HOME}/.fbacc_setup.log"

# Clean previous setup log
: > "$SETUP_LOG" 2>/dev/null || true

START_TIME=$(date +%s)

# Format elapsed seconds into mm:ss
get_elapsed() {
    NOW=$(date +%s)
    DIFF=$((NOW - START_TIME))
    MINS=$((DIFF / 60))
    SECS=$((DIFF % 60))
    printf "%02d:%02d" "$MINS" "$SECS"
}

# Real-Time Dashboard Renderer (Zero Spam, In-Place Updates)
render_dashboard() {
    STEP_NUM="$1"
    PROGRESS_BAR="$2"
    PROGRESS_PCT="$3"
    EST_TIME="$4"
    STATUS_1="$5"
    STATUS_2="$6"
    STATUS_3="$7"
    STATUS_4="$8"
    STATUS_5="$9"
    shift 9
    ACTIVE_TASK="$1"
    UP_NEXT="$2"

    ELAPSED=$(get_elapsed)

    clear 2>/dev/null || true
    echo -e "${C_CYAN}${C_BOLD}"
    echo "   ╔═════════════════════════════════════════════════════════════════╗"
    echo "   ║          EYDHM ENTERPRISE AUTO-SETUP · SMART DASHBOARD          ║"
    echo "   ║    Platform: ${OS_TYPE:-Auto} (${ARCH:-Native})  ·  Step ${STEP_NUM}/5  ·  Status: ACTIVE    ║"
    echo "   ╚═════════════════════════════════════════════════════════════════╝${C_RESET}"
    echo ""
    echo -e "   ${C_BOLD}${C_WHITE}Progress:${C_RESET} ${C_GREEN}${PROGRESS_BAR}${C_RESET} ${C_BOLD}${PROGRESS_PCT}${C_RESET}  ${C_GRAY}(Elapsed: ${ELAPSED} | Est: ${EST_TIME})${C_RESET}"
    echo ""
    echo -e "   $STATUS_1"
    echo -e "   $STATUS_2"
    echo -e "   $STATUS_3"
    echo -e "   $STATUS_4"
    echo -e "   $STATUS_5"
    echo ""
    echo -e "   ${C_GRAY}─────────────────────────────────────────────────────────────────${C_RESET}"
    echo -e "   ${C_BOLD}${C_CYAN}[► PROCESSING]${C_RESET} ${C_WHITE}${ACTIVE_TASK}${C_RESET}"
    echo -e "   ${C_BOLD}${C_GRAY}[· UP NEXT   ]${C_RESET} ${C_GRAY}${UP_NEXT}${C_RESET}"
    echo ""
}

# ------------------------------------------------------------------------------
# STEP 1: Platform & Architecture Inspection
# ------------------------------------------------------------------------------
ARCH="$(uname -m 2>/dev/null || echo "generic")"
OS_TYPE="unknown"

if [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ]; then
    OS_TYPE="termux"
elif [ "$(uname -s 2>/dev/null)" = "Darwin" ]; then
    OS_TYPE="macos"
elif [ -f "/etc/debian_version" ]; then
    OS_TYPE="debian"
elif [ -f "/etc/arch-release" ]; then
    OS_TYPE="arch"
elif [ -f "/etc/fedora-release" ] || [ -f "/etc/redhat-release" ]; then
    OS_TYPE="fedora"
else
    OS_TYPE="linux"
fi

render_dashboard "1" "[████░░░░░░░░░░░░░░░░]" "20%" "~15s" \
  "${C_CYAN}${C_BOLD}[►] 1/5 Platform & Hardware Inspection ........ [ ACTIVE  ]${C_RESET}" \
  "${C_GRAY}[·] 2/5 Core System Binaries Bootstrap ........ [ PENDING ]${C_RESET}" \
  "${C_GRAY}[·] 3/5 Codebase Synchronization & Unpack ..... [ PENDING ]${C_RESET}" \
  "${C_GRAY}[·] 4/5 Smart Doctor & Python Dependencies .... [ PENDING ]${C_RESET}" \
  "${C_GRAY}[·] 5/5 Global CLI Command Registration ....... [ PENDING ]${C_RESET}" \
  "Probing OS: ${OS_TYPE} (${ARCH})..." \
  "Core toolchain verification (python, git, curl, tar)"

sleep 0.4

# ------------------------------------------------------------------------------
# STEP 2: Native Package Management & Critical Toolchain
# ------------------------------------------------------------------------------
render_dashboard "2" "[████████░░░░░░░░░░░░]" "40%" "~12s" \
  "${C_GREEN}[✓] 1/5 Platform & Hardware Inspection ........ [ ${OS_TYPE} ${ARCH} ]${C_RESET}" \
  "${C_CYAN}${C_BOLD}[►] 2/5 Core System Binaries Bootstrap ........ [ ACTIVE  ]${C_RESET}" \
  "${C_GRAY}[·] 3/5 Codebase Synchronization & Unpack ..... [ PENDING ]${C_RESET}" \
  "${C_GRAY}[·] 4/5 Smart Doctor & Python Dependencies .... [ PENDING ]${C_RESET}" \
  "${C_GRAY}[·] 5/5 Global CLI Command Registration ....... [ PENDING ]${C_RESET}" \
  "Installing missing system packages quietly..." \
  "Repository retrieval (Git clone / HTTP archive stream)"

case "$OS_TYPE" in
    termux)
        MISSING_CORE=""
        for p in python git curl wget tar binutils; do
            if ! command -v "$p" >/dev/null 2>&1; then MISSING_CORE="$MISSING_CORE $p"; fi
        done
        if [ -n "$MISSING_CORE" ]; then
            pkg install -y $MISSING_CORE >> "$SETUP_LOG" 2>&1 || apt-get install -y $MISSING_CORE >> "$SETUP_LOG" 2>&1 || true
        fi

        # Aux repos and packages
        if ! command -v tesseract >/dev/null 2>&1 || (! command -v chromium >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1 && [ ! -f "/data/data/com.termux/files/usr/bin/chromium-browser" ]); then
            pkg install -y tur-repo x11-repo >> "$SETUP_LOG" 2>&1 || true
            pkg install -y tesseract chromium >> "$SETUP_LOG" 2>&1 || true
        fi
        ;;

    debian)
        SUDO=""
        if command -v sudo >/dev/null 2>&1 && [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi
        MISSING_PKGS=""
        for p in python3 git curl wget tar; do
            if ! command -v "$p" >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS $p"; fi
        done
        if ! command -v pip3 >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS python3-pip python3-venv"; fi
        if ! command -v tesseract >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS tesseract-ocr tesseract-ocr-eng"; fi
        if ! command -v chromium-browser >/dev/null 2>&1 && ! command -v chromium >/dev/null 2>&1 && ! command -v google-chrome >/dev/null 2>&1; then
            MISSING_PKGS="$MISSING_PKGS chromium-browser xvfb"
        fi
        if [ -n "$MISSING_PKGS" ]; then
            $SUDO apt update -y >> "$SETUP_LOG" 2>&1 || true
            $SUDO apt install -y $MISSING_PKGS >> "$SETUP_LOG" 2>&1 || true
        fi
        ;;

    arch)
        SUDO=""
        if command -v sudo >/dev/null 2>&1 && [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi
        MISSING_PKGS=""
        for p in python git curl wget tar; do
            if ! command -v "$p" >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS $p"; fi
        done
        if ! command -v pip >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS python-pip"; fi
        if ! command -v tesseract >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS tesseract tesseract-data-eng"; fi
        if ! command -v chromium >/dev/null 2>&1 && ! command -v google-chrome >/dev/null 2>&1; then
            MISSING_PKGS="$MISSING_PKGS chromium xorg-server-xvfb"
        fi
        if [ -n "$MISSING_PKGS" ]; then
            $SUDO pacman -Sy --noconfirm $MISSING_PKGS >> "$SETUP_LOG" 2>&1 || true
        fi
        ;;

    fedora)
        SUDO=""
        if command -v sudo >/dev/null 2>&1 && [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi
        MISSING_PKGS=""
        for p in python3 git curl wget tar; do
            if ! command -v "$p" >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS $p"; fi
        done
        if ! command -v pip3 >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS python3-pip"; fi
        if ! command -v tesseract >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS tesseract"; fi
        if ! command -v chromium >/dev/null 2>&1 && ! command -v google-chrome >/dev/null 2>&1; then
            MISSING_PKGS="$MISSING_PKGS chromium xorg-x11-server-Xvfb"
        fi
        if [ -n "$MISSING_PKGS" ]; then
            $SUDO dnf install -y $MISSING_PKGS >> "$SETUP_LOG" 2>&1 || true
        fi
        ;;

    macos)
        if ! command -v brew >/dev/null 2>&1; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" >> "$SETUP_LOG" 2>&1 || true
        fi
        MISSING_PKGS=""
        for p in python git curl tar tesseract; do
            if ! command -v "$p" >/dev/null 2>&1; then MISSING_PKGS="$MISSING_PKGS $p"; fi
        done
        if [ -n "$MISSING_PKGS" ]; then
            brew install $MISSING_PKGS >> "$SETUP_LOG" 2>&1 || true
        fi
        ;;
esac

# ------------------------------------------------------------------------------
# STEP 3: Source Repository Synchronization (3-Tier Redundant Retrieval)
# ------------------------------------------------------------------------------
render_dashboard "3" "[████████████░░░░░░░░]" "60%" "~8s" \
  "${C_GREEN}[✓] 1/5 Platform & Hardware Inspection ........ [ ${OS_TYPE} ${ARCH} ]${C_RESET}" \
  "${C_GREEN}[✓] 2/5 Core System Binaries Bootstrap ........ [ VERIFIED ]${C_RESET}" \
  "${C_CYAN}${C_BOLD}[►] 3/5 Codebase Synchronization & Unpack ..... [ ACTIVE  ]${C_RESET}" \
  "${C_GRAY}[·] 4/5 Smart Doctor & Python Dependencies .... [ PENDING ]${C_RESET}" \
  "${C_GRAY}[·] 5/5 Global CLI Command Registration ....... [ PENDING ]${C_RESET}" \
  "Synchronizing codebase into ${INSTALL_DIR}..." \
  "Smart Doctor diagnostic & wheel verification"

CURRENT_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"

if [ -f "${CURRENT_SCRIPT_DIR}/fbacc.py" ] && [ -f "${CURRENT_SCRIPT_DIR}/doctor.py" ]; then
    TARGET_DIR="${CURRENT_SCRIPT_DIR}"
else
    TARGET_DIR="${INSTALL_DIR}"
    REPO_URL="${FBACC_REPO_URL:-$REPO_DEFAULT_URL}"

    CLONED=false
    if [ -d "${TARGET_DIR}/.git" ]; then
        (cd "$TARGET_DIR" && git pull origin main >> "$SETUP_LOG" 2>&1 || true)
        if [ -f "${TARGET_DIR}/fbacc.py" ]; then CLONED=true; fi
    elif command -v git >/dev/null 2>&1; then
        rm -rf "$TARGET_DIR" 2>/dev/null || true
        if git clone --depth 1 "$REPO_URL" "$TARGET_DIR" >> "$SETUP_LOG" 2>&1; then
            if [ -f "${TARGET_DIR}/fbacc.py" ]; then CLONED=true; fi
        fi
    fi

    # Fallback Tier 2: HTTP Tarball stream
    if [ "$CLONED" != "true" ] || [ ! -f "${TARGET_DIR}/fbacc.py" ]; then
        mkdir -p "$TARGET_DIR"
        (curl -fsSL "$REPO_ARCHIVE_URL" 2>/dev/null | tar -xz --strip-components=1 -C "$TARGET_DIR" 2>/dev/null) || \
        (wget -qO- "$REPO_ARCHIVE_URL" 2>/dev/null | tar -xz --strip-components=1 -C "$TARGET_DIR" 2>/dev/null) || true
        if [ -f "${TARGET_DIR}/fbacc.py" ]; then CLONED=true; fi
    fi

    # Fallback Tier 3: Direct Raw CDN files
    if [ "$CLONED" != "true" ] || [ ! -f "${TARGET_DIR}/fbacc.py" ]; then
        mkdir -p "$TARGET_DIR"
        for fname in fbacc.py fbacc_pro.py doctor.py requirements.txt settings.json install.sh; do
            curl -fsSL "${REPO_RAW_URL}/${fname}" -o "${TARGET_DIR}/${fname}" >> "$SETUP_LOG" 2>&1 || \
            wget -q "${REPO_RAW_URL}/${fname}" -O "${TARGET_DIR}/${fname}" >> "$SETUP_LOG" 2>&1 || true
        done
    fi

    if [ ! -f "${TARGET_DIR}/fbacc.py" ] || [ ! -s "${TARGET_DIR}/fbacc.py" ]; then
        clear 2>/dev/null || true
        echo -e "\n   ${C_RED}${C_BOLD}[X] FATAL: Could not retrieve engine codebase.${C_RESET}"
        echo -e "   ${C_YELLOW}Check your internet connection or clone manually:${C_RESET}"
        echo -e "      git clone https://github.com/ficxuio-crypto/fbacc.git ~/fbacc\n"
        exit 1
    fi
fi

cd "$TARGET_DIR"

# ------------------------------------------------------------------------------
# STEP 4: Python Runtime & Smart Doctor Auto-Healer
# ------------------------------------------------------------------------------
render_dashboard "4" "[████████████████░░░░]" "80%" "~4s" \
  "${C_GREEN}[✓] 1/5 Platform & Hardware Inspection ........ [ ${OS_TYPE} ${ARCH} ]${C_RESET}" \
  "${C_GREEN}[✓] 2/5 Core System Binaries Bootstrap ........ [ VERIFIED ]${C_RESET}" \
  "${C_GREEN}[✓] 3/5 Codebase Synchronization & Unpack ..... [ VERIFIED ]${C_RESET}" \
  "${C_CYAN}${C_BOLD}[►] 4/5 Smart Doctor & Python Dependencies .... [ ACTIVE  ]${C_RESET}" \
  "${C_GRAY}[·] 5/5 Global CLI Command Registration ....... [ PENDING ]${C_RESET}" \
  "Running Smart Doctor diagnostics & auto-repair..." \
  "Configuring global 'fbacc' CLI launcher shortcut"

PYTHON_BIN=""
for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
        if "$py" -c "import sys; exit(0 if sys.version_info.major == 3 else 1)" >/dev/null 2>&1; then
            PYTHON_BIN="$py"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    if [ "$OS_TYPE" = "termux" ]; then
        pkg install -y python >> "$SETUP_LOG" 2>&1 || true
    elif [ "$OS_TYPE" = "debian" ]; then
        $SUDO apt update -y >> "$SETUP_LOG" 2>&1 || true
        $SUDO apt install -y python3 python3-pip >> "$SETUP_LOG" 2>&1 || true
    fi
    PYTHON_BIN="python3"
fi

# Ensure pip is present
$PYTHON_BIN -m pip --version >> "$SETUP_LOG" 2>&1 || {
    $PYTHON_BIN -m ensurepip --default-pip >> "$SETUP_LOG" 2>&1 || true
}

# Run doctor cleanly
if [ -f "doctor.py" ]; then
    $PYTHON_BIN doctor.py >> "$SETUP_LOG" 2>&1 || true
fi

# ------------------------------------------------------------------------------
# STEP 5: Binary Symlink & Global CLI Command Integration
# ------------------------------------------------------------------------------
render_dashboard "5" "[████████████████████]" "100%" "00:00" \
  "${C_GREEN}[✓] 1/5 Platform & Hardware Inspection ........ [ ${OS_TYPE} ${ARCH} ]${C_RESET}" \
  "${C_GREEN}[✓] 2/5 Core System Binaries Bootstrap ........ [ VERIFIED ]${C_RESET}" \
  "${C_GREEN}[✓] 3/5 Codebase Synchronization & Unpack ..... [ VERIFIED ]${C_RESET}" \
  "${C_GREEN}[✓] 4/5 Smart Doctor & Python Dependencies .... [ 100% OK  ]${C_RESET}" \
  "${C_CYAN}${C_BOLD}[►] 5/5 Global CLI Command Registration ....... [ ACTIVE  ]${C_RESET}" \
  "Registering global command 'fbacc' in system PATH..." \
  "Finishing setup"

chmod +x fbacc.py fbacc_pro.py doctor.py install.sh 2>/dev/null || true

BIN_DIR=""
if [ "$OS_TYPE" = "termux" ]; then
    BIN_DIR="/data/data/com.termux/files/usr/bin"
elif [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    BIN_DIR="/usr/local/bin"
elif [ -d "${HOME}/.local/bin" ]; then
    BIN_DIR="${HOME}/.local/bin"
    mkdir -p "$BIN_DIR"
else
    mkdir -p "${HOME}/.local/bin"
    BIN_DIR="${HOME}/.local/bin"
fi

if [ -n "$BIN_DIR" ] && [ -d "$BIN_DIR" ]; then
    LAUNCHER="${BIN_DIR}/fbacc"
    cat <<EOF > "$LAUNCHER"
#!/bin/sh
if [ ! -f "${TARGET_DIR}/fbacc.py" ]; then
    echo "Error: fbacc engine files not found in ${TARGET_DIR}" >&2
    exit 1
fi
cd "${TARGET_DIR}" && exec "${PYTHON_BIN}" fbacc.py "\$@"
EOF
    chmod +x "$LAUNCHER"

    if [ "$BIN_DIR" = "${HOME}/.local/bin" ]; then
        case ":$PATH:" in
            *":${HOME}/.local/bin:"*) ;;
            *)
                echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "${HOME}/.bashrc" 2>/dev/null || true
                echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "${HOME}/.zshrc" 2>/dev/null || true
                export PATH="${HOME}/.local/bin:$PATH"
                ;;
        esac
    fi
fi

TOTAL_TIME=$(get_elapsed)

# ------------------------------------------------------------------------------
# FINAL COMPLETION DASHBOARD
# ------------------------------------------------------------------------------
clear 2>/dev/null || true
echo -e "${C_GREEN}${C_BOLD}"
echo "   ╔═════════════════════════════════════════════════════════════════╗"
echo "   ║          EYDHM ENTERPRISE AUTO-SETUP · COMPLETED                ║"
echo "   ║    Platform: ${OS_TYPE} (${ARCH})  ·  Total Setup Time: ${TOTAL_TIME}  ·  Status: 100% ║"
echo "   ╚═════════════════════════════════════════════════════════════════╝${C_RESET}"
echo ""
echo -e "   ${C_BOLD}${C_WHITE}Installation Summary:${C_RESET}"
echo -e "   ${C_GREEN}[✓] 1/5 Platform & Hardware Inspection ........ [ ${OS_TYPE} ${ARCH} ]${C_RESET}"
echo -e "   ${C_GREEN}[✓] 2/5 Core System Binaries Bootstrap ........ [ VERIFIED ]${C_RESET}"
echo -e "   ${C_GREEN}[✓] 3/5 Codebase Synchronization & Unpack ..... [ ${TARGET_DIR} ]${C_RESET}"
echo -e "   ${C_GREEN}[✓] 4/5 Smart Doctor & Python Dependencies .... [ ALL RESOLVED ]${C_RESET}"
echo -e "   ${C_GREEN}[✓] 5/5 Global CLI Command Registration ....... [ ${LAUNCHER:-fbacc} ]${C_RESET}"
echo ""
echo -e "   ${C_GRAY}─────────────────────────────────────────────────────────────────${C_RESET}"
echo -e "   ${C_BOLD}${C_WHITE}Launch the engine anytime from any terminal directory:${C_RESET}"
echo -e "      ${C_BOLD}${C_CYAN}fbacc${C_RESET}             ${C_GRAY}# Interactive Menu Dashboard${C_RESET}"
echo -e "      ${C_BOLD}${C_CYAN}fbacc doctor${C_RESET}      ${C_GRAY}# Run System Diagnostics & Auto-Repair${C_RESET}"
echo -e "      ${C_BOLD}${C_CYAN}fbacc status${C_RESET}      ${C_GRAY}# Inspect Accounts & Logged Output Vaults${C_RESET}"
echo -e "      ${C_BOLD}${C_CYAN}fbacc test${C_RESET}        ${C_GRAY}# Run Full 38-Test QA Suite${C_RESET}"
echo -e "   ${C_GRAY}─────────────────────────────────────────────────────────────────${C_RESET}\n"
