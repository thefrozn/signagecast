# SignageCast – Offline-Kopie für Player im Direktmodus (seit 0.51).
# Der Server nennt dem Player alle Dateien, die sein Kanal ohne Server braucht: die TV-Seite mit Skripten, Schriften und
# Bildern, die Bilder seiner Layouts, Galerie- und PDF-Seiten und die eigenen Medien – je mit Größe und SHA-256. Der Player
# holt sie über seinen Anzeige-Zugang (wie die Seite selbst) und prüft die Summe. Livestreams, Kameras und Radio gehören
# nicht dazu. Reihenfolge („Rang“): Reicht der Platz nicht, fallen zuerst die eigenen Medien weg, die Seite nie.
# Nur Python-Standardbibliothek.
import hashlib, json, os, re, threading

RANG_SEITE, RANG_LAYOUT, RANG_GALERIE, RANG_MEDIEN = 0, 1, 2, 3
GRENZE_STANDARD_MB, GRENZE_MAX_MB = 512, 65536
NICHT = {"pult.html", "leistungstest.html"}           # gehören nicht zur TV-Seite
PFAD_OK = re.compile(r"/([A-Za-z0-9_\-][A-Za-z0-9_.\-]*/)*[A-Za-z0-9_\-][A-Za-z0-9_.\-]*")
_summen, _sperre = {}, threading.Lock()


def grenze_mb(wert):
    """Einstellung „Offline-Kopie höchstens … MB“: 0 = aus, sonst 32 MB bis 64 GB; Unsinn = Standard."""
    try:
        n = int(wert)
    except (TypeError, ValueError):
        return GRENZE_STANDARD_MB
    return 0 if n <= 0 else max(32, min(GRENZE_MAX_MB, n))


def summe(pfad):
    """(Größe, SHA-256) einer Datei – gemerkt, solange Änderungszeit und Größe gleich bleiben. None: nicht lesbar."""
    try:
        st = os.stat(pfad)
    except OSError:
        return None
    marke = (pfad, st.st_mtime_ns, st.st_size)
    with _sperre:
        if marke in _summen:
            return st.st_size, _summen[marke]
    h = hashlib.sha256()
    try:
        with open(pfad, "rb") as f:
            for teil in iter(lambda: f.read(1 << 20), b""):
                h.update(teil)
    except OSError:
        return None
    with _sperre:
        if len(_summen) > 20000:
            _summen.clear()
        _summen[marke] = h.hexdigest()
    return st.st_size, h.hexdigest()


def www_dateien(www):
    """Alle Dateien der TV-Seite: [(Adresse, Datei)]."""
    aus = []
    for ordner, unter, namen in os.walk(www):
        unter.sort()
        for n in sorted(namen):
            pfad = os.path.join(ordner, n)
            rel = os.path.relpath(pfad, www).replace(os.sep, "/")
            if rel in NICHT or n.endswith((".md", ".map")):
                continue
            aus.append(("/" + rel, pfad))
    return aus


def layouts_fuer(tv, layouts):
    """Alle Layouts, die dieser Kanal zeigen kann: Grundlayout, Zeitplan und Karussell."""
    ids = {tv.get("layout")} | {r.get("layout") for r in tv.get("zeitplan", [])} | set((tv.get("karussell") or {}).get("layouts", []))
    aus = [l for l in layouts if l["id"] in ids]
    return aus or layouts[:1]


def bild_namen(layouts):
    """Namen aller hochgeladenen Bilder (Logo, Hintergrund, je Tageszeit …), die in diesen Layouts vorkommen."""
    return sorted(set(m.group(1) for m in re.finditer(r'"([0-9a-f]{16}\.(?:jpg|png))"', json.dumps(layouts))))


def liste(eintraege):
    """[(Adresse, Datei, Rang)] -> [{"p", "g", "h", "r"}], ohne fehlende Dateien und Doppelte, sortiert nach Rang und Adresse."""
    aus, gesehen = [], set()
    for adresse, pfad, rang in eintraege:
        if adresse in gesehen or not PFAD_OK.fullmatch(adresse) or ".." in adresse:
            continue
        s = summe(pfad)
        if not s:
            continue
        gesehen.add(adresse)
        aus.append({"p": adresse, "g": s[0], "h": s[1], "r": int(rang)})
    aus.sort(key=lambda d: (d["r"], d["p"]))
    return aus


def stand(dateien, version, grenze):
    """Kurzer Fingerabdruck: ändert er sich, holt der Player die Liste neu."""
    roh = json.dumps([version, grenze, [(d["p"], d["h"]) for d in dateien]])
    return hashlib.sha256(roh.encode()).hexdigest()[:16]


def auswahl(dateien, grenze_bytes):
    """Was in die Grenze passt (nach Rang, kleine zuerst): (behalten, ausgelassen). Rang 0 bleibt immer."""
    behalten, weg, summe_b = [], [], 0
    for d in sorted(dateien, key=lambda d: (d["r"], d["g"], d["p"])):
        if d["r"] == RANG_SEITE or summe_b + d["g"] <= grenze_bytes:
            behalten.append(d)
            summe_b += d["g"]
        else:
            weg.append(d)
    return behalten, weg


def bericht(roh):
    """Meldung des Players säubern (für die Verwaltung): nur bekannte Felder, begrenzte Werte."""
    if not isinstance(roh, dict):
        return None
    zahl = lambda k: max(0, int(roh.get(k) or 0)) if isinstance(roh.get(k), (int, float)) and not isinstance(roh.get(k), bool) else 0
    return {"bereit": bool(roh.get("bereit")), "grund": str(roh.get("grund") or "")[:20], "stand": str(roh.get("stand") or "")[:16],
            "bytes": zahl("bytes"), "platz": zahl("platz"), "dateien": zahl("dateien"), "fehlt": zahl("fehlt"),
            "ausgelassen": zahl("ausgelassen"), "vollstaendig": bool(roh.get("vollstaendig")), "offline": bool(roh.get("offline")),
            "seit": zahl("seit"), "abgleich": zahl("abgleich")}
