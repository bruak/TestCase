
## 5. Detaylı Loglama İmplementasyonu

```python
import logging
import os
from logging.handlers import RotatingFileHandler
import time

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup loggers"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_path = os.path.join(log_dir, log_file)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup file handler with rotation
    file_handler = RotatingFileHandler(
        log_path, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Get logger and set level
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Add handlers if they don't exist
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# Websocket için logger oluşturma
websocket_logger = setup_logger('websocket', 'websocket.log')
auth_logger = setup_logger('auth', 'auth.log')
app_logger = setup_logger('app', 'app.log')

# Kullanım örneği:
# from logger import websocket_logger
# websocket_logger.info("User connected")
# websocket_logger.error("Authentication failed", exc_info=True)
```

Bu logger'ı websocket.py dosyasında şu şekilde kullanabilirsiniz:

```python
from logger import websocket_logger as logger

# print() yerine logger kullanımı:
# print(f"NEW CLIENT CONNECTED: {request.sid}")
logger.info(f"NEW CLIENT CONNECTED: {request.sid}")

# Hata durumlarında:
try:
    # ...kod...
except Exception as e:
    logger.error(f"Error during authentication", exc_info=True)
    emit('response', {'message': 'An authentication error occurred'})
```

Bu değişiklikler uygulamanızı daha güvenli hale getirecek ve sorunları daha kolay teşhis etmenizi sağlayacaktır.




NOTE:
Potansiyel bir DoS (Denial of Service) vektörü olabilir, ancak korunuyor çünkü:

Tüm bağlantılar JWT doğrulamasına tabi
Aynı kullanıcı aynı anda iki kez giriş yapmaya çalışırsa, eski oturum otomatik olarak kapatılıyor
Toplam bağlantı sayısı MAX_CONNECTIONS ile sınırlanıyor


en son dökümantasyon yapılırken websocket.js üzerindeki eventler izlenebilir.



TODO

.......

loglar alınacak 
docker secret kullanılabilir


TESTLER

TEST SENARYO: user tarayıcıdan giriş yapar, kötü niyetli olarak JWT token verisi alınır ve postman ile disconnect atılır.
SONUÇ: Token doğru şekilde revoke edilir fakat user hala aktif olarak bağlı gözükür ve kalan hak artmaz. kötü niyet önlenir.


TEST SENARYO: 5 kişilik hak var ve 5 kişi bağlandı bu durumda bağlanan 6. kişi
.......

bruak: #codebase analyse all the code and make a detailed documentation. auth.py, app.py, wesocket.py - frontend files.

GitHub Copilot: # Flask WebSocket Application Documentation

This documentation provides a comprehensive overview of the Flask WebSocket application with JWT authentication, analyzing the core components including auth.py, app.py, websocket.py, and frontend files.

## 1. System Architecture

The application implements a real-time WebSocket communication system with secure authentication:

```
+------------------------+            +------------------------+
|                        |            |                        |
|     Client Browser     |            |    Flask Server        |
|                        |            |                        |
|  +------------------+  |  HTTPS/WSS |  +------------------+  |
|  |                  |  |<---------->|  |                  |  |
|  |  Frontend        |  |            |  |  App.py          |  |
|  |  - HTML          |  |            |  |  - Routes        |  |
|  |  - JavaScript    |  |            |  |  - Config        |  |
|  |  - CSS           |  |            |  |                  |  |
|  +------------------+  |            |  +------------------+  |
|          |             |            |          |             |
|          v             |            |          v             |
|  +------------------+  |            |  +------------------+  |
|  |                  |  |            |  |                  |  |
|  |  WebSocket.js    |  |<---------->|  |  WebSocket.py    |  |
|  |  - Socket.IO     |  |   Events   |  |  - Socket.IO     |  |
|  |  - Connection    |  |            |  |  - User Tracking |  |
|  |    Management    |  |            |  |  - Authentication|  |
|  +------------------+  |            |  +------------------+  |
|                        |            |          |             |
|                        |            |          v             |
|                        |            |  +------------------+  |
|                        |            |  |                  |  |
|                        |            |  |  Auth.py         |  |
|                        |            |  |  - JWT           |  |
|                        |            |  |  - Token Mgmt    |  |
|                        |            |  |  - Validation    |  |
|                        |            |  +------------------+  |
|                        |            |          |             |
|                        |            |          v             |
|                        |            |  +------------------+  |
|                        |            |  |                  |  |
|                        |            |  |  DB.py           |  |
|                        |            |  |  - SQLite        |  |
|                        |            |  |  - User Model    |  |
|                        |            |  |                  |  |
|                        |            |  +------------------+  |
+------------------------+            +------------------------+
```

