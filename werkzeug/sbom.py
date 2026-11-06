#!/usr/bin/env python3
"""SignageCast – Software-Stückliste (SBOM) im Format CycloneDX 1.5 (JSON) erzeugen. Nur Standardbibliothek.

    python3 werkzeug/sbom.py paket --version 0.30.0 --datei signagecast-v0.30.0.tar.gz > signagecast-v0.30.0.cdx.json
    python3 werkzeug/sbom.py pi --version 0.30.0 --dpkg pakete.tsv --basis raspios.img.xz > signagecast-player-v0.30.0.cdx.json

„paket“: Release-Paket – SignageCast selbst (Prüfsumme des Pakets), die mitgelieferten Fremdkomponenten aus
werkzeug/komponenten.json (mit Prüfsumme ihrer Dateien), MediaMTX und die Debian-Pakete, die installieren.sh
installiert (ohne Version – die bestimmt Debian bei der Installation).
„pi“: Player-Image – alle Pakete des Images mit Version aus `dpkg-query -W -f '${Package}\\t${Version}\\t${Architecture}\\t${source:Package}\\n'`.
Das Container-Image bekommt seine SBOM von GitHub (docker/build-push-action, sbom: true).
Zeitstempel aus SOURCE_DATE_EPOCH (sonst jetzt), Seriennummer aus Inhalt – gleiche Eingaben ergeben die gleiche SBOM."""
import argparse, hashlib, json, os, re, sys, time, uuid

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "thefrozn/signagecast"


def sha256_datei(pfad):
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for teil in iter(lambda: f.read(1 << 20), b""):
            h.update(teil)
    return h.hexdigest()


def sha256_pfade(pfade):
    """Prüfsumme über Dateien/Ordner: SHA-256 über „<sha256>  <pfad>“ aller Dateien, sortiert (wie sha256sum)."""
    zeilen = []
    for p in pfade:
        voll = os.path.join(BASIS, p)
        dateien = [voll] if os.path.isfile(voll) else sorted(os.path.join(w, d) for w, _, ds in os.walk(voll) for d in ds)
        zeilen += [f"{sha256_datei(d)}  {os.path.relpath(d, BASIS)}" for d in dateien]
    return hashlib.sha256("\n".join(sorted(zeilen)).encode()).hexdigest() if zeilen else None


def komponenten():
    return json.load(open(os.path.join(BASIS, "werkzeug", "komponenten.json"), encoding="utf-8"))["komponenten"]


def debian_pakete_installation():
    """Paketnamen aus dem apt-get-install-Block von installieren.sh."""
    text = open(os.path.join(BASIS, "installieren.sh"), encoding="utf-8").read()
    m = re.search(r"^apt-get install [^\n]*?--no-install-recommends(.*?)>/dev/null", text, re.S | re.M)
    if not m:
        raise SystemExit("apt-get install in installieren.sh nicht gefunden")
    return sorted({w for w in m.group(1).replace("\\\n", " ").split() if re.fullmatch(r"[a-z0-9][a-z0-9.+-]+", w)})


def deb_purl(name, version=None, arch=None, distro="debian-13"):
    q = "&".join(x for x in (f"arch={arch}" if arch else "", f"distro={distro}") if x)
    return f"pkg:deb/debian/{name}" + (f"@{version}" if version else "") + f"?{q}"


def bom(version, haupt, teile, beschreibung):
    zeit = time.gmtime(int(os.environ.get("SOURCE_DATE_EPOCH", time.time())))
    inhalt = json.dumps([haupt, teile], sort_keys=True)
    haupt = dict(haupt, **{"bom-ref": "signagecast", "type": "application", "version": version,
                           "supplier": {"name": "SignageCast", "url": [f"https://github.com/{REPO}"]},
                           "licenses": [{"license": {"id": "MIT"}}],
                           "externalReferences": [{"type": "vcs", "url": f"https://github.com/{REPO}"}]})
    return {"bomFormat": "CycloneDX", "specVersion": "1.5",
            "serialNumber": "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, f"https://github.com/{REPO}/sbom/{inhalt}")),
            "version": 1,
            "metadata": {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", zeit),
                         "tools": {"components": [{"type": "application", "name": "signagecast werkzeug/sbom.py", "version": version}]},
                         "component": haupt, "properties": [{"name": "signagecast:inhalt", "value": beschreibung}]},
            "components": teile,
            "dependencies": [{"ref": "signagecast", "dependsOn": [t["bom-ref"] for t in teile]}]}


def paket(version, datei):
    teile = []
    for k in komponenten():
        t = {"type": "library", "bom-ref": k["id"], "name": k["name"], "version": k["version"], "purl": k["purl"],
             "licenses": [{"license": {"id": k["lizenz"]}}], "externalReferences": [{"type": "website", "url": k["url"]}]}
        h = sha256_pfade(k["pfade"])
        if h:
            t["hashes"] = [{"alg": "SHA-256", "content": h}]
            t["properties"] = [{"name": "signagecast:pfade", "value": ", ".join(k["pfade"])}]
        else:
            t["scope"] = "required"
            t["properties"] = [{"name": "signagecast:herkunft", "value": k.get("geladen", "")}]
        teile.append(t)
    for n in debian_pakete_installation():
        teile.append({"type": "library", "bom-ref": f"deb:{n}", "name": n, "purl": deb_purl(n, arch="amd64"), "scope": "required",
                      "properties": [{"name": "signagecast:herkunft", "value": "Debian 13, installiert von installieren.sh (Version bei Installation)"}]})
    haupt = {"name": "signagecast", "purl": f"pkg:github/{REPO}@v{version}"}
    if datei:
        haupt["hashes"] = [{"alg": "SHA-256", "content": sha256_datei(datei)}]
    return bom(version, haupt, teile, f"Release-Paket {os.path.basename(datei) if datei else ''}".strip())


def pi(version, dpkg, basis):
    teile, gesehen = [], set()
    for z in open(dpkg, encoding="utf-8"):
        f = z.rstrip("\n").split("\t")
        if len(f) < 3 or not f[0] or (f[0], f[1]) in gesehen:
            continue
        gesehen.add((f[0], f[1]))
        t = {"type": "library", "bom-ref": f"deb:{f[0]}:{f[2]}", "name": f[0], "version": f[1], "purl": deb_purl(f[0], f[1], f[2])}
        if len(f) > 3 and f[3] and f[3] != f[0]:
            t["properties"] = [{"name": "signagecast:quellpaket", "value": f[3]}]
        teile.append(t)
    teile.sort(key=lambda t: t["bom-ref"])
    haupt = {"name": "signagecast-player", "purl": f"pkg:github/{REPO}@v{version}#player"}
    return bom(version, haupt, teile, f"Raspberry-Pi-Player-Image auf Basis {basis}")


def main():
    ap = argparse.ArgumentParser(description="SBOM (CycloneDX 1.5) für SignageCast")
    ap.add_argument("art", choices=("paket", "pi"))
    ap.add_argument("--version", required=True)
    ap.add_argument("--datei", help="paket: Release-Paket (für die Prüfsumme)")
    ap.add_argument("--dpkg", help="pi: Ausgabe von dpkg-query (TSV)")
    ap.add_argument("--basis", default="Raspberry Pi OS Lite (arm64)", help="pi: Grundimage")
    a = ap.parse_args()
    if a.art == "pi" and not a.dpkg:
        ap.error("pi braucht --dpkg")
    b = paket(a.version, a.datei) if a.art == "paket" else pi(a.version, a.dpkg, a.basis)
    json.dump(b, sys.stdout, indent=1, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
