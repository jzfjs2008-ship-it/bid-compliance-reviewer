import re
from datetime import datetime
from .normalizer import Normalizer
from database.models import load_comparison_rules
from utils.queue_handler import MessageType


OPERATOR_MAP = {}


def register_op(name):
    def wrapper(fn):
        OPERATOR_MAP[name] = fn
        return fn
    return wrapper


@register_op("EQ")
def op_eq(bid_val, resp_val):
    if bid_val is None or resp_val is None:
        return None
    return str(bid_val).strip() == str(resp_val).strip()


@register_op("NE")
def op_ne(bid_val, resp_val):
    if bid_val is None or resp_val is None:
        return None
    return str(bid_val).strip() != str(resp_val).strip()


@register_op("GTE")
def op_gte(bid_val, resp_val):
    b = Normalizer.extract_number(bid_val)
    r = Normalizer.extract_number(resp_val)
    if b is None or r is None:
        return None
    return r >= b


@register_op("LTE")
def op_lte(bid_val, resp_val):
    b = Normalizer.extract_number(bid_val)
    r = Normalizer.extract_number(resp_val)
    if b is None or r is None:
        return None
    return r <= b


@register_op("GT")
def op_gt(bid_val, resp_val):
    b = Normalizer.extract_number(bid_val)
    r = Normalizer.extract_number(resp_val)
    if b is None or r is None:
        return None
    return r > b


@register_op("LT")
def op_lt(bid_val, resp_val):
    b = Normalizer.extract_number(bid_val)
    r = Normalizer.extract_number(resp_val)
    if b is None or r is None:
        return None
    return r < b


@register_op("CONTAINS")
def op_contains(bid_val, resp_val):
    if bid_val is None or resp_val is None:
        return None
    return str(bid_val).strip() in str(resp_val).strip()


@register_op("NOT_CONTAINS")
def op_not_contains(bid_val, resp_val):
    if bid_val is None or resp_val is None:
        return None
    return str(bid_val).strip() not in str(resp_val).strip()


@register_op("REGEX")
def op_regex(bid_val, resp_val):
    if bid_val is None or resp_val is None:
        return None
    try:
        return bool(re.search(str(resp_val), str(bid_val)))
    except re.error:
        return None


class Comparator:
    def __init__(self, queue_handler=None):
        self.queue_handler = queue_handler

    def compare(self, bid_data, resp_data_by_slot):
        rules = load_comparison_rules()
        results = []

        for rule in rules:
            try:
                result = self._evaluate_rule(rule, bid_data, resp_data_by_slot)
                results.append(result)
                if self.queue_handler:
                    self.queue_handler.put(MessageType.PROGRESS, ("Compare", f"比对规则 [{rule['rule_name']}]: {result['status']}"))
            except Exception as e:
                results.append({
                    "rule_id": rule["id"],
                    "rule_name": rule["rule_name"],
                    "status": "error",
                    "risk_level": rule["risk_level"],
                    "error_message": rule["error_message"],
                    "detail": str(e),
                })

        return results

    def _evaluate_rule(self, rule, bid_data, resp_data_by_slot):
        field_bid = rule.get("field_bid")
        field_resp = rule.get("field_response")
        operator = rule.get("operator")
        error_msg = rule.get("error_message")
        risk_level = rule.get("risk_level")
        cross_validate = rule.get("cross_validate", 0)
        cross_slot = rule.get("cross_slot")
        cross_field = rule.get("cross_field")

        # Resolve response value: search across all response slots
        resp_val = None
        for slot_name, data in resp_data_by_slot.items():
            extracted = data.get("extracted", {})
            if field_resp in extracted:
                resp_val = extracted[field_resp]
                break

        # Resolve bid / reference value
        bid_val = None

        if cross_validate and cross_slot and cross_field:
            # Cross-document: look up the reference field from another slot
            if cross_slot == "招标文件" and bid_data:
                extracted = bid_data.get("extracted", {})
                if cross_field in extracted:
                    bid_val = extracted[cross_field]
                elif self.queue_handler:
                    self.queue_handler.put(MessageType.PROGRESS,
                        ("Compare", f"  跨文档: {cross_slot}.{cross_field} 未提取到"))
            elif cross_slot in resp_data_by_slot:
                extracted = resp_data_by_slot[cross_slot].get("extracted", {})
                if cross_field in extracted:
                    bid_val = extracted[cross_field]
                elif self.queue_handler:
                    self.queue_handler.put(MessageType.PROGRESS,
                        ("Compare", f"  跨文档: {cross_slot}.{cross_field} 未提取到"))
            # Also try field_bid as fallback
            if bid_val is None and field_bid and bid_data:
                extracted = bid_data.get("extracted", {})
                if field_bid in extracted:
                    bid_val = extracted[field_bid]
        elif field_bid and bid_data:
            extracted = bid_data.get("extracted", {})
            if field_bid in extracted:
                bid_val = extracted[field_bid]

        op_fn = OPERATOR_MAP.get(operator)
        if not op_fn:
            return self._make_result(rule, "error", risk_level, error_msg,
                                     f"未知操作符: {operator}")

        passed = op_fn(bid_val, resp_val)

        if passed is None:
            return self._make_result(rule, "skip", "合规", error_msg,
                                     "缺失比对数据，已跳过")
        if passed:
            return self._make_result(rule, "pass", "合规", error_msg,
                                     "比对通过")
        else:
            from database.models import load_rejection_tags
            tags = load_rejection_tags()
            matched_tags = []
            for tag in tags:
                for slot_data in resp_data_by_slot.values():
                    raw_text = slot_data.get("raw_text", "")
                    if tag in raw_text:
                        matched_tags.append(tag)
                        break
            return self._make_result(rule, "fail", risk_level, error_msg,
                                     f"值不匹配: bid={bid_val}, resp={resp_val}",
                                     matched_tags)

    def _make_result(self, rule, status, risk_level, error_message, detail, tags=None):
        return {
            "rule_id": rule["id"],
            "rule_name": rule["rule_name"],
            "status": status,
            "risk_level": risk_level,
            "error_message": error_message,
            "detail": detail,
            "matched_tags": tags or [],
        }
