# Meldungen mit Kennung: Fehler aus Datenquellen, Kameras, Wetter, Zeit und Einspielern tragen eine Kennung (code) und
# ihre Werte (p). Der deutsche Text hier dient für Protokoll und deutsche Verwaltung; die Verwaltung übersetzt anhand der
# Kennung (cockpit/signagecast/tv.js, T.meldung) in andere Sprachen. Eine Meldung kann eine innere enthalten
# (innen=…, z. B. „Layout X: <Grund>“) – ihr Text steht im Wert {d}, die Verwaltung übersetzt beide.

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
    # Eigene Medien
    "med_art": "Nur Bilder (JPG, PNG) und Videos (MP4, WebM)",
    "med_kaputt": "Video nicht lesbar",
    "med_hevc": "Video ist H.265 – das kann der Browser im Container nicht abspielen; bitte als H.264 (MP4) speichern",
    "med_upload": "Hochladen unterbrochen – bitte erneut versuchen",
    "med_gross": "Datei größer als 1 GB",
    "med_unbekannt": "Unbekanntes Medium",
    # Updates
    "upd_laeuft": "Es läuft bereits ein Update – bitte warten",
    "upd_aktion": "Unbekannte Update-Aktion",
    "upd_container": "Im Docker-/Podman-Betrieb wird über das Image aktualisiert (docker pull)",
    # Einstellungen prüfen (seit 0.19.3)
    "e_zahl": "keine Zahl: {w}",
    "e_bereich": "{w} liegt nicht zwischen {lo} und {hi}",
    "e_wert": "ungültiger Wert: {w}",
    "e_objekt": "Einstellungen müssen ein Objekt sein",
    "e_layout": "Layout {name}: {d}",
    "e_layout_doppelt": "Layout-Kennung doppelt: {id}",
    "e_tv_doppelt": "Fernseher-Kennung doppelt: {id}",
    "e_ton": "Ton nur aus, radio oder tiere",
    "e_aufloesung": "Auflösung nur 1080 oder 2160",
    "e_tv_fehlt": "Mindestens ein Fernseher nötig",
    "e_zeitzone": "unbekannte Zeitzone {zz}",
    "e_stufe": "unbekannte Stufe",
    "e_suchmuster": "ungültiges Suchmuster: {x}",
    "e_ortsmuster": "ungültiges Ortsmuster: {m}",
    "e_ep_quelle": "Einspieler: unbekannte Quelle",
    "e_ep_adresse": "Einspieler: Adresse fehlt",
    "e_medium_art": "Medium: Art bild oder video",
    "e_pult_pw": "Pult-Passwort: mindestens 6 Zeichen",
    "e_bild_gross": "Bild zu groß (höchstens 8 MB)",
    "e_bild_art": "Nur JPG oder PNG",
    "e_einspielen": "Keine SignageCast-Sicherung bzw. kein Profil",
    "e_streamliste": "Streamliste fehlt",
    "e_stream_id": "ungültige ID {id}",
    # Layouts und Zeitplan
    "l_entitaet": "ungültige Entität {w}",
    "l_symbol": "Symbol muss mdi-… sein",
    "l_farbe": "Farbe als #rrggbb",
    "l_bild": "ungültiges Bild",
    "l_quelle": "ungültige Datenquelle",
    "l_pfad": "Pfad zu lang",
    "l_adresse": "Adresse mit http:// oder https://",
    "l_wahl": "erlaubt: {werte}",
    "l_vergleich": "unbekannter Vergleich",
    "l_kennung": "ungültige Layout-Kennung {id}",
    "l_hintergrund": "Hintergrund: wetter, stil, farbe oder bild",
    "l_hg_bild": "ungültiges Hintergrundbild",
    "l_schema": "Schema hell, dunkel oder gedimmt",
    "l_schrift": "unbekannte Schrift",
    "l_baustein": "unbekannter Baustein {typ}",
    "l_baustein_id": "ungültige oder doppelte Baustein-Kennung {id}",
    "z_uhrzeit": "Zeitplan: Uhrzeit als HH:MM",
    "z_layout": "Zeitplan: unbekanntes Layout {id}",
    # Video-Streams, Radio, Durchsagen
    "s_kein_link": "Kein YouTube-Video- oder Kanal-Link erkannt",
    "s_nicht_einbettbar": "Dieses Video darf nicht eingebettet werden (oder existiert nicht)",
    "s_ort": "ungültiger Ort ({k})",
    "r_adresse": "Adresse muss mit http:// oder https:// beginnen",
    "r_nicht_erreichbar": "Adresse nicht erreichbar: {d}",
    "r_hls": "HLS-Radio (m3u8) wird nicht unterstützt – bitte eine MP3/AAC-Adresse nehmen",
    "r_keine_adresse": "Playlist enthält keine Stream-Adresse",
    "r_kein_audio": "Kein Audio-Stream (Inhalt: {typ})",
    "r_verschachtelt": "Zu viele verschachtelte Playlists",
    "r_playlist_leer": "Keine Stream-Adresse (http/https) in der Playlist gefunden",
    "d_text_tv": "Text und mindestens ein Fernseher nötig",
    "d_stimme_fehlt": "Stimme noch nicht geladen (Verwaltung → Einstellungen → Durchsage-Pult)",
    "d_stimme": "unbekannte Stimme",
    "bn_kanal": "unbekannter Kanal",
    # seit 0.21: PDF, Abfahrten, Zeitraum, Notfall-Vollbild, Fernseher schalten
    "l_pdf": "ungültiges PDF",
    "l_haltestelle": "ungültige Haltestelle",
    "l_zeitraum": "Zeitraum: Datum als JJJJ-MM-TT, optional mit Uhrzeit",
    "pdf_art": "Keine PDF-Datei",
    "pdf_werkzeug": "pdftoppm fehlt (Paket poppler-utils) – bitte SignageCast aktualisieren",
    "pdf_zeit": "Umwandeln dauert länger als {s} s – bitte ein kleineres PDF nehmen",
    "pdf_kaputt": "PDF nicht lesbar: {d}",
    "ab_http": "Fahrplan-Dienst antwortet {code}",
    "ab_nicht_erreichbar": "Fahrplan-Dienst nicht erreichbar: {d}",
    "ab_antwort": "Fahrplan-Dienst: unerwartete Antwort",
    "al_text": "Text für das Notfall-Vollbild fehlt",
    "sch_entitaet": "Für diesen Fernseher ist keine Entität zum Schalten eingetragen",
}


class Meldung(ValueError):
    def __init__(self, kennung, innen=None, **p):  # „kennung“, weil Werte selbst „code“ heißen können (HTTP-Status)
        self.innen = als_dict(innen) if innen is not None else None
        if innen is not None:
            p["d"] = str(innen).strip("'")
        self.code, self.p = kennung, {k: str(v)[:200] for k, v in p.items()}
        super().__init__(DE.get(kennung, kennung).format(**self.p))


def als_dict(ex):
    """Für die Verwaltung: {"code", "p", "text"[, "innen"]} – bei fremden Fehlern nur der Text."""
    if isinstance(ex, Meldung):
        return dict({"code": ex.code, "p": ex.p, "text": str(ex)}, **({"innen": ex.innen} if ex.innen else {}))
    return {"code": "", "p": {}, "text": (str(ex).strip("'") if isinstance(ex, KeyError) else str(ex))[:300]}
