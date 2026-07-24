# Imagen base liviana con Python
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de dependencias
COPY requirements.txt .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el proyecto al contenedor
COPY . .

# Expone el puerto que usará Uvicorn
EXPOSE 8000

# Comando para ejecutar la API con recarga automática
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


