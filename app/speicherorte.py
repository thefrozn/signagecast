# Speicherorte (seit 0.48): Ordner auf einem NAS, in einer Cloud oder auf dem Server, zentral eingetragen und von allen
# Dateidialogen der Verwaltung nutzbar („Aus Speicherort“), dazu Verknüpfen (Galerie-Ordner und Datenquellen werden
# regelmäßig abgeglichen) und – mit Schreibrecht – als Ziel der automatischen Sicherung.
#
# Arten:
#   lokal   Ordner auf dem Server unter /mnt, /media, /srv oder /speicherorte (z. B. ein auf dem Proxmox-Host
#           eingebundenes NAS, per Bind-Mount nur lesbar im Container; Docker: Volume nach /speicherorte)
#   webdav  https://… (Nextcloud, ownCloud, NAS) – nur Python-Standardbibliothek
#   smb     smb://server/freigabe/ordner über libsmbclient (Paket python3-smbc), nur SMB3 (siehe smb_konfig)
#
# Sicherheit:
# - Zugangsdaten nur in speicherorte.json (Rechte 600), nie in Einstellungen, Sicherungen, Protokoll oder Antworten an die
#   Verwaltung (dort ••••). Nach dem Einspielen einer Sicherung auf einem neuen Server: Speicherorte neu eintragen.
# - Standard ist „nur lesen“; Schreiben/Löschen nur, wenn beim Speicherort ausdrücklich erlaubt (Sicherung).
# - Pfade sind immer relativ zum eingetragenen Ordner: kein „..“, keine absoluten Pfade, bei „lokal“ auch kein Ausbruch
#   über symbolische Links. WebDAV folgt keinen Umleitungen (der Anmeldekopf ginge sonst an eine fremde Adresse).
# - Antworten und Dateien haben Obergrenzen; nichts wird ohne Prüfung des freien Speichers geschrieben (Aufrufer).
import base64, email.utils, importlib.util, json, os, re, secrets, shutil, ssl, stat, threading, time, urllib.error, urllib.parse, urllib.request

from meldung import Meldung

ARTEN = ("lokal", "webdav", "smb")
MASKE = "••••"
ZEIT = 20                                    # Sekunden je Netzwerk-Anfrage
MAX_ORTE = 20
MAX_LISTE = 5000                             # Einträge je Ordner (mehr wird abgeschnitten, Hinweis in der Antwort)
MAX_PROPFIND = 8 * 1024 * 1024
LOKAL_WURZELN = ("/mnt", "/media", "/srv", "/speicherorte")
ID = re.compile(r"[a-z0-9]{2,12}")
BLOCK = 1 << 20


def rel_pfad(p):
    """Relativen Pfad prüfen und vereinheitlichen ("" = der eingetragene Ordner selbst)."""
    p = str(p or "").replace("\\", "/")
    teile = [t for t in p.split("/") if t not in ("", ".")]
    if len(teile) > 32 or any(t == ".." or "\x00" in t or len(t) > 255 or any(ord(c) < 32 for c in t) for t in teile):
        raise Meldung("so_pfad")
    return "/".join(teile)


# ---------- Arten ----------
def _unter_wurzel(echt):
    return any(echt.startswith(w + "/") for w in LOKAL_WURZELN)


