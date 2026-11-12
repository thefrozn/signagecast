#!/usr/bin/env python3
# SignageCast – Datendienst. Liefert die TV-Seite (www/) und ihre Daten, führt die Streamliste, sucht neue Streams,
# misst die Qualität (Wache) und bietet der Verwaltung (Cockpit-Erweiterung) eine kleine API.
# Lauscht nur auf 127.0.0.1:8080 – von außen ist nur der fertige Videostream (MediaMTX) und Cockpit erreichbar.
# Im Docker-/Podman-Container (SC_BETRIEB=container) gibt es kein Cockpit: dann liefert verwaltung.py die Verwaltung
# selbst aus (eigene Anmeldung, Port SC_VERWALTUNG_PORT) und reicht ihre Anfragen hierher weiter.
# Nur Python-Standardbibliothek.
import glob, json, os, re, secrets, shutil, signal, socket, ssl, subprocess, sys, threading, time, urllib.error, urllib.parse, urllib.request
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


class Server(ThreadingHTTPServer):
    """Wie ThreadingHTTPServer, aber ohne Traceback, wenn der Browser die Verbindung abbricht (z. B. eine lange Anfrage
    beim Beenden einer Kette) – das ist normal (seit 0.32.1). Andere Fehler werden wie bisher protokolliert."""
    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


class PultServer(Server):
    """Port des Pults/Webhooks (seit 0.40 auch MCP im Heimnetz): versteht http und https auf demselben Port. Ob eine
    Verbindung TLS spricht, steht im ersten Byte (0x16 = Handshake). Ohne Zertifikat (tls=None) nur http."""
    tls = None

    def finish_request(self, request, client_address):
        verpackt = None
        try:
            request.settimeout(120)
            if self.tls and request.recv(1, socket.MSG_PEEK) == b"\x16":
                request = verpackt = self.tls.wrap_socket(request, server_side=True)
        except (OSError, ValueError):
            return
        try:
            self.RequestHandlerClass(request, client_address, self)
        finally:
            if verpackt is not None:
                try:
                    verpackt.close()
                except OSError:
                    pass
import hardware as HW                         # noqa: E402
import meldung as M                           # noqa: E402
import sicherung as S                         # noqa: E402
import medien as MED                          # noqa: E402
import unwetter as UW                         # noqa: E402
import benachrichtigung as BN                 # noqa: E402
import durchsage as DS                        # noqa: E402
import quellen as Q                           # noqa: E402
import csvimport as CSV                       # noqa: E402
import webbild as WB                          # noqa: E402
import todo as TD                             # noqa: E402
import pdf as PDF                             # noqa: E402
import speicher as SP                         # noqa: E402
import galerie as GAL                         # noqa: E402
import player as PL                           # noqa: E402
import fernwartung as FW                      # noqa: E402
import netz as NZ                             # noqa: E402
import protokoll as PR                        # noqa: E402
import ausgabe as AG                          # noqa: E402
import kizugang as KZ                         # noqa: E402
import fernnetz as FN                         # noqa: E402
import mcp as MCP                             # noqa: E402
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

zustand = {"einstellungen": E.laden(), "kodier_fehler": {}, "probe": {}, "ha_teil": {"wetter": {}, "vorhersage": [], "werte": {}},
           "vorhersage": [], "vh_zeit": 0, "kalender": {}, "wache": {}, "cpu": None, "ha_fehler": None}
BILDER = os.path.join(DATEN, "bilder")
Q.DATEIEN = os.path.join(DATEN, "quelldateien")       # hochgeladene Dateien der Datenquellen (seit 0.26)
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
                benachrichtigung=bn_geheim(e["benachrichtigung"], lambda w: Q.MASKE if w else ""),
                pult=dict(e["pult"], zugaenge=[dict(z, passwort=Q.MASKE if z["passwort"] else "") for z in e["pult"]["zugaenge"]]))


def bn_geheim(b, ersatz):
    """Kopie der Benachrichtigungs-Einstellungen mit ersetzten Geheimnissen (Bot-Token, SMTP-Passwort)."""
    b = json.loads(json.dumps(b))
    for kanal, feld in BN.GEHEIM:
        if isinstance(b.get(kanal), dict) and feld in b[kanal]:
            b[kanal][feld] = ersatz(b[kanal][feld])
    return b


def pult_behalten(neu):
    """Pult-Zugänge: neues Passwort (passwort_neu) hashen, sonst den vorhandenen Hash (gleiche id) behalten."""
    if not (isinstance(neu, dict) and isinstance(neu.get("pult"), dict) and isinstance(neu["pult"].get("zugaenge"), list)):
        return
    alt = {z["id"]: z["passwort"] for z in einst()["pult"]["zugaenge"]}
    for z in neu["pult"]["zugaenge"]:
        if not isinstance(z, dict):
            continue
        pw = str(z.pop("passwort_neu", "") or "")
        if pw:
            if len(pw) < 6:
                raise E.Fehler("e_pult_pw")
            z["passwort"] = DS.passwort_hash(pw)
        elif z.get("passwort") in (None, "", Q.MASKE):
            z["passwort"] = alt.get(z.get("id"), "")


def bn_behalten(neu, auch_leer=False):
    """Maskierte (beim Einspielen ohne Geheimnisse auch leere) Geheimnisse durch die vorhandenen ersetzen."""
    if isinstance(neu, dict) and isinstance(neu.get("benachrichtigung"), dict):
        alt = einst()["benachrichtigung"]
        for kanal, feld in BN.GEHEIM:
            k = neu["benachrichtigung"].get(kanal)
            if isinstance(k, dict) and feld in k and (k[feld] == Q.MASKE or auch_leer and not k[feld]):
                k[feld] = alt[kanal][feld]


qn = Q.Quellen(lambda: einst(), os.path.join(DATEN, "verlauf.json"))
TODO = TD.Liste(os.path.join(DATEN, "todo.json"))   # ausgeblendete Einträge von „Zu erledigen“ (seit 0.35)
NETZ = NZ.Wache(bedarf=lambda: einst()["video"]["aktiv"] and any(t["video"] for t in einst()["fernseher"]))   # Internet? (seit 0.38)
PROTOKOLL = PR.Protokoll(os.path.join(DATEN, "protokoll.json"))          # wer hat wann was geändert (seit 0.38)
VERSIONEN = PR.Versionen(os.path.join(DATEN, "layout-versionen.json"))   # alte Fassungen der Layouts (seit 0.38)
KI = KZ.Zugaenge(os.path.join(DATEN, "ki-zugaenge.json"))                 # verbundene Computer für MCP im Heimnetz (seit 0.40)
FERN = FN.Fernnetz(os.path.join(DATEN, "fernnetz.json"))                  # Player an anderem Standort per Tailscale/Headscale (seit 0.41)


def fern(aufruf, *a):
    """Fernnetz-Aufruf; Fehler als Meldung für die Verwaltung."""
    try:
        return aufruf(*a)
    except FN.Fehler as f:
        raise M.Meldung(f.code, d=f.innen) from None


def tailscale_hier():
    """Tailscale auf diesem Server: {"ip", "tun"} oder None (nicht installiert, z. B. im Container).
    tun = False heißt Userspace-Modus (--tun=userspace-networking): dann reicht tailscaled Verbindungen aus dem Tailnet
    an 127.0.0.1 weiter – auch an die Verwaltungs-API (127.0.0.1:8080, ohne Anmeldung). Das darf nie sein."""
    try:
        r = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=5)
        d = json.loads(r.stdout) if r.stdout.strip().startswith("{") else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    if not isinstance(d, dict) or "TUN" not in d:
        return None
    s = d.get("Self") or {}
    ips = s.get("TailscaleIPs") or []
    konto = ((d.get("User") or {}).get(str(s.get("UserID"))) or {}).get("LoginName", "")
    return {"ip": next((a for a in ips if FN._adresse_ok(a)), ""), "tun": bool(d.get("TUN")),
            "laeuft": d.get("BackendState") == "Running", "zustand": d.get("BackendState", ""),
            "url": d.get("AuthURL", "") if re.match(r"https?://", str(d.get("AuthURL", ""))) else "",
            "name": s.get("HostName", ""), "konto": konto, "tailnet": (d.get("CurrentTailnet") or {}).get("Name", "")}


TS_ANMELDUNG = {"proc": None}


def tailscale_anmelden():
    """Server per Link ins Tailnet (seit 0.42): tailscale up im Hintergrund (als Dienst-Benutzer – dafür setzt die
    Einrichtung --operator), dann den Anmelde-Link aus tailscale status lesen. Der Nutzer öffnet ihn und meldet sich an."""
    h = tailscale_hier()
    if not h:
        raise M.Meldung("fn_kein_tailscale")
    if not h["tun"]:
        raise M.Meldung("fn_userspace")
    if h["laeuft"]:
        return h
    p = TS_ANMELDUNG["proc"]
    if not p or p.poll() is not None:
        TS_ANMELDUNG["proc"] = p = subprocess.Popen(
            ["tailscale", "up", "--accept-dns=false", "--hostname=" + (h["name"] or "signagecast"), "--timeout=900s"]
            + (["--login-server=" + FERN.k["url"]] if FERN.k["url"] else []),
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    for _ in range(30):
        time.sleep(0.5)
        h = tailscale_hier() or h
        if h["url"] or h["laeuft"]:
            return h
        if p.poll() is not None:
            fehler = (p.stderr.read() or "")[-300:]
            raise M.Meldung("fn_operator" if re.search(r"access denied|operator|permission", fehler, re.I) else "fn_anmeldung", d=fehler.strip())
    raise M.Meldung("fn_anmeldung", d="kein Anmelde-Link")


def fern_sicher():
    """Fernstandorte nur, wenn Tailscale hier nicht im Userspace-Modus läuft (sonst wäre die Verwaltungs-API offen)."""
    h = tailscale_hier()
    if h and not h["tun"]:
        raise M.Meldung("fn_userspace")
layout_vorrang = {}                                # tv -> {"layout", "bis", "von"}: vom Pult gewählt (seit 0.38, nur im Speicher)


def layout_fuer(t, layouts=None):
    """Layout, das der Fernseher jetzt zeigt: vom Pult vorübergehend gewähltes vor Zeitplan, Karussell und Grundlayout."""
    layouts = layouts if layouts is not None else einst()["layouts"]
    v = layout_vorrang.get(t["id"])
    if v and v["bis"] > time.time():
        l = next((x for x in layouts if x["id"] == v["layout"]), None)
        if l:
            return l
    return L.aktuelles_layout(t, layouts, time.strftime("%H:%M"))


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
            SP.pruefen(DATEN, grenze)            # seit 0.45: der Vorrat wächst nicht in die Reserve hinein
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
UPDATE_AKTIONEN = ("pruefen", "system", "sicherheit", "signagecast", "zurueck", "tailscale")


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
    """Laufschrift-Meldung: vom Pult (seit 0.38, je Fernseher) vor der aus dem Webhook."""
    p = zustand.get("meldung_pult")
    if p and p["bis"] > time.time() and tv_id in p["tvs"]:
        return {"text": p["text"], "stil": p["stil"], "bis": p["bis"]}
    m = zustand.get("meldung_extern")
    if not m or m["bis"] < time.time() or (m.get("tv") and m["tv"] != tv_id):
        return None
    return {"text": m["text"], "stil": m["stil"], "bis": m["bis"]}


def meldung_setzen(tvs, text, dauer_s, stil, von):
    """Laufschrift-Meldung auf den Fernsehern tvs (Pult seit 0.38, Verwaltung/MCP seit 0.39)."""
    text = " ".join(str(text or "").split())[:200]
    alle = {t["id"] for t in einst()["fernseher"]}
    tvs = [x for x in tvs if x in alle]
    if not text or not tvs:
        raise M.Meldung("d_text_tv")
    zustand["meldung_pult"] = {"text": text, "bis": time.time() + max(60, min(12 * 3600, int(dauer_s or 3600))), "tvs": tvs,
                               "von": str(von)[:40], "stil": "warnung" if stil == "warnung" else "info"}


def meldung_beenden(tvs):
    mp = zustand.get("meldung_pult")
    if mp:
        mp["tvs"] = [x for x in mp["tvs"] if x not in tvs]


def vorrang_setzen(tvs, layout_id, minuten, von):
    """Layout vorübergehend zeigen (vor Zeitplan und Karussell); Pult seit 0.38, Verwaltung/MCP seit 0.39."""
    l = next((x for x in einst()["layouts"] if x["id"] == layout_id), None)
    alle = {t["id"] for t in einst()["fernseher"]}
    tvs = [x for x in tvs if x in alle]
    if not l or not tvs:
        raise M.Meldung("d_text_tv")
    minuten = max(5, min(12 * 60, int(minuten or 60)))
    for x in tvs:
        layout_vorrang[x] = {"layout": l["id"], "bis": time.time() + minuten * 60, "von": str(von)[:40]}
    schalten_neu.set()                            # war der Fernseher im Zeitplan „schwarz“: einschalten
    return l, minuten


def vorrang_beenden(tvs):
    for x in tvs:
        layout_vorrang.pop(x, None)
    schalten_neu.set()


def tv_namen(ids):
    return ", ".join(t["name"] for t in einst()["fernseher"] if t["id"] in ids)


# ---------- Durchsagen (seit 0.19) ----------
# Nur im Arbeitsspeicher: laufende Durchsagen und „Zuletzt“ (höchstens 10, 2 Stunden) – Namen werden nirgends gespeichert.
durchsagen = []                                   # [{id, text, tvs, bis, audio, zeit, von, t}]
pult_sitzungen = {}                               # token -> {zugang, bis}


def durchsagen_aktiv():
    jetzt = time.time()
    durchsagen[:] = [x for x in durchsagen if jetzt - x["t"] < 7200][:10]
    DS.aufraeumen({x["id"] for x in durchsagen if x["bis"] > jetzt})
    return [x for x in durchsagen if x["bis"] > jetzt]


def durchsage_senden(text, tvs, vorlesen, gong, dauer, von):
    text = " ".join(str(text).split())[:200]
    if not text or not tvs:
        raise M.Meldung("d_text_tv")
    p, did = einst()["pult"], secrets.token_hex(6)
    audio = []
    if vorlesen:
        if not DS.bereit(p["stimme"]):
            raise M.Meldung("d_stimme_fehlt")
        DS.sprechen(text, p["stimme"], did, mit_gong=gong); audio.append(f"/durchsage/{did}.wav")
    durchsagen.insert(0, {"id": did, "text": text, "tvs": list(tvs), "bis": time.time() + dauer, "audio": audio,
                          "zeit": time.strftime("%H:%M"), "von": von, "t": time.time()})
    durchsagen_aktiv()
    ds_melden()
    return did


# Seit 0.29 holt die TV-Seite Durchsagen und Notfall-Vollbild per Long-Polling: die Anfrage wartet, bis sich etwas
# ändert (höchstens 20 s) – statt alle 2 s zu fragen. Jede Änderung weckt die wartenden Anfragen.
ds_aenderung = threading.Condition()


def ds_melden():
    with ds_aenderung:
        ds_aenderung.notify_all()


def ds_warten(tv_id, stand, max_s=20.0):
    """Antwort für /durchsage.json; mit `stand` (Kennung der letzten Antwort) wird gewartet, bis sie sich ändert."""
    ende = time.time() + max_s
    while True:
        d, a = durchsage_fuer(tv_id), alarm_fuer(tv_id)
        jetzt = f"{d['id'] if d else '-'}.{a['id'] if a else '-'}"
        rest = ende - time.time()
        if not stand or stand != jetzt or rest <= 0:
            return {"ok": True, "durchsage": d, "alarm": a, "stand": jetzt}
        if d:                                     # rechtzeitig zum Ende der Durchsage antworten (Fenster ausblenden)
            rest = min(rest, max(0.2, d["bis"] - time.time() + 0.2))
        with ds_aenderung:
            ds_aenderung.wait(rest)


def durchsage_fuer(tv_id):
    x = next((x for x in durchsagen if tv_id in x["tvs"] and x["bis"] > time.time()), None)
    return {"id": x["id"], "text": x["text"], "bis": x["bis"], "audio": x["audio"]} if x else None


# ---------- Notfall-Vollbild (seit 0.21) ----------
# Bleibt, bis jemand es beendet – auch über einen Neustart des Dienstes (Datei), damit eine Räumung nicht verschwindet.
ALARM = os.path.join(DATEN, "alarm.json")


def alarm_laden():
    try:
        a = json.load(open(ALARM))
        return a if isinstance(a, dict) and a.get("text") else None
    except (OSError, ValueError):
        return None


alarm = {"jetzt": alarm_laden()}


def alarm_ausloesen(text, tvs, von, quelle="pult"):
    """tvs leer = alle Fernseher."""
    text = " ".join(str(text or "").split())[:200]
    if not text:
        raise M.Meldung("al_text")
    alle = {t["id"] for t in einst()["fernseher"]}
    a = {"id": secrets.token_hex(6), "text": text, "tvs": [x for x in (tvs or []) if x in alle], "von": str(von)[:40],
         "seit": int(time.time()), "zeit": time.strftime("%H:%M")}
    tmp = ALARM + ".tmp"
    with open(tmp, "w") as f:
        json.dump(a, f, ensure_ascii=False)
    os.replace(tmp, ALARM)
    alarm["jetzt"] = a
    ds_melden()
    schalten_neu.set()                           # ausgeschaltete Fernseher sofort einschalten
    print(f"Notfall-Vollbild ausgelöst von {a['von']}", flush=True)
    PROTOKOLL.eintragen(a["von"], quelle, "alarm_an", text)
    return a


def alarm_beenden(von, quelle="pult"):
    if alarm["jetzt"]:
        print(f"Notfall-Vollbild beendet von {str(von)[:40]}", flush=True)
        PROTOKOLL.eintragen(von, quelle, "alarm_aus")
    alarm["jetzt"] = None
    ds_melden()
    try:
        os.remove(ALARM)
    except OSError:
        pass
    schalten_neu.set()


def alarm_fuer(tv_id):
    a = alarm["jetzt"]
    if not a or (a["tvs"] and tv_id not in a["tvs"]):
        return None
    return {"id": a["id"], "text": a["text"], "ton": einst()["alarm"]["ton"]}


def pult_zugang(handler):
    """Angemeldeter Pult-Zugang aus dem Sitzungs-Cookie (oder None)."""
    for teil in (handler.headers.get("Cookie") or "").split(";"):
        k, _, v = teil.strip().partition("=")
        if k == "sc_pult" and v in pult_sitzungen and pult_sitzungen[v]["bis"] > time.time():
            return next((z for z in einst()["pult"]["zugaenge"] if z["id"] == pult_sitzungen[v]["zugang"]), None)
    return None


def pult_fernseher(z):
    return [t for t in einst()["fernseher"] if not z["fernseher"] or t["id"] in z["fernseher"]]


# ---------- KI-Assistenten im Heimnetz (MCP über HTTP/HTTPS, seit 0.40) ----------
TLS_ORDNER = os.path.join(DATEN, "tls")
KI_DATEIEN = {}                                   # id -> (gültig bis, Dateiname, .mcpb) – zum Herunterladen (seit 0.40.1)
KI_FEHLVERSUCHE = {}                              # IP -> [Zeitpunkte] falscher Schlüssel/Code (höchstens 10 je Minute)
MCP_MAX = 16_000_000                              # ein Bild (10 MB) als base64 passt hinein


def tls_zertifikat():
    """Selbst erzeugtes Zertifikat für https auf dem Pult-Port (einmalig, 10 Jahre). Gibt (cert_pfad, key_pfad) oder None.
    Die Brücke für Claude Desktop vertraut genau diesem Zertifikat – neu erzeugt = Computer neu verbinden."""
    cert, key = os.path.join(TLS_ORDNER, "zertifikat.pem"), os.path.join(TLS_ORDNER, "schluessel.pem")
    if os.path.exists(cert) and os.path.exists(key):
        return cert, key
    try:
        os.makedirs(TLS_ORDNER, mode=0o700, exist_ok=True)
        subprocess.run(["openssl", "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes",
                        "-days", "3650", "-subj", "/CN=SignageCast", "-addext", "subjectAltName=DNS:signagecast,DNS:signagecast.local",
                        "-keyout", key + ".tmp", "-out", cert + ".tmp"], check=True, capture_output=True, timeout=60)
        os.chmod(key + ".tmp", 0o600)
        os.replace(key + ".tmp", key)
        os.replace(cert + ".tmp", cert)
        print("TLS-Zertifikat für den Pult-Port erzeugt", flush=True)
        return cert, key
    except (OSError, subprocess.SubprocessError) as f:
        print(f"TLS-Zertifikat nicht erzeugt ({f}) – KI-Assistenten nur über http", flush=True)
        return None


def ki_fehlversuch(ip):
    jetzt = time.time()
    KI_FEHLVERSUCHE[ip] = [t for t in KI_FEHLVERSUCHE.get(ip, []) if jetzt - t < 60][-20:] + [jetzt]
    time.sleep(1)


def ki_gesperrt(ip):
    return len([t for t in KI_FEHLVERSUCHE.get(ip, []) if time.time() - t < 60]) >= 10


def ki_datei_merken(eintrag, roh):
    """Die .mcpb bis zum Einlösen (höchstens EINLOESEN_S) im Speicher halten, damit der Browser sie als echten Download
    holen kann – Safari lädt in der Cockpit-Verwaltung keine im Browser erzeugten Dateien (blob:) herunter (0.40.1)."""
    jetzt = time.time()
    for k in [k for k, (bis, _, _) in KI_DATEIEN.items() if bis < jetzt]:
        KI_DATEIEN.pop(k, None)
    name = re.sub(r"[^a-z0-9._-]+", "-", eintrag["name"].lower()).strip("-.") or "computer"
    KI_DATEIEN[eintrag["id"]] = (jetzt + KZ.EINLOESEN_S, f"signagecast-{name}.mcpb", roh)
    return KI_DATEIEN[eintrag["id"]][1]


ABLAGE = {}                                       # id -> (gültig bis, Dateiname, Typ, Inhalt) – Downloads aus dem Browser
ABLAGE_S, ABLAGE_MAX = 300, 3
ABLAGE_TYPEN = ("application/json", "text/markdown")


def ablegen(name, typ, inhalt):
    """Datei, die die Verwaltung erzeugt (Layout-Export, KI-Anleitung), kurz ablegen und einmal als echten Download
    ausliefern – Safari lädt in der Cockpit-Verwaltung keine im Browser erzeugten Dateien (blob:) herunter (0.40.1)."""
    name = str(name or "")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,120}", name) or typ not in ABLAGE_TYPEN or not isinstance(inhalt, str):
        raise E.Fehler("ungültige Datei")
    jetzt = time.time()
    for k in [k for k, x in ABLAGE.items() if x[0] < jetzt] + sorted(ABLAGE, key=lambda k: ABLAGE[k][0])[:max(0, len(ABLAGE) - ABLAGE_MAX + 1)]:
        ABLAGE.pop(k, None)
    aid = secrets.token_urlsafe(16)
    ABLAGE[aid] = (jetzt + ABLAGE_S, name, typ, inhalt.encode())
    return aid


