#!/usr/bin/env python3
# SignageCast Player – läuft auf dem Raspberry Pi am Fernseher (Image aus der Verwaltung, seit 0.23).
# Zeigt den fertigen Stream eines SignageCast-Fernsehers per HDMI (mpv direkt auf dem Bildschirm, ohne Desktop), meldet
# sich alle paar Sekunden beim Server (Webhook-Port 8890) und holt dabei Einstellungen und Befehle ab: Pull-Prinzip,
# am Pi ist kein Port offen. Ohne Netz öffnet er einen Hotspot mit Einrichtungsseite; der QR-Code steht auf dem TV.
# Alles, was einen Neustart überstehen muss, steht in /boot/firmware/signagecast.json – so verträgt sich der Player mit
# dem Schreibschutz (overlayroot): das System selbst bleibt unverändert, Stromausfälle schaden der Karte nicht.
# Direktmodus (seit 0.24, Pi 4/5): Statt des Streams zeigt Chromium im Kiosk-Rahmen cage die TV-Seite selbst; Hinweise
# (Start, Hotspot, Fehler) zeigt weiter mpv. Macht der Browser dreimal in 10 min Probleme, nimmt der Pi eine Stunde den Stream.
# Kopplung (seit 0.25): Ein Image für mehrere Pis hat keinen Schlüssel. Der Pi handelt ihn per Diffie-Hellman mit dem
# Server aus und zeigt einen 6-stelligen Code, den man in der Verwaltung eingibt; der Schlüssel geht nie übers Netz.
# Fernwartung (seit 1.3 / SignageCast 0.33): Terminal aus der Verwaltung – nur, wenn dieser Pi es erlaubt („fernwartung“
# in signagecast.json, beim Image erstellen oder auf der Einrichtungsseite; ab Werk aus). Die Shell (root) läuft in einem
# PTY; Ein- und Ausgabe gehen verschlüsselt über zwei signierte Anfragen, am Pi bleibt jeder Port zu. Ende nach 10 min
# ohne Eingabe, spätestens nach 60 min; solange steht „Fernwartung aktiv“ auf dem Fernseher.
# PC-Player (seit 1.5 / SignageCast 0.36, experimentell): derselbe Agent auf x86-64-Geräten (Debian live, UEFI). Merkmal
# /etc/signagecast-pc; statt der Boot-Partition nimmt er die Datenpartition des Sticks (SC_BOOT, start.sh). Unterschiede:
# Modell aus DMI, Bildschirm an jedem Anschluss (HDMI, DisplayPort, …), Ton über den angeschlossenen HDMI/DP-Ausgang,
# Video-Dekodierung per VAAPI, Schreibschutz immer an (live), kein Systemupdate (das kommt mit einem neuen Image).
# Nur Python-Standardbibliothek; läuft als root (WLAN, CEC, Neustart), mpv und Chromium als Benutzer „signage“.
import base64, fcntl, hashlib, hmac, json, os, pty, re, secrets, select, shutil, signal, socket, struct, subprocess, sys, termios, threading, time, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "1.8"
PC = os.path.exists("/etc/signagecast-pc")       # PC-Player (seit 1.5)
BOOT = os.environ.get("SC_BOOT", "/boot/firmware")
KONFIG = os.environ.get("SC_KONFIG", BOOT + "/signagecast.json")
AGENT_BOOT = BOOT + "/signagecast/agent.py"       # vom Server aktualisiert; start.sh nimmt ihn vor dem eingebauten
LAUF = "/run/signagecast"
SOCK = LAUF + "/mpv.sock"
HOTSPOT_IP = "10.42.0.1"                          # NetworkManager „shared“
START = time.time()
STANDARD_ANZEIGE = {"lautstaerke": 100, "drehung": 0, "modus": "preferred", "hwdec": "auto"}
# Diffie-Hellman für die Kopplung: RFC 3526, 2048-Bit-Gruppe 14, Erzeuger 2 (wie app/player.py)
DH_P = int("FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DD"
           "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F2411"
           "7C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D"
           "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497C"
           "EA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF", 16)

