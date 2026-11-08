# SignageCast – Raspberry-Pi-Player (seit 0.23). Die Pis sind reine Abspielgeräte: Sie zeigen den fertigen Stream eines
# Fernsehers per HDMI und melden sich alle paar Sekunden über den Webhook-Port (8890) – dabei holen sie Einstellungen und
# Befehle ab (Pull, am Pi ist kein Port offen). Jede Anfrage und jede Antwort ist mit dem Schlüssel des Geräts signiert
# (HMAC-SHA256); der Schlüssel steht nur in der Gerätedatei auf der SD-Karte und hier.
# Direktmodus (seit 0.24): Statt des Streams zeigt der Pi die TV-Seite selbst (Chromium im Kiosk-Rahmen cage). Der Pi
# öffnet dazu /anzeige/<Schlüssel> auf dem Webhook-Port; der Schlüssel ist aus dem Geräte-Schlüssel abgeleitet und gilt
# nur für die Seite seines eigenen Fernsehers (Weiterleitung an den Datendienst, ohne /api/).
# Image je Gerät: ein Grundimage (GitHub-Release, signiert) wird einmal geladen; beim Herunterladen schreibt die
# Verwaltung die Gerätedatei in den Platzhalter auf der Boot-Partition (bekannter Versatz) und packt neu – ohne mounten.
# Kopplung (seit 0.25): Ein Image für mehrere Pis enthält Server und WLAN, aber keinen Schlüssel. Der Pi handelt ihn mit
# dem Server per Diffie-Hellman aus und zeigt einen daraus abgeleiteten 6-stelligen Code; erst die Eingabe dieses Codes
# in der Verwaltung macht aus der Anfrage ein Gerät. Wer sich im Netz dazwischenschiebt, hätte einen anderen Code.
# PC-Player (seit 0.36, experimentell): derselbe Agent auf x86-64-Geräten mit UEFI – eigenes Grundimage (ISO, auch für
# USB-Sticks), Modell „pc“, Direktmodus als Standard. Browser-Gerät (seit 0.36): kein Agent, nur ein geheimer Link
# /anzeige/<Schlüssel> für eine beliebige Kiosk-Live-CD oder einen Browser im Vollbild; online = die Seite ruft Daten ab.
import hashlib, hmac, json, lzma, os, re, secrets, shutil, subprocess, threading, time, urllib.request, zlib

from streams import DATEN
from meldung import Meldung as Fehler
import fernwartung as FW

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT = os.path.join(BASIS, "player", "agent.py")
DATEI = os.path.join(DATEN, "player.json")
ORDNER = os.path.join(DATEN, "player")
GRUND = os.path.join(ORDNER, "basis")
GRUND_PC = os.path.join(ORDNER, "basis-pc")            # PC-Player (seit 0.36)
ARTEN = {"pi": {"name": "signagecast-player-v", "endung": ".img.xz", "art": "signagecast-player-image"},
         "pc": {"name": "signagecast-pc-v", "endung": ".iso.xz", "art": "signagecast-pc-image"}}


def ordner(art):
    """Ordner des Grundimages (zur Laufzeit gelesen – die Tests biegen GRUND/GRUND_PC um)."""
    return GRUND_PC if art == "pc" else GRUND
PROJEKT = "thefrozn/signagecast"
QUELLE = os.environ.get("SC_PLAYER_QUELLE", "")       # Ordner mit Grundimage (Test vor dem Release), sonst GitHub
# Öffentlicher Schlüssel der Releases (wie werkzeug/aktualisieren.sh; release.sh prüft, dass beide gleich sind)
SCHLUESSEL = "RWS+1ozfjYuftY7DYt4RjDJLsJKenGkFL7prSxRjeDuk3c+++cclZqgD"
PLATZ = 16384                                          # Länge des Platzhalters signagecast.json im Image
MODELLE = ("pi45", "pi3", "pc")                        # Pi 5/4/400/CM4 | Pi 3/Zero 2 W (nur H.264 bis Full HD) | PC (seit 0.36)
BROWSER = "browser"                                    # Browser-Gerät (seit 0.36): nur Link, kein Agent
AUFLOESUNGEN = ("auto", "720", "1080", "2160")
ANZEIGE_MODI = ("stream", "direkt")                    # Direktmodus nur Pi 4/5 und PC (Pi 3/Zero 2 W: zu wenig Speicher)
BEFEHLE = ("neustart", "player_neu", "bild", "protokoll", "cec_an", "cec_aus", "erkennen", "systemupdate")
ONLINE_S = 60
LAENDER = {"Europe/Berlin": "DE", "Europe/Vienna": "AT", "Europe/Zurich": "CH", "Europe/Amsterdam": "NL", "Europe/Brussels": "BE",
           "Europe/Luxembourg": "LU", "Europe/Paris": "FR", "Europe/London": "GB", "Europe/Dublin": "IE", "Europe/Rome": "IT",
           "Europe/Madrid": "ES", "Europe/Lisbon": "PT", "Europe/Copenhagen": "DK", "Europe/Stockholm": "SE", "Europe/Oslo": "NO",
           "Europe/Helsinki": "FI", "Europe/Warsaw": "PL", "Europe/Prague": "CZ", "Europe/Budapest": "HU", "Australia/Sydney": "AU"}

