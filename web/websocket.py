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

# Global olarak connected_users tanımla
connected_users = {}

# Maksimum eşzamanlı bağlantı sınırı
MAX_CONNECTIONS = 1

# Kalan bağlantı sayısını hesapla
def get_remaining_slots():
    return max(0, MAX_CONNECTIONS - len(connected_users))

def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not hasattr(f, 'authenticated') or not f.authenticated:
            return f(*args, **kwargs)
            
        # Check if the connection includes authentication
        auth_token = None
        if 'token' in kwargs.get('auth', {}):
            auth_token = kwargs.get('auth').get('token')
        
        if not auth_token:
            disconnect()
            return False
            
        try:
            # Token blacklist kontrolü
            if is_token_blacklisted(auth_token):
                emit('response', {'message': 'Token has been revoked!'})
                disconnect()
                return False
                
            # Decode the JWT token
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

def update_remaining_slots(socketio_instance=None):
    """
    Kalan bağlantı hakkını hesaplar ve tüm istemcilere yayınlar
    """
    try:
        count = len(connected_users)
        remaining_slots = get_remaining_slots()
        print(f"Broadcasting remaining slots: {remaining_slots}, max: {MAX_CONNECTIONS}, current: {count}")
        
        # socketio_instance parametresi kontrol edilir
        if socketio_instance is None:
            # websocket_init içinden çağrıldığında kullanılacak
            if 'socketio' in globals():
                socketio_instance = globals()['socketio']
            else:
                print("Warning: socketio not available yet")
                return
        
        # Tüm bağlı kullanıcılara kalan bağlantı bilgisini gönder
        socketio_instance.emit('connection_slots', {
            'count': count,
            'remaining_slots': remaining_slots,
            'max_connections': MAX_CONNECTIONS
        }, namespace='/')
        
        print(f"Remaining slots broadcast completed")
    except Exception as e:
        print(f"Error broadcasting remaining slots: {str(e)}")

