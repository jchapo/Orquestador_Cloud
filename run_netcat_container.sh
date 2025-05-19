#!/bin/bash
# Script para configurar reenvío de puertos en el gateway

# Variables - MODIFICAR ESTOS VALORES
GATEWAY_IP="10.20.12.252"
SERVER_IP="10.0.10.1"  # Reemplazar con la IP real del servidor
PORT="3080"
GATEWAY_INTERFACE="ens3"  # Ejemplo: eth0, reemplazar con la interfaz correcta

# Colores para salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Configurando reenvío de puertos en el gateway...${NC}"
echo "Gateway: $GATEWAY_IP"
echo "Servidor: $SERVER_IP"
echo "Puerto: $PORT"
echo "Interfaz: $GATEWAY_INTERFACE"
echo ""

# Verificar que la IP del servidor ha sido configurada
if [ "$SERVER_IP" = "[IP-DEL-SERVIDOR-1]" ]; then
    echo -e "${RED}Error: Debes modificar el script y configurar la IP del servidor.${NC}"
    exit 1
fi

# Verificar que la interfaz ha sido configurada
if [ "$GATEWAY_INTERFACE" = "[INTERFAZ-EXTERNA]" ]; then
    echo -e "${RED}Error: Debes modificar el script y configurar la interfaz de red correcta.${NC}"
    exit 1
fi

# Verificar conectividad con el gateway
echo -e "${YELLOW}Verificando conectividad con el gateway...${NC}"
if ! ping -c 1 "$GATEWAY_IP" &> /dev/null; then
    echo -e "${RED}Error: No se puede acceder al gateway $GATEWAY_IP${NC}"
    exit 1
fi

# Habilitar el reenvío de IP en el gateway
echo -e "${YELLOW}Habilitando el reenvío de IP en el gateway...${NC}"
ssh -t ubuntu@$GATEWAY_IP "sudo bash -c 'echo 1 > /proc/sys/net/ipv4/ip_forward'"
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: No se pudo habilitar el reenvío de IP.${NC}"
    echo "Verifica que puedes acceder al gateway como root mediante SSH."
    exit 1
fi

# Configurar sysctl para que el reenvío persista tras reinicios
ssh ubuntu@$GATEWAY_IP "grep -q 'net.ipv4.ip_forward = 1' /etc/sysctl.conf || echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf"
ssh ubuntu@$GATEWAY_IP "sysctl -p"

# Configurar NAT y reenvío de puertos en el gateway
echo -e "${YELLOW}Configurando reglas de NAT y reenvío de puertos...${NC}"

# Verificar si la regla ya existe
RULE_EXISTS=$(ssh ubuntu@$GATEWAY_IP "iptables -t nat -L PREROUTING -n | grep $SERVER_IP | grep $PORT")
if [ -n "$RULE_EXISTS" ]; then
    echo -e "${YELLOW}Aviso: El reenvío de puertos ya está configurado. Actualizando configuración...${NC}"
    ssh ubuntu@$GATEWAY_IP "iptables -t nat -D PREROUTING -i $GATEWAY_INTERFACE -p tcp --dport $PORT -j DNAT --to-destination $SERVER_IP:$PORT"
fi

# Agregar regla de DNAT
ssh ubuntu@$GATEWAY_IP "iptables -t nat -A PREROUTING -i $GATEWAY_INTERFACE -p tcp --dport $PORT -j DNAT --to-destination $SERVER_IP:$PORT"
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: No se pudo configurar la regla DNAT.${NC}"
    exit 1
fi

# Verificar si la regla de MASQUERADE ya existe
MASQ_EXISTS=$(ssh ubuntu@$GATEWAY_IP "iptables -t nat -L POSTROUTING -n | grep MASQUERADE")
if [ -z "$MASQ_EXISTS" ]; then
    ssh root@$GATEWAY_IP "iptables -t nat -A POSTROUTING -o $GATEWAY_INTERFACE -j MASQUERADE"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: No se pudo configurar la regla MASQUERADE.${NC}"
        exit 1
    fi
fi

# Guardar reglas de iptables
echo -e "${YELLOW}Guardando reglas de iptables...${NC}"
ssh ubuntu@$GATEWAY_IP "iptables-save > /etc/iptables/rules.v4 || (mkdir -p /etc/iptables && iptables-save > /etc/iptables/rules.v4)"

# Configurar para que las reglas se carguen al reiniciar (si es necesario)
ssh ubuntu@$GATEWAY_IP "if [ ! -f /etc/network/if-pre-up.d/iptables ]; then
    echo '#!/bin/sh' > /etc/network/if-pre-up.d/iptables
    echo 'iptables-restore < /etc/iptables/rules.v4' >> /etc/network/if-pre-up.d/iptables
    chmod +x /etc/network/if-pre-up.d/iptables
fi"

echo -e "${GREEN}¡Configuración completada!${NC}"
echo -e "${GREEN}Reenvío de puertos configurado en el gateway.${NC}"
echo "Los usuarios ahora pueden acceder a la aplicación mediante:"
echo "nc $GATEWAY_IP $PORT"
echo ""
echo "Para probar la conexión, ejecuta:"
echo "nc $GATEWAY_IP $PORT"
