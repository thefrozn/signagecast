#!/usr/bin/env python3
"""Statische Live-Demo für GitHub Pages bauen (seit 0.64): python3 werkzeug/demo_bauen.py <zielordner>

Erzeugt aus dem aktuellen Code einen Ordner, der ohne Server läuft:
  index.html, demo.css, demo.js     Hülle mit Hinweisbalken und Umschaltern (Vorlage, Tageszeit, Sprache)
  tv/                               die echte TV-Seite (www/) – nur index.html bekommt demo-netz.js vorangestellt
  tv/demo-daten.json                Layouts aus layouts.vorlagen() (Praxis, Imbiss, Hotel) und demo/wohnzimmer.json,
                                    fertige Bausteinwerte aus quellen.baustein_werte() mit demo/beispiel.json
Die echte TV-Seite bleibt unverändert: demo-netz.js ersetzt in der Kopie nur fetch() für /daten.json,
/durchsage.json und /meldung/… durch Antworten aus demo-daten.json (Uhrzeit und Sonnenstand rechnet es im Browser)
und lehnt jede Anfrage an fremde Server ab. Keine Cookies, kein Tracking, keine fremden Schriften oder Skripte.
"""
import html, json, os, re, shutil, sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WURZEL, "app"))
import layouts as L    # noqa: E402
import quellen as Q    # noqa: E402

VORLAGEN = ("wohnzimmer", "praxis", "imbiss", "hotel")      # Reihenfolge im Umschalter; wohnzimmer aus demo/
SPRACHEN = ("de", "en")
# aus www/ nicht in die Demo: Durchsage-Pult, Leistungstest, Designer-Vorschau, HLS-Spieler (nur für Kameras)
WEGLASSEN = {"pult.html", "leistungstest.html", "vorschau.html", "hls"}
CSP = ("default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; style-src 'self' 'unsafe-inline'; "
       "script-src 'self'; connect-src 'self'; font-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'; form-action 'none'")


class Beispielquellen:
    """Ersatz für den Datenquellen-Zustand: daten(id) liefert den Wert aus demo/beispiel.json."""
    def __init__(self, werte):
        self.werte = werte

    def daten(self, qid):
        return self.werte.get(qid)


def lesen(*pfad):
    with open(os.path.join(WURZEL, *pfad), encoding="utf-8") as f:
        return f.read()


def daten_bauen():
    beispiel = json.loads(lesen("demo", "beispiel.json"))
    eigene = json.loads(lesen("demo", "wohnzimmer.json"))
    qz = Beispielquellen(beispiel["quellen"])
    vorlagen = {}
    for s in SPRACHEN:
        alle = {v["id"]: v for v in L.vorlagen(s)}
        for vid in VORLAGEN:
            layout = L.pruefe_layout(eigene[s]) if vid == "wohnzimmer" else alle[vid]
            api, bed = Q.baustein_werte(layout, qz, s, [], None)
            # nur die HA-Werte, die das Layout braucht (wie der Dienst)
            gebraucht = L.entitaeten([layout], "")
            werte = {k: v for k, v in beispiel["werte"].items() if k in gebraucht}
            werte.update(bed)
            vorlagen.setdefault(vid, {})[s] = {"name": layout["name"], "layout": layout, "api": api, "werte": werte}
    return {"version": lesen("VERSION").strip(), "vorlagen": vorlagen, "reihenfolge": list(VORLAGEN),
            "beispiel": {k: v for k, v in beispiel.items() if not k.startswith("_")}}


def bauen(ziel):
    if os.path.exists(ziel):
        shutil.rmtree(ziel)
    tv = os.path.join(ziel, "tv")
    shutil.copytree(os.path.join(WURZEL, "www"), tv, ignore=lambda d, n: [x for x in n if x in WEGLASSEN and d.endswith("www")])
    # index.html der Kopie: Netz-Ersatz vor allen anderen Skripten, Symbol relativ (die Seite liegt nicht im Wurzelpfad)
    seite = lesen("www", "index.html")
    if '<script src="qrcode.js">' not in seite or 'href="/favicon.svg"' not in seite:
        raise SystemExit("www/index.html hat sich geändert – demo_bauen.py anpassen")
    seite = seite.replace('href="/favicon.svg"', 'href="favicon.svg"')
    # zusätzlich zur Sperre in demo-netz.js: der Browser selbst lässt nur Abrufe vom eigenen Server zu
    seite = seite.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="' + CSP + '">', 1)
    seite = seite.replace('<script src="qrcode.js">', '<script src="demo-netz.js"></script>\n  <script src="qrcode.js">', 1)
    with open(os.path.join(tv, "index.html"), "w", encoding="utf-8") as f:
        f.write(seite)
    shutil.copy(os.path.join(WURZEL, "demo", "demo-netz.js"), tv)
    d = daten_bauen()
    with open(os.path.join(tv, "demo-daten.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    for n in ("demo.css", "demo.js"):
        shutil.copy(os.path.join(WURZEL, "demo", n), ziel)
    shutil.copy(os.path.join(WURZEL, "www", "favicon.svg"), ziel)
    huelle = lesen("demo", "index.html").replace("{VERSION}", html.escape(d["version"]))
    huelle = huelle.replace("{VORLAGEN}", "".join(
        f'<option value="{v}">{html.escape(d["vorlagen"][v]["de"]["name"])}</option>' for v in VORLAGEN))
    if re.search(r"\{[A-Z]+\}", huelle):
        raise SystemExit("Platzhalter in demo/index.html nicht ersetzt")
    with open(os.path.join(ziel, "index.html"), "w", encoding="utf-8") as f:
        f.write(huelle)
    open(os.path.join(ziel, ".nojekyll"), "w").close()       # GitHub Pages: Dateien unverändert ausliefern
    return d


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    d = bauen(sys.argv[1])
    print(f"Demo {d['version']} in {sys.argv[1]}: " + ", ".join(f"{v} ({len(d['vorlagen'][v]['de']['layout']['elemente'])} Bausteine)"
                                                         for v in d["reihenfolge"]))
