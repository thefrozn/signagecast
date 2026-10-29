# Datenquellen: eigene API-Abfragen (JSON/Text), RSS-/Atom-Feeds und Bilder, die der Datendienst regelmäßig holt.
# Die TV-Seite bekommt nie die Abfrage selbst (Adresse, Kopfzeilen, Schlüssel), sondern nur die fertigen Werte der
# Bausteine im aktuellen Layout. Abruf nur http/https, Antwort höchstens 1 MB (Bilder 5 MB), Zeitlimit 10 s; bei
# Fehlern wird der Abstand bis zum nächsten Versuch verdoppelt (höchstens 1 h). Nur Python-Standardbibliothek.
import base64, datetime, email.utils, json, os, re, shlex, threading, time, urllib.error, urllib.parse, urllib.request, zoneinfo
import xml.etree.ElementTree as ET

MASKE = "••••"                    # so erscheinen geheime Kopfzeilen in der Verwaltung
ARTEN = ("json", "text", "rss", "bild", "ical", "video")
FORMATE = ("auto", "rtsp", "hls", "mjpeg")          # Video: wie die Kamera liefert (auto = aus der Adresse)
MAX_BYTES, MAX_BILD = 1_000_000, 5_000_000
UA = "SignageCast (+https://github.com/thefrozn/signagecast)"
GEHEIM_KOPF = re.compile(r"authorization|api[-_]?key|token|secret|cookie|passw", re.I)
PLATZHALTER = re.compile(r"\{([^{}]{1,160})\}")


class Fehler(Exception):
    pass


# ---------- Prüfen (Einstellungen) ----------
def pruefen(liste):
    aus, ids = [], set()
    for q in (liste or [])[:30]:
        qid = str(q.get("id", "")).strip().lower()
        if not re.fullmatch(r"[a-z0-9_]{2,16}", qid) or qid in ids:
            raise Fehler(f"Datenquelle: ungültige oder doppelte Kennung {qid!r} (2–16 Zeichen a–z, 0–9, _)")
        ids.add(qid)
        art = q.get("art", "json")
        if art not in ARTEN:
            raise Fehler("Datenquelle: Art json, text, rss, bild, ical oder video")
        url = str(q.get("url", "")).strip()
        if art == "video":
            if not re.fullmatch(r"(rtsps?|https?)://[^\s\"']{1,1000}", url):
                raise Fehler(f"Datenquelle {qid}: Kamera-Adresse mit rtsp://, rtsps://, http:// oder https://")
        elif not re.fullmatch(r"https?://\S{1,1000}", url):
            raise Fehler(f"Datenquelle {qid}: Adresse muss mit http:// oder https:// beginnen")
        methode = q.get("methode", "GET") if q.get("methode") in ("GET", "POST") else "GET"
        kopf = []
        for k in (q.get("kopf") or [])[:20]:
            name = str(k.get("name", "")).strip()
            if not name:
                continue
            if not re.fullmatch(r"[A-Za-z0-9!#$%&'*+.^_`|~-]{1,80}", name):
                raise Fehler(f"Datenquelle {qid}: ungültiger Kopfzeilen-Name {name!r}")
            wert = str(k.get("wert", ""))
            if "\n" in wert or "\r" in wert or len(wert) > 4000:
                raise Fehler(f"Datenquelle {qid}: ungültiger Wert für {name}")
            kopf.append({"name": name, "wert": wert, "geheim": bool(k.get("geheim", False))})
        try:
            intervall = int(q.get("intervall_s", 300))
        except (TypeError, ValueError):
            raise Fehler("Datenquelle: Intervall in Sekunden")
        aus.append({"id": qid, "name": str(q.get("name", "") or qid)[:40], "art": art, "url": url, "methode": methode,
                    "kopf": kopf, "inhalt": str(q.get("inhalt", ""))[:8000] if methode == "POST" else "",
                    "intervall_s": max(30, min(86400, intervall)), "aktiv": bool(q.get("aktiv", True)),
                    "format": q.get("format") if q.get("format") in FORMATE else "auto"})
    return aus


def video_format(q):
    """rtsp | hls | mjpeg – bei „auto“ aus der Adresse (rtsp:// bzw. .m3u8, sonst MJPEG)."""
    if q.get("format", "auto") != "auto":
        return q["format"]
    if q["url"].startswith("rtsp"):
        return "rtsp"
    return "hls" if ".m3u8" in q["url"].split("?")[0] else "mjpeg"


def _url_passwort(url, ersatz):
    """Passwort in der Adresse (rtsp://benutzer:passwort@kamera/…) ersetzen; (neue Adresse, altes Passwort)."""
    t = urllib.parse.urlsplit(url)
    if t.password is None:
        return url, None
    host = f"[{t.hostname}]" if ":" in (t.hostname or "") else t.hostname
    netloc = f"{t.username}:{ersatz}@{host}" + (f":{t.port}" if t.port else "")
    return urllib.parse.urlunsplit(t._replace(netloc=netloc)), t.password