def ki_datei(zid):
    x = KI_DATEIEN.get(zid)
    if x and x[0] < time.time():
        KI_DATEIEN.pop(zid, None)
        return None
    return x


def mcpb_bauen(eintrag, code, adresse):
    """Erweiterung für Claude Desktop (.mcpb = ZIP mit manifest.json, Brücke und Verbindung) – im Speicher."""
    import io, zipfile
    with open(os.path.join(TLS_ORDNER, "zertifikat.pem")) as f:
        cert = f.read()
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_bruecke.js")) as f:
        bruecke = f.read()
    url = f"https://{adresse}:{WEBHOOK_PORT}/mcp"
    version = re.sub(r"[^0-9.]", "", VERSION) or "0.0.0"
    manifest = {
        "manifest_version": "0.3", "name": "signagecast", "display_name": "SignageCast",
        "version": version if version.count(".") == 2 else "0.0.0",
        "description": "Manage the content of your SignageCast TVs (layouts, ticker, announcements, streams) – in your home network.",
        "author": {"name": "SignageCast", "url": f"https://github.com/{PROJEKT}"},
        "homepage": f"https://github.com/{PROJEKT}", "documentation": f"https://github.com/{PROJEKT}/blob/main/docs/MCP.md",
        "license": "MIT",
        "server": {"type": "node", "entry_point": "server/index.js",
                   "mcp_config": {"command": "node", "args": ["${__dirname}/server/index.js"]}},
        "tools_generated": True,
        "compatibility": {"platforms": ["darwin", "win32", "linux"], "runtimes": {"node": ">=16.0.0"}},
    }
    verbindung = {"url": url, "id": eintrag["id"], "name": eintrag["name"], "code": code, "zertifikat": cert}
    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        z.writestr("server/index.js", bruecke)
        z.writestr("server/verbindung.json", json.dumps(verbindung, indent=1))
    return puffer.getvalue()


class WebhookBearbeiter(BaseHTTPRequestHandler):
    """Nur /meldung, nur mit Schlüssel (Authorization: Bearer … oder ?token=…). Alles andere: 404."""
    def log_message(self, *a):
        pass

    def antwort(self, code, obj):
        roh = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(roh)))
        self.end_headers(); self.wfile.write(roh)

    def datei(self, pfad, art):
        roh = open(pfad, "rb").read()
        self.send_response(200); self.send_header("Content-Type", art); self.send_header("Content-Length", str(len(roh)))
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(roh)

    def bearbeiten(self, daten):
        import hmac
        u = urllib.parse.urlparse(self.path)
        jetzt, ip = time.time(), self.client_address[0]
        liste = [t for t in webhook_versuche.get(ip, []) if jetzt - t < 60]
        webhook_versuche[ip] = (liste + [jetzt])[-200:]
        # 20 Anfragen je Minute und Adresse (gegen Raten von Passwort/Schlüssel); angemeldete Pult-Sitzungen fragen
        # regelmäßig nach (Liste, Notfall, Stand) und teilen sich evtl. eine Adresse – für sie 120 (seit 0.38)
        grenze = 120 if u.path.startswith("/pult/") and u.path != "/pult/anmelden" and pult_zugang(self) else 20
        if len(liste) >= grenze:
            return self.antwort(429, {"ok": False, "fehler": "zu viele Anfragen"})
        # Leistungstest auf dem Abspielgerät (seit 0.18): http wie der Stream – aus der https-Verwaltung blockiert der Browser
        if u.path == "/test" and self.command == "GET":
            return self.datei(os.path.join(WWW, "leistungstest.html"), "text/html; charset=utf-8")
        if u.path == "/test/hls.js" and self.command == "GET":
            return self.datei(os.path.join(WWW, "hls", "hls.light.min.js"), "application/javascript")
        if u.path == "/test/info" and self.command == "GET":
            return self.antwort(200, {"ok": True, "port": HLS_PORT, "sprache": einst()["sprache"] or "en",
                                      "fernseher": [{"id": t["id"], "name": t["name"], "bitrate_mbit": t["bitrate_mbit"],
                                                     "codec": codec_fuer(t), "aufloesung": t["aufloesung"]} for t in einst()["fernseher"]]})
        if u.path == "/test/ergebnis" and self.command == "POST":
            erg = {k: daten.get(k) for k in ("tv", "mbit", "segment_s", "segment_max_s", "dekodiert", "verloren", "stocken", "dauer_s")
                   if isinstance(daten.get(k), (int, float, str)) and len(str(daten.get(k))) < 40}
            erg.update(zeit=time.strftime("%Y-%m-%d %H:%M:%S"), geraet=str(self.headers.get("User-Agent", ""))[:160], ip=ip)
            zustand["leistung_geraete"] = ([erg] + zustand.get("leistung_geraete", []))[:5]
            return self.antwort(200, {"ok": True})
        if u.path.startswith("/pult"):
            return self.pult(u.path, daten)
        if u.path not in ("/meldung", "/alarm"):
            return self.antwort(404, {"ok": False})
        wh = einst()["webhook"]
        q = urllib.parse.parse_qs(u.query)
        gegeben = (self.headers.get("Authorization") or "").removeprefix("Bearer ").strip() or (q.get("token") or [""])[0]
        if not wh["aktiv"] or not wh["token"] or not hmac.compare_digest(gegeben.encode(), wh["token"].encode()):
            time.sleep(1)
            return self.antwort(403, {"ok": False})
        if u.path == "/alarm":                    # Notfall-Vollbild (seit 0.21): {"text": …} auslösen, {"aus": true} beenden
            if daten.get("aus") or (q.get("aus") or [""])[0] in ("1", "true"):
                alarm_beenden("Webhook", "webhook")
                return self.antwort(200, {"ok": True, "beendet": True})
            if self.command != "POST":
                return self.antwort(405, {"ok": False})
            tv = str(daten.get("tv", (q.get("tv") or [""])[0]))[:12]
            try:
                text = daten.get("text") or (q.get("text") or [""])[0] or (einst()["alarm"]["vorlagen"] or [""])[0]
                a = alarm_ausloesen(text, [tv] if tv else [], "Webhook", "webhook")
            except M.Meldung:
                return self.antwort(400, {"ok": False, "fehler": "text fehlt"})
            return self.antwort(200, {"ok": True, "id": a["id"]})
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

    def pult(self, pfad, daten):
        """Durchsage-Pult: nur Meldungen senden/beenden – keine Einstellungen."""
        if pfad == "/pult" and self.command == "GET":
            return self.datei(os.path.join(WWW, "pult.html"), "text/html; charset=utf-8")
        if self.command == "POST" and self.headers.get("X-Pult") != "1":     # gegen fremde Formulare (CSRF)
            return self.antwort(403, {"ok": False})
        if pfad == "/pult/anmelden" and self.command == "POST":
            pw = str(daten.get("passwort", ""))
            z = next((z for z in einst()["pult"]["zugaenge"] if z["passwort"] and DS.passwort_ok(pw, z["passwort"])), None)
            if not z:
                time.sleep(1)
                return self.antwort(403, {"ok": False, "fehler": "falsches Passwort"})
            token = secrets.token_urlsafe(24)
            pult_sitzungen[token] = {"zugang": z["id"], "bis": time.time() + 12 * 3600}
            roh = json.dumps({"ok": True}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", f"sc_pult={token}; HttpOnly; SameSite=Strict; Path=/pult; Max-Age=43200")
            self.send_header("Content-Length", str(len(roh))); self.end_headers(); self.wfile.write(roh)
            return
        z = pult_zugang(self)
        if not z:
            return self.antwort(401, {"ok": False})
        p = einst()["pult"]
        if pfad == "/pult/info":
            return self.antwort(200, {"ok": True, "zugang": z["name"], "sprache": einst()["sprache"] or "de",
                                      "fernseher": [{"id": t["id"], "name": t["name"], "schalten": bool(t["ha_schalten"])}
                                                    for t in pult_fernseher(z)],
                                      "rechte": {k: bool(z.get(k)) for k in ("meldung", "layout", "schalten")},
                                      "layouts": [{"id": l["id"], "name": l["name"]} for l in einst()["layouts"]] if z.get("layout") else [],
                                      "vorlagen": p["vorlagen"], "vorlesen": p["vorlesen"] and DS.bereit(p["stimme"]),
                                      "gong": p["gong"], "dauer_s": p["dauer_s"],
                                      "alarm": z.get("alarm", False), "alarm_vorlagen": einst()["alarm"]["vorlagen"] if z.get("alarm") else []})
        erlaubt = {t["id"] for t in pult_fernseher(z)}
        if pfad == "/pult/liste":
            return self.antwort(200, {"ok": True, "liste": [{k: x[k] for k in ("id", "text", "zeit", "von")} | {
                "tvs": [t["name"] for t in einst()["fernseher"] if t["id"] in x["tvs"]], "laeuft": x["bis"] > time.time()}
                for x in (durchsagen_aktiv(), durchsagen)[1] if set(x["tvs"]) & erlaubt]})
        if pfad == "/pult/senden" and self.command == "POST":
            tvs = [x for x in (daten.get("fernseher") or []) if x in erlaubt]
            try:
                dauer = max(10, min(3600, int(daten.get("dauer_s") or p["dauer_s"])))
                did = durchsage_senden(daten.get("text", ""), tvs, bool(daten.get("vorlesen")) and p["vorlesen"],
                                       bool(daten.get("gong", p["gong"])), dauer, z["name"])
                PROTOKOLL.eintragen(z["name"], "pult", "durchsage", ", ".join(t["name"] for t in pult_fernseher(z) if t["id"] in tvs))
            except (ValueError, RuntimeError, subprocess.TimeoutExpired) as f:
                return self.antwort(200, {"ok": False, "fehler": str(f)[:200], "code": getattr(f, "code", "")})
            return self.antwort(200, {"ok": True, "id": did})
        if pfad == "/pult/beenden" and self.command == "POST":
            for x in durchsagen:
                if x["id"] == daten.get("id") and set(x["tvs"]) & erlaubt:
                    x["bis"] = 0
            ds_melden()
            return self.antwort(200, {"ok": True})
        if pfad == "/pult/alarm":                 # Notfall-Vollbild (seit 0.21): nur Zugänge mit dem Recht „alarm“
            if not z.get("alarm"):
                return self.antwort(403, {"ok": False})
            if self.command == "POST":
                if daten.get("aus"):
                    alarm_beenden(z["name"])
                else:
                    try:
                        alarm_ausloesen(daten.get("text", ""), [x for x in (daten.get("fernseher") or []) if x in erlaubt] or
                                        ([] if not z["fernseher"] else sorted(erlaubt)), z["name"])
                    except M.Meldung as f:
                        return self.antwort(200, {"ok": False, "fehler": str(f), "code": f.code})
            a = alarm["jetzt"]
            return self.antwort(200, {"ok": True, "aktiv": bool(a), **({"text": a["text"], "zeit": a["zeit"], "von": a["von"]} if a else {})})
        if pfad == "/pult/stand":                 # seit 0.38: was das Pult je Fernseher eingestellt hat, Zustand aus HA
            jetzt, mp = time.time(), zustand.get("meldung_pult")
            return self.antwort(200, {"ok": True, "fernseher": [{
                "id": t["id"], "layout": ({"name": layout_fuer(t)["name"], "bis": int(v["bis"]), "von": v["von"]}
                                          if (v := layout_vorrang.get(t["id"])) and v["bis"] > jetzt else None),
                "meldung": {"text": mp["text"], "bis": int(mp["bis"])} if mp and mp["bis"] > jetzt and t["id"] in mp["tvs"] else None,
                "zustand": ((schalten_stand.get(t["id"]) or {}).get("ha") or {}).get("zustand")} for t in pult_fernseher(z)]})
        if pfad == "/pult/meldung" and self.command == "POST":
            if not z.get("meldung"):
                return self.antwort(403, {"ok": False, "code": "p_recht"})
            tvs = [x for x in (daten.get("fernseher") or []) if x in erlaubt]
            if daten.get("aus"):
                meldung_beenden(tvs or erlaubt)
                PROTOKOLL.eintragen(z["name"], "pult", "meldung_aus", tv_namen(tvs or erlaubt))
                return self.antwort(200, {"ok": True})
            try:
                meldung_setzen(tvs, daten.get("text", ""), daten.get("dauer_s"), daten.get("stil"), z["name"])
            except (M.Meldung, ValueError) as f:
                return self.antwort(200, {"ok": False, "code": getattr(f, "code", "d_text_tv")})
            PROTOKOLL.eintragen(z["name"], "pult", "meldung", tv_namen(tvs))
            return self.antwort(200, {"ok": True})
        if pfad == "/pult/layout" and self.command == "POST":
            if not z.get("layout"):
                return self.antwort(403, {"ok": False, "code": "p_recht"})
            tvs = [x for x in (daten.get("fernseher") or []) if x in erlaubt]
            if daten.get("aus"):
                vorrang_beenden(tvs or erlaubt)
                PROTOKOLL.eintragen(z["name"], "pult", "layout_aus", tv_namen(tvs or erlaubt))
                return self.antwort(200, {"ok": True})
            try:
                l, minuten = vorrang_setzen(tvs, daten.get("layout"), daten.get("minuten"), z["name"])
            except (M.Meldung, ValueError) as f:
                return self.antwort(200, {"ok": False, "code": getattr(f, "code", "d_text_tv")})
            PROTOKOLL.eintragen(z["name"], "pult", "layout", f"{l['name']} → {tv_namen(tvs)} ({minuten} min)")
            return self.antwort(200, {"ok": True})
        if pfad == "/pult/schalten" and self.command == "POST":
            if not z.get("schalten"):
                return self.antwort(403, {"ok": False, "code": "p_recht"})
            t = next((t for t in pult_fernseher(z) if t["id"] == daten.get("tv")), None)
            if not t or not t["ha_schalten"]:
                return self.antwort(200, {"ok": False, "code": "p_kein_schalten"})
            try:
                tv_schalten(t, bool(daten.get("an")))
            except (HAFehler, M.Meldung) as f:
                return self.antwort(200, {"ok": False, "fehler": str(f)[:200], "code": getattr(f, "code", "")})
            threading.Timer(8, zustand_abfragen).start()
            PROTOKOLL.eintragen(z["name"], "pult", "schalten", f"{t['name']} – {'an' if daten.get('an') else 'aus'}")
            return self.antwort(200, {"ok": True})
        if pfad == "/pult/abmelden" and self.command == "POST":
            for k in [k for k, v in pult_sitzungen.items() if v["zugang"] == z["id"] and k in (self.headers.get("Cookie") or "")]:
                pult_sitzungen.pop(k, None)
            return self.antwort(200, {"ok": True})
        return self.antwort(404, {"ok": False})

    def do_GET(self):
        if self.anzeige():
            return
        if urllib.parse.urlparse(self.path).path == "/mcp":
            # MCP über HTTP: kein Ereignis-Strom (SSE) vom Server – laut Spezifikation dann 405
            return self.antwort(405 if KI.vorhanden() else 404, {"ok": False})
        self.bearbeiten({})

    def do_DELETE(self):
        return self.antwort(405 if urllib.parse.urlparse(self.path).path == "/mcp" and KI.vorhanden() else 404, {"ok": False})

    def mcp(self, pfad, n):
        """MCP im Heimnetz (seit 0.40): nur für verbundene Computer (Einstellungen → KI-Assistenten).
        POST /mcp mit Authorization: Bearer <Schlüssel>; POST /mcp/koppeln tauscht den Einmal-Code der Claude-Desktop-Datei."""
        ip = self.client_address[0]
        if not KI.vorhanden():
            return self.antwort(404, {"ok": False})
        if self.headers.get("Origin"):           # Webseiten im Browser haben hier nichts zu suchen (DNS-Rebinding, CSRF)
            return self.antwort(403, {"ok": False})
        if ki_gesperrt(ip):
            return self.antwort(429, {"ok": False, "fehler": "zu viele Fehlversuche"})
        if pfad == "/mcp/koppeln":
            if n > 4096:
                return self.antwort(413, {"ok": False})
            try:
                d = json.loads(self.rfile.read(n) or b"{}")
            except ValueError:
                d = {}
            x, schluessel = KI.einloesen(str(d.get("code", "")) if isinstance(d, dict) else "", ip)
            if not x:
                ki_fehlversuch(ip)
                return self.antwort(403, {"ok": False})
            KI_DATEIEN.pop(x["id"], None)             # eingelöst – die Datei ist wertlos
            PROTOKOLL.eintragen(x["name"], "system", "ki_gekoppelt", ip)
            return self.antwort(200, {"ok": True, "schluessel": schluessel})
        x = KI.pruefen((self.headers.get("Authorization") or "").removeprefix("Bearer ").strip(), ip)
        if not x:
            ki_fehlversuch(ip)
            roh = json.dumps({"ok": False, "fehler": "unbekannter Computer"}).encode()
            self.send_response(401); self.send_header("Content-Type", "application/json")
            self.send_header("WWW-Authenticate", 'Bearer realm="SignageCast"'); self.send_header("Content-Length", str(len(roh)))
            self.end_headers(); self.wfile.write(roh)
            return
        if n > MCP_MAX:
            return self.antwort(413, {"ok": False})
        try:
            m = json.loads(self.rfile.read(n) or b"null")
        except ValueError:
            return self.antwort(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "kein JSON"}})
        a = MCP.verarbeiten(m, "MCP " + x["name"], x["recht"] == "lesen")
        if a is None:                            # nur Benachrichtigungen/Antworten
            self.send_response(202); self.send_header("Content-Length", "0"); self.end_headers()
            return
        return self.antwort(200, a)

    # --- Direktmodus (seit 0.24): der Pi zeigt die TV-Seite selbst ---
    def anzeige(self):
        """/anzeige/<Schlüssel> setzt ein Cookie und leitet auf die TV-Seite; danach reicht der Zugang alle Abrufe der Seite
        an den Datendienst weiter – nur für den Fernseher dieses Pi, ohne Verwaltungs-API. True = beantwortet."""
        u = urllib.parse.urlparse(self.path)
        m = re.fullmatch(r"/anzeige/([0-9a-f]{32})", u.path)
        if m:
            g = PL.geraet_fuer_anzeige(m.group(1))
            if not g:
                time.sleep(1)
                self.antwort(403, {"ok": False})
                return True
            self.send_response(302); self.send_header("Location", "/?tv=" + urllib.parse.quote(g["tv"] or "-"))
            self.send_header("Set-Cookie", f"sc_anzeige={m.group(1)}; HttpOnly; SameSite=Strict; Path=/; Max-Age=31536000")
            self.send_header("Content-Length", "0"); self.end_headers()
            return True
        c = re.search(r"(?:^|;\s*)sc_anzeige=([0-9a-f]{32})", self.headers.get("Cookie") or "")
        if not c or u.path.startswith(("/test", "/pult", "/meldung", "/alarm", "/player/")):
            return False
        g = PL.geraet_fuer_anzeige(c.group(1))
        t = next((t for t in einst()["fernseher"] if t["id"] == g["tv"]), None) if g else None
        if not t:
            time.sleep(0 if g else 1)
            self.antwort(403 if not g else 404, {"ok": False})
            return True
        m = re.fullmatch(r"/hlscam/(cam_[a-z0-9_]{2,16})/([A-Za-z0-9_.\-]{1,80})", u.path)
        if m:                                     # Kamera-Stream: nur Kameras aus der letzten daten.json dieses Fernsehers
            if m.group(1) not in PL.kameras_erlaubt.get(t["id"], set()):
                self.antwort(404, {"ok": False})
                return True
            self.weiterleiten(HLS_PORT, f"/{m.group(1)}/{m.group(2)}" + ("?" + u.query if u.query else ""))
            return True
        m = re.fullmatch(r"/radio/([a-z][a-z0-9]{0,11})/.*", u.path)
        if (m and m.group(1) != t["id"]) or not PL.anzeige_pfad_ok(u.path):
            self.antwort(404, {"ok": False})
            return True
        q = [(k, v) for k, v in urllib.parse.parse_qsl(u.query, keep_blank_values=True) if k != "tv"]
        if u.path in ("/", "/index.html", "/daten.json", "/durchsage.json") or "tv=" in u.query:
            q.append(("tv", t["id"]))             # immer der eigene Fernseher, egal was die Seite fragt
        ziel = u.path + ("?" + urllib.parse.urlencode(q) if q else "")
        if u.path == "/daten.json":
            PL.direkt_abruf[g["id"]] = time.time()
            self.weiterleiten(int(os.environ.get("SC_PORT", "8080")), ziel, kameras=t["id"], fernwartung=bool(FW.zustand(g["id"])))
        else:
            self.weiterleiten(int(os.environ.get("SC_PORT", "8080")), ziel)
        return True

    def weiterleiten(self, port, ziel, kameras=None, fernwartung=False):
        """GET an 127.0.0.1:<port> durchreichen (mit Range, als Datenstrom – auch Radio und MJPEG)."""
        import http.client
        kopf = {k: self.headers[k] for k in ("Range", "If-None-Match", "If-Modified-Since", "User-Agent") if self.headers.get(k)}
        try:
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
            c.request("GET", ziel, headers=kopf)
            r = c.getresponse()
        except OSError:
            return self.antwort(502, {"ok": False})
        try:
            if kameras is not None:               # Kamera-Adressen (nur im Container lesbar) auf diesen Zugang umschreiben
                roh = r.read().replace(f"http://127.0.0.1:{HLS_PORT}/cam_".encode(), b"/hlscam/cam_")
                PL.kameras_erlaubt[kameras] = set(x.decode() for x in re.findall(rb"/hlscam/(cam_[a-z0-9_]{2,16})/", roh))
                if fernwartung and roh.rstrip().endswith(b"}"):   # nur auf diesem Pi: Hinweis „Fernwartung aktiv“ (seit 0.33)
                    roh = roh.rstrip()[:-1] + b', "fernwartung": true}'
                self.send_response(r.status); self.send_header("Content-Type", r.getheader("Content-Type") or "application/json")
                self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(roh)))
                self.end_headers(); self.wfile.write(roh)
                return
            self.send_response(r.status)
            for k in ("Content-Type", "Content-Length", "Content-Range", "Accept-Ranges", "Cache-Control", "Last-Modified", "ETag"):
                if r.getheader(k):
                    self.send_header(k, r.getheader(k))
            ort = r.getheader("Location") or ""
            if ort.startswith("/") and r.status in (301, 302, 303, 307, 308):   # z. B. MediaMTX: „cookieCheck“-Umleitung
                self.send_header("Location", ("/hlscam" if port == HLS_PORT else "") + ort)
            self.end_headers()
            while True:
                teil = r.read1(65536) if hasattr(r, "read1") else r.read(65536)
                if not teil:
                    break
                self.wfile.write(teil)
        except OSError:
            pass
        finally:
            c.close()

    def koppeln(self, pfad, roh):
        """Pi ohne Schlüssel (Image für mehrere Pis, seit 0.25): DH-Wert austauschen, dann nachfragen, ob sein Code
        in der Verwaltung eingegeben wurde. Die Antwort „gekoppelt“ ist mit dem ausgehandelten Schlüssel signiert."""
        try:
            d = json.loads(roh or b"{}")
            d = d if isinstance(d, dict) else {}
        except ValueError:
            d = {}
        g = None
        if pfad == "/player/koppeln":
            try:
                code, antwort = 200, PL.koppel_anfrage(d, self.client_address[0])
            except M.Meldung as f:
                code, antwort = (429 if f.code == "pi_koppel_voll" else 400), {"ok": False, "code": f.code}
        elif pfad == "/player/koppeln/status":
            code, antwort, g = PL.koppel_status(str(d.get("kennung", ""))[:64])
        else:
            return self.antwort(404, {"ok": False})
        roh_a = json.dumps(antwort).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(roh_a)))
        self.send_header("X-Server-Zeit", str(int(time.time())))
        if g:
            self.send_header("X-Signatur", PL.signatur(g, str(d.get("zeit", ""))[:64], roh_a))
        self.end_headers(); self.wfile.write(roh_a)

    def player(self, pfad, roh):
        """Raspberry-Pi-Player (seit 0.23): signierte Meldungen, Bildschirmfotos, Protokolle, Agent-Update."""
        if pfad.startswith("/player/koppeln"):
            return self.koppeln(pfad, roh)
        g, code, zeit = PL.pruefen(self.headers, pfad, roh)
        if not g:
            if code in (403, 404):
                time.sleep(1)
            roh_a = json.dumps({"ok": False}).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json")
            self.send_header("X-Server-Zeit", str(int(time.time()))); self.send_header("Content-Length", str(len(roh_a)))
            self.end_headers(); self.wfile.write(roh_a)
            return
        if pfad == "/player/melden":
            try:
                bericht = json.loads(roh or b"{}")
            except ValueError:
                bericht = {}
            antwort = json.dumps(player_antwort(g, bericht, self.client_address[0])).encode()
            typ = "application/json"
        elif pfad == "/player/bild" and (roh[:2] == b"\xff\xd8" or roh[:8] == b"\x89PNG\r\n\x1a\n"):   # PNG seit 0.36 (grim ohne JPEG)
            PL.datei_ablegen(g, ".jpg", roh)
            antwort, typ = b'{"ok": true}', "application/json"
        elif pfad == "/player/protokoll":
            PL.datei_ablegen(g, ".log", roh[-300_000:])
            antwort, typ = b'{"ok": true}', "application/json"
        elif pfad == "/player/agent":
            antwort, typ = open(PL.AGENT, "rb").read(), "text/x-python"
        elif pfad in ("/player/terminal/ein", "/player/terminal/aus"):   # Fernwartung (seit 0.33)
            try:
                d = json.loads(roh or b"{}")
                d = d if isinstance(d, dict) else {}
            except ValueError:
                d = {}
            erg = FW.pi_ein(g, d) if pfad.endswith("/ein") else FW.pi_aus(g, d)
            antwort, typ = json.dumps(erg).encode(), "application/json"
        else:
            return self.antwort(404, {"ok": False})
        self.send_response(200); self.send_header("Content-Type", typ); self.send_header("Content-Length", str(len(antwort)))
        self.send_header("X-Server-Zeit", str(int(time.time()))); self.send_header("X-Signatur", PL.signatur(g, zeit, antwort))
        self.end_headers(); self.wfile.write(antwort)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        if urllib.parse.urlparse(self.path).path in ("/mcp", "/mcp/koppeln"):
            return self.mcp(urllib.parse.urlparse(self.path).path, n)
        if urllib.parse.urlparse(self.path).path.startswith("/player/"):
            if n > 8_000_000:
                return self.antwort(413, {"ok": False})
            return self.player(urllib.parse.urlparse(self.path).path, self.rfile.read(n) if n else b"")
        roh = self.rfile.read(min(n, 4096)) if n else b""
        try:
            daten = json.loads(roh) if roh.strip().startswith(b"{") else {"text": roh.decode(errors="replace")}
        except ValueError:
            daten = {}
        self.bearbeiten(daten if isinstance(daten, dict) else {})


