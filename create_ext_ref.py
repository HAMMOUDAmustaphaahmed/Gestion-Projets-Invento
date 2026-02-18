"""
create_task_external_ref_table.py
===================================
Crée la table `task_external_ref` dans la base Invento.
Lance ce script UNE SEULE FOIS avant de déployer la fonctionnalité.

    pip install pymysql
    python create_task_external_ref_table.py
"""

import pymysql, sys

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

SQL = """
CREATE TABLE IF NOT EXISTS task_external_ref (
    id           INT           NOT NULL AUTO_INCREMENT,
    task_id      INT           NOT NULL,

    -- Identification de la pièce / équipement
    reference    VARCHAR(128)  NOT NULL   COMMENT 'Référence libre saisie par l utilisateur',
    item_type    ENUM('equipement','piece') NOT NULL DEFAULT 'piece',
    description  VARCHAR(255)             COMMENT 'Libellé court optionnel',

    -- Quantités
    quantity          DECIMAL(10,2) DEFAULT 1.00  COMMENT 'Quantité estimée nécessaire',
    quantity_used     DECIMAL(10,2)               COMMENT 'Quantité réellement utilisée',
    quantity_returned DECIMAL(10,2)               COMMENT 'Quantité retournée / non utilisée',

    -- Suivi
    notes        TEXT,
    created_by   INT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX idx_ter_task      (task_id),
    INDEX idx_ter_reference (reference),
    INDEX idx_ter_type      (item_type),

    CONSTRAINT fk_ter_task FOREIGN KEY (task_id)
        REFERENCES task (id) ON DELETE CASCADE,
    CONSTRAINT fk_ter_user FOREIGN KEY (created_by)
        REFERENCES `user` (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

def main():
    print("\n=== Création de task_external_ref ===\n")
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("  [✓] Connecté")
    except pymysql.MySQLError as e:
        print(f"  [✗] {e}"); sys.exit(1)

    with conn:
        with conn.cursor() as cur:
            cur.execute(SQL)
            conn.commit()
            print("  [✓] Table 'task_external_ref' créée (ou déjà existante)")
            print("""
  Colonnes :
    id                PK auto
    task_id           FK → task.id  CASCADE DELETE
    reference         VARCHAR(128)  NOT NULL
    item_type         ENUM  'equipement' | 'piece'
    description       VARCHAR(255)  optionnel
    quantity          DECIMAL  (estimée, défaut 1)
    quantity_used     DECIMAL  (réelle)
    quantity_returned DECIMAL  (retournée)
    notes             TEXT
    created_by        FK → user.id
    created_at / updated_at  auto timestamps
""")
    print("  Terminé.\n")

if __name__ == '__main__':
    main()