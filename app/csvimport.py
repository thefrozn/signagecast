# CSV-Import (seit 0.26), allgemein gehalten: Er ist nicht an die Datenquellen gebunden, damit andere Stellen ihn
# wiederverwenden können (z. B. Medienlisten, Fernseher, Termine). Ablauf:
#   1. analysieren(roh, optionen)  -> Trennzeichen/Anführungszeichen/Kopfzeile/Zeichensatz erkennen (was nicht vorgegeben
#                                     ist), Spalten mit Beispielwerten und eine Vorschau liefern
#   2. Die Verwaltung lässt wählen, welche Spalten übernommen werden und wie sie heißen (optionen["felder"])
#   3. lesen(roh, optionen)        -> Liste von Zeilen als {Feldname: Wert}
# Dazu Hilfen für Datum/Uhrzeit in freier Schreibweise („Mi 07.01.2026“, „2026-01-07 18:30“). Nur Standardbibliothek.
import csv, datetime, io, re
from meldung import Meldung

TRENNER = {",": ",", ";": ";", "tab": "\t", "|": "|", " ": " "}          # Kennung -> Zeichen
ANFUEHRUNG = {'"': '"', "'": "'", "": None}                                # "" = ohne Anführungszeichen
KODIERUNGEN = ("auto", "utf-8", "cp1252", "latin-1")
MAX_SPALTEN, MAX_ZEILEN, MAX_FELD = 100, 5000, 2000


def dekodieren(roh, kodierung="auto"):
    """Bytes -> (Text, benutzte Kodierung). auto: UTF-8 (mit/ohne BOM), sonst Windows-1252 (Excel unter Windows)."""
    if isinstance(roh, str):
        return roh, "utf-8"
    if kodierung == "auto":
        try:
            return roh.decode("utf-8-sig"), "utf-8"
        except UnicodeDecodeError:
            return roh.decode("cp1252", errors="replace"), "cp1252"
    if kodierung not in KODIERUNGEN:
        raise Meldung("csv_kodierung")
    return roh.decode("utf-8-sig" if kodierung == "utf-8" else kodierung, errors="replace"), kodierung


def erkennen(text):
    """Trennzeichen, Anführungszeichen und Kopfzeile schätzen (Kennungen wie in TRENNER/ANFUEHRUNG)."""
    zeilen = [z for z in text.splitlines()[:50] if z.strip()]
    probe = "\n".join(zeilen)
    # Trennzeichen: das Zeichen, das (ohne Text in Anführungszeichen) in den meisten Zeilen gleich oft vorkommt
    ohne = [re.sub(r'"[^"]*"', "", z) for z in zeilen]
    beste, trenner = (0, 0), ","
    for t in ",;\t|":
        anz = [z.count(t) for z in ohne]
        haeufig = max(set(anz), key=anz.count) if anz else 0
        if haeufig:
            wert = (round(anz.count(haeufig) / len(anz), 1), haeufig)
            if wert > beste:
                beste, trenner = wert, t
    anfuehrung = '"' if '"' in probe else ("'" if re.search(r"(^|[,;\t|])'", probe, re.M) else '"')
    kopfzeile = True
    try:
        kopfzeile = csv.Sniffer().has_header(probe) if len(zeilen) > 1 else True
    except csv.Error:
        pass
    if zeilen and not kopfzeile:          # Sniffer irrt bei reinen Textspalten: Kopf ohne Ziffern, darunter mit -> Kopfzeile
        erste = zeilen[0]
        if not re.search(r"\d", erste) and any(re.search(r"\d", z) for z in zeilen[1:]):
            kopfzeile = True
    kennung = next(k for k, v in TRENNER.items() if v == trenner) if trenner in TRENNER.values() else ","
    return {"trenner": kennung, "anfuehrung": anfuehrung, "kopfzeile": kopfzeile}


def optionen_pruefen(o, felder_pflicht=False):
    """Optionen vereinheitlichen. felder: [{spalte: Nummer ab 0, name}] – leer = alle Spalten unter ihrem Namen."""
    o = o if isinstance(o, dict) else {}
    trenner = o.get("trenner", ",")
    if trenner not in TRENNER:
        raise Meldung("csv_trenner")
    anf = o.get("anfuehrung", '"')
    if anf not in ANFUEHRUNG:
        raise Meldung("csv_anfuehrung")
    kod = o.get("kodierung", "auto")
    if kod not in KODIERUNGEN:
        raise Meldung("csv_kodierung")
    felder, namen = [], set()
    for f in (o.get("felder") or [])[:MAX_SPALTEN]:
        try:
            spalte = int(f.get("spalte"))
        except (TypeError, ValueError, AttributeError):
            raise Meldung("csv_spalte")
        name = str(f.get("name", "")).strip()[:60]
        if not 0 <= spalte < MAX_SPALTEN or not name or name in namen:
            raise Meldung("csv_feldname", name=repr(name))
        namen.add(name)
        felder.append({"spalte": spalte, "name": name})
    if felder_pflicht and not felder:
        raise Meldung("csv_keine_felder")
    return {"trenner": trenner, "anfuehrung": anf, "kopfzeile": bool(o.get("kopfzeile", True)), "kodierung": kod, "felder": felder}


