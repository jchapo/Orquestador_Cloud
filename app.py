#!/usr/bin/env python3
"""
Script de compatibilidad para mantener el comando python3 app.py
"""
import sys
import os

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ejecutar la aplicación desde su nueva ubicación
from core.app import CloudOrchestrator

if __name__ == "__main__":
    app = CloudOrchestrator()
    app.start()