def maskieren(liste):
    """Für die Verwaltung: Werte geheimer Kopfzeilen und Passwörter in Adressen nicht herausgeben."""
    return [dict(q, url=_url_passwort(q["url"], MASKE)[0],
                 kopf=[dict(k, wert=MASKE if k["geheim"] and k["wert"] else k["wert"]) for k in q["kopf"]]) for q in liste]


def demaskieren(neu, alt):
    """Beim Speichern aus der Verwaltung: maskierte Werte durch die gespeicherten ersetzen (gleiche Quelle, gleicher Name)."""
    alt_kopf = {(q["id"], k["name"].lower()): k["wert"] for q in alt for k in q["kopf"]}
    alt_url = {q["id"]: q["url"] for q in alt}
    for q in neu or []:
        url = str(q.get("url", ""))
        if MASKE in url or urllib.parse.quote(MASKE) in url:
            q["url"] = url.replace(urllib.parse.quote(MASKE), MASKE)
            alt_pw = _url_passwort(alt_url.get(str(q.get("id", "")).lower(), ""), "")[1]
            q["url"] = _url_passwort(q["url"], alt_pw or "")[0]
        for k in q.get("kopf") or []:
            if k.get("wert") == MASKE:
                k["wert"] = alt_kopf.get((str(q.get("id", "")).lower(), str(k.get("name", "")).lower()), "")
    return neu


def ohne_geheimnisse(liste):
    return [dict(q, url=_url_passwort(q["url"], "")[0], kopf=[dict(k, wert="" if k["geheim"] else k["wert"]) for k in q["kopf"]])
            for q in liste]


# ---------- curl-Befehl zerlegen (nur lesen, nie ausführen) ----------
def aus_curl(befehl):
    befehl = re.sub(r"\\\r?\n", " ", str(befehl or "")).strip()
    try:
        teile = shlex.split(befehl)
    except ValueError as ex:
        raise Fehler(f"curl-Befehl nicht lesbar: {ex}")
    if teile and teile[0].lower().endswith("curl"):
        teile = teile[1:]
    url, methode, kopf, daten, get, hinweise = "", "", [], [], False, []
    i = 0
    def naechster():
        nonlocal i
        i += 1
        if i >= len(teile):
            raise Fehler(f"curl: Wert fehlt nach {teile[i - 1]}")
        return teile[i]
    while i < len(teile):
        t = teile[i]
        if t in ("-X", "--request"):
            methode = naechster().upper()
        elif t.startswith("-X") and len(t) > 2:
            methode = t[2:].upper()
        elif t in ("-H", "--header"):
            h = naechster()
            if ":" in h:
                n, w = h.split(":", 1)
                kopf.append({"name": n.strip(), "wert": w.strip(), "geheim": bool(GEHEIM_KOPF.search(n))})
        elif t in ("-d", "--data", "--data-raw", "--data-binary", "--data-ascii", "--json"):
            daten.append(naechster())
            if t == "--json":
                kopf.append({"name": "Content-Type", "wert": "application/json", "geheim": False})
        elif t == "--data-urlencode":
            w = naechster()
            n, _, v = w.partition("=")
            daten.append(f"{n}={urllib.parse.quote(v)}" if _ else urllib.parse.quote(w))
        elif t in ("-u", "--user"):
            kopf.append({"name": "Authorization", "wert": "Basic " + base64.b64encode(naechster().encode()).decode(), "geheim": True})
        elif t in ("-A", "--user-agent"):
            kopf.append({"name": "User-Agent", "wert": naechster(), "geheim": False})
        elif t in ("-b", "--cookie"):
            kopf.append({"name": "Cookie", "wert": naechster(), "geheim": True})
        elif t in ("-e", "--referer"):
            kopf.append({"name": "Referer", "wert": naechster(), "geheim": False})
        elif t in ("-G", "--get"):
            get = True
        elif t == "--url":
            url = naechster()
        elif t in ("-o", "--output", "-w", "--write-out", "--connect-timeout", "-m", "--max-time", "--retry", "-x", "--proxy",
                   "-T", "--upload-file", "-F", "--form", "--cacert", "--cert", "-E", "-K", "--config"):
            hinweise.append(f"{t} wird nicht übernommen")
            naechster()
        elif t.startswith("-"):
            if t not in ("-s", "--silent", "-S", "--show-error", "-L", "--location", "--compressed", "-k", "--insecure",
                         "-i", "--include", "-v", "--verbose", "-f", "--fail", "-sS", "-sSL", "-fsSL", "-sL", "-g", "--globoff"):
                hinweise.append(f"{t} wird ignoriert")
        elif not url:
            url = t
        i += 1
    if not url:
        raise Fehler("curl: keine Adresse gefunden")
    if not re.match(r"https?://", url):
        url = "https://" + url
    inhalt = "&".join(daten)
    if get and inhalt:
        url += ("&" if "?" in url else "?") + inhalt
        inhalt = ""
    methode = methode or ("POST" if inhalt else "GET")
    if methode not in ("GET", "POST"):
        hinweise.append(f"Methode {methode} nicht unterstützt – GET genommen")
        methode = "GET"
    host = urllib.parse.urlparse(url).hostname or "quelle"
    vorschlag = re.sub(r"[^a-z0-9]", "", host.split(".")[-2] if host.count(".") else host)[:16] or "quelle"
    return {"quelle": {"id": vorschlag if len(vorschlag) >= 2 else "quelle", "name": host[:40], "art": "json", "url": url,
                       "methode": methode, "kopf": kopf, "inhalt": inhalt, "intervall_s": 300, "aktiv": True},
            "hinweise": hinweise}


