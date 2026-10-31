# Durchsagen (seit 0.19): Sprachausgabe mit Piper (offline), Gong, Passwörter der Pult-Zugänge.
# Piper und die Stimmen lädt der Dienst bei Bedarf selbst (ohne root) – nur mit passender Prüfsumme.
import hashlib, hmac, io, math, os, secrets, struct, subprocess, tarfile, threading, urllib.request, wave

DATEN = os.environ.get("SC_DATEN", "/var/lib/signagecast")
ORDNER = os.path.join(DATEN, "piper")
AUDIO = os.path.join(DATEN, "durchsage")
VOICES = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/de/de_DE"

PIPER = {"url": "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz",
         "sha256": "a50cb45f355b7af1f6d758c1b360717877ba0a398cc8cbe6d2a7a3a26e225992"}
# Nur Stimmen mit freier Lizenz (CC0). Kerstin ist Standard (weiblich, sanft).
STIMMEN = {
    "kerstin": {"name": "Kerstin", "art": "weiblich", "pfad": "kerstin/low/de_DE-kerstin-low",
                "onnx": "d352a7641892cebf2903859af94e9ba81a141110215fe3943bcda7f7da401b7a",
                "json": "56e708556b7b9b7a53c4f8957e021421e69f11a600962bba554cffbe72cf2d47"},
    "thorsten": {"name": "Thorsten", "art": "männlich", "pfad": "thorsten/medium/de_DE-thorsten-medium",
                 "onnx": "7e64762d8e5118bb578f2eea6207e1a35a8e0c30595010b666f983fc87bb7819",
                 "json": "974adee790533adb273a1ac88f49027d2a1b8f0f2cf4905954a4791e79264e85"},
}
_laden = threading.Lock()
stand = {"laeuft": False, "fehler": None}          # Fortschritt des Ladens für die Verwaltung


def _holen(url, sha, ziel):
    """Datei laden, Prüfsumme vergleichen, erst dann an ihren Platz legen."""
    h, tmp = hashlib.sha256(), ziel + ".teil"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "SignageCast"}), timeout=60) as a, \
            open(tmp, "wb") as f:
        for block in iter(lambda: a.read(1 << 20), b""):
            h.update(block); f.write(block)
    if h.hexdigest() != sha:
        os.remove(tmp)
        raise RuntimeError(f"Prüfsumme falsch: {os.path.basename(ziel)}")
    os.replace(tmp, ziel)


def piper_pfad():
    return os.path.join(ORDNER, "piper", "piper")


def bereit(stimme):
    s = STIMMEN.get(stimme)
    return bool(s) and os.path.exists(piper_pfad()) and os.path.exists(os.path.join(ORDNER, stimme + ".onnx"))


def laden(stimme):
    """Piper (falls nötig) und die Stimme laden – einige Minuten bei langsamer Leitung, daher im eigenen Thread."""
    if stimme not in STIMMEN:
        raise ValueError("unbekannte Stimme")
    with _laden:
        stand.update(laeuft=True, fehler=None)
        try:
            os.makedirs(ORDNER, exist_ok=True)
            if not os.path.exists(piper_pfad()):
                tgz = os.path.join(ORDNER, "piper.tgz")
                _holen(PIPER["url"], PIPER["sha256"], tgz)
                with tarfile.open(tgz) as t:     # nur piper/…; filter "data" verhindert Pfade/Links nach außen
                    t.extractall(ORDNER, members=[m for m in t.getmembers() if m.name.startswith("piper/")], filter="data")
                os.remove(tgz)
            s = STIMMEN[stimme]
            for endung, sha in ((".onnx.json", s["json"]), (".onnx", s["onnx"])):
                ziel = os.path.join(ORDNER, stimme + endung)
                if not os.path.exists(ziel):
                    _holen(f"{VOICES}/{s['pfad']}{endung}", sha, ziel)
        except Exception as f:
            stand["fehler"] = str(f)[:200]
            raise
        finally:
            stand["laeuft"] = False


def sprechen(text, stimme, name):
    """Text als WAV nach AUDIO/<name>.wav – dauert etwa 1 s je Satz."""
    os.makedirs(AUDIO, exist_ok=True)
    ziel = os.path.join(AUDIO, name + ".wav")
    r = subprocess.run([piper_pfad(), "--model", os.path.join(ORDNER, stimme + ".onnx"), "--output_file", ziel, "--quiet"],
                       input=text.encode(), capture_output=True, timeout=60,
                       env={"LD_LIBRARY_PATH": os.path.dirname(piper_pfad())})
    if r.returncode or not os.path.exists(ziel):
        raise RuntimeError("Sprachausgabe fehlgeschlagen: " + r.stderr.decode(errors="replace")[-200:])
    return ziel


def gong():
    """Zweiklang (Ding-Dong) einmal selbst erzeugen – keine fremde Tondatei nötig."""
    ziel = os.path.join(AUDIO, "gong.wav")
    if os.path.exists(ziel):
        return ziel
    os.makedirs(AUDIO, exist_ok=True)
    rate, puffer = 22050, io.BytesIO()
    for frequenz, dauer in ((784, 0.55), (587, 0.9)):        # g'' – d''
        for i in range(int(rate * dauer)):
            t = i / rate
            huelle = math.exp(-3.2 * t) * min(1, t * 200)
            wert = huelle * (0.6 * math.sin(2 * math.pi * frequenz * t) + 0.2 * math.sin(4 * math.pi * frequenz * t))
            puffer.write(struct.pack("<h", int(wert * 16000)))
    with wave.open(ziel, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(puffer.getvalue())
    return ziel


def aufraeumen(behalten):
    """Alte Sprachdateien entfernen (Namen nicht in behalten) – Texte sollen nicht liegen bleiben."""
    try:
        for n in os.listdir(AUDIO):
            if n.endswith(".wav") and n != "gong.wav" and n[:-4] not in behalten:
                os.remove(os.path.join(AUDIO, n))
    except OSError:
        pass


# ---------- Passwörter der Pult-Zugänge ----------
def passwort_hash(pw):
    salz = secrets.token_hex(8)
    return f"pbkdf2${200000}${salz}${hashlib.pbkdf2_hmac('sha256', pw.encode(), salz.encode(), 200000).hex()}"


def passwort_ok(pw, gespeichert):
    try:
        _, runden, salz, h = gespeichert.split("$")
        return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256", pw.encode(), salz.encode(), int(runden)).hex(), h)
    except (ValueError, AttributeError):
        return False
