#!/usr/bin/env python3
# SignageCast – MCP-Server (seit 0.39): Inhalte mit Claude oder einem anderen KI-Assistenten verwalten.
#
# Model Context Protocol über stdio (JSON-RPC 2.0, eine Nachricht je Zeile). Der Assistent startet den Server per SSH
# auf dem SignageCast-Rechner, z. B.  ssh tvadmin@signagecast.local signagecast-mcp  – angemeldet wird mit dem
# SSH-Schlüssel, es gibt keinen neuen Port und keinen Token. Im Container: docker exec -i signagecast signagecast-mcp.
# Seit 0.40 zusätzlich im Heimnetz über HTTP(S) auf dem Port des Pults (/mcp, Datendienst ruft verarbeiten() auf) –
# nur für Computer, die in der Verwaltung verbunden wurden (kizugang.py).
#
# Der Server spricht nur mit der API des Datendienstes (127.0.0.1:8080, wie die Verwaltung). Er kann Inhalte lesen und
# ändern – Layouts, Zuweisung an Fernseher, Zeitplan, Karussell, Laufschrift, Durchsagen, Bilder, Streams, Datenquellen;
# seit 0.60 auch Vorlagen, Lesbarkeits-Hinweise, Dateien (PDF, Medien, Galerie, Datei-Quellen), Galerie-Ordner, Themen,
# Stream-Suche, Einspieler und Radio – aber bewusst nichts am System und kein Notfall-Vollbild: keine Updates, keine Sicherungen, keine Befehle an Player, keine Terminals, keine
# Passwörter oder Schlüssel. Player nur lesen (seit 0.44: list_players – Zustand, letzte Meldung, Fernverwaltung). Jede Änderung steht im Änderungsprotokoll („MCP <Benutzer>“); Layouts bekommen vorher eine Version.
# Nur Python-Standardbibliothek.
import base64, json, os, re, sys, threading, time, urllib.error, urllib.parse, urllib.request

PROTOKOLL_VERSIONEN = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
DIENST = f"http://127.0.0.1:{os.environ.get('SC_PORT', '8080')}"
BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = (open(os.path.join(BASIS, "VERSION")).read().strip() if os.path.exists(os.path.join(BASIS, "VERSION")) else "dev")
BILD_MAX = 10 * 1024 * 1024
WER = "MCP " + re.sub(r"[^\w.@-]", "", os.environ.get("SUDO_USER") or os.environ.get("USER") or os.environ.get("LOGNAME") or "ssh")[:30]

_lokal = threading.local()        # je Anfrage (HTTP, seit 0.40): wer, nur_lesen

ANLEITUNG = (
    "SignageCast shows layouts on TVs. Typical flow: status → list_layouts / get_layout → change or create a layout with "
    "save_layout (read get_layout_format first; every change keeps a version, restore_layout_version undoes it) → "
    "preview to look at the result and its readability notes → set_tv_layout to put it on a TV. list_templates / "
    "create_layout_from_template give ready layouts for many places. For short-term things use send_ticker, "
    "show_layout_for_a_while or announce. Pictures for layouts come from upload_picture (target 'layout'). "
    "Ask the user before deleting anything or changing what a TV shows right now. list_players shows the Raspberry Pi/PC "
    "players (read only: last report, display mode, remote management log) – commands and settings for players stay in the admin.")


class Fehler(Exception):
    pass


# ---------- Zugriff auf den Datendienst ----------
def anfrage(methode, pfad, daten=None, roh=False):
    kopf = {"X-SignageCast": "1", "X-SignageCast-Benutzer": getattr(_lokal, "wer", WER)}
    inhalt = None
    if daten is not None:
        inhalt = json.dumps(daten).encode()
        kopf["Content-Type"] = "application/json"
    r = urllib.request.Request(DIENST + pfad, data=inhalt, method=methode, headers=kopf)
    try:
        with urllib.request.urlopen(r, timeout=120) as a:
            b = a.read()
            typ = a.headers.get("Content-Type", "")
    except urllib.error.HTTPError as f:
        raise Fehler(f"SignageCast antwortet {f.code} auf {pfad}") from None
    except OSError as f:
        raise Fehler(f"SignageCast nicht erreichbar ({f}) – läuft der Dienst?") from None
    if roh:
        return b, typ
    d = json.loads(b or b"{}")
    if isinstance(d, dict) and d.get("ok") is False:
        raise Fehler(d.get("fehler") or d.get("code") or "Fehler")
    return d


def get(pfad, **q):
    return anfrage("GET", pfad + ("?" + urllib.parse.urlencode(q) if q else ""))


def post(pfad, daten):
    return anfrage("POST", pfad, daten)


def einst():
    return get("/api/einstellungen")["einstellungen"]


def fernseher_ids(e, tvs):
    alle = {t["id"]: t for t in e["fernseher"]}
    if not tvs:
        return list(alle)
    falsch = [x for x in tvs if x not in alle]
    if falsch:
        raise Fehler(f"unbekannte Fernseher: {', '.join(falsch)} (vorhanden: {', '.join(alle)})")
    return list(tvs)


def nutzer(e, lid):
    return [t["id"] for t in e["fernseher"] if t["layout"] == lid or any(z["layout"] == lid for z in t.get("zeitplan") or [])
            or lid in ((t.get("karussell") or {}).get("layouts") or [])]


def tv_aendern(tv, f):
    e = einst()
    tvs = e["fernseher"]
    t = next((x for x in tvs if x["id"] == tv), None)
    if not t:
        raise Fehler(f"unbekannter Fernseher {tv} (vorhanden: {', '.join(x['id'] for x in tvs)})")
    f(t, e)
    post("/api/einstellungen", {"fernseher": tvs})
    return next(x for x in einst()["fernseher"] if x["id"] == tv)


def layout_pruefen(e, lid):
    if not any(l["id"] == lid for l in e["layouts"]):
        raise Fehler(f"unbekanntes Layout {lid} (vorhanden: {', '.join(l['id'] for l in e['layouts'])})")


def bild_laden(url, daten_base64):
    if bool(url) == bool(daten_base64):
        raise Fehler("genau eines von url oder data_base64 angeben")
    if url:
        if not re.match(r"https?://", url):
            raise Fehler("nur http:// oder https://")
        r = urllib.request.Request(url, headers={"User-Agent": "SignageCast-MCP"})
        with urllib.request.urlopen(r, timeout=30) as a:
            roh = a.read(BILD_MAX + 1)
    else:
        roh = base64.b64decode(re.sub(r"^data:[^,]*,", "", daten_base64), validate=False)
    if len(roh) > BILD_MAX:
        raise Fehler("größer als 10 MB")
    if roh[:3] == b"\xff\xd8\xff":
        return roh, "image/jpeg"
    if roh[:8] == b"\x89PNG\r\n\x1a\n":
        return roh, "image/png"
    raise Fehler("nur JPG oder PNG")


