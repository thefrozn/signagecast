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

    def test_ram_hinweis_direktmodus(self):
        """Seit 0.34: unter 2 GB nur ein Hinweis – der Direktmodus bleibt erlaubt. Agent liest MemTotal."""
        PL = self.PL
        for mb, knapp in ((420, True), (906, True), (1535, True), (1850, False), (3790, False), (None, False), ("viel", False), (True, False), (0, False)):
            self.assertEqual(PL.ram_knapp_direkt(mb), knapp, mb)
        g = PL.neu({"name": "A", "tv": "tv", "anzeige_modus": "direkt"}, {"tv"})
        a = PL.melden(g, {"modell": "Raspberry Pi 4 Model B Rev 1.5", "ram_mb": 906}, "1.2.3.4", None, None)
        self.assertEqual(a["modus"], "direkt")
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "player"))
        import agent
        alt = agent.lesen
        try:
            agent.lesen = lambda pfad, vorgabe="": "MemTotal:        1897892 kB\nMemFree:  100 kB\n" if pfad == "/proc/meminfo" else alt(pfad, vorgabe)
            self.assertEqual(agent.ram_mb(), 1853)
            agent.lesen = lambda pfad, vorgabe="": vorgabe
            self.assertIsNone(agent.ram_mb())
        finally:
            agent.lesen = alt

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


class Kategorien037(unittest.TestCase):
    """Seit 0.37: Kategorien editierbar – eigene anlegen, eingebaute ändern, löschen, einsortieren."""

    def setUp(self):
        self.e = E.pruefen({})
        self.s = ST.Streams(lambda: self.e)
        ST.schreib(ST.STRIKES, {})
        ST.schreib(ST.CACHE, {"quellen": {}, "pause_bis": 0})

    def eigene(self, **k):
        return dict({"id": "kraniche", "name": "Kraniche", "gruppe": "tiere", "begriffe": ["crane live cam"],
                     "woerter": ["crane", "kranich"]}, **k)

    def test_pruefen(self):
        ks = E.pruefen({"kategorien": [self.eigene()]})["kategorien"]
        self.assertEqual([k["id"] for k in ks], E.KATEGORIEN + ["kraniche"])           # eingebaute kommen wieder dazu
        self.assertFalse(ks[-1]["eingebaut"])
        self.assertTrue(ks[0]["eingebaut"])
        with self.assertRaises(E.Fehler):
            E.pruefen({"kategorien": [self.eigene(name="")]})                         # eigene braucht Namen
        with self.assertRaises(E.Fehler):
            E.pruefen({"kategorien": [self.eigene(woerter=["(kaputt"])]})              # ungültiges Muster
        with self.assertRaises(E.Fehler):
            E.pruefen({"kategorien": [self.eigene(), self.eigene()]})                  # doppelt
        with self.assertRaises(E.Fehler):
            E.pruefen({"kategorien": [self.eigene(id=f"k{i:02d}") for i in range(E.KAT_MAX)]})
        with self.assertRaises(E.Fehler):
            E.pruefen({"kategorien": [self.eigene(begriffe=[f"b{i}" for i in range(E.KAT_BEGRIFFE_MAX + 1)])]})   # Anfragen begrenzt
        neu = E.pruefen({"kategorien": [{"id": "neu", "begriffe": ["x"], "woerter": ["y"]}]})["kategorien"]
        self.assertEqual(next(k for k in neu if k["id"] == "neu")["begriffe"], [])     # „neu“ ohne Suche

    def test_standard_folgt_updates(self):
        e = E.pruefen({})
        safari = next(k for k in e["kategorien"] if k["id"] == "safari")
        self.assertTrue(safari["standard"])
        alt = json.loads(json.dumps(e))                                             # Datei einer älteren Version
        next(k for k in alt["kategorien"] if k["id"] == "safari")["woerter"] = ["elephant"]
        self.assertEqual(next(k for k in E.pruefen(alt)["kategorien"] if k["id"] == "safari")["woerter"], safari["woerter"])
        geaendert = json.loads(json.dumps(e))                                       # vom Nutzer geändert (ohne Merker)
        k = next(k for k in geaendert["kategorien"] if k["id"] == "safari")
        k.pop("standard"); k["woerter"] = ["elephant"]
        neu = next(k for k in E.pruefen(geaendert)["kategorien"] if k["id"] == "safari")
        self.assertEqual((neu["woerter"], neu["standard"]), (["elephant"], False))
        self.assertEqual(next(k for k in E.pruefen(E.pruefen(geaendert))["kategorien"] if k["id"] == "safari")["woerter"], ["elephant"])

    def test_fernseher_und_global(self):
        e = E.pruefen({"kategorien": [self.eigene()], "video": {"kategorien_aus": ["kraniche", "weg"], "kategorien_bekannt": E.KATEGORIEN},
                       "fernseher": [{"id": "tv", "kategorien_aus": ["kraniche", "weg"]}]})
        self.assertEqual(e["video"]["kategorien_aus"], ["kraniche"])
        self.assertEqual(e["fernseher"][0]["kategorien_aus"], ["kraniche"])
        e2 = E.pruefen(dict(e, kategorien=[]))                                       # gelöscht: Verweise verschwinden
        self.assertEqual(e2["video"]["kategorien_aus"], [])
        self.assertEqual(e2["fernseher"][0]["kategorien_aus"], [])
        e3 = E.pruefen({"kategorien": [self.eigene()], "video": {"takt_min": 3, "kategorien_bekannt": E.KATEGORIEN}})
        self.assertNotIn("kraniche", e3["video"]["kategorien_aus"])                   # neue eigene startet an

    def test_suche_und_einsortieren(self):
        self.e = E.pruefen({"kategorien": [self.eigene()]})
        ST.schreib(ST.STREAMS, {"streams": {
            "alt00000001": {"kategorie": "neu", "herkunft": "entdeckt", "titel": "Grizzly bear live cam Alaska", "name": "x",
                            "zuletzt_gefunden": time.strftime("%Y-%m-%d")},
            "alt00000002": {"kategorie": "neu", "herkunft": "entdeckt", "titel": "Bear cam", "name": "x", "kategorie_fest": True,
                            "zuletzt_gefunden": time.strftime("%Y-%m-%d")},
            "alt00000003": {"kategorie": "neu", "herkunft": "fest", "titel": "Bear cam", "name": "x"},
            "alt00000004": {"kategorie": "geloescht", "herkunft": "fest", "titel": "irgendwas", "name": "x"}}, "abgelehnt": []})
        treffer = {"crane live cam": [("kkkkkkkkkkk", "Sandhill crane nest live cam"), ("lllllllllll", "Construction site live")],
                   "bird feeder live cam": [("vvvvvvvvvvv", "Bird feeder live cam Cornell")]}
        self.s._suche = lambda b: treffer.get(b, [])
        alt = ST.oembed
        try:
            ST.oembed = lambda vid: True
            self.s.suchen()
        finally:
            ST.oembed = alt
        d = self.s.alle()["streams"]
        self.assertEqual(d["kkkkkkkkkkk"]["kategorie"], "kraniche")
        self.assertNotIn("lllllllllll", d)                                             # Titel ohne Wörter der Kategorie
        self.assertEqual(d["vvvvvvvvvvv"]["kategorie"], "vogel")                       # Tiersuche: einsortiert
        self.assertEqual(d["alt00000001"]["kategorie"], "baer")                        # alter Fund aus „neu“
        self.assertEqual(d["alt00000002"]["kategorie"], "neu")                         # von Hand gesetzt: bleibt
        self.assertEqual(d["alt00000003"]["kategorie"], "neu")                         # feste: bleiben
        self.assertEqual(d["alt00000004"]["kategorie"], "neu")                         # Kategorie gibt es nicht mehr

    def test_loeschen_verschiebt(self):
        self.e = E.pruefen({"kategorien": [self.eigene()]})
        ST.schreib(ST.STREAMS, {"streams": {"kkkkkkkkkkk": {"kategorie": "kraniche", "herkunft": "fest", "name": "x"}}, "abgelehnt": []})
        self.e = E.pruefen(dict(self.e, kategorien=[k for k in self.e["kategorien"] if k["id"] != "kraniche"]))
        self.assertEqual(self.s.einsortieren({"kraniche": "vogel"}), 1)
        self.assertEqual(self.s.alle()["streams"]["kkkkkkkkkkk"]["kategorie"], "vogel")

    def test_ohne_tag_eigene(self):
        self.e = E.pruefen({"kategorien": [self.eigene(id="mond", name="Mond", gruppe="themen", ohne_tag=True)]})
        jetzt = time.time()
        ST.schreib(ST.STREAMS, {"streams": {"mmmmmmmmmmm": {"art": "video", "name": "Mond", "kategorie": "mond",
                                                            "breite": None, "laenge": None, "aktiv": True}}, "abgelehnt": []})
        ST.schreib(ST.CACHE, {"quellen": {"mmmmmmmmmmm": {"video_id": "mmmmmmmmmmm", "live": True, "hoehe": 1080, "geprueft": jetzt}}})
        self.assertEqual([x["video_id"] for x in self.s.liste_bauen()], ["mmmmmmmmmmm"])

    def test_kurzname_nie_leer(self):
        self.assertEqual(ST.Streams.kurzname("LIVE - Earth from space"), "Earth from space")
        self.assertEqual(ST.Streams.kurzname("🔴 LIVE | Planet Earth from the ISS"), "Planet Earth from the ISS")
        self.assertEqual(ST.Streams.kurzname("Nubble Lighthouse, York – LIVE"), "Nubble Lighthouse, York")

    def test_aendern_von_hand(self):
        ST.schreib(ST.STREAMS, {"streams": {"kkkkkkkkkkk": {"kategorie": "neu", "herkunft": "entdeckt", "name": "x"}}, "abgelehnt": []})
        self.s.aendern("kkkkkkkkkkk", {"kategorie": "gibtsnicht"})
        self.assertEqual(self.s.alle()["streams"]["kkkkkkkkkkk"]["kategorie"], "neu")
        self.s.aendern("kkkkkkkkkkk", {"kategorie": "zoo"})
        self.assertTrue(self.s.alle()["streams"]["kkkkkkkkkkk"]["kategorie_fest"])


