from gevent import monkey
monkey.patch_all()

import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from api.bots import bot_routes
from api.auth import auth_routes
from api.online import online_routes
from socketio_instance import socketio
from database import test_connection, init_database

load_dotenv()

# Test database connection and initialize database at startup
test_connection()
init_database()

app = Flask(__name__)
app.config.from_object(Config)  
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

CORS(app, resources={r"/*": {"origins": [
    "http://localhost:3000",
    "https://www.utictactoe.online",
    "https://utictactoe.online",
    "https://utictactoe.vercel.app"
]}})

jwt = JWTManager(app)

@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({"message": "Missing or invalid token."}), 401

@jwt.expired_token_loader
def expired_token_response(jwt_header, jwt_payload):
    return jsonify({"message": "Token has expired."}), 401

app.register_blueprint(bot_routes)
app.register_blueprint(auth_routes)
app.register_blueprint(online_routes)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify(status="healthy"), 200

@app.errorhandler(Exception)
def handle_exception(e):
    response = {
        "message": "An unexpected error occurred.",
        "details": str(e)
    }
    return jsonify(response), 500

socketio.init_app(app, cors_allowed_origins="*")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, use_reloader=False)