# ---------- Werkzeuge ----------
def w_status(a):
    s = get("/api/status")
    return {"version": s.get("version"), "internet": "offline" if (s.get("netz") or {}).get("offline") else "online",
            "zuschauer": (s.get("stream") or {}).get("zuschauer"),
            "fernseher": [{"id": t["id"], "name": t["name"], "wiedergabe_laeuft": t["laeuft"], "layout_jetzt": t["layout"],
                           "bildpruefung": t.get("bild") or None, "pult_layout": t.get("pult_layout"),
                           "stream": (t.get("aktuell") or {}).get("name")} for t in s["fernseher"]],
            "zu_erledigen": [w["key"] for w in s.get("todo_warn") or []]}


def w_list_tvs(a):
    e = einst()
    return [{"id": t["id"], "name": t["name"], "layout": t["layout"], "zeitplan": t.get("zeitplan") or [],
             "karussell": t.get("karussell"), "video": t["video"], "video_quelle": t.get("video_quelle"),
             "kategorien_aus": t.get("kategorien_aus") or [], "ton": t.get("ton")} for t in e["fernseher"]]


def w_list_layouts(a):
    e = einst()
    return [{"id": l["id"], "name": l["name"], "bausteine": len(l["elemente"]),
             "typen": sorted({x["typ"] for x in l["elemente"]}), "verwendet_von": nutzer(e, l["id"])} for l in e["layouts"]]


def w_get_layout(a):
    e = einst()
    l = next((l for l in e["layouts"] if l["id"] == a["id"]), None)
    if not l:
        layout_pruefen(e, a["id"])
    return l


def w_get_layout_format(a):
    b, _ = anfrage("GET", "/api/layouts/format", roh=True)
    return b.decode("utf-8")


def w_save_layout(a):
    l = a["layout"]
    if isinstance(l, str):
        anfrage_daten = {"text": l}
    elif isinstance(l, dict):
        anfrage_daten = {"layout": l}
    else:
        raise Fehler("layout muss ein JSON-Objekt sein")
    e = einst()
    ersetzen = a.get("replace_id") or ""
    if ersetzen:
        layout_pruefen(e, ersetzen)
        if isinstance(l, dict):
            l["id"] = ersetzen
        anfrage_daten["ersetzen"] = ersetzen
    r = post("/api/layouts/pruefen", anfrage_daten)
    neu = r["layout"]
    if ersetzen:
        neu["id"] = ersetzen
        ls = [neu if x["id"] == ersetzen else x for x in e["layouts"]]
    else:
        ls = e["layouts"] + [neu]
    post("/api/einstellungen", {"layouts": ls})
    return {"id": neu["id"], "name": neu["name"], "ersetzt": bool(ersetzen), "bausteine": len(neu["elemente"]),
            "verwendet_von": nutzer(einst(), neu["id"]),
            "hinweise": [h.get("text") for h in r.get("hinweise") or []],
            "notes": hinweise_text(r.get("geometrie")) + ([{"note": "check text size, contrast and fit with preview"}] if neu["elemente"] else [])}


def w_delete_layout(a):
    e = einst()
    layout_pruefen(e, a["id"])
    if nutzer(e, a["id"]):
        raise Fehler(f"Layout wird verwendet von: {', '.join(nutzer(e, a['id']))} – erst dort ein anderes zuweisen")
    if len(e["layouts"]) < 2:
        raise Fehler("das letzte Layout kann nicht gelöscht werden")
    post("/api/einstellungen", {"layouts": [l for l in e["layouts"] if l["id"] != a["id"]]})
    return {"geloescht": a["id"], "zurueckholen": "list_layout_versions mit dieser id, dann restore_layout_version nr 0"}


def w_list_layout_versions(a):
    d = get("/api/layouts/versionen", id=a.get("id", ""))
    return {"versionen": [dict(v, zeit=time.strftime("%Y-%m-%d %H:%M", time.localtime(v["zeit"]))) for v in d["versionen"]],
            "geloeschte_layouts": [dict(g, zeit=time.strftime("%Y-%m-%d %H:%M", time.localtime(g["zeit"]))) for g in d["geloescht"]]}


def w_restore_layout_version(a):
    post("/api/layouts/wiederherstellen", {"id": a["id"], "nr": int(a.get("nr", 0))})
    return {"wiederhergestellt": a["id"]}


def w_set_tv_layout(a):
    def f(t, e):
        layout_pruefen(e, a["layout"])
        t["layout"] = a["layout"]
    t = tv_aendern(a["tv"], f)
    return {"tv": t["id"], "layout": t["layout"], "hinweis": "Zeitplan und Karussell haben Vorrang" if t.get("zeitplan") or
            (t.get("karussell") or {}).get("aktiv") else ""}


def w_set_tv_schedule(a):
    def f(t, e):
        for z in a["schedule"]:
            if z.get("layout") != "schwarz":
                layout_pruefen(e, z.get("layout"))
        t["zeitplan"] = [{"von": z["von"], "bis": z["bis"], "layout": z["layout"]} for z in a["schedule"]]
    return {"tv": a["tv"], "zeitplan": tv_aendern(a["tv"], f)["zeitplan"]}


def w_set_tv_carousel(a):
    def f(t, e):
        for lid in a.get("layouts") or []:
            layout_pruefen(e, lid)
        k = dict(t.get("karussell") or {})
        k.update({"aktiv": bool(a["active"])})
        if a.get("layouts") is not None:
            k["layouts"] = a["layouts"]
        if a.get("minutes"):
            k["minuten"] = int(a["minutes"])
        t["karussell"] = k
    return {"tv": a["tv"], "karussell": tv_aendern(a["tv"], f)["karussell"]}


def w_preview(a):
    q = {"tv": a.get("tv") or ""}
    if a.get("layout"):
        q["layout"] = a["layout"]
    if a.get("notes") is False:                       # nur das Bild (wie bis 0.59)
        b, typ = anfrage("GET", "/api/vorschau/bild?" + urllib.parse.urlencode(q), roh=True)
        if not typ.startswith("image/"):
            raise Fehler(json.loads(b).get("fehler") or "keine Vorschau")
        return {"_bild": base64.b64encode(b).decode(), "_typ": typ}
    r = get("/api/vorschau/pruefen", **q)            # seit 0.60: Bild und Lesbarkeits-Hinweise in einem Lauf
    return {"_bild": r["bild"], "_typ": "image/png",
            "_text": {"layout": r.get("layout"), "notes": hinweise_text(r.get("hinweise")),
                      "measured": r.get("gemessen"),
                      "rules": "main text at least 18 px (1080p), no text under 12 px, contrast at least 3:1, content fits, nothing fully covered, at most one live video"}}


def w_send_ticker(a):
    e = einst()
    post("/api/meldung", {"text": a["text"], "fernseher": fernseher_ids(e, a.get("tvs")), "dauer_s": int(a.get("minutes", 60)) * 60,
                          "stil": "warnung" if a.get("warning") else "info"})
    return {"gesendet": True, "erscheint_in_s": 15}


def w_end_ticker(a):
    post("/api/meldung", {"aus": True, "fernseher": fernseher_ids(einst(), a.get("tvs"))})
    return {"beendet": True}