# ---------- Abrufen und Zerlegen ----------
def _text_aus_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"&nbsp;", " ", s)
    s = re.sub(r"&(amp|lt|gt|quot|#39);", lambda m: {"amp": "&", "lt": "<", "gt": ">", "quot": '"', "#39": "'"}[m.group(1)], s)
    return re.sub(r"\s+", " ", s).strip()


def _datum(s):
    if not s:
        return ""
    try:
        return email.utils.parsedate_to_datetime(s).isoformat()
    except (TypeError, ValueError):
        return s.strip()[:40]


def rss_zerlegen(roh):
    try:
        wurzel = ET.fromstring(roh)
    except ET.ParseError as ex:
        raise Fehler(f"kein gültiger Feed: {ex}")
    def kind(e, *namen):
        for n in namen:
            for c in e:
                if c.tag.split("}")[-1] == n and (c.text or "").strip():
                    return c.text.strip()
        return ""
    eintraege, titel = [], ""
    if wurzel.tag.split("}")[-1] == "feed":                       # Atom
        titel = kind(wurzel, "title")
        for e in [c for c in wurzel if c.tag.split("}")[-1] == "entry"][:50]:
            link = next((c.get("href", "") for c in e if c.tag.split("}")[-1] == "link" and c.get("rel", "alternate") == "alternate"), "")
            eintraege.append({"titel": _text_aus_html(kind(e, "title")), "link": link,
                              "datum": _datum(kind(e, "updated", "published")),
                              "text": _text_aus_html(kind(e, "summary", "content"))[:400]})
    else:                                                         # RSS 2.0 / RDF
        kanal = next((c for c in wurzel.iter() if c.tag.split("}")[-1] == "channel"), wurzel)
        titel = kind(kanal, "title")
        for e in [c for c in wurzel.iter() if c.tag.split("}")[-1] == "item"][:50]:
            eintraege.append({"titel": _text_aus_html(kind(e, "title")), "link": kind(e, "link"),
                              "datum": _datum(kind(e, "pubDate", "date")), "text": _text_aus_html(kind(e, "description"))[:400]})
    return {"titel": _text_aus_html(titel), "eintraege": eintraege}


# ---------- iCal (.ics): Termine der nächsten Wochen, auch Wiederholungen ----------
WOCHENTAGE = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def _ical_zeit(wert, param):
    """-> (datetime oder date, ganztägig)"""
    wert = wert.strip()
    if param.get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", wert):
        return datetime.datetime.strptime(wert[:8], "%Y%m%d").date(), True
    d = datetime.datetime.strptime(wert.rstrip("Z")[:15], "%Y%m%dT%H%M%S")
    if wert.endswith("Z"):
        return d.replace(tzinfo=datetime.timezone.utc), False
    try:
        if param.get("TZID"):
            return d.replace(tzinfo=zoneinfo.ZoneInfo(param["TZID"].strip('"'))), False
    except (zoneinfo.ZoneInfoNotFoundError, ValueError):
        pass
    return d.astimezone(), False                      # ohne bekannte Zone: Ortszeit


def _monatstag(jahr, monat, tag):
    try:
        return datetime.date(jahr, monat, tag)
    except ValueError:
        return None


