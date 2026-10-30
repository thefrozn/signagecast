# Layouts von SignageCast: was ein Fernseher zeigt und wo. Fläche 1920x1080, Raster 48 x 27 Felder à 40 px.
# Ein Layout = Hintergrund + Farbschema + Liste von Bausteinen (Position/Größe in Rasterfeldern, Optionen, Bedingung).
# Werte kommen aus HA-Entitäten oder (seit 0.9) aus eigenen Datenquellen (app/quellen.py: API, RSS, Bild).
import copy, re

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
STILE = ["natur", "stadt", "himmel", "berge", "meer", "gemischt"]
TAGESZEITEN = ["morgen", "tag", "abend", "nacht"]
WECHSEL = ["tageszeit", "tageszeit_wetter", "diashow"]

# Bausteine: Typ -> erlaubte Optionen mit Prüffunktion und Standardwert
def _b(w):  return bool(w)
def _t(n):  return lambda w: str(w)[:n]
def _ent(domains=None):
    def p(w):
        w = str(w or "").strip()
        if w and (not ENTITY.fullmatch(w) or (domains and w.split(".")[0] not in domains)):
            raise ValueError(f"ungültige Entität {w!r}")
        return w
    return p
def _zahl(lo, hi):
    def p(w):
        w = int(w)
        if not lo <= w <= hi:
            raise ValueError(f"{w} nicht zwischen {lo} und {hi}")
        return w
    return p
def _icon(w):
    w = str(w or "mdi-information-outline")
    if not re.fullmatch(r"mdi-[a-z0-9-]{1,60}", w):
        raise ValueError("Symbol muss mdi-… sein")
    return w
def _farbe(w):
    w = str(w or "")
    if w and not FARBE.fullmatch(w):
        raise ValueError("Farbe als #rrggbb")
    return w
def _bild(w):
    w = str(w or "")
    if w and not re.fullmatch(r"[0-9a-f]{16}\.(jpg|png)", w):
        raise ValueError("ungültiges Bild")
    return w
def _fl(lo, hi):
    def p(w):
        w = float(str(w).replace(",", "."))
        if not lo <= w <= hi:
            raise ValueError(f"{w} nicht zwischen {lo} und {hi}")
        return w
    return p
def _qid(w):
    w = str(w or "").strip()
    if w and not re.fullmatch(r"[a-z0-9_]{2,16}", w):
        raise ValueError("ungültige Datenquelle")
    return w
def _pfad(w):
    w = str(w or "").strip()
    if len(w) > 160 or "\n" in w:
        raise ValueError("Pfad zu lang")
    return w
def _url(w):
    w = str(w or "").strip()
    if w and not re.fullmatch(r"https?://[^\s\"'<>]{1,1000}", w):
        raise ValueError("Adresse mit http:// oder https://")
    return w
def _icon_leer(w):
    return _icon(w) if str(w or "").strip() else ""
def _wahl(*werte):
    def p(w):
        if w not in werte:
            raise ValueError(f"erlaubt: {', '.join(werte)}")
        return w
    return p
def _raeume(w):
    return [{"name": str(r.get("name", ""))[:30], "entity": _ent()(r.get("entity"))} for r in (w or [])[:8] if r.get("entity")]

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
    "kalender":   {"entity": (_ent(["calendar"]), ""), "quelle": (_qid, ""), "anzahl": (_zahl(1, 10), 4), "tage": (_zahl(1, 60), 14),
                   "titel": (_t(40), "")},                                   # quelle = iCal-Datenquelle statt HA (seit 0.10)
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
    "webseite":   {"url": (_url, ""), "neu_laden_min": (_zahl(0, 1440), 15), "zoom": (_zahl(25, 300), 100),
                   "versatz_x": (_zahl(0, 10000), 0), "versatz_y": (_zahl(0, 10000), 0)},
}
# Mindestgröße je Typ (Felder)
MINDEST = {"logo": (2, 1), "video": (8, 5), "kamera": (4, 3), "kalender": (6, 3), "raeume": (4, 2), "vorhersage": (4, 3),
           "apibild": (2, 2), "qrcode": (2, 2), "apiliste": (4, 1), "webcam": (4, 3), "diagramm": (4, 2), "webseite": (4, 3)}


