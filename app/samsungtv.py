# Samsung-Fernseher übers Netzwerk steuern (seit 0.71) – ohne App, ohne Entwicklermodus, ohne Samsung-Dateien.
# Samsung-Fernseher (Tizen, etwa ab 2016) haben eine Schnittstelle für Fernbedienungs-Apps:
#   http://<tv>:8001/api/v2/                  Geräteinfo ohne Anmeldung (Modell, PowerState, MAC)
#   POST/DELETE http://<tv>:8001/api/v2/applications/<App>   App starten/beenden ohne Anmeldung (Browser → Startseite)
#   wss://<tv>:8002/api/v2/channels/samsung.remote.control?name=<Base64>&token=<Token>
#                                             Tasten senden; beim ersten Verbinden fragt der Fernseher einmal
#                                             „Zulassen?“ und gibt danach einen Token heraus.
# Einschalten aus dem Standby geht über Wake-on-LAN an die MAC aus der Geräteinfo. Nur Standardbibliothek: der
# WebSocket-Teil (RFC 6455, nur was hier nötig ist) steht unten. Der Fernseher hat ein eigenes, selbst ausgestelltes
# Zertifikat – im eigenen Netz wird es nicht geprüft (wie bei allen Fernbedienungs-Apps).
import base64, json, os, re, socket, ssl, struct, time, urllib.request

NAME = "SignageCast"
PORT_INFO, PORT_WS, TLS = 8001, 8002, True          # die Tests biegen das auf einen nachgebauten Fernseher um
TASTEN = {"lauter": "KEY_VOLUP", "leiser": "KEY_VOLDOWN", "stumm": "KEY_MUTE", "aus": "KEY_POWER"}
IP = re.compile(r"[0-9a-fA-F:.]{3,45}")


class Fehler(Exception):
    pass