def _wiederholungen(start, regel, bis_fenster):
    """Einfache RRULE-Auswertung: FREQ DAILY/WEEKLY/MONTHLY/YEARLY, INTERVAL, COUNT, UNTIL, BYDAY, BYMONTHDAY, BYMONTH."""
    r = dict(t.split("=", 1) for t in regel.split(";") if "=" in t)
    freq, iv = r.get("FREQ"), max(1, int(r.get("INTERVAL", "1") or 1))
    anzahl = int(r["COUNT"]) if r.get("COUNT", "").isdigit() else None
    bis = None
    if r.get("UNTIL"):
        try:
            bis = _ical_zeit(r["UNTIL"], {})[0]
        except ValueError:
            pass
    ist_datum = not isinstance(start, datetime.datetime)
    t0 = start if ist_datum else start.date()
    def mit_zeit(d):
        return d if ist_datum else datetime.datetime.combine(d, start.timetz())
    def nach_bis(x):
        if bis is None:
            return False
        a = x if isinstance(x, datetime.datetime) else datetime.datetime.combine(x, datetime.time(), tzinfo=datetime.timezone.utc)
        b = bis if isinstance(bis, datetime.datetime) else datetime.datetime.combine(bis, datetime.time(23, 59, 59), tzinfo=datetime.timezone.utc)
        if a.tzinfo is None: a = a.astimezone()
        if b.tzinfo is None: b = b.astimezone()
        return a > b
    byday = [x for x in r.get("BYDAY", "").split(",") if x]
    bymd = [int(x) for x in r.get("BYMONTHDAY", "").split(",") if re.fullmatch(r"-?\d+", x)]
    bymon = [int(x) for x in r.get("BYMONTH", "").split(",") if x.isdigit()]
    gefunden, n = [], 0
    for schritt in range(0, 3000):
        if freq == "DAILY":
            tage = [t0 + datetime.timedelta(days=schritt * iv)]
        elif freq == "WEEKLY":
            woche = t0 - datetime.timedelta(days=t0.weekday()) + datetime.timedelta(weeks=schritt * iv)
            wt = [WOCHENTAGE.index(x[-2:]) for x in byday if x[-2:] in WOCHENTAGE] or [t0.weekday()]
            tage = [woche + datetime.timedelta(days=w) for w in sorted(wt)]
        elif freq == "MONTHLY":
            m = t0.month - 1 + schritt * iv
            jahr, monat = t0.year + m // 12, m % 12 + 1
            tage = []
            if byday:
                for x in byday:
                    mm = re.fullmatch(r"([+-]?\d+)?(MO|TU|WE|TH|FR|SA|SU)", x)
                    if not mm:
                        continue
                    wt = WOCHENTAGE.index(mm.group(2))
                    alle = [d for d in (_monatstag(jahr, monat, i) for i in range(1, 32)) if d and d.weekday() == wt]
                    nr = int(mm.group(1) or 0)
                    tage += alle if nr == 0 else ([alle[nr - 1]] if 0 < nr <= len(alle) else [alle[nr]] if -len(alle) <= nr < 0 else [])
            else:
                for md in bymd or [t0.day]:
                    letzter = max(i for i in range(28, 32) if _monatstag(jahr, monat, i))
                    d = _monatstag(jahr, monat, md if md > 0 else letzter + md + 1)
                    if d:
                        tage.append(d)
        elif freq == "YEARLY":
            jahr = t0.year + schritt * iv
            tage = [d for mo in (bymon or [t0.month]) for md in (bymd or [t0.day]) for d in [_monatstag(jahr, mo, md)] if d]
        else:
            return [start]
        for d in sorted(tage):
            if d < t0:
                continue
            x = mit_zeit(d)
            if nach_bis(x) or (anzahl is not None and n >= anzahl):
                return gefunden
            n += 1
            gefunden.append(x)
        letzter_tag = max(tage) if tage else t0
        if letzter_tag > bis_fenster:
            return gefunden
    return gefunden


def ical_zerlegen(text, tage=120):
    text = re.sub(r"\r?\n[ \t]", "", text.replace("\r\n", "\n"))
    ereignisse, akt, kalname = [], None, ""
    for zeile in text.split("\n"):
        if zeile == "BEGIN:VEVENT":
            akt = {}
            continue
        if zeile == "END:VEVENT":
            if akt is not None:
                ereignisse.append(akt)
            akt = None
            continue
        m = re.match(r"([A-Za-z0-9-]+)((?:;[^:]*)?):(.*)", zeile)
        if not m:
            continue
        name, param_text, wert = m.group(1).upper(), m.group(2), m.group(3)
        if akt is None:
            if name == "X-WR-CALNAME":
                kalname = wert
            continue
        param = dict(p.split("=", 1) for p in param_text.strip(";").split(";") if "=" in p)
        akt.setdefault(name, []).append((param, wert))
    def text_wert(e, k):
        w = (e.get(k) or [({}, "")])[0][1]
        return re.sub(r"\\([,;\\])", r"\1", w).replace("\\n", " ").replace("\\N", " ").strip()
    jetzt = datetime.datetime.now().astimezone()
    heute = jetzt.date()
    fenster = heute + datetime.timedelta(days=tage)
    ueberschrieben = set()
    for e in ereignisse:
        if "RECURRENCE-ID" in e:
            try:
                ueberschrieben.add((text_wert(e, "UID"), _ical_zeit(e["RECURRENCE-ID"][0][1], e["RECURRENCE-ID"][0][0])[0]))
            except ValueError:
                pass
    termine = []
    for e in ereignisse:
        try:
            if "DTSTART" not in e or text_wert(e, "STATUS").upper() == "CANCELLED":
                continue
            start, ganztag = _ical_zeit(e["DTSTART"][0][1], e["DTSTART"][0][0])
            if "DTEND" in e:
                ende = _ical_zeit(e["DTEND"][0][1], e["DTEND"][0][0])[0]
            else:
                m = re.fullmatch(r"P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?", text_wert(e, "DURATION"))
                dauer = datetime.timedelta(weeks=int(m.group(1) or 0), days=int(m.group(2) or 0), hours=int(m.group(3) or 0),
                                           minutes=int(m.group(4) or 0)) if m else datetime.timedelta(days=1 if ganztag else 0)
                ende = start + dauer
            dauer = ende - start
            ausnahmen = set()
            for p, w in e.get("EXDATE", []):
                for x in w.split(","):
                    try:
                        ausnahmen.add(_ical_zeit(x, p)[0])
                    except ValueError:
                        pass
            uid = text_wert(e, "UID")
            vorkommen = _wiederholungen(start, e["RRULE"][0][1], fenster) if "RRULE" in e and "RECURRENCE-ID" not in e else [start]
            for s in vorkommen:
                if s in ausnahmen or ("RECURRENCE-ID" not in e and (uid, s) in ueberschrieben):
                    continue
                en = s + dauer
                s_tag = s if ganztag else s.astimezone().date()
                en_vergleich = en if ganztag else en.astimezone()
                if (en_vergleich <= heute if ganztag else en_vergleich < jetzt) or s_tag > fenster:
                    continue
                termine.append({"titel": text_wert(e, "SUMMARY")[:120], "ort": text_wert(e, "LOCATION")[:120], "ganztag": ganztag,
                                "start": s.isoformat() if ganztag else s.astimezone().isoformat(),
                                "ende": en.isoformat() if ganztag else en.astimezone().isoformat()})
        except (ValueError, KeyError, IndexError):
            continue
    termine.sort(key=lambda t: t["start"] if "T" in t["start"] else t["start"] + "T00:00")
    return {"kalender": kalname, "termine": termine[:300]}


