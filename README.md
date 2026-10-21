# Facebook Automation & Account Recovery Engine (fbacc)

Enterprise-grade asynchronous DOM automation engine for Facebook account provisioning, OTP dispatch, account password recovery, and graph liveness auditing. Engineered for cross-platform reliability on **Android Termux (aarch64)**, **Linux (Debian/Ubuntu/Arch/Fedora)**, **macOS**, and **Windows**.

---

## ⚡ Instant One-Line Auto-Install

Run this single command on **Termux (Android)**, **Linux**, or **macOS** to auto-detect your OS, install system dependencies (Chromium, Python, Tesseract), install Python libraries, and create a global `fbacc` shortcut:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ficxuio-crypto/fbacc/main/install.sh)
```

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/ficxuio-crypto/fbacc/main/install.ps1 | iex
```

---

## 🛠 Manual Installation

```bash
# 1. Clone repository
git clone https://github.com/ficxuio-crypto/fbacc.git
cd fbacc

# 2. Run automated installer
chmod +x install.sh
./install.sh

# 3. Launch interactive terminal interface
fbacc
# or directly:
python3 fbacc.py
```

---

## 🚀 Key Modules & Capabilities

| Option | Module | Functionality |
|---|---|---|
| **[1]** | **Create Account** | Full automated account creation (Single-step / Multi-step Limited Edition). |
| **[2]** | **90% Phone Creation** | Provisions account up to SMS OTP barrier, extracts `c_user`, password, and session cookies. |
| **[3]** | **Identity Appeal** | Automated photo upload & KYC bypass using EXIF-sanitized image buffer. |
| **[4]** | **Full Pipeline** | Multi-stage registration + challenge resolver with auto-retry. |
| **[5]** | **Account Recovery** | Password reset using phone-OTP pairs, handling "Try another way" & SMS radio selection. |
| **[6]** | **Reset OTP Dispatch** | Dispatches password reset SMS OTPs with in-session multi-round (`driver.back()`) loops. |
| **[7]** | **Hybrid Pipeline** | Chained execution: Phase 1 (90% Phone Creation) + Phase 2 (Option 6 Reset OTP Dispatch). |
| **[8]** | **Liveness Health Check**| Real-time profile audit via Facebook Graph API (`/picture` routing & redirect tracing). |
| **[9]** | **Settings & Proxies** | Granular per-option proxy routing (`before_otp_random`, `before_otp_country`, `browser_launch`). |

---

## 🧠 Core Engineering Invariants

1. **Post-Submission Smart Reload & Cache Preservation:**
   - Detects quiet submission states where Facebook's client SPA hangs.
   - Automatically executes browser reloads without wiping cookies or localStorage cache.
   - Fallback session inspection against `m.facebook.com` to capture active `c_user` or OTP checkpoint.
2. **Multilingual Recovery Option Discovery:**
   - Fully decoupled "Try another way" button discovery from password field existence.
   - Supports international localizations: English, Italian (*"Prova in un altro modo"*), Spanish (*"Probar de otra forma"*), French, German, and Portuguese.
   - Matches recovery SMS radio buttons via ending phone digits (`last2` / `last4`) and phone keywords.
3. **High-Fidelity Input Parser:**
   - Ingests phone numbers, c_users, and recovery pairs from clipboard paste, comma/semicolon/newline delimiters, or local file paths.
   - Filters out dates, timestamps, resolutions, and invalid 24-digit noise.
4. **Resilient Terminal UI:**
   - Live rich status dashboard, color-coded tabular reports, zero-success clean failure verdicts, and post-task re-run action menus.

---

## 💻 CLI Flags Reference

```bash
# Launch interactive terminal UI
python3 fbacc.py

# Option 7: Hybrid Creation + Option 6 Dispatch (Dry-Run simulation)
python3 fbacc.py --hybrid --contact-source "+260750410071, +260750410213" --dry-run

# Option 6: Reset OTP Dispatch (2 rounds)
python3 fbacc.py --reset-otp --pairs "+393760167315" --reco-rounds 2

# Option 5: Account Password Recovery
python3 fbacc.py --reset-account --pairs "393760167315 699632"

# Option 8: Audit Account Liveness from log or direct IDs
python3 fbacc.py --check-live phone_accounts.txt

# Run complete QA unit test suite
python3 fbacc.py --test
```

---

## 🔒 Security & Privacy

All output credential logs (`phone_accounts.txt`, `accounts_log.txt`, `successful_recovery.txt`, `reco_sms.txt`) and session cookies are strictly excluded by `.gitignore` to guarantee zero credential leakage.