class NachEinschalten037(unittest.TestCase):
    """Seit 0.37: nach dem Einschalten über HA Quelle wählen und/oder die TV-Seite öffnen; Zustand an/aus anzeigen."""

    def tv(self, **k):
        return E.pruefen({"fernseher": [dict({"id": "tv", "ha_schalten": "media_player.tv"}, **k)]})["fernseher"][0]

    def mit_ha(self, zustaende, fn):
        import dienst as D
        gesendet, it = [], iter(zustaende)
        class HA:
            def get(self, pfad): return next(it)
            def post(self, pfad, d): gesendet.append((pfad, d))
        alt, alt_ip = D.ha, D.eigene_ip
        try:
            D.ha, D.eigene_ip = HA(), lambda: "10.0.0.5"
            return fn(D), gesendet
        finally:
            D.ha, D.eigene_ip = alt, alt_ip

    def test_einstellung(self):
        t = self.tv(ha_quelle="HDMI 2", ha_oeffnen="eigen", ha_dienst="script.turn_on", ha_daten='{"variables": {"u": "{url}"}}')
        self.assertEqual((t["ha_quelle"], t["ha_oeffnen"], t["ha_dienst"]), ("HDMI 2", "eigen", "script.turn_on"))
        self.assertEqual(self.tv()["ha_oeffnen"], "")
        with self.assertRaises(E.Fehler):
            self.tv(ha_daten="[1, 2]")
        with self.assertRaises(E.Fehler):
            self.tv(ha_dienst="kein dienst")

    def test_wartet_quelle_dann_lg(self):
        t = self.tv(ha_quelle="HDMI 2", ha_oeffnen="lg")
        fehler, gesendet = self.mit_ha([{"state": "off", "attributes": {}},
                                        {"state": "on", "attributes": {"source_list": ["HDMI 1", "HDMI 2"], "source": "HDMI 1"}}],
                                       lambda D: D.nach_einschalten(t, warten=5, takt=0))
        self.assertIsNone(fehler)
        self.assertEqual(gesendet, [
            ("/api/services/media_player/select_source", {"entity_id": "media_player.tv", "source": "HDMI 2"}),
            ("/api/services/webostv/command", {"entity_id": "media_player.tv", "command": "system.launcher/open",
                                               "payload": {"target": "http://10.0.0.5:8888/tv"}})])

    def test_android_und_eigen(self):
        t = self.tv(ha_oeffnen="android")
        _, g = self.mit_ha([{"state": "on", "attributes": {}}], lambda D: D.nach_einschalten(t, warten=0))
        self.assertEqual(g, [("/api/services/androidtv/adb_command", {"entity_id": "media_player.tv",
                              "command": "am start -a android.intent.action.VIEW -d http://10.0.0.5:8888/tv"})])
        t = self.tv(ha_oeffnen="eigen", ha_dienst="script.turn_on", ha_daten='{"variables": {"adresse": "{url}", "tv": "{entity}"}}')
        _, g = self.mit_ha([{"state": "on", "attributes": {}}], lambda D: D.nach_einschalten(t, warten=0))
        self.assertEqual(g, [("/api/services/script/turn_on", {"variables": {"adresse": "http://10.0.0.5:8888/tv", "tv": "media_player.tv"},
                                                              "entity_id": "media_player.tv"})])

    def test_unbekannte_quelle_und_aus(self):
        t = self.tv(ha_quelle="HDMI 3")
        fehler, g = self.mit_ha([{"state": "on", "attributes": {"source_list": ["HDMI 1"]}}] * 3,
                                lambda D: D.nach_einschalten(t, warten=0))
        self.assertEqual((fehler, g), ("unbekannte Quelle", []))
        fehler, g = self.mit_ha([{"state": "off", "attributes": {}}], lambda D: D.nach_einschalten(self.tv(ha_quelle="HDMI 1"), warten=0))
        self.assertEqual((fehler, g), ("nicht bereit", []))

    def test_zustand(self):
        import dienst as D
        D.zustand["einstellungen"] = E.pruefen({"ha": {"url": "http://ha.local:8123"},
                                                "fernseher": [{"id": "tv", "ha_schalten": "media_player.tv"}]})
        D.schalten_stand["tv"] = {"soll": "an"}
        for roh, erwartet in (("on", "an"), ("standby", "aus"), ("unavailable", "weg")):
            self.mit_ha([{"state": roh, "attributes": {"source": "HDMI 2"}}], lambda D: D.zustand_abfragen())
            self.assertEqual(D.schalten_stand["tv"]["ha"]["zustand"], erwartet)


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
        self.assertEqual({k["id"] for k in E.pruefen({})["kategorien"] if k["gruppe"] == "themen"}, set(E.THEMEN_KATEGORIEN))

    def test_suche_je_thema(self):
        self.e["video"]["kategorien_aus"] = ["bahn"]
        ST.schreib(ST.STREAMS, {"streams": {}, "abgelehnt": []})
        ST.schreib(ST.STRIKES, {})
        ST.schreib(ST.CACHE, {"quellen": {}, "pause_bis": 0})
        gefragt = []
        treffer = {"times square live cam": [("aaaaaaaaaaa", "Times Square LIVE cam New York"),
                                             ("eeeeeeeeeee", "Times Square crossroads live"),
                                             ("fffffffffff", "Times Square 1560 Broadway live"),
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
        self.assertEqual(self.s.ort("Maho Beach St Maarten LIVE"), (18.04, -63.12))     # genaue Orte
        self.assertEqual(self.s.ort("Los Angeles Live Cam · Venice Beach"), (34.01, -118.49))
        self.assertEqual(self.s.ort("Mount Etna Volcano, Sicily, Italy"), (37.75, 14.99))
        self.assertIsNone(self.s.ort("Beach Live Stream on a small island"))
        for titel in ("Ocean Ambience 4K Waves Sounds", "The Wedge Raw Footage | loop", "Maria's Store Cam6 Davao City"):
            self.assertTrue(ST.THEMEN_AUSSCHLUSS.search(titel), titel)
        self.assertNotIn("bbbbbbbbbbb", d)                                             # Musik aussortiert
        self.assertEqual(sum(1 for x in "aef" if x * 11 in d), 2)                         # höchstens 2 vom selben Ort
        self.assertEqual(d["ccccccccccc"]["kategorie"], "weltraum")
        self.assertEqual(d["ddddddddddd"]["kategorie"], "safari")                      # seit 0.37 einsortiert
        self.assertFalse(any(b in gefragt for b in E.KATEGORIEN_STANDARD["bahn"]["begriffe"]))   # ausgeschaltet: keine Anfragen

    def test_themen_eigene_grenze(self):
        heute = time.strftime("%Y-%m-%d")
        st = {"ddddddddddd": {"kategorie": "neu", "breite": 0.0, "laenge": 0.0, "herkunft": "entdeckt", "zuletzt_gefunden": heute}}
        for i in range(ST.THEMA_MAX + 2):                                             # 10 Weltraum-Streams, ohne Ort
            st[f"w{i:010d}"] = {"kategorie": "weltraum", "breite": None, "herkunft": "entdeckt",
                                "zuletzt_gefunden": f"2026-10-{10 + i:02d}"}
        v = dict(self.e["video"], nur_tag=False)
        raus = ST.Streams.ueberzaehlig(st, 1, v)
        self.assertEqual(sorted(raus), ["w0000000000", "w0000000001"])               # die ältesten zwei über der Grenze
        self.assertNotIn("ddddddddddd", raus)                                         # Tier-Platz nicht belegt

    def test_weltraum_ohne_ort_und_nacht(self):
        jetzt = time.time()
        ST.schreib(ST.STREAMS, {"streams": {"ccccccccccc": {"art": "video", "name": "ISS", "kategorie": "weltraum",
                                                            "breite": None, "laenge": None, "aktiv": True}}, "abgelehnt": []})
        ST.schreib(ST.CACHE, {"quellen": {"ccccccccccc": {"video_id": "ccccccccccc", "live": True, "hoehe": 1080, "geprueft": jetzt}}})
        ST.schreib(ST.STRIKES, {})
        self.assertEqual([x["video_id"] for x in self.s.liste_bauen()], ["ccccccccccc"])



class FernseherReste0321(unittest.TestCase):
    def test_reste_geloeschter_fernseher(self):
        import dienst as D
        alt = set(os.listdir(D.DATEN))
        for n in ("render-tv.env", "render-weg.env", "render-laeuft.env", "kette-laeuft.pids"):
            open(os.path.join(D.DATEN, n), "w").close()
        for n in ("chromium-tv", "chromium-weg", "chromium-laeuft", "chromium-tv.alt-20261107"):
            os.makedirs(os.path.join(D.DATEN, n, "Default"), exist_ok=True)
        self.assertEqual(sorted(D.fernseher_reste_entfernen({"tv"})), ["chromium-weg", "render-weg.env"])
        self.assertEqual(sorted(set(os.listdir(D.DATEN)) - alt),
                         ["chromium-laeuft", "chromium-tv", "chromium-tv.alt-20261107", "kette-laeuft.pids",
                          "render-laeuft.env", "render-tv.env"])


    def test_abgebrochene_verbindung_ohne_traceback(self):
        import contextlib, io
        from http.server import BaseHTTPRequestHandler
        import dienst as D
        srv = D.Server(("127.0.0.1", 0), BaseHTTPRequestHandler)
        try:
            for fehler, gemeldet in ((BrokenPipeError(32, "Broken pipe"), False), (ConnectionResetError(104, "reset"), False),
                                     (ValueError("echt"), True)):
                aus = io.StringIO()
                with contextlib.redirect_stderr(aus):
                    try:
                        raise fehler
                    except Exception:
                        srv.handle_error(None, ("127.0.0.1", 1))
                self.assertEqual("Traceback" in aus.getvalue(), gemeldet, type(fehler).__name__)
        finally:
            srv.server_close()



class Fernwartung033(unittest.TestCase):
    """Terminal zum Pi: Verschlüsselung wie im Agent, nur mit Erlaubnis des Pi, Schutz vor Wiedereinspielen, Zeitgrenzen."""
    def setUp(self):
        import fernwartung as FW
        self.FW = FW
        self.g = {"id": "abcd1234", "name": "Test-Pi", "schluessel": "11" * 32}
        FW.sitzungen.clear()

    def agent(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "player"))
        import agent
        return agent

    def test_verschluesselung_wie_agent(self):
        A, FW = self.agent(), self.FW
        k = FW.schluessel(self.g)
        self.assertEqual(k, A.fw_schluessel(self.g))
        for roh in (b"", b"ls -la\r", os.urandom(70000)):
            text = FW.verschluesseln(k, roh)
            self.assertEqual(A.fw_entschluesseln(k, text), roh)
            self.assertEqual(FW.entschluesseln(k, A.fw_verschluesseln(k, roh)), roh)
            if roh:
                self.assertNotIn(roh[:6], __import__("base64").b64decode(text))
        self.assertNotEqual(FW.verschluesseln(k, b"gleich"), FW.verschluesseln(k, b"gleich"))   # neue Nonce je Nachricht

    def test_nur_mit_erlaubnis_des_pi(self):
        with self.assertRaises(ValueError):
            self.FW.starten(self.g, False, 80, 24, "x")
        self.assertIsNone(self.FW.fuer_meldung(self.g))

    def test_ablauf_und_wiedereinspielen(self):
        FW, g = self.FW, self.g
        k = FW.schluessel(g)
        sid = FW.starten(g, True, 100, 30, "tester")
        t = FW.fuer_meldung(g)
        self.assertEqual((t["sid"], t["spalten"], t["zeilen"]), (sid, 100, 30))
        self.assertTrue(FW.pi_ein(g, {"sid": sid, "n": 1}, warten=0.05)["offen"])
        self.assertEqual(FW.zustand(g["id"])["zustand"], "offen")
        self.assertTrue(FW.eingabe(g["id"], sid, "ls\r"))
        d = FW.pi_ein(g, {"sid": sid, "n": 2, "groesse_rev": 1}, warten=0.05)
        self.assertEqual(FW.entschluesseln(k, d["daten"]), b"ls\r")
        self.assertFalse(FW.pi_ein(g, {"sid": sid, "n": 2}, warten=0.05)["offen"])      # mitgeschnittene Anfrage
        self.assertFalse(FW.pi_ein(g, {"sid": "0" * 32, "n": 9}, warten=0.05)["offen"])  # fremde Sitzung
        self.assertTrue(FW.pi_aus(g, {"sid": sid, "n": 1, "daten": FW.verschluesseln(k, b"datei.txt\r\n")})["offen"])
        self.assertFalse(FW.pi_aus(g, {"sid": sid, "n": 1, "daten": FW.verschluesseln(k, b"nochmal")})["offen"])
        a = FW.ausgabe(g["id"], sid, 0, warten=0)
        self.assertEqual(__import__("base64").b64decode(a["daten"]), b"datei.txt\r\n")
        self.assertEqual(FW.ausgabe(g["id"], sid, a["ab"], warten=0)["daten"], "")
        self.assertTrue(FW.eingabe(g["id"], sid, "", 120, 40))
        d = FW.pi_ein(g, {"sid": sid, "n": 3, "groesse_rev": 1}, warten=0.05)
        self.assertEqual((d["spalten"], d["zeilen"], d["groesse_rev"]), (120, 40, 2))
        FW.pi_aus(g, {"sid": sid, "n": 2, "daten": FW.verschluesseln(k, b""), "ende": "beendet"})
        self.assertEqual(FW.ausgabe(g["id"], sid, a["ab"], warten=0)["zustand"], "zu")
        p = FW.protokoll(g["id"])[0]
        self.assertEqual((p["wer"], p["grund"], p["name"]), ("tester", "pi_beendet", "Test-Pi"))
        self.assertNotIn("datei.txt", open(FW.PROTOKOLL).read())                         # keine Inhalte im Protokoll
        self.assertIsNone(FW.zustand(g["id"]))

    def test_zeitgrenzen(self):
        FW, g = self.FW, self.g
        for feld, grund in (("eingabe_zeit", "leerlauf"), ("start", "zeitgrenze"), ("verwaltung_zeit", "verwaltung_weg")):
            sid = FW.starten(g, True, 80, 24, "x")
            FW.pi_ein(g, {"sid": sid, "n": 1}, warten=0.01)
            FW.sitzungen[g["id"]][feld] -= 4000
            self.assertIsNone(FW.zustand(g["id"]))
            self.assertEqual(FW.protokoll(g["id"])[0]["grund"], grund)
        sid = FW.starten(g, True, 80, 24, "x")
        FW.sitzungen[g["id"]]["start"] -= 50                                                    # Pi meldet sich nicht
        self.assertIsNone(FW.fuer_meldung(g))
        self.assertEqual(FW.protokoll(g["id"])[0]["grund"], "pi_antwortet_nicht")

    def test_image_nur_auf_wunsch(self):
        import player as PL
        g = {"id": "abcd1234", "schluessel": "11" * 32, "name": "x", "hotspot_pw": "y" * 10, "schreibschutz": True,
             "lautstaerke": 100, "drehung": 0, "hwdec": "auto", "aufloesung": "auto"}
        ohne = json.loads(PL.konfig(g, [], "http://10.0.0.1:8890", "de", ""))
        mit = json.loads(PL.konfig(g, [], "http://10.0.0.1:8890", "de", "", True))
        self.assertNotIn("fernwartung", ohne)
        self.assertTrue(mit["fernwartung"])



class Todo035(unittest.TestCase):
    """Seit 0.35: Einträge von „Zu erledigen“ ausblenden – Tipp dauerhaft, Update je Version, Warnung bis das Problem weg war."""
    def setUp(self):
        import todo as TD
        self.TD, self.pfad = TD, os.path.join(tempfile.mkdtemp(), "todo.json")
        self.l = TD.Liste(self.pfad)

    def test_arten(self):
        art = self.TD.art
        for k, a in (("sicherung", "tipp"), ("benachrichtigung", "tipp"), ("software", "tipp"), ("update:v0.35.0", "update"),
                     ("update:0.35.1", "update"), ("ha", "warn"), ("wetter", "warn"), ("allgemein", "warn"), ("sicherung_fehler", "warn"),
                     ("bn_fehler", "warn"), ("player:0123abcd", "warn"), ("bildrate:tv", "warn"), ("doppelt:kueche2", "warn")):
            self.assertEqual(art(k), a, k)
        for k in ("passwort", "", None, 5, "player:xyz", "bildrate:TV", "update:neu", "ha ", "x" * 50, "../todo"):
            self.assertIsNone(art(k), k)                 # Startpasswort und Unbekanntes lassen sich nicht ausblenden
        self.assertFalse(self.l.ausblenden("passwort"))

    def test_tipp_bleibt_update_je_version(self):
        l = self.l
        self.assertTrue(l.ausblenden("sicherung") and l.ausblenden("update:v0.35.0"))
        for _ in range(3):
            l.pruefen(set(), "v0.35.0")
        self.assertEqual(l.liste(), ["sicherung", "update:v0.35.0"])
        l.pruefen(set(), "v0.36.0")                       # neue Version: Hinweis kommt wieder, Tipp bleibt weg
        self.assertEqual(l.liste(), ["sicherung"])
        self.assertEqual(self.TD.Liste(self.pfad).liste(), ["sicherung"])   # gespeichert
        self.assertTrue(l.einblenden("sicherung"))
        self.assertFalse(l.einblenden("sicherung"))
        self.assertEqual(l.liste(), [])

    def test_warnung_bis_problem_weg(self):
        l = self.l
        l.ausblenden("player:0123abcd")
        l.ausblenden("ha")
        for _ in range(5):                                # Problem besteht weiter: bleibt ausgeblendet
            l.pruefen({"player:0123abcd", "ha"}, None)
        self.assertEqual(l.liste(), ["ha", "player:0123abcd"])
        l.pruefen({"ha"}, None)                           # einmal weg: noch nicht (Aussetzer)
        l.pruefen({"ha", "player:0123abcd"}, None)        # wieder da: Zähler zurück
        l.pruefen({"ha"}, None)
        self.assertIn("player:0123abcd", l.liste())
        self.assertEqual(l.pruefen({"ha"}, None), ["player:0123abcd"])   # zweimal hintereinander weg: freigegeben
        self.assertEqual(l.liste(), ["ha"])

    def test_sicherung_und_kaputte_datei(self):
        self.l.ausblenden("software")
        roh = self.l.als_bytes()
        neu = self.TD.Liste(os.path.join(tempfile.mkdtemp(), "todo.json"))
        neu.einspielen(roh)
        self.assertEqual(neu.liste(), ["software"])
        neu.einspielen(b'{"aus": {"passwort": {"art": "tipp"}, "ha": {"art": "warn"}, "x": 1}}')
        self.assertEqual(neu.liste(), ["ha"])             # Unbekanntes aus Sicherungen wird verworfen
        neu.einspielen(b"kaputt")
        self.assertEqual(neu.liste(), ["ha"])
        open(self.pfad, "w").write("{kaputt")
        self.assertEqual(self.TD.Liste(self.pfad).liste(), [])

    def test_obergrenze(self):
        for i in range(self.TD.MAX):
            self.assertTrue(self.l.ausblenden(f"player:{i:08x}"))
        self.assertFalse(self.l.ausblenden("ha"))


class PcPlayer036(unittest.TestCase):
    """Seit 0.36: PC-Player (eigenes Grundimage, ISO roh oder .img.gz, Kopplung mit Plattform) und Browser-Gerät (nur Link)."""
    def setUp(self):
        import player as PL
        self.PL, d = PL, tempfile.mkdtemp()
        PL.DATEI, PL.ORDNER = os.path.join(d, "player.json"), os.path.join(d, "p")
        PL.GRUND, PL.GRUND_PC = os.path.join(d, "p", "basis"), os.path.join(d, "p", "basis-pc")
        PL.daten.clear()
        PL.daten.update(PL._leer())
        PL.stand.clear()
        PL.direkt_abruf.clear()
        PL.kopplungen.clear()
        PL.koppel_zeiten.clear()

    def grundimage_pc(self):
        import lzma
        PL, marke = self.PL, "SCPH-pc"
        platz = b"".join((f"{marke}-{i:04d}".ljust(511) + "\n").encode() for i in range(32))
        img = bytearray(os.urandom(1 << 20)) + bytes(2 << 20)
        img[1 << 20:(1 << 20) + len(platz)] = platz
        os.makedirs(PL.GRUND_PC)
        open(os.path.join(PL.GRUND_PC, "x.iso.xz"), "wb").write(lzma.compress(bytes(img)))
        json.dump({"art": "signagecast-pc-image", "version": "0.36.0", "datei": "x.iso.xz", "groesse": len(img),
                   "platzhalter": {"offset": 1 << 20, "laenge": 16384, "marke": marke}}, open(os.path.join(PL.GRUND_PC, "meta.json"), "w"))
        return bytes(img)

    def test_pc_image_roh_und_gz(self):
        import gzip
        PL, img = self.PL, self.grundimage_pc()
        g = PL.neu({"name": "Empfang", "tv": "tv", "modell": "pc"}, {"tv"})
        self.assertEqual((g["modell"], g["anzeige_modus"]), ("pc", "direkt"))       # PC: Direktmodus als Standard
        with self.assertRaises(M.Meldung):                                          # kein Pi-Grundimage nötig, aber das PC-Image
            PL.herunterladen_vorbereiten("", None, "http://192.0.2.1:8890")          # (Sammel-Image ohne Art = Pi: fehlt)
        k = PL.herunterladen_vorbereiten(g["id"], None, "http://192.0.2.1:8890", form="iso")
        self.assertEqual(PL.dateiname_fuer(k), "signagecast-pc-empfang.iso")
        aus = []
        PL.image_schreiben(k, aus.append, "de", "Europe/Berlin")
        roh = b"".join(aus)                                                         # ungepackt, gleiche Länge
        self.assertEqual(len(roh), len(img))
        self.assertEqual(roh[:1 << 20], img[:1 << 20])
        self.assertEqual(json.loads(roh[1 << 20:(1 << 20) + 16384])["id"], g["id"])
        k = PL.herunterladen_vorbereiten("", None, "http://192.0.2.1:8890", art="pc")
        self.assertEqual(PL.dateiname_fuer(k), "signagecast-pc-kopplung.img.gz")
        aus = []
        PL.image_schreiben(k, aus.append, "de", "Europe/Berlin")
        self.assertTrue(json.loads(gzip.decompress(b"".join(aus))[1 << 20:(1 << 20) + 16384])["kopplung"])
        p = PL.neu({"name": "Pi", "tv": "tv"}, {"tv"})                              # Pi bleibt Pi: ohne Pi-Grundimage kein Download
        with self.assertRaises(M.Meldung):
            PL.herunterladen_vorbereiten(p["id"], None, "http://192.0.2.1:8890", form="iso")

    def test_pc_kein_systemupdate(self):
        PL = self.PL
        g = PL.neu({"name": "PC", "tv": "tv", "modell": "pc"}, {"tv"})
        PL.stand[g["id"]] = {"zeit": time.time(), "bericht": {"letztes_update": None}}
        import unittest.mock as um
        with um.patch("time.localtime", return_value=time.struct_time((2026, 11, 8, 3, 10, 0, 6, 312, 0))):
            PL.wochenpflege()
        self.assertEqual(PL.befehle.get(g["id"], []), [])

    def test_koppeln_als_pc(self):
        PL = self.PL
        a = secrets_pub()
        d = PL.koppel_anfrage({"a": format(a, "x"), "modell": "PC LENOVO ThinkCentre M720q", "plattform": "pc"}, "192.0.2.9")
        code = PL.kopplungen[d["kennung"]]["code"]
        g = PL.koppeln(code, {"name": "Empfang", "tv": "tv"}, {"tv"})
        self.assertEqual(g["modell"], "pc")

    def test_browser_geraet(self):
        PL = self.PL
        g = PL.neu({"name": "Smart-TV", "tv": "tv", "modell": "browser", "anzeige_modus": "stream"}, {"tv"})
        self.assertEqual((g["modell"], g["anzeige_modus"], PL.modus_fuer(g)), ("browser", "direkt", "direkt"))
        PL.aendern(g["id"], {"modell": "pi45"}, {"tv"})                             # bleibt ein Browser-Gerät
        self.assertEqual(g["modell"], "browser")
        p = PL.neu({"name": "Pi", "tv": "tv"}, {"tv"})
        PL.aendern(p["id"], {"modell": "browser"}, {"tv"})                          # und ein Pi wird keines
        self.assertEqual(p["modell"], "pi45")
        self.assertFalse(PL.online(g["id"]) or PL.gesehen(g["id"]))
        PL.direkt_abruf[g["id"]] = time.time()                                      # die Seite hat Daten geholt
        self.assertTrue(PL.online(g["id"]) and PL.gesehen(g["id"]))
        eintrag = next(x for x in PL.liste(lambda g: []) if x["id"] == g["id"])
        alt = PL.anzeige_schluessel(g)
        self.assertEqual(eintrag["link_pfad"], "/anzeige/" + alt)
        self.assertNotIn("schluessel", eintrag)
        self.assertIsNone(next(x for x in PL.liste(lambda g: []) if x["id"] == p["id"])["link_pfad"])
        with self.assertRaises(M.Meldung):
            PL.befehl(g["id"], "bild")
        with self.assertRaises(M.Meldung):
            PL.herunterladen_vorbereiten(g["id"], None, "http://192.0.2.1:8890")
        PL.link_neu(g["id"])                                                        # alter Link sofort ungültig
        self.assertIsNone(PL.geraet_fuer_anzeige(alt))
        self.assertIs(PL.geraet_fuer_anzeige(PL.anzeige_schluessel(g)), g)
        self.assertFalse(PL.online(g["id"]))
        with self.assertRaises(M.Meldung):
            PL.link_neu(p["id"])                                                    # nur für Browser-Geräte

    def test_agent_pc_erkennung(self):
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "player"))
        import agent
        alt = agent.PC, agent.lesen, agent.glob_liste
        werte = {"/sys/class/dmi/id/sys_vendor": "LENOVO", "/sys/class/dmi/id/product_version": "ThinkCentre M720q",
                 "/sys/class/dmi/id/product_name": "10T7S0A600", "/sys/class/hwmon/hwmon1/name": "coretemp",
                 "/sys/class/hwmon/hwmon1/temp1_input": "45000", "/proc/cmdline": "boot=live quiet"}
        try:
            agent.PC, agent.lesen = True, lambda p, e="": werte.get(p, e)
            agent.glob_liste = lambda m: {"/sys/class/hwmon/hwmon*": ["/sys/class/hwmon/hwmon0", "/sys/class/hwmon/hwmon1"],
                                          "/sys/class/drm/card*-*/status": ["/sys/class/drm/card1-eDP-1/status", "/sys/class/drm/card1-DP-2/status",
                                                                            "/sys/class/drm/card1-Writeback-1/status"]}.get(m, [])
            self.assertEqual(agent.modell(), "PC LENOVO ThinkCentre M720q 10T7S0A600")
            self.assertEqual(agent.temperatur(), 45.0)
            self.assertTrue(agent.schreibschutz_aktiv())
            self.assertFalse(agent.schreibschutz_setzen(False))
            self.assertEqual(agent.ausgaenge(), ["/sys/class/drm/card1-DP-2/status", "/sys/class/drm/card1-eDP-1/status"])
        finally:
            agent.PC, agent.lesen, agent.glob_liste = alt