sperre = threading.Lock()
stand = {}            # id -> {"zeit", "bericht", "ip"} (letzte Meldung, nur im Speicher)
befehle = {}          # id -> [{"id", "art", "zeit"}] noch nicht abgeholt
ergebnisse = {}       # id -> [{"art", "ok", "hinweis", "zeit"}] (die letzten 10)
einmal = {}           # Download-Kennung -> {"id" ("" = Image für mehrere Pis), "netze", "server", "bis"}
kopplungen = {}       # Anfrage-Kennung -> {"code", "schluessel", "bis", "ip", "modell", "geraet"} (nur im Speicher)
koppel_zeiten = []    # Zeitpunkte neuer Kopplungsanfragen der letzten Stunde (Grenze gegen Durchprobieren)
direkt_abruf = {}     # id -> Zeit des letzten Abrufs von daten.json im Direktmodus (zeigt: die Seite lebt)
kameras_erlaubt = {}  # TV-Kennung -> {"cam_<id>", …} aus der letzten daten.json (nur diese Kamera-Streams gibt der Zugang frei)
basis_stand = {a: {"phase": "", "geladen": 0, "gesamt": 0, "fehler": "", "code": "", "p": {}, "version": ""} for a in ARTEN}


# Diffie-Hellman für die Kopplung: RFC 3526, 2048-Bit-Gruppe 14, Erzeuger 2 (wie im Agent; nur Standardbibliothek)
DH_P = int("FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DD"
           "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F2411"
           "7C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D"
           "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497C"
           "EA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF", 16)
KOPPEL_S = 600                                         # so lange gilt ein Code; danach fragt der Pi neu
KOPPEL_OFFEN = 20                                      # höchstens so viele offene Anfragen
KOPPEL_STUNDE = 60                                     # höchstens so viele neue Anfragen je Stunde


def dh_ableiten(geheim, fremd, a_pub, b_pub):
    """(Code, Geräte-Schlüssel) aus dem gemeinsamen DH-Wert – Pi und Server rechnen dasselbe."""
    s = pow(fremd, geheim, DH_P)
    k = hashlib.sha256(b"signagecast-kopplung\n" + b"\n".join(format(x, "x").encode() for x in (s, a_pub, b_pub))).digest()
    code = int.from_bytes(hmac.new(k, b"code", "sha256").digest()[:8], "big") % 1_000_000
    return f"{code:06d}", hmac.new(k, b"geraet", "sha256").hexdigest()


def _leer():
    return {"geraete": [], "wlan": [], "server": "", "stream_port": 0, "entfernt": []}


def laden():
    try:
        with open(DATEI) as f:
            d = json.load(f)
        return dict(_leer(), **d) if isinstance(d, dict) else _leer()
    except (OSError, ValueError):
        return _leer()


def speichern(d):
    os.makedirs(os.path.dirname(DATEI), exist_ok=True)
    tmp = DATEI + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, DATEI)


daten = laden()


def geraet(gid):
    return next((g for g in daten["geraete"] if g["id"] == gid), None)


def psk(ssid, passwort):
    """WPA2-Schlüssel (64 hex) aus Name und Passwort – auf der Karte und hier steht nie das Passwort selbst."""
    if not 1 <= len(ssid.encode()) <= 32:
        raise Fehler("pi_ssid")
    if not 8 <= len(passwort) <= 63:
        raise Fehler("pi_wlan_pw")
    return hashlib.pbkdf2_hmac("sha1", passwort.encode(), ssid.encode(), 4096, 32).hex()


def wlan_aus_anfrage(w):
    """{"ssid", "passwort", "speichern"} oder {"gespeichert": ssid} -> (Netz, speichern?) bzw. (None, False) für Kabel."""
    if not w:
        return None, False
    if w.get("gespeichert"):
        n = next((n for n in daten["wlan"] if n["ssid"] == w["gespeichert"]), None)
        if not n:
            raise Fehler("pi_wlan_unbekannt")
        return dict(n), False
    ssid = str(w.get("ssid", "")).strip()
    return {"ssid": ssid, "psk": psk(ssid, str(w.get("passwort", "")))}, bool(w.get("speichern"))


def wlan_merken(netz):
    with sperre:
        daten["wlan"] = [netz] + [n for n in daten["wlan"] if n["ssid"] != netz["ssid"]][:9]
        speichern(daten)


