# SignageCast – Bild per HDMI auf diesem Rechner (seit 0.52). Läuft als Dienst signagecast-hdmi (Benutzer signagecast).
# Der Datendienst schreibt den Link des HDMI-Geräts nach DATEN/hdmi.json; dieses Skript öffnet ihn in Chromium im
# Kiosk-Rahmen cage – wie der Direktmodus der Player, nur ohne Agent (Server und Anzeige sind derselbe Rechner).
# Ohne HDMI-Gerät und solange der Einrichtungsassistent nicht abgeschlossen ist, bleibt die Konsole sichtbar: dort steht
# die Adresse der Verwaltung. Nur Python-Standardbibliothek.
import json, os, shutil, signal, subprocess, sys, time

DATEN = os.environ.get("SC_DATEN", "/var/lib/signagecast")
EINST = os.environ.get("SC_EINSTELLUNGEN", "/etc/signagecast/einstellungen.json")
PORT = int(os.environ.get("SC_WEBHOOK_PORT", "8890"))
LAUF = os.environ.get("XDG_RUNTIME_DIR", "/run/signagecast-hdmi")
HEIM = os.path.join(DATEN, "hdmi-browser")


def lesen(pfad):
    try:
        with open(pfad) as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def soll():
    """(Adresse, Sprache) – Adresse None: nichts zeigen."""
    pfad = str(lesen(os.path.join(DATEN, "hdmi.json")).get("pfad") or "")
    e = lesen(EINST)
    sprache = "en" if e.get("sprache") == "en" else "de"
    if not pfad.startswith("/anzeige/") or not e.get("assistent_fertig"):
        return None, sprache
    return f"http://127.0.0.1:{PORT}{pfad}", sprache


def befehl(url, sprache):
    chromium = shutil.which("chromium") or shutil.which("chromium-browser") or "chromium"
    return ["cage", "-d", "--", chromium, "--kiosk", "--ozone-platform=wayland", "--noerrdialogs", "--disable-infobars",
            "--no-first-run", "--disable-session-crashed-bubble", "--disable-features=Translate,TranslateUI,MediaRouter",
            "--check-for-update-interval=31536000", "--autoplay-policy=no-user-gesture-required", "--password-store=basic",
            "--overscroll-history-navigation=0", "--disable-pinch", "--force-device-scale-factor=1", "--disk-cache-size=67108864",
            "--enable-features=AcceleratedVideoDecodeLinuxGL,AcceleratedVideoDecodeLinuxZeroCopyGL,VaapiVideoDecoder",
            f"--user-data-dir={HEIM}/chromium", f"--lang={'en-GB' if sprache == 'en' else 'de-DE'}", url]


def umgebung():
    # cage ohne WAYLAND_DISPLAY (sonst sucht wlroots eine laufende Sitzung) und nur mit dem Bildschirm – ohne
    # Eingabegeräte, sonst steht cages Mauszeiger mitten im Bild
    u = {k: v for k, v in os.environ.items() if k != "WAYLAND_DISPLAY"}
    u.update(HOME=HEIM, XDG_RUNTIME_DIR=LAUF, LIBSEAT_BACKEND="seatd", WLR_BACKENDS="drm")
    return u


def stoppen(proc):
    if proc and proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(10)
        except (OSError, subprocess.TimeoutExpired):
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except OSError:
                pass


def main():
    os.makedirs(HEIM, exist_ok=True)
    z = {"proc": None, "url": None, "start": 0.0, "pause": 10}

    def starten(sprache):
        print("Bild per HDMI:", z["url"].rsplit("/", 1)[0] + "/…", flush=True)
        z["proc"] = subprocess.Popen(befehl(z["url"], sprache), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL, env=umgebung(), start_new_session=True)
        z["start"] = time.time()

    def ende(*_):
        stoppen(z["proc"])
        sys.exit(0)
    signal.signal(signal.SIGTERM, ende)
    signal.signal(signal.SIGINT, ende)
    while True:
        url, sprache = soll()
        laeuft = z["proc"] is not None and z["proc"].poll() is None
        if url != z["url"]:                              # neues Gerät, neuer Link oder aus
            stoppen(z["proc"])
            z.update(proc=None, url=url, pause=10)
            if url:
                starten(sprache)
            else:
                print("Bild per HDMI: aus", flush=True)
        elif url and not laeuft and time.time() >= z["start"] + z["pause"]:
            print(f"Browser beendet (Code {z['proc'].returncode if z['proc'] else '?'}) – neuer Versuch", flush=True)
            z["pause"] = min(z["pause"] * 2, 300)        # stürzt er immer wieder ab: seltener versuchen
            starten(sprache)
        elif laeuft and time.time() - z["start"] > 600:
            z["pause"] = 10                              # läuft stabil: Wartezeit zurücksetzen
        time.sleep(5)


if __name__ == "__main__":
    main()
