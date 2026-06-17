import os
from .extractor import Extractor
from database.models import load_extraction_rules
from .normalizer import Normalizer
from utils.queue_handler import QueueHandler, MessageType


PARSER_MAP = {
    ".pdf": Extractor.extract_pdf,
    ".docx": Extractor.extract_docx,
    ".doc": Extractor.extract_docx,
    ".xlsx": Extractor.extract_excel,
    ".xls": Extractor.extract_excel,
}


SUPPORTED_EXTENSIONS = set(PARSER_MAP.keys())


def resolve_parser(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    return PARSER_MAP.get(ext)


def parse_document(file_path, slot=None, queue_handler=None):
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的文件类型: {ext}")

    if queue_handler:
        queue_handler.put(MessageType.PROGRESS, ("Parse", f"正在解析: {os.path.basename(file_path)}"))

    rules = load_extraction_rules(slot=slot)
    normalizer = Normalizer()

    if ext == ".pdf":
        pages = Extractor.extract_pdf(file_path)
        full_text = "\n".join(p["text"] for p in pages)
        rich_text = "\n".join(p["rich_text"] for p in pages)
        tables = Extractor.extract_table_from_pdf(file_path)

        result = {"raw_text": full_text, "rich_text": rich_text, "pages": pages, "tables": tables}

        extracted = {}
        import re
        for rule in rules:
            pattern = re.compile(rule["regex"])
            match = pattern.search(full_text)
            if match:
                value = match.group(1).strip()
                value = normalizer.full_normalize(value)
                extracted[rule["field_name"]] = value
                if queue_handler:
                    queue_handler.put(MessageType.PROGRESS, ("Extract", f"  提取 [{rule['field_name']}] = {value}"))
        result["extracted"] = extracted
        return result

    elif ext in (".docx", ".doc"):
        data = Extractor.extract_docx(file_path)
        full_text = "\n".join(p["text"] for p in data["paragraphs"])
        tables = data["tables"]

        result = {"raw_text": full_text, "paragraphs": data["paragraphs"], "tables": tables}

        extracted = {}
        import re
        for rule in rules:
            pattern = re.compile(rule["regex"])
            match = pattern.search(full_text)
            if match:
                value = match.group(1).strip()
                value = normalizer.full_normalize(value)
                extracted[rule["field_name"]] = value
                if queue_handler:
                    queue_handler.put(MessageType.PROGRESS, ("Extract", f"  提取 [{rule['field_name']}] = {value}"))
        result["extracted"] = extracted
        return result

    elif ext in (".xlsx", ".xls"):
        sheets = Extractor.extract_excel(file_path)
        all_text = "\n".join(
            "\n".join("\t".join(row) for row in rows)
            for rows in sheets.values()
        )

        result = {"raw_text": all_text, "sheets": sheets}

        extracted = {}
        import re
        for rule in rules:
            pattern = re.compile(rule["regex"])
            match = pattern.search(all_text)
            if match:
                value = match.group(1).strip()
                value = normalizer.full_normalize(value)
                extracted[rule["field_name"]] = value
                if queue_handler:
                    queue_handler.put(MessageType.PROGRESS, ("Extract", f"  提取 [{rule['field_name']}] = {value}"))
        result["extracted"] = extracted
        return result

    return None
