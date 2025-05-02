
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



TODO
loglar alınacak 
docker secret kullanılabilir
SSL ileride problem yaratır mı o kontrol edilecek.



GitHub Copilot: # Flask WebSocket Uygulaması Teknik Dokümantasyonu

Bu dokümantasyon, JWT (JSON Web Tokens) tabanlı kimlik doğrulama ile güvenli bir WebSocket uygulamasının teknik detaylarını ve mimarisini açıklamaktadır.

## İçindekiler

1. Genel Mimari
2. Güvenlik Bileşenleri
3. API Endpoints
4. WebSocket Akışı
5. Kimlik Doğrulama Süreci
6. Docker Konteyneri
7. Güvenlik En İyi Uygulamaları

## Genel Mimari

Uygulama, şu temel bileşenlerden oluşmaktadır:

```
+--------------------------+
|         Flask App        |
+--------------------------+
|                          |
|  +------------------+    |
|  |      Auth        |    |
|  | (JWT Validation) |    |
|  +------------------+    |
|                          |
|  +------------------+    |
|  |     WebSocket    |    |
|  |   (SocketIO)     |    |
|  +------------------+    |
|                          |
|  +------------------+    |
|  |    Database      |    |
|  |    (SQLite)      |    |
|  +------------------+    |
|                          |
+--------------------------+
```

Sistem, HTTPS üzerinden güvenli bağlantı sağlayan bir Flask uygulamasıdır. Uygulama, JWT tabanlı kimlik doğrulama ile korunan WebSocket (Socket.IO) bağlantılarını destekler. Kullanıcı verileri SQLite veritabanında saklanır.

## Dosya Yapısı ve Açıklamaları

- createapp.py - Flask uygulamasını oluşturur
- db.py - SQLite veritabanı bağlantısını ve kullanıcı modelini yönetir
- auth.py - JWT tabanlı kimlik doğrulama ve token yönetimini içerir
- websocket.py - SocketIO bağlantılarını ve olaylarını yönetir
- app.py - Ana uygulama dosyası, tüm bileşenleri birleştirir ve HTTPS ile başlatır
- websockettest.html - WebSocket bağlantılarını test etmek için kullanıcı arayüzü

## Güvenlik Bileşenleri

### HTTPS (SSL/TLS)

Uygulama, güvenli iletişim için HTTPS protokolünü kullanır. Self-signed sertifika otomatik olarak üretilir.

```python
# app.py içinden
socketio.run(app, host='0.0.0.0', port=5000, debug=True, 
            certfile=cert_path, keyfile=key_path)
```

### JWT (JSON Web Tokens)

Kullanıcı kimlik doğrulaması JWT kullanılarak gerçekleştirilir:

```python
# auth.py içinden
token_payload = {
    'username': username,
    'exp': datetime.now(timezone.utc) + JWT_EXPIRATION_DELTA,
    'iat': datetime.now(timezone.utc),
    'user_id': user_id,
}
token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm="HS256")
```

JWT güvenlik özellikleri:
- Son kullanma tarihi (expiration time) kontrolü
- Token blacklist mekanizması
- Kullanıcı bazlı token yönetimi (oturum başına bir token)
- Token içeriğinin doğrulanması

## API Endpoints

| Endpoint | Metod | Açıklama | Yetkilendirme Gerekli |
|----------|-------|----------|----------------------|
| `/` | GET | WebSocket test sayfası | Hayır |
| `/register` | POST | Yeni kullanıcı kaydı oluşturma | Hayır |
| `/login-token` | POST | Kullanıcı giriş ve JWT token alma | Hayır |
| `/logout` | POST | Kullanıcı çıkışı (token geçersizleştirme) | Evet |
| `/protected` | GET | Test amaçlı korumalı endpoint | Evet |
| `/users` | GET | Tüm kullanıcıları listeler (test amaçlı) | Hayır |

### `/register` Endpoint

Yeni kullanıcı kaydı için:

```json
// POST /register
{
  "username": "testuser",
  "password": "securepassword123"
}
```

### `/login-token` Endpoint

Kullanıcı girişi ve JWT token almak için:

```json
// POST /login-token
{
  "username": "testuser",
  "password": "securepassword123"
}
```

Başarılı yanıt:

```json
{
  "token": "eyJhbGc...",
  "user": {
    "username": "testuser",
    "user_id": 1
  },
  "expires_in": 86400,
  "message": "Login successful"
}
```

