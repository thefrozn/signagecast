# Einstellungen von SignageCast: Standardwerte, Laden, Prüfen, Speichern.
# Datei: /etc/signagecast/einstellungen.json (Benutzer signagecast, Rechte 600). Unbekannte Schlüssel werden verworfen,
# fehlende mit Standardwerten ergänzt – so übersteht die Datei auch Updates mit neuen Optionen.
import copy, json, os, re
import layouts as L
import quellen as Q
from meldung import Meldung
import sicherung as S

PFAD = os.environ.get("SC_EINSTELLUNGEN", "/etc/signagecast/einstellungen.json")

KATEGORIEN = ["safari", "affen", "meer", "vogel", "baer", "wald", "zoo", "neu"]
STUFEN = ["tiny", "small", "medium", "large", "hd720", "hd1080", "hd1440", "hd2160", "highres"]

STANDARD = {
    "sprache": "",                        # de | en – TV-Seite und Verwaltung; leer = beim ersten Öffnen der Verwaltung aus der Browsersprache
    "ha": {"url": "http://homeassistant.local:8123"},
    "standort": {"breite": 52.52, "laenge": 13.40, "name": ""},
    # Jeder Fernseher ist eine eigene Ausgabe mit eigener Adresse http://<IP>:8888/<id> und eigener Render-Kette
    "fernseher": [
        {"id": "tv", "nr": 0, "name": "TV", "layout": "standard", "zeitplan": [], "video": True, "ton": "aus", "radio_sender": "", "lautstaerke": 70,
         "kategorien_aus": [], "aufloesung": 2160, "bitrate_mbit": 16},
    ],
    "radio": {
        "sender": [],                     # [{"id": "s1a2b3", "name": "…", "url": "https://…"}] – für alle Fernseher
        "region_woerter": [],             # zusätzliche Suchwörter für Sender in der Nähe, z. B. ["Oberpfalz"]
        "anzeigen": True,                 # Sendername auf der TV-Seite zeigen
        "puffer_s": 15,                   # Sekunden Vorlauf (Datendienst puffert den Sender) – 0 = direkt abspielen
    },
    "anzeige": {
        "wetter_quelle": "met",           # met = eigenes Wetter (MET Norway, Standort aus „Verbindung“) | ha = Wetter-Entität aus HA
        "wetter": "weather.forecast_home",
        "vorhersage": True,
        "raeume": [],                     # bis 0.2: Räume/Kacheln hier – seit 0.3 als Bausteine im Layout
        "kacheln": [],
    },
    "layouts": [],                        # leer = beim Laden aus „anzeige“ das Layout „Standard“ bauen
    "quellen": [],                        # eigene Datenquellen (API/RSS/Bild), siehe app/quellen.py
    # eigene Medien (seit 0.15): [{"id", "name", "art": bild|video, "datei", "dauer_s", "aktiv"}], Dateien in DATEN/medien
    "medien": [],
    # Meldung per Webhook (seit 0.16): eigener Port (SC_WEBHOOK_PORT, Standard 8890), nur mit geheimem Schlüssel
    "webhook": {"aktiv": False, "token": ""},
    # Einrichtungs-Assistent (seit 0.17): nur bei Neuinstallation; vorhandene Einstellungen ohne den Schlüssel gelten als eingerichtet
    "assistent_fertig": False,
    # Benachrichtigungen (seit 0.16): Kanäle Telegram, E-Mail (SMTP), Home Assistant; Geheimnisse: Bot-Token, SMTP-Passwort
    "benachrichtigung": {
        "telegram": {"aktiv": False, "token": "", "chat_id": ""},
        "email": {"aktiv": False, "server": "", "port": 587, "sicherheit": "starttls", "benutzer": "", "passwort": "",
                  "absender": "", "empfaenger": ""},
        "ha": {"aktiv": False, "dienst": "notify.notify"},
        "ereignisse": {"ausfall": True, "update": True, "sicherung": True, "ha": True},
    },
    # automatische Sicherung (seit 0.12): plan aus/taeglich/woechentlich; mit Zugangsdaten nur mit Passwort (AES-256)
    "sicherung": {"plan": "aus", "wochentag": 0, "uhrzeit": "03:30", "behalten": 7, "mit_geheimnissen": False, "passwort": ""},
    # Updates (seit 0.13): melden = nur anzeigen; system auch „sicherheit“ (nur Sicherheitsupdates) oder „auto“ – automatisch
    # nur im Wartungsfenster und nur, wenn niemand zuschaut
    "updates": {"system": "melden", "signagecast": "melden", "fenster_von": "03:00", "fenster_bis": "05:00"},
    "video": {
        "aktiv": True,
        "takt_min": 3,                    # Minuten je Stream
        "nur_tag": True,                  # nur Streams zeigen, wo vor Ort Tag ist
        "min_sonnenhoehe": 3,             # Grad über dem Horizont
        "mindeststufe": "hd720",          # darunter gilt ein Stream als schlecht
        "schlecht_s": 20,                 # so lange unter der Mindeststufe -> Strike und weiter
        "strike_grenze": 3,               # ab so vielen Strikes nicht mehr zeigen
        "sperre_h": 2,                    # nach einem Strike so lange überspringen
        "kategorien_aus": [],             # abgeschaltete Kategorien
    },
    "suche": {
        "aktiv": True,
        "uhrzeit": "04:30",
        "max": 40,                        # höchstens so viele gefundene Streams
        "behalten_tage": 14,              # so lange nicht mehr gefunden -> raus
        "begriffe": ["africam live", "waterhole live cam", "safari live cam", "underwater live cam",
                     "coral reef live cam", "aquarium live cam", "zoo live cam", "bear live cam", "wolf live cam",
                     "penguin live cam", "bird feeder live cam", "seal live cam", "otter live cam",
                     "wildlife live cam", "explore.org live", "elephant live cam", "gorilla live cam",
                     "panda live cam", "eagle nest live cam", "hummingbird live cam"],
        "tierwoerter": ["elephant", "lion", "giraffe", "zebra", "rhino", "hippo", "bear", "wolf", "wolves", "bison",
                        "moose", "elk", "deer", "eagle", "owl", "osprey", "falcon", "penguin", "puffin", "seal",
                        "sea lion", "otter", "whale", "orca", "dolphin", "shark", "reef", "coral", "underwater",
                        "aquarium", "jelly", "manatee", "turtle", "alligator", "crocodile", "gorilla", "chimp",
                        "bonobo", "orangutan", "monkey", "sloth", "panda", "koala", "kangaroo", "capybara", "zoo",
                        "safari", "waterhole", "wildlife", "africam", "bird", "feeder", "hummingbird", "toucan",
                        "macaw", "flamingo", "stork", "beaver", "fox", "badger", "meerkat", "lemur", "tier", "vogel",
                        "storch", "adler", "robbe", "seehund", "pinguin", "wasserloch"],
        "ausschluss": ["radio", "music", "song", "lofi", "sleep", "relax", "asmr", "game", "gaming", "minecraft",
                       "roblox", "cartoon", "kids", "news", "stock", "crypto", "street", "city", "downtown", "beach",
                       "traffic", "rail", "airport", "hotel", "resort", r"\bbar\b", "church", "weather", "surf",
                       "hunting", "compilation", "simulator", "8k", "cat tv", "dog tv", "chicken", "hens", "puppy",
                       "kitten", "farm", "sheep", "archive", "documentary", "movie", "episode", "peppa", "disney",
                       "meditation", "ambient", "screensaver", "ukraine", "war", r"best.{0,8}aquarium", "beste",
                       "faszinierend", "mesmerizing", "marvel", "stunning", "real nature", "nature sounds", "giants",
                       "wassergeräusch", "realm", "4k ocean", "katzen"],
        # Ort aus dem Titel gefundener Streams (für Tag/Nacht); erster Treffer gewinnt, genaue Orte zuerst
        "orte": [
            {"muster": r"masai|maasai|mara\b|amboseli|tsavo|kenya|kenia|ol pejeta|lentorre|nairobi", "breite": -1.5, "laenge": 35.5},
            {"muster": r"serengeti|tarangire|ngorongoro|tanzania", "breite": -3.5, "laenge": 35.5},
            {"muster": r"kruger|sabi|klaserie|timbavati|djuma|naledi|tau\b|madikwe|pilanesberg|south africa|südafrika|stony point|africam", "breite": -24.5, "laenge": 31.0},
            {"muster": r"botswana|chobe|okavango|selinda|boteti|kalahari|makgadikgadi|senyati", "breite": -19.5, "laenge": 24.5},
            {"muster": r"zimbabwe|simbabwe|hwange|victoria falls", "breite": -18.5, "laenge": 26.5},
            {"muster": r"namibia|etosha|namib", "breite": -20.0, "laenge": 16.0},
            {"muster": r"malawi|majete|zambia|uganda|congo|kongo|rwanda", "breite": -10.0, "laenge": 30.0},
            {"muster": r"alaska|katmai|brooks|anan|kodiak|juneau|mendenhall", "breite": 59.0, "laenge": -150.0},
            {"muster": r"vancouver|british columbia|orcalab|canada|kanada|banff|alberta", "breite": 50.0, "laenge": -123.0},
            {"muster": r"california|kalifornien|monterey|san diego|santa barbara|catalina|big bear|aquarium of the pacific", "breite": 36.0, "laenge": -120.0},
            {"muster": r"hawaii|maui|honolulu|waikiki", "breite": 21.0, "laenge": -157.0},
            {"muster": r"florida|homosassa|silver spring|st\.? augustine|islamorada|keys|tampa|orlando|miami", "breite": 28.0, "laenge": -82.0},
            {"muster": r"texas|galveston|moody gardens|houston", "breite": 29.5, "laenge": -95.0},
            {"muster": r"minnesota|wisconsin|iowa|decorah|missouri|st\.? louis|kansas|nebraska|ohio|cincinnati|michigan|illinois|chicago", "breite": 41.0, "laenge": -90.0},
            {"muster": r"pennsylvania|pittsburgh|new york|ithaca|cornell|sapsucker|maryland|baltimore|virginia|carolina|new jersey|maine|vermont", "breite": 40.5, "laenge": -76.5},
            {"muster": r"montana|colorado|wyoming|yellowstone|idaho|utah|oregon|washington|seattle|grasslands", "breite": 45.0, "laenge": -110.0},
            {"muster": r"panama|costa rica|honduras|utopia|roatan|belize|guatemala|curaçao|curacao|caribbean|karibik", "breite": 12.0, "laenge": -80.0},
            {"muster": r"ecuador|peru|colombia|brazil|brasil|pantanal|amazon|paraguay|argentina|patagonia", "breite": -10.0, "laenge": -65.0},
            {"muster": r"england|uk\b|wales|scotland|schottland|yorkshire|peak district|skomer|national trust|ireland", "breite": 53.0, "laenge": -2.0},
            {"muster": r"netherlands|niederlande|holland|lauwersoog|texel|ecomare|veluwe|belgium", "breite": 52.5, "laenge": 5.5},
            {"muster": r"germany|deutschland|bayern|austria|österreich|wien|vienna|switzerland|schweiz|czech|tschech|hungary|ungarn|budapest|poland|polen", "breite": 49.0, "laenge": 13.0},
            {"muster": r"latvia|lettland|riga|estonia|lithuania|finland|sweden|schweden|norway|norwegen|denmark|dänemark", "breite": 59.0, "laenge": 20.0},
            {"muster": r"romania|rumänien|bulgaria|greece|italy|italien|spain|spanien|portugal|france|frankreich|croatia", "breite": 43.0, "laenge": 12.0},
            {"muster": r"japan|tokyo|osaka|kyoto|hokkaido|okinawa", "breite": 35.0, "laenge": 137.0},
            {"muster": r"china|chengdu|panda base|gengda|taiwan|taipei|hong kong|korea|seoul", "breite": 31.0, "laenge": 115.0},
            {"muster": r"thailand|vietnam|borneo|malaysia|indonesia|singapore|india|indien|sri lanka|nepal", "breite": 10.0, "laenge": 105.0},
            {"muster": r"australia|australien|sydney|taronga|melbourne|werribee|phillip island|queensland|perth|adelaide", "breite": -34.0, "laenge": 145.0},
            {"muster": r"new zealand|neuseeland|oamaru|ōamaru|otago|auckland|napier|kororā|korora|antipodes|royalcam|albatross", "breite": -42.0, "laenge": 172.0},
            {"muster": r"africa|afrika", "breite": -24.5, "laenge": 31.0},
        ],
    },
    # Einspieler: zu festen Minuten (z. B. :00 und :30) unterbricht ein Beitrag die Rotation im Videofenster
    "einspieler": [],                     # [{"id", "name", "quelle": tagesschau100|video|youtube, "url", "minuten": [0, 30],
                                          #   "von": "06:00", "bis": "23:59", "ton": True, "fernseher": [] (leer = alle), "aktiv": True}]
    # Zeitquelle: NTP-Server (leer = Länder-Pool zum Standort, z. B. de.pool.ntp.org) und Zeitzone (leer = System)
    "zeit": {"ntp": "", "zeitzone": ""},
    "stream": {
        "abschalten_s": 60,               # so lange nach dem letzten Zuschauer bis alles aus ist (plus 60 s HLS)
    },
}


