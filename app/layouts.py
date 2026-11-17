# Layouts von SignageCast: was ein Fernseher zeigt und wo. Fläche 1920x1080, Raster 48 x 27 Felder à 40 px.
# Ein Layout = Hintergrund + Farbschema + Liste von Bausteinen (Position/Größe in Rasterfeldern, Optionen, Bedingung).
# Werte kommen aus HA-Entitäten oder (seit 0.9) aus eigenen Datenquellen (app/quellen.py: API, RSS, Bild).
import copy, re
from meldung import Meldung

SPALTEN, ZEILEN = 48, 27
ENTITY = re.compile(r"[a-z_]+\.[a-z0-9_]+")
FARBE = re.compile(r"#[0-9a-fA-F]{6}")
UHRZEIT = re.compile(r"([01]\d|2[0-3]):[0-5]\d")
# Schriften aus Debian-Paketen (installieren.sh) – keine Abhängigkeit zur Laufzeit
SCHRIFTEN = ["Roboto", "Noto Sans", "Noto Serif", "Open Sans", "Lato", "Montserrat", "Ubuntu", "Cantarell",
             "DejaVu Sans", "DejaVu Serif", "DejaVu Sans Mono", "Fira Code", "Comic Neue"]
GEWICHTE = ["", "duenn", "normal", "fett"]
# Position der Schrift im Feld: senkrecht (oben/mitte/unten) x waagrecht (links/mitte/rechts); "links" usw. = Mitte senkrecht
AUSRICHTUNGEN = ["oben-links", "oben-mitte", "oben-rechts", "links", "mitte", "rechts", "unten-links", "unten-mitte", "unten-rechts"]
OPERATOREN = ["=", "!=", ">", "<", "an", "aus"]
# Hintergrund-Bildersets (www/bilder/stile/<stil>-<tageszeit>.jpg, CC0/gemeinfrei, Quellen in www/bilder/stile/QUELLEN.md)
# seit 0.54: essen/sport/architektur für die Branchen-Vorlagen (nicht in „gemischt“, das bleibt bei der Landschaft)
STILE = ["natur", "stadt", "himmel", "berge", "meer", "essen", "sport", "architektur", "gemischt"]
TAGESZEITEN = ["morgen", "tag", "abend", "nacht"]
WECHSEL = ["tageszeit", "tageszeit_wetter", "diashow"]
KARTEN = ["weiss", "glas_hell", "glas_dunkel"]   # seit 0.54: Karten deckend weiß oder durchscheinend (ohne Weichzeichner)
HG_ARTEN = ("wetter", "stil", "farbe", "bild", "galerie")    # galerie seit 0.45: Ordner als Diashow

# Bausteine: Typ -> erlaubte Optionen mit Prüffunktion und Standardwert
def _b(w):  return bool(w)
def _t(n):
    p = lambda w: str(w)[:n]
    p.art = f"text (max {n} characters)"
    return p
def _ent(domains=None):
    def p(w):
        w = str(w or "").strip()
        if w and (not ENTITY.fullmatch(w) or (domains and w.split(".")[0] not in domains)):
            raise Meldung("l_entitaet", w=repr(w))
        return w
    p.art = "Home Assistant entity id" + (f" ({', '.join(d + '.*' for d in domains)})" if domains else "") + ", empty = none"
    return p
def _zahl(lo, hi):
    def p(w):
        w = int(w)
        if not lo <= w <= hi:
            raise Meldung("e_bereich", w=w, lo=lo, hi=hi)
        return w
    p.art = f"integer {lo}–{hi}"
    return p
def _icon(w):
    w = str(w or "mdi-information-outline")
    if not re.fullmatch(r"mdi-[a-z0-9-]{1,60}", w):
        raise Meldung("l_symbol")
    return w
def _farbe(w):
    w = str(w or "")
    if w and not FARBE.fullmatch(w):
        raise Meldung("l_farbe")
    return w
def _bild(w):
    w = str(w or "")
    if w and not re.fullmatch(r"[0-9a-f]{16}\.(jpg|png)", w):
        raise Meldung("l_bild")
    return w
def _fl(lo, hi):
    def p(w):
        w = float(str(w).replace(",", "."))
        if not lo <= w <= hi:
            raise Meldung("e_bereich", w=w, lo=lo, hi=hi)
        return w
    p.art = "number"
    return p
def _qid(w):
    w = str(w or "").strip()
    if w and not re.fullmatch(r"[a-z0-9_]{2,16}", w):
        raise Meldung("l_quelle")
    return w
def _pfad(w):
    w = str(w or "").strip()
    if len(w) > 160 or "\n" in w:
        raise Meldung("l_pfad")
    return w
def _url(w):
    w = str(w or "").strip()
    if w and not re.fullmatch(r"https?://[^\s\"'<>]{1,1000}", w):
        raise Meldung("l_adresse")
    return w
def _icon_leer(w):
    return _icon(w) if str(w or "").strip() else ""
def _wahl(*werte):
    def p(w):
        if w not in werte:
            raise Meldung("l_wahl", werte=", ".join(werte))
        return w
    p.art = "one of " + ", ".join(f'"{x}"' for x in werte)
    return p
def _pdf(w):
    w = str(w or "")
    if w and not re.fullmatch(r"[0-9a-f]{16}", w):
        raise Meldung("l_pdf")
    return w
def _gid(w):
    w = str(w or "").strip()
    if w and not re.fullmatch(r"[a-z0-9]{2,12}", w):
        raise Meldung("l_galerie")
    return w
def _symbole(w):
    """Kalender als Symbole (seit 0.28): Regeln „Titel enthält …“ -> Symbol und Farbe, die erste passende gilt."""
    aus = []
    for r in (w if isinstance(w, list) else [])[:12]:
        if not isinstance(r, dict) or not str(r.get("text", "")).strip():
            continue
        aus.append({"text": str(r["text"]).strip()[:40], "icon": _icon(r.get("icon") or "mdi-calendar"), "farbe": _farbe(r.get("farbe"))})
    return aus
def _zeilen(w):
    """Zeilen des Bausteins „Liste“ (seit 0.53): Text links, Zusatz klein darunter, Wert rechts (Preis, Uhrzeit, Ebene)."""
    aus = []
    for r in (w if isinstance(w, list) else [])[:20]:
        if not isinstance(r, dict):
            continue
        z = {"text": str(r.get("text", "")).strip()[:60], "info": str(r.get("info", "")).strip()[:120],
             "wert": str(r.get("wert", "")).strip()[:24], "icon": _icon_leer(r.get("icon")), "hervor": bool(r.get("hervor"))}
        if z["text"] or z["wert"] or z["info"]:
            aus.append(z)
    return aus
def _raeume(w):
    return [{"name": str(r.get("name", ""))[:30], "entity": _ent()(r.get("entity"))} for r in (w or [])[:8] if r.get("entity")]

# Beschreibung der Werte für die Formatbeschreibung (seit 0.38, für Menschen und KI – siehe format_beschreibung)
_b.art = "true or false"
_icon.art = 'Material Design Icon name "mdi-…" (e.g. "mdi-thermometer")'
_icon_leer.art = 'Material Design Icon name "mdi-…" or "" for none'
_farbe.art = 'colour "#rrggbb" or "" for the default'
_bild.art = 'file name of an uploaded picture ("" = none; the user uploads it later in the editor)'
_qid.art = "id of one of your own data sources (Content → Data sources), \"\" = none"
_pfad.art = 'path into the data source answer, e.g. "current.temp" or "items.0.title"'
_url.art = "web address starting with http:// or https://"
_pdf.art = '16 hex characters of an uploaded PDF ("" = none; the user uploads it later)'
_gid.art = 'id of a gallery folder (Content → Media library → Galleries), "" = none; the user picks it later in the editor'
_symbole.art = 'list of rules {"text": "word in the title", "icon": "mdi-…", "farbe": "#rrggbb"} (max 12)'
_zeilen.art = 'list of rows {"text": "Currywurst", "info": "small line below, e.g. allergens", "wert": "4,50 €", "icon": "mdi-…" or "", "hervor": true/false = highlight} (max 20)'
_raeume.art = 'list of {"name": "Living room", "entity": "sensor.living_room_temperature"} (max 8)'

