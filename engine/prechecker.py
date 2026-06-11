import os
from .parser_router import SUPPORTED_EXTENSIONS


SLOT_NAMES = ["招标文件", "商务标", "技术标", "价格标"]


def precheck_files(file_map):
    warnings = []
    errors = []

    for slot in SLOT_NAMES:
        files = file_map.get(slot, [])
        if not files:
            warnings.append({
                "slot": slot,
                "level": "warning",
                "message": f"未上传 [{slot}]，涉及该分卷的比对规则将被跳过",
            })
            continue

        for f in files:
            if not os.path.isfile(f):
                errors.append({
                    "slot": slot,
                    "level": "error",
                    "message": f"文件不存在: {f}",
                })
                continue

            ext = os.path.splitext(f)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                errors.append({
                    "slot": slot,
                    "level": "error",
                    "message": f"不支持的文件类型: {f}",
                })

            file_size = os.path.getsize(f)
            if file_size == 0:
                errors.append({
                    "slot": slot,
                    "level": "error",
                    "message": f"空文件: {f}",
                })

    return {
        "has_error": len(errors) > 0,
        "errors": errors,
        "warnings": warnings,
        "can_proceed": len(errors) == 0,
    }


def get_slots_with_files(file_map):
    return {slot: files for slot, files in file_map.items() if files}
