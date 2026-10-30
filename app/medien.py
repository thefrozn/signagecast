# Eigene Medien: Bilder (JPG/PNG) und Videos (MP4/WebM) für das Videofenster. Hochladen in Stücken (große Videos über
# die Verwaltung), Art am Inhalt erkennen (nicht an der Endung), Dauer/Codec per ffprobe, Name = Prüfsumme.
import hashlib, json, os, re, secrets, subprocess, time

from meldung import Meldung

MAX_DATEI = 1024 * 1024 * 1024           # 1 GB je Datei
KENNUNG = re.compile(r"[a-z0-9]{8,24}")


def art_erkennen(kopf):
    """-> (art, endung) aus den ersten Bytes, sonst Meldung."""
    if kopf[:3] == b"\xff\xd8\xff":
        return "bild", "jpg"
    if kopf[:8] == b"\x89PNG\r\n\x1a\n":
        return "bild", "png"
    if kopf[4:8] == b"ftyp":
        return "video", "mp4"
    if kopf[:4] == b"\x1a\x45\xdf\xa3":
        return "video", "webm"
    raise Meldung("med_art")


def video_pruefen(pfad):
    """Dauer (s) und Video-Codec; H.265 kann Chromium im Container nicht abspielen."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name",
                            "-of", "json", pfad], capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout or "{}")
    except (OSError, subprocess.TimeoutExpired, ValueError):
        raise Meldung("med_kaputt")
    codec = next((s.get("codec_name") for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
    if not codec:
        raise Meldung("med_kaputt")
    if codec in ("hevc", "h265"):
        raise Meldung("med_hevc")
    return max(1, round(float((d.get("format") or {}).get("duration") or 0))), codec


class Hochladen:
    """Datei in Stücken annehmen: teil(kennung, nr, bytes) … fertig(kennung) -> (art, datei, dauer)."""

    def __init__(self, ordner):
        self.ordner = ordner
        self.offen = {}                   # kennung -> {"pfad", "naechste", "groesse", "zeit"}

    def teil(self, kennung, nr, daten):
        if not KENNUNG.fullmatch(kennung or ""):
            raise Meldung("med_upload")
        os.makedirs(self.ordner, exist_ok=True)
        for k in [k for k, v in self.offen.items() if time.time() - v["zeit"] > 3600]:   # liegen gebliebene
            self._weg(k)
        u = self.offen.get(kennung)
        if nr == 0:
            self._weg(kennung)
            u = self.offen[kennung] = {"pfad": os.path.join(self.ordner, f".upload-{kennung}"), "naechste": 0, "groesse": 0}
            open(u["pfad"], "wb").close()
        if not u or nr != u["naechste"]:
            raise Meldung("med_upload")
        u["groesse"] += len(daten)
        if u["groesse"] > MAX_DATEI:
            self._weg(kennung)
            raise Meldung("med_gross")
        with open(u["pfad"], "ab") as f:
            f.write(daten)
        u["naechste"], u["zeit"] = nr + 1, time.time()

    def fertig(self, kennung):
        u = self.offen.pop(kennung, None)
        if not u:
            raise Meldung("med_upload")
        try:
            with open(u["pfad"], "rb") as f:
                art, endung = art_erkennen(f.read(16))
                f.seek(0)
                h = hashlib.sha256()
                for block in iter(lambda: f.read(1 << 20), b""):
                    h.update(block)
            name = f"{h.hexdigest()[:16]}.{endung}"
            dauer = 15
            if art == "video":
                dauer, _ = video_pruefen(u["pfad"])
            os.replace(u["pfad"], os.path.join(self.ordner, name))
            return art, name, dauer
        except Exception:
            try:
                os.remove(u["pfad"])
            except OSError:
                pass
            raise

    def _weg(self, kennung):
        u = self.offen.pop(kennung, None)
        if u:
            try:
                os.remove(u["pfad"])
            except OSError:
                pass


def neue_kennung():
    return secrets.token_hex(4)
