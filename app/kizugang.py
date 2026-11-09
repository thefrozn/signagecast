# Verbundene Computer für KI-Assistenten im Heimnetz (seit 0.40).
#
# Jeder Computer bekommt einen eigenen Schlüssel (Token); gespeichert wird nur dessen SHA-256-Prüfwert. Entfernen in der
# Verwaltung macht den Schlüssel sofort ungültig. Recht je Computer: "aendern" (alle Werkzeuge) oder "lesen" (nur lesende).
#
# Claude Desktop (Datei .mcpb): die Datei enthält keinen dauerhaften Schlüssel, sondern einen Einmal-Code (EINLOESEN_S
# gültig). Die Brücke auf dem Computer tauscht ihn beim ersten Start gegen den Schlüssel und merkt ihn sich dort.
# Andere Programme (Claude Code, Cursor, VS Code) bekommen den Schlüssel direkt – er wird nur einmal angezeigt.
#
# Keine Computer = keine Verbindung möglich (/mcp antwortet 404).
import hashlib, json, os, re, secrets, threading, time

MAX = 20
EINLOESEN_S = 3600
ZULETZT_SPEICHERN_S = 300          # „zuletzt benutzt“ nicht bei jedem Aufruf auf die Platte schreiben
ARTEN = ("desktop", "code", "cursor", "vscode")
RECHTE = ("aendern", "lesen")


class Fehler(ValueError):
    """Kennung einer Meldung (meldung.py)."""


def _hash(geheim):
    return hashlib.sha256(geheim.encode()).hexdigest()


class Zugaenge:
    def __init__(self, pfad):
        self.pfad = pfad
        self.sperre = threading.Lock()
        self.liste_ = []
        self.geschrieben = 0
        try:
            with open(pfad) as f:
                d = json.load(f)
            if isinstance(d, list):
                self.liste_ = [x for x in d if isinstance(x, dict) and x.get("id")]
        except (OSError, ValueError):
            pass

    def _speichern(self):
        tmp = self.pfad + ".tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(self.liste_, f, ensure_ascii=False)
        os.replace(tmp, self.pfad)
        self.geschrieben = time.time()

    def vorhanden(self):
        return bool(self.liste_)

    def liste(self):
        """Ohne Prüfwerte – für die Verwaltung."""
        jetzt = time.time()
        return [{"id": x["id"], "name": x["name"], "art": x["art"], "recht": x["recht"], "erstellt": x["erstellt"],
                 "zuletzt": x.get("zuletzt"), "ip": x.get("ip", ""),
                 "wartet": not x.get("token") and bool(x.get("code")) and x.get("code_bis", 0) > jetzt,
                 "abgelaufen": not x.get("token") and x.get("code_bis", 0) <= jetzt} for x in self.liste_]

    def neu(self, name, art, recht):
        """Gibt (eintrag, geheimnis) zurück: bei Claude Desktop den Einmal-Code, sonst den Schlüssel."""
        name = " ".join(str(name or "").split())[:30]          # im Protokoll „MCP <name>“ (höchstens 40 Zeichen)
        if not re.fullmatch(r"[\w.@ -]{1,30}", name) or art not in ARTEN or recht not in RECHTE:
            raise Fehler("ki_name")
        with self.sperre:
            if len(self.liste_) >= MAX:
                raise Fehler("ki_max")
            if any(x["name"].lower() == name.lower() for x in self.liste_):
                raise Fehler("ki_doppelt")
            geheim = "sc_" + secrets.token_urlsafe(32)
            x = {"id": secrets.token_hex(4), "name": name, "art": art, "recht": recht, "erstellt": time.strftime("%Y-%m-%d %H:%M")}
            if art == "desktop":
                x.update(code=_hash(geheim), code_bis=time.time() + EINLOESEN_S)
            else:
                x["token"] = _hash(geheim)
            self.liste_.append(x)
            self._speichern()
        return dict(x), geheim

    def einloesen(self, code, ip=""):
        """Einmal-Code gegen einen Schlüssel tauschen. Gibt (eintrag, schluessel) oder (None, None)."""
        h = _hash(str(code or ""))
        with self.sperre:
            x = next((x for x in self.liste_ if x.get("code") and secrets.compare_digest(x["code"], h)), None)
            if not x or x.get("code_bis", 0) < time.time():
                return None, None
            schluessel = "sc_" + secrets.token_urlsafe(32)
            x.pop("code", None); x.pop("code_bis", None)
            x.update(token=_hash(schluessel), zuletzt=time.strftime("%Y-%m-%d %H:%M"), ip=str(ip)[:45])
            self._speichern()
        return dict(x), schluessel

    def pruefen(self, schluessel, ip=""):
        """Eintrag zum Schlüssel oder None. Merkt „zuletzt benutzt“."""
        if not schluessel or not schluessel.startswith("sc_"):
            return None
        h = _hash(schluessel)
        with self.sperre:
            x = next((x for x in self.liste_ if x.get("token") and secrets.compare_digest(x["token"], h)), None)
            if x:
                x["zuletzt"], x["ip"] = time.strftime("%Y-%m-%d %H:%M"), str(ip)[:45]
                if time.time() - self.geschrieben > ZULETZT_SPEICHERN_S:
                    self._speichern()
            return dict(x) if x else None

    def entfernen(self, zid):
        with self.sperre:
            x = next((x for x in self.liste_ if x["id"] == zid), None)
            if x:
                self.liste_.remove(x)
                self._speichern()
            return dict(x) if x else None