TYPEN = {
    "uhr":        {"sekunden": (_b, False)},
    "datum":      {"wochentag": (_b, True), "jahr": (_b, True)},
    "temperatur": {"entity": (_ent(["weather", "sensor"]), "")},          # leer = Wetter-Entität aus „Anzeige“
    "wetterlage": {"entity": (_ent(["weather"]), "")},
    "feuchte":    {"entity": (_ent(["weather", "sensor"]), "")},
    "wind":       {"entity": (_ent(["weather", "sensor"]), "")},
    "vorhersage": {"tage": (_zahl(1, 5), 3)},
    "raeume":     {"liste": (_raeume, [])},
    "kachel":     {"entity": (_ent(), ""), "name": (_t(30), ""), "icon": (_icon, "mdi-information-outline")},
    "video":      {"leiste": (_b, True)},
    "sender":     {},
    "text":       {"text": (_t(300), ""), "laufband": (_b, False)},
    "logo":       {"bild": (_bild, "")},
    "kamera":     {"entity": (_ent(["camera"]), ""), "intervall": (_zahl(1, 60), 2)},
    "kalender":   {"entity": (_ent(["calendar"]), ""), "quelle": (_qid, ""), "anzahl": (_zahl(1, 10), 4), "tage": (_zahl(1, 60), 14), "nur_mit_terminen": (_b, False),
                   "titel": (_t(40), ""),
                   # seit 0.28: nur Symbole (z. B. Mülltonne), Regeln je Termin; ohne passende Regel: ohne_symbol ("" = weglassen)
                   "ansicht": (_wahl("liste", "symbole"), "liste"), "symbole": (_symbole, []),
                   "ohne_symbol": (_icon_leer, "mdi-calendar"), "wann": (_b, True)},                                   # quelle = iCal-Datenquelle statt HA (seit 0.10)
    "meldung":    {"entity": (_ent(["input_text", "sensor", "text"]), ""), "dauer": (_zahl(3, 600), 20)},
    "flaeche":    {"farbe": (_farbe, "#f0f0f0"), "deckkraft": (_zahl(0, 100), 100)},
    # eigene Datenquellen (seit 0.9); Platzhalter {pfad} bzw. {quelle:pfad}
    "apiwert":    {"quelle": (_qid, ""), "pfad": (_pfad, ""), "vorlage": (_t(300), ""), "name": (_t(30), ""),
                   "icon": (_icon_leer, "mdi-api"), "einheit": (_t(12), ""), "nachkomma": (_zahl(-1, 6), -1), "faktor": (_t(16), "1")},
    "apiliste":   {"quelle": (_qid, ""), "pfad": (_pfad, "eintraege"), "zeile": (_t(300), "{titel}"), "anzahl": (_zahl(1, 20), 5),
                   "titel": (_t(40), ""), "laufband": (_b, False), "nachkomma": (_zahl(-1, 6), -1), "faktor": (_t(16), "1")},
    "apibild":    {"quelle": (_qid, ""), "pfad": (_pfad, ""), "anpassung": (_wahl("einpassen", "fuellen"), "einpassen")},
    "anzeige":    {"quelle": (_qid, ""), "pfad": (_pfad, ""), "name": (_t(30), ""), "darstellung": (_wahl("balken", "ampel"), "balken"),
                   "min": (_fl(-1e9, 1e9), 0.0), "max": (_fl(-1e9, 1e9), 100.0), "gelb": (_fl(-1e9, 1e9), 60.0), "rot": (_fl(-1e9, 1e9), 80.0),
                   "umkehren": (_b, False), "einheit": (_t(12), ""), "nachkomma": (_zahl(-1, 6), -1), "faktor": (_t(16), "1")},
    "countdown":  {"ziel": (_t(40), ""), "quelle": (_qid, ""), "pfad": (_pfad, ""), "vorlage": (_t(120), "noch {tage} Tage"),
                   "ende": (_t(60), "Heute!")},
    "qrcode":     {"inhalt": (_t(900), ""), "beschriftung": (_t(60), "")},
    # seit 0.10: Kamera, Verlauf, Webseite
    "webcam":     {"quelle": (_qid, ""), "ton": (_b, False), "anpassung": (_wahl("fuellen", "einpassen"), "fuellen")},
    "diagramm":   {"quelle": (_qid, ""), "pfad": (_pfad, ""), "entity": (_ent(["sensor", "input_number", "number", "counter"]), ""),
                   "stunden": (_zahl(1, 168), 24), "name": (_t(30), ""), "einheit": (_t(12), ""), "nachkomma": (_zahl(-1, 6), 1),
                   "faktor": (_t(16), "1")},
    "unwetter":   {"anzahl": (_zahl(1, 3), 1), "immer": (_b, False)},                  # DWD-Warnungen (seit 0.16)
    # modus bild (seit 0.20): SignageCast fotografiert die Seite (app/webbild.py) – auch wenn sie das Einbetten verbietet
    "webseite":   {"url": (_url, ""), "modus": (_wahl("einbetten", "bild"), "einbetten"), "neu_laden_min": (_zahl(0, 1440), 15), "zoom": (_zahl(25, 300), 100),
                   "versatz_x": (_zahl(0, 10000), 0), "versatz_y": (_zahl(0, 10000), 0)},
    # seit 0.21: PDF Seite für Seite (app/pdf.py wandelt beim Hochladen in Bilder um)
    "pdf":        {"datei": (_pdf, ""), "sekunden": (_zahl(3, 3600), 15), "anpassung": (_wahl("einpassen", "fuellen"), "einpassen")},
    # seit 0.45: Ordner mit Bildern/PDFs (Inhalte → Mediathek → Galerien), Folie für Folie nach der Uhr
    "galerie":    {"ordner": (_gid, ""), "sekunden": (_zahl(3, 3600), 10), "anpassung": (_wahl("einpassen", "fuellen"), "einpassen"),
                   "rand": (_wahl("schwarz", "unscharf"), "schwarz"), "reihenfolge": (_wahl("eigene", "name", "neu", "zufall"), "eigene"),
                   "uebergang": (_wahl("blenden", "hart"), "blenden")},
    # seit 0.53: feste Liste (Speisekarte, Öffnungszeiten, Wegweiser) – oder Zeilen aus einer Datenquelle (z. B. CSV)
    "liste":      {"titel": (_t(40), ""), "zeilen": (_zeilen, []), "spalten": (_zahl(1, 3), 1), "punkte": (_b, True),
                   "quelle": (_qid, ""), "pfad": (_pfad, "zeilen"), "spalte_text": (_t(120), "{text}"),
                   "spalte_info": (_t(120), "{info}"), "spalte_wert": (_t(120), "{wert}")},
}
ENTFERNT = {"abfahrten"}                 # seit 0.26 ausgebaut (kein offener Fahrplan-Dienst für Deutschland)
# Mindestgröße je Typ (Felder)
MINDEST = {"logo": (2, 1), "video": (8, 5), "kamera": (4, 3), "kalender": (6, 3), "raeume": (4, 2), "vorhersage": (4, 3),
           "apibild": (2, 2), "qrcode": (2, 2), "apiliste": (4, 1), "webcam": (4, 3), "diagramm": (4, 2), "webseite": (4, 3),
           "pdf": (3, 3), "galerie": (3, 3), "liste": (4, 2)}
# Zeitraum eines Bausteins (seit 0.21): „ab“/„bis“ als Datum oder Datum mit Uhrzeit (Ortszeit); leer = unbegrenzt
ZEITPUNKT = re.compile(r"\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])(T([01]\d|2[0-3]):[0-5]\d)?")


def _zeitpunkt(w):
    w = str(w or "").strip().replace(" ", "T")[:16]
    if w and not ZEITPUNKT.fullmatch(w):
        raise Meldung("l_zeitraum")
    return w


def im_zeitraum(e, jetzt):
    """Liegt jetzt ("YYYY-MM-DDTHH:MM", Ortszeit) im Zeitraum des Bausteins? Ein reines Datum bei „bis“ gilt bis Tagesende."""
    ab, bis = e.get("ab") or "", e.get("bis") or ""
    if ab and jetzt[:len(ab)] < ab:
        return False
    if bis and (jetzt[:10] > bis if len(bis) == 10 else jetzt[:16] >= bis):
        return False
    return True


def _pruefe_bedingung(b):
    if not b or not (b.get("entity") or b.get("quelle")):
        return None
    op = b.get("op", "=")
    if op not in OPERATOREN:
        raise Meldung("l_vergleich")
    if b.get("quelle"):                       # Wert aus einer Datenquelle (seit 0.9)
        return {"quelle": _qid(b["quelle"]), "pfad": _pfad(b.get("pfad", "")), "op": op, "wert": str(b.get("wert", ""))[:60]}
    return {"entity": _ent()(b["entity"]), "op": op, "wert": str(b.get("wert", ""))[:60]}