# ---------- Raspberry-Pi-Player (seit 0.23) ----------
def player_antwort(g, bericht, ip):
    t = next((t for t in einst()["fernseher"] if t["id"] == g["tv"]), None)
    stream = {"port": PL.daten["stream_port"] or HLS_PORT, "pfad": t["id"]} if t else None
    bildschirm = schalten_soll(t) if t and g["cec_zeitplan"] else None
    return PL.melden(g, bericht, ip, stream, bildschirm)


def player_hinweise(g):
    """Passt der Fernseher zum Pi? Pi 3/Zero 2 W: nur H.264 bis Full HD; Pi 5: H.264 nur per CPU (kein 4K).
    PC und Browser-Gerät (seit 0.36): keine Codec-Hinweise (Intel/AMD dekodieren beides, der Browser ist unbekannt)."""
    t = next((t for t in einst()["fernseher"] if t["id"] == g["tv"]), None)
    if not t:
        return ["pi_kein_tv"]
    if g.get("modell") == PL.BROWSER:
        return []
    b = (PL.stand.get(g["id"]) or {}).get("bericht") or {}
    modell = b.get("modell") or ""
    if g.get("modell") == "pc" or b.get("plattform") == "pc":
        h = ["pi_heiss"] if (b.get("temperatur") or 0) >= 90 else []
        if PL.online(g["id"]) and b.get("hdmi") is False:
            h.append("pc_kein_bildschirm")
        if g.get("anzeige_modus") == "direkt" and b.get("rueckfall"):
            h.append("pi_direkt_rueckfall")
        if b.get("plattform") == "pi":
            h.append("pc_ist_pi")
        elif g.get("modell") != "pc":
            h.append("pi_ist_pc")
        return h
    klasse = "pi3" if re.search(r"Pi 3|Zero 2", modell) else "pi5" if "Pi 5" in modell else g["modell"] if not modell else "pi4"
    hoehe = 2160 if t["aufloesung"] == 2160 and encoder_fuer(t) != "software" else 1080
    h = []
    if klasse == "pi3" and codec_fuer(t) == "h265":
        h.append("pi_h265")
    if klasse == "pi3" and hoehe == 2160:
        h.append("pi_4k")
    if klasse == "pi5" and codec_fuer(t) == "h264" and hoehe == 2160:
        h.append("pi5_h264_4k")
    if b.get("drossel") not in (None, "", "0x0"):
        h.append("pi_strom")
    if (b.get("temperatur") or 0) >= 80:
        h.append("pi_heiss")
    if PL.online(g["id"]) and b.get("hdmi") is False:
        h.append("pi_kein_hdmi")
    if g.get("anzeige_modus") == "direkt":       # Direktmodus (seit 0.24)
        if klasse == "pi3":
            h.append("pi_direkt_pi3")
        elif b.get("browser") is False:
            h.append("pi_direkt_kein_browser")
        elif b.get("rueckfall"):
            h.append("pi_direkt_rueckfall")
        if klasse != "pi3" and PL.ram_knapp_direkt(b.get("ram_mb")):
            h.append("pi_direkt_ram")     # nur Hinweis (seit 0.34): Chromium samt Cache liegt mit Schreibschutz im RAM
    return h


def player_server():
    """Adresse, unter der die Pis den Server erreichen: eingestellt, sonst eigene IP mit Webhook-Port."""
    ip = eigene_ip()
    if not ip and not CONTAINER:                 # ohne Home Assistant: Adresse der Standardroute (im Container wäre es die interne)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("192.0.2.1", 9))
                ip = s.getsockname()[0]
        except OSError:
            ip = None
    return PL.daten["server"] or (f"http://{ip}:{WEBHOOK_PORT}" if ip else "")


def player_schleife():
    """Jede Minute: Ausfall eines Players melden (5 min ohne Meldung), sonntags 3 Uhr Systemupdates anstoßen."""
    weg = {}
    while True:
        time.sleep(60)
        try:
            for g in PL.daten["geraete"]:
                s = PL.zuletzt(g["id"])                # Agent: letzte Meldung; Browser-Gerät: letzter Datenabruf
                if s and time.time() - s > 300:
                    if not weg.get(g["id"]):
                        weg[g["id"]] = True
                        melder.melden("player-" + g["id"], "ausfall", "player_aus", name=g["name"])
                elif s:
                    weg.pop(g["id"], None)
                    melder.vorbei("player-" + g["id"], "player_wieder", name=g["name"])
            PL.wochenpflege()
        except Exception as ex:
            print("Player:", ex, flush=True)


# ---------- Benachrichtigungen (seit 0.16) ----------
melder = BN.Melder(lambda: einst(), lambda pfad, daten: ha.post(pfad, daten))


dup_stand, dup_hoch = {}, {}              # je Fernseher: (Bilder, doppelte) der letzten Prüfung, Minuten mit vielen doppelten


def ton_neu_starten():
    """PulseAudio (läuft als signagecast) beenden und alle Ketten neu starten – tv-render.sh startet PulseAudio neu."""
    for pid in os.listdir("/proc"):
        try:
            if pid.isdigit() and open(f"/proc/{pid}/comm").read().strip() == "pulseaudio":
                os.kill(int(pid), signal.SIGTERM)
        except OSError:
            pass
    return any([kette_neu_starten(t["id"]) for t in einst()["fernseher"]])


def benachrichtigung_schleife():
    """Jede Minute: Fernseher-Ausfall (2 Prüfungen in Folge), neue Update-/Sicherungsfehler, HA länger als 5 min getrennt."""
    DS.aufraeumen(set())                         # nach einem Neustart: keine alten Sprachdateien liegen lassen
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
                        melder.melden("ausfall-" + t["id"], "ausfall", "ausfall", tv=t["name"])
                else:
                    kaputt.pop(t["id"], None)
                    melder.vorbei("ausfall-" + t["id"], "ausfall_vorbei", tv=t["name"])
            u = update_status() or {}
            if u.get("ts") != gesehen_update:
                gesehen_update = u.get("ts")
                if u.get("meldung"):                       # seit 0.38: Ergebnis jedes Updates ins Protokoll
                    PROTOKOLL.eintragen("SignageCast", "system", "update_ergebnis", f"{u.get('aktion') or ''}: {u.get('meldung')}")
                if u.get("phase") == "fehler" or (u.get("phase") == "zurueck" and u.get("aktion") != "zurueck"):
                    melder.melden(f"update-{u.get('ts')}", "update", "update", aktion=u.get("aktion"), meldung=u.get("meldung"),
                                  zeit=u.get("zeit"))
            sa = zustand.get("sicherung_auto") or {}
            if sa.get("fehler") and sa.get("zeit") != gesehen_sicherung:
                gesehen_sicherung = sa["zeit"]
                melder.melden(f"sicherung-{sa['zeit']}", "sicherung", "sicherung", zeit=sa["zeit"], fehler=sa["fehler"])
            durchsagen_aktiv()                     # abgelaufene Durchsagen und ihre Sprachdateien entfernen (Datenschutz)
            # Doppelte Bilder der Aufnahme (seit 0.18): mehr als 3 je Sekunde, 3 Minuten in Folge -> melden. Beobachtet am
            # 2026-10-31 mit Echtzeit-Ton; behoben durch Neustart von PulseAudio (Knopf im Leistungstest)
            for t in einst()["fernseher"]:
                f = ff_fortschritt(t["id"]) if kette_laeuft(t["id"]) else {}
                alt = dup_stand.get(t["id"])
                try:
                    neu = (int(f["frame"]), int(f["dup_frames"]))
                except (KeyError, ValueError):
                    dup_stand.pop(t["id"], None); dup_hoch.pop(t["id"], None)
                    continue
                dup_stand[t["id"]] = neu
                if alt and neu[0] > alt[0]:
                    dup_hoch[t["id"]] = dup_hoch.get(t["id"], 0) + 1 if (neu[1] - alt[1]) / 60 > 3 else 0
                    if dup_hoch[t["id"]] == 3:
                        melder.melden("doppelt-" + t["id"], "leistung", "doppelt", tv=t["name"])
                    elif dup_hoch[t["id"]] == 0:
                        melder.vorbei("doppelt-" + t["id"], "doppelt_vorbei", tv=t["name"])
            # Bildrate der TV-Seite: 5 Minuten im Schnitt unter 20 Bildern/s -> melden (seit 0.18)
            for t in einst()["fernseher"]:
                br = [x for x in (zustand.get("bildrate") or {}).get(t["id"], []) if time.time() - x["t"] < 330]
                schnitt = sum(x["fps"] for x in br) / len(br) if len(br) >= 25 else None
                if schnitt is not None and schnitt < 20:
                    melder.melden("leistung-" + t["id"], "leistung", "leistung", tv=t["name"], fps=f"{schnitt:.0f}")
                elif schnitt is not None and schnitt >= 22 or not kette_laeuft(t["id"]):
                    melder.vorbei("leistung-" + t["id"], "leistung_vorbei", tv=t["name"])
            # Internet weg (seit 0.38): Telegram/E-Mail kommen dann meist nicht an (HA schon) – die Entwarnung nennt
            # deshalb den Zeitraum. Je Ausfall ein Eintrag im Protokoll.
            if NETZ.offline_seit and time.time() - NETZ.offline_seit > 300 and not zustand.get("internet_weg"):
                zustand["internet_weg"] = time.strftime("%H:%M", time.localtime(NETZ.offline_seit))
                melder.melden("internet", "internet", "internet", seit=zustand["internet_weg"])
                PROTOKOLL.eintragen("SignageCast", "system", "internet_weg", zustand["internet_weg"])
            elif not NETZ.offline and zustand.get("internet_weg"):
                melder.vorbei("internet", "internet_vorbei", seit=zustand["internet_weg"], bis=time.strftime("%H:%M"))
                PROTOKOLL.eintragen("SignageCast", "system", "internet_wieder", f"{zustand['internet_weg']}–{time.strftime('%H:%M')}")
                zustand["internet_weg"] = None
            sp = SP.lage(DATEN)                    # Speicher (seit 0.45): bei gelb und noch einmal bei rot melden
            if sp["stufe"] != "gruen":
                melder.melden("speicher-" + sp["stufe"], "speicher", "speicher_" + sp["stufe"], frei=SP.gb(sp["frei"]),
                              reserve=SP.gb(sp["reserve"]))
            elif sp["frei"] > 2.2 * sp["reserve"]:  # etwas Abstand, damit es an der Grenze nicht hin und her meldet
                melder.vorbei("speicher-rot", "speicher_vorbei", frei=SP.gb(sp["frei"]))
                melder.vorbei("speicher-gelb", "speicher_vorbei", frei=SP.gb(sp["frei"]))
            if einst()["ha"]["url"] and zustand["ha_fehler"]:
                ha_weg = ha_weg or time.time()
                if time.time() - ha_weg > 300:
                    code, detail = zustand.get("ha_fehler_code") or ("", "")
                    grund = zustand["ha_fehler"] if melder.sprache() == "de" or code not in BN.HA_GRUND_EN else \
                        BN.HA_GRUND_EN[code] + (f" ({detail})" if detail else "")
                    melder.melden("ha", "ha", "ha", seit=time.strftime("%H:%M", time.localtime(ha_weg)), grund=grund)
            else:
                ha_weg = None
                melder.vorbei("ha", "ha_vorbei")
        except Exception as ex:
            print("Benachrichtigung:", ex, flush=True)


