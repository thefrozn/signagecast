# Eigenes Wetter von MET Norway (api.met.no, Locationforecast 2.0 „compact“): kostenlos, ohne Schlüssel, weltweit,
# auch kommerziell nutzbar mit Quellenhinweis (CC BY 4.0, „Wetterdaten: MET Norway“). Nutzungsregeln: aussagekräftiger
# User-Agent, Koordinaten mit höchstens 4 Nachkommastellen, „Expires“ beachten, nachfragen mit If-Modified-Since.
# Liefert dieselbe Form wie das HA-Wetter (Zustände wie HA: sunny, partlycloudy, rainy …).
import datetime, json, os, time, urllib.error, urllib.request
from meldung import Meldung, als_dict

try:
    _V = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "VERSION")).read().strip()
except OSError:
    _V = "dev"
UA = f"SignageCast/{_V} github.com/thefrozn/signagecast"     # MET verlangt einen aussagekräftigen User-Agent
URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={:.4f}&lon={:.4f}"


def zustand_aus_symbol(code):
    """MET-Symbol (z. B. 'lightrainshowers_day') -> HA-Wetterzustand."""
    c = (code or "").replace("_day", "").replace("_night", "").replace("_polartwilight", "")
    nacht = (code or "").endswith("_night")
    if "thunder" in c:
        return "lightning-rainy" if ("rain" in c or "sleet" in c or "snow" in c) else "lightning"
    if "heavyrain" in c:
        return "pouring"
    if "sleet" in c:
        return "snowy-rainy"
    if "snow" in c:
        return "snowy"
    if "rain" in c or "drizzle" in c:
        return "rainy"
    if c == "fog":
        return "fog"
    if c == "cloudy":
        return "cloudy"
    if c in ("fair", "partlycloudy"):
        return "partlycloudy"
    if c == "clearsky":
        return "clear-night" if nacht else "sunny"
    return "cloudy"


class MetWetter:
    def __init__(self):
        self.daten = None            # letzte Antwort (JSON)
        self.ort = None              # (breite, länge), für die die Daten gelten
        self.gueltig_bis = 0         # aus „Expires“
        self.geaendert = None        # „Last-Modified“ für If-Modified-Since
        self.fehler = None
        self.fehler_m = None             # dieselbe Meldung mit Kennung (für die Übersetzung in der Verwaltung)
        self.abruf = None

    def holen(self, breite, laenge):
        ort = (round(breite, 4), round(laenge, 4))
        if ort == self.ort and time.time() < self.gueltig_bis:
            return
        kopf = {"User-Agent": UA}
        if ort == self.ort and self.geaendert:
            kopf["If-Modified-Since"] = self.geaendert
        try:
            with urllib.request.urlopen(urllib.request.Request(URL.format(*ort), headers=kopf), timeout=20) as r:
                self.daten = json.load(r)
                self.geaendert = r.headers.get("Last-Modified")
                ablauf = r.headers.get("Expires")
            self.ort, self.fehler, self.fehler_m = ort, None, None
        except urllib.error.HTTPError as e:
            if e.code != 304:                    # 304 = unverändert, alte Daten gelten weiter
                m = Meldung("met_http", code=e.code)
                self.fehler, self.fehler_m = str(m), als_dict(m)
                self.gueltig_bis = time.time() + 600
                return
            ablauf = e.headers.get("Expires")
        except Exception as e:
            m = Meldung("met_nicht_erreichbar", d=e)
            self.fehler, self.fehler_m = str(m), als_dict(m)
            self.gueltig_bis = time.time() + 600
            return
        self.abruf = time.strftime("%Y-%m-%d %H:%M")
        try:
            self.gueltig_bis = max(time.time() + 600, datetime.datetime.strptime(ablauf, "%a, %d %b %Y %H:%M:%S %Z")
                                   .replace(tzinfo=datetime.timezone.utc).timestamp())
        except Exception:
            self.gueltig_bis = time.time() + 1800

    def aktuell(self):
        """Wetter jetzt in der Form der TV-Seite (wie aus HA)."""
        if not self.daten:
            return None
        ts = self.daten["properties"]["timeseries"]
        jetzt = datetime.datetime.now(datetime.timezone.utc)
        # der jüngste Zeitpunkt, der nicht in der Zukunft liegt (sonst der erste)
        eintrag = ts[0]
        for t in ts:
            if datetime.datetime.fromisoformat(t["time"].replace("Z", "+00:00")) <= jetzt:
                eintrag = t
            else:
                break
        d = eintrag["data"]
        werte = d["instant"]["details"]
        symbol = (d.get("next_1_hours") or d.get("next_6_hours") or {}).get("summary", {}).get("symbol_code")
        return {"zustand": zustand_aus_symbol(symbol), "temperatur": werte.get("air_temperature"),
                "feuchte": werte.get("relative_humidity"),
                "wind": round(werte.get("wind_speed", 0) * 3.6, 1), "wind_einheit": "km/h", "quelle": "MET Norway"}

    def vorhersage(self, tage=5):
        """Tageswerte (Ortszeit): Höchst-/Tiefstwert, Zustand um die Mittagszeit."""
        if not self.daten:
            return []
        nach_tag = {}
        for t in self.daten["properties"]["timeseries"]:
            zeit = datetime.datetime.fromisoformat(t["time"].replace("Z", "+00:00")).astimezone()
            temp = t["data"]["instant"]["details"].get("air_temperature")
            if temp is None:
                continue
            tag = nach_tag.setdefault(zeit.date().isoformat(), {"temps": [], "symbol": None, "abstand": 99})
            tag["temps"].append(temp)
            sym = (t["data"].get("next_6_hours") or t["data"].get("next_1_hours") or {}).get("summary", {}).get("symbol_code")
            abstand = abs(zeit.hour - 12)
            if sym and abstand < tag["abstand"]:
                tag["symbol"], tag["abstand"] = sym, abstand
        heute = datetime.date.today().isoformat()
        aus = []
        for tag in sorted(nach_tag):
            if tag < heute or len(aus) >= tage:
                continue
            w = nach_tag[tag]
            aus.append({"tag": tag, "zustand": zustand_aus_symbol((w["symbol"] or "").replace("_night", "_day")),
                        "max": round(max(w["temps"]), 1), "min": round(min(w["temps"]), 1)})
        return aus
