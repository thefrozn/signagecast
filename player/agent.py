#!/usr/bin/env python3
# SignageCast Player – läuft auf dem Raspberry Pi am Fernseher (Image aus der Verwaltung, seit 0.23).
# Zeigt den fertigen Stream eines SignageCast-Fernsehers per HDMI (mpv direkt auf dem Bildschirm, ohne Desktop), meldet
# sich alle paar Sekunden beim Server (Webhook-Port 8890) und holt dabei Einstellungen und Befehle ab: Pull-Prinzip,
# am Pi ist kein Port offen. Ohne Netz öffnet er einen Hotspot mit Einrichtungsseite; der QR-Code steht auf dem TV.
# Alles, was einen Neustart überstehen muss, steht in /boot/firmware/signagecast.json – so verträgt sich der Player mit
# dem Schreibschutz (overlayroot): das System selbst bleibt unverändert, Stromausfälle schaden der Karte nicht.
# Nur Python-Standardbibliothek; läuft als root (WLAN, CEC, Neustart), mpv als Benutzer „signage“.
import hashlib, hmac, json, os, re, socket, subprocess, sys, threading, time, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "1.0"
BOOT = "/boot/firmware"
KONFIG = os.environ.get("SC_KONFIG", BOOT + "/signagecast.json")
AGENT_BOOT = BOOT + "/signagecast/agent.py"       # vom Server aktualisiert; start.sh nimmt ihn vor dem eingebauten
LAUF = "/run/signagecast"
SOCK = LAUF + "/mpv.sock"
HOTSPOT_IP = "10.42.0.1"                          # NetworkManager „shared“
START = time.time()
STANDARD_ANZEIGE = {"lautstaerke": 100, "drehung": 0, "modus": "preferred", "hwdec": "auto"}

TEXTE = {
    "de": {"start": "SignageCast startet …", "verbinde": "Verbinde mit dem Server …", "kein_server": "Server nicht erreichbar",
           "kein_stream": "Warte auf den Stream …", "kein_tv": "Diesem Player ist noch kein Fernseher zugewiesen.",
           "gesperrt": "Dieser Player wurde in der Verwaltung entfernt.", "unbekannt": "Der Server kennt diesen Player nicht.",
           "leer": "Dieses Image ist noch nicht eingerichtet.",
           "leer2": "In der SignageCast-Verwaltung unter Fernseher → Player ein Image für diesen Bildschirm erstellen.",
           "wlan_titel": "WLAN einrichten", "wlan1": "1. Diesen Code mit dem Handy scannen",
           "wlan1b": "   oder mit dem WLAN „{ssid}“ verbinden, Passwort: {pw}",
           "wlan2": "2. Die Einrichtungsseite öffnet sich – sonst http://10.42.0.1 aufrufen",
           "wlan3": "3. WLAN auswählen und Passwort eingeben", "wlan_fehler": "„{ssid}“: Verbindung fehlgeschlagen – Passwort prüfen",
           "wlan_versuch": "Verbinde mit WLAN „{ssid}“ …", "suche": "Suche bekannte WLANs …", "update": "Systemupdate läuft – bitte nicht ausschalten …",
           "neustart": "Starte neu …", "seite_titel": "SignageCast – WLAN einrichten", "netz": "WLAN", "anderes": "anderes WLAN (Name eingeben)",
           "passwort": "Passwort", "speichern": "Verbinden", "fertig": "Der Player verbindet sich jetzt. Erscheint der QR-Code in einer Minute "
           "wieder auf dem Fernseher, war das Passwort falsch.", "name": "Name des WLANs"},
    "en": {"start": "SignageCast is starting …", "verbinde": "Connecting to the server …", "kein_server": "Server not reachable",
           "kein_stream": "Waiting for the stream …", "kein_tv": "No TV has been assigned to this player yet.",
           "gesperrt": "This player was removed in the admin.", "unbekannt": "The server does not know this player.",
           "leer": "This image has not been set up yet.",
           "leer2": "In the SignageCast admin, create an image for this screen under TVs → Players.",
           "wlan_titel": "Set up Wi-Fi", "wlan1": "1. Scan this code with your phone",
           "wlan1b": "   or join the Wi-Fi “{ssid}”, password: {pw}",
           "wlan2": "2. The setup page opens – otherwise open http://10.42.0.1",
           "wlan3": "3. Choose your Wi-Fi and enter its password", "wlan_fehler": "“{ssid}”: connection failed – check the password",
           "wlan_versuch": "Connecting to Wi-Fi “{ssid}” …", "suche": "Looking for known Wi-Fi networks …", "update": "System update running – do not switch off …",
           "neustart": "Restarting …", "seite_titel": "SignageCast – set up Wi-Fi", "netz": "Wi-Fi", "anderes": "other Wi-Fi (enter name)",
           "passwort": "Password", "speichern": "Connect", "fertig": "The player is connecting now. If the QR code appears on the TV again "
           "within a minute, the password was wrong.", "name": "Wi-Fi name"},
}


def log(*a):
    print(*a, flush=True)