class Fehler(ValueError):
    pass


def _zahl(w, lo, hi, art=float):
    try:
        w = art(w)
    except Exception:
        raise Fehler(f"keine Zahl: {w!r}")
    if not lo <= w <= hi:
        raise Fehler(f"{w} liegt nicht zwischen {lo} und {hi}")
    return w


def _text(w, maxlen=200, muster=None):
    w = str(w).strip()
    if len(w) > maxlen or (muster and not re.fullmatch(muster, w)):
        raise Fehler(f"ungültiger Wert: {w[:60]!r}")
    return w


ENTITY = r"[a-z_]+\.[a-z0-9_]+"


def _zeitplan(z, layout_ids):
    try:
        return L.pruefe_zeitplan(z, layout_ids)
    except (ValueError, TypeError) as ex:
        raise Fehler(str(ex))


def pruefen(e):
    """Nimmt beliebige (z. B. aus der Verwaltung kommende) Einstellungen und liefert eine geprüfte, vollständige Fassung."""
    s = copy.deepcopy(STANDARD)
    if not isinstance(e, dict):
        raise Fehler("Einstellungen müssen ein Objekt sein")
    if "sprache" in e:
        s["sprache"] = e["sprache"] if e["sprache"] in ("de", "en", "") else ""
    ha = e.get("ha", {})
    if "url" in ha:
        s["ha"]["url"] = _text(ha["url"], 200, r"https?://[\w.\-]+(:\d{1,5})?/?").rstrip("/")
    st = e.get("standort", {})
    if "breite" in st: s["standort"]["breite"] = round(_zahl(st["breite"], -90, 90), 4)
    if "laenge" in st: s["standort"]["laenge"] = round(_zahl(st["laenge"], -180, 180), 4)
    if "name" in st: s["standort"]["name"] = _text(st["name"], 120)
    # Layouts (seit 0.3). Fehlen sie, wird aus der bisherigen Anzeige (Räume, Kacheln) das Layout „Standard“ gebaut.
    if e.get("layouts"):
        ls, ids = [], set()
        for l in e["layouts"][:30]:
            try:
                l = L.pruefe_layout(l)
            except (ValueError, TypeError) as ex:
                raise Fehler(f"Layout {l.get('name', '?')}: {ex}")
            if l["id"] in ids:
                raise Fehler(f"Layout-Kennung doppelt: {l['id']}")
            ids.add(l["id"])
            ls.append(l)
        s["layouts"] = ls
    else:
        an_alt = e.get("anzeige", {})
        s["layouts"] = [L.standard(an_alt.get("raeume", []), an_alt.get("kacheln", []), an_alt.get("vorhersage", True))]
    layout_ids = {l["id"] for l in s["layouts"]}
    alt = e.get("stream", {})                 # bis 0.1: Auflösung/Bitrate global – als Vorgabe für die Fernseher
    if True:                                  # immer prüfen: Layout-Verweise müssen zu den Layouts passen
        liste, ids = [], set()
        for t in (e.get("fernseher") or [dict(STANDARD["fernseher"][0])])[:8]:
            tid = _text(t.get("id", "tv"), 12, r"[a-z][a-z0-9]{0,11}")
            if tid in ids:
                raise Fehler(f"Fernseher-Kennung doppelt: {tid}")
            ids.add(tid)
            ton = t.get("ton", "aus")
            if ton not in ("aus", "radio", "tiere"):
                raise Fehler("Ton nur aus, radio oder tiere")
            aufl = int(t.get("aufloesung", alt.get("aufloesung", 2160)))
            if aufl not in (1080, 2160):
                raise Fehler("Auflösung nur 1080 oder 2160")
            liste.append({"id": tid, "name": _text(t.get("name", tid), 40) or tid, "video": bool(t.get("video", True)),
                          "ton": ton, "radio_sender": _text(t.get("radio_sender", ""), 12, r"[a-z0-9]*"),
                          "lautstaerke": _zahl(t.get("lautstaerke", 70), 0, 100, int),
                          "kategorien_aus": [k for k in t.get("kategorien_aus", []) if k in KATEGORIEN],
                          "aufloesung": aufl, "bitrate_mbit": _zahl(t.get("bitrate_mbit", alt.get("bitrate_mbit", 16)), 2, 40, int),
                          "nr": t.get("nr") if isinstance(t.get("nr"), int) and 0 <= t.get("nr") < 8 else None,
                          "layout": t.get("layout") if t.get("layout") in layout_ids else s["layouts"][0]["id"],
                          "zeitplan": _zeitplan(t.get("zeitplan"), layout_ids),
                          # seit 0.15: Quelle des Videofensters und Layout-Karussell
                          "video_quelle": t.get("video_quelle") if t.get("video_quelle") in ("youtube", "medien", "gemischt") else "youtube",
                          "medien_alle": _zahl(t.get("medien_alle", 3), 1, 20, int),
                          "karussell": {"aktiv": bool((t.get("karussell") or {}).get("aktiv", False)),
                                        "layouts": [x for x in (t.get("karussell") or {}).get("layouts", []) if x in layout_ids][:10],
                                        "minuten": _zahl((t.get("karussell") or {}).get("minuten", 5), 1, 1440, int)}})
        # feste Nummer je Fernseher (virtueller Bildschirm :99+nr, DevTools-Port 9222+nr) – bleibt beim Umsortieren gleich
        belegt = set()
        for t in liste:
            if t["nr"] in belegt:
                t["nr"] = None
            belegt.add(t["nr"])
        for t in liste:
            if t["nr"] is None:
                t["nr"] = min(set(range(8)) - belegt)
                belegt.add(t["nr"])
        if not liste:
            raise Fehler("Mindestens ein Fernseher nötig")
        s["fernseher"] = liste
    ra = e.get("radio", {})
    if "sender" in ra:
        sender, ids = [], set()
        for x in ra["sender"][:200]:
            sid = _text(x.get("id", ""), 12, r"[a-z0-9]{4,12}")
            if sid in ids:
                continue
            ids.add(sid)
            url = _text(x.get("url", ""), 500, r"https?://\S+")
            sender.append({"id": sid, "name": _text(x.get("name", ""), 60) or url[:60], "url": url})
        s["radio"]["sender"] = sender
    if "region_woerter" in ra:
        s["radio"]["region_woerter"] = [_text(w, 40) for w in ra["region_woerter"] if str(w).strip()][:10]
    if "anzeigen" in ra: s["radio"]["anzeigen"] = bool(ra["anzeigen"])
    if "puffer_s" in ra: s["radio"]["puffer_s"] = _zahl(ra["puffer_s"], 0, 120, int)
    an = e.get("anzeige", {})
    if "wetter" in an: s["anzeige"]["wetter"] = _text(an["wetter"], 100, r"weather\.[a-z0-9_]+|")
    if "wetter_quelle" in an:
        s["anzeige"]["wetter_quelle"] = an["wetter_quelle"] if an["wetter_quelle"] in ("met", "ha") else "met"
    elif an.get("wetter"):
        s["anzeige"]["wetter_quelle"] = "ha"      # bis 0.6: Wetter kam immer aus HA – so lassen, bis jemand umstellt
    z = e.get("zeit", {})
    if "ntp" in z:
        s["zeit"]["ntp"] = _text(z["ntp"], 100, r"([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+|")
    if "zeitzone" in z:
        import zoneinfo
        zz = _text(z["zeitzone"], 60)
        if zz and zz not in zoneinfo.available_timezones():
            raise Fehler(f"unbekannte Zeitzone {zz!r}")
        s["zeit"]["zeitzone"] = zz
    if "vorhersage" in an: s["anzeige"]["vorhersage"] = bool(an["vorhersage"])
    if "raeume" in an:
        s["anzeige"]["raeume"] = [{"name": _text(r.get("name", ""), 30), "entity": _text(r.get("entity", ""), 100, ENTITY)}
                                  for r in an["raeume"][:4]]
    if "kacheln" in an:
        s["anzeige"]["kacheln"] = [{"name": _text(k.get("name", ""), 30), "entity": _text(k.get("entity", ""), 100, ENTITY),
                                    "icon": _text(k.get("icon", "mdi-information-outline"), 60, r"mdi-[a-z0-9-]+")}
                                   for k in an["kacheln"][:8]]
    v = e.get("video", {})
    sv = s["video"]
    if "aktiv" in v: sv["aktiv"] = bool(v["aktiv"])
    if "takt_min" in v: sv["takt_min"] = _zahl(v["takt_min"], 1, 30, int)
    if "nur_tag" in v: sv["nur_tag"] = bool(v["nur_tag"])
    if "min_sonnenhoehe" in v: sv["min_sonnenhoehe"] = _zahl(v["min_sonnenhoehe"], -18, 30)
    if "mindeststufe" in v:
        if v["mindeststufe"] not in STUFEN: raise Fehler("unbekannte Stufe")
        sv["mindeststufe"] = v["mindeststufe"]
    if "schlecht_s" in v: sv["schlecht_s"] = _zahl(v["schlecht_s"], 5, 170, int)
    if "strike_grenze" in v: sv["strike_grenze"] = _zahl(v["strike_grenze"], 1, 20, int)
    if "sperre_h" in v: sv["sperre_h"] = _zahl(v["sperre_h"], 0, 72)
    if "kategorien_aus" in v: sv["kategorien_aus"] = [k for k in v["kategorien_aus"] if k in KATEGORIEN]
    su = e.get("suche", {})
    ss = s["suche"]
    if "aktiv" in su: ss["aktiv"] = bool(su["aktiv"])
    if "uhrzeit" in su: ss["uhrzeit"] = _text(su["uhrzeit"], 5, r"([01]\d|2[0-3]):[0-5]\d")
    if "max" in su: ss["max"] = _zahl(su["max"], 0, 200, int)
    if "behalten_tage" in su: ss["behalten_tage"] = _zahl(su["behalten_tage"], 1, 365, int)
    for feld in ("begriffe", "tierwoerter", "ausschluss"):
        if feld in su:
            liste = [_text(x, 80) for x in su[feld] if str(x).strip()][:200]
            for x in liste:
                try:
                    re.compile(x)
                except re.error:
                    raise Fehler(f"ungültiges Suchmuster: {x!r}")
            ss[feld] = liste
    if "orte" in su:
        orte = []
        for o in su["orte"][:100]:
            m = _text(o.get("muster", ""), 300)
            try:
                re.compile(m)
            except re.error:
                raise Fehler(f"ungültiges Ortsmuster: {m!r}")
            orte.append({"muster": m, "breite": _zahl(o.get("breite"), -90, 90), "laenge": _zahl(o.get("laenge"), -180, 180)})
        ss["orte"] = orte
    if "einspieler" in e:
        liste, ids = [], set()
        for x in (e["einspieler"] or [])[:20]:
            eid = _text(x.get("id", ""), 12, r"[a-z0-9]{4,12}")
            if eid in ids:
                continue
            ids.add(eid)
            quelle = x.get("quelle", "tagesschau100")
            if quelle not in ("tagesschau100", "video", "youtube"):
                raise Fehler("Einspieler: unbekannte Quelle")
            url = _text(x.get("url", ""), 500, r"(https?://\S+|[\w-]{11}|UC[\w-]{22})?")
            if quelle != "tagesschau100" and not url:
                raise Fehler("Einspieler: Adresse fehlt")
            minuten = sorted({_zahl(m, 0, 59, int) for m in (x.get("minuten") or [0])})
            liste.append({"id": eid, "name": _text(x.get("name", "") or quelle, 40), "quelle": quelle, "url": url,
                          "minuten": minuten, "von": _text(x.get("von", "00:00"), 5, r"([01]\d|2[0-3]):[0-5]\d"),
                          "bis": _text(x.get("bis", "23:59"), 5, r"([01]\d|2[0-3]):[0-5]\d"), "ton": bool(x.get("ton", True)),
                          "fernseher": [str(t)[:12] for t in (x.get("fernseher") or [])][:8], "aktiv": bool(x.get("aktiv", True)),
                          # Puffer (seit 0.11): vorab = Container lädt die Ausgabe komplett herunter und spielt sie lokal ab;
                          # vorlauf = direkt vom Server, Start erst nach vorlauf_s gepufferten Sekunden; aus = direkt
                          "puffer": x.get("puffer") if x.get("puffer") in ("vorab", "vorlauf", "aus") else "vorab",
                          "vorlauf_s": _zahl(x.get("vorlauf_s", 10), 0, 60, int),
                          "vorab_mb": _zahl(x.get("vorab_mb", 0), 0, 2000, int)})      # 0 = komplett, sonst so viele MB vorab
        s["einspieler"] = liste
    up = e.get("updates", {})
    if "system" in up: s["updates"]["system"] = up["system"] if up["system"] in ("melden", "sicherheit", "auto") else "melden"
    if "signagecast" in up: s["updates"]["signagecast"] = up["signagecast"] if up["signagecast"] in ("melden", "auto") else "melden"
    for k in ("fenster_von", "fenster_bis"):
        if k in up: s["updates"][k] = _text(up[k], 5, r"([01]\d|2[0-3]):[0-5]\d")
    si = e.get("sicherung", {})
    ss_ = s["sicherung"]
    if "plan" in si: ss_["plan"] = si["plan"] if si["plan"] in ("aus", "taeglich", "woechentlich") else "aus"
    if "wochentag" in si: ss_["wochentag"] = _zahl(si["wochentag"], 0, 6, int)
    if "uhrzeit" in si: ss_["uhrzeit"] = _text(si["uhrzeit"], 5, r"([01]\d|2[0-3]):[0-5]\d")
    if "behalten" in si: ss_["behalten"] = _zahl(si["behalten"], 1, 60, int)
    if "mit_geheimnissen" in si: ss_["mit_geheimnissen"] = bool(si["mit_geheimnissen"])
    if "passwort" in si:
        ss_["passwort"] = str(si["passwort"] or "")[:200]
        if ss_["passwort"]:
            S.passwort_pruefen(ss_["passwort"])          # auch das Passwort der automatischen Sicherung muss stark sein
    if ss_["mit_geheimnissen"] and ss_["plan"] != "aus" and not ss_["passwort"]:
        raise Meldung("sich_geheim_ohne_pw")
    if "assistent_fertig" in e: s["assistent_fertig"] = bool(e["assistent_fertig"])
    wh = e.get("webhook", {})
    if "aktiv" in wh: s["webhook"]["aktiv"] = bool(wh["aktiv"])
    if "token" in wh: s["webhook"]["token"] = _text(wh.get("token") or "", 64, r"[A-Za-z0-9_-]*")
    be, sb = e.get("benachrichtigung", {}), s["benachrichtigung"]
    if isinstance(be, dict):
        tg = be.get("telegram", {})
        if "aktiv" in tg: sb["telegram"]["aktiv"] = bool(tg["aktiv"])
        if "token" in tg: sb["telegram"]["token"] = _text(tg["token"] or "", 100, r"(\d{5,15}:[A-Za-z0-9_-]{20,80})?")
        if "chat_id" in tg: sb["telegram"]["chat_id"] = _text(tg["chat_id"] or "", 40, r"(-?\d{1,20}|@[A-Za-z0-9_]{4,32})?")
        em = be.get("email", {})
        if "aktiv" in em: sb["email"]["aktiv"] = bool(em["aktiv"])
        if "server" in em: sb["email"]["server"] = _text(em["server"] or "", 200, r"[\w.\-]*")
        if "port" in em: sb["email"]["port"] = _zahl(em["port"], 1, 65535, int)
        if "sicherheit" in em: sb["email"]["sicherheit"] = em["sicherheit"] if em["sicherheit"] in ("starttls", "ssl", "keine") else "starttls"
        if "benutzer" in em: sb["email"]["benutzer"] = _text(em["benutzer"] or "", 200)
        if "passwort" in em: sb["email"]["passwort"] = _text(em["passwort"] or "", 200)
        for k in ("absender", "empfaenger"):
            if k in em: sb["email"][k] = _text(em[k] or "", 300, r"([^@\s,]+@[^@\s,]+)?(\s*,\s*[^@\s,]+@[^@\s,]+)*")
        hb = be.get("ha", {})
        if "aktiv" in hb: sb["ha"]["aktiv"] = bool(hb["aktiv"])
        if "dienst" in hb: sb["ha"]["dienst"] = _text(hb["dienst"] or "notify.notify", 100, r"notify\.[a-z0-9_]+")
        for k, w in (be.get("ereignisse") or {}).items():
            if k in sb["ereignisse"]: sb["ereignisse"][k] = bool(w)
    if "medien" in e:
        aus_m, ids_m = [], set()
        for m in (e.get("medien") or [])[:300]:
            mid = _text(m.get("id", ""), 12, r"[a-z0-9]{4,12}")
            if mid in ids_m:
                continue
            ids_m.add(mid)
            if m.get("art") not in ("bild", "video"):
                raise Fehler("Medium: Art bild oder video")
            aus_m.append({"id": mid, "name": _text(m.get("name", "") or mid, 60), "art": m["art"],
                          "datei": _text(m.get("datei", ""), 40, r"[0-9a-f]{16}\.(jpg|png|mp4|webm)"),
                          "dauer_s": _zahl(m.get("dauer_s", 15), 1, 7200), "aktiv": bool(m.get("aktiv", True))})
        s["medien"] = aus_m
    if "quellen" in e:
        try:
            s["quellen"] = Q.pruefen(e["quellen"])
        except Q.Fehler:
            raise                                  # Meldung mit Kennung (Verwaltung übersetzt sie)
    sr = e.get("stream", {})
    if "abschalten_s" in sr: s["stream"]["abschalten_s"] = _zahl(sr["abschalten_s"], 10, 3600, int)
    return s


def zusammenfuehren(alt, neu):
    """Teiländerung (z. B. nur {"video": {"takt_min": 4}}) in die bestehenden Einstellungen einarbeiten; Listen werden ersetzt."""
    erg = copy.deepcopy(alt)
    for k, w in (neu or {}).items():
        if isinstance(w, dict) and isinstance(erg.get(k), dict):
            erg[k] = zusammenfuehren(erg[k], w)
        else:
            erg[k] = w
    return erg


def laden():
    try:
        with open(PFAD) as f:
            d = json.load(f)
        if isinstance(d, dict):
            d.setdefault("assistent_fertig", True)
        return pruefen(d)
    except (FileNotFoundError, Fehler):
        return pruefen(copy.deepcopy(STANDARD))       # baut u. a. das Layout „Standard“ – sonst fehlt der TV-Seite ein Layout


def speichern(e):
    e = pruefen(e)
    tmp = PFAD + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(e, f, ensure_ascii=False, indent=1)
    os.replace(tmp, PFAD)
    return e
