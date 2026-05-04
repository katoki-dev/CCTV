from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db
from logging_manager import get_logging_manager

auth_bp = Blueprint('auth', __name__)
logging_manager = get_logging_manager()

@auth_bp.route('/')
def index():
    """Redirect to login or campus portal as home page"""
    if current_user.is_authenticated:
        return redirect(url_for('campus.portal_page'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('campus.portal_page'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Check if user is approved
            if not user.is_approved:
                error_msg = 'Your account is pending admin approval. Please contact an administrator.'
                if request.is_json:
                    return jsonify({'success': False, 'error': error_msg}), 403
                return render_template('login.html', error=error_msg)
            
            login_user(user)
            logging_manager.log_system_event("LOGIN", f"User '{username}' logged in")
            
            redirect_url = url_for('campus.portal_page')
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'redirect': redirect_url,
                    'user': user.to_dict()
                })
            return redirect(redirect_url)
        
        if request.is_json:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            error_msg = 'All fields are required'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            return render_template('register.html', error=error_msg)
        
        if password != confirm_password:
            error_msg = 'Passwords do not match'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            return render_template('register.html', error=error_msg)
        
        if len(password) < 6:
            error_msg = 'Password must be at least 6 characters'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            return render_template('register.html', error=error_msg)
        
        # Check for existing user
        if User.query.filter_by(username=username).first():
            error_msg = 'Username already exists'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            return render_template('register.html', error=error_msg)
        
        if User.query.filter_by(email=email).first():
            error_msg = 'Email already registered'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            return render_template('register.html', error=error_msg)
        
        # Create new user (not approved by default)
        user = User(
            username=username,
            email=email,
            phone_number=data.get('phone_number', '').strip() or None,
            role=data.get('role', 'student'),
            is_admin=False,
            is_approved=False  # Requires admin approval
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logging_manager.log_system_event("USER_REGISTERED", f"New user '{username}' registered, pending approval")
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Registration successful. Pending admin approval.'}), 201
        
        return render_template('register.html', success=True)
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout"""
    logging_manager.log_system_event("LOGOUT", f"User '{current_user.username}' logged out")
    logout_user()
    return redirect(url_for('auth.login'))
