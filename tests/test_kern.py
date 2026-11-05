# Automatische Tests für SignageCast (nur Python-Standardbibliothek; pyzipper optional).
# Aufruf im Projektordner:  python3 -m unittest discover -s tests -v
import datetime, json, os, re, sys, tempfile, time, unittest

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

    def test_kodierung_je_fernseher(self):
        t = E.pruefen({})["fernseher"][0]
        self.assertEqual((t["encoder"], t["preset"], t["tune"], t["bframes"]), ("auto", "veryfast", "zerolatency", 0))
        t = E.pruefen({"fernseher": [{"id": "tv", "encoder": "nvenc", "preset": "medium", "tune": "keins", "bframes": 2}]})["fernseher"][0]
        self.assertEqual((t["encoder"], t["preset"], t["tune"], t["bframes"]), ("nvenc", "medium", "keins", 2))
        t = E.pruefen({"fernseher": [{"id": "tv", "encoder": "amf", "preset": "slow", "tune": "film"}]})["fernseher"][0]
        self.assertEqual((t["encoder"], t["preset"], t["tune"]), ("auto", "veryfast", "zerolatency"))
        with self.assertRaises(E.Fehler):
            E.pruefen({"fernseher": [{"id": "tv", "bframes": 5}]})

    def test_video_args(self):
        import hardware as HW
        self.assertIn("libx264 -preset fast -pix_fmt yuv420p -bf 1", HW.video_args("software", "h264", 1920, 1080, "fast", "keins", 1))
        self.assertIn("-tune zerolatency", HW.video_args("software", "h264", 1920, 1080))
        v = HW.video_args("vaapi", "h265", 3840, 2160, "medium", "keins", 2)
        self.assertIn("scale_vaapi=w=3840:h=2160", v)
        self.assertIn("hevc_vaapi -profile:v main -bf 2", v)
        self.assertNotIn("preset", v)
        self.assertIn("h264_qsv -profile:v high -preset faster -async_depth 1 -bf 0", HW.video_args("qsv", "h264", 3840, 2160))
        n = HW.video_args("nvenc", "h265", 1920, 1080, "ultrafast", "zerolatency", 0)
        self.assertIn("hevc_nvenc -profile:v main -preset p1 -tune ull", n)
        for enc in HW.ENCODER[1:]:            # keine Zeichen, die die .env-Datei (sh) stören
            for pr in HW.PRESETS:
                self.assertNotRegex(HW.video_args(enc, "h264", 1920, 1080, pr, "keins", 4), r"[\"'$`\\;]")

    def test_codec_je_fernseher(self):
        self.assertEqual(E.pruefen({})["fernseher"][0]["codec"], "auto")
        t = E.pruefen({"fernseher": [{"id": "tv", "codec": "h264"}]})["fernseher"][0]
        self.assertEqual(t["codec"], "h264")
        self.assertEqual(E.pruefen({"fernseher": [{"id": "tv", "codec": "vp9"}]})["fernseher"][0]["codec"], "auto")

    def test_pult_zugaenge_und_passwort(self):
        import durchsage as DS
        h = DS.passwort_hash("geheim123")
        self.assertTrue(DS.passwort_ok("geheim123", h)); self.assertFalse(DS.passwort_ok("falsch", h))
        p = E.pruefen({"pult": {"zugaenge": [{"id": "rezep1", "name": "Rezeption", "passwort": h, "fernseher": ["tv", "../x"]}],
                                "stimme": "ramona", "dauer_s": 120}})["pult"]
        self.assertEqual((p["zugaenge"][0]["fernseher"], p["stimme"]), (["tv"], "kerstin"))
        with self.assertRaises(E.Fehler):
            E.pruefen({"pult": {"dauer_s": 5000}})
        with self.assertRaises(E.Fehler):
            E.pruefen({"pult": {"zugaenge": [{"id": "rezep1", "passwort": "klartext"}]}})

    def test_meldung_mit_code_parameter(self):                              # Fehler aus 0.11.3
        m = M.Meldung("http", code=404, grund="Not Found")
        self.assertEqual((m.code, str(m)), ("http", "HTTP 404 Not Found"))


