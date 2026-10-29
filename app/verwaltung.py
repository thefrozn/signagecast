# SignageCast – Verwaltung ohne Cockpit (Docker/Podman). Liefert dieselbe Verwaltungsseite wie die Cockpit-Erweiterung
# aus und ersetzt die zwei Cockpit-Funktionen, die sie braucht (cockpit.http, cockpit.language), durch einen kleinen
# Ersatz (/base1/cockpit.js). Anfragen an /dienst/… reicht sie an den Datendienst (127.0.0.1:8080) weiter.
# Schutz: ein Passwort (PBKDF2), Sitzung als Cookie (HttpOnly, SameSite=Strict); jede Anfrage an den Datendienst
# braucht zusätzlich den Kopf X-SignageCast: 1 (fremde Seiten können ihn ohne CORS-Freigabe nicht setzen).
# Startpasswort: SC_PASSWORT oder zufällig – steht dann bei jedem Start im Protokoll (docker logs), bis es geändert ist.
import hashlib, hmac, json, mimetypes, os, secrets, threading, time, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import einstellungen as E

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEITE = os.environ.get("SC_VERWALTUNG_DATEIEN", os.path.join(BASIS, "cockpit", "signagecast"))
PW_DATEI = os.path.join(os.path.dirname(E.PFAD), "verwaltung.json")
DIENST = f"http://127.0.0.1:{os.environ.get('SC_PORT', '8080')}"
SITZUNG_S = 30 * 86400
sitzungen = {}                 # Kennung -> Ablaufzeit (nur im Speicher: Neustart = neu anmelden)
sperre = threading.Lock()

CSP = ("default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; font-src 'self' data:; "
       "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")

ERSATZ = """// Ersatz für die zwei Cockpit-Funktionen, die die Verwaltung nutzt (Docker/Podman-Betrieb)
"use strict";
window.cockpit = {
  language: navigator.language || "en",
  signagecastContainer: true,
  http(port, opt) {
    const binaer = !!(opt && opt.binary);
    const anfrage = async (methode, pfad, params, inhalt, kopf) => {
      const q = params && Object.keys(params).length ? (pfad.includes("?") ? "&" : "?") + new URLSearchParams(params) : "";
      const r = await fetch("/dienst" + pfad + q, { method: methode, body: inhalt, credentials: "same-origin",
        headers: Object.assign({}, kopf || {}, { "X-SignageCast": "1" }) });
      if (r.status === 401) { location.reload(); throw new Error("Bitte neu anmelden"); }
      if (!r.ok) { const e = new Error((await r.text()) || r.statusText); e.status = r.status; throw e; }
      return binaer ? new Uint8Array(await r.arrayBuffer()) : r.text();
    };
    return { get: (p, params, k) => anfrage("GET", p, params, undefined, k),
             post: (p, inhalt, k) => anfrage("POST", p, null, inhalt, k) };
  },
};
"""

