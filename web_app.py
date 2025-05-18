import os
import sys
import argparse
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import json
from modules.Authentication import AuthenticationModule
from topologia_app import app as topology_app
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.register_blueprint(topology_app, url_prefix='/topology')

auth_module = AuthenticationModule()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    try:
        result = auth_module.login(username, password)
        if result and 'token' in result:
            session['user_id'] = result['user']['id']
            session['username'] = result['user']['username']
            session['role'] = result['user']['role']
            session['token'] = result['token']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Credenciales inválidas")
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return render_template('login.html', error=f"Error de autenticación: {str(e)}")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    return render_template('dashboard.html', 
                           username=session.get('username'), 
                           role=session.get('role'))

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "running", "version": "1.0.0"})

# Crear directorio de templates si no existe
os.makedirs('templates', exist_ok=True)

# Crear templates básicos
with open('templates/login.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>PUCP PRIVATE CLOUD ORCHESTRATOR - Login</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { width: 400px; margin: 100px auto; background: white; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #333; }
        input[type="text"], input[type="password"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 3px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 3px; cursor: pointer; }
        button:hover { background: #45a049; }
        .error { color: red; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PUCP PRIVATE CLOUD ORCHESTRATOR</h1>
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
        <form action="/login" method="post">
            <input type="text" name="username" placeholder="Usuario" required>
            <input type="password" name="password" placeholder="Contraseña" required>
            <button type="submit">Iniciar sesión</button>
        </form>
    </div>
</body>
</html>
    ''')

with open('templates/dashboard.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>PUCP PRIVATE CLOUD ORCHESTRATOR - Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }
        .header { background-color: #333; color: white; padding: 15px; text-align: center; }
        .user-info { float: right; margin-right: 20px; color: white; }
        .container { width: 90%; margin: 20px auto; background: white; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .menu { display: flex; flex-wrap: wrap; }
        .menu-item { width: 200px; height: 150px; margin: 15px; padding: 20px; text-align: center; background-color: #007BFF; color: white; border-radius: 5px; cursor: pointer; display: flex; flex-direction: column; justify-content: center; transition: all 0.3s; }
        .menu-item:hover { background-color: #0056b3; transform: scale(1.05); }
        a { text-decoration: none; }
        .admin-only { background-color: #FF5722; }
        .admin-only:hover { background-color: #E64A19; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PUCP PRIVATE CLOUD ORCHESTRATOR</h1>
        <div class="user-info">
            Usuario: {{ username }} | Rol: {{ role }}
            <a href="/logout" style="color: white; margin-left: 15px;">Cerrar sesión</a>
        </div>
    </div>
    
    <div class="container">
        <h2>MENU PRINCIPAL</h2>
        <div class="menu">
            <a href="/topology">
                <div class="menu-item">
                    <h3>Administrador de topología de red</h3>
                </div>
            </a>
            
            {% if role == 'Administrador' %}
            <a href="/users">
                <div class="menu-item admin-only">
                    <h3>Gestión de Usuarios</h3>
                </div>
            </a>
            {% endif %}
            
            <a href="/settings">
                <div class="menu-item">
                    <h3>Configuración de Usuario</h3>
                </div>
            </a>
            
            {% if role == 'Administrador' %}
            <a href="/configuration">
                <div class="menu-item admin-only">
                    <h3>Configurar</h3>
                </div>
            </a>
            {% endif %}
            
            <a href="/slices">
                <div class="menu-item">
                    <h3>Listar slices</h3>
                </div>
            </a>
            
            {% if role == 'Administrador' %}
            <a href="/delete-slice">
                <div class="menu-item admin-only">
                    <h3>Borrar slice</h3>
                </div>
            </a>
            
            <a href="/availability-zone">
                <div class="menu-item admin-only">
                    <h3>Definir zona de disponibilidad</h3>
                </div>
            </a>
            {% endif %}
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='PUCP Private Cloud Orchestrator Web App')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=3080, help='Port to run the server on')
    args = parser.parse_args()
    
    print(f"Iniciando servidor web en {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True)
