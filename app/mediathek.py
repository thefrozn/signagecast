# Mediathek (seit 0.72): alle Bilder, Videos und PDFs an einem Ort. Die Dateien bleiben, wo sie schon immer lagen
# (DATEN/medien, DATEN/galerie/dateien, DATEN/pdf) – nichts zieht um, keine Adresse ändert sich, die Offline-Kopie und
# die Pis merken nichts. Neu ist nur ein Katalog über der Prüfsumme (16 Hex-Zeichen, gleicher Inhalt = gleicher Eintrag)
# in den Einstellungen ("mediathek": {"dateien": {h: {"name", "tags", "ab", "bis"}}}) und damit in der Sicherung:
#   name   eigener Name (leer = Name aus der Ablage)
#   tags   Schlagwörter (klein, ohne #), für Filter und ab 0.73 für automatische Playlists
#   ab/bis Gültigkeit wie beim Zeitraum eines Bausteins ("YYYY-MM-DD" oder "YYYY-MM-DDTHH:MM", Ortszeit). Ausserhalb
#          zeigt keine Ausgabe die Datei: Videofenster, Galerie-Diashow, PDF-Baustein (der Server lässt sie weg).
# Dazu die Videoumwandlung: Videos, die der Browser auf dem Fernseher oder der Pi nicht sicher abspielt (H.265, MOV,
# MKV, AVI, über Full HD), wandelt der Server im Hintergrund in H.264/AAC (MP4, höchstens 1920 x 1080) um – mit
# nice 19, begrenzten Threads (zusammen gut 2 Kerne) und immer nur eins zur Zeit, damit die laufenden Fernseher kein Bild verlieren.
import json, os, re, subprocess, threading, time

from meldung import Meldung
import layouts as L

H = re.compile(r"[0-9a-f]{16}")
TAG = re.compile(r"[0-9a-zäöüß][0-9a-zäöüß_-]{0,29}")
MAX_DATEIEN = 3000
MAX_TAGS = 10
BALD_TAGE = 3                                  # „läuft ab“ so viele Tage vorher
GUT = {"h264", "vp8", "vp9"}                   # spielt Chromium im Container und auf dem Pi (VP9/AV1 nur Software: siehe 0.29.1)


def tags_pruefen(w):
    if isinstance(w, str):
        w = re.split(r"[\s,;]+", w)
    aus = []
    for t in (w or [])[:50]:
        t = str(t).strip().lstrip("#").lower()
        if t and TAG.fullmatch(t) and t not in aus:
            aus.append(t)
    return aus[:MAX_TAGS]


def pruefen(m, alt):
    """Abschnitt "mediathek" der Einstellungen prüfen (m = neu, alt = bisher) -> geprüfter Abschnitt."""
    aus = {"umwandeln": bool(m.get("umwandeln", alt.get("umwandeln", True))), "dateien": dict(alt.get("dateien") or {})}
    if "dateien" in m:
        neu = {}
        for h, e in list((m.get("dateien") or {}).items())[:MAX_DATEIEN]:
            if not H.fullmatch(str(h)) or not isinstance(e, dict):
                continue
            ab, bis = L._zeitpunkt(e.get("ab")), L._zeitpunkt(e.get("bis"))
            if ab and bis and bis[:len(ab)] < ab:
                raise Meldung("mt_zeitraum")
            eintrag = {"name": re.sub(r"[\x00-\x1f]", "", str(e.get("name") or ""))[:80].strip(),
                       "tags": tags_pruefen(e.get("tags")), "ab": ab, "bis": bis}
            if any(eintrag.values()):              # leere Einträge nicht speichern
                neu[h] = eintrag
        aus["dateien"] = neu
    return aus


def gueltig(meta, h, jetzt):
    """Darf die Datei h jetzt laufen? jetzt = "YYYY-MM-DDTHH:MM" (Ortszeit). Ohne Katalog-Eintrag: immer."""
    e = (meta or {}).get(h)
    return not e or L.im_zeitraum(e, jetzt)


def status(e, jetzt):
    """-> (code, wert): laeuft | ab (wert = ab) | bald (wert = bis) | abgelaufen (wert = bis)."""
    e = e or {}
    ab, bis = e.get("ab") or "", e.get("bis") or ""
    if ab and jetzt[:len(ab)] < ab:
        return "ab", ab
    if bis and not L.im_zeitraum({"bis": bis}, jetzt):
        return "abgelaufen", bis
    if bis:
        grenze = time.strftime("%Y-%m-%dT%H:%M", time.localtime(time.mktime(time.strptime(jetzt, "%Y-%m-%dT%H:%M")) + BALD_TAGE * 86400))
        if not L.im_zeitraum({"bis": bis}, grenze):
            return "bald", bis
    return "laeuft", ""


