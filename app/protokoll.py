# Änderungsprotokoll und Layout-Versionen (seit 0.38).
#
# Protokoll: wer hat wann was geändert – Verwaltung (Cockpit-Benutzer bzw. „Verwaltung“ im Container), Pult-Zugänge,
# Webhook und das System selbst (z. B. automatische Updates). Es werden nur Art und Bereich der Änderung
# festgehalten, nie Werte: keine Passwörter, Schlüssel oder Texte von Durchsagen (Namen von Patienten u. Ä.).
# Höchstens MAX Einträge (älteste fallen weg), Datei /var/lib/signagecast/protokoll.json.
#
# Layout-Versionen: Vor jeder Änderung eines Layouts wird die alte Fassung aufgehoben (je Layout höchstens
# VERSIONEN_MAX), auch beim Löschen – so lässt sich ein gelöschtes Layout zurückholen (höchstens GELOESCHT_MAX).
# Datei /var/lib/signagecast/layout-versionen.json. Beide Dateien sind Teil der Sicherung.
import copy, json, os, re, threading, time

MAX = 500
VERSIONEN_MAX = 10
GELOESCHT_MAX = 10
WER = re.compile(r"[\w.@ -]{1,40}")


def _laden(pfad, standard):
    try:
        d = json.load(open(pfad))
        return d if isinstance(d, type(standard)) else standard
    except (OSError, ValueError):
        return standard


def _schreiben(pfad, d):
    tmp = pfad + ".neu"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, pfad)


def wer_pruefen(w, rueckfall="Verwaltung"):
    w = " ".join(str(w or "").split())[:40]
    return w if w and WER.fullmatch(w) else rueckfall


class Protokoll:
    def __init__(self, pfad):
        self.pfad, self.sperre = pfad, threading.Lock()
        d = _laden(pfad, {})
        self.eintraege = [x for x in (d.get("eintraege") or []) if isinstance(x, dict)][-MAX:]

    def eintragen(self, wer, quelle, aktion, detail=""):
        """quelle: verwaltung | pult | webhook | system. aktion: Kennung (die Verwaltung übersetzt sie). detail: kurzer Text."""
        x = {"zeit": time.strftime("%Y-%m-%d %H:%M:%S"), "wer": wer_pruefen(wer, "?"), "quelle": quelle,
             "aktion": str(aktion)[:60], "detail": " ".join(str(detail or "").split())[:200]}
        with self.sperre:
            self.eintraege.append(x)
            del self.eintraege[:-MAX]
            try:
                _schreiben(self.pfad, {"eintraege": self.eintraege})
            except OSError as f:                 # Protokoll darf nie eine Änderung verhindern
                print("Protokoll:", f, flush=True)

    def liste(self, n=MAX):
        with self.sperre:
            return list(reversed(self.eintraege[-n:]))

    def als_bytes(self):
        with self.sperre:
            return json.dumps({"eintraege": self.eintraege}, ensure_ascii=False).encode()

    def einspielen(self, roh):
        try:
            d = json.loads(roh)
        except ValueError:
            return
        if not isinstance(d, dict):
            return
        with self.sperre:
            alt = [x for x in (d.get("eintraege") or []) if isinstance(x, dict) and isinstance(x.get("zeit"), str)]
            self.eintraege = sorted(alt + self.eintraege, key=lambda x: x["zeit"])[-MAX:]
            _schreiben(self.pfad, {"eintraege": self.eintraege})


def _gleich(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


class Versionen:
    def __init__(self, pfad):
        self.pfad, self.sperre = pfad, threading.Lock()
        d = _laden(pfad, {})
        self.layouts = {k: v for k, v in (d.get("layouts") or {}).items() if isinstance(v, list)}
        self.geloescht = {k: v for k, v in (d.get("geloescht") or {}).items() if isinstance(v, (int, float))}

    def _speichern(self):
        _schreiben(self.pfad, {"layouts": self.layouts, "geloescht": self.geloescht})

    def merken(self, alt, neu, wer):
        """alt/neu: Listen geprüfter Layouts. Geänderte und gelöschte Layouts: alte Fassung aufheben.
        Gibt (geändert, gelöscht, neu) als Namenslisten zurück – für das Protokoll."""
        neu_ids = {l["id"]: l for l in neu}
        alt_ids = {l["id"] for l in alt}
        geaendert, weg = [], []
        jetzt = int(time.time())
        with self.sperre:
            for l in alt:
                n = neu_ids.get(l["id"])
                if n is not None and _gleich(n, l):
                    continue
                v = self.layouts.setdefault(l["id"], [])
                v.insert(0, {"zeit": jetzt, "wer": wer_pruefen(wer, "?"), "layout": copy.deepcopy(l)})
                del v[VERSIONEN_MAX:]
                (geaendert if n is not None else weg).append(n["name"] if n is not None else l["name"])
                if n is None:
                    self.geloescht[l["id"]] = jetzt
            for lid in list(self.geloescht):
                if lid in neu_ids:                   # wiederhergestellt
                    self.geloescht.pop(lid)
            zu_viel = max(0, len(self.geloescht) - GELOESCHT_MAX)       # älteste gelöschte Layouts vergessen
            for lid in sorted(self.geloescht, key=self.geloescht.get)[:zu_viel]:
                self.geloescht.pop(lid)
                self.layouts.pop(lid, None)
            for lid in list(self.layouts):           # Versionen zu Layouts, die es weder gibt noch als gelöscht gibt
                if lid not in neu_ids and lid not in self.geloescht:
                    self.layouts.pop(lid)
            if geaendert or weg:
                try:
                    self._speichern()
                except OSError as f:
                    print("Layout-Versionen:", f, flush=True)
        return geaendert, weg, [l["name"] for l in neu if l["id"] not in alt_ids]

    def liste(self, lid):
        with self.sperre:
            return [{"nr": i, "zeit": v["zeit"], "wer": v.get("wer", "?"), "name": v["layout"].get("name", lid),
                     "bausteine": len(v["layout"].get("elemente") or [])} for i, v in enumerate(self.layouts.get(lid, []))]

    def holen(self, lid, nr):
        with self.sperre:
            v = self.layouts.get(lid) or []
            if not isinstance(nr, int) or not 0 <= nr < len(v):
                raise KeyError(f"{lid}/{nr}")
            return copy.deepcopy(v[nr]["layout"])

    def geloeschte(self):
        with self.sperre:
            return [{"id": lid, "zeit": z, "name": (self.layouts.get(lid) or [{"layout": {"name": lid}}])[0]["layout"].get("name", lid),
                     "versionen": len(self.layouts.get(lid) or [])}
                    for lid, z in sorted(self.geloescht.items(), key=lambda x: -x[1]) if self.layouts.get(lid)]

    def als_bytes(self):
        with self.sperre:
            return json.dumps({"layouts": self.layouts, "geloescht": self.geloescht}, ensure_ascii=False).encode()

    def einspielen(self, roh):
        try:
            d = json.loads(roh)
        except ValueError:
            return
        if not isinstance(d, dict):
            return
        with self.sperre:
            self.layouts = {k: v[:VERSIONEN_MAX] for k, v in (d.get("layouts") or {}).items()
                            if isinstance(v, list) and all(isinstance(x, dict) and isinstance(x.get("layout"), dict) for x in v)}
            self.geloescht = {k: v for k, v in (d.get("geloescht") or {}).items() if isinstance(v, (int, float))}
            self._speichern()
