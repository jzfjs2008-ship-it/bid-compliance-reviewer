import customtkinter as ctk
from ui.theme import *


class RiskList(ctk.CTkScrollableFrame):
    def __init__(self, master, on_item_click=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_item_click = on_item_click
        self.items = []

    def set_items(self, results):
        self.items = results
        for widget in self.winfo_children():
            widget.destroy()

        risk_order = {"致命": 0, "高危": 1, "人工复核": 2, "合规": 3}
        sorted_items = sorted(results, key=lambda x: risk_order.get(x.get("risk_level", "合规"), 99))

        for item in sorted_items:
            self._add_item(item)

    def _add_item(self, item):
        risk_level = item.get("risk_level", "合规")
        status = item.get("status", "skip")
        color = RISK_COLORS.get(risk_level, TEXT_SECONDARY)

        frame = ctk.CTkFrame(self, fg_color=BG_WHITE, border_color=BORDER, border_width=1, corner_radius=4)
        frame.pack(fill="x", padx=PADDING_NORMAL, pady=2)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=PADDING_NORMAL, pady=(PADDING_SMALL, 0))

        badge = ctk.CTkLabel(
            header, text=f" [{risk_level}] ",
            fg_color=color, text_color=BG_WHITE,
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
            corner_radius=3,
        )
        badge.pack(side="left")

        name = ctk.CTkLabel(
            header, text=item.get("rule_name", ""),
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            text_color=TEXT_PRIMARY,
        )
        name.pack(side="left", padx=(PADDING_NORMAL, 0))

        status_text = {"pass": "✓ 通过", "fail": "✗ 未通过", "skip": "— 跳过", "error": "! 错误"}.get(status, status)
        status_label = ctk.CTkLabel(
            header, text=status_text,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            text_color=TEXT_SECONDARY,
        )
        status_label.pack(side="right")

        msg = ctk.CTkLabel(
            frame, text=item.get("error_message", ""),
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            text_color=TEXT_SECONDARY, wraplength=400,
            justify="left",
        )
        msg.pack(fill="x", padx=PADDING_NORMAL, pady=(0, PADDING_SMALL))

        detail = item.get("detail", "")
        if detail:
            detail_label = ctk.CTkLabel(
                frame, text=detail,
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                text_color="#999999", wraplength=400,
                justify="left",
            )
            detail_label.pack(fill="x", padx=PADDING_NORMAL, pady=(0, PADDING_SMALL))

        tags = item.get("matched_tags", [])
        if tags:
            tag_text = "触发标签: " + ", ".join(tags)
            tag_label = ctk.CTkLabel(
                frame, text=tag_text,
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                text_color=DANGER,
            )
            tag_label.pack(fill="x", padx=PADDING_NORMAL, pady=(0, PADDING_SMALL))

        frame.bind("<Button-1>", lambda e, i=item: self._on_click(i))
        for child in frame.winfo_children():
            child.bind("<Button-1>", lambda e, i=item: self._on_click(i))

    def _on_click(self, item):
        if self.on_item_click:
            self.on_item_click(item)

    def get_summary(self):
        total = len(self.items)
        fails = sum(1 for i in self.items if i.get("status") == "fail")
        errors = sum(1 for i in self.items if i.get("status") == "error")
        passes = sum(1 for i in self.items if i.get("status") == "pass")
        skips = sum(1 for i in self.items if i.get("status") == "skip")
        fatals = sum(1 for i in self.items if i.get("risk_level") == "致命" and i.get("status") == "fail")
        highs = sum(1 for i in self.items if i.get("risk_level") == "高危" and i.get("status") == "fail")
        return {
            "total": total, "pass": passes, "fail": fails,
            "error": errors, "skip": skips,
            "fatal_count": fatals, "high_count": highs,
        }
