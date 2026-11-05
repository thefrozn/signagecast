# SignageCast – Raspberry-Pi-Player (seit 0.23). Die Pis sind reine Abspielgeräte: Sie zeigen den fertigen Stream eines
# Fernsehers per HDMI und melden sich alle paar Sekunden über den Webhook-Port (8890) – dabei holen sie Einstellungen und
# Befehle ab (Pull, am Pi ist kein Port offen). Jede Anfrage und jede Antwort ist mit dem Schlüssel des Geräts signiert
# (HMAC-SHA256); der Schlüssel steht nur in der Gerätedatei auf der SD-Karte und hier.
# Image je Gerät: ein Grundimage (GitHub-Release, signiert) wird einmal geladen; beim Herunterladen schreibt die
# Verwaltung die Gerätedatei in den Platzhalter auf der Boot-Partition (bekannter Versatz) und packt neu – ohne mounten.
import hashlib, hmac, json, lzma, os, re, secrets, shutil, subprocess, threading, time, urllib.request, zlib

from streams import DATEN
from meldung import Meldung as Fehler

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT = os.path.join(BASIS, "player", "agent.py")
DATEI = os.path.join(DATEN, "player.json")
ORDNER = os.path.join(DATEN, "player")
GRUND = os.path.join(ORDNER, "basis")
PROJEKT = "thefrozn/signagecast"
QUELLE = os.environ.get("SC_PLAYER_QUELLE", "")       # Ordner mit Grundimage (Test vor dem Release), sonst GitHub
# Öffentlicher Schlüssel der Releases (wie werkzeug/aktualisieren.sh; release.sh prüft, dass beide gleich sind)
SCHLUESSEL = "RWS+1ozfjYuftY7DYt4RjDJLsJKenGkFL7prSxRjeDuk3c+++cclZqgD"
PLATZ = 16384                                          # Länge des Platzhalters signagecast.json im Image
MODELLE = ("pi45", "pi3")                              # Pi 5/4/400/CM4 | Pi 3/Zero 2 W (nur H.264 bis Full HD)
AUFLOESUNGEN = ("auto", "720", "1080", "2160")
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
einmal = {}           # Download-Kennung -> {"id", "netze", "server", "bis"}
basis_stand = {"phase": "", "geladen": 0, "gesamt": 0, "fehler": "", "code": "", "p": {}, "version": ""}


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
    if d.get("modell") in MODELLE:
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


def neu(d, tvs):
    """Neues Gerät anlegen. Gibt das Gerät zurück; das Image dazu kommt über herunterladen_vorbereiten()."""
    g = {"id": secrets.token_hex(4), "schluessel": secrets.token_hex(32), "erstellt": time.strftime("%Y-%m-%d %H:%M"),
         "name": "", "tv": "", "modell": "pi45", "aufloesung": "auto", "drehung": 0, "lautstaerke": 100, "cec_zeitplan": False,
         "schreibschutz": True, "systemupdate": "woechentlich", "hwdec": "auto", "wlan_rev": 0, "wlan_soll": None,
         "hotspot_pw": "".join(secrets.choice("abcdefghjkmnpqrstuvwxyz23456789") for _ in range(10))}
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
    for endung in (".jpg", ".log"):
        try:
            os.unlink(os.path.join(ORDNER, gid + endung))
        except OSError:
            pass


def befehl(gid, art):
    if art not in BEFEHLE:
        raise Fehler("pi_befehl")
    if not geraet(gid):
        raise Fehler("pi_unbekannt")
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
    return {"ok": True, "intervall": 15, "name": g["name"], "stream": stream, "lautstaerke": g["lautstaerke"],
            "drehung": g["drehung"], "aufloesung": g["aufloesung"], "hwdec": g["hwdec"], "schreibschutz": g["schreibschutz"],
            "bildschirm": bildschirm, "befehle": [{"id": b["id"], "art": b["art"]} for b in offen],
            "wlan": {"rev": g["wlan_soll"]["rev"], "netze": g["wlan_soll"]["netze"]} if g.get("wlan_soll") else None,
            "agent": agent_hash()}


def ergebnisse_merken(g, liste):
    if not isinstance(liste, list):
        return
    neu = [{"art": str(e.get("art", ""))[:20], "ok": bool(e.get("ok")), "hinweis": str(e.get("hinweis") or "")[:200],
            "zeit": time.strftime("%H:%M")} for e in liste[:10] if isinstance(e, dict)]
    if neu:
        ergebnisse[g["id"]] = (neu + ergebnisse.get(g["id"], []))[:10]


def datei_ablegen(g, endung, roh):
    os.makedirs(ORDNER, exist_ok=True)
    pfad = os.path.join(ORDNER, g["id"] + endung)
    with open(pfad + ".tmp", "wb") as f:
        f.write(roh)
    os.replace(pfad + ".tmp", pfad)


