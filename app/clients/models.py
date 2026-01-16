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


# Modification du modèle Project - ajouter cette ligne dans la classe Project
# Après les colonnes existantes, ajouter:
client_id = db.Column(db.Integer, db.ForeignKey('client.id'))