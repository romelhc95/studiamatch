# Usamos una imagen base de Node.js (Debian)
FROM node:20-bookworm

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar Python 3 y dependencias del sistema para Playwright/Browsers
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Exponer el puerto de Next.js
EXPOSE 3000

# Comando por defecto: Mantener el contenedor vivo
CMD ["tail", "-f", "/dev/null"]
