# Benachrichtigungen (seit 0.16): Ereignisse (Fernseher-Ausfall, Update-/Sicherungsfehler, Home Assistant getrennt)
# über Telegram, E-Mail (SMTP) und Home Assistant melden. Jedes Ereignis nur einmal, Entwarnung wenn es vorbei ist.
import json, smtplib, ssl, threading, time, urllib.error, urllib.request
from email.message import EmailMessage

GEHEIM = (("telegram", "token"), ("email", "passwort"))

# Betreff und Text je Ereignis in der Sprache der Verwaltung (seit 0.19.3; vorher nur Deutsch)
TEXTE = {
    "de": {
        "ausfall": ("SignageCast: Ausfall „{tv}“", "Die Wiedergabe für den Fernseher „{tv}“ ist ausgefallen (Render-Kette unvollständig)."),
        "ausfall_vorbei": ("SignageCast: „{tv}“ läuft wieder", "Die Wiedergabe für den Fernseher „{tv}“ läuft wieder."),
        "update": ("SignageCast: Update fehlgeschlagen", "{aktion}: {meldung} ({zeit})"),
        "sicherung": ("SignageCast: Sicherung fehlgeschlagen", "Die automatische Sicherung um {zeit} ist fehlgeschlagen: {fehler}"),
        "doppelt": ("SignageCast: „{tv}“ ruckelt", "Die Aufnahme für „{tv}“ verdoppelt seit 3 Minuten viele Bilder. "
                    "Abhilfe: System → Leistungstest → „Ton und Stream neu starten“."),
        "doppelt_vorbei": ("SignageCast: „{tv}“ läuft wieder flüssig", "Die Aufnahme für „{tv}“ läuft wieder ohne doppelte Bilder."),
        "leistung": ("SignageCast: „{tv}“ ruckelt", "Die TV-Seite für „{tv}“ erreicht seit 5 Minuten nur {fps} Bilder/s (Ziel 25). "
                     "Leistungstest in der Verwaltung: System → Leistungstest."),
        "leistung_vorbei": ("SignageCast: „{tv}“ läuft wieder flüssig", "Die TV-Seite für „{tv}“ erreicht wieder genug Bilder/s."),
        "ha": ("SignageCast: Home Assistant nicht erreichbar", "Seit {seit}: {grund}"),
        "ha_vorbei": ("SignageCast: Home Assistant wieder verbunden", "Die Verbindung zu Home Assistant steht wieder."),
        "test": ("SignageCast: Test", "Testnachricht von SignageCast {version} ({host})."),
        "player_aus": ("SignageCast: Player „{name}“ meldet sich nicht", "Der Raspberry-Pi-Player „{name}“ hat sich seit 5 Minuten "
                       "nicht gemeldet (Strom, Netz oder WLAN?)."),
        "player_wieder": ("SignageCast: Player „{name}“ wieder da", "Der Raspberry-Pi-Player „{name}“ meldet sich wieder."),
        "internet": ("SignageCast: Internet nicht erreichbar", "Seit {seit} ist das Internet nicht erreichbar. Die Fernseher zeigen "
                     "eigene Medien bzw. ein Ersatzbild statt der Live-Kameras."),
        "internet_vorbei": ("SignageCast: Internet wieder erreichbar", "Das Internet war von {seit} bis {bis} nicht erreichbar. "
                            "Die Live-Kameras laufen wieder."),
        "bild_schwarz": ("SignageCast: „{tv}“ zeigt nur Schwarz", "Der Fernseher „{tv}“ zeigt seit einigen Minuten ein schwarzes Bild, "
                         "obwohl die Wiedergabe läuft. Neu laden und Neustart haben nicht geholfen – bitte in der Verwaltung prüfen."),
        "bild_steht": ("SignageCast: Bild von „{tv}“ steht", "Das Bild von „{tv}“ ändert sich seit einigen Minuten nicht, obwohl die Uhr "
                       "laufen müsste. Neu laden und Neustart haben nicht geholfen – bitte in der Verwaltung prüfen."),
        "bild_vorbei": ("SignageCast: „{tv}“ zeigt wieder ein Bild", "Der Fernseher „{tv}“ zeigt wieder ein normales Bild."),
        "speicher_gelb": ("SignageCast: Speicher wird knapp", "Nur noch {frei} GB frei (Reserve {reserve} GB). Uploads gehen noch – "
                          "bitte unter System → Speicher aufräumen (Galerie, Medien, Sicherungen)."),
        "speicher_rot": ("SignageCast: Speicher voll – Uploads gesperrt", "Nur noch {frei} GB frei, die Reserve von {reserve} GB ist "
                         "erreicht. Alles läuft weiter, aber Uploads sind gesperrt, bis unter System → Speicher Platz frei ist."),
        "speicher_vorbei": ("SignageCast: Speicher wieder in Ordnung", "Wieder {frei} GB frei."),
    },
    "en": {
        "ausfall": ("SignageCast: “{tv}” failed", "Playback for the TV “{tv}” has failed (render chain incomplete)."),
        "ausfall_vorbei": ("SignageCast: “{tv}” is running again", "Playback for the TV “{tv}” is running again."),
        "update": ("SignageCast: update failed", "{aktion}: {meldung} ({zeit})"),
        "sicherung": ("SignageCast: backup failed", "The automatic backup at {zeit} failed: {fehler}"),
        "doppelt": ("SignageCast: “{tv}” is stuttering", "The capture for “{tv}” has been duplicating many frames for 3 minutes. "
                    "Remedy: System → Performance test → “Restart sound and stream”."),
        "doppelt_vorbei": ("SignageCast: “{tv}” is smooth again", "The capture for “{tv}” runs without duplicate frames again."),
        "leistung": ("SignageCast: “{tv}” is stuttering", "The TV page for “{tv}” has only reached {fps} frames/s for 5 minutes (target 25). "
                     "Performance test in the admin: System → Performance test."),
        "leistung_vorbei": ("SignageCast: “{tv}” is smooth again", "The TV page for “{tv}” reaches enough frames/s again."),
        "ha": ("SignageCast: Home Assistant not reachable", "Since {seit}: {grund}"),
        "ha_vorbei": ("SignageCast: Home Assistant connected again", "The connection to Home Assistant is back."),
        "test": ("SignageCast: test", "Test message from SignageCast {version} ({host})."),
        "player_aus": ("SignageCast: player “{name}” not responding", "The Raspberry Pi player “{name}” has not reported for "
                       "5 minutes (power, network or Wi-Fi?)."),
        "player_wieder": ("SignageCast: player “{name}” is back", "The Raspberry Pi player “{name}” reports again."),
        "internet": ("SignageCast: internet not reachable", "The internet has not been reachable since {seit}. The TVs show own media "
                     "or a fallback picture instead of the live cams."),
        "internet_vorbei": ("SignageCast: internet reachable again", "The internet was not reachable from {seit} to {bis}. "
                            "The live cams are running again."),
        "bild_schwarz": ("SignageCast: “{tv}” shows only black", "The TV “{tv}” has shown a black picture for several minutes although "
                         "playback is running. Reloading and restarting did not help – please check the admin."),
        "bild_steht": ("SignageCast: picture of “{tv}” is frozen", "The picture of “{tv}” has not changed for several minutes although "
                       "the clock should run. Reloading and restarting did not help – please check the admin."),
        "bild_vorbei": ("SignageCast: “{tv}” shows a picture again", "The TV “{tv}” shows a normal picture again."),
        "speicher_gelb": ("SignageCast: storage is getting low", "Only {frei} GB free (reserve {reserve} GB). Uploads still work – "
                          "please clean up under System → Storage (gallery, media, backups)."),
        "speicher_rot": ("SignageCast: storage full – uploads blocked", "Only {frei} GB free, the reserve of {reserve} GB is reached. "
                         "Everything keeps running, but uploads are blocked until space is freed under System → Storage."),
        "speicher_vorbei": ("SignageCast: storage OK again", "{frei} GB free again."),
    },
}
# Gründe aus ha.py (HAFehler.code) – auf Deutsch steht der Text von ha.py
HA_GRUND_EN = {"nicht_erreichbar": "HA not reachable", "kein_trusted": "HA offers no login via trusted networks for this address",
               "kein_benutzer": "trusted_networks: no user assigned to this IP", "abgelehnt": "login rejected",
               "http": "HA answered with an error"}


