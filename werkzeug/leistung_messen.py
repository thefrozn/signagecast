#!/usr/bin/env python3
"""SignageCast – Verbrauch messen (seit 0.29), im Container/auf dem Server ausführen, während ein Stream läuft:

    python3 /opt/signagecast/werkzeug/leistung_messen.py [--dauer 60] [--json ergebnis.json] [--vergleich alt.json]

Misst über die Dauer die CPU (in % eines Kerns) und den Arbeitsspeicher der Render-Ketten (Xvfb, Chromium, ffmpeg),
von MediaMTX und dem Datendienst sowie je Fernseher Bildrate, doppelte und verlorene Bilder aus dem Fortschritt von
ffmpeg. Mit --vergleich: Abweichung zu einer früheren Messung; Rückgabe 1, wenn CPU oder Arbeitsspeicher um mehr als
10 % (und mindestens 5 Prozentpunkte bzw. 50 MB) schlechter sind oder neue Bildverluste auftreten.
Nur Standardbibliothek, liest nur /proc und /dev/shm – ändert nichts."""
import argparse, glob, json, os, re, sys, time

TAKT = os.sysconf("SC_CLK_TCK")
GRUPPEN = [("chromium-gpu", re.compile(r"^chrom\S* .*--type=gpu-process")), ("chromium", re.compile(r"^chrom")), ("ffmpeg", re.compile(r"^ffmpeg")), ("xvfb", re.compile(r"^Xvfb")),
           ("mediamtx", re.compile(r"mediamtx")), ("dienst", re.compile(r"python3.*dienst\.py")),
           ("pulseaudio", re.compile(r"^pulseaudio"))]


def prozesse():
    """{pid: (gruppe, cpu_ticks, pss_kb)} aller Prozesse, die zu SignageCast gehören."""
    erg = {}
    for d in glob.glob("/proc/[0-9]*"):
        try:
            cmd = open(d + "/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace").strip()
            if not cmd:
                continue
            name = os.path.basename(cmd.split(" ")[0]) + cmd[len(cmd.split(" ")[0]):]
            gruppe = next((g for g, m in GRUPPEN if m.search(name)), None)
            if not gruppe:
                continue
            st = open(d + "/stat").read().rsplit(")", 1)[1].split()
            try:                                   # PSS: geteilter Speicher (Chromium!) anteilig, nicht mehrfach
                rss = next(int(z.split()[1]) for z in open(d + "/smaps_rollup") if z.startswith("Pss:"))
            except (OSError, StopIteration):
                rss = next((int(z.split()[1]) for z in open(d + "/status") if z.startswith("VmRSS:")), 0)
            erg[int(d[6:])] = (gruppe, int(st[11]) + int(st[12]), rss)
        except (OSError, ValueError, IndexError):
            continue
    return erg


def fortschritt():
    """{tv: {bilder, doppelt, verloren}} aus /dev/shm/signagecast-ff-<tv> (schreibt tv-render.sh alle 2 s)."""
    erg = {}
    for p in glob.glob("/dev/shm/signagecast-ff-*"):
        if p.endswith((".fifo", ".neu")):
            continue
        try:
            w = dict(z.split("=", 1) for z in open(p).read().split() if "=" in z)
            erg[p.rsplit("-ff-", 1)[1]] = {"bilder": int(w.get("frame", 0)), "doppelt": int(w.get("dup_frames", 0)),
                                           "verloren": int(w.get("drop_frames", 0))}
        except (OSError, ValueError):
            continue
    return erg