def secrets_pub():
    import player as PL, secrets
    return pow(2, secrets.randbits(320), PL.DH_P)


if __name__ == "__main__":
    unittest.main()


class Netz038(unittest.TestCase):
    """Seit 0.38: Internet erreichbar? Zwei Fehlschläge in Folge = offline, ein Erfolg = wieder online."""

    def test_zustaende(self):
        import netz as NZ
        alt = NZ.NOCHMAL_S
        NZ.NOCHMAL_S = 0
        try:
            antworten = iter([False, True, False, False, True])
            w = NZ.Wache(pruefen=lambda timeout=5: next(antworten))
            self.assertTrue(w.einmal())                 # erst falsch, Wiederholung klappt -> online
            self.assertFalse(w.offline)
            self.assertFalse(w.einmal())                # zweimal falsch -> offline
            self.assertTrue(w.offline)
            self.assertIsNotNone(w.stand()["seit"])
            self.assertFalse(w.jetzt_online())          # offline: ohne Prüfung False
            self.assertTrue(w.einmal())                 # ein Erfolg genügt
            self.assertEqual(w.stand(), {"offline": False, "seit": None})
        finally:
            NZ.NOCHMAL_S = alt


class Ausgabe038(unittest.TestCase):
    """Seit 0.38: Bildprüfung – schwarz oder stehend (nur mit sichtbarer Uhr), jeweils erst nach 3 Prüfungen."""
    N = 160 * 90

    def test_schwarz_und_bewegt(self):
        import ausgabe as AG
        self.assertTrue(AG.schwarz(bytes(self.N)))
        self.assertTrue(AG.schwarz(bytes([200] * 20) + bytes(self.N - 20)))      # einzelne Punkte zählen nicht
        self.assertFalse(AG.schwarz(bytes([85] * 500) + bytes(self.N - 500)))    # gedimmte Uhr auf Schwarz
        a = bytes([100] * self.N)
        self.assertFalse(AG.bewegt(a, bytes([110] * self.N)))                   # Kodier-Rauschen
        self.assertTrue(AG.bewegt(a, bytes([200] * 10) + a[10:]))

    def test_befunde(self):
        import ausgabe as AG
        p, sw, bild = AG.Pruefer(), bytes(self.N), bytes([90] * 3000) + bytes(self.N - 3000)
        self.assertEqual([p.pruefen("tv", sw, False, False, 0) for _ in range(3)], ["", "", "schwarz"])
        self.assertEqual(p.pruefen("tv", bild, False, False, 0), "ok")
        self.assertEqual([p.pruefen("tv", sw, True, False, 0) for _ in range(4)][-1], "ok")       # Zeitplan „schwarz“
        q = AG.Pruefer()
        self.assertEqual([q.pruefen("tv", bild, False, True, 0) for _ in range(4)], ["ok", "ok", "ok", "steht"])
        r = AG.Pruefer()
        self.assertEqual([r.pruefen("tv", bild, False, False, 0) for _ in range(5)][-1], "ok")    # ohne Uhr darf es stehen
        self.assertEqual(r.pruefen("tv", None, False, False, 0), "ok")                             # kein Bild: Befund bleibt