TEXTE = {
    "de": {"start": "SignageCast startet …", "verbinde": "Verbinde mit dem Server …", "kein_server": "Server nicht erreichbar",
           "kein_stream": "Warte auf den Stream …", "kein_tv": "Diesem Player ist noch kein Fernseher zugewiesen.",
           "gesperrt": "Dieser Player wurde in der Verwaltung entfernt.", "unbekannt": "Der Server kennt diesen Player nicht.",
           "fern_weg": "Vom Tailnet getrennt – in der Verwaltung entfernt oder im Tailnet gelöscht. Für einen Neustart ein neues Image erstellen.",
           "fern_link": "Player freigeben: QR-Code scannen und bei Tailscale anmelden", "fern_link2": "oder in der SignageCast-Verwaltung „Player freigeben“",
           "leer": "Dieses Image ist noch nicht eingerichtet.",
           "leer2": "In der SignageCast-Verwaltung unter Fernseher → Player ein Image für diesen Bildschirm erstellen.",
           "wlan_titel": "WLAN einrichten", "wlan1": "1. Diesen Code mit dem Handy scannen",
           "wlan1b": "   oder mit dem WLAN „{ssid}“ verbinden, Passwort: {pw}",
           "wlan2": "2. Die Einrichtungsseite öffnet sich – sonst http://10.42.0.1 aufrufen",
           "wlan3": "3. WLAN auswählen und Passwort eingeben", "wlan_fehler": "„{ssid}“: Verbindung fehlgeschlagen – Passwort prüfen",
           "wlan_versuch": "Verbinde mit WLAN „{ssid}“ …", "suche": "Suche bekannte WLANs …", "update": "Systemupdate läuft – bitte nicht ausschalten …",
           "neustart": "Starte neu …", "direkt": "Lade die Seite …", "code": "Code: {code}",
           "koppeln1": "In der SignageCast-Verwaltung unter Fernseher → Player → „Player koppeln“ diesen Code eingeben.",
           "koppeln2": "Der Code gilt 10 Minuten, danach erscheint ein neuer.", "gekoppelt": "Gekoppelt – starte …", "seite_titel": "SignageCast – WLAN einrichten", "netz": "WLAN", "anderes": "anderes WLAN (Name eingeben)",
           "passwort": "Passwort", "speichern": "Verbinden", "fertig": "Der Player verbindet sich jetzt. Erscheint der QR-Code in einer Minute "
           "wieder auf dem Fernseher, war das Passwort falsch.", "name": "Name des WLANs",
           "fw_hinweis": "Fernwartung aktiv", "fw_titel": "Fernwartung", "fw_text": "Erlaubt ein Terminal (root) zu diesem Player aus der "
           "SignageCast-Verwaltung. Ab Werk aus. Jede Sitzung wird protokolliert und steht solange auf dem Fernseher.",
           "fw_erlauben": "Fernwartung erlauben", "fw_speichern": "Speichern", "fw_gespeichert": "Gespeichert."},
    "en": {"start": "SignageCast is starting …", "verbinde": "Connecting to the server …", "kein_server": "Server not reachable",
           "kein_stream": "Waiting for the stream …", "kein_tv": "No TV has been assigned to this player yet.",
           "gesperrt": "This player was removed in the admin.", "unbekannt": "The server does not know this player.",
           "fern_weg": "Disconnected from the tailnet – removed in the admin or deleted in the tailnet. Create a new image to start again.",
           "fern_link": "Approve this player: scan the QR code and log in to Tailscale", "fern_link2": "or “Approve player” in the SignageCast admin",
           "leer": "This image has not been set up yet.",
           "leer2": "In the SignageCast admin, create an image for this screen under TVs → Players.",
           "wlan_titel": "Set up Wi-Fi", "wlan1": "1. Scan this code with your phone",
           "wlan1b": "   or join the Wi-Fi “{ssid}”, password: {pw}",
           "wlan2": "2. The setup page opens – otherwise open http://10.42.0.1",
           "wlan3": "3. Choose your Wi-Fi and enter its password", "wlan_fehler": "“{ssid}”: connection failed – check the password",
           "wlan_versuch": "Connecting to Wi-Fi “{ssid}” …", "suche": "Looking for known Wi-Fi networks …", "update": "System update running – do not switch off …",
           "neustart": "Restarting …", "direkt": "Loading the page …", "code": "Code: {code}",
           "koppeln1": "In the SignageCast admin under TVs → Players → “Pair a player”, enter this code.",
           "koppeln2": "The code is valid for 10 minutes, then a new one appears.", "gekoppelt": "Paired – starting …", "seite_titel": "SignageCast – set up Wi-Fi", "netz": "Wi-Fi", "anderes": "other Wi-Fi (enter name)",
           "passwort": "Password", "speichern": "Connect", "fertig": "The player is connecting now. If the QR code appears on the TV again "
           "within a minute, the password was wrong.", "name": "Wi-Fi name",
           "fw_hinweis": "Remote maintenance active", "fw_titel": "Remote maintenance", "fw_text": "Allows a terminal (root) to this player "
           "from the SignageCast admin. Off by default. Every session is logged and shown on the TV while it lasts.",
           "fw_erlauben": "Allow remote maintenance", "fw_speichern": "Save", "fw_gespeichert": "Saved."},
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
    if not isinstance(k, dict) or k.get("art") != "signagecast-player":
        return None
    return k if (k.get("id") and k.get("schluessel")) or (k.get("kopplung") and k.get("server")) else None


def dh_ableiten(geheim, fremd, a_pub, b_pub):
    """(Code, Geräte-Schlüssel) aus dem gemeinsamen DH-Wert – wie app/player.py."""
    s = pow(fremd, geheim, DH_P)
    k = hashlib.sha256(b"signagecast-kopplung\n" + b"\n".join(format(x, "x").encode() for x in (s, a_pub, b_pub))).digest()
    code = int.from_bytes(hmac.new(k, b"code", "sha256").digest()[:8], "big") % 1_000_000
    return f"{code:06d}", hmac.new(k, b"geraet", "sha256").hexdigest()


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
    if PC:                                      # z. B. „LENOVO ThinkCentre M720q“, „Fujitsu FUTRO S740“
        teile = [lesen(f"/sys/class/dmi/id/{n}") for n in ("sys_vendor", "product_version", "product_name")]
        teile = [t for t in teile if t and not re.search(r"to be filled|default string|^none$|^system", t, re.I)]
        if len(teile) > 2 and not re.search(r"[a-z]", teile[1], re.I):
            teile.pop(1)                        # Versionsnummer statt Name (Dell, HP)
        return ("PC " + " ".join(dict.fromkeys(teile))).strip()[:80]
    return lesen("/proc/device-tree/model", "unbekannt")


def temperatur():
    """CPU-Temperatur in °C (PC: coretemp/k10temp – die ACPI-Zone zeigt oft einen festen Wert)."""
    if PC:
        for h in sorted(glob_liste("/sys/class/hwmon/hwmon*")):
            if lesen(h + "/name") in ("coretemp", "k10temp", "zenpower", "cpu_thermal"):
                w = lesen(h + "/temp1_input")
                if w.isdigit():
                    return round(int(w) / 1000, 1)
    w = lesen("/sys/class/thermal/thermal_zone0/temp", "0")
    return round(int(w) / 1000, 1) if w.lstrip("-").isdigit() else 0


def ram_mb():
    """Arbeitsspeicher in MB (MemTotal; etwas unter der Nenngröße, z. B. 2-GB-Pi ≈ 1850). None, wenn unbekannt."""
    m = re.search(r"^MemTotal:\s+(\d+) kB", lesen("/proc/meminfo", ""), re.M)
    return int(m.group(1)) // 1024 if m else None


def schreibschutz_aktiv():
    if PC:                                      # live-System: immer schreibgeschützt (squashfs + RAM-Schicht)
        return True
    return "overlayroot=tmpfs" in lesen("/proc/cmdline")


def schreibschutz_setzen(an):
    """overlayroot (wie raspi-config): das Wort in cmdline.txt. Gibt True zurück, wenn sich die Datei geändert hat."""
    if PC or lauf("dpkg-query", "-W", "overlayroot")[0] != 0:
        return False
    pfad = BOOT + "/cmdline.txt"
    alt = lesen(pfad)
    ohne = " ".join(w for w in alt.split() if w != "overlayroot=tmpfs")
    neu = ("overlayroot=tmpfs " + ohne) if an else ohne
    if neu == alt:
        return False
    schreiben_sicher(pfad, neu + "\n")
    return True


def ausgaenge():
    """Status-Dateien der Bildschirm-Anschlüsse: Pi nur HDMI; PC alle außer Writeback (HDMI, DP, DVI, VGA, eDP, VM)."""
    if not PC:
        return sorted(glob_liste("/sys/class/drm/card*-HDMI-A-*/status"))
    alle = [p for p in glob_liste("/sys/class/drm/card*-*/status") if "-Writeback-" not in p]
    return sorted(alle, key=lambda p: ("-eDP-" in p or "-LVDS-" in p, p))    # eingebaute Bildschirme zuletzt


def hdmi():
    """Erster verbundener Ausgang: (verbunden, Name aus EDID, Ausgang)."""
    for st in ausgaenge():
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
                "--hwdec=" + ("no" if o.get("hwdec") == "aus" else "vaapi,auto-safe" if PC else "drm-copy,v4l2m2m-copy,auto-copy-safe"),
                "--cache=yes", "--demuxer-max-bytes=64MiB", "--network-timeout=15", "--keep-open=no",
                "--image-display-duration=inf", "--osd-bar=no", "--osd-level=1", "--cursor-autohide=always",
                "--osc=no",                     # ohne Bedienleiste – und ohne das Leerlauf-Logo von mpv ab 0.38 (Debian 13)
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


# ---------- Direktmodus: Chromium im Kiosk-Rahmen cage (Wayland, ohne Desktop) ----------
BROWSER_HOME = "/var/lib/signage"
BROWSER_AUFLOESUNG = {"preferred": "1920x1080", "1920x1080": "1920x1080", "1280x720": "1280x720", "3840x2160": "3840x2160"}


def chromium_pfad():
    return shutil.which("chromium") or shutil.which("chromium-browser")


class Browser:
    """Zeigt die TV-Seite des Servers. Ton über ALSA (eigener Lautstärkeregler „SignageCast“ vor dem HDMI-Ausgang)."""
    def __init__(self):
        self.proc, self.gestartet, self.url, self.optionen, self.lautstaerke = None, 0, None, {}, None

    @staticmethod
    def verfuegbar():
        return bool(shutil.which("cage") and chromium_pfad())

    def laeuft(self):
        return self.proc is not None and self.proc.poll() is None

    def _umgebung(self):
        return dict(os.environ, HOME=BROWSER_HOME, XDG_RUNTIME_DIR=LAUF, WAYLAND_DISPLAY="wayland-0", LIBSEAT_BACKEND="seatd")

    def _als_signage(self, *befehl, zeit=15):
        uid, gid = benutzer_ids()
        try:
            r = subprocess.run(befehl, capture_output=True, timeout=zeit, user=uid, group=gid, extra_groups=gruppen(), env=self._umgebung())
            return r.returncode, r.stdout
        except (OSError, subprocess.TimeoutExpired):
            return 1, b""

    def _ton(self):
        """ALSA: Kette „signagecast“ = Lautstärkeregler (softvol) vor dem HDMI-Gerät; Chromium spielt dorthin."""
        t = ton_geraet()
        if not t:
            return None
        art, karte, dev = t
        art = "hw" if art == "plughw" else art          # vor softvol kein zweites plug (die Kette hat schon eins)
        try:
            with open(BROWSER_HOME + "/.asoundrc", "w") as f:
                f.write(f'''pcm.signagecast {{ type plug; slave.pcm "sc_lautstaerke" }}
pcm.sc_lautstaerke {{ type softvol; slave.pcm "{art}:CARD={karte},DEV={dev}"; control {{ name "SignageCast"; card {karte} }} }}
''')
            os.chown(BROWSER_HOME + "/.asoundrc", *benutzer_ids())
        except (OSError, KeyError):
            return None
        return karte

    @staticmethod
    def seatd_sicherstellen():
        """seatd muss laufen (vergibt den Bildschirm an cage). Images bis 0.35 haben einen Drop-in mit /usr/bin/seatd – Debian
        liefert /usr/sbin/seatd, der Dienst startet dann nie. Reparatur zur Laufzeit unter /run (auch mit Schreibschutz)."""
        if os.path.exists("/run/seatd.sock") or not shutil.which("seatd"):
            return
        d = "/run/systemd/system/seatd.service.d"
        try:
            os.makedirs(d, exist_ok=True)
            with open(d + "/zz-signagecast.conf", "w") as f:
                f.write(f"[Service]\nExecStart=\nExecStart={shutil.which('seatd')} -g video\n")
        except OSError:
            return
        lauf("systemctl", "daemon-reload")
        lauf("systemctl", "reset-failed", "seatd.service")
        lauf("systemctl", "restart", "seatd.service")
        for _ in range(20):
            if os.path.exists("/run/seatd.sock"):
                log("seatd repariert und gestartet")
                return
            time.sleep(0.1)
        log("seatd startet nicht")

    def starten(self, url, optionen, sprache):
        self.beenden()
        self.seatd_sicherstellen()
        self.gestartet, self.url, self.optionen, self.lautstaerke = time.time(), url, dict(optionen), None
        os.makedirs(LAUF, exist_ok=True)
        try:
            os.makedirs(BROWSER_HOME, exist_ok=True)
            os.chown(LAUF, *benutzer_ids())
            os.chmod(LAUF, 0o700)
        except (OSError, KeyError):
            pass
        karte = self._ton()
        args = ["cage", "-d", "--", chromium_pfad(), "--kiosk", "--ozone-platform=wayland", "--noerrdialogs", "--disable-infobars",
                "--no-first-run", "--disable-session-crashed-bubble", "--disable-features=Translate,TranslateUI,MediaRouter",
                "--check-for-update-interval=31536000", "--autoplay-policy=no-user-gesture-required", "--password-store=basic",
                "--overscroll-history-navigation=0", "--disable-pinch", "--force-device-scale-factor=1", "--disk-cache-size=67108864",
                f"--user-data-dir={BROWSER_HOME}/chromium", f"--lang={'en-GB' if sprache == 'en' else 'de-DE'}"]
        if karte:
            args.append("--alsa-output-device=signagecast")
        if optionen.get("hwdec") == "aus":
            args.append("--disable-accelerated-video-decode")
        elif PC:                                    # VAAPI (Intel/AMD) unter Wayland – ohne passende Grafik nimmt Chromium die CPU
            args.append("--enable-features=AcceleratedVideoDecodeLinuxGL,AcceleratedVideoDecodeLinuxZeroCopyGL,VaapiVideoDecoder")
        args.append(url)
        uid, gid = benutzer_ids()
        try:
            # cage selbst ohne WAYLAND_DISPLAY: sonst sucht wlroots eine vorhandene Wayland-Sitzung, statt den Bildschirm
            # zu nehmen („Could not connect to remote display“). Nur der Bildschirm, keine Eingabegeräte (seit 1.6): eine
            # angesteckte Maus (oder die einer VM) zeigt sonst cages Zeiger mitten im Bild, bis sie bewegt wird – der Kiosk
            # braucht weder Maus noch Tastatur
            umg = {k: v for k, v in self._umgebung().items() if k != "WAYLAND_DISPLAY"}
            umg.update(WLR_BACKENDS="drm")
            self.proc = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                         user=uid, group=gid, extra_groups=gruppen(), env=umg, start_new_session=True)
        except (OSError, KeyError, TypeError) as f:
            log("Browser startet nicht:", f)
            self.proc = None
            return False
        threading.Thread(target=self._fehlerausgabe, args=(self.proc,), daemon=True).start()
        threading.Thread(target=self._ausgabe_einstellen, args=(self.proc, karte), daemon=True).start()
        log("Direktmodus:", url.rsplit("/", 1)[0] + "/…")
        return True

    def _fehlerausgabe(self, proc):
        for z in proc.stderr:
            z = z.decode(errors="replace").strip()
            if "dbus/" in z or "WebGL1 blocklisted" in z:      # ohne Sitzungsbus/GPU unvermeidlich, nur Lärm im Protokoll
                continue
            if z and ("ERROR" in z or "FATAL" in z or z.startswith("[cage]") or "seat" in z.lower()):
                log("Browser:", z[:300])

    def _ausgabe_einstellen(self, proc, karte):
        """Nach dem Start: Auflösung und Drehung (wlr-randr), Lautstärke."""
        for _ in range(20):
            time.sleep(1)
            if proc.poll() is not None:
                return
            code, aus = self._als_signage("wlr-randr")
            namen = re.findall(rb"^(\S+)", aus, re.M)
            if code == 0 and namen:
                break
        else:
            return
        o = self.optionen
        dreh = {0: "normal", 90: "90", 180: "180", 270: "270"}.get(o.get("drehung", 0), "normal")
        for n in namen:
            self._als_signage("wlr-randr", "--output", n.decode(), "--mode", BROWSER_AUFLOESUNG.get(o.get("modus"), "1920x1080"), "--transform", dreh)
        self.lautstaerke_setzen(o.get("lautstaerke", 100), karte)

    def lautstaerke_setzen(self, wert, karte=None):
        t = ton_geraet()
        karte = karte or (t[1] if t else None)
        if karte and wert != self.lautstaerke and lauf("amixer", "-q", "-c", karte, "sset", "SignageCast", f"{min(100, int(wert))}%")[0] == 0:
            self.lautstaerke = wert                 # der Regler entsteht erst, wenn Chromium das erste Mal Ton abspielt

    def beenden(self):
        if self.proc and self.proc.poll() is None:
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.wait(8)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    os.killpg(self.proc.pid, signal.SIGKILL)
                except OSError:
                    pass
        self.proc, self.gestartet = None, 0

    def bildschirmfoto(self):
        """JPEG – Debians grim kann aber kein JPEG („jpeg support disabled“), dann PNG (seit 1.5; Server ab 0.36)."""
        code, roh = self._als_signage("grim", "-t", "jpeg", "-q", "70", "-", zeit=20)
        if code == 0 and roh[:2] == b"\xff\xd8":
            return roh
        code, roh = self._als_signage("grim", "-t", "png", "-l", "3", "-", zeit=20)
        return roh if code == 0 and roh[:8] == b"\x89PNG\r\n\x1a\n" else None


