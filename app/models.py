from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
import json
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

# Table de liaison pour les groupes et personnels
group_members = db.Table('group_members',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    db.Column('personnel_id', db.Integer, db.ForeignKey('personnel.id'), primary_key=True)
)

# Table de liaison pour les tâches et personnels
task_personnel = db.Table('task_personnel',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('personnel_id', db.Integer, db.ForeignKey('personnel.id'), primary_key=True)
)

# Table de liaison pour les tâches et groupes
task_groups = db.Table('task_groups',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)

class Role(db.Model):
    """Modèle pour les rôles d'utilisateurs"""
    __tablename__ = 'role'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    permissions = db.Column(db.Text)  # JSON string des permissions
    
    # Relations
    users = db.relationship('User', backref='role_ref', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = json.dumps({})
    
    def get_permissions(self):
        """Retourne les permissions comme dictionnaire"""
        try:
            return json.loads(self.permissions)
        except:
            return {}
    
    def set_permissions(self, permissions_dict):
        """Définit les permissions depuis un dictionnaire"""
        self.permissions = json.dumps(permissions_dict)
    
    def has_permission(self, module, action):
        """Vérifie si le rôle a une permission spécifique"""
        perms = self.get_permissions()
        return perms.get(module, {}).get(action, False)

class User(UserMixin, db.Model):
    """Modèle pour les utilisateurs"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)
    
    # Clés étrangères
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    
    # Relations
    role = db.relationship('Role', backref=db.backref('users_list', lazy='dynamic'))
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        """Set password using the property setter"""
        self.password_hash = generate_password_hash(password)
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """Verify the password against the hash"""
        return check_password_hash(self.password_hash, password)
    
    def check_password(self, password):
        """Alias for verify_password - for compatibility"""
        return self.verify_password(password)
    
    def get_reset_password_token(self, expires_in=3600):
        """
        Génère un token sécurisé pour réinitialiser le mot de passe
        expires_in: durée de validité du token en secondes (1 heure par défaut)
        """
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps({'reset_password': self.id}, salt='password-reset-salt')

    @staticmethod
    def verify_reset_password_token(token, expires_in=3600):
        """
        Vérifie et décode le token de réinitialisation
        Retourne l'utilisateur si le token est valide, None sinon
        """
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token, salt='password-reset-salt', max_age=expires_in)
            return User.query.get(data['reset_password'])
        except:
            return None
    
    def get_permissions(self):
        """Retourne les permissions de l'utilisateur"""
        if self.role:
            return self.role.get_permissions()
        return {}
    
    def has_permission(self, module, action):
        """Vérifie si l'utilisateur a une permission spécifique"""
        # L'admin a tous les droits
        if self.role and self.role.name == 'admin':
            return True
        return self.role and self.role.has_permission(module, action)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Supplier(db.Model):
    """Modèle pour les fournisseurs"""
    __tablename__ = 'supplier'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    contact_person = db.Column(db.String(128))
    email = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(64))
    country = db.Column(db.String(64))
    website = db.Column(db.String(128))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    stock_items = db.relationship('StockItem', backref='supplier', lazy='dynamic')
    
    def __repr__(self):
        return f'<Supplier {self.name}>'

class StockItem(db.Model):
    """Modèle pour les éléments du stock"""
    __tablename__ = 'stock_item'
    
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(64), unique=True, nullable=False, index=True)
    libelle = db.Column(db.String(255), nullable=False)
    item_type = db.Column(db.String(64), nullable=False)  # Type pour gérer les attributs dynamiques
    quantity = db.Column(db.Float, default=0.0)  # Changé de Integer à Float
    min_quantity = db.Column(db.Float, default=0.0)  # Changé de Integer à Float
    price = db.Column(db.Float, default=0.0)
    task_stock_items = db.relationship(
        'TaskStockItem',
        back_populates='stock_item',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    value = db.Column(db.Float, default=0.0)  # Calculé: price * quantity
    unit = db.Column(db.String(32), default='piece')  # Ajouté pour gérer l'unité
    location = db.Column(db.String(128))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Clés étrangères
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('stock_category.id'))
    
    # Relations
    attributes = db.relationship('StockAttribute', backref='stock_item', lazy='dynamic', cascade='all, delete-orphan')
    files = db.relationship('StockFile', backref='stock_item', lazy='dynamic', cascade='all, delete-orphan')
    task_stock_items = db.relationship('TaskStockItem', back_populates='stock_item', lazy='dynamic', cascade='all, delete-orphan')
    def calculate_value(self):
        """Calcule la valeur totale"""
        self.value = self.price * self.quantity
        return self.value
    
    def check_alert(self):
        """Vérifie si une alerte doit être générée"""
        return self.quantity <= self.min_quantity
    @property
    def used_in_tasks(self):
        return self.task_stock_items.count()

    
    def __repr__(self):
        return f'<StockItem {self.reference}: {self.libelle}>'

