"""Script pour corriger les relations de base de données"""
from app import create_app, db
from app.models import StockItem, TaskStockItem
import sqlalchemy as sa

app = create_app()

with app.app_context():
    # Vérifier la structure actuelle
    inspector = sa.inspect(db.engine)
    
    print("Tables existantes:")
    for table_name in inspector.get_table_names():
        print(f"  - {table_name}")
    
    print("\nColonnes de task_stock_item:")
    for column in inspector.get_columns('task_stock_item'):
        print(f"  - {column['name']}: {column['type']}")
    
    # Vérifier si la colonne unit_type existe
    columns = [col['name'] for col in inspector.get_columns('task_stock_item')]
    
    if 'unit_type' not in columns:
        print("\nAjout de la colonne unit_type à task_stock_item...")
        try:
            db.engine.execute(
                "ALTER TABLE task_stock_item ADD COLUMN unit_type VARCHAR(32) DEFAULT 'piece'"
            )
            print("Colonne unit_type ajoutée avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'ajout de unit_type: {e}")
    
    if 'additional_quantity' not in columns:
        print("\nAjout de la colonne additional_quantity à task_stock_item...")
        try:
            db.engine.execute(
                "ALTER TABLE task_stock_item ADD COLUMN additional_quantity FLOAT DEFAULT 0.0"
            )
            print("Colonne additional_quantity ajoutée avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'ajout de additional_quantity: {e}")
    
    # Vérifier et mettre à jour les types de colonnes
    print("\nMise à jour des types de colonnes...")
    try:
        # Mettre à jour quantity et min_quantity dans stock_item
        db.engine.execute(
            "ALTER TABLE stock_item ALTER COLUMN quantity TYPE FLOAT USING quantity::float"
        )
        db.engine.execute(
            "ALTER TABLE stock_item ALTER COLUMN min_quantity TYPE FLOAT USING min_quantity::float"
        )
        
        # Mettre à jour les colonnes dans task_stock_item
        db.engine.execute(
            "ALTER TABLE task_stock_item ALTER COLUMN estimated_quantity TYPE FLOAT USING estimated_quantity::float"
        )
        db.engine.execute(
            "ALTER TABLE task_stock_item ALTER COLUMN actual_quantity_used TYPE FLOAT USING actual_quantity_used::float"
        )
        db.engine.execute(
            "ALTER TABLE task_stock_item ALTER COLUMN remaining_quantity TYPE FLOAT USING remaining_quantity::float"
        )
        
        print("Types de colonnes mis à jour avec succès.")
    except Exception as e:
        print(f"Erreur lors de la mise à jour des types: {e}")
    
    print("\nMigration terminée!")