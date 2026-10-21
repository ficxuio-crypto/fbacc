# Facebook Automation & Account Recovery Engine (fbacc)

[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue?logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Termux%20%7C%20Linux%20%7C%20macOS%20%7C%20Windows-brightgreen?logo=linux&logoColor=white)](https://github.com/ficxuio-crypto/fbacc)
[![Architecture](https://img.shields.io/badge/architecture-Async%20EventBus%20%7C%20Multi--Tier%20DOM-orange)](#-architecture--design)
[![QA Tests](https://img.shields.io/badge/tests-38%2F38%20passing%20(100%25)-emerald?logo=checkmarx&logoColor=white)](#-qa-validation--testing)
[![Self-Healing Doctor](https://img.shields.io/badge/doctor-self--healing%20auto--repair-cyan)](#-smart-self-healing-doctor-doctorpy)
[![License](https://img.shields.io/badge/license-MIT-purple)](#license)

Enterprise-grade asynchronous DOM automation engine and recovery suite for Facebook account provisioning, OTP dispatch, account password recovery, identity challenge appeals, and Graph API liveness health auditing. Built from the ground up for high-concurrency cross-platform execution on **Android Termux (aarch64/arm)**, **Linux (Debian, Ubuntu, Arch, Fedora)**, **macOS**, and **Windows**.

---

## ⚡ Instant One-Line Auto-Install

Run this single command on **Termux (Android)**, **Linux**, or **macOS** to auto-detect your OS, bootstrap Python, auto-install missing system and Python packages via the **Smart Doctor**, and configure a global `fbacc` command:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ficxuio-crypto/fbacc/main/install.sh)
```

### Windows (PowerShell)
Run from PowerShell as Administrator:

```powershell
irm https://raw.githubusercontent.com/ficxuio-crypto/fbacc/main/install.ps1 | iex
```

---

## 🏗️ Project Architecture & Repository Structure

```
fbacc/
├── fbacc.py               # Master CLI dispatcher & smart auto-healing entrypoint
├── fbacc_pro.py           # Core E2E automation & async state machine engine (350KB)
├── doctor.py              # Self-healing diagnostic & dependency auto-repair engine
├── install.sh             # Universal POSIX/Bash cross-platform auto-installer
├── install.ps1            # Native Windows PowerShell auto-installer
├── requirements.txt       # Pinned production Python wheels
├── settings.json          # Persistent engine configuration & proxy routing
├── .gitignore             # Strict exclusion for credentials, cookies, and tokens
├── accounts_log.txt       # Detailed creation audit vault
├── phone_accounts.txt     # Harvested accounts (c_user, phone, password, cookies)
├── successful_recovery.txt# Recovered checkpoint accounts
├── reco_sms.txt           # Recovery OTP dispatch records
├── default_selfie.jpg     # Stock reference photo for synthetic appeal generation
└── synthetic_camera.y4m   # Virtual video feed for video KYC injection
```

---

## 🩺 Smart Self-Healing Doctor (`doctor.py`)

No more `ModuleNotFoundError` or missing binary headaches! The built-in **Smart Doctor** automatically probes your environment before execution, verifies every runtime package (from small helper utilities to large browser automation drivers), and **automatically installs missing dependencies on the fly** with a sleek terminal dashboard:

```
╭──────────────────────────────────────────────────────────────────╮
│             EYDHM AUTOMATION ENGINE · SYSTEM DOCTOR              │
│            Platform: Termux (aarch64) · Python 3.14.6            │
╰──────────────────────────────────────────────────────────────────╯

 [1/3] Environment & Runtime Diagnostics
  ├── Python Runtime (3.14.6) ................... [ PASS ]
  ├── Workspace Storage I/O ..................... [ PASS ] Read/Write OK

 [2/3] System Tools & Binary Drivers
  ├── Git CLI ................................... [ FOUND ] git
  ├── Network Transport (curl/wget) ............. [ FOUND ] curl
  ├── Chromium Browser Engine ................... [ FOUND ] chromium-browser
  ├── Tesseract OCR Engine ...................... [ FOUND ] tesseract

 [3/3] Python Wheels & Libraries Check
  ├── requests .................................. [ OK ] HTTP client & API transport
  ├── aiohttp ................................... [ OK ] Asynchronous network pipeline
  ├── websockets ................................ [ OK ] Real-time telemetry event bus
  ├── selenium .................................. [ OK ] DOM automation driver
  ├── rich ...................................... [ OK ] Terminal UI & live render engine
  ├── faker ..................................... [ OK ] Synthetic identity generation
  ├── PIL ....................................... [ OK ] EXIF-sanitization & selfie synthesis
  ├── phonenumbers .............................. [ OK ] International phone parser
  ├── pytesseract ............................... [ OK ] OCR challenge solver binding
  ├── fake_useragent ............................ [ OK ] Browser fingerprint rotator
  ├── cryptography .............................. [ OK ] Cryptographic session protection

─────────────────────────────────────────────────────────────────
  ✔ ALL DEPENDENCIES VERIFIED & HEALTHY!
```

To run diagnostics manually anytime:
```bash
fbacc doctor
# or
python3 doctor.py
```

---

## 🚀 Key Modules & Capabilities

| Module | Subcommand | Functionality & Invariants |
|---|---|---|
| **System Doctor** | `fbacc doctor` | Visual diagnostic check; auto-installs missing Python packages & system binaries. |
| **System Status** | `fbacc status` | Displays environment specs, `settings.json` parameters, and account metrics. |
| **Interactive Menu**| `fbacc` | Full-screen Rich interactive dashboard with 9 specialized workflows. |
| **Account Creation**| `fbacc register` | Full automated multi-step registration (names, DOB, gender, password, contact). |
| **90% Phone Create**| `fbacc register --contact-mode phone` | Provisions account up to SMS OTP barrier, harvests `c_user`, password, & cookies. |
| **Account Recovery**| `fbacc recover` | Recovers checkpoint accounts with Phone-OTP pairs; handles "Try another way". |
| **Reset OTP Dispatch**| `fbacc reset-otp` | Multi-round password reset SMS dispatcher (`driver.back()` loops, 1-1000 rounds). |
| **Hybrid Pipeline**| `fbacc hybrid` | Chained execution: Phase 1 (90% Phone Create) + Phase 2 (Reset OTP Dispatch). |
| **Liveness Auditor**| `fbacc check-live` | Real-time Facebook Graph API `/picture` routing and HTTP status code verification. |
| **QA Test Suite** | `fbacc test` | Runs the internal 38/38 unit test suite verifying all parsers and invariants. |

---

## 💻 CLI Command Reference & Examples

### 1. Interactive Menu
Simply run:
```bash
fbacc
```

### 2. High-Speed Headless Account Creation
```bash
# Register using phones from file in ultra mode (cookie wipe, instant execution)
fbacc register --contact-source phones.txt --mode ultra --headless

# Register with explicit count and custom password
fbacc register --count 5 --password "SecretPass@2026" --mode instant
```

### 3. Checkpoint Account Recovery
```bash
# Recover accounts from phone-OTP pairs file
fbacc recover --pairs recovery_pairs.txt --mode ultra

# Single target inline recovery
fbacc recover --pairs "+393300962123,699632" --mode instant
```

### 4. Reset OTP Multi-Round Dispatch
```bash
# Dispatch 3 consecutive recovery OTP SMS rounds to target list
fbacc reset-otp --pairs targets.txt --reco-rounds 3 --mode ultra
```

### 5. Graph API Account Liveness Health Audit
```bash
# Audit all created c_users in phone_accounts.txt
fbacc check-live phone_accounts.txt

# Audit specific c_user directly
fbacc check-live 61595607657979
```

---

## ⚙️ Persistent Configuration (`settings.json`)

Engine parameters can be persisted across sessions via `settings.json`:

```json
{
  "default_password": "MyStrongPassword@2026",
  "default_mode": "instant",
  "default_endpoint": "limited",
  "kyc_image_url": "https://i.ibb.co.com/jkJ9cNZf/IMG-8bdbd8b0.jpg",
  "proxy": null,
  "proxy_pool": [],
  "proxy_routing": {
    "opt1": "disabled",
    "opt3": "disabled",
    "opt5": "before_otp_random",
    "opt6": "disabled",
    "opt7": "disabled"
  },
  "delay": 1.0,
  "email_provider": "tempmail_lol"
}
```

---

## 🧠 Core Engineering Invariants

1. **Self-Healing Environment Layer (`doctor.py`):**
   - Automatically probes system packages (`chromium`, `tesseract`, `git`, `curl`) and Python wheels (`requests`, `selenium`, `rich`, `Pillow`, `faker`, `phonenumbers`, `pytesseract`, `fake-useragent`, `cryptography`).
   - Automatically detects PEP 668 managed environments (Debian 12+, Ubuntu 24.04+, Termux) and passes appropriate `--break-system-packages` and `--no-cache-dir` flags.
2. **Post-Submission Smart Reload & Cache Preservation:**
   - Detects quiet submission states where Facebook's client SPA hangs.
   - Automatically triggers browser reloads without wiping cookies or localStorage cache.
   - Fallback session inspection against `m.facebook.com` to capture active `c_user` or OTP checkpoint.
3. **Multilingual Recovery Option Discovery:**
   - Fully decoupled "Try another way" button discovery from password field presence.
   - Supports international localizations: English, Italian (*"Prova in un altro modo"*), Spanish (*"Probar de otra forma"*), French (*"Essayer une autre méthode"*), German, and Portuguese.
   - Matches recovery SMS radio buttons via ending phone digits (`last2` / `last4`) and phone keywords.
4. **Smart Input Parser:**
   - Ingests phone numbers, c_users, and recovery pairs from clipboard paste, comma/semicolon/newline delimiters, or local file paths.
   - Filters out dates, timestamps, resolutions, and invalid 24-digit noise.
5. **Anti-Detection & Fingerprint Masking:**
   - Strips `navigator.webdriver` flags, spoofs WebGL renderer strings, and injects realistic user agents.
   - Synthetic human-cadence typing jitter with randomized micro-delays.

---

## 🧪 QA Validation & Testing

Run the full built-in test suite verifying all 38 core operational components:

```bash
fbacc test
```

Expected result:
```
   Result: 38/38 tests passed (100.0%)
```

---

## 📜 License
Released under the MIT License. Built for authorized QA automation, resilience benchmarking, and recovery testing.