def lauf(*befehl, zeit=30, eingabe=None):
    """Befehl ausführen: (Rückgabecode, Ausgabe). Fehlt das Programm: (127, '')."""
    try:
        r = subprocess.run(befehl, capture_output=True, text=True, timeout=zeit, input=eingabe)
        return r.returncode, (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return 127, ""
    except subprocess.TimeoutExpired:
        return 124, "Zeitüberschreitung"


def lesen(pfad, ersatz=""):
    try:
        with open(pfad, errors="replace") as f:
            return f.read().strip().strip("\x00")
    except OSError:
        return ersatz


# ---------- Konfiguration auf der Boot-Partition ----------
def konfig_laden():
    """Die Datei ist im Image ein Platzhalter fester Länge; die Verwaltung schreibt JSON hinein (Rest: Leerzeichen)."""
    try:
        k = json.loads(lesen(KONFIG) or "{}")
    except ValueError:
        return None
    return k if isinstance(k, dict) and k.get("art") == "signagecast-player" and k.get("id") and k.get("schluessel") else None


def boot_beschreibbar():
    if lauf("findmnt", "-no", "OPTIONS", BOOT)[1].split(",")[:1] == ["ro"]:
        lauf("mount", "-o", "remount,rw", BOOT)


def schreiben_sicher(pfad, inhalt):
    """Auf die FAT-Partition: erst Kopie, dann umbenennen – ein Stromausfall lässt die alte oder die neue Datei zurück."""
    boot_beschreibbar()
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    tmp = pfad + ".neu"
    with open(tmp, "w" if isinstance(inhalt, str) else "wb") as f:
        f.write(inhalt)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, pfad)
    lauf("sync")


def konfig_speichern(k):
    schreiben_sicher(KONFIG, json.dumps(k, ensure_ascii=False, indent=1) + "\n")


# ---------- System ----------
def modell():
    return lesen("/proc/device-tree/model", "unbekannt")


def schreibschutz_aktiv():
    return "overlayroot=tmpfs" in lesen("/proc/cmdline")


def schreibschutz_setzen(an):
    """overlayroot (wie raspi-config): das Wort in cmdline.txt. Gibt True zurück, wenn sich die Datei geändert hat."""
    if lauf("dpkg-query", "-W", "overlayroot")[0] != 0:
        return False
    pfad = BOOT + "/cmdline.txt"
    alt = lesen(pfad)
    ohne = " ".join(w for w in alt.split() if w != "overlayroot=tmpfs")
    neu = ("overlayroot=tmpfs " + ohne) if an else ohne
    if neu == alt:
        return False
    schreiben_sicher(pfad, neu + "\n")
    return True


def hdmi():
    """Erster verbundener HDMI-Ausgang: (verbunden, Name aus EDID, Ausgang)."""
    for st in sorted(glob_liste("/sys/class/drm/card*-HDMI-A-*/status")):
        if lesen(st) == "connected":
            name = ""
            try:
                edid = open(os.path.dirname(st) + "/edid", "rb").read()
                for o in (54, 72, 90, 108):
                    if len(edid) >= o + 18 and edid[o:o + 3] == b"\0\0\0" and edid[o + 3] == 0xFC:
                        name = edid[o + 5:o + 18].split(b"\n")[0].decode(errors="replace").strip()
            except OSError:
                pass
            return True, name, os.path.basename(os.path.dirname(st)).split("-", 1)[1]
    return False, "", ""


def glob_liste(muster):
    import glob
    return glob.glob(muster)


def netz():
    """(art, ssid, signal, ip): art = kabel, wlan, hotspot oder keins."""
    ip = ""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
    except OSError:
        pass
    _, aus = lauf("nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device")
    art, ssid, signal = "keins", "", None
    for z in aus.splitlines():
        teile = z.split(":")
        if len(teile) < 4 or teile[2] != "connected":
            continue
        if teile[1] == "ethernet":
            art = "kabel"
            break
        if teile[1] == "wifi":
            art = "hotspot" if teile[3] == "sc-hotspot" else "wlan"
    if art == "wlan":
        _, aus = lauf("nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL", "device", "wifi", "list", "--rescan", "no")
        for z in aus.splitlines():
            if z.startswith("*:"):
                teile = z[2:].rsplit(":", 1)
                ssid, signal = teile[0].replace("\\:", ":"), int(teile[1]) if teile[1].isdigit() else None
    return art, ssid, signal, ip


def kabel_steckt():
    return any(lesen(p) == "1" for p in glob_liste("/sys/class/net/e*/carrier"))


def psk(ssid, passwort):
    """WPA2-Schlüssel (64 hex) – so steht das Passwort nicht im Klartext auf der Karte."""
    return hashlib.pbkdf2_hmac("sha1", passwort.encode(), ssid.encode(), 4096, 32).hex()


def wlan_verbindungen(netze, land):
    """Bekannte WLANs als NetworkManager-Verbindungen nur im Speicher (save no) – bei jedem Start neu aus der Konfiguration."""
    if land:
        lauf("iw", "reg", "set", land)
    lauf("rfkill", "unblock", "wifi")
    _, aus = lauf("nmcli", "-t", "-f", "NAME", "connection", "show")
    for name in aus.splitlines():
        if name.startswith("sc-wlan-"):
            lauf("nmcli", "connection", "delete", name)
    for i, n in enumerate(netze[:5]):
        lauf("nmcli", "connection", "add", "save", "no", "type", "wifi", "ifname", "wlan0", "con-name", f"sc-wlan-{i}",
             "ssid", n["ssid"], "wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", n["psk"],
             "connection.autoconnect", "yes", "connection.autoconnect-priority", str(50 - i))


