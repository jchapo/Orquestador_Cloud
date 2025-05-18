FROM python:3.8-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    socat \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todos los archivos de la aplicación
COPY . .

# Hacer ejecutable el wrapper
RUN chmod +x cli_wrapper.sh

# Socat escuchará en el puerto 3080 y ejecutará el script por cada conexión
CMD ["socat", "TCP-LISTEN:3080,fork,reuseaddr", "EXEC:./cli_wrapper.sh,pty,stderr"]
