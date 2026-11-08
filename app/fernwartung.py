# SignageCast – Fernwartung (seit 0.33): Terminal im Browser zu einem Raspberry-Pi-Player.
# Der Pi öffnet keinen Port: Er erfährt bei seiner Meldung (alle ≤ 15 s), dass eine Sitzung wartet, und spricht dann
# über zwei eigene, signierte Anfragen mit dem Server – /player/terminal/ein (lange Anfrage: wartet auf Eingaben) und
# /player/terminal/aus (Ausgabe). Die Verwaltung spricht über die lokale API (/api/player/<id>/terminal/…).
# Sicherungen:
# - Nur, wenn der Pi selbst Fernwartung erlaubt (signagecast.json auf der SD-Karte oder Einrichtungsseite) – wer den
#   Server übernimmt, kommt damit nicht auf Pis, die es nicht erlauben. Der Pi prüft das selbst, nicht der Server.
# - Inhalte verschlüsselt (Port 8890 ist HTTP): SHAKE-256 als Schlüsselstrom mit eigenem Schlüssel aus dem
#   Geräte-Schlüssel und zufälliger Nonce je Nachricht; die Signatur der Anfrage/Antwort schützt vor Veränderung.
#   Laufende Nummern je Richtung verhindern das Wiedereinspielen mitgeschnittener Anfragen.
# - Zeitgrenzen: 10 min ohne Eingabe, höchstens 60 min; Verwaltung 60 s nicht mehr da: Ende. Der Pi prüft das ebenso.
# - Protokoll jeder Sitzung (wer, wann, wie lange, warum beendet) – ohne Eingaben und Ausgaben.
import base64, hashlib, hmac, json, os, secrets, threading, time

from streams import DATEN
from meldung import Meldung as Fehler

LEER_S = 600                  # ohne Eingabe
MAX_S = 3600                  # insgesamt
VERWALTUNG_WEG_S = 60         # Browser fragt nicht mehr nach Ausgabe (Fenster zu, Netz weg)
PI_START_S = 45               # so lange darf der Pi brauchen, bis er sich meldet (Meldung alle ≤ 15 s)
PUFFER = 1 << 20              # Ausgabe, die der Browser noch nicht abgeholt hat (älteres fällt weg)
PROTOKOLL = os.path.join(DATEN, "fernwartung.json")
PROTOKOLL_MAX = 200

sperre = threading.Condition()
sitzungen = {}                # Geräte-ID -> Sitzung (höchstens eine je Pi)


def schluessel(g):
    """Eigener Schlüssel für die Verschlüsselung (nicht der Signatur-Schlüssel selbst)."""
    return hmac.new(bytes.fromhex(g["schluessel"]), b"fernwartung", "sha256").digest()


def _xor(k, nonce, roh):
    if not roh:
        return b""
    strom = hashlib.shake_256(k + nonce).digest(len(roh))
    return (int.from_bytes(roh, "big") ^ int.from_bytes(strom, "big")).to_bytes(len(roh), "big")


def verschluesseln(k, roh):
    nonce = secrets.token_bytes(16)
    return base64.b64encode(nonce + _xor(k, nonce, roh)).decode()


def entschluesseln(k, text):
    roh = base64.b64decode(text or "", validate=True)
    return _xor(k, roh[:16], roh[16:]) if len(roh) >= 16 else b""


def _protokoll_lesen():
    try:
        d = json.load(open(PROTOKOLL))
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def _protokoll(s):
    eintrag = {"geraet": s["gid"], "name": s["name"], "wer": s["wer"], "start": int(s["start"]), "ende": int(time.time()),
               "grund": s["grund"]}
    liste = ([eintrag] + _protokoll_lesen())[:PROTOKOLL_MAX]
    tmp = PROTOKOLL + ".tmp"
    with open(tmp, "w") as f:
        json.dump(liste, f, ensure_ascii=False)
    os.chmod(tmp, 0o600)
    os.replace(tmp, PROTOKOLL)
    print(f"Fernwartung {s['name']} ({s['gid']}): beendet ({s['grund']}) nach {eintrag['ende'] - eintrag['start']} s", flush=True)


