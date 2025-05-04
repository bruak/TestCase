from functools import wraps
from flask import jsonify, request
import jwt, os
from datetime import datetime, timedelta, timezone
from werkzeug.security import check_password_hash
from db import User, db
from createapp import app

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', ':D')
JWT_EXPIRATION_DELTA = timedelta(hours=24)

BLACKLISTED_TOKENS = set()

USER_TOKENS = {}

def is_token_blacklisted(token):
    return token in BLACKLISTED_TOKENS

def add_token_to_blacklist(token):
    BLACKLISTED_TOKENS.add(token)
    return True

def invalidate_user_tokens(username):
    if username in USER_TOKENS:
        old_token = USER_TOKENS[username]
        if old_token:
            add_token_to_blacklist(old_token)
    return True

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        if is_token_blacklisted(token):
            return jsonify({'message': 'Token has been revoked!'}), 401
            
        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = data['username']
            
            user = User.query.filter_by(username=current_user).first()
            if not user or str(user.id) != str(data.get('user_id')):
                return jsonify({'message': 'Token validation failed!'}), 401
                
            if datetime.now(timezone.utc) > datetime.fromtimestamp(data['exp'], timezone.utc):
                return jsonify({'message': 'Token has expired!'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        except Exception as e:
            return jsonify({'message': f'Token validation error: {str(e)}'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route('/login-token', methods=['POST'])
def login_token():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": 'Invalid credentials'}), 401
    
    user_id = user.id
    token_payload = {
        'username': username,
        'exp': datetime.now(timezone.utc) + JWT_EXPIRATION_DELTA,
        'iat': datetime.now(timezone.utc),
        'user_id': user_id,
    }
    
    invalidate_user_tokens(username)
    
    token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm="HS256")
    
    USER_TOKENS[username] = token
    
    return jsonify({
        'token': token,
        'user': {
            'username': username,
            'user_id': user_id,
        },
        'expires_in': int(JWT_EXPIRATION_DELTA.total_seconds()),
        'message': 'Login successful'
    })

@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    token = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    
    if token:
        add_token_to_blacklist(token)
        
        if current_user in USER_TOKENS:
            USER_TOKENS.pop(current_user, None)
            
        return jsonify({"message": "Logged out successfully"}), 200
    
    return jsonify({"message": "No token provided"}), 400