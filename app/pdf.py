# PDF als Baustein (seit 0.21): beim Hochladen wandelt pdftoppm (Paket poppler-utils) jede Seite in ein JPG um.
# Ordner DATEN/pdf/<prüfsumme>/1.jpg, 2.jpg, … – die TV-Seite blättert nur noch durch Bilder (kein PDF-Betrachter
# im Container nötig). Höchstens SEITEN_MAX Seiten; längste Kante 2160 px (scharf auch auf 4K).
import hashlib, os, re, shutil, subprocess, time

from meldung import Meldung

SEITEN_MAX = 50
KANTE = 2160
NAME = re.compile(r"[0-9a-f]{16}")


def ist_pdf(kopf):
    return kopf[:5] == b"%PDF-"


def seiten(ordner, name):
    """Anzahl der umgewandelten Seiten (0 = unbekannt oder noch nicht da)."""
    try:
        return sum(1 for n in os.listdir(os.path.join(ordner, name)) if re.fullmatch(r"\d{1,3}\.jpg", n))
    except OSError:
        return 0


def umwandeln(pfad, ordner, zeit_s=180):
    """PDF-Datei -> (name, seiten). Gleicher Inhalt = gleicher Name, dann wird nicht neu umgewandelt."""
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        if not ist_pdf(f.read(8)):
            raise Meldung("pdf_art")
        f.seek(0)
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    name = h.hexdigest()[:16]
    ziel = os.path.join(ordner, name)
    if seiten(ordner, name):
        return name, seiten(ordner, name)
    if not shutil.which("pdftoppm"):
        raise Meldung("pdf_werkzeug")
    tmp = ziel + ".neu"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    try:
        r = subprocess.run(["nice", "-n", "10", "pdftoppm", "-jpeg", "-jpegopt", "quality=88", "-scale-to", str(KANTE),
                            "-f", "1", "-l", str(SEITEN_MAX), pfad, os.path.join(tmp, "s")],
                           capture_output=True, timeout=zeit_s)
    except subprocess.TimeoutExpired:
        shutil.rmtree(tmp, ignore_errors=True)
        raise Meldung("pdf_zeit", s=zeit_s) from None
    # pdftoppm nummeriert je nach Seitenzahl mit führenden Nullen (s-1.jpg, s-01.jpg …) -> 1.jpg, 2.jpg …
    teile = sorted((int(m.group(1)), n) for n in os.listdir(tmp) if (m := re.fullmatch(r"s-0*(\d+)\.jpg", n)))
    if r.returncode != 0 or not teile:
        shutil.rmtree(tmp, ignore_errors=True)
        raise Meldung("pdf_kaputt", d=(r.stderr.decode("utf-8", "replace").strip().splitlines() or ["?"])[-1][:160])
    for i, (_, n) in enumerate(teile, 1):
        os.replace(os.path.join(tmp, n), os.path.join(tmp, f"{i}.jpg"))
    shutil.rmtree(ziel, ignore_errors=True)
    os.replace(tmp, ziel)
    return name, len(teile)


def aufraeumen(ordner, benutzt, alter_s=86400):
    """Umgewandelte PDFs entfernen, die kein Layout mehr nutzt (erst nach einem Tag – das Layout ist evtl. noch nicht gespeichert)."""
    try:
        for n in os.listdir(ordner):
            p = os.path.join(ordner, n)
            if (NAME.fullmatch(n) and n not in benutzt or n.endswith(".neu")) and time.time() - os.path.getmtime(p) > alter_s:
                shutil.rmtree(p, ignore_errors=True)
    except OSError:
        pass
