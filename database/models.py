from .schema import get_connection


def load_extraction_rules(slot=None):
    conn = get_connection()
    try:
        if slot:
            rows = conn.execute(
                "SELECT * FROM extraction_rules WHERE is_active=1 AND slot=?",
                (slot,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM extraction_rules WHERE is_active=1"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def load_comparison_rules():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM comparison_rules WHERE is_active=1"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def load_unit_dict():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT raw_unit, clean_unit FROM unit_dict").fetchall()
        return {r["raw_unit"]: r["clean_unit"] for r in rows}
    finally:
        conn.close()


def load_synonym_dict():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT raw_text, normalized FROM synonym_dict").fetchall()
        return {r["raw_text"]: r["normalized"] for r in rows}
    finally:
        conn.close()


def load_rejection_tags():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT tag FROM rejection_tags").fetchall()
        return [r["tag"] for r in rows]
    finally:
        conn.close()
