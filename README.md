# Ultimate Tic-Tac-Toe Backend

A Flask-based backend server for Ultimate Tic-Tac-Toe, featuring AI opponents with different skill levels and strategies.

## 🎮 What is Ultimate Tic-Tac-Toe?

Ultimate Tic-Tac-Toe is a complex variant of the classic Tic-Tac-Toe game. The board consists of nine 3×3 Tic-Tac-Toe boards arranged in a 3×3 grid. To win, you need to win three small boards in a row, column, or diagonal.

## 🚀 Features

- RESTful API for game management
- Real-time gameplay with Flask-SocketIO
- Multiple AI agents with different strategies and difficulty levels
- User authentication and game history tracking
- Swiss tournament system for AI competitions

## 🛠️ Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/utictactoe-backend.git
   cd utictactoe-backend
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```

4. Set up environment variables:
   ```
   bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## 🏃‍♂️ Running the Server

### Development Mode

```bash
cd backend
python app.py
```

### Production Mode

```bash
cd backend
gunicorn --worker-class eventlet -w 1 app:app
```

Or using Docker:

```bash
docker-compose up -d
```