def pruefe_layout(l):
    lid = str(l.get("id", ""))
    if not re.fullmatch(r"[a-z0-9]{2,16}", lid):
        raise Meldung("l_kennung", id=repr(lid))
    hg = l.get("hintergrund", {}) or {}
    art = hg.get("art", "wetter")
    if art not in HG_ARTEN:
        raise Meldung("l_hintergrund")
    def _bildname(b):
        b = str(b or "")
        if b and not re.fullmatch(r"[0-9a-f]{16}\.(jpg|png)", b):
            raise Meldung("l_hg_bild")
        return b
    bild = _bildname(hg.get("bild"))
    je_zeit = {z: _bildname((hg.get("bilder_tageszeit") or {}).get(z)) for z in TAGESZEITEN}
    stil = hg.get("stil", "natur") if hg.get("stil", "natur") in STILE else "natur"
    wechsel = hg.get("wechsel", "tageszeit") if hg.get("wechsel", "tageszeit") in WECHSEL else "tageszeit"
    diashow_min = max(1, min(120, int(hg.get("diashow_min", 10) or 10)))
    # seit 0.54 in Sekunden (ältere Layouts haben nur Minuten)
    diashow_s = max(10, min(7200, int(hg.get("diashow_s") or diashow_min * 60)))
    galerie = _gid(hg.get("galerie"))
    galerie_s = max(5, min(3600, int(hg.get("galerie_s", 60) or 60)))
    b = hg.get("bereich") or {}
    bw = max(4, min(SPALTEN, int(b.get("w", SPALTEN)))); bh = max(3, min(ZEILEN, int(b.get("h", ZEILEN))))
    bereich = {"x": max(0, min(SPALTEN - bw, int(b.get("x", 0)))), "y": max(0, min(ZEILEN - bh, int(b.get("y", 0)))), "w": bw, "h": bh}
    anpassung = hg.get("anpassung") if hg.get("anpassung") in ("fuellen", "einpassen", "strecken") else "fuellen"
    ausschnitt = hg.get("ausschnitt") if hg.get("ausschnitt") in ("mitte", "oben", "unten", "links", "rechts") else "mitte"
    th = l.get("thema", {}) or {}
    schema = th.get("schema", "dunkel")
    if schema not in ("dunkel", "hell", "gedimmt"):
        raise Meldung("l_schema")
    schrift = th.get("schrift", "Roboto")
    if schrift not in SCHRIFTEN:
        raise Meldung("l_schrift")
    elemente, ids = [], set()
    for e in (l.get("elemente") or [])[:60]:
        typ = e.get("typ")
        if typ in ENTFERNT:                  # ausgebaute Bausteine aus alten Einstellungen/Sicherungen still verwerfen
            continue
        if typ not in TYPEN:
            raise Meldung("l_baustein", typ=repr(typ))
        eid = str(e.get("id", ""))
        if not re.fullmatch(r"[a-z0-9]{1,16}", eid) or eid in ids:
            raise Meldung("l_baustein_id", id=repr(eid))
        ids.add(eid)
        mw, mh = MINDEST.get(typ, (1, 1))
        if typ == "kalender" and (e.get("optionen") or {}).get("ansicht") == "symbole":
            mw, mh = 1, 1                    # seit 0.28: einzelnes Symbol in der Ecke
        w = max(mw, min(SPALTEN, int(e.get("w", 4))))
        h = max(mh, min(ZEILEN, int(e.get("h", 2))))
        x = max(0, min(SPALTEN - w, int(e.get("x", 0))))
        y = max(0, min(ZEILEN - h, int(e.get("y", 0))))
        opt_in = e.get("optionen", {}) or {}
        optionen = {k: (pf(opt_in[k]) if k in opt_in else copy.deepcopy(std)) for k, (pf, std) in TYPEN[typ].items()}
        elemente.append({"id": eid, "typ": typ, "x": x, "y": y, "w": w, "h": h, "sichtbar": bool(e.get("sichtbar", True)),
                         "karte": bool(e.get("karte", typ in ("kachel", "vorhersage", "kalender"))),
                         "ausrichtung": e.get("ausrichtung") if e.get("ausrichtung") in AUSRICHTUNGEN else "links",
                         "schrift": e.get("schrift") if e.get("schrift") in SCHRIFTEN else "",          # leer = wie Layout
                         "gewicht": e.get("gewicht") if e.get("gewicht") in GEWICHTE else "",
                         "textfarbe": _farbe(e.get("textfarbe", "")),                                   # leer = Farbschema
                         "optionen": optionen, "bedingung": _pruefe_bedingung(e.get("bedingung")),
                         "ab": _zeitpunkt(e.get("ab")), "bis": _zeitpunkt(e.get("bis"))})
    return {"id": lid, "name": str(l.get("name", lid))[:40] or lid,
            "hintergrund": {"art": art, "farbe": _farbe(hg.get("farbe", "#202020")) or "#202020", "bild": bild,
                            "bilder_tageszeit": je_zeit, "stil": stil, "wechsel": wechsel, "diashow_min": diashow_min,
                            "diashow_s": diashow_s, "bewegen": bool(hg.get("bewegen", False)),
                            "galerie": galerie, "galerie_s": galerie_s,
                            "nachts_dunkler": bool(hg.get("nachts_dunkler", True)), "abdunkeln": bool(hg.get("abdunkeln", True)),
                            "bereich": bereich, "anpassung": anpassung, "ausschnitt": ausschnitt},
            "thema": {"schema": schema, "akzent": _farbe(th.get("akzent", "#3d8cd0")) or "#3d8cd0", "schrift": schrift,
                      "karte": th.get("karte") if th.get("karte") in KARTEN else "weiss"},
            "elemente": elemente}


# ---------- Import (seit 0.38): fehlertolerant, z. B. für Layouts, die eine KI geschrieben hat ----------
def _neue_id(belegt, vorschlag, muster, laenge):
    v = re.sub(r"[^a-z0-9]", "", str(vorschlag or "").lower())[:laenge]
    if len(v) >= (2 if laenge == 16 and muster == "layout" else 1) and v not in belegt:
        return v
    basis = (v or ("layout" if muster == "layout" else "e"))[:laenge - 3]
    for i in range(1, 1000):
        k = f"{basis}{i}"[:laenge]
        if k not in belegt:
            return k
    raise Meldung("l_imp_kein")


def json_aus_text(text):
    """JSON aus eingefügtem Text: auch mit ```json …```-Zaun oder Text davor/danach (typisch für Antworten einer KI)."""
    import json
    t = str(text or "").strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    if not t.startswith(("{", "[")):
        a = t.find("{")
        if a < 0:
            raise Meldung("l_imp_json", d="kein { gefunden")
        t = t[a:t.rfind("}") + 1]
    try:
        return json.loads(t)
    except ValueError as f:
        raise Meldung("l_imp_json", d=str(f)[:120]) from None


def import_pruefen(roh, belegte_ids=(), bild_da=lambda n: True, quellen=(), pdf_da=lambda n: True, ordner=None):
    """Layout aus einer Datei oder einem eingefügten Text übernehmen: Was sich reparieren lässt, wird repariert und als
    Hinweis gemeldet (unbekannte Bausteine weglassen, ungültige Werte auf den Standard, fehlende Kennungen vergeben,
    fehlende Bilder leeren). Gibt (layout, hinweise) zurück; hinweise = Liste von Meldungen."""
    if isinstance(roh, dict) and roh.get("art") in ("signagecast-layout", "tv-stream-layout") and isinstance(roh.get("layout"), dict):
        roh = roh["layout"]
    if isinstance(roh, dict) and isinstance(roh.get("layouts"), list) and len(roh["layouts"]) == 1:
        roh = roh["layouts"][0]
    if not isinstance(roh, dict) or not isinstance(roh.get("elemente"), list):
        raise Meldung("l_imp_kein")
    hinweise = []
    l = {"id": _neue_id(set(belegte_ids), roh.get("id"), "layout", 16), "name": str(roh.get("name") or "Import")[:40]}
    hg = dict(roh.get("hintergrund") or {}) if isinstance(roh.get("hintergrund"), dict) else {}
    if hg.get("art", "wetter") not in HG_ARTEN:
        hinweise.append(Meldung("l_imp_wert", feld="hintergrund.art", w=str(hg.get("art"))[:40]))
        hg["art"] = "wetter"
    for feld in ("bild",):
        if hg.get(feld) and (not re.fullmatch(r"[0-9a-f]{16}\.(jpg|png)", str(hg[feld])) or not bild_da(hg[feld])):
            hinweise.append(Meldung("l_imp_bild", w=str(hg[feld])[:40])); hg[feld] = ""
    bt = hg.get("bilder_tageszeit") if isinstance(hg.get("bilder_tageszeit"), dict) else {}
    for z in list(bt):
        if bt[z] and (not re.fullmatch(r"[0-9a-f]{16}\.(jpg|png)", str(bt[z])) or not bild_da(bt[z])):
            hinweise.append(Meldung("l_imp_bild", w=str(bt[z])[:40])); bt[z] = ""
    hg["bilder_tageszeit"] = bt
    if hg.get("art") == "bild" and not hg.get("bild") and not any(bt.values()):
        hg["art"] = "wetter"
    if hg.get("galerie") and (not re.fullmatch(r"[a-z0-9]{2,12}", str(hg["galerie"])) or (ordner is not None and hg["galerie"] not in ordner)):
        hinweise.append(Meldung("l_imp_galerie", w=str(hg["galerie"])[:40])); hg["galerie"] = ""
    if hg.get("farbe") and not FARBE.fullmatch(str(hg["farbe"])):
        hinweise.append(Meldung("l_imp_wert", feld="hintergrund.farbe", w=str(hg["farbe"])[:40])); hg["farbe"] = "#202020"
    l["hintergrund"] = hg
    th = dict(roh.get("thema") or {}) if isinstance(roh.get("thema"), dict) else {}
    for feld, erlaubt, std in (("schema", ("dunkel", "hell", "gedimmt"), "dunkel"), ("schrift", SCHRIFTEN, "Roboto")):
        if feld in th and th[feld] not in erlaubt:
            hinweise.append(Meldung("l_imp_wert", feld="thema." + feld, w=str(th[feld])[:40])); th[feld] = std
    if th.get("akzent") and not FARBE.fullmatch(str(th["akzent"])):
        hinweise.append(Meldung("l_imp_wert", feld="thema.akzent", w=str(th["akzent"])[:40])); th["akzent"] = "#3d8cd0"
    l["thema"] = th
    elemente, ids = [], set()
    for nr, e in enumerate(roh["elemente"][:60], 1):
        if not isinstance(e, dict):
            continue
        typ = e.get("typ")
        if typ in ENTFERNT:
            continue
        if typ not in TYPEN:
            hinweise.append(Meldung("l_imp_typ", nr=nr, typ=str(typ)[:30]))
            continue
        x = dict(e)
        eid = str(x.get("id", ""))
        if not re.fullmatch(r"[a-z0-9]{1,16}", eid) or eid in ids:
            x["id"] = _neue_id(ids, eid or typ, "baustein", 16)
        ids.add(x["id"])
        name = f"{nr} ({typ})"
        try:
            for k in ("x", "y", "w", "h"):
                x[k] = int(float(x.get(k, 0 if k in "xy" else 4)))
        except (TypeError, ValueError):
            hinweise.append(Meldung("l_imp_typ", nr=nr, typ=str(typ)[:30]))
            continue
        if x["x"] < 0 or x["y"] < 0 or x["x"] + x["w"] > SPALTEN or x["y"] + x["h"] > ZEILEN:
            hinweise.append(Meldung("l_imp_raster", b=name))
        opt_in = x.get("optionen") if isinstance(x.get("optionen"), dict) else {}
        opt = {}
        for k, w in opt_in.items():
            if k not in TYPEN[typ]:
                hinweise.append(Meldung("l_imp_option", b=name, o=str(k)[:30]))
                continue
            try:
                opt[k] = TYPEN[typ][k][0](w)
            except (Meldung, ValueError, TypeError):
                bilddatei = k == "bild" or (typ == "pdf" and k == "datei")       # z. B. „logo.png“ einer KI: hochladen
                hinweise.append(Meldung("l_imp_bild", w=str(w)[:40]) if bilddatei and w else
                                Meldung("l_imp_wert", feld=f"{name}.{k}", w=str(w)[:40]))
                continue
            if k == "bild" and opt[k] and not bild_da(opt[k]):
                hinweise.append(Meldung("l_imp_bild", w=opt[k])); opt[k] = ""
            if k == "datei" and typ == "pdf" and opt[k] and not pdf_da(opt[k]):
                hinweise.append(Meldung("l_imp_bild", w=opt[k])); opt[k] = ""
            if k == "ordner" and typ == "galerie" and opt[k] and ordner is not None and opt[k] not in ordner:
                hinweise.append(Meldung("l_imp_galerie", w=opt[k])); opt[k] = ""
            if k == "quelle" and opt[k] and opt[k] not in quellen:
                hinweise.append(Meldung("l_imp_quelle", b=name, q=opt[k]))
        x["optionen"] = opt
        for k in ("textfarbe",):
            if x.get(k) and not FARBE.fullmatch(str(x[k])):
                hinweise.append(Meldung("l_imp_wert", feld=f"{name}.{k}", w=str(x[k])[:40])); x[k] = ""
        try:
            x["bedingung"] = _pruefe_bedingung(x.get("bedingung") if isinstance(x.get("bedingung"), dict) else None)
        except (Meldung, ValueError, TypeError):
            hinweise.append(Meldung("l_imp_bedingung", b=name)); x["bedingung"] = None
        for k in ("ab", "bis"):
            try:
                x[k] = _zeitpunkt(x.get(k))
            except Meldung:
                hinweise.append(Meldung("l_imp_wert", feld=f"{name}.{k}", w=str(x.get(k))[:40])); x[k] = ""
        elemente.append(x)
    l["elemente"] = elemente
    return pruefe_layout(l), hinweise


