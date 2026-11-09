# Internet erreichbar? (seit 0.38) – damit die TV-Seite bei einem Ausfall ein Ersatzbild bzw. eigene Medien zeigt statt
# Schwarz oder einer Fehlermeldung, und gute Streams in der Zeit keine Strikes bekommen.
#
# Prüfung: TCP-Verbindung (mit Namensauflösung) zum YouTube-Einbettungsplayer, Port 443 – kein HTTP, keine Daten.
# Takt 60 s; schlägt sie fehl, nach 10 s noch einmal: erst zwei Fehlschläge in Folge gelten als „offline“ (kein
# Flackern bei einem verlorenen Paket). Offline wird alle 20 s geprüft, ein Erfolg genügt für „wieder online“.
# Geprüft wird nur, solange es Bedarf gibt (ein Fernseher zeigt Live-Videos) – sonst keine Verbindung nach außen.
import socket, threading, time

ZIELE = (("www.youtube-nocookie.com", 443), ("www.youtube.com", 443))
TAKT_S, NOCHMAL_S, OFFLINE_TAKT_S, TIMEOUT_S = 60, 10, 20, 5


def erreichbar(timeout=TIMEOUT_S, ziele=ZIELE):
    """True, wenn eines der Ziele eine TCP-Verbindung annimmt."""
    for host, port in ziele:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


class Wache:
    def __init__(self, pruefen=erreichbar, bedarf=lambda: True):
        self.pruefen, self.bedarf = pruefen, bedarf
        self.offline_seit = None              # Zeitpunkt (time.time()) oder None
        self.letzte = None                    # Zeitpunkt der letzten Prüfung
        self.neu = threading.Event()          # sofort prüfen (z. B. nach einer Strike-Meldung)
        self.sperre = threading.Lock()

    @property
    def offline(self):
        return self.offline_seit is not None

    def einmal(self):
        """Eine Prüfrunde (mit Wiederholung). Gibt den neuen Zustand zurück (True = online)."""
        ok = self.pruefen()
        if not ok and not self.offline:
            time.sleep(NOCHMAL_S)
            ok = self.pruefen()
        with self.sperre:
            self.letzte = time.time()
            if ok:
                if self.offline:
                    print("Internet wieder erreichbar", flush=True)
                self.offline_seit = None
            elif not self.offline:
                self.offline_seit = time.time()
                print("Internet nicht erreichbar", flush=True)
        return ok

    def jetzt_online(self):
        """Für Strike-Meldungen: kurze Prüfung im Moment (höchstens 3 s je Ziel). Offline -> False ohne Prüfung."""
        if self.offline:
            return False
        return self.pruefen(timeout=3)

    def schleife(self):
        while True:
            try:
                if self.bedarf():
                    self.einmal()
                elif self.offline_seit is not None:
                    with self.sperre:
                        self.offline_seit = None
            except Exception as f:            # nie die Schleife verlieren
                print("Netzprüfung:", repr(f), flush=True)
            self.neu.wait(OFFLINE_TAKT_S if self.offline else TAKT_S)
            self.neu.clear()

    def stand(self):
        return {"offline": self.offline, "seit": int(self.offline_seit) if self.offline_seit else None}
