let socket;
let statusCheckInterval;

// Sayfanın yüklenme anında çalışacak fonksiyon
document.addEventListener('DOMContentLoaded', function() {
  // Başlangıçta sunucu durumunu kontrol et ve düzenli aralıklarla tekrarla
  checkServerStatus();
  // Her 1 saniyede bir sunucu durumunu kontrol et
  statusCheckInterval = setInterval(checkServerStatus, 10000);
});

// Sunucu durumunu kontrol eden fonksiyon
function checkServerStatus() {
  const url = "https://localhost:5000";
  
  // Sunucu bağlantısı test ediliyor
  fetch(url, { 
    method: 'GET'
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    // Sunucu çalışıyor, durumu güncelle
    updateServerStatus(true);
    return response;
  })
  .catch(error => {
    // Sunucu çalışmıyor, durumu güncelle
    updateServerStatus(false);
    console.error("Server connection test failed:", error);
  });
}

// Sunucu durumu göstergesini güncelle
function updateServerStatus(isOnline) {
  const statusElem = document.getElementById("serverStatus");
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
  
  if (isError) {
    message = `[${timestamp}] ERROR: ${msg}`;
  }
  
  logBox.textContent += message + "\n";
  logBox.scrollTop = logBox.scrollHeight;
}

function clearLog() {
  document.getElementById("log").textContent = "";
}

function updateConnectionStatus(isConnected) {
  const statusElem = document.getElementById("connectionStatus");
  if (isConnected) {
    statusElem.className = "status connected";
    statusElem.textContent = "Status: Connected";
  } else {
    statusElem.className = "status disconnected";
    statusElem.textContent = "Status: Disconnected";
  }
}

function connectSocket() {
  const token = document.getElementById("token").value;
  const username = document.getElementById("username").value;
  
  if (!token) {
    logMessage("JWT token is required", true);
    return;
  }
  
  if (!username) {
    logMessage("Username is required", true);
    return;
  }

  logMessage("Connecting to WebSocket server...");
  
  const url = "https://localhost:5000";
  
  try {
    // Close any existing connection
    if (socket) {
      socket.disconnect();
    }
    
    // Create new connection
    socket = io(url, {
      auth: {
        token: token
      },
      transports: ["websocket"],
      secure: true
    });

    // Register connection events
    socket.on("connect", () => {
      logMessage("WebSocket connection established!");
      updateConnectionStatus(true);
      updateServerStatus(true);
      
      // Register user after connection
      socket.emit("register_user", {
        token: token,
        username: username
      });
      
      logMessage(`Sent register_user event for: ${username}`);
    });

    socket.on("response", (data) => {
      logMessage(`RESPONSE: ${JSON.stringify(data)}`);
    });

    socket.on("user_status", (data) => {
      logMessage(`USER STATUS: ${JSON.stringify(data)}`);
    });
    
    socket.on("user_count", (data) => {
      logMessage(`USER COUNT: ${data.count} users online`);
    });
    
    socket.on("connection_slots", (data) => {
      logMessage(`CONNECTION SLOTS: ${JSON.stringify(data)}`);
    });

    socket.on("disconnect", () => {
      logMessage("WebSocket disconnected");
      updateConnectionStatus(false);
    });

    socket.on("connect_error", (err) => {
      logMessage(`Connection error: ${err.message}`, true);
      updateConnectionStatus(false);
    });

    socket.on("error", (err) => {
      logMessage(`Socket error: ${err.message}`, true);
    });
    
    socket.on("debug_info", (data) => {
      logMessage(`DEBUG INFO: ${JSON.stringify(data, null, 2)}`);
    });
    
    socket.on("force_disconnect", (data) => {
      logMessage(`Forced disconnect: ${JSON.stringify(data)}`);
      updateConnectionStatus(false);
    });
    
    socket.on("pong_manual", (data) => {
      logMessage(`PONG: ${JSON.stringify(data)}`);
    });
    
    socket.on("online_users", (data) => {
      logMessage(`ONLINE USERS: ${JSON.stringify(data)}`);
    });
    
  } catch (err) {
    logMessage(`Error creating connection: ${err.message}`, true);
  }
}

function disconnectSocket() {
  if (socket) {
    logMessage("Disconnecting from WebSocket server...");
    socket.disconnect();
    updateConnectionStatus(false);
  } else {
    logMessage("No active connection to disconnect", true);
  }
}

function pingServer() {
  if (!socket || !socket.connected) {
    logMessage("Not connected to server", true);
    return;
  }
  
  try {
    logMessage("Sending ping to server");
    
    // Ping gönderildiğinde yanıt için bir timeout başlat
    const pingTimeout = setTimeout(() => {
      logMessage("Ping timeout - no response from server", true);
    }, 5000);
    
    // Ping olayını gönder ve yanıt bekle
    socket.emit("ping_manual", {}, (response) => {
      clearTimeout(pingTimeout);
      if (response && response.success) {
        logMessage(`Ping successful: ${JSON.stringify(response)}`);
      } else {
        logMessage(`Ping failed: ${JSON.stringify(response)}`, true);
      }
    });
    
    // Alternatif yanıt yöntemi (socket.on zaten mevcut)
  } catch (error) {
    logMessage(`Error during ping: ${error.message}`, true);
  }
}

function getUserList() {
  if (!socket || !socket.connected) {
    logMessage("Not connected to server", true);
    return;
  }
  
  try {
    logMessage("Requesting online users");
    
    // Kullanıcı listesi istediğinde yanıt için bir timeout başlat
    const userListTimeout = setTimeout(() => {
      logMessage("User list request timeout - no response from server", true);
    }, 5000);
    
    // Kullanıcı listesi olayını gönder ve yanıt bekle
    socket.emit("get_online_users", {}, (response) => {
      clearTimeout(userListTimeout);
      if (response && response.success) {
        logMessage(`User list received: ${JSON.stringify(response)}`);
      } else {
        logMessage(`Failed to get user list: ${JSON.stringify(response)}`, true);
      }
    });
    
    // Alternatif yanıt yöntemi (socket.on zaten mevcut)
  } catch (error) {
    logMessage(`Error during user list request: ${error.message}`, true);
  }
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