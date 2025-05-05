
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

## 2. Kimlik Doğrulama Sistemi (auth.py)

Kimlik doğrulama sistemi, hem REST API hem de WebSocket bağlantılarını güvenli hale getirmek için JWT (JSON Web Tokens) kullanır.

### Temel Bileşenler:

#### 2.1 JWT Yapılandırması
```python
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', ':D')
JWT_EXPIRATION_DELTA = timedelta(hours=24)
```

#### 2.2 Token Yönetimi
```python
BLACKLISTED_TOKENS = set()  # İptal edilmiş tokenları takip eder
USER_TOKENS = {}  # Kullanıcı adlarını aktif tokenlara eşler
```

#### 2.3 Temel Kimlik Doğrulama Fonksiyonları

- **Token Kara Listesi**: Çıkış yapılmış tokenların kullanımını engeller, bu şekilde kullanıcı eski tokeni kuullanıp servise erişmesi engellenir.
  
  ```python
  def is_token_blacklisted(token):
      return token in BLACKLISTED_TOKENS
  
  def add_token_to_blacklist(token):
      BLACKLISTED_TOKENS.add(token)
      return True
  ```

- **Kullanıcı Başına Tek Token Politikası**: Yeni giriş yapıldığında eski tokenları geçersiz kılar. Aynı anda birden fazla geçerli oturumun olmaması için eski token blackliste eklenir.
  ```python
  def invalidate_user_tokens(username):
      if username in USER_TOKENS:
          old_token = USER_TOKENS[username]
          if old_token:
              add_token_to_blacklist(old_token)
      return True
  ```

- **Korumalı Rota Dekoratörü**: Dekaratör kullanarak erişilen Endpoint için yetkilendirme kontrolü yapılır bunun için dekaratör algoritmasını seçtim bu şekilde argüman olarak gönderdiğim her türden veriyi ve verileri parse edip işledikten sonra çalışacak. 
- **Yetkisiz Durumunda**: Yetkisiz bir işlem durumunda dakoratör fonksiyonu kendi error mekanizmasıı kullanarak error handle edecek. 
  ```python
  @token_required
  def funciton(current_user):
      # data
  ```

#### 2.4 Kimlik Doğrulama Endpoint'leri

 
  - **Yeni Token Kayıt**: Oluşturulan JWT token USERS_TOKEN listesine kaydedilir.
  ```python
        USER_TOKENS[username] = token
  ```
  - **Giriş**: Kullanıcı verilerini DB sorgusuyla kontrol eder. Doğrulanmış kullanıcılar için JWT token oluşturur.
  ```python
  @app.route('/login-token', methods=['POST'])
  def login_token():
      # Kimlik bilgilerini doğrular ve JWT token döndürür
  ```

  - **Çıkış**: Kullanıcının JWT tokenini geçersiz kılar. Dekoratör kullanır ve kullanıcının çıkış yapmak için geçerli bir tokeni olup olmadığını kontrol eder. Token geçerli ise blackliste eklenir ve USER_TOKENS listesinden çıkartılır.
   
  ```python
  @app.route('/logout', methods=['POST'])
  @token_required
  def logout(current_user):
      # Tokenı geçersiz kılar
  ```

#### 2.5 Güvenlik Özellikleri

- Token sona erme süresi (24 saat)
- Tokeni iptal etmek için kara listeye alma
- Kullanıcı başına tek aktif token

## 3. Uygulama Çekirdeği (app.py)

#### 3.1 Uygulama Başlatılması
- DB ve Flask app nesnesi.
```python
app = create_app()  # SQLite yapılandırması ile Flask uygulaması oluşturur
```

#### 3.2 Kullanıcı için erişebileceği Endpoint Yapılandırmaları
```python
# login sayfası için
@app.route('/', methods=['GET'])

# login sayfasından sonra geçerli tokene sahip kullanıcılara açılan test sayfası.
@app.route('/socket', methods=['GET'])
@token_required
def serve_testpage(current_user):
    return send_from_directory('.', 'frontend/html/websockettest.html')
```