class StockAttribute(db.Model):
    """Modèle pour les attributs dynamiques des éléments du stock"""
    __tablename__ = 'stock_attribute'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    value = db.Column(db.String(255))
    data_type = db.Column(db.String(32), default='string')  # string, number, date, etc.
    
    # Clés étrangères
    stock_item_id = db.Column(db.Integer, db.ForeignKey('stock_item.id', ondelete='CASCADE'))
    
    def __repr__(self):
        return f'<StockAttribute {self.name}: {self.value}>'

class StockCategory(db.Model):
    """Modèle pour les catégories de stock"""
    __tablename__ = 'stock_category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    attributes_template = db.Column(db.Text)  # JSON template pour les attributs
    
    # Relations
    items = db.relationship('StockItem', backref='category', lazy='dynamic')
    
    def get_attributes_template(self):
        """Retourne le template des attributs"""
        try:
            return json.loads(self.attributes_template)
        except:
            return []
    
    def __repr__(self):
        return f'<StockCategory {self.name}>'

class StockFile(db.Model):
    """Modèle pour les fichiers attachés aux éléments du stock"""
    __tablename__ = 'stock_file'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10))
    description = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clés étrangères
    stock_item_id = db.Column(db.Integer, db.ForeignKey('stock_item.id', ondelete='CASCADE'))
    
    def __repr__(self):
        return f'<StockFile {self.filename}>'

class StockMovement(db.Model):
    """Modèle pour les mouvements de stock (entrées/sorties)"""
    __tablename__ = 'stock_movement'
    
    id = db.Column(db.Integer, primary_key=True)
    movement_type = db.Column(db.String(20), nullable=False)  # 'purchase', 'sale', 'transfer', 'adjustment', 'waste', 'return'
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float)  # Prix unitaire au moment du mouvement
    total_price = db.Column(db.Float)  # Prix total (quantité * prix unitaire)
    reference = db.Column(db.String(64))  # N° facture, bon de commande, etc.
    notes = db.Column(db.Text)
    movement_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Clés étrangères
    stock_item_id = db.Column(db.Integer, db.ForeignKey('stock_item.id', ondelete='CASCADE'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    
    # Relations
    stock_item = db.relationship('StockItem', backref='movements')
    supplier = db.relationship('Supplier', backref='stock_movements')
    task = db.relationship('Task', backref='stock_movements')
    project = db.relationship('Project', backref='stock_movements')
    user = db.relationship('User', backref='recorded_movements')
    
    def __repr__(self):
        return f'<StockMovement {self.movement_type} - {self.quantity}>'


class PurchaseOrder(db.Model):
    """Modèle pour les commandes d'achat"""
    __tablename__ = 'purchase_order'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, ordered, delivered, cancelled
    order_date = db.Column(db.Date, nullable=False)
    delivery_date = db.Column(db.Date)
    total_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clés étrangères
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relations
    supplier = db.relationship('Supplier', backref='purchase_orders')
    creator = db.relationship('User', backref='created_orders')
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PurchaseOrder {self.order_number}>'


class PurchaseOrderItem(db.Model):
    """Modèle pour les éléments d'une commande d'achat"""
    __tablename__ = 'purchase_order_item'
    
    id = db.Column(db.Integer, primary_key=True)
    quantity_ordered = db.Column(db.Float, nullable=False)
    quantity_received = db.Column(db.Float, default=0.0)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float)
    notes = db.Column(db.Text)
    
    # Clés étrangères
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id', ondelete='CASCADE'))
    stock_item_id = db.Column(db.Integer, db.ForeignKey('stock_item.id'))
    
    # Relations
    stock_item = db.relationship('StockItem', backref='purchase_orders')
    
    def calculate_total(self):
        """Calcule le prix total"""
        self.total_price = self.quantity_ordered * self.unit_price
        return self.total_price
    
    def __repr__(self):
        return f'<PurchaseOrderItem {self.quantity_ordered}>'



class Personnel(db.Model):
    """Modèle pour le personnel"""
    __tablename__ = 'personnel'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(64), unique=True, nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    department = db.Column(db.String(64))
    position = db.Column(db.String(64))
    hire_date = db.Column(db.Date)
    address = db.Column(db.Text)
    city = db.Column(db.String(64))
    country = db.Column(db.String(64))
    emergency_contact = db.Column(db.String(128))
    emergency_phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    groups = db.relationship('Group', secondary=group_members, back_populates='members')
    tasks = db.relationship('Task', secondary=task_personnel, back_populates='assigned_personnel')
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Personnel {self.employee_id}: {self.get_full_name()}>'

class Group(db.Model):
    """Modèle pour les groupes de personnel"""
    __tablename__ = 'group'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    members = db.relationship('Personnel', secondary=group_members, back_populates='groups')
    tasks = db.relationship('Task', secondary=task_groups, back_populates='assigned_groups')
    
    def __repr__(self):
        return f'<Group {self.name}>'


class Client(db.Model):
    """Modèle pour les clients"""
    __tablename__ = 'client'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    company = db.Column(db.String(128))
    contact_person = db.Column(db.String(128))
    email = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(64))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(64))
    website = db.Column(db.String(128))
    siret = db.Column(db.String(64))  # Pour les entreprises françaises
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    projects = db.relationship('Project', backref='client', lazy='dynamic')
    
    def __repr__(self):
        return f'<Client {self.name}>'
    
    def get_active_projects_count(self):
        """Retourne le nombre de projets actifs"""
        return self.projects.filter(
            Project.status.in_(['planning', 'in_progress'])
        ).count()
    
    def get_total_budget(self):
        """Retourne le budget total de tous les projets"""
        return sum(p.estimated_budget for p in self.projects.all())

