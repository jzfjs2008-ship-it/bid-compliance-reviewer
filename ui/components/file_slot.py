import customtkinter as ctk
import os
from tkinter import filedialog
from ui.theme import *
from engine.parser_router import SUPPORTED_EXTENSIONS


class FileSlot(ctk.CTkFrame):
    def __init__(self, master, slot_name, icon="📄", on_change=None, **kwargs):
        super().__init__(master, **kwargs)
        self.slot_name = slot_name
        self.icon = icon
        self.on_change = on_change
        self.files = []
        self._drag_over = False

        self.configure(fg_color=BG_WHITE, border_color=BORDER_LIGHT, border_width=1, corner_radius=6)
        self._make_card_shadow()

        self._build_ui()

    def _make_card_shadow(self):
        self.configure(border_width=1)

    def _build_ui(self):
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent", height=28)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 0))
        header.grid_propagate(False)

        self.icon_label = ctk.CTkLabel(
            header, text=self.icon, font=(FONT_FAMILY, 13), anchor="w", width=20
        )
        self.icon_label.pack(side="left")

        self.title_label = ctk.CTkLabel(
            header, text=self.slot_name, font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            text_color=TEXT_PRIMARY, anchor="w"
        )
        self.title_label.pack(side="left", padx=(4, 0))

        self.count_label = ctk.CTkLabel(
            header, text="", font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=TEXT_TERTIARY, anchor="e"
        )
        self.count_label.pack(side="right")

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=12, pady=(4, 8))
        self.body.columnconfigure(0, weight=1)

        self.drop_hint = ctk.CTkFrame(self.body, fg_color=BG_CARD, corner_radius=4, height=48)
        self.drop_hint.grid(row=0, column=0, sticky="ew", pady=(0, 0))
        self.drop_hint.grid_propagate(False)

        hint_inner = ctk.CTkFrame(self.drop_hint, fg_color="transparent")
        hint_inner.place(relx=0.5, rely=0.5, anchor="center")

        self.hint_label = ctk.CTkLabel(
            hint_inner, text="点击选择文件，或将文件拖拽到此处",
            font=(FONT_FAMILY, FONT_SIZE_XS), text_color=TEXT_TERTIARY,
        )
        self.hint_label.pack()

        self.file_list = ctk.CTkFrame(self.body, fg_color="transparent")
        self.file_list.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.file_list.grid_remove()

        self._bind_events()

    def _bind_events(self):
        self._bind_recursive(self, "<Button-1>", self._on_click)
        self._bind_recursive(self.drop_hint, "<Button-1>", self._on_click)
        self._bind_recursive(self.hint_label, "<Button-1>", self._on_click)

    def _bind_recursive(self, widget, seq, handler):
        widget.bind(seq, handler, add="+")
        for child in widget.winfo_children():
            try:
                self._bind_recursive(child, seq, handler)
            except Exception:
                pass

    def _on_click(self, event):
        paths = filedialog.askopenfilenames(
            title=f"选择文件 - {self.slot_name}",
            filetypes=[
                ("支持的文件", "*.pdf *.docx *.doc *.xlsx *.xls"),
                ("PDF 文件", "*.pdf"),
                ("Word 文件", "*.docx *.doc"),
                ("Excel 文件", "*.xlsx *.xls"),
                ("所有文件", "*.*"),
            ]
        )
        if paths:
            valid = [p for p in paths if os.path.splitext(p)[1].lower() in SUPPORTED_EXTENSIONS]
            invalid = len(paths) - len(valid)
            self.add_files(valid)
            if invalid:
                from ui.components.dialogs import Toast
                Toast(self.winfo_toplevel()).show(f"{invalid} 个文件类型不支持，已忽略", 3000)

    def drop(self, event):
        raw = event.data
        if not raw:
            return
        paths = []
        for entry in raw.strip().split():
            entry = entry.strip("{}")
            entry = os.path.normpath(entry)
            if os.path.isdir(entry):
                for root_dir, _, filenames in os.walk(entry):
                    for fn in filenames:
                        full = os.path.join(root_dir, fn)
                        if os.path.splitext(full)[1].lower() in SUPPORTED_EXTENSIONS:
                            paths.append(full)
            elif os.path.isfile(entry):
                if os.path.splitext(entry)[1].lower() in SUPPORTED_EXTENSIONS:
                    paths.append(entry)
        self._on_drag_leave(None)
        self.add_files(paths)

    def add_files(self, file_paths):
        changed = False
        for fp in file_paths:
            fp = os.path.normpath(fp)
            if fp not in self.files:
                self.files.append(fp)
                changed = True
        if changed:
            self._refresh()
            if self.on_change:
                self.on_change()

    def remove_file(self, file_path):
        fp = os.path.normpath(file_path)
        if fp in self.files:
            self.files.remove(fp)
            self._refresh()
            if self.on_change:
                self.on_change()

    def clear(self):
        self.files.clear()
        self._refresh()
        if self.on_change:
            self.on_change()

    def get_files(self):
        return list(self.files)

    def _refresh(self):
        for w in self.file_list.winfo_children():
            w.destroy()

        if self.files:
            self.file_list.grid()
            self.drop_hint.grid_remove()
            self.count_label.configure(text=f"{len(self.files)} 个文件")
            for f in self.files:
                row = ctk.CTkFrame(self.file_list, fg_color="transparent")
                row.pack(fill="x", pady=1)
                name = os.path.basename(f)
                ctk.CTkLabel(
                    row, text=name, anchor="w",
                    font=(FONT_FAMILY, FONT_SIZE_SMALL),
                    text_color=TEXT_PRIMARY,
                ).pack(side="left", fill="x", expand=True)
                ctk.CTkButton(
                    row, text="×", width=24, height=20,
                    fg_color="#C42B1C", text_color="#FFFFFF",
                    hover_color="#A52616", font=(FONT_FAMILY, 11, "bold"),
                    corner_radius=3,
                    command=lambda fp=f: self.remove_file(fp),
                ).pack(side="right", padx=2)
        else:
            self.file_list.grid_remove()
            self.drop_hint.grid()
            self.count_label.configure(text="")
