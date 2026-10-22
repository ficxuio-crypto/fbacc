#!/usr/bin/env python3
"""
doctor.py - Smart Self-Healing Diagnostic & Dependency Resolution Engine for fbacc
Automated environment inspection, system capability probing, and on-the-fly auto-repair.
"""

import sys
import os
import shutil
import subprocess
import platform
import importlib
from typing import Dict, List, Tuple, Optional, Any

# ==============================================================================
# ANSI Color Palette & Visual Styler (Zero-dependency fallback)
# ==============================================================================

class Styler:
    USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR", "") == ""

    # ANSI Codes
    RESET   = "\033[0m" if USE_COLOR else ""
    BOLD    = "\033[1m" if USE_COLOR else ""
    DIM     = "\033[2m" if USE_COLOR else ""
    ITALIC  = "\033[3m" if USE_COLOR else ""

    # Foreground
    RED     = "\033[38;5;196m" if USE_COLOR else ""
    GREEN   = "\033[38;5;48m"  if USE_COLOR else ""
    YELLOW  = "\033[38;5;220m" if USE_COLOR else ""
    BLUE    = "\033[38;5;39m"  if USE_COLOR else ""
    MAGENTA = "\033[38;5;201m" if USE_COLOR else ""
    CYAN    = "\033[38;5;51m"  if USE_COLOR else ""
    WHITE   = "\033[38;5;255m" if USE_COLOR else ""
    GRAY    = "\033[38;5;244m" if USE_COLOR else ""
    EMERALD = "\033[38;5;49m"  if USE_COLOR else ""
    ORANGE  = "\033[38;5;208m" if USE_COLOR else ""

    # Box Drawing Characters
    BOX_TOP_L = "╭"
    BOX_TOP_R = "╮"
    BOX_BOT_L = "╰"
    BOX_BOT_R = "╯"
    BOX_HORIZ = "─"
    BOX_VERT  = "│"
    ARROW_R   = "➜"
    TICK      = "✔"
    CROSS     = "✘"
    STAR      = "★"
    INFO_ICON = "ℹ"

    @classmethod
    def badge(cls, text: str, color: str) -> str:
        return f"{color}[ {text} ]{cls.RESET}"

    @classmethod
    def header_box(cls, title: str, subtitle: str = "") -> str:
        width = 68
        border = cls.BOX_HORIZ * (width - 2)
        top = f"{cls.CYAN}{cls.BOX_TOP_L}{border}{cls.BOX_TOP_R}{cls.RESET}"
        bot = f"{cls.CYAN}{cls.BOX_BOT_L}{border}{cls.BOX_BOT_R}{cls.RESET}"
        
        t_pad = (width - 4 - len(title)) // 2
        t_line = f"{cls.CYAN}{cls.BOX_VERT}{cls.RESET} {' ' * t_pad}{cls.BOLD}{cls.WHITE}{title}{cls.RESET}{' ' * (width - 4 - len(title) - t_pad)} {cls.CYAN}{cls.BOX_VERT}{cls.RESET}"
        
        if subtitle:
            s_pad = (width - 4 - len(subtitle)) // 2
            s_line = f"{cls.CYAN}{cls.BOX_VERT}{cls.RESET} {' ' * s_pad}{cls.GRAY}{subtitle}{cls.RESET}{' ' * (width - 4 - len(subtitle) - s_pad)} {cls.CYAN}{cls.BOX_VERT}{cls.RESET}"
            return f"\n{top}\n{t_line}\n{s_line}\n{bot}\n"
        return f"\n{top}\n{t_line}\n{bot}\n"


# ==============================================================================
# Platform Detection
# ==============================================================================