def _pruefe_bedingung(b):
    if not b or not (b.get("entity") or b.get("quelle")):
        return None
    op = b.get("op", "=")
    if op not in OPERATOREN:
        raise ValueError("unbekannter Vergleich")
    if b.get("quelle"):                       # Wert aus einer Datenquelle (seit 0.9)
        return {"quelle": _qid(b["quelle"]), "pfad": _pfad(b.get("pfad", "")), "op": op, "wert": str(b.get("wert", ""))[:60]}
    return {"entity": _ent()(b["entity"]), "op": op, "wert": str(b.get("wert", ""))[:60]}


def pruefe_layout(l):
    lid = str(l.get("id", ""))
    if not re.fullmatch(r"[a-z0-9]{2,16}", lid):
        raise ValueError(f"ungültige Layout-Kennung {lid!r}")
    hg = l.get("hintergrund", {}) or {}
    art = hg.get("art", "wetter")
    if art not in ("wetter", "stil", "farbe", "bild"):
        raise ValueError("Hintergrund: wetter, stil, farbe oder bild")
    def _bildname(b):
        b = str(b or "")
        if b and not re.fullmatch(r"[0-9a-f]{16}\.(jpg|png)", b):
            raise ValueError("ungültiges Hintergrundbild")
        return b
    bild = _bildname(hg.get("bild"))
    je_zeit = {z: _bildname((hg.get("bilder_tageszeit") or {}).get(z)) for z in TAGESZEITEN}
    stil = hg.get("stil", "natur") if hg.get("stil", "natur") in STILE else "natur"
    wechsel = hg.get("wechsel", "tageszeit") if hg.get("wechsel", "tageszeit") in WECHSEL else "tageszeit"
    diashow_min = max(1, min(120, int(hg.get("diashow_min", 10) or 10)))
    b = hg.get("bereich") or {}
    bw = max(4, min(SPALTEN, int(b.get("w", SPALTEN)))); bh = max(3, min(ZEILEN, int(b.get("h", ZEILEN))))
    bereich = {"x": max(0, min(SPALTEN - bw, int(b.get("x", 0)))), "y": max(0, min(ZEILEN - bh, int(b.get("y", 0)))), "w": bw, "h": bh}
    anpassung = hg.get("anpassung") if hg.get("anpassung") in ("fuellen", "einpassen", "strecken") else "fuellen"
    ausschnitt = hg.get("ausschnitt") if hg.get("ausschnitt") in ("mitte", "oben", "unten", "links", "rechts") else "mitte"
    th = l.get("thema", {}) or {}
    schema = th.get("schema", "dunkel")
    if schema not in ("dunkel", "hell", "gedimmt"):
        raise ValueError("Schema hell, dunkel oder gedimmt")
    schrift = th.get("schrift", "Roboto")
    if schrift not in SCHRIFTEN:
        raise ValueError("unbekannte Schrift")
    elemente, ids = [], set()
    for e in (l.get("elemente") or [])[:60]:
        typ = e.get("typ")
        if typ not in TYPEN:
            raise ValueError(f"unbekannter Baustein {typ!r}")
        eid = str(e.get("id", ""))
        if not re.fullmatch(r"[a-z0-9]{1,16}", eid) or eid in ids:
            raise ValueError(f"ungültige oder doppelte Baustein-Kennung {eid!r}")
        ids.add(eid)
        mw, mh = MINDEST.get(typ, (1, 1))
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
                         "optionen": optionen, "bedingung": _pruefe_bedingung(e.get("bedingung"))})
    return {"id": lid, "name": str(l.get("name", lid))[:40] or lid,
            "hintergrund": {"art": art, "farbe": _farbe(hg.get("farbe", "#202020")) or "#202020", "bild": bild,
                            "bilder_tageszeit": je_zeit, "stil": stil, "wechsel": wechsel, "diashow_min": diashow_min,
                            "nachts_dunkler": bool(hg.get("nachts_dunkler", True)), "abdunkeln": bool(hg.get("abdunkeln", True)),
                            "bereich": bereich, "anpassung": anpassung, "ausschnitt": ausschnitt},
            "thema": {"schema": schema, "akzent": _farbe(th.get("akzent", "#3d8cd0")) or "#3d8cd0", "schrift": schrift},
            "elemente": elemente}


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
            raise ValueError("Zeitplan: Uhrzeit als HH:MM")
        if ziel != "schwarz" and ziel not in layout_ids:
            raise ValueError(f"Zeitplan: unbekanntes Layout {ziel!r}")
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


