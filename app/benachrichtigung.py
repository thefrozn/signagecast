# Benachrichtigungen (seit 0.16): Ereignisse (Fernseher-Ausfall, Update-/Sicherungsfehler, Home Assistant getrennt)
# über Telegram, E-Mail (SMTP) und Home Assistant melden. Jedes Ereignis nur einmal, Entwarnung wenn es vorbei ist.
import json, smtplib, ssl, threading, time, urllib.error, urllib.request
from email.message import EmailMessage

GEHEIM = (("telegram", "token"), ("email", "passwort"))


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
    """melden(schluessel, art, betreff, text) / vorbei(schluessel, betreff, text): jedes Ereignis nur einmal senden."""

    def __init__(self, einst, ha_post):
        self.einst, self.ha_post = einst, ha_post
        self.offen = {}                             # schluessel -> Zeitpunkt der Meldung
        self.letzte = []                            # [{zeit, betreff, ergebnis}] für die Verwaltung

    def _los(self, betreff, text):
        def senden_():
            e = senden(self.einst()["benachrichtigung"], self.ha_post, betreff, text)
            self.letzte = ([{"zeit": time.strftime("%Y-%m-%d %H:%M"), "betreff": betreff, "ergebnis": e}] + self.letzte)[:10]
        threading.Thread(target=senden_, daemon=True).start()

    def melden(self, schluessel, art, betreff, text):
        if schluessel in self.offen or not self.einst()["benachrichtigung"]["ereignisse"].get(art):
            return
        self.offen[schluessel] = time.time()
        self._los(betreff, text)

    def vorbei(self, schluessel, betreff, text):
        if self.offen.pop(schluessel, None) is not None:
            self._los(betreff, text)
