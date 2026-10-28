# Radio und Ortssuche für SignageCast.
# - Ortssuche: OpenStreetMap Nominatim (nur auf Knopfdruck in der Verwaltung; höchstens 1 Anfrage/s laut Nutzungsregeln).
# - Sendervorschläge: freies Senderverzeichnis radio-browser.info – im Umkreis des Standorts, nach Regionswörtern
#   (Ort, Region, eigene Wörter), im Bundesland und im Land. Das Verzeichnis ist lückenhaft (viele Sender ohne
#   Koordinaten), deshalb mehrere Wege.
# - Eigene Sender: Adresse prüfen (Playlist .m3u/.pls auflösen, Inhalt muss Audio sein).
import json, os, re, threading, time, urllib.parse, urllib.request

UA = {"User-Agent": "SignageCast/0.4 (TV info screen for Home Assistant)"}   # nur ASCII (HTTP-Kopf)
RB_SERVER = ["de1.api.radio-browser.info", "de2.api.radio-browser.info", "fi1.api.radio-browser.info", "at1.api.radio-browser.info"]
_letzte_osm = [0.0]
_osm_sperre = threading.Lock()
_ort_cache = {}


def _json(url, timeout=12):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return json.load(r)


def _osm(pfad):
    with _osm_sperre:                         # Nominatim: höchstens eine Anfrage je Sekunde
        warten = 1.1 - (time.time() - _letzte_osm[0])
        if warten > 0:
            time.sleep(warten)
        try:
            return _json("https://nominatim.openstreetmap.org" + pfad)
        finally:
            _letzte_osm[0] = time.time()


def ort_suchen(text, sprache="de"):
    text = str(text).strip()[:100]
    if len(text) < 2:
        return []
    d = _osm("/search?" + urllib.parse.urlencode({"q": text, "format": "jsonv2", "limit": 6, "addressdetails": 1,
                                                  "accept-language": sprache}))
    return [{"name": x.get("display_name", "")[:120], "breite": round(float(x["lat"]), 4),
             "laenge": round(float(x["lon"]), 4), "art": x.get("type", "")} for x in d]


def ort_beschreiben(breite, laenge):
    """Ort, Landkreis, Bundesland (deutsch und englisch) und Land zum Standort – für die Sendervorschläge."""
    schluessel = (round(breite, 2), round(laenge, 2))
    if schluessel in _ort_cache:
        return _ort_cache[schluessel]
    erg = {"orte": [], "land": "", "laendercode": ""}
    for sprache in ("de", "en"):
        try:
            a = _osm("/reverse?" + urllib.parse.urlencode({"lat": breite, "lon": laenge, "format": "jsonv2",
                                                           "zoom": 10, "accept-language": sprache})).get("address", {})
        except Exception:
            continue
        for k in ("city", "town", "village", "county", "state_district"):
            if a.get(k):
                erg["orte"].append(a[k])
        if a.get("state"):
            erg.setdefault("laender", []).append(a["state"])
        erg["laendercode"] = (a.get("country_code") or erg["laendercode"]).upper()
    erg["laender"] = list(dict.fromkeys(erg.get("laender", [])))
    erg["orte"] = list(dict.fromkeys(erg["orte"]))
    _ort_cache[schluessel] = erg
    return erg


def _rb(pfad, params):
    params = dict(params, hidebroken="true")
    for server in RB_SERVER:
        try:
            return _json(f"https://{server}/json/{pfad}?" + urllib.parse.urlencode(params))
        except Exception:
            continue
    raise RuntimeError("Senderverzeichnis radio-browser.info nicht erreichbar")


def _sender(x):
    return {"name": re.sub(r"\s+", " ", x.get("name", "")).strip()[:60], "url": x.get("url_resolved") or x.get("url"),
            "codec": x.get("codec", ""), "bitrate": x.get("bitrate", 0), "land": x.get("countrycode", ""),
            "region": x.get("state", ""), "stichworte": (x.get("tags") or "")[:60], "homepage": x.get("homepage", ""),
            "beliebt": x.get("clickcount", 0)}


def _nur_abspielbar(liste):
    gesehen, aus = set(), []
    for x in liste:
        s = _sender(x)
        if not s["url"] or not s["url"].startswith(("http://", "https://")) or s["codec"].upper() not in ("MP3", "AAC", "AAC+", "OGG", ""):
            continue
        if not s["name"] or re.match(r"[\W_]", s["name"]) or re.search(r"top ?100|charts? ---|#", s["name"], re.I):
            continue                              # Werbe-/Spam-Einträge im Verzeichnis
        k = (s["name"].lower(), s["url"])
        if k in gesehen:
            continue
        gesehen.add(k)
        aus.append(s)
    return aus