class Uebersetzungen(unittest.TestCase):
    """Seit 0.19.3: Prüfmeldungen tragen eine Kennung, jede Kennung hat einen englischen Text in der Verwaltung."""

    def test_layoutfehler_mit_innerer_meldung(self):
        with self.assertRaises(E.Fehler) as f:
            E.pruefen({"layouts": [{"id": "ab", "name": "Flur", "thema": {"schema": "bunt"}}]})
        m = M.als_dict(f.exception)
        self.assertEqual((m["code"], m["p"]["name"], m["innen"]["code"]), ("e_layout", "Flur", "l_schema"))
        self.assertEqual(m["text"], "Layout Flur: Schema hell, dunkel oder gedimmt")

    def test_bereich(self):
        with self.assertRaises(E.Fehler) as f:
            E.pruefen({"standort": {"breite": 200}})
        self.assertEqual(f.exception.code, "e_bereich")

    def test_jede_kennung_englisch(self):
        js = open(os.path.join(os.path.dirname(__file__), "..", "cockpit", "signagecast", "tv.js"), encoding="utf-8").read()
        en = js[js.index("meldung: {", js.index("Meldungen des Dienstes nach Kennung")):]
        fehlt = [k for k in M.DE if not re.search(r"\b" + k + r":", en[:en.index("\n    },")])]
        self.assertEqual(fehlt, [])

    def test_benachrichtigung_beide_sprachen(self):
        import benachrichtigung as BN
        self.assertEqual(set(BN.TEXTE["de"]), set(BN.TEXTE["en"]))
        self.assertEqual(BN.texte("en", "ausfall", tv="Flur")[0], "SignageCast: “Flur” failed")
        self.assertEqual(BN.texte("xx", "test", version="1", host="h")[0], "SignageCast: test")


class Webbild(unittest.TestCase):
    """Seit 0.20: Baustein „Webseite“ im Modus Bildschirmfoto."""

    def test_modus_pruefen(self):
        el = {"id": "w", "typ": "webseite", "optionen": {"url": "https://example.org", "modus": "bild"}}
        self.assertEqual(L.pruefe_layout({"id": "ab", "elemente": [el]})["elemente"][0]["optionen"]["modus"], "bild")
        el["optionen"]["modus"] = "video"
        with self.assertRaises(ValueError):
            L.pruefe_layout({"id": "ab", "elemente": [el]})
        self.assertEqual(L.pruefe_layout({"id": "ab", "elemente": [{"id": "w", "typ": "webseite"}]})["elemente"][0]["optionen"]["modus"], "einbetten")

    def test_faellig_und_bild(self):
        import webbild as WB
        with tempfile.TemporaryDirectory() as d:
            a = {"url": "https://example.org", "breite": 640, "hoehe": 480, "faktor": 1, "alle_min": 5}
            f = WB.Fotograf(d, lambda: [a])
            k = WB.schluessel(a["url"], 640, 480, 1)
            self.assertIsNone(f.bild(a))
            self.assertEqual(f.faellig(a, time.time()), k)                  # noch kein Foto
            open(f.datei(k), "wb").write(b"x")
            self.assertTrue(f.bild(a).startswith(f"/webbild/{k}.png?t="))
            self.assertIsNone(f.faellig(a, time.time()))                     # frisch
            self.assertEqual(f.faellig(a, time.time() + 301), k)             # nach 5 min wieder
            os.remove(f.datei(k))
            f.stand[k] = {"zeit": time.time(), "fehler": "kaputt"}
            self.assertIsNone(f.faellig(a, time.time() + 100))               # nach Fehler 5 min Pause
            self.assertEqual(f.faellig(a, time.time() + 301), k)