def protokoll(gid=None, n=10):
    return [e for e in _protokoll_lesen() if gid is None or e["geraet"] == gid][:n]


def _schliessen(s, grund):
    """Mit gehaltener Sperre."""
    if s["zustand"] == "zu":
        return
    s["zustand"], s["grund"], s["geschlossen"] = "zu", grund, time.time()
    sperre.notify_all()
    try:
        _protokoll(s)
    except OSError as f:
        print("Fernwartung: Protokoll:", f, flush=True)


def _pruefen(jetzt):
    """Zeitgrenzen; mit gehaltener Sperre."""
    for gid, s in list(sitzungen.items()):
        if s["zustand"] == "zu":
            if jetzt - s["geschlossen"] > 120:
                del sitzungen[gid]
            continue
        if s["zustand"] == "wartet" and jetzt - s["start"] > PI_START_S:
            _schliessen(s, "pi_antwortet_nicht")
        elif jetzt - s["eingabe_zeit"] > LEER_S:
            _schliessen(s, "leerlauf")
        elif jetzt - s["start"] > MAX_S:
            _schliessen(s, "zeitgrenze")
        elif jetzt - s["verwaltung_zeit"] > VERWALTUNG_WEG_S:
            _schliessen(s, "verwaltung_weg")


def _sitzung(gid, sid):
    s = sitzungen.get(gid)
    return s if s and hmac.compare_digest(s["sid"], str(sid or "")) else None


# ---------- Verwaltung ----------
def starten(g, erlaubt, spalten, zeilen, wer):
    """Neue Sitzung (eine ältere zu diesem Pi endet). erlaubt: der Pi meldet, dass er Fernwartung zulässt."""
    if not erlaubt:
        raise Fehler("pi_fernwartung_aus")
    jetzt = time.time()
    with sperre:
        _pruefen(jetzt)
        alt = sitzungen.get(g["id"])
        if alt:
            _schliessen(alt, "neue_sitzung")
        s = {"gid": g["id"], "name": g["name"], "sid": secrets.token_hex(16), "wer": str(wer or "verwaltung")[:40],
             "start": jetzt, "eingabe_zeit": jetzt, "verwaltung_zeit": jetzt, "zustand": "wartet", "grund": "",
             "geschlossen": 0, "ein": bytearray(), "groesse": [_zahl(spalten, 80, 20, 400), _zahl(zeilen, 24, 5, 200)],
             "groesse_rev": 1, "aus": bytearray(), "aus_ende": 0, "n_ein": 0, "n_aus": 0}
        sitzungen[g["id"]] = s
        sperre.notify_all()
    print(f"Fernwartung {g['name']} ({g['id']}): Sitzung angefordert von {s['wer']}", flush=True)
    return s["sid"]


def _zahl(x, ersatz, mini, maxi):
    try:
        return max(mini, min(maxi, int(x)))
    except (TypeError, ValueError):
        return ersatz


def eingabe(gid, sid, text, spalten=None, zeilen=None):
    with sperre:
        s = _sitzung(gid, sid)
        if not s or s["zustand"] == "zu":
            return False
        jetzt = time.time()
        s["verwaltung_zeit"] = jetzt
        if text:
            roh = str(text).encode("utf-8", "replace")[:65536]
            if len(s["ein"]) + len(roh) <= 262144:      # niemand tippt so schnell – Einfügen großer Texte begrenzen
                s["ein"] += roh
            s["eingabe_zeit"] = jetzt
        if spalten and zeilen:
            neu = [_zahl(spalten, 80, 20, 400), _zahl(zeilen, 24, 5, 200)]
            if neu != s["groesse"]:
                s["groesse"], s["groesse_rev"] = neu, s["groesse_rev"] + 1
        sperre.notify_all()
        return True


