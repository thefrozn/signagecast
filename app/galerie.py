# Galerie (seit 0.45): Ordner mit Bildern und PDFs, direkt in SignageCast hochgeladen (kein Cloud-Dienst).
# Die Ordner selbst (Kennung, Name) stehen in den Einstellungen ("galerie": {"ordner": […]}) und damit in der Sicherung;
# der Inhalt liegt in DATEN/galerie:
#   dateien/<prüfsumme>.jpg|png    Bild, beim Hochladen auf höchstens 3840 x 2160 verkleinert (nur diese Fassung bleibt)
#   dateien/<prüfsumme>/1.jpg …    PDF, Seite für Seite (app/pdf.py)
#   dateien/<prüfsumme>.k.jpg      Vorschaubild für die Verwaltung (320 px breit)
#   eintraege.json                 {ordner-id: [{"id", "name", "art": bild|pdf, "datei", "seiten", "zeit", "bytes"}]}
# Gleicher Inhalt = gleiche Prüfsumme: liegt ein Bild in zwei Ordnern, gibt es die Datei nur einmal.
# Die Bilder kommen nicht in die Sicherung (die ZIP entsteht im Arbeitsspeicher, Gigabytes wären zu viel).
import hashlib, json, os, re, shutil, subprocess, threading, time

from meldung import Meldung
import pdf as PDF

ORDNER_ID = re.compile(r"[a-z0-9]{2,12}")
NAME = re.compile(r"[0-9a-f]{16}")
MAX_BILD = 50 * 1024 * 1024
MAX_PDF = 100 * 1024 * 1024
MAX_EINTRAEGE = 1000                   # je Ordner
MAX_PIXEL = 100_000_000                # größer ist kein Foto, sondern ein Speicherfresser beim Dekodieren
BREITE, HOEHE = 3840, 2160
KLEIN = 320
# Pixelformate mit Durchsichtigkeit -> als PNG behalten (sonst JPG)
ALPHA = {"rgba", "bgra", "argb", "abgr", "ya8", "ya16be", "ya16le", "rgba64be", "rgba64le", "pal8", "yuva420p", "yuva444p",
         "gbrap", "gbrap16le", "gbrap16be"}


def art_erkennen(kopf):
    """-> "bild" | "pdf" aus den ersten Bytes, sonst Meldung (HEIC mit eigenem Hinweis)."""
    if kopf[:3] == b"\xff\xd8\xff" or kopf[:8] == b"\x89PNG\r\n\x1a\n" or kopf[:4] == b"GIF8" or (kopf[:4] == b"RIFF" and kopf[8:12] == b"WEBP"):
        return "bild"
    if PDF.ist_pdf(kopf):
        return "pdf"
    if kopf[4:8] == b"ftyp" and kopf[8:12] in (b"heic", b"heix", b"hevc", b"heim", b"heis", b"mif1", b"msf1", b"avif"):
        raise Meldung("gal_heic")
    raise Meldung("gal_art")


def _pruefsumme(pfad):
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()[:16]


def _ffmpeg(args, zeit_s=90):
    try:
        r = subprocess.run(["nice", "-n", "10", "ffmpeg", "-nostdin", "-v", "error", "-threads", "2"] + args,
                           capture_output=True, timeout=zeit_s)
    except subprocess.TimeoutExpired:
        raise Meldung("gal_zeit", s=zeit_s) from None
    return r.returncode, r.stderr.decode("utf-8", "replace").strip()


