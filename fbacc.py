#!/usr/bin/env python3
"""
fbacc.py - EYDHM Enterprise Facebook Automation & Recovery Engine
Master CLI Dispatcher, Auto-Healing Bootstrapper, and Runtime Controller.
"""

import sys
import os
import subprocess
import json
import shutil
import platform

# Ensure script directory is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

VERSION = "2.4.0-enterprise"


def print_banner():
    c_cyan = "\033[38;5;51m"
    c_green = "\033[38;5;48m"
    c_white = "\033[38;5;255m"
    c_gray = "\033[38;5;244m"
    c_bold = "\033[1m"
    c_reset = "\033[0m"

    print(f"""
{c_green}{c_bold}   ███████  ██    ██  ██████   ██   ██  ███    ███
   ██        ██  ██   ██   ██  ██   ██  ████  ████
   █████      ████    ██   ██  ███████  ██ ████ ██
   ██          ██     ██   ██  ██   ██  ██  ██  ██
   ███████     ██     ██████   ██   ██  ██      ██{c_reset}
   {c_cyan}{c_bold}EYDHM ENTERPRISE AUTOMATION & RECOVERY SUITE{c_reset}
   {c_gray}Version: {VERSION} · Cross-Platform DOM & Async EventBus Engine{c_reset}
   ─────────────────────────────────────────────────────────────────
""")


def cmd_status():
    """Display comprehensive status of accounts, logs, configuration, and environment."""
    from doctor import detect_platform
    plat = detect_platform()
    print_banner()

    c_cyan = "\033[38;5;51m"
    c_green = "\033[38;5;48m"
    c_white = "\033[38;5;255m"
    c_gray = "\033[38;5;244m"
    c_yellow = "\033[38;5;220m"
    c_bold = "\033[1m"
    c_reset = "\033[0m"

    print(f" {c_bold}{c_cyan}[*] System Environment:{c_reset}")
    print(f"  ├── OS / Distro:       {c_white}{plat['distro'].title()} ({plat['arch']}){c_reset}")
    print(f"  ├── Python Runtime:    {c_white}{plat['python_version']}{c_reset} ({plat['python_path']})")
    print(f"  └── Package Managers:  {c_white}{', '.join(plat['pkg_managers']) or 'None'}{c_reset}")

    # Settings
    settings_file = os.path.join(SCRIPT_DIR, "settings.json")
    print(f"\n {c_bold}{c_cyan}[*] Active Configuration ({settings_file}):{c_reset}")
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r") as f:
                cfg = json.load(f)
            for k, v in cfg.items():
                print(f"  ├── {k:<20}: {c_white}{v}{c_reset}")
        except Exception as e:
            print(f"  └── {c_yellow}Error parsing settings.json: {e}{c_reset}")
    else:
        print(f"  └── {c_gray}No settings.json found (using default internal parameters){c_reset}")

    # Accounts Metrics
    print(f"\n {c_bold}{c_cyan}[*] Output Vaults & Account Logs:{c_reset}")
    log_files = [
        ("phone_accounts.txt", "Primary Provisioned Accounts"),
        ("successful_recovery.txt", "Recovered Checkpoint Accounts"),
        ("reco_sms.txt", "Recovery OTP Dispatched Logs"),
        ("invalid_otp_accounts.txt", "Invalid OTP Accounts"),
        ("invalid_reset_accounts.txt", "Invalid Reset Targets"),
    ]

    for fname, desc in log_files:
        fpath = os.path.join(SCRIPT_DIR, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [l.strip() for l in f if l.strip()]
                print(f"  ├── {desc:<30}: {c_green}{len(lines)} records{c_reset} {c_gray}({fname}){c_reset}")
            except Exception:
                print(f"  ├── {desc:<30}: {c_yellow}Error reading{c_reset}")
        else:
            print(f"  ├── {desc:<30}: {c_gray}0 records (file empty/uncreated){c_reset}")

    print(f"\n{c_gray}Run 'fbacc doctor' to inspect packages or 'fbacc' to launch interactive menu.{c_reset}\n")


def cmd_version():
    """Print version and git commit."""
    git_hash = "unknown"
    try:
        git_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=SCRIPT_DIR, text=True).strip()
    except Exception:
        pass
    print(f"fbacc {VERSION} (git {git_hash}) - EYDHM Enterprise Automation Suite")


def ensure_ready():
    """Pre-flight check: auto-heal any missing package without breaking user workflow."""
    try:
        from doctor import run_doctor
        # Quiet auto-repair runs before anything else
        run_doctor(auto_repair=True, quiet=True)
    except Exception as e:
        pass


def main():
    args = sys.argv[1:]

    # Handle subcommands
    if len(args) >= 1:
        subcmd = args[0].lower()

        if subcmd in ("doctor", "check", "--doctor"):
            from doctor import run_doctor
            auto = "--no-repair" not in args
            success = run_doctor(auto_repair=auto, quiet=False)
            sys.exit(0 if success else 1)

        elif subcmd in ("status", "info"):
            ensure_ready()
            cmd_status()
            sys.exit(0)

        elif subcmd in ("version", "-v", "--version"):
            cmd_version()
            sys.exit(0)

        elif subcmd in ("test", "--test"):
            ensure_ready()
            from fbacc_pro import main as pro_main
            sys.argv = [sys.argv[0], "--test"] + args[1:]
            pro_main()
            return

        elif subcmd in ("register", "create"):
            ensure_ready()
            from fbacc_pro import main as pro_main
            sys.argv = [sys.argv[0]] + args[1:]
            pro_main()
            return

        elif subcmd in ("recover", "reset"):
            ensure_ready()
            from fbacc_pro import main as pro_main
            sys.argv = [sys.argv[0], "--reset-account"] + args[1:]
            pro_main()
            return

        elif subcmd in ("reset-otp", "otp"):
            ensure_ready()
            from fbacc_pro import main as pro_main
            sys.argv = [sys.argv[0], "--reset-otp"] + args[1:]
            pro_main()
            return

        elif subcmd in ("hybrid",):
            ensure_ready()
            from fbacc_pro import main as pro_main
            sys.argv = [sys.argv[0], "--hybrid"] + args[1:]
            pro_main()
            return

        elif subcmd in ("check-live", "audit"):
            ensure_ready()
            from fbacc_pro import main as pro_main
            target = args[1] if len(args) > 1 else "phone_accounts.txt"
            sys.argv = [sys.argv[0], "--check-live", target]
            pro_main()
            return

    # Regular invocation or interactive menu
    ensure_ready()
    from fbacc_pro import main as pro_main
    pro_main()


if __name__ == "__main__":
    main()