# ---------- Videoumwandlung ----------
def video_info(pfad):
    """ffprobe -> {"dauer", "codec", "breite", "hoehe", "format"} (format = Container laut ffprobe, z. B. "mov,mp4,…")."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration,format_name:format_tags=major_brand:stream=codec_type,codec_name,width,height",
                            "-of", "json", pfad], capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout or "{}")
    except (OSError, subprocess.TimeoutExpired, ValueError):
        raise Meldung("med_kaputt")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
    if not v:
        raise Meldung("med_kaputt")
    f = d.get("format") or {}
    return {"dauer": max(1, round(float(f.get("duration") or 0))), "codec": v.get("codec_name") or "",
            "breite": int(v.get("width") or 0), "hoehe": int(v.get("height") or 0), "format": f.get("format_name") or "",
            "marke": ((f.get("tags") or {}).get("major_brand") or "").strip()}


def braucht_umwandlung(i, endung):
    """Spielt der Browser das so nicht sicher? (H.265 & Co., QuickTime-/AVI-/MKV-Hülle, mehr als Full HD)"""
    if i["codec"] not in GUT:
        return True
    if endung in ("mov", "mkv", "avi") or i.get("marke") == "qt":
        return True
    if endung == "webm" and i["codec"] == "h264":   # H.264 in einer Matroska-Hülle (MKV mit .webm erkannt)
        return True
    return max(i["breite"], i["hoehe"]) > 1920 or min(i["breite"], i["hoehe"]) > 1080


class Umwandler:
    """Warteschlange: immer nur eine Umwandlung, im Hintergrund. fertig(auftrag, pfad_mp4, dauer) bzw. fehler(auftrag, meldung)
    ruft der Dienst auf (Medium eintragen)."""

    def __init__(self, ordner, fertig, fehler=None):
        self.ordner, self.fertig, self.fehler = ordner, fertig, fehler
        self.auftraege = []                # [{"id", "name", "roh", "dauer", "stand": 0..100, "fehler": None, …}]
        self.sperre = threading.Lock()
        self.neu = threading.Event()
        self.laeuft = None
        try:                               # Aufträge überleben keinen Neustart: liegen gebliebene Reste weg
            for n in os.listdir(ordner):
                if n.startswith((".roh-", ".umwandeln-")):
                    _weg(os.path.join(ordner, n))
        except OSError:
            pass
        threading.Thread(target=self._schleife, daemon=True, name="umwandeln").start()

    def anstellen(self, auftrag):
        with self.sperre:
            self.auftraege.append(dict(auftrag, stand=0, fehler=None, zeit=time.time()))
        self.neu.set()

    def liste(self):
        with self.sperre:
            return [{"id": a["id"], "name": a["name"], "stand": a["stand"], "fehler": a["fehler"], "laeuft": a is self.laeuft}
                    for a in self.auftraege]

    def verwerfen(self, aid):
        """Fehlgeschlagenen Auftrag aus der Liste nehmen (oder wartenden abbrechen)."""
        with self.sperre:
            for a in list(self.auftraege):
                if a["id"] == aid and a is not self.laeuft:
                    self.auftraege.remove(a)
                    _weg(a["roh"])
                    return True
        return False

    def _schleife(self):
        while True:
            self.neu.wait(30)
            self.neu.clear()
            while True:
                with self.sperre:
                    a = next((x for x in self.auftraege if x["fehler"] is None), None)
                    self.laeuft = a
                if not a:
                    break
                ziel = os.path.join(self.ordner, f".umwandeln-{a['id']}.mp4")
                try:
                    self._umwandeln(a, ziel)
                    self.fertig(a, ziel)
                    with self.sperre:
                        self.auftraege.remove(a)
                    _weg(a["roh"])
                except Exception as ex:          # Meldung oder unerwartet: Auftrag bleibt mit Fehler stehen
                    print("Umwandlung:", repr(ex), flush=True)
                    _weg(ziel)
                    a["fehler"] = ex.code if isinstance(ex, Meldung) else "med_umwandeln"
                    if self.fehler:
                        self.fehler(a)
                finally:
                    with self.sperre:
                        self.laeuft = None

    def _umwandeln(self, a, ziel):
        # Größe: höchstens 1920 x 1080 (Hochkant entsprechend), gerade Kantenlängen; Drehung aus den Metadaten wendet
        # ffmpeg selbst an. HDR (HLG/PQ vom Handy) wird nur nach yuv420p gebracht – Farben dann etwas flauer.
        skala = ("scale=w='if(gte(iw,ih),min(1920,iw),min(1080,iw))':h='if(gte(iw,ih),min(1080,ih),min(1920,ih))'"
                 ":force_original_aspect_ratio=decrease:force_divisible_by=2")
        # Threads begrenzen (gemessen 0.72, 4K-H.265): ohne Angabe nimmt ffmpeg knapp 4 Kerne (Dekoder und Skalierer eigene
        # Threads), so gut 2 – Dekoder 1, Filter 1, x264 2 (Vorausschau 1). Dazu nice 19: die Fernseher gehen immer vor.
        befehl = ["nice", "-n", "19", "ffmpeg", "-nostdin", "-v", "error", "-y", "-threads", "1", "-i", a["roh"], "-map", "0:v:0", "-map", "0:a:0?",
                  "-filter_threads", "1", "-vf", skala, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
                  "-profile:v", "high", "-level", "4.1", "-threads", "2", "-x264-params", "lookahead-threads=1", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
                  "-movflags", "+faststart", "-progress", "pipe:1", "-nostats", ziel]
        grenze = time.time() + max(900, a["dauer"] * 8)          # hängt etwas, wird abgebrochen
        p = subprocess.Popen(befehl, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            for zeile in p.stdout:
                m = re.fullmatch(r"out_time_us=(\d+)\s*", zeile)
                if m and a["dauer"]:
                    a["stand"] = min(99, int(int(m.group(1)) / 1e6 / a["dauer"] * 100))
                if time.time() > grenze:
                    p.kill()
                    raise Meldung("med_umwandeln")
            p.wait(timeout=60)
        finally:
            if p.poll() is None:
                p.kill()
        if p.returncode != 0 or not os.path.exists(ziel) or os.path.getsize(ziel) < 1000:
            print("ffmpeg:", (p.stderr.read() or "")[-400:], flush=True)
            raise Meldung("med_umwandeln")
        a["stand"] = 100


def _weg(p):
    try:
        os.remove(p)
    except OSError:
        pass
