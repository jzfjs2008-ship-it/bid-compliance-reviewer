#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import ctypes
import ctypes.wintypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.dpi_aware import enable_high_dpi
from database.schema import init_database
from database.init_data import seed_database


_SINGLE_INSTANCE_MUTEX_NAME = "Local\\招投标合规审查系统-{9E8B5C3A-1F4D-4A7E-9B2C-6D8E5F4A3B2C}"


def _try_acquire_single_instance():
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, True, _SINGLE_INSTANCE_MUTEX_NAME)
    if not mutex:
        return True
    if ctypes.GetLastError() == 183:
        kernel32.CloseHandle(mutex)
        hwnd = kernel32.FindWindowW(None, "招投标合规审查系统")
        if hwnd:
            kernel32.SetForegroundWindow(hwnd)
            kernel32.ShowWindow(hwnd, 9)
        return False
    return True


def main():
    if not _try_acquire_single_instance():
        sys.exit(0)

    enable_high_dpi()

    init_database()
    seed_database()

    import tkinterdnd2 as dnd
    import customtkinter as ctk

    root = dnd.Tk()
    ctk.set_appearance_mode("light")
    root.title("招投标合规审查系统")

    from ui.app import MainApp
    app = MainApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
