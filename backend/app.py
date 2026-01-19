from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:YOUR_PASSWORD@localhost/chat_app'  # Change password
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-change-this'  # Change kar

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)
jwt = JWTManager(app)

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

# Auth Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username taken'}), 400
    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=username)
        return jsonify({'access_token': access_token})
    return jsonify({'message': 'Invalid credentials'}), 401

# SocketIO Events
online_users = {}  # {room: set(users)}

@socketio.on('join')
@jwt_required()
def handle_join(data):
    username = get_jwt_identity()
    room = data.get('room', 'general')
    join_room(room)
    
    # Update online users
    if room not in online_users:
        online_users[room] = set()
    online_users[room].add(username)
    emit('online_users', list(online_users[room]), to=room)
    
    # Load last 50 messages for the room
    messages = Message.query.filter_by(room=room).order_by(Message.timestamp.asc()).limit(50).all()
    for msg in messages:
        emit('message', {
            'user': msg.user,
            'message': msg.content,
            'timestamp': msg.timestamp.strftime('%H:%M')
        })
    emit('message', {'user': 'System', 'message': f'{username} joined {room}!'}, to=room)

@socketio.on('leave')
@jwt_required()
def handle_leave(data):
    username = get_jwt_identity()
    room = data.get('room', 'general')
    leave_room(room)
    if room in online_users:
        online_users[room].discard(username)
        if not online_users[room]:
            del online_users[room]
        else:
            emit('online_users', list(online_users[room]), to=room)
    emit('message', {'user': 'System', 'message': f'{username} left {room}'}, to=room)

@socketio.on('message')
@jwt_required()
def handle_message(data):
    username = get_jwt_identity()
    content = data['message']
    room = data['room']
    if content.strip():
        new_msg = Message(user=username, content=content, room=room)
        db.session.add(new_msg)
        db.session.commit()
        emit('message', {
            'user': username,
            'message': content,
            'timestamp': datetime.utcnow().strftime('%H:%M')
        }, to=room)

@socketio.on('typing')
@jwt_required()
def handle_typing(data):
    username = get_jwt_identity()
    room = data['room']
    emit('typing', {'user': username}, to=room, include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    # Clean up online users (simple way, might not be perfect but works)
    for room in list(online_users.keys()):
        users_to_remove = [user for user in online_users[room] if user == request.sid]  # Approximate by sid
        for user in users_to_remove:
            online_users[room].discard(user)
            emit('online_users', list(online_users[room]), to=room)
            emit('message', {'user': 'System', 'message': f'{user} disconnected'}, to=room)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, port=5000)
