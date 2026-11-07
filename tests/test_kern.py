# Automatische Tests für SignageCast (nur Python-Standardbibliothek; pyzipper optional).
# Aufruf im Projektordner:  python3 -m unittest discover -s tests -v
import calendar, datetime, json, os, re, sys, tempfile, time, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
os.environ.setdefault("SC_EINSTELLUNGEN", os.path.join(tempfile.mkdtemp(), "einstellungen.json"))
os.environ.setdefault("SC_DATEN", tempfile.mkdtemp())
import einstellungen as E   # noqa: E402
import layouts as L         # noqa: E402
import meldung as M         # noqa: E402
import medien as MED        # noqa: E402
import quellen as Q         # noqa: E402
import sicherung as S       # noqa: E402
import streams as ST        # noqa: E402


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
    """Seit 0.21: PDF, Zeitraum, Notfall-Vollbild, Fernseher über HA schalten."""

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

    def test_pdf_pruefen(self):
        l = L.pruefe_layout({"id": "ab", "elemente": [{"id": "p", "typ": "pdf", "optionen": {"datei": "0123456789abcdef", "sekunden": 20}},
                                                      {"id": "a", "typ": "abfahrten", "optionen": {"haltestelle": "8011160"}}]})
        self.assertEqual(l["elemente"][0]["optionen"]["sekunden"], 20)
        self.assertEqual(len(l["elemente"]), 1)              # Abfahrten seit 0.26 ausgebaut: alte Bausteine fallen still weg
        with self.assertRaises(ValueError):
            L.pruefe_layout({"id": "ab", "elemente": [{"id": "p", "typ": "pdf", "optionen": {"datei": "../x"}}]})

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

    def test_sammel_image(self):
        """Image für mehrere Pis (0.25): ohne Schlüssel, mit Kopplung – nur aus einem Grundimage ab 0.25."""
        import gzip
        PL, img = self.PL, self.grundimage()
        with self.assertRaises(M.Meldung) as f:                      # Grundimage zu alt: dessen Agent kann nicht koppeln
            PL.herunterladen_vorbereiten("", None, "http://192.168.1.20:8890")
        self.assertEqual(f.exception.code, "pi_basis_alt")
        m = json.load(open(os.path.join(PL.GRUND, "meta.json")))
        m["version"] = "0.25.0"
        json.dump(m, open(os.path.join(PL.GRUND, "meta.json"), "w"))
        k = PL.herunterladen_vorbereiten("", {"ssid": "Heim", "passwort": "geheim123"}, "http://192.168.1.20:8890")
        aus = []
        PL.image_schreiben(k, aus.append, "en", "Europe/Berlin")
        neu = gzip.decompress(b"".join(aus))
        konf = json.loads(neu[3 << 20:(3 << 20) + 16384])
        self.assertTrue(konf["kopplung"])
        self.assertNotIn("schluessel", konf)
        self.assertNotIn("id", konf)
        self.assertEqual((konf["server"], konf["hostname"], konf["sprache"]), ("http://192.168.1.20:8890", "sc-player", "en"))
        self.assertEqual(PL.daten["geraete"], [])                     # kein Gerät angelegt

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


class Direktmodus024(unittest.TestCase):
    """Direktmodus: Schlüssel für /anzeige, erlaubte Pfade, Modus je Modell."""
    def setUp(self):
        import player as PL
        self.PL, d = PL, tempfile.mkdtemp()
        PL.DATEI, PL.ORDNER, PL.GRUND = os.path.join(d, "player.json"), os.path.join(d, "p"), os.path.join(d, "p", "basis")
        PL.daten.clear()
        PL.daten.update(PL._leer())
        PL.stand.clear()

    def test_schluessel_wie_agent(self):
        import types
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "player"))
        import agent
        PL = self.PL
        g = PL.neu({"name": "Flur", "tv": "tv"}, {"tv"})
        k = {"id": g["id"], "schluessel": g["schluessel"], "server": "http://x:8890"}
        url = agent.Player.direkt_url(types.SimpleNamespace(server=agent.Server(k), k=k))
        tok = PL.anzeige_schluessel(g)
        self.assertEqual(url, "http://x:8890/anzeige/" + tok)
        self.assertNotIn(g["schluessel"], url)
        self.assertIs(PL.geraet_fuer_anzeige(tok), g)
        self.assertIsNone(PL.geraet_fuer_anzeige("0" * 32))
        self.assertIsNone(PL.geraet_fuer_anzeige(tok + "x"))
        PL.entfernen(g["id"])
        self.assertIsNone(PL.geraet_fuer_anzeige(tok))           # entfernt: Zugang sofort ungültig

    def test_pfade(self):
        ok, PL = self.PL.anzeige_pfad_ok, self.PL
        for p in ("/", "/index.html", "/seite.js", "/daten.json", "/mdi/x.svg", "/hls/hls.light.min.js", "/medien/0123456789abcdef.mp4",
                  "/radio/tv/abcd", "/durchsage/gong.wav", "/kamera/camera.flur.jpg"):
            self.assertTrue(ok(p), p)
        for p in ("/api/einstellungen", "/api/player", "/../etc/passwd", "/a/../b", "//x", "/hlscam/cam_x/index.m3u8", "/a b"):
            self.assertFalse(ok(p), p)
        self.assertTrue(PL.ANZEIGE_MODI)

    def test_modus_je_modell(self):
        PL = self.PL
        g = PL.neu({"name": "A", "tv": "tv", "anzeige_modus": "direkt"}, {"tv"})
        self.assertEqual(PL.modus_fuer(g), "direkt")
        self.assertEqual(PL.modus_fuer(g, {"modell": "Raspberry Pi 3 Model B Rev 1.2"}), "stream")
        self.assertEqual(PL.modus_fuer(g, {"modell": "Raspberry Pi Zero 2 W Rev 1.0"}), "stream")
        a = PL.melden(g, {"modell": "Raspberry Pi 5 Model B Rev 1.0"}, "1.2.3.4", None, None)
        self.assertEqual((a["modus"], a["direkt_abruf"]), ("direkt", None))
        PL.direkt_abruf[g["id"]] = time.time() - 5
        self.assertLessEqual(PL.melden(g, {}, "1.2.3.4", None, None)["direkt_abruf"], 6)
        PL.aendern(g["id"], {"modell": "pi3", "anzeige_modus": "direkt"}, {"tv"})   # Pi 3: immer Stream
        self.assertEqual(g["anzeige_modus"], "stream")
        h = PL.neu({"name": "B"}, set())
        self.assertEqual(h["anzeige_modus"], "stream")                              # Standard bleibt der Stream
        alt = {k: v for k, v in h.items() if k != "anzeige_modus"}                   # Geräte von 0.23 ohne das Feld
        self.assertEqual(PL.modus_fuer(alt), "stream")
        self.assertNotIn("schluessel", json.dumps(PL.liste(lambda g: [])))

    def test_agent_umschalten_und_rueckfall(self):
        """Agent: Direktmodus startet den Browser statt mpv; drei Abstürze -> eine Stunde Stream; „Player neu“ setzt zurück."""
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "player"))
        import agent

        class Falsch:
            def __init__(self):
                self.an, self.gestartet, self.optionen, self.starts, self.url = False, 0, {}, 0, None

            def laeuft(self):
                return self.an

            def starten(self, url, *a, **k):
                self.an, self.gestartet, self.url = True, time.time(), url
                self.starts += 1
                return True

            def beenden(self):
                self.an, self.gestartet = False, 0

        alt_v, alt_m = agent.Browser.verfuegbar, agent.modell
        agent.Browser.verfuegbar, agent.modell = staticmethod(lambda: True), lambda: "Raspberry Pi 5 Model B Rev 1.0"
        try:
            p = agent.Player({"id": "abcd1234", "schluessel": "00" * 32, "server": "http://x:8890", "name": "T"})
            p.anzeige, p.browser = Falsch(), Falsch()
            p.anzeige.an = True
            p.kontakt, p.zustand = time.time(), "spielt"
            p.soll = {"modus": "direkt", "stream": {"port": 8888, "pfad": "tv"}, "direkt_abruf": 3}
            jetzt = time.time()
            self.assertTrue(p.direkt_gewuenscht(jetzt))
            p.direkt_schritt(jetzt)                         # mpv gibt den Bildschirm frei, Browser startet
            self.assertFalse(p.anzeige.an)
            self.assertTrue(p.browser.an and p.browser.url.startswith("http://x:8890/anzeige/"))
            p.direkt_schritt(jetzt)
            self.assertEqual(p.zustand, "direkt")
            for _ in range(3):                              # dreimal abgestürzt
                p.browser.an = False
                p.direkt_schritt(time.time())
                p.direkt_schritt(time.time())               # startet neu
            self.assertEqual(p.rueckfall, "abgestuerzt")
            self.assertFalse(p.direkt_gewuenscht(time.time()))   # eine Stunde Stream
            p.soll["befehle"] = [{"id": "1", "art": "player_neu"}]
            p.befehle()
            self.assertTrue(p.direkt_gewuenscht(time.time()))
            p.soll["befehle"] = []
            p.browser.starten("u")                          # Seite lädt nicht: Server sieht 90 s keine Abrufe
            p.browser.gestartet -= 100
            p.soll["direkt_abruf"] = None
            p.direkt_schritt(time.time())
            self.assertFalse(p.browser.an)
            self.assertEqual(len(p.direkt_fehler), 1)
            p.soll["modus"] = "stream"
            self.assertFalse(p.direkt_gewuenscht(time.time()))
            p.soll["modus"] = "direkt"
            agent.modell = lambda: "Raspberry Pi 3 Model B Plus Rev 1.3"
            self.assertFalse(p.direkt_gewuenscht(time.time()))    # Pi 3: nie direkt
        finally:
            agent.Browser.verfuegbar, agent.modell = alt_v, alt_m


