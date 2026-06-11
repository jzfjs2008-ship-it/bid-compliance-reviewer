import customtkinter as ctk
from ui.theme import *


class PreviewPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=BG_WHITE)

        self.textbox = ctk.CTkTextbox(
            self, wrap="word", font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            fg_color=BG_WHITE, text_color=TEXT_PRIMARY,
            border_width=0,
        )
        self.textbox.pack(fill="both", expand=True, padx=PADDING_NORMAL, pady=PADDING_NORMAL)
        self.textbox.configure(state="disabled")

        self.highlights = []

    def set_content(self, text, title=""):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        if title:
            self.textbox.insert("end", f"{title}\n{'='*40}\n\n")
        self.textbox.insert("end", text)
        self.textbox.configure(state="disabled")
        self.highlights.clear()

    def highlight_text(self, keyword, color="#FFEB3B"):
        self.textbox.configure(state="normal")
        start_pos = "1.0"
        while True:
            pos = self.textbox.search(keyword, start_pos, "end")
            if not pos:
                break
            end_pos = f"{pos}+{len(keyword)}c"
            self.textbox.tag_add("highlight", pos, end_pos)
            self.textbox.tag_config("highlight", background=color, foreground="#000000")
            start_pos = end_pos
        self.textbox.configure(state="disabled")

    def clear(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
        self.highlights.clear()
