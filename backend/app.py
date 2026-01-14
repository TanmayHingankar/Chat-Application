from flask import Flask
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = '4c1383f75c466bc9c07bac246f4b3cdf607f7f393f2dec7e3d24bd06bfbee10d'  # Change kar de
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:Manthan%4012@localhost/chat_app"
  

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.Column(db.String(50), nullable=False)

@socketio.on('join')
def handle_join(data):
    user = data['user']
    # Load last 50 messages from DB
    messages = Message.query.order_by(Message.timestamp.asc()).limit(50).all()
    for msg in messages:
        emit('message', {
            'user': msg.user,
            'message': msg.content,
            'timestamp': msg.timestamp.strftime('%H:%M')
        })
    emit('message', {'user': 'System', 'message': f'{user} joined the chat!'}, broadcast=True)

@socketio.on('message')
def handle_message(data):
    user = data['user']
    content = data['message']
    if content.strip():
        new_msg = Message(user=user, content=content)
        db.session.add(new_msg)
        db.session.commit()
        emit('message', {
            'user': user,
            'message': content,
            'timestamp': datetime.utcnow().strftime('%H:%M')
        }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tables bana dega pehli baar
    socketio.run(app, debug=True, port=5000)