# ---------- Änderungsprotokoll (seit 0.38) ----------
def verwaltung_wer(handler):
    """Wer in der Verwaltung angemeldet ist: Cockpit schickt den Benutzernamen mit (nur zur Anzeige – zugreifen darf
    ohnehin nur die angemeldete Verwaltung), im Container gibt es nur einen Zugang."""
    return PR.wer_pruefen(handler.headers.get("X-SignageCast-Benutzer"))


PROTOKOLL_PFADE = {                                # Pfad -> Kennung der Aktion (die Verwaltung übersetzt sie)
    "/api/fernnetz": "fernnetz",
    "/api/einstellungen": "einstellungen", "/api/medien/teil": "medien_neu", "/api/webhook/neu": "webhook_neu", "/api/medien/loeschen": "medien_loeschen",
    "/api/fernseher/schalten": "schalten", "/api/fernseher/nach-einschalten": "nach_einschalten",
    "/api/updates/anfrage": "update", "/api/sicherung/erstellen": "sicherung_erstellen", "/api/sicherung/loeschen": "sicherung_loeschen",
    "/api/sicherung/zip": "sicherung_einspielen", "/api/sicherung": "sicherung_einspielen", "/api/quellen/datei": "quelle_datei",
    "/api/kategorien/loeschen": "kategorie_loeschen", "/api/streams": "stream_neu", "/api/suche/starten": "suche",
    "/api/radio/sender": "radio_neu", "/api/aktion/seite-neu-laden": "seite_neu_laden", "/api/aktion/kette-neu-starten": "kette_neu",
    "/api/aktion/ton-neu": "ton_neu", "/api/layouts/wiederherstellen": "layout_wiederherstellen", "/api/pult/stimme-laden": "stimme_laden",
    "/api/pult/probe": "probedurchsage", "/api/player/neu": "player_neu", "/api/player/koppeln": "player_koppeln",
    "/api/player/einstellungen": "player_einstellungen", "/api/player/wlan-vergessen": "player_wlan", "/api/player/sammel-image": "player_image",
    "/api/meldung": "meldung", "/api/layout-vorrang": "layout", "/api/durchsage": "durchsage",
    "/api/ki/neu": "ki_neu", "/api/ki/entfernen": "ki_entfernen",
    "/api/galerie/ordner": "galerie_ordner", "/api/galerie/loeschen": "galerie_loeschen", "/api/galerie/ordnen": "galerie_ordnen",
    "/api/galerie/umbenennen": "galerie_umbenennen",
}
PROTOKOLL_MUSTER = [                               # (Muster, Kennung) – Kennung mit {0} = erste Gruppe
    (re.compile(r"/api/streams/([\w-]{11}|UC[\w-]{22})(?:/([a-z-]+))?"), "stream_{1}"),
    (re.compile(r"/api/abgelehnt/([\w-]{11}|UC[\w-]{22})/freigeben"), "stream_freigeben"),
    (re.compile(r"/api/radio/sender/([a-z0-9]{4,12})(?:/(entfernen))?"), "radio_{1}"),
    (re.compile(r"/api/einspieler/([a-z0-9]{4,12})/jetzt"), "einspieler_jetzt"),
    (re.compile(r"/api/player/([0-9a-f]{8})/terminal/(start|ende)"), "terminal_{1}"),       # nie die Eingaben („ein“)
    (re.compile(r"/api/player/([0-9a-f]{8})/(aendern|entfernen|befehl|wlan|image|link-neu)"), "player_{1}"),
]
EINST_BEREICHE_STILL = {"assistent_fertig"}        # zählt nicht als Änderung


def protokoll_verwaltung(handler, p, d, antwort):
    """Erfolgreiche Änderung aus der Verwaltung ins Protokoll – nur Art und Bereich, nie Werte (keine Geheimnisse)."""
    aktion, detail = PROTOKOLL_PFADE.get(p), ""
    if not aktion:
        for muster, k in PROTOKOLL_MUSTER:
            m = muster.fullmatch(p)
            if m:
                aktion = k.format(*m.groups()).replace("_None", "_aendern")
                break
    if not aktion:
        return
    if p == "/api/medien/teil" and not d.get("fertig"):
        return
    extra = handler.protokoll_detail or {}
    aktion = extra.get("aktion") or aktion
    if aktion == "einstellungen":
        teile = sorted(k for k in d if k not in EINST_BEREICHE_STILL and k != "layouts")
        detail = ", ".join(teile)
        lay = extra.get("layouts") or {}
        for k in ("neu", "geaendert", "geloescht"):
            if lay.get(k):
                detail += ("; " if detail else "") + f"layouts.{k}: " + ", ".join(lay[k])
        if not detail:
            return                                 # nichts geändert (z. B. Layouts unverändert gespeichert)
    elif extra.get("text"):
        detail = extra["text"]
    elif d.get("tv") and fernseher(str(d["tv"])):
        detail = fernseher(str(d["tv"]))["name"] + (" – an" if d.get("an") is True else " – aus" if d.get("an") is False else "")
    elif aktion.startswith("stream"):
        sid = re.sub(r"^/api/(streams|abgelehnt)/?", "", p).split("/")[0] or ""
        x = streams.alle()["streams"].get(sid) if sid else None
        detail = (x or {}).get("name") or (antwort.get("stream") or {}).get("name") or sid
    elif aktion == "update":
        detail = str(d.get("aktion", ""))[:30]
    elif aktion.startswith(("player_", "terminal_")):
        m = re.search(r"/api/player/([0-9a-f]{8})", p)
        g = next((g for g in PL.daten["geraete"] if m and g["id"] == m.group(1)), None)
        detail = g["name"] if g else ""
    PROTOKOLL.eintragen(verwaltung_wer(handler), "verwaltung", aktion, detail)


# ---------- Bildprüfung (seit 0.38): schwarzes oder eingefrorenes Bild erkennen und selbst beheben ----------
AUSGABE = AG.Pruefer()
ausgabe_massnahme = {}                             # tv -> {"n": Maßnahmen seit dem letzten guten Befund, "befund"}


def ausgabe_schleife():
    """Alle 2 min je laufendem Fernseher ein Miniaturbild vom virtuellen Bildschirm prüfen (app/ausgabe.py).
    Befund schwarz/steht: 1. TV-Seite neu laden; 2. kommt er wieder: Kette neu starten und melden; danach nur melden."""
    time.sleep(90)
    while True:
        try:
            e = einst()
            jetzt = time.strftime("%Y-%m-%dT%H:%M")
            for t in e["fernseher"]:
                if not kette_laeuft(t["id"]):
                    AUSGABE.vergessen(t["id"])
                    if time.time() - (ausgabe_massnahme.get(t["id"]) or {}).get("zeit", 0) > 600:
                        ausgabe_massnahme.pop(t["id"], None)      # niemand schaut mehr (nicht: gerade neu gestartet)
                    continue
                lay = layout_fuer(t, e["layouts"])
                uhr = any(x["typ"] == "uhr" and x["sichtbar"] and not x["bedingung"] and L.im_zeitraum(x, jetzt)
                          for x in lay.get("elemente", []))
                aw, ah = aufnahme_fuer(t)
                befund = AUSGABE.pruefen(t["id"], AG.aufnehmen(anzeige_nr(t), aw, ah), bool(lay.get("schwarz")),
                                         uhr and not alarm_fuer(t["id"]), time.time())
                if befund in ("schwarz", "steht"):
                    n = (ausgabe_massnahme.get(t["id"]) or {}).get("n", 0) + 1
                    ausgabe_massnahme[t["id"]] = {"n": n, "befund": befund, "zeit": time.time()}
                    AUSGABE.vergessen(t["id"])            # nach der Maßnahme neu zählen
                    if n == 1:
                        ok = False
                        try:
                            ok = wache.seite_neu_laden(wache.BASIS_PORT + t["nr"])
                        except Exception:
                            pass
                        print(f"Bildprüfung {t['id']}: {befund} – TV-Seite neu geladen ({ok})", flush=True)
                        PROTOKOLL.eintragen("SignageCast", "system", "bild_neu_laden", f"{t['name']}: {befund}")
                    else:
                        if n == 2:
                            kette_neu_starten(t["id"])
                            print(f"Bildprüfung {t['id']}: {befund} – Kette neu gestartet", flush=True)
                            PROTOKOLL.eintragen("SignageCast", "system", "bild_kette_neu", f"{t['name']}: {befund}")
                        melder.melden("bild-" + t["id"], "ausfall", "bild_" + befund, tv=t["name"])
                elif befund == "ok":
                    if ausgabe_massnahme.pop(t["id"], None):
                        print(f"Bildprüfung {t['id']}: wieder in Ordnung", flush=True)
                    melder.vorbei("bild-" + t["id"], "bild_vorbei", tv=t["name"])
        except Exception as ex:                    # nie die Schleife verlieren
            print("Bildprüfung:", repr(ex), flush=True)
        time.sleep(AG.TAKT_S)


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


# ---------- Webseite als Bildschirmfoto (seit 0.20) ----------
WEBBILD = os.path.join(DATEN, "webbild")


def webbild_auftrag(e):
    """Baustein „Webseite“ im Modus Bild -> Auftrag für den Fotografen (Größe wie der iframe: Feld / Zoom + Ausschnitt)."""
    o = e["optionen"]
    if e["typ"] != "webseite" or o.get("modus") != "bild" or not o.get("url"):
        return None
    skala = (o.get("zoom") or 100) / 100
    gr = lambda felder, versatz: max(40, min(WB.GROESSE_MAX, round(felder * 40 / skala + versatz)))
    return {"url": o["url"], "breite": gr(e["w"], o.get("versatz_x", 0)), "hoehe": gr(e["h"], o.get("versatz_y", 0)),
            "faktor": 1, "alle_min": o.get("neu_laden_min") or 60}         # 0 = „nie“ heißt hier: stündlich


def webbild_auftraege():
    """Nur Bausteine der aktuell gezeigten Layouts laufender Fernseher."""
    e, aus = einst(), []
    for t in e["fernseher"]:
        if kette_laeuft(t["id"]):
            lay = layout_fuer(t, e["layouts"])
            jetzt = time.strftime("%Y-%m-%dT%H:%M")
            aus += [a for a in (webbild_auftrag(x) for x in lay.get("elemente", []) if x["sichtbar"] and L.im_zeitraum(x, jetzt)) if a]
    return aus


fotograf = WB.Fotograf(WEBBILD, webbild_auftraege, lambda: einst()["sprache"] or "en")


# ---------- PDF (seit 0.21) ----------
PDF_ORDNER = os.path.join(DATEN, "pdf")


def pdf_schleife():
    """Stündlich: umgewandelte PDFs entfernen, die kein Layout mehr nutzt, und Reste gelöschter Fernseher."""
    while True:
        PDF.aufraeumen(PDF_ORDNER, {x["optionen"]["datei"] for l in einst()["layouts"] for x in l["elemente"] if x["typ"] == "pdf"})
        fernseher_reste_entfernen({t["id"] for t in einst()["fernseher"]})   # Kette lief beim Löschen noch
        try:
            GALERIE.aufraeumen({o["id"] for o in einst()["galerie"]["ordner"]})   # seit 0.45
        except Exception as f:
            print("Galerie aufräumen:", repr(f), flush=True)
        time.sleep(3600)


# ---------- Fernseher über HA schalten (seit 0.21) ----------
# Beginnt im Zeitplan „schwarz“, wird der Fernseher ausgeschaltet; endet es (oder kommt ein Notfall-Vollbild), wird er
# eingeschaltet. Nur beim Wechsel – wer nachts von Hand einschaltet, wird nicht gleich wieder ausgeschaltet.
schalten_neu = threading.Event()
schalten_stand = {}                               # tv -> {"soll", "zeit", "fehler", "versuche"}


def schalten_soll(t):
    lay = layout_fuer(t)
    return "an" if alarm_fuer(t["id"]) or not lay.get("schwarz") else "aus"


def tv_schalten(t, an):
    ent = t["ha_schalten"]
    try:
        ha.post(f"/api/services/{ent.split('.')[0]}/turn_{'on' if an else 'off'}", {"entity_id": ent})
    except HAFehler as f:
        if f.detail.startswith("400 "):            # HA: Entität bietet turn_on/turn_off nicht an (z. B. Samsung ohne WoL)
            raise M.Meldung("sch_an_nicht" if an else "sch_aus_nicht", e=ent) from None
        raise
    if an and (t.get("ha_quelle") and ent.startswith("media_player.") or t.get("ha_oeffnen")):
        threading.Thread(target=nach_einschalten, args=(t,), daemon=True).start()


QUELLE_WARTEN_S = 90                               # so lange darauf warten, dass der Fernseher nach dem Einschalten bereit ist
AUS_ZUSTAENDE = ("off", "standby")
WEG_ZUSTAENDE = ("unavailable", "unknown")


def tv_adresse(t):
    ip = eigene_ip()
    if not ip:
        raise M.Meldung("sch_keine_ip")
    return f"http://{ip}:{HLS_PORT}/{t['id']}"


def oeffnen_aufruf(t):
    """(Dienst, Daten), mit denen HA die TV-Seite auf dem Fernseher öffnet (seit 0.37)."""
    ent, url = t["ha_schalten"], tv_adresse(t)
    if t["ha_oeffnen"] == "lg":                   # LG webOS: Browser mit Adresse
        return "webostv.command", {"entity_id": ent, "command": "system.launcher/open", "payload": {"target": url}}
    if t["ha_oeffnen"] == "android":              # Android TV / Google TV / Fire TV (Integration androidtv, ADB)
        return "androidtv.adb_command", {"entity_id": ent, "command": f"am start -a android.intent.action.VIEW -d {url}"}
    if t["ha_oeffnen"] == "eigen" and t["ha_dienst"]:
        daten = json.loads(json.dumps(json.loads(t["ha_daten"] or "{}")).replace("{url}", url).replace("{entity}", ent))
        daten.setdefault("entity_id", ent)
        return t["ha_dienst"], daten
    return None


def nach_einschalten(t, warten=QUELLE_WARTEN_S, takt=3):
    """Seit 0.37: nach dem Einschalten Quelle wählen (z. B. „HDMI 2“) und/oder die TV-Seite öffnen. Wartet, bis HA den
    Fernseher als eingeschaltet meldet (und die Quelle anbietet). Ergebnis in schalten_stand[tv]["nach"]."""
    ent, quelle = t["ha_schalten"], t.get("ha_quelle") if t["ha_schalten"].startswith("media_player.") else ""
    ende, fehler, schritte = time.time() + warten, "nicht bereit", []
    while True:
        try:
            s = ha.get(f"/api/states/{ent}")
            a = s.get("attributes") or {}
            liste = a.get("source_list") or []
            if quelle and liste and quelle not in liste:
                fehler = "unbekannte Quelle"
            elif s.get("state") not in AUS_ZUSTAENDE + WEG_ZUSTAENDE:
                if warten:
                    time.sleep(takt)              # frisch eingeschaltete Fernseher nehmen Befehle erst kurz danach an
                if quelle and a.get("source") != quelle:
                    ha.post("/api/services/media_player/select_source", {"entity_id": ent, "source": quelle})
                    schritte.append("quelle")
                aufruf = oeffnen_aufruf(t) if t.get("ha_oeffnen") else None
                if aufruf:
                    if quelle:
                        time.sleep(takt)
                    ha.post("/api/services/" + aufruf[0].replace(".", "/", 1), aufruf[1])
                    schritte.append("oeffnen")
                fehler = None
                break
        except M.Meldung as ex:
            fehler = M.als_dict(ex)["text"]
            break
        except Exception as ex:
            fehler = str(ex)[:200]
        if time.time() >= ende:
            break
        time.sleep(takt)
    st = schalten_stand.setdefault(t["id"], {"soll": "an", "entity": ent, "zeit": None, "fehler": None, "versuche": 0})
    st["nach"] = {"zeit": time.strftime("%H:%M"), "fehler": fehler, "schritte": schritte, "quelle": quelle, "oeffnen": t.get("ha_oeffnen", "")}
    if fehler:
        print(f"Fernseher {t['id']}: nach dem Einschalten nicht ausgeführt:", fehler, flush=True)
    return fehler


def zustand_abfragen():
    """Seit 0.37: Zustand der Fernseher laut HA (an / aus / weg) – einmal je Minute, nur mit eingetragener Entität."""
    if not einst()["ha"]["url"]:
        return
    for t in einst()["fernseher"]:
        if not t["ha_schalten"]:
            continue
        st = schalten_stand.get(t["id"])
        if st is None:
            continue
        try:
            s = ha.get(f"/api/states/{t['ha_schalten']}")
            roh = str(s.get("state", ""))
            st["ha"] = {"zustand": "aus" if roh in AUS_ZUSTAENDE else "weg" if roh in WEG_ZUSTAENDE else "an", "roh": roh[:30],
                        "quelle": str((s.get("attributes") or {}).get("source") or "")[:60], "zeit": int(time.time())}
        except Exception as ex:
            st["ha"] = {"zustand": "fehler", "roh": str(ex)[:120], "quelle": "", "zeit": int(time.time())}


def schalten_einmal(erster=False):
    for t in einst()["fernseher"]:
        if not t["ha_schalten"] or not einst()["ha"]["url"]:
            schalten_stand.pop(t["id"], None)
            continue
        soll, st = schalten_soll(t), schalten_stand.get(t["id"])
        if erster or not st or st.get("entity") != t["ha_schalten"]:     # beim Start nur merken, nichts schalten
            schalten_stand[t["id"]] = {"soll": soll, "entity": t["ha_schalten"], "zeit": None, "fehler": None, "versuche": 0}
            continue
        if soll == st["soll"] and not (st["fehler"] and st["versuche"] < 5):
            continue
        try:
            tv_schalten(t, soll == "an")
            st.update(soll=soll, zeit=time.strftime("%H:%M"), fehler=None, versuche=0)
        except Exception as ex:
            st.update(soll=soll, zeit=time.strftime("%H:%M"), fehler=str(ex)[:200], versuche=st["versuche"] + 1)
            print(f"Fernseher {t['id']} {soll}schalten:", ex, flush=True)


def schalten_schleife():
    erster, zuletzt = True, 0
    while True:
        schalten_einmal(erster)
        erster = False
        if time.time() - zuletzt >= 60:
            zuletzt = time.time()
            try:
                zustand_abfragen()
            except Exception as ex:
                print("Zustand der Fernseher:", ex, flush=True)
        schalten_neu.wait(30)
        schalten_neu.clear()