def w_show_layout_for_a_while(a):
    e = einst()
    layout_pruefen(e, a["layout"])
    post("/api/layout-vorrang", {"layout": a["layout"], "fernseher": fernseher_ids(e, a.get("tvs")), "minuten": int(a.get("minutes", 60))})
    return {"gezeigt": a["layout"], "minuten": int(a.get("minutes", 60))}


def w_end_layout_for_a_while(a):
    post("/api/layout-vorrang", {"aus": True, "fernseher": fernseher_ids(einst(), a.get("tvs"))})
    return {"beendet": True}


def w_announce(a):
    e = einst()
    d = post("/api/durchsage", {"text": a["text"], "fernseher": fernseher_ids(e, a.get("tvs")), "vorlesen": bool(a.get("read_aloud")),
                                "dauer_s": int(a.get("seconds") or 60)})
    return {"gesendet": d.get("id")}


def w_list_media(a):
    return [{k: m.get(k) for k in ("id", "name", "art", "dauer_s", "aktiv")} for m in einst()["medien"]]


def w_upload_picture(a):
    roh, typ = bild_laden(a.get("url"), a.get("data_base64"))
    if a.get("target", "layout") == "layout":
        d = post("/api/bilder", {"daten": f"data:{typ};base64," + base64.b64encode(roh).decode()})
        return {"bild": d["bild"], "verwendung": "als optionen.bild eines logo-Bausteins oder als hintergrund.bild"}
    kennung = "mcp" + os.urandom(6).hex()
    stueck = 1024 * 1024
    teile = [roh[i:i + stueck] for i in range(0, len(roh), stueck)] or [b""]
    for nr, t in enumerate(teile):
        d = post("/api/medien/teil", {"kennung": kennung, "nr": nr, "daten": base64.b64encode(t).decode(),
                                      "fertig": nr == len(teile) - 1, "name": (a.get("name") or "Bild")[:60]})
    return {"medium": {k: d["medium"].get(k) for k in ("id", "name", "art", "dauer_s")}}


def w_set_media(a):
    e = einst()
    m = next((m for m in e["medien"] if m["id"] == a["id"]), None)
    if not m:
        raise Fehler(f"unbekanntes Medium {a['id']}")
    if "active" in a:
        m["aktiv"] = bool(a["active"])
    if a.get("duration_s"):
        m["dauer_s"] = int(a["duration_s"])
    if a.get("name"):
        m["name"] = str(a["name"])[:60]
    post("/api/einstellungen", {"medien": e["medien"]})
    return {k: m.get(k) for k in ("id", "name", "art", "dauer_s", "aktiv")}


def w_delete_media(a):
    post("/api/medien/loeschen", {"id": a["id"]})
    return {"geloescht": a["id"]}


def w_list_streams(a):
    liste = get("/api/streams").get("streams") or []
    aus = []
    for s in liste:
        if a.get("category") and s.get("kategorie") != a["category"]:
            continue
        aus.append({k: s.get(k) for k in ("id", "name", "kategorie", "aktiv", "geschuetzt", "zustand", "in_rotation", "tag")
                    if k in s})
    return {"anzahl": len(aus), "streams": aus[:int(a.get("limit", 100))]}


def w_add_stream(a):
    return post("/api/streams", {"link": a["link"], "name": a.get("name"), "kategorie": a.get("category", "neu")}).get("stream")


def w_update_stream(a):
    f = {}
    for k_en, k in (("active", "aktiv"), ("protected", "geschuetzt"), ("category", "kategorie"), ("name", "name")):
        if k_en in a:
            f[k] = a[k_en]
    return post(f"/api/streams/{a['id']}", f).get("stream")


def w_remove_stream(a):
    return post(f"/api/streams/{a['id']}/entfernen", {"ablehnen": bool(a.get("reject"))}).get("stream") or {"entfernt": a["id"]}


def w_get_source_data(a):
    d = get("/api/quellen/daten", id=a["id"])
    return {"daten": d.get("daten"), "fehler": d.get("fehler")}


def w_add_source_from_curl(a):
    q = post("/api/quellen/curl", {"befehl": a["curl"]})["quelle"]
    e = einst()
    if any(x["id"] == a["id"] for x in e["quellen"]):
        raise Fehler(f"Datenquelle {a['id']} gibt es schon")
    q.update({"id": a["id"], "name": a.get("name") or a["id"]})
    if a.get("interval_s"):
        q["intervall_s"] = int(a["interval_s"])
    post("/api/einstellungen", {"quellen": e["quellen"] + [q]})
    return {"angelegt": a["id"], "hinweis": "Werte nach dem ersten Abruf mit get_source_data ansehen"}


def w_get_log(a):
    return get("/api/protokoll")["eintraege"][:int(a.get("limit", 50))]


# ---------- seit 0.60: Lesbarkeit, Vorlagen, Datenquellen, Dateien, Galerie, Themen, Automatik, Einspieler, Radio ----------
HINWEIS_TEXT = {
    "klein": lambda h: f"text small ({h.get('px')} px at 1080p) – hard to read from about 3 m; make the element bigger or the text shorter",
    "kontrast": lambda h: f"low contrast {h.get('wert')}:1 between text and its background (at least 3:1)",
    "ueberlauf": lambda h: "content does not fit into the element",
    "verdeckt": lambda h: f"completely covered by element {h.get('von')}",
    "videos": lambda h: f"{h.get('n')} live videos in the layout – each one costs computing time on the server or player",
}


def hinweise_text(liste):
    return [{"element": h.get("baustein"), "type": h.get("typ"), "note": HINWEIS_TEXT.get(h.get("art"), lambda h: h.get("art"))(h)}
            for h in liste or []]


def kennung(muster_laenge=8):
    import secrets
    return "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(muster_laenge))


def slug(name, laenge=12):
    s = re.sub(r"[^a-z0-9]", "", name.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss"))
    s = re.sub(r"^[0-9]+", "", s)[:laenge]
    return s if len(s) >= 2 else "k" + kennung(5)


TEIL = 3 * 1024 * 1024
DATEI_MAX = {"pdf": 100 * 1024 * 1024, "gallery": 100 * 1024 * 1024, "media": 500 * 1024 * 1024, "source": 1024 * 1024}


def stuecke(url, daten_base64, max_b):
    """(gesamt, Iterator über Bytes-Stücke) aus einer http(s)-Adresse oder Base64 – höchstens max_b Bytes."""
    if bool(url) == bool(daten_base64):
        raise Fehler("genau eines von url oder data_base64 angeben")
    if daten_base64:
        roh = base64.b64decode(re.sub(r"^data:[^,]*,", "", daten_base64), validate=False)
        if len(roh) > max_b:
            raise Fehler(f"größer als {max_b // 2 ** 20} MB")
        return len(roh), iter([roh[i:i + TEIL] for i in range(0, len(roh), TEIL)] or [b""])
    if not re.match(r"https?://", url):
        raise Fehler("nur http:// oder https://")
    a = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "SignageCast-MCP"}), timeout=60)
    gesamt = int(a.headers.get("Content-Length") or 0)
    if gesamt > max_b:
        a.close()
        raise Fehler(f"größer als {max_b // 2 ** 20} MB")

    def lesen():
        n = 0
        with a:
            while True:
                b = a.read(TEIL)
                if not b:
                    return
                n += len(b)
                if n > max_b:
                    raise Fehler(f"größer als {max_b // 2 ** 20} MB")
                yield b
    return gesamt, lesen()


