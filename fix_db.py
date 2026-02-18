"""
fix_db.py  –  Invento Database Patcher
========================================
Compares the live Aiven MySQL database against models.py and applies
only the missing pieces:

  • Creates missing tables  (stock_movement, purchase_order, purchase_order_item)
  • Adds missing columns    (project: budget_reel, prix_vente, marge)
  • Fixes missing AUTO_INCREMENT on equipment_file.id, equipment_maintenance.id
  • Adds missing FK constraints on equipment_file, equipment_maintenance,
    equipment_stock_items

Everything is idempotent – safe to run multiple times.

Usage:
    pip install pymysql
    python fix_db.py
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

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def connect():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print(f"  [✓] Connected to '{DB_CONFIG['database']}'\n")
        return conn
    except pymysql.MySQLError as e:
        print(f"  [✗] Connection failed: {e}")
        sys.exit(1)


def table_exists(cursor, table):
    cursor.execute("""
        SELECT COUNT(*) AS cnt FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
    """, (DB_CONFIG['database'], table))
    return cursor.fetchone()['cnt'] > 0


def column_exists(cursor, table, column):
    cursor.execute("""
        SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
    """, (DB_CONFIG['database'], table, column))
    return cursor.fetchone()['cnt'] > 0


def fk_exists(cursor, table, constraint_name):
    cursor.execute("""
        SELECT COUNT(*) AS cnt FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
          AND CONSTRAINT_NAME = %s AND CONSTRAINT_TYPE = 'FOREIGN KEY'
    """, (DB_CONFIG['database'], table, constraint_name))
    return cursor.fetchone()['cnt'] > 0


def get_column_extra(cursor, table, column):
    """Return the EXTRA field for a column (e.g. 'auto_increment')."""
    cursor.execute("""
        SELECT EXTRA FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
    """, (DB_CONFIG['database'], table, column))
    row = cursor.fetchone()
    return row['EXTRA'] if row else None


def run(cursor, label, sql):
    try:
        cursor.execute(sql)
        print(f"  [✓] {label}")
        return True
    except pymysql.MySQLError as e:
        # 1060 = duplicate column, 1061 = duplicate key, 1826 = duplicate FK
        if e.args[0] in (1060, 1061, 1826, 1050):
            print(f"  [~] {label}  (already exists, skipped)")
        else:
            print(f"  [✗] {label}  ERROR {e.args[0]}: {e.args[1]}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Fix functions
# ─────────────────────────────────────────────────────────────────────────────

def fix_missing_tables(cursor):
    """Create the three tables that exist in models.py but not in the live DB."""
    print("── Missing tables ───────────────────────────────────────────────────")

    # 1. stock_movement ───────────────────────────────────────────────────────
    if not table_exists(cursor, 'stock_movement'):
        run(cursor, "CREATE TABLE stock_movement", """
            CREATE TABLE stock_movement (
                id            INT          NOT NULL AUTO_INCREMENT,
                movement_type VARCHAR(20)  NOT NULL
                    COMMENT 'purchase | sale | transfer | adjustment | waste | return',
                quantity      DECIMAL(10,2) NOT NULL,
                unit_price    DECIMAL(10,2),
                total_price   DECIMAL(10,2),
                reference     VARCHAR(64)   COMMENT 'invoice / PO number',
                notes         TEXT,
                movement_date DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
                recorded_by   INT,
                stock_item_id INT,
                supplier_id   INT,
                task_id       INT,
                project_id    INT,
                PRIMARY KEY (id),
                INDEX idx_smov_stock    (stock_item_id),
                INDEX idx_smov_date     (movement_date),
                INDEX idx_smov_type     (movement_type),
                CONSTRAINT fk_smov_user     FOREIGN KEY (recorded_by)
                    REFERENCES `user`    (id) ON DELETE SET NULL,
                CONSTRAINT fk_smov_stock    FOREIGN KEY (stock_item_id)
                    REFERENCES stock_item (id) ON DELETE CASCADE,
                CONSTRAINT fk_smov_supplier FOREIGN KEY (supplier_id)
                    REFERENCES supplier  (id) ON DELETE SET NULL,
                CONSTRAINT fk_smov_task     FOREIGN KEY (task_id)
                    REFERENCES task      (id) ON DELETE SET NULL,
                CONSTRAINT fk_smov_project  FOREIGN KEY (project_id)
                    REFERENCES project   (id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
    else:
        print("  [~] TABLE stock_movement  (already exists, skipped)")

    # 2. purchase_order ───────────────────────────────────────────────────────
    if not table_exists(cursor, 'purchase_order'):
        run(cursor, "CREATE TABLE purchase_order", """
            CREATE TABLE purchase_order (
                id            INT          NOT NULL AUTO_INCREMENT,
                order_number  VARCHAR(64)  NOT NULL UNIQUE,
                status        VARCHAR(20)  NOT NULL DEFAULT 'pending'
                    COMMENT 'pending | ordered | delivered | cancelled',
                order_date    DATE         NOT NULL,
                delivery_date DATE,
                total_amount  DECIMAL(12,2) DEFAULT 0.00,
                notes         TEXT,
                created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,
                supplier_id   INT,
                created_by    INT,
                PRIMARY KEY (id),
                INDEX idx_po_status      (status),
                INDEX idx_po_order_date  (order_date),
                INDEX fk_po_supplier     (supplier_id),
                INDEX fk_po_user         (created_by),
                CONSTRAINT fk_po_supplier FOREIGN KEY (supplier_id)
                    REFERENCES supplier (id) ON DELETE SET NULL,
                CONSTRAINT fk_po_user     FOREIGN KEY (created_by)
                    REFERENCES `user`   (id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
    else:
        print("  [~] TABLE purchase_order  (already exists, skipped)")

    # 3. purchase_order_item ──────────────────────────────────────────────────
    if not table_exists(cursor, 'purchase_order_item'):
        run(cursor, "CREATE TABLE purchase_order_item", """
            CREATE TABLE purchase_order_item (
                id                INT           NOT NULL AUTO_INCREMENT,
                quantity_ordered  DECIMAL(10,2) NOT NULL,
                quantity_received DECIMAL(10,2) DEFAULT 0.00,
                unit_price        DECIMAL(10,2) NOT NULL,
                total_price       DECIMAL(10,2),
                notes             TEXT,
                purchase_order_id INT,
                stock_item_id     INT,
                PRIMARY KEY (id),
                INDEX fk_poi_order (purchase_order_id),
                INDEX fk_poi_stock (stock_item_id),
                CONSTRAINT fk_poi_order FOREIGN KEY (purchase_order_id)
                    REFERENCES purchase_order (id) ON DELETE CASCADE,
                CONSTRAINT fk_poi_stock FOREIGN KEY (stock_item_id)
                    REFERENCES stock_item     (id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
    else:
        print("  [~] TABLE purchase_order_item  (already exists, skipped)")

    print()


def fix_project_columns(cursor):
    """Add budget_reel, prix_vente, marge to project table."""
    print("── project  –  missing columns ──────────────────────────────────────")

    if not column_exists(cursor, 'project', 'budget_reel'):
        run(cursor, "ALTER project ADD budget_reel",
            "ALTER TABLE project ADD COLUMN budget_reel DECIMAL(12,2) DEFAULT 0.00 AFTER estimated_budget")
    else:
        print("  [~] project.budget_reel  (already exists)")

    if not column_exists(cursor, 'project', 'prix_vente'):
        run(cursor, "ALTER project ADD prix_vente",
            "ALTER TABLE project ADD COLUMN prix_vente DECIMAL(12,2) DEFAULT 0.00 AFTER budget_reel")
    else:
        print("  [~] project.prix_vente  (already exists)")

    if not column_exists(cursor, 'project', 'marge'):
        run(cursor, "ALTER project ADD marge",
            "ALTER TABLE project ADD COLUMN marge DECIMAL(12,2) DEFAULT 0.00 AFTER prix_vente")
    else:
        print("  [~] project.marge  (already exists)")

    print()


def fix_equipment_file(cursor):
    """Fix equipment_file: add AUTO_INCREMENT to id, add missing FK constraints."""
    print("── equipment_file  –  auto_increment + FK constraints ───────────────")

    # Fix AUTO_INCREMENT on id
    extra = get_column_extra(cursor, 'equipment_file', 'id')
    if extra is not None and 'auto_increment' not in extra.lower():
        run(cursor, "ALTER equipment_file.id → AUTO_INCREMENT",
            "ALTER TABLE equipment_file MODIFY id INT NOT NULL AUTO_INCREMENT")
    else:
        print("  [~] equipment_file.id AUTO_INCREMENT  (already set)")

    # FK: equipment_file.equipment_id → equipment.id
    if not fk_exists(cursor, 'equipment_file', 'fk_ef_equipment'):
        run(cursor, "ADD FK equipment_file.equipment_id → equipment.id", """
            ALTER TABLE equipment_file
            ADD CONSTRAINT fk_ef_equipment
                FOREIGN KEY (equipment_id) REFERENCES equipment (id) ON DELETE CASCADE
        """)
    else:
        print("  [~] FK fk_ef_equipment  (already exists)")

    # FK: equipment_file.uploaded_by → user.id
    if not fk_exists(cursor, 'equipment_file', 'fk_ef_user'):
        run(cursor, "ADD FK equipment_file.uploaded_by → user.id", """
            ALTER TABLE equipment_file
            ADD CONSTRAINT fk_ef_user
                FOREIGN KEY (uploaded_by) REFERENCES `user` (id) ON DELETE SET NULL
        """)
    else:
        print("  [~] FK fk_ef_user  (already exists)")

    print()


def fix_equipment_maintenance(cursor):
    """Fix equipment_maintenance: add AUTO_INCREMENT to id, add FK constraints."""
    print("── equipment_maintenance  –  auto_increment + FK constraints ────────")

    # Fix AUTO_INCREMENT on id
    extra = get_column_extra(cursor, 'equipment_maintenance', 'id')
    if extra is not None and 'auto_increment' not in extra.lower():
        run(cursor, "ALTER equipment_maintenance.id → AUTO_INCREMENT",
            "ALTER TABLE equipment_maintenance MODIFY id INT NOT NULL AUTO_INCREMENT")
    else:
        print("  [~] equipment_maintenance.id AUTO_INCREMENT  (already set)")

    # FK: equipment_maintenance.equipment_id → equipment.id
    if not fk_exists(cursor, 'equipment_maintenance', 'fk_em_equipment'):
        run(cursor, "ADD FK equipment_maintenance.equipment_id → equipment.id", """
            ALTER TABLE equipment_maintenance
            ADD CONSTRAINT fk_em_equipment
                FOREIGN KEY (equipment_id) REFERENCES equipment (id) ON DELETE CASCADE
        """)
    else:
        print("  [~] FK fk_em_equipment  (already exists)")

    # FK: equipment_maintenance.performed_by_user → user.id
    if not fk_exists(cursor, 'equipment_maintenance', 'fk_em_user'):
        run(cursor, "ADD FK equipment_maintenance.performed_by_user → user.id", """
            ALTER TABLE equipment_maintenance
            ADD CONSTRAINT fk_em_user
                FOREIGN KEY (performed_by_user) REFERENCES `user` (id) ON DELETE SET NULL
        """)
    else:
        print("  [~] FK fk_em_user  (already exists)")

    print()


def fix_equipment_stock_items(cursor):
    """Add missing FK constraints on the equipment_stock_items junction table."""
    print("── equipment_stock_items  –  FK constraints ─────────────────────────")

    if not fk_exists(cursor, 'equipment_stock_items', 'fk_esi_equipment'):
        run(cursor, "ADD FK equipment_stock_items.equipment_id → equipment.id", """
            ALTER TABLE equipment_stock_items
            ADD CONSTRAINT fk_esi_equipment
                FOREIGN KEY (equipment_id) REFERENCES equipment  (id) ON DELETE CASCADE
        """)
    else:
        print("  [~] FK fk_esi_equipment  (already exists)")

    if not fk_exists(cursor, 'equipment_stock_items', 'fk_esi_stock'):
        run(cursor, "ADD FK equipment_stock_items.stock_item_id → stock_item.id", """
            ALTER TABLE equipment_stock_items
            ADD CONSTRAINT fk_esi_stock
                FOREIGN KEY (stock_item_id) REFERENCES stock_item (id) ON DELETE CASCADE
        """)
    else:
        print("  [~] FK fk_esi_stock  (already exists)")

    print()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 68)
    print("   INVENTO – DATABASE PATCHER  (fix_db.py)")
    print("=" * 68 + "\n")

    conn = connect()

    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

            fix_missing_tables(cursor)
            fix_project_columns(cursor)
            fix_equipment_file(cursor)
            fix_equipment_maintenance(cursor)
            fix_equipment_stock_items(cursor)

            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            conn.commit()

    print("=" * 68)
    print("  All fixes applied. Your database now matches models.py.")
    print("=" * 68 + "\n")


if __name__ == '__main__':
    main()