def vorschlaege(breite, laenge, eigene_woerter=()):
    """Sendervorschläge, gruppiert: in der Nähe, Region/Bundesland, Land."""
    ort = ort_beschreiben(breite, laenge)
    naehe = _rb("stations/search", {"geo_lat": breite, "geo_long": laenge, "geo_distance": 60000,
                                    "order": "clickcount", "reverse": "true", "limit": 40})
    woerter = [w for w in list(eigene_woerter) + [re.split(r"[ ,(/]", o)[0] for o in ort["orte"]] if len(w) >= 3]
    for w in dict.fromkeys(woerter):
        for feld in ("name", "tag"):
            try:
                naehe += _rb("stations/search", {feld: w, "order": "clickcount", "reverse": "true", "limit": 30})
            except Exception:
                pass
    region = []
    for land in ort.get("laender", []):
        region += _rb("stations/search", {"state": land, "countrycode": ort["laendercode"] or "DE",
                                          "order": "clickcount", "reverse": "true", "limit": 80})
    region.sort(key=lambda x: -x.get("clickcount", 0))
    landesweit = _rb("stations/search", {"countrycode": ort["laendercode"] or "DE", "order": "clickcount",
                                         "reverse": "true", "limit": 40}) if ort["laendercode"] else []
    gruppen = {"naehe": _nur_abspielbar(naehe), "region": _nur_abspielbar(region)[:60], "land": _nur_abspielbar(landesweit)}
    schon = {s["url"] for s in gruppen["naehe"]}
    gruppen["region"] = [s for s in gruppen["region"] if s["url"] not in schon]
    schon |= {s["url"] for s in gruppen["region"]}
    gruppen["land"] = [s for s in gruppen["land"] if s["url"] not in schon]
    return {"ort": ort, "woerter": list(dict.fromkeys(woerter)), "gruppen": gruppen}


def suchen(name):
    name = str(name).strip()[:60]
    if len(name) < 2:
        return []
    return _nur_abspielbar(_rb("stations/search", {"name": name, "order": "clickcount", "reverse": "true", "limit": 40}))


def adresse_pruefen(url):
    """Liefert die abspielbare Adresse (Playlist aufgelöst) oder wirft ValueError."""
    url = str(url).strip()
    if not re.fullmatch(r"https?://\S{4,490}", url):
        raise ValueError("Adresse muss mit http:// oder https:// beginnen")
    for _ in range(3):
        req = urllib.request.Request(url, headers=dict(UA, **{"Icy-MetaData": "0"}))
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                typ = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                anfang = r.read(4096)
        except Exception as e:
            raise ValueError(f"Adresse nicht erreichbar: {e}")
        text = anfang.decode("utf-8", "replace")
        if typ in ("audio/x-mpegurl", "audio/mpegurl", "application/x-mpegurl", "audio/x-scpls", "application/pls+xml") \
                or url.lower().split("?")[0].endswith((".m3u", ".pls")) or text.lstrip().startswith(("#EXTM3U", "[playlist]")):
            if "#EXT-X-" in text:
                raise ValueError("HLS-Radio (m3u8) wird nicht unterstützt – bitte eine MP3/AAC-Adresse nehmen")
            m = re.search(r"(?im)^(?:File\d+=)?(https?://\S+)", text)
            if not m:
                raise ValueError("Playlist enthält keine Stream-Adresse")
            url = m.group(1).strip()
            continue
        if typ.startswith("audio/") or typ in ("application/ogg", "video/mp2t") or (typ == "application/octet-stream" and anfang):
            return url        # nicht die Weiterleitung: deren Adresse enthält oft ablaufende Zugangsschlüssel
        raise ValueError(f"Kein Audio-Stream (Inhalt: {typ or 'unbekannt'})")
    raise ValueError("Zu viele verschachtelte Playlists")


def playlist_lesen(text):
    """Inhalt einer M3U- oder PLS-Datei -> [(name, url)]. Namen aus #EXTINF bzw. TitleN=, sonst leer."""
    text = str(text)[:200000]
    if "#EXT-X-" in text:
        raise ValueError("Das ist eine HLS-Playlist (m3u8 mit #EXT-X-…) – bitte eine MP3/AAC-Adresse nehmen")
    eintraege, name = [], ""
    pls_namen = dict(re.findall(r"(?im)^Title(\d+)\s*=\s*(.+)$", text))
    for zeile in text.splitlines():
        zeile = zeile.strip().lstrip("\ufeff")
        if zeile.upper().startswith("#EXTINF"):
            name = zeile.split(",", 1)[1].strip() if "," in zeile else ""
            continue
        m = re.match(r"(?i)^(?:File(\d+)\s*=\s*)?(https?://\S+)$", zeile)
        if m:
            eintraege.append(((pls_namen.get(m.group(1)) if m.group(1) else name) or "", m.group(2)))
            name = ""
    if not eintraege:
        raise ValueError("Keine Stream-Adresse (http/https) in der Playlist gefunden")
    return eintraege[:50]


def neue_id():
    return os.urandom(4).hex()[:8]
