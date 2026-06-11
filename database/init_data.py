import sqlite3
from .schema import DB_PATH


SEED_RULES = [
    # ===== extraction_rules =====

    # 招标文件
    ("项目名称", "项目名称", r"项目名称[:：\s]*(.+?)[\r\n]", "string", "招标文件"),
    ("招标编号", "招标编号", r"招标编号[:：\s]*(.+?)[\r\n]", "string", "招标文件"),
    ("投标截止日期", "投标截止", r"投标截止(?:日期|时间)?[:：\s]*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})", "date", "招标文件"),
    ("控制价", r"(?:控制价|最高限价|预算)", r"(?:控制价|最高限价|项目预算)[:：\s]*[¥￥]?([\d,]+(?:\.\d{1,2})?)", "number", "招标文件"),
    ("质保期要求", r"质保期", r"质保期[:：\s]*不少于?(\d+)[\s]*(年|月)", "number", "招标文件"),
    ("工期要求", r"(?:工期|交货期)", r"(?:工期|交货期|供货期)[:：\s]*不超过?(\d+)[\s]*(天|日|月|年)", "number", "招标文件"),
    ("付款方式", "付款方式", r"付款方式[:：\s]*(.+?)[\r\n]", "string", "招标文件"),
    ("投标有效期", "投标有效期", r"投标有效期[:：\s]*(\d+)[\s]*(天|日|月)", "number", "招标文件"),
    ("资质要求", "资质", r"(?:投标人)?资质(?:\s*要求)?[:：\s]*(.+?)[\r\n]", "string", "招标文件"),

    # 商务标
    ("投标人名称", "投标人", r"投标人(?:名称)?[:：\s]*(.+?)[\r\n]", "string", "商务标"),
    ("项目负责人", "项目负责人", r"项目负责人[:：\s]*(.+?)[\r\n]", "string", "商务标"),
    ("营业执照编号", "营业执照", r"营业执照(?:\s*编号)?[:：\s]*([A-Za-z0-9]+)", "string", "商务标"),
    ("投标人资质", "资质", r"(?:投标人)?资质(?:\s*证书|\s*等级)?[:：\s]*(.+?)[\r\n]", "string", "商务标"),
    ("付款方式响应", "付款方式", r"付款方式[:：\s]*(.+?)[\r\n]", "string", "商务标"),
    ("投标有效期响应", "投标有效期", r"投标有效期[:：\s]*(\d+)[\s]*(天|日|月)", "number", "商务标"),

    # 技术标
    ("质保期", "质保期", r"质保期[:：\s]*(\d+)[\s]*(年|月)", "number", "技术标"),
    ("工期", "工期", r"(?:工期|交货期|供货期)[:：\s]*(\d+)[\s]*(天|日|月|年)", "number", "技术标"),
    ("技术方案概述", "技术方案", r"技术方案[:：\s]*(.+?)(?:\r\n\r\n|\Z)", "string", "技术标"),

    # 价格标
    ("总报价", "总报价", r"总报价[:：\s]*[¥￥]?([\d,]+(?:\.\d{1,2})?)", "number", "价格标"),

    # ===== comparison_rules =====
    # (rule_name, field_bid, field_response, operator, error_message, risk_level, cross_validate, cross_slot, cross_field)

    # 形式合规 — 直接比对（招标文件 vs 响应文件同一字段）
    ("投标人名称一致性", "投标人名称", "投标人名称", "EQ", "投标人名称与招标文件要求不一致", "致命", 0, None, None),
    ("项目负责人一致性", "项目负责人", "项目负责人", "EQ", "项目负责人信息不一致", "人工复核", 0, None, None),
    ("营业执照有效性", "营业执照编号", "营业执照编号", "REGEX", "营业执照编号格式异常", "人工复核", 0, None, None),
    ("资质符合性", "资质要求", "投标人资质", "CONTAINS", "投标人资质不满足招标文件要求", "致命", 0, None, None),

    # 跨文档交叉校验（cross_validate=1: 不同文档之间的字段联动）
    ("总报价 vs 控制价", None, "总报价", "LTE", "投标总报价超过招标控制价", "致命", 1, "招标文件", "控制价"),
    ("质保期 vs 质保期要求", None, "质保期", "GTE", "质保期不满足招标文件最低要求", "高危", 1, "招标文件", "质保期要求"),
    ("工期 vs 工期要求", None, "工期", "LTE", "工期/交货期超出招标文件要求", "高危", 1, "招标文件", "工期要求"),
    ("付款方式一致性", None, "付款方式响应", "CONTAINS", "投标付款方式与招标文件不一致", "人工复核", 1, "招标文件", "付款方式"),
    ("投标有效期一致性", None, "投标有效期响应", "GTE", "投标有效期不满足招标文件要求", "高危", 1, "招标文件", "投标有效期"),

    # 技术-价格联动校验
    ("技术方案与报价匹配", "技术方案概述", "总报价", "REGEX", "技术方案与报价无明显关联，建议人工复核", "人工复核", 0, None, None),
]


UNIT_DICT = [
    ("年", "年"), ("月", "月"), ("天", "天"), ("日", "天"),
    ("GB", "GB"), ("MB", "MB"), ("TB", "GB"),
    ("个", "个"), ("套", "套"), ("台", "台"),
    ("万元", "元"), ("万", "元"),
    ("%", "%"), ("百分比", "%"),
]

SYNONYM_DICT = [
    ("近期", "近三个月"),
    ("近三年", "近三年"),
    ("合同签订后", "合同签订后"),
    ("甲方", "招标人"),
    ("乙方", "投标人"),
    ("控制价", "最高限价"),
    ("拦标价", "最高限价"),
]

REJECTION_TAGS = [
    ("围标串标", "多家投标人文件属性相同"),
    ("弄虚作假", "提供虚假资质材料"),
    ("低于成本价", "报价明显低于市场平均水平"),
    ("未按要求盖章", "投标文件缺少法定印章"),
    ("逾期送达", "投标文件未在截止时间前提交"),
    ("资质不符", "投标人不具备要求的资质证书"),
]


def seed_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM extraction_rules")
    if c.fetchone()[0] == 0:
        for rule in SEED_RULES:
            if len(rule) == 5:
                c.execute(
                    "INSERT INTO extraction_rules (field_name, anchor, regex, data_type, slot) VALUES (?,?,?,?,?)",
                    rule
                )
            elif len(rule) == 9:
                c.execute(
                    """INSERT INTO comparison_rules
                       (rule_name, field_bid, field_response, operator, error_message, risk_level, cross_validate, cross_slot, cross_field)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    rule
                )

    c.execute("SELECT COUNT(*) FROM unit_dict")
    if c.fetchone()[0] == 0:
        for raw, clean in UNIT_DICT:
            c.execute("INSERT INTO unit_dict (raw_unit, clean_unit) VALUES (?,?)", (raw, clean))

    c.execute("SELECT COUNT(*) FROM synonym_dict")
    if c.fetchone()[0] == 0:
        for raw, norm in SYNONYM_DICT:
            c.execute("INSERT INTO synonym_dict (raw_text, normalized) VALUES (?,?)", (raw, norm))

    c.execute("SELECT COUNT(*) FROM rejection_tags")
    if c.fetchone()[0] == 0:
        for tag, desc in REJECTION_TAGS:
            c.execute("INSERT INTO rejection_tags (tag, description) VALUES (?,?)", (tag, desc))

    conn.commit()
    conn.close()
