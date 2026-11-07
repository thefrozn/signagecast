# Streamliste von SignageCast: feste und gefundene YouTube-Livestreams, Tag/Nacht, Live-Prüfung (schonend),
# Strikes, Qualität und tägliche Suche. Nur Python-Standardbibliothek.
# Es werden nur öffentliche Seiten gelesen (Suche, Kanal-, Videoseite, oEmbed); abgespielt wird über den
# offiziellen Einbettungsplayer. Keine Umgehung von YouTube-Sperren: bei HTTP 429 wird eine Stunde pausiert.
import json, math, os, re, threading, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from meldung import Meldung

DATEN = os.environ.get("SC_DATEN", "/var/lib/signagecast")
STREAMS = os.path.join(DATEN, "streams.json")       # {"streams": {id: {...}}, "abgelehnt": [ids]}
STRIKES = os.path.join(DATEN, "strikes.json")       # {video_id: {"strikes": n, "gruende": [...]}}
QUALITAET = os.path.join(DATEN, "qualitaet.json")   # {video_id: {...}} – Meldungen des Players und der Wache
CACHE = os.path.join(DATEN, "cache.json")           # {"quellen": {id: {"video_id", "live", "geprueft"}}, "pause_bis": t}

PRUEF_ALTER_S = 2 * 3600     # ein Stream am Tag wird höchstens alle 2 h bei YouTube geprüft
NACHT_PRUEF_S = 6 * 3600     # Nachtstreams ab und an (alle 6 h), damit tote Streams nicht erst morgens auffallen
VOR_HELL_S = 30 * 60         # wird es am Ort in 30 min hell: vorher prüfen, damit er zum Sonnenaufgang bereit ist
VOR_ALTER_S = 20 * 60        # angekündigte Streams (nächste/übernächste) müssen höchstens 20 min alt geprüft sein
VOR_MAX = 10                 # höchstens so viele Vorabprüfungen je 5 min (zusätzlich zu MAX_PRUEFUNGEN)
NACHLAUF_S = 15 * 60         # wird ein angekündigter Stream dunkel, darf er noch so lange laufen (kein falsches „Nächstes“)
MAX_PRUEFUNGEN = 6           # höchstens so viele YouTube-Prüfungen je Durchlauf (alle 5 min)
ALLGEMEIN_FENSTER_S = 10 * 60  # Strikes aus demselben Grund in diesem Fenster nimmt eine allgemeine Störung zurück
ALLGEMEIN_GUT_S = 60          # so lange misst die Wache am Stück einen guten Stream -> Störung vorbei
ALLGEMEIN_GUELTIG_S = 15 * 60  # der Player meldet die Störung alle 5 min erneut; ohne Meldung gilt sie als vorbei
THEMA_MAX = 8                 # seit 0.32: so viele gefundene Streams je Thema (zählen nicht zu „max“)
MAX_GEFUNDEN_GESAMT = 80     # harte Obergrenze gefundener Streams (die Einstellung „max“ zählt nur Streams mit Tag)
PAUSE_BEI_429_S = 3600       # YouTube sagt "zu viele Anfragen": eine Stunde gar nicht fragen
HOEHEN = [(2160, "hd2160"), (1440, "hd1440"), (1080, "hd1080"), (720, "hd720"), (480, "large"), (360, "medium"),
          (240, "small"), (1, "tiny")]
GRUENDE = {"aufloesung", "puffert", "steht", "fehler", "startet_nicht"}
STUFEN = ["tiny", "small", "medium", "large", "hd720", "hd1080", "hd1440", "hd2160", "highres"]
# Seit 0.32: Themen ohne Tiere. Je Thema eigene Suchbegriffe und Pflichtwörter im Titel; gesucht wird nur, wenn das
# Thema eingeschaltet ist (keine unnötigen Anfragen). ohne_tag: Tag/Nacht am Ort gilt nicht (ganzes Thema oder Titel).
THEMEN = {
    "stadt": {"begriffe": ["city live cam", "times square live cam", "shibuya crossing live cam", "old town square live cam",
                           "piazza live webcam", "city skyline live cam"],
              "woerter": r"city|square|plaza|piazza|platz|crossing|downtown|street|skyline|old town|altstadt|harbourfront"},
    "strand": {"begriffe": ["beach live cam", "surf live cam", "island beach live cam", "pier live cam"],
               "woerter": r"beach|strand|surf|shore|coast|küste|playa|pier|lagoon|bay\b"},
    "berge": {"begriffe": ["mountain live cam", "alps live webcam", "ski resort live cam", "summit live cam"],
              "woerter": r"mountain|alps|alpen|\bberg|ski|summit|gipfel|peak|glacier|gletscher|valley|zugspitze|matterhorn|jungfrau"},
    "hafen": {"begriffe": ["harbor live cam ships", "port live cam ship traffic", "panama canal live cam", "ferry live cam"],
              "woerter": r"\bport\b|harbou?r|hafen|ship|schiff|canal|kanal|vessel|ferry|fähre|cruise|container|lock\b|schleuse"},
    "flug": {"begriffe": ["airport live cam", "plane spotting live", "runway live cam"],
             "woerter": r"airport|flughafen|plane|runway|landing|spotting|aviation|aircraft|flugzeug"},
    "bahn": {"begriffe": ["train live cam", "railway live cam", "railcam live"],
             "woerter": r"train|railway|railroad|\brail|bahn|\bzug\b|railcam|locomotive|station"},
    "weltraum": {"begriffe": ["iss live earth from space", "nasa live stream earth", "space station live"],
                 "woerter": r"\biss\b|space station|nasa|earth from space|from space|weltraum|orbit", "ohne_tag": True},
    "natur": {"begriffe": ["volcano live cam", "northern lights live cam", "waterfall live cam", "niagara falls live cam",
                           "geyser live cam"],
              "woerter": r"volcano|vulkan|aurora|northern lights|nordlicht|waterfall|wasserfall|falls\b|geyser|geysir|eruption",
              "ohne_tag_titel": r"aurora|northern lights|nordlicht"},
}
# Für Themen: Musik, Spiele, Nachrichten, Aufzeichnungen u. Ä. aussortieren (die Tier-Ausschlüsse wie „city“, „beach“,
# „airport“ gelten hier nicht)
THEMEN_AUSSCHLUSS = re.compile(r"radio|music|song|lofi|sleep|relax|asmr|\bgame|gaming|minecraft|roblox|simulator|\bsim\b|"
                               r"msfs|cartoon|kids|news|stock|crypto|compilation|archive|documentary|movie|episode|"
                               r"meditation|ambient|screensaver|nature sounds|\bbar\b|church|hunting|\batc\b|scanner|"
                               r"police|ukraine|\bwar\b|model railway|modellbahn|gta|replay|highlights|ambien|sounds\b|\bloop\b|footage|"
                               r"\bstore\b|\bshop\b|food|display", re.I)