def info(ip, zeit=3):
    """Geräteinfo oder None (aus, nicht erreichbar oder kein Samsung). PowerState: "on" | "standby" | None (ältere)."""
    if not IP.fullmatch(ip or ""):
        return None
    try:
        with urllib.request.urlopen(f"http://{_host(ip)}:{PORT_INFO}/api/v2/", timeout=zeit) as r:
            d = json.loads(r.read(200_000))
    except (OSError, ValueError):
        return None
    g = d.get("device") if isinstance(d, dict) else None
    if not isinstance(g, dict):
        return None
    mac = str(g.get("wifiMac") or "")
    return {"modell": str(g.get("modelName") or "")[:40], "name": str(g.get("name") or "")[:60],
            "an": (g.get("PowerState") or "on") == "on", "mac": mac if re.fullmatch(r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", mac) else "",
            "token_noetig": str(g.get("TokenAuthSupport")) == "true"}


def _host(ip):
    return f"[{ip}]" if ":" in ip else ip


# ---------- WebSocket (Client, Text-Rahmen, maskiert) ----------
def _verbinden(ip, token, zeit):
    q = f"name={base64.b64encode(NAME.encode()).decode()}" + (f"&token={token}" if token else "")
    s = socket.create_connection((ip, PORT_WS), timeout=zeit)
    if TLS:
        kontext = ssl.create_default_context()
        kontext.check_hostname = False
        kontext.verify_mode = ssl.CERT_NONE             # selbst ausgestelltes Zertifikat des Fernsehers
        s = kontext.wrap_socket(s, server_hostname=ip)
    schluessel = base64.b64encode(os.urandom(16)).decode()
    s.sendall((f"GET /api/v2/channels/samsung.remote.control?{q} HTTP/1.1\r\nHost: {_host(ip)}:{PORT_WS}\r\n"
               f"Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {schluessel}\r\n"
               "Sec-WebSocket-Version: 13\r\n\r\n").encode())
    kopf = b""
    while b"\r\n\r\n" not in kopf:
        teil = s.recv(4096)
        if not teil:
            raise Fehler("verbindung")
        kopf += teil
        if len(kopf) > 16384:
            raise Fehler("verbindung")
    if b" 101 " not in kopf.split(b"\r\n", 1)[0]:
        raise Fehler("verbindung")
    return s, kopf.split(b"\r\n\r\n", 1)[1]


def _senden(s, text):
    daten = text.encode()
    maske = os.urandom(4)
    n = len(daten)
    kopf = bytes([0x81]) + (bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack(">H", n) if n < 65536
                            else bytes([0x80 | 127]) + struct.pack(">Q", n))
    s.sendall(kopf + maske + bytes(b ^ maske[i % 4] for i, b in enumerate(daten)))


def _lesen(s, rest):
    """Nächste Textnachricht (oder None bei Ende) – gibt (Text, Rest) zurück."""
    puffer = rest

    def holen(n):
        nonlocal puffer
        while len(puffer) < n:
            teil = s.recv(65536)
            if not teil:
                raise Fehler("verbindung")
            puffer += teil
        out, puffer = puffer[:n], puffer[n:]
        return out
    while True:
        b1, b2 = holen(2)
        n = b2 & 0x7F
        if n == 126:
            n = struct.unpack(">H", holen(2))[0]
        elif n == 127:
            n = struct.unpack(">Q", holen(8))[0]
        if n > 1_000_000:
            raise Fehler("verbindung")
        maske = holen(4) if b2 & 0x80 else None
        daten = holen(n)
        if maske:
            daten = bytes(b ^ maske[i % 4] for i, b in enumerate(daten))
        op = b1 & 0x0F
        if op == 0x8:
            return None, puffer
        if op == 0x1:
            return daten.decode("utf-8", "replace"), puffer


def sitzung(ip, token, zeit=8):
    """Verbinden und auf „ms.channel.connect“ warten → (Socket, Token). Ohne gültigen Token fragt der Fernseher
    „Zulassen?“ – dann bis zu `zeit` Sekunden warten. Fehler „abgelehnt“, wenn abgelehnt oder nicht bestätigt."""
    if not IP.fullmatch(ip or ""):
        raise Fehler("verbindung")
    s = None
    try:
        s, rest = _verbinden(ip, token, zeit)
        while True:
            text, rest = _lesen(s, rest)
            if text is None:
                raise Fehler("abgelehnt")
            try:
                m = json.loads(text)
            except ValueError:
                continue
            ereignis = m.get("event")
            if ereignis == "ms.channel.connect":
                neu = str((m.get("data") or {}).get("token") or token or "")
                return s, re.sub(r"[^0-9A-Za-z]", "", neu)[:64]
            if ereignis in ("ms.channel.unauthorized", "ms.channel.timeOut"):
                raise Fehler("abgelehnt")
    except BaseException as f:
        if s:
            s.close()                                   # nie eine Verbindung offen lassen
        if isinstance(f, socket.timeout):
            raise Fehler("abgelehnt") from None
        if isinstance(f, (OSError, ssl.SSLError)):
            raise Fehler("verbindung") from None
        raise


def koppeln(ip, zeit=30):
    """Erste Verbindung: Am Fernseher erscheint „Zulassen?“. Gibt den Token zurück (leer bei Modellen ohne Token)."""
    s, token = sitzung(ip, "", zeit)
    s.close()
    return token


def taste(ip, token, was):
    if was not in TASTEN:
        raise Fehler("taste")
    s, token = sitzung(ip, token)
    try:
        _senden(s, json.dumps({"method": "ms.remote.control", "params": {"Cmd": "Click", "DataOfCmd": TASTEN[was],
                                                                        "Option": "false", "TypeOfRemote": "SendRemoteKey"}}))
    finally:
        s.close()
    return token


BROWSER_IDS = ("3202010022079", "org.tizen.browser")   # Browser ab etwa 2021 | ältere Fernseher


def _app(ip, app, methode, zeit=5):
    r = urllib.request.Request(f"http://{_host(ip)}:{PORT_INFO}/api/v2/applications/{app}", method=methode)
    with urllib.request.urlopen(r, timeout=zeit) as a:
        roh = a.read(20_000)
    try:
        return json.loads(roh)
    except ValueError:
        return {}


def browser(ip):
    """Browser des Fernsehers (neu) starten – er zeigt seine Startseite, die bei der Einrichtung auf …/samsung steht.
    Läuft er schon, wird er erst geschlossen: so lädt die Seite neu. Braucht keine Kopplung (wie Home Assistant).
    Eine Adresse mitzuschicken ignorieren neuere Fernseher (gemessen am AU8000, 2021) – deshalb die Startseite."""
    if not IP.fullmatch(ip or ""):
        raise Fehler("verbindung")
    for app in BROWSER_IDS:
        try:
            st = _app(ip, app, "GET")
        except OSError:
            continue                                     # 404: diese Kennung gibt es auf dem Gerät nicht
        try:
            if st.get("running"):
                _app(ip, app, "DELETE")
                time.sleep(2)
            _app(ip, app, "POST")
            return app
        except OSError:
            raise Fehler("verbindung") from None
    raise Fehler("kein_browser")


def wecken(mac, ip=""):
    """Wake-on-LAN (Magic Packet an Port 9): an alle, ins /24-Netz des Fernsehers und direkt an seine Adresse – über
    WLAN kommt je nach Gerät nur einer der Wege an. Am Fernseher muss „Einschalten mit Mobilgerät“ an sein."""
    if not re.fullmatch(r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", mac or ""):
        raise Fehler("mac")
    paket = b"\xff" * 6 + bytes.fromhex(mac.replace(":", "")) * 16
    ziele = ["255.255.255.255"]
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", ip or ""):
        ziele += [ip.rsplit(".", 1)[0] + ".255", ip]
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        for _ in range(3):
            for ziel in ziele:
                try:
                    s.sendto(paket, (ziel, 9))
                except OSError:
                    pass