def _zeilen(text, o):
    anf = ANFUEHRUNG[o["anfuehrung"]]
    leser = csv.reader(io.StringIO(text), delimiter=TRENNER[o["trenner"]], skipinitialspace=o["trenner"] != " ",
                       **({"quotechar": anf, "doublequote": True} if anf else {"quoting": csv.QUOTE_NONE}))
    aus = []
    try:
        for z in leser:
            if not any(x.strip() for x in z):
                continue                  # Leerzeilen überspringen
            aus.append([x.strip()[:MAX_FELD] for x in z[:MAX_SPALTEN]])
            if len(aus) > MAX_ZEILEN:
                break
    except csv.Error as ex:
        raise Meldung("csv_kaputt", d=ex)
    return aus


def _kopf(zeilen, o):
    """Spaltennamen: aus der Kopfzeile (doppelte/leere bekommen eine Nummer) oder „Spalte 1“, „Spalte 2“ …"""
    breite = max((len(z) for z in zeilen), default=0)
    roh = zeilen[0] if o["kopfzeile"] and zeilen else []
    namen, gesehen = [], set()
    for i in range(breite):
        n = (roh[i] if i < len(roh) else "").strip() or f"Spalte {i + 1}"
        if n in gesehen:
            n = f"{n} ({i + 1})"
        gesehen.add(n)
        namen.append(n[:60])
    return namen, (zeilen[1:] if o["kopfzeile"] else zeilen)


def analysieren(roh, optionen=None):
    """Für die Auswahl in der Verwaltung: {optionen, kodierung, spalten: [{nr, name, beispiele}], zeilen, vorschau}.
    Nicht vorgegebene Optionen werden erkannt; die Antwort enthält die tatsächlich benutzten."""
    vorgabe = optionen if isinstance(optionen, dict) else {}
    text, kod = dekodieren(roh, vorgabe.get("kodierung", "auto"))
    geschaetzt = erkennen(text)
    o = optionen_pruefen(dict(geschaetzt, **{k: v for k, v in vorgabe.items() if v not in (None, "auto") and k != "felder"},
                              felder=vorgabe.get("felder") or []))
    zeilen = _zeilen(text, o)
    if not zeilen:
        raise Meldung("csv_leer")
    namen, daten = _kopf(zeilen, o)
    spalten = [{"nr": i, "name": n, "beispiele": [z[i] for z in daten if i < len(z) and z[i]][:3]} for i, n in enumerate(namen)]
    return {"optionen": o, "erkannt": geschaetzt, "kodierung": kod, "spalten": spalten, "zeilen": len(daten),
            "abgeschnitten": len(zeilen) > MAX_ZEILEN, "vorschau": daten[:5]}


def lesen(roh, optionen):
    """Zeilen als Liste von {Feldname: Wert} – nur die gewählten Felder (ohne Auswahl: alle Spalten)."""
    o = optionen_pruefen(optionen)
    text, _ = dekodieren(roh, o["kodierung"])
    zeilen = _zeilen(text, o)
    namen, daten = _kopf(zeilen, o)
    felder = o["felder"] or [{"spalte": i, "name": n} for i, n in enumerate(namen)]
    return [{f["name"]: (z[f["spalte"]] if f["spalte"] < len(z) else "") for f in felder} for z in daten[:MAX_ZEILEN]]


# ---------- Datum und Uhrzeit in freier Schreibweise ----------
_DATUM = [
    (re.compile(r"(?<!\d)(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)"), ("j", "m", "t")),          # 2026-01-07
    (re.compile(r"(?<!\d)(\d{1,2})\.(\d{1,2})\.(\d{4}|\d{2})(?!\d)"), ("t", "m", "j")),  # 07.01.2026, 7.1.26
    (re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{4})(?!\d)"), ("t", "m", "j")),          # 07/01/2026 (Tag zuerst)
]
_ZEIT = re.compile(r"(?<![\d.])([01]?\d|2[0-3])[:.]([0-5]\d)(?:[:.][0-5]\d)?(?![\d.])")


def datum_finden(s):
    """Erstes Datum in einem Text -> datetime.date oder None (Wochentage und anderer Text drumherum stören nicht)."""
    for muster, reihe in _DATUM:
        m = muster.search(str(s or ""))
        if m:
            w = dict(zip(reihe, (int(x) for x in m.groups())))
            if w["j"] < 100:
                w["j"] += 2000
            try:
                return datetime.date(w["j"], w["m"], w["t"])
            except ValueError:
                return None
    return None


def zeit_finden(s):
    """Uhrzeit (hh:mm) in einem Text -> datetime.time oder None; ein Datum davor wird übersprungen."""
    s = str(s or "")
    for muster, _ in _DATUM:
        s = muster.sub(" ", s)
    m = _ZEIT.search(s)
    return datetime.time(int(m.group(1)), int(m.group(2))) if m else None