def benutzer_ids():
    import pwd
    p = pwd.getpwnam("signage")
    return p.pw_uid, p.pw_gid


def gruppen():
    import grp
    return [g.gr_gid for g in grp.getgrall() if g.gr_name in ("video", "render", "audio")]


def hdmi_ton():
    """ALSA-Gerät des HDMI-Tons (Pi 4/5: vc4hdmi0, Pi 3: vc4hdmi; PC: der HDMI/DP-Ausgang mit Bildschirm)."""
    if PC:
        return pc_ton()
    for z in lesen("/proc/asound/cards").splitlines():
        m = re.match(r"\s*\d+\s+\[(\w+)\s*\]", z)
        if m and "hdmi" in m.group(1).lower():
            return f"alsa/hdmi:CARD={m.group(1)},DEV=0"
    return "auto"


def pc_ton():
    """PC: HDMI-/DisplayPort-Ausgänge der Soundkarten; der mit angeschlossenem Bildschirm (ELD gefüllt) zuerst."""
    kandidaten = []
    for z in lesen("/proc/asound/cards").splitlines():
        m = re.match(r"\s*(\d+)\s+\[(\w+)\s*\]", z)
        if not m:
            continue
        nr, karte = m.groups()
        for pcm in sorted(glob_liste(f"/proc/asound/card{nr}/pcm*p")):
            if not re.search(r"HDMI|DP|DisplayPort", lesen(pcm + "/info")):
                continue
            dev = re.search(r"pcm(\d+)p$", pcm).group(1)
            eld = lauf("amixer", "-c", nr, "cget", f"iface=PCM,name=ELD,device={dev}")[1]
            m2 = re.search(r"values=(\d+)", eld)
            kandidaten.append((not (m2 and int(m2.group(1)) > 0), f"alsa/plughw:CARD={karte},DEV={dev}"))
    return sorted(kandidaten)[0][1] if kandidaten else "auto"