class Lokal:
    def __init__(self, k):
        self.wurzel = os.path.realpath(k["adresse"])
        if not _unter_wurzel(self.wurzel):     # auch, wenn der Ordner später durch einen Link ersetzt wurde
            raise Meldung("so_lokal", wurzeln=", ".join(LOKAL_WURZELN))

    def _voll(self, rel):
        p = os.path.realpath(os.path.join(self.wurzel, rel_pfad(rel)))
        if p != self.wurzel and not p.startswith(self.wurzel.rstrip("/") + "/"):
            raise Meldung("so_pfad")
        return p

    def _fehler(self, ex):
        if isinstance(ex, FileNotFoundError):
            return Meldung("so_fehlt")
        if isinstance(ex, PermissionError):
            return Meldung("so_rechte")
        return Meldung("so_fehler", d=getattr(ex, "strerror", None) or ex)

    def liste(self, rel):
        try:
            aus = []
            with os.scandir(self._voll(rel)) as it:
                for x in it:
                    try:
                        s = x.stat()
                    except OSError:
                        continue
                    ordner = stat.S_ISDIR(s.st_mode)
                    if ordner or stat.S_ISREG(s.st_mode):
                        aus.append({"name": x.name, "ordner": ordner, "groesse": 0 if ordner else s.st_size, "zeit": int(s.st_mtime)})
            return aus
        except OSError as ex:
            raise self._fehler(ex) from None

    def info(self, rel):
        try:
            s = os.stat(self._voll(rel))
        except OSError as ex:
            raise self._fehler(ex) from None
        return {"ordner": stat.S_ISDIR(s.st_mode), "groesse": s.st_size, "zeit": int(s.st_mtime)}

    def lesen(self, rel):
        try:
            return open(self._voll(rel), "rb")
        except OSError as ex:
            raise self._fehler(ex) from None

    def schreiben(self, rel, quelle):
        ziel = self._voll(rel)
        tmp = os.path.join(os.path.dirname(ziel), f".signagecast-{secrets.token_hex(4)}.tmp")
        try:
            with open(quelle, "rb") as q, open(tmp, "wb") as f:
                shutil.copyfileobj(q, f, BLOCK)
            os.replace(tmp, ziel)
        except OSError as ex:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise self._fehler(ex) from None

    def loeschen(self, rel):
        try:
            os.remove(self._voll(rel))
        except OSError as ex:
            raise self._fehler(ex) from None


