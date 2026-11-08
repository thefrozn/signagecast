# „Zu erledigen“ in der Übersicht (seit 0.35): Einträge ausblenden, ohne sie zu erledigen.
#
# Je nach Art bleibt ein ausgeblendeter Eintrag unterschiedlich lange weg:
#   tipp     dauerhaft, bis man ihn wieder einblendet (z. B. „Automatische Sicherung ist ausgeschaltet“)
#   update   nur für diese Version – die Kennung enthält die Versionsnummer, die nächste erscheint wieder
#   warn     bis das Problem einmal weg war: Fehlt die Warnung bei zwei Prüfungen hintereinander (je 60 s), wird
#            die Ausblendung gelöscht – tritt das Problem später wieder auf, erscheint es wieder
# „Startpasswort ändern“ (Container) lässt sich nicht ausblenden – Sicherheitslücke, kein Tipp.
# Gespeichert in /var/lib/signagecast/todo.json (eigene Datei: die Prüfschleife schreibt, ohne die Einstellungen
# anzufassen) und in Sicherungen enthalten.
import json, os, re, threading, time

TIPPS = ("sicherung", "benachrichtigung", "software")
WARN = re.compile(r"(ha|allgemein|wetter|sicherung_fehler|bn_fehler|(bildrate|doppelt):[a-z][a-z0-9]{0,11}|player:[0-9a-f]{8})")
UPDATE = re.compile(r"update:v?\d{1,3}\.\d{1,3}\.\d{1,3}")
MAX = 100

sperre = threading.Lock()


def art(schluessel):
    """tipp | update | warn – oder None (unbekannt bzw. nicht ausblendbar, z. B. „passwort“)."""
    if not isinstance(schluessel, str) or len(schluessel) > 40:
        return None
    if schluessel in TIPPS:
        return "tipp"
    if UPDATE.fullmatch(schluessel):
        return "update"
    if WARN.fullmatch(schluessel):
        return "warn"
    return None


class Liste:
    def __init__(self, pfad):
        self.pfad, self.fehlt = pfad, {}      # fehlt: Kennung -> Anzahl Prüfungen ohne die Warnung (nur im Speicher)
        self.aus = self._laden()

    def _laden(self):
        try:
            d = json.load(open(self.pfad))
            return {k: v for k, v in (d.get("aus") or {}).items() if art(k) and isinstance(v, dict)}
        except (OSError, ValueError, AttributeError):
            return {}

    def _speichern(self):
        tmp = self.pfad + ".neu"
        with open(tmp, "w") as f:
            json.dump({"aus": self.aus}, f, indent=1)
        os.replace(tmp, self.pfad)

    def liste(self):
        with sperre:
            return sorted(self.aus)

    def ausblenden(self, schluessel):
        a = art(schluessel)
        if not a:
            return False
        with sperre:
            if schluessel not in self.aus and len(self.aus) >= MAX:
                return False
            self.aus[schluessel] = {"art": a, "zeit": int(time.time())}
            self.fehlt.pop(schluessel, None)
            self._speichern()
        return True

    def einblenden(self, schluessel):
        with sperre:
            if self.aus.pop(schluessel, None) is None:
                return False
            self._speichern()
        return True

    def pruefen(self, aktive_warnungen, neue_version):
        """Alle 60 s: Warnungen, die zweimal hintereinander fehlten, und Updates alter Versionen wieder freigeben."""
        weg = []
        with sperre:
            for k, v in list(self.aus.items()):
                if v.get("art") == "warn":
                    if k in aktive_warnungen:
                        self.fehlt.pop(k, None)
                    else:
                        self.fehlt[k] = self.fehlt.get(k, 0) + 1
                        if self.fehlt[k] >= 2:
                            weg.append(k)
                elif v.get("art") == "update" and k != f"update:{neue_version}":
                    weg.append(k)
            for k in weg:
                self.aus.pop(k, None)
                self.fehlt.pop(k, None)
            if weg:
                self._speichern()
        return weg

    def als_bytes(self):
        with sperre:
            return json.dumps({"aus": self.aus}).encode()

    def einspielen(self, roh):
        try:
            d = json.loads(roh)
        except ValueError:
            return
        with sperre:
            self.aus = {k: v for k, v in (d.get("aus") or {}).items() if art(k) and isinstance(v, dict)} if isinstance(d, dict) else {}
            self.fehlt = {}
            self._speichern()