def ton_geraet():
    """(Art, Karte, Gerät) aus hdmi_ton(), z. B. ("hdmi", "vc4hdmi0", "0") – oder None (kein HDMI-Ton gefunden)."""
    m = re.match(r"alsa/(hdmi|plughw):CARD=(\w+),DEV=(\d+)$", hdmi_ton())
    return m.groups() if m else None


# ---------- Server ----------
class Server:
    def __init__(self, k):
        self.k, self.versatz = k, 0
        self.ersatz = None                  # anderer Standort per Link (seit 1.8): bis zur Anmeldung die Adresse im Heimnetz

    def basis(self):
        return (self.ersatz or self.k["server"]).rstrip("/")

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


    def offen(self, pfad, daten, zeit=20):
        """Unsignierte Anfrage (nur Kopplung): (Code, Inhalt, Kopf)."""
        anf = urllib.request.Request(self.basis() + pfad, data=json.dumps(daten).encode(), method="POST", headers={
            "Content-Type": "application/json", "User-Agent": f"SignageCast-Player/{VERSION}"})
        try:
            with urllib.request.urlopen(anf, timeout=zeit) as r:
                return r.status, r.read(), r.headers
        except urllib.error.HTTPError as f:
            return f.code, f.read(), f.headers


# ---------- Fernwartung (seit 1.3) ----------
FW_LEER_S, FW_MAX_S = 600, 3600


def fw_schluessel(k):
    return hmac.new(bytes.fromhex(k["schluessel"]), b"fernwartung", "sha256").digest()


def _fw_xor(s, nonce, roh):
    if not roh:
        return b""
    strom = hashlib.shake_256(s + nonce).digest(len(roh))
    return (int.from_bytes(roh, "big") ^ int.from_bytes(strom, "big")).to_bytes(len(roh), "big")


def fw_verschluesseln(s, roh):
    nonce = secrets.token_bytes(16)
    return base64.b64encode(nonce + _fw_xor(s, nonce, roh)).decode()


def fw_entschluesseln(s, text):
    roh = base64.b64decode(text or "", validate=True)
    return _fw_xor(s, roh[:16], roh[16:]) if len(roh) >= 16 else b""


