"""
Admin routes for monitoring and management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Admin, UserActivity, ChatMessage
from datetime import datetime, timedelta
from functools import wraps
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Silakan login terlebih dahulu', 'error')
            return redirect(url_for('admin.login'))
        
        # Check if current_user is Admin instance
        if not isinstance(current_user, Admin):
            flash('Anda tidak memiliki akses ke halaman ini', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
    # Redirect if already logged in as admin
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            flash('Username dan password harus diisi', 'error')
            return redirect(url_for('admin.login'))
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            if not admin.is_active:
                flash('Akun admin Anda telah dinonaktifkan', 'error')
                return redirect(url_for('admin.login'))
            
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            # Set session flag untuk menandai bahwa ini adalah admin
            session.permanent = True
            session['is_admin'] = True
            login_user(admin, remember=True)
            flash(f'Selamat datang, {admin.full_name or admin.username}!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Username atau password salah', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    """Admin logout"""
    session.pop('is_admin', None)  # Clear admin flag
    logout_user()
    flash('Anda telah logout dari admin panel', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_admin():
    """Create new admin (Only accessible by existing admins)"""
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        full_name = data.get('full_name')
        role = data.get('role', 'admin')

        if not username or not email or not password:
            flash('Username, email, dan password wajib diisi', 'error')
            return redirect(url_for('admin.create_admin'))

        if password != confirm_password:
            flash('Password tidak cocok', 'error')
            return redirect(url_for('admin.create_admin'))

        # Check existing
        if Admin.query.filter_by(username=username).first() or User.query.filter_by(username=username).first():
            flash('Username sudah digunakan', 'error')
            return redirect(url_for('admin.create_admin'))

        if Admin.query.filter_by(email=email).first() or User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar', 'error')
            return redirect(url_for('admin.create_admin'))

        new_admin = Admin(
            username=username,
            email=email,
            full_name=full_name,
            role=role
        )
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()

        flash(f'Admin baru {username} berhasil dibuat', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/create_admin.html')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_users = User.query.count()
    
    # Active users = users who logged in within last 30 minutes
    thirty_min_ago = datetime.utcnow() - timedelta(minutes=30)
    active_user_ids = db.session.query(UserActivity.user_id.distinct()).filter(
        UserActivity.action.in_(['login', 'google_login']),
        UserActivity.timestamp >= thirty_min_ago
    ).subquery()
    active_users = db.session.query(db.func.count()).select_from(active_user_ids).scalar() or 0
    
    # Get logins in last 7 days (both regular and Google OAuth)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_logins = UserActivity.query.filter(
        UserActivity.action.in_(['login', 'google_login']),
        UserActivity.timestamp >= seven_days_ago
    ).count()
    
    # Get recent activities
    recent_activities = UserActivity.query.order_by(
        UserActivity.timestamp.desc()
    ).limit(50).all()
    
    # Get total messages
    total_messages = ChatMessage.query.count()
    
    # Get traffic last 7 days
    traffic_data = db.session.query(
        db.func.date(UserActivity.timestamp).label('date'),
        db.func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.timestamp >= seven_days_ago
    ).group_by(
        db.func.date(UserActivity.timestamp)
    ).order_by(db.func.date(UserActivity.timestamp)).all()
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'recent_logins': recent_logins,
        'total_messages': total_messages,
        'traffic_data': traffic_data
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_activities=recent_activities)

@admin_bp.route('/users')
@admin_required
def users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.full_name.ilike(f'%{search}%')
            )
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, 
        per_page=20
    )
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:user_id>/details')
@admin_required
def user_details(user_id):
    """View user details and activities"""
    user = User.query.get_or_404(user_id)
    
    activities = UserActivity.query.filter_by(user_id=user_id).order_by(
        UserActivity.timestamp.desc()
    ).limit(100).all()
    
    messages = ChatMessage.query.filter_by(user_id=user_id).order_by(
        ChatMessage.timestamp.desc()
    ).limit(50).all()
    
    return render_template('admin/user_details.html', 
                         user=user, 
                         activities=activities, 
                         messages=messages)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'diaktifkan' if user.is_active else 'dinonaktifkan'
    flash(f'User {user.username} telah {status}', 'success')
    return redirect(url_for('admin.user_details', user_id=user_id))

@admin_bp.route('/activity')
@admin_required
def activity():
    """View all user activities"""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    user_filter = request.args.get('user_id', '')
    
    query = UserActivity.query
    
    if action_filter:
        query = query.filter_by(action=action_filter)
    
    if user_filter:
        query = query.filter_by(user_id=user_filter)
    
    activities = query.order_by(
        UserActivity.timestamp.desc()
    ).paginate(page=page, per_page=50)
    
    # Get unique actions for filter
    actions = db.session.query(UserActivity.action.distinct()).all()
    actions = [a[0] for a in actions]
    
    return render_template('admin/activity.html', 
                         activities=activities,
                         actions=actions,
                         selected_action=action_filter,
                         selected_user=user_filter)

@admin_bp.route('/traffic-chart')
@admin_required
def traffic_chart():
    """Get traffic data for chart"""
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    traffic_data = db.session.query(
        UserActivity.timestamp.cast(db.Date).label('date'),
        db.func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.timestamp >= since
    ).group_by(
        UserActivity.timestamp.cast(db.Date)
    ).order_by('date').all()
    
    data = {
        'labels': [str(t[0]) for t in traffic_data],
        'data': [t[1] for t in traffic_data]
    }
    
    return jsonify(data)

@admin_bp.route('/reports')
@admin_required
def reports():
    """View reports and analytics"""
    # User statistics
    total_users = User.query.count()
    new_users_today = User.query.filter(
        User.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    new_users_week = User.query.filter(
        User.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    # Activity statistics - count both regular login and google_login
    login_actions = ['login', 'google_login']
    today_logins = UserActivity.query.filter(
        UserActivity.action.in_(login_actions),
        UserActivity.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    week_logins = UserActivity.query.filter(
        UserActivity.action.in_(login_actions),
        UserActivity.timestamp >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    # Chat statistics
    total_messages = ChatMessage.query.count()
    today_messages = ChatMessage.query.filter(
        ChatMessage.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    reports_data = {
        'total_users': total_users,
        'new_users_today': new_users_today,
        'new_users_week': new_users_week,
        'today_logins': today_logins,
        'week_logins': week_logins,
        'total_messages': total_messages,
        'today_messages': today_messages
    }
    
    return render_template('admin/reports.html', reports=reports_data)

@admin_bp.route('/settings')
@admin_required
def settings():
    """Admin settings"""
    admin = Admin.query.get(current_user.id)
    return render_template('admin/settings.html', admin=admin)

@admin_bp.route('/settings/update', methods=['POST'])
@admin_required
def update_settings():
    """Update admin settings"""
    admin = Admin.query.get(current_user.id)
    if not admin:
        flash('Admin tidak ditemukan', 'error')
        return redirect(url_for('admin.dashboard'))
    data = request.form
    
    admin.full_name = data.get('full_name', admin.full_name)
    
    password = data.get('password', '')
    if password:
        confirm_password = data.get('confirm_password', '')
        if password != confirm_password:
            return jsonify({'error': 'Password tidak cocok'}), 400
        if len(password.strip()) < 6:
            return jsonify({'error': 'Password minimal 6 karakter'}), 400
        if admin:
            admin.set_password(password)
    
    db.session.commit()
    flash('Pengaturan berhasil diperbarui', 'success')
    return redirect(url_for('admin.settings'))

@admin_bp.route('/admins')
@admin_required
def manage_admins():
    """List and manage all admin accounts"""
    admins = Admin.query.order_by(Admin.created_at.desc()).all()
    return render_template('admin/manage_admins.html', admins=admins)

@admin_bp.route('/admins/<int:admin_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_admin_status(admin_id):
    """Toggle admin active status"""
    if admin_id == current_user.id:
        flash('Anda tidak dapat menonaktifkan akun Anda sendiri', 'error')
        return redirect(url_for('admin.manage_admins'))
    admin = Admin.query.get_or_404(admin_id)
    admin.is_active = not admin.is_active
    db.session.commit()
    status = 'diaktifkan' if admin.is_active else 'dinonaktifkan'
    flash(f'Admin {admin.username} telah {status}', 'success')
    return redirect(url_for('admin.manage_admins'))
