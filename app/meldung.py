# Meldungen mit Kennung: Fehler aus Datenquellen, Kameras, Wetter, Zeit und Einspielern tragen eine Kennung (code) und
# ihre Werte (p). Der deutsche Text hier dient für Protokoll und deutsche Verwaltung; die Verwaltung übersetzt anhand der
# Kennung (cockpit/signagecast/tv.js, T.meldung) in andere Sprachen.

DE = {
    # Datenquellen: Prüfen der Einstellungen
    "q_kennung": "Datenquelle: ungültige oder doppelte Kennung {id} (2–16 Zeichen a–z, 0–9, _)",
    "q_art": "Datenquelle: Art json, text, rss, bild, ical oder video",
    "q_adresse_video": "Datenquelle {id}: Kamera-Adresse mit rtsp://, rtsps://, http:// oder https://",
    "q_adresse": "Datenquelle {id}: Adresse muss mit http:// oder https:// beginnen",
    "q_kopfname": "Datenquelle {id}: ungültiger Kopfzeilen-Name {name}",
    "q_kopfwert": "Datenquelle {id}: ungültiger Wert für {name}",
    "q_intervall": "Datenquelle: Intervall in Sekunden",
    # curl-Befehl
    "curl_lesbar": "curl-Befehl nicht lesbar: {d}",
    "curl_wert": "curl: Wert fehlt nach {opt}",
    "curl_adresse": "curl: keine Adresse gefunden",
    # Abruf
    "nur_http": "nur http/https",
    "http": "HTTP {code} {grund}",
    "nicht_erreichbar": "nicht erreichbar: {d}",
    "zu_gross": "Antwort größer als {mb} MB",
    "kein_bild": "kein Bild (Content-Type {typ})",
    "kein_json": "kein gültiges JSON: {d}",
    "kein_feed": "kein gültiger Feed: {d}",
    # Kameras
    "kam_http": "Kamera: HTTP {code} {grund}",
    "kam_nicht_erreichbar": "Kamera nicht erreichbar: {d}",
    "kein_mjpeg": "kein MJPEG (Content-Type {typ})",
    "kam_zeit": "Kamera antwortet nicht (25 s)",
    "kam_fehler": "Kamera: {d}",
    # Wetter, Zeit
    "met_http": "MET Norway antwortet {code}",
    "met_nicht_erreichbar": "MET Norway nicht erreichbar: {d}",
    "ntp_stumm": "{server} antwortet nicht",
    "ntp_ungueltig": "ungültige NTP-Antwort",
    # Einspieler
    "kein_youtube": "kein YouTube-Link",
    "kein_video_kanal": "kein Video im Kanal gefunden",
    "ep_kein_range": "Server kann keine Teile liefern (kein Range) – bitte „komplett“ wählen",
    "ep_zu_gross": "Einspieler größer als 500 MB",
    "ep_keine_groesse": "Server nennt keine Gesamtgröße – nur „komplett“ möglich",
    "ep_nicht_bereit": "Einspieler noch nicht bereit – in ein paar Sekunden erneut versuchen",
    # Sicherung
    "sich_pw_kurz": "Passwort zu kurz – mindestens 12 Zeichen",
    "sich_pw_schwach": "Passwort zu schwach – Groß- und Kleinbuchstaben, Ziffern und Sonderzeichen mischen (oder eine Passphrase ab 20 Zeichen)",
    "sich_pw_fehlt": "Die Sicherung ist verschlüsselt – bitte das Passwort angeben",
    "sich_pw_falsch": "Falsches Passwort für die Sicherung",
    "sich_ungueltig": "Keine SignageCast-Sicherung",
    "sich_zu_gross": "Sicherung zu groß",
    "sich_kein_aes": "Verschlüsselung nicht verfügbar (Paket python3-pyzipper fehlt)",
    "sich_geheim_ohne_pw": "Mit Zugangsdaten und Passwörtern nur mit Passwort (AES-256)",
    "sich_name": "Unbekannte Sicherung",
}


class Meldung(ValueError):
    def __init__(self, kennung, **p):              # „kennung“, weil Werte selbst „code“ heißen können (HTTP-Status)
        self.code, self.p = kennung, {k: str(v)[:200] for k, v in p.items()}
        super().__init__(DE.get(kennung, kennung).format(**self.p))


def als_dict(ex):
    """Für die Verwaltung: {"code", "p", "text"} – bei fremden Fehlern nur der Text."""
    if isinstance(ex, Meldung):
        return {"code": ex.code, "p": ex.p, "text": str(ex)}
    return {"code": "", "p": {}, "text": str(ex)[:300]}