## 2. Authentication System (auth.py)

The authentication system uses JWT (JSON Web Tokens) to secure both REST API and WebSocket connections.

### Key Components:

#### 2.1 JWT Configuration
```python
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', ':D')
JWT_EXPIRATION_DELTA = timedelta(hours=24)
```

#### 2.2 Token Management
```python
BLACKLISTED_TOKENS = set()  # Tracks revoked tokens
USER_TOKENS = {}  # Maps usernames to active tokens
```

#### 2.3 Core Authentication Functions

- **Token Blacklisting**: Prevents usage of logged-out tokens
  ```python
  def is_token_blacklisted(token):
      return token in BLACKLISTED_TOKENS
  
  def add_token_to_blacklist(token):
      BLACKLISTED_TOKENS.add(token)
      return True
  ```

- **One Token Per User Policy**: Invalidates old tokens on new login
  ```python
  def invalidate_user_tokens(username):
      if username in USER_TOKENS:
          old_token = USER_TOKENS[username]
          if old_token:
              add_token_to_blacklist(old_token)
      return True
  ```

- **Protected Route Decorator**: Middleware for route protection
  ```python
  @token_required
  def protected_route(current_user):
      # Only accessible with valid token
  ```

#### 2.4 Authentication Endpoints

- **Login**: Generates JWT token for validated users
  ```python
  @app.route('/login-token', methods=['POST'])
  def login_token():
      # Validates credentials and returns JWT token
  ```

- **Logout**: Invalidates the user's JWT token
  ```python
  @app.route('/logout', methods=['POST'])
  @token_required
  def logout(current_user):
      # Invalidates the token
  ```

#### 2.5 Security Features

- Token expiration (24 hours)
- Blacklisting to revoke tokens immediately
- Single active token per user
- Comprehensive error handling for various token validation failures

## 3. Application Core (app.py)

The main application file ties together all components and configures the Flask server.

### Key Components:

#### 3.1 Application Setup
```python
app = create_app()  # Creates Flask app with SQLite configuration
app.static_folder = None  # Custom static file handling
```

#### 3.2 Route Configuration
```python
@app.route('/frontend/<path:path>')  # Serves frontend assets
@app.route('/', methods=['GET'])     # Serves login page
@app.route('/socket', methods=['GET'])  # Protected WebSocket test page
@token_required
def serve_testpage(current_user):
    return send_from_directory('.', 'frontend/html/websockettest.html')
```

#### 3.3 HTTPS Configuration
```python
socketio.run(app, host='0.0.0.0', port=5000, debug=True, 
            certfile=cert_path, keyfile=key_path)
```

#### 3.4 Environment Configuration
```python
dotenv_path = find_dotenv(usecwd=True)
if dotenv_path:
    print(f".env file found at: {dotenv_path} ✓ ")
    # Load environment variables
```

## 4. WebSocket Implementation (websocket.py)

The WebSocket implementation handles real-time communication with authenticated clients.

### Key Components:

#### 4.1 Connection Configuration
```python
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
```

#### 4.2 Connection Management
```python
connected_users = {}  # Maps usernames to session IDs
MAX_CONNECTIONS = 3  # Maximum concurrent connections allowed
```

#### 4.3 WebSocket Authentication
```python
def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        # Authenticate WebSocket events using JWT
    return wrapped
```

#### 4.4 WebSocket Events

- **Connection**: Handles new client connections
  ```python
  @socketio.on('connect')
  def handle_connect():
      # Handles new connections and updates stats
  ```