def holen(q, url=None, max_bytes=None):
    """Eine Abfrage ausführen: (Rohdaten, Content-Type)."""
    url = url or q["url"]
    if not re.match(r"https?://", url):
        raise Fehler("nur http/https")
    kopf = {"User-Agent": UA, "Accept": "*/*"}
    kopf.update({k["name"]: k["wert"] for k in q.get("kopf", [])})
    daten = q["inhalt"].encode() if q.get("methode") == "POST" else None
    anf = urllib.request.Request(url, data=daten, headers=kopf, method=q.get("methode", "GET"))
    grenze = max_bytes or (MAX_BILD if q.get("art") == "bild" else MAX_BYTES)
    try:
        with urllib.request.urlopen(anf, timeout=10) as r:
            roh = r.read(grenze + 1)
            art = r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as ex:
        raise Fehler(f"HTTP {ex.code} {ex.reason}")
    except urllib.error.URLError as ex:
        raise Fehler(f"nicht erreichbar: {ex.reason}")
    except (TimeoutError, OSError) as ex:
        raise Fehler(f"nicht erreichbar: {ex}")
    if len(roh) > grenze:
        raise Fehler(f"Antwort größer als {grenze // 1_000_000} MB")
    return roh, art


def zerlegen(q, roh, art):
    if q["art"] == "bild":
        if not art.startswith("image/"):
            raise Fehler(f"kein Bild (Content-Type {art or 'fehlt'})")
        return {"bild": roh, "typ": art.split(";")[0], "groesse": len(roh)}
    text = roh.decode(_zeichensatz(art), errors="replace")
    if q["art"] == "json":
        try:
            return json.loads(text)
        except ValueError as ex:
            raise Fehler(f"kein gültiges JSON: {ex}")
    if q["art"] == "rss":
        return rss_zerlegen(roh)
    if q["art"] == "ical":
        return ical_zerlegen(text)
    return text.strip()


def _zeichensatz(art):
    m = re.search(r"charset=([\w-]+)", art or "", re.I)
    return m.group(1) if m else "utf-8"


# ---------- Pfade und Vorlagen ----------
def pfad_teile(pfad):
    """'a.b[0].c' oder 'a.b.0.c' -> ['a', 'b', 0, 'c']"""
    teile = []
    for t in re.findall(r"[^.\[\]]+|\[\d+\]", str(pfad or "").strip()):
        if t.startswith("["):
            teile.append(int(t[1:-1]))
        elif t.isdigit():
            teile.append(int(t))
        else:
            teile.append(t)
    return teile


def wert_bei(daten, pfad):
    w = daten
    for t in pfad_teile(pfad):
        if isinstance(w, list) and isinstance(t, int) and -len(w) <= t < len(w):
            w = w[t]
        elif isinstance(w, dict) and str(t) in w:
            w = w[str(t)]
        elif isinstance(w, list) and str(t) == "length":
            w = len(w)
        else:
            return None
    return w


def als_zahl(w):
    if isinstance(w, bool):
        return None
    if isinstance(w, (int, float)):
        return float(w)
    try:
        return float(str(w).strip().replace(",", ".")) if re.fullmatch(r"\s*-?\d+([.,]\d+)?\s*", str(w)) else None
    except ValueError:
        return None


def formatieren(w, nachkomma=-1, faktor=1.0, sprache="de"):
    if w is None:
        return "–"
    z = als_zahl(w)
    if z is not None and (nachkomma >= 0 or faktor != 1.0):
        z *= faktor
        if nachkomma < 0:
            s = f"{z:g}" if abs(z) < 1e15 else str(z)
            return s.replace(".", ",") if sprache == "de" else s
        s = f"{z:,.{nachkomma}f}"                  # mit Tausendertrennung: 71,654.5 -> de 71.654,5
        return s.replace(",", "_").replace(".", ",").replace("_", ".") if sprache == "de" else s
    if isinstance(w, float):
        s = f"{w:g}"
        return s.replace(".", ",") if sprache == "de" else s
    if isinstance(w, (dict, list)):
        return json.dumps(w, ensure_ascii=False)[:200]
    if isinstance(w, bool):
        return ("ja" if w else "nein") if sprache == "de" else ("yes" if w else "no")
    return str(w)


