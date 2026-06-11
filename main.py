#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.dpi_aware import enable_high_dpi
from database.schema import init_database
from database.init_data import seed_database


def main():
    enable_high_dpi()

    init_database()
    seed_database()

    import tkinterdnd2 as dnd
    import customtkinter as ctk

    root = dnd.Tk()
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    from ui.app import MainApp
    app = MainApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
