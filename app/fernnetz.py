# Player an anderem Standort (seit 0.41): Tailscale oder Headscale (selbst betrieben, gleiche Clients).
#
# Der Player fragt ohnehin selbst beim Server an (Pull, kein Port offen). Liegt er an einem anderen Standort, braucht er nur
# einen Weg zum Server: Er tritt beim ersten Start mit einem Einmal-Schlüssel dem Tailnet bei und spricht SignageCast über
# dessen Tailnet-Adresse an. Anzeige, Befehle und das Terminal (Fernwartung) laufen dadurch unverändert mit.
#
# - Einmal-Schlüssel je Gerät, vorab freigegeben, mit Tag (Standard tag:signagecast-player), gültig SCHLUESSEL_TAGE. Er steht
#   im Image und ist nach dem ersten Start verbraucht; ein neuer Download zieht den vorigen, unbenutzten zurück.
# - Gerät entfernen löscht es auch aus dem Tailnet (per API) und zieht einen unbenutzten Schlüssel zurück.
# - Die Zugangsdaten (Tailscale: OAuth-Client mit den Rechten auth_keys und devices:core; Headscale: API-Schlüssel) liegen
#   nur in fernnetz.json (Rechte 600), nie in den Einstellungen, Sicherungen oder Antworten an die Verwaltung.
# Nur Python-Standardbibliothek.
import ipaddress, json, os, re, threading, time, urllib.error, urllib.parse, urllib.request

ARTEN = ("aus", "tailscale", "headscale")
TS_API = "https://api.tailscale.com/api/v2"
SCHLUESSEL_TAGE = 7
TAG_STD = "tag:signagecast-player"
MASKE = "••••"
ZEIT = 15


class Fehler(ValueError):
    """Kennung einer Meldung (meldung.py), optional mit Text (innen)."""
    def __init__(self, code, innen=""):
        super().__init__(code)
        self.code, self.innen = code, str(innen)[:200]


def _leer():
    return {"art": "aus", "server": "", "tag": TAG_STD, "client_id": "", "client_secret": "", "url": "", "api_key": "",
            "benutzer": ""}