def vorlagen():
    return [
        standard(),
        pruefe_layout({"id": "videogross", "name": "Video groß", "hintergrund": {"art": "farbe", "farbe": "#000000"},
                       "elemente": [_el("video", "video", 0, 0, 48, 27), _el("uhr", "uhr", 1, 1, 6, 2, karte=True),
                                    _el("temp", "temperatur", 1, 3, 6, 1, karte=True)]}),
        pruefe_layout({"id": "nurvideo", "name": "Nur Video", "hintergrund": {"art": "farbe", "farbe": "#000000"},
                       "elemente": [_el("video", "video", 0, 0, 48, 27, optionen={"leiste": False})]}),
        pruefe_layout({"id": "info", "name": "Info ohne Video", "hintergrund": {"art": "wetter", "abdunkeln": False},
                       "elemente": [_el("uhr", "uhr", 14, 4, 20, 7, ausrichtung="mitte"),
                                    _el("datum", "datum", 14, 11, 20, 2, ausrichtung="mitte"),
                                    _el("temp", "temperatur", 14, 14, 10, 3, ausrichtung="mitte"),
                                    _el("lage", "wetterlage", 24, 14, 10, 3, ausrichtung="mitte"),
                                    _el("vh", "vorhersage", 16, 19, 16, 5, karte=True),
                                    _el("sender", "sender", 14, 25, 20, 1, ausrichtung="mitte")]}),
        # Praxis: ruhig und hell für Wartezimmer einer Praxis – Logo, Uhr, Wetter, ruhiges Video ohne Leiste,
        # Willkommenstext. Für ruhige Tiere am Fernseher die Kategorien auf Meer, Vögel, Wald beschränken.
        pruefe_layout({"id": "praxis", "name": "Praxis – ruhig (Wartezimmer)",
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
                                        optionen={"text": "Herzlich willkommen – wir sind gleich für Sie da."})]}),
        # Firma: sachlich im eigenen Farbton – Kopfzeile mit Logo, Uhr, Datum; Video groß; Wetter rechts; Laufband unten
        pruefe_layout({"id": "firma", "name": "Firma – Corporate Design",
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
                                        optionen={"text": "Willkommen! Schön, dass Sie da sind."}),
                                    _el("band", "flaeche", 0, 24, 48, 3, optionen={"farbe": "#1f4e79", "deckkraft": 100}),
                                    _el("lauf", "text", 0, 24, 48, 3, textfarbe="#ffffff",
                                        optionen={"laufband": True, "text": "+++ Heute 14:00 Uhr: Teambesprechung im Saal A +++ "
                                                  "Kantine: Gemüselasagne +++ Wir begrüßen unsere Gäste +++"})]}),
        # Fenster zur Welt: Live-Video über den ganzen Bildschirm, oben links eine dunkle „Glas“-Tafel mit Uhr und Wetter,
        # oben mittig ein Meldungsbanner aus HA (erscheint erst, wenn eine Entität eingetragen ist)
        pruefe_layout({"id": "fenster", "name": "Fenster zur Welt",
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
        pruefe_layout({"id": "nacht", "name": "Nacht (nur Uhr, gedimmt)", "hintergrund": {"art": "farbe", "farbe": "#000000"},
                       "thema": {"schema": "gedimmt", "akzent": "#555555"},
                       "elemente": [_el("uhr", "uhr", 16, 10, 16, 6, ausrichtung="mitte")]}),
    ]
