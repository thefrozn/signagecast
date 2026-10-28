# Wache: liest über die DevTools-Schnittstelle der Render-Browser (nur 127.0.0.1, je Fernseher Port 9222 + Nummer) aus, was der YouTube-Player
# wirklich macht (Stufe, Codec, verlorene Bilder, Bandbreite, Puffer), und kann die TV-Seite neu laden.
# Läuft kein Stream, ist der Port zu – dann kostet die Wache praktisch nichts.
import base64, glob, json, os, socket, struct, time, urllib.request

BASIS_PORT = 9222
ORDNER = os.path.join(os.environ.get("SC_DATEN", "/var/lib/signagecast"), "wache")
AUFHEBEN_TAGE = 14

JS_MESSEN = r"""(() => {
  const v = document.querySelector('video'), p = document.getElementById('movie_player');
  if (!v || !p || !p.getStatsForNerds) return JSON.stringify(null);
  const q = v.getVideoPlaybackQuality ? v.getVideoPlaybackQuality() : {};
  let n = {}; try { n = p.getStatsForNerds(); } catch (e) {}
  let id = ''; try { id = p.getVideoData().video_id; } catch (e) {}
  return JSON.stringify({id, stufe: p.getPlaybackQuality(), angeboten: p.getAvailableQualityLevels(), zustand: p.getPlayerState(),
    breite: v.videoWidth, hoehe: v.videoHeight, bilder: q.totalVideoFrames || 0, verloren: q.droppedVideoFrames || 0,
    codec: (n.codecs || '').split(' ')[0], kbps: parseInt(n.bandwidth_kbps) || 0, puffer: parseFloat(n.buffer_health_seconds) || 0});
})()"""


def _senden(s, obj):
    d = json.dumps(obj).encode(); m = os.urandom(4); n = len(d)
    kopf = bytes([0x81]) + (bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack(">H", n))
    s.sendall(kopf + m + bytes(b ^ m[i % 4] for i, b in enumerate(d)))


def _lesen(s):
    def rd(k):
        b = b""
        while len(b) < k:
            t = s.recv(k - len(b))
            if not t:
                raise ConnectionError("geschlossen")
            b += t
        return b
    h = rd(2); n = h[1] & 0x7f
    if n == 126: n = struct.unpack(">H", rd(2))[0]
    elif n == 127: n = struct.unpack(">Q", rd(8))[0]
    return json.loads(rd(n))


def ziele(port):
    return json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3))


def befehl(port, ziel, methode, params):
    """Einen DevTools-Befehl an ein Ziel (Seite oder iframe) senden und die Antwort liefern."""
    pfad = ziel["webSocketDebuggerUrl"].split(str(port), 1)[1]
    with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
        s.sendall((f"GET {pfad} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                   f"Sec-WebSocket-Key: {base64.b64encode(os.urandom(16)).decode()}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        antwort = b""
        while b"\r\n\r\n" not in antwort:
            antwort += s.recv(1)
        _senden(s, {"id": 1, "method": methode, "params": params})
        while True:
            r = _lesen(s)
            if r.get("id") == 1:
                return r.get("result", {})


def messen(port):
    f = next((z for z in ziele(port) if z.get("type") == "iframe" and "youtube" in z.get("url", "")), None)
    if not f:
        return None
    r = befehl(port, f, "Runtime.evaluate", {"expression": JS_MESSEN, "returnByValue": True})
    return json.loads(r.get("result", {}).get("value") or "null")


def seite_neu_laden(port):
    f = next((z for z in ziele(port) if z.get("type") == "page" and ":8080" in z.get("url", "")), None)
    if not f:
        return False
    befehl(port, f, "Page.reload", {"ignoreCache": True})
    return True


def schleife(streams, zustand, fernseher, takt_s=10):
    """Alle 10 s je laufendem Fernseher messen, mitschreiben (JSONL je Tag, 14 Tage), an die Streamliste melden.
    fernseher: Funktion -> [(id, port)]."""
    os.makedirs(ORDNER, exist_ok=True)
    vorher, aufgeraeumt = {}, ""
    while True:
        jetzt = {}
        for tv, port in fernseher():
            try:
                m = messen(port)
            except Exception:
                m = None
            if m and m.get("id"):
                m["zeit"] = time.strftime("%Y-%m-%d %H:%M:%S")
                m["tv"] = tv
                jetzt[tv] = m
                try:
                    with open(os.path.join(ORDNER, time.strftime("%Y-%m-%d") + ".jsonl"), "a") as f:
                        f.write(json.dumps(m, ensure_ascii=False) + "\n")
                    streams.wache_melden(m, vorher.get(tv))
                except Exception:
                    pass
        zustand["wache"] = jetzt
        vorher = jetzt
        heute = time.strftime("%Y-%m-%d")
        if heute != aufgeraeumt:
            for alt in glob.glob(os.path.join(ORDNER, "*.jsonl")):
                if time.time() - os.path.getmtime(alt) > AUFHEBEN_TAGE * 86400:
                    os.remove(alt)
            aufgeraeumt = heute
        time.sleep(takt_s)