def ausgabe(gid, sid, ab, warten=20.0):
    """Ausgabe ab Stelle `ab` (lange Anfrage). Antwort: {daten (Base64, unverschlüsselt – nur lokal), ab, zustand, grund}."""
    ende = time.time() + max(0.0, min(25.0, warten))
    with sperre:
        while True:
            s = _sitzung(gid, sid)
            if not s:
                return {"daten": "", "ab": 0, "zustand": "zu", "grund": "unbekannt"}
            s["verwaltung_zeit"] = time.time()
            try:
                ab = max(0, int(ab))
            except (TypeError, ValueError):
                ab = 0
            anfang = s["aus_ende"] - len(s["aus"])
            if ab < s["aus_ende"] or s["zustand"] == "zu" or time.time() >= ende:
                von = max(ab, anfang) - anfang
                return {"daten": base64.b64encode(bytes(s["aus"][von:])).decode(), "ab": s["aus_ende"],
                        "zustand": s["zustand"], "grund": s["grund"], "verloren": ab < anfang}
            sperre.wait(min(2.0, max(0.05, ende - time.time())))
            _pruefen(time.time())


def beenden(gid, sid, grund="verwaltung"):
    with sperre:
        s = _sitzung(gid, sid)
        if s:
            _schliessen(s, grund)
        return bool(s)


def entfernen(gid):
    """Gerät gelöscht: laufende Sitzung beenden."""
    with sperre:
        s = sitzungen.get(gid)
        if s:
            _schliessen(s, "geraet_entfernt")


def zustand(gid):
    """Für die Geräteliste: offene Sitzung (ohne Kennung)."""
    with sperre:
        _pruefen(time.time())
        s = sitzungen.get(gid)
        return {"zustand": s["zustand"], "start": int(s["start"]), "wer": s["wer"]} if s and s["zustand"] != "zu" else None


# ---------- Pi ----------
def fuer_meldung(g):
    """Teil der Antwort auf /player/melden: wartende oder laufende Sitzung."""
    with sperre:
        _pruefen(time.time())
        s = sitzungen.get(g["id"])
        if not s or s["zustand"] == "zu":
            return None
        return {"sid": s["sid"], "spalten": s["groesse"][0], "zeilen": s["groesse"][1]}


def _nummer_ok(s, art, n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return False
    if n <= s[art]:
        return False
    s[art] = n
    return True


def pi_ein(g, d, warten=15.0):
    """Lange Anfrage des Pi: wartet auf Eingaben, Größenänderung oder Ende. Antwort verschlüsselt."""
    k = schluessel(g)
    ende = time.time() + warten
    with sperre:
        s = _sitzung(g["id"], d.get("sid"))
        if not s or not _nummer_ok(s, "n_ein", d.get("n")):
            return {"offen": False}
        if s["zustand"] == "wartet":
            s["zustand"] = "offen"
            print(f"Fernwartung {s['name']} ({s['gid']}): Pi verbunden", flush=True)
        groesse_rev = int(d.get("groesse_rev") or 0)
        while True:
            _pruefen(time.time())
            if s["zustand"] == "zu":
                return {"offen": False, "grund": s["grund"]}
            if s["ein"] or s["groesse_rev"] != groesse_rev or time.time() >= ende:
                roh, s["ein"] = bytes(s["ein"]), bytearray()
                return {"offen": True, "daten": verschluesseln(k, roh) if roh else "", "spalten": s["groesse"][0],
                        "zeilen": s["groesse"][1], "groesse_rev": s["groesse_rev"]}
            sperre.wait(min(2.0, max(0.05, ende - time.time())))


def pi_aus(g, d):
    """Ausgabe vom Pi (verschlüsselt); d["ende"]: die Shell ist beendet oder der Pi hat abgebrochen."""
    k = schluessel(g)
    with sperre:
        s = _sitzung(g["id"], d.get("sid"))
        if not s or not _nummer_ok(s, "n_aus", d.get("n")):
            return {"offen": False}
        try:
            roh = entschluesseln(k, d.get("daten"))
        except ValueError:
            return {"offen": s["zustand"] != "zu"}
        if roh and s["zustand"] != "zu":
            if s["zustand"] == "wartet":
                s["zustand"] = "offen"
            s["aus"] += roh
            s["aus_ende"] += len(roh)
            if len(s["aus"]) > PUFFER:
                del s["aus"][:len(s["aus"]) - PUFFER]
        if d.get("ende"):
            _schliessen(s, "pi_" + str(d.get("ende"))[:30])
        sperre.notify_all()
        return {"offen": s["zustand"] != "zu"}
