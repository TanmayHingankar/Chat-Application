import React, { useState, useEffect, useRef } from "react";
import io from "socket.io-client";
import axios from "axios";
import jwt_decode from "jwt-decode";
import "./App.css";

// ✅ keep it disconnected until token is set
const socket = io("http://localhost:5000", {
  autoConnect: false,
});

function App() {
  const [token, setToken] = useState(localStorage.getItem("access_token"));
  const [username, setUsername] = useState("");
  const [authUsername, setAuthUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLogin, setIsLogin] = useState(true);

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [room, setRoom] = useState("general");
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [typingUser, setTypingUser] = useState(null);

  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // ✅ connect socket after login
  useEffect(() => {
    if (token) {
      try {
        // ✅ Flask JWT identity is in sub
        const decoded = jwt_decode(token);
        setUsername(decoded.sub);

        // ✅ socket auth (backend reads from socket auth)
        socket.auth = { token };
        socket.connect();

        // ✅ join default room after connect
        socket.emit("join", { room: "general" });

      } catch (err) {
        console.log("Invalid token:", err);
        localStorage.removeItem("access_token");
        setToken(null);
      }
    }
  }, [token]);

  // ✅ socket listeners
  useEffect(() => {
    socket.on("connected", (data) => {
      console.log("Socket connected:", data);
    });

    socket.on("message", (data) => {
      setMessages((prev) => [...prev, data]);
    });

    socket.on("online_users", (data) => {
      // backend sends: {room, users}
      setOnlineUsers(data.users || []);
    });

    socket.on("typing", (data) => {
      setTypingUser(data.user);
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = setTimeout(() => setTypingUser(null), 2000);
    });

    socket.on("error", (data) => {
      console.log("Socket error:", data);
    });

    return () => {
      socket.off("connected");
      socket.off("message");
      socket.off("online_users");
      socket.off("typing");
      socket.off("error");
    };
  }, []);

  // ✅ auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ✅ login/register handler
  const handleAuth = async () => {
    try {
      const endpoint = isLogin ? "/login" : "/register";
      const res = await axios.post(`http://localhost:5000${endpoint}`, {
        username: authUsername,
        password,
      });

      // ✅ If register -> just show success
      if (!isLogin) {
        alert("Registered successfully! Now login.");
        setIsLogin(true);
        return;
      }

      // ✅ login returns access_token
      if (res.data.access_token) {
        localStorage.setItem("access_token", res.data.access_token);
        setToken(res.data.access_token);
      }
    } catch (err) {
      alert(err.response?.data?.message || "Error");
    }
  };

  // ✅ switch rooms
  const joinRoom = (newRoom) => {
    if (newRoom !== room) {
      socket.emit("leave", { room });
      setMessages([]);
      setRoom(newRoom);
      socket.emit("join", { room: newRoom });
    }
  };

  // ✅ send message
  const sendMessage = () => {
    if (message.trim()) {
      socket.emit("message", { message, room });
      setMessage("");
    }
  };

  // ✅ typing
  const handleTyping = (e) => {
    setMessage(e.target.value);
    socket.emit("typing", { room });
  };

  // ✅ logout
  const logout = () => {
    socket.disconnect();
    localStorage.removeItem("access_token");
    setToken(null);
    setUsername("");
    setMessages([]);
    setOnlineUsers([]);
    setRoom("general");
  };

  // ------------------- AUTH UI -------------------
  if (!token) {
    return (
      <div className="auth-container">
        <h2>{isLogin ? "Login" : "Register"}</h2>

        <input
          type="text"
          placeholder="Username"
          value={authUsername}
          onChange={(e) => setAuthUsername(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button onClick={handleAuth}>{isLogin ? "Login" : "Register"}</button>

        <p style={{ cursor: "pointer" }} onClick={() => setIsLogin(!isLogin)}>
          {isLogin ? "Need to register?" : "Already have account?"}
        </p>
      </div>
    );
  }

  // ------------------- CHAT UI -------------------
  return (
    <div className="chat-container">
      <h1>Real-Time Chat App - {username}</h1>

      <button onClick={logout} style={{ marginBottom: "10px" }}>
        Logout
      </button>

      <div className="sidebar">
        <h3>Rooms</h3>
        <button onClick={() => joinRoom("general")}>General</button>
        <button onClick={() => joinRoom("tech")}>Tech</button>
        <button onClick={() => joinRoom("fun")}>Fun</button>

        <h3>
          Online in {room}: {onlineUsers.length}
        </h3>

        <ul>
          {onlineUsers.map((user, i) => (
            <li key={i}>{user}</li>
          ))}
        </ul>
      </div>

      <div className="main-chat">
        <div className="chat-box">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${
                msg.user === username ? "my-message" : "other-message"
              }`}
            >
              <strong>{msg.user}: </strong>
              {msg.message}
              <span className="timestamp">{msg.timestamp}</span>
            </div>
          ))}

          {typingUser && <div className="typing">{typingUser} is typing...</div>}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <input
            type="text"
            value={message}
            onChange={handleTyping}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Type a message..."
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;