def texte(sprache, kennung, **p):
    """(betreff, text) für ein Ereignis; unbekannte Sprache -> Englisch."""
    betreff, text = TEXTE.get(sprache, TEXTE["en"])[kennung]
    return betreff.format(**p), text.format(**p)


def telegram(k, betreff, text):
    roh = json.dumps({"chat_id": k["chat_id"], "text": f"{betreff}\n{text}", "disable_web_page_preview": True}).encode()
    r = urllib.request.Request(f"https://api.telegram.org/bot{k['token']}/sendMessage", data=roh,
                               headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=20) as a:
            json.load(a)
    except urllib.error.HTTPError as f:            # Text von Telegram statt URL (die den Token enthält)
        try:
            raise RuntimeError(json.load(f).get("description") or f"HTTP {f.code}") from None
        except ValueError:
            raise RuntimeError(f"HTTP {f.code}") from None
    except urllib.error.URLError as f:
        raise RuntimeError(f"Telegram nicht erreichbar: {f.reason}") from None


def email(k, betreff, text):
    m = EmailMessage()
    m["Subject"], m["From"], m["To"] = betreff, k["absender"] or k["benutzer"], k["empfaenger"]
    m.set_content(text)
    kontext = ssl.create_default_context()
    if k["sicherheit"] == "ssl":
        s = smtplib.SMTP_SSL(k["server"], k["port"], timeout=30, context=kontext)
    else:
        s = smtplib.SMTP(k["server"], k["port"], timeout=30)
    with s:
        if k["sicherheit"] == "starttls":
            s.starttls(context=kontext)
        if k["benutzer"]:
            s.login(k["benutzer"], k["passwort"])
        s.send_message(m)


