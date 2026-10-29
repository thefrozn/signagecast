# Grafik erkennen: Kann die Grafikeinheit per VAAPI H.265 kodieren, rechnet sie hoch und kodiert (4K möglich);
# sonst Software-Notbetrieb (H.264 in Full HD per CPU). Geprüft wird mit einer kurzen echten Probe-Kodierung –
# ein vorhandenes /dev/dri allein heißt noch nicht, dass H.265 klappt (z. B. ältere oder andere Grafik).
import os, re, subprocess

GERAET = "/dev/dri/renderD128"


def _treiber():
    """Name des VAAPI-Treibers (z. B. 'Intel iHD driver …'), falls vainfo da ist."""
    try:
        r = subprocess.run(["vainfo", "--display", "drm", "--device", GERAET], capture_output=True, text=True, timeout=15)
        m = re.search(r"Driver version:\s*(.+)", r.stdout + r.stderr)
        return m.group(1).strip() if m else None
    except Exception:
        return None


def pruefen():
    if not os.path.exists(GERAET):
        return {"art": "software", "codec": "H.264", "max_hoehe": 1080, "grund": f"{GERAET} fehlt"}
    if not os.access(GERAET, os.R_OK | os.W_OK):
        return {"art": "software", "codec": "H.264", "max_hoehe": 1080, "grund": f"kein Zugriff auf {GERAET}"}
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=25",
                            "-t", "1", "-vaapi_device", GERAET, "-vf", "format=nv12,hwupload", "-c:v", "hevc_vaapi",
                            "-f", "null", "-"], capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return {"art": "vaapi", "codec": "H.265", "max_hoehe": 2160, "treiber": _treiber()}
        grund = (r.stderr.strip().splitlines() or ["H.265 per VAAPI geht nicht"])[-1][:200]
    except Exception as ex:
        grund = str(ex)[:200]
    return {"art": "software", "codec": "H.264", "max_hoehe": 1080, "grund": grund, "treiber": _treiber()}