def tv_daten(tv_id, vorschau_layout=None):
    e = einst()
    t = fernseher(tv_id)
    if not t:
        return {"ok": False, "fehler": "unbekannter Fernseher"}
    v = e["video"]
    # vorschau_layout (seit 0.39): ein bestimmtes Layout zeigen – nur für Vorschaubilder, ändert nichts
    layout = next((l for l in e["layouts"] if l["id"] == vorschau_layout), None) if vorschau_layout else None
    layout = layout or layout_fuer(t, e["layouts"])
    hat_video = any(x["typ"] == "video" and x["sichtbar"] for x in layout.get("elemente", []))
    vr = streams.vorrang if streams.vorrang and streams.vorrang["bis"] > time.time() \
        and streams.vorrang.get("tv") in (None, t["id"]) else None
    sender = next((x for x in e["radio"]["sender"] if x["id"] == t["radio_sender"]), None)
    liste = [x for x in streams.liste if x["kategorie"] not in t["kategorien_aus"]] \
        if v["aktiv"] and t["video"] and hat_video and t["video_quelle"] != "medien" else []
    alle_medien = [{"id": m["id"], "name": m["name"], "art": m["art"], "url": f"/medien/{m['datei']}", "dauer_s": m["dauer_s"]}
                   for m in e["medien"] if m["aktiv"]] if t["video"] and hat_video else []
    medien = alle_medien if t["video_quelle"] != "youtube" else []
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
                version=VERSION,                  # seit 0.28.1: TV-Seite lädt nach einem Update neu
                einspieler=eins if hat_video else [],
                zeit_abweichung_ms=round((zt.get("abweichung_s") or 0) * 1000) if zt.get("korrektur") else 0,
                zeitzone=wirksame_zeitzone(),
                einspieler_jetzt=zustand.get("einspieler_jetzt") if zustand.get("einspieler_jetzt", {}).get("bis", 0) > time.time() else None,
                tv=t["id"], layout=layout, kalender=kal, api=api,
                webbild={x["id"]: fotograf.bild(a) for x in layout.get("elemente", []) if (a := webbild_auftrag(x))},
                pdf={x["id"]: {"datei": x["optionen"]["datei"], "seiten": PDF.seiten(PDF_ORDNER, x["optionen"]["datei"])}
                     for x in layout.get("elemente", []) if x["typ"] == "pdf" and x["optionen"]["datei"]},
                # Galerie (seit 0.45): je gezeigtem Ordner nur der Stand – die Folien holt die Seite bei einer Änderung
                galerie={oid: GALERIE.stand(oid) for oid in galerie_im_layout(layout) if oid in {o["id"] for o in e["galerie"]["ordner"]}},
                jetzt_lokal=time.strftime("%Y-%m-%dT%H:%M"), alarm=alarm_fuer(t["id"]),
                medien=medien, medien_modus=t["video_quelle"], medien_alle=t["medien_alle"],
                # Internet weg (seit 0.38): statt der Live-Kameras eigene Medien im Kreis, sonst ein ruhiges Bild
                offline=NETZ.offline, ersatz={"medien": alle_medien, "bild": "bilder/stile/" + (
                    layout["hintergrund"]["stil"] if layout.get("hintergrund", {}).get("art") == "stil" else "natur") + f"-{tz}.jpg"},
                unwetter=(zustand.get("unwetter") or {}).get("liste", []),
                meldung_extern=meldung_fuer(t["id"]),
                durchsage=durchsage_fuer(t["id"]), streams=liste, allgemein=streams.allgemein_aktiv(), vorrang=vr if liste else None, versatz=t["nr"],
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
        raise E.Fehler("e_bild_gross")
    if daten[:3] == b"\xff\xd8\xff":
        endung = "jpg"
    elif daten[:8] == b"\x89PNG\r\n\x1a\n":
        endung = "png"
    else:
        raise E.Fehler("e_bild_art")
    SP.pruefen(DATEN, len(daten))
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


def vorab_schleife():
    """Vorabprüfung (seit 0.31): prüft die vom Player angekündigten Streams, sobald er sie meldet – getrennt vom
    5-min-Durchlauf und vom Wechsel am Fernseher. Ein Strike baut die Liste ebenfalls sofort neu (Pause für alle)."""
    while True:
        streams.vor_wecken.wait(60)
        streams.vor_wecken.clear()
        try:
            streams.vorpruefen()
        except Exception as ex:
            streams.status["vorab"] = {"zeit": time.strftime("%Y-%m-%d %H:%M"), "fehler": str(ex)[:300]}


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


def doppelt_hoch(e):
    return [t for t in e["fernseher"] if dup_hoch.get(t["id"], 0) >= 3]


def bildrate_niedrig(e):
    def niedrig(br):
        return len(br) >= 6 and sum(x["fps"] for x in br) / len(br) < 20
    return [t for t in e["fernseher"] if kette_laeuft(t["id"]) and
            niedrig([x for x in (zustand.get("bildrate") or {}).get(t["id"], []) if time.time() - x["t"] < 90])]


def todo_warnungen(e):
    """Warnungen für „Zu erledigen“ (seit 0.35 hier statt in der Verwaltung): Kennung + Werte für den Text. Die Kennung
    braucht die Prüfschleife, um ausgeblendete Warnungen wieder freizugeben, sobald das Problem weg war."""
    w = []
    if e["ha"]["url"] and zustand["ha_fehler"] is not None:
        w.append({"key": "ha"})
    w += [{"key": "bildrate:" + t["id"], "name": t["name"]} for t in bildrate_niedrig(e)]
    a = streams.allgemein_aktiv()
    if a:
        w.append({"key": "allgemein", "grund": a["grund"], "seit": a["seit"]})
    w += [{"key": "doppelt:" + t["id"], "name": t["name"]} for t in doppelt_hoch(e)]
    w += [{"key": "player:" + g["id"], "name": g["name"]} for g in PL.daten["geraete"] if PL.gesehen(g["id"]) and not PL.online(g["id"])]
    if (zustand.get("sicherung_auto") or {}).get("fehler"):
        w.append({"key": "sicherung_fehler"})
    if any(any((x.get("ergebnis") or {}).values()) for x in melder.letzte or []):
        w.append({"key": "bn_fehler"})
    if e["anzeige"]["wetter_quelle"] == "met" and met.fehler:
        w.append({"key": "wetter"})
    if NETZ.offline:                                       # seit 0.38
        w.append({"key": "internet", "seit": time.strftime("%H:%M", time.localtime(NETZ.offline_seit))})
    w += [{"key": "bild:" + t["id"], "name": t["name"], "befund": ausgabe_massnahme[t["id"]]["befund"]}
          for t in e["fernseher"] if ausgabe_massnahme.get(t["id"])]
    for art in ("pi", "pc"):                               # seit 0.47: Grundimage älter als SignageCast → neu laden
        alt = PL.basis_veraltet(VERSION, art)
        if alt:
            w.append({"key": f"player_basis:{art}:{VERSION}", "art": art, "alt": alt, "neu": VERSION})
    sp = SP.lage(DATEN)                                    # seit 0.45: gelb = Hinweis, rot = Uploads gesperrt
    if sp["stufe"] != "gruen":
        w.append({"key": "speicher", "stufe": sp["stufe"], "frei": SP.gb(sp["frei"]), "reserve": SP.gb(sp["reserve"])})
    return w


def todo_schleife():
    """Ausgeblendete Warnungen freigeben, sobald das Problem weg war. Erst 5 min nach dem Start: vorher sind HA, Wetter
    und Player noch nicht geprüft und sähen „in Ordnung“ aus."""
    time.sleep(300)
    while True:
        try:
            weg = TODO.pruefen({x["key"] for x in todo_warnungen(einst())}, zustand.get("neue_version"))
            if weg:
                print("Zu erledigen: wieder eingeblendet:", ", ".join(weg), flush=True)
        except Exception as f:                  # nie die Schleife verlieren
            print("Zu erledigen:", repr(f), flush=True)
        time.sleep(60)


def status():
    m = {}
    for z in open("/proc/meminfo"):
        k, w = z.split(":")
        m[k] = int(w.split()[0])
    sv = os.statvfs(DATEN if os.path.isdir(DATEN) else "/")   # seit 0.45 das Datenverzeichnis (Docker: das Volume)
    e = einst()
    return {"schalten": schalten_stand, "speicher": SP.lage(DATEN),
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
        "sicherung_auto": zustand.get("sicherung_auto"),
        "allgemein": streams.allgemein_aktiv(),
        "doppelt_hoch": [t["name"] for t in doppelt_hoch(e)],
        "bildrate_niedrig": [t["name"] for t in bildrate_niedrig(e)],
        "todo_warn": todo_warnungen(e), "todo_aus": TODO.liste(),
        "netz": NETZ.stand(),                                       # seit 0.38
        "fernseher": [fernseher_status(t) for t in e["fernseher"]],
        "player": [{"id": g["id"], "name": g["name"], "online": PL.online(g["id"]), "gesehen": PL.gesehen(g["id"])}
                   for g in PL.daten["geraete"]],
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
            "layout": layout_fuer(t)["name"],
            "radio_neu_verbunden": zustand.get("radio_neu", {}).get(t["id"], 0),
            "encoder": encoder_fuer(t), "kodier_fehler": zustand["kodier_fehler"].get(t["id"]),
            "bild": AUSGABE.befund(t["id"]) if kette_laeuft(t["id"]) else "",                  # seit 0.38: Bildprüfung
            "pult_layout": (lambda v: {"name": layout_fuer(t)["name"], "bis": int(v["bis"]), "von": v["von"]}
                            if v and v["bis"] > time.time() else None)(layout_vorrang.get(t["id"]))}


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
    aw, ah = aufnahme_fuer(t)
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "x11grab", "-video_size", f"{aw}x{ah}", "-i", anzeige_nr(t),
                        "-frames:v", "1", "-vf", "scale=960:-1", "-f", "mjpeg", "-"], capture_output=True, timeout=15)
    return r.stdout if r.returncode == 0 and r.stdout else None


vorschau_sperre = threading.Lock()


def vorschau_bild(tv_id, layout_id=""):
    """TV-Seite eines Fernsehers (wahlweise mit einem bestimmten Layout) in einem kurzlebigen Headless-Chromium
    fotografieren, 960 × 540 (seit 0.39). Nur eine Aufnahme gleichzeitig, niedrige Priorität."""
    t = fernseher(tv_id) or (einst()["fernseher"][0] if not tv_id else None)
    if not t:
        raise KeyError(f"unbekannter Fernseher {tv_id}")
    if layout_id and not any(l["id"] == layout_id for l in einst()["layouts"]):
        raise KeyError(f"unbekanntes Layout {layout_id}")
    url = f"http://127.0.0.1:{os.environ.get('SC_PORT', '8080')}/?tv={t['id']}&vorschau=1" + (f"&layout={layout_id}" if layout_id else "")
    ziel = os.path.join(DATEN, "vorschau-mcp.png")
    if not vorschau_sperre.acquire(timeout=60):
        raise RuntimeError("Vorschau beschäftigt")
    try:
        WB.aufnehmen(url, 1920, 1080, 0.5, ziel, einst()["sprache"] or "en")
        return open(ziel, "rb").read()
    finally:
        vorschau_sperre.release()


def schreib_wenn_anders(pfad, inhalt):
    try:
        if open(pfad).read() == inhalt:
            return
    except OSError:
        pass
    with open(pfad, "w") as f:
        f.write(inhalt)


def braucht_ton(t, e):
    """Kann auf diesem Fernseher überhaupt Ton laufen? (Fernseher-Ton, Einspieler mit Ton, Kamera mit Ton)
    Wenn nicht, nimmt die Kette Stille statt Echtzeit-Ton auf – ein Echtzeit-Toneingang lässt ffmpeg 7.1 bei x11grab
    bis zu 85 % der Bilder doppeln (gemessen 2026-10-31), der Stream ruckelt."""
    if t["ton"] != "aus":
        return True
    p = e.get("pult") or {}
    if p.get("vorlesen") and any(not z["fernseher"] or t["id"] in z["fernseher"] for z in p.get("zugaenge", [])):
        return True
    if any(x["aktiv"] and x["ton"] and (not x.get("fernseher") or t["id"] in x["fernseher"]) for x in e.get("einspieler", [])):
        return True
    ids = {t["layout"]} | {z.get("layout") for z in t.get("zeitplan", [])} | set((t.get("karussell") or {}).get("layouts", []))
    return any(el["typ"] == "webcam" and el["optionen"].get("ton") for l in e["layouts"] if l["id"] in ids for el in l["elemente"])


def codec_fuer(t):
    """Tatsächlicher Codec eines Fernsehers: in Software immer H.264; „auto“ = H.265 bei 4K, H.264 bei Full HD."""
    if encoder_fuer(t) == "software":
        return "h264"
    return t["codec"] if t["codec"] != "auto" else ("h265" if t["aufloesung"] == 2160 else "h264")


def encoder_fuer(t):
    """Tatsächlicher Encoder: der gewählte, wenn er auf diesem Rechner geht und seine Probe bestanden hat – sonst
    automatisch (VAAPI, ohne nutzbare Grafik Software). Solange die Erkennung noch läuft: VAAPI wie bisher."""
    k = zustand.get("kodierung") or {}
    auto = "software" if k.get("art") == "software" else "vaapi"
    w = t.get("encoder", "auto")
    if w == "auto" or not ((k.get("encoder") or {}).get(w) or {}).get("ok") or t["id"] in zustand["kodier_fehler"]:
        return auto
    return w


def aufnahme_fuer(t):
    """(Breite, Höhe), in der Chromium die TV-Seite zeichnet (seit 0.29 je Fernseher). In Software kodiert die CPU
    genau diese Größe – dort höchstens Full HD."""
    h = t.get("aufnahme", 1080)
    if encoder_fuer(t) == "software":
        h = min(h, 1080)
    return h * 16 // 9, h


def video_fuer(t):
    """(Encoder, Ausgabegröße, ffmpeg-Argumente) eines Fernsehers. Weicht etwas vom bewährten Standard ab (anderer
    Encoder, Preset, Tune oder B-Frames), wird es einmal probekodiert; geht der Encoder hier nicht oder scheitert die
    Probe, gilt „Automatisch“ und der Grund steht beim Fernseher (zustand["kodier_fehler"])."""
    k, fehler = zustand.get("kodierung"), zustand["kodier_fehler"]
    fehler.pop(t["id"], None)

    def standard():
        enc = encoder_fuer(t)
        ow, oh = aufnahme_fuer(t) if enc == "software" else (3840, 2160) if t["aufloesung"] == 2160 else (1920, 1080)
        return enc, (ow, oh), HW.video_args(enc, codec_fuer(t), ow, oh)
    w = t.get("encoder", "auto")
    if not k or (w == "auto" and t["preset"] == "veryfast" and t["tune"] == "zerolatency" and not t["bframes"]):
        return standard()
    if w != "auto" and not (k.get("encoder") or {}).get(w, {}).get("ok"):
        fehler[t["id"]] = {"encoder": w, "grund": (k.get("encoder") or {}).get(w, {}).get("grund") or k.get("grund") or "unbekannt"}
        return standard()
    enc = encoder_fuer(t)
    ow, oh = aufnahme_fuer(t) if enc == "software" else (3840, 2160) if t["aufloesung"] == 2160 else (1920, 1080)
    args = HW.video_args(enc, codec_fuer(t), ow, oh, t["preset"], t["tune"], t["bframes"])
    if args not in zustand["probe"]:
        zustand["probe"][args] = HW.probe(args)
    ok, grund = zustand["probe"][args]
    if ok:
        return enc, (ow, oh), args
    fehler[t["id"]] = {"encoder": enc, "grund": grund}
    return standard()


# ---------- Leistungstest (seit 0.18) ----------
def ff_fortschritt(tv_id):
    """Letzter Fortschritts-Block von ffmpeg (tv-render.sh schreibt ihn alle 2 s nach /dev/shm)."""
    try:
        return dict(z.split("=", 1) for z in open(f"/dev/shm/signagecast-ff-{tv_id}").read().split("\n") if "=" in z)
    except OSError:
        return {}


def sitzungs_cpu():
    """CPU-Zeit (Ticks) je Sitzung – die Render-Kette startet Xvfb, Chromium und ffmpeg je in einer eigenen Sitzung."""
    je = {}
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                f = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
                je[int(f[3])] = je.get(int(f[3]), 0) + int(f[11]) + int(f[12])
            except (OSError, IndexError, ValueError):
                pass
    return je


def gpu_takt():
    for k in sorted(glob.glob("/sys/class/drm/card*/gt_act_freq_mhz")):
        try:
            d = os.path.dirname(k)
            return int(open(k).read()), int(open(os.path.join(d, "gt_RP0_freq_mhz")).read())
        except (OSError, ValueError):
            pass
    return None


def leistung_test(dauer=10):
    """Misst dauer Sekunden lang Erzeugung (Chromium), Kodierung (ffmpeg) und System und gibt Empfehlungen."""
    e = einst()
    laufend = [t for t in e["fernseher"] if kette_laeuft(t["id"])]
    def cpu_ges():
        w = [int(x) for x in open("/proc/stat").readline().split()[1:]]
        return sum(w), w[3] + w[4]
    a_cpu, a_s, a_ff, t0 = cpu_ges(), sitzungs_cpu(), {t["id"]: ff_fortschritt(t["id"]) for t in laufend}, time.time()
    gpu = []
    for _ in range(dauer):
        time.sleep(1)
        g = gpu_takt()
        if g:
            gpu.append(g[0] / g[1] if g[1] else 0)
    b_cpu, b_s, dt = cpu_ges(), sitzungs_cpu(), time.time() - t0
    ticks = os.sysconf("SC_CLK_TCK")
    ges, leer = b_cpu[0] - a_cpu[0], b_cpu[1] - a_cpu[1]
    m = {k: int(v.split()[0]) for k, v in (z.split(":", 1) for z in open("/proc/meminfo"))}
    kerne = os.cpu_count() or 1
    erg = {"zeit": time.strftime("%Y-%m-%d %H:%M:%S"), "dauer_s": dauer,
           "system": {"cpu": round(100 * (ges - leer) / ges, 1) if ges else None, "kerne": kerne,
                      "ram_frei_mb": m.get("MemAvailable", 0) // 1024, "ram_gesamt_mb": m.get("MemTotal", 0) // 1024,
                      "gpu_last": round(100 * sum(gpu) / len(gpu)) if gpu else None,
                      "kodierung": (zustand.get("kodierung") or {}).get("art")},
           "fernseher": []}
    for t in e["fernseher"]:
        z = {"id": t["id"], "name": t["name"], "laeuft": t in laufend, "aufloesung": t["aufloesung"],
             "aufnahme": aufnahme_fuer(t)[1],
             "bitrate_mbit": t["bitrate_mbit"], "codec": codec_fuer(t), "encoder": encoder_fuer(t), "ton": braucht_ton(t, e)}
        if z["laeuft"]:
            br = [x for x in (zustand.get("bildrate") or {}).get(t["id"], []) if time.time() - x["t"] < 60]
            if br:
                z["fps_seite"] = round(sum(x["fps"] for x in br) / len(br), 1)
                z["ruckler"] = sum(x["ruckler"] for x in br)
            f0, f1 = a_ff.get(t["id"]) or {}, ff_fortschritt(t["id"])
            try:
                z["fps_kodierung"] = float(f1.get("fps", 0))
                z["tempo"] = float((f1.get("speed") or "0x").rstrip("x") or 0)
                z["doppelt"] = int(f1.get("dup_frames", 0)) - int(f0.get("dup_frames", f1.get("dup_frames", 0)))
                z["verworfen"] = int(f1.get("drop_frames", 0)) - int(f0.get("drop_frames", f1.get("drop_frames", 0)))
            except ValueError:
                pass
            sids = kette_pids(t["id"])
            z["cpu_kerne"] = round(sum(b_s.get(s, 0) - a_s.get(s, 0) for s in sids) / ticks / dt, 2)
        erg["fernseher"].append(z)
    erg["system"]["mediamtx_verworfen"] = mediamtx_verworfen()
    erg["empfehlungen"] = empfehlen(erg)
    zustand["leistung"] = erg
    return erg