def online(gid):
    s = stand.get(gid)
    return bool(s) and time.time() - s["zeit"] < ONLINE_S


def liste(hinweise):
    """Geräte für die Verwaltung – ohne Schlüssel und WLAN-Schlüssel."""
    aus = []
    for g in daten["geraete"]:
        s = stand.get(g["id"]) or {}
        bild = os.path.join(ORDNER, g["id"] + ".jpg")
        aus.append(dict({k: v for k, v in g.items() if k not in ("schluessel", "wlan_soll", "hotspot_pw")},
                        online=online(g["id"]), zuletzt=int(s["zeit"]) if s else None, seit=int(s.get("seit") or 0) or None,
                        bericht=s.get("bericht") or {}, ip=s.get("ip"), wlan_offen=(g.get("wlan_soll") or {}).get("netze", [{}])[0].get("ssid"),
                        befehle=[b["art"] for b in befehle.get(g["id"], [])], ergebnisse=ergebnisse.get(g["id"], []),
                        bild=int(os.path.getmtime(bild)) if os.path.exists(bild) else None,
                        protokoll=os.path.exists(os.path.join(ORDNER, g["id"] + ".log")), hinweise=hinweise(g)))
    return aus


def wochenpflege():
    """Sonntag 3–4 Uhr: Systemupdate für Geräte mit „wöchentlich“, die online sind und länger als 6 Tage keines hatten."""
    t = time.localtime()
    if t.tm_wday != 6 or t.tm_hour != 3:
        return
    for g in daten["geraete"]:
        lu = ((stand.get(g["id"]) or {}).get("bericht") or {}).get("letztes_update") or {}
        if g["systemupdate"] == "woechentlich" and online(g["id"]) and time.time() - (lu.get("zeit") or 0) > 6 * 86400 \
                and not any(b["art"] == "systemupdate" for b in befehle.get(g["id"], [])) and g["id"] not in pflege_heute:
            pflege_heute.add(g["id"])
            befehl(g["id"], "systemupdate")
    if t.tm_min > 55:
        pflege_heute.clear()


pflege_heute = set()


# ---------- Grundimage ----------
def basis_meta():
    try:
        m = json.load(open(os.path.join(GRUND, "meta.json")))
        return m if os.path.exists(os.path.join(GRUND, m["datei"])) else None
    except (OSError, ValueError, KeyError):
        return None


def _holen(url, ziel=None, fortschritt=None):
    anf = urllib.request.Request(url, headers={"User-Agent": "SignageCast", "Accept": "application/octet-stream"})
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


def _quelle(version):
    """(Version, {Name: Adresse}) des neuesten Release mit Player-Image – zuerst das zur eigenen Version."""
    if QUELLE:
        meta = next((n for n in sorted(os.listdir(QUELLE)) if re.fullmatch(r"signagecast-player-v.+\.json", n)), None)
        if not meta:
            raise Fehler("pi_kein_image")
        v = meta[len("signagecast-player-v"):-5]
        return v, {n: "file://" + os.path.join(QUELLE, n) for n in os.listdir(QUELLE)}
    rel = json.loads(_holen(f"https://api.github.com/repos/{PROJEKT}/releases?per_page=20"))
    rel.sort(key=lambda r: r.get("tag_name") != f"v{version}")
    for r in rel:
        if r.get("draft") or r.get("prerelease"):
            continue
        namen = {a["name"]: a["browser_download_url"] for a in r.get("assets", [])}
        v = r["tag_name"].lstrip("v")
        if all(f"signagecast-player-v{v}{e}" in namen for e in (".json", ".json.minisig", ".img.xz")):
            return v, namen
    raise Fehler("pi_kein_image")


