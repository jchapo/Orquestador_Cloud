#!/usr/bin/env python3
"""
Servidor CLI para Cloud Orchestrator usando netcat
Este script gestiona las conexiones entrantes y proporciona una interfaz CLI
para interactuar con la aplicación.
"""

import socket
import threading
import subprocess
import os
import signal
import sys
import time
import logging
import queue
import json
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/opt/cloud-orchestrator/data/cli_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("cli_server")

# Cola de tareas (implementación simple)
task_queue = queue.Queue()
active_sessions = {}
session_counter = 0
session_lock = threading.Lock()

class TaskWorker(threading.Thread):
    """Procesa tareas de la cola"""
    
    def __init__(self, task_queue):
        threading.Thread.__init__(self, daemon=True)
        self.task_queue = task_queue
        self.running = True
    
    def run(self):
        while self.running:
            try:
                # Obtener una tarea de la cola con timeout
                task = self.task_queue.get(timeout=1.0)
                logger.info(f"Procesando tarea: {task['type']}")
                
                if task['type'] == 'create_topology':
                    self.execute_task(task)
                elif task['type'] == 'delete_topology':
                    self.execute_task(task)
                    
                # Marcar tarea como completada
                self.task_queue.task_done()
                
            except queue.Empty:
                # Sin tareas, continuar esperando
                pass
            except Exception as e:
                logger.error(f"Error procesando tarea: {e}")
    
    def execute_task(self, task):
        """Ejecuta una tarea basada en su tipo"""
        try:
            # Registrar inicio
            task['start_time'] = datetime.now().isoformat()
            task['status'] = 'running'
            
            # Ejecutar el comando apropiado basado en el tipo de tarea
            if task['type'] == 'create_topology':
                # Simular tiempo de ejecución (reemplazar por código real)
                time.sleep(2)
                logger.info(f"Topología {task['params']['topology_type']} creada exitosamente")
                task['status'] = 'completed'
                task['result'] = {'success': True}
                
            elif task['type'] == 'delete_topology':
                # Simular tiempo de ejecución (reemplazar por código real)
                time.sleep(1)
                logger.info(f"Topología {task['params']['topology_id']} eliminada exitosamente")
                task['status'] = 'completed'
                task['result'] = {'success': True}
            
            # Registrar finalización
            task['end_time'] = datetime.now().isoformat()
            
            # Notificar al cliente si hay un socket asociado
            if 'client_socket' in task and task['client_socket'] is not None:
                try:
                    message = f"\n[Tarea completada] {task['type']}: {task['result']}\n"
                    task['client_socket'].send(message.encode())
                except:
                    logger.error("No se pudo notificar al cliente de la finalización")
            
        except Exception as e:
            logger.error(f"Error ejecutando tarea {task['type']}: {e}")
            task['status'] = 'failed'
            task['error'] = str(e)
            task['end_time'] = datetime.now().isoformat()