def senden(b, ha_post, betreff, text, nur=None):
    """An alle aktiven Kanäle (oder nur einen) senden -> {kanal: None | Fehlertext}."""
    ergebnis = {}
    for kanal in ("telegram", "email", "ha"):
        k = b[kanal]
        if nur and kanal != nur or not nur and not k["aktiv"]:
            continue
        try:
            if kanal == "telegram":
                telegram(k, betreff, text)
            elif kanal == "email":
                email(k, betreff, text)
            else:
                ha_post("/api/services/notify/" + k["dienst"].split(".", 1)[1], {"title": betreff, "message": text})
            ergebnis[kanal] = None
        except Exception as f:
            ergebnis[kanal] = str(f)[:300] or type(f).__name__
    return ergebnis


class Melder:
    """melden(schluessel, art, kennung, **werte) / vorbei(schluessel, kennung, **werte): jedes Ereignis nur einmal senden.
    Betreff und Text kommen aus TEXTE in der Sprache der Einstellungen."""

    def __init__(self, einst, ha_post):
        self.einst, self.ha_post = einst, ha_post
        self.offen = {}                             # schluessel -> Zeitpunkt der Meldung
        self.letzte = []                            # [{zeit, betreff, ergebnis}] für die Verwaltung

    def _los(self, betreff, text):
        def senden_():
            e = senden(self.einst()["benachrichtigung"], self.ha_post, betreff, text)
            self.letzte = ([{"zeit": time.strftime("%Y-%m-%d %H:%M"), "betreff": betreff, "ergebnis": e}] + self.letzte)[:10]
        threading.Thread(target=senden_, daemon=True).start()

    def sprache(self):
        return self.einst()["sprache"] or "en"

    def melden(self, schluessel, art, kennung, **p):
        if schluessel in self.offen or not self.einst()["benachrichtigung"]["ereignisse"].get(art):
            return
        self.offen[schluessel] = time.time()
        self._los(*texte(self.sprache(), kennung, **p))

    def vorbei(self, schluessel, kennung, **p):
        if self.offen.pop(schluessel, None) is not None:
            self._los(*texte(self.sprache(), kennung, **p))
