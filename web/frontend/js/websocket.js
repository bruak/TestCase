let socket;
let statusCheckInterval;

// Sayfanın yüklenme anında çalışacak fonksiyon
document.addEventListener('DOMContentLoaded', function() {
  // Başlangıçta sunucu durumunu kontrol et ve düzenli aralıklarla tekrarla
  checkServerStatus();
  // Her 1 saniyede bir sunucu durumunu kontrol et
  statusCheckInterval = setInterval(checkServerStatus, 100000);
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



function connectSocket() { // ! ITS FOR TESTING
  let token = document.getElementById("token").value;
  let username = document.getElementById("username").value;
  
  // If token or username is missing, use the saved token
  if (!token || !username) {
    // Load the predefined token and extract username
    const tokenValue = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InVzZXIyIiwiZXhwIjoxNzQ2Mzc0NzQ5LCJpYXQiOjE3NDYyODgzNDksInVzZXJfaWQiOjEyfQ.YqymYpVWg7laFLV6Cb7c1c9V980PD2Tq0F3hU0WE4hk";
    
    if (!token) {
      token = tokenValue;
      document.getElementById("token").value = token;
      logMessage("Using default token");
    }
    
    if (!username) {
      try {
        // Decode token payload (2nd part of JWT)
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.username) {
          username = payload.username;
          document.getElementById("username").value = username;
          logMessage(`Using username from token: ${username}`);
        } else {
          logMessage("Username not found in token", true);
          return;
        }
      } catch (error) {
        logMessage(`Error parsing token: ${error.message}`, true);
        return;
      }
    }
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
    });

    socket.on("connect_error", (err) => {
      logMessage(`Connection error: ${err.message}`, true);
    });

    socket.on("error", (err) => {
      logMessage(`Socket error: ${err.message}`, true);
    });
    
    socket.on("debug_info", (data) => {
      logMessage(`DEBUG INFO: ${JSON.stringify(data, null, 2)}`);
    });
    
    socket.on("force_disconnect", (data) => {
      logMessage(`Forced disconnect: ${JSON.stringify(data)}`);
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

function savedToken() {
    // Predefined token for user2
    const tokenValue = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InVzZXIyIiwiZXhwIjoxNzQ2Mzc0NzQ5LCJpYXQiOjE3NDYyODgzNDksInVzZXJfaWQiOjEyfQ.YqymYpVWg7laFLV6Cb7c1c9V980PD2Tq0F3hU0WE4hk";
    
    // Fill the token field
    document.getElementById("token").value = tokenValue;
    
    // Extract username from token and fill the username field
    try {
        // Decode token payload (2nd part of JWT)
        const payload = JSON.parse(atob(tokenValue.split('.')[1]));
        if (payload.username) {
            document.getElementById("username").value = payload.username;
            logMessage(`Username auto-filled from token: ${payload.username}`);
        }
    } catch (error) {
        console.error("Error parsing token:", error);
    }
    
    logMessage("Default token loaded automatically");
    
    // Automatically connect using this token
    connectSocket();
}