def messen(dauer):
    p0, f0, t0 = prozesse(), fortschritt(), time.time()
    rss_max = {}
    while time.time() - t0 < dauer:
        time.sleep(min(5, max(0.5, dauer - (time.time() - t0))))
        rss = {}
        for g, _, kb in prozesse().values():
            rss[g] = rss.get(g, 0) + kb
        for g, kb in rss.items():
            rss_max[g] = max(rss_max.get(g, 0), kb)
    p1, f1, dt = prozesse(), fortschritt(), time.time() - t0
    cpu = {}
    for pid, (g, ticks, _) in p1.items():
        vorher = p0.get(pid)
        d = ticks - (vorher[1] if vorher and vorher[0] == g else 0)
        cpu[g] = cpu.get(g, 0) + d
    gruppen = {g: {"cpu": round(100 * cpu.get(g, 0) / TAKT / dt, 1), "ram_mb": round(rss_max.get(g, 0) / 1024)}
               for g in sorted(set(cpu) | set(rss_max))}
    tvs = {}
    for tv, b in f1.items():
        a = f0.get(tv)
        if not a or b["bilder"] < a["bilder"]:
            continue                               # Kette erst während der Messung gestartet
        n = b["bilder"] - a["bilder"]
        tvs[tv] = {"fps": round(n / dt, 1), "doppelt": b["doppelt"] - a["doppelt"], "verloren": b["verloren"] - a["verloren"]}
    last = open("/proc/loadavg").read().split()[:3]
    return {"zeit": time.strftime("%Y-%m-%dT%H:%M:%S"), "dauer_s": round(dt), "kerne": os.cpu_count(),
            "last": [float(x) for x in last], "summe": {"cpu": round(sum(x["cpu"] for x in gruppen.values()), 1),
                                                       "ram_mb": sum(x["ram_mb"] for x in gruppen.values())},
            "gruppen": gruppen, "fernseher": tvs}


def vergleichen(alt, neu):
    """Liste der Verschlechterungen (leer = gut)."""
    schlecht = []
    a, n = alt["summe"], neu["summe"]
    if n["cpu"] > a["cpu"] * 1.1 and n["cpu"] - a["cpu"] >= 5:
        schlecht.append(f"CPU {a['cpu']} % -> {n['cpu']} %")
    if n["ram_mb"] > a["ram_mb"] * 1.1 and n["ram_mb"] - a["ram_mb"] >= 50:
        schlecht.append(f"RAM {a['ram_mb']} MB -> {n['ram_mb']} MB")
    for tv, x in neu["fernseher"].items():
        v = alt["fernseher"].get(tv, {"doppelt": 0, "verloren": 0})
        for k in ("doppelt", "verloren"):
            if x[k] > max(v[k] * 1.5, v[k] + 10):
                schlecht.append(f"{tv}: {k} {v[k]} -> {x[k]}")
    return schlecht


def main():
    ap = argparse.ArgumentParser(description="Verbrauch von SignageCast messen")
    ap.add_argument("--dauer", type=int, default=60)
    ap.add_argument("--json", help="Ergebnis zusätzlich als JSON speichern")
    ap.add_argument("--vergleich", help="frühere Messung (JSON) zum Vergleich")
    arg = ap.parse_args()
    e = messen(max(5, arg.dauer))
    print(f"Messung {e['zeit']} über {e['dauer_s']} s, {e['kerne']} Kerne, Last {e['last']}")
    print(f"{'Teil':<12}{'CPU %':>8}{'RAM MB':>9}")
    for g, x in e["gruppen"].items():
        print(f"{g:<12}{x['cpu']:>8}{x['ram_mb']:>9}")
    print(f"{'Summe':<12}{e['summe']['cpu']:>8}{e['summe']['ram_mb']:>9}")
    for tv, x in e["fernseher"].items():
        print(f"Fernseher {tv}: {x['fps']} Bilder/s, doppelt {x['doppelt']}, verloren {x['verloren']}")
    if not e["fernseher"]:
        print("Hinweis: kein laufender Stream gefunden – zum Messen einen Stream öffnen (z. B. ffmpeg -c copy).")
    if arg.json:
        with open(arg.json, "w") as f:
            json.dump(e, f, indent=1)
    if arg.vergleich:
        schlecht = vergleichen(json.load(open(arg.vergleich)), e)
        print("Vergleich: " + ("schlechter – " + "; ".join(schlecht) if schlecht else "nicht schlechter"))
        return 1 if schlecht else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