class Project(db.Model):
    """Modèle pour les projets"""
    __tablename__ = 'project'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    actual_end_date = db.Column(db.Date)
    estimated_budget = db.Column(db.Float, default=0.0)
    budget_reel = db.Column(db.Float, default=0.0, nullable=True)
    prix_vente = db.Column(db.Float, default=0.0, nullable=True)
    marge = db.Column(db.Float, default=0.0, nullable=True)
    actual_cost = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32), default='planning')  # planning, in_progress, completed, cancelled
    priority = db.Column(db.String(32), default='medium')  # low, medium, high
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    
    # Relations
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    files = db.relationship('ProjectFile', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def calculate_actual_cost(self):
        """Calcule le coût actuel du projet"""
        total = 0
        for task in self.tasks:
            total += task.calculate_cost()
        self.actual_cost = total
        return total
    
    def get_progress(self):
        """Calcule la progression du projet"""
        tasks = self.tasks.all()
        if not tasks:
            return 0
        completed = sum(1 for task in tasks if task.status == 'completed')
        return (completed / len(tasks)) * 100
    
    def __repr__(self):
        return f'<Project {self.name}>'

class TaskType(db.Model):
    """Modèle pour les types de tâches"""
    __tablename__ = 'task_type'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    default_duration = db.Column(db.Integer)  # en jours
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    tasks = db.relationship('Task', backref='task_type_ref', lazy='dynamic')
    
    def __repr__(self):
        return f'<TaskType {self.name}>'

class Task(db.Model):
    """Modèle pour les tâches"""
    __tablename__ = 'task'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    actual_end_date = db.Column(db.Date)
    status = db.Column(db.String(32), default='pending')
    priority = db.Column(db.String(32), default='medium')
    use_stock = db.Column(db.Boolean, default=True)
    justification = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Clés étrangères
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'))
    task_type_id = db.Column(db.Integer, db.ForeignKey('task_type.id'))
    
    # Relations
    assigned_personnel = db.relationship('Personnel', secondary=task_personnel, back_populates='tasks')
    assigned_groups = db.relationship('Group', secondary=task_groups, back_populates='tasks')
    stock_items = db.relationship('TaskStockItem', back_populates='task', lazy='dynamic', cascade='all, delete-orphan')
    additional_costs = db.relationship('AdditionalCost', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    def calculate_cost(self):
        """Calcule le coût total de la tâche"""
        total = 0
        
        # Coût des matériaux
        for item in self.stock_items:
            total += item.estimated_cost or 0
        
        # Coûts supplémentaires
        for cost in self.additional_costs:
            total += cost.amount
        
        return total
    def __init__(self, **kwargs):
        super(Task, self).__init__(**kwargs)
        # Validation des dates
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValueError("La date de fin doit être après la date de début")
    
    def update_dates(self, start_date, end_date):
        """Met à jour les dates avec validation"""
        if end_date < start_date:
            raise ValueError("La date de fin doit être après la date de début")
        self.start_date = start_date
        self.end_date = end_date
        
    def check_stock_availability(self):
        """Vérifie la disponibilité des matériaux dans le stock"""
        issues = []
        for task_item in self.stock_items:
            if task_item.stock_item and task_item.estimated_quantity > task_item.stock_item.quantity:
                issues.append({
                    'item': task_item.stock_item.libelle,
                    'required': task_item.estimated_quantity,
                    'available': task_item.stock_item.quantity,
                    'reference': task_item.stock_item.reference
                })
        return issues
    def calculate_material_shortage(self):
        """Calcule le manque total de matériaux"""
        shortage = 0
        for item in self.stock_items:
            if item.stock_item:
                item_shortage = max(0, item.estimated_quantity - item.stock_item.quantity)
                shortage += item_shortage
        return shortage
    
    def __repr__(self):
        return f'<Task {self.name}>'

class TaskStockItem(db.Model):
    """Modèle pour les éléments de stock utilisés dans une tâche"""
    __tablename__ = 'task_stock_item'
    
    id = db.Column(db.Integer, primary_key=True)
    estimated_quantity = db.Column(db.Float, default=0.0)
    actual_quantity_used = db.Column(db.Float)
    remaining_quantity = db.Column(db.Float)  # Quantité retournée au stock
    additional_quantity = db.Column(db.Float, default=0.0)  # Nouveau: quantité supplémentaire à ajouter
    estimated_cost = db.Column(db.Float)
    return_to_stock = db.Column(db.Boolean, default=False)
    justification_shortage = db.Column(db.Text)
    notes = db.Column(db.Text)
    unit_type = db.Column(db.String(32), default='piece')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Clés étrangères
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'))
    stock_item_id = db.Column(db.Integer, db.ForeignKey('stock_item.id'))
    
    # Relations
    # CORRECTION : Utilisez back_populates au lieu de backref
    stock_item = db.relationship('StockItem', back_populates='task_stock_items', foreign_keys=[stock_item_id])
    task = db.relationship('Task', back_populates='stock_items', foreign_keys=[task_id])
    
    # Méthodes utilitaires
    def is_quantity_sufficient(self):
        """Vérifie si la quantité est suffisante dans le stock"""
        if self.stock_item:
            return self.estimated_quantity <= self.stock_item.quantity
        return False
    
    def get_shortage_quantity(self):
        """Retourne la quantité manquante"""
        if self.stock_item:
            shortage = self.estimated_quantity - self.stock_item.quantity
            return max(0, shortage)
        return self.estimated_quantity
    
    def get_total_required_quantity(self):
        """Retourne la quantité totale requise (estimée + supplémentaire)"""
        return self.estimated_quantity + (self.additional_quantity or 0)
    
    def __repr__(self):
        return f'<TaskStockItem {self.id} - {self.estimated_quantity}>'

class AdditionalCost(db.Model):
    """Modèle pour les frais supplémentaires d'une tâche"""
    __tablename__ = 'additional_cost'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    justification = db.Column(db.Text)
    date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clés étrangères
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'))
    
    def __repr__(self):
        return f'<AdditionalCost {self.name}: {self.amount}>'

class ProjectFile(db.Model):
    """Modèle pour les fichiers de projets"""
    __tablename__ = 'project_file'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10))
    description = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clés étrangères
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'))
    
    def __repr__(self):
        return f'<ProjectFile {self.filename}>'

