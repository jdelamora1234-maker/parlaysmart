import json, os, random, string
from datetime import datetime, timedelta, timezone

_PINS_FILE = os.path.join(os.path.dirname(__file__), "pins.json")

def _now():
    return datetime.now(timezone.utc)

def _load():
    if not os.path.exists(_PINS_FILE):
        return {}
    try:
        with open(_PINS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def _save(pins):
    with open(_PINS_FILE, "w") as f:
        json.dump(pins, f, indent=2)

def _clean_expired(pins):
    now = _now().isoformat()
    return {k: v for k, v in pins.items() if v["expires_at"] > now}

def create_pin(days):
    pins = _clean_expired(_load())
    # Generar codigo unico de 6 digitos
    while True:
        code = ''.join(random.choices(string.digits, k=6))
        if code not in pins:
            break
    now = _now()
    expires = now + timedelta(days=days)
    label = {1: "1 dia", 3: "3 dias", 7: "1 semana"}.get(days, f"{days} dias")
    pins[code] = {
        "code": code,
        "days": days,
        "label": label,
        "created_at": now.isoformat(),
        "expires_at": expires.isoformat(),
    }
    _save(pins)
    return pins[code]

def validate_pin(code):
    pins = _load()
    if code not in pins:
        return False
    pin = pins[code]
    if pin["expires_at"] <= _now().isoformat():
        # Expirado — borrarlo
        del pins[code]
        _save(pins)
        return False
    return True

def list_pins():
    pins = _clean_expired(_load())
    _save(pins)
    result = []
    now = _now()
    for p in sorted(pins.values(), key=lambda x: x["expires_at"]):
        exp = datetime.fromisoformat(p["expires_at"])
        diff = exp - now
        hours = int(diff.total_seconds() // 3600)
        if hours >= 24:
            remaining = f"{hours // 24}d {hours % 24}h"
        else:
            remaining = f"{hours}h"
        result.append({**p, "remaining": remaining})
    return result

def delete_pin(code):
    pins = _load()
    if code in pins:
        del pins[code]
        _save(pins)
        return True
    return False
