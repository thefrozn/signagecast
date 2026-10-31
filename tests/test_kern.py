# Automatische Tests für SignageCast (nur Python-Standardbibliothek; pyzipper optional).
# Aufruf im Projektordner:  python3 -m unittest discover -s tests -v
import datetime, json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
os.environ.setdefault("SC_EINSTELLUNGEN", os.path.join(tempfile.mkdtemp(), "einstellungen.json"))
import einstellungen as E   # noqa: E402
import layouts as L         # noqa: E402
import meldung as M         # noqa: E402
import medien as MED        # noqa: E402
import quellen as Q         # noqa: E402
import sicherung as S       # noqa: E402


class Curl(unittest.TestCase):
    def test_kopfzeilen_und_post(self):
        r = Q.aus_curl("curl -s -H 'Authorization: Bearer abc' -H \"Accept: application/json\" 'https://api.example.com/x?a=1' -d '{\"a\":1}'")
        q = r["quelle"]
        self.assertEqual(q["url"], "https://api.example.com/x?a=1")
        self.assertEqual(q["methode"], "POST")
        self.assertTrue(next(k for k in q["kopf"] if k["name"] == "Authorization")["geheim"])
        self.assertFalse(next(k for k in q["kopf"] if k["name"] == "Accept")["geheim"])

    def test_benutzer_wird_basic_und_geheim(self):
        k = Q.aus_curl("curl -u nutzer:pw https://x.org/a")["quelle"]["kopf"][0]
        self.assertEqual(k["wert"], "Basic bnV0emVyOnB3")
        self.assertTrue(k["geheim"])

    def test_ohne_adresse(self):
        with self.assertRaises(Q.Fehler) as f:
            Q.aus_curl("curl -s")
        self.assertEqual(f.exception.code, "curl_adresse")


class PfadeUndVorlagen(unittest.TestCase):
    D = {"a": {"b": [{"c": 1.5}, {"c": "2,25"}]}, "liste": ["x", "y"]}

    def test_pfade(self):
        self.assertEqual(Q.wert_bei(self.D, "a.b[0].c"), 1.5)
        self.assertEqual(Q.wert_bei(self.D, "a.b.1.c"), "2,25")
        self.assertEqual(Q.wert_bei(self.D, "liste[1]"), "y")
        self.assertEqual(Q.wert_bei(self.D, "a.b.length"), 2)
        self.assertIsNone(Q.wert_bei(self.D, "fehlt.x"))

    def test_vorlage_mit_format(self):
        self.assertEqual(Q.fuellen("{a.b[0].c} € / {liste[0]}", "q", lambda q: self.D, nachkomma=2), "1,50 € / x")
        self.assertEqual(Q.fuellen("{qq:a.b[1].c} cm", None, lambda q: self.D, nachkomma=1, faktor=100), "225,0 cm")

    def test_tausender(self):
        self.assertEqual(Q.formatieren(71654, 0), "71.654")
        self.assertEqual(Q.formatieren(1234.5, 1, sprache="en"), "1,234.5")


class Geheimnisse(unittest.TestCase):
    def test_maskieren_und_zurueck(self):
        qs = Q.pruefen([{"id": "kamera", "url": "rtsp://u:pw@cam/x", "art": "video",
                         "kopf": [{"name": "X-Key", "wert": "geheim1", "geheim": True}]}])
        m = Q.maskieren(qs)
        self.assertNotIn("geheim1", json.dumps(m))
        self.assertNotIn(":pw@", json.dumps(m))
        zurueck = Q.demaskieren(json.loads(json.dumps(m)), qs)
        self.assertEqual(zurueck[0]["kopf"][0]["wert"], "geheim1")
        self.assertIn(":pw@", zurueck[0]["url"])
        self.assertEqual(Q.ohne_geheimnisse(qs)[0]["kopf"][0]["wert"], "")


