from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, traceback

# Cargar .env si existe
_env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(_env_file):
    for line in open(_env_file):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

app = Flask(__name__, static_folder="static")
CORS(app)

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        body = request.get_json(force=True)
        query       = body.get("query", "").strip()
        team_a      = body.get("team_a", "").strip()
        team_b      = body.get("team_b", "").strip()
        sport       = body.get("sport", "Fútbol").strip()
        competition = body.get("competition", "").strip()
        date_str    = body.get("date", "hoy").strip()
        context     = body.get("context", "").strip()

        if not query and not team_a:
            return jsonify({"error": "Escribe el partido a analizar"}), 400

        from analyzer import analyze_match
        result = analyze_match(team_a, team_b, sport, competition, date_str, context, query=query)
        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("⚠️  ANTHROPIC_API_KEY no encontrada en el environment")
    else:
        print(f"✅ API key cargada ({key[:8]}...)")
    port = int(os.environ.get("PORT", 5050))
    print(f"🚀 Servidor iniciando en http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
