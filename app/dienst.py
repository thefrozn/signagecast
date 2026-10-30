#!/usr/bin/env python3
# SignageCast – Datendienst. Liefert die TV-Seite (www/) und ihre Daten, führt die Streamliste, sucht neue Streams,
# misst die Qualität (Wache) und bietet der Verwaltung (Cockpit-Erweiterung) eine kleine API.
# Lauscht nur auf 127.0.0.1:8080 – von außen ist nur der fertige Videostream (MediaMTX) und Cockpit erreichbar.
# Im Docker-/Podman-Container (SC_BETRIEB=container) gibt es kein Cockpit: dann liefert verwaltung.py die Verwaltung
# selbst aus (eigene Anmeldung, Port SC_VERWALTUNG_PORT) und reicht ihre Anfragen hierher weiter.
# Nur Python-Standardbibliothek.
import json, os, re, signal, socket, subprocess, sys, threading, time, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import einstellungen as E                     # noqa: E402
from ha import HA, HAFehler                   # noqa: E402
from streams import Streams, ID, DATEN, sonnenhoehe   # noqa: E402
import wache                                  # noqa: E402
import radio                                  # noqa: E402
import layouts as L                           # noqa: E402
import wetter as W                            # noqa: E402
import zeit as Z                              # noqa: E402
import hardware as HW                         # noqa: E402
import meldung as M                           # noqa: E402
import sicherung as S                         # noqa: E402
import medien as MED                          # noqa: E402
import unwetter as UW                         # noqa: E402
import benachrichtigung as BN                 # noqa: E402
import quellen as Q                           # noqa: E402
import base64, hashlib, datetime, queue       # noqa: E402

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WWW = os.path.join(BASIS, "www")
VERSION = open(os.path.join(BASIS, "VERSION")).read().strip() if os.path.exists(os.path.join(BASIS, "VERSION")) else "dev"
MEDIAMTX_YML = os.environ.get("SC_MEDIAMTX", "/etc/signagecast/mediamtx.yml")
MEDIAMTX_VORLAGE = os.path.join(BASIS, "render", "mediamtx.yml")
HLS_PORT = int(os.environ.get("SC_STREAM_PORT", "8888"))   # Stream für die Fernseher (MediaMTX); änderbar über SC_STREAM_PORT
PROJEKT = "thefrozn/signagecast"            # GitHub: Projektseite, Fehlermeldungen, Hinweis auf neue Versionen
CONTAINER = os.environ.get("SC_BETRIEB") == "container"     # Docker/Podman statt LXC
START = time.time()

zustand = {"einstellungen": E.laden(), "ha_teil": {"wetter": {}, "vorhersage": [], "werte": {}},
           "vorhersage": [], "vh_zeit": 0, "kalender": {}, "wache": {}, "cpu": None, "ha_fehler": None}
BILDER = os.path.join(DATEN, "bilder")
met = W.MetWetter()
zeit_neu = threading.Event()
wetter_neu = threading.Event()
sperre = threading.Lock()
neu_liste = threading.Event()
einspieler_neu = threading.Event()


def einst():
    return zustand["einstellungen"]


def einst_aussen():
    """Einstellungen für die Verwaltung: geheime Kopfzeilen der Datenquellen und das Sicherungs-Passwort nur als ••••."""
    e = einst()
    return dict(e, quellen=Q.maskieren(e["quellen"]),
                sicherung=dict(e["sicherung"], passwort=Q.MASKE if e["sicherung"]["passwort"] else ""),
                webhook=dict(e["webhook"], token=Q.MASKE if e["webhook"]["token"] else ""),
                benachrichtigung=bn_geheim(e["benachrichtigung"], lambda w: Q.MASKE if w else ""))


def bn_geheim(b, ersatz):
    """Kopie der Benachrichtigungs-Einstellungen mit ersetzten Geheimnissen (Bot-Token, SMTP-Passwort)."""
    b = json.loads(json.dumps(b))
    for kanal, feld in BN.GEHEIM:
        if isinstance(b.get(kanal), dict) and feld in b[kanal]:
            b[kanal][feld] = ersatz(b[kanal][feld])
    return b


def bn_behalten(neu, auch_leer=False):
    """Maskierte (beim Einspielen ohne Geheimnisse auch leere) Geheimnisse durch die vorhandenen ersetzen."""
    if isinstance(neu, dict) and isinstance(neu.get("benachrichtigung"), dict):
        alt = einst()["benachrichtigung"]
        for kanal, feld in BN.GEHEIM:
            k = neu["benachrichtigung"].get(kanal)
            if isinstance(k, dict) and feld in k and (k[feld] == Q.MASKE or auch_leer and not k[feld]):
                k[feld] = alt[kanal][feld]


qn = Q.Quellen(lambda: einst(), os.path.join(DATEN, "verlauf.json"))


ha = HA(lambda: einst()["ha"]["url"])
streams = Streams(einst)


# ---------- Daten für die TV-Seite ----------
def holen():
    """Werte aller Entitäten, die irgendein Layout braucht, plus Wetter und Vorhersage (5 Tage, alle 10 min)."""
    e = einst()
    wetter = e["anzeige"]["wetter"]
    gebraucht = L.entitaeten(e["layouts"], wetter)
    werte = {}
    for st in ha.get("/api/states"):
        if st["entity_id"] in gebraucht:
            a = st.get("attributes", {})
            werte[st["entity_id"]] = {"state": st.get("state"), "einheit": a.get("unit_of_measurement", ""),
                                      "name": a.get("friendly_name", ""),
                                      **({k: a.get(k) for k in ("temperature", "humidity", "wind_speed", "wind_speed_unit")}
                                         if st["entity_id"].startswith("weather.") else {})}
    if wetter and e["anzeige"]["wetter_quelle"] == "ha" and time.time() - zustand["vh_zeit"] > 600:
        try:
            r = ha.post("/api/services/weather/get_forecasts?return_response", {"entity_id": wetter, "type": "daily"})
            zustand["vorhersage"] = [{"tag": x["datetime"][:10], "zustand": x.get("condition"),
                                      "max": x.get("temperature"), "min": x.get("templow")}
                                     for x in r["service_response"][wetter]["forecast"][:5]]
            zustand["vh_zeit"] = time.time()
        except Exception:
            pass
    w = werte.get(wetter, {})
    return {"wetter": {"entity": wetter, "zustand": w.get("state"), "temperatur": w.get("temperature"),
                       "feuchte": w.get("humidity"), "wind": w.get("wind_speed"), "wind_einheit": w.get("wind_speed_unit") or "km/h"},
            "vorhersage": zustand["vorhersage"], "werte": werte}


def wetter_schleife():
    """Eigenes Wetter (MET Norway): alle 5 min nachsehen – abgerufen wird nur, wenn die Daten abgelaufen sind."""
    while True:
        e = einst()
        if e["anzeige"]["wetter_quelle"] == "met":
            met.holen(e["standort"]["breite"], e["standort"]["laenge"])
        wetter_neu.wait(300)
        wetter_neu.clear()


def zeit_schleife():
    """Abweichung der Systemuhr zur Zeitquelle (NTP) alle 30 min messen; bei geänderter Einstellung sofort."""
    while True:
        e = einst()
        server = e["zeit"]["ntp"]
        if not server:
            try:
                server = Z.standard_server(radio.ort_beschreiben(e["standort"]["breite"], e["standort"]["laenge"]).get("laendercode"))
            except Exception:
                server = "pool.ntp.org"
        zeitzone_setzen()
        host = Z.host_synchronisiert()
        try:
            abw, laufzeit = Z.messen(server)
            # Uhr vom Host synchronisiert und genau genug -> nichts korrigieren (nur kontrollieren);
            # sonst die gemessene Abweichung auf Uhr, Takt und Einspieler anwenden
            zustand["zeit"] = {"server": server, "abweichung_s": round(abw, 4), "laufzeit_ms": round(laufzeit * 1000),
                               "gemessen": time.strftime("%Y-%m-%d %H:%M"), "fehler": None, "fehler_m": None, "host_synchronisiert": host,
                               "korrektur": not (host and abs(abw) < 1.0)}
        except Exception as ex:
            zustand["zeit"] = dict(zustand.get("zeit") or {}, server=server, fehler=str(ex)[:200], fehler_m=M.als_dict(ex), host_synchronisiert=host,
                                   korrektur=False)
        zeit_neu.wait(1800)
        zeit_neu.clear()


def system_zeitzone():
    try:
        return os.path.realpath("/etc/localtime").split("zoneinfo/", 1)[1]
    except Exception:
        return time.tzname[0]


def zeitzone_setzen():
    """Zeitstempel und Tagesgrenzen (Vorhersage, Zeitplan) in der wirksamen Zeitzone – auch wenn der Container in UTC läuft."""
    os.environ["TZ"] = wirksame_zeitzone()
    time.tzset()


def wirksame_zeitzone():
    """Eingestellte Zeitzone, sonst die automatische."""
    return einst()["zeit"]["zeitzone"] or auto_zeitzone()


def auto_zeitzone():
    """Die des Systems – läuft das System in UTC, die des Landes am Standort."""
    e = einst()
    sz = system_zeitzone()
    if sz in ("Etc/UTC", "UTC", "Etc/Universal", "Universal", "Zulu"):
        try:
            land = radio.ort_beschreiben(e["standort"]["breite"], e["standort"]["laenge"]).get("laendercode", "")
            return Z.ZONE_NACH_LAND.get(land, sz)
        except Exception:
            return sz
    return sz


def einspieler_aufloesen(x):
    """Abspielbare Adresse eines Einspielers: {"art": "video"|"youtube", "url"|"video_id", "stand"}."""
    import urllib.request
    kopf = {"User-Agent": radio.UA["User-Agent"]}
    if x["quelle"] == "tagesschau100":
        d = json.load(urllib.request.urlopen(urllib.request.Request("https://www.tagesschau.de/api2u/channels", headers=kopf), timeout=15))
        k = next(c for c in d.get("channels", []) if "100 Sekunden" in c.get("title", ""))
        st = k.get("streams") or {}
        url = st.get("h264xl") or st.get("h264m")
        gross = url.replace(".webxl.h264.mp4", ".webxxl.h264.mp4") if url else None    # 1080p, wenn vorhanden
        if gross and gross != url:
            try:
                urllib.request.urlopen(urllib.request.Request(gross, method="HEAD", headers=kopf), timeout=10)
                url = gross
            except Exception:
                pass
        return {"art": "video", "url": url, "stand": k.get("date", "")[:16]}
    if x["quelle"] == "video":
        return {"art": "video", "url": x["url"], "stand": ""}
    from streams import aus_link
    art_id = aus_link(x["url"])
    if not art_id:
        raise M.Meldung("kein_youtube")
    if art_id[0] == "video":
        return {"art": "youtube", "video_id": art_id[1], "stand": ""}
    # Kanal: neuestes Video aus dem öffentlichen Feed
    t = urllib.request.urlopen(urllib.request.Request(f"https://www.youtube.com/feeds/videos.xml?channel_id={art_id[1]}", headers=kopf), timeout=15).read().decode()
    m = re.search(r"<yt:videoId>([\w-]{11})</yt:videoId>.*?<published>([^<]+)</published>", t, re.S)
    if not m:
        raise M.Meldung("kein_video_kanal")
    return {"art": "youtube", "video_id": m.group(1), "stand": m.group(2)[:16]}


