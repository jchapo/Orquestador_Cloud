FROM python:3.10-slim

WORKDIR /app

# Copiamos todos los archivos necesarios
COPY . /app

# Instalamos dependencias
RUN pip install flask

EXPOSE 3080

CMD ["python3", "web_app.py"]
