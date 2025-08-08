# Imagen base con Node.js
FROM node:20

# Instalar Python y pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Carpeta de trabajo en el contenedor
WORKDIR /app

# Copiar backend completo al contenedor
COPY . .

# Dependencias Node.js
RUN npm install

# Dependencias Python
RUN pip3 install -r Python/requirements.txt

# Puerto del servidor
EXPOSE 8080

# Arranca el backend
CMD ["node", "server.js"]