def _felder(g, d, tvs):
    """Einstellbare Felder eines Geräts prüfen und übernehmen."""
    if "name" in d:
        name = str(d["name"]).strip()[:40]
        if not name:
            raise Fehler("pi_name")
        g["name"] = name
    if "tv" in d:
        if d["tv"] and d["tv"] not in tvs:
            raise Fehler("pi_tv")
        g["tv"] = d["tv"] or ""
    if d.get("modell") in MODELLE and g.get("modell") != BROWSER:     # ein Browser-Gerät bleibt eines (kein Agent)
        g["modell"] = d["modell"]
    if d.get("aufloesung") in AUFLOESUNGEN:
        g["aufloesung"] = d["aufloesung"]
    if d.get("drehung") in (0, 90, 180, 270):
        g["drehung"] = d["drehung"]
    if "lautstaerke" in d:
        try:
            g["lautstaerke"] = max(0, min(100, int(d["lautstaerke"])))
        except (TypeError, ValueError):
            raise Fehler("pi_lautstaerke") from None
    for k in ("cec_zeitplan", "schreibschutz"):
        if k in d:
            g[k] = bool(d[k])
    if d.get("systemupdate") in ("woechentlich", "aus"):
        g["systemupdate"] = d["systemupdate"]
    if d.get("hwdec") in ("auto", "aus"):
        g["hwdec"] = d["hwdec"]
    if d.get("anzeige_modus") in ANZEIGE_MODI:
        g["anzeige_modus"] = d["anzeige_modus"]
    if g.get("modell") == "pi3":
        g["anzeige_modus"] = "stream"
    if g.get("modell") == BROWSER:
        g["anzeige_modus"] = "direkt"


def neu(d, tvs, schluessel=None):
    """Neues Gerät anlegen. Gibt das Gerät zurück; das Image dazu kommt über herunterladen_vorbereiten() – oder der
    Schlüssel aus einer Kopplung."""
    g = {"id": secrets.token_hex(4), "schluessel": schluessel or secrets.token_hex(32), "erstellt": time.strftime("%Y-%m-%d %H:%M"),
         "name": "", "tv": "", "modell": "pi45", "aufloesung": "auto", "drehung": 0, "lautstaerke": 100, "cec_zeitplan": False,
         "schreibschutz": True, "systemupdate": "woechentlich", "hwdec": "auto", "anzeige_modus": "stream", "wlan_rev": 0, "wlan_soll": None,
         "hotspot_pw": "".join(secrets.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(10))}
    if d.get("modell") == BROWSER:                     # seit 0.36: Gerät ohne Agent, nur Link
        g["modell"] = BROWSER
    elif d.get("modell") == "pc" and "anzeige_modus" not in d:
        g["anzeige_modus"] = "direkt"                  # PC: Direktmodus als Standard (genug Speicher, VAAPI)
    _felder(g, dict({"name": d.get("name", "")}, **d), tvs)
    with sperre:
        daten["geraete"].append(g)
        speichern(daten)
    return g


def aendern(gid, d, tvs):
    with sperre:
        g = geraet(gid)
        if not g:
            raise Fehler("pi_unbekannt")
        _felder(g, d, tvs)
        speichern(daten)
    return g


def entfernen(gid):
    """Gerät löschen: Sein Schlüssel gilt nicht mehr; der Pi zeigt „in der Verwaltung entfernt“."""
    with sperre:
        daten["geraete"] = [g for g in daten["geraete"] if g["id"] != gid]
        daten["entfernt"] = ([gid] + daten["entfernt"])[:100]
        speichern(daten)
    stand.pop(gid, None)
    befehle.pop(gid, None)
    direkt_abruf.pop(gid, None)
    FW.entfernen(gid)
    for endung in (".jpg", ".log"):
        try:
            os.unlink(os.path.join(ORDNER, gid + endung))
        except OSError:
            pass


def link_neu(gid):
    """Browser-Gerät: neuen Schlüssel – der alte Link gilt sofort nicht mehr."""
    with sperre:
        g = geraet(gid)
        if not g or g.get("modell") != BROWSER:
            raise Fehler("pi_unbekannt")
        g["schluessel"] = secrets.token_hex(32)
        speichern(daten)
    direkt_abruf.pop(gid, None)


def befehl(gid, art):
    if art not in BEFEHLE:
        raise Fehler("pi_befehl")
    g = geraet(gid)
    if not g:
        raise Fehler("pi_unbekannt")
    if g.get("modell") == BROWSER:
        raise Fehler("pi_browser_befehl")
    with sperre:
        liste = [b for b in befehle.get(gid, []) if b["art"] != art]
        befehle[gid] = liste + [{"id": secrets.token_hex(4), "art": art, "zeit": time.time()}]


def wlan_wechseln(gid, w):
    """Neues WLAN an den Pi schicken. Er probiert es aus und kehrt zum alten zurück, wenn er den Server damit nicht erreicht."""
    netz, merken = wlan_aus_anfrage(w)
    if not netz:
        raise Fehler("pi_ssid")
    if merken:
        wlan_merken(netz)
    with sperre:
        g = geraet(gid)
        if not g:
            raise Fehler("pi_unbekannt")
        g["wlan_rev"] = int(g.get("wlan_rev", 0)) + 1
        g["wlan_soll"] = {"rev": g["wlan_rev"], "netze": [netz], "seit": time.strftime("%Y-%m-%d %H:%M")}
        speichern(daten)


def wlan_vergessen(ssid):
    with sperre:
        daten["wlan"] = [n for n in daten["wlan"] if n["ssid"] != ssid]
        speichern(daten)