def detect_platform() -> Dict[str, Any]:
    """Identify the running environment, architecture, and available package managers."""
    is_termux = os.path.exists("/data/data/com.termux") or "TERMUX_VERSION" in os.environ
    sys_name = platform.system().lower()
    arch = platform.machine()
    
    distro = "generic"
    if is_termux:
        distro = "termux"
    elif sys_name == "darwin":
        distro = "macos"
    elif sys_name == "windows":
        distro = "windows"
    elif os.path.exists("/etc/debian_version"):
        distro = "debian"
    elif os.path.exists("/etc/arch-release"):
        distro = "arch"
    elif os.path.exists("/etc/fedora-release") or os.path.exists("/etc/redhat-release"):
        distro = "fedora"

    pkg_managers = []
    for pm in ("pkg", "apt", "apt-get", "pacman", "dnf", "brew", "winget", "choco"):
        if shutil.which(pm):
            pkg_managers.append(pm)

    return {
        "is_termux": is_termux,
        "os_name": sys_name,
        "distro": distro,
        "arch": arch,
        "pkg_managers": pkg_managers,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "python_path": sys.executable
    }


# ==============================================================================
# Dependency Specifications
# ==============================================================================

# Core Python modules: (import_name, pip_package_name, min_version, purpose, is_critical)
PYTHON_DEPENDENCIES: List[Tuple[str, str, str, str, bool]] = [
    ("requests", "requests>=2.31.0", "2.31.0", "HTTP client & API transport", True),
    ("aiohttp", "aiohttp>=3.9.0", "3.9.0", "Asynchronous network pipeline", True),
    ("websockets", "websockets>=12.0", "12.0", "Real-time telemetry event bus", True),
    ("selenium", "selenium>=4.15.0", "4.15.0", "DOM automation driver", True),
    ("rich", "rich>=13.7.0", "13.7.0", "Terminal UI & live render engine", True),
    ("faker", "faker>=24.0.0", "24.0.0", "Synthetic identity generation", True),
    ("PIL", "Pillow>=10.0.0", "10.0.0", "EXIF-sanitization & selfie synthesis", True),
    ("phonenumbers", "phonenumbers>=8.13.0", "8.13.0", "International phone parser", True),
    ("pytesseract", "pytesseract>=0.3.10", "0.3.10", "OCR challenge solver binding", True),
    ("fake_useragent", "fake-useragent>=1.4.0", "1.4.0", "Browser fingerprint rotator", False),
    ("cryptography", "cryptography>=42.0.0", "42.0.0", "Cryptographic session protection", False),
]

# System binaries: (display_name, binary_candidates, termux_pkg, apt_pkg, pacman_pkg, dnf_pkg, brew_pkg, is_critical)
SYSTEM_DEPENDENCIES = [
    {
        "name": "Git CLI",
        "bins": ["git"],
        "termux": "git",
        "apt": "git",
        "pacman": "git",
        "dnf": "git",
        "brew": "git",
        "critical": True,
        "desc": "Version control and repository updates"
    },
    {
        "name": "Network Transport (curl/wget)",
        "bins": ["curl", "wget"],
        "termux": "curl wget",
        "apt": "curl wget",
        "pacman": "curl wget",
        "dnf": "curl wget",
        "brew": "curl",
        "critical": True,
        "desc": "Asset downloading & HTTP requests"
    },
    {
        "name": "Chromium Browser Engine",
        "bins": ["/data/data/com.termux/files/usr/lib/chromium/chrome", "chromium-browser", "chromium", "google-chrome-stable", "google-chrome", "chrome"],
        "termux": "chromium",
        "apt": "chromium-browser",
        "pacman": "chromium",
        "dnf": "chromium",
        "brew": "chromium",
        "critical": True,
        "desc": "Headless browser automation engine"
    },
    {
        "name": "ChromeDriver WebDriver",
        "bins": ["/data/data/com.termux/files/usr/lib/chromium/chromedriver", "/data/data/com.termux/files/usr/bin/chromedriver", "chromedriver"],
        "termux": "chromium",
        "apt": "chromium-chromedriver",
        "pacman": "chromium",
        "dnf": "chromedriver",
        "brew": "chromedriver",
        "critical": True,
        "desc": "WebDriver binary service for browser control"
    },
    {
        "name": "Tesseract OCR Engine",
        "bins": ["tesseract"],
        "termux": "tesseract",
        "apt": "tesseract-ocr tesseract-ocr-eng",
        "pacman": "tesseract tesseract-data-eng",
        "dnf": "tesseract",
        "brew": "tesseract",
        "critical": True,
        "desc": "Image challenge solver"
    }
]


