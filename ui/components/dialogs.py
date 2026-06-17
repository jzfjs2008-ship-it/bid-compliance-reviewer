import customtkinter as ctk
from ui.theme import *


class ModalDialog(ctk.CTkToplevel):
    def __init__(self, master, title, message, buttons=None, width=420, height=160):
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.result = None

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(self, fg_color=BG_WHITE, corner_radius=8)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        msg_label = ctk.CTkLabel(
            frame, text=message, wraplength=340,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            text_color=TEXT_PRIMARY, justify="center",
        )
        msg_label.pack(expand=True, pady=(30, 20))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))

        buttons = buttons or [{"text": "确定", "result": True, "primary": True}]
        for btn_cfg in buttons:
            if btn_cfg.get("primary"):
                btn = ctk.CTkButton(
                    btn_frame, text=btn_cfg["text"],
                    fg_color="#0078D4", text_color="#FFFFFF",
                    font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                    corner_radius=4, height=32, width=100,
                    hover_color="#106EBE",
                    command=lambda r=btn_cfg["result"]: self._close(r),
                )
            else:
                btn = ctk.CTkButton(
                    btn_frame, text=btn_cfg["text"],
                    fg_color="#F0F0F0", text_color="#000000",
                    font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                    corner_radius=4, height=32, width=100,
                    hover_color="#E0E0E0",
                    command=lambda r=btn_cfg["result"]: self._close(r),
                )
            btn.pack(side="left", padx=8)

        self.protocol("WM_DELETE_WINDOW", lambda: self._close(None))

    def _close(self, result):
        self.result = result
        self.grab_release()
        self.destroy()


class Toast:
    _instance = None

    def __init__(self, master):
        self.master = master
        self._label = None
        self._after_id = None

    def show(self, message, duration=3000):
        if self._after_id:
            self.master.after_cancel(self._after_id)

        if self._label:
            self._label.destroy()

        self._label = ctk.CTkLabel(
            self.master, text=message,
            fg_color="#333333", text_color=BG_WHITE,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            corner_radius=6, padx=16, pady=8,
        )
        self._label.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")

        self._after_id = self.master.after(duration, self._hide)

    def _hide(self):
        if self._label:
            self._label.destroy()
            self._label = None
        self._after_id = None