class ICal(unittest.TestCase):
    def test_wiederholungen_und_ausnahmen(self):
        heute = datetime.date.today()
        start = heute - datetime.timedelta(weeks=1)                 # vergangen; danach heute, +1 Woche (Ausnahme), +2, +3
        aus = heute + datetime.timedelta(weeks=1)
        ics = f"""BEGIN:VCALENDAR
BEGIN:VEVENT
UID:1
SUMMARY:Woche\\, Halle
DTSTART;VALUE=DATE:{start:%Y%m%d}
RRULE:FREQ=WEEKLY;COUNT=5
EXDATE;VALUE=DATE:{aus:%Y%m%d}
END:VEVENT
BEGIN:VEVENT
UID:2
SUMMARY:Abgesagt
STATUS:CANCELLED
DTSTART;VALUE=DATE:{heute + datetime.timedelta(days=3):%Y%m%d}
END:VEVENT
END:VCALENDAR"""
        t = Q.ical_zerlegen(ics, tage=60)["termine"]
        tage = [x["start"] for x in t]
        self.assertTrue(all(x["titel"] == "Woche, Halle" for x in t))
        self.assertNotIn(aus.isoformat(), tage)
        self.assertNotIn((start).isoformat(), tage)                      # vergangen
        self.assertEqual(tage, [(heute + datetime.timedelta(weeks=w)).isoformat() for w in (0, 2, 3)])   # 5 – vergangen – Ausnahme


class Sicherung(unittest.TestCase):
    def test_passwortregeln(self):
        for schlecht, code in (("kurz", "sich_pw_kurz"), ("passwortpasswort", "sich_pw_schwach")):
            with self.assertRaises(M.Meldung) as f:
                S.passwort_pruefen(schlecht)
            self.assertEqual(f.exception.code, code)
        S.passwort_pruefen("Correct-Horse#Battery9")
        S.passwort_pruefen("eine sehr lange passphrase ohne ziffern")

    @unittest.skipIf(S.pyzipper is None, "python3-pyzipper fehlt")
    def test_aes_zip(self):
        man = json.dumps({"art": S.ART}).encode()
        roh = S.erstellen({"manifest.json": man, "geheim.txt": b"GEHEIM"}, "Correct-Horse#Battery9")
        self.assertNotIn(b"GEHEIM", roh)
        self.assertEqual(S.lesen(roh, "Correct-Horse#Battery9")["geheim.txt"], b"GEHEIM")
        for pw, code in ((None, "sich_pw_fehlt"), ("Falsch-Falsch#123", "sich_pw_falsch")):
            with self.assertRaises(M.Meldung) as f:
                S.lesen(roh, pw)
            self.assertEqual(f.exception.code, code)


class Medien(unittest.TestCase):
    def test_art_am_inhalt(self):
        self.assertEqual(MED.art_erkennen(b"\xff\xd8\xff\xe0" + b"0" * 12), ("bild", "jpg"))
        self.assertEqual(MED.art_erkennen(b"\x00\x00\x00\x20ftypisom" + b"0" * 4), ("video", "mp4"))
        with self.assertRaises(M.Meldung):
            MED.art_erkennen(b"#!/bin/sh\nrm -rf /")

    def test_hochladen_in_stuecken(self):
        h = MED.Hochladen(tempfile.mkdtemp())
        png = b"\x89PNG\r\n\x1a\n" + b"x" * 5000
        h.teil("abcd1234", 0, png[:2000])
        with self.assertRaises(M.Meldung):                    # Stück übersprungen
            h.teil("abcd1234", 2, png[2000:])
        h.teil("abcd1234", 0, png[:2000]); h.teil("abcd1234", 1, png[2000:])
        art, name, _ = h.fertig("abcd1234")
        self.assertEqual(art, "bild")
        self.assertRegex(name, r"^[0-9a-f]{16}\.png$")
        self.assertEqual(open(os.path.join(h.ordner, name), "rb").read(), png)


