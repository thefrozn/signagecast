# Abfahrten von Bus und Bahn (seit 0.21) über eine HAFAS-REST-Schnittstelle im Format von „db-rest“
# (https://v6.db.transport.rest, Deutschland, ohne Schlüssel; andere Instanzen wie v6.vbb.transport.rest oder eine
# eigene lassen sich je Baustein eintragen). Abgerufen wird nur für Bausteine in Layouts, höchstens einmal je Minute
# und Haltestelle – die öffentlichen Instanzen erlauben 100 Anfragen je Minute.
import json, time, urllib.error, urllib.parse, urllib.request

from meldung import Meldung

DIENST = "https://v6.db.transport.rest"
UA = "SignageCast (TV info screen; https://github.com/thefrozn/signagecast)"


def _holen(url, zeit_s=15):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"}),
                                    timeout=zeit_s) as r:
            return json.loads(r.read(2_000_000))
    except urllib.error.HTTPError as f:
        raise Meldung("ab_http", code=f.code) from None
    except (urllib.error.URLError, OSError) as f:
        raise Meldung("ab_nicht_erreichbar", d=getattr(f, "reason", f)) from None
    except ValueError:
        raise Meldung("ab_antwort") from None


def suchen(text, dienst=""):
    """Haltestellen zum Suchtext -> [{"id", "name"}] (für die Verwaltung)."""
    text = " ".join(str(text).split())[:80]
    if len(text) < 2:
        return []
    q = urllib.parse.urlencode({"query": text, "results": 8, "stops": "true", "addresses": "false", "poi": "false"})
    roh = _holen(f"{(dienst or DIENST).rstrip('/')}/locations?{q}")
    return [{"id": str(x["id"]), "name": x.get("name") or str(x["id"])} for x in (roh if isinstance(roh, list) else [])
            if isinstance(x, dict) and x.get("type") in ("stop", "station") and x.get("id")][:8]


def _zeit(w):
    """ISO-Zeit der Schnittstelle (mit Zeitzone) -> Unix-Zeit."""
    import datetime
    try:
        return datetime.datetime.fromisoformat(str(w)).timestamp()
    except ValueError:
        return None


def aufbereiten(roh, jetzt=None):
    """Antwort der Schnittstelle -> sortierte Liste kleiner Einträge für die TV-Seite."""
    jetzt = jetzt or time.time()
    liste = roh.get("departures") if isinstance(roh, dict) else roh          # v6: Objekt, v5: Liste
    aus = []
    for x in liste if isinstance(liste, list) else []:
        if not isinstance(x, dict):
            continue
        plan = _zeit(x.get("plannedWhen") or x.get("when"))
        wann = _zeit(x.get("when")) or plan
        if not plan or wann < jetzt - 60:
            continue
        linie = x.get("line") or {}
        verspaetung = x.get("delay")
        aus.append({"zeit": int(wann), "plan": int(plan), "linie": str(linie.get("name") or "")[:12],
                    "art": str(linie.get("product") or "")[:20], "ziel": str(x.get("direction") or "")[:60],
                    "gleis": str(x.get("platform") or x.get("plannedPlatform") or "")[:8],
                    "plus": round(verspaetung / 60) if isinstance(verspaetung, (int, float)) else None,
                    "ausfall": bool(x.get("cancelled"))})
    return sorted(aus, key=lambda a: a["zeit"])


class Abfahrten:
    """bausteine() -> [{"haltestelle", "dienst", "anzahl", "vorlauf_min"}]; daten[(dienst, haltestelle)] = {"liste", "zeit", "fehler"}."""

    def __init__(self, bausteine):
        self.bausteine = bausteine
        self.daten = {}

    def einmal(self, jetzt=None):
        jetzt = jetzt or time.time()
        bedarf = {}
        for b in self.bausteine():
            if b["haltestelle"]:
                k = ((b["dienst"] or DIENST).rstrip("/"), b["haltestelle"])
                bedarf[k] = max(bedarf.get(k, 0), b["anzahl"] + 6, 60 + b["vorlauf_min"])
        for (dienst, hs), n in bedarf.items():
            alt = self.daten.get((dienst, hs)) or {}
            if jetzt - alt.get("zeit", 0) < (300 if alt.get("fehler") else 60):
                continue
            q = urllib.parse.urlencode({"duration": min(240, max(60, n)), "results": min(60, n), "remarks": "false"})
            try:
                liste = aufbereiten(_holen(f"{dienst}/stops/{urllib.parse.quote(hs)}/departures?{q}"), jetzt)
                self.daten[(dienst, hs)] = {"liste": liste, "zeit": jetzt, "fehler": None}
            except Meldung as f:
                self.daten[(dienst, hs)] = dict(alt, zeit=jetzt, fehler=str(f))
        for k in [k for k in self.daten if k not in bedarf]:
            del self.daten[k]

    def fuer(self, o, jetzt=None):
        """Werte für einen Baustein: die nächsten Abfahrten ab „vorlauf_min“ Minuten (Weg zur Haltestelle)."""
        jetzt = jetzt or time.time()
        d = self.daten.get(((o.get("dienst") or DIENST).rstrip("/"), o.get("haltestelle"))) or {}
        ab = jetzt + o.get("vorlauf_min", 0) * 60 - 30
        return {"liste": [a for a in d.get("liste", []) if a["zeit"] >= ab][:o.get("anzahl", 6)],
                "stand": int(d.get("zeit") or 0), "fehler": d.get("fehler")}

    def schleife(self):
        while True:
            try:
                self.einmal()
            except Exception as ex:                # nie den Dienst mitreißen
                print("Abfahrten:", ex, flush=True)
            time.sleep(20)
