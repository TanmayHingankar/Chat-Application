import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import axios from 'axios';
import jwt_decode from 'jwt-decode';
import './App.css';

const socket = io('http://localhost:5000', { autoConnect: false });

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [room, setRoom] = useState('general');
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [typingUser, setTypingUser] = useState(null);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  useEffect(() => {
    if (token) {
      socket.auth = { token };
      socket.connect();
      const decoded = jwt_decode(token);
      setUsername(decoded.identity);
    }
  }, [token]);

  useEffect(() => {
    socket.on('message', (data) => {
      setMessages((prev) => [...prev, data]);
    });
    socket.on('online_users', (users) => {
      setOnlineUsers(users);
    });
    socket.on('typing', (data) => {
      setTypingUser(data.user);
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = setTimeout(() => setTypingUser(null), 2000);
    });

    return () => {
      socket.off('message');
      socket.off('online_users');
      socket.off('typing');
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleAuth = async () => {
    try {
      const endpoint = isLogin ? '/login' : '/register';
      const res = await axios.post(`http://localhost:5000${endpoint}`, { username, password });
      if (res.data.access_token) {
        localStorage.setItem('token', res.data.access_token);
        setToken(res.data.access_token);
      }
    } catch (err) {
      alert(err.response?.data?.message || 'Error');
    }
  };

  const joinRoom = (newRoom) => {
    if (newRoom !== room) {
      socket.emit('leave', { room });
      setMessages([]);
      setRoom(newRoom);
      socket.emit('join', { room: newRoom });
    }
  };

  const sendMessage = () => {
    if (message.trim()) {
      socket.emit('message', { message, room });
      setMessage('');
    }
  };

  const handleTyping = (e) => {
    setMessage(e.target.value);
    socket.emit('typing', { room });
  };

  if (!token) {
    return (
      <div className="auth-container">
        <h2>{isLogin ? 'Login' : 'Register'}</h2>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button onClick={handleAuth}>{isLogin ? 'Login' : 'Register'}</button>
        <p onClick={() => setIsLogin(!isLogin)}>
          {isLogin ? 'Need to register?' : 'Already have account?'}
        </p>
      </div>
    );
  }

  return (
    <div className="chat-container">
      <h1>Real-Time Chat App - {username}</h1>
      <div className="sidebar">
        <h3>Rooms</h3>
        <button onClick={() => joinRoom('general')}>General</button>
        <button onClick={() => joinRoom('tech')}>Tech</button>
        <button onClick={() => joinRoom('fun')}>Fun</button>
        <h3>Online in {room}: {onlineUsers.length}</h3>
        <ul>
          {onlineUsers.map((user, i) => <li key={i}>{user}</li>)}
        </ul>
      </div>
      <div className="main-chat">
        <div className="chat-box">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${msg.user === username ? 'my-message' : 'other-message'}`}
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
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type a message..."
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;