def basis_laden(version):
    """Grundimage holen und prüfen: Signatur der .json (minisign, Schlüssel der Releases), dann Prüfsumme des Images."""
    if basis_stand["phase"] == "laedt":
        return
    basis_stand.update(phase="laedt", geladen=0, gesamt=0, fehler="", code="", p={}, version="")
    try:
        v, namen = _quelle(version)
        os.makedirs(GRUND, exist_ok=True)
        tmp = os.path.join(GRUND, "neu")
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
        n = f"signagecast-player-v{v}"
        _holen(namen[n + ".json"], os.path.join(tmp, "meta.json"))
        _holen(namen[n + ".json.minisig"], os.path.join(tmp, "meta.json.minisig"))
        r = subprocess.run(["minisign", "-Vqm", os.path.join(tmp, "meta.json"), "-P", SCHLUESSEL, "-x", os.path.join(tmp, "meta.json.minisig")],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise Fehler("pi_signatur")
        meta = json.load(open(os.path.join(tmp, "meta.json")))
        if meta.get("art") != "signagecast-player-image" or meta["platzhalter"]["laenge"] != PLATZ:
            raise Fehler("pi_signatur")
        if shutil.disk_usage(GRUND).free < meta["xz_groesse"] + 500_000_000:
            raise Fehler("pi_platz", mb=meta["xz_groesse"] // 1_000_000 + 500)
        basis_stand.update(gesamt=meta["xz_groesse"], version=v)
        h = hashlib.sha256()

        def weiter(n):
            basis_stand["geladen"] += n
        _holen(namen[meta["datei"]], os.path.join(tmp, meta["datei"]), weiter)
        with open(os.path.join(tmp, meta["datei"]), "rb") as f:
            for teil in iter(lambda: f.read(1 << 20), b""):
                h.update(teil)
        if h.hexdigest() != meta["sha256"]:
            raise Fehler("pi_pruefsumme")
        for alt in os.listdir(GRUND):              # altes Grundimage weg, neues an seine Stelle
            if alt != "neu":
                os.unlink(os.path.join(GRUND, alt))
        for x in os.listdir(tmp):
            os.replace(os.path.join(tmp, x), os.path.join(GRUND, x))
        os.rmdir(tmp)
        basis_stand.update(phase="fertig")
    except Exception as f:
        shutil.rmtree(os.path.join(GRUND, "neu"), ignore_errors=True)
        basis_stand.update(phase="fehler", fehler=str(f)[:200], code=getattr(f, "code", ""), p=getattr(f, "p", {}))


def basis_info():
    m = basis_meta()
    return dict(basis_stand, vorhanden={"version": m["version"], "groesse": m["groesse"], "erstellt": m.get("erstellt"),
                                         "basis": m.get("basis")} if m else None)


# ---------- Image je Gerät ----------
def konfig(g, netze, server, sprache, zeitzone):
    """Gerätedatei für die Boot-Partition – genau PLATZ Byte (JSON, Rest Leerzeichen)."""
    host = "sc-" + (re.sub(r"[^a-z0-9]+", "-", g["name"].lower()).strip("-")[:20] or g["id"])
    k = {"art": "signagecast-player", "v": 1, "id": g["id"], "schluessel": g["schluessel"], "name": g["name"], "server": server,
         "sprache": sprache if sprache in ("de", "en") else "de", "zeitzone": zeitzone or "", "land": LAENDER.get(zeitzone, "DE"),
         "hostname": host.strip("-"), "wlan": netze, "wlan_rev": g.get("wlan_rev", 0), "hotspot_pw": g["hotspot_pw"],
         "schreibschutz": g["schreibschutz"],
         "anzeige": {"lautstaerke": g["lautstaerke"], "drehung": g["drehung"], "hwdec": g["hwdec"],
                     "modus": {"1080": "1920x1080", "2160": "3840x2160", "720": "1280x720"}.get(g["aufloesung"], "preferred")}}
    roh = json.dumps(k, ensure_ascii=False, indent=1).encode()
    if len(roh) > PLATZ - 1:
        raise Fehler("pi_konfig_gross")
    return roh + b" " * (PLATZ - 1 - len(roh)) + b"\n"


def herunterladen_vorbereiten(gid, w, server):
    """Einmal-Kennung (30 min) für den Download; das WLAN lebt nur bis dahin im Speicher, wenn es nicht gespeichert wird."""
    g = geraet(gid)
    if not g:
        raise Fehler("pi_unbekannt")
    if not basis_meta():
        raise Fehler("pi_kein_image")
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
    einmal[kennung] = {"id": gid, "netze": [netz] if netz else [], "server": server, "bis": jetzt + 1800}
    return kennung


def dateiname(g):
    return "signagecast-player-" + (re.sub(r"[^a-z0-9]+", "-", g["name"].lower()).strip("-") or g["id"]) + ".img.gz"


def image_schreiben(kennung, schreiben, sprache, zeitzone):
    """Grundimage entpacken, Gerätedatei in den Platzhalter schreiben, als .img.gz ausgeben (schreiben(bytes))."""
    e = einmal.get(kennung)
    if not e or e["bis"] < time.time():
        raise Fehler("pi_link_alt")
    g, meta = geraet(e["id"]), basis_meta()
    if not g or not meta:
        raise Fehler("pi_kein_image")
    neu = konfig(g, e["netze"], e["server"], sprache, zeitzone)
    off, marke = meta["platzhalter"]["offset"], meta["platzhalter"]["marke"].encode() + b"-0000"
    ende = off + PLATZ
    dec, gz, pos, alt = lzma.LZMADecompressor(), zlib.compressobj(1, zlib.DEFLATED, 31), 0, b""
    with open(os.path.join(GRUND, meta["datei"]), "rb") as f:
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
                schreiben(gz.compress(teil))
    if pos != meta["groesse"] or not alt.startswith(marke):
        raise Fehler("pi_platzhalter")
    schreiben(gz.flush())
    einmal.pop(kennung, None)