def teile_hochladen(gesamt, it, **extra):
    """Wie die Verwaltung: in Stücken an /api/medien/teil (zweck pdf, galerie oder eigene Medien)."""
    k, nr, r = kennung(10), 0, {}
    stueck = next(it, b"")
    while True:
        folgt = next(it, None)
        r = post("/api/medien/teil", dict(extra, kennung=k, nr=nr, daten=base64.b64encode(stueck).decode(), fertig=folgt is None, gesamt=gesamt))
        if folgt is None:
            return r
        stueck, nr = folgt, nr + 1


def w_list_templates(a):
    return [{"id": v["id"], "name": v["name"], "elements": sorted({e["typ"] for e in v.get("elemente", [])}),
             "background": (v.get("hintergrund") or {}).get("art")} for v in get("/api/vorlagen")["vorlagen"]]


def w_create_layout_from_template(a):
    v = next((x for x in get("/api/vorlagen")["vorlagen"] if x["id"] == a["template"]), None)
    if not v:
        raise Fehler(f"unbekannte Vorlage {a['template']} (list_templates)")
    l = json.loads(json.dumps(v))
    l.pop("id", None)
    l["name"] = a.get("name") or v["name"]
    return w_save_layout({"layout": l})


QUELL_ART = {"json": "json", "text": "text", "rss": "rss", "picture": "bild", "ical": "ical", "camera": "video", "csv": "csv"}
QUELL_ART_EN = {v: k for k, v in QUELL_ART.items()}


def quellen_speichern(liste):
    post("/api/einstellungen", {"quellen": liste})


def quelle_finden(e, qid):
    q = next((x for x in e["quellen"] if x["id"] == qid), None)
    if not q:
        raise Fehler(f"unbekannte Datenquelle {qid} (vorhanden: {', '.join(x['id'] for x in e['quellen']) or '–'})")
    return q


def quelle_benutzt(e, qid):
    muster = re.compile(r"\{" + re.escape(qid) + r"[:}]")
    aus = []
    for l in e["layouts"]:
        for el in l.get("elemente", []):
            o = el.get("optionen") or {}
            if o.get("quelle") == qid or (el.get("bedingung") or {}).get("quelle") == qid or any(isinstance(w, str) and muster.search(w) for w in o.values()):
                aus.append(l["name"])
                break
    return aus


def w_list_sources(a):
    e, st = einst(), {}
    try:
        st = get("/api/quellen/status").get("status") or {}
    except Fehler:
        pass
    return [{"id": q["id"], "name": q.get("name"), "kind": QUELL_ART_EN.get(q.get("art"), q.get("art")), "from": q.get("herkunft", "url"),
             "url": q.get("url") or (q.get("datei") or {}).get("name") or "", "interval_s": q.get("intervall_s"), "active": q.get("aktiv", True),
             "used_in": quelle_benutzt(e, q["id"]), "last_fetch": (st.get(q["id"]) or {}).get("abruf"), "error": (st.get(q["id"]) or {}).get("fehler"),
             "last_value": (st.get(q["id"]) or {}).get("kurz")}
            for q in e["quellen"]]


def w_add_source(a):
    e = einst()
    if any(x["id"] == a["id"] for x in e["quellen"]):
        raise Fehler(f"Datenquelle {a['id']} gibt es schon")
    art = QUELL_ART.get(a.get("kind", "json"))
    if not art or art == "csv":
        raise Fehler("kind: json, text, rss, picture, ical or camera (CSV files: upload_file target 'source')")
    q = {"id": a["id"], "name": a.get("name") or a["id"], "art": art, "url": a["url"], "intervall_s": int(a.get("interval_s") or 300), "aktiv": True}
    t = post("/api/quellen/test", {"quelle": q})
    quellen_speichern(e["quellen"] + [q])
    werte = t.get("daten") if art != "bild" else (t.get("daten") or {}).get("bild")
    text = json.dumps(werte, ensure_ascii=False)
    return {"angelegt": a["id"], "test_ms": t.get("dauer_ms"),
            "werte_vorschau": werte if len(text) <= 1500 else text[:1500] + " …",          # ganze Antwort: get_source_data
            "hinweis": "paths for elements: get_source_data"}


def w_update_source(a):
    e = einst()
    q = quelle_finden(e, a["id"])
    for en, k in (("name", "name"), ("url", "url"), ("interval_s", "intervall_s"), ("active", "aktiv")):
        if en in a:
            q[k] = a[en]
    if "url" in a and q.get("herkunft", "url") != "url":
        raise Fehler("this source reads a file – upload a new one with upload_file target 'source'")
    quellen_speichern(e["quellen"])
    return {k: q.get(k) for k in ("id", "name", "url", "intervall_s", "aktiv")}


def w_delete_source(a):
    e = einst()
    quelle_finden(e, a["id"])
    benutzt = quelle_benutzt(e, a["id"])
    if benutzt and not a.get("confirm_in_use"):
        raise Fehler(f"used in layouts: {', '.join(benutzt)} – their values would disappear. Ask the user, then call again with confirm_in_use true")
    quellen_speichern([x for x in e["quellen"] if x["id"] != a["id"]])
    return {"geloescht": a["id"], "layouts_ohne_werte": benutzt}


def w_fetch_source_now(a):
    quelle_finden(einst(), a["id"])
    post("/api/quellen/jetzt", {"id": a["id"]})
    return {"abruf": "started – read the result with get_source_data in a few seconds"}


def w_upload_file(a):
    ziel = a["target"]
    gesamt, it = stuecke(a.get("url"), a.get("data_base64"), DATEI_MAX[ziel])
    name = (a.get("name") or os.path.basename(urllib.parse.urlparse(a.get("url") or "").path) or "datei")[:80]
    if ziel == "pdf":
        r = teile_hochladen(gesamt, it, zweck="pdf", name=name)
        return {"pdf": r.get("pdf"), "seiten": r.get("seiten"), "hinweis": "use as option 'datei' of a 'pdf' element"}
    if ziel == "media":
        r = teile_hochladen(gesamt, it, zweck="", name=re.sub(r"\.[^.]+$", "", name))
        m = r.get("medium") or {}
        return {"medium": {k: m.get(k) for k in ("id", "name", "art", "dauer_s", "aktiv")}}
    if ziel == "gallery":
        e = einst()
        if a.get("folder") not in {o["id"] for o in e["galerie"]["ordner"]}:
            raise Fehler("folder: id of a gallery folder (list_gallery, create_gallery_folder)")
        r = teile_hochladen(gesamt, it, zweck="galerie", ordner=a["folder"], name=name)
        return {"ordner": a["folder"], "eintrag": r.get("eintrag")}
    # Datenquelle aus einer Datei (JSON, Text, RSS, iCal, CSV; höchstens 1 MB)
    roh = b"".join(it)
    qid = a.get("source_id") or ""
    if not re.fullmatch(r"[a-z0-9_]{2,16}", qid):
        raise Fehler("source_id: 2-16 characters a-z, 0-9, _")
    d = post("/api/quellen/datei", {"daten": base64.b64encode(roh).decode(), "name": name})
    e = einst()
    alt = next((x for x in e["quellen"] if x["id"] == qid), None)
    q = alt or {"id": qid, "name": a.get("source_name") or qid, "intervall_s": 3600, "aktiv": True}
    q.update(herkunft="datei", datei={"hash": d["datei"]["hash"], "name": d["datei"]["name"]}, url="", art=d.get("art") or "text")
    if q["art"] == "csv":
        an = post("/api/csv/analysieren", {"datei": d["datei"]["hash"]})
        q["csv"] = dict(an["optionen"], felder=[{"spalte": s["nr"], "name": s["name"]} for s in an["spalten"]])
    quellen_speichern(([x for x in e["quellen"] if x["id"] != qid]) + [q])
    return {"quelle": qid, "art": QUELL_ART_EN.get(q["art"], q["art"]), "ersetzt": bool(alt), "hinweis": "values: get_source_data"}