def websocket_init():
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
        
        # Yeni bağlantı geldiğinde kalan bağlantı hakkını güncelle
        update_remaining_slots(socketio)
    
    # connected_users global değişkenini kullan
    global connected_users
    
    # Anlık kullanıcı sayısını güncelleme ve yayınlama
    def update_user_count():
        count = len(connected_users)
        remaining_slots = get_remaining_slots()
        print(f"Updating user count: {count}, remaining slots: {remaining_slots}")
        try:
            print(f"Current users: {connected_users}")
            print(f"Broadcasting user count: {count} to all connected clients")
            socketio.emit('user_count', {
                'count': count, 
                'remaining_slots': remaining_slots,
                'max_connections': MAX_CONNECTIONS
            }, namespace='/')
            print(f"User count broadcast completed")
        except Exception as e:
            print(f"Error broadcasting user count: {str(e)}")
    
    @socketio.on('register_user')
    def register_user(data):
        global connected_users
        
        print(f"Register user request received: {data}")
        
        try:
            if 'token' not in data or 'username' not in data:
                emit('response', {'message': 'Missing token or username'})
                return
                
            token = data.get('token')
            user_id = data.get('username')
            
            print(f"Processing registration for {user_id}")
            
            # Token blacklist kontrolü
            try:
                if is_token_blacklisted(token):
                    emit('response', {'message': 'Token has been revoked!'})
                    return
            except Exception as e:
                print(f"Blacklist check error: {str(e)}")
                emit('response', {'message': f'Blacklist verification error: {str(e)}'})
                return
            
            # Verify token
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
            
            # İçerik doğrulama kontrolü
            if jwt_data.get('username') != user_id:
                print(f"Username mismatch: {jwt_data.get('username')} != {user_id}")
                emit('response', {'message': 'Token username mismatch!'})
                return
                
            session_id = request.sid  # Socket ID
            
            # Bağlantı sınırı kontrolü
            if user_id not in connected_users and len(connected_users) >= MAX_CONNECTIONS:
                print(f"Connection limit reached ({MAX_CONNECTIONS}). Rejecting connection from {user_id}")
                emit('response', {'message': f'Connection limit reached. Maximum {MAX_CONNECTIONS} concurrent connections allowed.'})
                disconnect()
                return
            
            # Aynı kullanıcının önceki bağlantısını sonlandır
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
            
            # Store the user connection
            connected_users[user_id] = session_id
            print(f"User registered: {user_id} with SID {session_id}")
            print(f"Current connected users: {connected_users}")
            
            emit('response', {'message': f'User {user_id} registered successfully'})
            
            try:
                socketio.emit('user_status', {'user': user_id, 'status': 'online'}, to=None)
                update_user_count()
                update_remaining_slots(socketio)  # Kalan bağlantı hakkını güncelle
            except Exception as e:
                print(f"Error during status broadcast: {str(e)}")
                
        except Exception as e:
            print(f"Register user unexpected error: {str(e)}")
            emit('response', {'message': f'Registration error: {str(e)}'})
    
    @socketio.on('disconnect')
    def handle_disconnect(data=None):
        global connected_users
        sid = request.sid
        print(f"Client disconnecting: SID={sid}")
        disconnected_user = None
        
        for user_id, user_sid in list(connected_users.items()):
            if user_sid == sid:
                disconnected_user = user_id
                del connected_users[user_id]
                print(f"User removed from connected_users: {user_id}")
                break
        
        print(f"CLIENT DISCONNECTED: {sid}, USER: {disconnected_user}")
        print(f"Remaining connected users: {connected_users}")
        
        try:
            emit('response', {'message': 'WEBSOCKET DISCONNECTED'})
        except Exception as e:
            print(f"Error sending disconnect response: {str(e)}")
        
        if disconnected_user:
            try:
                socketio.emit('user_status', {'user': disconnected_user, 'status': 'offline'}, namespace='/')
                print(f"Broadcast user offline status: {disconnected_user}")
            except Exception as e:
                print(f"Error during status broadcast: {str(e)}")
        
        try:
            print("Updating user count after disconnect")
            update_user_count()
            update_remaining_slots(socketio)  # Kalan bağlantı hakkını güncelle
            print("User count updated successfully after disconnect")
        except Exception as e:
            print(f"Error updating user count after disconnect: {str(e)}")
    
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
    
    @socketio.on('check_connections')
    def check_connections():
        print("Checking and cleaning up connections")
        
        active_sids = set()
        removed_users = []
        
        try:
            if hasattr(socketio, 'server') and hasattr(socketio.server, 'eio') and hasattr(socketio.server.eio, 'sockets'):
                active_sids = set(socketio.server.eio.sockets.keys())
                print(f"Active SIDs from server: {active_sids}")
            else:
                print("Could not get active SIDs: socketio server structure not as expected")
                # Aktif bağlantıları alamıyorsak, temizlik yapmayalım
                emit('online_users', {'users': list(connected_users.keys()), 'count': len(connected_users)})
                return
        except Exception as e:
            print(f"Error getting active sids: {str(e)}")
            # Hata durumunda da temizlik yapmayalım
            emit('online_users', {'users': list(connected_users.keys()), 'count': len(connected_users)})
            return
        
        # Aktif SID listesi boşsa ve kullanıcı listesi boş değilse, temizlik yapmayalım
        # Bu, server.eio.sockets yapısının beklediğimiz gibi olmadığını gösterir
        if not active_sids and connected_users:
            print("Warning: Active SIDs list is empty but there are connected users. Skipping cleanup.")
            emit('online_users', {'users': list(connected_users.keys()), 'count': len(connected_users)})
            return
        
        for user_id, sid in list(connected_users.items()):
            try:
                if sid not in active_sids:
                    print(f"Found stale connection: {user_id} with SID {sid}")
                    del connected_users[user_id]
                    removed_users.append(user_id)
            except Exception as e:
                print(f"Error checking connection for {user_id}: {str(e)}")
        
        if removed_users:
            print(f"Removed {len(removed_users)} stale connections: {removed_users}")
            
            for user_id in removed_users:
                try:
                    socketio.emit('user_status', {'user': user_id, 'status': 'offline'}, namespace='/')
                except Exception as e:
                    print(f"Error broadcasting offline status for {user_id}: {str(e)}")
            
            update_user_count()
            update_remaining_slots(socketio)
        
        print(f"Current connected users after cleanup: {list(connected_users.keys())}, count: {len(connected_users)}")
        
        emit('online_users', {'users': list(connected_users.keys()), 'count': len(connected_users)})
    
    @socketio.on('get_user_count')
    def get_user_count():
        # check_connections() fonksiyonu çağrılmadan kullanıcı sayısını doğrudan döndür
        count = len(connected_users)
        remaining_slots = get_remaining_slots()
        print(f"User count requested, returning: {count}, remaining slots: {remaining_slots}")
        emit('user_count', {
            'count': count,
            'remaining_slots': remaining_slots,
            'max_connections': MAX_CONNECTIONS
        })
    
    @socketio.on('authenticated_message')
    @authenticated_only
    def handle_authenticated_message(data):
        print(f"Received authenticated message: {data}")
        emit('response', {'message': 'Received your authenticated message', 'data': data})
    
    @socketio.on('message')
    def handle_message(data):
        print(f"Received message: {data}")
        emit('response', {'message': 'Received your message', 'data': data})
    
    @socketio.on('get_online_users')
    @authenticated_only
    def get_online_users():
        # Burada check_connections() çağrılmıyor, böylece gereksiz temizlik yapılmıyor
        # Bunun yerine sadece kullanıcı listesini doğrudan gönderiyoruz
        online_users = list(connected_users.keys())
        print(f"get_online_users called - returning users: {online_users}, count: {len(online_users)}")
        emit('online_users', {'users': online_users, 'count': len(online_users)})
    get_online_users.authenticated = True
    
    @socketio.on('ping_manual')
    def handle_ping():
        sid = request.sid
        print(f"Ping received from {sid}")
        
        for user_id, session_sid in list(connected_users.items()):
            if session_sid == sid:
                print(f"Updating last activity for {user_id}")
                break
        
        emit('pong_manual', {'time': time.time()})
    
    return socketio


