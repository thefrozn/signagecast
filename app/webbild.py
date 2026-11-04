# Webseite als Bildschirmfoto (seit 0.20): Seiten, die das Einbetten verbieten (X-Frame-Options, CSP frame-ancestors),
# lädt SignageCast selbst in einem kurzlebigen Headless-Chromium und zeigt alle paar Minuten ein Foto davon.
# Nur solange ein Fernseher mit so einem Baustein läuft; immer nur eine Aufnahme gleichzeitig, mit niedriger Priorität.
# Die Fotos bleiben auf der Platte, damit nach dem Einschalten sofort das letzte Bild erscheint.
import hashlib, os, shutil, subprocess, tempfile, threading, time

GROESSE_MAX = 4000                      # Kantenlänge in Pixeln (Schutz vor Unsinnswerten)


def schluessel(url, breite, hoehe, faktor):
    return hashlib.sha256(f"{url}|{breite}x{hoehe}@{faktor}".encode()).hexdigest()[:16]


def aufnehmen(url, breite, hoehe, faktor, ziel, sprache="de", zeit_s=45):
    """Ein Foto der Seite in der Größe breite x hoehe (CSS-Pixel) nach ziel (PNG). Wirft RuntimeError bei Fehlern."""
    profil = tempfile.mkdtemp(prefix="sc-webbild-")
    tmp = ziel + ".neu.png"
    try:
        befehl = ["nice", "-n", "10", "chromium", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                  "--mute-audio", "--no-first-run", "--disable-extensions", "--disable-features=Translate,MediaRouter",
                  f"--lang={sprache}", f"--user-data-dir={profil}", f"--window-size={breite},{hoehe}",
                  f"--force-device-scale-factor={faktor}", "--virtual-time-budget=15000", f"--screenshot={tmp}", url]
        try:
            r = subprocess.run(befehl, capture_output=True, timeout=zeit_s, env=dict(os.environ, HOME=profil))
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"keine Antwort nach {zeit_s} s") from None
        if not os.path.exists(tmp) or os.path.getsize(tmp) < 100:
            fehler = r.stderr.decode("utf-8", "replace").strip().splitlines()
            raise RuntimeError((fehler[-1] if fehler else f"Chromium beendet mit {r.returncode}")[:200])
        os.replace(tmp, ziel)
    finally:
        shutil.rmtree(profil, ignore_errors=True)
        if os.path.exists(tmp):
            os.remove(tmp)


class Fotograf:
    """auftraege() -> [{"url", "breite", "hoehe", "faktor", "alle_min"}]; stand[schluessel] = {"zeit", "fehler"}."""

    def __init__(self, ordner, auftraege, sprache=lambda: "de"):
        self.ordner, self.auftraege, self.sprache = ordner, auftraege, sprache
        self.stand = {}
        self.neu = threading.Event()        # setzen: sofort prüfen (z. B. nach dem Speichern eines Layouts)

    def datei(self, k):
        return os.path.join(self.ordner, k + ".png")

    def bild(self, a):
        """Adresse für die TV-Seite oder None, solange es noch kein Foto gibt."""
        k = schluessel(a["url"], a["breite"], a["hoehe"], a["faktor"])
        try:
            return f"/webbild/{k}.png?t={int(os.path.getmtime(self.datei(k)))}"
        except OSError:
            return None

    def faellig(self, a, jetzt):
        k = schluessel(a["url"], a["breite"], a["hoehe"], a["faktor"])
        s = self.stand.get(k, {})
        try:
            zuletzt = os.path.getmtime(self.datei(k))
        except OSError:
            zuletzt = 0
        if s.get("fehler") and jetzt - s.get("zeit", 0) < 300:          # nach einem Fehler 5 min Pause
            return None
        return k if jetzt - zuletzt >= max(1, a["alle_min"]) * 60 else None

    def einmal(self):
        os.makedirs(self.ordner, exist_ok=True)
        gesehen = set()
        for a in self.auftraege():
            k = self.faellig(a, time.time())
            if not k or k in gesehen:
                continue
            gesehen.add(k)
            try:
                aufnehmen(a["url"], a["breite"], a["hoehe"], a["faktor"], self.datei(k), self.sprache())
                self.stand[k] = {"zeit": time.time(), "fehler": None}
            except (RuntimeError, OSError) as f:
                self.stand[k] = {"zeit": time.time(), "fehler": str(f)}
                print("Webseiten-Foto:", a["url"][:80], f, flush=True)

    def aufraeumen(self, tage=30):
        """Fotos, die 30 Tage nicht erneuert wurden (Baustein gelöscht oder Adresse geändert), entfernen."""
        try:
            for n in os.listdir(self.ordner):
                p = os.path.join(self.ordner, n)
                if n.endswith(".png") and time.time() - os.path.getmtime(p) > tage * 86400:
                    os.remove(p)
        except OSError:
            pass

    def schleife(self):
        while True:
            try:
                self.einmal()
                self.aufraeumen()
            except Exception as ex:                # nie den Dienst mitreißen
                print("Webseiten-Foto:", ex, flush=True)
            self.neu.wait(20)
            self.neu.clear()