def w_list_gallery(a):
    g = get("/api/galerie")
    aus = {"ordner": [{k: o.get(k) for k in ("id", "name", "anzahl", "bytes", "quelle") if k in o} for o in g.get("ordner", [])]}
    if a.get("folder"):
        aus["eintraege"] = [{k: x.get(k) for k in ("id", "name", "art", "seiten") if k in x}
                            for x in get("/api/galerie/ordner", id=a["folder"]).get("eintraege", [])]
    return aus


def w_create_gallery_folder(a):
    r = post("/api/galerie/ordner", {"aktion": "neu", "name": a["name"]})
    return {"ordner": r["id"], "name": a["name"]}


def w_delete_gallery_folder(a):
    post("/api/galerie/ordner", {"aktion": "loeschen", "id": a["id"]})
    return {"geloescht": a["id"]}


def w_delete_gallery_items(a):
    r = post("/api/galerie/loeschen", {"ordner": a["folder"], "ids": a["ids"]})
    return {"ordner": a["folder"], "verbleibend": len(r.get("eintraege") or [])}


def w_list_topics(a):
    e = einst()
    aus_global = set(e["video"].get("kategorien_aus") or [])
    zahl = {}
    for s in get("/api/streams").get("streams", []):
        zahl[s.get("kategorie")] = zahl.get(s.get("kategorie"), 0) + 1
    return [{"id": k["id"], "name": k.get("name") or k["id"], "group": "animals" if k.get("gruppe") == "tiere" else "themes",
             "builtin": k.get("eingebaut"), "active": k["id"] not in aus_global, "search_terms": k.get("begriffe"),
             "title_words": k.get("woerter"), "ignore_daylight": k.get("ohne_tag"), "streams": zahl.get(k["id"], 0),
             "off_on_tvs": [t["id"] for t in e["fernseher"] if k["id"] in (t.get("kategorien_aus") or [])]} for k in e["kategorien"]]


def w_save_topic(a):
    e = einst()
    ks = e["kategorien"]
    kid = a.get("id") or ""
    k = next((x for x in ks if x["id"] == kid), None) if kid else None
    if kid and not k:
        raise Fehler(f"unbekanntes Thema {kid} (list_topics)")
    if not k:
        if not a.get("name"):
            raise Fehler("name is needed for a new topic")
        kid = slug(a["name"])
        while any(x["id"] == kid for x in ks):
            kid = kid[:9] + kennung(3)
        k = {"id": kid, "name": a["name"], "gruppe": "themen", "begriffe": [], "woerter": [], "ohne_tag": False, "ohne_tag_woerter": []}
        ks.append(k)
    for en, f in (("name", "name"), ("search_terms", "begriffe"), ("title_words", "woerter"), ("ignore_daylight", "ohne_tag")):
        if en in a:
            k[f] = a[en]
    if "group" in a:
        k["gruppe"] = "tiere" if a["group"] == "animals" else "themen"
    k.pop("standard", None) if any(en in a for en in ("search_terms", "title_words", "ignore_daylight", "group")) else None
    neu = {"kategorien": ks}
    if "active" in a:
        aus = [x for x in e["video"].get("kategorien_aus") or [] if x != kid] + ([] if a["active"] else [kid])
        neu["video"] = {"kategorien_aus": aus, "kategorien_bekannt": [x["id"] for x in ks]}
    post("/api/einstellungen", neu)
    return next(x for x in w_list_topics({}) if x["id"] == kid)


def w_delete_topic(a):
    r = post("/api/kategorien/loeschen", {"id": a["id"], "ziel": a.get("move_to") or "neu"})
    return {"geloescht": a["id"], "streams_verschoben": r.get("verschoben")}


def w_set_tv_topics(a):
    ids = {k["id"] for k in einst()["kategorien"]}
    falsch = [x for x in a["off"] if x not in ids]
    if falsch:
        raise Fehler(f"unbekannte Themen: {', '.join(falsch)}")
    return {"tv": a["tv"], "aus": tv_aendern(a["tv"], lambda t, e: t.update(kategorien_aus=list(a["off"])))["kategorien_aus"]}


VIDEO_FELDER = (("minutes_per_stream", "takt_min"), ("daytime_only", "nur_tag"), ("min_quality", "mindeststufe"), ("videos_active", "aktiv"))
SUCHE_FELDER = (("search_active", "aktiv"), ("search_time", "uhrzeit"), ("search_max", "max"), ("keep_days", "behalten_tage"),
                ("search_terms", "begriffe"), ("exclude_words", "ausschluss"))


def w_get_video_settings(a):
    e = einst()
    return dict({en: e["video"].get(k) for en, k in VIDEO_FELDER}, **{en: e["suche"].get(k) for en, k in SUCHE_FELDER},
                quality_levels=["small", "medium", "large", "hd720", "hd1080", "hd1440", "hd2160"])


def w_update_video_settings(a):
    neu = {}
    for teil, felder in (("video", VIDEO_FELDER), ("suche", SUCHE_FELDER)):
        x = {k: a[en] for en, k in felder if en in a}
        if x:
            neu[teil] = x
    if not neu:
        raise Fehler("nothing to change")
    post("/api/einstellungen", neu)
    return w_get_video_settings({})


def w_run_stream_search_now(a):
    """Die Suche dauert oft länger als eine MCP-Antwort warten darf – im Hintergrund starten, der Dienst sucht zu Ende."""
    def suchen():
        try:
            post("/api/suche/starten", {})
        except Fehler:
            pass
    threading.Thread(target=suchen, daemon=True).start()
    return {"gestartet": True, "hinweis": "takes a few minutes; new streams then appear in list_streams (topic 'neu' or the matching topic)"}


EP_FELDER = (("name", "name"), ("source", "quelle"), ("url", "url"), ("minutes", "minuten"), ("from", "von"), ("to", "bis"),
             ("sound", "ton"), ("tvs", "fernseher"), ("active", "aktiv"))