class ClientHandler:
    """Maneja una conexión de cliente"""
    
    def __init__(self, client_socket, client_address, session_id):
        self.client_socket = client_socket
        self.client_address = client_address
        self.session_id = session_id
        self.authenticated = False
        self.user_id = None
        self.user_name = None
        self.running = True
        
        # Marcador para seguir si el cliente está en el app.py o topologia_app.py
        self.in_application = False
        self.current_app = None
        self.app_process = None
    
    def handle(self):
        """Maneja la conexión"""
        logger.info(f"Nueva conexión de {self.client_address}, sesión {self.session_id}")
        
        try:
            # Manejar autenticación
            if not self.authenticate():
                return
            
            # Mostrar menú principal
            while self.running:
                self.show_menu()
                
        except BrokenPipeError:
            logger.info(f"Cliente {self.session_id} desconectado")
        except Exception as e:
            logger.error(f"Error en sesión {self.session_id}: {e}")
        finally:
            try:
                if self.app_process:
                    # Terminar proceso de aplicación si está en ejecución
                    self.app_process.terminate()
                    logger.info(f"Terminado proceso de aplicación para sesión {self.session_id}")
                
                self.client_socket.close()
                logger.info(f"Conexión cerrada para sesión {self.session_id}")
                
                # Eliminar sesión
                with session_lock:
                    if self.session_id in active_sessions:
                        del active_sessions[self.session_id]
                        
            except Exception as e:
                logger.error(f"Error cerrando sesión {self.session_id}: {e}")
    
    def authenticate(self):
        """Autenticación básica por ahora, mejorar según necesidades"""
        # Enviar banner de bienvenida
        welcome = "\n" + "=" * 60 + "\n"
        welcome += "         CLOUD ORCHESTRATOR - ACCESO A CONSOLA\n"
        welcome += "=" * 60 + "\n\n"
        welcome += "Por favor inicie sesión para continuar.\n"
        
        self.client_socket.send(welcome.encode())
        
        # En un sistema real, conectar con base de datos
        # Por ahora, aceptar cualquier usuario/contraseña
        self.client_socket.send("Usuario: ".encode())
        username = self.recv_line().strip()
        
        if not username:
            self.client_socket.send("Nombre de usuario requerido.\n".encode())
            return False
        
        self.client_socket.send("Contraseña: ".encode())
        password = self.recv_line().strip()
        
        # En sistema real, verificar credenciales en DB
        # Por ahora, simplemente aceptar cualquier credencial no vacía
        if not password:
            self.client_socket.send("Contraseña requerida.\n".encode())
            return False
        
        # Simulando verificación (reemplazar con verificación real)
        time.sleep(1)
        
        self.authenticated = True
        self.user_id = 1  # ID ficticio
        self.user_name = username
        
        self.client_socket.send(f"\nBienvenido, {username}!\n\n".encode())
        return True
        
    def show_menu(self):
        """Muestra el menú principal y procesa la selección"""
        if self.in_application:
            # Si ya está en una aplicación, no mostrar menú
            return
            
        menu = "\nMENÚ PRINCIPAL - CLOUD ORCHESTRATOR\n"
        menu += "-" * 40 + "\n"
        menu += "1. Iniciar Administrador de Topologías\n"
        menu += "2. Iniciar Aplicación Principal\n"
        menu += "3. Ver estado de tareas\n"
        menu += "4. Salir\n"
        menu += "-" * 40 + "\n"
        menu += "Seleccione una opción: "
        
        self.client_socket.send(menu.encode())
        choice = self.recv_line().strip()
        
        if choice == "1":
            self.run_topology_app()
        elif choice == "2":
            self.run_main_app()
        elif choice == "3":
            self.show_task_status()
        elif choice == "4":
            self.running = False
            self.client_socket.send("¡Hasta pronto!\n".encode())
        else:
            self.client_socket.send("Opción no válida. Intente de nuevo.\n".encode())
    
    def run_topology_app(self):
        """Ejecuta la aplicación de topología"""
        self.in_application = True
        self.current_app = "topologia_app.py"
        
        try:
            # Iniciar subproceso para la aplicación
            cmd = ["python3", "/opt/cloud-orchestrator/topologia_app.py"]
            
            # Crear el proceso con redirección de entrada/salida
            self.app_process = subprocess.Popen(
                cmd, 
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Crear hilos para manejar entrada/salida
            threading.Thread(target=self.process_output, daemon=True).start()
            threading.Thread(target=self.process_input, daemon=True).start()
            
            logger.info(f"Sesión {self.session_id} inició {self.current_app}")
            
        except Exception as e:
            self.in_application = False
            self.current_app = None
            logger.error(f"Error iniciando aplicación de topología: {e}")
            self.client_socket.send(f"Error iniciando aplicación: {e}\n".encode())
    
    def run_main_app(self):
        """Ejecuta la aplicación principal"""
        self.in_application = True
        self.current_app = "app.py"
        
        try:
            # Iniciar subproceso para la aplicación
            cmd = ["python3", "/opt/cloud-orchestrator/app.py"]
            
            # Crear el proceso con redirección de entrada/salida
            self.app_process = subprocess.Popen(
                cmd, 
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Crear hilos para manejar entrada/salida
            threading.Thread(target=self.process_output, daemon=True).start()
            threading.Thread(target=self.process_input, daemon=True).start()
            
            logger.info(f"Sesión {self.session_id} inició {self.current_app}")
            
        except Exception as e:
            self.in_application = False
            self.current_app = None
            logger.error(f"Error iniciando aplicación principal: {e}")
            self.client_socket.send(f"Error iniciando aplicación: {e}\n".encode())
    
    def process_output(self):
        """Procesa la salida de la aplicación y la envía al cliente"""
        try:
            for line in iter(self.app_process.stdout.readline, ''):
                if self.running:
                    self.client_socket.send(line.encode())
                else:
                    break
                    
            # Si llegamos aquí, la aplicación terminó
            if self.running:
                self.client_socket.send("\nLa aplicación ha terminado. Volviendo al menú principal.\n".encode())
            
            self.in_application = False
            self.current_app = None
            self.app_process = None
            
        except BrokenPipeError:
            logger.info(f"Cliente {self.session_id} desconectado durante ejecución de aplicación")
            self.running = False
        except Exception as e:
            logger.error(f"Error procesando salida de aplicación: {e}")
            self.running = False
    
    def process_input(self):
        """Procesa la entrada del cliente y la envía a la aplicación"""
        try:
            while self.running and self.in_application:
                # Leer entrada del cliente
                user_input = self.recv_line()
                
                # Verificar si el usuario quiere salir
                if user_input.strip().lower() in ['exit', 'quit', 'salir']:
                    # Terminar la aplicación
                    if self.app_process:
                        self.app_process.terminate()
                    
                    self.in_application = False
                    self.current_app = None
                    self.client_socket.send("\nSaliendo de la aplicación. Volviendo al menú principal.\n".encode())
                    break
                    
                # Enviar a la aplicación
                if self.app_process and self.app_process.poll() is None:
                    self.app_process.stdin.write(user_input + "\n")
                    self.app_process.stdin.flush()
                else:
                    self.in_application = False
                    self.current_app = None
                    break
                    
        except BrokenPipeError:
            logger.info(f"Cliente {self.session_id} desconectado durante entrada a aplicación")
            self.running = False
        except Exception as e:
            logger.error(f"Error procesando entrada a aplicación: {e}")
            self.in_application = False
    
    def show_task_status(self):
        """Muestra el estado de las tareas en cola y completadas"""
        # Obtener estado de la cola
        queue_size = task_queue.qsize()
        
        status = "\nESTADO DE TAREAS\n"
        status += "-" * 40 + "\n"
        status += f"Tareas en cola: {queue_size}\n"
        status += f"Sesiones activas: {len(active_sessions)}\n"
        status += "-" * 40 + "\n"
        
        self.client_socket.send(status.encode())
        
        # Pedir al usuario que presione Enter para continuar
        self.client_socket.send("\nPresione Enter para continuar...".encode())
        self.recv_line()  # Esperar a que el usuario presione Enter
    
    def recv_line(self):
        """Recibe una línea del cliente"""
        buffer = b''
        while self.running:
            chunk = self.client_socket.recv(1)
            if not chunk:
                raise BrokenPipeError("Conexión cerrada por el cliente")
                
            if chunk == b'\n' or chunk == b'\r':
                # Ignorar CR, devolver en LF
                if chunk == b'\r':
                    # Verificar si hay un LF siguiente (CRLF)
                    self.client_socket.settimeout(0.01)
                    try:
                        next_char = self.client_socket.recv(1)
                        if next_char != b'\n':
                            # Si no es LF, devolver al buffer
                            buffer += next_char
                    except socket.timeout:
                        pass
                    finally:
                        self.client_socket.settimeout(None)
                
                return buffer.decode()
                
            buffer += chunk

class NetcatServer:
    """Servidor que acepta conexiones y las maneja"""
    
    def __init__(self, port=3080, host='0.0.0.0'):
        self.port = port
        self.host = host
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False
        
        # Iniciar worker para procesar tareas
        self.task_worker = TaskWorker(task_queue)
    
    def start(self):
        """Inicia el servidor"""
        global session_counter
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            # Iniciar worker
            self.task_worker.start()
            
            logger.info(f"Servidor iniciado en {self.host}:{self.port}")
            
            # Manejar señales para cierre graceful
            signal.signal(signal.SIGINT, self.handle_signal)
            signal.signal(signal.SIGTERM, self.handle_signal)
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    
                    # Crear identificador de sesión único
                    with session_lock:
                        session_counter += 1
                        session_id = session_counter
                    
                    # Crear manejador de cliente
                    handler = ClientHandler(client_socket, client_address, session_id)
                    
                    # Registrar sesión activa
                    with session_lock:
                        active_sessions[session_id] = {
                            'address': client_address,
                            'started': datetime.now().isoformat(),
                            'handler': handler
                        }
                    
                    # Iniciar hilo para manejar cliente
                    client_thread = threading.Thread(
                        target=handler.handle,
                        name=f"client-{session_id}"
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Error aceptando conexión: {e}")
            
        except Exception as e:
            logger.error(f"Error iniciando servidor: {e}")
        finally:
            self.cleanup()
    
    def handle_signal(self, signum, frame):
        """Maneja señales para cierre graceful"""
        logger.info(f"Recibida señal {signum}, cerrando servidor")
        self.stop()
    
    def stop(self):
        """Detiene el servidor"""
        self.running = False
        
        # Cerrar todas las sesiones activas
        with session_lock:
            for session_id, session in active_sessions.items():
                try:
                    handler = session.get('handler')
                    if handler:
                        handler.running = False
                except Exception as e:
                    logger.error(f"Error cerrando sesión {session_id}: {e}")
        
        # Detener worker
        if self.task_worker:
            self.task_worker.running = False
        
        # Cerrar socket del servidor
        try:
            self.server_socket.shutdown(socket.SHUT_RDWR)
            self.server_socket.close()
        except Exception as e:
            logger.error(f"Error cerrando socket del servidor: {e}")
    
    def cleanup(self):
        """Limpieza final"""
        logger.info("Limpiando recursos del servidor")
        
        # Cerrar socket del servidor si sigue abierto
        try:
            self.server_socket.close()
        except:
            pass
        
        # Terminar procesos de aplicación de clientes
        with session_lock:
            for session_id, session in active_sessions.items():
                try:
                    handler = session.get('handler')
                    if handler and handler.app_process:
                        handler.app_process.terminate()
                except:
                    pass
        
        logger.info("Servidor detenido")

if __name__ == "__main__":
    try:
        # Verificar que el directorio de datos exista
        os.makedirs("/opt/cloud-orchestrator/data", exist_ok=True)
        
        # Crear y ejecutar servidor
        server = NetcatServer(port=3080)
        server.start()
        
    except KeyboardInterrupt:
        logger.info("Detenido por interrupción de teclado")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)