def fuellen(vorlage, standard_quelle, daten_von, nachkomma=-1, faktor=1.0, sprache="de", basis=None):
    """{pfad} (Quelle des Bausteins bzw. Listeneintrag) oder {quelle:pfad} durch Werte ersetzen."""
    def ersetzen(m):
        inhalt = m.group(1).strip()
        if ":" in inhalt and re.fullmatch(r"[a-z0-9_]{2,16}", inhalt.split(":", 1)[0]):
            qid, pfad = inhalt.split(":", 1)
            return formatieren(wert_bei(daten_von(qid), pfad), nachkomma, faktor, sprache)
        if basis is not None:
            return formatieren(wert_bei(basis, inhalt), nachkomma, faktor, sprache)
        return formatieren(wert_bei(daten_von(standard_quelle), inhalt) if standard_quelle else None, nachkomma, faktor, sprache)
    return PLATZHALTER.sub(ersetzen, vorlage or "")


def gekuerzt(w, tiefe=0):
    """Antwort für die Testansicht der Verwaltung verkleinern (Listen bis 20 Einträge, Texte bis 500 Zeichen)."""
    if tiefe > 8:
        return "…"
    if isinstance(w, dict):
        return {k: gekuerzt(v, tiefe + 1) for k, v in list(w.items())[:80]}
    if isinstance(w, list):
        return [gekuerzt(v, tiefe + 1) for v in w[:20]] + ([f"… {len(w) - 20} weitere"] if len(w) > 20 else [])
    if isinstance(w, str) and len(w) > 500:
        return w[:500] + "…"
    return w


# ---------- Laufender Abruf ----------
class Verlauf:
    """Werte von Datenquellen über die Zeit (für den Baustein „Diagramm“): je (Quelle, Pfad) höchstens 7 Tage und
    5000 Punkte, gespeichert als JSON (spätestens alle 5 min und beim Beenden nicht garantiert – Lücken sind möglich)."""
    TAGE, PUNKTE = 7, 5000

    def __init__(self, datei):
        self.datei = datei
        try:
            self.reihen = {k: v for k, v in json.load(open(datei)).items() if isinstance(v, list)}
        except (OSError, ValueError):
            self.reihen = {}
        self.gespeichert = time.time()
        self.sperre = threading.Lock()

    def merken(self, qid, pfad, wert):
        z = als_zahl(wert)
        if z is None:
            return
        grenze = time.time() - self.TAGE * 86400
        with self.sperre:
            r = self.reihen.setdefault(f"{qid}:{pfad}", [])
            r.append([int(time.time()), z])
            while r and r[0][0] < grenze:
                r.pop(0)
            del r[:-self.PUNKTE]
            if time.time() - self.gespeichert > 300:
                self.speichern()

    def speichern(self):
        try:
            tmp = self.datei + ".neu"
            with open(tmp, "w") as f:
                json.dump(self.reihen, f)
            os.replace(tmp, self.datei)
            self.gespeichert = time.time()
        except OSError:
            pass

    def punkte(self, qid, pfad, stunden):
        ab = time.time() - stunden * 3600
        with self.sperre:
            return [p for p in self.reihen.get(f"{qid}:{pfad}", []) if p[0] >= ab]

    def aufraeumen(self, benutzt):
        """Reihen, die kein Diagramm mehr braucht und deren letzter Wert älter als 7 Tage ist, entfernen."""
        grenze = time.time() - self.TAGE * 86400
        with self.sperre:
            for k in [k for k, r in self.reihen.items() if k not in benutzt and (not r or r[-1][0] < grenze)]:
                del self.reihen[k]


def verkleinern(punkte, n=240):
    """Für die Anzeige höchstens n Punkte (Mittelwert je Abschnitt)."""
    if len(punkte) <= n:
        return punkte
    schritt = len(punkte) / n
    aus = []
    for i in range(n):
        teil = punkte[int(i * schritt):int((i + 1) * schritt)] or [punkte[-1]]
        aus.append([teil[-1][0], sum(p[1] for p in teil) / len(teil)])
    return aus


