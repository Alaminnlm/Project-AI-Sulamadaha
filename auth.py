"""
Authentication routes and logic
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, UserActivity
from datetime import datetime
from functools import wraps
import os
import requests
from urllib.parse import urlencode
import secrets
from dotenv import load_dotenv

# Load env vars
load_dotenv()

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Helper function to get Google OAuth config (load dynamically to ensure env vars are loaded)
def get_google_oauth_config():
    """Get Google OAuth configuration from environment"""
    return {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
    }

def get_client_ip():
    """Get client IP address"""
    if request.environ.get('HTTP_CF_CONNECTING_IP'):
        return request.environ.get('HTTP_CF_CONNECTING_IP')
    return request.remote_addr

def log_activity(user_id, action, endpoint='', method='', status_code=200, details=''):
    """Log user activity"""
    activity = UserActivity()
    activity.user_id = user_id
    activity.action = action
    activity.ip_address = get_client_ip()
    activity.user_agent = request.headers.get('User-Agent', '')
    activity.endpoint = endpoint or request.endpoint
    activity.method = method or request.method
    activity.status_code = status_code
    activity.details = details
    db.session.add(activity)
    db.session.commit()

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        full_name = data.get('full_name')
        
        # Validation
        if not username or not email or not password:
            flash('Semua kolom harus diisi', 'error')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Password tidak cocok', 'error')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('Password minimal 6 karakter', 'error')
            return redirect(url_for('auth.register'))
        
        # Check existing user
        if User.query.filter_by(username=username).first():
            flash('Username sudah terdaftar', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar', 'error')
            return redirect(url_for('auth.register'))
        
        # Create new user
        user = User()
        user.username = username
        user.email = email
        user.full_name = full_name
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'register', details=f'User {username} registered')
        
        flash('Registrasi berhasil! Silakan login', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with username/password"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            flash('Username dan password harus diisi', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Akun Anda telah dinonaktifkan', 'error')
                return redirect(url_for('auth.login'))
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Set session flag untuk menandai bahwa ini adalah user (bukan admin)
            session.permanent = True
            session['is_admin'] = False
            login_user(user, remember=True)
            log_activity(user.id, 'login', details='User logged in')
            
            flash(f'Selamat datang kembali, {user.full_name or user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Username atau password salah', 'error')
            log_activity(0, 'failed_login', details=f'Failed login attempt for {username}')
    
    return render_template('auth/login.html')

@auth_bp.route('/google-login')
def google_login():
    """Initiate Google OAuth login"""
    config = get_google_oauth_config()
    if not config['client_id']:
        flash('Google OAuth belum dikonfigurasi', 'error')
        return redirect(url_for('auth.login'))
    
    google_auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
    params = {
        'client_id': config['client_id'],
        'redirect_uri': config['redirect_uri'],
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline'
    }
    
    return redirect(f"{google_auth_url}?{urlencode(params)}")

@auth_bp.route('/callback')
def google_callback():
    """Handle Google OAuth callback"""
    # Check for user denial
    error = request.args.get('error')
    if error:
        flash(f'Google login dibatalkan: {error}', 'error')
        return redirect(url_for('auth.login'))
    
    config = get_google_oauth_config()
    if not config['client_id'] or not config['client_secret']:
        flash('Google OAuth belum dikonfigurasi', 'error')
        return redirect(url_for('auth.login'))
    
    code = request.args.get('code')
    if not code:
        flash('Kode otorisasi tidak ditemukan', 'error')
        return redirect(url_for('auth.login'))
    
    # Exchange code for token
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': code,
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'redirect_uri': config['redirect_uri'],
        'grant_type': 'authorization_code'
    }
    
    try:
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'error' in token_json:
            flash('Gagal mendapatkan token dari Google', 'error')
            return redirect(url_for('auth.login'))
        
        access_token = token_json.get('access_token')
        
        # Get user info
        user_info_url = 'https://openidconnect.googleapis.com/v1/userinfo'
        user_info_response = requests.get(
            user_info_url,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        user_info = user_info_response.json()
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        full_name = user_info.get('name')
        picture = user_info.get('picture')
        
        # Find or create user
        user = User.query.filter_by(google_id=google_id).first()
        
        if not user:
            # Check if email already exists with different auth method
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Create new user with Google auth
                username = email.split('@')[0]
                # Make username unique if exists
                base_username = username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User()
                user.username = username
                user.email = email
                user.full_name = full_name
                user.google_id = google_id
                user.profile_picture = picture
                db.session.add(user)
            else:
                # Link Google account to existing user
                user.google_id = google_id
                user.profile_picture = picture
        else:
            user.profile_picture = picture
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Set session flag untuk menandai bahwa ini adalah user (bukan admin)
        session.permanent = True
        session['is_admin'] = False
        login_user(user, remember=True)
        log_activity(user.id, 'google_login', details='User logged in with Google')
        
        flash(f'Selamat datang, {user.full_name or user.username}!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    log_activity(current_user.id, 'logout')
    session.pop('is_admin', None)  # Clear admin flag
    logout_user()
    flash('Anda telah logout', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    data = request.form
    
    current_user.full_name = data.get('full_name', current_user.full_name)
    
    password = data.get('password', '')
    if password:
        confirm_password = data.get('confirm_password', '')
        if password != confirm_password:
            return jsonify({'error': 'Password tidak cocok'}), 400
        if len(password.strip()) < 6:
            return jsonify({'error': 'Password minimal 6 karakter'}), 400
        current_user.set_password(password)
    
    db.session.commit()
    log_activity(current_user.id, 'profile_update')
    
    flash('Profil berhasil diperbarui', 'success')
    return redirect(url_for('auth.profile'))
