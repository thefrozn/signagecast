# Speicherwächter (seit 0.45): Uploads und Vorrat-Downloads dürfen das Datenverzeichnis nie volllaufen lassen.
# Gemessen wird das Dateisystem von DATEN (Docker-Volume bzw. /var/lib/signagecast), nicht „/“. Eine feste Reserve von
# max(2 GB, 10 % der Platte) bleibt immer frei – für Stream-Puffer, Chromium, Protokolle und automatische Sicherungen.
#   grün: mehr als die doppelte Reserve frei · gelb: weniger (Hinweis, Uploads gehen noch) · rot: Reserve erreicht
#   (alle Uploads gesperrt, der Einspieler-Vorrat wächst nicht weiter; was schon da ist, läuft weiter).
import os, threading, time

from meldung import Meldung

RESERVE_MIN = 2 * 1024 ** 3
RESERVE_ANTEIL = 0.10
GB = 1024 ** 3

_belegung = {"zeit": 0, "werte": {}}
_sperre = threading.Lock()


def lage(pfad):
    """-> {"gesamt", "frei", "reserve", "nutzbar", "stufe"} in Bytes; nutzbar = was über der Reserve noch frei ist."""
    try:
        sv = os.statvfs(pfad)
    except OSError:
        sv = os.statvfs("/")
    gesamt = sv.f_blocks * sv.f_frsize
    frei = sv.f_bavail * sv.f_frsize
    reserve = max(RESERVE_MIN, int(gesamt * RESERVE_ANTEIL))
    reserve = min(reserve, gesamt // 2)              # winzige Platten (Tests, kleine Volumes): höchstens die Hälfte
    stufe = "gruen" if frei > 2 * reserve else "gelb" if frei > reserve else "rot"
    return {"gesamt": gesamt, "frei": frei, "reserve": reserve, "nutzbar": max(0, frei - reserve), "stufe": stufe}


def gb(n):
    return round(n / GB, 1)


def pruefen(pfad, bedarf):
    """Passt bedarf (Bytes) noch über die Reserve? Sonst Meldung „sp_voll“ (nichts wird geschrieben)."""
    l = lage(pfad)
    if l["frei"] - max(0, int(bedarf)) < l["reserve"]:
        raise Meldung("sp_voll", frei=gb(l["frei"]), reserve=gb(l["reserve"]), bedarf=max(0.1, gb(bedarf)))
    return l


def groesse(pfad):
    """Belegter Platz eines Ordners (oder einer Datei) in Bytes; fehlt er, 0."""
    if os.path.isfile(pfad):
        return os.path.getsize(pfad)
    summe = 0
    for wurzel, _, dateien in os.walk(pfad):
        for n in dateien:
            try:
                summe += os.lstat(os.path.join(wurzel, n)).st_size
            except OSError:
                pass
    return summe


def belegung(bereiche, max_alter=60):
    """{"galerie": pfad, …} -> {"galerie": bytes, …}; höchstens einmal pro max_alter Sekunden neu gezählt."""
    with _sperre:
        if time.time() - _belegung["zeit"] > max_alter or set(_belegung["werte"]) != set(bereiche):
            werte = {}
            for k, p in bereiche.items():
                werte[k] = sum(groesse(x) for x in (p if isinstance(p, (list, tuple)) else [p]))
            _belegung.update(zeit=time.time(), werte=werte)
        return dict(_belegung["werte"])


def neu_zaehlen():
    """Nach Upload/Löschen: beim nächsten Abruf neu zählen."""
    with _sperre:
        _belegung["zeit"] = 0