ANMELDUNG = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SignageCast</title><link rel="stylesheet" href="/tv.css"></head>
<body><header><h1>SignageCast</h1></header>
<main id="inhalt"><div class="karte" style="max-width:420px;margin:40px auto">
<form method="post" action="/anmelden">
<div class="zeile"><label for="pw">Passwort / Password</label></div>
<div class="zeile"><input type="password" id="pw" name="passwort" autofocus autocomplete="current-password" required></div>
<div class="zeile"><button class="knopf haupt" type="submit">Anmelden / Log in</button></div>
{FEHLER}
<p class="leise">Startpasswort: <code>docker logs signagecast</code> (bzw. podman logs) · Initial password: see the container log.</p>
</form></div></main></body></html>
"""


def _hash(pw, salz):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salz), 200_000).hex()


def _lesen():
    try:
        return json.load(open(PW_DATEI))
    except (OSError, ValueError):
        return None


def _schreiben(d):
    tmp = PW_DATEI + ".neu"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(d, f)
    os.replace(tmp, PW_DATEI)


def passwort_setzen(pw, start=False):
    salz = secrets.token_hex(16)
    d = {"salz": salz, "hash": _hash(pw, salz)}
    if start:
        d["start"] = pw          # Startpasswort bleibt lesbar (Datei 600), damit es bei jedem Start im Protokoll steht
    _schreiben(d)


def einrichten():
    d = _lesen()
    if not d:
        pw = os.environ.get("SC_PASSWORT") or secrets.token_urlsafe(9)
        passwort_setzen(pw, start=not os.environ.get("SC_PASSWORT"))
        d = _lesen()
    if d.get("start"):
        print(f"SignageCast – Startpasswort der Verwaltung: {d['start']}  (bitte in der Verwaltung unter „Verbindung“ ändern)",
              flush=True)


def passwort_ok(pw):
    d = _lesen() or {}
    return bool(d) and hmac.compare_digest(_hash(pw, d["salz"]), d["hash"])


class Bearbeiter(BaseHTTPRequestHandler):
    server_version = "SignageCast"
    sys_version = ""

    def log_message(self, *a):
        pass

    def sitzung(self):
        for teil in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = teil.strip().partition("=")
            if k == "sc_sitzung":
                with sperre:
                    ablauf = sitzungen.get(v)
                    if ablauf and ablauf > time.time():
                        return v
        return None

    def senden(self, code, inhalt=b"", art="text/plain; charset=utf-8", kopf=None):
        if isinstance(inhalt, str):
            inhalt = inhalt.encode()
        self.send_response(code)
        self.send_header("Content-Type", art)
        self.send_header("Content-Length", str(len(inhalt)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Content-Security-Policy", CSP)
        for k, v in (kopf or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(inhalt)

    def inhalt(self, grenze=32 * 1024 * 1024):
        n = int(self.headers.get("Content-Length") or 0)
        if n > grenze:
            raise ValueError("zu groß")
        return self.rfile.read(n) if n else b""

    def datei(self, pfad):
        ziel = os.path.realpath(os.path.join(SEITE, pfad.lstrip("/")))
        if not ziel.startswith(os.path.realpath(SEITE) + os.sep) or not os.path.isfile(ziel):
            return self.senden(404, "nicht gefunden")
        art = mimetypes.guess_type(ziel)[0] or "application/octet-stream"
        if art.startswith("text/") or art in ("application/javascript", "application/json"):
            art += "; charset=utf-8"
        self.senden(200, open(ziel, "rb").read(), art)

    def weiterreichen(self):
        if not self.sitzung():
            return self.senden(401, "abgemeldet")
        if self.headers.get("X-SignageCast") != "1":
            return self.senden(403, "Kopf X-SignageCast fehlt")
        kopf = {"X-SignageCast": "1"}
        if self.headers.get("Content-Type"):
            kopf["Content-Type"] = self.headers["Content-Type"]
        grenze = 420 * 1024 * 1024 if self.path.startswith("/dienst/api/sicherung/zip") else 32 * 1024 * 1024
        anf = urllib.request.Request(DIENST + self.path[len("/dienst"):], data=self.inhalt(grenze) if self.command == "POST" else None,
                                     headers=kopf, method=self.command)
        try:
            with urllib.request.urlopen(anf, timeout=120) as r:
                self.senden(r.status, r.read(), r.headers.get("Content-Type") or "application/octet-stream")
        except urllib.error.HTTPError as e:
            self.senden(e.code, e.read(), e.headers.get("Content-Type") or "text/plain; charset=utf-8")
        except Exception as e:
            self.senden(502, f"Datendienst nicht erreichbar: {e}")

    def do_GET(self):
        pfad = urllib.parse.urlparse(self.path).path
        if pfad.startswith("/dienst/"):
            return self.weiterreichen()
        if pfad == "/base1/cockpit.js":
            return self.senden(200, ERSATZ, "application/javascript; charset=utf-8")
        if pfad == "/verwaltung/info":
            if not self.sitzung():
                return self.senden(401, "abgemeldet")
            return self.senden(200, json.dumps({"startpasswort": bool((_lesen() or {}).get("start"))}), "application/json")
        if pfad in ("/", "/index.html"):
            if not self.sitzung():
                return self.senden(200, ANMELDUNG.replace("{FEHLER}", ""), "text/html; charset=utf-8")
            return self.datei("index.html")
        self.datei(pfad)

    do_HEAD = do_GET

    def do_POST(self):
        pfad = urllib.parse.urlparse(self.path).path
        if pfad.startswith("/dienst/"):
            return self.weiterreichen()
        if pfad == "/anmelden":
            try:
                pw = urllib.parse.parse_qs(self.inhalt(4096).decode()).get("passwort", [""])[0]
            except ValueError:
                pw = ""
            if pw and passwort_ok(pw):
                kennung = secrets.token_urlsafe(32)
                with sperre:
                    jetzt = time.time()
                    for k in [k for k, a in sitzungen.items() if a < jetzt]:
                        del sitzungen[k]
                    sitzungen[kennung] = jetzt + SITZUNG_S
                return self.senden(303, "", kopf={"Location": "/", "Set-Cookie":
                                   f"sc_sitzung={kennung}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SITZUNG_S}"})
            time.sleep(1.5)          # Raten bremsen
            return self.senden(401, ANMELDUNG.replace("{FEHLER}", '<p class="schlecht">Falsches Passwort / Wrong password</p>'),
                               "text/html; charset=utf-8")
        if pfad == "/abmelden":
            k = self.sitzung()
            if k:
                with sperre:
                    sitzungen.pop(k, None)
            return self.senden(303, "", kopf={"Location": "/", "Set-Cookie": "sc_sitzung=; Path=/; Max-Age=0"})
        if pfad == "/verwaltung/passwort":
            if not self.sitzung():
                return self.senden(401, "abgemeldet")
            if self.headers.get("X-SignageCast") != "1":
                return self.senden(403, "Kopf X-SignageCast fehlt")
            try:
                d = json.loads(self.inhalt(4096) or b"{}")
            except ValueError:
                d = {}
            alt, neu = str(d.get("alt", "")), str(d.get("neu", ""))
            if not passwort_ok(alt):
                time.sleep(1.5)
                return self.senden(200, json.dumps({"ok": False, "fehler": "altes Passwort falsch"}), "application/json")
            if len(neu) < 8:
                return self.senden(200, json.dumps({"ok": False, "fehler": "mindestens 8 Zeichen"}), "application/json")
            passwort_setzen(neu)
            eigene = self.sitzung()
            with sperre:                       # andere Sitzungen abmelden, diese behalten
                for k in [k for k in sitzungen if k != eigene]:
                    del sitzungen[k]
            return self.senden(200, json.dumps({"ok": True}), "application/json")
        self.senden(404, "nicht gefunden")


def starten(port):
    einrichten()
    ThreadingHTTPServer(("0.0.0.0", port), Bearbeiter).serve_forever()