class Quellen:
    def __init__(self, einstellungen, verlauf_datei=None):
        self.einst = einstellungen            # Funktion -> aktuelle Einstellungen
        self.stand = {}                       # id -> {daten, abruf, fehler, dauer_ms, naechster, versuche, signatur}
        self.bilder = {}                      # (id, url) -> {bild, typ, zeit}
        self.neu = threading.Event()
        self.sperre = threading.Lock()
        self.verlauf = Verlauf(verlauf_datei) if verlauf_datei else None

    def verlauf_pfade(self):
        """(Quelle, Pfad) aller Diagramm-Bausteine in allen Layouts."""
        return {(e["optionen"]["quelle"], e["optionen"]["pfad"]) for l in self.einst().get("layouts", []) for e in l["elemente"]
                if e["typ"] == "diagramm" and e["optionen"].get("quelle")}

    def daten(self, qid):
        s = self.stand.get(qid)
        return s["daten"] if s and s.get("daten") is not None else None

    def abrufen(self, q):
        t0 = time.time()
        roh, art = holen(q)
        return zerlegen(q, roh, art), round((time.time() - t0) * 1000)

    def schleife(self):
        while True:
            quellen = {q["id"]: q for q in self.einst().get("quellen", [])}
            jetzt = time.time()
            for qid in list(self.stand):
                if qid not in quellen:
                    self.stand.pop(qid, None)
            for qid, q in quellen.items():
                sig = json.dumps(q, sort_keys=True)
                s = self.stand.setdefault(qid, {"daten": None, "abruf": None, "fehler": None, "dauer_ms": None,
                                                "naechster": 0, "versuche": 0, "signatur": sig})
                if s["signatur"] != sig:          # geändert -> sofort neu holen, alte Daten verwerfen
                    s.update(signatur=sig, naechster=0, versuche=0, daten=None, fehler=None)
                if not q["aktiv"] or q["art"] == "video" or jetzt < s["naechster"]:
                    continue
                try:
                    daten, ms = self.abrufen(q)
                    s.update(daten=daten, abruf=time.time(), fehler=None, dauer_ms=ms, versuche=0,
                             naechster=time.time() + q["intervall_s"])
                    if self.verlauf:
                        for vq, vp in self.verlauf_pfade():
                            if vq == qid:
                                self.verlauf.merken(qid, vp, wert_bei(daten, vp))
                except Exception as ex:
                    s["versuche"] += 1
                    s.update(fehler=str(ex)[:300], naechster=time.time() + min(max(q["intervall_s"], 3600),
                                                                              q["intervall_s"] * 2 ** min(s["versuche"], 6)))
            if self.verlauf and time.time() - getattr(self, "_aufgeraeumt", 0) > 3600:
                self._aufgeraeumt = time.time()
                self.verlauf.aufraeumen({f"{q}:{p}" for q, p in self.verlauf_pfade()})
            self.neu.wait(1)
            self.neu.clear()

    def status(self):
        aus = {}
        for q in self.einst().get("quellen", []):
            s = self.stand.get(q["id"], {})
            aus[q["id"]] = {"abruf": s.get("abruf"), "fehler": s.get("fehler"), "dauer_ms": s.get("dauer_ms"),
                            "naechster": s.get("naechster"), "versuche": s.get("versuche", 0), "hat_daten": s.get("daten") is not None}
        return aus

    def bild_aus_url(self, q, url):
        """Bild-Adresse aus einer JSON-Antwort holen (zwischengespeichert für das Intervall der Quelle)."""
        if not isinstance(url, str) or not re.match(r"https?://", url):
            return None
        with self.sperre:
            b = self.bilder.get((q["id"], url))
        if b and time.time() - b["zeit"] < q["intervall_s"]:
            return b
        try:
            roh, art = holen(dict(q, art="bild", methode="GET", inhalt=""), url=url, max_bytes=MAX_BILD)
            if not art.startswith("image/"):
                return None
            b = {"bild": roh, "typ": art.split(";")[0], "zeit": time.time()}
        except Exception:
            return b
        with self.sperre:
            for k in [k for k in self.bilder if k[0] == q["id"] and k != (q["id"], url)]:
                del self.bilder[k]
            self.bilder[(q["id"], url)] = b
        return b


# ---------- Werte der Bausteine für die TV-Seite ----------
API_TYPEN = ("apiwert", "apiliste", "apibild", "anzeige", "countdown", "qrcode", "text", "webcam", "diagramm", "kalender")
HLS_INTERN = f"http://127.0.0.1:{os.environ.get('SC_STREAM_PORT', '8888')}"          # MediaMTX im Container (Pfade cam_<id> nur von 127.0.0.1 lesbar)