def bild_umwandeln(pfad, ziel, name):
    """Bild -> ziel/<name>.jpg|png (höchstens 3840 x 2160, Drehung aus EXIF angewendet). -> Dateiname."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,pix_fmt",
                            "-of", "json", pfad], capture_output=True, text=True, timeout=30)
        s = (json.loads(r.stdout or "{}").get("streams") or [{}])[0]
    except (OSError, subprocess.TimeoutExpired, ValueError):
        raise Meldung("gal_kaputt", d="ffprobe") from None
    b, h = int(s.get("width") or 0), int(s.get("height") or 0)
    if not b or not h:
        raise Meldung("gal_kaputt", d="?")
    if b * h > MAX_PIXEL:
        raise Meldung("gal_pixel", mp=round(b * h / 1e6))
    endung = "png" if s.get("pix_fmt") in ALPHA else "jpg"
    datei = f"{name}.{endung}"
    tmp = os.path.join(ziel, f".neu-{name}.{endung}")
    skal = f"scale=w='min({BREITE},iw)':h='min({HOEHE},ih)':force_original_aspect_ratio=decrease:flags=lanczos"
    code, fehler = _ffmpeg(["-i", pfad, "-frames:v", "1", "-vf", skal] + (["-q:v", "3"] if endung == "jpg" else []) +
                           ["-update", "1", "-y", tmp])
    if code != 0 or not os.path.exists(tmp) or not os.path.getsize(tmp):
        _weg(tmp)
        raise Meldung("gal_kaputt", d=(fehler.splitlines() or ["?"])[-1][:160])
    os.replace(tmp, os.path.join(ziel, datei))
    return datei


def vorschau(quelle, ziel):
    """Kleines Vorschaubild (JPG, 320 px breit) für die Verwaltung – Fehler sind egal (dann ohne Vorschau)."""
    tmp = ziel + ".neu.jpg"
    code, _ = _ffmpeg(["-i", quelle, "-frames:v", "1", "-vf", f"scale='min({KLEIN},iw)':-2:flags=bilinear", "-q:v", "5", "-update", "1", "-y", tmp], 30)
    if code == 0 and os.path.exists(tmp):
        os.replace(tmp, ziel)
    else:
        _weg(tmp)


def _weg(pfad):
    try:
        if os.path.isdir(pfad):
            shutil.rmtree(pfad, ignore_errors=True)
        else:
            os.remove(pfad)
    except OSError:
        pass


class Galerie:
    def __init__(self, wurzel):
        self.wurzel = wurzel
        self.dateien = os.path.join(wurzel, "dateien")
        self.index = os.path.join(wurzel, "eintraege.json")
        self.sperre = threading.RLock()
        self.umwandeln = threading.Lock()      # immer nur eine Umwandlung gleichzeitig (CPU der Fernseher geht vor)
        try:
            with open(self.index) as f:
                d = json.load(f)
            self.daten = {k: v for k, v in d.items() if ORDNER_ID.fullmatch(k) and isinstance(v, list)} if isinstance(d, dict) else {}
        except (OSError, ValueError):
            self.daten = {}

    def _speichern(self):
        os.makedirs(self.wurzel, exist_ok=True)
        tmp = self.index + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.daten, f, ensure_ascii=False)
        os.replace(tmp, self.index)

    def liste(self, oid):
        with self.sperre:
            return [dict(e) for e in self.daten.get(oid, [])]

    def anzahl(self, oid):
        with self.sperre:
            return len(self.daten.get(oid, []))

    def stand(self, oid):
        """Kurzer Fingerabdruck des Ordnerinhalts – die TV-Seite lädt die Liste nur neu, wenn er sich ändert."""
        with self.sperre:
            roh = json.dumps([(e["id"], e["name"]) for e in self.daten.get(oid, [])])
        return hashlib.sha1(roh.encode()).hexdigest()[:10]

    def folien(self, oid):
        """Alles, was die TV-Seite zeigt: je Bild eine Folie, je PDF-Seite eine; Reihenfolge = eigene Reihenfolge."""
        aus = []
        for i, e in enumerate(self.liste(oid)):
            if e["art"] == "pdf":
                aus += [{"u": f"galerie/{e['id']}/{n}.jpg", "n": e["name"], "z": e["zeit"], "i": i} for n in range(1, e["seiten"] + 1)]
            else:
                aus.append({"u": f"galerie/{e['datei']}", "n": e["name"], "z": e["zeit"], "i": i})
        return aus

    def belegt(self):
        summe = 0
        try:
            for n in os.listdir(self.dateien):
                p = os.path.join(self.dateien, n)
                if os.path.isdir(p):
                    summe += sum(os.path.getsize(os.path.join(p, x)) for x in os.listdir(p))
                else:
                    summe += os.path.getsize(p)
        except OSError:
            pass
        return summe

    def hinzufuegen(self, oid, pfad, name, grenze_bytes):
        """Hochgeladene Datei (pfad, wird nicht gelöscht) in den Ordner übernehmen -> Eintrag. Schon im Ordner = derselbe Eintrag."""
        if not ORDNER_ID.fullmatch(oid or ""):
            raise Meldung("gal_ordner")
        if self.anzahl(oid) >= MAX_EINTRAEGE:
            raise Meldung("gal_viele", n=MAX_EINTRAEGE)
        with open(pfad, "rb") as f:
            art = art_erkennen(f.read(16))
        groesse = os.path.getsize(pfad)
        if groesse > (MAX_PDF if art == "pdf" else MAX_BILD):
            raise Meldung("gal_gross", mb=(MAX_PDF if art == "pdf" else MAX_BILD) // (1024 * 1024))
        h = _pruefsumme(pfad)
        with self.sperre:
            schon = next((e for e in self.daten.get(oid, []) if e["id"] == h), None)
        if schon:
            return dict(schon)
        os.makedirs(self.dateien, exist_ok=True)
        with self.umwandeln:
            vorher = self.belegt()
            neu_angelegt = False
            if art == "pdf":
                neu_angelegt = not PDF.seiten(self.dateien, h)
                _, seiten = PDF.umwandeln(pfad, self.dateien)
                datei, bytes_ = None, sum(os.path.getsize(os.path.join(self.dateien, h, x)) for x in os.listdir(os.path.join(self.dateien, h)))
                erste = os.path.join(self.dateien, h, "1.jpg")
            else:
                vorhanden = next((x for x in (f"{h}.jpg", f"{h}.png") if os.path.exists(os.path.join(self.dateien, x))), None)
                datei = vorhanden or bild_umwandeln(pfad, self.dateien, h)
                neu_angelegt = not vorhanden
                seiten, bytes_ = 1, os.path.getsize(os.path.join(self.dateien, datei))
                erste = os.path.join(self.dateien, datei)
            if neu_angelegt and vorher + bytes_ > grenze_bytes:   # Grenze der Galerie: nicht übernehmen
                self._datei_weg(h)
                raise Meldung("gal_voll", gb=round(grenze_bytes / 1024 ** 3, 1))
            if not os.path.exists(os.path.join(self.dateien, f"{h}.k.jpg")):
                vorschau(erste, os.path.join(self.dateien, f"{h}.k.jpg"))
            e = {"id": h, "name": re.sub(r"[\x00-\x1f]", "", str(name or h))[:80] or h, "art": art, "datei": datei, "seiten": seiten,
                 "zeit": int(time.time()), "bytes": bytes_}
            with self.sperre:                  # noch unter self.umwandeln: aufraeumen sieht nie eine Datei ohne Eintrag
                self.daten.setdefault(oid, []).append(e)
                self._speichern()
        return dict(e)

    def _benutzt(self, h):
        return any(e["id"] == h for l in self.daten.values() for e in l)

    def _datei_weg(self, h):
        for n in (f"{h}.jpg", f"{h}.png", f"{h}.k.jpg", h):
            _weg(os.path.join(self.dateien, n))

    def loeschen(self, oid, ids):
        """Einträge aus dem Ordner nehmen; Dateien, die kein Ordner mehr nutzt, gleich löschen. -> Anzahl."""
        ids = set(ids)
        with self.sperre:
            alt = self.daten.get(oid, [])
            self.daten[oid] = [e for e in alt if e["id"] not in ids]
            weg = [e["id"] for e in alt if e["id"] in ids]
            for h in weg:
                if not self._benutzt(h):
                    self._datei_weg(h)
            self._speichern()
        return len(weg)

    def ordnen(self, oid, ids):
        """Eigene Reihenfolge: ids in der neuen Reihenfolge (Fehlende bleiben hinten in alter Reihenfolge)."""
        with self.sperre:
            alt = self.daten.get(oid, [])
            pos = {h: i for i, h in enumerate(ids)}
            self.daten[oid] = sorted(alt, key=lambda e: (pos.get(e["id"], len(pos)), alt.index(e)))
            self._speichern()

    def umbenennen(self, oid, h, name):
        with self.sperre:
            for e in self.daten.get(oid, []):
                if e["id"] == h:
                    e["name"] = re.sub(r"[\x00-\x1f]", "", str(name))[:80] or h
            self._speichern()

    def aufraeumen(self, ordner_ids, alter_s=3600):
        """Inhalte gelöschter Ordner und Dateien ohne Eintrag entfernen (Reste abgebrochener Umwandlungen erst nach alter_s)."""
        with self.sperre:
            weg = [k for k in self.daten if k not in ordner_ids]
            for oid in weg:
                del self.daten[oid]
            if weg:
                self._speichern()
        try:
            namen = os.listdir(self.dateien)
        except OSError:
            return
        for n in namen:
            p = os.path.join(self.dateien, n)
            m = re.fullmatch(r"([0-9a-f]{16})(\.k\.jpg|\.jpg|\.png)?", n)
            try:
                alt = time.time() - os.path.getmtime(p) > alter_s
            except OSError:
                continue
            if not m and not alt:              # .neu-…: gerade in Arbeit
                continue
            with self.umwandeln, self.sperre:  # nie während einer Umwandlung entscheiden
                if not m or not self._benutzt(m.group(1)):
                    _weg(p)
