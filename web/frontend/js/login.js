document.addEventListener('DOMContentLoaded', function() {
    checkServerStatus();
    
    const token = localStorage.getItem('jwt_token');
    const username = localStorage.getItem('username');
    
    if (token && username) {
        logMessage("Aktif oturumunuz bulunuyor, WebSocket Test sayfasına yönlendiriliyorsunuz...");
        setTimeout(() => {
            window.location.href = '/';
        }, 1500);
    }
    
    document.getElementById('password').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            login();
        }
    });
});

function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showMessage("Kullanıcı adı ve şifre boş olamaz!", true);
        return;
    }
    
    const loginButton = document.getElementById('loginButton');
    loginButton.disabled = true;
    loginButton.textContent = "Giriş yapılıyor...";
    
    showMessage("Giriş yapılıyor, lütfen bekleyin...");
    
    fetch('https://localhost:5000/login-token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Giriş başarısız: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        showMessage("Giriş başarılı! Yönlendiriliyorsunuz...");
        
        localStorage.setItem('jwt_token', data.token);
        localStorage.setItem('username', data.user.username);
        localStorage.setItem('user_id', data.user.user_id);
        
        document.getElementById('logSection').style.display = 'block';
        logMessage(`Giriş başarılı: ${data.message}`);
        logMessage(`Kullanıcı: ${data.user.username}`);
        logMessage(`Token geçerlilik süresi: ${data.expires_in} saniye`);
        
        setTimeout(() => {
            window.location.href = '/';
        }, 1500);
    })
    .catch(error => {
        showMessage(error.message, true);
        logMessage(error.message, true);
        loginButton.disabled = false;
        loginButton.textContent = "Giriş Yap";
    });
}

function showMessage(message, isError = false) {
    const messageElement = document.getElementById('message');
    messageElement.textContent = message;
    messageElement.className = isError ? 'alert error' : 'alert success';
    messageElement.style.display = 'block';
}