def einstellen(d):
    """Server-Adresse und Stream-Port, die die Pis nutzen sollen (leer = automatisch)."""
    with sperre:
        if "server" in d:
            s = str(d["server"]).strip().rstrip("/")
            if s and not re.fullmatch(r"https?://[A-Za-z0-9.\-\[\]:]+", s):
                raise Fehler("pi_server")
            daten["server"] = s
        if "stream_port" in d:
            try:
                p = int(d["stream_port"] or 0)
            except (TypeError, ValueError):
                raise Fehler("pi_port") from None
            if p and not 1 <= p <= 65535:
                raise Fehler("pi_port")
            daten["stream_port"] = p
        speichern(daten)


# ---------- Kopplung (seit 0.25) ----------
def _koppel_aufraeumen(jetzt):
    for k in [k for k, v in kopplungen.items() if v["bis"] < jetzt]:
        del kopplungen[k]
    koppel_zeiten[:] = [z for z in koppel_zeiten if z > jetzt - 3600]


def koppel_anfrage(d, ip):
    """Pi ohne Schlüssel meldet sich mit seinem DH-Wert; Antwort: eigener DH-Wert und Kennung zum Nachfragen."""
    try:
        a_pub = int(str(d.get("a", "")), 16)
    except ValueError:
        raise Fehler("pi_koppel_ungueltig") from None
    if not 2 <= a_pub <= DH_P - 2 or pow(a_pub, (DH_P - 1) // 2, DH_P) != 1:     # nur Werte aus der Untergruppe
        raise Fehler("pi_koppel_ungueltig")
    jetzt = time.time()
    with sperre:
        _koppel_aufraeumen(jetzt)
        for k in [k for k, v in kopplungen.items() if v["ip"] == ip and not v["geraet"]]:
            del kopplungen[k]                     # derselbe Pi fragt neu (Neustart, Code abgelaufen): alte Anfrage weg
        if len(kopplungen) >= KOPPEL_OFFEN or len(koppel_zeiten) >= KOPPEL_STUNDE:
            raise Fehler("pi_koppel_voll")
        koppel_zeiten.append(jetzt)
    b = secrets.randbits(320)
    b_pub = pow(2, b, DH_P)
    code, schluessel = dh_ableiten(b, a_pub, a_pub, b_pub)
    kennung = secrets.token_hex(16)
    with sperre:
        kopplungen[kennung] = {"code": code, "schluessel": schluessel, "bis": jetzt + KOPPEL_S, "ip": ip, "geraet": "",
                               "modell": str(d.get("modell", ""))[:80], "zeit": jetzt,
                               "plattform": "pc" if d.get("plattform") == "pc" else "pi"}
    return {"kennung": kennung, "b": format(b_pub, "x"), "gueltig": KOPPEL_S}


def koppel_status(kennung):
    """(HTTP-Code, Antwort, Gerät): 202 = Code noch nicht eingegeben, 404 = abgelaufen, 200 = gekoppelt (signiert)."""
    with sperre:
        _koppel_aufraeumen(time.time())
        e = kopplungen.get(kennung)
        g = geraet(e["geraet"]) if e and e["geraet"] else None
    if not e:
        return 404, {"ok": False}, None
    if not g:
        return 202, {"ok": True, "warten": True}, None
    return 200, {"ok": True, "id": g["id"], "name": g["name"], "hostname": hostname(g)}, g


def koppeln(code, d, tvs):
    """Code aus der Verwaltung: passende Anfrage suchen und daraus ein Gerät machen."""
    code = re.sub(r"\D", "", str(code or ""))
    with sperre:
        _koppel_aufraeumen(time.time())
        e = next((v for v in kopplungen.values() if len(code) == 6 and hmac.compare_digest(v["code"], code) and not v["geraet"]), None)
    if not e:
        raise Fehler("pi_code")
    modell = "pc" if e.get("plattform") == "pc" else "pi3" if re.search(r"Pi 3|Zero 2", e["modell"]) else "pi45"
    g = neu(dict(d, modell=modell), tvs, schluessel=e["schluessel"])
    with sperre:
        e["geraet"], e["bis"] = g["id"], time.time() + KOPPEL_S       # der Pi holt das Ergebnis in den nächsten Sekunden ab
    return g


def wartend():
    """Pis, die gerade einen Code zeigen (für die Verwaltung: Modell, IP und Zeit – nie der Code)."""
    with sperre:
        _koppel_aufraeumen(time.time())
        return [{"modell": v["modell"], "ip": v["ip"], "seit": int(v["zeit"])} for v in kopplungen.values() if not v["geraet"]]


# ---------- Anfragen der Player ----------
def pruefen(kopf, pfad, koerper):
    """(Gerät, Fehlercode, Zeit) einer Anfrage: Signatur über Methode, Pfad, Zeit und Inhalt; Zeit ±5 min."""
    gid, zeit, sig = kopf.get("X-Geraet", ""), kopf.get("X-Zeit", ""), kopf.get("X-Signatur", "")
    g = geraet(gid)
    if not g:
        return None, 410 if gid in daten["entfernt"] else 404, zeit
    if not zeit.isdigit() or abs(int(zeit) - time.time()) > 300:
        return None, 401, zeit
    soll = hmac.new(bytes.fromhex(g["schluessel"]), f"POST\n{pfad}\n{zeit}\n".encode() + koerper, "sha256").hexdigest()
    if not hmac.compare_digest(soll, sig):
        return None, 403, zeit
    return g, 200, zeit


def signatur(g, zeit, inhalt):
    return hmac.new(bytes.fromhex(g["schluessel"]), f"antwort\n{zeit}\n".encode() + inhalt, "sha256").hexdigest()


def anzeige_schluessel(g):
    """Schlüssel für den Direktmodus: aus dem Geräte-Schlüssel abgeleitet (der Pi rechnet ihn selbst aus)."""
    return hmac.new(bytes.fromhex(g["schluessel"]), b"anzeige", "sha256").hexdigest()[:32]


def geraet_fuer_anzeige(schluessel):
    if not re.fullmatch(r"[0-9a-f]{32}", schluessel or ""):
        return None
    return next((g for g in daten["geraete"] if hmac.compare_digest(anzeige_schluessel(g), schluessel)), None)


def anzeige_pfad_ok(pfad):
    """Was der Direktmodus abrufen darf: die TV-Seite mit ihren Dateien, nie die Verwaltungs-API."""
    if pfad.startswith(("/api/", "/hlscam/")) or ".." in pfad or "//" in pfad:
        return False
    return bool(re.fullmatch(r"/([A-Za-z0-9_.\-]+/)*[A-Za-z0-9_.\-]*", pfad))


def modus_fuer(g, bericht=None):
    """Stream oder direkt – Pi 3/Zero 2 W (laut Meldung oder Einstellung) immer Stream."""
    if g.get("modell") == BROWSER:
        return "direkt"
    modell = ((bericht or (stand.get(g["id"]) or {}).get("bericht")) or {}).get("modell") or ""
    if g.get("modell") == "pi3" or re.search(r"Pi 3|Zero 2", modell):
        return "stream"
    return g.get("anzeige_modus", "stream") if g.get("anzeige_modus") in ANZEIGE_MODI else "stream"


RAM_DIREKT_MIN = 1536     # MB MemTotal: darunter ein Pi mit 1 GB oder weniger – für den Direktmodus zu knapp (Empfehlung ab 2 GB)


def ram_knapp_direkt(mb):
    """Direktmodus: Pi meldet weniger als 2 GB Arbeitsspeicher (nur Hinweis, der Modus bleibt erlaubt)."""
    return isinstance(mb, int) and not isinstance(mb, bool) and 0 < mb < RAM_DIREKT_MIN


def agent_hash():
    try:
        return hashlib.sha256(open(AGENT, "rb").read()).hexdigest()
    except OSError:
        return ""


def melden(g, bericht, ip, stream, bildschirm):
    """Meldung eines Players verbuchen; Antwort: alles, was er tun soll."""
    bericht = bericht if isinstance(bericht, dict) else {}
    ergebnisse_merken(g, bericht.pop("ergebnisse", None))
    with sperre:
        alt = stand.get(g["id"]) or {}
        stand[g["id"]] = {"zeit": time.time(), "bericht": bericht, "ip": ip, "seit": alt.get("seit") if alt.get("zeit", 0) > time.time() - ONLINE_S * 2 else time.time()}
        offen = befehle.pop(g["id"], [])
        ws = g.get("wlan_soll")
        if ws and int(bericht.get("wlan_rev") or 0) >= ws["rev"]:
            g["wlan_soll"] = None
            speichern(daten)
    abruf = direkt_abruf.get(g["id"])
    return {"ok": True, "intervall": 15, "name": g["name"], "stream": stream, "lautstaerke": g["lautstaerke"],
            "modus": modus_fuer(g, bericht), "direkt_abruf": int(time.time() - abruf) if abruf else None,
            "drehung": g["drehung"], "aufloesung": g["aufloesung"], "hwdec": g["hwdec"], "schreibschutz": g["schreibschutz"],
            "bildschirm": bildschirm, "befehle": [{"id": b["id"], "art": b["art"]} for b in offen],
            "wlan": {"rev": g["wlan_soll"]["rev"], "netze": g["wlan_soll"]["netze"]} if g.get("wlan_soll") else None,
            "agent": agent_hash(), "terminal": FW.fuer_meldung(g) if bericht.get("fernwartung") else None}


def ergebnisse_merken(g, liste):
    if not isinstance(liste, list):
        return
    neu = [{"art": str(e.get("art", ""))[:20], "ok": bool(e.get("ok")), "hinweis": str(e.get("hinweis") or "")[:200],
            "zeit": time.strftime("%H:%M"), "ts": int(time.time())} for e in liste[:10] if isinstance(e, dict)]   # ts: Verwaltung formatiert selbst (seit 0.23.2)
    if neu:
        ergebnisse[g["id"]] = (neu + ergebnisse.get(g["id"], []))[:10]


def datei_ablegen(g, endung, roh):
    os.makedirs(ORDNER, exist_ok=True)
    pfad = os.path.join(ORDNER, g["id"] + endung)
    with open(pfad + ".tmp", "wb") as f:
        f.write(roh)
    os.replace(pfad + ".tmp", pfad)


def online(gid):
    g = geraet(gid)
    if g and g.get("modell") == BROWSER:               # Browser-Gerät: die Seite holt alle 15 s ihre Daten
        a = direkt_abruf.get(gid)
        return bool(a) and time.time() - a < ONLINE_S
    s = stand.get(gid)
    return bool(s) and time.time() - s["zeit"] < ONLINE_S


def gesehen(gid):
    """Hat sich das Gerät seit dem Start des Dienstes schon einmal gemeldet (Agent) bzw. Daten abgerufen (Browser)?"""
    return bool(stand.get(gid) or direkt_abruf.get(gid))


def zuletzt(gid):
    g, s = geraet(gid), stand.get(gid)
    if g and g.get("modell") == BROWSER:
        return direkt_abruf.get(gid)
    return s["zeit"] if s else None


def liste(hinweise):
    """Geräte für die Verwaltung – ohne Schlüssel und WLAN-Schlüssel."""
    aus = []
    for g in daten["geraete"]:
        s = stand.get(g["id"]) or {}
        bild = os.path.join(ORDNER, g["id"] + ".jpg")
        z = zuletzt(g["id"])
        aus.append(dict({k: v for k, v in g.items() if k not in ("schluessel", "wlan_soll", "hotspot_pw")},
                        online=online(g["id"]), zuletzt=int(z) if z else None, seit=int(s.get("seit") or 0) or None,
                        link_pfad="/anzeige/" + anzeige_schluessel(g) if g.get("modell") == BROWSER else None,
                        bericht=s.get("bericht") or {}, ip=s.get("ip"), wlan_offen=(g.get("wlan_soll") or {}).get("netze", [{}])[0].get("ssid"),
                        befehle=[b["art"] for b in befehle.get(g["id"], [])], ergebnisse=ergebnisse.get(g["id"], []),
                        bild=int(os.path.getmtime(bild)) if os.path.exists(bild) else None,
                        protokoll=os.path.exists(os.path.join(ORDNER, g["id"] + ".log")), hinweise=hinweise(g),
                        anzeige_modus=g.get("anzeige_modus", "stream"), modus=modus_fuer(g),
                        fernwartung=bool((s.get("bericht") or {}).get("fernwartung")), terminal=FW.zustand(g["id"]),
                        fernwartung_protokoll=FW.protokoll(g["id"], 5)))
    return aus


def wochenpflege():
    """Sonntag 3–4 Uhr: Systemupdate für Geräte mit „wöchentlich“, die online sind und länger als 6 Tage keines hatten."""
    t = time.localtime()
    if t.tm_wday != 6 or t.tm_hour != 3:
        return
    for g in daten["geraete"]:
        lu = ((stand.get(g["id"]) or {}).get("bericht") or {}).get("letztes_update") or {}
        if g.get("modell") in ("pc", BROWSER):        # PC: Updates mit neuem Image; Browser: kein Agent
            continue
        if g["systemupdate"] == "woechentlich" and online(g["id"]) and time.time() - (lu.get("zeit") or 0) > 6 * 86400 \
                and not any(b["art"] == "systemupdate" for b in befehle.get(g["id"], [])) and g["id"] not in pflege_heute:
            pflege_heute.add(g["id"])
            befehl(g["id"], "systemupdate")
    if t.tm_min > 55:
        pflege_heute.clear()


pflege_heute = set()


# ---------- Grundimage ----------
def basis_meta(art="pi"):
    try:
        o = ordner(art)
        m = json.load(open(os.path.join(o, "meta.json")))
        return m if os.path.exists(os.path.join(o, m["datei"])) else None
    except (OSError, ValueError, KeyError):
        return None


def _holen(url, ziel=None, fortschritt=None):
    art = "application/vnd.github+json" if url.startswith("https://api.github.com/") else "application/octet-stream"
    anf = urllib.request.Request(url, headers={"User-Agent": "SignageCast", "Accept": art})
    with urllib.request.urlopen(anf, timeout=60) as r:
        if not ziel:
            return r.read(4_000_000)
        with open(ziel, "wb") as f:
            while True:
                teil = r.read(1 << 20)
                if not teil:
                    break
                f.write(teil)
                if fortschritt:
                    fortschritt(len(teil))


def _quelle(version, art="pi"):
    """(Version, {Name: Adresse}) des neuesten Release mit diesem Image – zuerst das zur eigenen Version."""
    a = ARTEN[art]
    if QUELLE:
        meta = next((n for n in sorted(os.listdir(QUELLE)) if re.fullmatch(re.escape(a["name"]) + r".+\.json", n)
                     and not n.endswith(".cdx.json")), None)          # seit 0.30 liegt die SBOM daneben
        if not meta:
            raise Fehler("pi_kein_image")
        v = meta[len(a["name"]):-5]
        return v, {n: "file://" + os.path.join(QUELLE, n) for n in os.listdir(QUELLE)}
    rel = json.loads(_holen(f"https://api.github.com/repos/{PROJEKT}/releases?per_page=20"))
    rel.sort(key=lambda r: r.get("tag_name") != f"v{version}")
    for r in rel:
        if r.get("draft") or r.get("prerelease"):
            continue
        namen = {a["name"]: a["browser_download_url"] for a in r.get("assets", [])}
        v = r["tag_name"].lstrip("v")
        if all(f"{a['name']}{v}{e}" in namen for e in (".json", ".json.minisig", a["endung"])):
            return v, namen
    raise Fehler("pi_kein_image")


def basis_laden(version, art="pi"):
    """Grundimage holen und prüfen: Signatur der .json (minisign, Schlüssel der Releases), dann Prüfsumme des Images."""
    st, a = basis_stand[art], ARTEN[art]
    grund = ordner(art)
    if st["phase"] == "laedt":
        return
    st.update(phase="laedt", geladen=0, gesamt=0, fehler="", code="", p={}, version="")
    try:
        v, namen = _quelle(version, art)
        os.makedirs(grund, exist_ok=True)
        tmp = os.path.join(grund, "neu")
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
        n = a["name"] + v
        _holen(namen[n + ".json"], os.path.join(tmp, "meta.json"))
        _holen(namen[n + ".json.minisig"], os.path.join(tmp, "meta.json.minisig"))
        r = subprocess.run(["minisign", "-Vqm", os.path.join(tmp, "meta.json"), "-P", SCHLUESSEL, "-x", os.path.join(tmp, "meta.json.minisig")],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise Fehler("pi_signatur")
        meta = json.load(open(os.path.join(tmp, "meta.json")))
        if meta.get("art") != a["art"] or meta["platzhalter"]["laenge"] != PLATZ or not re.fullmatch(r"[A-Za-z0-9._-]+", meta.get("datei", "")):
            raise Fehler("pi_signatur")
        if shutil.disk_usage(grund).free < meta["xz_groesse"] + 500_000_000:
            raise Fehler("pi_platz", mb=meta["xz_groesse"] // 1_000_000 + 500)
        st.update(gesamt=meta["xz_groesse"], version=v)
        h = hashlib.sha256()

        def weiter(n):
            st["geladen"] += n
        _holen(namen[meta["datei"]], os.path.join(tmp, meta["datei"]), weiter)
        with open(os.path.join(tmp, meta["datei"]), "rb") as f:
            for teil in iter(lambda: f.read(1 << 20), b""):
                h.update(teil)
        if h.hexdigest() != meta["sha256"]:
            raise Fehler("pi_pruefsumme")
        for alt in os.listdir(grund):              # altes Grundimage weg, neues an seine Stelle
            if alt != "neu":
                os.unlink(os.path.join(grund, alt))
        for x in os.listdir(tmp):
            os.replace(os.path.join(tmp, x), os.path.join(grund, x))
        os.rmdir(tmp)
        st.update(phase="fertig")
    except Exception as f:
        shutil.rmtree(os.path.join(grund, "neu"), ignore_errors=True)
        st.update(phase="fehler", fehler=str(f)[:200], code=getattr(f, "code", ""), p=getattr(f, "p", {}))


def basis_info(art="pi"):
    m = basis_meta(art)
    return dict(basis_stand[art], vorhanden={"version": m["version"], "groesse": m["groesse"], "erstellt": m.get("erstellt"),
                                              "basis": m.get("basis")} if m else None)


# ---------- Image je Gerät ----------
def hostname(g):
    return ("sc-" + (re.sub(r"[^a-z0-9]+", "-", g["name"].lower()).strip("-")[:20] or g["id"])).strip("-")


def sammel_hotspot_pw():
    with sperre:
        if not daten.get("sammel_hotspot_pw"):
            daten["sammel_hotspot_pw"] = "".join(secrets.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(10))
            speichern(daten)
        return daten["sammel_hotspot_pw"]


def konfig(g, netze, server, sprache, zeitzone, fernwartung=False):
    """Gerätedatei für die Boot-Partition – genau PLATZ Byte (JSON, Rest Leerzeichen). g = None: Image für mehrere Pis
    (ohne Schlüssel – der Pi koppelt sich per Code)."""
    k = {"art": "signagecast-player", "v": 1, "server": server,
         "sprache": sprache if sprache in ("de", "en") else "de", "zeitzone": zeitzone or "", "land": LAENDER.get(zeitzone, "DE"),
         "wlan": netze}
    if fernwartung:                                    # seit 0.33: Terminal aus der Verwaltung erlaubt (ab Werk aus)
        k["fernwartung"] = True
    if g:
        k.update(id=g["id"], schluessel=g["schluessel"], name=g["name"], hostname=hostname(g), wlan_rev=g.get("wlan_rev", 0),
                 hotspot_pw=g["hotspot_pw"], schreibschutz=g["schreibschutz"],
                 anzeige={"lautstaerke": g["lautstaerke"], "drehung": g["drehung"], "hwdec": g["hwdec"],
                          "modus": {"1080": "1920x1080", "2160": "3840x2160", "720": "1280x720"}.get(g["aufloesung"], "preferred")})
    else:
        k.update(kopplung=True, name="", hostname="sc-player", wlan_rev=0, hotspot_pw=sammel_hotspot_pw(), schreibschutz=True)
    roh = json.dumps(k, ensure_ascii=False, indent=1).encode()
    if len(roh) > PLATZ - 1:
        raise Fehler("pi_konfig_gross")
    return roh + b" " * (PLATZ - 1 - len(roh)) + b"\n"


def image_art(g, art=None):
    """pi oder pc: aus dem Modell des Geräts, beim Image für mehrere Geräte aus der Auswahl."""
    if g:
        return "pc" if g.get("modell") == "pc" else "pi"
    return "pc" if art == "pc" else "pi"


def herunterladen_vorbereiten(gid, w, server, fernwartung=False, art=None, form="gz"):
    """Einmal-Kennung (30 min) für den Download; das WLAN lebt nur bis dahin im Speicher, wenn es nicht gespeichert wird.
    gid = "": Image für mehrere Geräte (Kopplung per Code). form: gz (.img.gz, USB-Stick/SD-Karte) oder iso (PC: roh,
    für Ventoy, CD und VMs)."""
    g = geraet(gid) if gid else None
    if gid and not g:
        raise Fehler("pi_unbekannt")
    if g and g.get("modell") == BROWSER:
        raise Fehler("pi_browser_befehl")
    art = image_art(g, art)
    meta = basis_meta(art)
    if not meta:
        raise Fehler("pi_kein_image")
    if not gid and _version(meta.get("version")) < (0, 25):       # erst der Agent ab 0.25 kann sich koppeln
        raise Fehler("pi_basis_alt", v=meta.get("version") or "?")
    netz, merken = wlan_aus_anfrage(w)
    if merken:
        wlan_merken(netz)
    if not re.fullmatch(r"https?://[A-Za-z0-9.\-\[\]:]+", server or ""):
        raise Fehler("pi_server")
    if re.match(r"https?://(localhost|127\.|\[::1\]|0\.0\.0\.0)", server):
        raise Fehler("pi_server_lokal")
    jetzt = time.time()
    for k in [k for k, v in einmal.items() if v["bis"] < jetzt]:
        del einmal[k]
    kennung = secrets.token_urlsafe(18)
    einmal[kennung] = {"id": gid, "netze": [netz] if netz else [], "server": server, "bis": jetzt + 1800, "fernwartung": bool(fernwartung),
                       "art": art, "form": "iso" if art == "pc" and form == "iso" else "gz"}
    return kennung


def _version(v):
    try:
        return tuple(int(x) for x in str(v).split(".")[:3])
    except ValueError:
        return (0,)


def dateiname(g, art="pi", form="gz"):
    vorne = "signagecast-pc-" if art == "pc" else "signagecast-player-"
    name = (re.sub(r"[^a-z0-9]+", "-", g["name"].lower()).strip("-") or g["id"]) if g else "kopplung"
    return vorne + name + (".iso" if art == "pc" and form == "iso" else ".img.gz")


def dateiname_fuer(kennung):
    e = einmal.get(kennung) or {}
    return dateiname(geraet(e["id"]) if e.get("id") else None, e.get("art", "pi"), e.get("form", "gz"))


def image_schreiben(kennung, schreiben, sprache, zeitzone):
    """Grundimage entpacken, Gerätedatei in den Platzhalter schreiben, als .img.gz (bzw. PC: auch roh als .iso)
    ausgeben (schreiben(bytes))."""
    e = einmal.get(kennung)
    if not e or e["bis"] < time.time():
        raise Fehler("pi_link_alt")
    art, roh_aus = e.get("art", "pi"), e.get("form") == "iso"
    g, meta = geraet(e["id"]) if e["id"] else None, basis_meta(art)
    if (e["id"] and not g) or not meta:
        raise Fehler("pi_kein_image")
    neu = konfig(g, e["netze"], e["server"], sprache, zeitzone, e.get("fernwartung", False))
    off, marke = meta["platzhalter"]["offset"], meta["platzhalter"]["marke"].encode() + b"-0000"
    ende = off + PLATZ
    dec, gz, pos, alt = lzma.LZMADecompressor(), zlib.compressobj(1, zlib.DEFLATED, 31), 0, b""
    with open(os.path.join(ordner(art), meta["datei"]), "rb") as f:
        roh = b""
        while not dec.eof:
            if dec.needs_input:
                roh = f.read(1 << 20)
                if not roh:
                    break
            teil = dec.decompress(roh, max_length=4 << 20)
            roh = b""
            if pos < ende and pos + len(teil) > off:   # Abschnitt berührt den Platzhalter
                a, b = max(off, pos), min(ende, pos + len(teil))
                alt += teil[a - pos:b - pos]
                if len(alt) >= len(marke) and not alt.startswith(marke):
                    raise Fehler("pi_platzhalter")
                teil = teil[:a - pos] + neu[a - off:b - off] + teil[b - pos:]
            pos += len(teil)
            if teil:
                schreiben(teil if roh_aus else gz.compress(teil))
    if pos != meta["groesse"] or not alt.startswith(marke):
        raise Fehler("pi_platzhalter")
    if not roh_aus:
        schreiben(gz.flush())
    einmal.pop(kennung, None)
