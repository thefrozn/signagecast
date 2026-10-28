# Verbindung zu Home Assistant. Anmeldung über "vertrauenswürdige Netzwerke" (trusted_networks): kein Passwort und kein
# gespeicherter Token – HA erkennt den Container an seiner IP und meldet ihn als zugeordneten Benutzer an.
# Zugangs- und Erneuerungs-Token liegen nur im Speicher.
import json, threading, time, urllib.error, urllib.parse, urllib.request

CLIENT = "http://127.0.0.1:8080/"


class HAFehler(Exception):
    pass


class HA:
    def __init__(self, url_holen):
        self.url_holen = url_holen          # Funktion -> aktuelle HA-Adresse (aus den Einstellungen)
        self.token = self.refresh = None
        self.ablauf = 0
        self.url = None
        self.sperre = threading.Lock()

    def _anfrage(self, pfad, daten=None, form=False, token=None, timeout=15):
        kopf, body = {}, None
        if daten is not None:
            body = urllib.parse.urlencode(daten).encode() if form else json.dumps(daten).encode()
            kopf["Content-Type"] = "application/x-www-form-urlencoded" if form else "application/json"
        if token:
            kopf["Authorization"] = "Bearer " + token
        req = urllib.request.Request(self.url_holen() + pfad, data=body, headers=kopf)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)

    def _anmelden(self):
        if self.refresh:
            try:
                t = self._anfrage("/auth/token", {"grant_type": "refresh_token", "refresh_token": self.refresh,
                                                  "client_id": CLIENT}, form=True)
                self.token, self.ablauf = t["access_token"], time.time() + t["expires_in"] - 120
                return
            except Exception:
                self.refresh = None
        try:
            anbieter = self._anfrage("/auth/providers")
        except Exception as e:
            raise HAFehler(f"HA nicht erreichbar: {e}")
        if not any(a.get("type") == "trusted_networks" for a in (anbieter.get("providers", anbieter) if isinstance(anbieter, dict) else anbieter)):
            raise HAFehler("HA bietet dieser Adresse keine Anmeldung über vertrauenswürdige Netzwerke an "
                           "(trusted_networks fehlt oder die IP des Containers ist nicht eingetragen)")
        f = self._anfrage("/auth/login_flow", {"client_id": CLIENT, "handler": ["trusted_networks", None],
                                               "redirect_uri": CLIENT})
        if f.get("type") == "form":          # mehrere Benutzer für diese IP: den ersten nehmen
            schema = {x["name"]: x for x in f.get("data_schema", [])}
            opt = schema.get("user", {}).get("options") or []
            wahl = list(opt.keys()) if isinstance(opt, dict) else [o[0] for o in opt]
            if not wahl:
                raise HAFehler("Anmeldung über vertrauenswürdige Netzwerke: kein Benutzer für diese IP zugeordnet")
            f = self._anfrage(f"/auth/login_flow/{f['flow_id']}", {"client_id": CLIENT, "user": wahl[0]})
        if f.get("type") != "create_entry":
            raise HAFehler(f"Anmeldung abgelehnt: {f.get('errors') or f.get('reason') or f.get('type')}")
        t = self._anfrage("/auth/token", {"grant_type": "authorization_code", "code": f["result"], "client_id": CLIENT}, form=True)
        self.token, self.refresh = t["access_token"], t.get("refresh_token")
        self.ablauf = time.time() + t["expires_in"] - 120

    def _gueltiger_token(self):
        with self.sperre:
            if self.url != self.url_holen():          # Adresse geändert -> neu anmelden
                self.token = self.refresh = None
                self.url = self.url_holen()
            if not self.token or time.time() > self.ablauf:
                self._anmelden()
            return self.token

    def get(self, pfad):
        try:
            return self._anfrage(pfad, token=self._gueltiger_token())
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.token = None
            raise HAFehler(f"HA antwortet {e.code} auf {pfad}")

    def post(self, pfad, daten):
        try:
            return self._anfrage(pfad, daten, token=self._gueltiger_token())
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.token = None
            raise HAFehler(f"HA antwortet {e.code} auf {pfad}")

    def testen(self):
        """Für die Verwaltung: Erreichbarkeit, Anmeldung, Version, Standort."""
        try:
            self.token = self.refresh = None
            k = self.get("/api/config")
            return {"ok": True, "version": k.get("version"), "ort": k.get("location_name"),
                    "breite": k.get("latitude"), "laenge": k.get("longitude"), "zeitzone": k.get("time_zone")}
        except HAFehler as e:
            return {"ok": False, "fehler": str(e)}
        except Exception as e:
            return {"ok": False, "fehler": f"HA nicht erreichbar: {e}"}