class Protokoll038(unittest.TestCase):
    """Seit 0.38: Änderungsprotokoll (ohne Werte) und Layout-Versionen (je Layout 10, gelöschte zurückholen)."""

    def test_protokoll_begrenzt_und_einspielen(self):
        import protokoll as PR
        d = tempfile.mkdtemp()
        p = PR.Protokoll(os.path.join(d, "p.json"))
        for i in range(PR.MAX + 5):
            p.eintragen("anna", "verwaltung", "einstellungen", f"x{i}")
        self.assertEqual(len(p.liste()), PR.MAX)
        self.assertEqual(p.liste()[0]["detail"], f"x{PR.MAX + 4}")
        self.assertEqual(PR.Protokoll(os.path.join(d, "p.json")).liste(1)[0]["detail"], f"x{PR.MAX + 4}")
        p.eintragen("<script>", "pult", "x")
        self.assertEqual(p.liste(1)[0]["wer"], "?")
        q = PR.Protokoll(os.path.join(d, "q.json"))
        q.eintragen("bob", "pult", "durchsage")
        q.einspielen(p.als_bytes())
        self.assertEqual(len(q.liste()), PR.MAX)

    def test_versionen(self):
        import protokoll as PR
        d = tempfile.mkdtemp()
        v = PR.Versionen(os.path.join(d, "v.json"))
        a = L.pruefe_layout({"id": "aa", "name": "A", "elemente": [{"id": "u", "typ": "uhr"}]})
        b = L.pruefe_layout({"id": "bb", "name": "B", "elemente": []})
        self.assertEqual(v.merken([a, b], [a, b], "x"), ([], [], []))           # unverändert: nichts aufheben
        a2 = dict(a, name="A2")
        self.assertEqual(v.merken([a, b], [a2, b], "anna"), (["A2"], [], []))
        self.assertEqual(v.liste("aa")[0]["wer"], "anna")
        self.assertEqual(v.holen("aa", 0)["name"], "A")
        for i in range(12):
            v.merken([dict(a2, name=f"n{i}")], [dict(a2, name=f"n{i + 1}")], "x")
        self.assertEqual(len(v.liste("aa")), PR.VERSIONEN_MAX)
        self.assertEqual(v.merken([a2, b], [a2], "x"), ([], ["B"], []))           # gelöscht -> zurückholbar
        self.assertEqual([g["id"] for g in v.geloeschte()], ["bb"])
        self.assertEqual(v.holen("bb", 0)["name"], "B")
        v.merken([a2], [a2, b], "x")                                              # wiederhergestellt
        self.assertEqual(v.geloeschte(), [])
        w = PR.Versionen(os.path.join(d, "v.json"))
        self.assertEqual(len(w.liste("aa")), PR.VERSIONEN_MAX)
        with self.assertRaises(KeyError):
            w.holen("aa", 99)
        for i in range(PR.GELOESCHT_MAX + 3):                                     # gelöschte begrenzt
            x = L.pruefe_layout({"id": f"z{i:02d}", "name": f"z{i}", "elemente": []})
            w.merken([x], [], "x")
        self.assertEqual(len(w.geloeschte()), PR.GELOESCHT_MAX)


class LayoutImport038(unittest.TestCase):
    """Seit 0.38: Layout aus Datei oder eingefügtem Text (z. B. von einer KI) – fehlertolerant, mit Hinweisen."""

    def test_reparaturen(self):
        roh = {"art": "signagecast-layout", "layout": {"id": "aa", "name": "KI", "thema": {"schrift": "Comic Sans", "schema": "bunt"},
               "hintergrund": {"art": "video", "farbe": "rot"},
               "elemente": [{"typ": "uhr", "x": 1, "y": 1, "w": 8, "h": 3}, {"typ": "wetterkarte"},
                            {"id": "t", "typ": "text", "x": 40, "y": 0, "w": 20, "h": "2", "optionen": {"text": "Hallo", "groesse": 9}},
                            {"id": "t", "typ": "logo", "optionen": {"bild": "0123456789abcdef.jpg"}},
                            {"typ": "kachel", "optionen": {"entity": "kein entity"}, "bedingung": {"entity": "x", "op": "~"}},
                            {"typ": "apiwert", "optionen": {"quelle": "fehlt"}}]}}
        l, h = L.import_pruefen(roh, ["aa"], bild_da=lambda n: False, quellen=["da"])
        self.assertNotEqual(l["id"], "aa")
        self.assertEqual((l["thema"]["schrift"], l["thema"]["schema"], l["hintergrund"]["art"]), ("Roboto", "dunkel", "wetter"))
        self.assertEqual([e["typ"] for e in l["elemente"]], ["uhr", "text", "logo", "kachel", "apiwert"])
        self.assertEqual(len({e["id"] for e in l["elemente"]}), 5)
        self.assertEqual(l["elemente"][1]["x"] + l["elemente"][1]["w"], 48)
        self.assertEqual(l["elemente"][2]["optionen"]["bild"], "")
        self.assertIsNone(l["elemente"][3]["bedingung"])
        codes = [x.code for x in h]
        for c in ("l_imp_wert", "l_imp_typ", "l_imp_raster", "l_imp_option", "l_imp_bild", "l_imp_bedingung", "l_imp_quelle"):
            self.assertIn(c, codes)

    def test_kein_layout_und_text(self):
        with self.assertRaises(M.Meldung):
            L.import_pruefen({"name": "x"})
        self.assertEqual(L.json_aus_text('Gern!\n```json\n{"elemente": []}\n```\nViel Spaß'), {"elemente": []})
        self.assertEqual(L.json_aus_text('Hier: {"elemente": [{"typ": "uhr"}]} – fertig'), {"elemente": [{"typ": "uhr"}]})
        with self.assertRaises(M.Meldung):
            L.json_aus_text("nichts")
        l, h = L.import_pruefen({"layouts": [{"elemente": [{"typ": "uhr"}]}]})
        self.assertEqual(h, [])

    def test_format_vollstaendig_und_doku_aktuell(self):
        t = L.format_beschreibung()
        for typ in L.TYPEN:
            self.assertIn(f"### `{typ}`", t)
            self.assertIn(typ, L.TYP_TEXT)
        doku = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "LAYOUT-FORMAT.md")
        self.assertEqual(open(doku, encoding="utf-8").read(), t,
                         "docs/LAYOUT-FORMAT.md neu erzeugen: python3 -c 'import layouts; print(layouts.format_beschreibung(), end=\"\")' (in app/)")

    def test_vorlagen_lassen_sich_importieren(self):
        for v in L.vorlagen():                     # Export/Import einer Vorlage ändert nichts
            l, h = L.import_pruefen({"art": "signagecast-layout", "layout": v}, [])
            self.assertEqual(h, [], v["id"])
            self.assertEqual(l["elemente"], v["elemente"])


