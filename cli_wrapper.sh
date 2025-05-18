#!/bin/bash

# Script para ejecutar la aplicación CLI a través de socat
# Este script será ejecutado por cada conexión entrante

# Configurar el entorno
export TERM=linux
export PYTHONUTF8=1

# Ejecutar la aplicación CLI
python3 app.py