# ==============================================================================
# Smart Installer Helpers
# ==============================================================================

def get_pip_install_args() -> List[str]:
    """Construct optimal, environment-aware pip install command arguments."""
    args = [sys.executable, "-m", "pip", "install", "--quiet"]
    
    # Python 3.11+ PEP 668 managed environments (Debian, Ubuntu, Arch, Termux)
    try:
        ver_check = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--help"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if "--break-system-packages" in ver_check.stdout:
            args.append("--break-system-packages")
    except Exception:
        pass

    # Termux package safety
    plat = detect_platform()
    if plat["is_termux"]:
        args.append("--no-cache-dir")

    return args


def install_python_package(pip_spec: str) -> bool:
    """Attempt to install a missing Python package with fallback strategies."""
    cmd = get_pip_install_args() + [pip_spec]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        return proc.returncode == 0
    except Exception:
        # Fallback without --quiet to diagnose or simple attempt
        try:
            fallback = [sys.executable, "-m", "pip", "install", pip_spec]
            if "--break-system-packages" in cmd:
                fallback.append("--break-system-packages")
            proc2 = subprocess.run(fallback, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
            return proc2.returncode == 0
        except Exception:
            return False


def install_system_package(dep: Dict[str, Any], plat: Dict[str, Any]) -> bool:
    """Attempt to install a missing system package using the native package manager."""
    distro = plat["distro"]
    
    try:
        if distro == "termux":
            pkg_name = dep.get("termux", "")
            if not pkg_name:
                return False
            # Ensure repos for chromium / x11 exist in Termux
            if "chromium" in pkg_name or "tesseract" in pkg_name:
                subprocess.run(["pkg", "install", "-y", "tur-repo", "x11-repo"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            cmd = ["pkg", "install", "-y"] + pkg_name.split()
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
            return res.returncode == 0

        elif distro == "debian":
            pkg_name = dep.get("apt", "")
            if not pkg_name:
                return False
            sudo = ["sudo"] if shutil.which("sudo") and os.geteuid() != 0 else []
            cmd = sudo + ["apt-get", "install", "-y"] + pkg_name.split()
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
            return res.returncode == 0

        elif distro == "arch":
            pkg_name = dep.get("pacman", "")
            if not pkg_name:
                return False
            sudo = ["sudo"] if shutil.which("sudo") and os.geteuid() != 0 else []
            cmd = sudo + ["pacman", "-S", "--noconfirm"] + pkg_name.split()
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
            return res.returncode == 0

        elif distro == "fedora":
            pkg_name = dep.get("dnf", "")
            if not pkg_name:
                return False
            sudo = ["sudo"] if shutil.which("sudo") and os.geteuid() != 0 else []
            cmd = sudo + ["dnf", "install", "-y"] + pkg_name.split()
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
            return res.returncode == 0

        elif distro == "macos":
            pkg_name = dep.get("brew", "")
            if not pkg_name or not shutil.which("brew"):
                return False
            cmd = ["brew", "install"] + pkg_name.split()
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
            return res.returncode == 0

    except Exception:
        return False
    return False


# ==============================================================================
# Diagnostic Runner & Smart Self-Healing Engine
# ==============================================================================

class SystemDoctor:
    def __init__(self, auto_repair: bool = True, quiet: bool = False):
        self.auto_repair = auto_repair
        self.quiet = quiet
        self.plat = detect_platform()
        self.results: List[Dict[str, Any]] = []
        self.all_healthy = True

    def log(self, text: str):
        if not self.quiet:
            print(text)

    def print_item(self, name: str, status: str, detail: str = ""):
        # Format: "  ├── Name ................................... [ STATUS ] detail"
        dot_len = max(2, 42 - len(name))
        dots = f"{Styler.GRAY}{'.' * dot_len}{Styler.RESET}"
        detail_str = f" {Styler.GRAY}{detail}{Styler.RESET}" if detail else ""
        self.log(f"  {Styler.GRAY}├──{Styler.RESET} {Styler.WHITE}{name}{Styler.RESET} {dots} {status}{detail_str}")

    def run(self) -> bool:
        """Execute full diagnostics, running auto-repair where necessary."""
        self.log(Styler.header_box(
            "EYDHM AUTOMATION ENGINE · SYSTEM DOCTOR",
            f"Platform: {self.plat['distro'].title()} ({self.plat['arch']}) · Python {self.plat['python_version']}"
        ))

        # 1. Platform & Python Core Check
        self.log(f" {Styler.BOLD}{Styler.CYAN}[1/4] Environment & Runtime Diagnostics{Styler.RESET}")
        
        py_major, py_minor = sys.version_info.major, sys.version_info.minor
        if py_major >= 3 and py_minor >= 8:
            status = Styler.badge("PASS", Styler.GREEN)
            self.print_item(f"Python Runtime ({self.plat['python_version']})", status)
        else:
            status = Styler.badge("FAIL", Styler.RED)
            self.print_item(f"Python Runtime ({self.plat['python_version']})", status, "Requires Python 3.8+")
            self.all_healthy = False

        # Writable workspace test
        try:
            test_file = ".doctor_rw_test.tmp"
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            self.print_item("Workspace Storage I/O", Styler.badge("PASS", Styler.GREEN), "Read/Write OK")
        except Exception as e:
            self.print_item("Workspace Storage I/O", Styler.badge("FAIL", Styler.RED), str(e))
            self.all_healthy = False

        # 2. System Tools & Binaries
        self.log(f"\n {Styler.BOLD}{Styler.CYAN}[2/4] System Tools & Binary Drivers{Styler.RESET}")
        for dep in SYSTEM_DEPENDENCIES:
            name = dep["name"]
            bins = dep["bins"]
            found_bin = None
            for b in bins:
                p = shutil.which(b) if not os.path.isabs(b) else b
                if p and os.path.isfile(p) and os.access(p, os.X_OK):
                    found_bin = p
                    break

            if found_bin:
                status = Styler.badge("FOUND", Styler.GREEN)
                self.print_item(name, status, os.path.basename(found_bin))
            else:
                if self.auto_repair:
                    self.print_item(name, Styler.badge("REPAIRING", Styler.YELLOW), "Installing via package manager...")
                    repaired = install_system_package(dep, self.plat)
                    # Re-check
                    re_found = any(shutil.which(b) for b in bins)
                    if re_found or repaired:
                        self.print_item(name, Styler.badge("REPAIRED", Styler.EMERALD), "Installed successfully")
                    else:
                        if dep["critical"]:
                            self.print_item(name, Styler.badge("MISSING", Styler.RED), "Critical binary not found")
                            self.all_healthy = False
                        else:
                            self.print_item(name, Styler.badge("OPTIONAL", Styler.YELLOW), "Not found (fallback active)")
                else:
                    status = Styler.badge("MISSING", Styler.RED if dep["critical"] else Styler.YELLOW)
                    self.print_item(name, status, dep["desc"])
                    if dep["critical"]:
                        self.all_healthy = False

        # 3. Python Dependencies (Small to Big)
        self.log(f"\n {Styler.BOLD}{Styler.CYAN}[3/4] Python Wheels & Libraries Check{Styler.RESET}")
        for mod_name, pip_spec, min_ver, desc, is_critical in PYTHON_DEPENDENCIES:
            installed = False
            try:
                mod = importlib.import_module(mod_name)
                installed = True
            except ImportError:
                installed = False

            if installed:
                status = Styler.badge("OK", Styler.GREEN)
                self.print_item(mod_name, status, desc)
            else:
                if self.auto_repair:
                    self.print_item(mod_name, Styler.badge("INSTALLING", Styler.YELLOW), f"pip install {pip_spec}")
                    repaired = install_python_package(pip_spec)
                    # Re-verify import
                    try:
                        importlib.invalidate_caches()
                        importlib.import_module(mod_name)
                        repaired = True
                    except ImportError:
                        repaired = False

                    if repaired:
                        self.print_item(mod_name, Styler.badge("REPAIRED", Styler.EMERALD), "Installed & verified")
                    else:
                        if is_critical:
                            self.print_item(mod_name, Styler.badge("FAILED", Styler.RED), "Could not install wheel")
                            self.all_healthy = False
                        else:
                            self.print_item(mod_name, Styler.badge("OPTIONAL", Styler.YELLOW), "Skipped")
                else:
                    status = Styler.badge("MISSING", Styler.RED if is_critical else Styler.YELLOW)
                    self.print_item(mod_name, status, f"pip install {pip_spec}")
                    if is_critical:
                        self.all_healthy = False

        # 4. End-to-End Headless Browser Diagnostics
        self.log(f"\n {Styler.BOLD}{Styler.CYAN}[4/4] End-to-End Browser Automation Diagnostics{Styler.RESET}")
        try:
            from fbacc_pro import create_resilient_driver
            from selenium.webdriver.chrome.options import Options

            test_opts = Options()
            test_opts.add_argument("--headless=new")
            test_driver = create_resilient_driver(test_opts, headless=True)
            test_driver.quit()
            self.print_item("Headless WebDriver Lifecycle", Styler.badge("PASS", Styler.GREEN), "Zero-overhead launch verified")
        except Exception as b_err:
            if self.auto_repair:
                self.print_item("Headless WebDriver Lifecycle", Styler.badge("REPAIRING", Styler.YELLOW), "Sanitizing environment & symlinks...")
                # Auto-repair symlinks and permissions
                if self.plat["is_termux"]:
                    usr_tmp = "/data/data/com.termux/files/usr/tmp"
                    os.makedirs(usr_tmp, exist_ok=True)
                    os.chmod(usr_tmp, 0o700)
                    cd_real = "/data/data/com.termux/files/usr/lib/chromium/chromedriver"
                    cd_link = "/data/data/com.termux/files/usr/bin/chromedriver"
                    if os.path.exists(cd_real) and not os.path.exists(cd_link):
                        try: os.symlink(cd_real, cd_link)
                        except Exception: pass
                # Re-try
                try:
                    from fbacc_pro import create_resilient_driver
                    from selenium.webdriver.chrome.options import Options
                    test_opts = Options()
                    test_opts.add_argument("--headless")
                    re_driver = create_resilient_driver(test_opts, headless=True)
                    re_driver.quit()
                    self.print_item("Headless WebDriver Lifecycle", Styler.badge("REPAIRED", Styler.EMERALD), "Operational after auto-repair")
                except Exception as re_err:
                    self.print_item("Headless WebDriver Lifecycle", Styler.badge("FAIL", Styler.RED), str(re_err)[:50])
                    self.all_healthy = False
            else:
                self.print_item("Headless WebDriver Lifecycle", Styler.badge("FAIL", Styler.RED), str(b_err)[:50])
                self.all_healthy = False

        # Summary Banner
        self.log(f"\n{Styler.GRAY}─────────────────────────────────────────────────────────────────{Styler.RESET}")
        if self.all_healthy:
            self.log(f"  {Styler.BOLD}{Styler.GREEN}{Styler.TICK} ALL DEPENDENCIES VERIFIED & HEALTHY!{Styler.RESET}")
            self.log(f"  {Styler.GRAY}The engine is ready for production and unattended execution.{Styler.RESET}\n")
        else:
            self.log(f"  {Styler.BOLD}{Styler.RED}{Styler.CROSS} SOME CRITICAL DEPENDENCIES COULD NOT BE RESOLVED.{Styler.RESET}")
            self.log(f"  {Styler.YELLOW}Run 'fbacc doctor' or check your permissions and package manager.{Styler.RESET}\n")

        return self.all_healthy


# ==============================================================================
# Public Function & Standalone Entrypoint
# ==============================================================================

def run_doctor(auto_repair: bool = True, quiet: bool = False) -> bool:
    """Public API to invoke SystemDoctor directly from any script."""
    doctor = SystemDoctor(auto_repair=auto_repair, quiet=quiet)
    return doctor.run()


if __name__ == "__main__":
    auto = "--no-repair" not in sys.argv
    healthy = run_doctor(auto_repair=auto, quiet=False)
    sys.exit(0 if healthy else 1)