class Notification(db.Model):
    """Modèle pour les notifications"""
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(32))  # stock_alert, task_assignment, etc.
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clés étrangères
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    stock_item_id = db.Column(db.Integer, db.ForeignKey('stock_item.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    
    # Relations
    stock_item = db.relationship('StockItem', backref='notifications')
    task = db.relationship('Task', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.title}>'

class DashboardChart(db.Model):
    """Modèle pour les configurations des graphiques du dashboard"""
    __tablename__ = 'dashboard_chart'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    chart_type = db.Column(db.String(32), nullable=False)  # bar, line, pie, etc.
    data_source = db.Column(db.String(64), nullable=False)  # stock, projects, tasks, etc.
    config = db.Column(db.Text)  # JSON configuration
    position = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clés étrangères
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    
    # Relations
    user = db.relationship('User', backref='dashboard_charts')
    
    def get_config(self):
        """Retourne la configuration comme dictionnaire"""
        try:
            return json.loads(self.config)
        except:
            return {}
    
    def set_config(self, config_dict):
        """Définit la configuration depuis un dictionnaire"""
        self.config = json.dumps(config_dict)
    
    def __repr__(self):
        return f'<DashboardChart {self.title}>'

class InterventionType(db.Model):
    """Modèle pour les types d'interventions"""
    __tablename__ = 'intervention_type'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relations
    interventions = db.relationship('Intervention', backref='type', lazy='dynamic')
    
    def __repr__(self):
        return f'<InterventionType {self.name}>'

class InterventionClass(db.Model):
    """Modèle pour les classes d'interventions"""
    __tablename__ = 'intervention_class'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relations - CHANGÉ: backref='intervention_class' au lieu de 'class'
    interventions = db.relationship('Intervention', backref='intervention_class', lazy='dynamic')
    
    def __repr__(self):
        return f'<InterventionClass {self.name}>'

class InterventionEntity(db.Model):
    """Modèle pour les entités d'interventions"""
    __tablename__ = 'intervention_entity'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relations
    interventions = db.relationship('Intervention', backref='entity', lazy='dynamic')
    
    def __repr__(self):
        return f'<InterventionEntity {self.name}>'

# Table de liaison pour les interventions et le personnel
intervention_personnel = db.Table('intervention_personnel',
    db.Column('intervention_id', db.Integer, db.ForeignKey('intervention.id'), primary_key=True),
    db.Column('personnel_id', db.Integer, db.ForeignKey('personnel.id'), primary_key=True)
)

class Intervention(db.Model):
    """Modèle pour les interventions"""
    __tablename__ = 'intervention'
    
    id = db.Column(db.Integer, primary_key=True)
    intervention_number = db.Column(db.String(50), nullable=False, unique=True)
    client_name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))

    
    # Clés étrangères
    type_id = db.Column(db.Integer, db.ForeignKey('intervention_type.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('intervention_class.id'))  # Gardé comme nom de colonne
    entity_id = db.Column(db.Integer, db.ForeignKey('intervention_entity.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    
    # Dates
    client_contact_date = db.Column(db.Date, nullable=False)
    intervention_date = db.Column(db.Date, nullable=False)
    planned_end_date = db.Column(db.Date, nullable=False)
    actual_end_date = db.Column(db.Date)
    
    # Statut
    status = db.Column(db.Enum('planned', 'in_progress', 'completed', 'cancelled'), 
                      default='planned', nullable=False)
    
    # Descriptions
    anomaly_description = db.Column(db.Text)
    tasks_description = db.Column(db.Text)
    
    # Liens
    linked_to_project = db.Column(db.Boolean, default=False)
    justification_delay = db.Column(db.Text)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relations
    personnel = db.relationship('Personnel', secondary=intervention_personnel, 
                               backref='interventions', lazy='dynamic')
    stock_items = db.relationship('InterventionStock', backref='intervention', 
                                 lazy='dynamic', cascade='all, delete-orphan')
    costs = db.relationship('InterventionCost', backref='intervention', 
                           lazy='dynamic', cascade='all, delete-orphan')
    files = db.relationship('InterventionFile', backref='intervention', 
                           lazy='dynamic', cascade='all, delete-orphan')
    project = db.relationship('Project', backref='interventions')
    equipment = db.relationship('Equipment', backref='interventions')
    
    # NOTE: Pas besoin de déclarer intervention_class ici car c'est déjà fait dans InterventionClass
    
    def __repr__(self):
        return f'<Intervention {self.intervention_number}>'
    
    def get_status_label(self):
        """Retourne le libellé du statut"""
        labels = {
            'planned': 'Planifiée',
            'in_progress': 'En cours',
            'completed': 'Terminée',
            'cancelled': 'Annulée'
        }
        return labels.get(self.status, self.status)
    
    def calculate_total_cost(self):
        """Calcule le coût total de l'intervention"""
        total = 0
        
        # Coût des articles de stock
        for item in self.stock_items:
            if item.stock_item and item.actual_quantity:
                total += item.actual_quantity * (item.stock_item.price or 0)
        
        # Coûts supplémentaires
        for cost in self.costs:
            total += cost.amount
        
        return total

class InterventionStock(db.Model):
    """Modèle pour les articles de stock utilisés dans une intervention"""
    __tablename__ = 'intervention_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    intervention_id = db.Column(db.Integer, db.ForeignKey('intervention.id', ondelete='CASCADE'))
    stock_item_id = db.Column(db.Integer, db.ForeignKey('stock_item.id'))
    
    # Quantités
    estimated_quantity = db.Column(db.Float, default=0)
    actual_quantity = db.Column(db.Float)
    remaining_quantity = db.Column(db.Float, default=0)
    additional_quantity = db.Column(db.Float, default=0)
    
    # Validation
    justification = db.Column(db.Text)
    validated = db.Column(db.Boolean, default=False)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    stock_item = db.relationship('StockItem', backref='intervention_usage')
    
    def __repr__(self):
        return f'<InterventionStock {self.id}>'
    
    def get_quantity_difference(self):
        """Calcule la différence entre la quantité prévue et réelle"""
        if self.actual_quantity is not None:
            return self.actual_quantity - self.estimated_quantity
        return 0

class InterventionCost(db.Model):
    """Modèle pour les coûts supplémentaires d'une intervention"""
    __tablename__ = 'intervention_cost'
    
    id = db.Column(db.Integer, primary_key=True)
    intervention_id = db.Column(db.Integer, db.ForeignKey('intervention.id', ondelete='CASCADE'))
    cost_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<InterventionCost {self.cost_name}: {self.amount}>'

class InterventionFile(db.Model):
    """Modèle pour les fichiers attachés aux interventions"""
    __tablename__ = 'intervention_file'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10))
    file_name = db.Column(db.String(255))  # Nom donné par l'utilisateur
    description = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clés étrangères
    intervention_id = db.Column(db.Integer, db.ForeignKey('intervention.id', ondelete='CASCADE'))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relations
    uploader = db.relationship('User', backref='intervention_files')
    
    def __repr__(self):
        return f'<InterventionFile {self.file_name}>'

# Tables d'association
equipment_stock_items = db.Table('equipment_stock_items',
    db.Column('equipment_id', db.Integer, db.ForeignKey('equipment.id'), primary_key=True),
    db.Column('stock_item_id', db.Integer, db.ForeignKey('stock_item.id'), primary_key=True),
    db.Column('quantity_used', db.Float, default=1.0),
    db.Column('notes', db.Text),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)

class EquipmentCategory(db.Model):
    """Catégories d'équipements"""
    __tablename__ = 'equipment_category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    
    def __repr__(self):
        return f'<EquipmentCategory {self.name}>'

class Equipment(db.Model):
    """Modèle pour les équipements"""
    __tablename__ = 'equipment'
    
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    serial_number = db.Column(db.String(128), unique=True)
    model = db.Column(db.String(128))
    brand = db.Column(db.String(128))
    
    # Statut et localisation
    status = db.Column(db.String(32), default='available')  # available, in_use, maintenance, out_of_service
    location = db.Column(db.String(128))
    department = db.Column(db.String(64))
    responsible_person = db.Column(db.String(128))
    
    # Dates importantes
    purchase_date = db.Column(db.Date)
    warranty_until = db.Column(db.Date)
    last_maintenance = db.Column(db.Date)
    next_maintenance = db.Column(db.Date)
    
    # Coûts
    purchase_price = db.Column(db.Float, default=0.0)
    current_value = db.Column(db.Float, default=0.0)
    
    # Informations supplémentaires
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Clés étrangères
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('equipment_category.id'))
    
    # Relations
    supplier = db.relationship('Supplier', backref='equipments')
    category = db.relationship('EquipmentCategory', backref='equipments')
    
    # Relation many-to-many avec StockItem
    stock_items = db.relationship('StockItem', 
                                 secondary='equipment_stock_items',
                                 backref=db.backref('equipments', lazy='dynamic'),
                                 lazy='dynamic')
    
    # Autres relations
    files = db.relationship('EquipmentFile', backref='equipment', lazy='dynamic', cascade='all, delete-orphan')
    maintenance_logs = db.relationship('EquipmentMaintenance', backref='equipment', lazy='dynamic', cascade='all, delete-orphan')
    
        
    def get_attached_stock_value(self):
        """Calcule la valeur totale des éléments de stock attachés"""
        total = 0
        for stock_item in self.stock_items:
            # Récupérer la quantité utilisée pour cet équipement
            association = db.session.execute(
                db.select(equipment_stock_items).filter_by(
                    equipment_id=self.id,
                    stock_item_id=stock_item.id
                )
            ).first()
            if association:
                quantity_used = association.quantity_used
                total += stock_item.price * quantity_used
        return total
    
    def get_total_value(self):
        """Calcule la valeur totale (équipement + stock attaché)"""
        return (self.current_value or 0) + self.get_attached_stock_value()
    
    def __repr__(self):
        return f'<Equipment {self.reference}: {self.name}>'
class EquipmentFile(db.Model):
    """Fichiers attachés aux équipements"""
    __tablename__ = 'equipment_file'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10))
    description = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clés étrangères
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='CASCADE'))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relations
    uploader = db.relationship('User', backref='equipment_files')
    
    def __repr__(self):
        return f'<EquipmentFile {self.filename}>'