def baustein_werte(layout, quellen, sprache, einst_quellen, ha_verlauf=None):
    """Je Baustein des Layouts die fertigen Werte (Texte, Zeilen, Bildadresse, Zahl) – nichts von der Abfrage selbst."""
    qmap = {q["id"]: q for q in einst_quellen}
    dv = quellen.daten
    aus, bed = {}, {}
    for e in layout.get("elemente", []):
        o, typ = e["optionen"], e["typ"]
        b = e.get("bedingung")
        if b and b.get("quelle"):
            w = wert_bei(dv(b["quelle"]), b["pfad"]) if dv(b["quelle"]) is not None else None
            bed[f"api:{b['quelle']}:{b['pfad']}"] = {"state": None if w is None else (w if isinstance(w, (int, float, str)) else json.dumps(w))}
        if typ not in API_TYPEN:
            continue
        fmt = dict(nachkomma=o.get("nachkomma", -1), faktor=_faktor(o.get("faktor")), sprache=sprache)
        if typ == "text":
            if PLATZHALTER.search(o.get("text", "")):
                aus[e["id"]] = {"text": fuellen(o["text"], None, dv, sprache=sprache)}
        elif typ == "apiwert":
            vorlage = o.get("vorlage") or ("{" + o["pfad"] + "}" if o.get("pfad") else "")
            text = fuellen(vorlage, o.get("quelle"), dv, **fmt)
            if o.get("einheit"):
                text += " " + o["einheit"]
            aus[e["id"]] = {"text": text, "da": dv(o.get("quelle")) is not None}
        elif typ == "apiliste":
            liste = wert_bei(dv(o.get("quelle")), o.get("pfad", "")) if dv(o.get("quelle")) is not None else None
            if isinstance(liste, dict):
                liste = list(liste.values())
            zeilen = [fuellen(o.get("zeile") or "{titel}", o.get("quelle"), dv, basis=x, **fmt)
                      for x in (liste if isinstance(liste, list) else [])[:o.get("anzahl", 5)]]
            aus[e["id"]] = {"zeilen": zeilen, "da": isinstance(liste, list)}
        elif typ == "apibild":
            q = qmap.get(o.get("quelle"))
            s = quellen.stand.get(o.get("quelle"), {})
            if q and q["art"] == "bild" and s.get("abruf"):
                aus[e["id"]] = {"bild": f"/qbild/{q['id']}?t={int(s['abruf'])}"}
            elif q and o.get("pfad") and dv(q["id"]) is not None:
                url = wert_bei(dv(q["id"]), o["pfad"])
                if isinstance(url, str) and re.match(r"https?://", url):
                    aus[e["id"]] = {"bild": f"/qbild/{q['id']}?p={urllib.parse.quote(o['pfad'])}&t={int(s.get('abruf') or 0)}"}
        elif typ == "anzeige":
            w = wert_bei(dv(o.get("quelle")), o.get("pfad", "")) if o.get("quelle") and dv(o.get("quelle")) is not None else None
            z = als_zahl(w)
            aus[e["id"]] = {"zahl": None if z is None else z * _faktor(o.get("faktor")),
                            "text": formatieren(w, **fmt) + (" " + o["einheit"] if o.get("einheit") and w is not None else "")}
        elif typ == "countdown":
            ziel = o.get("ziel", "")
            if o.get("quelle") and o.get("pfad") and dv(o["quelle"]) is not None:
                ziel = str(wert_bei(dv(o["quelle"]), o["pfad"]) or "")
            aus[e["id"]] = {"ziel": _iso(ziel)}
        elif typ == "webcam":
            q = qmap.get(o.get("quelle"))
            if q and q["art"] == "video" and q["aktiv"]:
                f = video_format(q)
                aus[e["id"]] = {"art": "mjpeg", "url": f"/qvideo/{q['id']}"} if f == "mjpeg" else \
                    {"art": "hls", "url": f"{HLS_INTERN}/cam_{q['id']}/index.m3u8"}
        elif typ == "diagramm":
            if o.get("entity"):
                pkt = (ha_verlauf or {}).get(o["entity"], [])
                pkt = [p for p in pkt if p[0] >= time.time() - o.get("stunden", 24) * 3600]
            elif o.get("quelle") and quellen.verlauf:
                pkt = quellen.verlauf.punkte(o["quelle"], o.get("pfad", ""), o.get("stunden", 24))
            else:
                pkt = []
            f = _faktor(o.get("faktor"))
            pkt = [[t, v * f] for t, v in verkleinern(pkt)]
            aktuell = pkt[-1][1] if pkt else None
            aus[e["id"]] = {"punkte": pkt, "text": (formatieren(aktuell, o.get("nachkomma", -1), 1.0, sprache) if aktuell is not None else "–")
                            + (" " + o["einheit"] if o.get("einheit") and aktuell is not None else "")}
        elif typ == "kalender" and o.get("quelle"):
            d = dv(o["quelle"])
            grenze = (datetime.date.today() + datetime.timedelta(days=o.get("tage", 14))).isoformat()
            aus[e["id"]] = {"termine": [t for t in (d or {}).get("termine", []) if t["start"][:10] <= grenze][:o.get("anzahl", 4)]}
        elif typ == "qrcode":
            aus[e["id"]] = {"inhalt": fuellen(o.get("inhalt", ""), None, dv, sprache=sprache)[:900]}
    return aus, bed


def _faktor(w):
    try:
        return float(str(w or "1").replace(",", "."))
    except ValueError:
        return 1.0


def _iso(s):
    """Zieldatum vereinheitlichen: '2026-12-24', '2026-12-24T18:00', Unix-Zeit (s/ms) -> ISO-Zeit in Ortszeit."""
    s = str(s or "").strip()
    if re.fullmatch(r"\d{9,13}", s):
        z = int(s) / (1000 if len(s) > 11 else 1)
        return datetime.datetime.fromtimestamp(z).isoformat()
    try:
        d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return (d.astimezone() if d.tzinfo else d).replace(tzinfo=None).isoformat()
    except ValueError:
        return ""
