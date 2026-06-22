from flask import Flask, request, jsonify, send_from_directory, session, abort
from functools import wraps
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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
app.secret_key = os.environ.get("SECRET_KEY", "parlaysmart-secret-2025")
CORS(app, supports_credentials=True)

ACCESS_CODE = os.environ.get("ACCESS_CODE", "MAFE2025")

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("auth"):
            return jsonify({"error": "No autorizado"}), 401
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


@app.route("/login", methods=["POST"])
def login():
    code = request.get_json(force=True).get("code", "").strip()
    if code.upper() == ACCESS_CODE.upper():
        session["auth"] = True
        return jsonify({"ok": True})
    return jsonify({"error": "Codigo incorrecto"}), 401


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/today-matches", methods=["GET"])
@limiter.limit("30 per hour")
@require_auth
def today_matches():
    try:
        from datetime import date as dt_date
        date_str = request.args.get("date", str(dt_date.today()))
        from analyzer import fetch_today_matches
        result = fetch_today_matches(date_str)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/multi-analyze", methods=["POST"])
@limiter.limit("20 per hour")
@require_auth
def multi_analyze():
    try:
        body = request.get_json(force=True)
        matches  = body.get("matches", [])
        date_str = body.get("date", "hoy")
        if not matches:
            return jsonify({"error": "Selecciona al menos un partido"}), 400
        from analyzer import analyze_multi_matches
        result = analyze_multi_matches(matches, date_str)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/analyze", methods=["POST"])
@limiter.limit("20 per hour")
@require_auth
def analyze():
    try:
        body = request.get_json(force=True)
        query       = body.get("query", "").strip()
        team_a      = body.get("team_a", "").strip()
        team_b      = body.get("team_b", "").strip()
        sport       = body.get("sport", "Futbol").strip()
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


@app.route("/predict-tournament", methods=["POST"])
@limiter.limit("10 per hour")
@require_auth
def predict_tournament():
    try:
        body = request.get_json(force=True)
        tournament = body.get("tournament", "").strip()
        if not tournament:
            return jsonify({"error": "Escribe el nombre del torneo"}), 400
        from analyzer import predict_tournament as do_predict
        result = do_predict(tournament)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY no encontrada en el environment")
    else:
        print(f"Gemini API key cargada ({key[:12]}...)")
    code = os.environ.get("ACCESS_CODE", "MAFE2025")
    print(f"Codigo de acceso: {code}")
    port = int(os.environ.get("PORT", 5050))
    print(f"Servidor iniciando en http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