# Genaue Orte (vor allem für Themen-Streams) – vor der groben Liste der Einstellungen geprüft
THEMEN_ORTE = [
    (r"los angeles|venice beach|santa monica|malibu", 34.01, -118.49),
    (r"maho|st\.? ?maarten|sint maarten|saint martin", 18.04, -63.12),
    (r"times square|manhattan|new york|nyc|brooklyn", 40.76, -73.99),
    (r"las vegas", 36.17, -115.14),
    (r"new orleans", 29.95, -90.07),
    (r"north sea|nordsee|sylt|wadden|wattenmeer|helgoland", 54.5, 8.0),
    (r"dubai|abu dhabi", 25.2, 55.27),
    (r"jerusalem|tel aviv|israel", 31.78, 35.22),
    (r"istanbul|turkey|türkei", 41.01, 28.98),
    (r"iceland|reykjav|isländ", 64.13, -21.9),
    (r"philippines|philippinen|manila|davao|cebu|mayon", 12.9, 122.5),
    (r"mexico|méxico|cancun|cancún|tulum", 21.16, -86.85),
    (r"rio de janeiro|copacabana", -22.97, -43.18),
    (r"cape town|kapstadt", -33.92, 18.42),
    (r"niagara", 43.08, -79.07),
    (r"yellowstone|old faithful", 44.46, -110.83),
    (r"etna|sicily|sizilien", 37.75, 14.99),
    (r"venice|venezia|venedig", 45.43, 12.33),
    (r"prague|praha|prag", 50.09, 14.42),
    (r"paris", 48.86, 2.35),
    (r"london", 51.51, -0.13),
    (r"tromsø|tromso|lofoten|abisko|lapland|lappland", 69.0, 19.0),
]


def ohne_tag(s):
    """Tag/Nacht am Ort gilt nicht: am Stream vermerkt (z. B. Nordlicht) oder für das ganze Thema (Weltraum)."""
    return bool(s.get("ohne_tag") or THEMEN.get(s.get("kategorie"), {}).get("ohne_tag"))


ID = re.compile(r"[\w-]{11}")
KANAL = re.compile(r"UC[\w-]{22}")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
      "Accept-Language": "de-DE,de;q=0.9,en;q=0.8", "Cookie": "CONSENT=YES+1"}

sperre = threading.RLock()
cache_sperre = threading.Lock()     # Lesen-Ändern-Schreiben von cache.json (Durchlauf und Vorabprüfung laufen parallel)


class Gesperrt(Exception):
    pass


def lies(pfad, leer):
    try:
        with open(pfad) as f:
            return json.load(f)
    except Exception:
        return leer


def schreib(pfad, daten):
    tmp = pfad + ".tmp"
    with open(tmp, "w") as f:
        json.dump(daten, f, ensure_ascii=False, indent=1)
    os.replace(tmp, pfad)


def lade(url):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15).read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise Gesperrt()
        raise


def sonnenhoehe(breite, laenge, t=None):
    # Sonnenhöhe in Grad (NOAA-Näherung, genau auf ca. 1°) für Ort und Zeitpunkt
    t = time.gmtime(t)
    stunde = t.tm_hour + t.tm_min / 60
    g = 2 * math.pi / 365 * (t.tm_yday - 1 + (stunde - 12) / 24)
    zeitgl = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                       - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    dekl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    sw = math.radians((stunde * 60 + zeitgl + 4 * laenge) / 4 - 180)
    b = math.radians(breite)
    return math.degrees(math.asin(math.sin(b) * math.sin(dekl) + math.cos(b) * math.cos(dekl) * math.cos(sw)))


def hell_ab(breite, laenge, min_hoehe, jetzt=None):
    """Zeitpunkt, ab dem die Sonne am Ort über min_hoehe steht (jetzt, wenn schon); None, wenn nicht in 36 h (Polarnacht)."""
    jetzt = time.time() if jetzt is None else jetzt
    if sonnenhoehe(breite, laenge, jetzt) >= min_hoehe:
        return jetzt
    for i in range(1, 36 * 6 + 1):                # in 10-min-Schritten suchen, dann auf die Minute genau
        t = jetzt + i * 600
        if sonnenhoehe(breite, laenge, t) >= min_hoehe:
            for m in range(9, 0, -1):
                if sonnenhoehe(breite, laenge, t - m * 60) >= min_hoehe:
                    return t - m * 60
            return t
    return None