EINSPIELER = os.path.join(DATEN, "einspieler")
EINSPIELER_MAX = 500 * 1024 * 1024


def einspieler_vorladen(x, a):
    """Puffer „vorab“: die Ausgabe in den Container laden (nur MP4-Adressen, nie YouTube) und lokal ausliefern –
    komplett (vorab_mb = 0) oder nur die ersten vorab_mb MB; den Rest holt einspieler_ausliefern beim Abspielen nach.
    Bis eine neue Ausgabe fertig ist, gilt die vorherige weiter. -> a mit "lokal" (Adresse für die TV-Seite) und "vorab"."""
    meta_pfad = os.path.join(EINSPIELER, f"{x['id']}.json")
    datei = os.path.join(EINSPIELER, f"{x['id']}.mp4")
    try:
        meta = json.load(open(meta_pfad))
    except (OSError, ValueError):
        meta = {}
    if a.get("art") != "video" or not a.get("url"):
        return a
    grenze = x["vorab_mb"] * 1024 * 1024 if x["vorab_mb"] else EINSPIELER_MAX
    if meta.get("url") != a["url"] or meta.get("vorab_mb") != x["vorab_mb"] or not os.path.exists(datei):
        os.makedirs(EINSPIELER, exist_ok=True)
        tmp, t0, n, gesamt, ende_erreicht = datei + ".neu", time.time(), 0, None, False
        try:
            kopf = {"User-Agent": radio.UA["User-Agent"]}
            if x["vorab_mb"]:
                kopf["Range"] = f"bytes=0-{grenze - 1}"
            with urllib.request.urlopen(urllib.request.Request(a["url"], headers=kopf), timeout=30) as r, open(tmp, "wb") as f:
                if x["vorab_mb"] and r.status != 206:
                    raise M.Meldung("ep_kein_range")
                m = re.search(r"/(\d+)$", r.headers.get("Content-Range", "") or "")
                gesamt = int(m.group(1)) if m else (int(r.headers["Content-Length"]) if r.headers.get("Content-Length") and r.status == 200 else None)
                while n < grenze:
                    teil = r.read(min(1 << 20, grenze - n))
                    if not teil:
                        ende_erreicht = True
                        break
                    n += len(teil)
                    f.write(teil)
            if not x["vorab_mb"] and not ende_erreicht:
                raise M.Meldung("ep_zu_gross")
            komplett = ende_erreicht or (gesamt is not None and n >= gesamt)
            if not komplett and gesamt is None:
                raise M.Meldung("ep_keine_groesse")
            os.replace(tmp, datei)
            meta = {"url": a["url"], "vorab_mb": x["vorab_mb"], "groesse": n, "gesamt": gesamt if gesamt else n, "komplett": komplett,
                    "zeit": time.strftime("%Y-%m-%d %H:%M"), "stand": a.get("stand", ""), "dauer_s": round(time.time() - t0, 1)}
            with open(meta_pfad, "w") as f:
                json.dump(meta, f)
        except Exception as ex:
            try:
                os.remove(tmp)
            except OSError:
                pass
            a = dict(a, vorab_fehler=f"Vorab laden: {str(ex)[:150]}", vorab_fehler_m=M.als_dict(ex))
    if os.path.exists(datei) and meta.get("url"):
        a = dict(a, lokal=f"/einspieler/{x['id']}.mp4?v={hashlib.sha1((meta['url'] + str(meta.get('vorab_mb'))).encode()).hexdigest()[:10]}",
                 vorab={k: meta.get(k) for k in ("groesse", "gesamt", "komplett", "zeit", "stand")} | {"aktuell": meta.get("url") == a["url"]})
    return a


def einspieler_ausliefern(h, eid):
    """Vorab geladenen Einspieler an die TV-Seite geben: komplett aus der Datei, sonst Anfang aus dem Cache und den Rest
    mit einer Range-Anfrage vom Server (der Browser bekommt eine durchgehende Datei)."""
    datei = os.path.join(EINSPIELER, eid + ".mp4")
    try:
        meta = json.load(open(os.path.join(EINSPIELER, eid + ".json")))
    except (OSError, ValueError):
        return h.antwort(404, {"ok": False})
    if meta.get("komplett"):
        return datei_mit_range(h, datei, "video/mp4")
    gesamt, cache = int(meta["gesamt"]), int(meta["groesse"])
    start, ende = 0, gesamt - 1
    m = re.fullmatch(r"bytes=(\d*)-(\d*)", h.headers.get("Range", "") or "")
    if m and (m.group(1) or m.group(2)):
        if m.group(1):
            start = int(m.group(1)); ende = min(int(m.group(2)) if m.group(2) else gesamt - 1, gesamt - 1)
        else:
            start = max(0, gesamt - int(m.group(2)))
        if start >= gesamt:
            h.send_response(416); h.send_header("Content-Range", f"bytes */{gesamt}"); h.end_headers(); return
        h.send_response(206); h.send_header("Content-Range", f"bytes {start}-{ende}/{gesamt}")
    else:
        h.send_response(200)
    h.send_header("Content-Type", "video/mp4"); h.send_header("Accept-Ranges", "bytes")
    h.send_header("Content-Length", str(ende - start + 1)); h.send_header("Cache-Control", "no-cache")
    h.end_headers()
    try:
        pos = start
        if pos < cache:                           # Anfang aus dem Cache
            with open(datei, "rb") as f:
                f.seek(pos)
                while pos <= min(ende, cache - 1):
                    teil = f.read(min(1 << 20, min(ende, cache - 1) - pos + 1))
                    if not teil:
                        break
                    h.wfile.write(teil); pos += len(teil)
        if pos <= ende:                           # Rest vom Server nachladen
            anf = urllib.request.Request(meta["url"], headers={"User-Agent": radio.UA["User-Agent"], "Range": f"bytes={pos}-{ende}"})
            with urllib.request.urlopen(anf, timeout=30) as r:
                if r.status != 206:
                    return                        # Server kann kein Range – Browser bricht ab, Wache beendet den Einspieler
                while pos <= ende:
                    teil = r.read(1 << 20)
                    if not teil:
                        break
                    h.wfile.write(teil); pos += len(teil)
    except (OSError, urllib.error.URLError):
        pass


def einspieler_aufraeumen(behalten):
    try:
        for n in os.listdir(EINSPIELER):
            if n.split(".")[0] not in behalten:
                os.remove(os.path.join(EINSPIELER, n))
    except OSError:
        pass


def einspieler_schleife():
    while True:
        neu = {}
        for x in einst()["einspieler"]:
            if not x["aktiv"]:
                continue
            try:
                neu[x["id"]] = einspieler_aufloesen(x)
            except Exception as ex:
                neu[x["id"]] = dict(zustand.get("einspieler", {}).get(x["id"], {}), fehler=str(ex)[:200], fehler_m=M.als_dict(ex))
            if x["puffer"] == "vorab":
                neu[x["id"]] = einspieler_vorladen(x, neu[x["id"]])
        einspieler_aufraeumen({x["id"] for x in einst()["einspieler"] if x["aktiv"] and x["puffer"] == "vorab"})
        zustand["einspieler"] = neu
        einspieler_neu.wait(300)
        einspieler_neu.clear()


# ---------- Updates (LXC/nativ): Anfrage an das root-Skript werkzeug/aktualisieren.sh ----------
UPDATE_ANFRAGE = os.path.join(DATEN, "update-anfrage")
UPDATE_AKTIONEN = ("pruefen", "system", "sicherheit", "signagecast", "zurueck")


def updates_moeglich():
    return not CONTAINER and os.path.exists("/etc/systemd/system/signagecast-aktualisieren.path")


def update_status(aktion=None):
    try:
        return json.load(open(os.path.join(DATEN, f"aktualisierung-{aktion}.json" if aktion else "aktualisierung.json")))
    except (OSError, ValueError):
        return None


def update_anfragen(aktion):
    if not updates_moeglich():
        raise M.Meldung("upd_container")
    if aktion not in UPDATE_AKTIONEN:
        raise M.Meldung("upd_aktion")
    st = update_status() or {}
    laeuft = st.get("phase") == "laeuft" and time.time() - os.path.getmtime(os.path.join(DATEN, "aktualisierung.json")) < 3600
    if laeuft or os.path.exists(UPDATE_ANFRAGE):
        raise M.Meldung("upd_laeuft")
    with open(UPDATE_ANFRAGE, "w") as f:
        f.write(aktion)


def update_info():
    vorher = None
    try:
        vorher = open("/opt/signagecast.vorher/VERSION").read().strip()
    except OSError:
        pass
    return {"ok": True, "moeglich": updates_moeglich(), "betrieb": "container" if CONTAINER else "lxc", "version": VERSION,
            "neue_version": zustand.get("neue_version"), "vorher": vorher, "letzte": update_status(),
            "pruefung": update_status("pruefen"), "anfrage_offen": os.path.exists(UPDATE_ANFRAGE)}


def update_auto_schleife():
    """Täglich prüfen; im Wartungsfenster, wenn niemand zuschaut, je nach Einstellung automatisch aktualisieren
    (SignageCast vor dem System, höchstens eine Aktion pro Durchlauf, jede Art einmal pro Tag)."""
    time.sleep(120)
    erledigt = {}
    while True:
        try:
            if updates_moeglich():
                u = einst()["updates"]
                p = update_status("pruefen") or {}
                alt = time.time() - os.path.getmtime(os.path.join(DATEN, "aktualisierung-pruefen.json")) if p else 1e9
                heute = time.strftime("%Y-%m-%d")
                jetzt = time.strftime("%H:%M")
                im_fenster = u["fenster_von"] <= jetzt < u["fenster_bis"] if u["fenster_von"] < u["fenster_bis"] \
                    else (jetzt >= u["fenster_von"] or jetzt < u["fenster_bis"])
                if alt > 20 * 3600:
                    update_anfragen("pruefen")
                elif im_fenster and zuschauer() == 0:
                    pakete = p.get("pakete") or []
                    if u["signagecast"] == "auto" and zustand.get("neue_version") and erledigt.get("signagecast") != heute:
                        erledigt["signagecast"] = heute
                        update_anfragen("signagecast")
                    elif u["system"] == "auto" and pakete and erledigt.get("system") != heute:
                        erledigt["system"] = heute
                        update_anfragen("system")
                    elif u["system"] == "sicherheit" and any(x.get("sicherheit") for x in pakete) and erledigt.get("system") != heute:
                        erledigt["system"] = heute
                        update_anfragen("sicherheit")
        except Exception:
            pass                                  # z. B. „läuft bereits“ – beim nächsten Durchlauf erneut
        time.sleep(60)


