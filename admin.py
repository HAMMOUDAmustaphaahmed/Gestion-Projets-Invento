"""
admin.py - Script to create an admin user in the Invento database.
Run this script from the root of your Flask project:
    python admin.py
"""

import pymysql
from werkzeug.security import generate_password_hash
from datetime import datetime

# ── Database connection (from config.py) ──────────────────────────────────────
DB_CONFIG = {
    'host':     'mysql-tchs-ahmedmustaphahammouda.k.aivencloud.com',
    'port':     19932,
    'user':     'avnadmin',
    'password': 'AVNS_gk-MK5-1fa-HjpSNe28',
    'database': 'defaultdb',
    'charset':  'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'connect_timeout': 20,
}

# ── Admin user details ─────────────────────────────────────────────────────────
ADMIN = {
    'username':   'Hammouda',
    'email':      'hammouda@invento.com',   # change if needed
    'password':   'Hammouda.123!',
    'first_name': 'Hammouda',
    'last_name':  'Admin',
    'is_active':  True,
}


def get_or_create_admin_role(cursor):
    """Return the id of the 'admin' role, creating it if it doesn't exist."""
    cursor.execute("SELECT id FROM role WHERE name = 'admin'")
    row = cursor.fetchone()
    if row:
        print(f"  [✓] Role 'admin' found (id={row['id']})")
        return row['id']

    # Full-access permissions for every known module
    import json
    modules = [
        'personnel', 'groups', 'stock', 'projects', 'tasks',
        'interventions', 'equipment', 'suppliers', 'users', 'reports',
    ]
    permissions = {m: {'read': True, 'create': True, 'update': True, 'delete': True}
                   for m in modules}

    cursor.execute(
        "INSERT INTO role (name, description, permissions) VALUES (%s, %s, %s)",
        ('admin', 'Administrateur système', json.dumps(permissions))
    )
    role_id = cursor.lastrowid
    print(f"  [+] Role 'admin' created (id={role_id})")
    return role_id


def create_admin_user():
    print("\n=== Invento – Create Admin User ===\n")

    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:

            # 1. Ensure the admin role exists
            role_id = get_or_create_admin_role(cursor)

            # 2. Check if the username already exists
            cursor.execute("SELECT id FROM user WHERE username = %s", (ADMIN['username'],))
            if cursor.fetchone():
                print(f"  [!] User '{ADMIN['username']}' already exists. Aborting.")
                return

            # 3. Check if the email already exists
            cursor.execute("SELECT id FROM user WHERE email = %s", (ADMIN['email'],))
            if cursor.fetchone():
                print(f"  [!] Email '{ADMIN['email']}' already exists. Aborting.")
                return

            # 4. Hash the password (same method Flask-Login / Werkzeug uses)
            password_hash = generate_password_hash(ADMIN['password'])
            now = datetime.utcnow()

            # 5. Insert the user
            sql = """
                INSERT INTO user
                    (username, email, password_hash, first_name, last_name,
                     is_active, role_id, created_at)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                ADMIN['username'],
                ADMIN['email'],
                password_hash,
                ADMIN['first_name'],
                ADMIN['last_name'],
                ADMIN['is_active'],
                role_id,
                now,
            ))

            user_id = cursor.lastrowid
            conn.commit()

            print(f"  [✓] Admin user created successfully!")
            print(f"      id       : {user_id}")
            print(f"      username : {ADMIN['username']}")
            print(f"      email    : {ADMIN['email']}")
            print(f"      password : {ADMIN['password']}")
            print(f"      role     : admin (id={role_id})\n")

    except pymysql.MySQLError as e:
        conn.rollback()
        print(f"  [✗] Database error: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    create_admin_user()