class Kopplung025(unittest.TestCase):
    """Image für mehrere Pis: DH-Kopplung per Code, Grenzen, Sammel-Image; iCal-Prüfung."""
    def setUp(self):
        import player as PL
        self.PL, d = PL, tempfile.mkdtemp()
        PL.DATEI, PL.ORDNER, PL.GRUND = os.path.join(d, "player.json"), os.path.join(d, "p"), os.path.join(d, "p", "basis")
        PL.daten.clear()
        PL.daten.update(PL._leer())
        PL.stand.clear()
        PL.kopplungen.clear()
        PL.koppel_zeiten.clear()
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "player"))
        import agent
        self.agent, self.ordner = agent, d

    def test_gruppe_wie_agent(self):
        self.assertEqual(self.PL.DH_P, self.agent.DH_P)
        self.assertEqual(self.PL.DH_P.bit_length(), 2048)
        self.assertEqual(pow(2, (self.PL.DH_P - 1) // 2, self.PL.DH_P), 1)

    def test_agent_koppelt_sich(self):
        """Agent und Server ganz durch: Code am Fernseher, Eingabe in der Verwaltung, signierte Antwort, Gerätedatei."""
        PL, agent = self.PL, self.agent
        import types

        class Netz:                                    # statt HTTP: direkt an die Server-Funktionen
            def __init__(self, k):
                self.k = k

            def basis(self):
                return "http://x:8890"

            def offen(self, pfad, d, zeit=20):
                if pfad == "/player/koppeln":
                    return 200, json.dumps(PL.koppel_anfrage(d, "192.0.2.7")).encode(), {}
                code, antwort, g = PL.koppel_status(d["kennung"])
                roh = json.dumps(antwort).encode()
                return code, roh, {"X-Signatur": PL.signatur(g, d["zeit"], roh)} if g else {}

        class Bild:
            def __init__(self):
                self.zeilen = []

            def zeigen(self, zeilen, qr=None):
                self.zeilen = zeilen

        kdatei = os.path.join(self.ordner, "signagecast.json")
        k = json.loads(PL.konfig(None, [], "http://x:8890", "de", "Europe/Berlin"))
        self.assertNotIn("schluessel", k)
        self.assertTrue(k["kopplung"])
        alt = agent.KONFIG, agent.modell, agent.schreiben_sicher, agent.lauf
        agent.KONFIG, agent.modell = kdatei, lambda: "Raspberry Pi 4 Model B Rev 1.5"
        agent.schreiben_sicher = lambda pfad, inhalt: open(pfad, "w").write(inhalt)
        agent.lauf = lambda *a, **kw: (0, "")
        try:
            open(kdatei, "w").write(json.dumps(k))
            k2 = agent.konfig_laden()
            self.assertTrue(k2 and k2["kopplung"])
            p = types.SimpleNamespace(k=k2, t=agent.TEXTE["de"], server=Netz(k2), anzeige=Bild(), kopplung=None, koppel_pause=0,
                                      zustand="", zustand_text="", letzte_meldung=1)
            p.koppel_start = types.MethodType(agent.Player.koppel_start, p)
            jetzt = time.time()
            agent.Player.koppel_schritt(p, jetzt)
            code = p.kopplung["code"]
            self.assertEqual(p.anzeige.zeilen[0], f"Code: {code[:3]} {code[3:]}")
            self.assertEqual(len(PL.wartend()), 1)
            self.assertNotIn(code, json.dumps(PL.wartend()))
            falsch = f"{(int(code) + 1) % 1_000_000:06d}"
            with self.assertRaises(M.Meldung) as f:
                PL.koppeln(falsch, {"name": "Flur", "tv": "tv"}, {"tv"})
            self.assertEqual(f.exception.code, "pi_code")
            agent.Player.koppel_schritt(p, jetzt + 6)          # noch nicht eingegeben
            self.assertFalse(p.k.get("schluessel"))
            g = PL.koppeln(code[:3] + " " + code[3:], {"name": "Flur", "tv": "tv"}, {"tv"})
            self.assertEqual(g["modell"], "pi45")
            self.assertEqual(PL.wartend(), [])
            agent.Player.koppel_schritt(p, jetzt + 12)
            self.assertEqual((p.k["id"], p.k["schluessel"], p.k["name"], p.k["hostname"]), (g["id"], g["schluessel"], "Flur", "sc-flur"))
            self.assertNotIn("kopplung", p.k)
            gespeichert = json.load(open(kdatei))
            self.assertEqual(gespeichert["schluessel"], g["schluessel"])
            self.assertIsNotNone(agent.konfig_laden())
            # gekoppelter Pi meldet sich ganz normal signiert
            kopf = {"X-Geraet": g["id"], "X-Zeit": str(int(time.time()))}
            kopf["X-Signatur"] = __import__("hmac").new(bytes.fromhex(p.k["schluessel"]), f"POST\n/player/melden\n{kopf['X-Zeit']}\n".encode() + b"{}", "sha256").hexdigest()
            self.assertEqual(PL.pruefen(kopf, "/player/melden", b"{}")[1], 200)
            with self.assertRaises(M.Meldung):                 # Code nur einmal verwendbar
                PL.koppeln(code, {"name": "Noch einer", "tv": "tv"}, {"tv"})
        finally:
            agent.KONFIG, agent.modell, agent.schreiben_sicher, agent.lauf = alt

    def test_falsche_signatur_wird_ignoriert(self):
        PL, agent = self.PL, self.agent
        import types
        a = 12345678901234567890
        a_pub = pow(2, a, PL.DH_P)
        r = PL.koppel_anfrage({"a": format(a_pub, "x"), "modell": "Raspberry Pi 3 Model B Rev 1.2"}, "192.0.2.8")
        code, schl = agent.dh_ableiten(a, int(r["b"], 16), a_pub, int(r["b"], 16))
        g = PL.koppeln(code, {"name": "Küche"}, set())
        self.assertEqual((g["schluessel"], g["modell"]), (schl, "pi3"))
        status, antwort, gg = PL.koppel_status(r["kennung"])
        self.assertEqual((status, antwort["id"]), (200, g["id"]))
        self.assertEqual(PL.koppel_status("unbekannt")[0], 404)

        class Netz:
            def basis(self):
                return "http://x:8890"

            def offen(self, pfad, d, zeit=20):
                return 200, json.dumps({"ok": True, "id": "deadbeef", "name": "Falle"}).encode(), {"X-Signatur": "0" * 64}

        p = types.SimpleNamespace(k={"kopplung": True, "server": "http://x:8890"}, t=agent.TEXTE["en"], server=Netz(),
                                  anzeige=types.SimpleNamespace(zeigen=lambda *a, **k: None), zustand="", zustand_text="", koppel_pause=0,
                                  kopplung={"kennung": "k", "code": "123456", "schluessel": "11" * 32, "bis": time.time() + 500, "gefragt": 0})
        alt = agent.modell
        agent.modell = lambda: "Pi"
        try:
            agent.Player.koppel_schritt(p, time.time())
        finally:
            agent.modell = alt
        self.assertNotIn("schluessel", p.k)                    # gefälschte Antwort: nichts übernommen

    def test_grenzen(self):
        PL = self.PL
        for x in ("", "zz", "1", format(PL.DH_P - 1, "x"), format(PL.DH_P, "x")):
            with self.assertRaises(M.Meldung):
                PL.koppel_anfrage({"a": x}, "192.0.2.1")
        ausserhalb = next(x for x in range(3, 200) if pow(x, (PL.DH_P - 1) // 2, PL.DH_P) != 1)
        with self.assertRaises(M.Meldung):                     # nicht aus der Untergruppe
            PL.koppel_anfrage({"a": format(ausserhalb, "x")}, "192.0.2.1")
        a_pub = format(pow(2, 99991, PL.DH_P), "x")
        PL.koppel_anfrage({"a": a_pub}, "192.0.2.1")
        PL.koppel_anfrage({"a": a_pub}, "192.0.2.1")           # derselbe Pi fragt neu: alte Anfrage ersetzt
        self.assertEqual(len(PL.wartend()), 1)
        for i in range(2, PL.KOPPEL_OFFEN + 1):
            PL.koppel_anfrage({"a": a_pub}, f"192.0.2.{i}")
        with self.assertRaises(M.Meldung) as f:
            PL.koppel_anfrage({"a": a_pub}, "192.0.2.250")
        self.assertEqual(f.exception.code, "pi_koppel_voll")
        for v in PL.kopplungen.values():                       # abgelaufen: Platz wird frei
            v["bis"] = 0
        PL.koppel_anfrage({"a": a_pub}, "192.0.2.250")
        PL.koppel_zeiten[:] = [time.time()] * PL.KOPPEL_STUNDE  # Grenze je Stunde
        with self.assertRaises(M.Meldung):
            PL.koppel_anfrage({"a": a_pub}, "192.0.2.251")
        self.assertEqual(PL.dateiname(None), "signagecast-player-kopplung.img.gz")
        k1 = json.loads(PL.konfig(None, [], "http://x:8890", "en", ""))
        k2 = json.loads(PL.konfig(None, [], "http://x:8890", "en", ""))
        self.assertEqual(k1["hotspot_pw"], k2["hotspot_pw"])     # ein Hotspot-Passwort für das Sammel-Image

    def test_ical_statt_html(self):
        with self.assertRaises(M.Meldung) as f:
            Q.zerlegen({"art": "ical"}, b"<!DOCTYPE html><html><title>Login</title></html>", "text/html; charset=utf-8")
        self.assertEqual(f.exception.code, "kein_ical")
        r = Q.zerlegen({"art": "ical"}, "\ufeffBEGIN:VCALENDAR\r\nX-WR-CALNAME:Test\r\nEND:VCALENDAR\r\n".encode(), "text/calendar")
        self.assertEqual(r["kalender"], "Test")


class Csv026(unittest.TestCase):
    """Seit 0.26: allgemeiner CSV-Import, Datenquellen aus hochgeladenen Dateien, CSV als Termine für den Kalender."""
    ROH = ("ORT,ORTSTEIL,STANDORT,FRAKTION,TERMIN\n"
           "Musterstadt,Hauptstr. ,,Restmüll,Mi 07.01.2026\n"
           "Musterstadt,Hauptstr. ,Wertstoffhof; Ringstraße 1,Problemmüll,Sa 07.03.2026\n"
           "\n"
           "Musterstadt,Hauptstr. ,,Papiertonne,Do 08.01.2026\n")

    def test_analysieren_erkennt_und_liest_windows_csv(self):
        import csvimport as C
        zitiert = self.ROH.replace("Wertstoffhof; Ringstraße 1", '"Wertstoffhof; Ringstraße 1"')
        for roh, trenner in ((self.ROH.encode("cp1252"), ","), (zitiert.replace(",", ";").encode(), ";"),
                             (zitiert.replace(",", "\t").encode("utf-8-sig"), "tab")):
            a = C.analysieren(roh)
            self.assertEqual((a["optionen"]["trenner"], a["optionen"]["kopfzeile"], a["zeilen"]), (trenner, True, 3))
            self.assertEqual([s["name"] for s in a["spalten"]], ["ORT", "ORTSTEIL", "STANDORT", "FRAKTION", "TERMIN"])
            self.assertEqual(a["spalten"][3]["beispiele"][0], "Restmüll")
        z = C.lesen(self.ROH.encode(), {"trenner": ",", "felder": [{"spalte": 3, "name": "Art"}, {"spalte": 4, "name": "Wann"}]})
        self.assertEqual(z[1], {"Art": "Problemmüll", "Wann": "Sa 07.03.2026"})
        self.assertEqual(len(C.lesen(self.ROH.encode(), {"trenner": ","})[0]), 5)          # ohne Auswahl alle Spalten
        mit = C.lesen(b'Name;Wert\n"M\xc3\xbcller; Hans";"3"\n', {"trenner": ";"})
        self.assertEqual(mit, [{"Name": "Müller; Hans", "Wert": "3"}])
        ohne = C.lesen(b'a;b\n"x;y\n', {"trenner": ";", "anfuehrung": ""})
        self.assertEqual(ohne, [{"a": '"x', "b": "y"}])
        self.assertEqual(C.analysieren(b"1,2\n3,4\n")["spalten"][0]["name"], "Spalte 1")
        for falsch in ({"trenner": "x"}, {"anfuehrung": "*"}, {"kodierung": "ebcdic"}, {"felder": [{"spalte": 0, "name": ""}]},
                       {"felder": [{"spalte": 0, "name": "a"}, {"spalte": 1, "name": "a"}]}):
            with self.assertRaises(M.Meldung):
                C.optionen_pruefen(falsch)
        with self.assertRaises(M.Meldung):
            C.analysieren(b"\n \n")

    def test_datum_und_zeit(self):
        import csvimport as C
        d = datetime.date
        self.assertEqual([C.datum_finden(s) for s in ("Mi 07.01.2026", "2026-01-07", "7.1.26", "07/01/2026", "31.02.2026", "")],
                         [d(2026, 1, 7)] * 4 + [None, None])
        self.assertEqual(C.zeit_finden("Mi 07.01.2026 18:30 Uhr"), datetime.time(18, 30))
        self.assertIsNone(C.zeit_finden("07.01.2026"))

    def test_quelle_aus_datei_mit_terminen(self):
        heute = datetime.date.today()
        tag = lambda n: (heute + datetime.timedelta(days=n)).strftime("%a %d.%m.%Y")
        roh = (f"FRAKTION;TERMIN;ORT\nRestmüll;{tag(-3)};\nBiotonne;{tag(5)};Hof\nPapier;{tag(1)} 07:30;\nkaputt;irgendwann;\n").encode("cp1252")
        alt = Q.DATEIEN
        with tempfile.TemporaryDirectory() as d:
            Q.DATEIEN = d
            try:
                self.assertEqual(Q.datei_art(roh, "abfuhr.csv"), "csv")
                self.assertEqual(Q.datei_art(b"BEGIN:VCALENDAR\r\nEND:VCALENDAR", "x.ics"), "ical")
                h = Q.datei_ablegen(roh)
                self.assertEqual(Q.datei_ablegen(roh), h)
                q = Q.pruefen([{"id": "muell", "art": "csv", "herkunft": "datei", "datei": {"hash": h, "name": "abfuhr.csv"}, "url": "egal",
                                "csv": {"trenner": ";", "felder": [{"spalte": 0, "name": "Art"}, {"spalte": 1, "name": "Datum"}, {"spalte": 2, "name": "Ort"}],
                                        "kalender": {"datum": "Datum", "titel": "Art", "ort": "Ort"}}}])[0]
                self.assertEqual((q["url"], q["herkunft"], q["csv"]["kalender"]["datum"]), ("", "datei", "Datum"))
                daten, _ = Q.Quellen(lambda: {}).abrufen(q)
                self.assertEqual(len(daten["zeilen"]), 4)
                self.assertEqual([t["titel"] for t in daten["termine"]], ["Papier", "Biotonne"])     # vergangene fallen weg, sortiert
                self.assertFalse(daten["termine"][0]["ganztag"])
                self.assertEqual((daten["termine"][1]["start"], daten["termine"][1]["ort"]), ((heute + datetime.timedelta(days=5)).isoformat(), "Hof"))
                # Kalender-Baustein zeigt CSV-Termine wie iCal
                class Qn:
                    stand, verlauf = {}, None
                    daten = staticmethod(lambda qid: daten if qid == "muell" else None)
                api, _ = Q.baustein_werte({"elemente": [{"id": "k", "typ": "kalender", "optionen": {"quelle": "muell", "tage": 3, "anzahl": 4}}]},
                                          Qn, "de", [q])
                self.assertEqual([t["titel"] for t in api["k"]["termine"]], ["Papier"])
                with self.assertRaises(M.Meldung) as f:
                    Q.csv_zerlegen(roh, dict(q["csv"], kalender={"datum": "Art"}))
                self.assertEqual(f.exception.code, "csv_kein_datum")
                for falsch in ({"datei": {"hash": "../etc/passwd"}}, {"art": "bild"}, {"csv": {"trenner": ";"}}):
                    with self.assertRaises(M.Meldung):
                        Q.pruefen([dict({"id": "muell", "art": "csv", "herkunft": "datei", "datei": {"hash": h},
                                         "csv": {"felder": [{"spalte": 0, "name": "a"}]}}, **falsch)])
                os.utime(os.path.join(d, h), (1, 1))
                Q.dateien_aufraeumen({h})
                self.assertTrue(os.path.exists(os.path.join(d, h)))
                Q.dateien_aufraeumen(set())
                self.assertFalse(os.path.exists(os.path.join(d, h)))
                with self.assertRaises(M.Meldung):
                    Q.datei_lesen(h)
            finally:
                Q.DATEIEN = alt

    def test_kalender_nur_mit_terminen(self):                      # seit 0.26.1
        el = {"id": "k", "typ": "kalender", "optionen": {"quelle": "muell", "tage": 3}}
        self.assertFalse(L.pruefe_layout({"id": "ab", "elemente": [el]})["elemente"][0]["optionen"]["nur_mit_terminen"])
        el["optionen"]["nur_mit_terminen"] = True
        self.assertTrue(L.pruefe_layout({"id": "ab", "elemente": [el]})["elemente"][0]["optionen"]["nur_mit_terminen"])
        js = open(os.path.join(os.path.dirname(__file__), "..", "www", "seite.js"), encoding="utf-8").read()
        self.assertIn("termine.length > 0 || !o.nur_mit_terminen", js)

    def test_alte_quellen_bleiben_gueltig(self):
        q = Q.pruefen([{"id": "news", "art": "rss", "url": "https://example.org/rss"}])[0]
        self.assertEqual((q["herkunft"], "datei" in q, "csv" in q), ("url", False, False))



class CsvFilter027(unittest.TestCase):
    """Seit 0.27: Zeilenfilter im CSV-Import (alle Regeln müssen zutreffen), auch für die Termine des Kalenders."""
    ROH = Csv026.ROH

    def test_regeln(self):
        import csvimport as C
        z = {"STANDORT": " ", "FRAKTION": "Restmüll"}
        self.assertTrue(C.passt(z, [{"feld": "STANDORT", "regel": "leer", "wert": ""}]))
        self.assertTrue(C.passt(z, [{"feld": "FRAKTION", "regel": "enthaelt", "wert": "rest"}]))
        self.assertFalse(C.passt(z, [{"feld": "FRAKTION", "regel": "enthaelt_nicht", "wert": "MÜLL"}]))
        self.assertTrue(C.passt(z, [{"feld": "FRAKTION", "regel": "gleich", "wert": " restmüll "},
                                    {"feld": "STANDORT", "regel": "ungleich", "wert": "x"}]))
        self.assertFalse(C.passt(z, [{"feld": "STANDORT", "regel": "nicht_leer", "wert": ""}]))
        with self.assertRaises(Exception):
            C.filter_pruefen([{"feld": "FRAKTION", "regel": "ungefähr"}])
        with self.assertRaises(Exception):
            C.optionen_pruefen({"felder": [{"spalte": 3, "name": "FRAKTION"}], "filter": [{"feld": "ORT", "regel": "leer"}]})
        self.assertEqual(C.filter_pruefen([{"feld": "A", "regel": "leer", "wert": "weg"}])[0]["wert"], "")

    def test_lesen_und_analysieren_mit_filter(self):
        import csvimport as C
        o = {"trenner": ",", "anfuehrung": '"', "kopfzeile": True, "kodierung": "auto",
             "felder": [{"spalte": 2, "name": "STANDORT"}, {"spalte": 3, "name": "FRAKTION"}, {"spalte": 4, "name": "TERMIN"}],
             "filter": [{"feld": "STANDORT", "regel": "leer", "wert": ""}]}
        self.assertEqual([z["FRAKTION"] for z in C.lesen(self.ROH.encode(), o)], ["Restmüll", "Papiertonne"])
        a = C.analysieren(self.ROH.encode(), o)
        self.assertEqual((a["zeilen"], a["treffer"], len(a["vorschau"])), (3, 2, 2))
        a = C.analysieren(self.ROH.encode(), dict(o, filter=[{"feld": "GIBTSNICHT", "regel": "leer"}]))
        self.assertNotIn("treffer", a)                       # unbekanntes Feld zählt in der Vorschau nicht
        self.assertNotIn("treffer", C.analysieren(self.ROH.encode(), {}))

    def test_termine_gefiltert(self):
        import datetime
        heute = datetime.date.today()
        roh = "".join(f"Musterstadt,{'Wertstoffhof' if i % 2 else ''},{'Sperrmüll' if i % 2 else 'Restmüll'},"
                      f"{(heute + datetime.timedelta(days=i)).strftime('%d.%m.%Y')}\n" for i in range(1, 5))
        o = {"trenner": ",", "anfuehrung": '"', "kopfzeile": False, "kodierung": "auto",
             "felder": [{"spalte": 1, "name": "STANDORT"}, {"spalte": 2, "name": "FRAKTION"}, {"spalte": 3, "name": "TERMIN"}],
             "filter": [{"feld": "STANDORT", "regel": "leer"}], "kalender": {"datum": "TERMIN", "titel": "FRAKTION"}}
        q = Q.pruefen([{"id": "muell", "art": "csv", "herkunft": "datei", "datei": {"hash": "0123456789abcdef", "name": "a.csv"}, "csv": o}])[0]
        self.assertEqual(q["csv"]["filter"], [{"feld": "STANDORT", "regel": "leer", "wert": ""}])
        d = Q.csv_zerlegen(roh.encode(), q["csv"])
        self.assertEqual([t["titel"] for t in d["termine"]], ["Restmüll", "Restmüll"])
        self.assertEqual(Q.pruefen([{"id": "alt", "art": "csv", "herkunft": "datei", "datei": {"hash": "0123456789abcdef", "name": "a.csv"},
                                     "csv": dict(o, filter=None)}])[0]["csv"]["filter"], [])

    def test_verwaltung_hat_filter(self):
        js = open(os.path.join(os.path.dirname(__file__), "..", "cockpit", "signagecast", "csvimport.js"), encoding="utf-8").read()
        for s in ("cFNeu", "cFFeld", "cFRegel", "cFWert", "filterBereinigen", "enthaelt_nicht"):
            self.assertIn(s, js)



class KalenderSymbole028(unittest.TestCase):
    """Seit 0.28: Kalender-Baustein als reine Symbole (z. B. Mülltonne), Regeln „Titel enthält“ -> Symbol/Farbe."""

    def el(self, **o):
        return L.pruefe_layout({"id": "ab", "elemente": [{"id": "m", "typ": "kalender", "x": 46, "y": 0, "w": 2, "h": 2, "optionen": o}]})["elemente"][0]

    def test_standard_bleibt_liste(self):
        e = self.el(quelle="muell")
        self.assertEqual((e["optionen"]["ansicht"], e["optionen"]["symbole"], e["optionen"]["ohne_symbol"], e["optionen"]["wann"]),
                         ("liste", [], "mdi-calendar", True))
        self.assertEqual((e["w"], e["h"]), (6, 3))                 # Liste: Mindestgröße wie bisher

    def test_symbole_pruefen(self):
        e = self.el(quelle="muell", ansicht="symbole", ohne_symbol="", symbole=[
            {"text": " Rest ", "icon": "mdi-trash-can", "farbe": "#9e9e9e"}, {"text": "", "icon": "mdi-leaf"},
            {"text": "Bio", "icon": "", "farbe": ""}])
        self.assertEqual(e["optionen"]["symbole"], [{"text": "Rest", "icon": "mdi-trash-can", "farbe": "#9e9e9e"},
                                                     {"text": "Bio", "icon": "mdi-calendar", "farbe": ""}])
        self.assertEqual(e["optionen"]["ohne_symbol"], "")
        self.assertEqual((e["x"], e["w"], e["h"]), (46, 2, 2))   # Symbol darf klein in die Ecke
        for falsch in ({"ansicht": "kacheln"}, {"symbole": [{"text": "x", "icon": "fa-trash"}]}, {"symbole": [{"text": "x", "farbe": "rot"}]}):
            with self.assertRaises(Exception):
                self.el(**falsch)
        self.assertEqual(len(self.el(symbole=[{"text": str(i)} for i in range(20)])["optionen"]["symbole"]), 12)

    def test_seite_und_verwaltung(self):
        basis = os.path.join(os.path.dirname(__file__), "..")
        js = open(os.path.join(basis, "www", "seite.js"), encoding="utf-8").read()
        for s in ('o.ansicht === "symbole"', "gesehen.has(icon + farbe)", "o.ohne_symbol"):
            self.assertIn(s, js)
        lj = open(os.path.join(basis, "cockpit", "signagecast", "layout.js"), encoding="utf-8").read()
        for s in ("symListe", "symVorlage", "SYM_VORSCHLAG", 'ansicht: ["liste", "symbole"]'):
            self.assertIn(s, lj)
        css = open(os.path.join(basis, "www", "mdi", "css", "materialdesignicons.min.css"), encoding="utf-8").read()
        import re
        for icon in re.findall(r'"(mdi-[a-z0-9-]+)"', lj[lj.index("SYM_VORSCHLAG"):lj.index("const QUELL_ARTEN")]):
            self.assertIn("." + icon + ":", css, icon)       # alle Vorschläge gibt es in der eingebauten Schrift



class NeuLaden0281(unittest.TestCase):
    """Seit 0.28.1: TV-Seite lädt nach einem Update neu; statische Dateien mit Cache-Control: no-cache."""

    def test_seite_vergleicht_version(self):
        basis = os.path.join(os.path.dirname(__file__), "..")
        js = open(os.path.join(basis, "www", "seite.js"), encoding="utf-8").read()
        self.assertIn("d.version !== seitenVersion", js)
        py = open(os.path.join(basis, "app", "dienst.py"), encoding="utf-8").read()
        self.assertIn("version=VERSION,", py[py.index("def tv_daten"):])
        self.assertIn('super().send_header("Cache-Control", "no-cache")', py)



class Leistung(unittest.TestCase):
    """Seit 0.29: Aufnahmegröße je Fernseher, Standard Full HD, Durchsagen per Long-Polling, Chromium ohne llvmpipe."""

    def test_aufnahme_und_standard(self):
        t = E.pruefen({})["fernseher"][0]
        self.assertEqual((t["aufloesung"], t["aufnahme"], t["bitrate_mbit"]), (1080, 1080, 8))
        self.assertEqual(E.pruefen({"fernseher": [{"id": "tv", "aufnahme": 720}]})["fernseher"][0]["aufnahme"], 720)
        with self.assertRaises(E.Fehler) as f:
            E.pruefen({"fernseher": [{"id": "tv", "aufnahme": 2160}]})
        self.assertEqual(f.exception.code, "e_aufnahme")
        self.assertIn("e_aufnahme", M.DE)

    def test_render_skript(self):
        basis = os.path.join(os.path.dirname(__file__), "..")
        sh = open(os.path.join(basis, "render", "tv-render.sh"), encoding="utf-8").read()
        for x in ('W=${AUFNAHME% *}', "--force-device-scale-factor=$FAKTOR", 'GPU=an', "--disable-background-networking"):
            self.assertIn(x, sh)
        py = open(os.path.join(basis, "app", "dienst.py"), encoding="utf-8").read()
        self.assertIn('f"AUFNAHME=\\"{aw} {ah}\\"\\n"', py)
        self.assertIn("ds_melden()", py[py.index("def alarm_beenden"):py.index("def alarm_fuer")])
        erw = open(os.path.join(basis, "render", "h264-fluessig", "inhalt.js"), encoding="utf-8").read()
        for x in ("MediaSource.isTypeSupported = ", "canPlayType = ", "av01"):
            self.assertIn(x, erw)                     # seit 0.29.1: VP9/AV1 gar nicht anbieten
        js = open(os.path.join(basis, "www", "seite.js"), encoding="utf-8").read()
        self.assertIn('"&stand="', js)
        self.assertNotIn("}, 2000);", js[js.index("durchsagenHolen") - 300:])



class Sbom(unittest.TestCase):
    """Seit 0.30: SBOM (CycloneDX) aus werkzeug/komponenten.json – muss zu NOTICE.md und den Installationsskripten passen."""
    BASIS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

    def lesen(self, *p):
        return open(os.path.join(self.BASIS, *p), encoding="utf-8").read()

    def test_komponenten_wie_notice_und_skripte(self):
        k = {x["id"]: x for x in json.loads(self.lesen("werkzeug", "komponenten.json"))["komponenten"]}
        notice = self.lesen("NOTICE.md")
        for x in k.values():
            self.assertIn(x["version"], notice, x["name"])
            for p in x["pfade"]:
                self.assertTrue(os.path.exists(os.path.join(self.BASIS, p)), p)
        mtx = k["mediamtx"]["version"]
        self.assertIn(f"MTX_VERSION={mtx}", self.lesen("installieren.sh"))
        self.assertIn(f"ARG MTX_VERSION={mtx}", self.lesen("Dockerfile"))
        self.assertIn(f'"{k["hlsjs"]["version"]}"', self.lesen("www", "hls", "hls.light.min.js"))
        self.assertIn(f'v={k["mdi"]["version"]}', self.lesen("www", "mdi", "css", "materialdesignicons.min.css"))

    def test_paket_sbom(self):
        sys.path.insert(0, os.path.join(self.BASIS, "werkzeug"))
        import sbom
        b = sbom.paket("9.9.9", None)
        self.assertEqual((b["bomFormat"], b["specVersion"]), ("CycloneDX", "1.5"))
        namen = {c["name"] for c in b["components"]}
        for n in ("MediaMTX", "hls.js", "chromium", "ffmpeg", "cockpit-ws"):
            self.assertIn(n, namen)
        self.assertTrue(all(c.get("hashes") for c in b["components"] if c["bom-ref"] in ("mdi", "qrcode", "hlsjs")))
        self.assertEqual(len({c["bom-ref"] for c in b["components"]}), len(b["components"]))
        self.assertEqual(sbom.paket("9.9.9", None)["serialNumber"], b["serialNumber"])        # wiederholbar

    def test_pi_sbom(self):
        sys.path.insert(0, os.path.join(self.BASIS, "werkzeug"))
        import sbom
        with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False) as f:
            f.write("mpv\t0.35.1-4\tarm64\t\nlibc6\t2.36-9+rpt2\tarm64\tglibc\nlibc6\t2.36-9+rpt2\tarm64\tglibc\n")
        b = sbom.pi("9.9.9", f.name, "raspios.img.xz")
        os.unlink(f.name)
        self.assertEqual([c["name"] for c in b["components"]], ["libc6", "mpv"])
        self.assertEqual(b["components"][0]["purl"], "pkg:deb/debian/libc6@2.36-9+rpt2?arch=arm64&distro=debian-13")

    def test_player_quelle_ignoriert_sbom(self):
        self.assertIn('not n.endswith(".cdx.json")', self.lesen("app", "player.py"))


class Streamliste(unittest.TestCase):
    """Seit 0.31: Nachtliste mit „hell ab“, Vorabprüfung, Grenze nur für Tag-Streams (ohne YouTube)."""
    MORGEN = calendar.timegm((2026, 3, 20, 5, 0, 0))      # Äquinoktium, am Ort 0°/0° kurz vor Sonnenaufgang
    ABEND = calendar.timegm((2026, 3, 20, 18, 5, 0))      # gerade unter 3° gesunken

    def setUp(self):
        self.e = E.pruefen({})
        self.s = ST.Streams(lambda: self.e)

    def strom(self, **k):
        return dict({"art": "video", "name": "x", "kategorie": "neu", "breite": 0.0, "laenge": 0.0, "aktiv": True}, **k)

    def test_hell_ab_minutengenau(self):
        h = ST.hell_ab(0, 0, 3, self.MORGEN)
        self.assertGreater(h, self.MORGEN + 3600)
        self.assertGreaterEqual(ST.sonnenhoehe(0, 0, h), 3)
        self.assertLess(ST.sonnenhoehe(0, 0, h - 60), 3)
        self.assertEqual(ST.hell_ab(0, 0, 3, self.MORGEN + 6 * 3600), self.MORGEN + 6 * 3600)   # schon Tag
        self.assertIsNone(ST.hell_ab(89.9, 0, 3, calendar.timegm((2026, 12, 21, 12, 0, 0))))   # Polarnacht

    def test_angebotene_aufloesung(self):
        seite = 'x var ytInitialPlayerResponse = {"streamingData": {"adaptiveFormats": [{"height": 480}, {"height": 1080}, ' \
                '{"mimeType": "audio/mp4"}]}};var meta = {};'
        self.assertEqual(ST.angebotene_hoehe(seite), 1080)
        self.assertIsNone(ST.angebotene_hoehe("kaputt"))
        self.assertIsNone(ST.angebotene_hoehe("ytInitialPlayerResponse = {nicht json"))
        self.assertEqual([ST.stufe_aus_hoehe(h) for h in (2160, 1080, 720, 480, 144, None)],
                         ["hd2160", "hd1080", "hd720", "large", "tiny", None])

    def test_zustaende(self):
        tag = self.MORGEN + 6 * 3600
        qc = {"a": {"video_id": "a", "live": True, "hoehe": 1080, "geprueft": tag},
              "q": {"video_id": "q", "live": True, "hoehe": 480, "geprueft": tag},
              "n": {"video_id": "n", "live": False, "geprueft": tag}}
        st = {"p": {"strikes": 1, "zeit": tag - 600}, "g": {"strikes": 3}}
        z = lambda sid, s, t=tag: self.s._zustand(sid, s, self.e, qc, st, t)[0]
        self.assertEqual(z("a", self.strom()), "bereit")
        self.assertEqual(z("q", self.strom()), "qualitaet")
        self.assertEqual(z("q", self.strom(geschuetzt=True)), "bereit")
        self.assertEqual(z("n", self.strom()), "nicht_live")
        self.assertEqual(z("p", self.strom()), "pause")
        self.assertEqual(z("p", self.strom(), tag + 3 * 3600), "bereit")          # Pause (sperre_h 2) vorbei
        self.assertEqual(z("g", self.strom()), "gesperrt")
        self.assertEqual(z("a", self.strom(breite=None, laenge=None)), "ohne_ort")
        self.assertEqual(z("k", self.strom(art="kanal")), "ungeprueft")
        self.assertEqual(z("a", self.strom(aktiv=False)), "inaktiv")
        zn, an = self.s._zustand("a", self.strom(), self.e, qc, st, self.MORGEN)
        self.assertEqual((zn, an["nachlauf"]), ("nacht", False))
        self.assertGreater(an["hell_ab"], self.MORGEN)
        self.assertTrue(self.s._zustand("a", self.strom(), self.e, qc, st, self.ABEND)[1]["nachlauf"])
        self.assertFalse(self.s._zustand("q", self.strom(), self.e, qc, st, self.ABEND)[1]["nachlauf"])  # war nicht bereit

    def test_pruefplan_vorrang(self):
        jetzt = calendar.timegm((2026, 3, 20, 6, 0, 0))        # 0°/0°: in ~20 min hell; 90°O: Tag; 90°W: Nacht
        d = {"streams": {"bald": self.strom(), "tag": self.strom(laenge=90.0), "frisch": self.strom(laenge=90.0),
                         "nacht": self.strom(laenge=-90.0), "nacht_frisch": self.strom(laenge=-90.0),
                         "ohne": self.strom(breite=None, laenge=None)}}
        qc = {"bald": {"geprueft": jetzt - 3600}, "tag": {"geprueft": jetzt - 3 * 3600}, "frisch": {"geprueft": jetzt - 60},
              "nacht": {"geprueft": jetzt - 7 * 3600}, "nacht_frisch": {"geprueft": jetzt - 3600}}
        self.assertEqual([sid for sid, _ in self.s._pruefplan(d, self.e, qc, jetzt)], ["bald", "tag", "nacht"])

    def test_grenze_zaehlt_nur_tag(self):
        tag = self.MORGEN + 6 * 3600
        st = {f"t{i}": self.strom(herkunft="entdeckt", zuletzt_gefunden=f"2026-03-1{i}") for i in range(3)}
        st.update({f"n{i}": self.strom(laenge=180.0, herkunft="entdeckt", zuletzt_gefunden=f"2026-03-0{i + 1}") for i in range(2)})
        st["o"] = self.strom(breite=None, laenge=None, herkunft="entdeckt", zuletzt_gefunden="2026-03-19")
        st["f"] = self.strom(laenge=90.0, herkunft="fest")
        self.assertEqual(ST.Streams.ueberzaehlig(st, 2, self.e["video"], tag), ["t0"])   # Nacht/ohne Ort zählen nicht
        alt = ST.MAX_GEFUNDEN_GESAMT
        try:
            ST.MAX_GEFUNDEN_GESAMT = 4
            # 6 gefundene, höchstens 4: zuerst der ohne Ort, dann der am längsten nicht mehr gefundene
            self.assertEqual(sorted(ST.Streams.ueberzaehlig(st, 10, self.e["video"], tag)), ["n0", "o"])
        finally:
            ST.MAX_GEFUNDEN_GESAMT = alt

    def test_vorabpruefung(self):
        jetzt = time.time()
        ST.schreib(ST.STREAMS, {"streams": {"aaaaaaaaaaa": self.strom(), "bbbbbbbbbbb": self.strom()}, "abgelehnt": []})
        ST.schreib(ST.CACHE, {"quellen": {"aaaaaaaaaaa": {"video_id": "aaaaaaaaaaa", "live": True, "geprueft": jetzt - 60},
                                          "bbbbbbbbbbb": {"video_id": "bbbbbbbbbbb", "live": True, "geprueft": jetzt - 3600}}})
        gesehen = []
        self.s._pruefen = lambda a: gesehen.extend(sid for sid, _ in a) or len(a)
        self.assertFalse(self.s.vormerken(["kaputt", 5]))
        self.assertTrue(self.s.vormerken(["aaaaaaaaaaa", "bbbbbbbbbbb"]))
        self.assertEqual(self.s.vorpruefen(), 1)
        self.assertEqual(gesehen, ["bbbbbbbbbbb"])                   # frisch geprüfte nicht noch einmal
        self.s.vor_zeiten = [time.time()] * ST.VOR_MAX                # Grenze je 5 min erreicht
        self.s.vormerken(["bbbbbbbbbbb"])
        self.assertEqual(self.s.vorpruefen(), 0)

    def test_liste_nur_bereit_und_nachlauf(self):
        ST.schreib(ST.STREAMS, {"streams": {"aaaaaaaaaaa": self.strom(), "bbbbbbbbbbb": self.strom(breite=None, laenge=None)},
                                "abgelehnt": []})
        ST.schreib(ST.CACHE, {"quellen": {"aaaaaaaaaaa": {"video_id": "aaaaaaaaaaa", "live": True, "hoehe": 1080, "geprueft": 1}}})
        alt = ST.time.time
        try:
            ST.time.time = lambda: self.ABEND
            l = self.s.liste_bauen()
            self.assertEqual([(x["video_id"], x["nachlauf"]) for x in l], [("aaaaaaaaaaa", True)])
            ST.time.time = lambda: self.ABEND + 3600
            self.assertEqual(self.s.liste_bauen(), [])
            self.assertEqual(self.s.zustaende["bbbbbbbbbbb"]["zustand"], "ohne_ort")
        finally:
            ST.time.time = alt


class Allgemein0311(unittest.TestCase):
    """Seit 0.31.1: allgemeine Störung – Strikes der Serie zurücknehmen, währenddessen keine neuen."""

    def setUp(self):
        self.e = E.pruefen({})
        self.s = ST.Streams(lambda: self.e)
        ST.schreib(ST.STREAMS, {"streams": {}, "abgelehnt": []})
        ST.schreib(ST.STRIKES, {"ccccccccccc": {"strikes": 1, "gruende": ["2026-10-01 10:00 puffert"]}})

    def test_serie_zuruecknehmen(self):
        for v in ("aaaaaaaaaaa", "bbbbbbbbbbb"):
            self.assertTrue(self.s.strike(v, "aufloesung"))
        self.assertTrue(self.s.strike("ddddddddddd", "puffert"))
        self.assertFalse(self.s.allgemein_melden("quatsch"))
        self.assertTrue(self.s.allgemein_melden("aufloesung"))
        st = self.s.strikes()
        for v in ("aaaaaaaaaaa", "bbbbbbbbbbb"):
            self.assertEqual(st[v]["strikes"], 0)
            self.assertNotIn("zeit", st[v])                            # keine Pause mehr
            self.assertTrue(st[v]["gruende"][-1].endswith("aufloesung (allgemein)"))
        self.assertEqual(st["ddddddddddd"]["strikes"], 1)               # anderer Grund bleibt
        self.assertEqual(st["ccccccccccc"]["strikes"], 1)               # alter Strike bleibt
        self.assertEqual(self.s.allgemein_aktiv()["grund"], "aufloesung")
        # währenddessen zählt derselbe Grund nicht, ein anderer schon
        self.s.strike("eeeeeeeeeee", "aufloesung")
        self.s.strike("fffffffffff", "steht")
        st = self.s.strikes()
        self.assertEqual(st["eeeeeeeeeee"]["strikes"], 0)
        self.assertTrue(st["eeeeeeeeeee"]["gruende"][-1].endswith("(allgemein)"))
        self.assertEqual(st["fffffffffff"]["strikes"], 1)
        # erneute Meldung nimmt nichts doppelt zurück
        self.s.allgemein_melden("aufloesung")
        self.assertEqual(self.s.strikes()["ddddddddddd"]["strikes"], 1)
        self.assertTrue(self.s.allgemein_melden("aufloesung", ende=True))
        self.assertIsNone(self.s.allgemein_aktiv())

    def test_wache_beendet(self):
        self.s.allgemein_melden("aufloesung")
        m = {"id": "aaaaaaaaaaa", "zustand": 1, "stufe": "medium"}
        self.s.wache_melden(m, None)
        self.assertIsNotNone(self.s.allgemein_aktiv())               # 360p: weiter gestört
        self.s.wache_melden(dict(m, stufe="hd1080"), None)
        self.assertIsNotNone(self.s.allgemein_aktiv())               # gut, aber noch keine Minute
        self.s.allgemein["gut_seit"] -= ST.ALLGEMEIN_GUT_S
        self.s.wache_melden(dict(m, stufe="hd1080"), None)
        self.assertIsNone(self.s.allgemein_aktiv())

    def test_ohne_meldung_vorbei(self):
        self.s.allgemein_melden("puffert")
        self.s.allgemein["zeit"] -= ST.ALLGEMEIN_GUELTIG_S + 1
        self.assertIsNone(self.s.allgemein_aktiv())
        self.s.strike("aaaaaaaaaaa", "puffert")
        self.assertEqual(self.s.strikes()["aaaaaaaaaaa"]["strikes"], 1)


class OhneGlobalenVideoschalter0311(unittest.TestCase):
    def test_aus_gilt_fuer_jeden_fernseher(self):
        s = E.pruefen({"video": {"aktiv": False}, "fernseher": [{"id": "tv", "video": True}, {"id": "tv2", "video": True}]})
        self.assertTrue(s["video"]["aktiv"])
        self.assertEqual([t["video"] for t in s["fernseher"]], [False, False])
        s = E.pruefen({"fernseher": [{"id": "tv", "video": True}]})
        self.assertEqual([t["video"] for t in s["fernseher"]], [True])


class Themen032(unittest.TestCase):
    """Seit 0.32: Themen ohne Tiere – neu bei bestehenden Installationen aus, eigene Suche, Weltraum ohne Tag/Nacht."""

    def setUp(self):
        self.e = E.pruefen({})
        self.s = ST.Streams(lambda: self.e)

    def test_neue_kategorien_bei_alter_installation_aus(self):
        self.assertEqual(E.pruefen({})["video"]["kategorien_aus"], [])                 # neue Installation: alles an
        alt = E.pruefen({"video": {"takt_min": 3, "kategorien_aus": ["affen"]}})      # von vor 0.32
        self.assertEqual(alt["video"]["kategorien_aus"], ["affen"] + E.THEMEN_KATEGORIEN)
        alt["video"]["kategorien_aus"].remove("stadt")                                # Nutzer schaltet Städte ein
        self.assertNotIn("stadt", E.pruefen(alt)["video"]["kategorien_aus"])           # bleibt an
        self.assertEqual(set(ST.THEMEN), set(E.THEMEN_KATEGORIEN))

    def test_suche_je_thema(self):
        self.e["video"]["kategorien_aus"] = ["bahn"]
        ST.schreib(ST.STREAMS, {"streams": {}, "abgelehnt": []})
        ST.schreib(ST.STRIKES, {})
        ST.schreib(ST.CACHE, {"quellen": {}, "pause_bis": 0})
        gefragt = []
        treffer = {"times square live cam": [("aaaaaaaaaaa", "Times Square LIVE cam New York"),
                                             ("bbbbbbbbbbb", "lofi city beats radio")],
                   "iss live earth from space": [("ccccccccccc", "ISS Live – Earth from space")],
                   "waterhole live cam": [("ddddddddddd", "Waterhole cam Kruger")]}
        def suche(b):
            gefragt.append(b)
            return treffer.get(b, [])
        self.s._suche = suche
        alt = ST.oembed
        try:
            ST.oembed = lambda vid: True
            self.s.suchen()
        finally:
            ST.oembed = alt
        d = self.s.alle()["streams"]
        self.assertEqual(d["aaaaaaaaaaa"]["kategorie"], "stadt")
        self.assertIsNotNone(d["aaaaaaaaaaa"]["breite"])                               # Ort aus der Liste der Einstellungen
        self.assertEqual(self.s.ort("Maho Beach St Maarten LIVE"), (18.04, -63.12))     # Themen-Orte danach
        self.assertNotIn("bbbbbbbbbbb", d)                                             # Musik aussortiert
        self.assertEqual(d["ccccccccccc"]["kategorie"], "weltraum")
        self.assertEqual(d["ddddddddddd"]["kategorie"], "neu")
        self.assertFalse(any(b in gefragt for b in ST.THEMEN["bahn"]["begriffe"]))     # ausgeschaltet: keine Anfragen

    def test_weltraum_ohne_ort_und_nacht(self):
        jetzt = time.time()
        ST.schreib(ST.STREAMS, {"streams": {"ccccccccccc": {"art": "video", "name": "ISS", "kategorie": "weltraum",
                                                            "breite": None, "laenge": None, "aktiv": True}}, "abgelehnt": []})
        ST.schreib(ST.CACHE, {"quellen": {"ccccccccccc": {"video_id": "ccccccccccc", "live": True, "hoehe": 1080, "geprueft": jetzt}}})
        ST.schreib(ST.STRIKES, {})
        self.assertEqual([x["video_id"] for x in self.s.liste_bauen()], ["ccccccccccc"])


if __name__ == "__main__":
    unittest.main()
