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

**⚠️ IMPORTANTE**: Este proyecto ahora usa una infraestructura nginx centralizada. El archivo `docker-compose.yml` solo ejecuta el backend y se conecta a la red externa `app-network` donde el nginx central maneja el proxy y SSL.

```bash
cd backend
gunicorn --worker-class eventlet -w 1 app:app
```

O usando Docker:

```bash
# Asegúrate de que la red externa exista
docker network create app-network

# Ejecutar solo el backend
docker-compose up -d
```

Para configurar el nginx central, ve al repositorio `server-nginx` y sigue las instrucciones allí.

## 🏗️ Arquitectura de Deployment

Este proyecto forma parte de una infraestructura nginx centralizada:

- **Backend UTicTacToe**: Corre en puerto interno 5000, contenedor `utictactoe-backend`
- **Nginx Central**: Repositorio `server-nginx` maneja proxy, SSL y dominios
- **Red Compartida**: `app-network` conecta todos los servicios
- **Dominio**: `api.utictactoe.online` (manejado por nginx central)
- **WebSockets**: Soporte completo para Socket.IO a través del proxy nginx

Para cambios en la configuración de proxy, SSL o WebSockets, edita los archivos en el repositorio `server-nginx`.