class EinstellungenUndLayouts(unittest.TestCase):
    def test_standard_hat_layout(self):
        e = E.pruefen({})
        self.assertTrue(e["layouts"])
        self.assertEqual(e["fernseher"][0]["layout"], e["layouts"][0]["id"])
        self.assertEqual(e["updates"]["system"], "melden")

    def test_alle_bausteine_pruefbar(self):
        el = [{"id": f"e{i}", "typ": t, "x": 0, "y": 0, "w": 10, "h": 6} for i, t in enumerate(L.TYPEN)]
        l = L.pruefe_layout({"id": "test", "name": "Test", "elemente": el})
        self.assertEqual(len(l["elemente"]), len(L.TYPEN))

    def test_bedingung_auf_datenquelle(self):
        l = L.pruefe_layout({"id": "test", "elemente": [{"id": "a", "typ": "text", "bedingung": {"quelle": "pegel", "pfad": "value", "op": ">", "wert": "1"}}]})
        self.assertEqual(l["elemente"][0]["bedingung"]["quelle"], "pegel")

    def test_karussell_und_zeitplan(self):
        ls = [{"id": i, "elemente": []} for i in ("aa", "bb", "cc")]
        tv = {"layout": "aa", "zeitplan": [{"von": "22:00", "bis": "06:00", "layout": "schwarz"}],
              "karussell": {"aktiv": True, "layouts": ["aa", "bb"], "minuten": 10}}
        self.assertEqual(L.aktuelles_layout(tv, ls, "12:05")["id"], "aa")
        self.assertEqual(L.aktuelles_layout(tv, ls, "12:15")["id"], "bb")
        self.assertEqual(L.aktuelles_layout(tv, ls, "12:25")["id"], "aa")
        self.assertTrue(L.aktuelles_layout(tv, ls, "23:00").get("schwarz"))         # Zeitplan hat Vorrang
        tv["karussell"]["aktiv"] = False
        self.assertEqual(L.aktuelles_layout(tv, ls, "12:15")["id"], "aa")

    def test_medien_und_fernseher_standard(self):
        e = E.pruefen({"medien": [{"id": "m1ab", "name": "Bild", "art": "bild", "datei": "0123456789abcdef.jpg", "dauer_s": 10}]})
        self.assertEqual(e["medien"][0]["dauer_s"], 10)
        t = e["fernseher"][0]
        self.assertEqual((t["video_quelle"], t["medien_alle"], t["karussell"]["aktiv"]), ("youtube", 3, False))
        with self.assertRaises(E.Fehler):
            E.pruefen({"medien": [{"id": "m1ab", "art": "bild", "datei": "../../etc/passwd"}]})

    def test_webhook_schluessel(self):
        self.assertEqual(E.pruefen({})["webhook"], {"aktiv": False, "token": ""})
        e = E.pruefen({"webhook": {"aktiv": 1, "token": "Ab_9-xY"}})
        self.assertEqual(e["webhook"], {"aktiv": True, "token": "Ab_9-xY"})
        with self.assertRaises(E.Fehler):
            E.pruefen({"webhook": {"token": "mit leerzeichen"}})

    def test_benachrichtigung(self):
        b = E.pruefen({})["benachrichtigung"]
        self.assertFalse(b["telegram"]["aktiv"] or b["email"]["aktiv"] or b["ha"]["aktiv"])
        e = E.pruefen({"benachrichtigung": {"telegram": {"aktiv": True, "token": "123456:" + "A" * 35, "chat_id": "-100123"},
                                            "email": {"port": "465", "sicherheit": "ssl", "empfaenger": "a@b.de, c@d.de"},
                                            "ha": {"dienst": "notify.mobile_app_handy"}, "ereignisse": {"ha": False, "x": True}}})["benachrichtigung"]
        self.assertEqual((e["email"]["port"], e["ereignisse"]["ha"], "x" in e["ereignisse"]), (465, False, False))
        for falsch in ({"telegram": {"token": "kein token"}}, {"ha": {"dienst": "light.turn_on"}}, {"email": {"empfaenger": "x"}}):
            with self.assertRaises(E.Fehler):
                E.pruefen({"benachrichtigung": falsch})

    def test_assistent_nur_bei_neuinstallation(self):
        self.assertFalse(E.pruefen({})["assistent_fertig"])
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"sprache": "de"}, f)
        alt, E.PFAD = E.PFAD, f.name
        try:
            self.assertTrue(E.laden()["assistent_fertig"])           # vorhandene Einrichtung ohne Schlüssel
            E.PFAD = f.name + ".fehlt"
            self.assertFalse(E.laden()["assistent_fertig"])          # Neuinstallation
        finally:
            E.PFAD = alt; os.remove(f.name)

    def test_meldung_mit_code_parameter(self):                              # Fehler aus 0.11.3
        m = M.Meldung("http", code=404, grund="Not Found")
        self.assertEqual((m.code, str(m)), ("http", "HTTP 404 Not Found"))


if __name__ == "__main__":
    unittest.main()