#### 3.3 HTTPS Yapılandırması

- HTTPS kullanarak Client ve Server arasındaki iletişim manüpülesinin önüne geçiliyor ve veriler erişilemeyecek şekilde şifreleniyor.
- HTTPS ile Önlenen bazı tehditler: Man-in-the-Middle Saldırıları, Şifrelenmemiş WebSocket bağlantıları (ws://), Sahte Sunucu Saldırıları, İçerik Enjeksiyonu.

```python
socketio.run(app, host='0.0.0.0', port=5000, debug=True, 
            certfile=cert_path, keyfile=key_path)
```

## 4. WebSocket Uygulaması (websocket.py)

JWT ile kullanıcı doğruluğunu yetkilendirme işlemlerini yapsam da anlık kullanıcı sistemini sürekli güncellemem gerektiği için websocket teknolijisinin uygun ve kolay uygulunabilir olduğunu düşündüm. Hem websocket SİD (oturum id) kullanarak hem de JWT token ile eş zamanlı kontrol yaparak sistemin manüpüle edilmesinin önüne geçtim.

### Temel Bileşenler:

#### 4.1 Bağlantı Yapılandırması Websocket oluşturma işlemi
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

#### 4.2 Bağlantı Yönetimi
- Tüm bağlanan kullanıcıların username ve benzersiz SİD (oturum id) bilgileri alınarak listede tutulur ve işlemler sırasında hem JWT hem de SİD kullanılarak kontrol edilir.
  
```python
connected_users = {}  # Kullanıcı adlarını oturum kimliklerine eşler
MAX_CONNECTIONS = 3  # İzin verilen maksimum eşzamanlı bağlantı sayısı
```

#### 4.3 WebSocket Kimlik Doğrulaması
- Websocker event driven olaylar şeklinde çalışır ve bu şekilde gönderilen her bir komut için istenilen fonksiyona eklenebilir. Websocket komutunun doğru çalışabilmesi için JWT kontrolü yapar. Blacklist durumunda kullanıcının bağlantısını keser.
  
```python
def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        # JWT kullanarak WebSocket olaylarını doğrular
    return wrapped
```

#### 4.4 WebSocket Olayları

- **Bağlantı**: Yeni istemci bağlantılarını yönetir, Handshake kısmı başlar.
  ```python
  @socketio.on('connect')
  def handle_connect():
      # Yeni bağlantıları işler ve istatistikleri günceller
  ```

- **Kullanıcı Kaydı**: WebSocket bağlantısını doğrulanmış kullanıcıyla ilişkilendirir. Doğrulama kısmı başlar ve kullanıcının JTW token kontrolü yapılır. Aynı kullanıcı tekrardan kayıt olmaya çalışırsa kullanıcının önceki oturumu kapatılır ve yenisi açılır.
  ```python
  @socketio.on('register_user')
  def register_user(data):
      # Kullanıcıyı doğrular ve bağlantı limitlerini yönetir
  ```

- **Bağlantı Kesme**: İstemciler bağlantıyı kestiğinde temizlik yapar. Çıkış yapan kullanıcı bağlı kullanıcılar listesinde ise o kullanıcının çıkışı yapılır.
  ```python
  @socketio.on('disconnect')
  def handle_disconnect(data=None):
      # Kullanıcıyı connected_users'dan kaldırır ve istatistikleri günceller
  ```

- **Kullanıcı Listesi**: Çevrimiçi kullanıcı listesi sağlar. Websocket ile bağlı kullanıcılara istedikleri veriyi verir. Bağlı kullanıcı listesini döner.
- **Örnek**:
    *[09:09:59] ÇEVRİMİÇİ KULLANICILAR: {"users":["user"],"count":1}
[09:09:59] ÇEVRİMİÇİ KULLANICI: 1 kullanıcı aktif*.

  ```python
  @socketio.on('get_online_users')
  @authenticated_only
  def get_online_users():
      # Bağlı kullanıcıların listesini döndürür
  ```

- **Ping/Pong**: Bağlantı sağlık kontrolü, kullanıcıya belirlenen aralıklarla "hala bağlı mısın" isteği gönderir, client ise bu isteğe pong yanıtıyla "hala bağlıyım" isteği gönderir.
  ```python
  @socketio.on('ping_manual')
  def handle_ping():
      # Sunucu zaman damgasıyla yanıt verir
  ```

#### 4.5 Güvenlik Özellikleri

- Bağlantı limiti uygulaması (MAX_CONNECTIONS = 3)
- Tüm kimlik doğrulamalı olaylar için JWT doğrulaması
- Aynı kullanıcı için birden fazla oturumun tespiti
- Yinelenen girişler için zorunlu bağlantı kesme

## 5. Frontend Uygulaması

### 5.1 Giriş Sayfası (login.html, login.js)

Eğer halihazırda Zaten giriş yapıldıysa otomatik yönlendirme yapılır.

```javascript
// Temel giriş işlevi
function login() {
    // Kullanıcıyı doğrular ve JWT token'ı saklar
    fetch('https://localhost:5000/login-token', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        localStorage.setItem('jwt_token', data.token);
        localStorage.setItem('username', data.user.username);
        // WebSocket test sayfasına yönlendir
    })
}
```

### 5.2 WebSocket Test Sayfası (websockettest.html, websocket.js)

- Gerçek zamanlı bağlantı durumu
- Kullanıcı listesi görüntüleme
- Bağlantı istatistikleri
- WebSocket işlemleri için komut düğmeleri

```javascript
function connectSocket() {
    socket = io(url, {
        auth: { token: token },
        transports: ["websocket"],
        secure: true
    });

    socket.on("connect", () => {
        // Kullanıcıyı token ile kaydet
        socket.emit("register_user", {
            token: token,
            username: username
        });
    });

    // Çeşitli soket olaylarını işle
    socket.on("response", (data) => { /* ... */ });
    socket.on("user_status", (data) => { /* ... */ });
    socket.on("connection_slots", (data) => { /* ... */ });
    // vb.
}
```

## 6. Güvenlik Değerlendirmeleri

1. **HTTPS**: Tüm iletişim TLS ile şifrelenir
2. **JWT Kimlik Doğrulama**: Hem HTTP hem de WebSocket bağlantılarını güvence altına alır
3. **Token Kara Listesi**: Çıkış yapılmış tokenları hemen geçersiz kılar
4. **Oturum Yönetimi**: Kullanıcı başına bir aktif token, eski oturumların bağlantısını keser
5. **Potansiyel bir DoS (Denial of Service)** vektörü olabilir (birden fazla kullanıcı ), ancak korunuyor çünkü tüm bağlantılar JWT doğrulamasına tabi

## 7. Dağıtım

- Docker ve Docker-compose ile öncesinde bir kurulum yapmadan sadece docker yüklü tüm cihazlarda çalışır.
- sadece imaj halindeki docker paylaşılarak kaynak kodlara gerek kalmadan canlı ortama sunulabilir.

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
      - EVENTLET_NO_GREENDNS=YES
```

## 8. Geliştirilebilecek kısımlar

- Nginx kullanılarak self signed imzalı ssl sertifikasının tarayıcı tarafından yarattığı hata mesajları çözülebilir.
- Detaylı bir Log mekanizması koyulabilir.
- Rate limit önlemi koyulabilir, böylece belli bir süre içinde sistemi kötü niyetle çözmeye çalışanlar yavaşlatılabilir.
- Kötü niyet kısmında eğer dışarı açık ağ var ise mail servisi ile lisans sahibi firmaya haber verilebilir.
- Docker secret kullanılabilir böylece .env durumundan kurtulunur.