def update_schleife():
    """Einmal am Tag nachsehen, ob es auf GitHub eine neuere Version gibt (nur Hinweis, installiert nichts)."""
    import urllib.request
    while True:
        try:
            req = urllib.request.Request(f"https://api.github.com/repos/{PROJEKT}/releases/latest",
                                         headers={"User-Agent": radio.UA["User-Agent"], "Accept": "application/vnd.github+json"})
            tag = json.load(urllib.request.urlopen(req, timeout=15)).get("tag_name", "")
            zahlen = lambda v: tuple(int(x) for x in re.findall(r"\d+", v)[:3])
            zustand["neue_version"] = tag if tag and zahlen(tag) > zahlen(VERSION) else None
        except Exception:
            pass
        time.sleep(86400)


def kalender_schleife():
    """Termine der Kalender-Bausteine (z. B. Müllabfuhr) alle 10 min aus HA holen."""
    while True:
        e = einst()
        kal = {}
        for l in e["layouts"]:
            for el in l["elemente"]:
                if el["typ"] == "kalender" and el["optionen"]["entity"]:
                    ent, tage = el["optionen"]["entity"], el["optionen"]["tage"]
                    kal[ent] = max(kal.get(ent, 0), tage)
        neu = {}
        for ent, tage in kal.items():
            start = datetime.datetime.now().astimezone()
            ende = start + datetime.timedelta(days=tage)
            try:
                ev = ha.get(f"/api/calendars/{ent}?" + urllib.parse.urlencode({"start": start.isoformat(), "end": ende.isoformat()}))
                neu[ent] = [{"titel": x.get("summary", "")[:80],
                             "start": (x.get("start") or {}).get("dateTime") or (x.get("start") or {}).get("date"),
                             "ganztag": "date" in (x.get("start") or {})} for x in ev][:20]
            except Exception:
                neu[ent] = zustand["kalender"].get(ent, [])
        zustand["kalender"] = neu
        time.sleep(600)


# ---------- Meldung per Webhook (seit 0.16) ----------
WEBHOOK_PORT = int(os.environ.get("SC_WEBHOOK_PORT", "8890"))
webhook_versuche = {}                             # IP -> [Zeitpunkte] (höchstens 20 Anfragen je Minute)


def meldung_fuer(tv_id):
    m = zustand.get("meldung_extern")
    if not m or m["bis"] < time.time() or (m.get("tv") and m["tv"] != tv_id):
        return None
    return {"text": m["text"], "stil": m["stil"], "bis": m["bis"]}


class WebhookBearbeiter(BaseHTTPRequestHandler):
    """Nur /meldung, nur mit Schlüssel (Authorization: Bearer … oder ?token=…). Alles andere: 404."""
    def log_message(self, *a):
        pass

    def antwort(self, code, obj):
        roh = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(roh)))
        self.end_headers(); self.wfile.write(roh)

    def bearbeiten(self, daten):
        import hmac
        u = urllib.parse.urlparse(self.path)
        if u.path != "/meldung":
            return self.antwort(404, {"ok": False})
        jetzt, ip = time.time(), self.client_address[0]
        liste = [t for t in webhook_versuche.get(ip, []) if jetzt - t < 60]
        webhook_versuche[ip] = liste + [jetzt]
        if len(liste) >= 20:
            return self.antwort(429, {"ok": False, "fehler": "zu viele Anfragen"})
        wh = einst()["webhook"]
        q = urllib.parse.parse_qs(u.query)
        gegeben = (self.headers.get("Authorization") or "").removeprefix("Bearer ").strip() or (q.get("token") or [""])[0]
        if not wh["aktiv"] or not wh["token"] or not hmac.compare_digest(gegeben.encode(), wh["token"].encode()):
            time.sleep(1)
            return self.antwort(403, {"ok": False})
        text = str(daten.get("text", (q.get("text") or [""])[0]))[:300].strip()
        if not text:
            zustand["meldung_extern"] = None
            return self.antwort(200, {"ok": True, "geloescht": True})
        try:
            dauer = max(5, min(86400, int(daten.get("dauer", (q.get("dauer") or ["60"])[0]))))
        except (TypeError, ValueError):
            dauer = 60
        stil = daten.get("stil", (q.get("stil") or ["info"])[0])
        zustand["meldung_extern"] = {"text": text, "bis": time.time() + dauer, "stil": stil if stil in ("info", "warnung") else "info",
                                     "tv": str(daten.get("tv", (q.get("tv") or [""])[0]))[:12] or None}
        return self.antwort(200, {"ok": True, "bis": int(zustand["meldung_extern"]["bis"])})

    def do_GET(self):
        self.bearbeiten({})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        roh = self.rfile.read(min(n, 4096)) if n else b""
        try:
            daten = json.loads(roh) if roh.strip().startswith(b"{") else {"text": roh.decode(errors="replace")}
        except ValueError:
            daten = {}
        self.bearbeiten(daten if isinstance(daten, dict) else {})


# ---------- Benachrichtigungen (seit 0.16) ----------
melder = BN.Melder(lambda: einst(), lambda pfad, daten: ha.post(pfad, daten))


def benachrichtigung_schleife():
    """Jede Minute: Fernseher-Ausfall (2 Prüfungen in Folge), neue Update-/Sicherungsfehler, HA länger als 5 min getrennt."""
    gesehen_update = (update_status() or {}).get("ts")
    gesehen_sicherung = None
    kaputt, ha_weg = {}, None
    while True:
        time.sleep(60)
        try:
            for t in einst()["fernseher"]:
                if kette_pids(t["id"]) and not kette_laeuft(t["id"]):
                    kaputt[t["id"]] = kaputt.get(t["id"], 0) + 1
                    if kaputt[t["id"]] == 2:
                        melder.melden("ausfall-" + t["id"], "ausfall", f"SignageCast: Ausfall „{t['name']}“",
                                      f"Die Wiedergabe für den Fernseher „{t['name']}“ ist ausgefallen (Render-Kette unvollständig).")
                else:
                    kaputt.pop(t["id"], None)
                    melder.vorbei("ausfall-" + t["id"], f"SignageCast: „{t['name']}“ läuft wieder",
                                  f"Die Wiedergabe für den Fernseher „{t['name']}“ läuft wieder.")
            u = update_status() or {}
            if u.get("ts") != gesehen_update:
                gesehen_update = u.get("ts")
                if u.get("phase") == "fehler" or (u.get("phase") == "zurueck" and u.get("aktion") != "zurueck"):
                    melder.melden(f"update-{u.get('ts')}", "update", "SignageCast: Update fehlgeschlagen",
                                  f"{u.get('aktion')}: {u.get('meldung')} ({u.get('zeit')})")
            sa = zustand.get("sicherung_auto") or {}
            if sa.get("fehler") and sa.get("zeit") != gesehen_sicherung:
                gesehen_sicherung = sa["zeit"]
                melder.melden(f"sicherung-{sa['zeit']}", "sicherung", "SignageCast: Sicherung fehlgeschlagen",
                              f"Die automatische Sicherung um {sa['zeit']} ist fehlgeschlagen: {sa['fehler']}")
            if einst()["ha"]["url"] and zustand["ha_fehler"]:
                ha_weg = ha_weg or time.time()
                if time.time() - ha_weg > 300:
                    melder.melden("ha", "ha", "SignageCast: Home Assistant nicht erreichbar",
                                  f"Seit {time.strftime('%H:%M', time.localtime(ha_weg))}: {zustand['ha_fehler']}")
            else:
                ha_weg = None
                melder.vorbei("ha", "SignageCast: Home Assistant wieder verbunden", "Die Verbindung zu Home Assistant steht wieder.")
        except Exception as ex:
            print("Benachrichtigung:", ex, flush=True)


def unwetter_schleife():
    """DWD-Warnungen für den Standort alle 10 min – nur, wenn ein Layout den Baustein „Unwetterwarnung“ nutzt."""
    while True:
        e = einst()
        if any(x["typ"] == "unwetter" for l in e["layouts"] for x in l["elemente"]):
            try:
                zustand["unwetter"] = {"liste": UW.holen(e["standort"]["breite"], e["standort"]["laenge"]), "zeit": time.time(), "fehler": None}
            except Exception as ex:
                zustand["unwetter"] = dict(zustand.get("unwetter") or {"liste": []}, fehler=str(ex)[:200])
        time.sleep(600)


def verlauf_ha_schleife():
    """Verlauf der HA-Entitäten in Diagramm-Bausteinen alle 5 min aus der HA-Historie holen (nur Zahlen)."""
    while True:
        ents = {}
        for l in einst()["layouts"]:
            for el in l["elemente"]:
                if el["typ"] == "diagramm" and el["optionen"].get("entity"):
                    ents[el["optionen"]["entity"]] = max(ents.get(el["optionen"]["entity"], 0), el["optionen"]["stunden"])
        neu = {}
        for ent, std in ents.items():
            start = (datetime.datetime.now().astimezone() - datetime.timedelta(hours=std)).isoformat()
            try:
                roh = ha.get(f"/api/history/period/{urllib.parse.quote(start)}?" +
                             urllib.parse.urlencode({"filter_entity_id": ent, "minimal_response": "", "no_attributes": ""}))
                pkt = []
                for x in (roh[0] if roh else []):
                    z = Q.als_zahl(x.get("state"))
                    if z is not None and x.get("last_changed"):
                        pkt.append([int(datetime.datetime.fromisoformat(x["last_changed"]).timestamp()), z])
                neu[ent] = pkt
            except Exception:
                neu[ent] = (zustand.get("verlauf_ha") or {}).get(ent, [])
        zustand["verlauf_ha"] = neu
        time.sleep(300)


def fernseher(tv_id=None):
    """Einstellungen eines Fernsehers (ohne Kennung: der erste)."""
    liste = einst()["fernseher"]
    return next((t for t in liste if t["id"] == tv_id), None) if tv_id else liste[0]