class Dienst038(unittest.TestCase):
    """Seit 0.38: Pult-Layout vor dem Zeitplan, Ersatz bei Internet-Ausfall, Protokoll aus der Verwaltung ohne Werte."""

    def test_pult_rechte_einstellung(self):
        z = E.pruefen({"pult": {"zugaenge": [{"id": "abcd", "name": "Empfang", "meldung": 1, "schalten": True}]}})["pult"]["zugaenge"][0]
        self.assertEqual((z["meldung"], z["layout"], z["schalten"], z["alarm"]), (True, False, True, False))

    def test_layout_vorrang(self):
        import dienst as D
        e = E.pruefen({"layouts": [L.standard(), L.vorlagen()[-1]],
                       "fernseher": [{"id": "tv", "layout": "standard", "zeitplan": [{"von": "00:00", "bis": "23:59", "layout": "schwarz"}]}]})
        t = e["fernseher"][0]
        self.assertTrue(D.layout_fuer(t, e["layouts"]).get("schwarz"))
        D.layout_vorrang["tv"] = {"layout": "nacht", "bis": time.time() + 60, "von": "Empfang"}
        try:
            self.assertEqual(D.layout_fuer(t, e["layouts"])["id"], "nacht")
            D.layout_vorrang["tv"]["bis"] = time.time() - 1                      # abgelaufen
            self.assertTrue(D.layout_fuer(t, e["layouts"]).get("schwarz"))
        finally:
            D.layout_vorrang.pop("tv", None)

    def test_protokoll_ohne_werte(self):
        import dienst as D
        class H:
            headers = {"X-SignageCast-Benutzer": "anna"}
            protokoll_detail = {"layouts": {"geaendert": ["Lobby"], "geloescht": [], "neu": []}}
        vorher = len(D.PROTOKOLL.liste())
        D.protokoll_verwaltung(H(), "/api/einstellungen", {"ha": {"token": "GEHEIM"}, "layouts": []}, {})
        x = D.PROTOKOLL.liste(1)[0]
        self.assertEqual((x["wer"], x["aktion"]), ("anna", "einstellungen"))
        self.assertEqual(x["detail"], "ha; layouts.geaendert: Lobby")
        self.assertNotIn("GEHEIM", json.dumps(D.PROTOKOLL.liste()))
        H.protokoll_detail = None
        D.protokoll_verwaltung(H(), "/api/player/0123abcd/terminal/ein", {"text": "passwort"}, {})    # Eingaben nie
        D.protokoll_verwaltung(H(), "/api/quellen/test", {}, {})
        self.assertEqual(len(D.PROTOKOLL.liste()), vorher + 1)
        D.protokoll_verwaltung(H(), "/api/streams/abcdefghijk/entfernen", {}, {})
        self.assertEqual(D.PROTOKOLL.liste(1)[0]["aktion"], "stream_entfernen")
        D.protokoll_verwaltung(H(), "/api/streams/abcdefghijk", {}, {})
        self.assertEqual(D.PROTOKOLL.liste(1)[0]["aktion"], "stream_aendern")

    def test_todo_kennungen(self):
        import todo as TD
        self.assertEqual(TD.art("internet"), "warn")
        self.assertEqual(TD.art("bild:tv"), "warn")


class Mcp039(unittest.TestCase):
    """Seit 0.39: MCP-Server über stdio – Handshake, Werkzeuge, Aufrufe gegen einen nachgestellten Datendienst."""

    def setUp(self):
        import io, mcp
        self.mcp, self.io = mcp, io
        self.e = {"layouts": [L.standard(), L.vorlagen()[-1]], "medien": [], "quellen": [],
                  "fernseher": [{"id": "tv", "name": "Wohnzimmer", "layout": "standard", "zeitplan": [], "karussell": {}, "video": True}]}
        self.gesendet = []
        def anfrage(methode, pfad, daten=None, roh=False):
            self.gesendet.append((methode, pfad, daten))
            if pfad == "/api/einstellungen" and methode == "GET":
                return {"einstellungen": json.loads(json.dumps(self.e))}
            if pfad == "/api/einstellungen":
                self.e.update(daten); return {"ok": True}
            if pfad == "/api/layouts/pruefen":
                l, h = L.import_pruefen(daten.get("layout") or L.json_aus_text(daten["text"]),
                                        [x["id"] for x in self.e["layouts"] if x["id"] != daten.get("ersetzen")])
                return {"layout": l, "hinweise": [M.als_dict(x) for x in h]}
            if pfad.startswith("/api/vorschau/bild"):
                return (b"\x89PNG\r\n\x1a\nxx", "image/png")
            if pfad == "/api/meldung":
                return {"ok": True}
            raise mcp.Fehler("unerwartet " + pfad)
        self.alt = mcp.anfrage
        mcp.anfrage = anfrage

    def tearDown(self):
        self.mcp.anfrage = self.alt

    def rufen(self, *nachrichten):
        alt_ein, alt_aus = sys.stdin, sys.stdout
        sys.stdin = self.io.StringIO("".join(json.dumps(n) + "\n" for n in nachrichten))
        sys.stdout = aus = self.io.StringIO()
        try:
            self.mcp.main()
        finally:
            sys.stdin, sys.stdout = alt_ein, alt_aus
        return [json.loads(z) for z in aus.getvalue().splitlines()]

    def werkzeug(self, name, args):
        return self.rufen({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}})[0]["result"]

    def test_handshake_und_liste(self):
        r = self.rufen({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}}},
                       {"jsonrpc": "2.0", "method": "notifications/initialized"},
                       {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                       {"jsonrpc": "2.0", "id": 3, "method": "gibtsnicht"})
        self.assertEqual(len(r), 3)                                   # keine Antwort auf die Benachrichtigung
        self.assertEqual(r[0]["result"]["protocolVersion"], "2025-06-18")
        namen = {w["name"] for w in r[1]["result"]["tools"]}
        self.assertTrue({"save_layout", "preview", "send_ticker", "get_layout_format"} <= namen)
        self.assertFalse(any(re.search(r"^(update|upgrade)s?$|backup|sicherung|terminal|player|passw|system", n) for n in namen))
        self.assertEqual(r[2]["error"]["code"], -32601)
        for w in r[1]["result"]["tools"]:
            self.assertEqual(w["inputSchema"]["type"], "object")

    def test_layout_neu_und_ersetzen(self):
        r = self.werkzeug("save_layout", {"layout": {"name": "KI", "elemente": [{"typ": "uhr"}, {"typ": "quatsch"}]}})
        d = json.loads(r["content"][0]["text"])
        self.assertEqual(len(self.e["layouts"]), 3)
        self.assertEqual(len(d["hinweise"]), 1)
        r = self.werkzeug("save_layout", {"layout": {"name": "KI 2", "elemente": []}, "replace_id": d["id"]})
        self.assertEqual(len(self.e["layouts"]), 3)
        self.assertEqual(next(l for l in self.e["layouts"] if l["id"] == d["id"])["name"], "KI 2")
        r = self.werkzeug("delete_layout", {"id": "standard"})                       # in Gebrauch
        self.assertTrue(r["isError"])
        self.assertIn("tv", r["content"][0]["text"])

    def test_fernseher_und_fehler(self):
        self.werkzeug("set_tv_layout", {"tv": "tv", "layout": "nacht"})
        self.assertEqual(self.e["fernseher"][0]["layout"], "nacht")
        r = self.werkzeug("set_tv_layout", {"tv": "tv", "layout": "gibtsnicht"})
        self.assertTrue(r["isError"])
        r = self.werkzeug("send_ticker", {"text": "Hallo", "tvs": ["falsch"]})
        self.assertTrue(r["isError"])
        self.werkzeug("send_ticker", {"text": "Hallo"})
        self.assertEqual(self.gesendet[-1][2]["fernseher"], ["tv"])
        r = self.werkzeug("preview", {"layout": "nacht"})
        self.assertEqual(r["content"][0]["type"], "image")
        r = self.werkzeug("save_layout", {})                                           # Pflichtangabe fehlt
        self.assertTrue(r["isError"])

    def test_bild_pruefung(self):
        with self.assertRaises(self.mcp.Fehler):
            self.mcp.bild_laden("", base64_text := __import__("base64").b64encode(b"GIF89a").decode())
        roh, typ = self.mcp.bild_laden("", "data:image/png;base64," + __import__("base64").b64encode(b"\x89PNG\r\n\x1a\n").decode())
        self.assertEqual(typ, "image/png")
        with self.assertRaises(self.mcp.Fehler):
            self.mcp.bild_laden("file:///etc/passwd", "")


class Admin039(unittest.TestCase):
    """Seit 0.39: Laufschrift, Layout auf Zeit und Vorschau-Layout auch über die Verwaltungs-API (für MCP)."""

    def test_meldung_und_vorrang(self):
        import dienst as D
        alt = D.zustand["einstellungen"]
        D.zustand["einstellungen"] = E.pruefen({"layouts": [L.standard(), L.vorlagen()[-1]], "fernseher": [{"id": "tv"}, {"id": "b"}]})
        try:
            D.meldung_setzen(["tv", "gibtsnicht"], "  Heute   zu ", 120, "warnung", "MCP x")
            self.assertEqual(D.meldung_fuer("tv")["text"], "Heute zu")
            self.assertIsNone(D.meldung_fuer("b"))
            D.meldung_beenden(["tv"])
            self.assertIsNone(D.meldung_fuer("tv"))
            with self.assertRaises(M.Meldung):
                D.meldung_setzen(["tv"], " ", 60, "", "x")
            l, m = D.vorrang_setzen(["b"], "nacht", 1, "x")
            self.assertEqual((l["id"], m), ("nacht", 5))                              # mindestens 5 min
            self.assertEqual(D.layout_fuer(D.fernseher("b"))["id"], "nacht")
            D.vorrang_beenden(["b"])
            self.assertEqual(D.layout_fuer(D.fernseher("b"))["id"], "standard")
            self.assertEqual(D.tv_daten("tv", "nacht")["layout"]["id"], "nacht")       # Vorschau-Layout
            self.assertEqual(D.tv_daten("tv", "gibtsnicht")["layout"]["id"], "standard")
        finally:
            D.zustand["einstellungen"] = alt
            D.layout_vorrang.clear(); D.zustand["meldung_pult"] = None


