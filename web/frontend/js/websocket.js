let socket;
let statusCheckInterval;

// Sayfanın yüklenme anında çalışacak fonksiyon
document.addEventListener('DOMContentLoaded', function() {
  // Token kontrolü
  const token = localStorage.getItem('jwt_token');
  const username = localStorage.getItem('username');

  // Başlangıçta sunucu durumunu kontrol et ve düzenli aralıklarla tekrarla
  checkServerStatus();
  // Her 1 saniyede bir sunucu durumunu kontrol et
  statusCheckInterval = setInterval(checkServerStatus, 100000);

  if (token && username) {
    connectSocket();
  } else if (localStorage.getItem('socket_connect_flag') === 'true') {
    localStorage.removeItem('socket_connect_flag');
    connectSocket();
  }
});

function checkServerStatus() {
  const url = "https://localhost:5000";
  
  fetch(url, { 
    method: 'GET'
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    updateServerStatus(true);
    return response;
  })
  .catch(error => {
    updateServerStatus(false);
    console.error("Server connection test failed:", error);
  });
}

// Sunucu durumu göstergesini güncelle
function updateServerStatus(isOnline) {
  const statusElem = document.getElementById("serverStatus");
  if (!statusElem) {
    // Eğer element yoksa (örneğin login sayfasındayız) sessizce çık
    console.log("Server status element not found, skipping update");
    return;
  }
  if (isOnline) {
    statusElem.className = "server-status server-online";
    statusElem.textContent = "Sunucu Çalışıyor";
  } else {
    statusElem.className = "server-status server-offline";
    statusElem.textContent = "Sunucu Çalışmıyor";
  }
}

function logMessage(msg, isError = false) {
  const logBox = document.getElementById("log");
  const timestamp = new Date().toISOString().substring(11, 19);
  let message = `[${timestamp}] ${msg}`;

  if (!logBox) {
    console.error(msg);
    return;
  }
  
  if (isError) {
    message = `[${timestamp}] ERROR: ${msg}`;
  }
  
  logBox.textContent += message + "\n";
  logBox.scrollTop = logBox.scrollHeight;
}

function clearLog() {
  document.getElementById("log").textContent = "";
}

// Add these functions to update the connection statistics
function updateConnectionStats(data) {
  document.getElementById('remainingSlots').textContent = data.remaining_slots;
  document.getElementById('connectionLimits').textContent = data.connection_limits;
  document.getElementById('activeConnections').textContent = data.count;
}

function updateConnectedUsers(data) {
  const usersContainer = document.getElementById('connectedUsers');
  
  usersContainer.innerHTML = '';
  
  let usersList = [];
  
  if (Array.isArray(data)) {
    usersList = data;
  } 

  else if (data && Array.isArray(data.users)) {
    usersList = data.users.map(username => ({ user: username, status: 'online' }));
  }
  
  if (!usersList || usersList.length === 0) {
    usersContainer.innerHTML = '<li class="empty-list">Henüz bağlı kullanıcı yok</li>';
    return;
  }
  
  usersList.forEach(user => {
    const userItem = document.createElement('li');
    
    if (typeof user === 'string') {
      userItem.classList.add('user-online');
      userItem.textContent = user;
    } else {
      userItem.classList.add(user.status === 'online' ? 'user-online' : 'user-offline');
      userItem.textContent = user.username || user.user || 'Anonim Kullanıcı';
    }
    
    usersContainer.appendChild(userItem);
  });
}

