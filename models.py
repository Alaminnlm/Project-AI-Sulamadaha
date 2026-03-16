"""
Database models for user authentication and tracking
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for user authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    google_id = db.Column(db.String(120), unique=True)
    profile_picture = db.Column(db.String(500))
    full_name = db.Column(db.String(120))
    _is_active = db.Column('is_active', db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    activities = db.relationship('UserActivity', backref='user', lazy=True, cascade='all, delete-orphan')
    
    @property
    def is_active(self):
        """Check if user is active"""
        return self._is_active
    
    @is_active.setter
    def is_active(self, value):
        """Set is_active"""
        self._is_active = value
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Admin(UserMixin, db.Model):
    """Admin model for administrative access"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(120))
    role = db.Column(db.String(50), default='admin')  # admin, super_admin
    _is_active = db.Column('is_active', db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    @property
    def is_active(self):
        """Check if admin is active"""
        return self._is_active
    
    @is_active.setter
    def is_active(self, value):
        """Set is_active"""
        self._is_active = value
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Admin {self.username}>'

class UserActivity(db.Model):
    """Track user activity and traffic"""
    __tablename__ = 'user_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # login, logout, chat, etc
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    endpoint = db.Column(db.String(255))
    method = db.Column(db.String(10))  # GET, POST, etc
    status_code = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)  # Additional info as JSON string
    
    def __repr__(self):
        return f'<Activity {self.action} by user {self.user_id}>'

class ChatMessage(db.Model):
    """Store chat message history"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # user, assistant
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Message {self.id} from user {self.user_id}>'