def w_list_clips(a):
    r = get("/api/einspieler")
    return [dict({en: x.get(k) for en, k in EP_FELDER}, id=x["id"], ready=x["id"] in (r.get("stand") or {})) for x in r["einspieler"]]


def w_save_clip(a):
    e = einst()
    ls = e["einspieler"]
    x = next((c for c in ls if c["id"] == a.get("id")), None) if a.get("id") else None
    if a.get("id") and not x:
        raise Fehler(f"unbekannter Einspieler {a['id']} (list_clips)")
    if not x:
        x = {"id": kennung(8), "quelle": "tagesschau100", "minuten": [0], "aktiv": True}
        ls.append(x)
    for en, k in EP_FELDER:
        if en in a:
            x[k] = a[en]
    if x.get("fernseher"):
        fernseher_ids(e, x["fernseher"])
    post("/api/einstellungen", {"einspieler": ls})
    return next(c for c in w_list_clips({}) if c["id"] == x["id"])


def w_delete_clip(a):
    e = einst()
    if not any(c["id"] == a["id"] for c in e["einspieler"]):
        raise Fehler(f"unbekannter Einspieler {a['id']}")
    post("/api/einstellungen", {"einspieler": [c for c in e["einspieler"] if c["id"] != a["id"]]})
    return {"geloescht": a["id"]}


def w_play_clip_now(a):
    post(f"/api/einspieler/{a['id']}/jetzt", {})
    return {"gestartet": a["id"], "erscheint_in_s": 15}


TON = {"off": "aus", "radio": "radio", "cams": "tiere"}
TON_EN = {v: k for k, v in TON.items()}


def w_list_radio(a):
    e = einst()
    return {"stations": e["radio"]["sender"], "show_station_name": e["radio"].get("anzeigen"),
            "tvs": [{"tv": t["id"], "sound": TON_EN.get(t["ton"], t["ton"]), "station": t.get("radio_sender"), "volume": t.get("lautstaerke")}
                    for t in e["fernseher"]]}


def w_search_radio(a):
    return [{k: s.get(k) for k in ("name", "url", "land", "region", "stichworte", "bitrate", "codec") if k in s} for s in get("/api/radio/suche", name=a["name"]).get("sender", [])[:20]]


def w_add_radio_station(a):
    s = post("/api/radio/sender", {"name": a.get("name"), "url": a["url"]})["sender"]
    return s


def w_remove_radio_station(a):
    post(f"/api/radio/sender/{a['id']}/entfernen", {})
    return {"entfernt": a["id"]}


def w_set_tv_sound(a):
    def f(t, e):
        if "sound" in a:
            if a["sound"] not in TON:
                raise Fehler("sound: off, radio or cams")
            t["ton"] = TON[a["sound"]]
        if "station" in a:
            if a["station"] and a["station"] not in {s["id"] for s in e["radio"]["sender"]}:
                raise Fehler("station: id from list_radio")
            t["radio_sender"] = a["station"]
        if "volume" in a:
            t["lautstaerke"] = int(a["volume"])
    t = tv_aendern(a["tv"], f)
    return {"tv": t["id"], "sound": TON_EN.get(t["ton"]), "station": t.get("radio_sender"), "volume": t.get("lautstaerke")}


PLAYER_BERICHT = ("version", "modell", "netz", "zustand", "temperatur", "hdmi", "modus_ist", "browser", "rueckfall", "schreibschutz", "laufzeit")


def w_list_players(a):
    """Player nur lesen (seit 0.44): ohne Schlüssel, WLAN, IP-Adressen und Terminal-Inhalte."""
    aus = []
    for g in get("/api/player").get("geraete", []):
        b = g.get("bericht") or {}
        aus.append({"id": g["id"], "name": g.get("name"), "modell": g.get("modell"), "tv": g.get("tv"), "online": g.get("online"),
                    "letzte_meldung_vor_s": g.get("zuletzt_vor"), "anzeige_modus_soll": g.get("anzeige_modus"),
                    "bericht": {k: b[k] for k in PLAYER_BERICHT if k in b}, "hinweise": g.get("hinweise") or [],
                    "fernverwaltung": [{k: e.get(k) for k in ("art", "was", "wert", "wer", "gesendet", "abgeholt", "fertig", "ok", "hinweis")}
                                       for e in (g.get("verlauf") or [])[:int(a.get("limit", 5))]]})
    return aus


S, I, B, O, A = ({"type": "string"}, {"type": "integer"}, {"type": "boolean"}, {"type": "object"},
                 {"type": "array", "items": {"type": "string"}})
TVS = dict(A, description="TV ids; empty = all TVs")


def schema(eigen, pflicht=()):
    return {"type": "object", "properties": eigen, "required": list(pflicht), "additionalProperties": False}