class Neu021(unittest.TestCase):
    """Seit 0.21: PDF, Abfahrten, Zeitraum, Notfall-Vollbild, Fernseher über HA schalten."""

    def test_zeitraum(self):
        el = {"id": "z", "typ": "text", "ab": "2026-12-23", "bis": "2027-01-02"}
        e = L.pruefe_layout({"id": "ab", "elemente": [el]})["elemente"][0]
        self.assertEqual((e["ab"], e["bis"]), ("2026-12-23", "2027-01-02"))
        self.assertFalse(L.im_zeitraum(e, "2026-12-22T23:59"))
        self.assertTrue(L.im_zeitraum(e, "2026-12-23T00:00"))
        self.assertTrue(L.im_zeitraum(e, "2027-01-02T23:59"))          # reines Datum: bis Tagesende
        self.assertFalse(L.im_zeitraum(e, "2027-01-03T00:00"))
        e = L.pruefe_layout({"id": "ab", "elemente": [dict(el, ab="2026-12-23 08:30", bis="2026-12-23T12:00")]})["elemente"][0]
        self.assertEqual(e["ab"], "2026-12-23T08:30")
        self.assertFalse(L.im_zeitraum(e, "2026-12-23T08:29"))
        self.assertTrue(L.im_zeitraum(e, "2026-12-23T11:59"))
        self.assertFalse(L.im_zeitraum(e, "2026-12-23T12:00"))
        self.assertTrue(L.im_zeitraum({"ab": "", "bis": ""}, "2026-01-01T00:00"))
        with self.assertRaises(ValueError):
            L.pruefe_layout({"id": "ab", "elemente": [dict(el, ab="23.12.2026")]})

    def test_pdf_und_abfahrten_pruefen(self):
        l = L.pruefe_layout({"id": "ab", "elemente": [{"id": "p", "typ": "pdf", "optionen": {"datei": "0123456789abcdef", "sekunden": 20}},
                                                      {"id": "a", "typ": "abfahrten", "optionen": {"haltestelle": "8011160", "name": "Berlin Hbf"}}]})
        self.assertEqual(l["elemente"][0]["optionen"]["sekunden"], 20)
        self.assertEqual(l["elemente"][1]["optionen"]["anzahl"], 6)
        for falsch in ({"id": "p", "typ": "pdf", "optionen": {"datei": "../x"}}, {"id": "a", "typ": "abfahrten", "optionen": {"haltestelle": "a b"}}):
            with self.assertRaises(ValueError):
                L.pruefe_layout({"id": "ab", "elemente": [falsch]})

    def test_pdf_erkennen_und_aufraeumen(self):
        import pdf as PDF
        self.assertTrue(PDF.ist_pdf(b"%PDF-1.7\n"))
        self.assertFalse(PDF.ist_pdf(b"\x89PNG"))
        with tempfile.TemporaryDirectory() as d:
            for n in ("0123456789abcdef", "fedcba9876543210"):
                os.makedirs(os.path.join(d, n))
                for i in (1, 2, 3):
                    open(os.path.join(d, n, f"{i}.jpg"), "wb").write(b"x")
            self.assertEqual(PDF.seiten(d, "0123456789abcdef"), 3)
            alt = time.time() - 2 * 86400
            os.utime(os.path.join(d, "fedcba9876543210"), (alt, alt))
            PDF.aufraeumen(d, {"0123456789abcdef"})
            self.assertEqual(sorted(os.listdir(d)), ["0123456789abcdef"])
            falsch = os.path.join(d, "kein.pdf")
            open(falsch, "wb").write(b"hallo")
            with self.assertRaises(M.Meldung) as f:
                PDF.umwandeln(falsch, d)
            self.assertEqual(f.exception.code, "pdf_art")

    def test_abfahrten_aufbereiten(self):
        import abfahrten as AB
        jetzt = 1_800_000_000
        iso = lambda s: __import__("datetime").datetime.fromtimestamp(jetzt + s, __import__("datetime").timezone.utc).isoformat()
        roh = {"departures": [
            {"when": iso(600), "plannedWhen": iso(480), "delay": 120, "line": {"name": "RE 3", "product": "regional"},
             "direction": "München Hbf", "platform": "4"},
            {"when": None, "plannedWhen": iso(300), "cancelled": True, "line": {"name": "Bus 6"}, "direction": "Klinikum"},
            {"when": iso(-600), "plannedWhen": iso(-600), "line": {"name": "alt"}, "direction": "weg"}]}
        liste = AB.aufbereiten(roh, jetzt)
        self.assertEqual([x["linie"] for x in liste], ["Bus 6", "RE 3"])
        self.assertEqual((liste[1]["plus"], liste[1]["gleis"], liste[0]["ausfall"]), (2, "4", True))
        a = AB.Abfahrten(lambda: [])
        a.daten[(AB.DIENST, "8000309")] = {"liste": liste, "zeit": jetzt, "fehler": None}
        self.assertEqual([x["linie"] for x in a.fuer({"haltestelle": "8000309", "anzahl": 5, "vorlauf_min": 6}, jetzt)["liste"]], ["RE 3"])
        self.assertEqual(len(a.fuer({"haltestelle": "8000309", "anzahl": 1, "vorlauf_min": 0}, jetzt)["liste"]), 1)

    def test_alarm_und_schalten_einstellungen(self):
        e = E.pruefen({"fernseher": [{"id": "tv", "ha_schalten": "media_player.wohnzimmer"}],
                       "pult": {"zugaenge": [{"id": "abcd", "name": "Empfang", "alarm": True}]}, "alarm": {"vorlagen": ["Raus!", " "], "ton": False}})
        self.assertEqual(e["fernseher"][0]["ha_schalten"], "media_player.wohnzimmer")
        self.assertTrue(e["pult"]["zugaenge"][0]["alarm"])
        self.assertEqual(e["alarm"], {"vorlagen": ["Raus!"], "ton": False})
        self.assertFalse(E.pruefen({})["pult"]["zugaenge"] or E.pruefen({"pult": {"zugaenge": [{"id": "abcd"}]}})["pult"]["zugaenge"][0]["alarm"])
        with self.assertRaises(E.Fehler):
            E.pruefen({"fernseher": [{"id": "tv", "ha_schalten": "light.flur"}]})


