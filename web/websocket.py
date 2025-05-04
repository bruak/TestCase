from flask_socketio import SocketIO, emit, disconnect
from createapp import app
from flask import request
import jwt
import os
import time
from functools import wraps
from auth import is_token_blacklisted
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', ':DDD')

connected_users = {}

MAX_CONNECTIONS = 3

def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not hasattr(f, 'authenticated') or not f.authenticated:
            return f(*args, **kwargs)
            
        auth_token = None
        if 'token' in kwargs.get('auth', {}):
            auth_token = kwargs.get('auth').get('token')
        
        if not auth_token:
            disconnect()
            return False
            
        try:
            if is_token_blacklisted(auth_token):
                emit('response', {'message': 'Token has been revoked!'})
                disconnect()
                return False
                
            jwt.decode(auth_token, JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            emit('response', {'message': 'Invalid token!'})
            disconnect()
            return False
        except jwt.ExpiredSignatureError:
            emit('response', {'message': 'Token has expired!'})
            disconnect()
            return False
        except Exception as e:
            emit('response', {'message': f'Token validation error: {str(e)}'})
            disconnect()
            return False
            
        return f(*args, **kwargs)
    return wrapped

def websocket_init():
    global connected_users
    
    socketio = SocketIO(
        app, 
        cors_allowed_origins=["https://localhost:5000", "https://127.0.0.1:5000"],
        cors_credentials=True,  
        engineio_logger=True,
        logger=True,
        ping_timeout=120,      
        ping_interval=25,      
        async_mode='eventlet',  
        max_http_buffer_size=1e8,    
        always_connect=True,         
    )
    
    @socketio.on('connect')
    def handle_connect():
        print(f"NEW CLIENT CONNECTED: {request.sid}")
        emit('response', {'message': 'WEBSOCKET CONNECTED'})
        
        update_remaining_slots(socketio)
    
    # * Kalan bağlantı hakkını günceller.
    def update_remaining_slots(socketio_instance=None):
        try:
            count = len(connected_users)
            remaining_slots = get_remaining_slots()
            
            if socketio_instance is None:
                if 'socketio' in globals():
                    socketio_instance = globals()['socketio']
                else:
                    print("Warning: socketio not available yet")
                    return
            
            socketio_instance.emit('connection_slots', {
                'count': count,
                'remaining_slots': remaining_slots,
                'connection_limits': MAX_CONNECTIONS
            }, namespace='/')
            
        except Exception as e:
            print(f"Error broadcasting remaining slots: {str(e)}")
    
    def get_remaining_slots():
        return max(0, MAX_CONNECTIONS - len(connected_users))
    
    # * Anlık kullanıcı sayısını Connect ve Disconnect olaylarında günceller.
    def update_user_count():
        count = len(connected_users)
        remaining_slots = get_remaining_slots()
        try:
            socketio.emit('user_count', {
                'count': count, 
                'remaining_slots': remaining_slots,
                'max_connections': MAX_CONNECTIONS
            }, namespace='/')
        except Exception as e:
            print(f"Error broadcasting user count: {str(e)}")
    
    @socketio.on('register_user')
    def register_user(data):
        try:
            if 'token' not in data or 'username' not in data:
                emit('response', {'message': 'Missing token or username'})
                return
                
            token = data.get('token')
            user_id = data.get('username')
            
            try:
                if is_token_blacklisted(token):
                    emit('response', {'message': 'Token has been revoked!'})
                    return
            except Exception as e:
                print(f"Blacklist check error: {str(e)}")
                emit('response', {'message': f'Blacklist verification error: {str(e)}'})
                return
            
            try:
                jwt_data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
                print(f"Token decoded: {jwt_data}")
            except jwt.ExpiredSignatureError:
                emit('response', {'message': 'Token has expired!'})
                return
            except jwt.InvalidTokenError:
                emit('response', {'message': 'Invalid token!'})
                return
            except Exception as e:
                print(f"Token decode error: {str(e)}")
                emit('response', {'message': f'Token decode error: {str(e)}'})
                return
            

            if jwt_data.get('username') != user_id:
                print(f"Username mismatch: {jwt_data.get('username')} != {user_id}")
                emit('response', {'message': 'Token username mismatch!'})
                return
                
            session_id = request.sid
            
            if user_id not in connected_users and len(connected_users) >= MAX_CONNECTIONS:
                print(f"Connection limit reached ({MAX_CONNECTIONS}). Rejecting connection from {user_id}")
                emit('response', {'message': f'Connection limit reached. Maximum {MAX_CONNECTIONS} concurrent connections allowed.'})
                disconnect()
                return
            
            # * Eğer kullanıcı zaten bağlıysa, eski bağlantıyı kapatır.
            if user_id in connected_users:
                old_sid = connected_users[user_id]
                if old_sid != session_id:
                    try:
                        socketio.emit('force_disconnect', 
                                    {'message': 'New login detected from another location'}, 
                                    room=old_sid)
                        print(f"Forcing disconnect for previous session of {user_id}")
                    except Exception as e:
                        print(f"Error during force disconnect: {str(e)}")
            
            connected_users[user_id] = session_id
            print(f"User registered: {user_id} with SID {session_id}")
            print(f"Current connected users: {connected_users}")
            
            emit('response', {'message': f'User {user_id} registered successfully'})
            
            try:
                socketio.emit('user_status', {'user': user_id, 'status': 'online'}, to=None)
                update_user_count()
                update_remaining_slots(socketio)
            except Exception as e:
                print(f"Error during status broadcast: {str(e)}")
                
        except Exception as e:
            print(f"Register user unexpected error: {str(e)}")
            emit('response', {'message': f'Registration error: {str(e)}'})
    
    @socketio.on('disconnect')
    def handle_disconnect(data=None):
        sid = request.sid
        print(f"Client disconnecting: SID={sid}")
        disconnected_user = None
        
        for user_id, user_sid in list(connected_users.items()):
            if user_sid == sid:
                disconnected_user = user_id
                del connected_users[user_id]
                break
            
        try:
            emit('response', {'message': 'WEBSOCKET DISCONNECTED'})
        except Exception as e:
            print(f"Error sending disconnect response: {str(e)}")
        
        if disconnected_user:
            try:
                socketio.emit('user_status', {'user': disconnected_user, 'status': 'offline'}, namespace='/')
            except Exception as e:
                print(f"Error during status broadcast: {str(e)}")
        
        try:
            update_user_count()
            update_remaining_slots(socketio)
        except Exception as e:
            print(f"Error updating user count after disconnect: {str(e)}")
    
    @socketio.on('get_online_users')
    @authenticated_only
    def get_online_users():
            online_users = list(connected_users.keys())
            print(f"Returning online users-------------->: {online_users}")
            emit('online_users', {'users': online_users, 'count': len(online_users)})
    get_online_users.authenticated = True
    
    @socketio.on('authenticated_message')
    @authenticated_only
    def handle_authenticated_message(data):
        print(f"Received authenticated message: {data}")
        emit('response', {'message': 'Received your authenticated message', 'data': data})
    
    @socketio.on('ping_manual')
    def handle_ping():
        sid = request.sid
        print(f"Ping received from {sid}")
        
        for user_id, session_sid in list(connected_users.items()):
            if session_sid == sid:
                print(f"Updating last activity for {user_id}")
                break
        
        emit('pong_manual', {'time': time.time()})
    
    @socketio.on_error_default
    def default_error_handler(e):
        print(f"SocketIO error: {str(e)}")
        try:
            sid = request.sid
            if sid:
                print(f"Processing error for SID: {sid}")
                handle_disconnect()
        except Exception as ex:
            print(f"Error in error handler: {str(ex)}")
    return socketio