def wlan_verbinden(i, warten=45):
    lauf("nmcli", "connection", "up", f"sc-wlan-{i}", zeit=warten + 5)
    for _ in range(warten // 3):
        if netz()[0] == "wlan":
            return True
        time.sleep(3)
    return False


def wlan_suchen():
    _, aus = lauf("nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list", "--rescan", "yes", zeit=40)
    netze = {}
    for z in aus.splitlines():
        teile = re.split(r"(?<!\\):", z)
        if len(teile) >= 2 and teile[0]:
            ssid = teile[0].replace("\\:", ":")
            sig = int(teile[1]) if teile[1].isdigit() else 0
            netze[ssid] = max(sig, netze.get(ssid, 0))
    return sorted(netze, key=lambda s: -netze[s])[:30]


# ---------- HDMI-CEC ----------
def cec(an):
    """Fernseher per HDMI-CEC ein- oder ausschalten (Gerät /dev/cec0 bzw. cec1 am verbundenen Ausgang)."""
    geraete = sorted(glob_liste("/dev/cec*"))
    if not geraete:
        return False, "kein CEC-Gerät"
    ausgang = hdmi()[2]
    dev = geraete[1] if ausgang.endswith("-2") and len(geraete) > 1 else geraete[0]
    lauf("cec-ctl", "-d", dev, "--playback", "-o", "SignageCast")
    code, aus = lauf("cec-ctl", "-d", dev, "--to", "0", "--image-view-on" if an else "--standby", zeit=15)
    if an and code == 0:
        lauf("cec-ctl", "-d", dev, "--to", "0", "--active-source", "phys-addr=" + phys_adresse(dev), zeit=15)
    return code == 0, aus[-200:] if code else ""


def phys_adresse(dev):
    m = re.search(r"Physical Address\s*:\s*([0-9a-f.]+)", lauf("cec-ctl", "-d", dev)[1])
    return m.group(1) if m else "1.0.0.0"


# ---------- Anzeige: mpv über JSON-IPC ----------
class Anzeige:
    def __init__(self):
        self.proc, self.sock, self.puffer, self.antworten, self.nr, self.gestartet = None, None, b"", {}, 0, 0
        self.sperre = threading.Lock()
        self.url, self.text, self.qr = None, None, None
        self.optionen = dict(STANDARD_ANZEIGE)
        self.ende_grund, self.zuletzt_pos, self.pos_zeit = "", None, time.time()

    def starten(self, optionen):
        self.beenden()
        self.gestartet = time.time()
        self.optionen = dict(optionen)
        os.makedirs(LAUF, exist_ok=True)
        try:
            os.chown(LAUF, *benutzer_ids())
        except (OSError, KeyError):
            pass
        if os.path.exists(SOCK):
            os.unlink(SOCK)
        o = self.optionen
        args = ["mpv", "--idle=yes", "--force-window=yes", "--fullscreen", "--no-terminal", "--config=no",
                f"--input-ipc-server={SOCK}", "--vo=gpu", "--gpu-context=drm", "--drm-mode=" + o.get("modus", "preferred"),
                "--hwdec=" + ("no" if o.get("hwdec") == "aus" else "drm-copy,v4l2m2m-copy,auto-copy-safe"),
                "--cache=yes", "--demuxer-max-bytes=64MiB", "--network-timeout=15", "--keep-open=no",
                "--image-display-duration=inf", "--osd-bar=no", "--osd-level=1", "--cursor-autohide=always",
                "--background-color=#000000", "--screenshot-format=jpg", "--screenshot-jpeg-quality=70",
                f"--volume={o.get('lautstaerke', 100)}", f"--video-rotate={o.get('drehung', 0)}",
                "--ao=alsa", "--audio-device=" + hdmi_ton(), "--audio-fallback-to-null=yes",
                "--hls-bitrate=max", "--profile=fast"]
        uid, gid = benutzer_ids()
        env = dict(os.environ, HOME=LAUF, XDG_RUNTIME_DIR=LAUF)
        try:
            self.proc = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                         user=uid, group=gid, extra_groups=gruppen(), env=env)
        except (OSError, KeyError) as f:
            log("mpv startet nicht:", f)
            return False
        threading.Thread(target=self._fehlerausgabe, args=(self.proc,), daemon=True).start()
        for _ in range(50):
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(SOCK)
                self.sock = s
                break
            except OSError:
                time.sleep(0.2)
        if not self.sock:
            log("mpv: keine Steuerverbindung")
            return False
        threading.Thread(target=self._lesen, daemon=True).start()
        url, text, qr = self.url, self.text, self.qr
        self.url, self.text = None, None
        if url:
            self.spielen(url)
        if text:
            self.zeigen(text, qr)
        return True

    def _fehlerausgabe(self, proc):
        for z in proc.stderr:
            z = z.decode(errors="replace").strip()
            if z and not z.startswith("[ffmpeg/") and "Opening " not in z:
                log("mpv:", z[:300])

    def laeuft(self):
        return self.proc is not None and self.proc.poll() is None and self.sock is not None

    def beenden(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None

    def _lesen(self):
        s = self.sock
        while s is self.sock:
            try:
                teil = s.recv(65536)
            except OSError:
                break
            if not teil:
                break
            self.puffer += teil
            while b"\n" in self.puffer:
                zeile, self.puffer = self.puffer.split(b"\n", 1)
                try:
                    m = json.loads(zeile)
                except ValueError:
                    continue
                if "request_id" in m:
                    self.antworten[m["request_id"]] = m
                elif m.get("event") == "end-file" and m.get("reason") == "error":
                    self.ende_grund = str(m.get("file_error", "Fehler"))

    def befehl(self, *args, warten=True):
        if not self.sock:
            return None
        with self.sperre:
            self.nr += 1
            nr = self.nr
            try:
                self.sock.sendall(json.dumps({"command": list(args), "request_id": nr}).encode() + b"\n")
            except OSError:
                return None
        if not warten:
            return None
        for _ in range(50):
            if nr in self.antworten:
                return self.antworten.pop(nr)
            time.sleep(0.05)
        return None

    def eigenschaft(self, name):
        a = self.befehl("get_property", name)
        return a.get("data") if a and a.get("error") == "success" else None

    def spielen(self, url):
        self.text, self.qr = None, None
        self.befehl("osd-overlay", 1, "none", "", warten=False)
        if url != self.url or self.eigenschaft("idle-active"):
            self.url, self.ende_grund, self.zuletzt_pos, self.pos_zeit = url, "", None, time.time()
            self.befehl("loadfile", url, "replace")

    def zeigen(self, zeilen, qr=None):
        """Text (Liste von Zeilen, erste groß) auf schwarzem Grund, wahlweise mit QR-Code links daneben."""
        if self.text == zeilen and self.qr == qr and self.url is None:
            return
        self.url, self.text, self.qr = None, zeilen, qr
        if qr:
            bild = LAUF + "/qr.png"
            if lauf("qrencode", "-o", bild, "-s", "14", "-m", "2", qr)[0] == 0:
                os.chmod(bild, 0o644)
                self.befehl("loadfile", bild, "replace")
        else:
            self.befehl("stop")
        esc = lambda t: t.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        x = 1200 if qr else 960
        teile = [f"{{\\an{4 if qr else 5}\\pos({x if not qr else 1080},540)\\fs64\\bord0\\shad0\\b1}}{esc(zeilen[0])}"]
        for i, z in enumerate(zeilen[1:]):
            teile.append(f"{{\\an{4 if qr else 5}\\pos({x if not qr else 1080},{640 + 60 * i})\\fs38\\bord0\\shad0}}{esc(z)}")
        self.befehl("osd-overlay", 1, "ass-events", "\n".join(teile), 1920, 1080, warten=False)
        if qr:      # QR-Code links: Bild verkleinern und verschieben
            self.befehl("set_property", "video-zoom", -0.6, warten=False)
            self.befehl("set_property", "video-align-x", -0.85, warten=False)
        else:
            self.befehl("set_property", "video-zoom", 0, warten=False)
            self.befehl("set_property", "video-align-x", 0, warten=False)

    def gesund(self):
        """Läuft der Stream? (ok, Grund). Steht die Position 20 s still, gilt er als hängend."""
        if not self.url:
            return True, ""
        if self.eigenschaft("idle-active"):
            return False, self.ende_grund or "beendet"
        pos = self.eigenschaft("time-pos")
        if pos is not None and pos != self.zuletzt_pos:
            self.zuletzt_pos, self.pos_zeit = pos, time.time()
        if time.time() - self.pos_zeit > 30:
            return False, "hängt"
        return True, ""

    def neu_laden(self):
        url, self.url = self.url, None
        if url:
            self.spielen(url)

    def bildschirmfoto(self):
        pfad = LAUF + "/bild.jpg"
        for art in ("window", "video"):
            a = self.befehl("screenshot-to-file", pfad, art)
            if a and a.get("error") == "success" and os.path.exists(pfad):
                roh = open(pfad, "rb").read()
                os.unlink(pfad)
                return roh
        return None

    def video_info(self):
        return {"codec": self.eigenschaft("video-codec"), "breite": self.eigenschaft("width"), "hoehe": self.eigenschaft("height"),
                "hwdec": self.eigenschaft("hwdec-current"), "verworfen": self.eigenschaft("frame-drop-count")}


def benutzer_ids():
    import pwd
    p = pwd.getpwnam("signage")
    return p.pw_uid, p.pw_gid


def gruppen():
    import grp
    return [g.gr_gid for g in grp.getgrall() if g.gr_name in ("video", "render", "audio")]


def hdmi_ton():
    """ALSA-Gerät des HDMI-Tons (Pi 4/5: vc4hdmi0, Pi 3: vc4hdmi)."""
    for z in lesen("/proc/asound/cards").splitlines():
        m = re.match(r"\s*\d+\s+\[(\w+)\s*\]", z)
        if m and "hdmi" in m.group(1).lower():
            return f"alsa/hdmi:CARD={m.group(1)},DEV=0"
    return "auto"


# ---------- Server ----------
class Server:
    def __init__(self, k):
        self.k, self.versatz = k, 0

    def basis(self):
        return self.k["server"].rstrip("/")

    def anfrage(self, pfad, daten=None, roh=None, zeit=20):
        """Signierte Anfrage (HMAC mit dem Geräte-Schlüssel, der Schlüssel selbst geht nie übers Netz); die Antwort ist
        ebenso signiert – ein fremdes Gerät im Netz kann dem Player nichts unterschieben."""
        koerper = roh if roh is not None else json.dumps(daten or {}).encode()
        jetzt = str(int(time.time() + self.versatz))
        sig = hmac.new(bytes.fromhex(self.k["schluessel"]), f"POST\n{pfad}\n{jetzt}\n".encode() + koerper, "sha256").hexdigest()
        anf = urllib.request.Request(self.basis() + pfad, data=koerper, method="POST", headers={
            "Content-Type": "application/octet-stream" if roh is not None else "application/json",
            "X-Geraet": self.k["id"], "X-Zeit": jetzt, "X-Signatur": sig, "User-Agent": f"SignageCast-Player/{VERSION}"})
        try:
            with urllib.request.urlopen(anf, timeout=zeit) as r:
                inhalt, kopf, code = r.read(), r.headers, r.status
        except urllib.error.HTTPError as f:
            inhalt, kopf, code = f.read(), f.headers, f.code
        if kopf.get("X-Server-Zeit", "").isdigit():
            abw = int(kopf["X-Server-Zeit"]) - time.time()
            if abs(abw - self.versatz) > 60:          # Uhr des Pi (ohne Echtzeituhr) weicht ab: Serverzeit nehmen
                self.versatz = abw
        erwartet = hmac.new(bytes.fromhex(self.k["schluessel"]), f"antwort\n{jetzt}\n".encode() + inhalt, "sha256").hexdigest()
        if code == 200 and not hmac.compare_digest(erwartet, kopf.get("X-Signatur", "")):
            raise PermissionError("Antwort ohne gültige Signatur")
        return code, inhalt


# ---------- Hotspot und Einrichtungsseite ----------
class Hotspot:
    def __init__(self, player):
        self.p, self.aktiv, self.server, self.netze, self.fehler = player, False, None, [], ""

    def ssid(self):
        name = re.sub(r"[^A-Za-z0-9-]", "", self.p.k.get("name", "")).strip("-")[:16]
        return "SignageCast-" + (name or self.p.k["id"][:6])

    def starten(self):
        if self.aktiv:
            return
        self.netze = wlan_suchen()
        pw = self.p.k.get("hotspot_pw") or "signagecast"
        lauf("nmcli", "connection", "delete", "sc-hotspot")
        code, aus = lauf("nmcli", "connection", "add", "save", "no", "type", "wifi", "ifname", "wlan0", "con-name", "sc-hotspot",
                         "autoconnect", "no", "ssid", self.ssid(), "802-11-wireless.mode", "ap", "802-11-wireless.band", "bg",
                         "ipv4.method", "shared", "ipv4.addresses", HOTSPOT_IP + "/24", "wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", pw)
        if code == 0:
            code, aus = lauf("nmcli", "connection", "up", "sc-hotspot", zeit=40)
        if code != 0:
            log("Hotspot startet nicht:", aus[-300:])
            return
        self.aktiv = True
        log("Hotspot an:", self.ssid())
        if not self.server:
            try:
                self.server = ThreadingHTTPServer((HOTSPOT_IP, 80), self.bearbeiter())
                threading.Thread(target=self.server.serve_forever, daemon=True).start()
            except OSError as f:
                log("Einrichtungsseite:", f)
        self.anzeigen()

    def anzeigen(self):
        t, pw = self.p.t, self.p.k.get("hotspot_pw") or "signagecast"
        zeilen = [t["wlan_titel"], t["wlan1"], t["wlan1b"].format(ssid=self.ssid(), pw=pw), t["wlan2"], t["wlan3"]]
        if self.fehler:
            zeilen.append(self.fehler)
        self.p.anzeige.zeigen(zeilen, f"WIFI:T:WPA;S:{self.ssid()};P:{pw};;")

    def stoppen(self):
        if self.aktiv:
            lauf("nmcli", "connection", "down", "sc-hotspot", zeit=20)
            lauf("nmcli", "connection", "delete", "sc-hotspot")
            self.aktiv = False
            if self.server:                 # Einrichtungsseite nur, solange der Hotspot läuft – nie im Heimnetz
                self.server.shutdown()
                self.server.server_close()
                self.server = None
            log("Hotspot aus")

    def gaeste(self):
        return bool(lauf("iw", "dev", "wlan0", "station", "dump")[1].strip())

    def bearbeiter(self):
        hs = self

        class B(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def senden(self, html):
                roh = html.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(roh)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(roh)

            def do_GET(self):         # jede Adresse: Einrichtungsseite (Handys öffnen sie so als „Anmeldung im WLAN“)
                self.senden(hs.seite())

            def do_POST(self):
                n = min(int(self.headers.get("Content-Length") or 0), 4096)
                f = urllib.parse.parse_qs(self.rfile.read(n).decode(errors="replace"))
                ssid = (f.get("ssid_frei") or [""])[0].strip() or (f.get("ssid") or [""])[0].strip()
                pw = (f.get("passwort") or [""])[0]
                if not ssid or not 8 <= len(pw) <= 63:
                    return self.senden(hs.seite("SSID / Passwort (8–63 Zeichen)"))
                self.senden(hs.seite(fertig=True))
                threading.Thread(target=hs.p.wlan_neu, args=(ssid, pw), daemon=True).start()
        return B

    def seite(self, fehler="", fertig=False):
        import html
        t = self.p.t
        if fertig:
            inhalt = f"<p>{html.escape(t['fertig'])}</p>"
        else:
            opt = "".join(f"<option>{html.escape(s)}</option>" for s in self.netze)
            inhalt = (f"<form method=post><label>{html.escape(t['netz'])}<select name=ssid>{opt}<option value=''>{html.escape(t['anderes'])}"
                      f"</option></select></label><label>{html.escape(t['name'])}<input name=ssid_frei autocapitalize=off></label>"
                      f"<label>{html.escape(t['passwort'])}<input name=passwort type=password minlength=8 maxlength=63 required></label>"
                      f"<button>{html.escape(t['speichern'])}</button></form>" + (f"<p class=f>{html.escape(fehler)}</p>" if fehler else ""))
        return (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
                f"<title>{html.escape(t['seite_titel'])}</title><style>body{{font:17px system-ui,sans-serif;max-width:28em;margin:2em auto;"
                f"padding:0 16px;background:#111;color:#eee}}label{{display:block;margin:1em 0}}select,input,button{{display:block;width:100%;"
                f"font:inherit;padding:.6em;margin-top:.3em;box-sizing:border-box}}button{{background:#2f7d4f;color:#fff;border:0;border-radius:6px}}"
                f".f{{color:#f88}}</style><h1>{html.escape(t['seite_titel'])}</h1><p>{html.escape(self.p.k.get('name', ''))}</p>{inhalt}")


# ---------- Player ----------
class Player:
    def __init__(self, k):
        self.k = k
        self.t = TEXTE.get(k.get("sprache"), TEXTE["de"])
        self.server = Server(k)
        self.anzeige = Anzeige()
        self.hotspot = Hotspot(self)
        self.soll = {}                      # letzte Antwort des Servers
        self.ergebnisse = []                # erledigte Befehle für die nächste Meldung
        self.kontakt = 0                    # Zeit der letzten erfolgreichen Meldung
        self.zustand, self.zustand_text = "start", ""
        self.bildschirm = None              # zuletzt per CEC gesetzt
        self.wlan_rev = k.get("wlan_rev", 0)
        self.offline_seit = time.time()
        self.letzte_meldung, self.wlan_laeuft, self.versuche, self.erkennen_bis, self.hotspot_seit = 0, False, 0, 0, 0

    # --- Einrichtung beim Start ---
    def einrichten(self):
        k = self.k
        if k.get("hostname"):
            lauf("hostnamectl", "set-hostname", k["hostname"])
        if k.get("zeitzone"):
            lauf("timedatectl", "set-timezone", k["zeitzone"])
        wlan_verbindungen(k.get("wlan") or [], k.get("land") or "DE")
        if schreibschutz_aktiv():          # Updates landen im RAM und wären nach dem Neustart weg – Pflege übernimmt der Server
            lauf("systemctl", "stop", "apt-daily.timer", "apt-daily-upgrade.timer")
        if k.get("pflege") == "update" and not schreibschutz_aktiv():
            self.systemupdate()
        if schreibschutz_setzen(bool(k.get("schreibschutz", True))):
            self.neustart()

    def systemupdate(self):
        self.anzeige.zeigen([self.t["update"]])
        for _ in range(40):                 # bis zu 2 min auf Netz warten
            if netz()[0] in ("kabel", "wlan"):
                break
            time.sleep(3)
        code1, a1 = lauf("apt-get", "update", zeit=900)
        code2, a2 = lauf("env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "-y", "-o", "Dpkg::Options::=--force-confold",
                         "full-upgrade", zeit=3600)
        self.k.pop("pflege", None)
        self.k["letztes_update"] = {"zeit": int(time.time()), "ok": code1 == 0 and code2 == 0,
                                     "meldung": "" if code1 == 0 and code2 == 0 else (a2 or a1)[-300:]}
        konfig_speichern(self.k)
        log("Systemupdate:", "ok" if code1 == code2 == 0 else "Fehler")

    def neustart(self):
        self.anzeige.zeigen([self.t["neustart"]])
        time.sleep(2)
        lauf("sync")
        lauf("systemctl", "reboot")
        time.sleep(60)

    # --- WLAN ---
    def wlan_neu(self, ssid, passwort):
        """Aus der Einrichtungsseite: neues WLAN vorne einreihen, Hotspot aus, verbinden; klappt es nicht: Hotspot wieder."""
        self.wlan_laeuft = True
        try:
            self._wlan_neu(ssid, passwort)
        finally:
            self.wlan_laeuft = False

    def _wlan_neu(self, ssid, passwort):
        time.sleep(2)                       # Antwortseite noch ausliefern
        alt = self.k.get("wlan") or []
        neu = [{"ssid": ssid, "psk": psk(ssid, passwort)}] + [n for n in alt if n["ssid"] != ssid]
        self.hotspot.stoppen()
        self.anzeige.zeigen([self.t["wlan_versuch"].format(ssid=ssid)])
        wlan_verbindungen(neu, self.k.get("land") or "DE")
        if wlan_verbinden(0):
            self.k["wlan"] = neu[:5]
            konfig_speichern(self.k)
            self.hotspot.fehler = ""
            self.offline_seit = time.time()
            log("WLAN eingerichtet:", ssid)
        else:
            wlan_verbindungen(alt, self.k.get("land") or "DE")
            self.hotspot.fehler = self.t["wlan_fehler"].format(ssid=ssid)
            self.hotspot.starten()

    def wlan_vom_server(self, w):
        """WLAN-Wechsel aus der Verwaltung: neue Liste testen; erreicht der Player den Server damit nicht, zurück zur alten."""
        alt = self.k.get("wlan") or []
        netze = [{"ssid": str(n["ssid"])[:32], "psk": str(n["psk"])} for n in w.get("netze", []) if re.fullmatch(r"[0-9a-f]{64}", str(n.get("psk", "")))]
        netze = (netze + [n for n in alt if n["ssid"] not in {x["ssid"] for x in netze}])[:5]     # bisherige bleiben als Ersatz
        erg = {"art": "wlan", "rev": w["rev"], "ok": True, "hinweis": ""}
        wlan_verbindungen(netze, self.k.get("land") or "DE")
        if netze and netz()[0] != "kabel":
            ok = wlan_verbinden(0) and self.melden_versuch()
            if not ok:
                wlan_verbindungen(alt, self.k.get("land") or "DE")
                if alt:
                    wlan_verbinden(0)
                erg.update(ok=False, hinweis="nicht_erreichbar")
        elif netz()[0] == "kabel":
            erg["hinweis"] = "kabel"
        if erg["ok"]:
            self.k["wlan"] = netze
        self.k["wlan_rev"] = self.wlan_rev = w["rev"]
        konfig_speichern(self.k)
        self.ergebnisse.append(erg)

    # --- Meldung an den Server ---
    def bericht(self):
        art, ssid, signal, ip = netz()
        verbunden, tv_name, ausgang = hdmi()
        v = self.anzeige.video_info() if self.anzeige.url else {}
        return {"version": VERSION, "modell": modell(), "netz": art, "ssid": ssid, "signal": signal, "ip": ip,
                "temperatur": round(int(lesen("/sys/class/thermal/thermal_zone0/temp", "0") or 0) / 1000, 1),
                "drossel": lauf("vcgencmd", "get_throttled")[1].partition("=")[2], "laufzeit": int(time.time() - START),
                "hochgefahren": int(float(lesen("/proc/uptime", "0").split()[0])), "hdmi": verbunden, "tv_name": tv_name,
                "ausgang": ausgang, "zustand": self.zustand, "zustand_text": self.zustand_text, "video": v,
                "schreibschutz": schreibschutz_aktiv(), "cec": bool(glob_liste("/dev/cec*")), "wlan_rev": self.wlan_rev,
                "netze": [n["ssid"] for n in self.k.get("wlan") or []], "letztes_update": self.k.get("letztes_update"),
                "ergebnisse": self.ergebnisse[:10]}

    def melden_versuch(self):
        try:
            code, inhalt = self.server.anfrage("/player/melden", self.bericht())
            if code == 401 and self.server.versatz:           # Uhr wurde gerade korrigiert: gleich noch einmal
                code, inhalt = self.server.anfrage("/player/melden", self.bericht())
        except (OSError, PermissionError, ValueError) as f:
            self.zustand_text = str(f)[:120]
            return False
        if code in (403, 404, 410):
            self.zustand = "gesperrt" if code == 410 else "unbekannt"
            return False
        if code != 200:
            return False
        try:
            self.soll = json.loads(inhalt)
        except ValueError:
            return False
        self.ergebnisse = []
        self.kontakt = time.time()
        return True

    # --- Befehle ---
    def befehle(self):
        for b in self.soll.get("befehle", []):
            art, erg = b.get("art"), {"id": b.get("id"), "art": b.get("art"), "ok": True}
            try:
                if art == "neustart":
                    self.ergebnisse.append(erg)
                    self.melden_versuch()
                    self.neustart()
                elif art == "player_neu":
                    self.anzeige.beenden()
                elif art == "bild":
                    roh = self.anzeige.bildschirmfoto()
                    if roh:
                        self.server.anfrage("/player/bild", roh=roh, zeit=60)
                    else:
                        erg["ok"] = False
                elif art == "protokoll":
                    text = lauf("journalctl", "-b", "-u", "signagecast-player", "-n", "300", "--no-pager")[1]
                    text += "\n\n== dmesg\n" + "\n".join(lauf("dmesg")[1].splitlines()[-80:])
                    self.server.anfrage("/player/protokoll", roh=text.encode()[-200000:], zeit=60)
                elif art in ("cec_an", "cec_aus"):
                    erg["ok"], erg["hinweis"] = cec(art == "cec_an")
                elif art == "erkennen":
                    self.erkennen_bis = time.time() + 30
                elif art == "systemupdate":
                    self.k["pflege"] = "update"
                    konfig_speichern(self.k)
                    self.ergebnisse.append(erg)
                    self.melden_versuch()
                    if schreibschutz_aktiv():
                        schreibschutz_setzen(False)
                        self.neustart()
                    else:
                        self.systemupdate()
                        if schreibschutz_setzen(bool(self.k.get("schreibschutz", True))):
                            self.neustart()
                    continue
                else:
                    erg.update(ok=False, hinweis="unbekannt")
            except (OSError, PermissionError) as f:
                erg.update(ok=False, hinweis=str(f)[:200])
            self.ergebnisse.append(erg)

    def einstellungen_anwenden(self):
        s = self.soll
        opt = {"lautstaerke": max(0, min(130, int(s.get("lautstaerke", 100)))), "drehung": s.get("drehung", 0) if s.get("drehung") in (0, 90, 180, 270) else 0,
               "modus": {"1080": "1920x1080", "2160": "3840x2160", "720": "1280x720"}.get(str(s.get("aufloesung")), "preferred"),
               "hwdec": "aus" if s.get("hwdec") == "aus" else "auto"}
        if opt != self.k.get("anzeige"):            # merken: nach dem Neustart gleich richtig gedreht
            self.k["anzeige"] = opt
            konfig_speichern(self.k)
        if self.anzeige.laeuft() and opt != self.anzeige.optionen:
            if {k: v for k, v in opt.items() if k != "lautstaerke"} == {k: v for k, v in self.anzeige.optionen.items() if k != "lautstaerke"}:
                self.anzeige.befehl("set_property", "volume", opt["lautstaerke"], warten=False)
                self.anzeige.optionen = opt
            else:
                self.anzeige.starten(opt)
        elif not self.anzeige.laeuft():
            self.anzeige.optionen = opt
        if "schreibschutz" in s and bool(s["schreibschutz"]) != bool(self.k.get("schreibschutz", True)):
            self.k["schreibschutz"] = bool(s["schreibschutz"])
            konfig_speichern(self.k)
            if schreibschutz_setzen(self.k["schreibschutz"]):
                self.melden_versuch()
                self.neustart()
        if s.get("name") and s["name"] != self.k.get("name"):
            self.k["name"] = str(s["name"])[:60]
            konfig_speichern(self.k)
        w = s.get("wlan")
        if isinstance(w, dict) and isinstance(w.get("rev"), int) and w["rev"] > self.wlan_rev:
            self.wlan_vom_server(w)
        if s.get("bildschirm") in ("an", "aus") and s["bildschirm"] != self.bildschirm:
            ok, _ = cec(s["bildschirm"] == "an")
            self.bildschirm = s["bildschirm"]
            log("Bildschirm per CEC", s["bildschirm"], "ok" if ok else "ohne Antwort")
        elif s.get("bildschirm") is None:
            self.bildschirm = None
        h = s.get("agent")
        if h and h != datei_hash(os.path.abspath(__file__)):
            self.agent_aktualisieren(h)

    def agent_aktualisieren(self, soll):
        try:
            code, roh = self.server.anfrage("/player/agent", {}, zeit=60)
        except (OSError, PermissionError) as f:
            log("Agent-Update:", f)
            return
        if code == 200 and hashlib.sha256(roh).hexdigest() == soll:
            try:
                compile(roh, "agent.py", "exec")
            except SyntaxError:
                return
            schreiben_sicher(AGENT_BOOT, roh)
            log("Agent aktualisiert – starte neu")
            self.anzeige.beenden()
            sys.exit(0)

    # --- Hauptschleife ---
    def schritt(self):
        jetzt = time.time()
        intervall = max(5, min(120, int(self.soll.get("intervall", 15))))
        if jetzt - self.letzte_meldung >= intervall or (self.ergebnisse and jetzt - self.kontakt < 60):
            self.letzte_meldung = jetzt
            if self.melden_versuch():
                self.einstellungen_anwenden()
                self.befehle()
        if self.wlan_laeuft:
            return
        if not self.anzeige.laeuft():
            if (hdmi()[0] or not glob_liste("/sys/class/drm/card*-HDMI-A-*")) and jetzt - self.anzeige.gestartet > 10:
                self.anzeige.starten(self.anzeige.optionen)
            return
        online = jetzt - self.kontakt < 60
        art = netz()[0]
        # Netz weg: nach 2 min Hotspot (beim Stromausfall bootet der Pi oft schneller als der Router – nicht zu früh);
        # im Hotspot alle 5 min ohne Gäste kurz die bekannten WLANs versuchen
        if art in ("kabel", "wlan") or kabel_steckt():
            self.offline_seit = jetzt
            if self.hotspot.aktiv:
                self.hotspot.stoppen()
        elif art == "keins" and not self.hotspot.aktiv and jetzt - self.offline_seit > (30 if not self.k.get("wlan") else 120):
            self.hotspot.starten()
            self.hotspot_seit = jetzt
            return
        if self.hotspot.aktiv:
            if jetzt - self.hotspot_seit > 300 and self.k.get("wlan") and not self.hotspot.gaeste():
                self.hotspot.stoppen()
                self.anzeige.zeigen([self.t["suche"]])
                wlan_verbindungen(self.k["wlan"], self.k.get("land") or "DE")
                if not wlan_verbinden(0, 60):
                    self.hotspot.starten()
                    self.hotspot_seit = time.time()
            return
        if self.erkennen_bis > jetzt:
            self.anzeige.zeigen([self.k.get("name", ""), f"{modell()} · {netz()[3]}", self.k["id"]])
            return
        if self.zustand in ("gesperrt", "unbekannt"):
            self.anzeige.zeigen([self.t[self.zustand], self.k.get("name", "")])
            return
        if not online and not self.anzeige.url:
            self.zustand = "verbinde"
            self.anzeige.zeigen([self.t["verbinde"] if jetzt - START < 90 else self.t["kein_server"],
                                 self.k.get("name", ""), self.server.basis()] + ([self.zustand_text] if self.zustand_text else []))
            return
        stream = self.soll.get("stream")
        if not stream:
            self.zustand = "kein_tv"
            self.anzeige.zeigen([self.t["kein_tv"], self.k.get("name", "")])
            return
        if self.soll.get("bildschirm") == "aus":      # Bildschirm laut Zeitplan aus: Stream anhalten, Server rendert dann nicht
            self.zustand = "aus"
            self.anzeige.zeigen([""])
            return
        u = urllib.parse.urlparse(self.server.basis())
        url = f"http://{u.hostname}:{stream['port']}/{stream['pfad']}/index.m3u8"
        if self.anzeige.url != url:
            self.anzeige.spielen(url)
            self.versuche = 0
            return
        ok, grund = self.anzeige.gesund()
        if ok:
            self.zustand, self.zustand_text, self.versuche = "spielt", "", 0
            return
        self.zustand, self.zustand_text = "stream_fehler", grund
        self.versuche += 1
        if self.versuche <= 3 or self.versuche % 5 == 0:
            log("Stream:", grund, "– lade neu")
            self.anzeige.neu_laden()
        if self.versuche > 3:
            self.anzeige.befehl("osd-overlay", 1, "ass-events", "{\\an2\\fs34\\bord2}" + self.t["kein_stream"], 1920, 1080, warten=False)

    def laufen(self):
        self.anzeige.starten(dict(STANDARD_ANZEIGE, **(self.k.get("anzeige") or {})))
        self.anzeige.zeigen([self.t["start"], self.k.get("name", "")])
        self.einrichten()
        gesund_seit = time.time()
        while True:
            try:
                self.schritt()
            except Exception as f:          # nie stehen bleiben – nächster Versuch in 3 s
                log("Fehler:", repr(f)[:300])
            if gesund_seit and time.time() - gesund_seit > 120:
                try:
                    open(LAUF + "/fehlstarts", "w").write("0")
                except OSError:
                    pass
                gesund_seit = None
            time.sleep(3)


def datei_hash(pfad):
    try:
        return hashlib.sha256(open(pfad, "rb").read()).hexdigest()
    except OSError:
        return ""


def unkonfiguriert():
    a = Anzeige()
    t = TEXTE["de"]
    while True:
        if not a.laeuft():
            a.starten(STANDARD_ANZEIGE)
            a.text = None
        a.zeigen([t["leer"], t["leer2"], "", TEXTE["en"]["leer"], TEXTE["en"]["leer2"]])
        time.sleep(10)


def main():
    os.makedirs(LAUF, exist_ok=True)
    k = konfig_laden()
    log(f"SignageCast Player {VERSION} auf {modell()}" + (f" – „{k.get('name')}“, Server {k.get('server')}" if k else " – nicht eingerichtet"))
    if not k:
        unkonfiguriert()
    Player(k).laufen()


if __name__ == "__main__":
    main()