- **User Registration**: Associates WebSocket connection with authenticated user
  ```python
  @socketio.on('register_user')
  def register_user(data):
      # Authenticates user and manages connection limits
  ```

- **Disconnection**: Cleans up when clients disconnect
  ```python
  @socketio.on('disconnect')
  def handle_disconnect(data=None):
      # Removes user from connected_users and updates stats
  ```

- **User Listing**: Provides list of online users
  ```python
  @socketio.on('get_online_users')
  @authenticated_only
  def get_online_users():
      # Returns list of connected users
  ```

- **Ping/Pong**: Connection health check
  ```python
  @socketio.on('ping_manual')
  def handle_ping():
      # Responds with server timestamp
  ```

#### 4.5 Security Features

- Connection limit enforcement (MAX_CONNECTIONS = 3)
- JWT validation for all authenticated events
- Detection of multiple sessions for the same user
- Force disconnection for duplicate logins

## 5. Frontend Implementation

The frontend provides user interface for authentication and WebSocket testing.

### 5.1 Login Page (login.html, login.js)

Provides interface for user authentication:
- Username/password input
- Token storage in localStorage
- Automatic redirection when already logged in
- Error handling for authentication failures

```javascript
// Key login functionality
function login() {
    // Authenticates user and stores JWT token
    fetch('https://localhost:5000/login-token', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        localStorage.setItem('jwt_token', data.token);
        localStorage.setItem('username', data.user.username);
        // Redirect to WebSocket test page
    })
}
```

### 5.2 WebSocket Test Page (websockettest.html, websocket.js)

Provides interface for testing WebSocket functionality:
- Real-time connection status
- User list display
- Connection statistics
- Command buttons for WebSocket operations

```javascript
// Key WebSocket functionality
function connectSocket() {
    socket = io(url, {
        auth: { token: token },
        transports: ["websocket"],
        secure: true
    });

    socket.on("connect", () => {
        // Register user with token
        socket.emit("register_user", {
            token: token,
            username: username
        });
    });

    // Handle various socket events
    socket.on("response", (data) => { /* ... */ });
    socket.on("user_status", (data) => { /* ... */ });
    socket.on("connection_slots", (data) => { /* ... */ });
    // etc.
}
```

## 6. Security Considerations

The application implements several security measures:

1. **HTTPS**: All communication is encrypted with TLS
2. **JWT Authentication**: Secures both HTTP and WebSocket connections
3. **Token Blacklisting**: Immediately invalidates logged-out tokens
4. **Connection Limiting**: Prevents resource exhaustion (3 concurrent connections)
5. **Password Hashing**: Uses secure password storage (pbkdf2:sha256)
6. **Session Management**: One active token per user, forcing old sessions to disconnect
7. **Error Handling**: Comprehensive error handling prevents information leakage

## 7. Deployment

The application is containerized using Docker for easy deployment:

```yaml
# docker-compose.yml
services:
  server:
    container_name: prodServer
    build: .
    volumes:
      - .:/app
    ports:
      - "5000:5000"
    environment:
      - PYTHONUNBUFFERED=1
      - FLASK_APP=app.py
      - FLASK_ENV=development
      - EVENTLET_NO_GREENDNS=YES
```

## 8. Recommendations for Improvement

1. **JWT Secret Management**: Use Azure Key Vault or another secure key management service instead of environment variables
2. **Structured Logging**: Implement the logging system outlined in Doc.md
3. **Rate Limiting**: Add rate limiting for authentication endpoints
4. **User Authentication Audit Trail**: Track login/logout events
5. **Token Refresh Mechanism**: Implement token refresh to extend sessions without re-login
6. **WebSocket Connection Cleanup**: Add periodic cleanup of stale connections
7. **HTTPS Certificate Management**: Use proper certificates instead of self-signed

## Summary

This Flask application demonstrates a complete implementation of secure WebSocket communication with JWT authentication. It includes proper user management, connection limiting, and a user-friendly test interface. The architecture supports real-time communication while maintaining security best practices.

Similar code found with 2 license types