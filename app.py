import os
import sys
from pathlib import Path

# Load environment variables FIRST
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Now import Flask and extensions
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
import google.generativeai as genai
from datetime import datetime

# Import models and blueprints
try:
    from models import db, User, Admin, UserActivity, ChatMessage
    from auth import auth_bp
    from admin import admin_bp
except ImportError as e:
    print(f"Import Error: {e}", file=sys.stderr)
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-2024-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{Path(__file__).parent}/chatbot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Initialize Database
db.init_app(app)

# Initialize Login Manager (Single manager for both entities)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # type: ignore
login_manager.login_message = 'Silakan login terlebih dahulu'

# Initialize Gemini LLM with API key
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)  # type: ignore
    model = genai.GenerativeModel("gemini-2.5-flash")  # type: ignore

@login_manager.user_loader
def load_user(user_id):
    """Unified user loader for both User and Admin"""
    from flask import session
    # Check session to determine if this is an admin or user
    if session.get('is_admin') is True:
        return Admin.query.get(int(user_id))
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

# Create database tables
with app.app_context():
    db.create_all()

def log_chat_activity(user_id, message, response):
    """Log chat activity"""
    activity = UserActivity()
    activity.user_id = user_id
    activity.action = 'chat'
    activity.endpoint = 'api/chat'
    activity.method = 'POST'
    activity.status_code = 200
    activity.details = f'Message: {message[:100]}...'
    db.session.add(activity)
    db.session.commit()

@app.route('/')
def index():
    """Home page - render landing page if not authenticated"""
    if current_user.is_authenticated:
        # Check if the logged in entity is an Admin
        is_admin = getattr(current_user, 'role', None) in ['admin', 'super_admin'] or isinstance(current_user, Admin)
        if is_admin:
            return redirect(url_for('admin.dashboard'))
        return render_template('index.html')
    return render_template('landing.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat API endpoint. Handles both authenticated (DB) and unauthenticated (transient) users."""
    try:
        if not api_key:
            return jsonify({'error': 'Google API key tidak dikonfigurasi'}), 500
            
        data = request.json or {}
        user_message = data.get('message', '').strip()
        
        if current_user.is_authenticated:
            session_id = data.get('session_id', f'user_{current_user.id}')
        else:
            session_id = data.get('session_id', 'transient_session')
        
        if not user_message:
            return jsonify({'error': 'Pesan tidak boleh kosong'}), 400
        
        # Check if user is authenticated
        if current_user.is_authenticated:
            # Get conversation history from database
            messages_db = ChatMessage.query.filter_by(
                user_id=current_user.id,
                session_id=session_id
            ).order_by(ChatMessage.timestamp).all()
            
            # Add user message to database
            user_msg = ChatMessage()
            user_msg.user_id = current_user.id
            user_msg.role = 'user'
            user_msg.content = user_message
            user_msg.session_id = session_id
            db.session.add(user_msg)
            db.session.commit()
            
            # Prepare conversation history for Gemini
            conversation_history = []
            for msg in messages_db:
                conversation_history.append({
                    "role": "user" if msg.role == "user" else "model",
                    "parts": [{"text": msg.content}]
                })
        else:
            # Unauthenticated User - use transient history from request
            transient_history = data.get('transient_history', [])
            conversation_history = transient_history
            
        # Add current user message to Gemini history (only needed for Gemini, not appending to transient_history)
        history_for_gemini = conversation_history.copy()
        
        # Start chat session with history (excluding current message)
        try:
            chat_session = model.start_chat(history=history_for_gemini)
            # Send current message and get response
            response = chat_session.send_message(user_message)
            bot_response = response.text
        except Exception as api_error:
            print(f"API Error: {str(api_error)}", flush=True)
            bot_response = f"Maaf, terjadi kesalahan saat memproses pesan. Error: {str(api_error)[:100]}"
        
        if current_user.is_authenticated:
            # Add bot response to database
            bot_msg = ChatMessage()
            bot_msg.user_id = current_user.id
            bot_msg.role = 'assistant'
            bot_msg.content = bot_response
            bot_msg.session_id = session_id
            db.session.add(bot_msg)
            db.session.commit()
            
            # Log activity
            log_chat_activity(current_user.id, user_message, bot_response)
        
        return jsonify({
            'success': True,
            'response': bot_response,
            'message': user_message
        })
    
    except Exception as e:
        print(f"Chat Endpoint Error: {str(e)}", flush=True)
        return jsonify({
            'error': f'Terjadi kesalahan: {str(e)[:100]}'
        }), 500

@app.route('/api/history')
@login_required
def get_history():
    """Get chat history"""
    session_id = request.args.get('session_id', f'user_{current_user.id}')
    
    messages = ChatMessage.query.filter_by(
        user_id=current_user.id,
        session_id=session_id
    ).order_by(ChatMessage.timestamp).all()
    
    history = [{
        'role': msg.role,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat()
    } for msg in messages]
    
    return jsonify({'history': history})

@app.route('/api/delete-session', methods=['POST'])
@login_required
def delete_session():
    """Delete specific chat session"""
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID tidak diberikan'}), 400
        
        # Delete all messages in this session
        ChatMessage.query.filter_by(
            user_id=current_user.id,
            session_id=session_id
        ).delete()
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-history', methods=['POST'])
@login_required
def clear_history():
    """Clear ALL chat history for current user"""
    try:
        # Delete all messages for this user
        ChatMessage.query.filter_by(
            user_id=current_user.id
        ).delete()
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions')
@login_required
def get_sessions():
    """Get all user sessions"""
    sessions = db.session.query(ChatMessage.session_id.distinct()).filter_by(
        user_id=current_user.id
    ).all()
    
    return jsonify({'sessions': [s[0] for s in sessions]})

@app.route('/api/latest-session')
@login_required
def get_latest_session():
    """Get the latest chat session for current user"""
    # Get latest message by timestamp
    latest_message = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.timestamp.desc()).first()
    
    if latest_message:
        return jsonify({
            'session_id': latest_message.session_id,
            'message_count': ChatMessage.query.filter_by(
                user_id=current_user.id,
                session_id=latest_message.session_id
            ).count()
        })
    else:
        # No previous session, return None to create new
        return jsonify({'session_id': None, 'message_count': 0})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