# ---------- Formatbeschreibung (seit 0.38) – aus TYPEN erzeugt, damit sie nie veraltet ----------
TYP_TEXT = {
    "uhr": "clock (HH:MM)", "datum": "date", "temperatur": "current outside temperature",
    "wetterlage": "current weather condition (icon and text)", "feuchte": "humidity", "wind": "wind speed and direction",
    "vorhersage": "weather forecast for the next days", "raeume": "list of room temperatures from Home Assistant",
    "kachel": "tile with one Home Assistant value (name, icon, value)",
    "video": "live video window: rotating YouTube nature/wildlife live cams or own media (at most one per layout makes sense)",
    "sender": "name of the current live cam or radio station", "text": "free text; laufband = scrolling ticker; "
    "placeholders {source:path} insert values of own data sources", "logo": "picture (e.g. company logo)",
    "kamera": "Home Assistant camera picture", "kalender": "calendar (Home Assistant calendar or iCal data source) as list or symbols",
    "meldung": "message banner from a Home Assistant text entity", "flaeche": "coloured rectangle, e.g. as panel behind other elements",
    "apiwert": "one value from an own data source", "apiliste": "list or feed from an own data source",
    "apibild": "picture from an own data source", "anzeige": "gauge (bar or traffic light) for a value",
    "countdown": "countdown to a date (ziel: YYYY-MM-DD or YYYY-MM-DDTHH:MM)", "qrcode": "QR code",
    "webcam": "IP camera (own data source of type video)", "diagramm": "history chart of a value",
    "unwetter": "official severe weather warnings (Germany, DWD)", "webseite": "web page (embedded or as screenshot)",
    "pdf": "PDF shown page by page",
    "liste": "fixed list with text left, small info line and value right (menu with prices, opening hours, directory); "
    "with quelle the rows come from a data source (CSV: columns text, info, wert – or own placeholders in spalte_*)",
    "galerie": "slideshow of a gallery folder (pictures and PDF pages uploaded under Content → Media library → Galleries); the user picks the folder",
}


def _wert_json(w):
    import json
    return json.dumps(w, ensure_ascii=False)


def format_beschreibung():
    """Beschreibung des Layout-Formats als Markdown (Englisch – versteht jede KI; Feldnamen sind deutsch)."""
    z = ["# SignageCast layout format", "",
         "A layout describes what a TV shows. It is a JSON object. Screen 1920 × 1080 px, divided into a grid of "
         f"**{SPALTEN} columns × {ZEILEN} rows** (one cell = 40 × 40 px). Every element has a position `x`, `y` (top-left "
         "cell, 0-based) and a size `w`, `h` in cells. Elements may overlap; later elements in the list are drawn on top. "
         "Unknown fields are ignored, invalid values fall back to the default on import (the admin lists every repair).",
         "", "## Layout", "", "```json",
         '{"art": "signagecast-layout", "version": 2, "layout": {', '  "id": "lobby", "name": "Lobby",',
         '  "hintergrund": {"art": "stil", "stil": "natur"},', '  "thema": {"schema": "dunkel", "akzent": "#3d8cd0", "schrift": "Roboto"},',
         '  "elemente": [', '    {"id": "uhr", "typ": "uhr", "x": 1, "y": 1, "w": 8, "h": 3},',
         '    {"id": "video", "typ": "video", "x": 11, "y": 1, "w": 36, "h": 20, "karte": true}', "  ]}}", "```", "",
         "The wrapper (`art`, `version`, `layout`) is optional – a bare layout object works too.", "",
         "| Field | Meaning |", "|---|---|",
         "| `id` | 2–16 characters a–z, 0–9 (a new one is assigned on import if it exists already) |",
         "| `name` | display name, max 40 characters |",
         '| `hintergrund.art` | `"wetter"` (picture matching the current weather), `"stil"` (picture set), `"farbe"` (plain colour), `"bild"` (uploaded picture), `"galerie"` (slideshow of a gallery folder) |',
         '| `hintergrund.galerie`, `hintergrund.galerie_s` | for art `galerie`: folder id ("" – the user picks it) and seconds per picture (5–3600) |',
         f"| `hintergrund.stil` | {', '.join(f'`{x}`' for x in STILE)} – picture changes with the time of day |",
         '| `hintergrund.wechsel`, `hintergrund.diashow_s` | `"tageszeit"`, `"tageszeit_wetter"` or `"diashow"`; for the slideshow seconds per picture (10–7200) |',
         '| `hintergrund.bewegen` | true = pictures move slowly (gentle zoom, cross-fade on change) |',
         '| `hintergrund.farbe` | `"#rrggbb"` for art `farbe` |',
         '| `hintergrund.abdunkeln` | true = darken the picture a little so text stays readable |',
         '| `hintergrund.nachts_dunkler` | true = darker at night |',
         '| `thema.schema` | `"dunkel"` (light text on dark), `"hell"` (dark text on light), `"gedimmt"` (very dim, for night) |',
         '| `thema.akzent` | accent colour `"#rrggbb"` |',
         '| `thema.karte` | cards: `"weiss"` (solid white), `"glas_hell"` (see-through light), `"glas_dunkel"` (see-through dark) |',
         f"| `thema.schrift` | font: {', '.join(f'`{x}`' for x in SCHRIFTEN)} |",
         "", "## Element", "", "| Field | Meaning | Default |", "|---|---|---|",
         "| `id` | 1–16 characters a–z, 0–9, unique in the layout | – |",
         f"| `typ` | element type, see below | – |",
         f"| `x`, `y`, `w`, `h` | position and size in cells (x + w ≤ {SPALTEN}, y + h ≤ {ZEILEN}) | 0, 0, 4, 2 |",
         "| `sichtbar` | false = hidden | true |",
         "| `karte` | true = drawn on a semi-transparent card | true for kachel, vorhersage, kalender |",
         f"| `ausrichtung` | text position: {', '.join(f'`{x}`' for x in AUSRICHTUNGEN)} | `links` |",
         '| `schrift` | font of this element (see above), "" = layout font | "" |',
         "| `gewicht` | " + ", ".join(f"`{x}`" for x in GEWICHTE if x) + ' or "" (normal) | "" |',
         '| `textfarbe` | `"#rrggbb"`, "" = colour scheme | "" |',
         "| `optionen` | options of the type, see below | defaults |",
         '| `bedingung` | show only when …: `{"entity": "binary_sensor.door", "op": "an"}` or `{"quelle": "id", "pfad": "a.b", "op": ">", "wert": "5"}`; '
         f"op: {', '.join(f'`{x}`' for x in OPERATOREN)} | null |",
         '| `ab`, `bis` | show only in this period: `"YYYY-MM-DD"` or `"YYYY-MM-DDTHH:MM"` (local time) | "" |',
         "", "## Element types and options", ""]
    for typ, opts in TYPEN.items():
        mw, mh = MINDEST.get(typ, (1, 1))
        z.append(f"### `{typ}` – {TYP_TEXT.get(typ, typ)}")
        z.append("")
        z.append(f"Minimum size {mw} × {mh} cells." if (mw, mh) != (1, 1) else "No minimum size.")
        if opts:
            z += ["", "| Option | Value | Default |", "|---|---|---|"]
            for k, (pf, std) in opts.items():
                z.append(f"| `{k}` | {getattr(pf, 'art', '')} | `{_wert_json(std)}` |")
        z.append("")
    z += ["## Rules for good layouts", "",
          "- Leave a margin of 1 cell at the screen edges (TVs often cut off the border).",
          "- Text needs height: a clock of 3 rows is easy to read from 3 m, a text line needs at least 1 row.",
          "- Only reference Home Assistant entities, data sources, pictures and PDFs that exist; otherwise leave them empty "
          "(\"\") – the user fills them in the editor.",
          "- Use `flaeche` with `deckkraft` 40–80 as a calm panel behind text on pictures or video.",
          "- Answer with the JSON only.", ""]
    return "\n".join(z)

