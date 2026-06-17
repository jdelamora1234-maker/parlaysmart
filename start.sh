#!/bin/bash
# ParlaySmart — Script de inicio

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cargar .env si existe
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Verificar API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo ""
  echo "⚠️  Falta la API key de Anthropic."
  echo ""
  echo "Obtén tu key en: https://console.anthropic.com/api-keys"
  echo "Luego crea el archivo .env:"
  echo ""
  echo "  echo 'ANTHROPIC_API_KEY=sk-ant-tu-key-aqui' > ~/.parlay-system/.env"
  echo ""
  echo "O pega tu key aquí directamente:"
  read -p "ANTHROPIC_API_KEY: " KEY
  if [ -n "$KEY" ]; then
    echo "ANTHROPIC_API_KEY=$KEY" > .env
    export ANTHROPIC_API_KEY="$KEY"
    echo "✅ Key guardada en .env"
  else
    echo "❌ Sin key no se pueden hacer análisis. Saliendo."
    exit 1
  fi
fi

# Verificar dependencias
python3 -c "import flask, anthropic, flask_cors" 2>/dev/null || {
  echo "📦 Instalando dependencias..."
  pip3 install -r requirements.txt -q
}

echo ""
echo "🎰 ParlaySmart iniciando..."
echo "👉  Abre Chrome en: http://localhost:5050"
echo ""

# Abrir Chrome automáticamente
sleep 1 && open "http://localhost:5050" &

# Iniciar servidor
python3 server.py