## WebSocket Akışı

```
+-------------------+                 +-------------------+
|                   |  1. HTTP Login  |                   |
|      Client       +---------------->+      Server       |
|                   |                 |                   |
+-------------------+                 +-------------------+
         |                                      |
         | 2. JWT Token                         |
         |                                      |
         v                                      |
+-------------------+                 +-------------------+
|                   |  3. WebSocket   |                   |
|      Browser      +---------------->+   SocketIO Server |
|                   |  Connection     |                   |
+-------------------+                 +-------------------+
         |                                      |
         | 4. Send register_user event          |
         | with token + username                |
         v                                      v
+-------------------+                 +-------------------+
|                   |  5. Validation  |                   |
|     WebSocket     |<----------------+   JWT Validator   |
|      Client       |                 |                   |
+-------------------+                 +-------------------+
         |                                      |
         | 6. Real-time Communication           |
         |                                      |
         v                                      v
+-------------------+                 +-------------------+
|                   |  Broadcasting   |                   |
|    Client Events  |<--------------->+    Server Events  |
|                   |  Event Handling |                   |
+-------------------+                 +-------------------+
```

### WebSocket Olayları (Events)

| Olay Adı | Yön | Açıklama |
|----------|-----|----------|
| `connect` | Client ← Server | Bağlantı kurulduğunda |
| `register_user` | Client → Server | Kullanıcı kaydı (token ile) |
| `message` | Client ↔ Server | Genel mesaj gönderimi |
| `authenticated_message` | Client ↔ Server | Sadece kimlik doğrulaması yapılmış kullanıcılar için |
| `ping_manual` | Client → Server | Manuel ping/pong kontrolü |
| `debug_connection` | Client → Server | Bağlantı bilgilerini almak için |
| `get_online_users` | Client → Server | Çevrimiçi kullanıcıları almak için |
| `user_status` | Client ← Server | Kullanıcı durumu değişikliği (online/offline) |
| `user_count` | Client ← Server | Bağlı kullanıcı sayısı |
| `check_connections` | Client → Server | Bağlantı kontrolü ve temizliği |
| `disconnect` | Client ↔ Server | Bağlantı kesildiğinde |

## Kimlik Doğrulama Süreci

1. Kullanıcı `/login-token` endpoint'ine kullanıcı adı ve şifre gönderir
2. Şifre doğrulaması başarılıysa sunucu JWT token üretir 
3. Client bu token'ı WebSocket bağlantısı için kullanır
4. WebSocket bağlantısı kurulduktan sonra `register_user` olayıyla token ve kullanıcı adı gönderilir
5. Sunucu token'ı doğrular ve kullanıcıyı bağlı kullanıcılar listesine ekler
6. Token geçersiz veya süresi dolmuşsa bağlantı kesilir

### Token Doğrulama

```python
# JWT token doğrulama süreci
try:
    # Token blacklist kontrolü
    if is_token_blacklisted(token):
        emit('response', {'message': 'Token has been revoked!'})
        disconnect()
        return False
        
    # Decode the JWT token
    jwt_data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    
    # İçerik doğrulama kontrolü
    if jwt_data.get('username') != user_id:
        emit('response', {'message': 'Token username mismatch!'})
        return
        
except jwt.ExpiredSignatureError:
    emit('response', {'message': 'Token has expired!'})
    return
except jwt.InvalidTokenError:
    emit('response', {'message': 'Invalid token!'})
    return
```

### Token Blacklist Mekanizması

Sistem, çıkış yapan kullanıcıların token'larını blacklist'e ekleyerek güvenliği artırır:

```python
# Token blacklist için hafıza içi yapı
BLACKLISTED_TOKENS = set()
USER_TOKENS = {}  # Kullanıcı adı -> aktif token eşlemesi

def invalidate_user_tokens(username):
    """Kullanıcının eski tokenlerini geçersiz kılar"""
    if username in USER_TOKENS:
        old_token = USER_TOKENS[username]
        if old_token:
            add_token_to_blacklist(old_token)
    return True
```

## Docker Konteyneri

Uygulama, Docker içinde çalışacak şekilde yapılandırılmıştır:

```
+------------------+
|   Docker Host    |
|                  |
| +---------------+|
| |   prodServer  ||
| |               ||
| | +-------------+|
| | |   Flask     ||
| | |  (HTTPS)    ||
| | +-------------+|
| |               ||
| | +-------------+|
| | | WebSocket   ||
| | | (SocketIO)  ||
| | +-------------+|
| |               ||
| | +-------------+|
| | |  SQLite DB  ||
| | +-------------+|
| +---------------+|
+------------------+
```

### Docker Compose Yapılandırması

```yaml
services:
  server:
    container_name: prodServer
    build: .
    volumes:
      - .:/app
    ports:
      - "5000:5000"  # For HTTPS access
      - "5001:5001"  # For HTTP access
    environment:
      - PYTHONUNBUFFERED=1
      - FLASK_APP=app.py
      - FLASK_ENV=development
      - EVENTLET_NO_GREENDNS=YES
    restart: always
```

## Kullanıcı Bağlantı Yönetimi

```
+------------------+             +------------------+
|                  |             |                  |
|  İstemci Tarafı  |             |   Sunucu Tarafı  |
|                  |             |                  |
+------------------+             +------------------+
         |                                 |
         | connect()                       |
         |-------------------------------->|
         |                                 | handle_connect()
         |                                 |
         | emit('register_user', data)     |
         |-------------------------------->|
         |                                 | register_user(data)
         |                                 | - Token doğrulama
         |                                 | - Kullanıcı kaydı
         |                                 |
         |     emit('user_status')         |
         |<--------------------------------|
         |                                 |
         |     emit('user_count')          |
         |<--------------------------------|
         |                                 |
         |        ...                      |
         |                                 |
         | disconnect()                    |
         |-------------------------------->|
         |                                 | handle_disconnect()
         |                                 | - Kullanıcıyı listeden sil
         |                                 | - Kullanıcı sayısını güncelle
         |     emit('user_status')         |
         |<--------------------------------|
         |                                 |
         |     emit('user_count')          |
         |<--------------------------------|
         |                                 |
```

Sistem aşağıdaki işlemleri yönetir:
- Kullanıcı bağlantı/kayıt işlemleri
- Kullanıcı sayısı takibi ve yayını
- Kullanıcı durumu değişiklikleri (online/offline)
- Bağlantı kesme işlemi ve temizlik

## Güvenlik En İyi Uygulamaları

1. **HTTPS Kullanımı**: Tüm iletişim HTTPS üzerinden şifrelenir.
2. **JWT Token Güvenliği**:
   - Sınırlı ömür (24 saat)
   - Token blacklist mekanizması
   - Kullanıcı başına bir aktif token
3. **Şifre Güvenliği**:
   - Şifreler hash'lenerek saklanır (pbkdf2:sha256)
   - Şifre doğrulaması güvenli fonksiyonlarla yapılır
4. **Ortam Değişkenleri**:
   - JWT_SECRET_KEY gibi hassas veriler ortam değişkenlerinden alınır
5. **Oturum Yönetimi**:
   - Aynı kullanıcı farklı yerden giriş yaptığında eski oturum sonlandırılır
   - Aktif olmayan bağlantılar temizlenir

## WebSocket Test Arayüzü

```
+----------------------------------+
|      WebSocket JWT Test          |
+----------------------------------+
|                                  |
| [Connection] [Testing] [Debug]   |
|                                  |
| JWT Token: [----------------]    |
| Username:  [----------------]    |
|                                  |
| [x] Ignore HTTPS certificate     |
|     errors                       |
|                                  |
| [Connect & Register] [Disconnect]|
|                                  |
| Status: Connected                |
|                                  |
| Messages:                        |
| [14:58:31] Connecting...         |
| [14:58:31] Connection established|
| [14:58:31] User registered       |
| [14:58:31] USER COUNT: 2 online  |
+----------------------------------+
```

Sistem, kolay test ve hata ayıklama için kapsamlı bir arayüz sunar:
- JWT login/register işlemleri
- WebSocket bağlantı yönetimi
- Olayları gönderme ve alma
- Debug bilgilerini görüntüleme
- Kullanıcı listesi ve sayısı takibi

## Sonuç

Bu Flask tabanlı WebSocket uygulaması, JWT kimlik doğrulama ve HTTPS ile güvenli gerçek zamanlı iletişim sağlar. Sistem, modern web uygulamalarının ihtiyaçlarını karşılayacak şekilde tasarlanmış olup, kullanıcı yönetimi, oturum güvenliği ve WebSocket protokolü entegrasyonu için eksiksiz bir örnek teşkil etmektedir.