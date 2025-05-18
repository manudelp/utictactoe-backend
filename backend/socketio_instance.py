from flask_socketio import SocketIO

# Explicitly list all allowed origins
allowed_origins = [
    "http://localhost:3000",
    "https://www.utictactoe.online",
    "https://utictactoe.online", 
    "https://utictactoe.vercel.app"
]

# For Python 3.13 compatibility, we don't specify async_mode='eventlet'
socketio = SocketIO(
    cors_allowed_origins=allowed_origins,
    engineio_logger=True  # For debugging, can remove in production
)