class _KeinUmleiten(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None                          # 3xx wird zum Fehler – der Anmeldekopf geht nie an eine andere Adresse


class WebDAV:
    def __init__(self, k):
        self.basis = k["adresse"].rstrip("/") + "/"
        self.basispfad = urllib.parse.urlparse(self.basis).path
        self.kopf = {"User-Agent": "SignageCast"}
        if k["benutzer"]:
            self.kopf["Authorization"] = "Basic " + base64.b64encode(f'{k["benutzer"]}:{k["passwort"]}'.encode()).decode()
        self.oeffner = urllib.request.build_opener(_KeinUmleiten, urllib.request.HTTPSHandler(context=ssl.create_default_context()))

    def _url(self, rel, ordner=False):
        rel = rel_pfad(rel)
        return self.basis + urllib.parse.quote(rel) + ("/" if ordner and rel else "")

    def _anfrage(self, methode, url, daten=None, kopf=None):
        r = urllib.request.Request(url, data=daten, method=methode, headers=dict(self.kopf, **(kopf or {})))
        try:
            return self.oeffner.open(r, timeout=ZEIT)
        except urllib.error.HTTPError as f:
            code = f.code
            f.close()
            if code in (401, 403):
                raise Meldung("so_anmeldung") from None
            if code == 404:
                raise Meldung("so_fehlt") from None
            if 300 <= code < 400:
                raise Meldung("so_umleitung") from None
            if code == 507:
                raise Meldung("so_ziel_voll") from None
            raise Meldung("so_http", code=code) from None
        except (urllib.error.URLError, OSError) as ex:
            raise Meldung("so_nicht_erreichbar", d=getattr(ex, "reason", None) or ex) from None

    def liste(self, rel):
        body = (b'<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:resourcetype/><d:getcontentlength/>'
                b'<d:getlastmodified/></d:prop></d:propfind>')
        url = self._url(rel, True)
        with self._anfrage("PROPFIND", url, body, {"Depth": "1", "Content-Type": "application/xml"}) as a:
            roh = a.read(MAX_PROPFIND + 1)
        if len(roh) > MAX_PROPFIND:
            raise Meldung("so_zu_viele")
        import xml.etree.ElementTree as ET     # erst bei Bedarf (Arbeitsspeicher des Dienstes)
        try:
            wurzel = ET.fromstring(roh)
        except ET.ParseError as ex:
            raise Meldung("so_antwort", d=ex) from None
        eigen = urllib.parse.unquote(urllib.parse.urlparse(url).path).rstrip("/")
        aus = []
        for r in wurzel.findall("{DAV:}response"):
            href = urllib.parse.unquote(urllib.parse.urlparse(r.findtext("{DAV:}href") or "").path)
            if not href or href.rstrip("/") == eigen:
                continue
            prop = None
            for ps in r.findall("{DAV:}propstat"):
                if " 200 " in (ps.findtext("{DAV:}status") or " 200 ") + " ":
                    prop = ps.find("{DAV:}prop")
                    break
            if prop is None:
                continue
            name = href.rstrip("/").rsplit("/", 1)[-1]
            ordner = prop.find("{DAV:}resourcetype/{DAV:}collection") is not None
            try:
                groesse = int(prop.findtext("{DAV:}getcontentlength") or 0)
            except ValueError:
                groesse = 0
            try:
                zeit = int(email.utils.parsedate_to_datetime(prop.findtext("{DAV:}getlastmodified")).timestamp())
            except (TypeError, ValueError):
                zeit = 0
            if name:
                aus.append({"name": name, "ordner": ordner, "groesse": 0 if ordner else groesse, "zeit": zeit})
        return aus

    def info(self, rel):
        rel = rel_pfad(rel)
        oben, _, name = rel.rpartition("/")
        if not name:
            self.liste("")
            return {"ordner": True, "groesse": 0, "zeit": 0}
        x = next((x for x in self.liste(oben) if x["name"] == name), None)
        if not x:
            raise Meldung("so_fehlt")
        return x

    def lesen(self, rel):
        return self._anfrage("GET", self._url(rel))

    def schreiben(self, rel, quelle):
        with open(quelle, "rb") as f:
            with self._anfrage("PUT", self._url(rel), f, {"Content-Length": str(os.path.getsize(quelle)),
                                                          "Content-Type": "application/octet-stream"}):
                pass

    def loeschen(self, rel):
        with self._anfrage("DELETE", self._url(rel)):
            pass


SMB_KONFIG = "# SignageCast (seit 0.48): Speicherorte per SMB nur mit SMB3\n[global]\n   client min protocol = SMB3\n"


def smb_konfig():
    """libsmbclient liest beim ersten Kontext $HOME/.smb/smb.conf – dort SMB3 als Mindestversion (pysmbc kennt dafür keine
    Option). HOME ist im LXC und im Container /var/lib/signagecast. Gelingt das nicht, gilt Sambas Standard (SMB2 oder neuer)."""
    home = os.environ.get("HOME") or ""
    if not home.startswith("/"):
        return False
    pfad = os.path.join(home, ".smb", "smb.conf")
    try:
        with open(pfad) as f:
            if f.read() == SMB_KONFIG:
                return True
    except OSError:
        pass
    try:
        os.makedirs(os.path.dirname(pfad), mode=0o700, exist_ok=True)
        with open(pfad + ".tmp", "w") as f:
            f.write(SMB_KONFIG)
        os.replace(pfad + ".tmp", pfad)
        return True
    except OSError:
        return False


class SMB:
    """libsmbclient ist nicht threadsicher: je Vorgang ein eigener Kontext, alle Vorgänge nacheinander."""
    sperre = threading.Lock()
    konfig = None

    def __init__(self, k):
        try:
            import smbc
        except ImportError:
            raise Meldung("so_smb_fehlt") from None
        if SMB.konfig is None:
            SMB.konfig = smb_konfig()
        self.smbc = smbc
        teile = urllib.parse.urlparse(k["adresse"])
        self.basis = "smb://" + teile.netloc + urllib.parse.quote(urllib.parse.unquote(teile.path.rstrip("/")))
        benutzer, domaene = k["benutzer"], ""
        if "\\" in benutzer:
            domaene, benutzer = benutzer.split("\\", 1)
        self.anmeldung = (domaene, benutzer, k["passwort"])

    def _kontext(self):
        c = self.smbc.Context(auth_fn=lambda server, freigabe, gruppe, b, p: self.anmeldung)
        c.optionNoAutoAnonymousLogin = True
        c.timeout = ZEIT * 1000
        return c

    def _url(self, rel):
        rel = rel_pfad(rel)
        return self.basis + ("/" + urllib.parse.quote(rel) if rel else "")

    def _fehler(self, ex):
        n = ex.args[0] if getattr(ex, "args", None) and isinstance(ex.args[0], int) else None
        art = lambda x: getattr(self.smbc, x, ())              # noqa: E731
        if isinstance(ex, art("PermissionError")) or n in (1, 13):
            return Meldung("so_anmeldung")
        if isinstance(ex, art("NoEntryError")) or n == 2:
            return Meldung("so_fehlt")
        if isinstance(ex, (art("TimedOutError"), art("ConnectionRefusedError"))) or n in (110, 111, 113, 101, 112):
            return Meldung("so_nicht_erreichbar", d=ex.args[-1] if ex.args else ex)
        return Meldung("so_fehler", d=ex.args[-1] if getattr(ex, "args", None) else ex)

    def _ausfuehren(self, f):
        with SMB.sperre:
            try:
                return f(self._kontext())
            except Meldung:
                raise
            except Exception as ex:          # pysmbc: eigene Fehlerklassen bzw. RuntimeError/ValueError mit errno
                raise self._fehler(ex) from None

    def liste(self, rel):
        def f(c):
            aus = []
            for x in c.opendir(self._url(rel)).getdents():
                if x.name in (".", "..") or x.smbc_type not in (self.smbc.DIR, self.smbc.FILE):
                    continue
                ordner = x.smbc_type == self.smbc.DIR
                groesse, zeit = 0, 0
                if not ordner:
                    try:
                        s = c.stat(self._url((rel_pfad(rel) + "/" if rel_pfad(rel) else "") + x.name))
                        groesse, zeit = s[6], int(s[8])
                    except Exception:
                        pass
                aus.append({"name": x.name, "ordner": ordner, "groesse": groesse, "zeit": zeit})
                if len(aus) > MAX_LISTE:
                    break
            return aus
        return self._ausfuehren(f)

    def info(self, rel):
        def f(c):
            s = c.stat(self._url(rel))
            return {"ordner": stat.S_ISDIR(s[0]), "groesse": s[6], "zeit": int(s[8])}
        return self._ausfuehren(f)

    def kopieren(self, rel, ziel, max_bytes):
        def f(c):
            q = c.open(self._url(rel), os.O_RDONLY)
            n = 0
            try:
                with open(ziel, "wb") as z:
                    while True:
                        b = q.read(BLOCK)
                        if not b:
                            break
                        n += len(b)
                        if n > max_bytes:
                            raise Meldung("so_gross", mb=max_bytes // (1024 * 1024))
                        z.write(b)
            finally:
                q.close()
            return n
        return self._ausfuehren(f)

    def schreiben(self, rel, quelle):
        def f(c):
            z = c.open(self._url(rel), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)
            try:
                with open(quelle, "rb") as q:
                    for b in iter(lambda: q.read(BLOCK), b""):
                        z.write(b)
            finally:
                z.close()
        return self._ausfuehren(f)

    def loeschen(self, rel):
        return self._ausfuehren(lambda c: c.unlink(self._url(rel)))


ZUGANG = {"lokal": Lokal, "webdav": WebDAV, "smb": SMB}


# ---------- Verwaltung der Speicherorte ----------
def _leer(oid=""):
    return {"id": oid, "name": "", "art": "webdav", "adresse": "", "benutzer": "", "passwort": "", "schreiben": False}


def smb_verfuegbar():
    """Ohne zu laden: libsmbclient belegt im Dienst ~13 MB, erst wenn wirklich ein SMB-Speicherort benutzt wird."""
    return importlib.util.find_spec("smbc") is not None


class Speicherorte:
    def __init__(self, pfad):
        self.pfad = pfad
        self.sperre = threading.Lock()
        self.orte = []
        self.zustand = {}                    # id -> {"ok", "zeit", "fehler_m"} (letzter Zugriff, nur im Speicher)
        try:
            with open(pfad) as f:
                d = json.load(f)
            for o in (d.get("orte") if isinstance(d, dict) else None) or []:
                k = _leer()
                k.update({x: o[x] for x in k if x in o and isinstance(o[x], type(k[x]))})
                if ID.fullmatch(k["id"]) and k["art"] in ARTEN:
                    self.orte.append(k)
        except (OSError, ValueError, AttributeError):
            pass

    # --- Einstellungen ---
    def aussen(self):
        """Für die Verwaltung – Passwörter nur als ••••, dazu der letzte Zustand."""
        return [dict(o, passwort=MASKE if o["passwort"] else "", zustand=self.zustand.get(o["id"]),
                     unverschluesselt=o["art"] == "webdav" and o["adresse"].startswith("http://")) for o in self.orte]

    def ids(self):
        return {o["id"] for o in self.orte}

    def ort(self, oid):
        o = next((o for o in self.orte if o["id"] == oid), None)
        if not o:
            raise Meldung("so_unbekannt")
        return o

    def name(self, oid):
        try:
            return self.ort(oid)["name"]
        except Meldung:
            return ""

    def speichern(self, liste):
        alt = {o["id"]: o for o in self.orte}
        neu, ids = [], set()
        for d in (liste or [])[:MAX_ORTE + 1]:
            if len(neu) >= MAX_ORTE:
                raise Meldung("so_viele", n=MAX_ORTE)
            if not isinstance(d, dict):
                raise Meldung("so_adresse")
            oid = str(d.get("id") or "")
            if not ID.fullmatch(oid) or oid in ids:
                oid = secrets.token_hex(3)
            ids.add(oid)
            k = _leer(oid)
            k["name"] = re.sub(r"[\x00-\x1f]", "", str(d.get("name") or "")).strip()[:40]
            k["art"] = str(d.get("art") or "")
            if k["art"] not in ARTEN:
                raise Meldung("so_art")
            k["adresse"] = str(d.get("adresse") or "").strip()
            k["benutzer"] = str(d.get("benutzer") or "").strip()[:120]
            pw = str(d.get("passwort") or "")
            k["passwort"] = (alt.get(oid) or {}).get("passwort", "") if pw == MASKE else pw[:300]
            k["schreiben"] = bool(d.get("schreiben"))
            if any(c in k["benutzer"] + k["passwort"] for c in "\r\n\x00"):
                raise Meldung("so_zugang")
            if k["art"] == "lokal":
                k["benutzer"] = k["passwort"] = ""
                p = os.path.normpath(k["adresse"]) if k["adresse"].startswith("/") else ""
                if not p or not _unter_wurzel(p) or not _unter_wurzel(os.path.realpath(p)):
                    raise Meldung("so_lokal", wurzeln=", ".join(LOKAL_WURZELN))
                k["adresse"] = p
            elif k["art"] == "webdav":
                u = urllib.parse.urlparse(k["adresse"])
                if u.scheme not in ("http", "https") or not u.hostname or u.username or u.query or u.fragment or len(k["adresse"]) > 500:
                    raise Meldung("so_adresse")
            else:
                u = urllib.parse.urlparse(k["adresse"])
                teile = [t for t in u.path.split("/") if t]
                if u.scheme != "smb" or not u.hostname or u.username or u.query or not teile or len(k["adresse"]) > 500:
                    raise Meldung("so_adresse_smb")
            k["name"] = k["name"] or (u.hostname if k["art"] != "lokal" else os.path.basename(k["adresse"])) or oid
            neu.append(k)
        with self.sperre:
            self.orte = neu
            for oid in list(self.zustand):
                if oid not in ids:
                    self.zustand.pop(oid, None)
            tmp = self.pfad + ".tmp"
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                json.dump({"orte": neu}, f)
            os.replace(tmp, self.pfad)

    # --- Zugriff ---
    def _zugang(self, oid):
        o = self.ort(oid)
        return o, ZUGANG[o["art"]](o)

    def _merken(self, oid, ex=None):
        from meldung import als_dict
        self.zustand[oid] = {"ok": ex is None, "zeit": int(time.time()), "fehler_m": als_dict(ex) if ex else None}

    def _mit(self, oid, f):
        try:
            _, z = self._zugang(oid)
            r = f(z)
        except Meldung as ex:
            if ex.code not in ("so_unbekannt", "so_pfad", "so_gross", "so_nur_lesen", "so_typ"):
                self._merken(oid, ex)
            raise
        self._merken(oid)
        return r

    def ordner(self, oid, rel=""):
        """Inhalt eines Ordners: Unterordner zuerst, dann Dateien, je nach Name; versteckte Einträge (.…) ausgelassen."""
        def f(z):
            l = [x for x in z.liste(rel) if not x["name"].startswith(".") and x["name"] not in ("@eaDir", "#recycle", "$RECYCLE.BIN")]
            l.sort(key=lambda x: (not x["ordner"], x["name"].lower()))
            return l[:MAX_LISTE], len(l) > MAX_LISTE
        eintraege, mehr = self._mit(oid, f)
        return {"pfad": rel_pfad(rel), "eintraege": eintraege, "mehr": mehr}

    def info(self, oid, rel):
        return self._mit(oid, lambda z: z.info(rel))

    def kopieren(self, oid, rel, ziel, max_bytes):
        """Datei nach ziel (lokaler Pfad) kopieren -> Bytes. Zu groß: Meldung so_gross, ziel wird gelöscht."""
        if not rel_pfad(rel):
            raise Meldung("so_typ")

        def f(z):
            if isinstance(z, SMB):
                return z.kopieren(rel, ziel, max_bytes)
            n = 0
            with z.lesen(rel) as q, open(ziel, "wb") as d:
                while True:
                    b = q.read(BLOCK)
                    if not b:
                        break
                    n += len(b)
                    if n > max_bytes:
                        raise Meldung("so_gross", mb=max_bytes // (1024 * 1024))
                    d.write(b)
            return n
        try:
            return self._mit(oid, f)
        except Exception:
            try:
                os.remove(ziel)
            except OSError:
                pass
            raise

    def lesen(self, oid, rel, max_bytes, arbeitsordner):
        """Kleine Datei als Bytes (CSV, Sicherung, Playlist …)."""
        tmp = os.path.join(arbeitsordner, f".speicherort-{secrets.token_hex(4)}")
        try:
            self.kopieren(oid, rel, tmp, max_bytes)
            with open(tmp, "rb") as f:
                return f.read()
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass

    def _schreibrecht(self, oid):
        if not self.ort(oid)["schreiben"]:
            raise Meldung("so_nur_lesen")

    def ablegen(self, oid, rel, quelle):
        self._schreibrecht(oid)
        if not rel_pfad(rel):
            raise Meldung("so_typ")
        return self._mit(oid, lambda z: z.schreiben(rel, quelle))

    def entfernen(self, oid, rel):
        self._schreibrecht(oid)
        if not rel_pfad(rel):
            raise Meldung("so_typ")
        return self._mit(oid, lambda z: z.loeschen(rel))

    def pruefen(self, oid):
        """Verbindung testen: Ordner lesen; mit Schreibrecht zusätzlich eine kleine Datei anlegen und löschen."""
        t0 = time.time()
        d = self.ordner(oid, "")
        geschrieben = None
        if self.ort(oid)["schreiben"]:
            import tempfile
            name = f".signagecast-test-{secrets.token_hex(3)}"
            with tempfile.NamedTemporaryFile() as t:
                t.write(b"SignageCast")
                t.flush()
                self.ablegen(oid, name, t.name)
            self.entfernen(oid, name)
            geschrieben = True
        return {"eintraege": len(d["eintraege"]), "schreiben": geschrieben, "ms": round((time.time() - t0) * 1000)}
