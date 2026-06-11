import customtkinter as ctk
from ui.theme import *
import threading
import time


class ProgressPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=BG_WHITE)

        self.progress_bar = ctk.CTkProgressBar(self, fg_color=BORDER, progress_color=PRIMARY)
        self.progress_bar.pack(fill="x", padx=PADDING_LARGE, pady=(PADDING_NORMAL, PADDING_SMALL))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self, text="就绪", anchor="w",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            text_color=TEXT_SECONDARY,
        )
        self.status_label.pack(fill="x", padx=PADDING_LARGE, pady=(0, PADDING_NORMAL))

        self._is_running = False

    def start(self):
        self._is_running = True
        self.progress_bar.set(0)
        self.status_label.configure(text="正在处理...")

    def set_progress(self, value, status_text=None):
        self.progress_bar.set(value)
        if status_text:
            self.status_label.configure(text=status_text)
        self.update_idletasks()

    def stop(self):
        self._is_running = False
        self.progress_bar.set(1)
        self.status_label.configure(text="处理完成")

    def reset(self):
        self._is_running = False
        self.progress_bar.set(0)
        self.status_label.configure(text="就绪")

    def update_status(self, text):
        self.status_label.configure(text=text)
        self.update_idletasks()