class Fernnetz:
    def __init__(self, pfad):
        self.pfad = pfad
        self.sperre = threading.Lock()
        self.k = _leer()
        self.token, self.token_bis = "", 0
        try:
            with open(pfad) as f:
                d = json.load(f)
            if isinstance(d, dict):
                self.k.update({x: str(d[x]) for x in self.k if isinstance(d.get(x), str)})
        except (OSError, ValueError):
            pass

    # --- Einstellungen ---
    def aktiv(self):
        return self.k["art"] != "aus" and bool(self.k["server"])

    def aussen(self):
        """Für die Verwaltung – Geheimnisse nur als ••••."""
        return dict(self.k, client_secret=MASKE if self.k["client_secret"] else "", api_key=MASKE if self.k["api_key"] else "")

    def speichern(self, d):
        neu = dict(self.k)
        art = str(d.get("art", neu["art"]))
        if art not in ARTEN:
            raise Fehler("fn_art")
        neu["art"] = art
        for x in ("server", "tag", "client_id", "url", "benutzer"):
            if x in d:
                neu[x] = str(d[x] or "").strip()
        for x in ("client_secret", "api_key"):
            if x in d and d[x] != MASKE:
                neu[x] = str(d[x] or "").strip()
        neu["tag"] = neu["tag"] or TAG_STD
        if art != "aus":
            if not _adresse_ok(neu["server"]):
                raise Fehler("fn_server")
            if not re.fullmatch(r"tag:[a-z0-9][a-z0-9-]{0,49}", neu["tag"]):
                raise Fehler("fn_tag")
            if art == "tailscale" and not (re.fullmatch(r"[\w-]{4,80}", neu["client_id"]) and len(neu["client_secret"]) >= 8):
                raise Fehler("fn_zugang")
            if art == "headscale":
                if not re.fullmatch(r"https?://[A-Za-z0-9.\-\[\]:]+(/[\w./-]*)?", neu["url"]) or len(neu["api_key"]) < 8:
                    raise Fehler("fn_zugang")
                if neu["benutzer"] and not neu["benutzer"].isdigit():
                    raise Fehler("fn_benutzer")
        for x in ("client_secret", "api_key", "client_id"):
            if len(neu[x]) > 300 or any(c in neu[x] for c in "\r\n"):
                raise Fehler("fn_zugang")
        with self.sperre:
            if (neu["client_id"], neu["client_secret"]) != (self.k["client_id"], self.k["client_secret"]):
                self.token, self.token_bis = "", 0
            self.k = neu
            tmp = self.pfad + ".tmp"
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                json.dump(neu, f)
            os.replace(tmp, self.pfad)

    # --- HTTP ---
    def _anfrage(self, methode, url, daten=None, kopf=None, form=False):
        kopf = dict(kopf or {})
        roh = None
        if daten is not None:
            roh = urllib.parse.urlencode(daten).encode() if form else json.dumps(daten).encode()
            kopf["Content-Type"] = "application/x-www-form-urlencoded" if form else "application/json"
        r = urllib.request.Request(url, data=roh, method=methode, headers=dict(kopf, Accept="application/json",
                                                                                  **{"User-Agent": "SignageCast"}))
        try:
            with urllib.request.urlopen(r, timeout=ZEIT) as a:
                text = a.read(4_000_000).decode("utf-8", "replace")
        except urllib.error.HTTPError as f:
            text = f.read(2000).decode("utf-8", "replace")
            try:
                text = json.loads(text).get("message") or text
            except (ValueError, AttributeError):
                pass
            raise Fehler("fn_api", f"{f.code} {text}".strip()) from None
        except (OSError, ValueError) as f:
            raise Fehler("fn_nicht_erreichbar", f) from None
        try:
            return json.loads(text) if text.strip() else {}
        except ValueError:
            raise Fehler("fn_api", "keine JSON-Antwort") from None

    def _ts(self, methode, pfad, daten=None):
        with self.sperre:
            if not self.token or time.time() > self.token_bis - 60:
                a = self._anfrage("POST", TS_API + "/oauth/token", {"client_id": self.k["client_id"],
                                  "client_secret": self.k["client_secret"], "grant_type": "client_credentials"}, form=True)
                self.token, self.token_bis = a.get("access_token", ""), time.time() + int(a.get("expires_in") or 3600)
                if not self.token:
                    raise Fehler("fn_api", "kein Zugriffstoken")
            token = self.token
        return self._anfrage(methode, TS_API + pfad, daten, {"Authorization": "Bearer " + token})

    def _hs(self, methode, pfad, daten=None):
        return self._anfrage(methode, self.k["url"].rstrip("/") + "/api/v1" + pfad, daten,
                             {"Authorization": "Bearer " + self.k["api_key"]})

    # --- Geräte im Tailnet ---
    def geraete(self):
        """[(id, name, [adressen], online)]"""
        if self.k["art"] == "tailscale":
            return [(d.get("nodeId") or d.get("id"), d.get("hostname") or d.get("name", ""), d.get("addresses") or [],
                     d.get("connectedToControl")) for d in self._ts("GET", "/tailnet/-/devices").get("devices", [])]
        if self.k["art"] == "headscale":
            return [(str(n.get("id")), n.get("givenName") or n.get("name", ""), n.get("ipAddresses") or [], n.get("online"))
                    for n in self._hs("GET", "/node").get("nodes", [])]
        raise Fehler("fn_aus")

    def pruefen(self):
        """Verbindung testen: Zugang gültig, und der Server selbst ist im Tailnet."""
        liste = self.geraete()
        ziel = self.k["server"].lower()
        for gid, name, adressen, online in liste:
            if ziel in [a.lower() for a in adressen]:
                return {"geraete": len(liste), "server_name": name, "server_online": online}
        raise Fehler("fn_server_fehlt", self.k["server"])

    def schluessel(self, beschreibung):
        """Einmal-Schlüssel für ein Gerät: (schluessel, kennung)."""
        if not self.aktiv():
            raise Fehler("fn_aus")
        text = re.sub(r"[^A-Za-z0-9 -]+", "-", beschreibung)[:50].strip(" -") or "SignageCast"
        if self.k["art"] == "tailscale":
            a = self._ts("POST", "/tailnet/-/keys", {"capabilities": {"devices": {"create": {
                "reusable": False, "ephemeral": False, "preauthorized": True, "tags": [self.k["tag"]]}}},
                "expirySeconds": SCHLUESSEL_TAGE * 86400, "description": text})
            return a.get("key", ""), str(a.get("id", ""))
        bis = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + SCHLUESSEL_TAGE * 86400))
        d = {"reusable": False, "ephemeral": False, "expiration": bis, "aclTags": [self.k["tag"]]}
        if self.k["benutzer"]:
            d["user"] = self.k["benutzer"]
        a = self._hs("POST", "/preauthkey", d).get("preAuthKey") or {}
        return a.get("key", ""), str(a.get("id", ""))

    def schluessel_zurueck(self, kennung):
        if not kennung or not self.aktiv():
            return
        if self.k["art"] == "tailscale":
            self._ts("DELETE", "/tailnet/-/keys/" + urllib.parse.quote(kennung, safe=""))
        else:
            self._hs("POST", "/preauthkey/expire", {"id": kennung})

    def entfernen(self, adresse):
        """Gerät mit dieser Tailnet-Adresse löschen. Gibt seinen Namen zurück oder None (nicht gefunden)."""
        if not adresse or not self.aktiv():
            return None
        for gid, name, adressen, _ in self.geraete():
            if adresse in adressen:
                if self.k["art"] == "tailscale":
                    self._ts("DELETE", "/device/" + urllib.parse.quote(gid, safe=""))
                else:
                    self._hs("DELETE", "/node/" + urllib.parse.quote(gid, safe=""))
                return name
        return None

    def regel(self, port, stream_port):
        """Vorschlag für die Zugriffsregel (ACL): Player dürfen nur SignageCast erreichen."""
        ziel = self.k["server"] or "<server>"
        return {"tagOwners": {self.k["tag"]: ["autogroup:admin"], "tag:signagecast-server": ["autogroup:admin"]},
                "acls": [{"action": "accept", "src": [self.k["tag"]], "dst": [f"{ziel}:{port},{stream_port}"]}]}


def _adresse_ok(a):
    """Tailnet-IPv4 (100.64.0.0/10) – der Player nimmt kein MagicDNS (--accept-dns=false), Namen gehen dort nicht."""
    try:
        return ipaddress.IPv4Address(a) in ipaddress.ip_network("100.64.0.0/10")
    except ValueError:
        return False
