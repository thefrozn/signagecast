#!/usr/bin/env python3
# SignageCast – MCP-Server (seit 0.39): Inhalte mit Claude oder einem anderen KI-Assistenten verwalten.
#
# Model Context Protocol über stdio (JSON-RPC 2.0, eine Nachricht je Zeile). Der Assistent startet den Server per SSH
# auf dem SignageCast-Rechner, z. B.  ssh tvadmin@signagecast.local signagecast-mcp  – angemeldet wird mit dem
# SSH-Schlüssel, es gibt keinen neuen Port und keinen Token. Im Container: docker exec -i signagecast signagecast-mcp.
#
# Der Server spricht nur mit der API des Datendienstes (127.0.0.1:8080, wie die Verwaltung). Er kann Inhalte lesen und
# ändern – Layouts, Zuweisung an Fernseher, Zeitplan, Karussell, Laufschrift, Durchsagen, Bilder, Streams, Datenquellen
# – aber bewusst nichts am System: keine Updates, keine Sicherungen, keine Player/Terminals, keine Passwörter oder
# Schlüssel. Jede Änderung steht im Änderungsprotokoll („MCP <Benutzer>“); Layouts bekommen vorher eine Version.
# Nur Python-Standardbibliothek.
import base64, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

PROTOKOLL_VERSIONEN = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
DIENST = f"http://127.0.0.1:{os.environ.get('SC_PORT', '8080')}"
BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = (open(os.path.join(BASIS, "VERSION")).read().strip() if os.path.exists(os.path.join(BASIS, "VERSION")) else "dev")
BILD_MAX = 10 * 1024 * 1024
WER = "MCP " + re.sub(r"[^\w.@-]", "", os.environ.get("SUDO_USER") or os.environ.get("USER") or os.environ.get("LOGNAME") or "ssh")[:30]

ANLEITUNG = (
    "SignageCast shows layouts on TVs. Typical flow: status → list_layouts / get_layout → change or create a layout with "
    "save_layout (read get_layout_format first; every change keeps a version, restore_layout_version undoes it) → "
    "preview to look at the result → set_tv_layout to put it on a TV. For short-term things use send_ticker, "
    "show_layout_for_a_while or announce. Pictures for layouts come from upload_picture (target 'layout'). "
    "Ask the user before deleting anything or changing what a TV shows right now.")


class Fehler(Exception):
    pass


# ---------- Zugriff auf den Datendienst ----------
def anfrage(methode, pfad, daten=None, roh=False):
    kopf = {"X-SignageCast": "1", "X-SignageCast-Benutzer": WER}
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
            "hinweise": [h.get("text") for h in r.get("hinweise") or []]}


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
    b, typ = anfrage("GET", "/api/vorschau/bild?" + urllib.parse.urlencode(q), roh=True)
    if not typ.startswith("image/"):
        raise Fehler(json.loads(b).get("fehler") or "keine Vorschau")
    return {"_bild": base64.b64encode(b).decode(), "_typ": typ}


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


def w_list_sources(a):
    e = einst()
    return [{k: q.get(k) for k in ("id", "name", "art", "url", "intervall_s") if k in q} for q in e["quellen"]]


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
    "preview": (w_preview, "Picture (960×540) of a TV page as it looks now – or with a given layout, without changing anything. Takes ~20 s.",
                schema({"tv": S, "layout": S}), False),
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
    "list_sources": (w_list_sources, "Own data sources (JSON/RSS/iCal/CSV/pictures) for values in layouts.", schema({}), False),
    "get_source_data": (w_get_source_data, "Current answer of a data source (to find paths for apiwert/apiliste/{source:path}).",
                        schema({"id": S}, ["id"]), False),
    "add_source_from_curl": (w_add_source_from_curl, "Create a data source from a curl command (headers like Authorization are stored as secrets).",
                             schema({"curl": S, "id": dict(S, description="2-16 characters a-z, 0-9, _"), "name": S, "interval_s": I}, ["curl", "id"]), True),
    "get_log": (w_get_log, "Change log (who changed what and when).", schema({"limit": I}), False),
}


# ---------- MCP über stdio ----------
def antwort(mid, ergebnis=None, fehler=None):
    m = {"jsonrpc": "2.0", "id": mid}
    if fehler:
        m["error"] = fehler
    else:
        m["result"] = ergebnis
    sys.stdout.write(json.dumps(m, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def werkzeug_liste():
    return [{"name": n, "description": b, "inputSchema": sch,
             "annotations": {"readOnlyHint": not aendert, "destructiveHint": n.startswith(("delete_", "remove_")), "openWorldHint": False}}
            for n, (_, b, sch, aendert) in WERKZEUGE.items()]


def aufrufen(name, args):
    if name not in WERKZEUGE:
        return {"content": [{"type": "text", "text": f"unbekanntes Werkzeug {name}"}], "isError": True}
    try:
        erg = WERKZEUGE[name][0](args or {})
    except Fehler as f:
        return {"content": [{"type": "text", "text": str(f)}], "isError": True}
    except (KeyError, TypeError, ValueError) as f:
        return {"content": [{"type": "text", "text": f"ungültige Angaben: {f}"}], "isError": True}
    if isinstance(erg, dict) and "_bild" in erg:
        return {"content": [{"type": "image", "data": erg["_bild"], "mimeType": erg["_typ"]}]}
    text = erg if isinstance(erg, str) else json.dumps(erg, ensure_ascii=False, indent=1)
    return {"content": [{"type": "text", "text": text}]}


def bearbeiten(m):
    mid, methode, p = m.get("id"), m.get("method"), m.get("params") or {}
    if methode == "initialize":
        v = p.get("protocolVersion")
        return antwort(mid, {"protocolVersion": v if v in PROTOKOLL_VERSIONEN else PROTOKOLL_VERSIONEN[0],
                             "capabilities": {"tools": {"listChanged": False}},
                             "serverInfo": {"name": "signagecast", "title": "SignageCast", "version": VERSION},
                             "instructions": ANLEITUNG})
    if mid is None:                                   # Benachrichtigungen (z. B. notifications/initialized)
        return None
    if methode == "ping":
        return antwort(mid, {})
    if methode == "tools/list":
        return antwort(mid, {"tools": werkzeug_liste()})
    if methode == "tools/call":
        return antwort(mid, aufrufen(p.get("name"), p.get("arguments")))
    return antwort(mid, fehler={"code": -32601, "message": f"unbekannte Methode {methode}"})


def main():
    for zeile in sys.stdin:
        zeile = zeile.strip()
        if not zeile:
            continue
        try:
            m = json.loads(zeile)
        except ValueError:
            antwort(None, fehler={"code": -32700, "message": "kein JSON"})
            continue
        for x in (m if isinstance(m, list) else [m]):
            try:
                bearbeiten(x)
            except Exception as f:                     # nie abbrechen – der Assistent bekommt den Fehler
                antwort(x.get("id") if isinstance(x, dict) else None, fehler={"code": -32603, "message": str(f)[:300]})


if __name__ == "__main__":
    main()
