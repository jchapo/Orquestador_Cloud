#!/usr/bin/env python3
import socket
import subprocess
import os
import sys

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 3080))
    server_socket.listen(5)
    print("Servidor iniciado en puerto 3080")
    
    while True:
        print("Esperando conexión...")
        client_socket, address = server_socket.accept()
        print(f"Conexión desde {address}")
        
        # Redireccionar stdin/stdout
        stdin_fd = os.dup(0)
        stdout_fd = os.dup(1)
        stderr_fd = os.dup(2)
        
        os.dup2(client_socket.fileno(), 0)
        os.dup2(client_socket.fileno(), 1)
        os.dup2(client_socket.fileno(), 2)
        
        try:
            # Ejecutar la aplicación
            subprocess.run(["python", "/app/app.py"])
        except Exception as e:
            error_msg = f"Error: {e}"
            client_socket.send(error_msg.encode())
        finally:
            # Restaurar stdin/stdout
            os.dup2(stdin_fd, 0)
            os.dup2(stdout_fd, 1)
            os.dup2(stderr_fd, 2)
            client_socket.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Servidor detenido")
        sys.exit(0)
