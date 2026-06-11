import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime


RISK_COLORS_REPORT = {
    "致命": "#E63946",
    "高危": "#F4A261",
    "人工复核": "#3498DB",
    "合规": "#2ECC71",
}


class ReportExporter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            "Disclaimer", parent=self.styles["Normal"],
            fontSize=8, textColor=colors.grey,
            alignment=1, spaceBefore=20,
        ))

    def export(self, file_path, results, file_map):
        doc = SimpleDocTemplate(
            file_path, pagesize=A4,
            topMargin=20*mm, bottomMargin=20*mm,
            leftMargin=15*mm, rightMargin=15*mm,
        )
        story = []

        # Title
        story.append(Paragraph(
            "标书合规预审报告", self.styles["Title"]
        ))
        story.append(Spacer(1, 6*mm))
        story.append(Paragraph(
            f"生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles["Normal"]
        ))
        story.append(Spacer(1, 4*mm))

        # File summary
        story.append(Paragraph("文件清单", self.styles["Heading2"]))
        for slot_name, files in file_map.items():
            if files:
                for f in files:
                    story.append(Paragraph(
                        f"  [{slot_name}] {os.path.basename(f)}",
                        self.styles["Normal"]
                    ))
        story.append(Spacer(1, 4*mm))

        # Summary stats
        story.append(Paragraph("审查结果总览", self.styles["Heading2"]))
        total = len(results)
        fails = sum(1 for r in results if r.get("status") == "fail")
        errors = sum(1 for r in results if r.get("status") == "error")
        passes = sum(1 for r in results if r.get("status") == "pass")
        skips = sum(1 for r in results if r.get("status") == "skip")
        fatals = sum(1 for r in results if r.get("risk_level") == "致命" and r.get("status") == "fail")
        highs = sum(1 for r in results if r.get("risk_level") == "高危" and r.get("status") == "fail")

        summary_data = [
            ["总规则数", str(total)],
            ["致命风险", str(fatals)],
            ["高危隐患", str(highs)],
            ["未通过", str(fails)],
            ["通过", str(passes)],
            ["跳过", str(skips)],
            ["错误", str(errors)],
        ]
        summary_table = Table(summary_data, colWidths=[80*mm, 60*mm])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.Color(0, 0.47, 0.83)),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 6*mm))

        # Detailed results
        story.append(Paragraph("详细审查记录", self.styles["Heading2"]))

        risk_order = {"致命": 0, "高危": 1, "人工复核": 2, "合规": 3}
        sorted_results = sorted(results, key=lambda x: risk_order.get(x.get("risk_level", "合规"), 99))

        for item in sorted_results:
            risk_level = item.get("risk_level", "合规")
            status = item.get("status", "skip")
            color = RISK_COLORS_REPORT.get(risk_level, "#999999")

            status_map = {"pass": "✓ 通过", "fail": "✗ 未通过", "skip": "— 已跳过", "error": "! 错误"}
            status_text = status_map.get(status, status)

            # Rule header with color
            header_style = ParagraphStyle(
                "RiskHeader", parent=self.styles["Heading3"],
                textColor=HexColor(color),
                spaceBefore=4*mm, spaceAfter=1*mm,
            )
            story.append(Paragraph(
                f"[{risk_level}] {item.get('rule_name', '')} - {status_text}",
                header_style,
            ))

            # Error message
            story.append(Paragraph(
                f"<b>提示:</b> {item.get('error_message', '')}",
                self.styles["Normal"],
            ))

            # Detail
            detail = item.get("detail", "")
            if detail:
                story.append(Paragraph(
                    f"<b>详情:</b> {detail}",
                    ParagraphStyle("Detail", parent=self.styles["Normal"], fontSize=9, textColor=colors.grey),
                ))

            # Tags
            tags = item.get("matched_tags", [])
            if tags:
                story.append(Paragraph(
                    f"<b>触发标签:</b> {', '.join(tags)}",
                    ParagraphStyle("Tags", parent=self.styles["Normal"], fontSize=9, textColor=colors.red),
                ))

            story.append(Spacer(1, 2*mm))

        # Disclaimer
        story.append(HRFlowable(width="100%", color=colors.grey))
        story.append(Paragraph(
            "免责声明：本工具仅提供基于预设规则的辅助性形式审查，不构成最终法律意见。"
            "实质性合规及主观偏离度需由专业人工复核确认。",
            self.styles["Disclaimer"],
        ))

        doc.build(story)
