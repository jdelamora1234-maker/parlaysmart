import os, json, requests, hashlib
from datetime import date as dt_date, datetime, timezone, timedelta

# Mexico City: UTC-6 permanente desde octubre 2022 (ya no cambia horario)
_MX_OFFSET = timedelta(hours=-6)

def _utc_to_mx(date_str):
    if not date_str or len(date_str) < 16:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        dt_mx = dt.astimezone(timezone(_MX_OFFSET))
        return dt_mx.strftime('%H:%M')
    except Exception:
        return date_str[11:16]

def _utc_to_mx_date(date_str):
    """Retorna la fecha YYYY-MM-DD en hora Mexico City."""
    if not date_str or len(date_str) < 10:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        dt_mx = dt.astimezone(timezone(_MX_OFFSET))
        return dt_mx.strftime('%Y-%m-%d')
    except Exception:
        return date_str[:10]

BASE_URL = "https://v3.football.api-sports.io"

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache", "fapi")
os.makedirs(_CACHE_DIR, exist_ok=True)


def _headers():
    return {"x-apisports-key": os.environ.get("API_FOOTBALL_KEY", "")}


def _cache_path(endpoint, params):
    key = hashlib.md5((endpoint + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    return os.path.join(_CACHE_DIR, key + ".json")


def _cache_get(endpoint, params):
    path = _cache_path(endpoint, params)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            entry = json.load(f)
        if entry.get("date") != str(dt_date.today()):
            return None
        return entry.get("data")
    except Exception:
        return None


def _cache_set(endpoint, params, data):
    path = _cache_path(endpoint, params)
    try:
        with open(path, "w") as f:
            json.dump({"date": str(dt_date.today()), "data": data}, f)
    except Exception:
        pass


def _get(endpoint, params=None):
    if params is None:
        params = {}
    cached = _cache_get(endpoint, params)
    if cached is not None:
        return cached
    try:
        r = requests.get(
            f"{BASE_URL}/{endpoint}",
            headers=_headers(),
            params=params,
            timeout=10
        )
        if r.status_code == 200:
            data = r.json().get("response", [])
            _cache_set(endpoint, params, data)
            return data
    except Exception:
        pass
    return []


def get_fixtures_by_date(date_str):
    """Obtiene fixtures por fecha UTC (para cache y busqueda de partido especifico)."""
    return _get("fixtures", {"date": date_str})


def get_fixtures_for_mx_date(mx_date_str):
    """Obtiene todos los fixtures que caen en una fecha Mexico City (UTC-6).

    Un partido de las 6pm Mexico = 00:00 UTC del dia siguiente, asi que hay
    que pedir dos fechas UTC y filtrar por la hora real en Mexico.
    """
    d = dt_date.fromisoformat(mx_date_str)
    d_next = d + timedelta(days=1)

    fixtures_a = _get("fixtures", {"date": mx_date_str}) or []
    fixtures_b = _get("fixtures", {"date": str(d_next)}) or []

    seen_ids = set()
    result = []
    for fix in fixtures_a + fixtures_b:
        fid = fix.get("fixture", {}).get("id")
        if fid in seen_ids:
            continue
        seen_ids.add(fid)
        raw_date = fix.get("fixture", {}).get("date", "")
        if _utc_to_mx_date(raw_date) == mx_date_str:
            result.append(fix)
    return result


def get_fixture_injuries(fixture_id):
    return _get("injuries", {"fixture": fixture_id})


def get_fixture_lineups(fixture_id):
    return _get("fixtures/lineups", {"fixture": fixture_id})


def get_fixture_statistics(fixture_id):
    return _get("fixtures/statistics", {"fixture": fixture_id})


def get_fixture_events(fixture_id):
    return _get("fixtures/events", {"fixture": fixture_id})


def search_fixture(team_a, team_b, date_str):
    fixtures = get_fixtures_by_date(date_str)
    a = team_a.lower().strip()
    b = team_b.lower().strip()
    for fix in fixtures:
        home = fix.get("teams", {}).get("home", {}).get("name", "").lower()
        away = fix.get("teams", {}).get("away", {}).get("name", "").lower()
        match_a = a in home or home in a or a in away or away in a
        match_b = b in away or away in b or b in home or home in b
        if match_a or match_b:
            return fix
    return None


def format_real_data(fixture, injuries=None, lineups=None):
    if not fixture:
        return ""

    teams  = fixture.get("teams", {})
    home   = teams.get("home", {})
    away   = teams.get("away", {})
    league = fixture.get("league", {})
    finfo  = fixture.get("fixture", {})
    goals  = fixture.get("goals", {})

    lines = ["=== DATOS REALES API-FOOTBALL ==="]
    lines.append(f"Partido: {home.get('name')} vs {away.get('name')}")
    lines.append(f"Liga: {league.get('name')} | Pais: {league.get('country')}")
    lines.append(f"Temporada: {league.get('season')}")
    lines.append(f"Estadio: {finfo.get('venue', {}).get('name', 'N/D')}, {finfo.get('venue', {}).get('city', '')}")

    status = finfo.get("status", {})
    short  = status.get("short", "NS")
    if short not in ("NS", "TBD"):
        elapsed = status.get("elapsed") or 0
        lines.append(f"Estado: {status.get('long')} (min {elapsed})")
        if goals.get("home") is not None:
            lines.append(f"Marcador: {home.get('name')} {goals.get('home')} - {goals.get('away')} {away.get('name')}")

    if injuries:
        home_inj = [i for i in injuries if i.get("team", {}).get("id") == home.get("id")]
        away_inj = [i for i in injuries if i.get("team", {}).get("id") == away.get("id")]
        if home_inj or away_inj:
            lines.append("\nLESIONADOS/BAJAS:")
        if home_inj:
            lines.append(f"  {home.get('name')}:")
            for inj in home_inj[:6]:
                p = inj.get("player", {})
                lines.append(f"    - {p.get('name')} ({inj.get('type')}: {inj.get('reason', '')})")
        if away_inj:
            lines.append(f"  {away.get('name')}:")
            for inj in away_inj[:6]:
                p = inj.get("player", {})
                lines.append(f"    - {p.get('name')} ({inj.get('type')}: {inj.get('reason', '')})")

    if lineups:
        lines.append("\nALINEACIONES CONFIRMADAS:")
        for tl in lineups[:2]:
            tname    = tl.get("team", {}).get("name", "")
            formation = tl.get("formation", "?")
            starters  = tl.get("startXI", [])
            lines.append(f"  {tname} [{formation}]:")
            for p in starters:
                pl = p.get("player", {})
                lines.append(f"    {pl.get('number','')}.{pl.get('name','')} ({pl.get('pos','')})")

    lines.append("=== FIN DATOS REALES ===")
    return "\n".join(lines)


def get_context_for_match(team_a, team_b, date_str):
    fixture = search_fixture(team_a, team_b, date_str)
    if not fixture:
        return "", None

    fid      = fixture.get("fixture", {}).get("id")
    injuries = get_fixture_injuries(fid) if fid else []
    lineups  = get_fixture_lineups(fid) if fid else []

    context = format_real_data(fixture, injuries, lineups)
    return context, fixture


# Competiciones globales — siempre se muestran sin importar el pais
_GLOBAL_COMPETITIONS = [
    'world cup', 'copa del mundo', 'copa mundo', 'fifa world',
    'european championship', 'euro 20',
    'nations league', 'uefa nations',
    'copa america', 'africa cup', 'afcon',
    'asian cup', 'afc asian',
    'gold cup', 'concacaf gold',
    'club world cup', 'mundial de clubes',
    'champions league', 'champions cup',
    'europa league',
    'conference league',
    'copa libertadores', 'libertadores',
    'copa sudamericana', 'sudamericana',
    'recopa sudamericana',
    'concacaf champions', 'concacaf league',
]

# Ligas validas solo si vienen del pais correcto
# clave = substring del nombre, valor = set de paises aceptados
_COUNTRY_LEAGUES = {
    'premier league':       {'England', 'Australia'},
    'championship':         {'England'},
    'fa cup':               {'England'},
    'league cup':           {'England'},
    'bundesliga':           {'Germany', 'Austria'},
    '2. bundesliga':        {'Germany'},
    'dfb pokal':            {'Germany'},
    'serie a':              {'Italy', 'Brazil'},
    'serie b':              {'Italy', 'Brazil'},
    'coppa italia':         {'Italy'},
    'la liga':              {'Spain'},
    'laliga':               {'Spain'},
    'copa del rey':         {'Spain'},
    'ligue 1':              {'France'},
    'ligue1':               {'France'},
    'ligue 2':              {'France'},
    'coupe de france':      {'France'},
    'eredivisie':           {'Netherlands'},
    'primeira liga':        {'Portugal'},
    'scottish premiership': {'Scotland'},
    'scottish cup':         {'Scotland'},
    'super lig':            {'Turkey'},
    'jupiler':              {'Belgium'},
    'allsvenskan':          {'Sweden'},
    'superettan':           {'Sweden'},
    'eliteserien':          {'Norway'},
    'ekstraklasa':          {'Poland'},
    'superliga':            {'Denmark', 'Serbia', 'Greece'},
    'super league':         {'Greece', 'China'},
    'mls':                  {'USA'},
    'liga mx':              {'Mexico'},
    'liga de expansion':    {'Mexico'},
    'copa mx':              {'Mexico'},
    'apertura':             {'Mexico', 'Argentina', 'Uruguay', 'Chile'},
    'clausura':             {'Mexico', 'Argentina', 'Uruguay', 'Chile'},
    'brasileirao':          {'Brazil'},
    'campeonato brasileiro': {'Brazil'},
    'liga profesional':     {'Argentina'},
    'primera division':     {'Argentina', 'Spain', 'Mexico', 'Chile', 'Colombia', 'Uruguay'},
    'j1 league':            {'Japan'},
    'j.league':             {'Japan'},
    'k league':             {'South Korea'},
    'chinese super':        {'China'},
    'saudi pro':            {'Saudi Arabia'},
    'saudi professional':   {'Saudi Arabia'},
}

# Ligas que nunca se muestran aunque coincidan con las reglas anteriores
_BLOCKLIST = [
    'next pro',      # MLS Next Pro (equipos filiales)
    'mls next',
    'reserve',
    'friendlies',    # Amistosos no programados
    'u20', 'u-20', 'u19', 'u-19', 'u18', 'u-18', 'u17', 'u-17',  # Sub-juveniles
    'npl ',          # National Premier Leagues (amateur)
    ' ii ',          # Equipos B/filiales
    ' 2 ',           # Segunda divisiones de ligas menores
    'amateur',
]

def _is_popular_league(name, country):
    n = name.lower()
    # Blocklist: jamas mostrar
    if any(bl in n for bl in _BLOCKLIST):
        return False
    # 1. Competicion global: siempre OK
    if any(kw in n for kw in _GLOBAL_COMPETITIONS):
        return True
    # 2. Liga especifica de pais
    for kw, countries in _COUNTRY_LEAGUES.items():
        if kw in n:
            return country in countries
    return False


def fixtures_to_matches(fixtures):
    by_league = {}
    for fix in fixtures:
        league  = fix.get("league", {})
        lname   = league.get("name", "Otra Liga")
        country = league.get("country", "")
        lflag   = league.get("flag") or league.get("logo") or ""
        finfo   = fix.get("fixture", {})
        teams   = fix.get("teams", {})
        goals   = fix.get("goals", {})
        status  = finfo.get("status", {})

        if not _is_popular_league(lname, country):
            continue

        match = {
            "id":        str(finfo.get("id", "")),
            "team_home": teams.get("home", {}).get("name", ""),
            "team_away": teams.get("away", {}).get("name", ""),
            "time":      _utc_to_mx(finfo.get("date", "")),
            "status":    status.get("short", "NS"),
            "elapsed":   status.get("elapsed") or 0,
            "score_home": goals.get("home"),
            "score_away": goals.get("away"),
            "league_name": lname,
            "league_flag": lflag,
            "venue":     finfo.get("venue", {}).get("name", ""),
        }

        key = f"{lname}|{country}"
        if key not in by_league:
            by_league[key] = {
                "league_name": lname,
                "league_country": country,
                "league_flag": lflag,
                "matches": []
            }
        by_league[key]["matches"].append(match)

    # Ordenar partidos de cada liga por hora
    for league in by_league.values():
        league["matches"].sort(key=lambda m: m.get("time") or "99:99")

    return list(by_league.values())