class McpDoku039(unittest.TestCase):
    def test_alle_werkzeuge_beschrieben(self):
        import mcp
        doku = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "MCP.md"), encoding="utf-8").read()
        for name in mcp.WERKZEUGE:
            self.assertIn(f"`{name}`", doku, name)


class Ki040(unittest.TestCase):
    """Seit 0.40: MCP im Heimnetz – verbundene Computer, http/https auf dem Pult-Port, Datei für Claude Desktop."""

    def setUp(self):
        import kizugang, mcp
        self.KZ, self.mcp = kizugang, mcp
        self.ordner = tempfile.mkdtemp()
        self.alt_anfrage = mcp.anfrage
        def anfrage(methode, pfad, daten=None, roh=False):
            self.wer = mcp._lokal.wer
            if pfad == "/api/einstellungen":
                return {"einstellungen": {"layouts": [L.standard()], "medien": [], "quellen": [], "fernseher": []}}
            if pfad == "/api/meldung":
                return {"ok": True}
            raise mcp.Fehler("unerwartet " + pfad)
        mcp.anfrage = anfrage

    def tearDown(self):
        self.mcp.anfrage = self.alt_anfrage

    def test_zugaenge(self):
        z = self.KZ.Zugaenge(os.path.join(self.ordner, "ki.json"))
        self.assertFalse(z.vorhanden())
        for falsch in ("", "a/b", "   ", "<script>"):
            with self.assertRaises(self.KZ.Fehler):
                z.neu(falsch, "code", "aendern")
        with self.assertRaises(self.KZ.Fehler):
            z.neu("Laptop", "telnet", "aendern")
        x, schluessel = z.neu("Laptop Büro", "code", "lesen")
        with self.assertRaises(self.KZ.Fehler):
            z.neu("laptop büro", "code", "lesen")                      # doppelt
        self.assertTrue(schluessel.startswith("sc_") and len(schluessel) > 40)
        self.assertNotIn(schluessel, open(os.path.join(self.ordner, "ki.json")).read())   # nur der Prüfwert
        self.assertEqual(oct(os.stat(os.path.join(self.ordner, "ki.json")).st_mode & 0o777), "0o600")
        self.assertEqual(z.pruefen(schluessel, "10.0.0.5")["name"], "Laptop Büro")
        self.assertIsNone(z.pruefen(schluessel + "x"))
        self.assertIsNone(z.pruefen(""))
        self.assertNotIn("token", json.dumps(z.liste()))
        # Claude Desktop: Einmal-Code, erst nach dem Einlösen ein Schlüssel
        d, code = z.neu("Mac", "desktop", "aendern")
        self.assertIsNone(z.pruefen(code))
        self.assertTrue(next(x for x in z.liste() if x["id"] == d["id"])["wartet"])
        e, s2 = z.einloesen(code, "10.0.0.6")
        self.assertEqual(e["id"], d["id"])
        self.assertEqual(z.einloesen(code), (None, None))               # nur einmal
        self.assertEqual(z.pruefen(s2)["recht"], "aendern")
        # abgelaufener Code
        f, code3 = z.neu("Alt", "desktop", "aendern")
        next(x for x in z.liste_ if x["id"] == f["id"])["code_bis"] = time.time() - 1
        self.assertEqual(z.einloesen(code3), (None, None))
        self.assertTrue(next(x for x in z.liste() if x["id"] == f["id"])["abgelaufen"])
        # Neu laden, entfernen = sofort ungültig
        z2 = self.KZ.Zugaenge(os.path.join(self.ordner, "ki.json"))
        self.assertEqual(z2.pruefen(schluessel)["id"], x["id"])
        z2.entfernen(x["id"])
        self.assertIsNone(z2.pruefen(schluessel))
        self.assertIsNone(self.KZ.Zugaenge(os.path.join(self.ordner, "ki.json")).pruefen(schluessel))

    def test_nur_lesen(self):
        m = self.mcp
        alle = m.verarbeiten({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, "MCP A")["result"]["tools"]
        lesen = m.verarbeiten({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, "MCP A", True)["result"]["tools"]
        self.assertGreater(len(alle), len(lesen))
        self.assertTrue(all(t["annotations"]["readOnlyHint"] for t in lesen))
        a = m.verarbeiten({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "send_ticker", "arguments": {"text": "x"}}}, "MCP A", True)
        self.assertTrue(a["result"]["isError"])
        a = m.verarbeiten({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "send_ticker", "arguments": {"text": "x"}}}, "MCP Laptop")
        self.assertFalse(a["result"].get("isError"))
        self.assertEqual(self.wer, "MCP Laptop")
        self.assertEqual(getattr(m._lokal, "wer", m.WER), m.WER)                    # nach der Anfrage zurückgesetzt
        self.assertIsNone(m.verarbeiten({"jsonrpc": "2.0", "method": "notifications/initialized"}, "x"))
        stapel = m.verarbeiten([{"jsonrpc": "2.0", "id": 1, "method": "ping"}, {"jsonrpc": "2.0", "method": "notifications/x"}], "x")
        self.assertEqual(len(stapel), 1)
        self.assertEqual(m.verarbeiten("quatsch", "x")["error"]["code"], -32600)

    def test_http_und_https(self):
        import dienst as D, ssl, threading, urllib.request, urllib.error, zipfile, io, shutil, subprocess
        alt = (D.KI, D.TLS_ORDNER, D.PultServer.tls, D.WEBHOOK_PORT)
        D.KI = self.KZ.Zugaenge(os.path.join(self.ordner, "ki.json"))
        D.TLS_ORDNER = os.path.join(self.ordner, "tls")
        D.KI_FEHLVERSUCHE.clear()
        tls = D.tls_zertifikat()
        if not tls:
            self.skipTest("openssl fehlt")
        k = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); k.load_cert_chain(*tls)
        D.PultServer.tls = k
        srv = D.PultServer(("127.0.0.1", 0), D.WebhookBearbeiter)
        port = srv.server_address[1]
        D.WEBHOOK_PORT = port
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        kunde = ssl.create_default_context(cafile=tls[0]); kunde.check_hostname = False

        def post(pfad, daten, schluessel=None, https=False, kopf=None):
            h = {"Content-Type": "application/json", **(kopf or {})}
            if schluessel:
                h["Authorization"] = "Bearer " + schluessel
            r = urllib.request.Request(f"{'https' if https else 'http'}://127.0.0.1:{port}{pfad}", data=json.dumps(daten).encode(), headers=h)
            try:
                with urllib.request.urlopen(r, timeout=10, context=kunde if https else None) as a:
                    return a.status, a.read()
            except urllib.error.HTTPError as f:
                return f.code, f.read()
        try:
            init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}
            self.assertEqual(post("/mcp", init)[0], 404)                        # kein Computer verbunden = aus
            x, s = D.KI.neu("Laptop", "code", "aendern")
            self.assertEqual(post("/mcp", init)[0], 401)
            self.assertEqual(post("/mcp", init, "sc_falsch")[0], 401)
            st, roh = post("/mcp", init, s)
            self.assertEqual((st, json.loads(roh)["result"]["serverInfo"]["name"]), (200, "signagecast"))
            self.assertEqual(post("/mcp", {"jsonrpc": "2.0", "method": "notifications/initialized"}, s)[0], 202)
            self.assertEqual(post("/mcp", init, s, kopf={"Origin": "http://boese.example"})[0], 403)
            st, roh = post("/mcp", init, s, https=True)                          # dasselbe über https auf demselben Port
            self.assertEqual(st, 200)
            self.assertEqual(post("/meldung", {"text": "x"})[0], 403)            # Webhook weiter wie bisher (ohne Schlüssel)
            # Claude Desktop: Datei bauen, Code einlösen
            d, code = D.KI.neu("Mac", "desktop", "lesen")
            datei = zipfile.ZipFile(io.BytesIO(D.mcpb_bauen(d, code, "127.0.0.1")))
            man = json.loads(datei.read("manifest.json"))
            for feld in ("manifest_version", "name", "version", "description", "author", "server"):
                self.assertIn(feld, man)
            self.assertEqual(man["server"]["mcp_config"]["args"], ["${__dirname}/server/index.js"])
            v = json.loads(datei.read("server/verbindung.json"))
            self.assertEqual((v["url"], v["code"]), (f"https://127.0.0.1:{port}/mcp", code))
            self.assertIn("BEGIN CERTIFICATE", v["zertifikat"])
            self.assertNotIn("PRIVATE", json.dumps(v))
            node = os.environ.get("SC_TEST_NODE") or shutil.which("node")
            if node:                                                             # Brücke wirklich laufen lassen
                ziel = os.path.join(self.ordner, "ext"); datei.extractall(ziel)
                heim = os.path.join(self.ordner, "heim"); os.makedirs(heim)
                ein = "".join(json.dumps(n) + "\n" for n in (init, {"jsonrpc": "2.0", "method": "notifications/initialized"},
                                                              {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
                r = subprocess.run([node, os.path.join(ziel, "server", "index.js")], input=ein, capture_output=True, text=True,
                                   timeout=30, env={**os.environ, "HOME": heim, "USERPROFILE": heim})
                aus = [json.loads(z) for z in r.stdout.splitlines()]
                self.assertEqual([a["id"] for a in aus], [1, 2], r.stderr)
                self.assertTrue(all(t["annotations"]["readOnlyHint"] for t in aus[1]["result"]["tools"]))   # Recht „lesen“
                with open(os.path.join(heim, ".signagecast", f"mcp-{d['id']}.json")) as f:
                    gespeichert = json.load(f)
                self.assertEqual(D.KI.pruefen(gespeichert["schluessel"])["name"], "Mac")
                self.assertEqual(oct(os.stat(os.path.join(heim, ".signagecast", f"mcp-{d['id']}.json")).st_mode & 0o777), "0o600")
                # entfernt → klare Meldung statt Absturz
                D.KI.entfernen(d["id"]); D.KI_FEHLVERSUCHE.clear()
                r = subprocess.run([node, os.path.join(ziel, "server", "index.js")], input=json.dumps(init) + "\n", capture_output=True,
                                   text=True, timeout=30, env={**os.environ, "HOME": heim, "USERPROFILE": heim})
                self.assertIn("nicht (mehr) verbunden", json.loads(r.stdout)["error"]["message"])
                # fremdes Zertifikat → keine Verbindung (kein Mitlesen)
                v["zertifikat"] = _fremdes_zertifikat(self.ordner)
                with open(os.path.join(ziel, "server", "verbindung.json"), "w") as f:
                    json.dump(v, f)
                shutil.rmtree(os.path.join(heim, ".signagecast"))
                r = subprocess.run([node, os.path.join(ziel, "server", "index.js")], input=json.dumps(init) + "\n", capture_output=True,
                                   text=True, timeout=30, env={**os.environ, "HOME": heim, "USERPROFILE": heim})
                self.assertIn("Zertifikat", json.loads(r.stdout)["error"]["message"])
            # Fehlversuche bremsen
            D.KI_FEHLVERSUCHE.clear()
            for _ in range(10):
                D.KI_FEHLVERSUCHE.setdefault("127.0.0.1", []).append(time.time())
            self.assertEqual(post("/mcp", init, s)[0], 429)
        finally:
            srv.shutdown(); srv.server_close()
            D.KI, D.TLS_ORDNER, D.PultServer.tls, D.WEBHOOK_PORT = alt
            D.KI_FEHLVERSUCHE.clear()


def _fremdes_zertifikat(ordner):
    import subprocess
    z, s = os.path.join(ordner, "fremd.pem"), os.path.join(ordner, "fremd.key")
    subprocess.run(["openssl", "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes", "-days", "1",
                    "-subj", "/CN=fremd", "-keyout", s, "-out", z], check=True, capture_output=True)
    with open(z) as f:
        return f.read()


class Download0401(unittest.TestCase):
    """Seit 0.40.1: Downloads der Verwaltung als echte Dateien vom Datendienst (Safari lädt in Cockpit keine blob:-Dateien)."""

    def setUp(self):
        import dienst as D, kizugang, threading
        self.D = D
        self.ordner = tempfile.mkdtemp()
        self.alt = (D.KI, D.TLS_ORDNER, D.PultServer.tls, D.SICHERUNGEN)
        D.KI = kizugang.Zugaenge(os.path.join(self.ordner, "ki.json"))
        D.TLS_ORDNER = os.path.join(self.ordner, "tls")
        D.SICHERUNGEN = os.path.join(self.ordner, "sicherungen")
        D.KI_DATEIEN.clear(); D.ABLAGE.clear()
        self.srv = D.Server(("127.0.0.1", 0), D.Bearbeiter)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.basis = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def tearDown(self):
        import shutil
        self.srv.shutdown(); self.srv.server_close()
        D = self.D
        D.KI, D.TLS_ORDNER, D.PultServer.tls, D.SICHERUNGEN = self.alt
        D.KI_DATEIEN.clear(); D.ABLAGE.clear()
        shutil.rmtree(self.ordner, ignore_errors=True)

    def holen(self, pfad, daten=None, kopf=True):
        import urllib.request, urllib.error
        r = urllib.request.Request(self.basis + pfad, data=json.dumps(daten).encode() if daten is not None else None,
                                   headers={"X-SignageCast": "1", "Content-Type": "application/json"} if kopf else {})
        try:
            with urllib.request.urlopen(r, timeout=10) as a:
                return a.status, a.headers, a.read()
        except urllib.error.HTTPError as f:
            return f.code, f.headers, f.read()

    def test_ablage_einmal(self):
        st, _, roh = self.holen("/api/ablage", {"name": "signagecast-layout-Lobby.json", "typ": "application/json", "inhalt": '{"ä": 1}'})
        aid = json.loads(roh)["id"]
        st, k, roh = self.holen("/api/ablage?id=" + aid, kopf=False)
        self.assertEqual(st, 403)                                         # nur mit dem Kopf der Verwaltung
        st, k, roh = self.holen("/api/ablage?id=" + aid)
        self.assertEqual((st, roh.decode()), (200, '{"ä": 1}'))
        self.assertEqual(k["Content-Disposition"], 'attachment; filename="signagecast-layout-Lobby.json"')
        self.assertEqual(self.holen("/api/ablage?id=" + aid)[0], 404)    # nur einmal
        for falsch in ({"name": "../x.json", "typ": "application/json", "inhalt": "x"},
                       {"name": 'a".json', "typ": "application/json", "inhalt": "x"},
                       {"name": "x.html", "typ": "text/html", "inhalt": "<script>"}):
            self.assertFalse(json.loads(self.holen("/api/ablage", falsch)[2])["ok"])
        for i in range(5):
            self.holen("/api/ablage", {"name": f"a{i}.md", "typ": "text/markdown", "inhalt": "x"})
        self.assertLessEqual(len(self.D.ABLAGE), self.D.ABLAGE_MAX)

    def test_ki_datei(self):
        import ssl, zipfile, io
        D = self.D
        if not D.tls_zertifikat():
            self.skipTest("openssl fehlt")
        D.PultServer.tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        a = json.loads(self.holen("/api/ki/neu", {"name": "Mac Book", "art": "desktop", "recht": "aendern", "adresse": "signagecast.local"})[2])
        self.assertTrue(a["ok"])
        self.assertEqual(a["datei"], "signagecast-mac-book.mcpb")
        st, k, roh = self.holen("/api/ki/datei?id=" + a["id"])
        self.assertEqual(st, 200)
        self.assertEqual(k["Content-Type"], "application/octet-stream")
        self.assertIn('filename="signagecast-mac-book.mcpb"', k["Content-Disposition"])
        z = zipfile.ZipFile(io.BytesIO(roh))
        self.assertEqual(json.loads(z.read("server/verbindung.json"))["id"], a["id"])
        self.assertEqual(self.holen("/api/ki/datei?id=" + a["id"])[0], 200)          # „nochmal herunterladen“
        D.KI_DATEIEN[a["id"]] = (time.time() - 1,) + D.KI_DATEIEN[a["id"]][1:]       # abgelaufen
        self.assertEqual(self.holen("/api/ki/datei?id=" + a["id"])[0], 404)
        b = json.loads(self.holen("/api/ki/neu", {"name": "Zwei", "art": "desktop", "recht": "lesen", "adresse": "signagecast.local"})[2])
        self.holen("/api/ki/entfernen", {"id": b["id"]})
        self.assertEqual(self.holen("/api/ki/datei?id=" + b["id"])[0], 404)          # entfernt = weg
        c = json.loads(self.holen("/api/ki/neu", {"name": "Drei", "art": "code", "recht": "lesen", "adresse": "signagecast.local"})[2])
        self.assertNotIn("datei", c)
        self.assertNotIn(c["id"], D.KI_DATEIEN)

    def test_sicherung_und_docker(self):
        import verwaltung as V
        os.makedirs(self.D.SICHERUNGEN)
        with open(os.path.join(self.D.SICHERUNGEN, "manuell-2026-01-02_0304.zip"), "wb") as f:
            f.write(b"PK\x05\x06" + b"\0" * 18)
        st, k, roh = self.holen("/api/sicherung/datei?name=manuell-2026-01-02_0304.zip")
        self.assertEqual((st, len(roh)), (200, 22))
        self.assertEqual(k["Content-Disposition"], 'attachment; filename="signagecast-manuell-2026-01-02_0304.zip"')
        self.assertEqual(set(V.LADEN.values()), {"/api/player/image", "/api/ki/datei", "/api/sicherung/datei", "/api/ablage"})
        def lesen(f):
            with open(os.path.join(os.path.dirname(__file__), "..", "cockpit", "signagecast", f), encoding="utf-8") as d:
                return d.read()
        tv = lesen("tv.js")
        for laden, api in V.LADEN.items():
            self.assertIn(f'"{api}": "{laden}"', tv)                     # Cockpit und Docker kennen dieselben Wege
        for f in ("tv.js", "layout.js"):
            js = lesen(f)
            self.assertNotIn(".download =", js.replace("a.download = datei", ""))   # keine blob:-Downloads mehr


class Fernnetz041(unittest.TestCase):
    """Seit 0.41: Player an anderem Standort über Tailscale/Headscale – Einmal-Schlüssel, Entfernen, Agent."""

    def setUp(self):
        import threading, fernnetz, player as PL
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        self.FN, self.PL = fernnetz, PL
        self.ordner = tempfile.mkdtemp()
        self.anfragen = anfragen = []
        self.zaehler = [0]
        test = self

        class Api(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def antwort(self, d, code=200):
                roh = json.dumps(d).encode()
                self.send_response(code); self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(roh))); self.end_headers(); self.wfile.write(roh)

            def bearbeiten(self):
                n = int(self.headers.get("Content-Length") or 0)
                roh = self.rfile.read(n).decode() if n else ""
                anfragen.append((self.command, self.path, roh, self.headers.get("Authorization", "")))
                p = self.path
                if p == "/api/v2/oauth/token":
                    return self.antwort({"access_token": "zugriff", "expires_in": 3600})
                if self.command == "POST" and p == "/api/v2/tailnet/-/keys":
                    test.zaehler[0] += 1
                    return self.antwort({"id": f"k{test.zaehler[0]}", "key": f"tskey-auth-{test.zaehler[0]}"})
                if p in ("/api/v2/tailnet/-/devices", "/api/v1/node") and self.command == "GET":
                    if p.startswith("/api/v2"):
                        return self.antwort({"devices": [{"nodeId": "nSRV", "hostname": "signagecast", "addresses": ["100.64.0.1"]},
                                                         {"nodeId": "nP1", "hostname": "sc-x", "addresses": ["100.64.0.7", "fd7a:115c:a1e0::7"]}]})
                    return self.antwort({"nodes": [{"id": "1", "givenName": "signagecast", "ipAddresses": ["100.64.0.1"]},
                                                   {"id": "3", "givenName": "sc-x", "ipAddresses": ["100.64.0.7"]}]})
                if p == "/api/v1/preauthkey" and self.command == "POST":
                    return self.antwort({"preAuthKey": {"id": "5", "key": "hskey-5"}})
                if self.command == "DELETE" or p == "/api/v1/preauthkey/expire":
                    return self.antwort({})
                return self.antwort({"message": "unbekannt"}, 404)

            do_GET = do_POST = do_DELETE = bearbeiten

        self.api = ThreadingHTTPServer(("127.0.0.1", 0), Api)
        threading.Thread(target=self.api.serve_forever, daemon=True).start()
        self.basis = f"http://127.0.0.1:{self.api.server_address[1]}"
        self.alt_ts = fernnetz.TS_API
        fernnetz.TS_API = self.basis + "/api/v2"

    def tearDown(self):
        import shutil
        self.FN.TS_API = self.alt_ts
        self.api.shutdown(); self.api.server_close()
        shutil.rmtree(self.ordner, ignore_errors=True)

    def neues_netz(self, art="tailscale"):
        f = self.FN.Fernnetz(os.path.join(self.ordner, "fernnetz.json"))
        if art == "tailscale":
            f.speichern({"art": "tailscale", "server": "100.64.0.1", "client_id": "kCLIENT123", "client_secret": "tskey-client-geheim"})
        else:
            f.speichern({"art": "headscale", "server": "100.64.0.1", "url": self.basis, "api_key": "hs-geheim-123", "benutzer": "2"})
        return f

    def test_einstellungen(self):
        FN = self.FN
        f = FN.Fernnetz(os.path.join(self.ordner, "fernnetz.json"))
        self.assertFalse(f.aktiv())
        for falsch, code in (({"art": "tailscale", "server": "10.0.0.5", "client_id": "kCLIENT", "client_secret": "x" * 10}, "fn_server"),
                             ({"art": "tailscale", "server": "100.64.0.1", "client_id": "kCLIENT", "client_secret": ""}, "fn_zugang"),
                             ({"art": "headscale", "server": "100.64.0.1", "url": "ftp://x", "api_key": "x" * 10}, "fn_zugang"),
                             ({"art": "headscale", "server": "100.64.0.1", "url": "https://hs.example.org", "api_key": "x" * 10, "benutzer": "anna"}, "fn_benutzer"),
                             ({"art": "tailscale", "server": "100.64.0.1", "client_id": "kCLIENT", "client_secret": "x" * 10, "tag": "player"}, "fn_tag"),
                             ({"art": "vpn"}, "fn_art")):
            with self.assertRaises(FN.Fehler) as e:
                f.speichern(falsch)
            self.assertEqual(e.exception.code, code)
        f = self.neues_netz()
        self.assertTrue(f.aktiv())
        self.assertEqual(os.stat(f.pfad).st_mode & 0o777, 0o600)
        self.assertEqual(f.aussen()["client_secret"], FN.MASKE)
        f.speichern({"client_secret": FN.MASKE, "tag": ""})          # •••• lässt das Geheimnis, wie es ist
        self.assertEqual(FN.Fernnetz(f.pfad).k["client_secret"], "tskey-client-geheim")
        self.assertEqual(f.k["tag"], FN.TAG_STD)
        r = f.regel(8890, 8888)
        self.assertEqual(r["acls"][0], {"action": "accept", "src": ["tag:signagecast-player"], "dst": ["100.64.0.1:8890,8888"]})

    def test_tailscale(self):
        f = self.neues_netz()
        self.assertEqual(f.pruefen()["server_name"], "signagecast")
        schluessel, kid = f.schluessel("SignageCast Praxis/Süd")
        self.assertEqual((schluessel, kid), ("tskey-auth-1", "k1"))
        post = [a for a in self.anfragen if a[1] == "/api/v2/tailnet/-/keys"][0]
        d = json.loads(post[2])
        self.assertEqual(d["capabilities"]["devices"]["create"], {"reusable": False, "ephemeral": False, "preauthorized": True,
                                                                   "tags": ["tag:signagecast-player"]})
        self.assertEqual(d["expirySeconds"], 7 * 86400)
        self.assertEqual(d["description"], "SignageCast Praxis-S-d")
        self.assertEqual(post[3], "Bearer zugriff")
        self.assertEqual(len([a for a in self.anfragen if a[1] == "/api/v2/oauth/token"]), 1)    # Token wird wiederverwendet
        self.assertIn("client_secret=tskey-client-geheim", [a for a in self.anfragen if a[1] == "/api/v2/oauth/token"][0][2])
        self.assertEqual(f.entfernen("100.64.0.7"), "sc-x")
        self.assertIn(("DELETE", "/api/v2/device/nP1"), [(a[0], a[1]) for a in self.anfragen])
        self.assertIsNone(f.entfernen("100.64.0.99"))
        f.schluessel_zurueck("k1")
        self.assertIn(("DELETE", "/api/v2/tailnet/-/keys/k1"), [(a[0], a[1]) for a in self.anfragen])
        f.speichern({"server": "100.64.0.2"})
        with self.assertRaises(self.FN.Fehler) as e:
            f.pruefen()
        self.assertEqual(e.exception.code, "fn_server_fehlt")
        f.speichern({"client_id": "kANDERS99"})                     # neuer Zugang: neues Token holen
        f.geraete()
        self.assertEqual(len([a for a in self.anfragen if a[1] == "/api/v2/oauth/token"]), 2)

    def test_headscale(self):
        f = self.neues_netz("headscale")
        self.assertEqual(f.pruefen()["geraete"], 2)
        self.assertEqual(f.schluessel("SignageCast X"), ("hskey-5", "5"))
        d = json.loads([a for a in self.anfragen if a[1] == "/api/v1/preauthkey"][0][2])
        self.assertEqual((d["user"], d["aclTags"], d["reusable"], d["ephemeral"]), ("2", ["tag:signagecast-player"], False, False))
        self.assertTrue(d["expiration"].endswith("Z"))
        self.assertEqual([a[3] for a in self.anfragen][-1], "Bearer hs-geheim-123")
        self.assertEqual(f.entfernen("100.64.0.7"), "sc-x")
        self.assertIn(("DELETE", "/api/v1/node/3"), [(a[0], a[1]) for a in self.anfragen])
        f.schluessel_zurueck("5")
        self.assertEqual(json.loads([a for a in self.anfragen if a[1] == "/api/v1/preauthkey/expire"][0][2]), {"id": "5"})

    def test_ueber_den_dienst(self):
        """Image mit „anderer Standort“: Schlüssel ins Image, alter zurückgezogen, bei Fehler kein Schlüssel übrig; Entfernen."""
        import threading, urllib.request
        import dienst as D
        PL = self.PL
        PL.DATEI, PL.ORDNER, PL.GRUND = os.path.join(self.ordner, "player.json"), os.path.join(self.ordner, "p"), os.path.join(self.ordner, "p", "basis")
        PL.daten.clear(); PL.daten.update(PL._leer()); PL.stand.clear(); PL.einmal.clear()
        alt = (D.FERN, PL.basis_meta)
        D.FERN = self.neues_netz()
        srv = D.Server(("127.0.0.1", 0), D.Bearbeiter)
        threading.Thread(target=srv.serve_forever, daemon=True).start()

        def post(pfad, d):
            r = urllib.request.Request(f"http://127.0.0.1:{srv.server_address[1]}{pfad}", data=json.dumps(d).encode(),
                                       headers={"X-SignageCast": "1", "Content-Type": "application/json"})
            with urllib.request.urlopen(r, timeout=20) as a:
                return json.load(a)
        try:
            gid = post("/api/player/neu", {"name": "Praxis", "modell": "pi45"})["geraet"]
            r = post(f"/api/player/{gid}/image", {"fern": True, "server": "http://signagecast.local:8890"})
            self.assertFalse(r["ok"])                                  # kein Grundimage – Schlüssel wieder weg
            self.assertIn(("DELETE", "/api/v2/tailnet/-/keys/k1"), [(a[0], a[1]) for a in self.anfragen])
            PL.basis_meta = lambda art="pi": {"version": "0.41.0"}
            r = post(f"/api/player/{gid}/image", {"fern": True, "server": "http://signagecast.local:8890"})
            self.assertTrue(r["ok"], r)
            e = PL.einmal[r["kennung"]]
            self.assertEqual(e["server"], "http://100.64.0.1:8890")
            k = json.loads(PL.konfig(PL.geraet(gid), [], e["server"], "de", "", fern=e["fern"]))
            self.assertEqual(k["fern"], {"art": "tailscale", "schluessel": "tskey-auth-2", "login": ""})
            self.assertEqual(PL.geraet(gid)["fern"]["kennung"], "k2")
            self.assertNotIn("tskey", json.dumps(PL.daten))           # der Schlüssel selbst wird nicht gespeichert
            post(f"/api/player/{gid}/image", {"fern": True})
            self.assertIn(("DELETE", "/api/v2/tailnet/-/keys/k2"), [(a[0], a[1]) for a in self.anfragen])   # unbenutzter alter
            r = post(f"/api/player/{gid}/image", {"fern": False})      # ohne: normales Image, kein neuer Schlüssel
            self.assertEqual(self.zaehler[0], 3)
            PL.melden(PL.geraet(gid), {"fern": {"ip": "100.64.0.7", "weg": "direkt"}}, "100.64.0.7", None, None)
            self.assertEqual(PL.geraet(gid)["fern"]["ip"], "100.64.0.7")
            self.assertEqual(post(f"/api/player/{gid}/entfernen", {})["fern"], "entfernt")
            self.assertIn(("DELETE", "/api/v2/device/nP1"), [(a[0], a[1]) for a in self.anfragen])
            gid = post("/api/player/neu", {"name": "Sammel", "modell": "pi45"})["geraet"]
            self.assertEqual(post("/api/player/sammel-image", {"fern": True})["code"], "fn_nur_geraet")
            D.FERN = self.FN.Fernnetz(os.path.join(self.ordner, "leer.json"))
            self.assertEqual(post(f"/api/player/{gid}/image", {"fern": True})["code"], "fn_aus")
        finally:
            srv.shutdown(); srv.server_close()
            D.FERN, PL.basis_meta = alt
            PL.daten.clear(); PL.daten.update(PL._leer()); PL.einmal.clear()

    def test_agent(self):
        """Agent: tailscaled starten, mit dem Schlüssel aus einer Datei beitreten, Schlüssel löschen, Zustand sichern, melden."""
        import types, stat
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "player"))
        import agent
        o = self.ordner
        bin_ = os.path.join(o, "bin"); os.makedirs(bin_)
        with open(os.path.join(bin_, "tailscaled"), "w") as f:
            f.write("#!/bin/sh\nexec sleep 30\n")
        with open(os.path.join(bin_, "tailscale"), "w") as f:
            f.write(f"""#!{sys.executable}
import json, os, sys
o = {o!r}
a = sys.argv[1:]
open(o + "/aufrufe", "a").write(" ".join(a) + "\\n")
if "status" in a:
    if not os.path.exists(o + "/drin"):
        print(json.dumps({{"BackendState": "NeedsLogin"}})); sys.exit(0)
    print(json.dumps({{"BackendState": "Running", "Self": {{"TailscaleIPs": ["100.64.0.7", "fd7a:115c:a1e0::7"]}},
                      "Peer": {{"x": {{"TailscaleIPs": ["100.64.0.1"], "CurAddr": "203.0.113.5:41641", "Relay": "fra"}}}}}}))
elif "up" in a:
    datei = [x for x in a if x.startswith("--auth-key=file:")][0].split(":", 1)[1]
    if open(datei).read() != "tskey-auth-2": sys.exit(1)
    open(o + "/drin", "w").write("1")
    open(o + "/ts/tailscaled.state", "w").write("{{zustand}}")
""")
        for n in ("tailscaled", "tailscale"):
            os.chmod(os.path.join(bin_, n), stat.S_IRWXU)
        alt = (os.environ["PATH"], agent.Fernnetz.ORDNER, agent.Fernnetz.SOCK, agent.konfig_speichern, agent.netz, agent.schreiben_sicher)
        os.environ["PATH"] = bin_ + os.pathsep + os.environ["PATH"]
        agent.Fernnetz.ORDNER, agent.Fernnetz.SOCK = os.path.join(o, "ts"), os.path.join(o, "ts.sock")
        gespeichert = []
        agent.konfig_speichern = lambda k: gespeichert.append(json.loads(json.dumps(k)))
        agent.netz = lambda: ("kabel", "", None, "10.0.0.9")
        def schreiben(pfad, inhalt):
            with open(pfad, "wb") as d:
                d.write(inhalt)
        agent.schreiben_sicher = schreiben
        p = types.SimpleNamespace(k={"server": "http://100.64.0.1:8890", "hostname": "sc-praxis",
                                     "fern": {"art": "tailscale", "schluessel": "tskey-auth-2", "login": ""}})
        f = agent.Fernnetz(p)
        f.zustand = os.path.join(o, "ts", "tailscaled.state")
        f.dauerhaft = os.path.join(o, "boot-tailscale.state")
        try:
            t = time.time()
            f.schritt(t)
            self.assertIsNotNone(f.proc)
            f.schritt(t + 1)
            f.faden.join(10)
            self.assertEqual(gespeichert[-1]["fern"], {"art": "tailscale", "login": ""})     # Schlüssel verbraucht und gelöscht
            self.assertFalse(os.path.exists(os.path.join(o, "ts", "schluessel")))
            with open(os.path.join(o, "aufrufe")) as d:
                up = [z for z in d.read().splitlines() if z.split()[1:2] == ["up"]][0]
            self.assertIn("--hostname=sc-praxis --accept-dns=false --accept-routes=false", up)
            self.assertNotIn("tskey", up)                              # nie auf der Befehlszeile
            f.schritt(t + 30)
            self.assertEqual(f.bericht(), {"ip": "100.64.0.7", "weg": "direkt", "art": "tailscale", "fehler": ""})
            with open(f.dauerhaft) as d:
                self.assertEqual(d.read(), "{zustand}")
            p.k["fern"]["login"] = "https://hs.example.org"
            self.assertIn("--login-server=https://hs.example.org", f.optionen(p.k["fern"]))
            p.k.pop("fern")
            self.assertIsNone(f.bericht())
        finally:
            if f.proc:
                f.proc.kill(); f.proc.wait()
            os.environ["PATH"], agent.Fernnetz.ORDNER, agent.Fernnetz.SOCK, agent.konfig_speichern, agent.netz, agent.schreiben_sicher = alt