class Vorlagen0233(unittest.TestCase):
    """Pult-/Notfall-Vorlagen folgen der Sprache, solange sie unverändert sind; eigene Texte bleiben."""
    def test_sprache(self):
        self.assertEqual(E.pruefen({"sprache": "en"})["alarm"]["vorlagen"], E.VORLAGEN["en"]["alarm"])
        self.assertEqual(E.pruefen({"sprache": "en"})["pult"]["vorlagen"], E.VORLAGEN["en"]["pult"])
        en = E.pruefen({"sprache": "en"})
        zurueck = E.pruefen(dict(en, sprache="de"))
        self.assertEqual(zurueck["pult"]["vorlagen"], E.VORLAGEN["de"]["pult"])
        self.assertEqual(E.pruefen({"sprache": "", "alarm": {"vorlagen": E.VORLAGEN["en"]["alarm"]}})["alarm"]["vorlagen"],
                         E.VORLAGEN["en"]["alarm"])          # Sprache noch offen: nichts ändern

    def test_eigene_bleiben(self):
        e = E.pruefen({"sprache": "en", "pult": {"vorlagen": ["Bitte warten"]}, "alarm": {"vorlagen": E.VORLAGEN["de"]["alarm"][:1]}})
        self.assertEqual(e["pult"]["vorlagen"], ["Bitte warten"])
        self.assertEqual(e["alarm"]["vorlagen"], E.VORLAGEN["de"]["alarm"][:1])

    def test_standard_gleich(self):
        self.assertEqual(E.STANDARD["pult"]["vorlagen"], E.VORLAGEN["de"]["pult"])
        self.assertEqual(E.STANDARD["alarm"]["vorlagen"], E.VORLAGEN["de"]["alarm"])

    def test_playlist_fehler_als_meldung(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
        import radio
        with self.assertRaises(M.Meldung) as k:
            radio.playlist_lesen("#EXTM3U\nkeine adresse\n")
        d = M.als_dict(k.exception)
        self.assertEqual(d["code"], "r_playlist_leer")
        self.assertIn(d["code"], M.DE)


class Player023(unittest.TestCase):
    """Raspberry-Pi-Player: Image je Gerät, signierte Meldungen, WLAN-Schlüssel."""
    def setUp(self):
        import player as PL
        self.PL, d = PL, tempfile.mkdtemp()
        PL.DATEI, PL.ORDNER, PL.GRUND = os.path.join(d, "player.json"), os.path.join(d, "p"), os.path.join(d, "p", "basis")
        PL.daten.clear()
        PL.daten.update(PL._leer())

    def grundimage(self):
        """Kleines Image (8 MiB) mit Platzhalter wie aus player/bauen.sh."""
        import lzma
        PL, marke = self.PL, "SCPH-test"
        platz = b"".join((f"{marke}-{i:04d}".ljust(511) + "\n").encode() for i in range(32))
        img = bytearray(os.urandom(1 << 20)) + bytes(6 << 20) + bytearray(os.urandom(1 << 20))
        img[3 << 20:(3 << 20) + len(platz)] = platz
        os.makedirs(PL.GRUND)
        open(os.path.join(PL.GRUND, "x.img.xz"), "wb").write(lzma.compress(bytes(img)))
        json.dump({"art": "signagecast-player-image", "version": "0", "datei": "x.img.xz", "groesse": len(img),
                   "platzhalter": {"offset": 3 << 20, "laenge": 16384, "marke": marke}}, open(os.path.join(PL.GRUND, "meta.json"), "w"))
        return bytes(img)

    def test_image_je_geraet(self):
        import gzip
        PL, img = self.PL, self.grundimage()
        g = PL.neu({"name": "Wohnzimmer Süd", "tv": "tv", "modell": "pi3"}, {"tv"})
        k = PL.herunterladen_vorbereiten(g["id"], {"ssid": "Heim", "passwort": "geheim123", "speichern": False}, "http://192.168.1.20:8890")
        aus = []
        PL.image_schreiben(k, aus.append, "de", "Europe/Vienna")
        neu = gzip.decompress(b"".join(aus))
        self.assertEqual(len(neu), len(img))
        self.assertEqual(neu[:3 << 20], img[:3 << 20])
        self.assertEqual(neu[(3 << 20) + 16384:], img[(3 << 20) + 16384:])
        konf = json.loads(neu[3 << 20:(3 << 20) + 16384])
        self.assertEqual((konf["id"], konf["land"], konf["hostname"], konf["server"]), (g["id"], "AT", "sc-wohnzimmer-s-d", "http://192.168.1.20:8890"))
        self.assertEqual(konf["wlan"], [{"ssid": "Heim", "psk": PL.psk("Heim", "geheim123")}])
        self.assertNotIn("geheim123", neu[3 << 20:(3 << 20) + 16384].decode())
        self.assertEqual(PL.daten["wlan"], [])                       # nicht gespeichert
        with self.assertRaises(M.Meldung):                           # Link nur einmal
            PL.image_schreiben(k, aus.append, "de", "")

    def test_psk_wie_wpa_supplicant(self):
        # wpa_passphrase "IEEE" "password" (Testvektor IEEE 802.11i)
        self.assertEqual(self.PL.psk("IEEE", "password"), "f42c6fc52df0ebef9ebb4b90b38a5f902e83fe1b135a70e23aed762e9710a12e")
        with self.assertRaises(M.Meldung):
            self.PL.psk("x", "kurz")

    def test_signatur_wie_agent(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "player"))
        import agent
        PL = self.PL
        g = PL.neu({"name": "Flur"}, set())
        gesendet = {}

        class Antwort:
            status, headers = 200, {}

            def __init__(self, inhalt, kopf):
                self.inhalt, self.headers = inhalt, kopf

            def read(self):
                return self.inhalt

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        def urlopen(anf, timeout=0):
            kopf = dict(anf.header_items())
            kopf = {k.title(): v for k, v in kopf.items()}
            gesendet.update(kopf)
            gg, code, zeit = PL.pruefen(kopf, "/player/melden", anf.data)
            self.assertEqual(code, 200)
            inhalt = json.dumps(PL.melden(gg, json.loads(anf.data), "1.2.3.4", None, None)).encode()
            return Antwort(inhalt, {"X-Signatur": PL.signatur(gg, zeit, inhalt), "X-Server-Zeit": str(int(time.time()))})
        alt = agent.urllib.request.urlopen
        agent.urllib.request.urlopen = urlopen
        try:
            s = agent.Server({"id": g["id"], "schluessel": g["schluessel"], "server": "http://x:8890"})
            code, inhalt = s.anfrage("/player/melden", {"modell": "Raspberry Pi 4"})
            self.assertEqual(json.loads(inhalt)["name"], "Flur")
            self.assertTrue(PL.online(g["id"]))
            self.assertNotIn(g["schluessel"], json.dumps(gesendet))
            # fremde Antwort (falsche Signatur) wird abgelehnt
            agent.urllib.request.urlopen = lambda a, timeout=0: Antwort(b"{}", {"X-Signatur": "0" * 64})
            with self.assertRaises(PermissionError):
                s.anfrage("/player/melden", {})
        finally:
            agent.urllib.request.urlopen = alt
        self.assertEqual(PL.pruefen({"X-Geraet": g["id"], "X-Zeit": str(int(time.time())), "X-Signatur": "0" * 64}, "/player/melden", b"{}")[1], 403)
        self.assertEqual(PL.pruefen({"X-Geraet": g["id"], "X-Zeit": "1", "X-Signatur": ""}, "/player/melden", b"{}")[1], 401)
        PL.entfernen(g["id"])
        self.assertEqual(PL.pruefen({"X-Geraet": g["id"]}, "/player/melden", b"")[1], 410)

    def test_github_api_kopf(self):
        """Die GitHub-API lehnt Accept: application/octet-stream mit 415 ab (Fehler in 0.23.0)."""
        PL, kopf = self.PL, {}

        class A:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def read(self, n=-1):
                return b"[]"

        def urlopen(anf, timeout=0):
            kopf[anf.full_url] = anf.get_header("Accept")
            return A()
        alt = PL.urllib.request.urlopen
        PL.urllib.request.urlopen = urlopen
        try:
            with self.assertRaises(M.Meldung):
                PL._quelle("0.23.0")
            PL._holen("https://github.com/x/releases/download/v1/a.img.xz")
        finally:
            PL.urllib.request.urlopen = alt
        self.assertEqual(list(kopf.values()), ["application/vnd.github+json", "application/octet-stream"])

    def test_felder_und_wlan_wechsel(self):
        PL = self.PL
        g = PL.neu({"name": "Empfang", "tv": "tv"}, {"tv"})
        with self.assertRaises(M.Meldung):
            PL.aendern(g["id"], {"tv": "gibtsnicht"}, {"tv"})
        PL.aendern(g["id"], {"drehung": 90, "lautstaerke": 250, "aufloesung": "1080", "drehung_x": 1}, {"tv"})
        self.assertEqual((g["drehung"], g["lautstaerke"], g["aufloesung"]), (90, 100, "1080"))
        PL.wlan_wechseln(g["id"], {"ssid": "Praxis", "passwort": "abcdefgh", "speichern": True})
        self.assertEqual(PL.daten["wlan"][0]["ssid"], "Praxis")
        a = PL.melden(g, {"wlan_rev": 0}, "", None, None)
        self.assertEqual((a["wlan"]["rev"], a["wlan"]["netze"][0]["ssid"]), (1, "Praxis"))
        a = PL.melden(g, {"wlan_rev": 1, "ergebnisse": [{"art": "wlan", "ok": True}]}, "", None, None)
        self.assertIsNone(a["wlan"])
        self.assertEqual(PL.ergebnisse[g["id"]][0]["art"], "wlan")
        self.assertAlmostEqual(PL.ergebnisse[g["id"]][0]["ts"], time.time(), delta=5)   # Zeitstempel für das Browserformat (0.23.2)
        self.assertNotIn("schluessel", json.dumps(PL.liste(lambda g: [])))
        self.assertNotIn(PL.daten["wlan"][0]["psk"], json.dumps(PL.liste(lambda g: [])))


if __name__ == "__main__":
    unittest.main()