function connectSocket() {
  let token = localStorage.getItem('jwt_token');
  let username = localStorage.getItem('username');

  
  if (!token || !username) {
    logMessage("Oturum bilgisi bulunamadı. Lütfen giriş yapın.", true);
    setTimeout(() => {
      window.location.href = '/';
    }, 1500);
    return;
  }

  logMessage(`${username} kullanıcısı için WebSocket bağlantısı kuruluyor...`);
  
  const url = "https://localhost:5000";
  
  try {
    if (socket) {
      socket.disconnect();
    }
    
    socket = io(url, {
      auth: {
        token: token
      },
      transports: ["websocket"],
      secure: true
    });

    socket.on("connect", () => {
      logMessage("WebSocket bağlantısı kuruldu!");
      updateServerStatus(true);
      
      socket.emit("register_user", {
        token: token,
        username: username
      });
      
      logMessage(`${username} için register_user olayı gönderildi`);
    });

    socket.on("response", (data) => {
      logMessage(`YANIT: ${JSON.stringify(data)}`);
    });

    socket.on("user_status", (data) => {
      logMessage(`KULLANICI DURUMU: ${JSON.stringify(data)}`);
      getUserList();
    });
    
    socket.on("user_count", (data) => {
      logMessage(`ÇEVRİMİÇİ KULLANICI: ${data.count} kullanıcı aktif`);
    });
    
    socket.on("connection_slots", (data) => {
      logMessage(`BAĞLANTI SLOTLARI: ${JSON.stringify(data)}`);
      updateConnectionStats(data);
    });

    socket.on("disconnect", () => {
      logMessage("WebSocket bağlantısı kesildi");
    });

    socket.on("connect_error", (err) => {
      logMessage(`Bağlantı hatası: ${err.message}`, true);
    });

    socket.on("error", (err) => {
      logMessage(`Socket hatası: ${err.message}`, true);
    });
    
    socket.on("debug_info", (data) => {
      logMessage(`HATA AYIKLAMA BİLGİSİ: ${JSON.stringify(data, null, 2)}`);
    });
    
    socket.on("force_disconnect", (data) => {
      logMessage(`Zorunlu bağlantı kesme: ${JSON.stringify(data)}`);
      localStorage.removeItem('jwt_token');
      localStorage.removeItem('username');
      localStorage.removeItem('user_id');
      
      setTimeout(() => {
        window.location.href = '/';
      }, 1500);
    });
    
    socket.on("pong_manual", (data) => {
      logMessage(`PONG: ${JSON.stringify(data)}`);
    });
    
    socket.on("online_users", (data) => {
      logMessage(`ÇEVRİMİÇİ KULLANICILAR: ${JSON.stringify(data)}`);
      
      updateConnectedUsers(data);
      
      if (data && data.hasOwnProperty('count')) {
        logMessage(`ÇEVRİMİÇİ KULLANICI: ${data.count} kullanıcı aktif`);
      }
    });
    
  } catch (err) {
    logMessage(`Bağlantı oluşturma hatası: ${err.message}`, true);
  }
}

function disconnectSocket() {
  if (socket) {
    logMessage("Disconnecting from WebSocket server...");
    socket.disconnect();
    logOut();
  } else {
    logMessage("No active connection to disconnect", true);
  }
}

function pingServer() {
    if (!socket || !socket.connected) {
      logMessage("Not connected to server", true);
      return;
    }
    
    logMessage("Sending ping to server");
    socket.emit("ping_manual");
  }
  
function getUserList() {
  if (!socket || !socket.connected) {
    logMessage("Not connected to server", true);
    return;
  }
  
  logMessage("Requesting online users");
  socket.emit("get_online_users");
}

function testConnection() {
  const url = "https://localhost:5000";
  logMessage(`Testing connection to ${url}...`);
  
  fetch(url, { 
    method: 'GET'
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    logMessage(`Connection test succeeded! Status: ${response.status}`);
    updateServerStatus(true);
    return response.text();
  })
  .then(data => {
    logMessage(`Response size: ${data.length} bytes`);
  })
  .catch(error => {
    logMessage(`Connection test failed: ${error.message}`, true);
    updateServerStatus(false);
  });
}

function logOut() {
  logMessage("Oturum kapatılıyor...");
  
  const token = localStorage.getItem('jwt_token');
  
  if (!token) {
    logMessage("Oturum bilgisi bulunamadı", true);
    window.location.href = '/';
    return;
  }
  
  fetch(`https://localhost:5000/logout?token=${encodeURIComponent(token)}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      token: token,
      username: localStorage.getItem('username')
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`Çıkış başarısız: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    logMessage(`Sunucu yanıtı: ${data.message}`);
    
    // LocalStorage'dan kullanıcı verilerini temizleyelim
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('username');
    localStorage.removeItem('user_id');
    localStorage.removeItem('socket_connect_flag'); // Also clean up this flag
    
    logMessage("Çıkış başarılı! Login sayfasına yönlendiriliyorsunuz...");
    
    // Login sayfasına yönlendir
    setTimeout(() => {
      window.location.href = '/';
    }, 1500);
  })
  .catch(error => {
    logMessage(`Çıkış işlemi sırasında hata: ${error.message}`, true);
    // Hata oluşsa bile kullanıcıyı çıkış yapmış sayalım ve login sayfasına yönlendirelim
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('username');
    localStorage.removeItem('user_id');
    localStorage.removeItem('socket_connect_flag');
    
    setTimeout(() => {
      window.location.href = '/';
    }, 1500);
  });
}