def tv_daten(tv_id):
    e = einst()
    t = fernseher(tv_id)
    if not t:
        return {"ok": False, "fehler": "unbekannter Fernseher"}
    v = e["video"]
    layout = L.aktuelles_layout(t, e["layouts"], time.strftime("%H:%M"))
    hat_video = any(x["typ"] == "video" and x["sichtbar"] for x in layout.get("elemente", []))
    vr = streams.vorrang if streams.vorrang and streams.vorrang["bis"] > time.time() \
        and streams.vorrang.get("tv") in (None, t["id"]) else None
    sender = next((x for x in e["radio"]["sender"] if x["id"] == t["radio_sender"]), None)
    liste = [x for x in streams.liste if x["kategorie"] not in t["kategorien_aus"]] \
        if v["aktiv"] and t["video"] and hat_video and t["video_quelle"] != "medien" else []
    medien = [{"id": m["id"], "name": m["name"], "art": m["art"], "url": f"/medien/{m['datei']}", "dauer_s": m["dauer_s"]}
              for m in e["medien"] if m["aktiv"]] if t["video"] and hat_video and t["video_quelle"] != "youtube" else []
    with sperre:
        teil = dict(zustand["ha_teil"])
    kal = {k: w for k, w in zustand["kalender"].items()
           if any(x["typ"] == "kalender" and x["optionen"]["entity"] == k for x in layout.get("elemente", []))}
    eins = []
    for x in e["einspieler"]:
        a = zustand.get("einspieler", {}).get(x["id"], {})
        if x["aktiv"] and (not x["fernseher"] or t["id"] in x["fernseher"]) and (a.get("url") or a.get("video_id")):
            eins.append({"id": x["id"], "name": x["name"], "minuten": x["minuten"], "von": x["von"], "bis": x["bis"], "ton": x["ton"],
                         "art": a["art"], "url": a.get("lokal") or a.get("url"), "video_id": a.get("video_id"), "stand": a.get("stand", ""),
                         "vorlauf_s": x["vorlauf_s"] if x["puffer"] == "vorlauf" else 0})
    if e["anzeige"]["wetter_quelle"] == "met" and met.daten:
        teil["wetter"] = met.aktuell()
        teil["vorhersage"] = met.vorhersage(5)
    api, bed = Q.baustein_werte(layout, qn, e["sprache"] or "en", e["quellen"], zustand.get("verlauf_ha"))
    if bed:
        teil["werte"] = dict(teil.get("werte") or {}, **bed)
    zt = zustand.get("zeit") or {}
    st = e["standort"]
    tz = L.tageszeit(sonnenhoehe(st["breite"], st["laenge"]), sonnenhoehe(st["breite"], st["laenge"], time.time() + 600))
    return dict(teil, ok=True, ha_ok=zustand["ha_fehler"] is None, zeit=int(time.time()), sprache=e["sprache"] or "en", tageszeit=tz,
                einspieler=eins if hat_video else [],
                zeit_abweichung_ms=round((zt.get("abweichung_s") or 0) * 1000) if zt.get("korrektur") else 0,
                zeitzone=wirksame_zeitzone(),
                einspieler_jetzt=zustand.get("einspieler_jetzt") if zustand.get("einspieler_jetzt", {}).get("bis", 0) > time.time() else None,
                tv=t["id"], layout=layout, kalender=kal, api=api,
                medien=medien, medien_modus=t["video_quelle"], medien_alle=t["medien_alle"],
                unwetter=(zustand.get("unwetter") or {}).get("liste", []),
                meldung_extern=meldung_fuer(t["id"]), streams=liste, vorrang=vr if liste else None, versatz=t["nr"],
                ton=t["ton"], lautstaerke=t["lautstaerke"],
                radio={"name": sender["name"], "anzeigen": e["radio"]["anzeigen"],
                       # mit Puffer über den Datendienst (siehe radio_weiterleiten), sonst direkt
                       "url": f"/radio/{t['id']}/{sender['id']}" if e["radio"]["puffer_s"] else sender["url"]}
                if t["ton"] == "radio" and sender else None,
                regeln={"takt_s": v["takt_min"] * 60, "mindeststufe": v["mindeststufe"], "schlecht_s": v["schlecht_s"],
                        "sperre_s": int(v["sperre_h"] * 3600)})


def radio_weiterleiten(handler, tv_id, sender_id):
    """Radio mit Puffer: den Sender selbst abholen, erst puffer_s Sekunden sammeln und dem Browser auf einen Schlag
    geben, danach laufend weiterreichen – so ist der Browser immer puffer_s voraus und überbrückt Aussetzer des
    Senders. Bricht die Verbindung zum Sender ab, wird ohne Wissen des Browsers neu verbunden."""
    import urllib.request
    e = einst()
    t = fernseher(tv_id)
    sender = next((x for x in e["radio"]["sender"] if x["id"] == sender_id), None)
    if not t or not sender or t["radio_sender"] != sender_id:
        return handler.antwort(404, {"ok": False})
    puffer_s = e["radio"]["puffer_s"]
    daten, ende, typ = queue.Queue(maxsize=4000), threading.Event(), {}

    def holen_sender():
        while not ende.is_set():
            try:
                req = urllib.request.Request(sender["url"], headers=dict(radio.UA, **{"Icy-MetaData": "0"}))
                with urllib.request.urlopen(req, timeout=15) as r:
                    typ.setdefault("ct", (r.headers.get("Content-Type") or "audio/mpeg").split(";")[0])
                    while not ende.is_set():
                        stueck = r.read(8192)
                        if not stueck:
                            break
                        daten.put(stueck, timeout=30)
            except Exception:
                pass
            if not ende.is_set():
                zustand.setdefault("radio_neu", {})[tv_id] = zustand.get("radio_neu", {}).get(tv_id, 0) + 1
                ende.wait(2)              # kurz warten, dann neu verbinden
    threading.Thread(target=holen_sender, daemon=True).start()
    try:
        vorlauf, bis = [], time.time() + puffer_s
        while time.time() < bis or not vorlauf:
            try:
                vorlauf.append(daten.get(timeout=max(0.2, bis - time.time())))
            except queue.Empty:
                if time.time() > bis + 30:
                    return handler.antwort(502, {"ok": False})
        handler.send_response(200)
        handler.send_header("Content-Type", typ.get("ct", "audio/mpeg"))
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        handler.wfile.write(b"".join(vorlauf))
        while True:
            try:
                handler.wfile.write(daten.get(timeout=60))
            except queue.Empty:
                break                         # Sender eine Minute stumm: Browser verbindet selbst neu
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass                                  # Browser hat aufgehört (Senderwechsel, Seite neu)
    finally:
        ende.set()


def kamera_bild(entity):
    """Kamerabild aus HA – nur für Kameras, die in einem Layout als Baustein stehen."""
    if not any(el["typ"] == "kamera" and el["optionen"]["entity"] == entity
               for l in einst()["layouts"] for el in l["elemente"]):
        return None
    import urllib.request
    req = urllib.request.Request(einst()["ha"]["url"] + f"/api/camera_proxy/{entity}",
                                 headers={"Authorization": "Bearer " + ha._gueltiger_token()})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read(8_000_000)


def bild_speichern(b64):
    daten = base64.b64decode(str(b64).split(",")[-1], validate=False)
    if len(daten) > 8_000_000:
        raise E.Fehler("Bild zu groß (höchstens 8 MB)")
    if daten[:3] == b"\xff\xd8\xff":
        endung = "jpg"
    elif daten[:8] == b"\x89PNG\r\n\x1a\n":
        endung = "png"
    else:
        raise E.Fehler("Nur JPG oder PNG")
    os.makedirs(BILDER, exist_ok=True)
    name = hashlib.sha256(daten).hexdigest()[:16] + "." + endung
    with open(os.path.join(BILDER, name), "wb") as f:
        f.write(daten)
    return name


def ha_schleife():
    # Update von ≤ 0.6: dort stand immer eine Wetter-Entität drin (Voreinstellung). Ist HA beim ersten Abruf nicht
    # erreichbar, auf das eigene Wetter umstellen – sonst bliebe das Wetter leer.
    try:
        roh = json.load(open(E.PFAD)).get("anzeige", {})
        alt_ohne_quelle = "wetter_quelle" not in roh
    except Exception:
        alt_ohne_quelle = False
    erster = True
    while True:
        try:
            teil = holen()
            zustand["ha_fehler"] = None
            zustand["ha_fehler_code"] = None
            with sperre:
                zustand["ha_teil"] = teil
        except Exception as ex:
            zustand["ha_fehler"] = str(ex)[:300]
            zustand["ha_fehler_code"] = (getattr(ex, "code", "") or "unbekannt", getattr(ex, "detail", "") or str(ex)[:200])
            if erster and alt_ohne_quelle and einst()["anzeige"]["wetter_quelle"] == "ha":
                zustand["einstellungen"] = E.speichern(E.zusammenfuehren(einst(), {"anzeige": {"wetter_quelle": "met"}}))
                wetter_neu.set()
        erster = False
        time.sleep(15)


def streams_schleife():
    while True:
        try:
            streams.aktualisieren()
        except Exception as ex:
            streams.status["fehler"] = str(ex)[:300]
        neu_liste.wait(300)
        neu_liste.clear()


def suche_schleife():
    # Nur zur eingestellten Uhrzeit suchen (nicht nachholen nach einem Neustart – die Suche fragt YouTube viel ab)
    letzte = time.strftime("%H:%M")
    while True:
        time.sleep(30)
        e = einst()["suche"]
        jetzt = time.strftime("%H:%M")
        if e["aktiv"] and letzte < e["uhrzeit"] <= jetzt:
            try:
                streams.suchen()
                neu_liste.set()
            except Exception as ex:
                streams.status["suche"] = {"zeit": time.strftime("%Y-%m-%d %H:%M"), "fehler": str(ex)[:300]}
        letzte = jetzt if jetzt >= letzte else "00:00"     # Mitternacht


# ---------- System ----------
def cpu_schleife():
    def lese():
        w = [int(x) for x in open("/proc/stat").readline().split()[1:]]
        return sum(w), w[3] + w[4]
    a = lese()
    while True:
        time.sleep(5)
        b = lese()
        ges, leer = b[0] - a[0], b[1] - a[1]
        zustand["cpu"] = round(100 * (ges - leer) / ges, 1) if ges else None
        a = b


def zuschauer():
    n = set()
    for datei in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            for z in open(datei).readlines()[1:]:
                f = z.split()
                if int(f[1].split(":")[1], 16) == HLS_PORT and f[3] == "01":
                    n.add(f[2].rsplit(":", 1)[0])
        except Exception:
            pass
    return len(n)


def kette_pids(tv_id):
    """Sitzungen (Xvfb, Chromium, ffmpeg) der Render-Kette eines Fernsehers, laut PID-Datei des Startskripts."""
    try:
        return [int(x) for x in open(os.path.join(DATEN, f"kette-{tv_id}.pids")).read().split()]
    except (OSError, ValueError):
        return []


def kette_laeuft(tv_id):
    pids = kette_pids(tv_id)
    return len(pids) == 3 and all(os.path.exists(f"/proc/{p}") for p in pids)


def anzeige_nr(t):
    return f":{99 + t['nr']}"


