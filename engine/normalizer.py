import re


class Normalizer:
    def __init__(self, unit_dict=None, synonym_dict=None):
        self.unit_dict = unit_dict or {}
        self.synonym_dict = synonym_dict or {}

    def clean_unit(self, text):
        if not text:
            return text
        result = str(text)
        for raw, clean in self.unit_dict.items():
            result = re.sub(re.escape(raw), clean, result, flags=re.IGNORECASE)
        return result

    def normalize_synonym(self, text):
        if not text:
            return text
        result = str(text)
        for raw, norm in self.synonym_dict.items():
            result = re.sub(re.escape(raw), norm, result, flags=re.IGNORECASE)
        return result

    def full_normalize(self, text):
        return self.normalize_synonym(self.clean_unit(text))

    @staticmethod
    def extract_number(text):
        if not text:
            return None
        match = re.search(r"([\d,]+(?:\.\d+)?)", str(text).replace(",", ""))
        if match:
            return float(match.group(1))
        return None

    @staticmethod
    def extract_number_with_unit(text):
        if not text:
            return None, None
        match = re.search(r"([\d,]+(?:\.\d+)?)\s*(\D+)", str(text))
        if match:
            num = float(match.group(1).replace(",", ""))
            unit = match.group(2).strip()
            return num, unit
        return None, None

    @staticmethod
    def cast_value(value, data_type):
        if value is None:
            return None
        if data_type == "number":
            try:
                return float(str(value).replace(",", "").replace("¥", "").replace("￥", ""))
            except (ValueError, TypeError):
                return None
        if data_type == "date":
            return str(value).strip()
        return str(value).strip()
