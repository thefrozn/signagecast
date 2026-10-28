# Streamliste von SignageCast: feste und gefundene YouTube-Livestreams, Tag/Nacht, Live-Prüfung (schonend),
# Strikes, Qualität und tägliche Suche. Nur Python-Standardbibliothek.
# Es werden nur öffentliche Seiten gelesen (Suche, Kanal-, Videoseite, oEmbed); abgespielt wird über den
# offiziellen Einbettungsplayer. Keine Umgehung von YouTube-Sperren: bei HTTP 429 wird eine Stunde pausiert.
import json, math, os, re, threading, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

DATEN = os.environ.get("SC_DATEN", "/var/lib/signagecast")
STREAMS = os.path.join(DATEN, "streams.json")       # {"streams": {id: {...}}, "abgelehnt": [ids]}
STRIKES = os.path.join(DATEN, "strikes.json")       # {video_id: {"strikes": n, "gruende": [...]}}
QUALITAET = os.path.join(DATEN, "qualitaet.json")   # {video_id: {...}} – Meldungen des Players und der Wache
CACHE = os.path.join(DATEN, "cache.json")           # {"quellen": {id: {"video_id", "live", "geprueft"}}, "pause_bis": t}

PRUEF_ALTER_S = 2 * 3600     # ein Stream wird höchstens alle 2 h bei YouTube geprüft
MAX_PRUEFUNGEN = 6           # höchstens so viele YouTube-Prüfungen je Durchlauf (alle 5 min)
PAUSE_BEI_429_S = 3600       # YouTube sagt "zu viele Anfragen": eine Stunde gar nicht fragen
GRUENDE = {"aufloesung", "puffert", "steht", "fehler", "startet_nicht"}
STUFEN = ["tiny", "small", "medium", "large", "hd720", "hd1080", "hd1440", "hd2160", "highres"]
ID = re.compile(r"[\w-]{11}")
KANAL = re.compile(r"UC[\w-]{22}")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
      "Accept-Language": "de-DE,de;q=0.9,en;q=0.8", "Cookie": "CONSENT=YES+1"}

sperre = threading.RLock()


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


