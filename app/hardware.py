# Grafik erkennen: Kann die Grafikeinheit per VAAPI H.265 kodieren, rechnet sie hoch und kodiert (4K möglich);
# sonst Software-Notbetrieb (H.264 in Full HD per CPU). Geprüft wird mit einer kurzen echten Probe-Kodierung –
# ein vorhandenes /dev/dri allein heißt noch nicht, dass H.265 klappt (z. B. ältere oder andere Grafik).
# Seit 0.22 je Fernseher wählbar: Encoder (VAAPI, Quick Sync, NVENC, Software), Preset, Tune, B-Frames – die
# ffmpeg-Argumente entstehen hier (video_args) und werden vor der Benutzung kurz probekodiert (probe).
import os, re, shlex, subprocess

GERAET = "/dev/dri/renderD128"
ENCODER = ("auto", "vaapi", "qsv", "nvenc", "software")
PRESETS = ("ultrafast", "superfast", "veryfast", "fast", "medium")
TUNES = ("zerolatency", "keins")
# Quick Sync kennt nur veryfast … veryslow, NVENC p1 (schnell) … p7 (gründlich)
QSV_PRESET = {"ultrafast": "veryfast", "superfast": "veryfast", "veryfast": "faster", "fast": "fast", "medium": "medium"}
NVENC_PRESET = {"ultrafast": "p1", "superfast": "p2", "veryfast": "p3", "fast": "p4", "medium": "p5"}


def video_args(enc, codec, ow, oh, preset="veryfast", tune="zerolatency", bf=0):
    """ffmpeg-Argumente für das Bild (ohne Bitrate/GOP) – Eingang ist x11grab bgr0 in Full HD."""
    h264 = codec == "h264"
    if enc == "software":
        return (f"-c:v libx264 -preset {preset}" + (" -tune zerolatency" if tune == "zerolatency" else "")
                + f" -pix_fmt yuv420p -bf {bf}")
    if enc == "qsv":
        # Fläche hochrechnen wie bei VAAPI, dann die Bilder an Quick Sync weiterreichen (gleiche Grafikeinheit)
        return (f"-init_hw_device vaapi=va:{GERAET} -init_hw_device qsv=qs@va -filter_hw_device va "
                f"-vf hwupload,scale_vaapi=w={ow}:h={oh}:format=nv12,hwmap=derive_device=qsv,format=qsv "
                f"-c:v {'h264_qsv -profile:v high' if h264 else 'hevc_qsv -profile:v main'} -preset {QSV_PRESET[preset]}"
                + (" -async_depth 1" if tune == "zerolatency" else "") + f" -bf {bf}")
    if enc == "nvenc":
        return (f"-init_hw_device cuda=cu:0 -filter_hw_device cu -vf format=nv12,hwupload_cuda,scale_cuda=w={ow}:h={oh} "
                f"-c:v {'h264_nvenc -profile:v high' if h264 else 'hevc_nvenc -profile:v main'} -preset {NVENC_PRESET[preset]}"
                f" -tune {'ull' if tune == 'zerolatency' else 'hq'} -bf {bf}")
    # VAAPI: keine Presets/Tune; B-Frames nur, wenn Grafik und Treiber sie können (die Probe zeigt es)
    return (f"-vaapi_device {GERAET} -vf hwupload,scale_vaapi=w={ow}:h={oh}:format=nv12 "
            f"-c:v {'h264_vaapi -profile:v high' if h264 else 'hevc_vaapi -profile:v main'} -bf {bf}")


def probe(args):
    """Kurze Probe-Kodierung mit genau diesen Argumenten: (ok, Grund) – Grund ist die erste Fehlerzeile von ffmpeg
    (die letzte ist meist nur „Error parsing global options“)."""
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-f", "lavfi", "-i",
                            "testsrc2=size=1920x1080:rate=25,format=bgr0", "-t", "1", *shlex.split(args),
                            "-b:v", "8M", "-g", "50", "-f", "null", "-"], capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return True, None
        zeilen = [z for z in r.stderr.strip().splitlines() if not z.startswith("libva info")]   # libva plaudert vorweg
        return False, (zeilen or ["ffmpeg " + str(r.returncode)])[0][:200]
    except Exception as ex:
        return False, str(ex)[:200]


def _encoder(vaapi_ok):
    """Welche Encoder auf diesem Rechner gehen – „grund“ ist eine Kennung (Text in der Verwaltung) oder ffmpeg-Text."""
    e = {"vaapi": {"ok": vaapi_ok}, "software": {"ok": True}}
    if not os.path.exists(GERAET):
        e["qsv"] = {"ok": False, "grund": "keine_grafik"}
    else:
        ok, grund = probe(video_args("qsv", "h264", 1920, 1080))
        # MFX-Fehler -9: oneVPL findet keine passende Laufzeit – Intel-Grafik älter als 11./12. Generation
        e["qsv"] = {"ok": ok} if ok else {"ok": False, "grund": "qsv_alt" if re.search(r"MFX session|-9\b", grund or "") else grund}
    if not os.path.exists("/dev/nvidia0"):
        e["nvenc"] = {"ok": False, "grund": "keine_nvidia"}
    else:
        ok, grund = probe(video_args("nvenc", "h264", 1920, 1080))
        e["nvenc"] = {"ok": ok} if ok else {"ok": False, "grund": grund}
    return e


def _treiber():
    """Name des VAAPI-Treibers (z. B. 'Intel iHD driver …'), falls vainfo da ist."""
    try:
        r = subprocess.run(["vainfo", "--display", "drm", "--device", GERAET], capture_output=True, text=True, timeout=15)
        m = re.search(r"Driver version:\s*(.+)", r.stdout + r.stderr)
        return m.group(1).strip() if m else None
    except Exception:
        return None


def pruefen():
    k = _pruefen_vaapi()
    k["encoder"] = _encoder(k["art"] == "vaapi")
    return k


def _pruefen_vaapi():
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
