from flask_socketio import SocketIO
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('socketio')
logger.setLevel(logging.DEBUG)

# Explicitly list all allowed origins
allowed_origins = [
    "http://localhost:3000",
    "https://www.utictactoe.online",
    "https://utictactoe.online", 
    "https://utictactoe.vercel.app",
    "*"  # Allow all origins in development - remove in production
]

# Use threading mode instead of eventlet for Python 3.13 compatibility
socketio = SocketIO(
    cors_allowed_origins=allowed_origins,
    async_mode='threading',
    logger=True,
    engineio_logger=True
)

logger.info("SocketIO initialized with threading mode")