class Terminal:
    """Eine Shell-Sitzung: bash als root in einem PTY. Zwei Fäden: Ausgabe lesen und senden, Eingaben abholen."""
    def __init__(self, server, k, sid, spalten, zeilen):
        self.server, self.sid, self.s = server, sid, fw_schluessel(k)
        self.offen, self.grund, self.start = True, "", time.time()
        self.eingabe_zeit, self.n_ein, self.n_aus, self.groesse_rev = self.start, 0, 0, 0
        self.sperre = threading.Lock()
        umgebung = {"TERM": "xterm-256color", "HOME": "/root", "USER": "root", "LOGNAME": "root", "SHELL": "/bin/bash",
                    "LANG": "C.UTF-8", "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "SIGNAGECAST_FERNWARTUNG": "1"}
        self.pid, self.fd = pty.fork()
        if self.pid == 0:                           # Kind: nur noch die Shell starten
            try:
                os.chdir("/root")
                os.execve("/bin/bash", ["bash", "-l"], umgebung)
            finally:
                os._exit(127)
        self.groesse(spalten, zeilen)
        log(f"Fernwartung: Sitzung beginnt (Shell {self.pid})")
        threading.Thread(target=self._lesen, daemon=True).start()
        threading.Thread(target=self._holen, daemon=True).start()

    def groesse(self, spalten, zeilen):
        try:
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", int(zeilen), int(spalten), 0, 0))
        except (OSError, ValueError):
            pass

    def _senden(self, roh, ende=""):
        with self.sperre:
            self.n_aus += 1
            daten = {"sid": self.sid, "n": self.n_aus, "daten": fw_verschluesseln(self.s, roh)}
            if ende:
                daten["ende"] = ende
        try:
            code, inhalt = self.server.anfrage("/player/terminal/aus", daten, zeit=20)
            return code == 200 and bool(json.loads(inhalt).get("offen"))
        except (OSError, PermissionError, ValueError):
            return True                            # kurz kein Netz: weiter versuchen (Zeitgrenzen gelten trotzdem)

    def _lesen(self):
        while self.offen:
            jetzt = time.time()
            if jetzt - self.eingabe_zeit > FW_LEER_S:
                return self.schliessen("leerlauf")
            if jetzt - self.start > FW_MAX_S:
                return self.schliessen("zeitgrenze")
            try:
                bereit = select.select([self.fd], [], [], 0.5)[0]
                if not bereit:
                    continue
                roh = os.read(self.fd, 65536)
                ende = time.time() + 0.02             # kurz sammeln: weniger, größere Anfragen
                while len(roh) < 65536 and time.time() < ende and select.select([self.fd], [], [], max(0, ende - time.time()))[0]:
                    teil = os.read(self.fd, 65536 - len(roh))
                    if not teil:
                        break
                    roh += teil
            except OSError:                          # Shell beendet (EIO)
                roh = b""
            if not roh:
                return self.schliessen("beendet")
            if not self._senden(roh):
                return self.schliessen("server", melden=False)

    def _holen(self):
        fehler = 0
        while self.offen:
            with self.sperre:
                self.n_ein += 1
                anfrage = {"sid": self.sid, "n": self.n_ein, "groesse_rev": self.groesse_rev}
            try:
                code, inhalt = self.server.anfrage("/player/terminal/ein", anfrage, zeit=30)
                d = json.loads(inhalt) if code == 200 else None
            except (OSError, PermissionError, ValueError):
                d = None
            if d is None:
                fehler += 1
                if fehler > 40:                      # gut 1 min kein Server
                    return self.schliessen("kein_server", melden=False)
                time.sleep(1.5)
                continue
            fehler = 0
            if not d.get("offen"):
                return self.schliessen("server", melden=False)
            if d.get("groesse_rev") and d["groesse_rev"] != self.groesse_rev:
                self.groesse_rev = d["groesse_rev"]
                self.groesse(d.get("spalten", 80), d.get("zeilen", 24))
            try:
                roh = fw_entschluesseln(self.s, d.get("daten"))
            except ValueError:
                roh = b""
            if roh:
                self.eingabe_zeit = time.time()
                try:
                    while roh:
                        roh = roh[os.write(self.fd, roh):]
                except OSError:
                    return self.schliessen("beendet")

    def _aufsammeln(self):
        try:
            os.waitpid(self.pid, 0)                  # kein Zombie
        except OSError:
            pass

    def schliessen(self, grund, melden=True):
        with self.sperre:
            if not self.offen:
                return
            self.offen, self.grund = False, grund
        for sig in (signal.SIGHUP, signal.SIGKILL):
            try:
                os.killpg(os.getpgid(self.pid), sig)
            except OSError:
                pass
            time.sleep(0.2)
        threading.Thread(target=self._aufsammeln, daemon=True).start()
        try:
            os.close(self.fd)
        except OSError:
            pass
        log(f"Fernwartung: Sitzung beendet ({grund}) nach {int(time.time() - self.start)} s")
        if melden:
            self._senden(b"", ende=grund)


# ---------- Hotspot und Einrichtungsseite ----------
class Fernnetz:
    """Anderer Standort (seit 1.7 / SignageCast 0.41): Tailscale oder Headscale. Steht „fern“ in signagecast.json, startet
    der Agent tailscaled selbst (der Systemdienst ist im Image aus) und tritt beim ersten Mal mit dem Einmal-Schlüssel bei;
    danach wird der Schlüssel aus der Datei gelöscht. tailscaled hält seinen Zustand unter /run (Schreibschutz); der Agent
    kopiert ihn bei Änderungen auf die Boot-/Datenpartition und beim Start zurück – so übersteht die Anmeldung Neustarts.
    Keine Protokolle an Tailscale (--no-logs-no-support), kein DNS und keine Routen aus dem Tailnet."""
    ORDNER = LAUF + "/tailscale"
    SOCK = LAUF + "/tailscaled.sock"

    def __init__(self, player):
        self.p, self.proc, self.naechster, self.geprueft, self.gesichert = player, None, 0, 0, ""
        self.faden, self.lief = None, False
        self.anmeldung, self.ohne_tag, self.url, self.anmelde_fehler = None, False, "", ""      # Link-Modus (seit 1.8)
        self.abgemeldet = False
        self.info, self.fehler = {}, ""
        self.dauerhaft = BOOT + "/signagecast/tailscale.state"
        self.zustand = self.ORDNER + "/tailscaled.state"

    def gewuenscht(self):
        return isinstance(self.p.k.get("fern"), dict)

    def ts(self, *a, zeit=20):
        return lauf("tailscale", "--socket=" + self.SOCK, *a, zeit=zeit)

    def starten(self):
        if not shutil.which("tailscaled") or not shutil.which("tailscale"):
            self.fehler = "fehlt"                 # Image vor 0.41 – neues Image nötig
            return
        os.makedirs(self.ORDNER, mode=0o700, exist_ok=True)
        if not os.path.exists(self.zustand) and os.path.exists(self.dauerhaft):
            shutil.copyfile(self.dauerhaft, self.zustand)
            os.chmod(self.zustand, 0o600)
            self.gesichert = datei_hash(self.zustand)
        self.proc = subprocess.Popen(["tailscaled", "--state=" + self.zustand, "--statedir=" + self.ORDNER,
                                      "--socket=" + self.SOCK, "--port=0", "--no-logs-no-support"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=dict(os.environ, TS_NO_LOGS_NO_SUPPORT="true"))
        log("Fernnetz: tailscaled gestartet")

    def optionen(self, f):
        """Immer dieselben Optionen – tailscale up lehnt sonst ab („requires mentioning all non-default flags“)."""
        arg = ["--hostname=" + (self.p.k.get("hostname") or "sc-player"), "--accept-dns=false", "--accept-routes=false"]
        if f.get("art") == "link" and f.get("tag") and not self.ohne_tag:
            arg.append("--advertise-tags=" + f["tag"])
        return arg + (["--login-server=" + f["login"]] if f.get("login") else [])

    def link_anmelden(self, f):
        """Link-Modus: tailscale up wartet im Hintergrund auf die Anmeldung; den Link liest schritt() aus dem Status.
        Erlaubt das Tailnet den Tag nicht (keine Zugriffsregel), noch einmal ohne Tag – die Verwaltung warnt dann."""
        if self.anmeldung and self.anmeldung.poll() is None:
            return
        if self.anmeldung is not None:            # beendet: war es der Tag?
            fehler = (self.anmeldung.stderr.read() if self.anmeldung.stderr else "") or ""
            if re.search(r"tag", fehler, re.I) and not self.ohne_tag:
                self.ohne_tag = True
                log("Fernnetz: Tag nicht erlaubt – Anmeldung ohne Tag")
            elif fehler.strip():
                self.anmelde_fehler = fehler.strip()[-160:]
        self.anmeldung = subprocess.Popen(["tailscale", "--socket=" + self.SOCK, "up", "--timeout=1800s", *self.optionen(f)],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

    def abmelden(self):
        """In der Verwaltung entfernt (seit 1.8): selbst aus dem Tailnet abmelden und die Anmeldung vergessen."""
        if not self.gewuenscht() or not self.proc or self.proc.poll() is not None or self.abgemeldet:
            return
        self.abgemeldet = True
        self.ts("logout", zeit=30)
        for d in (self.zustand, self.dauerhaft):
            try:
                os.unlink(d)
            except OSError:
                pass
        log("Fernnetz: abgemeldet (in der Verwaltung entfernt)")

    def beitreten(self, f):
        datei = self.ORDNER + "/schluessel"
        fd = os.open(datei, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as d:
            d.write(f["schluessel"])
        try:
            code, aus = self.ts("up", "--auth-key=file:" + datei, "--timeout=90s", *self.optionen(f), zeit=120)
        finally:
            os.unlink(datei)
        if code == 0:
            log("Fernnetz: beigetreten")
            f.pop("schluessel", None)             # verbraucht – nicht im Klartext liegen lassen
            konfig_speichern(self.p.k)
        else:
            self.fehler = "anmeldung: " + aus[-160:]
            log("Fernnetz: Beitritt fehlgeschlagen:", aus[-300:])

    def schritt(self, jetzt):
        if not self.gewuenscht() or self.fehler == "fehlt":
            return
        if self.proc is None or self.proc.poll() is not None:
            if jetzt >= self.naechster and netz()[0] in ("kabel", "wlan"):
                self.naechster = jetzt + 30
                self.starten()
            return
        if jetzt - self.geprueft < 20:
            return
        self.geprueft = jetzt
        code, aus = self.ts("status", "--json", zeit=10)
        try:
            st = json.loads(aus) if code in (0, 1) and aus.startswith("{") else {}
        except ValueError:
            st = {}
        lage = st.get("BackendState", "")
        f = self.p.k["fern"]
        if self.faden and self.faden.is_alive():
            return
        if lage == "NeedsLogin" and f.get("schluessel"):
            self.faden = threading.Thread(target=self.beitreten, args=(f,), daemon=True)     # bis 2 min – Anzeige läuft weiter
            self.faden.start()
            return
        link = f.get("art") == "link"
        if link:                                  # bis zur Anmeldung über das Heimnetz melden (Link an die Verwaltung)
            self.p.server.ersatz = None if lage == "Running" else (f.get("lan") or None)
            self.url = st.get("AuthURL", "") if lage == "NeedsLogin" and str(st.get("AuthURL", "")).startswith("https://") else ""
            if lage == "NeedsLogin" and self.p.zustand != "gesperrt":
                self.link_anmelden(f)
        if lage == "Stopped":
            self.ts("up", "--timeout=30s", *self.optionen(f), zeit=40)
            return
        if lage != "Running":
            self.fehler = "abgemeldet" if lage == "NeedsLogin" else (lage.lower() or "startet")
            self.info = {}
            if lage == "NeedsLogin" and self.lief and not link and self.p.zustand != "gesperrt":   # gelöscht
                self.p.zustand = "fern_weg"
            return
        self.fehler, self.lief = "", True
        eigen = (st.get("Self") or {}).get("TailscaleIPs") or []
        ziel = urllib.parse.urlparse(self.p.k.get("server", "")).hostname or ""
        weg = ""
        for peer in (st.get("Peer") or {}).values():
            if ziel in (peer.get("TailscaleIPs") or []):
                weg = "direkt" if peer.get("CurAddr") else ("relay:" + peer["Relay"] if peer.get("Relay") else "")
                break
        self.info = {"ip": next((a for a in eigen if "." in a), ""), "weg": weg}
        h = datei_hash(self.zustand)
        if h and h != self.gesichert:             # Anmeldung neu oder Schlüssel erneuert: dauerhaft sichern
            try:
                with open(self.zustand, "rb") as d:
                    schreiben_sicher(self.dauerhaft, d.read())
                self.gesichert = h
            except OSError as x:
                log("Fernnetz: Zustand nicht gesichert:", x)

    def bericht(self):
        if not self.gewuenscht():
            return None
        b = dict(self.info, art=self.p.k["fern"].get("art", ""), fehler=self.fehler)
        if self.p.k["fern"].get("art") == "link":
            b.update(url=self.url, ohne_tag=self.ohne_tag, anmelde_fehler=self.anmelde_fehler if not self.info else "")
        return b


class Hotspot:
    def __init__(self, player):
        self.p, self.aktiv, self.server, self.netze, self.fehler = player, False, None, [], ""

    def ssid(self):
        name = re.sub(r"[^A-Za-z0-9-]", "", self.p.k.get("name", "")).strip("-")[:16]
        return "SignageCast-" + (name or (self.p.k.get("id") or lesen("/etc/machine-id") or "player")[:6])

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
                if (f.get("aktion") or [""])[0] == "fernwartung":      # seit 1.3: am Pi selbst erlauben oder verbieten
                    hs.p.k["fernwartung"] = (f.get("fernwartung") or [""])[0] == "1"
                    konfig_speichern(hs.p.k)
                    log("Fernwartung", "erlaubt" if hs.p.k["fernwartung"] else "verboten", "(Einrichtungsseite)")
                    return self.senden(hs.seite(hinweis=hs.p.t["fw_gespeichert"]))
                ssid = (f.get("ssid_frei") or [""])[0].strip() or (f.get("ssid") or [""])[0].strip()
                pw = (f.get("passwort") or [""])[0]
                if not ssid or not 8 <= len(pw) <= 63:
                    return self.senden(hs.seite("SSID / Passwort (8–63 Zeichen)"))
                self.senden(hs.seite(fertig=True))
                threading.Thread(target=hs.p.wlan_neu, args=(ssid, pw), daemon=True).start()
        return B

    def seite(self, fehler="", fertig=False, hinweis=""):
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
            an = " checked" if self.p.k.get("fernwartung") else ""
            inhalt += (f"<h2>{html.escape(t['fw_titel'])}</h2><form method=post><input type=hidden name=aktion value=fernwartung>"
                       f"<p>{html.escape(t['fw_text'])}</p><label class=k><input type=checkbox name=fernwartung value=1{an}> "
                       f"{html.escape(t['fw_erlauben'])}</label><button>{html.escape(t['fw_speichern'])}</button></form>"
                       + (f"<p>{html.escape(hinweis)}</p>" if hinweis else ""))
        return (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
                f"<title>{html.escape(t['seite_titel'])}</title><style>body{{font:17px system-ui,sans-serif;max-width:28em;margin:2em auto;"
                f"padding:0 16px;background:#111;color:#eee}}label{{display:block;margin:1em 0}}select,input,button{{display:block;width:100%;"
                f"font:inherit;padding:.6em;margin-top:.3em;box-sizing:border-box}}button{{background:#2f7d4f;color:#fff;border:0;border-radius:6px}}"
                f".f{{color:#f88}}h2{{margin-top:2em;font-size:1.2em}}label.k input{{display:inline;width:auto;margin-right:.5em}}</style><h1>{html.escape(t['seite_titel'])}</h1><p>{html.escape(self.p.k.get('name', ''))}</p>{inhalt}")


# ---------- Player ----------
class Player:
    def __init__(self, k):
        self.k = k
        self.t = TEXTE.get(k.get("sprache"), TEXTE["de"])
        self.server = Server(k)
        self.anzeige = Anzeige()
        self.browser = Browser()
        self.direkt_fehler, self.rueckfall_bis, self.rueckfall, self.modus_alt = [], 0, "", None
        self.hotspot = Hotspot(self)
        self.soll = {}                      # letzte Antwort des Servers
        self.ergebnisse = []                # erledigte Befehle für die nächste Meldung
        self.kontakt = 0                    # Zeit der letzten erfolgreichen Meldung
        self.zustand, self.zustand_text = "start", ""
        self.bildschirm = None              # zuletzt per CEC gesetzt
        self.wlan_rev = k.get("wlan_rev", 0)
        self.offline_seit = time.time()
        self.letzte_meldung, self.wlan_laeuft, self.versuche, self.erkennen_bis, self.hotspot_seit = 0, False, 0, 0, 0
        self.kopplung, self.koppel_pause = None, 0     # laufende Kopplung (Image für mehrere Pis)
        self.terminal, self.fw_hinweis_an = None, False    # Fernwartung (seit 1.3)
        self.fern = Fernnetz(self)                         # anderer Standort (seit 1.7)

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
        if PC:
            k.pop("pflege", None)
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
        v = self.anzeige.video_info() if self.anzeige.url and self.anzeige.laeuft() else {}
        return {"version": VERSION, "modell": modell(), "ram_mb": ram_mb(), "netz": art, "ssid": ssid, "signal": signal, "ip": ip,
                "temperatur": temperatur(), "plattform": "pc" if PC else "pi",
                "drossel": lauf("vcgencmd", "get_throttled")[1].partition("=")[2], "laufzeit": int(time.time() - START),
                "hochgefahren": int(float(lesen("/proc/uptime", "0").split()[0])), "hdmi": verbunden, "tv_name": tv_name,
                "ausgang": ausgang, "zustand": self.zustand, "zustand_text": self.zustand_text, "video": v,
                "schreibschutz": schreibschutz_aktiv(), "cec": bool(glob_liste("/dev/cec*")), "wlan_rev": self.wlan_rev,
                "netze": [n["ssid"] for n in self.k.get("wlan") or []], "letztes_update": self.k.get("letztes_update"),
                "ergebnisse": self.ergebnisse[:10], "browser": Browser.verfuegbar(), "modus_ist": "direkt" if self.browser.laeuft() else "stream",
                "rueckfall": self.rueckfall if time.time() < self.rueckfall_bis else "",
                "fernwartung": bool(self.k.get("fernwartung")), "terminal": bool(self.terminal and self.terminal.offen),
                "fern": self.fern.bericht()}

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
            if code == 410:
                self.fern.abmelden()                # seit 1.8: auch aus dem Tailnet
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
                elif art == "player_neu":           # auch: Direktmodus nach einem Rückfall wieder versuchen
                    self.anzeige.beenden()
                    self.browser.beenden()
                    self.direkt_fehler, self.rueckfall_bis, self.rueckfall = [], 0, ""
                elif art == "bild":
                    roh = self.browser.bildschirmfoto() if self.browser.laeuft() else self.anzeige.bildschirmfoto()
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
                elif art == "systemupdate" and PC:      # live-System: Updates kommen mit einem neuen Image
                    erg.update(ok=False, hinweis="pc_image")
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

    # --- Fernwartung (seit 1.3) ---
    def fernwartung(self):
        """Sitzung starten, wenn der Server eine anbietet und dieser Pi Fernwartung erlaubt; sonst eine laufende beenden."""
        t, laeuft = self.soll.get("terminal"), self.terminal and self.terminal.offen
        if not self.k.get("fernwartung"):
            if laeuft:
                self.terminal.schliessen("abgeschaltet")
            return
        if laeuft and (not t or t.get("sid") != self.terminal.sid):
            self.terminal.schliessen("server", melden=False)
        elif t and not laeuft and isinstance(t.get("sid"), str) and re.fullmatch(r"[0-9a-f]{32}", t["sid"]) \
                and (not self.terminal or self.terminal.sid != t["sid"]):
            try:
                self.terminal = Terminal(self.server, self.k, t["sid"], t.get("spalten", 80), t.get("zeilen", 24))
            except OSError as f:
                log("Fernwartung: Shell startet nicht:", f)

    def fernwartung_hinweis(self):
        """Solange eine Sitzung läuft: klein oben rechts auf dem Fernseher (mpv; im Direktmodus zeigt ihn die TV-Seite)."""
        an = bool(self.terminal and self.terminal.offen)
        if an and self.anzeige.laeuft():
            self.anzeige.befehl("osd-overlay", 2, "ass-events", "{\\an9\\pos(1880,40)\\fs30\\bord2\\shad0\\1c&H00D7FF&}" + self.t["fw_hinweis"],
                                1920, 1080, warten=False)
        elif self.fw_hinweis_an and self.anzeige.laeuft():
            self.anzeige.befehl("osd-overlay", 2, "none", "", warten=False)
        self.fw_hinweis_an = an

    def einstellungen_anwenden(self):
        s = self.soll
        opt = {"lautstaerke": max(0, min(130, int(s.get("lautstaerke", 100)))), "drehung": s.get("drehung", 0) if s.get("drehung") in (0, 90, 180, 270) else 0,
               "modus": {"1080": "1920x1080", "2160": "3840x2160", "720": "1280x720"}.get(str(s.get("aufloesung")), "preferred"),
               "hwdec": "aus" if s.get("hwdec") == "aus" else "auto"}
        if opt != self.k.get("anzeige"):            # merken: nach dem Neustart gleich richtig gedreht
            self.k["anzeige"] = opt
            konfig_speichern(self.k)
        if self.browser.laeuft() and opt != self.browser.optionen:
            if {k: v for k, v in opt.items() if k != "lautstaerke"} == {k: v for k, v in self.browser.optionen.items() if k != "lautstaerke"}:
                self.browser.optionen = opt
                self.browser.lautstaerke_setzen(opt["lautstaerke"])
            else:
                self.browser.beenden()              # neu mit Drehung/Auflösung (nächste Runde)
        elif self.browser.laeuft() and self.browser.lautstaerke != opt["lautstaerke"]:
            self.browser.lautstaerke_setzen(opt["lautstaerke"])
        if s.get("modus") != self.modus_alt:        # Modus in der Verwaltung geändert: neuer Versuch ohne Rückfall
            self.modus_alt, self.direkt_fehler, self.rueckfall_bis, self.rueckfall = s.get("modus"), [], 0, ""
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
            self.browser.beenden()
            sys.exit(0)

    # --- Hauptschleife ---
    def schritt(self):
        jetzt = time.time()
        try:
            self.fern.schritt(jetzt)
        except Exception as f:                  # das Fernnetz darf die Anzeige nie aufhalten
            log("Fernnetz:", repr(f)[:200])
        intervall = max(5, min(120, int(self.soll.get("intervall", 15))))
        if self.k.get("schluessel") and (jetzt - self.letzte_meldung >= intervall or (self.ergebnisse and jetzt - self.kontakt < 60)):
            self.letzte_meldung = jetzt
            if self.melden_versuch():
                self.einstellungen_anwenden()
                self.befehle()
                self.fernwartung()
        self.fernwartung_hinweis()
        if self.wlan_laeuft:
            self.browser.beenden()
            return
        direkt = self.direkt_gewuenscht(jetzt)
        if self.browser.laeuft() and not direkt:
            self.browser.beenden()
        if not self.anzeige.laeuft() and not direkt:
            if (hdmi()[0] or not ausgaenge()) and jetzt - self.anzeige.gestartet > 10:
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
        if not self.k.get("schluessel"):
            return self.koppel_schritt(jetzt)
        if self.erkennen_bis > jetzt:
            self.anzeige.zeigen([self.k.get("name", ""), f"{modell()} · {netz()[3]}", self.k["id"]])
            return
        if self.zustand in ("gesperrt", "unbekannt", "fern_weg"):
            self.anzeige.zeigen([self.t[self.zustand], self.k.get("name", "")])
            return
        if not online and self.fern.url:            # anderer Standort per Link: hier freigeben (seit 1.8)
            self.zustand = "fern_link"
            self.anzeige.zeigen([self.t["fern_link"], self.k.get("name", ""), self.t["fern_link2"]], qr=self.fern.url)
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
        if direkt:
            return self.direkt_schritt(jetzt)
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

    # --- Kopplung (Image für mehrere Pis) ---
    def koppel_schritt(self, jetzt):
        self.zustand = "koppeln"
        kp = self.kopplung
        if not kp or jetzt > kp["bis"]:
            if jetzt < self.koppel_pause:
                return
            try:
                kp = self.kopplung = self.koppel_start(jetzt)
            except (OSError, ValueError, KeyError) as f:
                self.kopplung, self.koppel_pause = None, jetzt + 30
                self.zustand_text = str(f)[:120]
                self.anzeige.zeigen([self.t["verbinde"] if jetzt - START < 90 else self.t["kein_server"], self.server.basis(), self.zustand_text])
                return
        self.anzeige.zeigen([self.t["code"].format(code=kp["code"][:3] + " " + kp["code"][3:]), self.t["koppeln1"], self.t["koppeln2"],
                             f"{modell()} · {netz()[3] or ''}"])
        if jetzt - kp["gefragt"] < 5:
            return
        kp["gefragt"] = jetzt
        nonce = secrets.token_hex(16)
        try:
            code, inhalt, kopf = self.server.offen("/player/koppeln/status", {"kennung": kp["kennung"], "zeit": nonce})
        except OSError as f:
            self.zustand_text = str(f)[:120]
            return
        if code == 404:                    # abgelaufen oder Server neu gestartet: neuer Code
            self.kopplung = None
            return
        if code != 200:
            return
        erwartet = hmac.new(bytes.fromhex(kp["schluessel"]), f"antwort\n{nonce}\n".encode() + inhalt, "sha256").hexdigest()
        if not hmac.compare_digest(erwartet, kopf.get("X-Signatur", "")):
            log("Kopplung: Antwort ohne gültige Signatur")
            return
        d = json.loads(inhalt)
        if not re.fullmatch(r"[0-9a-f]{8}", str(d.get("id", ""))):
            return
        self.k.update(id=d["id"], schluessel=kp["schluessel"], name=str(d.get("name", ""))[:40],
                      hostname=str(d.get("hostname") or self.k.get("hostname") or "sc-player")[:30])
        self.k.pop("kopplung", None)
        konfig_speichern(self.k)
        log(f"Gekoppelt als {d['id']} „{self.k['name']}“")
        if re.fullmatch(r"[a-z0-9-]{1,30}", self.k["hostname"]):
            lauf("hostnamectl", "set-hostname", self.k["hostname"])
        self.server, self.kopplung, self.zustand, self.zustand_text, self.letzte_meldung = Server(self.k), None, "start", "", 0
        self.anzeige.zeigen([self.t["gekoppelt"], self.k["name"]])

    def koppel_start(self, jetzt):
        """DH-Wert schicken, Antwort des Servers verrechnen: Code für den Bildschirm, Schlüssel für später."""
        a = secrets.randbits(320)
        a_pub = pow(2, a, DH_P)
        code, inhalt, _ = self.server.offen("/player/koppeln", {"a": format(a_pub, "x"), "modell": modell(), "version": VERSION,
                                                                 "plattform": "pc" if PC else "pi"})
        if code == 429:
            raise ValueError("zu viele Kopplungsanfragen – später erneut")
        if code != 200:
            raise ValueError(f"Kopplung: HTTP {code}")
        d = json.loads(inhalt)
        b_pub = int(str(d["b"]), 16)
        if not 2 <= b_pub <= DH_P - 2:
            raise ValueError("Kopplung: ungültige Antwort")
        c, schluessel = dh_ableiten(a, b_pub, a_pub, b_pub)
        gueltig = max(60, min(3600, int(d.get("gueltig") or 600)))
        log(f"Kopplung: Code {c} angezeigt")
        return {"kennung": str(d["kennung"])[:64], "code": c, "schluessel": schluessel, "bis": jetzt + gueltig - 15, "gefragt": 0}

    # --- Direktmodus ---
    def direkt_gewuenscht(self, jetzt):
        s = self.soll
        return (s.get("modus") == "direkt" and Browser.verfuegbar() and jetzt >= self.rueckfall_bis and bool(s.get("stream"))
                and jetzt - self.kontakt < 120 and s.get("bildschirm") != "aus" and not self.hotspot.aktiv
                and self.erkennen_bis <= jetzt and self.zustand not in ("gesperrt", "unbekannt", "fern_weg") and not re.search(r"Pi 3|Zero 2", modell()))

    def direkt_url(self):
        return self.server.basis() + "/anzeige/" + hmac.new(bytes.fromhex(self.k["schluessel"]), b"anzeige", "sha256").hexdigest()[:32]

    def direkt_problem(self, grund, jetzt):
        """Drei Probleme in 10 min: eine Stunde lang den Stream zeigen (die Verwaltung zeigt den Grund)."""
        self.direkt_fehler = [t for t in self.direkt_fehler if jetzt - t < 600] + [jetzt]
        log("Direktmodus:", grund)
        self.browser.beenden()
        if len(self.direkt_fehler) >= 3:
            self.rueckfall, self.rueckfall_bis, self.direkt_fehler = grund, jetzt + 3600, []
            log("Direktmodus: Rückfall auf den Stream für 1 h")

    def direkt_schritt(self, jetzt):
        if self.anzeige.laeuft():                   # mpv gibt den Bildschirm frei (nur einer kann ihn belegen)
            self.anzeige.beenden()
        if not self.browser.laeuft():
            if self.browser.gestartet:              # lief und ist beendet: abgestürzt
                self.direkt_problem("abgestuerzt", jetzt)
                return
            self.zustand, self.zustand_text = "direkt_start", ""
            if not self.browser.starten(self.direkt_url(), self.anzeige.optionen, self.k.get("sprache")):
                self.direkt_problem("startet_nicht", jetzt)
            return
        abruf = self.soll.get("direkt_abruf")
        if jetzt - self.browser.gestartet > 90 and jetzt - self.kontakt < 30 and (abruf is None or abruf > 90):
            self.direkt_problem("seite_laedt_nicht", jetzt)   # der Server sieht keine Abrufe der Seite
            return
        self.zustand, self.zustand_text = "direkt", ""

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
        with open(pfad, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
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