def stufe_aus_hoehe(h):
    return next((s for grenze, s in HOEHEN if h and h >= grenze), None)


def angebotene_hoehe(seite):
    """Größte angebotene Bildhöhe aus ytInitialPlayerResponse (streamingData) der Videoseite; None, wenn nicht lesbar."""
    i = seite.find("ytInitialPlayerResponse = ")
    if i < 0:
        return None
    try:
        d, _ = json.JSONDecoder().raw_decode(seite, i + len("ytInitialPlayerResponse = "))
        f = (d.get("streamingData") or {}).get("adaptiveFormats") or []
        h = [x["height"] for x in f if isinstance(x, dict) and isinstance(x.get("height"), int)]
        return max(h) if h else None
    except (ValueError, AttributeError, TypeError):
        return None


def oembed(video):
    """Titel und Kanal, wenn das Einbetten erlaubt ist (oEmbed 200), sonst None."""
    try:
        d = json.loads(lade(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video}&format=json"))
        return {"titel": d.get("title", ""), "kanal": d.get("author_name", "")}
    except Gesperrt:
        raise
    except Exception:
        return None


def seite_pruefen(video):
    """Live und einbettbar? Dazu die größte angebotene Bildhöhe – aus derselben Seite, keine weitere Abfrage."""
    try:
        seite = lade("https://www.youtube.com/watch?v=" + video)
        if '"isLiveNow":true' not in seite:
            return {"live": False, "hoehe": None}
        return {"live": oembed(video) is not None, "hoehe": angebotene_hoehe(seite)}
    except Gesperrt:
        raise
    except Exception:
        return {"live": False, "hoehe": None}


def aktuelles_video(art, ident):
    if art == "video":
        return ident
    try:   # Kanal: /live zeigt auf das aktuelle Livevideo
        m = re.search(r'<link rel="canonical" href="https://www\.youtube\.com/watch\?v=([\w-]{11})"',
                      lade(f"https://www.youtube.com/channel/{ident}/live"))
        return m.group(1) if m else None
    except Gesperrt:
        raise
    except Exception:
        return None


def aus_link(text):
    """YouTube-Link oder ID -> ("video", id) bzw. ("kanal", UC…); None, wenn nicht erkannt."""
    text = text.strip()
    if ID.fullmatch(text):
        return "video", text
    if KANAL.fullmatch(text):
        return "kanal", text
    try:
        u = urllib.parse.urlparse(text)
    except Exception:
        return None
    if not re.fullmatch(r"(www\.|m\.)?(youtube\.com|youtube-nocookie\.com|youtu\.be)", u.netloc or ""):
        return None
    if u.netloc.endswith("youtu.be") and ID.fullmatch(u.path.strip("/")):
        return "video", u.path.strip("/")
    q = urllib.parse.parse_qs(u.query)
    if "v" in q and ID.fullmatch(q["v"][0]):
        return "video", q["v"][0]
    m = re.match(r"/(?:live|embed|shorts)/([\w-]{11})", u.path)
    if m:
        return "video", m.group(1)
    m = re.match(r"/channel/(UC[\w-]{22})", u.path)
    if m:
        return "kanal", m.group(1)
    return None


class Streams:
    """Alle Daten rund um die Streams. Threadsicher über die Modul-Sperre."""

    def __init__(self, einstellungen_holen):
        self.e = einstellungen_holen          # Funktion -> aktuelle Einstellungen
        self.liste = []                       # aktuelle Rotationsliste [{video_id, name, kategorie, geschuetzt}]
        self.status = {"zeit": None, "geprueft": 0, "suche": None}
        self.vorrang = None                   # {"video_id", "name", "bis"} – "Jetzt zeigen" aus der Verwaltung
        self.zustaende = {}                   # {stream_id: {zustand, video_id, hell_ab, nachlauf}} – aus liste_bauen
        self.vorgemerkt = {}                  # {video_id: zeit} – vom Player angekündigt, Vorabprüfung fällig
        self.vor_zeiten = []                  # Zeitpunkte der Vorabprüfungen (Begrenzung je 5 min)
        self.vor_wecken = threading.Event()
        self.allgemein = None                 # {grund, seit, zeit} – allgemeine Störung, vom Player gemeldet (seit 0.31.1)
        os.makedirs(DATEN, exist_ok=True)

    # ---------- Daten ----------
    def alle(self):
        with sperre:
            return lies(STREAMS, {"streams": {}, "abgelehnt": []})

    def _speichern(self, d):
        with sperre:
            schreib(STREAMS, d)

    def strikes(self):
        return lies(STRIKES, {})

    def qualitaet(self):
        return lies(QUALITAET, {})

    def uebersicht(self):
        """Für die Verwaltung: jeder Stream mit Strikes, Qualität, Tag/Nacht und ob er gerade in der Liste ist."""
        d, st, qu, ca = self.alle(), self.strikes(), self.qualitaet(), lies(CACHE, {"quellen": {}})
        e, jetzt = self.e(), time.time()
        in_liste = {x["video_id"] for x in self.liste}
        aus, zaehler = [], {}
        for sid, s in d["streams"].items():
            z, a = self._zustand(sid, s, e, ca.get("quellen", {}), st, jetzt)
            zaehler[z] = zaehler.get(z, 0) + 1
            vid = ca["quellen"].get(sid, {}).get("video_id") or (sid if s.get("art") == "video" else None)
            q = qu.get(vid or "", {})
            h = ca["quellen"].get(sid, {}).get("hoehe")
            aus.append(dict(s, id=sid, video_id=vid,
                            strikes=st.get(vid or "", {}).get("strikes", 0),
                            strike_gruende=st.get(vid or "", {}).get("gruende", [])[-3:],
                            live=ca["quellen"].get(sid, {}).get("live"),
                            geprueft=ca["quellen"].get(sid, {}).get("geprueft"),
                            tag=sonnenhoehe(s["breite"], s["laenge"]) >= e["video"]["min_sonnenhoehe"]
                            if s.get("breite") is not None else None,
                            in_rotation=vid in in_liste, zustand=z, hell_ab=a["hell_ab"], nachlauf=a["nachlauf"],
                            angeboten=stufe_aus_hoehe(h), angeboten_hoehe=h,
                            pause_bis=(st.get(vid or "", {}).get("zeit", 0) + e["video"]["sperre_h"] * 3600) if z == "pause" else None,
                            qualitaet={k: q.get(k) for k in ("anteil_720p_plus", "verloren_prozent", "codecs",
                                                              "proben", "beste_angeboten", "zuletzt")}))
        return {"streams": sorted(aus, key=lambda x: (x.get("herkunft") != "fest", x.get("kategorie", ""), x.get("name", ""))),
                "abgelehnt": d.get("abgelehnt", []), "pause_bis": ca.get("pause_bis", 0), "zaehler": zaehler,
                "vorab": self.status.get("vorab")}

    def aendern(self, sid, felder):
        with sperre:
            d = self.alle()
            s = d["streams"].get(sid)
            if not s:
                raise KeyError(sid)
            from einstellungen import KATEGORIEN
            for k, w in felder.items():
                if k in ("aktiv", "geschuetzt"):
                    s[k] = bool(w)
                elif k == "name":
                    s[k] = str(w).strip()[:80] or s[k]
                elif k == "kategorie" and w in KATEGORIEN:
                    s[k] = w
                elif k in ("breite", "laenge"):
                    w = float(w)
                    if not (-90 <= w <= 90 if k == "breite" else -180 <= w <= 180):
                        raise Meldung("s_ort", k=k)
                    s[k] = round(w, 3)
                elif k == "herkunft" and w == "fest":
                    s[k] = "fest"            # gefundenen Stream übernehmen: verfällt nicht mehr
            self._speichern(d)
            return s

    def entfernen(self, sid, ablehnen=False):
        with sperre:
            d = self.alle()
            s = d["streams"].pop(sid, None)
            if ablehnen and sid not in d["abgelehnt"]:
                d["abgelehnt"].append(sid)
            self._speichern(d)
            return s

    def hinzufuegen(self, link, name=None, kategorie="neu", breite=None, laenge=None):
        art_id = aus_link(link)
        if not art_id:
            raise Meldung("s_kein_link")
        art, ident = art_id
        info = oembed(ident) if art == "video" else {"titel": name or ident, "kanal": ""}
        if info is None:
            raise Meldung("s_nicht_einbettbar")
        if breite is None and laenge is None:
            o = self.ort(info["titel"])
            breite, laenge = o if o else (None, None)
        with sperre:
            d = self.alle()
            d["streams"][ident] = {"art": art, "name": (name or info["titel"])[:80], "titel": info["titel"][:160],
                                   "kategorie": kategorie, "breite": breite, "laenge": laenge, "aktiv": True,
                                   "geschuetzt": False, "herkunft": "fest", "seit": time.strftime("%Y-%m-%d")}
            if ident in d["abgelehnt"]:
                d["abgelehnt"].remove(ident)
            self._speichern(d)
            return dict(d["streams"][ident], id=ident)

    def strike(self, video, grund):
        if not ID.fullmatch(video) or grund not in GRUENDE:
            return False
        geschuetzt = any(s.get("geschuetzt") and (sid == video) for sid, s in self.alle()["streams"].items()) \
            or any(x["video_id"] == video and x.get("geschuetzt") for x in self.liste)
        with sperre:
            d = self.strikes()
            e = d.setdefault(video, {"strikes": 0, "gruende": []})
            a = self.allgemein_aktiv()
            allgemein = bool(a and a["grund"] == grund)   # während einer allgemeinen Störung zählt der Strike nicht
            if not geschuetzt and not allgemein:
                e["strikes"] += 1
                e["zeit"] = int(time.time())     # seit 0.31: Pause für alle Fernseher (sperre_h), siehe _basis
            e["gruende"] = (e["gruende"] + [f"{time.strftime('%Y-%m-%d %H:%M')} {grund}" + (" (geschützt)" if geschuetzt else " (allgemein)" if allgemein else "")])[-10:]
            schreib(STRIKES, d)
        return True

    def allgemein_melden(self, grund, ende=False):
        """Der Player meldet: mehrere Streams hintereinander fallen aus demselben Grund durch (seit 0.31.1).
        Das liegt nicht an den Streams (z. B. liefert YouTube überall nur 360p) – die Strikes dieser Serie zählen nicht,
        ihre Pause entfällt. ende=True: der Player hat wieder einen Stream ohne Problem."""
        if grund not in GRUENDE:
            return False
        a, jetzt = self.allgemein, time.time()
        if ende:
            if a and a["grund"] == grund:
                self.allgemein = None
            return True
        neu = not (a and a["grund"] == grund and jetzt - a["zeit"] < ALLGEMEIN_GUELTIG_S)
        self.allgemein = {"grund": grund, "seit": time.strftime("%Y-%m-%d %H:%M") if neu else a["seit"], "zeit": jetzt}
        if neu:
            with sperre:
                d, geaendert = self.strikes(), False
                for e in d.values():
                    g = e.get("gruende") or []
                    if e.get("zeit", 0) >= jetzt - ALLGEMEIN_FENSTER_S and g and g[-1].endswith(" " + grund):
                        e["strikes"] = max(0, e.get("strikes", 0) - 1)
                        g[-1] += " (allgemein)"
                        e.pop("zeit", None)
                        geaendert = True
                if geaendert:
                    schreib(STRIKES, d)
        return True

    def _allgemein_ende_pruefen(self, m):
        """Allgemeine Störung auch ohne Meldung des Players beenden (er kann neu gestartet sein und nichts mehr davon
        wissen): misst die Wache ALLGEMEIN_GUT_S am Stück einen laufenden Stream – bei „aufloesung“ mit Mindeststufe."""
        a = self.allgemein
        if not a:
            return
        stufe, mindest = m.get("stufe"), self.e()["video"]["mindeststufe"]
        gut = m.get("zustand") == 1 and (a["grund"] != "aufloesung"
                                         or (stufe in STUFEN and STUFEN.index(stufe) >= STUFEN.index(mindest)))
        if not gut:
            a.pop("gut_seit", None)
        elif time.time() - a.setdefault("gut_seit", time.time()) >= ALLGEMEIN_GUT_S:
            self.allgemein = None

    def allgemein_aktiv(self):
        a = self.allgemein
        return {"grund": a["grund"], "seit": a["seit"]} if a and time.time() - a["zeit"] < ALLGEMEIN_GUELTIG_S else None

    def strikes_zuruecksetzen(self, video):
        with sperre:
            d = self.strikes()
            d.pop(video, None)
            schreib(STRIKES, d)

    def qualitaet_melden(self, video, stufe, beste, phase):
        if (not ID.fullmatch(video) or stufe not in STUFEN + ["auto", "unknown"]
                or beste not in STUFEN + ["unknown"] or phase not in ("start", "ende")):
            return False
        with sperre:
            d = self.qualitaet()
            e = d.setdefault(video, {})
            feld = "stufen" if phase == "start" else "stufen_ende"
            e.setdefault(feld, {})
            e[feld][stufe] = e[feld].get(stufe, 0) + 1
            if beste in STUFEN:
                e["beste_angeboten"] = max([beste, e.get("beste_angeboten", "tiny")], key=lambda q: STUFEN.index(q) if q in STUFEN else -1)
            e["zuletzt"] = time.strftime("%Y-%m-%d %H:%M")
            schreib(QUALITAET, d)
        return True

    def wache_melden(self, m, vorher):
        """Messung der Wache (alle 10 s) in die Qualitätsübersicht einrechnen."""
        if not ID.fullmatch(m.get("id", "")):
            return
        self._allgemein_ende_pruefen(m)
        gut = set(STUFEN[STUFEN.index("hd720"):])
        with sperre:
            d = self.qualitaet()
            e = d.setdefault(m["id"], {})
            e["proben"] = e.get("proben", 0) + 1
            e["gut"] = e.get("gut", 0) + (m.get("stufe") in gut)
            if vorher and vorher.get("id") == m["id"] and m.get("bilder", 0) >= vorher.get("bilder", 0):
                e["bilder"] = e.get("bilder", 0) + m["bilder"] - vorher["bilder"]
                e["verloren"] = e.get("verloren", 0) + max(0, m.get("verloren", 0) - vorher.get("verloren", 0))
            if m.get("codec") and m["codec"] not in e.setdefault("codecs", []):
                e["codecs"].append(m["codec"])
            e["anteil_720p_plus"] = round(e["gut"] / e["proben"], 2)
            e["verloren_prozent"] = round(100 * e.get("verloren", 0) / e["bilder"], 2) if e.get("bilder") else 0
            if m.get("angeboten"):
                best = [q for q in m["angeboten"] if q in STUFEN]
                if best:
                    e["beste_angeboten"] = max(best, key=STUFEN.index)
            e["zuletzt"] = time.strftime("%Y-%m-%d %H:%M")
            schreib(QUALITAET, d)

    # ---------- Ort aus dem Titel ----------
    def ort(self, titel):
        for muster, b, l in THEMEN_ORTE:                   # genaue Orte zuerst (seit 0.32)
            if re.search(muster, titel, re.I):
                return b, l
        for o in self.e()["suche"]["orte"]:
            try:
                if re.search(o["muster"], titel, re.I):
                    return o["breite"], o["laenge"]
            except re.error:
                continue
        return None

    # ---------- Zustand je Stream (seit 0.31) ----------
    def _zustand(self, sid, s, e, qc, st, jetzt):
        """(zustand, angaben) eines Streams. zustand: inaktiv, kategorie_aus, ohne_ort, nacht, ungeprueft, nicht_live,
        gesperrt, pause, qualitaet, bereit. angaben: video_id, hell_ab, nachlauf (gerade dunkel geworden, noch zeigbar)."""
        v = e["video"]
        a = {"video_id": None, "hell_ab": None, "nachlauf": False}
        x = qc.get(sid)
        if x is None and s.get("art", "video") == "video":
            x = {"video_id": sid, "live": True}            # nie geprüft: feste Videos zunächst als live annehmen
        a["video_id"] = (x or {}).get("video_id")
        if not s.get("aktiv", True):
            return "inaktiv", a
        if s.get("kategorie") in v["kategorien_aus"]:
            return "kategorie_aus", a
        if ohne_tag(s):
            return self._basis(s, x, e, st, jetzt), a      # seit 0.32: z. B. Weltraum – Tag/Nacht am Ort gilt nicht
        if s.get("breite") is None:
            return "ohne_ort", a                           # Ort unbekannt: Tag/Nacht nicht bestimmbar
        basis = self._basis(s, x, e, st, jetzt)
        if v["nur_tag"] and sonnenhoehe(s["breite"], s["laenge"], jetzt) < v["min_sonnenhoehe"]:
            a["hell_ab"] = hell_ab(s["breite"], s["laenge"], v["min_sonnenhoehe"], jetzt)
            a["nachlauf"] = basis == "bereit" and sonnenhoehe(s["breite"], s["laenge"], jetzt - NACHLAUF_S) >= v["min_sonnenhoehe"]
            return "nacht", a
        return basis, a

    def _basis(self, s, x, e, st, jetzt):
        """Live, Strikes und Qualität – unabhängig von Tag/Nacht."""
        v = e["video"]
        if x is None:
            return "ungeprueft"                            # Kanal noch nie geprüft: aktuelles Video unbekannt
        vid = x.get("video_id")
        if not x.get("live") or not vid:
            return "nicht_live"
        if s.get("geschuetzt"):
            return "bereit"                                # geschützte nie wegen Strikes oder Auflösung aussortieren
        k = st.get(vid, {})
        if k.get("strikes", 0) >= v["strike_grenze"]:
            return "gesperrt"
        if k.get("zeit", 0) + v["sperre_h"] * 3600 > jetzt:
            return "pause"                                 # letzter Strike noch nicht lange her (für alle Fernseher)
        stufe = stufe_aus_hoehe(x.get("hoehe"))
        if stufe and STUFEN.index(stufe) < STUFEN.index(v["mindeststufe"]):
            return "qualitaet"                             # bietet weniger als die Mindeststufe an
        return "bereit"

    def _pruefplan(self, d, e, qc, jetzt):
        """Welche Streams der Durchlauf bei YouTube prüft, nach Vorrang: (1) wird in 30 min hell, (2) Tag, älter als 2 h,
        (3) Nacht, älter als 6 h. Innerhalb gleichen Vorrangs der am längsten nicht geprüfte zuerst."""
        v = e["video"]
        plan = []
        for sid, s in d["streams"].items():
            if not s.get("aktiv", True) or s.get("kategorie") in v["kategorien_aus"] or (s.get("breite") is None and not ohne_tag(s)):
                continue
            alt = jetzt - qc.get(sid, {}).get("geprueft", 0)
            if not v["nur_tag"] or ohne_tag(s) or sonnenhoehe(s["breite"], s["laenge"], jetzt) >= v["min_sonnenhoehe"]:
                if alt > PRUEF_ALTER_S:
                    plan.append((2, -alt, sid, s))
                continue
            h = hell_ab(s["breite"], s["laenge"], v["min_sonnenhoehe"], jetzt)
            if h is not None and h - jetzt <= VOR_HELL_S and alt > VOR_HELL_S:
                plan.append((1, -alt, sid, s))
            elif alt > NACHT_PRUEF_S:
                plan.append((3, -alt, sid, s))
        return [(sid, s) for *_, sid, s in sorted(plan, key=lambda p: p[:2])]

    def _pruefen(self, auftraege):
        """auftraege [(sid, stream)] bei YouTube prüfen (höchstens 3 gleichzeitig) und ins cache.json schreiben.
        Rückgabe: Anzahl geprüfter. Bei HTTP 429 eine Stunde Pause für alle Prüfungen und die Suche."""
        if not auftraege:
            return 0
        if time.time() < lies(CACHE, {}).get("pause_bis", 0):
            return 0
        jetzt, erg, gesperrt = time.time(), {}, False

        def pruefe(k):
            sid, s = k
            vid = aktuelles_video(s.get("art", "video"), sid)
            r = seite_pruefen(vid) if vid else {"live": False, "hoehe": None}
            return sid, {"video_id": vid, "live": bool(vid and r["live"]), "hoehe": r["hoehe"], "geprueft": jetzt}
        try:
            with ThreadPoolExecutor(max_workers=3) as pool:
                for sid, x in pool.map(pruefe, auftraege):
                    erg[sid] = x
        except Gesperrt:
            gesperrt = True
        with cache_sperre:
            cache = lies(CACHE, {"quellen": {}, "pause_bis": 0})
            cache.setdefault("quellen", {}).update(erg)
            if gesperrt:
                cache["pause_bis"] = jetzt + PAUSE_BEI_429_S
            schreib(CACHE, cache)
        return len(erg)

    # ---------- Rotationsliste (alle 5 min) ----------
    def aktualisieren(self):
        e = self.e()
        jetzt = time.time()
        geprueft = self._pruefen(self._pruefplan(self.alle(), e, lies(CACHE, {"quellen": {}}).get("quellen", {}), jetzt)[:MAX_PRUEFUNGEN])
        self.liste_bauen()
        self.status.update(zeit=time.strftime("%Y-%m-%d %H:%M"), geprueft=geprueft, anzahl=len(self.liste),
                           pause_bis=lies(CACHE, {}).get("pause_bis", 0))
        return self.liste

    def liste_bauen(self):
        """Rotation aus den Zuständen – ohne YouTube zu fragen. In der Liste stehen nur bereite Streams und solche, die
        gerade dunkel geworden sind (nachlauf: der Player kündigt sie nicht neu an, zeigt sie aber, wenn schon angekündigt)."""
        e, jetzt = self.e(), time.time()
        d, st = self.alle(), self.strikes()
        qc = lies(CACHE, {"quellen": {}}).get("quellen", {})
        gefunden, zust = [], {}
        for sid, s in d["streams"].items():
            z, a = self._zustand(sid, s, e, qc, st, jetzt)
            zust[sid] = dict(a, zustand=z)
            if (z == "bereit" or a["nachlauf"]) and a["video_id"]:
                gefunden.append({"video_id": a["video_id"], "name": s["name"], "kategorie": s.get("kategorie", "neu"),
                                 "geschuetzt": bool(s.get("geschuetzt")), "nachlauf": z == "nacht",
                                 "geprueft": int(qc.get(sid, {}).get("geprueft", 0))})
        # Abwechslung: jede Kategorie gleichmäßig über den Durchlauf verteilen
        nach_kat = {}
        for x in gefunden:
            nach_kat.setdefault(x["kategorie"], []).append(x)
        verteilt = sorted(((i + 0.5) / len(l), k, i, x["video_id"], x) for k, l in nach_kat.items() for i, x in enumerate(l))
        self.zustaende = zust
        self.liste = [x for *_, x in verteilt]
        return self.liste

    # ---------- Vorabprüfung angekündigter Streams (seit 0.31) ----------
    def vormerken(self, videos):
        """Der Player meldet seinen nächsten und übernächsten Stream. Sind sie länger als VOR_ALTER_S nicht geprüft,
        prüft die Vorabprüfung sie sofort – unabhängig vom Wechsel. True, wenn etwas zu prüfen ist."""
        ids = [v for v in videos if isinstance(v, str) and ID.fullmatch(v)][:3]
        with sperre:
            for v in ids:
                self.vorgemerkt[v] = time.time()
        if ids:
            self.vor_wecken.set()
        return bool(ids)

    def vorpruefen(self):
        """Gemerkte Streams prüfen, wenn nötig; danach die Liste neu bauen (fällt einer durch, kündigt der Player sofort
        einen anderen an). Höchstens VOR_MAX Prüfungen je 5 min. Rückgabe: Anzahl geprüfter."""
        jetzt = time.time()
        with sperre:
            ids = [v for v, t in self.vorgemerkt.items() if jetzt - t < 600]
            self.vorgemerkt = {}
            self.vor_zeiten = [t for t in self.vor_zeiten if jetzt - t < 300]
            frei = VOR_MAX - len(self.vor_zeiten)
        if not ids or frei <= 0:
            return 0
        d = self.alle()
        qc = lies(CACHE, {"quellen": {}}).get("quellen", {})
        auftraege = []
        for sid, s in d["streams"].items():
            x = qc.get(sid)
            vid = (x or {}).get("video_id") or (sid if s.get("art", "video") == "video" else None)
            if vid in ids and jetzt - (x or {}).get("geprueft", 0) > VOR_ALTER_S:
                auftraege.append((sid, s))
        auftraege = auftraege[:frei]
        with sperre:
            self.vor_zeiten += [jetzt] * len(auftraege)
        n = self._pruefen(auftraege)
        if n:
            self.liste_bauen()
            self.status["vorab"] = {"zeit": time.strftime("%Y-%m-%d %H:%M"), "geprueft": n}
        return n

    # ---------- Suche (täglich) ----------
    def _suche(self, begriff):
        try:
            t = lade("https://www.youtube.com/results?search_query=" + urllib.parse.quote(begriff) + "&sp=EgJAAQ%253D%253D")
            d = json.loads(re.search(r"var ytInitialData = (\{.*?\});</script>", t).group(1))
        except Gesperrt:
            raise
        except Exception:
            return []
        funde = []

        def lauf(o):
            if isinstance(o, dict):
                v = o.get("videoRenderer")
                if v and "LIVE" in json.dumps(v.get("badges", [])):
                    funde.append((v["videoId"], "".join(r.get("text", "") for r in v.get("title", {}).get("runs", []))))
                for x in o.values():
                    lauf(x)
            elif isinstance(o, list):
                for x in o:
                    lauf(x)
        lauf(d)
        return funde

    @staticmethod
    def kurzname(titel):
        t = re.sub(r"[^\w\s·,.:'&()/-]", "", titel)
        t = re.sub(r"\b(LIVE|Live|live|24/7|4K|HD|powered by EXPLORE\.org|explore\.org)\b", "", t)
        t = re.split(r"\s[|–—]\s|\s-\s|\s/\s", t)[0]
        return re.sub(r"\s+", " ", t).strip(" -:,")[:55]

    @staticmethod
    def ueberzaehlig(streams, max_tag, v, jetzt=None):
        """Gefundene Streams, die raus müssen (seit 0.31): „max“ zählt nur Streams, an deren Ort gerade Tag ist –
        Nacht und „Ort unbekannt“ belegen keinen Platz. Insgesamt höchstens MAX_GEFUNDEN_GESAMT; darüber gehen zuerst
        die ohne Ort, dann die am längsten nicht mehr gefundenen. Geschützte und übernommene zählen nie mit.
        Seit 0.32 zählen Themen-Streams nicht mit: je Thema höchstens THEMA_MAX (die zuletzt gefundenen bleiben)."""
        jetzt = time.time() if jetzt is None else jetzt
        entdeckt = sorted((k for k, s in streams.items() if s.get("herkunft") == "entdeckt" and not s.get("geschuetzt")),
                          key=lambda k: (streams[k].get("breite") is not None, streams[k].get("zuletzt_gefunden", "")), reverse=True)
        raus, tag, behalten, je_thema = [], 0, 0, {}
        for k in entdeckt:
            s = streams[k]
            if s.get("kategorie") in THEMEN:
                je_thema[s["kategorie"]] = je_thema.get(s["kategorie"], 0) + 1
                if je_thema[s["kategorie"]] > THEMA_MAX:
                    raus.append(k)
                continue
            ist_tag = s.get("breite") is not None and (not v["nur_tag"] or
                                                       sonnenhoehe(s["breite"], s["laenge"], jetzt) >= v["min_sonnenhoehe"])
            if (ist_tag and tag >= max_tag) or behalten >= MAX_GEFUNDEN_GESAMT:
                raus.append(k)
                continue
            tag += ist_tag
            behalten += 1
        return raus

    def suchen(self):
        e = self.e()
        su, v = e["suche"], e["video"]
        cache = lies(CACHE, {"quellen": {}, "pause_bis": 0})
        if time.time() < cache.get("pause_bis", 0):
            self.status["suche"] = {"zeit": time.strftime("%Y-%m-%d %H:%M"), "pause": True, "neu": []}
            return self.status["suche"]
        tier = re.compile("|".join(su["tierwoerter"]) or "^$", re.I)
        nein = re.compile("|".join(su["ausschluss"]) or "^$", re.I)
        d = self.alle()
        st = self.strikes()
        # Seit 0.32 zusätzlich je eingeschaltetem Thema; Tier-Treffer haben Vorrang
        themen = [k for k in THEMEN if k not in v["kategorien_aus"]]
        auftraege = [(b, None) for b in su["begriffe"]] + [(b, k) for k in themen for b in THEMEN[k]["begriffe"]]
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                ergebnisse = list(pool.map(lambda a: (a[1], self._suche(a[0])), auftraege))
        except Gesperrt:
            cache["pause_bis"] = time.time() + PAUSE_BEI_429_S
            schreib(CACHE, cache)
            self.status["suche"] = {"zeit": time.strftime("%Y-%m-%d %H:%M"), "pause": True, "neu": []}
            return self.status["suche"]
        heute = time.strftime("%Y-%m-%d")
        funde, kat = {}, {}
        for k, liste in ergebnisse:
            for vid, t in liste:
                funde.setdefault(vid, t)
        bekannt = lambda vid: vid in d["streams"] or vid in d["abgelehnt"] or st.get(vid, {}).get("strikes", 0) >= v["strike_grenze"]
        neu_ids = [vid for k, liste in ergebnisse if k is None for vid, t in liste
                   if not bekannt(vid) and tier.search(t) and not nein.search(t)]
        neu_ids = list(dict.fromkeys(neu_ids))[:30]
        for k in themen:
            wort = re.compile(THEMEN[k]["woerter"], re.I)
            ids = [vid for kk, liste in ergebnisse if kk == k for vid, t in liste
                   if not bekannt(vid) and vid not in neu_ids and vid not in kat
                   and wort.search(t) and not THEMEN_AUSSCHLUSS.search(t)]
            orte = {}
            for vid in dict.fromkeys(ids):
                o = self.ort(funde[vid])
                if o and orte.get(o, 0) >= 2:
                    continue                      # höchstens 2 vom selben Ort je Thema (sonst 6× Times Square)
                orte[o] = orte.get(o, 0) + (o is not None)
                kat[vid] = k
                if sum(1 for x in kat.values() if x == k) >= THEMA_MAX:
                    break
        neu_ids += list(kat)

        def einbettbar(vid):
            try:
                return vid if oembed(vid) else None
            except Gesperrt:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            ok = [vid for vid in pool.map(einbettbar, neu_ids) if vid]
        neu = []
        with sperre:
            d = self.alle()
            for vid in ok:
                if vid in d["streams"] or vid in d["abgelehnt"]:
                    continue                      # inzwischen anders bekannt (z. B. Profil eingespielt) – nie überschreiben
                o = self.ort(funde[vid])
                k = kat.get(vid, "neu")
                th = THEMEN.get(k, {})
                d["streams"][vid] = {"art": "video", "name": self.kurzname(funde[vid]), "titel": funde[vid][:160],
                                     "kategorie": k, "breite": o[0] if o else None, "laenge": o[1] if o else None,
                                     "aktiv": True, "geschuetzt": False, "herkunft": "entdeckt", "seit": heute,
                                     "zuletzt_gefunden": heute}
                if th.get("ohne_tag") or (th.get("ohne_tag_titel") and re.search(th["ohne_tag_titel"], funde[vid], re.I)):
                    d["streams"][vid]["ohne_tag"] = True
                neu.append(d["streams"][vid]["name"])
            for vid in funde:
                if vid in d["streams"] and d["streams"][vid].get("herkunft") == "entdeckt":
                    d["streams"][vid]["zuletzt_gefunden"] = heute
            # Aufräumen: lange nicht gefunden oder gesperrt -> raus (geschützte und übernommene bleiben)
            grenze = time.strftime("%Y-%m-%d", time.localtime(time.time() - su["behalten_tage"] * 86400))
            for vid in [k for k, s in d["streams"].items() if s.get("herkunft") == "entdeckt" and not s.get("geschuetzt")
                        and (s.get("zuletzt_gefunden", "") < grenze or st.get(k, {}).get("strikes", 0) >= v["strike_grenze"])]:
                d["streams"].pop(vid)
            for vid in self.ueberzaehlig(d["streams"], su["max"], v):
                d["streams"].pop(vid)
            self._speichern(d)
        self.status["suche"] = {"zeit": time.strftime("%Y-%m-%d %H:%M"), "pause": False, "neu": neu,
                                "gefunden": len(funde)}
        return self.status["suche"]
