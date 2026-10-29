# Sicherung als ZIP: Einstellungen, Streamliste, Strikes, hochgeladene Bilder, Verlauf der Diagramme (und im Docker-
# Betrieb das Passwort der Verwaltung). Mit Zugangsdaten/Passwörtern nur verschlüsselt: AES-256 (WinZip-AES, über
# python3-pyzipper – das Passwort geht nie über eine Befehlszeile) und ein starkes Passwort ist Pflicht.
# Lesbar auch mit 7-Zip/WinRAR (nicht mit den Bordmitteln von Windows/macOS).
import io, json, os, re, time, zipfile

from meldung import Meldung

try:
    import pyzipper
except ImportError:                       # ohne pyzipper: nur unverschlüsselte Sicherungen
    pyzipper = None

ART = "signagecast-sicherung-zip"
NAME = re.compile(r"(auto|manuell)-\d{4}-\d{2}-\d{2}_\d{4}(-geheim)?\.zip")
BILD = re.compile(r"[0-9a-f]{16}\.(jpg|png)")
MAX_ZIP = 300 * 1024 * 1024


def passwort_pruefen(pw):
    """Mindestens 12 Zeichen und drei der vier Zeichenarten (klein, groß, Ziffer, Sonderzeichen) – ab 20 Zeichen reicht
    die Länge (Passphrase). Gleiche oder fortlaufende Zeichen allein sind kein Passwort."""
    pw = pw or ""
    if len(pw) < 12:
        raise Meldung("sich_pw_kurz")
    arten = sum(bool(re.search(m, pw)) for m in (r"[a-z]", r"[A-Z]", r"\d", r"[^a-zA-Z\d]"))
    if (arten < 3 and len(pw) < 20) or len(set(pw)) < 6:
        raise Meldung("sich_pw_schwach")


def erstellen(dateien, passwort=None):
    """dateien: {pfad im ZIP: bytes} -> ZIP (bytes); mit Passwort AES-256."""
    puffer = io.BytesIO()
    if passwort:
        if pyzipper is None:
            raise Meldung("sich_kein_aes")
        z = pyzipper.AESZipFile(puffer, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES)
        z.setpassword(passwort.encode())
        z.setencryption(pyzipper.WZ_AES, nbits=256)
    else:
        z = zipfile.ZipFile(puffer, "w", compression=zipfile.ZIP_DEFLATED)
    with z:
        for name, inhalt in dateien.items():
            z.writestr(name, inhalt)
    return puffer.getvalue()


def lesen(roh, passwort=None):
    """ZIP -> {pfad: bytes}. Verschlüsselt ohne/mit falschem Passwort -> Meldung."""
    if len(roh) > MAX_ZIP:
        raise Meldung("sich_zu_gross")
    try:
        z = (pyzipper.AESZipFile if pyzipper else zipfile.ZipFile)(io.BytesIO(roh))
    except zipfile.BadZipFile:
        raise Meldung("sich_ungueltig")
    with z:
        infos = z.infolist()
        if any(i.flag_bits & 1 for i in infos):
            if pyzipper is None:
                raise Meldung("sich_kein_aes")
            if not passwort:
                raise Meldung("sich_pw_fehlt")
            z.setpassword(passwort.encode())
        aus, gesamt = {}, 0
        for i in infos:
            if i.is_dir() or i.filename.startswith("/") or ".." in i.filename.split("/"):
                continue
            try:
                aus[i.filename] = z.read(i.filename)
            except RuntimeError:
                raise Meldung("sich_pw_falsch")
            gesamt += len(aus[i.filename])
            if gesamt > MAX_ZIP * 2:
                raise Meldung("sich_zu_gross")
    if "manifest.json" not in aus:
        raise Meldung("sich_ungueltig")
    m = json.loads(aus["manifest.json"])
    if m.get("art") != ART:
        raise Meldung("sich_ungueltig")
    return aus


def verschluesselt(pfad):
    try:
        with zipfile.ZipFile(pfad) as z:
            return any(i.flag_bits & 1 for i in z.infolist())
    except (OSError, zipfile.BadZipFile):
        return None


def liste(ordner):
    aus = []
    try:
        namen = sorted(os.listdir(ordner), key=lambda n: os.path.getmtime(os.path.join(ordner, n)), reverse=True)   # neueste zuerst
    except OSError:
        return aus
    for n in namen:
        if NAME.fullmatch(n):
            p = os.path.join(ordner, n)
            aus.append({"name": n, "groesse": os.path.getsize(p), "zeit": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(p))),
                        "auto": n.startswith("auto-"), "geheim": n.endswith("-geheim.zip"), "verschluesselt": verschluesselt(p)})
    return aus


def ablegen(ordner, roh, auto, geheim, behalten=None):
    """Sicherung speichern; bei automatischen nur die letzten `behalten` aufheben."""
    os.makedirs(ordner, mode=0o700, exist_ok=True)
    name = f"{'auto' if auto else 'manuell'}-{time.strftime('%Y-%m-%d_%H%M')}{'-geheim' if geheim else ''}.zip"
    pfad = os.path.join(ordner, name)
    fd = os.open(pfad + ".neu", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(roh)
    os.replace(pfad + ".neu", pfad)
    if auto and behalten:
        for alt in [x["name"] for x in liste(ordner) if x["auto"]][behalten:]:
            os.remove(os.path.join(ordner, alt))
    return name
