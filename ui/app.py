import customtkinter as ctk
import os
import threading
from tkinter import filedialog
from ui.theme import *
from ui.components.file_slot import FileSlot
from ui.components.tree_view import TreeView, TreeNode
from ui.components.risk_list import RiskList
from ui.components.preview_panel import PreviewPanel
from ui.components.progress_bar import ProgressPanel
from ui.components.dialogs import ModalDialog, Toast
from engine.parser_router import parse_document, SUPPORTED_EXTENSIONS
from engine.comparator import Comparator
from engine.prechecker import precheck_files
from utils.queue_handler import QueueHandler, MessageType
from report.pdf_exporter import ReportExporter


class MainApp:
    def __init__(self, master):
        self.master = master
        self._setup_window()
        self._queue = QueueHandler()
        self._toast = Toast(self.master)
        self._compare_results = []
        self._parsed_data = {}
        self._bid_data = None
        self._resp_data = {}

        self._build_top_bar()
        self._build_main_area()
        self._poll_queue()

    def _setup_window(self):
        m = self.master
        m.title("招投标合规审查系统 v3.0")
        m.geometry("1400x900+100+50")
        m.minsize(1200, 720)

    def _build_top_bar(self):
        bar = ctk.CTkFrame(self.master, fg_color=BG_WHITE, height=48, corner_radius=0)
        bar.pack(fill="x", padx=0, pady=0)
        bar.pack_propagate(False)

        title_frame = ctk.CTkFrame(bar, fg_color="transparent")
        title_frame.pack(side="left", fill="y", padx=(PADDING_LARGE, 0))

        ctk.CTkLabel(
            title_frame, text="招投标合规审查系统",
            font=(FONT_FAMILY, FONT_SIZE_XL, "bold"),
            text_color=PRIMARY,
        ).pack(side="left")

        self.btn_start = ctk.CTkButton(
            bar, text="开始审查", command=self._start_review,
            fg_color=PRIMARY, text_color=BG_WHITE,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            corner_radius=4, height=32, width=100,
        )
        self.btn_start.pack(side="right", padx=(0, PADDING_LARGE), pady=8)

        self.btn_export = ctk.CTkButton(
            bar, text="导出报告", command=self._export_report,
            fg_color=BG_WHITE, text_color=PRIMARY,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            border_color=PRIMARY, border_width=1,
            corner_radius=4, height=32, width=100,
            hover_color=PRIMARY_LIGHT,
        )
        self.btn_export.pack(side="right", padx=(0, PADDING_NORMAL), pady=8)

        sep = ctk.CTkFrame(bar, fg_color=BORDER_LIGHT, height=1)
        sep.pack(side="bottom", fill="x")

    def _build_main_area(self):
        main = ctk.CTkFrame(self.master, fg_color=BG_PAGE)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        self._build_sidebar(main)
        self._build_content(main)

    def _build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, fg_color=BG_WHITE, width=360, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 1))
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)

        # File slots — all visible without scrolling
        slots_container = ctk.CTkFrame(sidebar, fg_color="transparent")
        slots_container.grid(row=0, column=0, sticky="ew", padx=PADDING_LARGE, pady=(PADDING_LARGE, PADDING_NORMAL))
        slots_container.columnconfigure(0, weight=1)

        self.slots = {}
        for i, (name, icon) in enumerate(zip(SLOT_NAMES, SLOT_ICONS)):
            slot = FileSlot(
                slots_container, name, icon=icon,
                on_change=self._on_slot_change,
            )
            slot.grid(row=i, column=0, sticky="ew", pady=(0, PADDING_NORMAL))
            self.slots[name] = slot
            self._register_drop(slot)

        # Separator
        sep = ctk.CTkFrame(sidebar, fg_color=BORDER_LIGHT, height=1)
        sep.grid(row=1, column=0, sticky="ew", padx=PADDING_LARGE, pady=(0, PADDING_NORMAL))

        # Tree label
        tree_header = ctk.CTkFrame(sidebar, fg_color="transparent")
        tree_header.grid(row=2, column=0, sticky="ew", padx=PADDING_LARGE)
        ctk.CTkLabel(
            tree_header, text="项目结构", anchor="w",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        self.tree_view = TreeView(sidebar, on_select=self._on_tree_select)
        self.tree_view.grid(row=3, column=0, sticky="nsew", padx=PADDING_LARGE, pady=(PADDING_SMALL, PADDING_LARGE))
        sidebar.rowconfigure(3, weight=1)

    def _register_drop(self, slot):
        try:
            slot.drop_target_register("*")
            slot.dnd_bind("<<Drop>>", slot.drop)
            for child in slot.winfo_children():
                try:
                    child.drop_target_register("*")
                    child.dnd_bind("<<Drop>>", slot.drop)
                except Exception:
                    pass
        except Exception:
            pass

    def _build_content(self, parent):
        content = ctk.CTkFrame(parent, fg_color=BG_PAGE)
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=0)
        content.rowconfigure(1, weight=1)
        content.rowconfigure(2, weight=0)

        # Tab view
        self.tab_view = ctk.CTkTabview(
            content, fg_color=BG_WHITE,
            corner_radius=6,
            segmented_button_fg_color=BG_CARD,
            segmented_button_selected_color=PRIMARY,
            segmented_button_selected_hover_color=PRIMARY_HOVER,
            segmented_button_unselected_color=BG_CARD,
            segmented_button_unselected_hover_color=BG_HOVER,
            text_color=TEXT_PRIMARY,
        )
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=PADDING_LARGE, pady=(PADDING_LARGE, PADDING_NORMAL))
        self.tab_view._segmented_button.configure(font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        self.tab_view._segmented_button.configure(corner_radius=4)

        tab_preview = self.tab_view.add("原文预览")
        tab_preview.columnconfigure(0, weight=1)
        tab_preview.rowconfigure(0, weight=1)

        self.preview = PreviewPanel(tab_preview)
        self.preview.grid(row=0, column=0, sticky="nsew")

        tab_risks = self.tab_view.add("风险列表")
        tab_risks.columnconfigure(0, weight=1)
        tab_risks.rowconfigure(0, weight=0)
        tab_risks.rowconfigure(1, weight=1)

        risk_header = ctk.CTkFrame(tab_risks, fg_color="transparent")
        risk_header.grid(row=0, column=0, sticky="ew", pady=(0, PADDING_SMALL))
        ctk.CTkLabel(
            risk_header, text="审查结果", anchor="w",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")
        self.summary_label = ctk.CTkLabel(
            risk_header, text="", anchor="e",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            text_color=TEXT_SECONDARY,
        )
        self.summary_label.pack(side="right")

        self.risk_list = RiskList(tab_risks, on_item_click=self._on_risk_click)
        self.risk_list.grid(row=1, column=0, sticky="nsew")

        # Bottom area
        bottom = ctk.CTkFrame(content, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=PADDING_LARGE, pady=(0, PADDING_LARGE))
        bottom.columnconfigure(0, weight=1)

        self.progress = ProgressPanel(bottom)
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, PADDING_NORMAL))

        disclaimer = ctk.CTkLabel(
            bottom,
            text="免责声明：本工具仅提供基于预设规则的辅助性形式审查，不构成最终法律意见。实质性合规及主观偏离度需由专业人工复核确认。",
            font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=TEXT_TERTIARY, wraplength=800, justify="center",
        )
        disclaimer.grid(row=1, column=0, sticky="ew")

    def _on_slot_change(self):
        self._rebuild_tree()

    def _rebuild_tree(self):
        root = TreeNode("项目")
        for slot_name, slot in self.slots.items():
            files = slot.get_files()
            if files:
                slot_node = TreeNode(slot_name)
                root.add_child(slot_node)
                for f in files:
                    slot_node.add_child(TreeNode(os.path.basename(f), data=f))
        self.tree_view.set_tree(root)

    def _on_tree_select(self, node):
        if node and node.data and os.path.isfile(node.data):
            try:
                result = parse_document(node.data)
                text = result.get("raw_text", "")
                self.preview.set_content(text[:5000], title=os.path.basename(node.data))
            except Exception as e:
                self.preview.set_content(f"无法预览: {e}", title=os.path.basename(node.data))

    def _on_risk_click(self, item):
        detail = item.get("detail", "")
        if detail:
            self.preview.highlight_text(detail[:50], "#FFCDD2")

    def _start_review(self):
        file_map = {name: slot.get_files() for name, slot in self.slots.items()}

        check = precheck_files(file_map)
        if check["has_error"]:
            err_text = "\n".join(e["message"] for e in check["errors"])
            ModalDialog(self.master, "文件错误", f"存在以下错误：\n\n{err_text}")
            return

        self._compare_results.clear()
        self._parsed_data.clear()
        self._bid_data = None
        self._resp_data = {}

        self.btn_start.configure(state="disabled", text="审查中...")
        self.progress.start()

        thread = threading.Thread(target=self._run_review, args=(file_map,), daemon=True)
        thread.start()

    def _run_review(self, file_map):
        try:
            bid_files = file_map.get("招标文件", [])
            if bid_files:
                self._queue.put(MessageType.PROGRESS, ("Parse", "解析招标文件..."))
                self._bid_data = parse_document(bid_files[0], slot="招标文件", queue_handler=self._queue)

            resp_slots = {k: v for k, v in file_map.items() if k != "招标文件"}
            total = sum(len(v) for v in resp_slots.values())
            done = 0
            for slot_name, files in resp_slots.items():
                for f in files:
                    self._queue.put(MessageType.PROGRESS, ("Parse", f"解析 [{slot_name}]: {os.path.basename(f)}"))
                    data = parse_document(f, slot=slot_name, queue_handler=self._queue)
                    self._parsed_data[f] = {"slot": slot_name, "data": data}
                    done += 1
                    self._queue.put(MessageType.PROGRESS, ("Progress", done / max(total, 1)))

            self._queue.put(MessageType.PROGRESS, ("Compare", "开始规则比对..."))
            resp_by_slot = {}
            for fp, info in self._parsed_data.items():
                s = info["slot"]
                if s not in resp_by_slot:
                    resp_by_slot[s] = info["data"]

            comparator = Comparator(queue_handler=self._queue)
            results = comparator.compare(self._bid_data, resp_by_slot)
            self._compare_results = results
            self._queue.put(MessageType.DONE, ("Done", results))
        except Exception as e:
            self._queue.put(MessageType.ERROR, ("Error", str(e)))

    def _poll_queue(self):
        try:
            for msg in self._queue.drain():
                self._handle_message(msg)
        except Exception:
            pass
        self.master.after(100, self._poll_queue)

    def _handle_message(self, msg):
        t = msg.get("type")
        d = msg.get("data")
        if t == "progress":
            label, val = d
            if label == "Progress":
                self.progress.set_progress(val)
            else:
                self.progress.update_status(str(val))
        elif t == "error":
            self.progress.stop()
            self.btn_start.configure(state="normal", text="开始审查")
            ModalDialog(self.master, "审查错误", f"审查过程中发生错误：\n\n{d[1]}")
        elif t == "done":
            self.progress.stop()
            self.btn_start.configure(state="normal", text="开始审查")
            results = d[1]
            self.risk_list.set_items(results)
            s = self.risk_list.get_summary()
            self.summary_label.configure(
                text=f"总计 {s['total']} 项 | 致命 {s['fatal_count']} | 高危 {s['high_count']} | 通过 {s['pass']} | 跳过 {s['skip']}"
            )
            self._toast.show("审查完成", 3000)

    def _export_report(self):
        if not self._compare_results:
            self._toast.show("请先执行审查", 3000)
            return
        path = filedialog.asksaveasfilename(
            title="导出报告", defaultextension=".pdf",
            filetypes=[("PDF 文件", "*.pdf")],
        )
        if not path:
            return
        try:
            exporter = ReportExporter()
            file_map = {n: s.get_files() for n, s in self.slots.items()}
            exporter.export(path, self._compare_results, file_map)
            self._toast.show(f"报告已导出", 3000)
        except Exception as e:
            ModalDialog(self.master, "导出失败", f"报告导出失败：\n\n{str(e)}")
