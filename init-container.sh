#!/bin/bash
# ConfiguraciÃ³n inicial dentro del contenedor

echo "ðŸš€ Iniciando configuraciÃ³n de entorno StudIAMatch (Linux)..."

# 1. ConfiguraciÃ³n de Python
echo "ðŸ“¦ Instalando dependencias de Python..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install --with-deps chromium

# 2. ConfiguraciÃ³n de Next.js
echo "ðŸ“¦ Instalando dependencias de Next.js..."
cd web
npm install

echo "âœ… Entorno listo en Linux."
echo "Para arrancar la web: 'npm run dev' dentro de la carpeta web."
echo "Para los scripts: 'source venv/bin/activate' en la raÃ­z."