def status():
    m = {}
    for z in open("/proc/meminfo"):
        k, w = z.split(":")
        m[k] = int(w.split()[0])
    sv = os.statvfs("/")
    e = einst()
    return {
        "version": VERSION, "zeit": time.strftime("%Y-%m-%d %H:%M:%S"),
        "neue_version": zustand.get("neue_version"), "projekt": f"https://github.com/{PROJEKT}",
        "wetter": {"quelle": e["anzeige"]["wetter_quelle"], "abruf": met.abruf, "fehler": met.fehler, "fehler_m": met.fehler_m,
                   "jetzt": met.aktuell() if e["anzeige"]["wetter_quelle"] == "met" else None},
        "zeit_quelle": dict(zustand.get("zeit") or {}, zeitzone=wirksame_zeitzone(), system_zeitzone=system_zeitzone()),
        "cpu_prozent": zustand["cpu"], "last": os.getloadavg(), "kerne": os.cpu_count(),
        "ram_mb": {"gesamt": m["MemTotal"] // 1024, "frei": m["MemAvailable"] // 1024},
        "platte_gb": {"gesamt": round(sv.f_blocks * sv.f_frsize / 1e9, 1), "frei": round(sv.f_bavail * sv.f_frsize / 1e9, 1)},
        "laufzeit_s": int(time.time() - START) if CONTAINER else int(float(open("/proc/uptime").read().split()[0])),
        "betrieb": "container" if CONTAINER else "lxc", "kodierung": zustand.get("kodierung"),
        "stream": {"zuschauer": zuschauer(), "adresse_port": HLS_PORT},
        "benachrichtigung": melder.letzte,
        "fernseher": [fernseher_status(t) for t in e["fernseher"]],
        "ha": {"ok": zustand["ha_fehler"] is None, "fehler": zustand["ha_fehler"], "url": e["ha"]["url"],
               "code": (zustand.get("ha_fehler_code") or (None, None))[0], "detail": (zustand.get("ha_fehler_code") or (None, None))[1]},
        "liste": streams.status, "anzahl_in_rotation": len(streams.liste),
        # Zeiten als Zahlen – den Text setzt die Verwaltung in ihrer Sprache
        "aufgaben": [{"name": "streamliste", "alle_s": 300},
                     {"name": "suche", "wann": e["suche"]["uhrzeit"] if e["suche"]["aktiv"] else None,
                      "zuletzt": streams.status.get("suche")},
                     {"name": "wache", "alle_s": 10, "nur_stream": True}],
    }


def fernseher_status(t):
    w = zustand["wache"].get(t["id"])
    sender = next((x["name"] for x in einst()["radio"]["sender"] if x["id"] == t["radio_sender"]), None)
    return {"id": t["id"], "name": t["name"], "laeuft": kette_laeuft(t["id"]), "wache": w,
            "aktuell": {"video_id": w["id"], "name": next((x["name"] for x in streams.liste if x["video_id"] == w["id"]), w["id"])}
            if w else None, "ton": t["ton"], "sender": sender if t["ton"] == "radio" else None, "video": t["video"],
            "layout": L.aktuelles_layout(t, einst()["layouts"], time.strftime("%H:%M"))["name"],
            "radio_neu_verbunden": zustand.get("radio_neu", {}).get(t["id"], 0)}


def eigene_ip():
    """IP, mit der der Container HA erreicht – die muss HA als vertrauenswürdig kennen. Im Docker-Container sieht HA
    die IP des Hosts (NAT): die steht in SC_HOST_IP; ohne sie nimmt die Verwaltung die Adresse aus dem Browser."""
    if os.environ.get("SC_HOST_IP"):
        return os.environ["SC_HOST_IP"]
    if CONTAINER and not os.environ.get("SC_HOST_NETZ"):
        return None
    try:
        host = urllib.parse.urlparse(einst()["ha"]["url"]).hostname
        port = urllib.parse.urlparse(einst()["ha"]["url"]).port or 8123
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect((socket.gethostbyname(host), port))
            return s.getsockname()[0]
    except Exception:
        return None


def vorschau(tv_id):
    t = fernseher(tv_id)
    if not t or not kette_laeuft(t["id"]):
        return None
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "x11grab", "-video_size", "1920x1080", "-i", anzeige_nr(t),
                        "-frames:v", "1", "-vf", "scale=960:-1", "-f", "mjpeg", "-"], capture_output=True, timeout=15)
    return r.stdout if r.returncode == 0 and r.stdout else None


def schreib_wenn_anders(pfad, inhalt):
    try:
        if open(pfad).read() == inhalt:
            return
    except OSError:
        pass
    with open(pfad, "w") as f:
        f.write(inhalt)


def render_schreiben(e):
    """Je Fernseher die Werte für tv-render.sh (wirken beim nächsten Start seiner Kette) und die MediaMTX-Pfade
    (MediaMTX lädt die Datei bei Änderung selbst neu)."""
    pfade = ""
    for t in e["fernseher"]:
        k = zustand.get("kodierung") or {}
        software = k.get("art") == "software"           # ohne nutzbare Grafik: H.264 in Full HD per CPU
        aus = "3840 2160" if t["aufloesung"] == 2160 and not software else "1920 1080"
        schreib_wenn_anders(os.path.join(DATEN, f"render-{t['id']}.env"),
                            f"DISP={anzeige_nr(t)}\nDEVPORT={wache.BASIS_PORT + t['nr']}\nAUSGABE=\"{aus}\"\nBITRATE={t['bitrate_mbit']}\n"
                            f"KODIERUNG={'software' if software else 'vaapi'}\n")
        pfade += (f"  {t['id']}:\n    runOnDemand: /opt/signagecast/render/tv-render.sh\n    runOnDemandRestart: yes\n"
                  f"    runOnDemandStartTimeout: 40s\n    runOnDemandCloseAfter: {e['stream']['abschalten_s']}s\n")
    # Kameras (Datenquellen der Art „video“, RTSP/HLS): MediaMTX holt sie nur, solange jemand schaut; lesen darf sie
    # nur der Container selbst (siehe authInternalUsers in render/mediamtx.yml)
    for q in e.get("quellen", []):
        if q["art"] == "video" and q["aktiv"] and Q.video_format(q) in ("rtsp", "hls"):
            pfade += (f"  cam_{q['id']}:\n    source: {json.dumps(q['url'])}\n    sourceOnDemand: yes\n"
                      f"    sourceOnDemandStartTimeout: 15s\n    sourceOnDemandCloseAfter: 20s\n")
    try:
        if os.path.exists(MEDIAMTX_YML):
            vorlage = open(MEDIAMTX_VORLAGE).read().replace("hlsAddress: :8888", f"hlsAddress: :{HLS_PORT}")
            schreib_wenn_anders(MEDIAMTX_YML, vorlage.replace("{PFADE}", pfade.rstrip("\n")))
    except OSError:
        pass


def kette_neu_starten(tv_id):
    # Das Startskript des Fernsehers beenden (räumt Browser, ffmpeg und Xvfb auf); MediaMTX startet neu, solange jemand schaut
    try:
        pid = int(open(os.path.join(DATEN, f"kette-{tv_id}.skript")).read())
        os.kill(pid, 2)
        return True
    except (OSError, ValueError):
        return False


def devport(tv_id):
    t = fernseher(tv_id)
    return wache.BASIS_PORT + t["nr"] if t else None


# ---------- Sicherung / Profil ----------
SICHERUNGEN = os.path.join(DATEN, "sicherungen")
MEDIEN = os.path.join(DATEN, "medien")
hochladen = MED.Hochladen(MEDIEN)
MEDIEN_SICHERUNG_MAX = 200 * 1024 * 1024        # Videos nur in die Sicherung, solange alle Medien zusammen darunter bleiben


def sicherung(mit_geheimnissen=False):
    e = einst()
    if not mit_geheimnissen:              # Standard: ohne API-Schlüssel/Passwörter (Datei kann weitergegeben werden)
        e = dict(e, quellen=Q.ohne_geheimnisse(e["quellen"]), sicherung=dict(e["sicherung"], passwort=""),
                 webhook=dict(e["webhook"], token=""), benachrichtigung=bn_geheim(e["benachrichtigung"], lambda w: ""))
    return {"art": "signagecast-sicherung", "version": 1, "erstellt": time.strftime("%Y-%m-%d %H:%M"),
            "mit_geheimnissen": mit_geheimnissen, "einstellungen": e, "streams": streams.alle(), "strikes": streams.strikes()}


def sicherung_zip(mit_geheimnissen, passwort=None):
    """Komplette Sicherung als ZIP: sicherung.json (wie bisher) + Bilder + Verlauf (+ Passwort der Verwaltung im Docker-
    Betrieb). Mit Zugangsdaten nur mit starkem Passwort (AES-256)."""
    if mit_geheimnissen and not passwort:
        raise M.Meldung("sich_geheim_ohne_pw")
    if passwort:
        S.passwort_pruefen(passwort)
    dateien = {"sicherung.json": json.dumps(sicherung(mit_geheimnissen), ensure_ascii=False, indent=1).encode()}
    try:
        for n in os.listdir(BILDER):
            if S.BILD.fullmatch(n):
                dateien[f"bilder/{n}"] = open(os.path.join(BILDER, n), "rb").read()
    except OSError:
        pass
    if qn.verlauf:
        with qn.verlauf.sperre:
            dateien["verlauf.json"] = json.dumps(qn.verlauf.reihen).encode()
    # eigene Medien: Bilder immer, Videos nur bis MEDIEN_SICHERUNG_MAX insgesamt (sonst wird die ZIP unhandlich)
    ausgelassen, summe = [], 0
    for m in sorted(einst()["medien"], key=lambda x: x["art"] != "bild"):
        p = os.path.join(MEDIEN, m["datei"])
        if not os.path.exists(p) or f"medien/{m['datei']}" in dateien:
            continue
        g = os.path.getsize(p)
        if m["art"] == "video" and summe + g > MEDIEN_SICHERUNG_MAX:
            ausgelassen.append(m["name"])
            continue
        summe += g
        dateien[f"medien/{m['datei']}"] = open(p, "rb").read()
    vw = os.path.join(os.path.dirname(E.PFAD), "verwaltung.json")
    if mit_geheimnissen and CONTAINER and os.path.exists(vw):
        dateien["verwaltung.json"] = open(vw, "rb").read()
    dateien["manifest.json"] = json.dumps({"art": S.ART, "version": VERSION, "erstellt": time.strftime("%Y-%m-%d %H:%M"),
                                           "mit_geheimnissen": bool(mit_geheimnissen), "verschluesselt": bool(passwort),
                                           "medien_ausgelassen": ausgelassen,
                                           "dateien": sorted(dateien)}, indent=1).encode()
    return S.erstellen(dateien, passwort)


