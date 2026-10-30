# Unwetterwarnungen des Deutschen Wetterdienstes (DWD) für den Standort: Geodienst (WFS) „Warnungen_Gemeinden“, Abfrage
# per Punkt (Breite Länge). Kostenlos, ohne Schlüssel; Quellenvermerk „Deutscher Wetterdienst“ ist Pflicht.
# Außerhalb Deutschlands gibt es keine Treffer – der Baustein bleibt dann leer.
import json, urllib.parse, urllib.request

URL = ("https://maps.dwd.de/geoserver/dwd/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=dwd:Warnungen_Gemeinden"
       "&outputFormat=application/json&propertyName=EVENT,SEVERITY,HEADLINE,DESCRIPTION,ONSET,EXPIRES,IDENTIFIER&CQL_FILTER=")
STUFEN = {"Minor": 1, "Moderate": 2, "Severe": 3, "Extreme": 4}
UA = {"User-Agent": "SignageCast (+https://github.com/thefrozn/signagecast)"}


def holen(breite, laenge):
    """Aktuelle Warnungen am Standort, schwerste zuerst: [{ereignis, stufe 1–4, titel, text, von, bis}]."""
    filt = urllib.parse.quote(f"INTERSECTS(THE_GEOM,POINT({breite:.4f} {laenge:.4f}))")
    with urllib.request.urlopen(urllib.request.Request(URL + filt, headers=UA), timeout=20) as r:
        d = json.load(r)
    aus, gesehen = [], set()
    for f in d.get("features", []):
        p = f.get("properties") or {}
        schluessel = p.get("IDENTIFIER") or (p.get("EVENT"), p.get("ONSET"))
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        aus.append({"ereignis": str(p.get("EVENT", ""))[:60], "stufe": STUFEN.get(p.get("SEVERITY"), 1),
                    "titel": str(p.get("HEADLINE", ""))[:120], "text": str(p.get("DESCRIPTION", ""))[:300],
                    "von": p.get("ONSET"), "bis": p.get("EXPIRES")})
    return sorted(aus, key=lambda w: -w["stufe"])
