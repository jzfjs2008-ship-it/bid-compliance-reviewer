import sqlite3
import os


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules.db")


def get_connection(read_only=True):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if read_only:
        conn.execute("PRAGMA query_only = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL")
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS extraction_rules (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name  TEXT NOT NULL,
            anchor      TEXT NOT NULL,
            regex       TEXT NOT NULL,
            data_type   TEXT NOT NULL DEFAULT 'string',
            slot        TEXT NOT NULL CHECK(slot IN ('招标文件','商务标','技术标','价格标')),
            description TEXT DEFAULT '',
            is_active   INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS comparison_rules (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_name           TEXT NOT NULL,
            field_bid           TEXT,
            field_response      TEXT,
            operator            TEXT NOT NULL CHECK(operator IN ('EQ','NE','GTE','LTE','GT','LT','CONTAINS','NOT_CONTAINS','REGEX')),
            error_message       TEXT NOT NULL,
            risk_level          TEXT NOT NULL CHECK(risk_level IN ('致命','高危','人工复核','合规')),
            cross_validate      INTEGER NOT NULL DEFAULT 0,
            cross_slot          TEXT DEFAULT NULL,
            cross_field         TEXT DEFAULT NULL,
            is_active           INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS unit_dict (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_unit    TEXT NOT NULL,
            clean_unit  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS synonym_dict (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_text    TEXT NOT NULL,
            normalized  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS rejection_tags (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            tag         TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT ''
        );
    """)

    conn.commit()
    conn.close()
    return DB_PATH
