#!/usr/bin/env python3
"""Launch the GUI application."""

import sys
import os

if not getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from password_manager.gui.main_window import main

if __name__ == "__main__":
    main()