def mediamtx_verworfen(seit_s=600):
    """Wie oft hat MediaMTX zuletzt Bilder weggeworfen („reader is too slow“)? – sichtbar als Sprung um ~1 s."""
    try:
        r = subprocess.run(["journalctl", "-u", "signagecast-mediamtx", "--since", f"-{seit_s}s", "--no-pager", "-q", "-o", "cat"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.count("too slow") if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def empfehlen(erg):
    """Ampel-Hinweise als Kennung + Werte; die Verwaltung setzt den Text in ihrer Sprache."""
    l, s = [], erg["system"]
    laufend = [t for t in erg["fernseher"] if t["laeuft"]]
    if not laufend:
        l.append({"code": "keine_kette", "stufe": "info"})
    for t in laufend:
        p = {"tv": t["name"], "aufloesung": t["aufloesung"], "bitrate": t["bitrate_mbit"], "codec": t["codec"]}
        if t.get("fps_seite") is not None and t["fps_seite"] < 22:
            l.append({"code": "seite_langsam", "stufe": "schlecht", "p": dict(p, fps=t["fps_seite"])})
        if t.get("tempo") and t["tempo"] < 0.97:
            l.append({"code": "kodierung_langsam", "stufe": "schlecht", "p": dict(p, tempo=t["tempo"])})
        if t.get("verworfen", 0) + t.get("doppelt", 0) > erg["dauer_s"] * 2:
            n = t.get("verworfen", 0) + t.get("doppelt", 0)
            seite_ok = (t.get("fps_seite") or 0) >= 22
            # Seite flüssig, aber viele Kopien und Ton live: bekannte Ursache (Echtzeit-Toneingang, siehe braucht_ton)
            l.append({"code": "ton_doppelt" if seite_ok and t["ton"] else "bilder_verloren", "stufe": "warn", "p": dict(p, n=n)})
    if s["cpu"] is not None and s["cpu"] > 85:
        l.append({"code": "cpu_hoch", "stufe": "schlecht", "p": {"cpu": s["cpu"], "kerne": s["kerne"], "ketten": len(laufend)}})
    elif s["cpu"] is not None and s["cpu"] > 70:
        l.append({"code": "cpu_knapp", "stufe": "warn", "p": {"cpu": s["cpu"], "kerne": s["kerne"], "ketten": len(laufend)}})
    if s["ram_frei_mb"] < 400:
        l.append({"code": "ram_knapp", "stufe": "schlecht", "p": {"frei": s["ram_frei_mb"]}})
    if s["gpu_last"] is not None and s["gpu_last"] > 90:
        l.append({"code": "gpu_hoch", "stufe": "warn", "p": {"gpu": s["gpu_last"]}})
    if s.get("mediamtx_verworfen"):
        l.append({"code": "mediamtx_langsam", "stufe": "schlecht", "p": {"n": s["mediamtx_verworfen"]}})
    if s["kodierung"] == "software":
        l.append({"code": "software", "stufe": "warn"})
    if laufend and not any(x["stufe"] in ("schlecht", "warn") for x in l):
        l.append({"code": "server_ok", "stufe": "gut"})
    return l


def fernseher_reste_entfernen(ids):
    """Dateien gelöschter Fernseher entfernen: render-<id>.env und das Browser-Profil chromium-<id> (seit 0.32.1).
    Nur genaue Namen (gesicherte Profile wie chromium-tv.alt-… bleiben) und nur, wenn seine Kette nicht mehr läuft."""
    weg = []
    for pfad in glob.glob(os.path.join(DATEN, "render-*.env")) + glob.glob(os.path.join(DATEN, "chromium-*")):
        name = os.path.basename(pfad)
        tid = name[len("render-"):-len(".env")] if name.startswith("render-") else name[len("chromium-"):]
        if not re.fullmatch(r"[a-z][a-z0-9]{0,11}", tid) or tid in ids or os.path.exists(os.path.join(DATEN, f"kette-{tid}.pids")):
            continue
        try:
            if os.path.isdir(pfad) and not os.path.islink(pfad):
                shutil.rmtree(pfad)
            else:
                os.remove(pfad)
            weg.append(name)
        except OSError as f:
            print(f"Reste von Fernseher {tid}: {f}", flush=True)
    if weg:
        print("Reste gelöschter Fernseher entfernt: " + ", ".join(sorted(weg)), flush=True)
    return weg


def reste_nach_kette(ids):
    """Läuft die Kette eines gerade gelöschten Fernsehers noch (MediaMTX beendet sie nach dem Neuladen), nach ihrem Ende
    aufräumen statt erst beim stündlichen Durchlauf. Ein Thread, höchstens 2 min."""
    offen = [os.path.basename(p)[len("kette-"):-len(".pids")] for p in glob.glob(os.path.join(DATEN, "kette-*.pids"))]
    if not [x for x in offen if x not in ids] or zustand.get("reste_wartet"):
        return
    zustand["reste_wartet"] = True

    def warten():
        try:
            for _ in range(60):
                time.sleep(2)
                if all(t in {x["id"] for x in einst()["fernseher"]} or not os.path.exists(os.path.join(DATEN, f"kette-{t}.pids"))
                       for t in offen):
                    break
            fernseher_reste_entfernen({t["id"] for t in einst()["fernseher"]})
        finally:
            zustand["reste_wartet"] = False
    threading.Thread(target=warten, daemon=True).start()


def render_schreiben(e):
    """Je Fernseher die Werte für tv-render.sh (wirken beim nächsten Start seiner Kette) und die MediaMTX-Pfade
    (MediaMTX lädt die Datei bei Änderung selbst neu)."""
    pfade, geaendert = "", []
    for t in e["fernseher"]:
        enc, (ow, oh), video = video_fuer(t)            # Software: H.264 in Full HD per CPU
        pfad = os.path.join(DATEN, f"render-{t['id']}.env")
        aw, ah = aufnahme_fuer(t)
        try:
            alt = open(pfad).read()
        except OSError:
            alt = None
        neu = f'VIDEO="{video}"'
        # neue Kodierung oder Aufnahmegröße: Kette neu starten (Xvfb und Chromium haben die Größe beim Start bekommen)
        if alt:
            v_alt = re.search(r"^VIDEO=.*$", alt, re.M)
            a_alt = re.search(r'^AUFNAHME="(.*)"$', alt, re.M)
            if (v_alt and v_alt.group(0) != neu) or (a_alt.group(1) if a_alt else "1920 1080") != f"{aw} {ah}":
                geaendert.append(t["id"])
        schreib_wenn_anders(pfad, f"DISP={anzeige_nr(t)}\nDEVPORT={wache.BASIS_PORT + t['nr']}\nAUSGABE=\"{ow} {oh}\"\n"
                                  f"AUFNAHME=\"{aw} {ah}\"\n"
                                  f"BITRATE={t['bitrate_mbit']}\nKODIERUNG={'software' if enc == 'software' else 'vaapi'}\n"
                                  f"CODEC={codec_fuer(t)}\n{neu}\nTON={'live' if braucht_ton(t, e) else 'stille'}\n")
        pfade += (f"  {t['id']}:\n    runOnDemand: /opt/signagecast/render/tv-render.sh\n    runOnDemandRestart: yes\n"
                  f"    runOnDemandStartTimeout: 40s\n    runOnDemandCloseAfter: {e['stream']['abschalten_s']}s\n")
    # Kameras (Datenquellen der Art „video“, RTSP/HLS): MediaMTX holt sie nur, solange jemand schaut; lesen darf sie
    # nur der Container selbst (siehe authInternalUsers in render/mediamtx.yml)
    for q in e.get("quellen", []):
        if q["art"] == "video" and q["aktiv"] and Q.video_format(q) in ("rtsp", "hls"):
            pfade += (f"  cam_{q['id']}:\n    source: {json.dumps(q['url'])}\n    sourceOnDemand: yes\n"
                      f"    sourceOnDemandStartTimeout: 15s\n    sourceOnDemandCloseAfter: 20s\n")
    fernseher_reste_entfernen({t["id"] for t in e["fernseher"]})
    reste_nach_kette({t["id"] for t in e["fernseher"]})
    try:
        if os.path.exists(MEDIAMTX_YML):
            vorlage = open(MEDIAMTX_VORLAGE).read().replace("hlsAddress: :8888", f"hlsAddress: :{HLS_PORT}")
            schreib_wenn_anders(MEDIAMTX_YML, vorlage.replace("{PFADE}", pfade.rstrip("\n")))
    except OSError:
        pass
    return geaendert


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


# ---------- CSV-Import (seit 0.26) ----------
def csv_roh(d):
    """Rohdaten für den CSV-Import: {"daten": base64} | {"datei": hash} | {"quelle": {...}} (Adresse wird geholt)."""
    if d.get("daten"):
        roh = base64.b64decode(str(d["daten"]).split(",")[-1], validate=False)
        if len(roh) > Q.MAX_DATEI:
            raise Q.Fehler("zu_gross", mb=Q.MAX_DATEI // 1_000_000)
        return roh
    if d.get("datei"):
        return Q.datei_lesen(str(d["datei"]))
    if isinstance(d.get("quelle"), dict):
        roh = [dict(d["quelle"], art="text", herkunft="url")]
        Q.demaskieren(roh, einst()["quellen"])
        return Q.holen(Q.pruefen(roh)[0])[0]
    raise M.Meldung("csv_leer")


def csv_analysieren(d):
    return CSV.analysieren(csv_roh(d), d.get("optionen") if isinstance(d.get("optionen"), dict) else None)


# ---------- Sicherung / Profil ----------
SICHERUNGEN = os.path.join(DATEN, "sicherungen")
MEDIEN = os.path.join(DATEN, "medien")
hochladen = MED.Hochladen(MEDIEN, platz=lambda n: SP.pruefen(DATEN, n))   # seit 0.45 mit Speicherwächter
GALERIE = GAL.Galerie(os.path.join(DATEN, "galerie"))


def galerie_grenze():
    """Höchstens so viele Bytes für alle Galerie-Ordner: eingestellte Grenze, aber nie mehr als belegt + über der Reserve frei."""
    belegt = GALERIE.belegt()
    return min(einst()["galerie"]["grenze_gb"] * SP.GB, belegt + SP.lage(DATEN)["nutzbar"])


def galerie_im_layout(l, oid=None):
    """Ordner, die ein Layout zeigt (Baustein „Galerie“ und Hintergrund) – mit oid: zeigt es diesen Ordner?"""
    ids = {x["optionen"]["ordner"] for x in l.get("elemente", []) if x["typ"] == "galerie" and x["optionen"]["ordner"]}
    hg = l.get("hintergrund") or {}
    if hg.get("art") == "galerie" and hg.get("galerie"):
        ids.add(hg["galerie"])
    return oid in ids if oid else ids


def galerie_stand():
    """Für die Verwaltung: Ordner mit Anzahl und Platz, Belegung und Grenze der Galerie, Lage des Speichers."""
    ordner = []
    for o in einst()["galerie"]["ordner"]:
        l = GALERIE.liste(o["id"])
        ordner.append(dict(o, anzahl=len(l), folien=sum(e["seiten"] for e in l), bytes=sum(e["bytes"] for e in l)))
    belegt = GALERIE.belegt()
    return {"ordner": ordner, "belegt": belegt, "grenze": galerie_grenze(), "grenze_gb": einst()["galerie"]["grenze_gb"],
            "speicher": SP.lage(DATEN), "max_bild_mb": GAL.MAX_BILD // 2 ** 20, "max_pdf_mb": GAL.MAX_PDF // 2 ** 20,
            "max_eintraege": GAL.MAX_EINTRAEGE}


def speicher_bericht():
    """System → Speicher (seit 0.45): Lage des Datenverzeichnisses und Belegung je Bereich (höchstens einmal je Minute gezählt)."""
    bereiche = {"galerie": os.path.join(DATEN, "galerie"), "medien": MEDIEN, "pdf": PDF_ORDNER, "bilder": BILDER,
                "sicherungen": SICHERUNGEN, "einspieler": EINSPIELER, "quelldateien": Q.DATEIEN,
                "player": PL.ORDNER, "protokolle": [os.path.join(DATEN, "wache"), os.path.join(DATEN, "protokoll.json")]}
    return {"lage": SP.lage(DATEN), "bereiche": SP.belegung(bereiche), "pfad": DATEN}
MEDIEN_SICHERUNG_MAX = 200 * 1024 * 1024        # Videos nur in die Sicherung, solange alle Medien zusammen darunter bleiben


def sicherung(mit_geheimnissen=False):
    e = einst()
    if not mit_geheimnissen:              # Standard: ohne API-Schlüssel/Passwörter (Datei kann weitergegeben werden)
        e = dict(e, quellen=Q.ohne_geheimnisse(e["quellen"]), sicherung=dict(e["sicherung"], passwort=""),
                 webhook=dict(e["webhook"], token=""), benachrichtigung=bn_geheim(e["benachrichtigung"], lambda w: ""),
                 pult=dict(e["pult"], zugaenge=[dict(z, passwort="") for z in e["pult"]["zugaenge"]]))
    return dict({"art": "signagecast-sicherung", "version": 1, "erstellt": time.strftime("%Y-%m-%d %H:%M"),
                 "mit_geheimnissen": mit_geheimnissen, "einstellungen": e, "streams": streams.alle(), "strikes": streams.strikes()},
                **({"player": PL.daten} if mit_geheimnissen and PL.daten["geraete"] else {}))


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
    for n in {x["optionen"]["datei"] for l in einst()["layouts"] for x in l["elemente"] if x["typ"] == "pdf" and x["optionen"]["datei"]}:
        for i in range(1, PDF.seiten(PDF_ORDNER, n) + 1):             # Seiten der PDFs in Layouts (seit 0.21)
            dateien[f"pdf/{n}/{i}.jpg"] = open(os.path.join(PDF_ORDNER, n, f"{i}.jpg"), "rb").read()
    for q in einst()["quellen"]:                 # hochgeladene Dateien der Datenquellen (seit 0.26)
        if q.get("datei") and os.path.exists(os.path.join(Q.DATEIEN, q["datei"]["hash"])):
            dateien[f"quelldateien/{q['datei']['hash']}"] = open(os.path.join(Q.DATEIEN, q["datei"]["hash"]), "rb").read()
    if qn.verlauf:
        with qn.verlauf.sperre:
            dateien["verlauf.json"] = json.dumps(qn.verlauf.reihen).encode()
    dateien["todo.json"] = TODO.als_bytes()      # ausgeblendete Einträge von „Zu erledigen“ (seit 0.35)
    dateien["protokoll.json"] = PROTOKOLL.als_bytes()            # seit 0.38
    dateien["layout-versionen.json"] = VERSIONEN.als_bytes()
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
    for name, inhalt in dateien.items():
        m = re.fullmatch(r"pdf/([0-9a-f]{16})/(\d{1,3})\.jpg", name)
        if m:
            os.makedirs(os.path.join(PDF_ORDNER, m.group(1)), exist_ok=True)
            with open(os.path.join(PDF_ORDNER, m.group(1), m.group(2) + ".jpg"), "wb") as f:
                f.write(inhalt)
    for name, inhalt in dateien.items():
        if name.startswith("quelldateien/") and Q.DATEI_NAME.fullmatch(name[13:]):
            os.makedirs(Q.DATEIEN, exist_ok=True)
            with open(os.path.join(Q.DATEIEN, name[13:]), "wb") as f:
                f.write(inhalt)
    if "verlauf.json" in dateien and qn.verlauf:
        reihen = json.loads(dateien["verlauf.json"])
        with qn.verlauf.sperre:
            qn.verlauf.reihen = {k: v for k, v in reihen.items() if isinstance(v, list)}
        qn.verlauf.speichern()
    if "todo.json" in dateien:
        TODO.einspielen(dateien["todo.json"])
    if "protokoll.json" in dateien:                # seit 0.38: Einträge der Sicherung und eigene zusammen
        PROTOKOLL.einspielen(dateien["protokoll.json"])
    if "layout-versionen.json" in dateien:
        VERSIONEN.einspielen(dateien["layout-versionen.json"])
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
                SP.pruefen(DATEN, len(roh))      # seit 0.45: nicht in die Reserve schreiben (Fehler wird gemeldet)
                zustand["sicherung_auto"] = {"zeit": time.strftime("%Y-%m-%d %H:%M"),
                                             "name": S.ablegen(SICHERUNGEN, roh, True, geheim, si["behalten"]), "fehler_m": None}
            except Exception as ex:
                zustand["sicherung_auto"] = {"zeit": time.strftime("%Y-%m-%d %H:%M"), "fehler": str(ex)[:200], "fehler_m": M.als_dict(ex)}
        time.sleep(20)


def einspielen(d, mit_strikes=True):
    if not isinstance(d, dict) or d.get("art") not in ("signagecast-sicherung", "signagecast-profil",
                                                         "tv-stream-sicherung", "tv-stream-profil"):   # alte Namen (bis 0.4.1)
        raise E.Fehler("e_einspielen")
    if "einstellungen" in d:
        neu = d["einstellungen"]
        if isinstance(neu, dict) and isinstance(neu.get("webhook"), dict) and not neu["webhook"].get("token"):
            neu["webhook"]["token"] = einst()["webhook"]["token"]
        bn_behalten(neu, auch_leer=True)
        pult_behalten(neu)
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
            raise E.Fehler("e_streamliste")
        for sid, x in s["streams"].items():
            if not (ID.fullmatch(sid) or re.fullmatch(r"UC[\w-]{22}", sid)):
                raise E.Fehler("e_stream_id", id=repr(sid))
        streams._speichern({"streams": s["streams"], "abgelehnt": [a for a in s.get("abgelehnt", []) if isinstance(a, str)]})
    if isinstance(d.get("player"), dict) and isinstance(d["player"].get("geraete"), list):   # Pis behalten ihre Schlüssel
        with PL.sperre:
            PL.daten.clear()
            PL.daten.update(dict(PL._leer(), **d["player"]))
            PL.speichern(PL.daten)
    if mit_strikes and isinstance(d.get("strikes"), dict):
        from streams import STRIKES, schreib
        schreib(STRIKES, d["strikes"])
    streams.einsortieren()                       # Streams unbekannter Kategorien nach „neu“ (seit 0.37)
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

    # Statische Dateien (seite.js, stil.css …) ohne Cache-Control würde Chromium heuristisch zwischenspeichern – nach einem
    # Update liefe die TV-Seite dann mit altem Code weiter. Seit 0.28.1: immer nachfragen (no-cache, meist 304).
    def send_header(self, k, v):
        if k.lower() == "cache-control":
            self._cache_gesetzt = True
        super().send_header(k, v)

    def end_headers(self):
        if not getattr(self, "_cache_gesetzt", False):
            super().send_header("Cache-Control", "no-cache")
        self._cache_gesetzt = False
        super().end_headers()

    def antwort(self, code, obj, typ="application/json; charset=utf-8"):
        b = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def unveraenderlich(self, pfad, typ):
        """Datei, deren Name ihre Prüfsumme ist (Galerie): darf der Browser lange behalten – spart Netz zu den Pis."""
        try:
            roh = open(pfad, "rb").read()
        except OSError:
            return self.antwort(404, {"ok": False})
        self.send_response(200)
        self.send_header("Content-Type", typ)
        self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        self.send_header("Content-Length", str(len(roh)))
        self.end_headers()
        self.wfile.write(roh)

    def herunterladen(self, roh, dateiname, typ):
        """Datei mit Content-Disposition – der Browser speichert sie direkt (Cockpit: externer Kanal; Docker: /laden/…)."""
        self.send_response(200)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Disposition", f'attachment; filename="{dateiname}"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(roh)))
        self.end_headers()
        self.wfile.write(roh)

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
        if p.path == "/durchsage.json":               # Long-Polling (seit 0.29): wartet mit ?stand= auf eine Änderung
            qs = urllib.parse.parse_qs(p.query)
            return self.antwort(200, ds_warten((qs.get("tv") or [""])[0], (qs.get("stand") or [""])[0][:40]))
        if p.path == "/daten.json":
            qs = urllib.parse.parse_qs(p.query)
            return self.antwort(200, tv_daten((qs.get("tv") or [None])[0], (qs.get("layout") or [None])[0]))
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
        m = re.fullmatch(r"/pdf/([0-9a-f]{16})/(\d{1,3})\.jpg", p.path)
        if m:                                     # Seite eines PDFs (Baustein „PDF“, seit 0.21)
            try:
                return self.antwort(200, open(os.path.join(PDF_ORDNER, m.group(1), m.group(2) + ".jpg"), "rb").read(), "image/jpeg")
            except OSError:
                return self.antwort(404, {"ok": False})
        m = re.fullmatch(r"/webbild/([0-9a-f]{16})\.png", p.path)
        if m:                                     # Bildschirmfoto einer Webseite (Baustein „Webseite“, Modus Bild)
            try:
                return self.antwort(200, open(fotograf.datei(m.group(1)), "rb").read(), "image/png")
            except OSError:
                return self.antwort(404, {"ok": False})
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
        m = re.fullmatch(r"/durchsage/([0-9a-f]{12}|gong)\.wav", p.path)     # Ton der Durchsagen für die TV-Seite
        if m:
            try:
                return self.antwort(200, open(os.path.join(DS.AUDIO, m.group(1) + ".wav"), "rb").read(), "audio/wav")
            except OSError:
                return self.antwort(404, {"ok": False})
        m = re.fullmatch(r"/galerie/([0-9a-f]{16})(?:\.(jpg|png|k\.jpg|hd\.jpg)|/(\d{1,3})(\.hd)?\.jpg)", p.path)
        if m:                                     # Galerie (seit 0.45): Bild, Full-HD-Fassung, PDF-Seite oder Vorschaubild
            if m.group(3):
                return self.unveraenderlich(os.path.join(GALERIE.dateien, m.group(1), m.group(3) + (m.group(4) or "") + ".jpg"), "image/jpeg")
            endung = m.group(2)
            return self.unveraenderlich(os.path.join(GALERIE.dateien, f"{m.group(1)}.{endung}"),
                                        "image/png" if endung == "png" else "image/jpeg")
        m = re.fullmatch(r"/galerie/ordner/([a-z0-9]{2,12})\.json", p.path)
        if m:                                     # Folien eines Ordners für die TV-Seite (nur, wenn sich der Stand ändert)
            if m.group(1) not in {o["id"] for o in einst()["galerie"]["ordner"]}:
                return self.antwort(404, {"ok": False})
            return self.antwort(200, {"ok": True, "stand": GALERIE.stand(m.group(1)), "folien": GALERIE.folien(m.group(1))})
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
            ks = einst()["kategorien"]
            return self.antwort(200, {"einstellungen": einst_aussen(), "kategorien": [k["id"] for k in ks],
                                      "kategorien_themen": [k["id"] for k in ks if k["gruppe"] == "themen"],
                                      "kategorien_standard": E.kategorien_standard(), "kategorien_max": E.KAT_MAX,
                                      "kategorien_begriffe_max": E.KAT_BEGRIFFE_MAX, "stufen": E.STUFEN,
                                      "bausteine": {t: {k: std for k, (_, std) in o.items()} for t, o in L.TYPEN.items()},
                                      "schriften": L.SCHRIFTEN, "operatoren": L.OPERATOREN, "raster": [L.SPALTEN, L.ZEILEN],
                                      "ausrichtungen": L.AUSRICHTUNGEN, "stile": L.STILE, "tageszeiten": L.TAGESZEITEN,
                                      "wechsel": L.WECHSEL})
        if pfad == "/api/ki":                          # verbundene Computer für KI-Assistenten (seit 0.40)
            return self.antwort(200, {"ok": True, "computer": KI.liste(), "port": WEBHOOK_PORT, "eigene_ip": eigene_ip(),
                                      "https": PultServer.tls is not None})
        if pfad == "/api/fernnetz":                    # Fernstandorte (seit 0.41) – Geheimnisse nur als ••••
            h = tailscale_hier()
            return self.antwort(200, {"ok": True, "fernnetz": FERN.aussen(), "regel": FERN.regel(WEBHOOK_PORT, HLS_PORT),
                                      "tailnet_ip": (h or {}).get("ip", ""), "userspace": bool(h and not h["tun"]),
                                      "hier": h, "einrichtung": update_status("tailscale"), "tun": os.path.exists("/dev/net/tun"),
                                      "einrichten_moeglich": updates_moeglich(), "port": WEBHOOK_PORT, "stream_port": HLS_PORT})
        if pfad == "/api/ki/datei":                    # .mcpb als Download (seit 0.40.1), bis zum Einlösen, höchstens 1 h
            x = ki_datei((q.get("id") or [""])[0])
            if not x:
                return self.antwort(404, {"ok": False})
            return self.herunterladen(x[2], x[1], "application/octet-stream")
        if pfad == "/api/ablage":                      # einmal abholen (seit 0.40.1)
            x = ABLAGE.pop((q.get("id") or [""])[0], None)
            if not x or x[0] < time.time():
                return self.antwort(404, {"ok": False})
            return self.herunterladen(x[3], x[1], x[2] + "; charset=utf-8")
        if pfad == "/api/galerie":                     # seit 0.45: Ordner, Belegung, Grenze
            return self.antwort(200, dict(galerie_stand(), ok=True))
        if pfad == "/api/galerie/ordner":
            oid = (q.get("id") or [""])[0]
            if oid not in {o["id"] for o in einst()["galerie"]["ordner"]}:
                return self.antwort(404, {"ok": False})
            return self.antwort(200, {"ok": True, "eintraege": GALERIE.liste(oid)})
        if pfad == "/api/speicher":                    # seit 0.45: System → Speicher
            return self.antwort(200, dict(speicher_bericht(), ok=True))
        if pfad == "/api/protokoll":                   # seit 0.38
            return self.antwort(200, {"ok": True, "eintraege": PROTOKOLL.liste()})
        if pfad == "/api/layouts/versionen":
            lid = (q.get("id") or [""])[0]
            return self.antwort(200, {"ok": True, "versionen": VERSIONEN.liste(lid), "geloescht": VERSIONEN.geloeschte()})
        if pfad == "/api/layouts/version":
            try:
                return self.antwort(200, {"ok": True, "layout": VERSIONEN.holen((q.get("id") or [""])[0], int((q.get("nr") or ["-1"])[0]))})
            except (KeyError, ValueError):
                return self.antwort(404, {"ok": False})
        if pfad == "/api/layouts/format":              # Formatbeschreibung für Menschen und KI (Markdown)
            return self.antwort(200, L.format_beschreibung().encode(), "text/markdown; charset=utf-8")
        if pfad == "/api/pult":
            return self.antwort(200, {"ok": True, "stimmen": {k: dict(v, bereit=DS.bereit(k)) for k, v in DS.STIMMEN.items()},
                                      "laden": DS.stand, "port": WEBHOOK_PORT, "eigene_ip": eigene_ip(),
                                      "aktiv": [dict(x, text="…") for x in durchsagen_aktiv()]})
        if pfad == "/api/alarm":
            return self.antwort(200, {"ok": True, "jetzt": alarm["jetzt"], "port": WEBHOOK_PORT, "eigene_ip": eigene_ip(),
                                      "schalten": schalten_stand})
        if pfad == "/api/leistung":
            return self.antwort(200, {"ok": True, "letzte": zustand.get("leistung"), "geraete": zustand.get("leistung_geraete", []),
                                      "port": WEBHOOK_PORT, "eigene_ip": eigene_ip()})
        if pfad == "/api/player":
            return self.antwort(200, {"ok": True, "jetzt": int(time.time()), "geraete": PL.liste(player_hinweise), "basis": PL.basis_info("pi", VERSION), "basis_pc": PL.basis_info("pc", VERSION),
                                      "wlan": [n["ssid"] for n in PL.daten["wlan"]], "server": PL.daten["server"],
                                      "server_auto": player_server() if not PL.daten["server"] else "", "stream_port": PL.daten["stream_port"],
                                      "hls_port": HLS_PORT, "webhook_port": WEBHOOK_PORT, "container": CONTAINER, "wartend": PL.wartend(),
                                      "fern": {"art": FERN.k["art"], "server": FERN.k["server"]} if FERN.aktiv() else None})
        m = re.fullmatch(r"/api/player/([0-9a-f]{8})/terminal/aus", pfad)
        if m:                                        # Fernwartung: lange Anfrage nach Ausgabe (seit 0.33)
            return self.antwort(200, dict(FW.ausgabe(m.group(1), (q.get("sid") or [""])[0], (q.get("ab") or ["0"])[0]), ok=True))
        m = re.fullmatch(r"/api/player/([0-9a-f]{8})/(bild|protokoll)", pfad)
        if m:
            try:
                roh = open(os.path.join(PL.ORDNER, m.group(1) + (".jpg" if m.group(2) == "bild" else ".log")), "rb").read()
            except OSError:
                return self.antwort(404, {"ok": False})
            typ = ("image/png" if roh[:4] == b"\x89PNG" else "image/jpeg") if m.group(2) == "bild" else "text/plain; charset=utf-8"
            return self.antwort(200, roh, typ)
        if pfad == "/api/player/image":            # Image je Gerät als Datenstrom (.img.gz, ohne Länge, endet mit der Verbindung)
            kennung = (q.get("t") or [""])[0]
            e = PL.einmal.get(kennung)
            g = PL.geraet(e["id"]) if e and e["id"] else None
            meta = PL.basis_meta(e.get("art", "pi")) if e else None
            if not e or (e["id"] and not g) or not meta:
                return self.antwort(404, {"ok": False, "fehler": str(M.Meldung("pi_link_alt"))})
            self.send_response(200)
            if e.get("form") == "iso":                 # PC-Player roh als ISO (seit 0.36): Länge bekannt
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(meta["groesse"]))
            else:
                self.send_header("Content-Type", "application/gzip")
            self.send_header("Content-Disposition", f'attachment; filename="{PL.dateiname_fuer(kennung)}"')
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            try:
                PL.image_schreiben(kennung, self.wfile.write, einst()["sprache"] or "de", wirksame_zeitzone())
            except (OSError, M.Meldung) as f:
                print("Player-Image:", f, flush=True)
            return
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
        if pfad == "/api/ha/quellen":              # Quellen eines Fernsehers in HA (source_list), seit 0.37
            ent = (q.get("entity") or [""])[0]
            if not re.fullmatch(r"media_player\.[a-z0-9_]+", ent):
                return self.antwort(200, {"ok": False, "fehler": "media_player"})
            try:
                a = ha.get(f"/api/states/{ent}").get("attributes") or {}
                return self.antwort(200, {"ok": True, "quellen": a.get("source_list") or [], "aktuell": a.get("source")})
            except Exception as ex:
                return self.antwort(200, {"ok": False, "fehler": str(ex)})
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
        if pfad == "/api/vorschau/bild":              # seit 0.39: Foto der TV-Seite (auch ohne Zuschauer), z. B. für MCP
            try:
                bild = vorschau_bild((q.get("tv") or [""])[0], (q.get("layout") or [""])[0])
            except (RuntimeError, KeyError) as f:
                return self.antwort(200, {"ok": False, "fehler": str(f)[:200]})
            return self.antwort(200, bild, "image/png")
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
            with open(os.path.join(SICHERUNGEN, name), "rb") as f:
                return self.herunterladen(f.read(), "signagecast-" + name, "application/zip")
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
            d = self.koerper(420_000_000 if p == "/api/sicherung/zip" else 100_000_000 if p == "/api/ablage" and self.api_erlaubt() else 12_000_000)
        except Exception:
            return self.antwort(400, {"ok": False, "fehler": "ungültige Anfrage"})
        m = re.fullmatch(r"/meldung/(strike|qualitaet|naechster|allgemein)", p)
        if m:                                     # vom Player der TV-Seite
            vid = str(d.get("video_id", ""))
            if m.group(1) == "naechster":         # seit 0.31: angekündigte Streams vorab prüfen
                ids = d.get("video_ids")
                ok = isinstance(ids, list) and streams.vormerken([str(x) for x in ids[:3]])
            elif m.group(1) == "allgemein":       # seit 0.31.1: viele Streams fallen aus demselben Grund durch
                ok = streams.allgemein_melden(str(d.get("grund", "")), bool(d.get("ende")))
                if ok:
                    streams.liste_bauen()         # zurückgenommene Pausen gelten sofort
            elif m.group(1) == "strike" and not NETZ.jetzt_online():
                ok = False                        # seit 0.38: Internet weg – nicht die Schuld des Streams
                NETZ.neu.set()
            elif m.group(1) == "strike":
                ok = streams.strike(vid, str(d.get("grund", "")))
                if ok:
                    streams.liste_bauen()         # Pause gilt sofort für alle Fernseher
            else:
                ok = streams.qualitaet_melden(vid, str(d.get("stufe", "")), str(d.get("beste", "")), str(d.get("phase", "")))
            return self.antwort(200 if ok else 400, {"ok": ok})
        if not p.startswith("/api/") or not self.api_erlaubt():
            return self.antwort(403, {"ok": False})
        try:
            self.protokoll_detail = None
            antwort = dict(self.api_post(p, d) or {}, ok=True)
            try:
                protokoll_verwaltung(self, p, d, antwort)
            except Exception as ex:               # das Protokoll darf nie eine Änderung scheitern lassen
                print("Protokoll:", repr(ex), flush=True)
            return self.antwort(200, antwort)
        except (E.Fehler, ValueError, KeyError, HAFehler) as ex:
            # 200 mit ok=false: die Verwaltung zeigt den Text direkt an
            m = M.als_dict(ex)
            return self.antwort(200, dict({"ok": False, "fehler": str(ex).strip("'") if isinstance(ex, KeyError) else str(ex), "code": m["code"], "p": m["p"]},
                                          **({"innen": m["innen"]} if m.get("innen") else {})))

    def api_post(self, p, d):
        if p == "/api/einstellungen" and isinstance(d.get("quellen"), list):
            Q.demaskieren(d["quellen"], einst()["quellen"])
        if p == "/api/einstellungen" and isinstance(d.get("webhook"), dict) and d["webhook"].get("token") == Q.MASKE:
            d["webhook"]["token"] = einst()["webhook"]["token"]
        if p == "/api/einstellungen":
            bn_behalten(d)
            pult_behalten(d)
        if p == "/api/pult/stimme-laden":
            st = d.get("stimme") or einst()["pult"]["stimme"]
            threading.Thread(target=lambda: DS.laden(st), daemon=True).start()
            return {}
        if p == "/api/pult/probe":
            ziel = [t["id"] for t in einst()["fernseher"] if not d.get("tv") or t["id"] == d.get("tv")]
            return {"id": durchsage_senden("Dies ist eine Probedurchsage.", ziel, True, einst()["pult"]["gong"], 20, "Verwaltung")}
        if p in ("/api/todo/aus", "/api/todo/ein"):  # „Zu erledigen“: Eintrag aus-/wieder einblenden (seit 0.35)
            if not (TODO.ausblenden if p.endswith("/aus") else TODO.einblenden)(d.get("key")):
                raise M.Meldung("todo_unbekannt")
            return {"todo_aus": TODO.liste()}
        if p == "/api/aktion/ton-neu":
            return {"erledigt": ton_neu_starten()}
        if p == "/api/leistung/test":                # ca. 10 s messen (läuft im eigenen Anfrage-Thread)
            return {"ergebnis": leistung_test()}
        if p == "/api/benachrichtigung/test":        # Testnachricht über einen Kanal (gespeicherte Einstellungen)
            kanal = d.get("kanal")
            if kanal not in ("telegram", "email", "ha"):
                raise M.Meldung("bn_kanal")
            f = BN.senden(einst()["benachrichtigung"], ha.post,
                          *BN.texte(melder.sprache(), "test", version=VERSION, host=socket.gethostname()), nur=kanal)[kanal]
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
        if p == "/api/galerie/ordner":            # seit 0.45: Ordner anlegen, umbenennen, löschen
            g = einst()["galerie"]
            ordner = [dict(o) for o in g["ordner"]]
            a, oid = d.get("aktion"), str(d.get("id", ""))
            if a == "neu":
                if len(ordner) >= 50:
                    raise M.Meldung("gal_ordner_viele")
                oid = next(k for k in (MED.neue_kennung()[:8] for _ in range(20)) if k not in {o["id"] for o in ordner})
                ordner.append({"id": oid, "name": str(d.get("name") or "").strip()[:40] or oid})
            elif a == "umbenennen":
                for o in ordner:
                    if o["id"] == oid:
                        o["name"] = str(d.get("name") or "").strip()[:40] or oid
            elif a == "loeschen":
                benutzt = [l["name"] for l in einst()["layouts"] if galerie_im_layout(l, oid)]
                if benutzt:
                    raise M.Meldung("gal_benutzt", layouts=", ".join(benutzt))
                ordner = [o for o in ordner if o["id"] != oid]
            else:
                raise M.Meldung("gal_ordner")
            zustand["einstellungen"] = E.speichern(E.zusammenfuehren(einst(), {"galerie": {"ordner": ordner}}))
            if a == "loeschen":
                GALERIE.aufraeumen({o["id"] for o in ordner}, alter_s=0)
                SP.neu_zaehlen()
            self.protokoll_detail = {"text": next((o["name"] for o in ordner if o["id"] == oid), oid)[:60]}
            return {"id": oid, "galerie": galerie_stand(), "einstellungen": einst_aussen()}
        if p in ("/api/galerie/loeschen", "/api/galerie/ordnen", "/api/galerie/umbenennen"):
            oid = str(d.get("ordner", ""))
            if oid not in {o["id"] for o in einst()["galerie"]["ordner"]}:
                raise M.Meldung("gal_ordner")
            ids = [str(x) for x in (d.get("ids") or [])[:GAL.MAX_EINTRAEGE] if GAL.NAME.fullmatch(str(x))]
            if p.endswith("/loeschen"):
                self.protokoll_detail = {"text": str(GALERIE.loeschen(oid, ids))}
                SP.neu_zaehlen()
            elif p.endswith("/ordnen"):
                GALERIE.ordnen(oid, ids)
            else:
                GALERIE.umbenennen(oid, str(d.get("id", "")), str(d.get("name", "")))
            return {"eintraege": GALERIE.liste(oid), "galerie": galerie_stand()}
        if p == "/api/medien/teil":
            stueck = base64.b64decode(str(d.get("daten", "")), validate=False)
            nr, gesamt, max_b = int(d.get("nr", -1)), max(0, int(d.get("gesamt") or 0)), MED.MAX_DATEI
            if d.get("zweck") == "galerie":        # seit 0.45: Bild/PDF für einen Galerie-Ordner
                oid = str(d.get("ordner", ""))
                if oid not in {o["id"] for o in einst()["galerie"]["ordner"]}:
                    raise M.Meldung("gal_ordner")
                if nr == 0:
                    max_b = GAL.MAX_PDF if GAL.art_erkennen(stueck[:16]) == "pdf" else GAL.MAX_BILD
                    SP.pruefen(DATEN, min(gesamt, max_b) * 2)   # erst die Platte (klarere Meldung), dann die Grenze der Galerie
                    if GALERIE.belegt() + min(gesamt, max_b) > galerie_grenze():
                        raise M.Meldung("gal_voll", gb=SP.gb(galerie_grenze()))
                else:
                    max_b = GAL.MAX_PDF
            hochladen.teil(str(d.get("kennung", "")), nr, stueck, gesamt=gesamt, max_bytes=max_b)
            if not d.get("fertig"):
                return {}
            if d.get("zweck") == "galerie":
                roh = hochladen.fertig_roh(str(d["kennung"]))
                try:
                    SP.pruefen(DATEN, os.path.getsize(roh) * 2)    # Platz für die umgewandelte Fassung
                    try:
                        eintrag = GALERIE.hinzufuegen(oid, roh, os.path.basename(str(d.get("name") or ""))[:80], galerie_grenze())
                    except M.Meldung as f:          # Grenze nur wegen der Platte erreicht: das sagen
                        if f.code == "gal_voll" and galerie_grenze() < einst()["galerie"]["grenze_gb"] * SP.GB:
                            SP.pruefen(DATEN, SP.lage(DATEN)["nutzbar"] + 1)
                        raise
                finally:
                    os.remove(roh)
                    SP.neu_zaehlen()
                self.protokoll_detail = {"text": eintrag["name"][:60], "aktion": "galerie_neu"}
                return {"eintrag": eintrag, "galerie": galerie_stand()}
            if d.get("zweck") == "pdf":           # PDF für den Baustein „PDF“: in Seitenbilder umwandeln, nicht in die Medienliste
                roh = hochladen.fertig_roh(str(d["kennung"]))
                try:
                    SP.pruefen(DATEN, os.path.getsize(roh) * 2 + PDF.SEITEN_MAX * 1024 * 1024)
                    name, n = PDF.umwandeln(roh, PDF_ORDNER)
                finally:
                    os.remove(roh)
                self.protokoll_detail = {"text": "PDF"}
                return {"pdf": name, "seiten": n}
            art, datei, dauer = hochladen.fertig(str(d["kennung"]))
            self.protokoll_detail = {"text": str(d.get("name") or datei)[:60]}
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
        if p == "/api/alarm":                    # Notfall-Vollbild aus der Verwaltung
            if d.get("aus"):
                alarm_beenden(verwaltung_wer(self), "verwaltung")
                return {"jetzt": None}
            return {"jetzt": alarm_ausloesen(d.get("text", ""), d.get("fernseher") or [], verwaltung_wer(self), "verwaltung")}
        if p == "/api/fernseher/schalten":        # Ein-/Ausschalten über HA ausprobieren
            t = fernseher(str(d.get("tv", "")))
            if not t or not t["ha_schalten"]:
                raise M.Meldung("sch_entitaet")
            tv_schalten(t, bool(d.get("an")))
            threading.Timer(8, zustand_abfragen).start()   # Zustand kurz danach neu abfragen (Anzeige in der Karte)
            return {}
        if p == "/api/fernseher/nach-einschalten":   # Quelle/Seite öffnen jetzt ausprobieren (seit 0.37), Fernseher muss an sein
            t = fernseher(str(d.get("tv", "")))
            if not t or not t["ha_schalten"]:
                raise M.Meldung("sch_entitaet")
            if not t["ha_oeffnen"] and not (t["ha_quelle"] and t["ha_schalten"].startswith("media_player.")):
                raise M.Meldung("sch_nichts")
            fehler = nach_einschalten(t, warten=0)
            return {"fehler": fehler, "nach": schalten_stand[t["id"]]["nach"]}
        if p == "/api/updates/anfrage":
            update_anfragen(str(d.get("aktion", "")))
            return {}
        if p == "/api/sicherung/erstellen":
            geheim = bool(d.get("mit_geheimnissen"))
            roh = sicherung_zip(geheim, str(d.get("passwort") or "") or None)
            SP.pruefen(DATEN, len(roh))
            return {"name": S.ablegen(SICHERUNGEN, roh, False, geheim)}
        if p == "/api/sicherung/loeschen":
            name = str(d.get("name", ""))
            if not S.NAME.fullmatch(name):
                raise M.Meldung("sich_name")
            os.remove(os.path.join(SICHERUNGEN, name))
            return {}
        if p == "/api/sicherung/zip":
            roh = base64.b64decode(str(d.get("daten", "")).split(",")[-1], validate=False)
            SP.pruefen(DATEN, len(roh) * 2)      # Bilder/Medien der Sicherung werden ausgepackt
            return {"manifest": sicherung_zip_einspielen(roh, str(d.get("passwort") or "") or None, bool(d.get("strikes")))}
        if p == "/api/quellen/datei":            # Datei für eine Datenquelle hochladen (seit 0.26), höchstens 1 MB
            roh = base64.b64decode(str(d.get("daten", "")).split(",")[-1], validate=False)
            name = os.path.basename(str(d.get("name", "")))[:80]
            SP.pruefen(DATEN, len(roh))
            return {"datei": {"hash": Q.datei_ablegen(roh), "name": name or "datei", "groesse": len(roh)}, "art": Q.datei_art(roh, name)}
        if p == "/api/csv/analysieren":           # CSV-Import, allgemein (seit 0.26): Inhalt, hochgeladene Datei oder Datenquelle
            return csv_analysieren(d)
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
        if p == "/api/layouts/pruefen":                # Import (seit 0.38): Datei oder eingefügter Text, fehlertolerant
            roh = L.json_aus_text(d["text"]) if isinstance(d.get("text"), str) else d.get("layout")
            e = einst()
            ersetzen = str(d.get("ersetzen") or "")      # seit 0.39: Kennung behalten (Layout ersetzen)
            l, hinweise = L.import_pruefen(roh, [x["id"] for x in e["layouts"] if x["id"] != ersetzen], bild_da=lambda n: os.path.exists(os.path.join(BILDER, n)),
                                           quellen=[q["id"] for q in e["quellen"]],
                                           pdf_da=lambda n: bool(PDF.seiten(PDF_ORDNER, n)),
                                           ordner={o["id"] for o in e["galerie"]["ordner"]})
            return {"layout": l, "hinweise": [M.als_dict(h) for h in hinweise]}
        if p == "/api/layouts/wiederherstellen":       # alte Fassung zurückholen (seit 0.38) – auch ein gelöschtes Layout
            lid, nr = str(d.get("id", "")), d.get("nr")
            try:
                l = VERSIONEN.holen(lid, nr)
            except KeyError:
                raise M.Meldung("l_version_fehlt") from None
            e = einst()
            neu = [l if x["id"] == lid else x for x in e["layouts"]] if any(x["id"] == lid for x in e["layouts"]) else e["layouts"] + [l]
            alt_layouts = e["layouts"]
            zustand["einstellungen"] = E.speichern(E.zusammenfuehren(einst(), {"layouts": neu}))
            VERSIONEN.merken(alt_layouts, einst()["layouts"], verwaltung_wer(self))
            self.protokoll_detail = {"text": l["name"]}
            return {"einstellungen": einst_aussen()}
        if p == "/api/fernnetz":                      # Fernstandorte speichern (seit 0.41)
            if str(d.get("art", "aus")) != "aus":
                fern_sicher()
            if d.get("art") == "link":               # seit 0.42: Adresse = die eigene im Tailnet
                h = tailscale_hier()
                if not h or not h["laeuft"]:
                    raise M.Meldung("fn_nicht_verbunden")
                d = dict(d, server=h["ip"])
            fern(FERN.speichern, d)
            self.protokoll_detail = {"text": FERN.k["art"]}
            return {"fernnetz": FERN.aussen(), "regel": FERN.regel(WEBHOOK_PORT, HLS_PORT)}
        if p == "/api/fernnetz/pruefen":
            fern_sicher()
            if FERN.k["art"] == "link":                # ohne API: der Server selbst ist verbunden
                h = tailscale_hier()
                if not h or not h["laeuft"] or h["ip"] != FERN.k["server"]:
                    raise M.Meldung("fn_server_fehlt", d=FERN.k["server"])
                return {"pruefung": {"geraete": None, "server_name": h["name"], "server_online": True}}
            return {"pruefung": fern(FERN.pruefen)}
        if p == "/api/fernnetz/anmelden":             # seit 0.42: Server per Link ins Tailnet
            return {"hier": tailscale_anmelden()}
        if p == "/api/ablage":                        # Datei der Verwaltung zum Herunterladen ablegen (seit 0.40.1)
            return {"id": ablegen(d.get("name"), d.get("typ"), d.get("inhalt"))}
        if p == "/api/ki/neu":                        # Computer für einen KI-Assistenten verbinden (seit 0.40)
            adresse = str(d.get("adresse") or "").strip()
            if not re.fullmatch(r"[A-Za-z0-9.-]{1,253}|\[[0-9A-Fa-f:]{2,45}\]", adresse):
                raise M.Meldung("ki_adresse")
            art = str(d.get("art", ""))
            if art == "desktop" and PultServer.tls is None:
                art = ""                                 # ohne Zertifikat keine Datei für Claude Desktop
            try:
                x, geheim = KI.neu(d.get("name"), art, str(d.get("recht", "")))
            except KZ.Fehler as f:
                raise M.Meldung(str(f), n=KZ.MAX) from None
            self.protokoll_detail = {"text": x["name"]}
            a = {"computer": KI.liste(), "id": x["id"], "url": f"http://{adresse}:{WEBHOOK_PORT}/mcp"}
            if art == "desktop":
                a["datei"] = ki_datei_merken(x, mcpb_bauen(x, geheim, adresse))   # Name; laden über GET /api/ki/datei
            else:
                a["schluessel"] = geheim               # nur dieses eine Mal – gespeichert ist nur der Prüfwert
            return a
        if p == "/api/ki/entfernen":
            x = KI.entfernen(str(d.get("id", "")))
            KI_DATEIEN.pop(str(d.get("id", "")), None)
            self.protokoll_detail = {"text": x["name"] if x else "?"}
            return {"computer": KI.liste()}
        if p == "/api/meldung":                       # Laufschrift (seit 0.39, wie am Pult) – leer = alle Fernseher
            tvs = [str(x) for x in (d.get("fernseher") or [t["id"] for t in einst()["fernseher"]])]
            if d.get("aus"):
                meldung_beenden(tvs)
                self.protokoll_detail = {"text": tv_namen(tvs), "aktion": "meldung_aus"}
                return {}
            meldung_setzen(tvs, d.get("text", ""), d.get("dauer_s"), d.get("stil"), verwaltung_wer(self))
            self.protokoll_detail = {"text": tv_namen(tvs)}
            return {}
        if p == "/api/layout-vorrang":                # Layout vorübergehend (seit 0.39, wie am Pult)
            tvs = [str(x) for x in (d.get("fernseher") or [t["id"] for t in einst()["fernseher"]])]
            if d.get("aus"):
                vorrang_beenden(tvs)
                self.protokoll_detail = {"text": tv_namen(tvs), "aktion": "layout_aus"}
                return {}
            l, minuten = vorrang_setzen(tvs, d.get("layout"), d.get("minuten"), verwaltung_wer(self))
            self.protokoll_detail = {"text": f"{l['name']} → {tv_namen(tvs)} ({minuten} min)"}
            return {}
        if p == "/api/durchsage":                     # Durchsage (seit 0.39, wie am Pult; Text nicht ins Protokoll)
            tvs = [t["id"] for t in einst()["fernseher"] if not d.get("fernseher") or t["id"] in d["fernseher"]]
            pu = einst()["pult"]
            did = durchsage_senden(d.get("text", ""), tvs, bool(d.get("vorlesen")) and pu["vorlesen"], pu["gong"],
                                   max(10, min(3600, int(d.get("dauer_s") or pu["dauer_s"]))), verwaltung_wer(self))
            self.protokoll_detail = {"text": tv_namen(tvs)}
            return {"id": did}
        if p == "/api/kategorien/loeschen":           # eigene Kategorie löschen, ihre Streams in eine andere (seit 0.37)
            kid, ziel = str(d.get("id", "")), str(d.get("ziel") or "neu")
            ks = einst()["kategorien"]
            k = next((x for x in ks if x["id"] == kid), None)
            if not k or ziel == kid or not any(x["id"] == ziel for x in ks):
                raise M.Meldung("e_kat_unbekannt")
            if k["eingebaut"]:
                raise M.Meldung("e_kat_eingebaut")
            zustand["einstellungen"] = E.speichern(dict(einst(), kategorien=[x for x in ks if x["id"] != kid]))
            n = streams.einsortieren({kid: ziel})
            neu_liste.set()
            return {"einstellungen": einst_aussen(), "verschoben": n}
        if p == "/api/einstellungen":
            alt_layouts = einst()["layouts"]
            zustand["einstellungen"] = E.speichern(E.zusammenfuehren(einst(), d))
            if "layouts" in d:                           # seit 0.38: alte Fassungen aufheben (Versionen)
                g, w, n = VERSIONEN.merken(alt_layouts, einst()["layouts"], verwaltung_wer(self))
                self.protokoll_detail = {"layouts": {"geaendert": g, "geloescht": w, "neu": n}}
            if "kategorien" in d:                        # Wörter geändert: gefundene Streams neu einsortieren
                streams.einsortieren()
            for tv_id in render_schreiben(einst()):          # neue Kodierung: laufende Kette neu (kurz schwarz)
                kette_neu_starten(tv_id)
            neu_liste.set()
            einspieler_neu.set()
            fotograf.neu.set()
            zeit_neu.set()
            wetter_neu.set()
            qn.neu.set()
            return {"einstellungen": einst_aussen()}
        if p == "/api/streams":
            kat = d.get("kategorie", "neu")
            s = streams.hinzufuegen(str(d.get("link", "")), d.get("name") or None,
                                    kat if any(k["id"] == kat for k in einst()["kategorien"]) else "neu",
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
                except ValueError as ex:          # als Meldung mit Kennung – die Verwaltung übersetzt (seit 0.23.3)
                    return nu[0], nu[1], ex
            with ThreadPoolExecutor(max_workers=4) as pool:
                ergebnis = list(pool.map(pruefen, eintraege))
            e = einst()
            vorhanden = {x["url"] for x in e["radio"]["sender"]}
            neu = [{"id": radio.neue_id(), "name": (n or u)[:60], "url": u} for n, u, f in ergebnis if not f and u not in vorhanden]
            if neu:
                zustand["einstellungen"] = E.speichern(E.zusammenfuehren(e, {"radio": {"sender": e["radio"]["sender"] + neu}}))
            return {"neu": [x["name"] for x in neu], "fehler": [f"{n or u}: {f}" for n, u, f in ergebnis if f],
                    "fehler_m": [dict(M.als_dict(f), name=n or u) for n, u, f in ergebnis if f],
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
        if p.startswith("/api/player"):
            return self.player_post(p, d)
        raise KeyError(p)

    def player_post(self, p, d):
        tvs = {t["id"] for t in einst()["fernseher"]}
        if p == "/api/player/neu":
            return {"geraet": PL.neu(d, tvs)["id"]}
        if p == "/api/player/koppeln":                # Code vom Fernseher eingeben (seit 0.25)
            return {"geraet": PL.koppeln(d.get("code"), {"name": d.get("name", ""), "tv": d.get("tv", "")}, tvs)["id"]}
        if p == "/api/player/sammel-image":           # Image für mehrere Geräte, ohne Schlüssel (seit 0.25; PC seit 0.36)
            if d.get("fern"):                        # anderer Standort nur je Gerät (kein Schlüssel für viele)
                raise M.Meldung("fn_nur_geraet")
            kennung = PL.herunterladen_vorbereiten("", d.get("wlan"), str(d.get("server") or player_server()), bool(d.get("fernwartung")),
                                                   art=d.get("art"), form=d.get("form", "gz"))
            return {"kennung": kennung, "datei": PL.dateiname_fuer(kennung)}
        if p == "/api/player/basis-laden":
            art = "pc" if d.get("art") == "pc" else "pi"
            threading.Thread(target=PL.basis_laden, args=(VERSION, art), daemon=True).start()
            return {}
        if p == "/api/player/einstellungen":
            PL.einstellen(d)
            return {}
        if p == "/api/player/wlan-vergessen":
            PL.wlan_vergessen(str(d.get("ssid", "")))
            return {}
        m = re.fullmatch(r"/api/player/([0-9a-f]{8})/terminal/(start|ein|ende)", p)
        if m:                                        # Fernwartung (seit 0.33)
            return self.terminal_post(m.group(1), m.group(2), d)
        m = re.fullmatch(r"/api/player/([0-9a-f]{8})/(aendern|entfernen|befehl|wlan|image|link-neu)", p)
        if not m:
            raise KeyError(p)
        gid, art = m.groups()
        if art == "aendern":
            PL.aendern(gid, d, tvs, verwaltung_wer(self))
        elif art == "entfernen":
            g = PL.entfernen(gid)
            f = (g or {}).get("fern")
            if f and f.get("art") == "link":         # seit 0.42: kein API-Zugang – der Player meldet sich selbst ab
                return {"fern": "link", "fern_ip": f.get("ip", "")}
            if f:                                    # seit 0.41: auch aus dem Tailnet (sonst bliebe nur der Weg zum Server)
                try:
                    if not FERN.aktiv() or FERN.k["art"] != f.get("art"):
                        raise FN.Fehler("fn_aus")
                    name = FERN.entfernen(f.get("ip")) if f.get("ip") else None
                    if not f.get("ip"):
                        FERN.schluessel_zurueck(f.get("kennung"))
                    return {"fern": "entfernt" if name or not f.get("ip") else "nicht_gefunden"}
                except FN.Fehler as x:
                    print("Fernnetz beim Entfernen:", x.code, x.innen, flush=True)
                    return {"fern": "fehler", "fern_text": str(M.Meldung(x.code, d=x.innen))}
        elif art == "befehl":
            PL.befehl(gid, str(d.get("art", "")), verwaltung_wer(self))
        elif art == "wlan":
            PL.wlan_wechseln(gid, d.get("wlan") or {}, verwaltung_wer(self))
        elif art == "image":
            server, f = str(d.get("server") or player_server()), None
            if d.get("fern"):                        # seit 0.41: anderer Standort – Einmal-Schlüssel fürs Tailnet
                g = PL.geraet(gid)
                if not g or g.get("modell") == PL.BROWSER:
                    raise M.Meldung("pi_unbekannt" if not g else "pi_browser_befehl")
                if not FERN.aktiv():
                    raise M.Meldung("fn_aus")
                fern_sicher()
                if FERN.k["art"] == "link":          # seit 0.42: Player meldet sich per Link an (kein Schlüssel)
                    f = {"art": "link", "lan": server, "tag": FERN.k["tag"], "kennung": "", "login": FERN.k["url"]}
                else:
                    schluessel, kid = fern(FERN.schluessel, "SignageCast " + g["name"])
                    f = {"art": FERN.k["art"], "schluessel": schluessel, "kennung": kid,
                         "login": FERN.k["url"] if FERN.k["art"] == "headscale" else ""}
                server = f"http://{FERN.k['server']}:{WEBHOOK_PORT}"
            try:
                kennung = PL.herunterladen_vorbereiten(gid, d.get("wlan"), server, bool(d.get("fernwartung")),
                                                       form=d.get("form", "gz"), fern=f)
            except M.Meldung:
                if f and f["kennung"]:                   # Schlüssel nicht ungenutzt liegen lassen
                    try:
                        FERN.schluessel_zurueck(f["kennung"])
                    except FN.Fehler:
                        pass
                raise
            if f:
                alt = PL.fern_merken(gid, f)
                if alt and alt != f["kennung"]:
                    try:
                        FERN.schluessel_zurueck(alt)         # voriger Schlüssel, nie benutzt
                    except FN.Fehler as x:
                        print("Fernnetz: alter Schlüssel nicht zurückgezogen:", x.code, x.innen, flush=True)
            return {"kennung": kennung, "datei": PL.dateiname_fuer(kennung)}
        elif art == "link-neu":                      # Browser-Gerät: neuer Link, der alte gilt nicht mehr (seit 0.36)
            PL.link_neu(gid)
        return {}

    def terminal_post(self, gid, art, d):
        g = PL.geraet(gid)
        if not g:
            raise M.Meldung("pi_unbekannt")
        if art == "start":
            b = (PL.stand.get(gid) or {}).get("bericht") or {}
            if not PL.online(gid):
                raise M.Meldung("pi_offline")
            if "fernwartung" not in b:
                raise M.Meldung("pi_fernwartung_alt")
            return {"sid": FW.starten(g, bool(b.get("fernwartung")), d.get("spalten"), d.get("zeilen"), d.get("wer"))}
        if art == "ein":
            return {"offen": FW.eingabe(gid, str(d.get("sid", "")), d.get("text") or "", d.get("spalten"), d.get("zeilen"))}
        return {"beendet": FW.beenden(gid, str(d.get("sid", "")))}


def main():
    os.makedirs(DATEN, exist_ok=True)
    render_schreiben(einst())
    zeitzone_setzen()
    try:
        n = streams.einsortieren()                # seit 0.37: nach dem Update alte Funde gleich in ihre Kategorien
        if n:
            print(f"Streams einsortiert: {n}", flush=True)
    except Exception as ex:
        print("Einsortieren:", ex, flush=True)

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
        tls = tls_zertifikat()
        if tls:
            try:
                k = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                k.minimum_version = ssl.TLSVersion.TLSv1_2
                k.load_cert_chain(*tls)
                PultServer.tls = k
            except (OSError, ssl.SSLError) as f:
                print(f"TLS für den Pult-Port nicht verfügbar: {f}", flush=True)
        webhook_server = PultServer(("0.0.0.0", WEBHOOK_PORT), WebhookBearbeiter)
        threading.Thread(target=webhook_server.serve_forever, daemon=True).start()
    except OSError as f:
        print(f"Webhook-Port {WEBHOOK_PORT} nicht verfügbar: {f}", flush=True)
    if os.environ.get("SC_VERWALTUNG_PORT"):
        import verwaltung
        threading.Thread(target=verwaltung.starten, args=(int(os.environ["SC_VERWALTUNG_PORT"]),), daemon=True).start()
    for ziel in (ha_schleife, streams_schleife, vorab_schleife, suche_schleife, cpu_schleife, kalender_schleife, einspieler_schleife, update_schleife,
                 wetter_schleife, zeit_schleife, qn.schleife, verlauf_ha_schleife, sicherung_schleife,
                 update_auto_schleife, unwetter_schleife, benachrichtigung_schleife, fotograf.schleife,
                 pdf_schleife, schalten_schleife, player_schleife, todo_schleife, NETZ.schleife, ausgabe_schleife):
        threading.Thread(target=ziel, daemon=True).start()
    threading.Thread(target=wache.schleife, daemon=True,
                     args=(streams, zustand, lambda: [(t["id"], wache.BASIS_PORT + t["nr"]) for t in einst()["fernseher"]
                                                      if kette_laeuft(t["id"])])).start()
    Server(("127.0.0.1", int(os.environ.get("SC_PORT", "8080"))), Bearbeiter).serve_forever()


if __name__ == "__main__":
    main()