# name: (Funktion, Beschreibung, Schema, ändert etwas?)
WERKZEUGE = {
    "status": (w_status, "Overview: version, internet, each TV with its current layout, playback and picture check, open problems.", schema({}), False),
    "list_tvs": (w_list_tvs, "All TVs with base layout, schedule, carousel, video and sound settings.", schema({}), False),
    "list_layouts": (w_list_layouts, "All layouts with element types and which TVs use them.", schema({}), False),
    "get_layout": (w_get_layout, "Complete JSON of one layout.", schema({"id": S}, ["id"]), False),
    "get_layout_format": (w_get_layout_format, "Description of the layout JSON format (grid, element types, options). Read before save_layout.", schema({}), False),
    "save_layout": (w_save_layout, "Create a new layout or replace one (replace_id). Invalid parts are repaired and listed in 'hinweise'. "
                    "The previous version is kept.", schema({"layout": dict(O, description="layout object (or JSON text)"),
                                                            "replace_id": dict(S, description="id of the layout to replace; empty = new layout")}, ["layout"]), True),
    "delete_layout": (w_delete_layout, "Delete a layout that no TV uses (can be restored from its versions).", schema({"id": S}, ["id"]), True),
    "list_layout_versions": (w_list_layout_versions, "Earlier versions of a layout (newest first, nr 0) and deleted layouts.", schema({"id": S}), False),
    "restore_layout_version": (w_restore_layout_version, "Restore version nr of a layout (also brings back a deleted layout).",
                               schema({"id": S, "nr": I}, ["id", "nr"]), True),
    "set_tv_layout": (w_set_tv_layout, "Set the base layout of a TV.", schema({"tv": S, "layout": S}, ["tv", "layout"]), True),
    "set_tv_schedule": (w_set_tv_schedule, "Replace the schedule of a TV: list of {von: 'HH:MM', bis: 'HH:MM', layout: id or 'schwarz'}; empty list removes it.",
                        schema({"tv": S, "schedule": {"type": "array", "items": O}}, ["tv", "schedule"]), True),
    "set_tv_carousel": (w_set_tv_carousel, "Carousel of a TV: switch between layouts every N minutes (needs at least two layouts).",
                        schema({"tv": S, "active": B, "layouts": A, "minutes": I}, ["tv", "active"]), True),
    "preview": (w_preview, "Picture (960×540) of a TV page as it looks now – or with a given layout, without changing anything – plus "
                "readability notes per element (text too small for 3 m, low contrast, content does not fit, covered, several live videos), "
                "measured on the rendered page like the admin's layout editor. Fix the notes before putting a layout on a TV. Takes ~20 s.",
                schema({"tv": S, "layout": S, "notes": dict(B, description="false = only the picture")}), False),
    "send_ticker": (w_send_ticker, "Ticker message along the bottom of the TVs for N minutes (warning = red).",
                    schema({"text": S, "tvs": TVS, "minutes": I, "warning": B}, ["text"]), True),
    "end_ticker": (w_end_ticker, "End the ticker message.", schema({"tvs": TVS}), True),
    "show_layout_for_a_while": (w_show_layout_for_a_while, "Show a layout on TVs for N minutes (before schedule and carousel), then back by itself.",
                                schema({"layout": S, "tvs": TVS, "minutes": I}, ["layout"]), True),
    "end_layout_for_a_while": (w_end_layout_for_a_while, "Switch back to the normal layout now.", schema({"tvs": TVS}), True),
    "announce": (w_announce, "Announcement in the middle of the TVs (optionally read aloud).",
                 schema({"text": S, "tvs": TVS, "read_aloud": B, "seconds": I}, ["text"]), True),
    "list_media": (w_list_media, "Own pictures and videos for the video window.", schema({}), False),
    "upload_picture": (w_upload_picture, "Upload a JPG/PNG (url or data_base64, max 10 MB). target 'layout' returns a file name for logo/background; "
                       "'media' adds it to the own media.", schema({"url": S, "data_base64": S, "name": S,
                                                                   "target": {"type": "string", "enum": ["layout", "media"]}}), True),
    "set_media": (w_set_media, "Change an own medium: active, duration_s (pictures), name.", schema({"id": S, "active": B, "duration_s": I, "name": S}, ["id"]), True),
    "delete_media": (w_delete_media, "Delete an own medium.", schema({"id": S}, ["id"]), True),
    "list_streams": (w_list_streams, "Live cam streams with category and state.", schema({"category": S, "limit": I}), False),
    "add_stream": (w_add_stream, "Add a YouTube live stream (link) to a category.", schema({"link": S, "name": S, "category": S}, ["link"]), True),
    "update_stream": (w_update_stream, "Change a stream: active, protected, category, name.",
                      schema({"id": S, "active": B, "protected": B, "category": S, "name": S}, ["id"]), True),
    "remove_stream": (w_remove_stream, "Remove a stream; reject = never add it again by search.", schema({"id": S, "reject": B}, ["id"]), True),
    "list_sources": (w_list_sources, "Own data sources (JSON/RSS/iCal/CSV/pictures/cameras) with state, last value and the layouts using them.", schema({}), False),
    "get_source_data": (w_get_source_data, "Current answer of a data source (to find paths for apiwert/apiliste/{source:path}).",
                        schema({"id": S}, ["id"]), False),
    "add_source_from_curl": (w_add_source_from_curl, "Create a data source from a curl command (headers like Authorization are stored as secrets).",
                             schema({"curl": S, "id": dict(S, description="2-16 characters a-z, 0-9, _"), "name": S, "interval_s": I}, ["curl", "id"]), True),
    "add_source": (w_add_source, "Create a data source from an address (kind json, text, rss, picture, ical or camera); it is tested first. "
                   "For APIs with headers use add_source_from_curl, for files upload_file target 'source'.",
                   schema({"id": dict(S, description="2-16 characters a-z, 0-9, _"), "name": S, "kind": {"type": "string", "enum": ["json", "text", "rss", "picture", "ical", "camera"]},
                           "url": S, "interval_s": I}, ["id", "url"]), True),
    "update_source": (w_update_source, "Change a data source: name, url, interval_s, active (false = pause fetching).",
                      schema({"id": S, "name": S, "url": S, "interval_s": I, "active": B}, ["id"]), True),
    "delete_source": (w_delete_source, "Delete a data source. If layouts use it, ask the user first and pass confirm_in_use.",
                      schema({"id": S, "confirm_in_use": B}, ["id"]), True),
    "fetch_source_now": (w_fetch_source_now, "Fetch a data source now instead of waiting for its interval.", schema({"id": S}, ["id"]), True),
    "list_templates": (w_list_templates, "The ready layouts for places (living room, waiting room, reception, menu board, hospital, hotel, canteen …).", schema({}), False),
    "create_layout_from_template": (w_create_layout_from_template, "New layout as a copy of a template – then adapt it with get_layout/save_layout.",
                                    schema({"template": S, "name": S}, ["template"]), True),
    "upload_file": (w_upload_file, "Upload a file (url or data_base64). target 'pdf': PDF for a 'pdf' element (returns the name for option 'datei'); "
                    "'media': picture or video for the video window; 'gallery': picture or PDF into a gallery folder (folder); "
                    "'source': JSON/text/RSS/iCal/CSV file (max 1 MB) as data source source_id (new or replaced).",
                    schema({"target": {"type": "string", "enum": ["pdf", "media", "gallery", "source"]}, "url": S, "data_base64": S, "name": S,
                            "folder": S, "source_id": S, "source_name": S}, ["target"]), True),
    "list_gallery": (w_list_gallery, "Gallery folders (for the 'galerie' element and gallery backgrounds); with folder: its pictures and PDFs.",
                     schema({"folder": S}), False),
    "create_gallery_folder": (w_create_gallery_folder, "Create a gallery folder.", schema({"name": S}, ["name"]), True),
    "delete_gallery_folder": (w_delete_gallery_folder, "Delete a gallery folder with its content (not possible while a layout shows it). Ask the user first.",
                              schema({"id": S}, ["id"]), True),
    "delete_gallery_items": (w_delete_gallery_items, "Delete pictures/PDFs from a gallery folder (ids from list_gallery).",
                             schema({"folder": S, "ids": A}, ["folder", "ids"]), True),
    "list_topics": (w_list_topics, "Live video topics (categories): search terms, title words, on/off overall and per TV, number of streams.", schema({}), False),
    "save_topic": (w_save_topic, "Create (no id) or change a topic: name, group animals/themes, search_terms (YouTube search), title_words "
                   "(regular expressions, one must be in the title), ignore_daylight, active.",
                   schema({"id": S, "name": S, "group": {"type": "string", "enum": ["animals", "themes"]}, "search_terms": A, "title_words": A,
                           "ignore_daylight": B, "active": B}), True),
    "delete_topic": (w_delete_topic, "Delete an own topic; its streams move to move_to (default 'neu'). Built-in topics can only be switched off.",
                     schema({"id": S, "move_to": S}, ["id"]), True),
    "set_tv_topics": (w_set_tv_topics, "Topics switched off on one TV (list of topic ids; empty = all on).",
                      schema({"tv": S, "off": A}, ["tv", "off"]), True),
    "get_video_settings": (w_get_video_settings, "Live video rotation (minutes per stream, daytime only, minimum quality) and the automatic stream search "
                           "(time, max streams, keep days, search terms, exclude words).", schema({}), False),
    "update_video_settings": (w_update_video_settings, "Change live video rotation and automatic search (only the given fields).",
                              schema({"videos_active": B, "minutes_per_stream": I, "daytime_only": B, "min_quality": S, "search_active": B,
                                      "search_time": dict(S, description="HH:MM"), "search_max": I, "keep_days": I, "search_terms": A, "exclude_words": A}), True),
    "run_stream_search_now": (w_run_stream_search_now, "Run the automatic stream search now (takes a few minutes).", schema({}), True),
    "list_clips": (w_list_clips, "Clips at fixed times (e.g. tagesschau in 100 seconds on the hour) that interrupt the video window.", schema({}), False),
    "save_clip": (w_save_clip, "Create (no id) or change a clip: source tagesschau100/video/youtube, url (video address or YouTube id/link), "
                  "minutes (list 0-59), from/to (HH:MM), sound, tvs (empty = all), active.",
                  schema({"id": S, "name": S, "source": {"type": "string", "enum": ["tagesschau100", "video", "youtube"]}, "url": S,
                          "minutes": {"type": "array", "items": I}, "from": S, "to": S, "sound": B, "tvs": TVS, "active": B}), True),
    "delete_clip": (w_delete_clip, "Delete a clip.", schema({"id": S}, ["id"]), True),
    "play_clip_now": (w_play_clip_now, "Show a clip now on its TVs (to test it).", schema({"id": S}, ["id"]), True),
    "list_radio": (w_list_radio, "Internet radio stations and the sound of every TV (off, radio, cams = original sound of the live cams).", schema({}), False),
    "search_radio": (w_search_radio, "Search radio stations by name (radio-browser.info), playable ones only.", schema({"name": S}, ["name"]), False),
    "add_radio_station": (w_add_radio_station, "Add a radio station (stream address is checked).", schema({"name": S, "url": S}, ["url"]), True),
    "remove_radio_station": (w_remove_radio_station, "Remove a radio station.", schema({"id": S}, ["id"]), True),
    "set_tv_sound": (w_set_tv_sound, "Sound of a TV: off, radio (with station id) or cams; volume 0-100.",
                     schema({"tv": S, "sound": {"type": "string", "enum": ["off", "radio", "cams"]}, "station": S, "volume": I}, ["tv"]), True),
    "list_players": (w_list_players, "Raspberry Pi/PC players (read only): online, seconds since the last report, display mode wanted/actual, "
                     "temperature, hints and the newest remote management entries (sent → picked up → result).", schema({"limit": I}), False),
    "get_log": (w_get_log, "Change log (who changed what and when).", schema({"limit": I}), False),
}


