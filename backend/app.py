from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
from flask_jwt_extended import decode_token
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:YOUR_PASSWORD@localhost/chat_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-change-this'

db = SQLAlchemy(app)
CORS(app)

# ✅ IMPORTANT: threading mode for Windows stability
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

jwt = JWTManager(app)

# ------------------- MODELS -------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.Column(db.String(50), nullable=False)
    room = db.Column(db.String(50), nullable=False, default='general')


# ------------------- AUTH ROUTES -------------------

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'message': 'Username & Password required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username taken'}), 400

    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Registered successfully'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=username)
        return jsonify({'access_token': access_token}), 200

    return jsonify({'message': 'Invalid credentials'}), 401


# ------------------- SOCKET AUTH HELPERS -------------------

online_users = {}      # {room: set(usernames)}
sid_to_user = {}       # {sid: username}
user_to_sid = {}       # {username: sid}


def get_user_from_socket():
    """
    ✅ SocketIO handshake token auth:
    frontend should send: io(url, { auth: { token } })
    """
    try:
        token = request.args.get("token")  # fallback
        if not token:
            token = request.environ.get("HTTP_AUTHORIZATION")

        # ✅ Flask-SocketIO puts auth in request.environ sometimes
        # But easiest is to rely on request.args or socket auth.
        # We'll use request.headers too (polling).
        if not token:
            token = request.headers.get("Authorization")

        # If "Bearer <token>" format
        if token and token.startswith("Bearer "):
            token = token.split("Bearer ")[1]

        # ✅ BEST method (socket auth):
        # Flask-SocketIO stores auth in `request.environ['flask.socketio'].auth`
        sock = request.environ.get("flask.socketio")
        if sock and getattr(sock, "auth", None):
            if not token:
                token = sock.auth.get("token")

        if not token:
            return None

        decoded = decode_token(token)
        return decoded.get("sub")  # identity stored here

    except Exception:
        return None


# ------------------- SOCKET EVENTS -------------------

@socketio.on("connect")
def on_connect():
    username = get_user_from_socket()
    if not username:
        # ❌ Block unauthenticated socket connection
        return False

    sid_to_user[request.sid] = username
    user_to_sid[username] = request.sid

    emit("connected", {"message": f"Connected as {username}"})


@socketio.on('join')
def handle_join(data):
    username = get_user_from_socket()
    if not username:
        emit("error", {"message": "Unauthorized"})
        return

    room = data.get('room', 'general')
    join_room(room)

    if room not in online_users:
        online_users[room] = set()

    online_users[room].add(username)

    emit('online_users', {"room": room, "users": list(online_users[room])}, to=room)

    # ✅ Load last 50 messages
    messages = Message.query.filter_by(room=room).order_by(Message.timestamp.asc()).limit(50).all()
    for msg in messages:
        emit('message', {
            'user': msg.user,
            'message': msg.content,
            'timestamp': msg.timestamp.strftime('%H:%M'),
            'room': room
        })

    emit('message', {'user': 'System', 'message': f'{username} joined {room}!', 'room': room}, to=room)


@socketio.on('leave')
def handle_leave(data):
    username = get_user_from_socket()
    if not username:
        emit("error", {"message": "Unauthorized"})
        return

    room = data.get('room', 'general')
    leave_room(room)

    if room in online_users and username in online_users[room]:
        online_users[room].discard(username)

        if not online_users[room]:
            del online_users[room]
        else:
            emit('online_users', {"room": room, "users": list(online_users[room])}, to=room)

    emit('message', {'user': 'System', 'message': f'{username} left {room}', 'room': room}, to=room)


@socketio.on('message')
def handle_message(data):
    username = get_user_from_socket()
    if not username:
        emit("error", {"message": "Unauthorized"})
        return

    content = data.get('message', '').strip()
    room = data.get('room', 'general')

    if not content:
        return

    new_msg = Message(user=username, content=content, room=room)
    db.session.add(new_msg)
    db.session.commit()

    emit('message', {
        'user': username,
        'message': content,
        'timestamp': datetime.utcnow().strftime('%H:%M'),
        'room': room
    }, to=room)


@socketio.on('typing')
def handle_typing(data):
    username = get_user_from_socket()
    if not username:
        return

    room = data.get('room', 'general')
    emit('typing', {'user': username, 'room': room}, to=room, include_self=False)


@socketio.on('disconnect')
def handle_disconnect():
    username = sid_to_user.get(request.sid)
    if not username:
        return

    # ✅ Remove user from all rooms
    for room in list(online_users.keys()):
        if username in online_users[room]:
            online_users[room].discard(username)
            emit('online_users', {"room": room, "users": list(online_users[room])}, to=room)
            emit('message', {'user': 'System', 'message': f'{username} disconnected', 'room': room}, to=room)

            if not online_users[room]:
                del online_users[room]

    sid_to_user.pop(request.sid, None)
    user_to_sid.pop(username, None)


# ------------------- RUN -------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    socketio.run(app, debug=True, port=5000)