def sicherung_zip_einspielen(roh, passwort=None, mit_strikes=True):
    dateien = S.lesen(roh, passwort)
    d = json.loads(dateien["sicherung.json"])
    einspielen(d, mit_strikes=mit_strikes)
    os.makedirs(BILDER, exist_ok=True)
    for name, inhalt in dateien.items():
        if name.startswith("bilder/") and S.BILD.fullmatch(name[7:]):
            with open(os.path.join(BILDER, name[7:]), "wb") as f:
                f.write(inhalt)
    os.makedirs(MEDIEN, exist_ok=True)
    for name, inhalt in dateien.items():
        if name.startswith("medien/") and re.fullmatch(r"[0-9a-f]{16}\.(jpg|png|mp4|webm)", name[7:]):
            with open(os.path.join(MEDIEN, name[7:]), "wb") as f:
                f.write(inhalt)
    if "verlauf.json" in dateien and qn.verlauf:
        reihen = json.loads(dateien["verlauf.json"])
        with qn.verlauf.sperre:
            qn.verlauf.reihen = {k: v for k, v in reihen.items() if isinstance(v, list)}
        qn.verlauf.speichern()
    if "verwaltung.json" in dateien and CONTAINER:
        vw = os.path.join(os.path.dirname(E.PFAD), "verwaltung.json")
        fd = os.open(vw, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(dateien["verwaltung.json"])
    return json.loads(dateien["manifest.json"])


def sicherung_schleife():
    """Automatische Sicherung nach Plan (täglich/wöchentlich zur Uhrzeit), abgelegt im Container, die letzten N bleiben."""
    erledigt = None
    while True:
        si = einst()["sicherung"]
        jetzt = time.localtime()
        heute = time.strftime("%Y-%m-%d", jetzt)
        faellig = si["plan"] != "aus" and time.strftime("%H:%M", jetzt) == si["uhrzeit"] and erledigt != heute \
            and (si["plan"] == "taeglich" or jetzt.tm_wday == si["wochentag"])
        if faellig:
            erledigt = heute
            try:
                geheim = si["mit_geheimnissen"]
                roh = sicherung_zip(geheim, si["passwort"] if geheim else None)
                zustand["sicherung_auto"] = {"zeit": time.strftime("%Y-%m-%d %H:%M"),
                                             "name": S.ablegen(SICHERUNGEN, roh, True, geheim, si["behalten"]), "fehler_m": None}
            except Exception as ex:
                zustand["sicherung_auto"] = {"zeit": time.strftime("%Y-%m-%d %H:%M"), "fehler": str(ex)[:200], "fehler_m": M.als_dict(ex)}
        time.sleep(20)


def einspielen(d, mit_strikes=True):
    if not isinstance(d, dict) or d.get("art") not in ("signagecast-sicherung", "signagecast-profil",
                                                         "tv-stream-sicherung", "tv-stream-profil"):   # alte Namen (bis 0.4.1)
        raise E.Fehler("Keine SignageCast-Sicherung bzw. kein Profil")
    if "einstellungen" in d:
        neu = d["einstellungen"]
        if isinstance(neu, dict) and isinstance(neu.get("webhook"), dict) and not neu["webhook"].get("token"):
            neu["webhook"]["token"] = einst()["webhook"]["token"]
        bn_behalten(neu, auch_leer=True)
        if isinstance(neu, dict) and isinstance(neu.get("sicherung"), dict) and not neu["sicherung"].get("passwort"):
            neu["sicherung"]["passwort"] = einst()["sicherung"]["passwort"]     # ohne Geheimnisse: vorhandenes behalten
        if isinstance(neu, dict) and isinstance(neu.get("quellen"), list):
            # Sicherung ohne Geheimnisse: leere geheime Werte aus der laufenden Einrichtung übernehmen
            for q in neu["quellen"]:
                for k in q.get("kopf") or []:
                    if k.get("geheim") and not k.get("wert"):
                        k["wert"] = Q.MASKE
            Q.demaskieren(neu["quellen"], einst()["quellen"])
        zustand["einstellungen"] = E.speichern(E.zusammenfuehren(einst(), neu))
        render_schreiben(einst())
    if "streams" in d:
        s = d["streams"]
        if not isinstance(s.get("streams"), dict):
            raise E.Fehler("Streamliste fehlt")
        for sid, x in s["streams"].items():
            if not (ID.fullmatch(sid) or re.fullmatch(r"UC[\w-]{22}", sid)):
                raise E.Fehler(f"ungültige ID {sid!r}")
        streams._speichern({"streams": s["streams"], "abgelehnt": [a for a in s.get("abgelehnt", []) if isinstance(a, str)]})
    if mit_strikes and isinstance(d.get("strikes"), dict):
        from streams import STRIKES, schreib
        schreib(STRIKES, d["strikes"])
    neu_liste.set()


def datei_mit_range(h, pfad, typ):
    try:
        groesse = os.path.getsize(pfad)
        f = open(pfad, "rb")
    except OSError:
        return h.antwort(404, {"ok": False})
    with f:
        start, ende = 0, groesse - 1
        m = re.fullmatch(r"bytes=(\d*)-(\d*)", h.headers.get("Range", "") or "")
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                start = int(m.group(1)); ende = int(m.group(2)) if m.group(2) else groesse - 1
            else:
                start = max(0, groesse - int(m.group(2)))
            if start >= groesse:
                h.send_response(416); h.send_header("Content-Range", f"bytes */{groesse}"); h.end_headers(); return
            ende = min(ende, groesse - 1)
            h.send_response(206); h.send_header("Content-Range", f"bytes {start}-{ende}/{groesse}")
        else:
            h.send_response(200)
        h.send_header("Content-Type", typ); h.send_header("Accept-Ranges", "bytes")
        h.send_header("Content-Length", str(ende - start + 1)); h.send_header("Cache-Control", "no-cache")
        h.end_headers()
        f.seek(start)
        rest = ende - start + 1
        try:
            while rest > 0:
                teil = f.read(min(1 << 20, rest))
                if not teil:
                    break
                h.wfile.write(teil); rest -= len(teil)
        except OSError:
            pass


def mjpeg_anfrage(q):
    """Adresse und Kopfzeilen für eine MJPEG-Kamera; Benutzer:Passwort in der Adresse -> Basic-Anmeldung."""
    kopf = {"User-Agent": Q.UA}
    kopf.update({k["name"]: k["wert"] for k in q["kopf"]})
    url, pw = Q._url_passwort(q["url"], "")
    if pw is not None:
        t = urllib.parse.urlsplit(q["url"])
        kopf["Authorization"] = "Basic " + base64.b64encode(f"{urllib.parse.unquote(t.username or '')}:{urllib.parse.unquote(pw)}".encode()).decode()
        url = urllib.parse.urlunsplit(t._replace(netloc=t.hostname + (f":{t.port}" if t.port else "")))
    return url, kopf


def mjpeg_weiterleiten(h, qid):
    q = next((x for x in einst()["quellen"] if x["id"] == qid and x["art"] == "video" and x["aktiv"]), None)
    if not q or Q.video_format(q) != "mjpeg":
        return h.antwort(404, {"ok": False})
    url, kopf = mjpeg_anfrage(q)
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=kopf), timeout=10)
    except Exception:
        return h.antwort(502, {"ok": False})
    with r:
        h.send_response(200)
        h.send_header("Content-Type", r.headers.get("Content-Type", "multipart/x-mixed-replace"))
        h.send_header("Cache-Control", "no-store")
        h.end_headers()
        try:
            while True:
                teil = r.read1(65536) if hasattr(r, "read1") else r.read(65536)
                if not teil:
                    break
                h.wfile.write(teil)
        except (OSError, ValueError):
            pass


def video_pruefen(q):
    """Kamera testen: RTSP/HLS mit ffprobe (Codec, Größe), MJPEG mit einem ersten Abruf."""
    f = Q.video_format(q)
    if f == "mjpeg":                              # endloser Stream: nur den Anfang lesen
        url, kopf = mjpeg_anfrage(q)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=kopf), timeout=10) as r:
                art, anfang = r.headers.get("Content-Type", ""), r.read(65536)
        except urllib.error.HTTPError as ex:
            raise Q.Fehler("kam_http", code=ex.code, grund=ex.reason)
        except Exception as ex:
            raise Q.Fehler("kam_nicht_erreichbar", d=ex)
        if not (art.startswith("multipart/") or art.startswith("image/") or b"\xff\xd8\xff" in anfang):
            raise Q.Fehler("kein_mjpeg", typ=art or "–")
        return {"format": f, "content_type": art, "erste_bytes": len(anfang)}
    arg = ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height", "-of", "json"]
    if f == "rtsp":
        arg += ["-rtsp_transport", "tcp"]
    try:
        r = subprocess.run(arg + ["-i", q["url"]], capture_output=True, text=True, timeout=25)
    except subprocess.TimeoutExpired:
        raise Q.Fehler("kam_zeit")
    if r.returncode:
        raise Q.Fehler("kam_fehler", d=(r.stderr.strip().splitlines() or ["–"])[-1].replace(q["url"], "…"))
    streams_ = json.loads(r.stdout or "{}").get("streams", [])
    d = {"format": f, "streams": streams_}
    if any(x.get("codec_name") in ("hevc", "h265") for x in streams_):
        d["hinweis"] = "H.265: kann Chromium im Container nicht dekodieren – an der Kamera H.264 einstellen"
    return d


def einbettbar(url):
    """Erlaubt die Seite das Einbetten (X-Frame-Options / CSP frame-ancestors)? Es wird nichts umgangen."""
    try:
        anf = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SignageCast"})
        with urllib.request.urlopen(anf, timeout=10) as r:
            xfo = (r.headers.get("X-Frame-Options") or "").lower()
            csp = (r.headers.get("Content-Security-Policy") or "").lower()
    except urllib.error.HTTPError as ex:
        return {"einbettbar": None, "grund": f"HTTP {ex.code}"}
    except Exception as ex:
        return {"einbettbar": None, "grund": str(ex)[:200]}
    m = re.search(r"frame-ancestors([^;]*)", csp)
    if m and "*" not in m.group(1):
        return {"einbettbar": False, "grund": "Content-Security-Policy frame-ancestors" + m.group(1)[:120]}
    if xfo in ("deny", "sameorigin"):
        return {"einbettbar": False, "grund": f"X-Frame-Options: {xfo.upper()}"}
    return {"einbettbar": True, "grund": ""}


