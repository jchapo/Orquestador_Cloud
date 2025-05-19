#!/bin/bash
/usr/sbin/sshd
echo "Iniciando servidor TCP en puerto 3080"
python3 /app/tcp_server.py
