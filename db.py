"""
db.py  –  Invento Database Inspector
=====================================
Connects to the Aiven MySQL database and prints a full description
of every table: columns, types, keys, nullability, defaults, and FKs.

Usage:
    pip install pymysql
    python db.py
"""

import pymysql
import sys

# ── Connection ────────────────────────────────────────────────────────────────
DB_CONFIG = {
    'host':        'mysql-tchs-ahmedmustaphahammouda.k.aivencloud.com',
    'port':        19932,
    'user':        'avnadmin',
    'password':    'AVNS_gk-MK5-1fa-HjpSNe28',
    'database':    'defaultdb',
    'charset':     'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'connect_timeout': 20,
}


def connect():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print(f"  [✓] Connected to '{DB_CONFIG['database']}' "
              f"on {DB_CONFIG['host']}:{DB_CONFIG['port']}\n")
        return conn
    except pymysql.MySQLError as e:
        print(f"  [✗] Connection failed: {e}")
        sys.exit(1)


def get_tables(cursor):
    cursor.execute("SHOW TABLES;")
    rows = cursor.fetchall()
    key = list(rows[0].keys())[0] if rows else None
    return [r[key] for r in rows] if key else []


def describe_table(cursor, table):
    cursor.execute(f"DESCRIBE `{table}`;")
    return cursor.fetchall()


def get_indexes(cursor, table):
    cursor.execute(f"SHOW INDEX FROM `{table}`;")
    return cursor.fetchall()


def get_foreign_keys(cursor, table, database):
    sql = """
        SELECT
            kcu.CONSTRAINT_NAME        AS constraint_name,
            kcu.COLUMN_NAME            AS column_name,
            kcu.REFERENCED_TABLE_NAME  AS ref_table,
            kcu.REFERENCED_COLUMN_NAME AS ref_column,
            rc.UPDATE_RULE,
            rc.DELETE_RULE
        FROM information_schema.KEY_COLUMN_USAGE kcu
        JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
          ON rc.CONSTRAINT_NAME   = kcu.CONSTRAINT_NAME
         AND rc.CONSTRAINT_SCHEMA = kcu.TABLE_SCHEMA
        WHERE kcu.TABLE_SCHEMA          = %s
          AND kcu.TABLE_NAME            = %s
          AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY kcu.CONSTRAINT_NAME;
    """
    cursor.execute(sql, (database, table))
    return cursor.fetchall()


def get_table_meta(cursor, table, database):
    cursor.execute("""
        SELECT TABLE_COMMENT, TABLE_ROWS, ENGINE
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
    """, (database, table))
    return cursor.fetchone()


def sep(char="─", width=72):
    print(char * width)


def print_table_info(cursor, table, database):
    sep("═")
    meta   = get_table_meta(cursor, table, database)
    engine = meta['ENGINE']    if meta else '?'
    rows   = meta['TABLE_ROWS'] if meta else '?'
    print(f"  TABLE: {table.upper():<35} engine={engine}  ~{rows} rows")
    sep("═")

    # ── Columns ──────────────────────────────────────────────────────────────
    columns = describe_table(cursor, table)
    fmt = "  {:<28} {:<22} {:<8} {:<8} {:<20} {}"
    print(fmt.format("Column", "Type", "Null", "Key", "Default", "Extra"))
    sep()
    for col in columns:
        print(fmt.format(
            col.get('Field',   ''),
            col.get('Type',    ''),
            col.get('Null',    ''),
            col.get('Key',     ''),
            str(col.get('Default', '') or ''),
            col.get('Extra',   '')
        ))

    # ── Indexes ──────────────────────────────────────────────────────────────
    indexes = get_indexes(cursor, table)
    if indexes:
        print()
        print("  INDEXES:")
        grouped = {}
        for idx in indexes:
            name   = idx['Key_name']
            unique = "UNIQUE" if idx['Non_unique'] == 0 else "INDEX"
            grouped.setdefault(name, {'type': unique, 'cols': []})
            grouped[name]['cols'].append(idx['Column_name'])
        for name, info in grouped.items():
            label = "PRIMARY KEY" if name == "PRIMARY" else f"{info['type']} {name}"
            print(f"    {label}  ({', '.join(info['cols'])})")

    # ── Foreign Keys ─────────────────────────────────────────────────────────
    fks = get_foreign_keys(cursor, table, database)
    if fks:
        print()
        print("  FOREIGN KEYS:")
        for fk in fks:
            print(f"    [{fk['constraint_name']}]")
            print(f"      {table}.{fk['column_name']}  →  "
                  f"{fk['ref_table']}.{fk['ref_column']}"
                  f"  (UPDATE {fk['UPDATE_RULE']} | DELETE {fk['DELETE_RULE']})")

    print()


def main():
    print("\n" + "=" * 72)
    print("   INVENTO – DATABASE SCHEMA INSPECTOR")
    print("=" * 72 + "\n")

    conn = connect()

    with conn:
        with conn.cursor() as cursor:
            tables = get_tables(cursor)

            if not tables:
                print("  No tables found in the database.")
                return

            print(f"  Found {len(tables)} table(s):\n")
            for i, t in enumerate(sorted(tables), 1):
                print(f"    {i:>2}. {t}")
            print()

            for table in sorted(tables):
                print_table_info(cursor, table, DB_CONFIG['database'])

    print("=" * 72)
    print(f"  Done — {len(tables)} tables described.")
    print("=" * 72 + "\n")


if __name__ == '__main__':
    main()