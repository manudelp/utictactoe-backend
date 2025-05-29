import os
import jwt
import psycopg2
from dotenv import load_dotenv
from supabase_client import get_supabase_client
from flask import abort

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

def get_connection():
    """Create and return a connection to the PostgreSQL database"""
    try:
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        return connection
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return None

def test_connection():
    """Test the database connection"""
    try:
        connection = get_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT NOW();")
            result = cursor.fetchone()
            print("Database connection successful! Current Time:", result)
            cursor.close()
            connection.close()
            
            # Also test Supabase connection
            try:
                supabase = get_supabase_client()
                response = supabase.table('users').select('*').limit(1).execute()
                print(f"Supabase connection successful! Retrieved {len(response.data)} records.")
                return True
            except Exception as e:
                print(f"Supabase connection failed: {e}")
                # Continue even if Supabase fails, since direct PostgreSQL works
                return True
        return False
    except Exception as e:
        print(f"Failed to test connection: {e}")
        return False

def init_database():
    """Initialize database tables if they don't exist"""
    try:
        connection = get_connection()
        if connection:
            cursor = connection.cursor()
            
            # Create users table if not exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            # Create game_history table if not exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                opponent_type VARCHAR(50) NOT NULL,
                opponent_name VARCHAR(255),
                result VARCHAR(10) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            connection.commit()
            print("Database tables initialized successfully.")
            cursor.close()
            connection.close()
            return True
        return False
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        return False

def register_user(email, password, name):
    """
    Register a new user using Supabase Auth
    
    Args:
        email (str): User's email
        password (str): User's password
        name (str): User's name
        
    Returns:
        dict: User data or None if registration failed
    """
    try:
        supabase = get_supabase_client()
        
        # Register user with Supabase Auth
        user_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if user_response.user and user_response.user.id:
            user_data = {
                "id": user_response.user.id,
                "name": name,
                "email": email
            }
            supabase.table('users').insert(user_data).execute()
            
            return user_response.user

        return None
    except Exception as e:
        print(f"Failed to register user: {e}")
        return None

def login_user(email, password):
    """
    Login user using Supabase Auth
    
    Args:
        email (str): User's email
        password (str): User's password
        
    Returns:
        tuple: (session, user) or (None, None) if login failed
    """
    try:
        supabase = get_supabase_client()
        
        # Sign in with email and password
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.session and response.user:
            # Get user user data
            user = supabase.table('users').select('*').eq('id', response.user.id).execute()
            
            user_data = {
                "id": response.user.id,
                "email": response.user.email,
                "name": user.data[0]['name'] if user.data else response.user.email
            }
            
            return response.session, user_data
        
        return None, None
    except Exception as e:
        print(f"Failed to login user: {e}")
        return None, None


def verify_token(token):
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded  # Validate further if needed
    except jwt.InvalidTokenError:
        abort(401)
