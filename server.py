from flask import Flask, request, jsonify, send_from_directory, session, abort
from functools import wraps
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os, traceback

def _friendly_error(e):
    s = str(e)
    if "429" in s or "RESOURCE_EXHAUSTED" in s:
        return "El servicio de IA esta temporalmente sin cupo. Intenta de nuevo despues.", 503
    if "quota" in s.lower():
        return "Limite de uso alcanzado. Intenta mas tarde.", 503
    if "Gemini" in s or "HTML" in s or "<" in s or "doctype" in s.lower() or "ldoctype" in s.lower():
        return "No se pudo obtener datos para este partido. Intenta con otro partido o mas tarde.", 503
    if "no candidates" in s.lower() or "no parts" in s.lower() or "empty" in s.lower():
        return "El analisis no pudo completarse. Intenta de nuevo.", 503
    if "json" in s.lower() or "parse" in s.lower():
        return "Error procesando la respuesta. Intenta de nuevo.", 500
    return "Error inesperado. Intenta de nuevo mas tarde.", 500

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
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
CORS(app, supports_credentials=True)

ACCESS_CODE = os.environ.get("ACCESS_CODE", "Jorge2252")

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
    from pins import validate_pin
    code = request.get_json(force=True).get("code", "").strip()
    if code.upper() == ACCESS_CODE.upper():
        session["auth"] = True
        session["is_admin"] = True
        return jsonify({"ok": True, "is_admin": True})
    if validate_pin(code):
        session["auth"] = True
        session["is_admin"] = False
        return jsonify({"ok": True, "is_admin": False})
    return jsonify({"error": "Codigo incorrecto o expirado"}), 401


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("auth") or not session.get("is_admin"):
            return jsonify({"error": "No autorizado"}), 403
        return f(*args, **kwargs)
    return decorated


@app.route("/admin/pins", methods=["GET"])
@require_admin
def admin_list_pins():
    from pins import list_pins
    return jsonify(list_pins())


@app.route("/admin/pins", methods=["POST"])
@require_admin
def admin_create_pin():
    from pins import create_pin
    days = int(request.get_json(force=True).get("days", 1))
    if days not in (1, 3, 7):
        return jsonify({"error": "Duracion invalida"}), 400
    pin = create_pin(days)
    return jsonify(pin)


@app.route("/admin/pins/<code>", methods=["DELETE"])
@require_admin
def admin_delete_pin(code):
    from pins import delete_pin
    delete_pin(code)
    return jsonify({"ok": True})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/debug-simple", methods=["GET"])
def debug_simple():
    """Simple debug endpoint"""
    try:
        gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        return jsonify({
            "gemini_configured": bool(gemini_key),
            "gemini_length": len(gemini_key) if gemini_key else 0,
            "gemini_start": gemini_key[:10] if gemini_key else "N/A",
            "access_code": os.environ.get("ACCESS_CODE", "DEFAULT"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/test-gemini-call", methods=["GET"])
def test_gemini_call():
    """Test Gemini API call"""
    try:
        from analyzer import _call_gemini
        result = _call_gemini("Responde con JSON válido: {\"test\": \"ok\", \"message\": \"Hello\"}", max_tokens=8000)
        return jsonify({
            "status": "OK",
            "result": result[:500],
            "result_length": len(result),
            "full_result": result
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": "ERROR"}), 500


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
        msg, code = _friendly_error(e)
        traceback.print_exc()
        return jsonify({"error": msg}), code


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
        msg, code = _friendly_error(e)
        traceback.print_exc()
        return jsonify({"error": msg}), code


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
        msg, code = _friendly_error(e)
        traceback.print_exc()
        return jsonify({"error": msg}), code


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
        msg, code = _friendly_error(e)
        traceback.print_exc()
        return jsonify({"error": msg}), code


if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("❌ GEMINI_API_KEY NO ENCONTRADA")
    else:
        print(f"✅ Gemini API Key cargada: {key[:20]}...")
    code = os.environ.get("ACCESS_CODE", "Jorge2252")
    print(f"✅ Codigo de acceso: {code}")
    port = int(os.environ.get("PORT", 5050))
    print(f"✅ Puerto: {port}")
    print(f"✅ Servidor iniciando...")
    app.run(host="0.0.0.0", port=port, debug=False)