# ---------- HTTP ----------
class Bearbeiter(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=WWW, **k)

    def log_message(self, *a):
        pass

    def antwort(self, code, obj, typ="application/json; charset=utf-8"):
        b = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def koerper(self, maxlen=12_000_000):
        n = int(self.headers.get("Content-Length", "0") or 0)
        if n > maxlen:
            raise E.Fehler("zu groß")
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def api_erlaubt(self):
        # Nur die Verwaltung (Cockpit) schickt diesen Kopf; Browser-Seiten anderer Herkunft können ihn ohne
        # CORS-Freigabe nicht setzen – so kann z. B. eingebetteter Inhalt die API nicht aufrufen.
        return self.headers.get("X-SignageCast") == "1"

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == "/daten.json":
            tv = (urllib.parse.parse_qs(p.query).get("tv") or [None])[0]
            return self.antwort(200, tv_daten(tv))
        m = re.fullmatch(r"/kamera/(camera\.[a-z0-9_]+)\.jpg", p.path)
        if m:                                     # für die TV-Seite (nur Kameras aus den Layouts)
            try:
                bild = kamera_bild(m.group(1))
            except Exception:
                bild = None
            return self.antwort(200, bild, "image/jpeg") if bild else self.antwort(404, {"ok": False})
        m = re.fullmatch(r"/radio/([a-z][a-z0-9]{0,11})/([a-z0-9]{4,12})", p.path)
        if m:                                     # Radio mit Puffer (für die TV-Seite)
            return radio_weiterleiten(self, m.group(1), m.group(2))
        m = re.fullmatch(r"/medien/([0-9a-f]{16})\.(jpg|png|mp4|webm)", p.path)
        if m:                                     # eigene Medien für die TV-Seite (mit Range für Videos)
            typ = {"jpg": "image/jpeg", "png": "image/png", "mp4": "video/mp4", "webm": "video/webm"}[m.group(2)]
            return datei_mit_range(self, os.path.join(MEDIEN, f"{m.group(1)}.{m.group(2)}"), typ)
        m = re.fullmatch(r"/einspieler/([a-z0-9]{4,12})\.mp4", p.path)
        if m:                                     # vorab geladener Einspieler (mit Range, damit der Browser springen kann)
            return einspieler_ausliefern(self, m.group(1))
        m = re.fullmatch(r"/qvideo/([a-z0-9_]{2,16})", p.path)
        if m:                                     # MJPEG-Kamera durchreichen (Zugangsdaten bleiben im Container)
            return mjpeg_weiterleiten(self, m.group(1))
        m = re.fullmatch(r"/qbild/([a-z0-9_]{2,16})", p.path)
        if m:                                     # Bild aus einer Datenquelle (für die TV-Seite)
            q = next((x for x in einst()["quellen"] if x["id"] == m.group(1)), None)
            pfad = (urllib.parse.parse_qs(p.query).get("p") or [""])[0]
            b = None
            if q and q["art"] == "bild":
                b = qn.daten(q["id"])
            elif q and pfad and qn.daten(q["id"]) is not None:
                b = qn.bild_aus_url(q, Q.wert_bei(qn.daten(q["id"]), pfad))
            return self.antwort(200, b["bild"], b["typ"]) if b else self.antwort(404, {"ok": False})
        m = re.fullmatch(r"/bild/([0-9a-f]{16}\.(jpg|png))", p.path)
        if m:
            try:
                return self.antwort(200, open(os.path.join(BILDER, m.group(1)), "rb").read(), "image/" + ("jpeg" if m.group(2) == "jpg" else "png"))
            except OSError:
                return self.antwort(404, {"ok": False})
        if p.path.startswith("/api/"):
            if not self.api_erlaubt():
                return self.antwort(403, {"ok": False})
            return self.api_get(p.path, urllib.parse.parse_qs(p.query))
        return super().do_GET()

    def api_get(self, pfad, q):
        if pfad == "/api/status":
            return self.antwort(200, status())
        if pfad == "/api/einstellungen":
            return self.antwort(200, {"einstellungen": einst_aussen(), "kategorien": E.KATEGORIEN, "stufen": E.STUFEN,
                                      "bausteine": {t: {k: std for k, (_, std) in o.items()} for t, o in L.TYPEN.items()},
                                      "schriften": L.SCHRIFTEN, "operatoren": L.OPERATOREN, "raster": [L.SPALTEN, L.ZEILEN],
                                      "ausrichtungen": L.AUSRICHTUNGEN, "stile": L.STILE, "tageszeiten": L.TAGESZEITEN,
                                      "wechsel": L.WECHSEL})
        if pfad == "/api/einspieler":
            return self.antwort(200, {"einspieler": einst()["einspieler"], "stand": zustand.get("einspieler", {})})
        if pfad == "/api/zeitzonen":
            import zoneinfo
            return self.antwort(200, {"zeitzonen": sorted(zoneinfo.available_timezones()), "system": auto_zeitzone()})
        if pfad == "/api/vorlagen":
            return self.antwort(200, {"vorlagen": L.vorlagen()})
        if pfad == "/api/vorschau/daten":
            return self.antwort(200, tv_daten((q.get("tv") or [None])[0]))
        if pfad == "/api/streams":
            return self.antwort(200, streams.uebersicht())
        if pfad == "/api/ha/test":
            return self.antwort(200, dict(ha.testen(), eigene_ip=eigene_ip()))
        if pfad == "/api/ha/einrichtung":
            return self.antwort(200, {"eigene_ip": eigene_ip(), "url": einst()["ha"]["url"], "stream_port": HLS_PORT})
        if pfad == "/api/ha/entitaeten":
            try:
                liste = [{"id": s["entity_id"], "name": s.get("attributes", {}).get("friendly_name", ""),
                          "einheit": s.get("attributes", {}).get("unit_of_measurement", ""), "wert": s.get("state")}
                         for s in ha.get("/api/states")]
                return self.antwort(200, {"ok": True, "entitaeten": sorted(liste, key=lambda x: x["id"])})
            except Exception as ex:
                return self.antwort(200, {"ok": False, "fehler": str(ex)})
        if pfad == "/api/radio/vorschlaege":
            try:
                st = einst()["standort"]
                return self.antwort(200, dict(radio.vorschlaege(st["breite"], st["laenge"], einst()["radio"]["region_woerter"]), ok=True))
            except Exception as ex:
                return self.antwort(200, {"ok": False, "fehler": str(ex)})
        if pfad == "/api/radio/suche":
            try:
                return self.antwort(200, {"ok": True, "sender": radio.suchen((q.get("name") or [""])[0])})
            except Exception as ex:
                return self.antwort(200, {"ok": False, "fehler": str(ex)})
        if pfad == "/api/ort/suche":
            try:
                return self.antwort(200, {"ok": True, "orte": radio.ort_suchen((q.get("q") or [""])[0], einst()["sprache"])})
            except Exception as ex:
                return self.antwort(200, {"ok": False, "fehler": str(ex)})
        if pfad == "/api/vorschau.jpg":
            bild = vorschau((q.get("tv") or [None])[0])
            return self.antwort(200, bild, "image/jpeg") if bild else self.antwort(404, {"ok": False})
        if pfad == "/api/sicherung":
            return self.antwort(200, sicherung((q.get("geheim") or ["0"])[0] == "1"))
        if pfad == "/api/updates":
            return self.antwort(200, update_info())
        if pfad == "/api/sicherungen":
            return self.antwort(200, {"ok": True, "liste": S.liste(SICHERUNGEN), "auto": zustand.get("sicherung_auto"),
                                      "aes": S.pyzipper is not None})
        if pfad == "/api/sicherung/datei":
            name = (q.get("name") or [""])[0]
            if not S.NAME.fullmatch(name) or not os.path.exists(os.path.join(SICHERUNGEN, name)):
                return self.antwort(404, {"ok": False})
            return self.antwort(200, open(os.path.join(SICHERUNGEN, name), "rb").read(), "application/zip")
        if pfad == "/api/quellen/status":
            return self.antwort(200, {"ok": True, "status": qn.status()})
        if pfad == "/api/quellen/daten":
            qid = (q.get("id") or [""])[0]
            d = qn.daten(qid)
            if isinstance(d, dict) and "bild" in d and isinstance(d.get("bild"), bytes):
                d = {"bild": f"{d['typ']}, {d['groesse'] // 1024} KB"}
            st_ = qn.stand.get(qid) or {}
            return self.antwort(200, {"ok": d is not None, "daten": Q.gekuerzt(d), "fehler": st_.get("fehler"), "fehler_m": st_.get("fehler_m")})
        if pfad == "/api/wache":
            n = min(int((q.get("n") or ["60"])[0]), 2000)
            datei = os.path.join(wache.ORDNER, time.strftime("%Y-%m-%d") + ".jsonl")
            try:
                zeilen = open(datei).readlines()[-n:]
            except OSError:
                zeilen = []
            return self.antwort(200, [json.loads(z) for z in zeilen])
        return self.antwort(404, {"ok": False})

    def do_POST(self):
        p = urllib.parse.urlparse(self.path).path
        try:
            d = self.koerper(420_000_000 if p == "/api/sicherung/zip" else 12_000_000)
        except Exception:
            return self.antwort(400, {"ok": False, "fehler": "ungültige Anfrage"})
        m = re.fullmatch(r"/meldung/(strike|qualitaet)", p)
        if m:                                     # vom Player der TV-Seite
            vid = str(d.get("video_id", ""))
            if m.group(1) == "strike":
                ok = streams.strike(vid, str(d.get("grund", "")))
            else:
                ok = streams.qualitaet_melden(vid, str(d.get("stufe", "")), str(d.get("beste", "")), str(d.get("phase", "")))
            return self.antwort(200 if ok else 400, {"ok": ok})
        if not p.startswith("/api/") or not self.api_erlaubt():
            return self.antwort(403, {"ok": False})
        try:
            return self.antwort(200, dict(self.api_post(p, d) or {}, ok=True))
        except (E.Fehler, ValueError, KeyError, HAFehler) as ex:
            # 200 mit ok=false: die Verwaltung zeigt den Text direkt an
            m = M.als_dict(ex)
            return self.antwort(200, {"ok": False, "fehler": str(ex).strip("'"), "code": m["code"], "p": m["p"]})

    def api_post(self, p, d):
        if p == "/api/einstellungen" and isinstance(d.get("quellen"), list):
            Q.demaskieren(d["quellen"], einst()["quellen"])
        if p == "/api/einstellungen" and isinstance(d.get("webhook"), dict) and d["webhook"].get("token") == Q.MASKE:
            d["webhook"]["token"] = einst()["webhook"]["token"]
        if p == "/api/einstellungen":
            bn_behalten(d)
        if p == "/api/benachrichtigung/test":        # Testnachricht über einen Kanal (gespeicherte Einstellungen)
            kanal = d.get("kanal")
            if kanal not in ("telegram", "email", "ha"):
                raise ValueError("unbekannter Kanal")
            f = BN.senden(einst()["benachrichtigung"], ha.post, "SignageCast: Test",
                          f"Testnachricht von SignageCast {VERSION} ({socket.gethostname()}).", nur=kanal)[kanal]
            if f:
                raise ValueError(f)
            return {}
        if p == "/api/webhook/neu":                 # neuen Schlüssel erzeugen – nur in dieser Antwort im Klartext
            import secrets
            token = secrets.token_urlsafe(24)
            zustand["einstellungen"] = E.speichern(E.zusammenfuehren(einst(), {"webhook": {"token": token, "aktiv": True}}))
            return {"token": token, "port": WEBHOOK_PORT, "einstellungen": einst_aussen()}
        if p == "/api/einstellungen" and isinstance(d.get("sicherung"), dict) and d["sicherung"].get("passwort") == Q.MASKE:
            d["sicherung"]["passwort"] = einst()["sicherung"]["passwort"]
        if p == "/api/medien/teil":
            hochladen.teil(str(d.get("kennung", "")), int(d.get("nr", -1)), base64.b64decode(str(d.get("daten", "")), validate=False))
            if not d.get("fertig"):
                return {}
            art, datei, dauer = hochladen.fertig(str(d["kennung"]))
            medium = {"id": MED.neue_kennung(), "name": str(d.get("name") or datei)[:60], "art": art, "datei": datei,
                      "dauer_s": dauer, "aktiv": True}
            zustand["einstellungen"] = E.speichern(E.zusammenfuehren(einst(), {"medien": einst()["medien"] + [medium]}))
            return {"medium": medium, "einstellungen": einst_aussen()}
        if p == "/api/medien/loeschen":
            alle = einst()["medien"]
            weg = next((m for m in alle if m["id"] == d.get("id")), None)
            if not weg:
                raise M.Meldung("med_unbekannt")
            rest = [m for m in alle if m["id"] != weg["id"]]
            zustand["einstellungen"] = E.speichern(E.zusammenfuehren(einst(), {"medien": rest}))
            if not any(m["datei"] == weg["datei"] for m in rest):
                try:
                    os.remove(os.path.join(MEDIEN, weg["datei"]))
                except OSError:
                    pass
            return {"einstellungen": einst_aussen()}
        if p == "/api/updates/anfrage":
            update_anfragen(str(d.get("aktion", "")))
            return {}
        if p == "/api/sicherung/erstellen":
            geheim = bool(d.get("mit_geheimnissen"))
            roh = sicherung_zip(geheim, str(d.get("passwort") or "") or None)
            return {"name": S.ablegen(SICHERUNGEN, roh, False, geheim)}
        if p == "/api/sicherung/loeschen":
            name = str(d.get("name", ""))
            if not S.NAME.fullmatch(name):
                raise M.Meldung("sich_name")
            os.remove(os.path.join(SICHERUNGEN, name))
            return {}
        if p == "/api/sicherung/zip":
            roh = base64.b64decode(str(d.get("daten", "")).split(",")[-1], validate=False)
            return {"manifest": sicherung_zip_einspielen(roh, str(d.get("passwort") or "") or None, bool(d.get("strikes")))}
        if p == "/api/quellen/curl":
            try:
                return Q.aus_curl(d.get("befehl", ""))
            except Q.Fehler:
                raise                             # Meldung mit Kennung bleibt erhalten
        if p == "/api/quellen/test":
            try:
                roh = [d.get("quelle") or {}]
                Q.demaskieren(roh, einst()["quellen"])
                q = Q.pruefen(roh)[0]
                if q["art"] == "video":
                    t0 = time.time()
                    v = video_pruefen(q)
                    return {"dauer_ms": round((time.time() - t0) * 1000), "daten": v}
                daten, ms = qn.abrufen(q)
            except Q.Fehler:
                raise                             # Meldung mit Kennung bleibt erhalten
            if q["art"] == "bild":
                return {"ok": True, "dauer_ms": ms, "daten": {"bild": f"{daten['typ']}, {daten['groesse'] // 1024} KB"},
                        "bild": f"data:{daten['typ']};base64,{base64.b64encode(daten['bild']).decode()}" if daten["groesse"] < 1_500_000 else None}
            return {"ok": True, "dauer_ms": ms, "daten": Q.gekuerzt(daten)}
        if p == "/api/webseite/pruefen":
            return einbettbar(str(d.get("url", "")))
        if p == "/api/quellen/jetzt":
            s = qn.stand.get(str(d.get("id", "")))
            if s:
                s["naechster"] = 0
                qn.neu.set()
            return {}
        if p == "/api/einstellungen":
            zustand["einstellungen"] = E.speichern(E.zusammenfuehren(einst(), d))
            render_schreiben(einst())
            neu_liste.set()
            einspieler_neu.set()
            zeit_neu.set()
            wetter_neu.set()
            qn.neu.set()
            return {"einstellungen": einst_aussen()}
        if p == "/api/streams":
            s = streams.hinzufuegen(str(d.get("link", "")), d.get("name") or None, d.get("kategorie", "neu"),
                                    d.get("breite"), d.get("laenge"))
            neu_liste.set()
            return {"stream": s}
        m = re.fullmatch(r"/api/streams/([\w-]{11}|UC[\w-]{22})(/[a-z-]+)?", p)
        if m:
            sid, aktion = m.group(1), m.group(2)
            if not aktion:
                s = streams.aendern(sid, d)
            elif aktion == "/entfernen":
                s = streams.entfernen(sid, ablehnen=bool(d.get("ablehnen")))
            elif aktion == "/strikes-zuruecksetzen":
                s = streams.strikes_zuruecksetzen(d.get("video_id") or sid)
            elif aktion == "/zeigen":
                x = streams.alle()["streams"].get(sid)
                if not x:
                    raise KeyError(sid)
                tv = d.get("tv") if fernseher(d.get("tv")) else None
                streams.vorrang = {"video_id": d.get("video_id") or sid, "name": x["name"], "tv": tv,
                                   "bis": time.time() + einst()["video"]["takt_min"] * 60}
                s = streams.vorrang
            else:
                raise KeyError(aktion)
            neu_liste.set()
            return {"stream": s}
        m = re.fullmatch(r"/api/abgelehnt/([\w-]{11}|UC[\w-]{22})/freigeben", p)
        if m:
            with_d = streams.alle()
            with_d["abgelehnt"] = [a for a in with_d["abgelehnt"] if a != m.group(1)]
            streams._speichern(with_d)
            return {}
        if p == "/api/suche/starten":
            return {"suche": streams.suchen()}
        if p == "/api/liste/neu":
            neu_liste.set()
            return {}
        if p == "/api/radio/sender":
            url = radio.adresse_pruefen(d.get("url", ""))
            e = einst()
            sender = e["radio"]["sender"] + [{"id": radio.neue_id(), "name": str(d.get("name") or "").strip()[:60] or url[:60], "url": url}]
            zustand["einstellungen"] = E.speichern(E.zusammenfuehren(e, {"radio": {"sender": sender}}))
            return {"sender": sender[-1], "einstellungen": einst_aussen()}
        m = re.fullmatch(r"/api/einspieler/([a-z0-9]{4,12})/jetzt", p)
        if m:                                     # zum Testen sofort zeigen (die TV-Seiten holen es mit den nächsten Daten)
            if m.group(1) not in zustand.get("einspieler", {}):
                einspieler_neu.set()
                raise M.Meldung("ep_nicht_bereit")
            zustand["einspieler_jetzt"] = {"id": m.group(1), "nr": int(time.time()), "bis": time.time() + 40}
            return {}
        if p == "/api/bilder":
            return {"bild": bild_speichern(d.get("daten", ""))}
        if p == "/api/radio/playlist":
            # Inhalt einer M3U/PLS-Datei: jeden Eintrag prüfen (parallel) und die gültigen als Sender übernehmen
            from concurrent.futures import ThreadPoolExecutor
            eintraege = radio.playlist_lesen(d.get("text", ""))

            def pruefen(nu):
                try:
                    return nu[0], radio.adresse_pruefen(nu[1]), None
                except ValueError as ex:
                    return nu[0], nu[1], str(ex)
            with ThreadPoolExecutor(max_workers=4) as pool:
                ergebnis = list(pool.map(pruefen, eintraege))
            e = einst()
            vorhanden = {x["url"] for x in e["radio"]["sender"]}
            neu = [{"id": radio.neue_id(), "name": (n or u)[:60], "url": u} for n, u, f in ergebnis if not f and u not in vorhanden]
            if neu:
                zustand["einstellungen"] = E.speichern(E.zusammenfuehren(e, {"radio": {"sender": e["radio"]["sender"] + neu}}))
            return {"neu": [x["name"] for x in neu], "fehler": [f"{n or u}: {f}" for n, u, f in ergebnis if f],
                    "doppelt": sum(1 for n, u, f in ergebnis if not f and u in vorhanden), "einstellungen": einst_aussen()}
        m = re.fullmatch(r"/api/radio/sender/([a-z0-9]{4,12})", p)
        if m:                                     # Sender bearbeiten: Name und/oder Adresse (neue Adresse wird geprüft)
            e = einst()
            alt = next((x for x in e["radio"]["sender"] if x["id"] == m.group(1)), None)
            if not alt:
                raise KeyError("Sender nicht gefunden")
            url = alt["url"]
            if str(d.get("url", "")).strip() and str(d["url"]).strip() != alt["url"]:
                url = radio.adresse_pruefen(d["url"])
            name = str(d.get("name") or "").strip()[:60] or alt["name"]
            sender = [dict(x, name=name, url=url) if x["id"] == alt["id"] else x for x in e["radio"]["sender"]]
            zustand["einstellungen"] = E.speichern(E.zusammenfuehren(e, {"radio": {"sender": sender}}))
            return {"einstellungen": einst_aussen()}
        m = re.fullmatch(r"/api/radio/sender/([a-z0-9]{4,12})/entfernen", p)
        if m:
            e = einst()
            sender = [x for x in e["radio"]["sender"] if x["id"] != m.group(1)]
            tvs = [dict(t, radio_sender="" if t["radio_sender"] == m.group(1) else t["radio_sender"]) for t in e["fernseher"]]
            zustand["einstellungen"] = E.speichern(E.zusammenfuehren(e, {"radio": {"sender": sender}, "fernseher": tvs}))
            return {"einstellungen": einst_aussen()}
        if p in ("/api/aktion/seite-neu-laden", "/api/aktion/kette-neu-starten"):
            ziele = [t for t in einst()["fernseher"] if not d.get("tv") or t["id"] == d.get("tv")]
            if p.endswith("seite-neu-laden"):
                erg = []
                for t in ziele:
                    try:
                        erg.append(wache.seite_neu_laden(wache.BASIS_PORT + t["nr"]))
                    except Exception:
                        erg.append(False)
                return {"erledigt": any(erg)}
            return {"erledigt": any([kette_neu_starten(t["id"]) for t in ziele])}
        if p == "/api/sicherung":
            einspielen(d, mit_strikes=bool(d.get("strikes")))
            return {}
        raise KeyError(p)


