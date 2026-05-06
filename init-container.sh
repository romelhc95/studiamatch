#!/bin/bash
# Configuración inicial dentro del contenedor

echo "🔄 Iniciando configuración de entorno StudIAMatch (Linux)..."

# 1. Configuración de Python
echo "📦 Instalando dependencias de Python..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# También instalar system-wide para compatibilidad con docker exec
pip install --break-system-packages -r requirements.txt
playwright install --with-deps chromium

# 2. Configuración de Next.js
echo "📦 Instalando dependencias de Next.js..."
cd web
npm install

echo "✅ Entorno listo en Linux."
echo "Para arrancar la web: 'npm run dev' dentro de la carpeta web."
echo "Para los scripts: 'source venv/bin/activate' en la raíz."