class EquipmentMaintenance(db.Model):
    """Historique de maintenance des équipements"""
    __tablename__ = 'equipment_maintenance'
    
    id = db.Column(db.Integer, primary_key=True)
    maintenance_type = db.Column(db.String(64), nullable=False)  # preventive, corrective, calibration
    maintenance_date = db.Column(db.Date, nullable=False)
    next_maintenance_date = db.Column(db.Date)
    performed_by = db.Column(db.String(128))
    cost = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clés étrangères
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='CASCADE'))
    performed_by_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relations
    user = db.relationship('User', backref='maintenance_activities')
    
    def __repr__(self):
        return f'<EquipmentMaintenance {self.maintenance_type} - {self.maintenance_date}>'




class TaskExternalRef(db.Model):
    """
    Équipements / pièces utilisés dans une tâche qui n'existent PAS dans
    la table stock_item.  Seule la référence est obligatoire.
    """
    __tablename__ = 'task_external_ref'

    id                = db.Column(db.Integer, primary_key=True)
    task_id           = db.Column(db.Integer,
                                  db.ForeignKey('task.id', ondelete='CASCADE'),
                                  nullable=False)

    # Identification
    reference         = db.Column(db.String(128), nullable=False)
    item_type         = db.Column(
                            db.Enum('equipement', 'piece'),
                            nullable=False,
                            default='piece'
                        )
    description       = db.Column(db.String(255))   # libellé court, optionnel

    # Quantités
    quantity_used     = db.Column(db.Float)                # réellement utilisée

    # Métadonnées
    notes             = db.Column(db.Text)
    created_by        = db.Column(db.Integer,
                                  db.ForeignKey('user.id', ondelete='SET NULL'))
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at        = db.Column(db.DateTime, default=datetime.utcnow,
                                  onupdate=datetime.utcnow)

    # Relations
    task    = db.relationship('Task', backref=db.backref(
                  'external_refs', lazy='dynamic', cascade='all, delete-orphan'
              ))
    creator = db.relationship('User', backref='task_external_refs_created')

    TYPE_LABELS = {
        'equipement': 'Équipement',
        'piece':      'Pièce détachée',
    }

    def get_type_label(self):
        return self.TYPE_LABELS.get(self.item_type, self.item_type)

    def __repr__(self):
        return f'<TaskExternalRef {self.reference} ({self.item_type}) task={self.task_id}>'