# ---------- MCP-Nachrichten ----------
def antwort(mid, ergebnis=None, fehler=None):
    m = {"jsonrpc": "2.0", "id": mid}
    if fehler:
        m["error"] = fehler
    else:
        m["result"] = ergebnis
    return m


def nur_lesen():
    return bool(getattr(_lokal, "nur_lesen", False))


def werkzeug_liste():
    return [{"name": n, "description": b, "inputSchema": sch,
             "annotations": {"readOnlyHint": not aendert, "destructiveHint": n.startswith(("delete_", "remove_")), "openWorldHint": False}}
            for n, (_, b, sch, aendert) in WERKZEUGE.items() if not (aendert and nur_lesen())]


def aufrufen(name, args):
    if name not in WERKZEUGE:
        return {"content": [{"type": "text", "text": f"unbekanntes Werkzeug {name}"}], "isError": True}
    if WERKZEUGE[name][3] and nur_lesen():
        return {"content": [{"type": "text", "text": "This computer may only read (SignageCast admin → AI assistants)."}], "isError": True}
    try:
        erg = WERKZEUGE[name][0](args or {})
    except Fehler as f:
        return {"content": [{"type": "text", "text": str(f)}], "isError": True}
    except (KeyError, TypeError, ValueError) as f:
        return {"content": [{"type": "text", "text": f"ungültige Angaben: {f}"}], "isError": True}
    if isinstance(erg, dict) and "_bild" in erg:
        inhalt = [{"type": "image", "data": erg["_bild"], "mimeType": erg["_typ"]}]
        if erg.get("_text") is not None:
            inhalt.append({"type": "text", "text": json.dumps(erg["_text"], ensure_ascii=False, indent=1)})
        return {"content": inhalt}
    text = erg if isinstance(erg, str) else json.dumps(erg, ensure_ascii=False, indent=1)
    return {"content": [{"type": "text", "text": text}]}


def bearbeiten(m):
    """Eine JSON-RPC-Nachricht → Antwort (dict) oder None bei Benachrichtigungen."""
    if not isinstance(m, dict):
        return antwort(None, fehler={"code": -32600, "message": "ungültige Anfrage"})
    mid, methode, p = m.get("id"), m.get("method"), m.get("params") or {}
    if not isinstance(p, dict):
        return antwort(mid, fehler={"code": -32602, "message": "params"})
    if methode == "initialize":
        v = p.get("protocolVersion")
        return antwort(mid, {"protocolVersion": v if v in PROTOKOLL_VERSIONEN else PROTOKOLL_VERSIONEN[0],
                             "capabilities": {"tools": {"listChanged": False}},
                             "serverInfo": {"name": "signagecast", "title": "SignageCast", "version": VERSION},
                             "instructions": ANLEITUNG + (" This computer may only read." if nur_lesen() else "")})
    if mid is None:                                   # Benachrichtigungen (z. B. notifications/initialized)
        return None
    if methode == "ping":
        return antwort(mid, {})
    if methode == "tools/list":
        return antwort(mid, {"tools": werkzeug_liste()})
    if methode == "tools/call":
        return antwort(mid, aufrufen(p.get("name"), p.get("arguments")))
    return antwort(mid, fehler={"code": -32601, "message": f"unbekannte Methode {methode}"})


def sicher_bearbeiten(x):
    try:
        return bearbeiten(x)
    except Exception as f:                             # nie abbrechen – der Assistent bekommt den Fehler
        return antwort(x.get("id") if isinstance(x, dict) else None, fehler={"code": -32603, "message": str(f)[:300]})


def verarbeiten(m, wer, lesen_nur=False):
    """Für MCP über HTTP (seit 0.40): eine Nachricht oder ein Stapel → Antwort(en) oder None. wer steht im Protokoll."""
    _lokal.wer, _lokal.nur_lesen = wer, lesen_nur
    try:
        if isinstance(m, list):
            a = [x for x in (sicher_bearbeiten(y) for y in m[:50]) if x]
            return a or None
        return sicher_bearbeiten(m)
    finally:
        _lokal.wer, _lokal.nur_lesen = WER, False


def schreiben(m):
    if m is not None:
        sys.stdout.write(json.dumps(m, ensure_ascii=False) + "\n")
        sys.stdout.flush()


def main():
    for zeile in sys.stdin:
        zeile = zeile.strip()
        if not zeile:
            continue
        try:
            m = json.loads(zeile)
        except ValueError:
            schreiben(antwort(None, fehler={"code": -32700, "message": "kein JSON"}))
            continue
        for x in (m if isinstance(m, list) else [m]):
            schreiben(sicher_bearbeiten(x))


if __name__ == "__main__":
    main()