def main():
    os.makedirs(DATEN, exist_ok=True)
    render_schreiben(einst())
    zeitzone_setzen()

    def beenden(*_):
        # Verlauf (Diagramme) beim Stoppen/Update sichern – sonst fehlen bis zu 5 min Werte
        if qn.verlauf:
            qn.verlauf.speichern()
        os._exit(0)
    signal.signal(signal.SIGTERM, beenden)
    signal.signal(signal.SIGINT, beenden)

    def kodierung():
        zustand["kodierung"] = HW.pruefen()
        k = zustand["kodierung"]
        print(f"Kodierung: {k['art']} ({k['codec']}, bis {k['max_hoehe']}p)" + (f" – {k['grund']}" if k.get("grund") else ""), flush=True)
        render_schreiben(einst())
    threading.Thread(target=kodierung, daemon=True).start()
    try:
        webhook_server = ThreadingHTTPServer(("0.0.0.0", WEBHOOK_PORT), WebhookBearbeiter)
        threading.Thread(target=webhook_server.serve_forever, daemon=True).start()
    except OSError as f:
        print(f"Webhook-Port {WEBHOOK_PORT} nicht verfügbar: {f}", flush=True)
    if os.environ.get("SC_VERWALTUNG_PORT"):
        import verwaltung
        threading.Thread(target=verwaltung.starten, args=(int(os.environ["SC_VERWALTUNG_PORT"]),), daemon=True).start()
    for ziel in (ha_schleife, streams_schleife, suche_schleife, cpu_schleife, kalender_schleife, einspieler_schleife, update_schleife,
                 wetter_schleife, zeit_schleife, qn.schleife, verlauf_ha_schleife, sicherung_schleife,
                 update_auto_schleife, unwetter_schleife, benachrichtigung_schleife):
        threading.Thread(target=ziel, daemon=True).start()
    threading.Thread(target=wache.schleife, daemon=True,
                     args=(streams, zustand, lambda: [(t["id"], wache.BASIS_PORT + t["nr"]) for t in einst()["fernseher"]
                                                      if kette_laeuft(t["id"])])).start()
    ThreadingHTTPServer(("127.0.0.1", int(os.environ.get("SC_PORT", "8080"))), Bearbeiter).serve_forever()


if __name__ == "__main__":
    main()