def tageszeit(sonnenhoehe_jetzt, sonnenhoehe_spaeter):
    """morgen / tag / abend / nacht aus dem Sonnenstand (später = in 10 min, zeigt ob die Sonne steigt)."""
    if sonnenhoehe_jetzt < -6:
        return "nacht"
    if sonnenhoehe_jetzt >= 8:
        return "tag"
    return "morgen" if sonnenhoehe_spaeter > sonnenhoehe_jetzt else "abend"


def pruefe_zeitplan(z, layout_ids):
    aus = []
    for r in (z or [])[:12]:
        von, bis, ziel = str(r.get("von", "")), str(r.get("bis", "")), str(r.get("layout", ""))
        if not UHRZEIT.fullmatch(von) or not UHRZEIT.fullmatch(bis):
            raise Meldung("z_uhrzeit")
        if ziel != "schwarz" and ziel not in layout_ids:
            raise Meldung("z_layout", id=repr(ziel))
        aus.append({"von": von, "bis": bis, "layout": ziel})
    return aus


def aktuelles_layout(tv, layouts, jetzt_hhmm):
    """Layout eines Fernsehers zur Uhrzeit (Zeitplan vor Grundlayout; Zeiträume über Mitternacht erlaubt)."""
    for r in tv.get("zeitplan", []):
        von, bis = r["von"], r["bis"]
        drin = von <= jetzt_hhmm < bis if von < bis else (jetzt_hhmm >= von or jetzt_hhmm < bis)
        if drin:
            if r["layout"] == "schwarz":
                return {"id": "schwarz", "name": "schwarz", "schwarz": True}
            l = next((x for x in layouts if x["id"] == r["layout"]), None)
            if l:
                return l
    k = tv.get("karussell") or {}
    reihe = [x for x in (next((l for l in layouts if l["id"] == i), None) for i in k.get("layouts", [])) if x]
    if k.get("aktiv") and len(reihe) >= 2:
        # Karussell: alle N Minuten das nächste Layout (nach Uhrzeit, damit alle Fernseher/Neustarts im Takt bleiben)
        h, m = (int(x) for x in jetzt_hhmm.split(":"))
        return reihe[((h * 60 + m) // k.get("minuten", 5)) % len(reihe)]
    return next((x for x in layouts if x["id"] == tv.get("layout")), layouts[0])


def entitaeten(layouts, wetter):
    """Alle Entitäten, deren Werte die TV-Seiten brauchen (Bausteine und Bedingungen)."""
    s = {wetter} if wetter else set()
    for l in layouts:
        for e in l["elemente"]:
            o = e["optionen"]
            if o.get("entity"):
                s.add(o["entity"])
            for r in o.get("liste", []):
                s.add(r["entity"])
            if e["bedingung"] and e["bedingung"].get("entity"):
                s.add(e["bedingung"]["entity"])
    return {x for x in s if x}


# ---------- Vorlagen ----------
def _el(eid, typ, x, y, w, h, **kw):
    return dict({"id": eid, "typ": typ, "x": x, "y": y, "w": w, "h": h}, **kw)


def standard(raeume=(), kacheln=(), vorhersage=True):
    """Nachbau der bisherigen Ansicht (Wetterbild, Spalte links, großes Video, Leiste unten)."""
    el = [_el("bar", "flaeche", 0, 22, 48, 5, karte=False, optionen={"farbe": "#f0f0f0"}),
          _el("uhr", "uhr", 1, 1, 8, 3), _el("datum", "datum", 1, 5, 9, 1),
          _el("temp", "temperatur", 1, 7, 8, 2), _el("lage", "wetterlage", 1, 10, 9, 1),
          _el("feuchte", "feuchte", 1, 12, 9, 1), _el("wind", "wind", 1, 13, 9, 1),
          _el("raeume", "raeume", 1, 15, 9, 5, optionen={"liste": list(raeume)}),
          _el("sender", "sender", 1, 20, 9, 1),
          _el("video", "video", 11, 1, 36, 20, karte=True)]
    x = 0
    if vorhersage:
        el.append(_el("vh", "vorhersage", 0, 22, 8, 5, karte=True))
        x = 8
    for i, k in enumerate(list(kacheln)[:8]):
        el.append(_el(f"k{i + 1}", "kachel", x + i * 5, 22, 5, 5, karte=True,
                      optionen={"entity": k["entity"], "name": k["name"], "icon": k.get("icon", "mdi-information-outline")}))
    return pruefe_layout({"id": "standard", "name": "Standard", "hintergrund": {"art": "wetter", "abdunkeln": True},
                          "elemente": el})


def _z(text, wert="", info="", icon="", hervor=False):
    return {"text": text, "info": info, "wert": wert, "icon": icon, "hervor": hervor}


def vorlagen(sprache="de"):
    """Vorlagen für neue Layouts – Namen und Beispieltexte in der Sprache der Verwaltung (seit 0.53 auch Englisch).
    Die Beispieltexte sind Platzhalter: Logo, Zeilen, Adressen und Datenquellen trägt man im Editor ein."""
    import datetime
    en = sprache == "en"
    t = lambda de, eng: eng if en else de
    eur = lambda de, eng: eng if en else de                     # Preise: 6,50 € / €6.50
    fest = (datetime.date.today() + datetime.timedelta(days=60)).isoformat()

    def laufband(y, text, farbe, schrift="#ffffff"):
        return [_el("lauff", "flaeche", 0, y, 48, 27 - y, optionen={"farbe": farbe, "deckkraft": 100}),
                _el("lauf", "text", 0, y, 48, 27 - y, textfarbe=schrift, optionen={"laufband": True, "text": text})]

    def kopf(farbe, titel):
        return [_el("kopf", "flaeche", 0, 0, 48, 3, optionen={"farbe": farbe, "deckkraft": 100}),
                _el("logo", "logo", 1, 0, 9, 3, ausrichtung="links"),
                _el("titel", "text", 11, 0, 27, 3, ausrichtung="mitte", textfarbe="#ffffff", gewicht="fett", optionen={"text": titel}),
                _el("uhr", "uhr", 40, 0, 7, 3, ausrichtung="rechts", textfarbe="#ffffff", gewicht="normal")]

    def liste(eid, x, y, w, h, titel, zeilen, karte=True, **kw):
        return _el(eid, "liste", x, y, w, h, karte=karte, ausrichtung="oben-links", optionen=dict({"titel": titel, "zeilen": zeilen}, **kw))

    eg, og1, og2, og3, ug = t("EG", "GF"), t("1. OG", "1st fl."), t("2. OG", "2nd fl."), t("3. OG", "3rd fl."), t("UG", "LG")
    return [
        standard(),
        pruefe_layout({"id": "videogross", "name": t("Video groß", "Large video"), "hintergrund": {"art": "farbe", "farbe": "#000000"},
                       "elemente": [_el("video", "video", 0, 0, 48, 27), _el("uhr", "uhr", 1, 1, 6, 2, karte=True),
                                    _el("temp", "temperatur", 1, 3, 6, 1, karte=True)]}),
        pruefe_layout({"id": "nurvideo", "name": t("Nur Video", "Video only"), "hintergrund": {"art": "farbe", "farbe": "#000000"},
                       "elemente": [_el("video", "video", 0, 0, 48, 27, optionen={"leiste": False})]}),
        pruefe_layout({"id": "info", "name": t("Info ohne Video", "Info without video"), "hintergrund": {"art": "wetter", "abdunkeln": False},
                       "elemente": [_el("uhr", "uhr", 14, 4, 20, 7, ausrichtung="mitte"),
                                    _el("datum", "datum", 14, 11, 20, 2, ausrichtung="mitte"),
                                    _el("temp", "temperatur", 14, 14, 10, 3, ausrichtung="mitte"),
                                    _el("lage", "wetterlage", 24, 14, 10, 3, ausrichtung="mitte"),
                                    _el("vh", "vorhersage", 16, 19, 16, 5, karte=True),
                                    _el("sender", "sender", 14, 25, 20, 1, ausrichtung="mitte")]}),
        # Praxis: ruhig und hell für Wartezimmer einer Praxis – Logo, Uhr, Wetter, ruhiges Video ohne Leiste,
        # Willkommenstext. Für ruhige Tiere am Fernseher die Kategorien auf Meer, Vögel, Wald beschränken.
        pruefe_layout({"id": "praxis", "name": t("Praxis – ruhig (Wartezimmer)", "Practice – calm (waiting room)"),
                       "hintergrund": {"art": "stil", "stil": "himmel", "wechsel": "tageszeit", "nachts_dunkler": False, "abdunkeln": False},
                       "thema": {"schema": "hell", "akzent": "#5bb5a2", "schrift": "Lato"},
                       "elemente": [_el("panel", "flaeche", 1, 1, 14, 25, karte=False, optionen={"farbe": "#ffffff", "deckkraft": 82}),
                                    _el("logo", "logo", 2, 2, 12, 5, ausrichtung="mitte"),
                                    _el("uhr", "uhr", 2, 8, 12, 4, ausrichtung="mitte", gewicht="duenn"),
                                    _el("datum", "datum", 2, 12, 12, 1, ausrichtung="mitte"),
                                    _el("temp", "temperatur", 2, 15, 12, 3, ausrichtung="mitte", gewicht="duenn"),
                                    _el("lage", "wetterlage", 2, 18, 12, 1, ausrichtung="mitte"),
                                    _el("video", "video", 16, 1, 31, 21, karte=True, optionen={"leiste": False}),
                                    _el("gruss", "text", 16, 23, 31, 3, karte=True, ausrichtung="mitte", gewicht="duenn",
                                        optionen={"text": t("Herzlich willkommen – wir sind gleich für Sie da.", "Welcome – we will be with you shortly.")})]}),
        # Firma: sachlich im eigenen Farbton – Kopfzeile mit Logo, Uhr, Datum; Video groß; Wetter rechts; Laufband unten
        pruefe_layout({"id": "firma", "name": t("Firma – Corporate Design", "Company – corporate design"),
                       "hintergrund": {"art": "farbe", "farbe": "#eef1f5"},
                       "thema": {"schema": "hell", "akzent": "#1f4e79", "schrift": "Montserrat"},
                       "elemente": [_el("kopf", "flaeche", 0, 0, 48, 3, optionen={"farbe": "#1f4e79", "deckkraft": 100}),
                                    _el("logo", "logo", 1, 0, 10, 3, ausrichtung="links"),
                                    _el("datum", "datum", 24, 1, 13, 1, ausrichtung="rechts", textfarbe="#ffffff"),
                                    _el("uhr", "uhr", 38, 0, 9, 3, ausrichtung="rechts", textfarbe="#ffffff", gewicht="normal"),
                                    _el("video", "video", 1, 4, 34, 19, karte=True),
                                    _el("temp", "temperatur", 36, 4, 11, 3, karte=True, ausrichtung="mitte"),
                                    _el("lage", "wetterlage", 36, 7, 11, 2, karte=True, ausrichtung="mitte"),
                                    _el("vh", "vorhersage", 36, 9, 11, 6, karte=True),
                                    _el("gruss", "text", 36, 15, 11, 8, karte=True, ausrichtung="mitte",
                                        optionen={"text": t("Willkommen! Schön, dass Sie da sind.", "Welcome! Great to have you here.")}),
                                    _el("band", "flaeche", 0, 24, 48, 3, optionen={"farbe": "#1f4e79", "deckkraft": 100}),
                                    _el("lauf", "text", 0, 24, 48, 3, textfarbe="#ffffff",
                                        optionen={"laufband": True, "text": t("+++ Heute 14:00 Uhr: Teambesprechung im Saal A +++ "
                                                  "Kantine: Gemüselasagne +++ Wir begrüßen unsere Gäste +++",
                                                  "+++ Today 2 pm: team meeting in room A +++ Canteen: vegetable lasagne +++ We welcome our guests +++")})]}),
        # ---------- seit 0.53: Vorlagen für Branchen (Baustein „Liste“) ----------
        # Imbiss (seit 0.54 mit Bildern): links Essensfotos als Diashow, die sich langsam bewegen, darauf das Tagesangebot;
        # rechts die Karte auf dunklen, durchscheinenden Karten; Laufband in der Akzentfarbe; ohne Video (spart CPU)
        pruefe_layout({"id": "imbiss", "name": t("Imbiss – Menütafel", "Snack bar – menu board"),
                       "hintergrund": {"art": "stil", "stil": "essen", "wechsel": "diashow", "diashow_s": 12, "bewegen": True,
                                       "farbe": "#161616", "nachts_dunkler": False, "abdunkeln": False,
                                       "bereich": {"x": 0, "y": 0, "w": 20, "h": 24}},
                       "thema": {"schema": "dunkel", "akzent": "#f5a623", "schrift": "Montserrat", "karte": "glas_dunkel"},
                       "elemente": [_el("logo", "logo", 1, 1, 9, 4, ausrichtung="links"),
                                    _el("titel", "text", 21, 1, 17, 3, ausrichtung="links", gewicht="fett", textfarbe="#f5a623",
                                        optionen={"text": t("Unsere Karte", "Our menu")}),
                                    _el("uhr", "uhr", 39, 1, 8, 3, ausrichtung="rechts"),
                                    liste("l1", 20, 4, 14, 20, t("Burger & Wurst", "Burgers & sausages"), [
                                        _z("Hamburger", eur("6,50 €", "€6.50"), t("100 % Rind, Salat, Tomate", "100 % beef, lettuce, tomato")),
                                        _z("Cheeseburger", eur("7,00 €", "€7.00"), t("mit Cheddar", "with cheddar")),
                                        _z(t("Veggie-Burger", "Veggie burger"), eur("7,50 €", "€7.50"), t("vegetarisch", "vegetarian"), "mdi-leaf"),
                                        _z("Currywurst", eur("4,50 €", "€4.50"), t("hausgemachte Soße", "homemade sauce")),
                                        _z("Bratwurst", eur("3,90 €", "€3.90")),
                                        _z(t("Schnitzel im Brötchen", "Schnitzel roll"), eur("6,90 €", "€6.90"))]),
                                    liste("l2", 34, 4, 14, 9, t("Beilagen", "Sides"), [
                                        _z(t("Pommes", "Fries"), eur("3,00 €", "€3.00")),
                                        _z(t("Süßkartoffel-Pommes", "Sweet potato fries"), eur("4,20 €", "€4.20")),
                                        _z(t("Zwiebelringe", "Onion rings"), eur("3,80 €", "€3.80")),
                                        _z(t("Kleiner Salat", "Side salad"), eur("3,50 €", "€3.50"))]),
                                    _el("angebotf", "flaeche", 1, 17, 18, 6, karte=True, optionen={"farbe": "#f5a623", "deckkraft": 94}),
                                    _el("angebot", "text", 2, 17, 16, 6, ausrichtung="mitte", gewicht="fett", textfarbe="#161616",
                                        optionen={"text": t("Tagesangebot: Currywurst, Pommes und Getränk 8,90 €",
                                                            "Today's deal: currywurst, fries and a drink €8.90")}),
                                    liste("l3", 34, 13, 14, 11, t("Getränke", "Drinks"), [
                                        _z("Cola", eur("2,80 €", "€2.80"), t("0,33 l", "330 ml")),
                                        _z(t("Wasser", "Water"), eur("2,20 €", "€2.20"), t("0,5 l", "500 ml")),
                                        _z(t("Apfelschorle", "Apple spritzer"), eur("2,80 €", "€2.80"), t("0,33 l", "330 ml")),
                                        _z(t("Bier", "Beer"), eur("3,90 €", "€3.90"), t("0,5 l", "500 ml")),
                                        _z(t("Kaffee", "Coffee"), eur("2,20 €", "€2.20"))]),
                                    *laufband(24, t("+++ Alle Preise inkl. MwSt. +++ Allergene auf Nachfrage +++ Kartenzahlung möglich +++",
                                                    "+++ All prices incl. VAT +++ Ask us about allergens +++ Cards welcome +++"), "#f5a623", "#161616")]}),
        # Einkaufszentrum: Stadtbild nach Tageszeit (langsam bewegt), Wegweiser mit Ebene, Aktionen als Galerie,
        # Öffnungszeiten, Wetter, Laufband – alles auf dunklen, durchscheinenden Karten
        pruefe_layout({"id": "center", "name": t("Einkaufszentrum – Info", "Shopping centre – info"),
                       "hintergrund": {"art": "stil", "stil": "stadt", "wechsel": "tageszeit", "bewegen": True, "abdunkeln": False},
                       "thema": {"schema": "dunkel", "akzent": "#e0457b", "schrift": "Open Sans", "karte": "glas_dunkel"},
                       "elemente": [*kopf("#c2185b", t("Willkommen im Center", "Welcome to the centre")),
                                    liste("weg", 1, 4, 22, 19, t("Wegweiser", "Directory"), [
                                        _z(t("Supermarkt", "Supermarket"), eg, icon="mdi-cart"),
                                        _z(t("Drogerie", "Drugstore"), eg, icon="mdi-spa"),
                                        _z(t("Apotheke", "Pharmacy"), eg, icon="mdi-pill"),
                                        _z("Information", eg, icon="mdi-information"),
                                        _z(t("Toiletten", "Toilets"), eg, icon="mdi-human-male-female"),
                                        _z(t("Mode", "Fashion"), og1, icon="mdi-tshirt-crew"),
                                        _z(t("Schuhe", "Shoes"), og1, icon="mdi-shoe-sneaker"),
                                        _z(t("Elektronik", "Electronics"), og1, icon="mdi-television"),
                                        _z("Café", og2, icon="mdi-coffee"),
                                        _z(t("Restaurants", "Food court"), og2, icon="mdi-silverware-fork-knife"),
                                        _z(t("Parkhaus", "Car park"), ug, icon="mdi-parking")]),
                                    _el("aktion", "galerie", 24, 4, 23, 13, karte=True, optionen={"sekunden": 10}),
                                    liste("zeit", 24, 18, 12, 5, t("Öffnungszeiten", "Opening hours"), [
                                        _z(t("Mo–Sa", "Mon–Sat"), t("9–20 Uhr", "9 am–8 pm")),
                                        _z(t("Sonntag", "Sunday"), t("geschlossen", "closed"))], punkte=False),
                                    _el("temp", "temperatur", 37, 18, 10, 3, karte=True, ausrichtung="mitte"),
                                    _el("lage", "wetterlage", 37, 21, 10, 2, karte=True, ausrichtung="mitte"),
                                    *laufband(24, t("+++ Diese Woche: Frühlingsaktion in allen Geschäften +++ 2 Stunden kostenlos parken +++ "
                                                    "Kostenloses WLAN: Center-Gast +++",
                                                    "+++ This week: spring sale in all shops +++ 2 hours free parking +++ Free Wi-Fi: Centre-Guest +++"), "#c2185b")]}),
        # Praxis – Info: Sprechzeiten, Hinweise, QR-Code zur Online-Terminbuchung, Notdienst, Laufband (seit 0.54);
        # Himmel nach Tageszeit, langsam bewegt, helle durchscheinende Karten; ohne Video
        pruefe_layout({"id": "praxisinfo", "name": t("Praxis – Info (Sprechzeiten)", "Practice – info (opening hours)"),
                       "hintergrund": {"art": "stil", "stil": "himmel", "wechsel": "tageszeit", "bewegen": True,
                                       "nachts_dunkler": False, "abdunkeln": False},
                       "thema": {"schema": "hell", "akzent": "#2a9d8f", "schrift": "Lato", "karte": "glas_hell"},
                       "elemente": [_el("kopfglas", "flaeche", 1, 1, 46, 4, karte=True, optionen={"farbe": "#ffffff", "deckkraft": 84}),
                                    _el("logo", "logo", 2, 1, 12, 4, ausrichtung="links"),
                                    _el("uhr", "uhr", 38, 1, 8, 3, ausrichtung="rechts", gewicht="duenn"),
                                    _el("datum", "datum", 27, 4, 19, 1, ausrichtung="rechts"),
                                    liste("zeiten", 1, 6, 22, 11, t("Sprechzeiten", "Opening hours"), [
                                        _z(t("Montag", "Monday"), t("8–12 · 14–18 Uhr", "8–12 · 2–6 pm")),
                                        _z(t("Dienstag", "Tuesday"), t("8–12 · 14–18 Uhr", "8–12 · 2–6 pm")),
                                        _z(t("Mittwoch", "Wednesday"), t("8–12 Uhr", "8 am–12 pm")),
                                        _z(t("Donnerstag", "Thursday"), t("8–12 · 14–19 Uhr", "8–12 · 2–7 pm")),
                                        _z(t("Freitag", "Friday"), t("8–13 Uhr", "8 am–1 pm"))]),
                                    liste("hinweis", 24, 6, 23, 11, t("Bitte beachten", "Please note"), [
                                        _z(t("Versichertenkarte bitte am Empfang zeigen", "Please show your insurance card at reception"), icon="mdi-card-account-details"),
                                        _z(t("Handy bitte lautlos stellen", "Please switch your phone to silent"), icon="mdi-cellphone-off"),
                                        _z(t("Bei Infekt bitte Maske tragen", "Please wear a mask if you have an infection"), icon="mdi-face-mask"),
                                        _z(t("Wartezeiten können variieren – danke für Ihre Geduld", "Waiting times may vary – thank you for your patience"), icon="mdi-clock-outline")],
                                          punkte=False),
                                    _el("qr", "qrcode", 1, 18, 6, 5, karte=True, optionen={"inhalt": "https://example.org/termin",
                                                                                          "beschriftung": t("Online-Termin", "Book online")}),
                                    _el("notdienst", "text", 8, 18, 23, 5, karte=True, ausrichtung="mitte",
                                        optionen={"text": t("Außerhalb der Sprechzeiten: ärztlicher Bereitschaftsdienst 116 117 – im Notfall 112",
                                                            "Outside opening hours: please call the out-of-hours service – in an emergency 112")}),
                                    _el("vh", "vorhersage", 32, 18, 15, 5, karte=True),
                                    *laufband(24, t("+++ Vom 23.12. bis 2.1. geschlossen – Vertretung: Praxis Dr. Muster +++ "
                                                    "Grippeimpfung ab sofort ohne Termin +++ Rezepte auch per Telefon bestellen +++",
                                                    "+++ Closed 23 Dec – 2 Jan, cover: Dr Example's practice +++ Flu jabs now without "
                                                    "appointment +++ Order prescriptions by phone too +++"), "#2a9d8f")]}),
        # Krankenhaus – Foyer: Wegweiser zu den Stationen, Besuchszeiten, Meldung aus HA, Wetter, Laufband; ohne Video;
        # seit 0.54 helle Architektur als langsame Diashow hinter durchscheinenden Karten
        pruefe_layout({"id": "klinik", "name": t("Krankenhaus – Foyer", "Hospital – lobby"),
                       "hintergrund": {"art": "stil", "stil": "architektur", "wechsel": "diashow", "diashow_s": 30, "bewegen": True,
                                       "nachts_dunkler": False, "abdunkeln": False},
                       "thema": {"schema": "hell", "akzent": "#0d47a1", "schrift": "Noto Sans", "karte": "glas_hell"},
                       "elemente": [*kopf("#0d47a1", t("Herzlich willkommen", "Welcome")),
                                    liste("weg", 1, 4, 30, 16, t("Wegweiser", "Directory"), [
                                        _z(t("Notaufnahme", "Emergency"), t("EG · Eingang B", "GF · Entrance B"), icon="mdi-ambulance", hervor=True),
                                        _z(t("Patientenaufnahme", "Admissions"), eg, icon="mdi-account-check"),
                                        _z(t("Radiologie", "Radiology"), eg, icon="mdi-radiology-box"),
                                        _z("Cafeteria", eg, icon="mdi-coffee"),
                                        _z(t("Innere Medizin", "Internal medicine"), og1, icon="mdi-stethoscope"),
                                        _z(t("Kardiologie", "Cardiology"), og1, icon="mdi-heart-pulse"),
                                        _z(t("Kapelle", "Chapel"), og1, icon="mdi-church"),
                                        _z(t("Chirurgie", "Surgery"), og2, icon="mdi-hospital-box"),
                                        _z(t("Geburtshilfe", "Maternity"), og3, icon="mdi-baby-carriage"),
                                        _z(t("Parkhaus", "Car park"), ug, icon="mdi-parking")]),
                                    liste("besuch", 32, 4, 15, 9, t("Besuchszeiten", "Visiting hours"), [
                                        _z(t("Stationen", "Wards"), t("14–19 Uhr", "2–7 pm")),
                                        _z(t("Intensivstation", "Intensive care"), t("nach Absprache", "by arrangement")),
                                        _z(t("Kinderstation", "Children's ward"), t("Eltern jederzeit", "parents any time"))], punkte=False),
                                    _el("temp", "temperatur", 32, 14, 7, 3, karte=True, ausrichtung="mitte"),
                                    _el("lage", "wetterlage", 39, 14, 8, 3, karte=True, ausrichtung="mitte"),
                                    _el("vh", "vorhersage", 32, 17, 15, 6, karte=True),
                                    _el("meldung", "meldung", 1, 20, 30, 3, ausrichtung="mitte", karte=True),
                                    *laufband(24, t("+++ Bitte beachten Sie die Hygieneregeln +++ Cafeteria täglich 8–18 Uhr +++ "
                                                    "WLAN für Patienten und Besucher: Klinik-Gast +++",
                                                    "+++ Please follow the hygiene rules +++ Cafeteria daily 8 am–6 pm +++ "
                                                    "Wi-Fi for patients and visitors: Hospital-Guest +++"), "#0d47a1")]}),
        # Hotel / Pension – Lobby: Bergbild, dunkle Tafel mit Uhr und Wetter, Infos, WLAN-QR-Code, Veranstaltungen, Video
        pruefe_layout({"id": "hotel", "name": t("Hotel / Pension – Lobby", "Hotel / guest house – lobby"),
                       "hintergrund": {"art": "stil", "stil": "berge", "wechsel": "tageszeit", "abdunkeln": True, "bewegen": True},
                       "thema": {"schema": "dunkel", "akzent": "#c9a227", "schrift": "Noto Serif", "karte": "glas_dunkel"},
                       "elemente": [_el("glas", "flaeche", 1, 1, 16, 25, optionen={"farbe": "#000000", "deckkraft": 50}),
                                    _el("logo", "logo", 2, 2, 14, 4, ausrichtung="mitte"),
                                    _el("uhr", "uhr", 2, 7, 14, 4, ausrichtung="mitte", gewicht="duenn"),
                                    _el("datum", "datum", 2, 11, 14, 1, ausrichtung="mitte"),
                                    _el("vh", "vorhersage", 2, 13, 14, 6),
                                    _el("wlan", "qrcode", 2, 20, 6, 6, optionen={"inhalt": "WIFI:T:WPA;S:Hotel-Gast;P:bitte-aendern;;",
                                                                                "beschriftung": t("WLAN", "Wi-Fi")}),
                                    _el("wlantext", "text", 8, 20, 8, 6, ausrichtung="mitte",
                                        optionen={"text": t("Code scannen und lossurfen", "Scan the code to connect")}),
                                    liste("info", 18, 1, 29, 9, t("Gut zu wissen", "Good to know"), [
                                        _z(t("Frühstück", "Breakfast"), t("7–10:30 Uhr", "7–10:30 am"), icon="mdi-food-croissant"),
                                        _z(t("Rezeption", "Reception"), t("7–22 Uhr", "7 am–10 pm"), icon="mdi-key"),
                                        _z(t("Sauna & Spa", "Sauna & spa"), t("16–21 Uhr", "4–9 pm"), icon="mdi-hot-tub"),
                                        _z("Check-out", t("bis 11 Uhr", "by 11 am"), icon="mdi-door-open")]),
                                    # feste Liste – wer einen Kalender pflegt, nimmt stattdessen den Baustein „Kalender“
                                    liste("heute", 18, 11, 13, 15, t("Heute bei uns", "Today"), [
                                        _z(t("Geführte Wanderung", "Guided hike"), t("9:30", "9:30 am"), t("Treffpunkt Rezeption", "Meet at reception")),
                                        _z(t("Kaffee & Kuchen", "Coffee & cake"), t("15:00", "3 pm"), t("Terrasse", "Terrace")),
                                        _z(t("Weinprobe", "Wine tasting"), t("19:00", "7 pm"), t("Kaminzimmer", "Fireplace room"), hervor=True)]),
                                    _el("video", "video", 32, 11, 15, 15, karte=True)]}),
        # Fitnessstudio / Verein: Kursplan, Auslastung (Ampel aus einer Datenquelle), Countdown zum nächsten Event, Video;
        # seit 0.54 Sportbilder als langsame Diashow, leicht abgedunkelt, dunkle durchscheinende Karten
        pruefe_layout({"id": "fitness", "name": t("Fitnessstudio / Verein", "Gym / sports club"),
                       "hintergrund": {"art": "stil", "stil": "sport", "wechsel": "diashow", "diashow_s": 15, "bewegen": True,
                                       "farbe": "#111111", "nachts_dunkler": False, "abdunkeln": False},
                       "thema": {"schema": "dunkel", "akzent": "#e53935", "schrift": "Montserrat", "karte": "glas_dunkel"},
                       "elemente": [_el("dunkel", "flaeche", 0, 0, 48, 24, optionen={"farbe": "#000000", "deckkraft": 35}),
                                    _el("logo", "logo", 1, 1, 9, 4, ausrichtung="links"),
                                    _el("titel", "text", 11, 1, 26, 4, ausrichtung="mitte", gewicht="fett", optionen={"text": t("Heute im Studio", "Today at the gym")}),
                                    _el("uhr", "uhr", 38, 1, 9, 4, ausrichtung="rechts", gewicht="fett"),
                                    liste("kurse", 1, 6, 20, 17, t("Kurse heute", "Classes today"), [
                                        _z(t("Rücken fit", "Back fit"), "09:00", t("Raum 1", "Room 1"), "mdi-human-handsup"),
                                        _z("Yoga", "10:30", t("Raum 2", "Room 2"), "mdi-yoga"),
                                        _z("Spinning", "17:00", t("Raum 1 · bitte anmelden", "Room 1 · please sign up"), "mdi-bicycle", True),
                                        _z("Zumba", "18:30", t("Raum 2", "Room 2"), "mdi-run"),
                                        _z("Functional Training", "19:30", t("Halle", "Hall"), "mdi-dumbbell")]),
                                    _el("video", "video", 22, 6, 25, 13, karte=True),
                                    _el("auslastung", "anzeige", 22, 20, 12, 3, karte=True,
                                        optionen={"name": t("Auslastung", "Occupancy"), "darstellung": "ampel", "einheit": "%"}),
                                    _el("fest", "countdown", 35, 20, 12, 3, karte=True, ausrichtung="mitte",
                                        optionen={"ziel": fest, "vorlage": t("noch {tage} Tage bis zum Sommerfest", "{tage} days to our summer party"),
                                                  "ende": t("Heute: Sommerfest!", "Today: summer party!")}),
                                    *laufband(24, t("+++ Handtuch bitte nicht vergessen +++ Getränke an der Theke +++ Neue Kurse ab Montag +++",
                                                    "+++ Please bring a towel +++ Drinks at the bar +++ New classes from Monday +++"), "#e53935")]}),
        # Kantine – Speiseplan: Woche als Liste (am einfachsten per CSV-Datei als Datenquelle), Extras, Zeiten, Laufband;
        # seit 0.54 Naturbild nach Tageszeit, langsam bewegt, helle durchscheinende Karten
        pruefe_layout({"id": "kantine", "name": t("Kantine – Speiseplan", "Canteen – weekly menu"),
                       "hintergrund": {"art": "stil", "stil": "natur", "wechsel": "tageszeit", "bewegen": True,
                                       "nachts_dunkler": False, "abdunkeln": False},
                       "thema": {"schema": "hell", "akzent": "#2e7d32", "schrift": "Lato", "karte": "glas_hell"},
                       "elemente": [*kopf("#2e7d32", t("Speiseplan dieser Woche", "This week's menu")),
                                    liste("woche", 1, 4, 32, 19, t("Mittagessen", "Lunch"), [
                                        _z(t("Montag: Spaghetti Bolognese", "Monday: spaghetti bolognese"), eur("5,20 €", "€5.20"),
                                           t("vegetarisch: mit Tomatensoße · A, C, G", "vegetarian: with tomato sauce · A, C, G")),
                                        _z(t("Dienstag: Hähnchencurry mit Reis", "Tuesday: chicken curry with rice"), eur("5,60 €", "€5.60"),
                                           t("vegetarisch: Gemüsecurry", "vegetarian: vegetable curry")),
                                        _z(t("Mittwoch: Gemüselasagne", "Wednesday: vegetable lasagne"), eur("4,90 €", "€4.90"),
                                           t("vegetarisch · A, G", "vegetarian · A, G")),
                                        _z(t("Donnerstag: Schnitzel mit Kartoffelsalat", "Thursday: schnitzel with potato salad"), eur("6,20 €", "€6.20"), "A, C"),
                                        _z(t("Freitag: Fisch mit Salzkartoffeln", "Friday: fish with boiled potatoes"), eur("6,40 €", "€6.40"),
                                           t("vegetarisch: Gemüsepfanne · D", "vegetarian: stir-fried vegetables · D"))]),
                                    liste("extra", 34, 4, 13, 9, t("Außerdem", "Also"), [
                                        _z(t("Salatbar", "Salad bar"), eur("1,20 €/100 g", "€1.20/100 g")),
                                        _z(t("Suppe", "Soup"), eur("2,50 €", "€2.50")),
                                        _z("Dessert", eur("1,80 €", "€1.80")),
                                        _z(t("Kaffee", "Coffee"), eur("1,00 €", "€1.00"))]),
                                    liste("zeit", 34, 14, 13, 6, t("Geöffnet", "Open"), [
                                        _z(t("Frühstück", "Breakfast"), "7:30–9:30"),
                                        _z(t("Mittag", "Lunch"), "11:30–14:00")], punkte=False),
                                    _el("temp", "temperatur", 34, 21, 13, 2, karte=True, ausrichtung="mitte"),
                                    *laufband(24, t("+++ Allergene: A Gluten · C Ei · D Fisch · G Milch +++ Guten Appetit! +++",
                                                    "+++ Allergens: A gluten · C egg · D fish · G milk +++ Enjoy your meal! +++"), "#2e7d32")]}),
        # Fenster zur Welt: Live-Video über den ganzen Bildschirm, oben links eine dunkle „Glas“-Tafel mit Uhr und Wetter,
        # oben mittig ein Meldungsbanner aus HA (erscheint erst, wenn eine Entität eingetragen ist)
        pruefe_layout({"id": "fenster", "name": t("Fenster zur Welt", "Window to the world"),
                       "hintergrund": {"art": "farbe", "farbe": "#000000"},
                       "thema": {"schema": "dunkel", "akzent": "#ffcc66", "schrift": "Open Sans"},
                       "elemente": [_el("video", "video", 0, 0, 48, 27),
                                    _el("glas", "flaeche", 1, 1, 15, 7, optionen={"farbe": "#000000", "deckkraft": 45}),
                                    _el("uhr", "uhr", 2, 1, 8, 4, gewicht="duenn"),
                                    _el("temp", "temperatur", 10, 1, 5, 4, ausrichtung="rechts", gewicht="duenn"),
                                    _el("datum", "datum", 2, 5, 13, 1),
                                    _el("lage", "wetterlage", 2, 6, 7, 1),
                                    _el("sender", "sender", 9, 6, 6, 1, ausrichtung="rechts"),
                                    _el("meldung", "meldung", 17, 1, 22, 3, ausrichtung="mitte")]}),
        # Galerie Vollbild (seit 0.45): ein Galerie-Ordner über den ganzen Bildschirm – den Ordner wählt man im Editor
        pruefe_layout({"id": "galerie", "name": t("Galerie Vollbild", "Gallery full screen"), "hintergrund": {"art": "farbe", "farbe": "#000000"},
                       "elemente": [_el("galerie", "galerie", 0, 0, 48, 27, optionen={"sekunden": 15})]}),
        pruefe_layout({"id": "nacht", "name": t("Nacht (nur Uhr, gedimmt)", "Night (clock only, dimmed)"), "hintergrund": {"art": "farbe", "farbe": "#000000"},
                       "thema": {"schema": "gedimmt", "akzent": "#555555"},
                       "elemente": [_el("uhr", "uhr", 16, 10, 16, 6, ausrichtung="mitte")]}),
    ]
