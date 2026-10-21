#!/usr/bin/env python3
"""
fbacc.py - Wrapper entrypoint redirecting to EYDHM Enterprise QA Automation Suite (fbacc_pro.py)
"""
import sys
import os

# Delegate directly to fbacc_pro
from fbacc_pro import main

if __name__ == "__main__":
    main()
