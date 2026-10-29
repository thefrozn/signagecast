# Zeitquelle: misst per SNTP (UDP 123) die Abweichung der Systemuhr zu einem NTP-Server.
# Ein Container kann seine Uhr nicht selbst stellen (sie kommt vom Host) – SignageCast korrigiert deshalb die angezeigte
# Uhrzeit, den Takt der Rotation und den Start der Einspieler um die gemessene Abweichung.
# Standard-Server: Länder-Pool zum Standort (z. B. de.pool.ntp.org), sonst pool.ntp.org.
import ctypes, ctypes.util, socket, statistics, struct, time
from meldung import Meldung

NTP_EPOCHE = 2208988800          # Sekunden zwischen 1900-01-01 (NTP) und 1970-01-01 (Unix)


def _zeitstempel(daten, pos):
    sek, bruch = struct.unpack("!II", daten[pos:pos + 8])
    return sek - NTP_EPOCHE + bruch / 2 ** 32


def abfragen(server, timeout=4):
    """Eine SNTP-Abfrage: (Abweichung in s – positiv = Systemuhr geht nach, Laufzeit in s)."""
    paket = b"\x23" + 47 * b"\0"              # LI 0, Version 4, Modus 3 (Client)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(timeout)
        t0 = time.time()
        s.sendto(paket, (server, 123))
        daten, _ = s.recvfrom(48)
        t3 = time.time()
    if len(daten) < 48 or (daten[0] & 0x07) not in (4, 5) or daten[1] == 0:
        raise Meldung("ntp_ungueltig")
    t1, t2 = _zeitstempel(daten, 32), _zeitstempel(daten, 40)
    return ((t1 - t0) + (t2 - t3)) / 2, (t3 - t0) - (t2 - t1)


def messen(server, versuche=4):
    """Mehrere Abfragen, die mit der kürzesten Laufzeit zählen am meisten (Median der besten Hälfte)."""
    ergebnisse = []
    for _ in range(versuche):
        try:
            ergebnisse.append(abfragen(server))
        except Exception:
            pass
        time.sleep(0.3)
    if not ergebnisse:
        raise Meldung("ntp_stumm", server=server)
    ergebnisse.sort(key=lambda x: x[1])
    beste = ergebnisse[:max(1, len(ergebnisse) // 2)]
    return statistics.median(x[0] for x in beste), min(x[1] for x in ergebnisse)


def standard_server(laendercode):
    cc = (laendercode or "").lower()
    return f"{cc}.pool.ntp.org" if len(cc) == 2 and cc.isalpha() else "pool.ntp.org"


def host_synchronisiert():
    """True, wenn der Kernel seine Uhr als synchronisiert führt (NTP/chrony auf dem Host, z. B. Proxmox).
    Container und Host teilen sich den Kernel; adjtimex() mit modes = 0 liest nur und ist ohne Rechte erlaubt.
    Rückgabe 5 (TIME_ERROR) = nicht synchronisiert. None, wenn sich das nicht feststellen lässt."""
    try:
        libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
        return libc.adjtimex(ctypes.create_string_buffer(512)) not in (5, -1)
    except Exception:
        return None


# Zeitzone aus dem Land (nur Länder mit einer einzigen Zeitzone) – für Container, die in UTC laufen
ZONE_NACH_LAND = {
    "DE": "Europe/Berlin", "AT": "Europe/Vienna", "CH": "Europe/Zurich", "LI": "Europe/Vaduz", "NL": "Europe/Amsterdam",
    "BE": "Europe/Brussels", "LU": "Europe/Luxembourg", "FR": "Europe/Paris", "IT": "Europe/Rome", "ES": "Europe/Madrid",
    "GB": "Europe/London", "IE": "Europe/Dublin", "DK": "Europe/Copenhagen", "SE": "Europe/Stockholm", "NO": "Europe/Oslo",
    "FI": "Europe/Helsinki", "PL": "Europe/Warsaw", "CZ": "Europe/Prague", "SK": "Europe/Bratislava", "HU": "Europe/Budapest",
    "SI": "Europe/Ljubljana", "HR": "Europe/Zagreb", "GR": "Europe/Athens", "RO": "Europe/Bucharest", "BG": "Europe/Sofia",
    "EE": "Europe/Tallinn", "LV": "Europe/Riga", "LT": "Europe/Vilnius", "IS": "Atlantic/Reykjavik", "JP": "Asia/Tokyo",
    "KR": "Asia/Seoul", "IN": "Asia/Kolkata", "ZA": "Africa/Johannesburg", "IL": "Asia/Jerusalem", "TR": "Europe/Istanbul",
}
