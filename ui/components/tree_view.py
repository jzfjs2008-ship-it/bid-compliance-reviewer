import customtkinter as ctk
from ui.theme import *


class TreeNode:
    def __init__(self, name, data=None, parent=None):
        self.name = name
        self.data = data
        self.parent = parent
        self.children = []
        self.expanded = False

    def add_child(self, child):
        self.children.append(child)
        child.parent = self
        return child


class TreeView(ctk.CTkScrollableFrame):
    def __init__(self, master, on_select=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_select = on_select
        self.selected_path = None
        self._nodes = {}

    def set_tree(self, root_node):
        for widget in self.winfo_children():
            widget.destroy()
        self._nodes.clear()
        self._render_node(root_node, 0)

    def _render_node(self, node, depth):
        indent = depth * 20
        has_children = len(node.children) > 0

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=0, pady=0)

        container = ctk.CTkFrame(frame, fg_color="transparent", height=28)
        container.pack(fill="x")
        container.pack_propagate(False)

        if has_children:
            toggle_btn = ctk.CTkButton(
                container, text="▾" if node.expanded else "▸",
                width=20, height=20,
                fg_color="transparent", text_color=TEXT_SECONDARY,
                hover_color=BG_LIGHT, font=(FONT_FAMILY, 10),
                command=lambda n=node, f=frame: self._toggle(n, f),
            )
            toggle_btn.place(x=indent, y=4)

        label = ctk.CTkLabel(
            container, text=node.name, anchor="w",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            text_color=TEXT_PRIMARY,
        )
        label.place(x=indent + (24 if has_children else 4), y=4, relwidth=0.9)

        node_key = id(node)
        self._nodes[node_key] = {"frame": frame, "node": node, "container": container, "label": label}

        container.bind("<Button-1>", lambda e, n=node: self._select(n))
        label.bind("<Button-1>", lambda e, n=node: self._select(n))
        if has_children:
            toggle_btn.bind("<Button-1>", lambda e, n=node, f=frame: self._toggle(n, f))

        if has_children and node.expanded:
            children_frame = ctk.CTkFrame(frame, fg_color="transparent")
            children_frame.pack(fill="x")
            frame.children_frame = children_frame
            for child in node.children:
                self._render_node(child, depth + 1)

    def _toggle(self, node, frame):
        node.expanded = not node.expanded
        self.set_tree(node if node.parent is None else node.parent)

    def _select(self, node):
        self.selected_path = self._get_path(node)
        for key, info in self._nodes.items():
            info["label"].configure(text_color=TEXT_PRIMARY)
        node_key = id(node)
        if node_key in self._nodes:
            self._nodes[node_key]["label"].configure(text_color=PRIMARY)
        if self.on_select:
            self.on_select(node)

    def _get_path(self, node):
        parts = []
        while node:
            parts.append(node.name)
            node = node.parent
        return " / ".join(reversed(parts))
