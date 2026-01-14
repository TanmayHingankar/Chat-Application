# RealTimeChatApp

A full-stack real-time chat application built with Flask (Python) backend and React (JavaScript) frontend. It supports user authentication, multiple chat rooms, real-time messaging, online user lists, typing indicators, and persistent message storage using MySQL.

This project demonstrates a modern chat app with secure authentication (JWT), real-time updates via WebSockets (Socket.IO), and a responsive UI. Messages are saved in a database for persistence across sessions.

## Features

- **User Authentication**: Register and login with username/password. JWT-based security.
- **Multiple Chat Rooms**: Join different rooms (e.g., General, Tech, Fun) with room-specific messages.
- **Real-Time Messaging**: Send and receive messages instantly with timestamp.
- **Online Users List**: See who is currently online in the active room.
- **Typing Indicator**: Displays "User is typing..." when someone is composing a message.
- **Message Persistence**: All messages are stored in MySQL database and loaded on room join (last 50 messages).
- **Responsive UI**: Chat bubbles, scrollable chat box, sidebar for rooms and online users.
- **Broadcast Notifications**: System messages for join/leave/disconnect events.

## Tech Stack

- **Backend**: Python 3.10+, Flask, Flask-SocketIO, Flask-SQLAlchemy, PyMySQL, Flask-CORS, Flask-JWT-Extended, Werkzeug (for password hashing), Eventlet.
- **Frontend**: React (Create React App), Socket.IO-Client, Axios (for API calls), JWT-Decode.
- **Database**: MySQL (for users and messages).
- **Other**: WebSockets for real-time communication.

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- MySQL server (e.g., via XAMPP or MySQL Community Server)
- Git (optional for cloning)

## Installation

1. **Clone the Repository**:
   ```
   git clone https://github.com/YOUR_USERNAME/RealTimeChatApp.git
   cd RealTimeChatApp
   ```

2. **Set Up MySQL Database**:
   - Start your MySQL server.
   - Create a database named `chat_app`:
     ```sql
     CREATE DATABASE chat_app;
     ```
   - Update the database URI in `backend/app.py` with your MySQL credentials (e.g., username: root, password: your_password).

3. **Backend Setup**:
   - Navigate to the backend folder:
     ```
     cd backend
     ```
   - Create a virtual environment:
     - Windows: `python -m venv venv` then `venv\Scripts\activate`
     - macOS/Linux: `python3 -m venv venv` then `source venv/bin/activate`
   - Install dependencies:
     ```
     pip install -r requirements.txt
     ```

4. **Frontend Setup**:
   - Navigate to the frontend folder:
     ```
     cd ../frontend
     ```
   - Install dependencies:
     ```
     npm install
     ```

## Usage

1. **Run the Backend**:
   - In the `backend` folder (with virtual env activated):
     ```
     python app.py
     ```
   - The server will run on `http://localhost:5000`. It will automatically create database tables on first run.

2. **Run the Frontend**:
   - In the `frontend` folder:
     ```
     npm start
     ```
   - The app will open in your browser at `http://localhost:3000`.

3. **How to Use the App**:
   - On load, you'll see a login/register form.
   - Register a new user or login with existing credentials.
   - Select a room from the sidebar (General, Tech, Fun).
   - Type and send messages – they'll appear in real-time.
   - See online users in the sidebar and typing indicators in the chat box.
   - Open multiple browser tabs/windows to simulate multiple users.

## Project Structure

```
RealTimeChatApp/
├── backend/
│   ├── app.py              # Main Flask application with API and SocketIO
│   └── requirements.txt    # Python dependencies
└── frontend/
    ├── public/
    │   └── index.html      # React entry point
    ├── src/
    │   ├── App.js          # Main React component (auth, chat logic)
    │   ├── App.css         # Styles for UI
    │   └── index.js        # ReactDOM render
    └── package.json        # Node dependencies
```

## Configuration

- **Secret Keys**: Update `SECRET_KEY` and `JWT_SECRET_KEY` in `backend/app.py` for production.
- **Database URI**: Customize `SQLALCHEMY_DATABASE_URI` in `backend/app.py`.
- **CORS**: Allowed all origins for development; restrict in production.
- **Rooms**: Hardcoded in frontend (General, Tech, Fun); can be extended dynamically.

## Troubleshooting

- **Database Connection Issues**: Ensure MySQL is running and credentials are correct.
- **CORS Errors**: If frontend can't connect, verify Flask-CORS setup.
- **Real-Time Not Working**: Check if SocketIO is connected (browser console).
- **Dependencies**: If errors, recreate virtual env and reinstall.

## Screenshots  


## Contributing

Feel free to fo<img width="1920" height="1080" alt="Screenshot 2026-01-14 140351" src="https://github.com/user-attachments/assets/c543d030-5ee1-475c-b46d-5559dddf2b2f" />
rk and submit pull requests. For major changes, open an issue first.
<img width="1920" height="1080" alt="Screenshot 2026-01-14 140242" src="https://github.com/user-attachments/assets/e58430f1-381b-4c60-9603-a324b8147c46" />

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (create one if needed).

## Acknowledgments

- Built with inspiration from real-time chat tutorials.
- Thanks to Flask, React, and Socket.IO communities.