def oembed(video):
    """Titel und Kanal, wenn das Einbetten erlaubt ist (oEmbed 200), sonst None."""
    try:
        d = json.loads(lade(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video}&format=json"))
        return {"titel": d.get("title", ""), "kanal": d.get("author_name", "")}
    except Gesperrt:
        raise
    except Exception:
        return None


def ist_live_und_einbettbar(video):
    try:
        if '"isLiveNow":true' not in lade("https://www.youtube.com/watch?v=" + video):
            return False
        return oembed(video) is not None
    except Gesperrt:
        raise
    except Exception:
        return False


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
        e = self.e()
        in_liste = {x["video_id"] for x in self.liste}
        aus = []
        for sid, s in d["streams"].items():
            vid = ca["quellen"].get(sid, {}).get("video_id") or (sid if s.get("art") == "video" else None)
            q = qu.get(vid or "", {})
            aus.append(dict(s, id=sid, video_id=vid,
                            strikes=st.get(vid or "", {}).get("strikes", 0),
                            strike_gruende=st.get(vid or "", {}).get("gruende", [])[-3:],
                            live=ca["quellen"].get(sid, {}).get("live"),
                            geprueft=ca["quellen"].get(sid, {}).get("geprueft"),
                            tag=sonnenhoehe(s["breite"], s["laenge"]) >= e["video"]["min_sonnenhoehe"]
                            if s.get("breite") is not None else None,
                            in_rotation=vid in in_liste,
                            qualitaet={k: q.get(k) for k in ("anteil_720p_plus", "verloren_prozent", "codecs",
                                                              "proben", "beste_angeboten", "zuletzt")}))
        return {"streams": sorted(aus, key=lambda x: (x.get("herkunft") != "fest", x.get("kategorie", ""), x.get("name", ""))),
                "abgelehnt": d.get("abgelehnt", []), "pause_bis": ca.get("pause_bis", 0)}

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
                        raise ValueError(k)
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
            raise ValueError("Kein YouTube-Video- oder Kanal-Link erkannt")
        art, ident = art_id
        info = oembed(ident) if art == "video" else {"titel": name or ident, "kanal": ""}
        if info is None:
            raise ValueError("Dieses Video darf nicht eingebettet werden (oder existiert nicht)")
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
            if not geschuetzt:
                e["strikes"] += 1
            e["gruende"] = (e["gruende"] + [f"{time.strftime('%Y-%m-%d %H:%M')} {grund}" + (" (geschützt)" if geschuetzt else "")])[-10:]
            schreib(STRIKES, d)
        return True

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
        for o in self.e()["suche"]["orte"]:
            try:
                if re.search(o["muster"], titel, re.I):
                    return o["breite"], o["laenge"]
            except re.error:
                continue
        return None

    # ---------- Rotationsliste (alle 5 min) ----------
    def aktualisieren(self):
        e = self.e()
        v = e["video"]
        jetzt = time.time()
        d = self.alle()
        st = self.strikes()
        gesperrt = {vid for vid, x in st.items() if x.get("strikes", 0) >= v["strike_grenze"]}
        cache = lies(CACHE, {"quellen": {}, "pause_bis": 0})
        qc = cache.setdefault("quellen", {})

        kandidaten = []
        for sid, s in d["streams"].items():
            if not s.get("aktiv", True) or s.get("kategorie") in v["kategorien_aus"]:
                continue
            if s.get("breite") is None:
                continue                                  # Ort unbekannt: Tag/Nacht nicht bestimmbar
            if v["nur_tag"] and sonnenhoehe(s["breite"], s["laenge"]) < v["min_sonnenhoehe"]:
                continue
            kandidaten.append((sid, s))

        faellig = sorted((k for k in kandidaten if jetzt - qc.get(k[0], {}).get("geprueft", 0) > PRUEF_ALTER_S),
                         key=lambda k: qc.get(k[0], {}).get("geprueft", 0))[:MAX_PRUEFUNGEN]
        geprueft = 0
        if jetzt >= cache.get("pause_bis", 0):
            def pruefe(k):
                sid, s = k
                vid = aktuelles_video(s.get("art", "video"), sid)
                return sid, {"video_id": vid, "live": bool(vid and ist_live_und_einbettbar(vid)), "geprueft": jetzt}
            try:
                with ThreadPoolExecutor(max_workers=3) as pool:
                    for sid, x in pool.map(pruefe, faellig):
                        qc[sid] = x
                        geprueft += 1
            except Gesperrt:
                cache["pause_bis"] = jetzt + PAUSE_BEI_429_S
        schreib(CACHE, cache)

        gefunden = []
        for sid, s in kandidaten:
            x = qc.get(sid)
            if x is None:
                if s.get("art") != "video":
                    continue
                x = {"video_id": sid, "live": True}       # nie geprüft: feste Videos zunächst als live annehmen
            vid = x.get("video_id")
            if x.get("live") and vid and (vid not in gesperrt or s.get("geschuetzt")):
                gefunden.append({"video_id": vid, "name": s["name"], "kategorie": s.get("kategorie", "neu"),
                                 "geschuetzt": bool(s.get("geschuetzt"))})
        # Abwechslung: jede Kategorie gleichmäßig über den Durchlauf verteilen
        nach_kat = {}
        for x in gefunden:
            nach_kat.setdefault(x["kategorie"], []).append(x)
        verteilt = sorted(((i + 0.5) / len(l), k, i, x) for k, l in nach_kat.items() for i, x in enumerate(l))
        self.liste = [x for *_, x in verteilt]
        self.status.update(zeit=time.strftime("%Y-%m-%d %H:%M"), geprueft=geprueft, anzahl=len(self.liste),
                           pause_bis=cache.get("pause_bis", 0))
        return self.liste

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
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                funde = {vid: t for l in pool.map(self._suche, su["begriffe"]) for vid, t in l}
        except Gesperrt:
            cache["pause_bis"] = time.time() + PAUSE_BEI_429_S
            schreib(CACHE, cache)
            self.status["suche"] = {"zeit": time.strftime("%Y-%m-%d %H:%M"), "pause": True, "neu": []}
            return self.status["suche"]
        heute = time.strftime("%Y-%m-%d")
        neu_ids = [vid for vid, t in funde.items() if vid not in d["streams"] and vid not in d["abgelehnt"]
                   and tier.search(t) and not nein.search(t)
                   and st.get(vid, {}).get("strikes", 0) < v["strike_grenze"]][:30]

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
                d["streams"][vid] = {"art": "video", "name": self.kurzname(funde[vid]), "titel": funde[vid][:160],
                                     "kategorie": "neu", "breite": o[0] if o else None, "laenge": o[1] if o else None,
                                     "aktiv": True, "geschuetzt": False, "herkunft": "entdeckt", "seit": heute,
                                     "zuletzt_gefunden": heute}
                neu.append(d["streams"][vid]["name"])
            for vid in funde:
                if vid in d["streams"] and d["streams"][vid].get("herkunft") == "entdeckt":
                    d["streams"][vid]["zuletzt_gefunden"] = heute
            # Aufräumen: lange nicht gefunden oder gesperrt -> raus (geschützte und übernommene bleiben)
            grenze = time.strftime("%Y-%m-%d", time.localtime(time.time() - su["behalten_tage"] * 86400))
            for vid in [k for k, s in d["streams"].items() if s.get("herkunft") == "entdeckt" and not s.get("geschuetzt")
                        and (s.get("zuletzt_gefunden", "") < grenze or st.get(k, {}).get("strikes", 0) >= v["strike_grenze"])]:
                d["streams"].pop(vid)
            entdeckt = sorted((k for k, s in d["streams"].items() if s.get("herkunft") == "entdeckt" and not s.get("geschuetzt")),
                              key=lambda k: d["streams"][k].get("zuletzt_gefunden", ""), reverse=True)
            for vid in entdeckt[su["max"]:]:
                d["streams"].pop(vid)
            self._speichern(d)
        self.status["suche"] = {"zeit": time.strftime("%Y-%m-%d %H:%M"), "pause": False, "neu": neu,
                                "gefunden": len(funde)}
        return self.status["suche"]
