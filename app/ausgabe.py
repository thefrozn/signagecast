# Bildprüfung (seit 0.38): Zeigt ein laufender Fernseher wirklich etwas? Erkennt ein schwarzes oder eingefrorenes Bild,
# auch wenn die Render-Kette sonst gesund aussieht (z. B. abgestürzte Seite im Browser).
#
# Geprüft wird das, was aufgenommen und kodiert wird: der virtuelle Bildschirm (Xvfb) des Fernsehers – ein einzelnes
# Bild, verkleinert auf 160 × 90 Graustufen (ffmpeg x11grab, niedrige Priorität). Bewusst NICHT der fertige Stream:
# Ein Leser am Stream zählte für MediaMTX als Zuschauer und hielte die Kette am Laufen.
# Nur für Fernseher, deren Kette läuft; alle TAKT_S Sekunden. Kosten: ein kurzer ffmpeg-Aufruf (gemessen bei 1080p:
# 0,2 s, 0,1 s CPU, 57 MB kurzzeitig).
#
# Schwarz:  fast alle Bildpunkte dunkel, PRUEFUNGEN-mal in Folge – außer der Zeitplan will „schwarz“.
# Steht:    das Bild ändert sich PRUEFUNGEN-mal in Folge nicht, obwohl das Layout eine sichtbare Uhr hat (sie ändert sich
#           mindestens jede Minute; Layouts ohne Uhr dürfen stillstehen – z. B. nur Text oder ein Bild).
import subprocess

BREITE, HOEHE = 160, 90
TAKT_S = 120
PRUEFUNGEN = 3
DUNKEL = 24                 # Graustufe 0–255: darunter gilt ein Bildpunkt als schwarz
HELL_ERLAUBT = 0.002        # Anteil heller Bildpunkte, der noch als „schwarz“ gilt (Rauschen, einzelne Punkte)
UNTERSCHIED = 16            # so viel muss sich ein Bildpunkt ändern, damit er als geändert zählt (Kodier-Rauschen ignorieren)
GEAENDERT_MIN = 4           # so viele geänderte Bildpunkte = Bild hat sich bewegt


def aufnehmen(anzeige, breite, hoehe, timeout=15):
    """Ein Bild vom virtuellen Bildschirm als Graustufen-Bytes (BREITE × HOEHE) oder None."""
    try:
        r = subprocess.run(["nice", "-n", "19", "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                            "-f", "x11grab", "-draw_mouse", "0", "-video_size", f"{breite}x{hoehe}", "-i", anzeige,
                            "-frames:v", "1", "-vf", f"scale={BREITE}:{HOEHE}:flags=area,format=gray",
                            "-f", "rawvideo", "-"], capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 and len(r.stdout) == BREITE * HOEHE else None


def schwarz(bild):
    hell = sum(1 for b in bild if b > DUNKEL)
    return hell <= len(bild) * HELL_ERLAUBT


def bewegt(a, b):
    n = 0
    for x, y in zip(a, b):
        if abs(x - y) > UNTERSCHIED:
            n += 1
            if n >= GEAENDERT_MIN:
                return True
    return False


class Pruefer:
    def __init__(self):
        self.stand = {}             # tv -> {"bild", "schwarz", "gleich", "befund", "zeit"}

    def pruefen(self, tv, bild, darf_schwarz, muss_bewegen, zeit):
        """Ein neues Bild bewerten. Gibt den Befund zurück: "ok" | "schwarz" | "steht" | "" (noch zu wenig Daten)."""
        s = self.stand.setdefault(tv, {"bild": None, "schwarz": 0, "gleich": 0, "befund": ""})
        if bild is None:
            return s["befund"]
        sw = schwarz(bild) and not darf_schwarz
        s["schwarz"] = s["schwarz"] + 1 if sw else 0
        if muss_bewegen and s["bild"] is not None and not sw:
            s["gleich"] = 0 if bewegt(s["bild"], bild) else s["gleich"] + 1
        elif not muss_bewegen:
            s["gleich"] = 0
        s["bild"], s["zeit"] = bild, zeit
        if s["schwarz"] >= PRUEFUNGEN:
            s["befund"] = "schwarz"
        elif s["gleich"] >= PRUEFUNGEN:
            s["befund"] = "steht"
        elif s["schwarz"] == 0 and s["gleich"] == 0:
            s["befund"] = "ok"
        return s["befund"]

    def vergessen(self, tv):
        self.stand.pop(tv, None)

    def befund(self, tv):
        return (self.stand.get(tv) or {}).get("befund", "")
